#!/usr/bin/env python3
"""Share derived CodeSleuth Markdown reports through an isolated Git branch."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from codesleuth_project.paths import LOCAL_ROOT, update_reports_index
from codesleuth_report_metadata import is_report_filename, parse_report_metadata, verify_index_matches_files

REPORTS_BRANCH = "reports"
REPORTS_REMOTE = "origin"
REPORTS_PREFIX = f"{LOCAL_ROOT}/reports/"
MAX_SHARED_REPORT_BYTES = 2 * 1024 * 1024
_REPORT_RE = re.compile(
    r"^(?:\d{8}T\d{4}(?:\d{2})?Z|\d{4}-\d{2}-\d{2}T\d{4}Z)-"
    r"[a-z0-9][a-z0-9-]*\.md$"
)
_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("openai-key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("bearer-token", re.compile(r"(?i)\bauthorization\s*:\s*bearer\s+[A-Za-z0-9._~+/=-]{16,}")),
    ("credential-url", re.compile(r"https?://[^/\s:@]+:[^/\s@]{8,}@")),
)
_GENERIC_SECRET_RE = re.compile(
    r"""(?ix)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password)
    \b\s*[:=]\s*["']?([^\s"'`]{8,})"""
)
_REDACTED = {"redacted", "<redacted>", "[redacted]", "placeholder", "<placeholder>", "example", "changeme"}

SHARED_README = """# CodeSleuth shared analytical reports

This orphan branch is a cross-assistant exchange channel for **derived Markdown
reports only**.

- Shared content is limited to `.codesleuth/reports/**`.
- Structured review/EHA state under `.opencode/state/reviews/**` stays local and
  authoritative and is never copied here.
- Reports are navigation/handoff material, not evidence authority. Re-check
  exact current source and exact-head acceptance before merge/release claims.
- Publication fails closed on report-name collisions, suspicious secrets,
  branch divergence, or any non-report path in this branch.

CodeSleuth updates this branch without switching the application worktree, so
sharing reports does not change the application's current branch or HEAD.
"""


def _git(
    repo: Path,
    *args: str,
    check: bool = True,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        encoding="utf-8",
        errors="strict",
        input=input_text,
        capture_output=True,
        check=check,
        env=merged,
    )


def _root(path: Path) -> Path:
    proc = _git(path.expanduser().resolve(), "rev-parse", "--show-toplevel")
    return Path(proc.stdout.strip()).resolve()


