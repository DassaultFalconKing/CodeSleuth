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
    assert ".codesleuth/*" in ignore
    assert "!.codesleuth/reports/README.md" in ignore
    assert ".opencode/state/" in ignore
    assert "tools/codesleuth" not in ignore
    assert subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", "tools/codesleuth"]).returncode != 0

    (oc / "opencode.json").write_text('{"codesleuth":true}\n', encoding="utf-8")
    (oc / "agents" / "repo-reviewer.md").write_text("managed\n", encoding="utf-8")
    (oc / "review-pack-user.json").write_text('{"x":1}\n', encoding="utf-8")
    managed_hash = lifecycle.sha256_file(oc / "agents" / "repo-reviewer.md")
    (oc / "review-pack.json").write_text(
        json.dumps({"managedFiles": {"agents/repo-reviewer.md": managed_hash}}), encoding="utf-8"
    )
    lifecycle.record_postinstall_snapshot(repo)

    result = lifecycle.restore_preinstall_snapshot(repo)
    assert result["restored"] is True
    assert json.loads((oc / "opencode.json").read_text(encoding="utf-8"))["original"] is True
    assert (oc / "agents" / "custom.md").read_text(encoding="utf-8") == "custom\n"
    assert not (oc / "agents" / "repo-reviewer.md").exists()
    assert not (oc / "review-pack-user.json").exists()


def test_postinstall_restore_hash_is_not_redefined_by_later_user_change(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    init_repo(repo)
    config = repo / ".opencode" / "opencode.json"
    config.parent.mkdir()
    config.write_text("baseline\n", encoding="utf-8")
    lifecycle.create_preinstall_snapshot(repo)
    config.write_text("installed\n", encoding="utf-8")
    installed_hash = lifecycle.sha256_file(config)
    lifecycle.record_postinstall_snapshot(repo)
    config.write_text("later user change\n", encoding="utf-8")
    lifecycle.record_postinstall_snapshot(repo)

    manifest, _ = lifecycle._load_snapshot(repo)
    assert manifest is not None
    entry = next(item for item in manifest["files"] if item["path"] == ".opencode/opencode.json")
    assert entry["installedSha256"] == installed_hash
    assert entry["installedSha256"] != lifecycle.sha256_file(config)


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


def _bound_repositories(tmp_path: Path) -> tuple[Path, Path, str]:
    source = tmp_path / "source"
    init_repo(source)
    (source / "tool.txt").write_text("codesleuth\n", encoding="utf-8")
    git(source, "add", "tool.txt")
    git(source, "commit", "-m", "tool")
    source_sha = git(source, "rev-parse", "HEAD")
    target = tmp_path / "target"
    init_repo(target)
    lifecycle.bind_dependency(target, source_metadata={"remote": str(source), "commit": source_sha})
    return source, target, source_sha


def test_dirty_submodule_removal_is_rejected(tmp_path: Path) -> None:
    _, target, _ = _bound_repositories(tmp_path)
    (target / "tools" / "codesleuth" / "tool.txt").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="dirty CodeSleuth submodule"):
        lifecycle.remove_dependency(target)


def test_clean_local_divergent_submodule_commit_removal_is_rejected(tmp_path: Path) -> None:
    _, target, recorded = _bound_repositories(tmp_path)
    submodule = target / "tools" / "codesleuth"
    git(submodule, "config", "user.email", "test@example.invalid")
    git(submodule, "config", "user.name", "CodeSleuth Test")
    (submodule / "local.txt").write_text("unpushed\n", encoding="utf-8")
    git(submodule, "add", "local.txt")
    git(submodule, "commit", "-m", "local unpushed work")
    local = git(submodule, "rev-parse", "HEAD")
    assert local != recorded
    assert git(submodule, "status", "--porcelain") == ""
    with pytest.raises(RuntimeError, match=local):
        lifecycle.remove_dependency(target)
    assert git(submodule, "rev-parse", "HEAD") == local
    assert lifecycle.dependency_status(target)["commit"] == recorded


def test_dependency_only_state_and_explicit_unbind(tmp_path: Path) -> None:
    _, target, _ = _bound_repositories(tmp_path)
    assert lifecycle.lifecycle_state(target) == "dependency-only"
    removed = lifecycle.remove_dependency(target)
    assert removed["removed"] is True
    assert lifecycle.lifecycle_state(target) == "unbound-inactive"


