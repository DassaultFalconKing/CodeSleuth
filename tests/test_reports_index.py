from __future__ import annotations

import subprocess
import sys
from pathlib import Path

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


def test_ensure_reports_workspace_uses_index_helper(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    reports = lifecycle.ensure_reports_workspace(repo)
    index = reports / "INDEX.md"
    assert index.is_file()
    text = index.read_text(encoding="utf-8")
    assert text == lifecycle.REPORTS_INDEX
    assert "_(no reports yet)_" in text


def test_update_reports_index_adds_exactly_once(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    lifecycle.ensure_reports_workspace(repo)
    report = repo / ".codesleuth" / "reports" / "20260825T031200Z-architecture.md"
    report.write_text("# Architecture\n\nbody\n", encoding="utf-8")
    lifecycle.update_reports_index(repo, add=report, scope="HEAD", head="HEAD abc1234")
    lifecycle.update_reports_index(repo, add=report, scope="HEAD", head="HEAD abc1234")
    lifecycle.update_reports_index(
        repo,
        add=report.name,
        title="Architecture",
        date="2026-08-25T03:12Z",
        scope="HEAD",
        head="HEAD abc1234",
    )
    text = (repo / ".codesleuth" / "reports" / "INDEX.md").read_text(encoding="utf-8")
    assert text.count("`20260825T031200Z-architecture.md`") == 1
    assert "_(no reports yet)_" not in text
    assert "`20260825T031200Z-architecture.md`" in text


def test_update_reports_index_orders_newest_first(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    reports = lifecycle.ensure_reports_workspace(repo)
    older = reports / "20260824T010000Z-older.md"
    newer = reports / "20260825T120000Z-newer.md"
    older.write_text("# Older\n", encoding="utf-8")
    newer.write_text("# Newer\n", encoding="utf-8")
    lifecycle.update_reports_index(repo, add=older)
    lifecycle.update_reports_index(repo, add=newer)
    text = (reports / "INDEX.md").read_text(encoding="utf-8")
    assert text.index("20260825T120000Z-newer.md") < text.index("20260824T010000Z-older.md")


def test_update_reports_index_remove_rewrites_newest_first(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    reports = lifecycle.ensure_reports_workspace(repo)
    a = reports / "20260825T010000Z-a.md"
    b = reports / "20260825T020000Z-b.md"
    c = reports / "20260825T030000Z-c.md"
    for path, title in ((a, "A"), (b, "B"), (c, "C")):
        path.write_text(f"# {title}\n", encoding="utf-8")
        lifecycle.update_reports_index(repo, add=path)
    b.unlink()
    lifecycle.update_reports_index(repo, remove=b.name)
    text = (reports / "INDEX.md").read_text(encoding="utf-8")
    assert "`20260825T020000Z-b.md`" not in text
    assert text.count("`20260825T030000Z-c.md`") == 1
    assert text.count("`20260825T010000Z-a.md`") == 1
    assert text.index("20260825T030000Z-c.md") < text.index("20260825T010000Z-a.md")


def test_update_reports_index_syncs_deleted_and_new_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    reports = lifecycle.ensure_reports_workspace(repo)
    keep = reports / "20260825T040000Z-keep.md"
    drop = reports / "20260825T010000Z-drop.md"
    keep.write_text("# Keep\n", encoding="utf-8")
    drop.write_text("# Drop\n", encoding="utf-8")
    lifecycle.update_reports_index(repo)
    drop.unlink()
    added = reports / "20260826T000000Z-added.md"
    added.write_text("# Added\n", encoding="utf-8")
    lifecycle.update_reports_index(repo)
    text = (reports / "INDEX.md").read_text(encoding="utf-8")
    assert "`20260825T010000Z-drop.md`" not in text
    assert "`20260826T000000Z-added.md`" in text
    assert "`20260825T040000Z-keep.md`" in text
    assert text.index("20260826T000000Z-added.md") < text.index("20260825T040000Z-keep.md")
