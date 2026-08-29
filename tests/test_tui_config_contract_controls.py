from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("textual")

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))

from codesleuth_tui import CodeSleuthApp, CodeSleuthConfigScreen  # noqa: E402
from textual.widgets import Select, Static, Switch  # noqa: E402


def init_repo(path: Path) -> None:
    path.mkdir()
    subprocess.run(["git", "-C", str(path), "init"], check=True, capture_output=True)
    (path / "README.md").write_text("target\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True, capture_output=True)


@pytest.mark.asyncio
async def test_branded_config_exposes_all_inherited_collection_controls(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    app = CodeSleuthApp(repo, None)

    async with app.run_test(size=(120, 140)) as pilot:
        await pilot.click("#configure")
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, CodeSleuthConfigScreen)
        assert screen.query_one("#enforce-agents", Switch)
        assert screen.query_one("#context-graph-provider", Select)

        collected = screen._collect()
        assert collected["policy"]["enforceAgentsMdRules"] is False
        assert collected["contextGraph"]["provider"] == "builtin"
        assert "Settings are not valid yet" not in str(screen.query_one("#summary", Static).render())
