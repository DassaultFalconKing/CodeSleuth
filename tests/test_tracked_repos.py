from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BIN))
import codesleuth_project as lifecycle  # noqa: E402


def init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "CodeSleuth Test"], check=True)
    (path / "README.md").write_text("target\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "commit", "-m", "initial"], check=True, capture_output=True)


def test_host_registry_records_lists_and_forgets(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    (repo / ".opencode").mkdir()
    (repo / ".opencode" / "review-pack.json").write_text(
        json.dumps({"version": "0.4.0", "complete": True}),
        encoding="utf-8",
    )

    entry = lifecycle.record_tracked_repository(repo)
    assert entry["path"] == str(repo.resolve())
    assert entry["version"] == "0.4.0"
    assert lifecycle.registry_path().is_file()

    listed = lifecycle.list_tracked_repositories(refresh=True)
    assert len(listed) == 1
    assert listed[0]["path"] == str(repo.resolve())
    assert listed[0]["lifecycle"] == lifecycle.lifecycle_state(repo)

    assert lifecycle.forget_tracked_repository(repo) is True
    assert lifecycle.list_tracked_repositories(refresh=False) == []


def test_host_registry_records_name_and_codesleuth_source(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    subprocess.run(
        ["git", "-C", str(repo), "remote", "add", "origin", "https://github.com/example/catalog-demo.git"],
        check=True,
        capture_output=True,
    )
    (repo / ".opencode").mkdir()
    (repo / ".opencode" / "review-pack.json").write_text(
        json.dumps(
            {
                "version": "0.4.0",
                "complete": True,
                "source": {
                    "remote": "https://github.com/DassaultFalconKing/CodeSleuth.git",
                    "ref": "main",
                    "subdir": "",
                    "commit": "abc123def4567890abc123def4567890abc12345",
                },
            }
        ),
        encoding="utf-8",
    )

    entry = lifecycle.record_tracked_repository(repo)
    assert entry["name"] == "example/catalog-demo"
    assert entry["origin"] == "https://github.com/example/catalog-demo.git"
    assert entry["source"]["remote"] == "https://github.com/DassaultFalconKing/CodeSleuth.git"
    assert entry["source"]["ref"] == "main"
    # commit must be visible — BLOCKER 1
    assert "abc123" in lifecycle.format_tracked_label(entry)
    assert "DassaultFalconKing/CodeSleuth" in lifecycle.format_tracked_label(entry)
    # lifecycle-only noisy label must not appear
    assert "unbound" not in lifecycle.format_tracked_label(entry).lower()


def test_source_label_commit_always_visible(tmp_path: Path) -> None:
    # 1. remote + ref + commit
    src = {"remote": "https://github.com/DassaultFalconKing/CodeSleuth.git", "ref": "main", "commit": "2d62781f70bbf079a84afcb8c429e8d8c5e87413"}
    label = lifecycle.source_label(src)
    assert "DassaultFalconKing/CodeSleuth" in label
    assert "main" in label
    assert "2d62781" in label  # commit must not disappear
    # commit must not be hidden behind branch ref authority — both present but commit visible
    assert label.count("2d62781") >= 1

    # 2. remote + null ref + commit (detached)
    src2 = {"remote": "https://github.com/DassaultFalconKing/CodeSleuth.git", "ref": None, "commit": "2d62781f70bbf079a84afcb8c429e8d8c5e87413"}
    label2 = lifecycle.source_label(src2)
    assert "DassaultFalconKing/CodeSleuth" in label2
    assert "2d62781" in label2
    assert label2 != "no source"

    # 3. commit without remote
    src3 = {"remote": None, "ref": None, "commit": "abc123def4567890abc123def4567890abc12345"}
    label3 = lifecycle.source_label(src3)
    assert "abc123" in label3 or "abc123d" in label3
    assert label3 != "no source"

    # 4. legacy/no source
    assert lifecycle.source_label(None) == "no source"
    assert lifecycle.source_label({}) == "no source"
    assert lifecycle.source_label({"remote": None, "ref": None, "commit": None}) == "no source"

    # 6. branch ref must not hide commit — commit still present even when ref is branch
    src_branch = {"remote": "https://github.com/owner/repo.git", "ref": "main", "commit": "deadbeef12345678"}
    label_branch = lifecycle.source_label(src_branch)
    assert "deadbee" in label_branch
    assert "main" in label_branch


def test_tui_label_contains_commit_identity(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "catalog-demo"
    init_repo(repo)
    subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", "https://github.com/example/catalog-demo.git"], check=True, capture_output=True)
    (repo / ".opencode").mkdir()
    (repo / ".opencode" / "review-pack.json").write_text(
        json.dumps({"version": "0.4.0", "source": {"remote": "https://github.com/DassaultFalconKing/CodeSleuth.git", "ref": "main", "commit": "deadbeef12345678deadbeef12345678deadbeef12"}}),
        encoding="utf-8",
    )
    entry = lifecycle.record_tracked_repository(repo)
    label = lifecycle.format_tracked_label(entry)
    assert "example/catalog-demo" in label
    assert "deadbee" in label
    assert "0.4.0" in label


def test_short_remote_variants() -> None:
    assert lifecycle.short_remote("https://github.com/owner/repo.git") == "owner/repo"
    assert lifecycle.short_remote("git@github.com:owner/repo.git") == "owner/repo"
    assert lifecycle.short_remote("ssh://git@github.com/owner/repo.git") == "owner/repo"
    assert lifecycle.short_remote("https://gitlab.com/group/sub/repo.git") == "group/repo" or lifecycle.short_remote("https://gitlab.com/group/sub/repo.git") == "sub/repo"
    # local path
    assert lifecycle.short_remote("/tmp/local-repo") == "local-repo"
    assert lifecycle.short_remote("C:\\path\\to\\repo") == "repo" or lifecycle.short_remote("C:\\path\\to\\repo") == "repo"
    # bare directory
    assert lifecycle.short_remote("../relative/path.git") == "path"
    # malformed/empty
    assert lifecycle.short_remote("") is None
    assert lifecycle.short_remote(None) is None
    assert lifecycle.short_remote("   ") is None


def test_host_registry_drops_missing_paths_on_refresh(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    live = tmp_path / "catalog-demo"
    init_repo(live)
    lifecycle.record_tracked_repository(live)
    missing = tmp_path / "target"
    payload = {
        "schemaVersion": 1,
        "repositories": [
            json.loads(lifecycle.registry_path().read_text(encoding="utf-8"))["repositories"][0],
            {
                "path": str(missing),
                "addedAt": "2026-01-01T00:00:00Z",
                "lastSeenAt": "2026-01-01T00:00:00Z",
                "name": "target",
                "version": "0.4.0",
                "lifecycle": "unbound-active",
                "source": None,
            },
        ],
    }
    lifecycle.registry_path().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    listed = lifecycle.list_tracked_repositories(refresh=True)
    assert [item["path"] for item in listed] == [str(live.resolve())]
    persisted = json.loads(lifecycle.registry_path().read_text(encoding="utf-8"))
    assert [item["path"] for item in persisted["repositories"]] == [str(live.resolve())]


def test_existing_repo_not_pruned_on_lifecycle_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "existing"
    init_repo(repo)
    entry = lifecycle.record_tracked_repository(repo)
    assert entry["path"] == str(repo.resolve())

    with mock.patch("codesleuth_project.lifecycle_state", side_effect=RuntimeError("probe fails")):
        listed = lifecycle.list_tracked_repositories(refresh=True)
    # must remain, not pruned, even though reachable is False
    assert len(listed) == 1
    assert listed[0]["path"] == str(repo.resolve())
    # previous name/version must be preserved
    assert listed[0].get("name") == entry.get("name")
    assert listed[0].get("version") == entry.get("version")


def test_existing_repo_not_pruned_on_malformed_metadata(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "existing2"
    init_repo(repo)
    (repo / ".opencode").mkdir(parents=True, exist_ok=True)
    (repo / ".opencode" / "review-pack.json").write_text("{ malformed json", encoding="utf-8")
    lifecycle.record_tracked_repository(repo)
    # now refresh — metadata is malformed but repo exists, should stay
    listed = lifecycle.list_tracked_repositories(refresh=True)
    assert len(listed) == 1
    assert listed[0]["path"] == str(repo.resolve())
    # should not lose previous identity — still has path, name
    assert listed[0]["path"] == str(repo.resolve())


def test_existing_repo_git_remote_failure_retained(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "existing3"
    init_repo(repo)
    subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", "https://github.com/example/repo.git"], check=True, capture_output=True)
    (repo / ".opencode").mkdir(parents=True, exist_ok=True)
    (repo / ".opencode" / "review-pack.json").write_text(json.dumps({"version": "0.4.0", "source": {"remote": "https://github.com/DassaultFalconKing/CodeSleuth.git", "ref": "main", "commit": "abc123"}}), encoding="utf-8")
    lifecycle.record_tracked_repository(repo)
    # simulate git remote get-url failure by removing origin and making probe still succeed for exists
    subprocess.run(["git", "-C", str(repo), "remote", "remove", "origin"], check=True, capture_output=True)
    listed = lifecycle.list_tracked_repositories(refresh=True)
    assert len(listed) == 1
    # fallback identity should be folder name or previous
    assert listed[0]["path"] == str(repo.resolve())
    # source should still be preserved from previous (not cleared)
    assert listed[0].get("source") is not None or listed[0].get("version") == "0.4.0"


def test_registry_persistence_after_degraded_refresh(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "repo"
    init_repo(repo)
    subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", "https://github.com/example/catalog-demo.git"], check=True, capture_output=True)
    (repo / ".opencode").mkdir(parents=True, exist_ok=True)
    (repo / ".opencode" / "review-pack.json").write_text(json.dumps({"version": "0.4.0", "source": {"remote": "https://github.com/DassaultFalconKing/CodeSleuth.git", "ref": "main", "commit": "fullcommit1234567890fullcommit1234567890full"}}), encoding="utf-8")
    orig = lifecycle.record_tracked_repository(repo)
    # degrade next refresh
    with mock.patch("codesleuth_project.lifecycle_state", side_effect=RuntimeError("transient")):
        degraded = lifecycle.list_tracked_repositories(refresh=True)
    assert degraded[0]["path"] == orig["path"]
    # must not lose useful fields
    assert degraded[0]["name"] == orig["name"]
    assert degraded[0]["source"] == orig["source"]
    assert degraded[0]["version"] == orig["version"]


def test_forget_removes_existing_and_normalizes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    lifecycle.record_tracked_repository(repo)
    # forget with normalized path (no probe required, even if repo would be degraded)
    with mock.patch("codesleuth_project.lifecycle_state", side_effect=RuntimeError("probe fails")):
        removed = lifecycle.forget_tracked_repository(repo)
    assert removed is True
    assert lifecycle.list_tracked_repositories(refresh=False) == []
    # forgetting non-existent returns False and exit code 1 for CLI
    assert lifecycle.forget_tracked_repository(repo) is False


def test_codesleuth_project_list_cli(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    lifecycle.record_tracked_repository(repo)

    env = os.environ.copy()
    env["CODESLEUTH_HOST_STATE_DIR"] = str(tmp_path / "host-state")
    env["PYTHONPATH"] = str(BIN)
    proc = subprocess.run(
        [sys.executable, "-m", "codesleuth_project", "--list"],
        cwd=str(BIN),
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )
    payload = json.loads(proc.stdout)
    assert isinstance(payload, list)
    assert payload[0]["path"] == str(repo.resolve())
    assert payload[0]["name"] == "target"


def test_codesleuth_project_forget_cli(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    lifecycle.record_tracked_repository(repo)

    env = os.environ.copy()
    env["CODESLEUTH_HOST_STATE_DIR"] = str(tmp_path / "host-state")
    env["PYTHONPATH"] = str(BIN)
    proc = subprocess.run(
        [sys.executable, "-m", "codesleuth_project", str(repo), "--forget"],
        cwd=str(BIN),
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )
    payload = json.loads(proc.stdout)
    assert payload["forgotten"] is True
    assert lifecycle.list_tracked_repositories(refresh=False) == []

    # forgetting again should exit 1
    proc2 = subprocess.run(
        [sys.executable, "-m", "codesleuth_project", str(repo), "--forget"],
        cwd=str(BIN),
        text=True,
        capture_output=True,
        env=env,
    )
    assert proc2.returncode == 1
    assert json.loads(proc2.stdout)["forgotten"] is False


def test_self_install_flag_required_for_source_checkout(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    env = os.environ.copy()
    env["CODESLEUTH_HOST_STATE_DIR"] = str(tmp_path / "host-state")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "install.py"), str(ROOT)],
        text=True,
        capture_output=True,
        env=env,
    )
    assert proc.returncode != 0
    assert "--self-install" in (proc.stderr + proc.stdout)

    blocked = subprocess.run(
        [sys.executable, str(ROOT / "install.py"), str(ROOT), "--self-install", "--bind-dependency"],
        text=True,
        capture_output=True,
        env=env,
    )
    assert blocked.returncode != 0
    combined = (blocked.stderr + blocked.stdout).lower()
    assert "bind-dependency" in combined or "self-install" in combined
