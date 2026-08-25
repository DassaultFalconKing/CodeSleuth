from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("textual")

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))
import codesleuth_project as lifecycle  # noqa: E402
from review_pack_tui import ConfigScreen, ReviewPackApp, UninstallScreen  # noqa: E402
from codesleuth_tui import (  # noqa: E402
    HELP_SECTIONS,
    NAV_SURFACES,
    CodeSleuthApp,
    CodeSleuthConfigScreen,
    CodeSleuthHelpScreen,
)
from textual.widgets import Button, Select, Switch  # noqa: E402


def init_repo(path: Path) -> None:
    path.mkdir()
    subprocess.run(["git", "-C", str(path), "init"], check=True, capture_output=True)
    (path / "README.md").write_text("target\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True, capture_output=True)


@pytest.mark.asyncio
async def test_app_mounts_and_exposes_dependency_and_uninstall_controls(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    init_repo(repo)
    app = ReviewPackApp(repo, None)
    assert "log" not in ReviewPackApp.__dict__
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert app.query_one("#configure")
        assert app.query_one("#uninstall")
        assert "Dependency:" in str(app.query_one("#status").render())


@pytest.mark.asyncio
async def test_uninstall_modal_requires_explicit_choice(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    init_repo(repo)
    app = ReviewPackApp(repo, None)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.click("#uninstall")
        await pilot.pause()
        assert isinstance(app.screen, UninstallScreen)
        assert app.screen.query_one("#preserve")
        assert app.screen.query_one("#purge")
        assert app.screen.query_one("#cancel")
        text = "\n".join(str(widget.render()) for widget in app.screen.query("Static"))
        assert "known CodeSleuth settings" in text
        assert "unrelated project files are not archived or deleted" in text


@pytest.mark.asyncio
async def test_pilot_can_unbind_dependency_without_uninstalling_runtime(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    init_repo(source)
    init_repo(target)
    subprocess.run(["git", "-C", str(source), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(source), "config", "user.name", "CodeSleuth Test"], check=True)
    subprocess.run(["git", "-C", str(source), "commit", "-m", "source"], check=True, capture_output=True)
    sha = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True, capture_output=True, check=True
    ).stdout.strip()
    lifecycle.bind_dependency(target, source_metadata={"remote": str(source), "commit": sha})
    runtime = target / ".opencode" / "review-pack.json"
    runtime.parent.mkdir()
    runtime.write_text('{"version":"0.3.0","complete":true,"source":{"remote":null,"ref":null}}\n', encoding="utf-8")
    (runtime.parent / "opencode.json").write_text("{}\n", encoding="utf-8")

    app = ReviewPackApp(target, None)
    async with app.run_test(size=(120, 140)) as pilot:
        await pilot.pause()
        assert app.query_one("#check-update", Button).disabled
        assert app.query_one("#update", Button).disabled
        await pilot.click("#configure")
        await pilot.pause()
        assert isinstance(app.screen, ConfigScreen)
        dependency_switch = app.screen.query_one("#bind-dependency", Switch)
        assert dependency_switch.value is True
        await pilot.click("#bind-dependency")
        await pilot.click("#apply")
        for _ in range(20):
            await pilot.pause(0.1)
            if not isinstance(app.screen, ConfigScreen):
                break
        assert not lifecycle.dependency_status(target)["bound"]
        assert runtime.is_file()


@pytest.mark.asyncio
@pytest.mark.parametrize("size", [(48, 20), (80, 24), (120, 35)])
async def test_branded_console_is_operable_at_supported_sizes(tmp_path: Path, size: tuple[int, int]) -> None:
    repo = tmp_path / "target"
    init_repo(repo)
    app = CodeSleuthApp(repo, None)
    async with app.run_test(size=size) as pilot:
        await pilot.pause()
        assert app.query_one("#brand")
        assert app.query_one("#compact-brand")
        assert app.query_one("#security")
        assert app.query_one("#uninstall")
        assert {button.id.removeprefix("nav-") for button in app.query(".nav-button")} == set(NAV_SURFACES)
        compact = size[0] < 100 or size[1] < 30
        assert app.query_one("#compact-nav", Select).display is compact
        assert app.query_one("#wide-nav").display is not compact
        for control_id in ("configure", "smoke", "playbooks", "help", "launch"):
            control = app.query_one(f"#{control_id}", Button)
            assert control.region.x >= 0
            assert control.region.right <= size[0]
        await pilot.press("h")
        await pilot.pause()
        assert isinstance(app.screen, CodeSleuthHelpScreen)
        help_text = "\n".join(body for _, body in HELP_SECTIONS)
        assert "automated uninstaller yet" not in help_text
        assert "codesleuth-project --uninstall" in help_text


@pytest.mark.asyncio
async def test_navigation_routes_explain_existing_opencode_owned_surfaces(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    init_repo(repo)
    app = CodeSleuthApp(repo, None)
    async with app.run_test(size=(120, 35)) as pilot:
        for route in NAV_SURFACES:
            await pilot.click(f"#nav-{route}")
            await pilot.pause()
            rendered = str(app.query_one("#surface").render())
            assert NAV_SURFACES[route][0] in rendered
        assert "OpenCode execution" in NAV_SURFACES["review"][0]
        assert "does not run a second review engine" in NAV_SURFACES["review"][1]
        assert "OpenCode-native" in NAV_SURFACES["tools"][0]


@pytest.mark.asyncio
async def test_branded_configuration_keeps_dependency_control(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    init_repo(repo)
    app = CodeSleuthApp(repo, None)
    async with app.run_test(size=(120, 140)) as pilot:
        await pilot.click("#configure")
        await pilot.pause()
        assert isinstance(app.screen, CodeSleuthConfigScreen)
        assert app.screen.query_one("#bind-dependency", Switch)


@pytest.mark.asyncio
async def test_branded_configuration_is_operable_at_mobile_size(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    init_repo(repo)
    app = CodeSleuthApp(repo, None)
    async with app.run_test(size=(48, 20)) as pilot:
        app.query_one("#body").scroll_to_widget(app.query_one("#configure"), animate=False)
        await pilot.pause()
        await pilot.click("#configure")
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, CodeSleuthConfigScreen)
        assert screen.has_class("compact")
        for control_id in ("operation", "preset", "websearch", "webfetch", "edit", "external"):
            control = screen.query_one(f"#{control_id}")
            assert control.region.x >= 0
            assert control.region.right <= 48
        dialog = screen.query_one("#config-dialog")
        dialog.scroll_end(animate=False)
        await pilot.pause()
        apply = screen.query_one("#apply", Button)
        assert apply.region.x >= 0
        assert apply.region.right <= 48
