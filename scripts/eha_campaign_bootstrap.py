#!/usr/bin/env python3
"""Create the minimal durable review/EHA campaign authority before model execution.

This helper is intentionally narrow. It does not run SIB profiles, record verdicts,
or complete a campaign. It creates the same review checkpoint and campaign_started
shape consumed by review_state/eha_state so a trusted controller can establish
campaign identity before provider/model transport is involved.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class BootstrapError(RuntimeError):
    pass


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def append_json_line(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, separators=(",", ":"), ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def compact_stamp(now: datetime) -> str:
    return now.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S")


def tracked_file_count(root: Path) -> int:
    raw = subprocess.check_output(
        ["git", "-C", str(root), "ls-files", "-z"],
    )
    return sum(1 for item in raw.split(b"\0") if item)


def start_trusted_campaign(
    root: Path,
    state_dir: Path,
    *,
    target_sha: str,
    target_branch: str,
    scope: str,
    controller_session: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    state_dir = state_dir.resolve()
    target_sha = target_sha.strip().lower()
    if not SHA_RE.fullmatch(target_sha):
        raise BootstrapError("target SHA must be a full 40-character lowercase Git SHA")
    head = git(root, "rev-parse", "HEAD")
    if head != target_sha:
        raise BootstrapError(
            f"EHA INVALIDATED — HEAD CHANGED: bootstrap expected {target_sha}, got {head}"
        )
    if git(root, "status", "--porcelain=v1"):
        raise BootstrapError("trusted campaign bootstrap requires a clean exact-target worktree")

    reviews = state_dir / "reviews"
    reviews.mkdir(parents=True, exist_ok=True)
    timestamp = now or datetime.now(timezone.utc)
    stamp = compact_stamp(timestamp)
    review_id = f"{stamp}-{target_sha[:12]}-bridge-{uuid4().hex[:8]}"
    campaign_id = f"EHA-{stamp}-{target_sha[:12]}-{uuid4().hex[:8]}"
    review_dir = reviews / review_id
    review_dir.mkdir(parents=False, exist_ok=False)

    started_at = timestamp.astimezone(timezone.utc).isoformat()
    review_state = {
        "schemaVersion": 2,
        "reviewId": review_id,
        "sessionID": controller_session,
        "mode": "review",
        "objective": "Trusted GitHub EHA exact-head acceptance",
        "target": target_sha,
        "startedAt": started_at,
        "updatedAt": started_at,
        "headSha": target_sha,
        "trackedFileCountAtStart": tracked_file_count(root),
        "dirtyAtStart": False,
        "phase": "authority",
        "completed": [],
        "reviewedPaths": [],
        "reviewedPathEvidence": [],
        "openQuestions": [],
        "next": ["consume prestarted EHA campaign and run SIB0 profile"],
        "note": "review checkpoint bootstrapped by trusted bridge before model/provider execution",
    }
    atomic_write(review_dir / "state.json", json.dumps(review_state, indent=2) + "\n")
    atomic_write(reviews / "latest.txt", review_id + "\n")

    event = {
        "type": "campaign_started",
        "eventId": f"E-{uuid4()}",
        "campaignId": campaign_id,
        "targetSha": target_sha,
        "targetBranch": target_branch,
        "scope": scope,
        "recordedAt": started_at,
        "recordedHeadSha": target_sha,
        "bootstrapAuthority": "trusted_github_bridge",
    }
    append_json_line(review_dir / "eha.ndjson", event)
    return {
        "reviewId": review_id,
        "campaign": event,
        "statePath": str(review_dir / "state.json"),
        "ledgerPath": str(review_dir / "eha.ndjson"),
    }
