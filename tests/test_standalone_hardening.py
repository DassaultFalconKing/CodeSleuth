from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)
    return proc.stdout.strip()


def load_installer():
    spec = importlib.util.spec_from_file_location("codesleuth_installer_for_test", ROOT / "install.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_detached_source_does_not_invent_origin_head_ref(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    git(source, "init", "-b", "main")
    git(source, "config", "user.email", "test@example.invalid")
    git(source, "config", "user.name", "CodeSleuth Test")
    (source / "README.md").write_text("source\n", encoding="utf-8")
    git(source, "add", "README.md")
    git(source, "commit", "-m", "init")
    sha = git(source, "rev-parse", "HEAD")
    git(source, "remote", "add", "origin", str(source))
    git(source, "update-ref", "refs/remotes/origin/main", sha)
    git(source, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    git(source, "checkout", "--detach", sha)

    installer = load_installer()
    installer.ROOT = source
    args = SimpleNamespace(
        source_remote=None,
        source_ref=None,
        source_subdir=None,
        source_commit=None,
    )
    metadata = installer.source_metadata(args)
    assert metadata["commit"] == sha
    assert metadata["ref"] is None


def test_builtin_profiles_are_permission_neutral() -> None:
    paths = [
        ROOT / "profiles" / "generic.json",
        ROOT / "pack" / ".opencode" / "profiles" / "builtin" / "generic.json",
    ]
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "permission" not in data
        config = data.get("config")
        if isinstance(config, dict):
            assert "permission" not in config


def test_apply_settings_never_sets_build_prompt(tmp_path: Path) -> None:
    import sys

    bin_dir = ROOT / "pack" / ".opencode" / "bin"
    sys.path.insert(0, str(bin_dir))
    from codesleuth_tui_core import apply_settings_to_config_dict, default_settings

    cfg = {"permission": {}, "compaction": {}}
    settings = default_settings(["generic"])
    settings["agent"] = {"profile": "claude", "model": "anthropic/claude-sonnet-4-5"}
    updated = apply_settings_to_config_dict(cfg, settings)
    assert updated.get("model") == "anthropic/claude-sonnet-4-5"
    agent = updated.get("agent")
    if isinstance(agent, dict):
        build = agent.get("build")
        if isinstance(build, dict):
            assert "prompt" not in build
    policy = updated["permission"]["edit"]
    assert policy[".codesleuth/reports/**"] == "allow"
    assert policy["*"] == "ask"
