from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))
import codesleuth_project as lifecycle  # noqa: E402
import codesleuth_project.tracked_repos as tracked  # noqa: E402


def init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "CodeSleuth Test"], check=True)
    (path / "README.md").write_text("target\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "commit", "-m", "initial"], check=True, capture_output=True)


def write_metadata(repo: Path) -> Path:
    opencode = repo / ".opencode"
    opencode.mkdir(parents=True, exist_ok=True)
    path = opencode / "review-pack.json"
    path.write_text(
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
    return path


def test_reachable_metadata_parse_failure_retains_previous_exact_identity(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    metadata = write_metadata(repo)
    original = lifecycle.record_tracked_repository(repo)
    assert original["source"]["commit"] == "abc123def4567890abc123def4567890abc12345"
    assert original["version"] == "0.4.0"

    metadata.write_text("{ malformed", encoding="utf-8")
    with (
        mock.patch("codesleuth_project.lifecycle_state", return_value=original["lifecycle"] or "unbound-active"),
        mock.patch("codesleuth_project.dependency_status", return_value={"bound": False}),
    ):
        listed = lifecycle.list_tracked_repositories(refresh=True)
        rerecorded = lifecycle.record_tracked_repository(repo)

    assert listed[0]["reachable"] is True
    assert listed[0]["source"] == original["source"]
    assert listed[0]["version"] == original["version"]
    assert "abc123" in lifecycle.format_tracked_label(listed[0])
    assert rerecorded["source"] == original["source"]
    assert rerecorded["version"] == original["version"]


def test_reachable_origin_probe_failure_retains_previous_origin_and_name(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "catalog-demo"
    init_repo(repo)
    subprocess.run(
        ["git", "-C", str(repo), "remote", "add", "origin", "https://github.com/example/catalog-demo.git"],
        check=True,
        capture_output=True,
    )
    write_metadata(repo)
    original = lifecycle.record_tracked_repository(repo)
    assert original["name"] == "example/catalog-demo"
    assert original["origin"] == "https://github.com/example/catalog-demo.git"

    real_git_output = tracked._git_output

    def fail_origin(path: Path, *args: str) -> str | None:
        if args == ("remote", "get-url", "origin"):
            return None
        return real_git_output(path, *args)

    with (
        mock.patch.object(tracked, "_git_output", side_effect=fail_origin),
        mock.patch("codesleuth_project.lifecycle_state", return_value=original["lifecycle"] or "unbound-active"),
        mock.patch("codesleuth_project.dependency_status", return_value={"bound": False}),
    ):
        listed = lifecycle.list_tracked_repositories(refresh=True)
        rerecorded = lifecycle.record_tracked_repository(repo)

    assert listed[0]["reachable"] is True
    assert listed[0]["origin"] == original["origin"]
    assert listed[0]["name"] == original["name"]
    assert rerecorded["origin"] == original["origin"]
    assert rerecorded["name"] == original["name"]
