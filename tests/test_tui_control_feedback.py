from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path

import pytest

pytest.importorskip("textual")

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))

from codesleuth_tui_runtime import CodeSleuthApp  # noqa: E402
import review_pack_tui  # noqa: E402
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


@pytest.mark.asyncio
async def test_home_exposes_update_codesleuth_action(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)

    app = RecordingCodeSleuthApp(repo, None)
    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.pause()
        update = app.query_one("#update", Button)
        assert app.current_surface == "home"
        assert update.display
        assert str(update.label) == "Update CodeSleuth"
        assert update.disabled


@pytest.mark.asyncio
async def test_update_available_highlights_home_action_and_dispatches(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    calls: list[str] = []
    monkeypatch.setattr(RecordingCodeSleuthApp, "run_runtime_action", lambda self, action: calls.append(action))

    app = RecordingCodeSleuthApp(repo, None)
    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.pause()
        update = app.query_one("#update", Button)
        update.disabled = False
        app.set_update_available(True)
        await pilot.pause()
        assert update.display
        assert update.variant == "primary"
        await pilot.click("#update")
        await pilot.pause()
        assert calls == ["update"]
        assert any("Update started" in line for line in app.recorded_log)


@pytest.mark.asyncio
async def test_runtime_workers_never_touch_widgets_and_mutating_actions_are_single_flight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    main_thread = threading.get_ident()
    validation_threads: list[int] = []
    started = threading.Event()
    release = threading.Event()
    action_calls: list[list[str]] = []
    original_run = review_pack_tui.subprocess.run

    class ThreadCheckingApp(RecordingCodeSleuthApp):
        def validate_target(self) -> Path:
            validation_threads.append(threading.get_ident())
            return super().validate_target()

    def controlled_run(command, *args, **kwargs):
        values = [str(value) for value in command]
        if any(value.endswith("review-pack-smoke.py") for value in values):
            action_calls.append(values)
            started.set()
            assert release.wait(5), "test did not release the runtime action"
            return subprocess.CompletedProcess(command, 0, "PACK SMOKE PASS\n", "")
        return original_run(command, *args, **kwargs)

    monkeypatch.setattr(review_pack_tui.subprocess, "run", controlled_run)
    app = ThreadCheckingApp(repo, None)
    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.pause()
        assert app.run_runtime_action("smoke") is True
        for _ in range(50):
            await pilot.pause(0.02)
            if started.is_set():
                break
        assert started.is_set(), "runtime worker did not start"
        assert app.run_runtime_action("update") is False
        assert len(action_calls) == 1, "a second lifecycle worker must not overlap the first"
        assert any("already running" in line for line in app.recorded_log)
        release.set()
        for _ in range(50):
            await pilot.pause(0.02)
            if not app._runtime_action_active:
                break
        assert not app._runtime_action_active

    assert validation_threads
    assert set(validation_threads) == {main_thread}, "widget-backed target validation must remain on the Textual app thread"
