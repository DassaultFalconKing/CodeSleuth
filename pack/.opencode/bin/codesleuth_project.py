#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOCAL_ROOT = ".codesleuth"
REPORTS_DIR = ".codesleuth/reports"
DEFAULT_DEPENDENCY_PATH = "tools/codesleuth"
IGNORE_BEGIN = "# BEGIN CodeSleuth local-only data"
IGNORE_END = "# END CodeSleuth local-only data"
IGNORE_LINES = (
    ".codesleuth/*",
    "!.codesleuth/reports/",
    ".codesleuth/reports/*",
    "!.codesleuth/reports/README.md",
    ".opencode/state/",
    ".opencode/cache/",
    ".opencode/logs/",
    ".opencode/sessions/",
    ".opencode/snapshots/",
    ".opencode/node_modules/",
    ".opencode/**/__pycache__/",
    ".opencode/**/*.pyc",
)
AGENTS_BEGIN = "<!-- BEGIN CodeSleuth reports -->"
AGENTS_END = "<!-- END CodeSleuth reports -->"
AGENTS_POINTER = textwrap.dedent(
    f"""\
    {AGENTS_BEGIN}
    Analytical reports for this worktree live in `.codesleuth/reports/` (see `INDEX.md`). Format: `.opencode/CODESLEUTH-REPORTS.md`. OpenCode `build` writes them. They are local-only by default because reports may contain source excerpts or credentials; reuse them in this worktree, and only publish sanitized reports or guidance intentionally when cross-clone reuse is desired.
    {AGENTS_END}
    """
)
REPORTS_README = """# CodeSleuth analytical reports

This folder is the durable, assistant-readable report store for this worktree.

- **Writer:** OpenCode's primary `build` agent (via `/repo-review`, `/repo-docs`, `/repo-report`).
- **Readers:** later CodeSleuth/OpenCode sessions, Cursor, Claude, Codex, Copilot, and humans working in this worktree by default.
- **Do not** invent a second CodeSleuth supervisor prompt. Reports are ordinary markdown files.

## Files

| Path | Git | Purpose |
|---|---|---|
| `README.md` | may be tracked | convention that can be intentionally shared |
| `INDEX.md` | locally excluded by default | catalog of reports in this worktree |
| `YYYY-MM-DDTHHMMZ-<slug>.md` | locally excluded by default | one analysis report |

Report bodies are excluded from Git by default because they may contain secrets, source excerpts, or credentials. CodeSleuth uses the repository-local Git exclude file (`.git/info/exclude`) and does not rewrite the project's tracked `.gitignore` for this purpose. Inspect and sanitize material before intentionally adding or publishing it. Fresh clones only receive reports or guidance that a maintainer deliberately commits.

## Required report sections

1. Title, UTC date, target (`HEAD`, dirty, scope)
2. Summary
3. Findings (severity, `path:line-line`, evidence, recommendation)
4. Paths inspected
5. Checks/tests actually run
6. Recommendations
7. Limitations / not reviewed
8. Link to `.opencode/state/reviews/<id>/` when a durable review exists

See `.opencode/CODESLEUTH-REPORTS.md` for the full template.
"""
REPORTS_INDEX_HEADER = """# CodeSleuth report index

Newest first. Each bullet: `file` — UTC date — title — scope — HEAD.
"""
REPORTS_INDEX_PLACEHOLDER = "- _(no reports yet)_"
REPORTS_INDEX = f"{REPORTS_INDEX_HEADER.rstrip()}\n\n{REPORTS_INDEX_PLACEHOLDER}\n"
_REPORT_INDEX_LINE_RE = re.compile(r"^- `([^`]+)`(?:\s*—\s*(.*))?$")
_REPORT_TS_RE = re.compile(
    r"^(?:"
    r"(?P<y1>\d{4})(?P<m1>\d{2})(?P<d1>\d{2})T(?P<h1>\d{2})(?P<n1>\d{2})(?P<s1>\d{2})?Z"
    r"|"
    r"(?P<y2>\d{4})-(?P<m2>\d{2})-(?P<d2>\d{2})T(?P<h2>\d{2})(?P<n2>\d{2})Z"
    r")-(?P<slug>.+)$"
)
SKIP_SNAPSHOT_DIRS = {
    ".cache",
    "cache",
    "logs",
    "sessions",
    "snapshots",
    "state",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
}


