#!/usr/bin/env python3
"""Run the canonical CodeSleuth EHA Playbook from a trusted GitHub runner.

This module is deliberately an adapter, not an EHA implementation.  It freezes
one literal release-stream SHA, wires host-persistent local evidence into the
checkout, invokes OpenCode `/eha-test`, and then derives a small execution status
from the authoritative `eha.ndjson` ledger.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable


SHA_RE = re.compile(r"^[0-9a-f]{40}$")
RELEASE_BRANCH_RE = re.compile(r"^dev/release-[0-9]+\.[0-9]+\.[0-9]+$")
LEVELS = ("SIB0", "SIB1", "SIB2")
DEFAULT_SCOPE = "SIB0/SIB1/SIB2 exact-head acceptance"


class BridgeError(RuntimeError):
    """Fail-closed bridge error."""


def run_git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def git_stdout(root: Path, *args: str) -> str:
    return run_git(root, *args).stdout.strip()


def validate_release_branch(value: str) -> str:
    branch = value.strip()
    if not RELEASE_BRANCH_RE.fullmatch(branch):
        raise BridgeError(
            "release branch must be a literal dev/release-X.Y.Z ref; "
            f"got {value!r}"
        )
    return branch


def validate_sha(value: str) -> str:
    sha = value.strip().lower()
    if not SHA_RE.fullmatch(sha):
        raise BridgeError("expected SHA must be a full 40-character lowercase Git SHA")
    return sha


def parse_issue_request(body: str) -> tuple[str, str, str]:
    """Parse one owner-authored `/eha-test <release> <sha> [scope]` line."""
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    if not lines:
        raise BridgeError("empty EHA request")
    try:
        parts = shlex.split(lines[0])
    except ValueError as exc:
        raise BridgeError(f"invalid EHA request quoting: {exc}") from exc
    if len(parts) < 3 or parts[0] != "/eha-test":
        raise BridgeError(
            "issue command must be: /eha-test dev/release-X.Y.Z <40-char-sha> [scope]"
        )
    branch = validate_release_branch(parts[1])
    sha = validate_sha(parts[2])
    scope = " ".join(parts[3:]).strip() or DEFAULT_SCOPE
    if len(scope) > 800:
        raise BridgeError("EHA scope is too long")
    return branch, sha, scope


def resolve_request(args: argparse.Namespace) -> tuple[str, str, str]:
    if args.request is not None:
        if args.release_branch or args.expected_sha:
            raise BridgeError("use either --request or explicit release/SHA arguments, not both")
        return parse_issue_request(args.request)
    if not args.release_branch or not args.expected_sha:
        raise BridgeError("--release-branch and --expected-sha are required together")
    branch = validate_release_branch(args.release_branch)
    sha = validate_sha(args.expected_sha)
    scope = (args.scope or DEFAULT_SCOPE).strip() or DEFAULT_SCOPE
    if len(scope) > 800:
        raise BridgeError("EHA scope is too long")
    return branch, sha, scope


def require_clean(root: Path, stage: str) -> None:
    status = git_stdout(root, "status", "--porcelain=v1")
    if status:
        raise BridgeError(f"{stage}: worktree is not clean:\n{status}")


def freeze_release_head(root: Path, release_branch: str, expected_sha: str) -> None:
    remote_ref = f"refs/remotes/origin/{release_branch}"
    fetch_refspec = f"+refs/heads/{release_branch}:{remote_ref}"
    run_git(root, "fetch", "--no-tags", "origin", fetch_refspec)
    resolved = validate_sha(git_stdout(root, "rev-parse", remote_ref))
    if resolved != expected_sha:
        raise BridgeError(
            "EHA request is stale: literal release-stream head is "
            f"{resolved}, requested {expected_sha}"
        )
    run_git(root, "checkout", "--detach", expected_sha)
    actual = validate_sha(git_stdout(root, "rev-parse", "HEAD"))
    if actual != expected_sha:
        raise BridgeError(f"checkout identity mismatch: expected {expected_sha}, got {actual}")
    require_clean(root, "candidate selection")


def ensure_external(root: Path, persist_root: Path) -> Path:
    worktree = root.resolve()
    target = persist_root.expanduser().resolve()
    try:
        target.relative_to(worktree)
    except ValueError:
        pass
    else:
        raise BridgeError(
            "EHA persistence root must be outside the checkout so Actions cleanup cannot erase authority"
        )
    target.mkdir(parents=True, exist_ok=True)
    return target


def ensure_symlink(link: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    if link.is_symlink():
        if link.resolve() == target.resolve():
            return
        raise BridgeError(f"refusing to replace unexpected symlink {link} -> {link.resolve()}")
    if link.exists():
        raise BridgeError(f"refusing to replace existing path used for EHA persistence: {link}")
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(target, target_is_directory=True)


def append_local_excludes(root: Path, paths: Iterable[str]) -> None:
    exclude_path = Path(git_stdout(root, "rev-parse", "--git-path", "info/exclude"))
    if not exclude_path.is_absolute():
        exclude_path = root / exclude_path
    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude_path.read_text(encoding="utf-8") if exclude_path.exists() else ""
    lines = set(existing.splitlines())
    additions = [path for path in paths if path not in lines]
    if additions:
        with exclude_path.open("a", encoding="utf-8") as handle:
            if existing and not existing.endswith("\n"):
                handle.write("\n")
            for item in additions:
                handle.write(f"{item}\n")


def wire_persistence(root: Path, persist_root: Path) -> tuple[Path, Path]:
    """Keep canonical logical paths while storing them outside the disposable checkout."""
    state_dir = persist_root / "state"
    report_dir = persist_root / "reports"
    append_local_excludes(root, ("/.opencode/state", "/.codesleuth/reports"))
    ensure_symlink(root / ".opencode" / "state", state_dir)
    ensure_symlink(root / ".codesleuth" / "reports", report_dir)
    require_clean(root, "persistence wiring")
    return state_dir, report_dir


def read_events(ledger: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not ledger.exists():
        return events
    for line_no, raw in enumerate(ledger.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise BridgeError(f"corrupt EHA ledger {ledger}:{line_no}: {exc}") from exc
        if not isinstance(event, dict):
            raise BridgeError(f"invalid EHA ledger record {ledger}:{line_no}")
        events.append(event)
    return events


def all_ledgers(state_dir: Path) -> Iterable[Path]:
    reviews = state_dir / "reviews"
    if not reviews.exists():
        return ()
    return sorted(reviews.glob("*/eha.ndjson"))


def prior_failed_sha(state_dir: Path, target_sha: str) -> tuple[str, str] | None:
    """Enforce failed-SHA immutability across review directories, not just one session."""
    for ledger in all_ledgers(state_dir):
        for event in read_events(ledger):
            if (
                event.get("type") == "verdict"
                and event.get("targetSha") == target_sha
                and event.get("verdict") == "FAIL"
            ):
                return ledger.parent.name, str(event.get("campaignId", "unknown"))
    return None


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def latest_new_campaign(
    state_dir: Path, target_sha: str, not_before: datetime
) -> tuple[str, dict[str, Any], list[dict[str, Any]]] | None:
    candidates: list[tuple[datetime, str, dict[str, Any], list[dict[str, Any]]]] = []
    floor = not_before - timedelta(seconds=5)
    for ledger in all_ledgers(state_dir):
        events = read_events(ledger)
        for event in events:
            if event.get("type") != "campaign_started" or event.get("targetSha") != target_sha:
                continue
            recorded = parse_time(event.get("recordedAt"))
            if recorded is None or recorded < floor:
                continue
            candidates.append((recorded, ledger.parent.name, event, events))
    if not candidates:
        return None
    _, review_id, start, events = max(candidates, key=lambda item: item[0])
    return review_id, start, events


def verdict_summary(start: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, str]:
    campaign_id = start.get("campaignId")
    result = {level: "PENDING" for level in LEVELS}
    for event in events:
        if event.get("type") != "verdict" or event.get("campaignId") != campaign_id:
            continue
        level = event.get("level")
        verdict = event.get("verdict")
        if level in result and verdict in {"PASS", "FAIL"}:
            result[str(level)] = str(verdict)
    return result


def opencode_environment(root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["OPENCODE_CONFIG"] = str(root / "pack" / ".opencode" / "opencode.json")
    env["OPENCODE_CONFIG_DIR"] = str(root / "pack" / ".opencode")
    env["OPENCODE_DISABLE_AUTOUPDATE"] = "true"
    env["OPENCODE_PERMISSION"] = json.dumps(
        {
            "edit": {"*": "deny", ".codesleuth/reports/**": "allow"},
            "bash": "allow",
            "external_directory": "allow",
            "question": "deny",
            "doom_loop": "deny",
        },
        separators=(",", ":"),
    )
    return env


def invoke_opencode(
    root: Path,
    release_branch: str,
    expected_sha: str,
    scope: str,
    model: str | None,
) -> tuple[int, str]:
    binary = shutil.which("opencode")
    if not binary:
        raise BridgeError(
            "opencode is not installed on this runner; canonical EHA requires a trusted OpenCode host"
        )
    version = subprocess.run(
        [binary, "--version"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ).stdout.strip()
    wrapper = root / "pack" / ".opencode" / "bin" / "opencode-review"
    if not wrapper.exists():
        raise BridgeError(f"CodeSleuth OpenCode wrapper missing at exact target: {wrapper}")

    message = (
        "GitHub EHA bridge request. Treat this as normal future-SIB selection. "
        f"Release stream: {release_branch}. Expected literal release HEAD and checkout SHA: "
        f"{expected_sha}. Scope: {scope}. The bridge already verified the remote release ref, "
        "checked out the exact SHA detached, and attached host-persistent canonical review/EHA state. "
        "Do not modify application/source files. Run the canonical eha-sib-acceptance Playbook only."
    )
    command = [str(wrapper), "run", "--command", "eha-test", "--format", "json"]
    if model:
        command.extend(["--model", model])
    command.append(message)
    print(f"OPENCODE VERSION {version}", flush=True)
    print(f"EHA EXACT TARGET {expected_sha} FROM {release_branch}", flush=True)
    completed = subprocess.run(command, cwd=root, env=opencode_environment(root), check=False)
    return completed.returncode, version


def write_bridge_status(
    persist_root: Path,
    *,
    review_id: str | None,
    campaign_id: str | None,
    release_branch: str,
    target_sha: str,
    verdicts: dict[str, str],
    outcome: str,
    opencode_version: str,
    opencode_returncode: int,
) -> Path:
    runs = persist_root / "bridge-runs"
    runs.mkdir(parents=True, exist_ok=True)
    run_id = os.environ.get("GITHUB_RUN_ID") or datetime.now(timezone.utc).strftime("local-%Y%m%dT%H%M%SZ")
    path = runs / f"{run_id}.json"
    payload = {
        "schemaVersion": 1,
        "adapter": "github-opencode-eha",
        "repository": os.environ.get("GITHUB_REPOSITORY"),
        "githubRunId": os.environ.get("GITHUB_RUN_ID"),
        "reviewId": review_id,
        "campaignId": campaign_id,
        "releaseBranch": release_branch,
        "targetSha": target_sha,
        "verdicts": verdicts,
        "outcome": outcome,
        "opencodeVersion": opencode_version,
        "opencodeReturnCode": opencode_returncode,
        "recordedAt": datetime.now(timezone.utc).isoformat(),
        "authority": "state/reviews/<reviewId>/eha.ndjson",
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", help="owner-authored GitHub issue comment command")
    parser.add_argument("--release-branch")
    parser.add_argument("--expected-sha")
    parser.add_argument("--scope", default=DEFAULT_SCOPE)
    parser.add_argument("--persist-root", required=True)
    parser.add_argument("--model", default=os.environ.get("CODESLEUTH_EHA_MODEL"))
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        root = Path.cwd().resolve()
        if not (root / ".git").exists():
            raise BridgeError("run the EHA bridge from the repository root")
        release_branch, expected_sha, scope = resolve_request(args)
        persist_root = ensure_external(root, Path(args.persist_root))

        require_clean(root, "bridge entry")
        freeze_release_head(root, release_branch, expected_sha)
        state_dir, _ = wire_persistence(root, persist_root)

        prior_fail = prior_failed_sha(state_dir, expected_sha)
        if prior_fail:
            review_id, campaign_id = prior_fail
            raise BridgeError(
                "exact target already has a durable FAIL verdict in review "
                f"{review_id}, campaign {campaign_id}; failed SHAs are immutable, repair to a new SHA"
            )

        started = datetime.now(timezone.utc)
        opencode_returncode, opencode_version = invoke_opencode(
            root, release_branch, expected_sha, scope, args.model
        )
        require_clean(root, "post-EHA exact-target check")

        found = latest_new_campaign(state_dir, expected_sha, started)
        if not found:
            raise BridgeError(
                "OpenCode returned without a new durable EHA campaign for the exact target"
            )
        review_id, start, events = found
        verdicts = verdict_summary(start, events)
        campaign_id = str(start.get("campaignId"))
        if "FAIL" in verdicts.values():
            outcome = "FAIL"
        elif all(verdicts[level] == "PASS" for level in LEVELS):
            outcome = "PASS"
        else:
            outcome = "INCOMPLETE"

        status_path = write_bridge_status(
            persist_root,
            review_id=review_id,
            campaign_id=campaign_id,
            release_branch=release_branch,
            target_sha=expected_sha,
            verdicts=verdicts,
            outcome=outcome,
            opencode_version=opencode_version,
            opencode_returncode=opencode_returncode,
        )
        print(
            "EHA BRIDGE RESULT "
            f"campaign={campaign_id} review={review_id} target={expected_sha} "
            f"SIB0={verdicts['SIB0']} SIB1={verdicts['SIB1']} SIB2={verdicts['SIB2']} "
            f"outcome={outcome}",
            flush=True,
        )
        print(f"BRIDGE STATUS {status_path}", flush=True)

        if opencode_returncode != 0:
            print(
                f"OpenCode exited {opencode_returncode}; durable ledger is preserved but bridge execution is not clean",
                file=sys.stderr,
            )
            return 4
        if outcome == "PASS":
            return 0
        if outcome == "FAIL":
            return 2
        return 3
    except BridgeError as exc:
        print(f"EHA BRIDGE ERROR: {exc}", file=sys.stderr)
        return 5
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        print(f"EHA BRIDGE ERROR: command failed ({exc.returncode}): {detail}", file=sys.stderr)
        return 6


if __name__ == "__main__":
    raise SystemExit(main())
