from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))
import codesleuth_project as lifecycle  # noqa: E402


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)
    return proc.stdout.strip()


def init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init")
    git(path, "config", "user.email", "test@example.invalid")
    git(path, "config", "user.name", "CodeSleuth Test")
    (path / "README.md").write_text("target\n", encoding="utf-8")
    git(path, "add", "README.md")
    git(path, "commit", "-m", "init")


def info_exclude(repo: Path) -> Path:
    raw = git(repo, "rev-parse", "--git-path", "info/exclude")
    path = Path(raw)
    return path if path.is_absolute() else repo / path


def is_ignored(repo: Path, rel: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(repo), "check-ignore", "-q", "--", rel],
        capture_output=True,
        check=False,
    ).returncode == 0


def test_ensure_local_gitignore_uses_info_exclude_and_preserves_root_gitignore(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    root_ignore = repo / ".gitignore"
    root_ignore.write_text("node_modules/\n", encoding="utf-8")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-m", "gitignore")
    before = root_ignore.read_bytes()

    written = lifecycle.ensure_local_gitignore(repo)

    assert written.resolve() == info_exclude(repo).resolve()
    assert root_ignore.read_bytes() == before
    local = info_exclude(repo).read_text(encoding="utf-8")
    assert lifecycle.IGNORE_BEGIN in local
    assert ".opencode/state/" in local
    assert lifecycle.IGNORE_BEGIN not in root_ignore.read_text(encoding="utf-8")


def test_ensure_local_gitignore_aborts_when_tracked_codesleuth_file_would_be_ignored(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    tracked = repo / ".codesleuth" / "reports" / "secret.md"
    tracked.parent.mkdir(parents=True, exist_ok=True)
    tracked.write_text("secret\n", encoding="utf-8")
    git(repo, "add", "-f", ".codesleuth/reports/secret.md")
    git(repo, "commit", "-m", "add tracked secret")
    assert git(repo, "ls-files", "--", ".codesleuth/reports/secret.md") == ".codesleuth/reports/secret.md"
    assert subprocess.run(
        ["git", "-C", str(repo), "check-ignore", "-q", ".codesleuth/reports/secret.md"]
    ).returncode != 0
    with pytest.raises(RuntimeError, match="would become ignored"):
        lifecycle.ensure_local_gitignore(repo)
    exclude = info_exclude(repo)
    if exclude.exists():
        assert lifecycle.IGNORE_BEGIN not in exclude.read_text(encoding="utf-8")


def test_ensure_local_gitignore_allows_tracked_readme_negation(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    readme = repo / ".codesleuth" / "reports" / "README.md"
    readme.parent.mkdir(parents=True, exist_ok=True)
    readme.write_text("readme\n", encoding="utf-8")
    git(repo, "add", "-f", ".codesleuth/reports/README.md")
    git(repo, "commit", "-m", "add tracked readme")
    lifecycle.ensure_local_gitignore(repo)
    exclude = info_exclude(repo)
    assert lifecycle.IGNORE_BEGIN in exclude.read_text(encoding="utf-8")
    assert not is_ignored(repo, ".codesleuth/reports/README.md")
    (repo / ".codesleuth" / "reports" / "secret2.md").write_text("x\n", encoding="utf-8")
    assert is_ignored(repo, ".codesleuth/reports/secret2.md")


def test_ensure_local_gitignore_allows_untracked_secret(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    untracked = repo / ".codesleuth" / "reports" / "secret.md"
    untracked.parent.mkdir(parents=True, exist_ok=True)
    untracked.write_text("untracked\n", encoding="utf-8")
    assert git(repo, "ls-files", "--", ".codesleuth") == ""
    lifecycle.ensure_local_gitignore(repo)
    exclude = info_exclude(repo)
    assert lifecycle.IGNORE_BEGIN in exclude.read_text(encoding="utf-8")
    assert is_ignored(repo, ".codesleuth/reports/secret.md")


def test_ensure_local_gitignore_restores_original_on_abort(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    (repo / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-m", "gitignore")
    tracked = repo / ".codesleuth" / "notes.txt"
    tracked.parent.mkdir(parents=True, exist_ok=True)
    tracked.write_text("tracked\n", encoding="utf-8")
    git(repo, "add", "-f", ".codesleuth/notes.txt")
    git(repo, "commit", "-m", "tracked notes")
    exclude = info_exclude(repo)
    original = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    with pytest.raises(RuntimeError, match="tracked file"):
        lifecycle.ensure_local_gitignore(repo)
    after = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    assert after == original
    assert lifecycle.IGNORE_BEGIN not in after


def test_create_preinstall_snapshot_aborts_when_tracked_codesleuth_would_be_ignored(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    tracked = repo / ".codesleuth" / "reports" / "evil.md"
    tracked.parent.mkdir(parents=True, exist_ok=True)
    tracked.write_text("evil\n", encoding="utf-8")
    git(repo, "add", "-f", ".codesleuth/reports/evil.md")
    git(repo, "commit", "-m", "evil")
    with pytest.raises(RuntimeError, match="would become ignored"):
        lifecycle.create_preinstall_snapshot(repo)
    exclude = info_exclude(repo)
    if exclude.exists():
        assert lifecycle.IGNORE_BEGIN not in exclude.read_text(encoding="utf-8")


def test_ensure_local_gitignore_preserve_archive_only_still_guards(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    tracked = repo / ".codesleuth" / "reports" / "secret.md"
    tracked.parent.mkdir(parents=True, exist_ok=True)
    tracked.write_text("s\n", encoding="utf-8")
    git(repo, "add", "-f", ".codesleuth/reports/secret.md")
    git(repo, "commit", "-m", "secret")
    with pytest.raises(RuntimeError, match="would become ignored"):
        lifecycle.ensure_local_gitignore(repo, preserve_archive_only=True)


def test_local_exclude_hides_report_bodies_but_not_shareable_readme(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    lifecycle.ensure_local_gitignore(repo)

    reports = repo / ".codesleuth" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "secret.md").write_text("secret\n", encoding="utf-8")
    (reports / "README.md").write_text("shareable convention\n", encoding="utf-8")

    assert is_ignored(repo, ".codesleuth/reports/secret.md")
    assert not is_ignored(repo, ".codesleuth/reports/README.md")


def test_create_preinstall_snapshot_does_not_mutate_tracked_gitignore(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    root_ignore = repo / ".gitignore"
    root_ignore.write_text("dist/\n# user-owned\n", encoding="utf-8")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-m", "user ignore")
    before = root_ignore.read_bytes()

    lifecycle.create_preinstall_snapshot(repo)

    assert root_ignore.read_bytes() == before
    assert lifecycle.IGNORE_BEGIN in info_exclude(repo).read_text(encoding="utf-8")


def test_preserve_archive_only_uses_local_exclude(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    lifecycle.ensure_local_gitignore(repo, preserve_archive_only=True)
    local = info_exclude(repo).read_text(encoding="utf-8")
    assert ".codesleuth/" in local
    assert ".opencode/state/" not in local
    assert not (repo / ".gitignore").exists()


def test_remove_local_gitignore_block_cleans_local_and_legacy_blocks(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    lifecycle.ensure_local_gitignore(repo)
    root_ignore = repo / ".gitignore"
    root_ignore.write_text(
        "node_modules/\n\n"
        + lifecycle.IGNORE_BEGIN
        + "\n.codesleuth/\n"
        + lifecycle.IGNORE_END
        + "\n",
        encoding="utf-8",
    )

    lifecycle.remove_local_gitignore_block(repo)

    local = info_exclude(repo).read_text(encoding="utf-8") if info_exclude(repo).exists() else ""
    assert lifecycle.IGNORE_BEGIN not in local
    assert root_ignore.read_text(encoding="utf-8") == "node_modules/\n"


def test_ignore_patterns_never_hide_codesleuth_dependency() -> None:
    assert all("tools/codesleuth" not in line for line in lifecycle.IGNORE_LINES)


def test_local_exclude_resolves_for_linked_worktree(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    linked = tmp_path / "linked"
    git(repo, "worktree", "add", str(linked), "HEAD")

    written = lifecycle.ensure_local_gitignore(linked)
    expected = info_exclude(linked)
    assert written.resolve() == expected.resolve()
    assert lifecycle.IGNORE_BEGIN in expected.read_text(encoding="utf-8")
    assert is_ignored(linked, ".codesleuth/reports/secret.md")
    assert not is_ignored(linked, ".codesleuth/reports/README.md")
    assert not is_ignored(linked, "tools/codesleuth")
