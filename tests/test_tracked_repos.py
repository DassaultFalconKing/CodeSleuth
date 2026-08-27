from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BIN))
import codesleuth_project as lifecycle  # noqa: E402


def init_repo(path: Path) -> None:
    path.mkdir()
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
    assert entry["name"] == "target"
    assert entry["version"] == "0.4.0"
    assert entry["source"] is None
    assert lifecycle.registry_path().is_file()
    assert lifecycle.format_tracked_label(entry) == "target · no source · 0.4.0"

    listed = lifecycle.list_tracked_repositories(refresh=True)
    assert len(listed) == 1
    assert listed[0]["path"] == str(repo.resolve())
    assert listed[0]["lifecycle"] == lifecycle.lifecycle_state(repo)
    assert listed[0]["name"] == "target"

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
                    "commit": "abc123",
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
    assert lifecycle.format_tracked_label(entry) == (
        "example/catalog-demo · DassaultFalconKing/CodeSleuth@main · 0.4.0"
    )
    assert "unbound-active" not in lifecycle.format_tracked_label(entry)


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