def test_ignored_dependency_path_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "source"
    init_repo(source)
    sha = git(source, "rev-parse", "HEAD")
    target = tmp_path / "target"
    init_repo(target)
    (target / ".gitignore").write_text("tools/\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="ignored by the target repository"):
        lifecycle.bind_dependency(target, source_metadata={"remote": str(source), "commit": sha})


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


@pytest.mark.parametrize("preserve_traces", [True, False])
def test_uninstall_never_loses_postinstall_change_to_preexisting_file(
    tmp_path: Path, preserve_traces: bool
) -> None:
    repo = tmp_path / "target"
    init_repo(repo)
    custom = repo / ".opencode" / "agents" / "custom.md"
    custom.parent.mkdir(parents=True)
    custom.write_text("baseline\n", encoding="utf-8")
    lifecycle.create_preinstall_snapshot(repo)

    custom.write_text("installed\n", encoding="utf-8")
    meta = repo / ".opencode" / "review-pack.json"
    meta.write_text(json.dumps({"managedFiles": {}}), encoding="utf-8")
    lifecycle.record_postinstall_snapshot(repo)
    custom.write_text("user change after install\n", encoding="utf-8")

    result = lifecycle.uninstall_project(
        repo,
        preserve_traces=preserve_traces,
        remove_bound_dependency=False,
    )
    assert custom.read_text(encoding="utf-8") == "user change after install\n"
    assert result["restore"]["conflicts"][0]["path"] == ".opencode/agents/custom.md"
    manifest = repo / result["restore"]["conflictManifest"]
    assert manifest.is_file()
    conflict = json.loads(manifest.read_text(encoding="utf-8"))["conflicts"][0]
    assert (repo / conflict["baseline"]).read_text(encoding="utf-8") == "baseline\n"
    assert (repo / conflict["current"]).read_text(encoding="utf-8") == "user change after install\n"
    assert ".codesleuth/" in (repo / ".gitignore").read_text(encoding="utf-8")
    if not preserve_traces:
        assert not (repo / ".codesleuth" / "backups").exists()
        assert (repo / ".codesleuth" / "restore-conflicts").is_dir()


@pytest.mark.parametrize("preserve_traces", [True, False])
@pytest.mark.parametrize("current_state", ["absent", "directory"])
def test_uninstall_preserves_postinstall_deletion_or_type_change(
    tmp_path: Path, preserve_traces: bool, current_state: str
) -> None:
    repo = tmp_path / "target"
    init_repo(repo)
    custom = repo / ".opencode" / "agents" / "custom.md"
    custom.parent.mkdir(parents=True)
    custom.write_text("baseline\n", encoding="utf-8")
    lifecycle.create_preinstall_snapshot(repo)

    custom.write_text("installed\n", encoding="utf-8")
    meta = repo / ".opencode" / "review-pack.json"
    meta.write_text(json.dumps({"managedFiles": {}}), encoding="utf-8")
    lifecycle.record_postinstall_snapshot(repo)
    custom.unlink()
    if current_state == "directory":
        custom.mkdir()
        (custom / "user.txt").write_text("type changed after install\n", encoding="utf-8")

    result = lifecycle.uninstall_project(
        repo,
        preserve_traces=preserve_traces,
        remove_bound_dependency=False,
    )
    conflict = result["restore"]["conflicts"][0]
    assert conflict["path"] == ".opencode/agents/custom.md"
    assert conflict["currentState"] == current_state
    assert conflict["current"] is None
    assert (repo / conflict["baseline"]).read_text(encoding="utf-8") == "baseline\n"
    if current_state == "absent":
        assert not custom.exists()
    else:
        assert custom.is_dir()
        assert (custom / "user.txt").read_text(encoding="utf-8") == "type changed after install\n"
    assert (repo / result["restore"]["conflictManifest"]).is_file()


def test_uninstall_purge_restores_config_and_removes_local_root(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    init_repo(repo)
    oc = repo / ".opencode"
    oc.mkdir()
    (oc / "opencode.json").write_text('{"before":1}\n', encoding="utf-8")
    lifecycle.create_preinstall_snapshot(repo)
    (oc / "opencode.json").write_text('{"after":1}\n', encoding="utf-8")
    (oc / "review-pack.json").write_text(json.dumps({"managedFiles": {}}), encoding="utf-8")
    lifecycle.record_postinstall_snapshot(repo)

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


def test_installer_normalizes_nested_target_to_git_root(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    init_repo(repo)
    nested = repo / "nested" / "directory"
    nested.mkdir(parents=True)
    subprocess.run([sys.executable, str(BIN.parents[2] / "install.py"), str(nested)], check=True)
    assert (repo / ".opencode" / "review-pack.json").is_file()
    assert not (nested / ".opencode").exists()
    reports = repo / ".codesleuth" / "reports"
    assert (reports / "README.md").is_file()
    assert (reports / "INDEX.md").is_file()
    assert "CodeSleuth reports" in (repo / "AGENTS.md").read_text(encoding="utf-8")
    ignore = (repo / ".gitignore").read_text(encoding="utf-8")
    assert "!.codesleuth/reports/README.md" in ignore
    assert subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", ".codesleuth/reports/secret.md"]).returncode == 0
    assert subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", ".codesleuth/reports/README.md"]).returncode != 0


def test_reports_workspace_is_seeded_and_uninstalled_pointer_removed(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    init_repo(repo)
    (repo / "AGENTS.md").write_text("# Project agents\n\nKeep this.\n", encoding="utf-8")
    git(repo, "add", "AGENTS.md")
    git(repo, "commit", "-m", "agents")
    lifecycle.ensure_reports_workspace(repo)
    lifecycle.ensure_agents_reports_pointer(repo)
    lifecycle.ensure_local_gitignore(repo)
    assert (repo / ".codesleuth" / "reports" / "README.md").is_file()
    text = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert "Keep this." in text
    assert lifecycle.AGENTS_BEGIN in text
    (repo / ".codesleuth" / "reports" / "20260825T010000Z-demo.md").write_text("# demo\n", encoding="utf-8")
    oc = repo / ".opencode"
    oc.mkdir()
    (oc / "review-pack.json").write_text(json.dumps({"managedFiles": {}}), encoding="utf-8")
    result = lifecycle.uninstall_project(repo, preserve_traces=True, remove_bound_dependency=False)
    archive = repo / result["archive"]
    assert (archive / "files" / ".codesleuth" / "reports" / "20260825T010000Z-demo.md").is_file()
    leftover = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert "Keep this." in leftover
    assert lifecycle.AGENTS_BEGIN not in leftover