def _ref(repo: Path, ref: str) -> str | None:
    proc = _git(repo, "rev-parse", "--verify", ref, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else None


def _remote_exists(repo: Path, remote: str) -> bool:
    proc = _git(repo, "remote", "get-url", remote, check=False)
    return proc.returncode == 0 and bool(proc.stdout.strip())


def _fetch(repo: Path, remote: str, branch: str) -> str | None:
    if not _remote_exists(repo, remote):
        return None
    remote_ref = f"refs/remotes/{remote}/{branch}"
    proc = _git(
        repo,
        "fetch",
        "--no-tags",
        remote,
        f"+refs/heads/{branch}:{remote_ref}",
        check=False,
    )
    if proc.returncode == 0:
        return _ref(repo, remote_ref)
    probe = _git(repo, "ls-remote", "--exit-code", "--heads", remote, branch, check=False)
    if probe.returncode == 2:
        return None
    raise RuntimeError(f"cannot fetch {remote}/{branch}: {(proc.stderr or proc.stdout).strip()}")


def _ancestor(repo: Path, older: str, newer: str) -> bool:
    return _git(repo, "merge-base", "--is-ancestor", older, newer, check=False).returncode == 0


def _base(repo: Path, remote_tip: str | None, branch: str) -> str | None:
    local = _ref(repo, f"refs/heads/{branch}")
    if local is None:
        return remote_tip
    if remote_tip is None or local == remote_tip:
        return local
    if _ancestor(repo, local, remote_tip):
        return remote_tip
    if _ancestor(repo, remote_tip, local):
        return local
    raise RuntimeError(f"reports branch diverged: local {local} vs remote {remote_tip}")


def _assert_reports_only(repo: Path, ref: str) -> None:
    paths = _git(repo, "ls-tree", "-r", "--name-only", ref).stdout.splitlines()
    bad = [p for p in paths if not p.startswith(REPORTS_PREFIX)]
    if bad:
        raise RuntimeError("reports branch contains non-report paths: " + ", ".join(bad[:5]))
    physical = {Path(path).name for path in paths if is_report_filename(Path(path).name)}
    index_path = f"{REPORTS_PREFIX}INDEX.md"
    if index_path not in paths:
        raise RuntimeError("reports branch INDEX.md missing")
    listed: set[str] = set()
    for line in _git(repo, "show", f"{ref}:{index_path}").stdout.splitlines():
        match = re.match(r"^- `([^`]+)`", line.strip())
        if match and is_report_filename(match.group(1)):
            listed.add(match.group(1))
    if listed != physical:
        raise RuntimeError("reports branch INDEX does not match timestamped files")


def _report(repo: Path, value: str | Path) -> Path:
    path = Path(value)
    path = (path if path.is_absolute() else repo / path).resolve()
    reports = (repo / LOCAL_ROOT / "reports").resolve()
    if path.parent != reports or not _REPORT_RE.match(path.name):
        raise ValueError(f"report must be one timestamped Markdown file under {REPORTS_PREFIX}")
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def _scan(text: str) -> None:
    size = len(text.encode("utf-8"))
    if size > MAX_SHARED_REPORT_BYTES:
        raise RuntimeError(f"report exceeds {MAX_SHARED_REPORT_BYTES} byte shared limit")
    for label, pattern in _SECRET_PATTERNS:
        match = pattern.search(text)
        if match:
            line = text.count("\n", 0, match.start()) + 1
            raise RuntimeError(f"secret scanner blocked {label} candidate on line {line}")
    for match in _GENERIC_SECRET_RE.finditer(text):
        value = match.group(2).strip().rstrip(",;").lower()
        if value in _REDACTED or set(value) <= {"*", "x", "-"}:
            continue
        line = text.count("\n", 0, match.start()) + 1
        raise RuntimeError(f"secret scanner blocked credential assignment on line {line}")


def _identity_env() -> dict[str, str]:
    return {
        "GIT_AUTHOR_NAME": os.environ.get("GIT_AUTHOR_NAME", "CodeSleuth Reports"),
        "GIT_AUTHOR_EMAIL": os.environ.get("GIT_AUTHOR_EMAIL", "codesleuth-reports@localhost.invalid"),
        "GIT_COMMITTER_NAME": os.environ.get("GIT_COMMITTER_NAME", "CodeSleuth Reports"),
        "GIT_COMMITTER_EMAIL": os.environ.get("GIT_COMMITTER_EMAIL", "codesleuth-reports@localhost.invalid"),
    }


def _empty_root(repo: Path) -> str:
    tree = _git(repo, "mktree", input_text="").stdout.strip()
    return _git(repo, "commit-tree", tree, "-m", "reports: initialize shared channel", env=_identity_env()).stdout.strip()


def _worktree_commit(repo: Path, base: str | None, report: Path) -> str:
    if base is not None:
        _assert_reports_only(repo, base)
    seed = base or _empty_root(repo)
    temp = Path(tempfile.mkdtemp(prefix="codesleuth-reports-"))
    added = False
    try:
        _git(repo, "worktree", "add", "--detach", str(temp), seed)
        added = True
        shared = temp / LOCAL_ROOT / "reports"
        shared.mkdir(parents=True, exist_ok=True)
        target = shared / report.name
        if target.is_file() and target.read_text(encoding="utf-8") != report.read_text(encoding="utf-8"):
            raise RuntimeError(f"published report name collision: {report.name}")
        shutil.copyfile(report, target)
        (shared / "README.md").write_text(SHARED_README, encoding="utf-8")
        app_head = _ref(repo, "HEAD")
        update_reports_index(temp, git_repo=repo, current_head=app_head)
        verify_index_matches_files(shared)
        _git(
            temp,
            "add",
            "-f",
            "--",
            f"{REPORTS_PREFIX}{report.name}",
            f"{REPORTS_PREFIX}README.md",
            f"{REPORTS_PREFIX}INDEX.md",
        )
        tracked = _git(temp, "ls-files").stdout.splitlines()
        bad = [p for p in tracked if not p.startswith(REPORTS_PREFIX)]
        if bad:
            raise RuntimeError("reports branch staging escaped allowlist: " + ", ".join(bad[:5]))
        _git(temp, "commit", "-m", f"reports: publish {report.name}", env=_identity_env())
        return _ref(temp, "HEAD") or ""
    finally:
        if added:
            _git(repo, "worktree", "remove", "--force", str(temp), check=False)
        shutil.rmtree(temp, ignore_errors=True)


def sync_shared_reports(
    repo: Path,
    *,
    remote: str = REPORTS_REMOTE,
    branch: str = REPORTS_BRANCH,
) -> dict[str, Any]:
    repo = _root(repo)
    tip = _fetch(repo, remote, branch)
    if tip is None:
        return {
            "branch": branch,
            "remote": remote if _remote_exists(repo, remote) else None,
            "remoteCommit": None,
            "imported": 0,
            "status": "no-shared-branch",
        }
    _assert_reports_only(repo, tip)
    shared = repo / LOCAL_ROOT / "reports"
    shared.mkdir(parents=True, exist_ok=True)
    imported = 0
    paths = _git(repo, "ls-tree", "-r", "--name-only", tip, "--", REPORTS_PREFIX).stdout.splitlines()
    for rel in paths:
        name = Path(rel).name
        if not _REPORT_RE.match(name):
            continue
        text = _git(repo, "show", f"{tip}:{rel}").stdout
        _scan(text)
        local = shared / name
        if local.is_file() and local.read_text(encoding="utf-8") != text:
            raise RuntimeError(f"local/shared report collision: {name}")
        if not local.exists():
            local.write_text(text, encoding="utf-8")
            imported += 1
    app_head = _ref(repo, "HEAD")
    update_reports_index(repo, git_repo=repo, current_head=app_head)
    verify_index_matches_files(shared)
    return {"branch": branch, "remote": remote, "remoteCommit": tip, "imported": imported, "status": "synced"}


def publish_shared_report(
    repo: Path,
    report: str | Path,
    *,
    remote: str = REPORTS_REMOTE,
    branch: str = REPORTS_BRANCH,
    retries: int = 3,
) -> dict[str, Any]:
    repo = _root(repo)
    report_path = _report(repo, report)
    text = report_path.read_text(encoding="utf-8")
    _scan(text)
    parse_report_metadata(text)
    app_head = _ref(repo, "HEAD")
    has_remote = _remote_exists(repo, remote)
    last_error = ""
    for attempt in range(1, retries + 1):
        remote_tip = _fetch(repo, remote, branch) if has_remote else None
        base = _base(repo, remote_tip, branch)
        commit = _worktree_commit(repo, base, report_path)
        if has_remote:
            push = _git(repo, "push", "--porcelain", remote, f"{commit}:refs/heads/{branch}", check=False)
            if push.returncode != 0:
                last_error = (push.stderr or push.stdout).strip()
                if attempt < retries:
                    continue
                raise RuntimeError(f"cannot publish {remote}/{branch}: {last_error}")
        old_local = _ref(repo, f"refs/heads/{branch}")
        args = ["update-ref", f"refs/heads/{branch}", commit]
        if old_local:
            args.append(old_local)
        _git(repo, *args)
        if has_remote:
            sync_shared_reports(repo, remote=remote, branch=branch)
        if _ref(repo, "HEAD") != app_head:
            raise RuntimeError("application HEAD changed during report publication")
        return {
            "branch": branch,
            "remote": remote if has_remote else None,
            "commit": commit,
            "publishedRemote": has_remote,
            "report": report_path.relative_to(repo).as_posix(),
            "applicationHead": app_head,
        }
    raise RuntimeError(last_error or "report publication failed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync/publish CodeSleuth shared Markdown reports.")
    parser.add_argument("--repo", default=".")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("sync")
    publish = sub.add_parser("publish")
    publish.add_argument("report")
    args = parser.parse_args()
    result = sync_shared_reports(Path(args.repo)) if args.action == "sync" else publish_shared_report(Path(args.repo), args.report)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
