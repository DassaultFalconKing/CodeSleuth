from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.tui_user_witness import (  # noqa: E402
    WitnessRecorder,
    capture_textual_checkpoint,
    load_journey,
    render_user_probe,
    render_ux_diff,
)


class Button:
    def __init__(self, label: str, node_id: str, *, disabled: bool = False) -> None:
        self.label = label
        self.id = node_id
        self.disabled = disabled
        self.display = True
        self.visible = True


class Switch:
    def __init__(self, label: str, node_id: str, value: bool) -> None:
        self.label = label
        self.id = node_id
        self.value = value
        self.disabled = False
        self.display = True
        self.visible = True


class FakeScreen:
    title = "Settings"

    def __init__(self, *nodes) -> None:
        self.nodes = list(nodes)

    def walk_children(self):
        return iter(self.nodes)


def test_user_probe_never_falls_back_to_machine_target() -> None:
    journey = load_journey(ROOT / "docs" / "tui-user-witness" / "journeys" / "configure-repository.json")
    journey = json.loads(json.dumps(journey))
    journey["trajectory"][0]["action"] = {
        "kind": "activate",
        "target": "#configure",
    }

    prompt = render_user_probe(journey)

    assert "Action: activate." in prompt
    assert "#configure" not in prompt


def test_ux_diff_reports_visible_change_without_machine_ids() -> None:
    before = {
        "screen_title": "Settings",
        "nodes": [
            {
                "role": "switch",
                "type": "Switch",
                "id": "enforce-agents",
                "text": "Maintain workflow rules",
                "state": {"value": False, "disabled": False},
            }
        ],
    }
    after = {
        "screen_title": "Settings",
        "nodes": [
            {
                "role": "switch",
                "type": "Switch",
                "id": "enforce-agents",
                "text": "Maintain workflow rules",
                "state": {"value": True, "disabled": False},
            },
            {
                "role": "button",
                "type": "Button",
                "id": "apply",
                "text": "Apply",
                "state": {"disabled": False},
            },
        ],
    }

    diff = render_ux_diff(before, after)

    assert "Maintain workflow rules" in diff
    assert "False" in diff
    assert "True" in diff
    assert "[button] Apply" in diff
    assert "enforce-agents" not in diff
    assert "#apply" not in diff
    assert "type=Switch" not in diff


def test_recorder_writes_complete_bundle(tmp_path: Path) -> None:
    journey = load_journey(ROOT / "docs" / "tui-user-witness" / "journeys" / "configure-repository.json")
    recorder = WitnessRecorder(journey, tmp_path / "bundle")

    recorder.checkpoint(
        "settings-before",
        FakeScreen(
            Switch("Maintain workflow rules", "enforce-agents", False),
            Button("Apply", "apply"),
        ),
        screenshot_svg="<svg><text>before</text></svg>",
        action={"kind": "observe", "label": "Open Settings"},
        user_expects="The repository policy is visible.",
    )
    recorder.checkpoint(
        "settings-after",
        FakeScreen(
            Switch("Maintain workflow rules", "enforce-agents", True),
            Button("Apply", "apply"),
        ),
        screenshot_svg="<svg><text>after</text></svg>",
        action={"kind": "change", "label": "Maintain workflow rules"},
        user_expects="The changed policy is visible before Apply.",
    )
    manifest = recorder.finalize()

    assert manifest["kind"] == "codesleuth-user-witness"
    assert manifest["diagnostic_only"] is True
    assert manifest["acceptance_authority"] is False
    assert manifest["state_count"] == 2

    expected_root_files = {
        "journey.json",
        "manifest.json",
        "trajectory.json",
        "ux-diff.txt",
    }
    assert expected_root_files <= {path.name for path in (tmp_path / "bundle").iterdir()}

    for state_dir in ("00-settings-before", "01-settings-after"):
        files = {path.name for path in (tmp_path / "bundle" / state_dir).iterdir()}
        assert {
            "screen.svg",
            "semantic.json",
            "user-view.txt",
            "developer-view.txt",
            "user-probe.txt",
            "ux-diff.txt",
        } <= files

    user_view = (tmp_path / "bundle" / "01-settings-after" / "user-view.txt").read_text(encoding="utf-8")
    developer_view = (tmp_path / "bundle" / "01-settings-after" / "developer-view.txt").read_text(encoding="utf-8")
    diff = (tmp_path / "bundle" / "01-settings-after" / "ux-diff.txt").read_text(encoding="utf-8")

    assert "#enforce-agents" not in user_view
    assert "id=#enforce-agents" in developer_view
    assert "False" in diff and "True" in diff
    assert "#enforce-agents" not in diff


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.mark.skipif(
    os.environ.get("CODESLEUTH_UI_VISUAL_REGRESSION") != "1",
    reason="real User Witness SVG bundle is captured in the dedicated TUI visual job",
)
@pytest.mark.asyncio
async def test_live_home_user_witness_bundle_is_artifacted(tmp_path: Path, monkeypatch) -> None:
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

    configured = os.environ.get("CODESLEUTH_UI_ARTIFACT_DIR")
    artifact_root = Path(configured) if configured else tmp_path / "tui-regression-artifacts"
    bundle_dir = artifact_root / "user-witness" / "home-orient"

    journey = load_journey(ROOT / "docs" / "tui-user-witness" / "smoke" / "home-orient.json")
    recorder = WitnessRecorder(journey, bundle_dir)
    app = CodeSleuthApp(repo, None)

    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.pause()
        capture_textual_checkpoint(
            app,
            recorder,
            "home",
            action={"kind": "observe", "label": "Open CodeSleuth"},
            user_expects="The current repository, primary surfaces, and recent activity are understandable.",
        )

    manifest = recorder.finalize()
    assert manifest["state_count"] == 1
    assert (bundle_dir / "00-home" / "screen.svg").stat().st_size > 1000

    user_view = (bundle_dir / "00-home" / "user-view.txt").read_text(encoding="utf-8")
    probe = (bundle_dir / "00-home" / "user-probe.txt").read_text(encoding="utf-8")
    assert "Settings" in user_view
    assert "Recent activity" in user_view
    assert "#" not in user_view
    assert "You are the operator, not the developer." in probe
