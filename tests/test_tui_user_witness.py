from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.tui_user_witness import (  # noqa: E402
    load_journey,
    render_semantic_text,
    render_user_probe,
    semantic_snapshot,
)


class Horizontal:
    def __init__(self, *children) -> None:
        self.children = list(children)
        self.display = True
        self.visible = True


class Button:
    def __init__(self, label: str, node_id: str) -> None:
        self.label = label
        self.id = node_id
        self.display = True
        self.visible = True
        self.disabled = False


class Switch:
    def __init__(self, label: str, node_id: str, value: bool) -> None:
        self.label = label
        self.id = node_id
        self.value = value
        self.display = True
        self.visible = True
        self.disabled = False


class Static:
    def __init__(self, text: str, node_id: str | None = None) -> None:
        self._text = text
        self.id = node_id
        self.display = True
        self.visible = True

    def render(self) -> str:
        return self._text


class FakeScreen:
    title = "CodeSleuth Configuration"

    def __init__(self, *nodes) -> None:
        self.nodes = list(nodes)

    def walk_children(self):
        return iter(self.nodes)


def test_semantic_snapshot_keeps_user_controls_and_filters_layout() -> None:
    root = FakeScreen(
        Horizontal(),
        Button("Settings", "configure"),
        Switch("Maintain workflow rules", "enforce-agents", False),
        Static("Settings are valid"),
    )

    snapshot = semantic_snapshot(root)
    assert [node["role"] for node in snapshot["nodes"]] == ["button", "switch", "static"]

    user_view = render_semantic_text(snapshot)
    assert "Settings" in user_view
    assert "Maintain workflow rules" in user_view
    assert "#configure" not in user_view
    assert "Button" not in user_view

    developer_view = render_semantic_text(snapshot, include_machine_ids=True)
    assert "id=#configure" in developer_view
    assert "type=Button" in developer_view


def test_initial_journeys_follow_protocol() -> None:
    journeys = ROOT / "docs" / "tui-user-witness" / "journeys"
    paths = sorted(journeys.glob("*.json"))
    assert [path.name for path in paths] == [
        "configure-repository.json",
        "inspect-playbook.json",
        "self-install.json",
    ]
    for path in paths:
        journey = load_journey(path)
        assert journey["surface"] == "tui"
        assert journey["trajectory"]
        assert journey["affordances"]


def test_model_as_user_prompt_hides_implementation_mapping() -> None:
    journey = load_journey(ROOT / "docs" / "tui-user-witness" / "journeys" / "configure-repository.json")
    prompt = render_user_probe(journey, "SCREEN Settings\n[button] Apply\n")

    assert "Configure CodeSleuth behavior" in prompt
    assert "[button] Apply" in prompt
    assert "CodeSleuthConfigScreen" not in prompt
    assert "#configure" not in prompt
    assert "#enforce-agents" not in prompt
    assert "ConfigScreen._collect" not in prompt


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.mark.asyncio
async def test_live_tui_home_has_a_compact_user_semantic_view(tmp_path: Path, monkeypatch) -> None:
    pytest.importorskip("textual")
    bin_dir = ROOT / "pack" / ".opencode" / "bin"
    sys.path.insert(0, str(bin_dir))
    from codesleuth_tui_runtime import CodeSleuthApp

    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
    _git(repo, "config", "user.email", "user-witness@example.invalid")
    _git(repo, "config", "user.name", "CodeSleuth User Witness")
    (repo / "README.md").write_text("user witness target\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "initial")

    app = CodeSleuthApp(repo, None)
    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.pause()
        snapshot = semantic_snapshot(app.screen)
        user_view = render_semantic_text(snapshot)

    assert "Settings" in user_view
    assert "Recent activity" in user_view
    assert "#" not in user_view
