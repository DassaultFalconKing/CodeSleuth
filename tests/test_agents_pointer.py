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


def test_validate_agents_pointer_accepts_missing_and_well_formed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    lifecycle.validate_agents_pointer(repo)
    lifecycle.ensure_agents_reports_pointer(repo)
    lifecycle.validate_agents_pointer(repo)


def test_agents_pointer_declares_local_report_scope(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    path = lifecycle.ensure_agents_reports_pointer(repo)
    text = path.read_text(encoding="utf-8")
    assert "local-only by default" in text
    assert "this worktree" in text
    assert "only publish sanitized reports or guidance intentionally" in text


def test_validate_agents_pointer_rejects_begin_without_end(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    path = repo / "AGENTS.md"
    path.write_text(
        "# User notes\n\nDo not lose me.\n\n" + lifecycle.AGENTS_BEGIN + "\nbroken\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="BEGIN without END|BEGIN and .* END"):
        lifecycle.validate_agents_pointer(repo)


def test_ensure_agents_reports_pointer_aborts_without_rewriting_malformed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    path = repo / "AGENTS.md"
    original = "# User notes\n\nDo not lose me.\n\n" + lifecycle.AGENTS_BEGIN + "\nbroken\n"
    path.write_text(original, encoding="utf-8")
    before_hash = lifecycle.sha256_file(path)
    with pytest.raises(RuntimeError, match="refusing to overwrite user content"):
        lifecycle.ensure_agents_reports_pointer(repo)
    assert path.read_text(encoding="utf-8") == original
    assert lifecycle.sha256_file(path) == before_hash
    assert "Do not lose me." in path.read_text(encoding="utf-8")


def test_validate_agents_pointer_rejects_end_without_begin(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    (repo / "AGENTS.md").write_text("# Title\n\n" + lifecycle.AGENTS_END + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="malformed CodeSleuth reports block"):
        lifecycle.validate_agents_pointer(repo)
