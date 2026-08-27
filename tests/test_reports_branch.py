from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))
import codesleuth_reports as shared_reports  # noqa: E402


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=check,
    )


def init_remote(tmp_path: Path) -> tuple[Path, Path]:
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    repo = tmp_path / "repo"
    subprocess.run(["git", "clone", str(remote), str(repo)], check=True, capture_output=True)
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "CodeSleuth Test")
    (repo / "README.md").write_text("application\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "init")
    git(repo, "push", "origin", "HEAD:main")
    return remote, repo


def write_report(repo: Path, name: str, body: str = "body") -> Path:
    reports = repo / ".codesleuth" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    path = reports / name
    path.write_text(
        "# Shared report\n\n"
        "- target: 0123456789abcdef\n"
        "- scope: HEAD\n\n"
        f"{body}\n",
        encoding="utf-8",
    )
    return path


def test_publish_creates_reports_only_orphan_branch_without_moving_head(tmp_path: Path) -> None:
    _, repo = init_remote(tmp_path)
    report = write_report(repo, "20260828T010000Z-first.md")
    app_head = git(repo, "rev-parse", "HEAD").stdout.strip()

    result = shared_reports.publish_shared_report(repo, report)

    assert result["branch"] == "reports"
    assert result["publishedRemote"] is True
    assert result["applicationHead"] == app_head
    assert git(repo, "rev-parse", "HEAD").stdout.strip() == app_head
    paths = git(repo, "ls-tree", "-r", "--name-only", "reports").stdout.splitlines()
    assert paths
    assert all(path.startswith(".codesleuth/reports/") for path in paths)
    assert "README.md" not in paths
    assert ".opencode/state/reviews" not in "\n".join(paths)

    root = git(repo, "rev-list", "--max-parents=0", "reports").stdout.strip()
    assert root
    assert git(repo, "ls-tree", "-r", "--name-only", root).stdout.strip() == ""


def test_second_clone_syncs_and_preserves_shared_reports(tmp_path: Path) -> None:
    remote, first = init_remote(tmp_path)
    one = write_report(first, "20260828T010000Z-first.md")
    shared_reports.publish_shared_report(first, one)

    second = tmp_path / "second"
    subprocess.run(["git", "clone", str(remote), str(second)], check=True, capture_output=True)
    git(second, "checkout", "main")
    git(second, "config", "user.email", "test2@example.invalid")
    git(second, "config", "user.name", "CodeSleuth Test 2")
    synced = shared_reports.sync_shared_reports(second)
    assert synced["status"] == "synced"
    assert synced["imported"] == 1
    assert (second / ".codesleuth/reports/20260828T010000Z-first.md").is_file()

    two = write_report(second, "20260828T020000Z-second.md")
    shared_reports.publish_shared_report(second, two)
    names = git(second, "ls-tree", "-r", "--name-only", "reports").stdout
    assert "20260828T010000Z-first.md" in names
    assert "20260828T020000Z-second.md" in names


def test_publish_blocks_secret_candidates_before_branch_write(tmp_path: Path) -> None:
    _, repo = init_remote(tmp_path)
    report = write_report(
        repo,
        "20260828T030000Z-secret.md",
        "Authorization: Bearer abcdefghijklmnopqrstuvwxyz012345",
    )

    with pytest.raises(RuntimeError, match="secret scanner"):
        shared_reports.publish_shared_report(repo, report)

    assert git(repo, "rev-parse", "--verify", "refs/heads/reports", check=False).returncode != 0


def test_existing_nonreport_reports_branch_is_rejected(tmp_path: Path) -> None:
    _, repo = init_remote(tmp_path)
    git(repo, "branch", "reports", "HEAD")
    report = write_report(repo, "20260828T040000Z-collision.md")

    with pytest.raises(RuntimeError, match="non-report paths"):
        shared_reports.publish_shared_report(repo, report)
