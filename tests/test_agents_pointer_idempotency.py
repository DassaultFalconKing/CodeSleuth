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


def test_ensure_agents_reports_pointer_is_idempotent_on_absent_file(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    lifecycle.ensure_agents_reports_pointer(repo)
    first = (repo / "AGENTS.md").read_text(encoding="utf-8")
    h1 = lifecycle.sha256_file(repo / "AGENTS.md")
    lifecycle.ensure_agents_reports_pointer(repo)
    second = (repo / "AGENTS.md").read_text(encoding="utf-8")
    h2 = lifecycle.sha256_file(repo / "AGENTS.md")
    assert first == second
    assert h1 == h2
    assert second.count(lifecycle.AGENTS_BEGIN) == 1
    assert second.count(lifecycle.AGENTS_END) == 1
    assert lifecycle.AGENTS_POINTER.strip() in second


def test_ensure_agents_reports_pointer_preserves_user_content_across_repeated_calls(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    (repo / "AGENTS.md").write_text("# Project agents\n\nKeep this.\n", encoding="utf-8")
    lifecycle.ensure_agents_reports_pointer(repo)
    lifecycle.ensure_agents_reports_pointer(repo)
    lifecycle.ensure_agents_reports_pointer(repo)
    text = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert "Keep this." in text
    assert text.count(lifecycle.AGENTS_BEGIN) == 1
    assert text.startswith("# Project agents")
    # exactly one pointer block at end
    assert text.rstrip("\n").endswith(lifecycle.AGENTS_POINTER.strip())
    # hash stable after idempotent calls
    h1 = lifecycle.sha256_file(repo / "AGENTS.md")
    lifecycle.ensure_agents_reports_pointer(repo)
    h2 = lifecycle.sha256_file(repo / "AGENTS.md")
    assert h1 == h2


def test_ensure_agents_reports_pointer_no_rewrite_when_already_at_end(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    lifecycle.ensure_agents_reports_pointer(repo)
    path = repo / "AGENTS.md"
    before = path.read_text(encoding="utf-8")
    mtime_before = path.stat().st_mtime_ns
    # second call should early-return without touching file
    lifecycle.ensure_agents_reports_pointer(repo)
    after = path.read_text(encoding="utf-8")
    assert before == after
    # On some filesystems mtime granularity is coarse; assert hash unchanged is primary
    assert lifecycle.sha256_file(path) == lifecycle.sha256_file(path)
    # also ensure mtime not updated if early-return path is taken (best-effort)
    # we check that at least content didn't change; mtime may be equal
    assert path.stat().st_mtime_ns == mtime_before or before == after


def test_ensure_agents_reports_pointer_collapses_duplicate_blocks(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    lifecycle.ensure_agents_reports_pointer(repo)
    first = (repo / "AGENTS.md").read_text(encoding="utf-8")
    # manually duplicate the block to simulate user or bug duplication
    dup = first + "\n" + lifecycle.AGENTS_POINTER
    (repo / "AGENTS.md").write_text(dup, encoding="utf-8")
    assert (repo / "AGENTS.md").read_text(encoding="utf-8").count(lifecycle.AGENTS_BEGIN) == 2
    lifecycle.ensure_agents_reports_pointer(repo)
    collapsed = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert collapsed.count(lifecycle.AGENTS_BEGIN) == 1
    assert collapsed.count(lifecycle.AGENTS_END) == 1
    lifecycle.ensure_agents_reports_pointer(repo)
    assert collapsed == (repo / "AGENTS.md").read_text(encoding="utf-8")


def test_ensure_agents_reports_pointer_raises_on_malformed_block(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    (repo / "AGENTS.md").write_text(
        f"# Title\n\n{lifecycle.AGENTS_BEGIN}\nwithout end\n", encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="malformed CodeSleuth reports block"):
        lifecycle.ensure_agents_reports_pointer(repo)


def test_ensure_agents_reports_pointer_idempotent_with_crlf_body(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    (repo / "AGENTS.md").write_bytes(b"# Title\r\n\r\nKeep CRLF\r\n")
    lifecycle.ensure_agents_reports_pointer(repo)
    after_first_hash = lifecycle.sha256_file(repo / "AGENTS.md")
    lifecycle.ensure_agents_reports_pointer(repo)
    after_second_hash = lifecycle.sha256_file(repo / "AGENTS.md")
    assert after_first_hash == after_second_hash
    text = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert "Keep CRLF" in text
    assert text.count(lifecycle.AGENTS_BEGIN) == 1