def run_git(repo: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run ``git`` in *repo* with *args* and return the completed process."""
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=check,
    )


def utc_stamp() -> str:
    """Return a compact UTC timestamp string for filenames."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest of *path*."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_rel(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"dependency path must stay inside the target repository: {value}")
    return path


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _path_state(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    if path.is_file():
        return "file"
    if path.is_dir():
        return "directory"
    if not path.exists():
        return "absent"
    return "other"


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _snapshot_candidates(repo: Path) -> list[Path]:
    candidates: list[Path] = []
    for root_name in (".gitignore", ".gitmodules"):
        root_file = repo / root_name
        if root_file.is_file():
            candidates.append(root_file)
    opencode = repo / ".opencode"
    if not opencode.is_dir():
        return candidates
    for path in sorted(opencode.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(opencode)
        if any(part in SKIP_SNAPSHOT_DIRS for part in rel.parts):
            continue
        if path.suffix in {".pyc", ".log", ".tmp"}:
            continue
        candidates.append(path)
    return candidates


def _git_info_exclude(repo: Path) -> Path:
    """Return this worktree's repository-local Git exclude file."""
    proc = run_git(repo, ["rev-parse", "--git-path", "info/exclude"])
    raw = proc.stdout.strip()
    if not raw:
        raise RuntimeError("git rev-parse --git-path info/exclude returned an empty path")
    path = Path(raw)
    if not path.is_absolute():
        path = repo / path
    return path.resolve()


def _replace_ignore_block(path: Path, lines: list[str], *, label: str) -> Path:
    """Replace the CodeSleuth ignore block in one Git ignore/exclude file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    original = path.read_text(encoding="utf-8") if path.is_file() else ""
    before, marker, tail = original.partition(IGNORE_BEGIN)
    if marker:
        _, end_marker, after = tail.partition(IGNORE_END)
        if not end_marker:
            raise RuntimeError(f"malformed CodeSleuth block in {label}")
        original = before.rstrip("\n") + ("\n" if before else "") + after.lstrip("\n")
    block = "\n".join([IGNORE_BEGIN, *lines, IGNORE_END])
    body = original.rstrip("\n")
    new_content = f"{body}\n\n{block}\n" if body else f"{block}\n"
    _atomic_write_text(path, new_content)
    return path


def ensure_local_gitignore(repo: Path, *, preserve_archive_only: bool = False) -> Path:
    """Ensure CodeSleuth local-only ignores without modifying tracked .gitignore.

    The historical function name is kept for compatibility with installer and
    lifecycle callers. New installations write only to ``.git/info/exclude``
    (or Git's worktree-aware equivalent from ``git rev-parse --git-path``).
    """
    repo = git_root(repo)
    lines = [".codesleuth/"] if preserve_archive_only else list(IGNORE_LINES)
    return _replace_ignore_block(_git_info_exclude(repo), lines, label="Git info/exclude")



def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def report_timestamp_key(name: str) -> tuple[int, ...]:
    """Return a sortable timestamp key for a report filename stem.

    Args:
        name: Report file name or stem (with or without ``.md``).

    Returns:
        A tuple suitable for newest-first ordering. Unparseable names sort last.
    """
    stem = name[:-3] if name.endswith(".md") else name
    match = _REPORT_TS_RE.match(stem)
    if not match:
        return (0, 0, 0, 0, 0, 0)
    g = match.groupdict()
    if g.get("y1"):
        return (
            int(g["y1"]),
            int(g["m1"]),
            int(g["d1"]),
            int(g["h1"]),
            int(g["n1"]),
            int(g["s1"] or 0),
        )
    return (
        int(g["y2"]),
        int(g["m2"]),
        int(g["d2"]),
        int(g["h2"]),
        int(g["n2"]),
        0,
    )


def _report_display_date(name: str) -> str:
    stem = name[:-3] if name.endswith(".md") else name
    match = _REPORT_TS_RE.match(stem)
    if not match:
        return ""
    g = match.groupdict()
    if g.get("y1"):
        return f"{g['y1']}-{g['m1']}-{g['d1']}T{g['h1']}:{g['n1']}Z"
    return f"{g['y2']}-{g['m2']}-{g['d2']}T{g['h2']}:{g['n2']}Z"


def _report_basename(value: str | Path) -> str:
    return Path(value).name


def _title_from_report(path: Path) -> str:
    if not path.is_file():
        return Path(path).stem
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip() or path.stem
    except OSError:
        pass
    return path.stem


def _format_index_line(
    name: str,
    *,
    date: str = "",
    title: str = "",
    scope: str = "",
    head: str = "",
) -> str:
    return " — ".join(
        [
            f"- `{name}`",
            date or "",
            title or "",
            scope or "",
            head or "",
        ]
    )


def _parse_index_entries(text: str) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        match = _REPORT_INDEX_LINE_RE.match(line.strip())
        if not match:
            continue
        name = match.group(1)
        rest = (match.group(2) or "").strip()
        fields = [p.strip() for p in rest.split("—")] if rest else []
        while len(fields) < 4:
            fields.append("")
        date, title, scope, head = fields[:4]
        entries[name] = {
            "date": date,
            "title": title,
            "scope": scope,
            "head": head,
        }
    return entries


def _iter_report_files(reports: Path) -> list[Path]:
    if not reports.is_dir():
        return []
    files: list[Path] = []
    for path in reports.iterdir():
        if not path.is_file() or path.suffix.lower() != ".md":
            continue
        if path.name in {"README.md", "INDEX.md"}:
            continue
        files.append(path)
    return files


def _write_reports_index(index_path: Path, entries: dict[str, dict[str, str]]) -> None:
    names = sorted(entries.keys(), key=report_timestamp_key, reverse=True)
    lines = [REPORTS_INDEX_HEADER.rstrip(), ""]
    if not names:
        lines.append(REPORTS_INDEX_PLACEHOLDER)
    else:
        for name in names:
            meta = entries[name]
            lines.append(
                _format_index_line(
                    name,
                    date=meta.get("date", ""),
                    title=meta.get("title", ""),
                    scope=meta.get("scope", ""),
                    head=meta.get("head", ""),
                )
            )
    lines.append("")
    _atomic_write_text(index_path, "\n".join(lines))


def update_reports_index(
    repo: Path,
    *,
    add: str | Path | None = None,
    remove: str | Path | None = None,
    title: str | None = None,
    date: str | None = None,
    scope: str | None = None,
    head: str | None = None,
) -> Path:
    """Atomically refresh ``.codesleuth/reports/INDEX.md``.

    Args:
        repo: Target repository root.
        add: Report path or basename to upsert.
        remove: Report path or basename to drop from the index.
        title: Optional report title override.
        date: Optional UTC date string override.
        scope: Optional scope label (for example ``HEAD``).
        head: Optional HEAD / commit label.

    Returns:
        Path to the written ``INDEX.md``.

    Notes:
        With neither ``add`` nor ``remove``, syncs the index to files on disk
        (newest first, one line per report).
    """
    reports = repo / LOCAL_ROOT / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    index_path = reports / "INDEX.md"
    existing_text = index_path.read_text(encoding="utf-8") if index_path.is_file() else REPORTS_INDEX
    entries = _parse_index_entries(existing_text)

    if remove is not None:
        entries.pop(_report_basename(remove), None)

    if add is not None:
        add_path = Path(add)
        if add_path.is_file():
            file_path = add_path
            name = add_path.name
        else:
            name = _report_basename(add)
            file_path = reports / name
        meta = dict(entries.get(name, {}))
        meta["title"] = title if title is not None else (meta.get("title") or _title_from_report(file_path))
        meta["date"] = date if date is not None else (meta.get("date") or _report_display_date(name))
        if scope is not None:
            meta["scope"] = scope
        else:
            meta.setdefault("scope", "")
        if head is not None:
            meta["head"] = head
        else:
            meta.setdefault("head", "")
        entries[name] = meta

    if add is None and remove is None:
        on_disk = {_report_basename(p): p for p in _iter_report_files(reports)}
        for name in list(entries):
            if name not in on_disk:
                entries.pop(name, None)
        for name, path in on_disk.items():
            meta = dict(entries.get(name, {}))
            meta["title"] = meta.get("title") or _title_from_report(path)
            meta["date"] = meta.get("date") or _report_display_date(name)
            meta.setdefault("scope", "")
            meta.setdefault("head", "")
            entries[name] = meta

    _write_reports_index(index_path, entries)
    return index_path


def ensure_reports_workspace(repo: Path) -> Path:
    """Ensure ``.codesleuth/reports`` exists with README and INDEX.

    Args:
        repo: Target repository root.

    Returns:
        Path to the reports directory.
    """
    reports = repo / LOCAL_ROOT / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    readme = reports / "README.md"
    if not readme.is_file():
        readme.write_text(REPORTS_README, encoding="utf-8")
    update_reports_index(repo)
    return reports


def validate_agents_pointer(repo: Path) -> None:
    """Validate the managed CodeSleuth reports block in ``AGENTS.md``.

    Args:
        repo: Target repository root.

    Raises:
        RuntimeError: If BEGIN/END markers are mismatched or unpaired.
    """
    path = repo / "AGENTS.md"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    begins = text.count(AGENTS_BEGIN)
    ends = text.count(AGENTS_END)
    if begins == 0 and ends == 0:
        return
    if begins != ends:
        if begins > ends:
            raise RuntimeError("BEGIN without END in AGENTS.md CodeSleuth reports block")
        raise RuntimeError("malformed CodeSleuth reports block in AGENTS.md")
    pos = 0
    for _ in range(begins):
        b = text.find(AGENTS_BEGIN, pos)
        if b < 0:
            raise RuntimeError("malformed CodeSleuth reports block in AGENTS.md")
        e = text.find(AGENTS_END, b + len(AGENTS_BEGIN))
        if e < 0:
            raise RuntimeError("BEGIN without END in AGENTS.md CodeSleuth reports block")
        next_b = text.find(AGENTS_BEGIN, b + len(AGENTS_BEGIN))
        if next_b != -1 and next_b < e:
            raise RuntimeError("BEGIN without END in AGENTS.md CodeSleuth reports block")
        pos = e + len(AGENTS_END)


def ensure_agents_reports_pointer(repo: Path) -> Path:
    """Ensure ``AGENTS.md`` ends with exactly one CodeSleuth reports pointer.

    Args:
        repo: Target repository root.

    Returns:
        Path to ``AGENTS.md``.

    Raises:
        RuntimeError: If a malformed block is present (refuses to overwrite
            user content).
    """
    path = repo / "AGENTS.md"
    try:
        validate_agents_pointer(repo)
    except RuntimeError as exc:
        raise RuntimeError(
            f"refusing to overwrite user content: malformed CodeSleuth reports block ({exc})"
        ) from exc

    original = path.read_text(encoding="utf-8") if path.is_file() else ""
    if (
        original.count(AGENTS_BEGIN) == 1
        and original.count(AGENTS_END) == 1
        and original.rstrip("\n").endswith(AGENTS_POINTER.rstrip("\n"))
    ):
        return path

    cleaned = original
    while True:
        before, marker, tail = cleaned.partition(AGENTS_BEGIN)
        if not marker:
            break
        _, end_marker, after = tail.partition(AGENTS_END)
        if not end_marker:
            raise RuntimeError(
                "refusing to overwrite user content: malformed CodeSleuth reports block"
            )
        cleaned = before.rstrip("\n") + ("\n" if before else "") + after.lstrip("\n")
    body = cleaned.rstrip("\n")
    new_content = (
        textwrap.dedent(
            f"""\
{body}

{AGENTS_POINTER.rstrip()}
"""
        )
        if body
        else AGENTS_POINTER
    )
    path.write_text(new_content, encoding="utf-8")
    return path


def remove_agents_reports_pointer(repo: Path) -> None:
    """Remove the managed CodeSleuth reports pointer from ``AGENTS.md``.

    Args:
        repo: Target repository root.

    Notes:
        Missing files or absent markers are soft no-ops.
    """
    path = repo / "AGENTS.md"
    if not path.exists():
        return
    original = path.read_text(encoding="utf-8")
    before, marker, tail = original.partition(AGENTS_BEGIN)
    if not marker:
        return
    _, end_marker, after = tail.partition(AGENTS_END)
    if not end_marker:
        return
    body = (before.rstrip("\n") + "\n" + after.lstrip("\n")).strip("\n")
    if body:
        path.write_text(body + "\n", encoding="utf-8")
    else:
        path.unlink()


def _remove_ignore_block(path: Path, *, label: str) -> None:
    if not path.exists():
        return
    original = path.read_text(encoding="utf-8")
    before, marker, tail = original.partition(IGNORE_BEGIN)
    if not marker:
        return
    _, end_marker, after = tail.partition(IGNORE_END)
    if not end_marker:
        raise RuntimeError(f"malformed CodeSleuth block in {label}")
    body = (before.rstrip("\n") + "\n" + after.lstrip("\n")).strip("\n")
    if body:
        _atomic_write_text(path, body + "\n")
    else:
        path.unlink()


def remove_local_gitignore_block(repo: Path) -> None:
    """Remove current local excludes and any legacy root .gitignore block."""
    repo = git_root(repo)
    _remove_ignore_block(_git_info_exclude(repo), label="Git info/exclude")
    # Backward compatibility: versions before this hardening release wrote the
    # same managed block into the user's root .gitignore. Uninstall/update may
    # clean that old block, but new installs never create it.
    _remove_ignore_block(repo / ".gitignore", label=".gitignore")


def create_preinstall_snapshot(repo: Path) -> dict[str, Any]:
    """Snapshot pre-existing OpenCode/project state before install."""
    repo = repo.resolve()
    root = repo / LOCAL_ROOT
    pointer = root / "preinstall.json"
    if pointer.is_file():
        data = json.loads(pointer.read_text(encoding="utf-8"))
        manifest_path = repo / data["manifest"]
        if manifest_path.is_file():
            return data

    stamp = utc_stamp()
    snapshot = root / "backups" / "pre-install" / stamp
    files_root = snapshot / "files"
    entries: list[dict[str, str]] = []
    for source in _snapshot_candidates(repo):
        rel = source.relative_to(repo)
        target = files_root / rel
        _copy_file(source, target)
        entries.append({"path": rel.as_posix(), "sha256": sha256_file(source)})

    manifest = {
        "schemaVersion": 1,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "opencodeExisted": (repo / ".opencode").exists(),
        "gitignoreExisted": (repo / ".gitignore").exists(),
        "gitmodulesExisted": (repo / ".gitmodules").exists(),
        "baselineKind": "pre-0.3-upgrade" if (repo / ".opencode" / "review-pack.json").is_file() else "pre-install",
        "files": entries,
    }
    manifest_path = snapshot / "manifest.json"
    _write_json(manifest_path, manifest)
    pointer_data = {
        "schemaVersion": 1,
        "manifest": manifest_path.relative_to(repo).as_posix(),
    }
    _write_json(pointer, pointer_data)
    ensure_local_gitignore(repo)
    return pointer_data


def _load_snapshot(repo: Path) -> tuple[dict[str, Any] | None, Path | None]:
    pointer = repo / LOCAL_ROOT / "preinstall.json"
    if not pointer.is_file():
        return None, None
    pointer_data = json.loads(pointer.read_text(encoding="utf-8"))
    manifest_path = repo / str(pointer_data.get("manifest", ""))
    if not manifest_path.is_file():
        return None, None
    return json.loads(manifest_path.read_text(encoding="utf-8")), manifest_path.parent


def git_root(path: Path) -> Path:
    """Return the Git repository root containing *path*."""
    resolved = path.expanduser().resolve()
    result = run_git(resolved, ["rev-parse", "--show-toplevel"])
    return Path(result.stdout.strip()).resolve()


def record_postinstall_snapshot(repo: Path) -> None:
    """Record the installed side of the restore three-way comparison."""
    repo = git_root(repo)
    manifest, snapshot_dir = _load_snapshot(repo)
    if not manifest or not snapshot_dir:
        return
    changed = False
    for entry in manifest.get("files", []):
        rel = Path(entry["path"])
        if rel.as_posix() in {".gitignore", ".gitmodules"}:
            continue
        current = repo / rel
        installed_state = _path_state(current)
        installed_hash = sha256_file(current) if installed_state == "file" else None
        if "installedSha256" not in entry:
            entry["installedSha256"] = installed_hash
            entry["installedState"] = installed_state
            changed = True
    if changed:
        _write_json(snapshot_dir / "manifest.json", manifest)


def dependency_status(repo: Path, dependency_path: str = DEFAULT_DEPENDENCY_PATH) -> dict[str, Any]:
    """Return binding status for the optional CodeSleuth git dependency."""
    repo = git_root(repo)
    rel = _safe_rel(dependency_path).as_posix()
    staged = run_git(repo, ["ls-files", "--stage", "--", rel], check=False)
    mode = None
    commit = None
    if staged.returncode == 0 and staged.stdout.strip():
        fields = staged.stdout.split()
        if len(fields) >= 2:
            mode, commit = fields[0], fields[1]
    worktree = repo / rel
    return {
        "path": rel,
        "bound": mode == "160000",
        "commit": commit if mode == "160000" else None,
        "worktreePresent": worktree.exists(),
    }


def lifecycle_state(repo: Path, dependency_path: str = DEFAULT_DEPENDENCY_PATH) -> str:
    """Classify the repository lifecycle state for install/update/uninstall."""
    repo = git_root(repo)
    runtime = (repo / ".opencode" / "review-pack.json").is_file()
    bound = dependency_status(repo, dependency_path)["bound"]
    if runtime and bound:
        return "bound-active"
    if bound:
        return "dependency-only"
    if runtime:
        return "unbound-active"
    return "unbound-inactive"


def _guard_submodule_head(repo: Path, status: dict[str, Any], *, requested_commit: str | None = None) -> None:
    worktree = repo / status["path"]
    if not worktree.exists():
        return
    dirty = run_git(worktree, ["status", "--porcelain"], check=False)
    if dirty.returncode != 0:
        raise RuntimeError(f"cannot inspect CodeSleuth submodule: {status['path']}")
    if dirty.stdout.strip():
        raise RuntimeError(f"refusing to discard dirty CodeSleuth submodule: {status['path']}")
    head = run_git(worktree, ["rev-parse", "HEAD"], check=False)
    if head.returncode != 0:
        raise RuntimeError(f"cannot resolve CodeSleuth submodule HEAD: {status['path']}")
    actual = head.stdout.strip()
    recorded = status.get("commit")
    if actual != recorded and actual != requested_commit:
        raise RuntimeError(
            f"refusing to discard local CodeSleuth commit {actual}; "
            f"superproject records {recorded}. Preserve/push the commit or intentionally advance the pin first"
        )


def _source_from_checkout(source_root: Path | None, metadata: dict[str, Any] | None) -> tuple[str, str]:
    remote = None
    commit = None
    if source_root is not None and source_root.exists():
        remote_result = run_git(source_root, ["remote", "get-url", "origin"], check=False)
        if remote_result.returncode == 0:
            remote = remote_result.stdout.strip() or None
        commit_result = run_git(source_root, ["rev-parse", "HEAD"], check=False)
        if commit_result.returncode == 0:
            commit = commit_result.stdout.strip() or None
    if metadata:
        remote = remote or metadata.get("remote")
        commit = commit or metadata.get("commit")
    if not remote or not commit:
        raise RuntimeError("CodeSleuth dependency binding requires an exact source remote and commit")
    return str(remote), str(commit)


def bind_dependency(
    repo: Path,
    *,
    source_root: Path | None = None,
    source_metadata: dict[str, Any] | None = None,
    dependency_path: str = DEFAULT_DEPENDENCY_PATH,
) -> dict[str, Any]:
    """Bind CodeSleuth as a pinned Git submodule dependency."""
    repo = repo.resolve()
    rel = _safe_rel(dependency_path).as_posix()
    current = dependency_status(repo, rel)
    remote, commit = _source_from_checkout(source_root, source_metadata)

    if current["bound"]:
        worktree = repo / rel
        if worktree.exists():
            _guard_submodule_head(repo, current, requested_commit=commit)
            run_git(worktree, ["fetch", "origin", commit], check=False)
            run_git(worktree, ["checkout", "--detach", commit])
            run_git(repo, ["add", "--", rel])
        return {**dependency_status(repo, rel), "remote": remote, "requestedCommit": commit}

    ignored = run_git(repo, ["check-ignore", "-q", "--", rel], check=False)
    if ignored.returncode == 0:
        raise RuntimeError(
            f"dependency path {rel} is ignored by the target repository; CodeSleuth will not override project ignore policy"
        )
    target = repo / rel
    if target.exists() and any(target.iterdir() if target.is_dir() else [target]):
        raise RuntimeError(f"dependency path already exists and is not a CodeSleuth gitlink: {rel}")
    target.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "git",
            "-c",
            "protocol.file.allow=always",
            "-C",
            str(repo),
            "submodule",
            "add",
            "--name",
            "codesleuth",
            "--",
            remote,
            rel,
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    worktree = repo / rel
    run_git(worktree, ["fetch", "origin", commit], check=False)
    run_git(worktree, ["checkout", "--detach", commit])
    run_git(repo, ["add", ".gitmodules", rel])
    return {**dependency_status(repo, rel), "remote": remote, "requestedCommit": commit}


def archive_traces(repo: Path) -> Path:
    """Archive managed CodeSleuth traces under ``.codesleuth/archive``."""
    stamp = utc_stamp()
    archive = repo / LOCAL_ROOT / "archive" / stamp
    candidates = [
        repo / ".opencode" / "review-pack.json",
        repo / ".opencode" / "review-pack-user.json",
        repo / ".opencode" / "opencode.json",
        repo / ".opencode" / "profiles",
        repo / ".opencode" / "state" / "reviews",
        repo / ".opencode" / "state" / "tui",
        repo / LOCAL_ROOT / "reports",
    ]
    copied: list[str] = []
    for source in candidates:
        if not source.exists():
            continue
        rel = source.relative_to(repo)
        target = archive / "files" / rel
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
            copied.extend(p.relative_to(repo).as_posix() for p in source.rglob("*") if p.is_file())
        else:
            _copy_file(source, target)
            copied.append(rel.as_posix())
    _write_json(
        archive / "manifest.json",
        {
            "schemaVersion": 1,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "files": sorted(set(copied)),
            "warning": "Archived review evidence may contain development credentials or other secrets. Inspect before sharing or force-adding to Git.",
        },
    )
    return archive


def _remove_codesleuth_files(
    repo: Path,
    metadata: dict[str, Any] | None,
    snapshot_paths: set[str],
    preserve_paths: set[str],
) -> None:
    target = repo / ".opencode"
    managed = (metadata or {}).get("managedFiles", {})
    remove_rel = set(managed)
    remove_rel.update({"review-pack.json", "review-pack-user.json", "profiles/detected.json"})
    if ".opencode/opencode.json" not in snapshot_paths:
        remove_rel.add("opencode.json")
    for rel in sorted(remove_rel, reverse=True):
        full_rel = (Path(".opencode") / rel).as_posix()
        if full_rel in preserve_paths:
            continue
        path = target / rel
        if path.is_file() or path.is_symlink():
            path.unlink(missing_ok=True)
        elif path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
    if target.exists():
        for directory in sorted((p for p in target.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                pass


def restore_preinstall_snapshot(repo: Path) -> dict[str, Any]:
    """Restore pre-install OpenCode files using the three-way comparison."""
    repo = git_root(repo)
    meta_path = repo / ".opencode" / "review-pack.json"
    metadata = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else None
    manifest, snapshot_dir = _load_snapshot(repo)
    snapshot_paths = {entry["path"] for entry in (manifest or {}).get("files", [])}

    if not manifest or not snapshot_dir:
        _remove_codesleuth_files(repo, metadata, snapshot_paths, set())
        return {"restored": False, "reason": "no pre-install snapshot; CodeSleuth-owned files removed without guessing prior config"}

    conflicts: list[dict[str, Any]] = []
    preserve_paths: set[str] = set()
    stamp = utc_stamp()
    conflict_root = repo / LOCAL_ROOT / "restore-conflicts" / stamp
    for entry in manifest.get("files", []):
        rel = Path(entry["path"])
        rel_key = rel.as_posix()
        if rel_key in {".gitignore", ".gitmodules"}:
            continue
        current = repo / rel
        current_state = _path_state(current)
        baseline_hash = entry["sha256"]
        installed_hash = entry.get("installedSha256")
        installed_state = entry.get("installedState", "file" if installed_hash is not None else "absent")
        current_hash = sha256_file(current) if current_state == "file" else None
        if current_hash == baseline_hash or (current_state == installed_state and current_hash == installed_hash):
            continue
        preserve_paths.add(rel_key)
        baseline_copy = conflict_root / "baseline" / rel
        _copy_file(snapshot_dir / "files" / rel, baseline_copy)
        current_copy = conflict_root / "current" / rel if current_state == "file" else None
        if current_copy is not None:
            _copy_file(current, current_copy)
        conflicts.append(
            {
                "path": rel_key,
                "reason": "pre-install file changed after CodeSleuth installation",
                "baseline": baseline_copy.relative_to(repo).as_posix(),
                "current": current_copy.relative_to(repo).as_posix() if current_copy else None,
                "currentState": current_state,
                "currentLinkTarget": str(current.readlink()) if current_state == "symlink" else None,
                "worktreePreserved": True,
            }
        )
    for managed_rel, installed_hash in (metadata or {}).get("managedFiles", {}).items():
        rel = Path(".opencode") / managed_rel
        rel_key = rel.as_posix()
        current = repo / rel
        if rel_key in snapshot_paths or not current.is_file() or sha256_file(current) == installed_hash:
            continue
        preserve_paths.add(rel_key)
        current_copy = conflict_root / "current" / rel
        _copy_file(current, current_copy)
        conflicts.append(
            {
                "path": rel_key,
                "reason": "CodeSleuth-managed file was locally modified after installation",
                "baseline": None,
                "current": current_copy.relative_to(repo).as_posix(),
                "worktreePreserved": True,
            }
        )
    if conflicts:
        _write_json(
            conflict_root / "manifest.json",
            {
                "schemaVersion": 1,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "policy": "divergent current files remain in the worktree; baseline and current copies are retained",
                "conflicts": conflicts,
            },
        )

    _remove_codesleuth_files(repo, metadata, snapshot_paths, preserve_paths)

    for entry in manifest.get("files", []):
        rel = Path(entry["path"])
        if rel.as_posix() in {".gitignore", ".gitmodules"}:
            # Root Git control files are backed up for recovery, but uninstall removes
            # only CodeSleuth-owned blocks/sections to preserve later user changes.
            continue
        if rel.as_posix() in preserve_paths:
            continue
        source = snapshot_dir / "files" / rel
        if source.is_file():
            _remove_path(repo / rel)
            _copy_file(source, repo / rel)
    return {
        "restored": True,
        "manifest": (snapshot_dir / "manifest.json").relative_to(repo).as_posix(),
        "conflicts": conflicts,
        "conflictManifest": (conflict_root / "manifest.json").relative_to(repo).as_posix() if conflicts else None,
    }


def remove_dependency(repo: Path, dependency_path: str = DEFAULT_DEPENDENCY_PATH) -> dict[str, Any]:
    """Remove the bound CodeSleuth submodule/gitlink when safe."""
    repo = git_root(repo)
    rel = _safe_rel(dependency_path).as_posix()
    status = dependency_status(repo, rel)
    if not status["bound"]:
        return {**status, "removed": False}
    worktree = repo / rel
    if worktree.exists():
        _guard_submodule_head(repo, status)
    run_git(repo, ["submodule", "deinit", "-f", "--", rel], check=False)
    run_git(repo, ["rm", "-f", "--", rel])
    return {"path": rel, "bound": False, "removed": True}


def uninstall_project(
    repo: Path,
    *,
    preserve_traces: bool = True,
    remove_bound_dependency: bool = True,
    dependency_path: str = DEFAULT_DEPENDENCY_PATH,
) -> dict[str, Any]:
    """Uninstall CodeSleuth from *repo* (runtime and optional dependency)."""
    repo = git_root(repo)
    archive = archive_traces(repo) if preserve_traces else None
    remove_agents_reports_pointer(repo)
    restored = restore_preinstall_snapshot(repo)
    dependency = (
        remove_dependency(repo, dependency_path)
        if remove_bound_dependency
        else {**dependency_status(repo, dependency_path), "removed": False}
    )
    if preserve_traces:
        ensure_local_gitignore(repo, preserve_archive_only=True)
    else:
        conflict_dir = repo / LOCAL_ROOT / "restore-conflicts"
        root = repo / LOCAL_ROOT
        if root.exists():
            for child in root.iterdir():
                if child == conflict_dir:
                    continue
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
        if restored.get("conflicts"):
            ensure_local_gitignore(repo, preserve_archive_only=True)
        else:
            remove_local_gitignore_block(repo)
            shutil.rmtree(root, ignore_errors=True)
    return {
        "preserveTraces": preserve_traces,
        "archive": archive.relative_to(repo).as_posix() if archive else None,
        "restore": restored,
        "dependency": dependency,
    }


def _metadata_source(repo: Path) -> dict[str, Any] | None:
    meta = repo / ".opencode" / "review-pack.json"
    if not meta.is_file():
        return None
    return json.loads(meta.read_text(encoding="utf-8")).get("source")


def main() -> int:
    """CLI entrypoint for project lifecycle operations."""
    parser = argparse.ArgumentParser(description="Manage CodeSleuth as a project-local dependency and reversible installation.")
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("--dependency-path", default=DEFAULT_DEPENDENCY_PATH)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--bind", action="store_true", help="pin CodeSleuth as a Git submodule")
    actions.add_argument("--unbind", action="store_true", help="remove the CodeSleuth dependency while keeping the installed runtime")
    actions.add_argument("--uninstall", action="store_true", help="restore pre-CodeSleuth config and remove CodeSleuth")
    parser.add_argument("--purge-traces", action="store_true", help="delete CodeSleuth reports/settings/backups instead of archiving them")
    parser.add_argument("--keep-dependency", action="store_true", help="uninstall the runtime but leave the CodeSleuth gitlink")
    args = parser.parse_args()
    repo = git_root(Path(args.repo))
    if args.bind:
        result = bind_dependency(repo, source_metadata=_metadata_source(repo), dependency_path=args.dependency_path)
    elif args.unbind:
        result = remove_dependency(repo, args.dependency_path)
    else:
        result = uninstall_project(
            repo,
            preserve_traces=not args.purge_traces,
            remove_bound_dependency=not args.keep_dependency,
            dependency_path=args.dependency_path,
        )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
