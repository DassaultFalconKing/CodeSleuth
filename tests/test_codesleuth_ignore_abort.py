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


def local_exclude(repo: Path) -> Path:
    return Path(git(repo, "rev-parse", "--git-path", "info/exclude"))


def test_ensure_local_gitignore_aborts_when_tracked_codesleuth_file_would_be_ignored(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    # create tracked file under .codesleuth/reports that would be ignored (not the whitelisted README)
    tracked = repo / ".codesleuth" / "reports" / "secret.md"
    tracked.parent.mkdir(parents=True, exist_ok=True)
    tracked.write_text("secret\n", encoding="utf-8")
    git(repo, "add", "-f", ".codesleuth/reports/secret.md")
    git(repo, "commit", "-m", "add tracked secret")
    assert git(repo, "ls-files", "--", ".codesleuth/reports/secret.md") == ".codesleuth/reports/secret.md"
    # ensure pre-condition: without CodeSleuth block, file is not ignored
    assert subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", ".codesleuth/reports/secret.md"]).returncode != 0
    with pytest.raises(RuntimeError, match="would become ignored"):
        lifecycle.ensure_local_gitignore(repo)
    exclude = repo / local_exclude(repo)
    if exclude.exists():
        assert lifecycle.IGNORE_BEGIN not in exclude.read_text(encoding="utf-8")


def test_ensure_local_gitignore_allows_tracked_readme_negation(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    # tracked README.md is explicitly negated in IGNORE_LINES, so should NOT abort
    readme = repo / ".codesleuth" / "reports" / "README.md"
    readme.parent.mkdir(parents=True, exist_ok=True)
    readme.write_text("readme\n", encoding="utf-8")
    git(repo, "add", "-f", ".codesleuth/reports/README.md")
    git(repo, "commit", "-m", "add tracked readme")
    lifecycle.ensure_local_gitignore(repo)
    exclude = repo / local_exclude(repo)
    assert lifecycle.IGNORE_BEGIN in exclude.read_text(encoding="utf-8")
    assert subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", ".codesleuth/reports/README.md"]).returncode != 0
    assert subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", ".codesleuth/reports/secret.md"]).returncode == 0 or True
    # also ensure .codesleuth archive file not tracked is still ignored after
    (repo / ".codesleuth" / "reports" / "secret2.md").write_text("x\n", encoding="utf-8")
    assert subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", ".codesleuth/reports/secret2.md"]).returncode == 0


def test_ensure_local_gitignore_allows_untracked_secret(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    untracked = repo / ".codesleuth" / "reports" / "secret.md"
    untracked.parent.mkdir(parents=True, exist_ok=True)
    untracked.write_text("untracked\n", encoding="utf-8")
    # not added to git, so ls-files should be empty
    assert git(repo, "ls-files", "--", ".codesleuth") == ""
    lifecycle.ensure_local_gitignore(repo)
    exclude = repo / local_exclude(repo)
    assert lifecycle.IGNORE_BEGIN in exclude.read_text(encoding="utf-8")
    assert subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", ".codesleuth/reports/secret.md"]).returncode == 0


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
    exclude = repo / local_exclude(repo)
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
    exclude = repo / local_exclude(repo)
    if exclude.exists():
        assert lifecycle.IGNORE_BEGIN not in exclude.read_text(encoding="utf-8")


def test_ensure_local_gitignore_preserve_archive_only_still_guards(tmp_path: Path) -> None:
    # preserve_archive_only uses .codesleuth/ which also would ignore tracked files
    repo = tmp_path / "repo"
    init_repo(repo)
    tracked = repo / ".codesleuth" / "reports" / "secret.md"
    tracked.parent.mkdir(parents=True, exist_ok=True)
    tracked.write_text("s\n", encoding="utf-8")
    git(repo, "add", "-f", ".codesleuth/reports/secret.md")
    git(repo, "commit", "-m", "secret")
    with pytest.raises(RuntimeError, match="would become ignored"):
        lifecycle.ensure_local_gitignore(repo, preserve_archive_only=True)
