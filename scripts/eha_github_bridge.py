#!/usr/bin/env python3
"""Run the canonical CodeSleuth EHA Playbook from a trusted GitHub runner.

This module is deliberately an adapter, not an EHA implementation. It freezes
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
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, NamedTuple


SHA_RE = re.compile(r"^[0-9a-f]{40}$")
RELEASE_BRANCH_RE = re.compile(r"^dev/release-[0-9]+\.[0-9]+\.[0-9]+$")
LEVELS = ("SIB0", "SIB1", "SIB2")
DEFAULT_SCOPE = "SIB0/SIB1/SIB2 exact-head acceptance"
DEFAULT_FIRST_RESPONSE_TIMEOUT_SECONDS = 120.0
DEFAULT_CAMPAIGN_START_TIMEOUT_SECONDS = 300.0
DEFAULT_IDLE_TIMEOUT_SECONDS = 480.0
DEFAULT_WATCHDOG_POLL_SECONDS = 1.0
MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._:-]*$")
EHA_READ_ONLY_BASH_PATTERNS = (
    "git status*",
    "git diff*",
    "git log*",
    "git show*",
    "git rev-parse*",
    "git ls-files*",
    "git branch --show-current*",
    "git merge-base*",
    "git cat-file*",
    "git blame*",
    "git grep*",
    "git ls-tree*",
    "git rev-list*",
    "Get-Content*",
    "Get-ChildItem*",
    "Get-Item*",
    "Get-Date*",
    "Test-Path*",
    "Resolve-Path*",
    "Select-String*",
    "Select-Object*",
    "Format-List*",
    "Format-Table*",
    "Out-String*",
    "head*",
    "tail*",
    "grep*",
    "rg*",
    "sort*",
    "uniq*",
    "wc*",
    "echo*",
    "pwd",
    "ls*",
    "python -m pytest*",
    "python3 -m pytest*",
    "python scripts/contributor_antipatterns.py scan --strict*",
    "python3 scripts/contributor_antipatterns.py scan --strict*",
    "python scripts/eha_candidate_status.py*",
    "python3 scripts/eha_candidate_status.py*",
    "python -m ruff check*",
    "python3 -m ruff check*",
    "ruff check*",
    "bun --version*",
    "bun run test*",
    "bun tests/*",
    ".opencode/bin/codesleuth-reports sync*",
    "./.opencode/bin/codesleuth-reports sync*",
    ".opencode/bin/codesleuth-reports publish*",
    "./.opencode/bin/codesleuth-reports publish*",
    ".opencode/bin/codesleuth-reports.ps1 sync*",
    ".opencode/bin/codesleuth-reports.ps1 publish*",
    "pack/.opencode/bin/codesleuth-reports sync*",
    "pack/.opencode/bin/codesleuth-reports publish*",
    "pack/.opencode/bin/codesleuth-reports.ps1 sync*",
    "pack/.opencode/bin/codesleuth-reports.ps1 publish*",
    "gh run list*",
    "gh run view*",
)
EHA_BASH_DENY_PATTERNS = (
    "*>*",
    "*Get-ChildItem*-Recurse*",
    "*Out-File*",
    "*Set-Content*",
    "*Add-Content*",
    "*Clear-Content*",
    "*New-Item*",
    "*Remove-Item*",
    "*Move-Item*",
    "*Copy-Item*",
    "*Rename-Item*",
    "*Tee-Object*",
)


class BridgeError(RuntimeError):
    """Fail-closed bridge error."""


class WatchdogConfig(NamedTuple):
    first_response_seconds: float = DEFAULT_FIRST_RESPONSE_TIMEOUT_SECONDS
    campaign_start_seconds: float = DEFAULT_CAMPAIGN_START_TIMEOUT_SECONDS
    idle_seconds: float = DEFAULT_IDLE_TIMEOUT_SECONDS
    poll_seconds: float = DEFAULT_WATCHDOG_POLL_SECONDS


class OpenCodeExecution(NamedTuple):
    returncode: int
    version: str
    model: str
    transport_outcome: str
    reason: str | None
    first_response_observed: bool
    campaign_observed: bool
    completion_observed: bool
    started_at: datetime
    last_activity_at: datetime
    stalled_at: datetime | None


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


def validate_model(value: str | None) -> str:
    model = (value or "").strip()
    if not model:
        raise BridgeError(
            "canonical EHA requires an explicit host-qualified model via "
            "--model or CODESLEUTH_EHA_MODEL"
        )
    if len(model) > 200 or not MODEL_RE.fullmatch(model):
        raise BridgeError(
            "EHA model must be an explicit provider/model identifier; "
            f"got {value!r}"
        )
    return model


def positive_seconds(value: str | float, name: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise BridgeError(f"{name} must be a positive number of seconds") from exc
    if parsed <= 0:
        raise BridgeError(f"{name} must be a positive number of seconds")
    return parsed


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


def campaign_completion(
    start: dict[str, Any], events: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Return only a valid durable completion event for the exact campaign."""
    campaign_id = start.get("campaignId")
    target_sha = start.get("targetSha")
    verdicts = verdict_summary(start, events)
    for event in reversed(events):
        if event.get("type") != "campaign_completed" or event.get("campaignId") != campaign_id:
            continue
        if event.get("targetSha") != target_sha:
            raise BridgeError(
                f"campaign completion target mismatch for {campaign_id}: "
                f"expected {target_sha}, got {event.get('targetSha')}"
            )
        report_path = event.get("reportPath")
        if not isinstance(report_path, str) or not report_path.startswith(
            ".codesleuth/reports/"
        ):
            raise BridgeError(
                f"campaign completion for {campaign_id} lacks a canonical report path"
            )
        if not all(verdicts[level] == "PASS" for level in LEVELS):
            raise BridgeError(
                f"campaign completion for {campaign_id} exists before all SIB verdicts are PASS"
            )
        return event
    return None


