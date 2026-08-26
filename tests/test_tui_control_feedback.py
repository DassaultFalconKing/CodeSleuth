from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("textual")

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))

from codesleuth_tui_runtime import CodeSleuthApp  # noqa: E402
from textual.widgets import Button  # noqa: E402


def init_repo(path: Path) -> None:
    path.mkdir()
    subprocess.run(["git", "-C", str(path), "init"], check=True, capture_output=True)
    (path / "README.md").write_text("target\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True, capture_output=True)


class RecordingCodeSleuthApp(CodeSleuthApp):
    def __init__(self, target: Path, distribution_root: Path | None) -> None:
        self.recorded_log: list[str] = []
        super().__init__(target, distribution_root)

    def write_ui_log(self, text: str) -> None:
        self.recorded_log.append(text)
        super().write_ui_log(text)


@pytest.mark.asyncio
@pytest.mark.parametrize("size", [(48, 20), (120, 35)])
async def test_activity_console_stays_visible_and_greets(tmp_path: Path, monkeypatch, size: tuple[int, int]) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)

    app = RecordingCodeSleuthApp(repo, None)
    async with app.run_test(size=size) as pilot:
        await pilot.pause()
        activity = app.query_one("#activity-panel")
        log = app.query_one("#log")
        assert activity.display
        assert activity.region.x >= 0
        assert activity.region.y >= 0
        assert activity.region.right <= size[0]
        assert activity.region.bottom <= size[1]
        assert log.region.height > 0
        assert any("Console opened" in line for line in app.recorded_log)


@pytest.mark.asyncio
async def test_verify_button_dispatches_and_acknowledges_immediately(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    calls: list[str] = []
    monkeypatch.setattr(RecordingCodeSleuthApp, "run_runtime_action", lambda self, action: calls.append(action))

    app = RecordingCodeSleuthApp(repo, None)
    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.pause()
        await pilot.click("#smoke")
        await pilot.pause()
        assert calls == ["smoke"]
        assert any("Verify started" in line for line in app.recorded_log)
        assert app.query_one("#activity-panel").display


@pytest.mark.asyncio
async def test_footer_check_update_reports_unavailable_instead_of_silence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)

    app = RecordingCodeSleuthApp(repo, None)
    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.pause()
        app.query_one("#check-update", Button).disabled = True
        await pilot.press("k")
        await pilot.pause()
        assert any("Check Updates unavailable" in line for line in app.recorded_log)


@pytest.mark.asyncio
async def test_update_button_dispatches_through_runtime_feedback_layer(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    calls: list[str] = []
    monkeypatch.setattr(RecordingCodeSleuthApp, "run_runtime_action", lambda self, action: calls.append(action))

    app = RecordingCodeSleuthApp(repo, None)
    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.pause()
        await pilot.click("#nav-tools")
        await pilot.pause()
        app.query_one("#update", Button).disabled = False
        await pilot.click("#update")
        await pilot.pause()
        assert calls == ["update"]
        assert any("Update started" in line for line in app.recorded_log)
