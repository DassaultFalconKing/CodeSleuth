#!/usr/bin/env python3
"""Create trusted durable EHA identity before provider/model execution.

This helper is intentionally narrow. It does not run SIB profiles, record verdicts,
or complete a campaign. It creates the review checkpoint, binds canonical
provenance metadata, and only then appends the campaign_started event consumed by
review_state/eha_state.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


SHA_RE = re.compile(r"^[0-9a-f]{40}$")
TRUSTED_ACTOR = "github-eha"


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
    raw = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"])
    return sum(1 for item in raw.split(b"\0") if item)


def canonical_session_watermark(
    root: Path, *, actor: str, target_sha: str, controller_session: str
) -> str:
    """Use the canonical provenance implementation instead of reimplementing its hash."""
    script = root / "scripts" / "provenance_watermark.py"
    if not script.is_file():
        raise BootstrapError("canonical provenance watermark implementation is missing")
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "session",
            "--actor",
            actor,
            "--head",
            target_sha,
            "--session-id",
            controller_session,
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise BootstrapError(
            "canonical provenance watermark computation failed: "
            + (completed.stderr.strip() or completed.stdout.strip())
        )
    watermark = completed.stdout.strip()
    if not watermark.startswith(actor + "-") or len(watermark) != len(actor) + 13:
        raise BootstrapError("canonical provenance watermark returned an invalid identity")
    return watermark


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

    # Provenance is attribution metadata only. It must exist before the first EHA
    # ledger event so even a provider failure before first response leaves an
    # attributable durable campaign. The hash itself remains owned by the
    # canonical provenance_watermark.py implementation.
    watermark = canonical_session_watermark(
        root,
        actor=TRUSTED_ACTOR,
        target_sha=target_sha,
        controller_session=controller_session,
    )
    provenance = {
        "schemaVersion": 1,
        "actor": TRUSTED_ACTOR,
        "watermark": watermark,
        "kind": "session-attribution",
        "headSha": target_sha,
        "reviewId": review_id,
        "sessionID": controller_session,
        "recordedAt": started_at,
    }
    atomic_write(review_dir / "provenance.json", json.dumps(provenance, indent=2) + "\n")

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
        "provenance": provenance,
        "statePath": str(review_dir / "state.json"),
        "provenancePath": str(review_dir / "provenance.json"),
        "ledgerPath": str(review_dir / "eha.ndjson"),
    }