def eha_bash_permissions() -> dict[str, str]:
    """Return a fail-closed allowlist for EHA inspection and test commands."""
    return {
        "*": "deny",
        **{pattern: "allow" for pattern in EHA_READ_ONLY_BASH_PATTERNS},
        **{pattern: "deny" for pattern in EHA_BASH_DENY_PATTERNS},
    }


def prepare_scratch_dir(root: Path, persist_root: Path) -> Path:
    """Allocate one external scratch directory without weakening checkout cleanliness."""
    external = ensure_external(root, persist_root)
    scratch = external / "bridge-runtime" / bridge_run_key() / "scratch"
    try:
        scratch.mkdir(parents=True, exist_ok=False, mode=0o700)
    except FileExistsError as exc:
        raise BridgeError(f"refusing to reuse existing EHA scratch directory: {scratch}") from exc
    return scratch


def opencode_environment(
    root: Path,
    scratch_dir: Path,
    *,
    release_branch: str,
    expected_sha: str,
) -> dict[str, str]:
    env = os.environ.copy()
    env["OPENCODE_CONFIG"] = str(root / "pack" / ".opencode" / "opencode.json")
    env["OPENCODE_CONFIG_DIR"] = str(root / "pack" / ".opencode")
    env["OPENCODE_DISABLE_AUTOUPDATE"] = "true"
    env["CODESLEUTH_EHA_SCRATCH_DIR"] = str(scratch_dir)
    env["TEMP"] = str(scratch_dir)
    env["TMP"] = str(scratch_dir)
    env["TMPDIR"] = str(scratch_dir)
    env["CODESLEUTH_EHA_PREVERIFIED"] = "1"
    env["CODESLEUTH_EHA_RELEASE_BRANCH"] = release_branch
    env["CODESLEUTH_EHA_EXPECTED_SHA"] = expected_sha
    env["OPENCODE_PERMISSION"] = json.dumps(
        {
            "edit": {"*": "deny", ".codesleuth/reports/**": "allow"},
            "bash": eha_bash_permissions(),
            "external_directory": "allow",
            "question": "deny",
            "doom_loop": "deny",
        },
        separators=(",", ":"),
    )
    return env


