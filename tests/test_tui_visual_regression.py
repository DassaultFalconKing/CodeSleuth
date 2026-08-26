from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))

from codesleuth_tui import CodeSleuthHelpPanel  # noqa: E402
from codesleuth_tui_runtime import CodeSleuthApp  # noqa: E402
from textual.widgets import Button  # noqa: E402

pytestmark = pytest.mark.skipif(
    os.environ.get("CODESLEUTH_UI_VISUAL_REGRESSION") != "1",
    reason="visual TUI regression runs in the dedicated canonical CI job",
)


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=True,
    )


def init_repo(path: Path) -> None:
    path.mkdir()
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
    git(path, "config", "user.email", "visual-regression@example.invalid")
    git(path, "config", "user.name", "CodeSleuth Visual Regression")
    (path / "README.md").write_text("visual regression target\n", encoding="utf-8")
    git(path, "add", "README.md")
    git(path, "commit", "-m", "initial")


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def screenshot_text(svg: str) -> str:
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    return normalize_space(" ".join(root.itertext()))


def assert_inside_viewport(widget, size: tuple[int, int]) -> None:
    assert widget.region.x >= 0
    assert widget.region.y >= 0
    assert widget.region.right <= size[0]
    assert widget.region.bottom <= size[1]
    assert widget.region.width > 0
    assert widget.region.height > 0


class RecordingCodeSleuthApp(CodeSleuthApp):
    def __init__(self, target: Path, distribution_root: Path | None) -> None:
        self.recorded_log: list[str] = []
        super().__init__(target, distribution_root)

    def write_ui_log(self, text: str) -> None:
        self.recorded_log.append(text)
        super().write_ui_log(text)


def event_recorder(events: list[str]):
    def hook(message) -> None:
        control = getattr(message, "control", None)
        control_id = getattr(control, "id", None)
        sender = getattr(message, "sender", None)
        sender_id = getattr(sender, "id", None)
        events.append(
            f"{message.__class__.__module__}.{message.__class__.__qualname__} "
            f"control={control_id or '-'} sender={sender_id or '-'}"
        )

    return hook


def artifact_root(tmp_path: Path) -> Path:
    configured = os.environ.get("CODESLEUTH_UI_ARTIFACT_DIR")
    root = Path(configured) if configured else tmp_path / "tui-regression-artifacts"
    root.mkdir(parents=True, exist_ok=True)
    return root


