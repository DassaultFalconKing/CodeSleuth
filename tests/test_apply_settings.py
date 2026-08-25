from __future__ import annotations

import sys
from pathlib import Path

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))
from review_pack_tui_core import apply_settings_to_config_dict, default_settings  # noqa: E402


def test_apply_settings_sets_top_level_model() -> None:
    settings = default_settings(["generic"])
    settings["agent"]["profile"] = "claude"
    settings["agent"]["model"] = "anthropic/claude-sonnet-4-5"
    cfg = apply_settings_to_config_dict({"permission": {}, "compaction": {}}, settings)
    assert cfg["model"] == "anthropic/claude-sonnet-4-5"


def test_apply_settings_clears_top_level_model_when_empty() -> None:
    settings = default_settings(["generic"])
    settings["agent"]["profile"] = "native"
    settings["agent"]["model"] = ""
    updated = apply_settings_to_config_dict(
        {"model": "anthropic/claude-sonnet-4-5", "permission": {}, "compaction": {}},
        settings,
    )
    assert "model" not in updated
    assert updated.get("model") != "anthropic/claude-sonnet-4-5"


def test_apply_settings_never_sets_build_prompt() -> None:
    settings = default_settings(["generic"])
    settings["agent"]["profile"] = "claude"
    settings["agent"]["model"] = "anthropic/claude-sonnet-4-5"
    cfg = apply_settings_to_config_dict({"permission": {}, "compaction": {}}, settings)
    build = (cfg.get("agent") or {}).get("build") or {}
    assert "prompt" not in build