def bridge_run_key() -> str:
    run_id = os.environ.get("GITHUB_RUN_ID")
    attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "1")
    if run_id:
        return f"{run_id}-attempt-{attempt}"
    return datetime.now(timezone.utc).strftime("local-%Y%m%dT%H%M%SZ")


def private_transcript_path(persist_root: Path) -> Path:
    logs = persist_root / "bridge-logs"
    logs.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = logs / f"{bridge_run_key()}.log"
    if path.exists():
        raise BridgeError(f"refusing to overwrite existing EHA transcript record: {path.name}")
    path.touch(mode=0o600, exist_ok=False)
    return path


def opencode_wrapper_command(root: Path, platform_name: str | None = None) -> list[str]:
    """Select the shipped OpenCode wrapper that the current host can execute."""
    platform_name = platform_name or os.name
    bin_dir = root / "pack" / ".opencode" / "bin"
    if platform_name == "nt":
        wrapper = bin_dir / "opencode-review.ps1"
        if not wrapper.exists():
            raise BridgeError(f"CodeSleuth Windows OpenCode wrapper missing at exact target: {wrapper}")
        powershell = shutil.which("pwsh") or shutil.which("powershell") or shutil.which("powershell.exe")
        if not powershell:
            raise BridgeError(
                "PowerShell is not installed on this Windows runner; canonical EHA requires the shipped opencode-review.ps1 wrapper"
            )
        return [
            powershell,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(wrapper),
        ]

    wrapper = bin_dir / "opencode-review"
    if not wrapper.exists():
        raise BridgeError(f"CodeSleuth OpenCode wrapper missing at exact target: {wrapper}")
    return [str(wrapper)]


def evidence_activity_signature(transcript_path: Path, state_dir: Path) -> tuple[tuple[str, int, int], ...]:
    """Return a bounded signature for transcript and authoritative EHA activity."""
    paths = [transcript_path]
    reviews = state_dir / "reviews"
    if reviews.exists():
        paths.extend(path for path in reviews.glob("*/eha.ndjson") if path.is_file())
    signature: list[tuple[str, int, int]] = []
    for path in sorted(paths):
        try:
            stat = path.stat()
        except FileNotFoundError:
            continue
        signature.append((str(path), stat.st_size, stat.st_mtime_ns))
    return tuple(signature)


def terminate_process_tree(
    process: subprocess.Popen[str], *, grace_seconds: float = 5.0
) -> int:
    """Terminate only the OpenCode process group created by this bridge."""
    if process.poll() is not None:
        return int(process.returncode or 0)
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        return process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        if os.name != "nt":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        return process.wait(timeout=grace_seconds)


