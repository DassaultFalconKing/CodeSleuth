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
        encoding="utf-8",
        errors="strict",
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
    git(repo, "config", "core.autocrlf", "false")
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
        newline="\n",
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


UTF8_REPORT_BODY = (
    "Handoff — отчёт: acceptance not transferred.\n"
    "Non-ASCII extras: € café 報告.\n"
)


def test_git_subprocess_decodes_stdout_as_strict_utf8(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _, repo = init_remote(tmp_path)
    recorded: list[dict[str, object]] = []
    real_run = subprocess.run

    def wrapped(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        recorded.append(kwargs)
        return real_run(*args, **kwargs)

    monkeypatch.setattr(shared_reports.subprocess, "run", wrapped)
    shared_reports._git(repo, "rev-parse", "HEAD")

    assert recorded
    for kwargs in recorded:
        assert kwargs.get("text") is True
        assert kwargs.get("encoding") == "utf-8"
        assert kwargs.get("errors") == "strict"


def test_publish_syncs_utf8_report_without_false_collision(tmp_path: Path) -> None:
    remote, first = init_remote(tmp_path)
    name = "20260828T200252Z-utf8.md"
    report = write_report(first, name, UTF8_REPORT_BODY)
    original_text = report.read_text(encoding="utf-8")
    original_bytes = report.read_bytes()
    assert original_bytes == original_text.encode("utf-8")
    assert "—" in original_text
    assert "отчёт" in original_text
    assert "€" in original_text
    app_head = git(first, "rev-parse", "HEAD").stdout.strip()

    result = shared_reports.publish_shared_report(first, report)

    assert result["publishedRemote"] is True
    assert result["applicationHead"] == app_head
    assert git(first, "rev-parse", "HEAD").stdout.strip() == app_head
    remote_tip = git(first, "ls-remote", "--heads", "origin", "reports").stdout.strip()
    assert result["commit"] in remote_tip
    rel = f".codesleuth/reports/{name}"
    shown = shared_reports._git(first, "show", f"{result['commit']}:{rel}").stdout
    assert shown == original_text
    blob = subprocess.run(
        ["git", "-C", str(first), "show", f"{result['commit']}:{rel}"],
        capture_output=True,
        check=True,
    )
    assert blob.stdout == original_bytes

    second = tmp_path / "second"
    subprocess.run(["git", "clone", str(remote), str(second)], check=True, capture_output=True)
    git(second, "checkout", "main")
    synced = shared_reports.sync_shared_reports(second)
    assert synced["status"] == "synced"
    imported = second / ".codesleuth" / "reports" / name
    assert imported.is_file()
    assert imported.read_text(encoding="utf-8") == original_text
    shown_second = shared_reports._git(second, "show", f"{synced['remoteCommit']}:{rel}").stdout
    assert shown_second == original_text
    assert git(second, "rev-parse", "HEAD").stdout.strip() == git(first, "rev-parse", "HEAD").stdout.strip()


def test_utf8_same_name_different_content_still_fails_closed(tmp_path: Path) -> None:
    remote, first = init_remote(tmp_path)
    name = "20260828T200252Z-utf8.md"
    shared_reports.publish_shared_report(first, write_report(first, name, UTF8_REPORT_BODY))

    second = tmp_path / "second"
    subprocess.run(["git", "clone", str(remote), str(second)], check=True, capture_output=True)
    git(second, "checkout", "main")
    write_report(second, name, "different — содержимое €\n")
    with pytest.raises(RuntimeError, match="local/shared report collision"):
        shared_reports.sync_shared_reports(second)
