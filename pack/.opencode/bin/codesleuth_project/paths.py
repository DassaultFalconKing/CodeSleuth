"""Workspace path helpers: local Git excludes, reports INDEX, and AGENTS.md pointer."""
from __future__ import annotations

import os
import re
import subprocess
import textwrap
from pathlib import Path

from codesleuth_report_metadata import (
    parse_report_file,
    relate_to_head,
    resolve_current_head,
    is_report_filename,
    index_fields,
    split_front_matter,
    verify_index_matches_files,
)

LOCAL_ROOT = ".codesleuth"
REPORTS_DIR = ".codesleuth/reports"
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
    CodeSleuth is installed in this repository. Use these repository-local surfaces instead of guessing or rebuilding them:
    - Human-readable reports: `.codesleuth/reports/`; catalog: `.codesleuth/reports/INDEX.md`. Reports are derived navigation/handoff material, not finding, source, EHA, or acceptance authority.
    - Durable review/evidence continuation: `.opencode/state/reviews/`. Prefer recorded structured state over chat memory when resuming review work.
    - Context graphs: `.opencode/state/context-graphs/`. They are derived, rebuildable navigation/context projections; reopen exact source before material repository claims.
    - Project Playbook overlay: `.opencode/playbooks/`; built-in CodeSleuth Playbooks come from the installed distribution pack. Browse with `/codesleuth/playbooks`; run with `/codesleuth/playbook <id>`.
    - CodeSleuth Skills use the `codesleuth-*` namespace on portable discovery surfaces.
    - Canonical distribution source: `DassaultFalconKing/CodeSleuth`.
    Format details for analytical reports remain in `.opencode/CODESLEUTH-REPORTS.md`. Reports are local-only by default because they may contain source excerpts or credentials; publish only intentionally sanitized material.
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

Newest first. Each bullet: `file` — UTC date — title — type — target SHA — status — HEAD relationship.
This catalog is a derived navigation/read model, not EHA or finding authority. PASS never transfers to another SHA.
"""
REPORTS_INDEX_PLACEHOLDER = "- _(no reports yet)_"
REPORTS_INDEX = f"{REPORTS_INDEX_HEADER.rstrip()}\n\n{REPORTS_INDEX_PLACEHOLDER}\n"
_REPORT_TS_RE = re.compile(
    r"^(?:"
    r"(?P<y1>\d{4})(?P<m1>\d{2})(?P<d1>\d{2})T(?P<h1>\d{2})(?P<n1>\d{2})(?P<s1>\d{2})?Z"
    r"|"
    r"(?P<y2>\d{4})-(?P<m2>\d{2})-(?P<d2>\d{2})T(?P<h2>\d{2})(?P<n2>\d{2})Z"
    r")-(?P<slug>.+)$"
)


def _run_git(repo: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=check,
    )


def _git_root(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    result = _run_git(resolved, ["rev-parse", "--show-toplevel"])
    return Path(result.stdout.strip()).resolve()


def _git_info_exclude(repo: Path) -> Path:
    """Return this worktree's repository-local Git exclude file."""
    proc = _run_git(repo, ["rev-parse", "--git-path", "info/exclude"])
    raw = proc.stdout.strip()
    if not raw:
        raise RuntimeError("git rev-parse --git-path info/exclude returned an empty path")
    path = Path(raw)
    if not path.is_absolute():
        path = repo / path
    return path.resolve()


def _restore_text_file(path: Path, existed: bool, content: str) -> None:
    if existed:
        path.write_text(content, encoding="utf-8")
    elif path.exists():
        path.unlink()