def run_monitored_process(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    transcript_path: Path,
    state_dir: Path,
    expected_sha: str,
    started_at: datetime,
    watchdog: WatchdogConfig,
) -> tuple[int, str | None, bool, bool, bool, datetime, datetime | None]:
    """Run OpenCode with root-session progress fuses and a durable completion handshake."""
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
    with transcript_path.open("w", encoding="utf-8", errors="replace") as transcript:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=transcript,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=os.name != "nt",
            creationflags=creationflags,
        )
        started_monotonic = time.monotonic()
        last_activity_monotonic = started_monotonic
        last_activity_at = started_at
        signature = evidence_activity_signature(transcript_path, state_dir)
        first_response_observed = transcript_path.stat().st_size > 0
        campaign_observed = False
        completion_observed = False
        try:
            found = latest_new_campaign(state_dir, expected_sha, started_at)
            campaign_observed = found is not None
            if found:
                completion_observed = campaign_completion(found[1], found[2]) is not None
        except BridgeError:
            campaign_observed = False
            completion_observed = False
        reason: str | None = None
        stalled_at: datetime | None = None

        while process.poll() is None:
            time.sleep(watchdog.poll_seconds)
            now_monotonic = time.monotonic()
            now = datetime.now(timezone.utc)
            current = evidence_activity_signature(transcript_path, state_dir)
            activity_changed = current != signature
            if activity_changed:
                signature = current
                last_activity_monotonic = now_monotonic
                last_activity_at = now
            if not first_response_observed and transcript_path.stat().st_size > 0:
                first_response_observed = True
            if activity_changed:
                try:
                    found = latest_new_campaign(state_dir, expected_sha, started_at)
                    if found:
                        campaign_observed = True
                        completion_observed = campaign_completion(found[1], found[2]) is not None
                except BridgeError:
                    # A writer can be between bytes of one append-only record. The
                    # final read remains fail-closed after the process exits.
                    pass

            if completion_observed:
                returncode = terminate_process_tree(process)
                return (
                    returncode,
                    None,
                    first_response_observed,
                    campaign_observed,
                    True,
                    last_activity_at,
                    None,
                )

            elapsed = now_monotonic - started_monotonic
            idle = now_monotonic - last_activity_monotonic
            if (
                not first_response_observed
                and elapsed >= watchdog.first_response_seconds
            ):
                reason = "FIRST_RESPONSE_TIMEOUT"
            elif not campaign_observed and elapsed >= watchdog.campaign_start_seconds:
                reason = "CAMPAIGN_START_TIMEOUT"
            elif idle >= watchdog.idle_seconds:
                reason = "NO_PROGRESS_TIMEOUT"
            if reason:
                stalled_at = now
                returncode = terminate_process_tree(process)
                return (
                    returncode,
                    reason,
                    first_response_observed,
                    campaign_observed,
                    False,
                    last_activity_at,
                    stalled_at,
                )

        now = datetime.now(timezone.utc)
        current = evidence_activity_signature(transcript_path, state_dir)
        if current != signature:
            last_activity_at = now
        first_response_observed = first_response_observed or transcript_path.stat().st_size > 0
        try:
            found = latest_new_campaign(state_dir, expected_sha, started_at)
            campaign_observed = campaign_observed or found is not None
            if found:
                completion_observed = campaign_completion(found[1], found[2]) is not None
        except BridgeError:
            campaign_observed = False
            completion_observed = False
        return (
            int(process.returncode or 0),
            None,
            first_response_observed,
            campaign_observed,
            completion_observed,
            last_activity_at,
            None,
        )


def invoke_opencode(
    root: Path,
    release_branch: str,
    expected_sha: str,
    scope: str,
    model: str,
    transcript_path: Path,
    state_dir: Path,
    started_at: datetime,
    watchdog: WatchdogConfig,
) -> OpenCodeExecution:
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

    message = (
        "GitHub EHA bridge request. Treat this as normal future-SIB selection. "
        f"Release stream: {release_branch}. Expected literal release HEAD and checkout SHA: "
        f"{expected_sha}. Scope: {scope}. The bridge already verified the remote release ref, "
        "checked out the exact SHA detached, and attached host-persistent canonical review/EHA state. "
        "For Step 1 run only `python scripts/eha_candidate_status.py` and use its bounded JSON as "
        "candidate_identity; do not rediscover refs or enumerate the persistence root. Start the "
        "durable campaign immediately after that bounded check and materialize only one Playbook Step "
        "at a time. "
        "The candidate checkout is read-only for this campaign: do not create, modify, rename, or "
        "delete any path inside it, including temporary or scratch files. If transient storage is "
        "unavoidable, use only the external CODESLEUTH_EHA_SCRATCH_DIR. Write analytical reports "
        "only through the bounded .codesleuth/reports route. Run the canonical "
        "eha-sib-acceptance Playbook only. After report persistence, write the durable "
        "campaign_completed handshake; do not wait for a final provider frame after that marker."
    )
    command = opencode_wrapper_command(root)
    command.extend(["run", "--command", "eha-test", "--format", "json"])
    command.extend(["--model", model])
    command.append(message)
    print(f"OPENCODE VERSION {version}", flush=True)
    print(f"EHA MODEL {model}", flush=True)
    print(f"EHA EXACT TARGET {expected_sha} FROM {release_branch}", flush=True)
    scratch_dir = prepare_scratch_dir(root, transcript_path.parent.parent)
    (
        returncode,
        reason,
        first_response_observed,
        campaign_observed,
        completion_observed,
        last_activity_at,
        stalled_at,
    ) = run_monitored_process(
        command,
        cwd=root,
        env=opencode_environment(
            root,
            scratch_dir,
            release_branch=release_branch,
            expected_sha=expected_sha,
        ),
        transcript_path=transcript_path,
        state_dir=state_dir,
        expected_sha=expected_sha,
        started_at=started_at,
        watchdog=watchdog,
    )
    return OpenCodeExecution(
        returncode=returncode,
        version=version,
        model=model,
        transport_outcome="ERROR" if reason else "PASS",
        reason=reason,
        first_response_observed=first_response_observed,
        campaign_observed=campaign_observed,
        completion_observed=completion_observed,
        started_at=started_at,
        last_activity_at=last_activity_at,
        stalled_at=stalled_at,
    )


