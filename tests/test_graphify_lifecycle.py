from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pack" / ".opencode" / "bin"))
import codesleuth_project as lifecycle  # noqa: E402
import review_pack_tui_core as tui_core  # noqa: E402


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def test_builtin_is_persisted_default_and_graphify_is_explicit() -> None:
    default = tui_core.default_settings(["generic"])
    assert default["contextGraph"]["provider"] == "builtin"
    selected = tui_core.validate_settings({"profiles": ["generic"], "contextGraph": {"provider": "graphify"}})
    assert selected["contextGraph"]["provider"] == "graphify"
    assert "Context graph provider: graphify" in tui_core.settings_summary(selected)
    assert '"provider": "graphify"' in tui_core.config_preview(selected)


def test_unknown_provider_fails_settings_validation() -> None:
    try:
        tui_core.validate_settings({"profiles": ["generic"], "contextGraph": {"provider": "automatic"}})
    except ValueError as error:
        assert "builtin or graphify" in str(error)
    else:
        raise AssertionError("unknown context provider must fail closed")


def test_provider_execution_tools_are_scoped_to_build_controller() -> None:
    config = json.loads((ROOT / "pack" / ".opencode" / "opencode.json").read_text(encoding="utf-8"))
    assert config["permission"]["repo_context_provider_*"] == "deny"
    build = config["agent"]["build"]["permission"]
    assert build["repo_context_provider_status"] == "allow"
    assert build["repo_context_provider_extract"] == "allow"


def test_optional_runtime_removal_is_exactly_scoped(tmp_path: Path) -> None:
    git(tmp_path, "init", "-q")
    runtime = tmp_path / ".runtime" / "graphify-provider"
    sibling = tmp_path / ".runtime" / "keep-me"
    runtime.mkdir(parents=True)
    sibling.mkdir()
    (runtime / "package.txt").write_text("graphifyy", encoding="utf-8")
    (sibling / "state.txt").write_text("preserve", encoding="utf-8")
    result = lifecycle.remove_graphify_provider_runtime(tmp_path)
    assert result["removed"] is True and result["recoverable"] is False
    assert not runtime.exists()
    assert (sibling / "state.txt").read_text(encoding="utf-8") == "preserve"
    second = lifecycle.remove_graphify_provider_runtime(tmp_path)
    assert second["removed"] is False