def capture_and_analyze(
    app: RecordingCodeSleuthApp,
    *,
    case: str,
    size: tuple[int, int],
    tmp_path: Path,
    events: list[str],
    required_text: tuple[str, ...],
) -> dict[str, object]:
    case_dir = artifact_root(tmp_path) / case
    case_dir.mkdir(parents=True, exist_ok=True)

    svg = app.export_screenshot(title=f"CodeSleuth visual regression: {case}", simplify=True)
    (case_dir / "screen.svg").write_text(svg, encoding="utf-8")

    ui_log = "\n".join(app.recorded_log) + ("\n" if app.recorded_log else "")
    (case_dir / "ui.log").write_text(ui_log, encoding="utf-8")
    (case_dir / "events.log").write_text("\n".join(events) + "\n", encoding="utf-8")

    visible = screenshot_text(svg)
    analysis = {
        "case": case,
        "viewport": {"width": size[0], "height": size[1]},
        "required_text": list(required_text),
        "required_text_present": {token: token in visible for token in required_text},
        "ui_log_lines": len(app.recorded_log),
        "event_count": len(events),
        "svg_bytes": len(svg.encode("utf-8")),
        "visible_text_excerpt": visible[:4000],
    }
    (case_dir / "analysis.json").write_text(
        json.dumps(analysis, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    assert len(svg) > 1000, "rendered SVG is unexpectedly empty"
    assert "Traceback" not in visible
    for token in required_text:
        assert token in visible, f"{token!r} missing from rendered screenshot {case}"
    return analysis


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("size", "case"),
    [((48, 20), "home-compact"), ((120, 35), "home-wide")],
)
async def test_home_render_is_visible_and_artifacted(
    tmp_path: Path,
    monkeypatch,
    size: tuple[int, int],
    case: str,
) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    events: list[str] = []
    app = RecordingCodeSleuthApp(repo, None)

    async with app.run_test(size=size, message_hook=event_recorder(events)) as pilot:
        await pilot.pause()
        assert_inside_viewport(app.query_one("#activity-panel"), size)
        assert_inside_viewport(app.query_one("#surface"), size)
        assert any("Console opened" in line for line in app.recorded_log)
        capture_and_analyze(
            app,
            case=case,
            size=size,
            tmp_path=tmp_path,
            events=events,
            required_text=("Home · Evidence Console", "Recent activity", "Repository"),
        )


@pytest.mark.asyncio
async def test_verify_click_has_single_dispatch_visible_feedback_and_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    events: list[str] = []
    calls: list[str] = []
    monkeypatch.setattr(RecordingCodeSleuthApp, "run_runtime_action", lambda self, action: calls.append(action))
    app = RecordingCodeSleuthApp(repo, None)
    size = (120, 35)

    async with app.run_test(size=size, message_hook=event_recorder(events)) as pilot:
        await pilot.pause()
        assert await pilot.click("#smoke")
        await pilot.pause()
        assert calls == ["smoke"]
        assert any("Verify started" in line for line in app.recorded_log)
        capture_and_analyze(
            app,
            case="verify-feedback",
            size=size,
            tmp_path=tmp_path,
            events=events,
            required_text=("Home · Evidence Console", "Recent activity", "Verify started"),
        )


@pytest.mark.asyncio
async def test_tools_update_has_single_dispatch_visible_feedback_and_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    events: list[str] = []
    calls: list[str] = []
    monkeypatch.setattr(RecordingCodeSleuthApp, "run_runtime_action", lambda self, action: calls.append(action))
    app = RecordingCodeSleuthApp(repo, None)
    size = (120, 35)

    async with app.run_test(size=size, message_hook=event_recorder(events)) as pilot:
        await pilot.pause()
        assert await pilot.click("#nav-tools")
        await pilot.pause()
        app.query_one("#update", Button).disabled = False
        assert await pilot.click("#update")
        await pilot.pause()
        assert calls == ["update"]
        assert any("Update started" in line for line in app.recorded_log)
        capture_and_analyze(
            app,
            case="tools-update-feedback",
            size=size,
            tmp_path=tmp_path,
            events=events,
            required_text=("Tools · OpenCode-native capabilities", "Recent activity", "Update started"),
        )


@pytest.mark.asyncio
async def test_left_navigation_collapse_restore_is_visually_stable(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    events: list[str] = []
    app = RecordingCodeSleuthApp(repo, None)
    size = (120, 35)

    async with app.run_test(size=size, message_hook=event_recorder(events)) as pilot:
        await pilot.pause()
        nav = app.query_one("#wide-nav")
        assert_inside_viewport(nav, size)
        capture_and_analyze(
            app,
            case="left-nav-expanded",
            size=size,
            tmp_path=tmp_path,
            events=events,
            required_text=("Surfaces", "Home", "Review", "Tools", "Settings"),
        )

        assert await pilot.click("#nav-collapse")
        await pilot.pause()
        assert nav.has_class("collapsed")
        assert all(not button.display for button in app.query("#wide-nav .nav-button"))
        assert_inside_viewport(nav, size)
        capture_and_analyze(
            app,
            case="left-nav-collapsed",
            size=size,
            tmp_path=tmp_path,
            events=events,
            required_text=("Home · Evidence Console", "Recent activity"),
        )

        assert await pilot.click("#nav-collapse")
        await pilot.pause()
        assert not nav.has_class("collapsed")
        assert all(button.display for button in app.query("#wide-nav .nav-button"))
        capture_and_analyze(
            app,
            case="left-nav-restored",
            size=size,
            tmp_path=tmp_path,
            events=events,
            required_text=("Surfaces", "Home", "Review", "Tools", "Settings"),
        )


@pytest.mark.asyncio
async def test_right_help_panel_collapse_restore_is_visually_stable(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    events: list[str] = []
    app = RecordingCodeSleuthApp(repo, None)
    size = (140, 40)

    async with app.run_test(size=size, message_hook=event_recorder(events)) as pilot:
        await pilot.pause()
        app.action_show_help_panel()
        await pilot.pause()
        panel = app.query_one(CodeSleuthHelpPanel)
        assert not panel.has_class("collapsed")
        assert_inside_viewport(panel, size)
        capture_and_analyze(
            app,
            case="right-help-expanded",
            size=size,
            tmp_path=tmp_path,
            events=events,
            required_text=("Home · Evidence Console", "Recent activity"),
        )

        assert await pilot.click("#right-collapse")
        await pilot.pause()
        assert panel.has_class("collapsed")
        assert_inside_viewport(panel, size)
        capture_and_analyze(
            app,
            case="right-help-collapsed",
            size=size,
            tmp_path=tmp_path,
            events=events,
            required_text=("Home · Evidence Console", "Recent activity"),
        )

        assert await pilot.click("#right-collapse")
        await pilot.pause()
        assert not panel.has_class("collapsed")
        assert_inside_viewport(panel, size)
        capture_and_analyze(
            app,
            case="right-help-restored",
            size=size,
            tmp_path=tmp_path,
            events=events,
            required_text=("Home · Evidence Console", "Recent activity"),
        )
