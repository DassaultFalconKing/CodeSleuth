from __future__ import annotations

import json
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
    path.mkdir(parents=True)
    git(path, "init")
    git(path, "config", "user.email", "test@example.invalid")
    git(path, "config", "user.name", "CodeSleuth Test")
    (path / "README.md").write_text("target\n", encoding="utf-8")
    git(path, "add", "README.md")
    git(path, "commit", "-m", "init")


def test_preinstall_backup_and_restore(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    init_repo(repo)
    (repo / ".gitignore").write_text("target/\n", encoding="utf-8")
    oc = repo / ".opencode"
    (oc / "agents").mkdir(parents=True)
    (oc / "opencode.json").write_text('{"original":true}\n', encoding="utf-8")
    (oc / "agents" / "custom.md").write_text("custom\n", encoding="utf-8")

    pointer = lifecycle.create_preinstall_snapshot(repo)
    assert (repo / pointer["manifest"]).is_file()
    ignore = (repo / ".gitignore").read_text(encoding="utf-8")
    assert ".codesleuth/" in ignore
    assert ".opencode/state/" in ignore
    assert "tools/codesleuth" not in ignore
    assert subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", "tools/codesleuth"]).returncode != 0

    (oc / "opencode.json").write_text('{"codesleuth":true}\n', encoding="utf-8")
    (oc / "agents" / "repo-reviewer.md").write_text("managed\n", encoding="utf-8")
    (oc / "review-pack-user.json").write_text('{"x":1}\n', encoding="utf-8")
    (oc / "review-pack.json").write_text(json.dumps({"managedFiles": {"agents/repo-reviewer.md": "deadbeef"}}), encoding="utf-8")

    result = lifecycle.restore_preinstall_snapshot(repo)
    assert result["restored"] is True
    assert json.loads((oc / "opencode.json").read_text(encoding="utf-8"))["original"] is True
    assert (oc / "agents" / "custom.md").read_text(encoding="utf-8") == "custom\n"
    assert not (oc / "agents" / "repo-reviewer.md").exists()
    assert not (oc / "review-pack-user.json").exists()


def test_bind_and_remove_dependency(tmp_path: Path) -> None:
    source = tmp_path / "source"
    init_repo(source)
    (source / "tool.txt").write_text("codesleuth\n", encoding="utf-8")
    git(source, "add", "tool.txt")
    git(source, "commit", "-m", "tool")
    source_sha = git(source, "rev-parse", "HEAD")

    target = tmp_path / "target"
    init_repo(target)
    bound = lifecycle.bind_dependency(
        target,
        source_metadata={"remote": str(source), "commit": source_sha},
    )
    assert bound["bound"] is True
    assert bound["commit"] == source_sha
    assert (target / ".gitmodules").is_file()
    stage = git(target, "ls-files", "--stage", "tools/codesleuth")
    assert stage.startswith("160000 ")

    removed = lifecycle.remove_dependency(target)
    assert removed["removed"] is True
    assert not lifecycle.dependency_status(target)["bound"]
    assert not (target / "tools" / "codesleuth").exists()


def test_uninstall_preserves_sensitive_traces_in_ignored_archive(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    init_repo(repo)
    oc = repo / ".opencode"
    oc.mkdir()
    (oc / "opencode.json").write_text('{"before":"codesleuth"}\n', encoding="utf-8")
    lifecycle.create_preinstall_snapshot(repo)

    (oc / "review-pack.json").write_text(json.dumps({"managedFiles": {}}), encoding="utf-8")
    (oc / "review-pack-user.json").write_text('{"profile":"rust"}\n', encoding="utf-8")
    reviews = oc / "state" / "reviews" / "r1"
    reviews.mkdir(parents=True)
    (reviews / "findings.ndjson").write_text('{"evidence":"TOKEN=secret"}\n', encoding="utf-8")

    result = lifecycle.uninstall_project(repo, preserve_traces=True, remove_bound_dependency=False)
    archive = repo / result["archive"]
    assert archive.is_dir()
    archived_finding = archive / "files" / ".opencode" / "state" / "reviews" / "r1" / "findings.ndjson"
    assert "TOKEN=secret" in archived_finding.read_text(encoding="utf-8")
    assert ".codesleuth/" in (repo / ".gitignore").read_text(encoding="utf-8")
    assert subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", ".codesleuth/archive"]).returncode == 0
    assert json.loads((oc / "opencode.json").read_text(encoding="utf-8"))["before"] == "codesleuth"


def test_uninstall_purge_restores_config_and_removes_local_root(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    init_repo(repo)
    oc = repo / ".opencode"
    oc.mkdir()
    (oc / "opencode.json").write_text('{"before":1}\n', encoding="utf-8")
    lifecycle.create_preinstall_snapshot(repo)
    (oc / "opencode.json").write_text('{"after":1}\n', encoding="utf-8")
    (oc / "review-pack.json").write_text(json.dumps({"managedFiles": {}}), encoding="utf-8")

    result = lifecycle.uninstall_project(repo, preserve_traces=False, remove_bound_dependency=False)
    assert result["archive"] is None
    assert not (repo / ".codesleuth").exists()
    assert json.loads((oc / "opencode.json").read_text(encoding="utf-8"))["before"] == 1
    if (repo / ".gitignore").exists():
        assert lifecycle.IGNORE_BEGIN not in (repo / ".gitignore").read_text(encoding="utf-8")


def test_invalid_dependency_path_fails_closed(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    init_repo(repo)
    with pytest.raises(ValueError):
        lifecycle.dependency_status(repo, "../codesleuth")