def write_bridge_status(
    persist_root: Path,
    *,
    review_id: str | None,
    campaign_id: str | None,
    release_branch: str,
    target_sha: str,
    verdicts: dict[str, str],
    outcome: str,
    transport_outcome: str,
    reason: str | None,
    model: str,
    opencode_version: str,
    opencode_returncode: int | None,
    transcript_path: Path,
    first_response_observed: bool,
    campaign_observed: bool,
    durable_completion_observed: bool,
    started_at: datetime,
    last_activity_at: datetime,
    stalled_at: datetime | None,
) -> Path:
    runs = persist_root / "bridge-runs"
    runs.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = runs / f"{bridge_run_key()}.json"
    if path.exists():
        raise BridgeError(f"refusing to overwrite existing EHA bridge record: {path.name}")
    payload = {
        "schemaVersion": 3,
        "adapter": "github-opencode-eha",
        "repository": os.environ.get("GITHUB_REPOSITORY"),
        "githubRunId": os.environ.get("GITHUB_RUN_ID"),
        "githubRunAttempt": os.environ.get("GITHUB_RUN_ATTEMPT", "1"),
        "reviewId": review_id,
        "campaignId": campaign_id,
        "releaseBranch": release_branch,
        "targetSha": target_sha,
        "verdicts": verdicts,
        "outcome": outcome,
        "transportOutcome": transport_outcome,
        "reason": reason,
        "model": model,
        "opencodeVersion": opencode_version,
        "opencodeReturnCode": opencode_returncode,
        "firstResponseObserved": first_response_observed,
        "campaignObserved": campaign_observed,
        "durableCompletionObserved": durable_completion_observed,
        "startedAt": started_at.isoformat(),
        "lastActivityAt": last_activity_at.isoformat(),
        "stalledAt": stalled_at.isoformat() if stalled_at else None,
        "transcriptRecord": str(transcript_path.relative_to(persist_root)),
        "recordedAt": datetime.now(timezone.utc).isoformat(),
        "authority": "state/reviews/<reviewId>/eha.ndjson",
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", help="owner-authored GitHub issue comment command")
    parser.add_argument("--release-branch")
    parser.add_argument("--expected-sha")
    parser.add_argument("--scope", default=DEFAULT_SCOPE)
    parser.add_argument("--persist-root", required=True)
    parser.add_argument("--model", default=os.environ.get("CODESLEUTH_EHA_MODEL"))
    parser.add_argument(
        "--first-response-timeout-seconds",
        default=os.environ.get(
            "CODESLEUTH_EHA_FIRST_RESPONSE_TIMEOUT_SECONDS",
            DEFAULT_FIRST_RESPONSE_TIMEOUT_SECONDS,
        ),
    )
    parser.add_argument(
        "--campaign-start-timeout-seconds",
        default=os.environ.get(
            "CODESLEUTH_EHA_CAMPAIGN_START_TIMEOUT_SECONDS",
            DEFAULT_CAMPAIGN_START_TIMEOUT_SECONDS,
        ),
    )
    parser.add_argument(
        "--idle-timeout-seconds",
        default=os.environ.get(
            "CODESLEUTH_EHA_IDLE_TIMEOUT_SECONDS", DEFAULT_IDLE_TIMEOUT_SECONDS
        ),
    )
    parser.add_argument(
        "--watchdog-poll-seconds",
        default=os.environ.get(
            "CODESLEUTH_EHA_WATCHDOG_POLL_SECONDS", DEFAULT_WATCHDOG_POLL_SECONDS
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        model = validate_model(args.model)
        watchdog = WatchdogConfig(
            first_response_seconds=positive_seconds(
                args.first_response_timeout_seconds, "first-response timeout"
            ),
            campaign_start_seconds=positive_seconds(
                args.campaign_start_timeout_seconds, "campaign-start timeout"
            ),
            idle_seconds=positive_seconds(args.idle_timeout_seconds, "idle timeout"),
            poll_seconds=positive_seconds(
                args.watchdog_poll_seconds, "watchdog poll interval"
            ),
        )
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

        transcript_path = private_transcript_path(persist_root)
        started = datetime.now(timezone.utc)
        execution = invoke_opencode(
            root,
            release_branch,
            expected_sha,
            scope,
            model,
            transcript_path,
            state_dir,
            started,
            watchdog,
        )
        postcondition_error: str | None = None
        try:
            require_clean(root, "post-EHA exact-target check")
        except BridgeError as exc:
            postcondition_error = str(exc)

        found = latest_new_campaign(state_dir, expected_sha, started)
        review_id: str | None = None
        campaign_id: str | None = None
        completion: dict[str, Any] | None = None
        verdicts = {level: "PENDING" for level in LEVELS}
        if found:
            review_id, start, events = found
            verdicts = verdict_summary(start, events)
            campaign_id = str(start.get("campaignId"))
            completion = campaign_completion(start, events)
        completion_observed = execution.completion_observed or completion is not None
        if "FAIL" in verdicts.values():
            outcome = "FAIL"
        elif found and all(verdicts[level] == "PASS" for level in LEVELS):
            outcome = "PASS"
        elif found:
            outcome = "INCOMPLETE"
        else:
            outcome = "NOT_RUN"

        transport_outcome = execution.transport_outcome
        reason = execution.reason
        if postcondition_error:
            transport_outcome = "ERROR"
            reason = "POSTCONDITION_DIRTY"
        elif execution.returncode != 0 and not completion_observed:
            transport_outcome = "ERROR"
            reason = reason or "OPENCODE_NONZERO_EXIT"
        elif not found:
            transport_outcome = "ERROR"
            reason = "NO_DURABLE_CAMPAIGN"
        elif outcome == "PASS" and not completion_observed:
            transport_outcome = "ERROR"
            reason = "NO_DURABLE_COMPLETION"

        write_bridge_status(
            persist_root,
            review_id=review_id,
            campaign_id=campaign_id,
            release_branch=release_branch,
            target_sha=expected_sha,
            verdicts=verdicts,
            outcome=outcome,
            transport_outcome=transport_outcome,
            reason=reason,
            model=execution.model,
            opencode_version=execution.version,
            opencode_returncode=execution.returncode,
            transcript_path=transcript_path,
            first_response_observed=execution.first_response_observed,
            campaign_observed=execution.campaign_observed or found is not None,
            durable_completion_observed=completion_observed,
            started_at=execution.started_at,
            last_activity_at=execution.last_activity_at,
            stalled_at=execution.stalled_at,
        )
        print(
            "EHA BRIDGE RESULT "
            f"campaign={campaign_id} review={review_id} target={expected_sha} "
            f"SIB0={verdicts['SIB0']} SIB1={verdicts['SIB1']} SIB2={verdicts['SIB2']} "
            f"completion={completion_observed} outcome={outcome} "
            f"transport={transport_outcome} reason={reason}",
            flush=True,
        )
        print("PRIVATE EHA TRANSCRIPT AND BRIDGE STATUS RECORDED ON TRUSTED HOST", flush=True)

        if postcondition_error:
            print(f"EHA BRIDGE ERROR: {postcondition_error}", file=sys.stderr)
            return 5
        if transport_outcome != "PASS":
            print(
                "OpenCode transport did not complete cleanly: "
                f"reason={reason} returncode={execution.returncode}; "
                "any durable ledger is preserved without upgrading its verdicts",
                file=sys.stderr,
            )
            return 7 if execution.reason else 4
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