def _abort_if_tracked_codesleuth_would_be_ignored(repo: Path) -> None:
    """Refuse ignore updates that would cover already-tracked ``.codesleuth`` paths.

    Uses ``git check-ignore --no-index`` so ignore rules are evaluated even for
    paths that remain tracked in the index (for example self-hosted report bodies).
    The README whitelist in ``IGNORE_LINES`` is respected by those rules.
    """
    proc = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "-z", "--", ".codesleuth"],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return
    tracked = [x for x in proc.stdout.decode("utf-8", "surrogateescape").split("\0") if x]
    for rel in tracked:
        check = subprocess.run(
            ["git", "-C", str(repo), "check-ignore", "--no-index", "-q", "--", rel],
            capture_output=True,
            check=False,
        )
        if check.returncode == 0:
            raise RuntimeError(
                f"tracked file {rel} would become ignored by CodeSleuth gitignore; aborting installation"
            )


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


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

    If applying the managed block would ignore an already-tracked ``.codesleuth``
    path (other than patterns explicitly negated, such as reports README), the
    exclude file is restored and installation aborts.
    """
    repo = _git_root(repo)
    _abort_if_tracked_codesleuth_would_be_ignored(repo)
    path = _git_info_exclude(repo)
    existed = path.is_file()
    original_raw = path.read_text(encoding="utf-8") if existed else ""
    lines = [".codesleuth/"] if preserve_archive_only else list(IGNORE_LINES)
    try:
        _replace_ignore_block(path, lines, label="Git info/exclude")
        _abort_if_tracked_codesleuth_would_be_ignored(repo)
    except Exception:
        _restore_text_file(path, existed, original_raw)
        raise
    return path


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
        _mapping, body = split_front_matter(path.read_text(encoding="utf-8"))
        for line in body.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip() or path.stem
    except (OSError, ValueError):
        pass
    return path.stem


def _format_index_line(
    name: str,
    *,
    date: str = "",
    title: str = "",
    report_type: str = "",
    target_sha: str = "",
    status: str = "",
    relationship: str = "",
    scope: str = "",
    head: str = "",
) -> str:
    return " — ".join(
        [
            f"- `{name}`",
            date or "",
            title or "",
            report_type or scope or "legacy",
            target_sha or "unknown",
            status or head or "unknown",
            relationship or "UNKNOWN",
        ]
    )


def _iter_report_files(reports: Path) -> list[Path]:
    if not reports.is_dir():
        return []
    files: list[Path] = []
    for path in reports.iterdir():
        if not path.is_file() or path.suffix.lower() != ".md":
            continue
        if path.name in {"README.md", "INDEX.md"}:
            continue
        if not is_report_filename(path.name):
            continue
        files.append(path)
    return files


def _entry_from_report(
    path: Path,
    *,
    git_repo: Path,
    current_head: str | None,
    title: str | None = None,
    date: str | None = None,
) -> dict[str, str]:
    meta = parse_report_file(path)
    relationship = relate_to_head(git_repo, meta.target_sha, current_head)
    fields = index_fields(meta, relationship)
    return {
        "date": date if date is not None else _report_display_date(path.name),
        "title": title if title is not None else _title_from_report(path),
        "report_type": fields["report_type"],
        "target_sha": fields["target_sha"],
        "status": fields["status"],
        "relationship": fields["relationship"],
        "scope": "",
        "head": "",
    }


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
                    report_type=meta.get("report_type", ""),
                    target_sha=meta.get("target_sha", ""),
                    status=meta.get("status", ""),
                    relationship=meta.get("relationship", ""),
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
    git_repo: Path | None = None,
    current_head: str | None = None,
) -> Path:
    """Atomically refresh ``.codesleuth/reports/INDEX.md`` from files on disk.

    Args:
        repo: Target repository root or isolated reports worktree.
        add: Report path or basename to upsert.
        remove: Report path or basename to drop from the index.
        title: Optional report title override.
        date: Optional UTC date string override.
        scope: Optional scope label (legacy callers; not identity).
        head: Optional HEAD / commit label (legacy callers; not identity).
        git_repo: Repository used for Git ancestry queries. Defaults to *repo*.
        current_head: Exact application HEAD SHA. Defaults to ``HEAD`` of *git_repo*.

    Returns:
        Path to the written ``INDEX.md``.

    Notes:
        The index is rebuilt from physically present timestamped report files.
        Ghost entries are dropped. ``README.md`` and ``INDEX.md`` are not
        report entries. Old INDEX metadata is never kept for a vanished report.
    """
    reports = repo / LOCAL_ROOT / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    index_path = reports / "INDEX.md"
    identity_repo = git_repo or repo
    head_sha = resolve_current_head(identity_repo, current_head)
    on_disk = {_report_basename(path): path for path in _iter_report_files(reports)}
    if remove is not None:
        on_disk.pop(_report_basename(remove), None)
    entries: dict[str, dict[str, str]] = {}
    for name, path in on_disk.items():
        entries[name] = _entry_from_report(path, git_repo=identity_repo, current_head=head_sha)
    if add is not None:
        add_path = Path(add)
        if add_path.is_file():
            file_path = add_path
            name = add_path.name
        else:
            name = _report_basename(add)
            file_path = reports / name
        if file_path.is_file() and is_report_filename(name):
            entry = _entry_from_report(
                file_path,
                git_repo=identity_repo,
                current_head=head_sha,
                title=title,
                date=date,
            )
            if scope:
                entry["scope"] = scope
            if head:
                entry["head"] = head
            entries[name] = entry
    _write_reports_index(index_path, entries)
    verify_index_matches_files(reports)
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
    repo = _git_root(repo)
    _remove_ignore_block(_git_info_exclude(repo), label="Git info/exclude")
    # Backward compatibility: versions before this hardening release wrote the
    # same managed block into the user's root .gitignore. Uninstall/update may
    # clean that old block, but new installs never create it.
    _remove_ignore_block(repo / ".gitignore", label=".gitignore")


__all__ = [
    "AGENTS_BEGIN",
    "AGENTS_END",
    "AGENTS_POINTER",
    "IGNORE_BEGIN",
    "IGNORE_END",
    "IGNORE_LINES",
    "LOCAL_ROOT",
    "REPORTS_DIR",
    "REPORTS_INDEX",
    "REPORTS_INDEX_HEADER",
    "REPORTS_INDEX_PLACEHOLDER",
    "REPORTS_README",
    "ensure_agents_reports_pointer",
    "ensure_local_gitignore",
    "ensure_reports_workspace",
    "remove_agents_reports_pointer",
    "remove_local_gitignore_block",
    "report_timestamp_key",
    "update_reports_index",
    "validate_agents_pointer",
]
