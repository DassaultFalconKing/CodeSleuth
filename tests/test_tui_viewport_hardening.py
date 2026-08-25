from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("textual")

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))
from codesleuth_tui import CodeSleuthApp, CodeSleuthHelpPanel, NAV_SURFACES  # noqa: E402
from textual.widgets import Footer, Static  # noqa: E402


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=check,
    )


def init_committed_repo(path: Path) -> None:
    path.mkdir()
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
    git(path, "config", "user.email", "test@example.invalid")
    git(path, "config", "user.name", "CodeSleuth Test")
    (path / "README.md").write_text("initial\n", encoding="utf-8")
    git(path, "add", "README.md")
    git(path, "commit", "-m", "initial")


@pytest.mark.asyncio
async def test_logo_and_keys_can_be_collapsed_and_restored(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    init_committed_repo(repo)
    app = CodeSleuthApp(repo, None)

    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.pause()
        brand = app.query_one("#brand", Static)
        tagline = app.query_one("#tagline", Static)
        keys = app.query_one("#keys", Footer)
        assert brand.display
        assert tagline.display
        assert keys.display

        await pilot.press("b")
        await pilot.pause()
        assert not brand.display
        assert not tagline.display

        await pilot.press("b")
        await pilot.pause()
        assert brand.display
        assert tagline.display

        await pilot.press("f2")
        await pilot.pause()
        assert not keys.display
        await pilot.press("f2")
        await pilot.pause()
        assert keys.display


@pytest.mark.asyncio
async def test_left_navigation_can_collapse_and_restore(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    init_committed_repo(repo)
    app = CodeSleuthApp(repo, None)

    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.pause()
        nav = app.query_one("#wide-nav")
        collapse = app.query_one("#nav-collapse")
        assert not nav.has_class("collapsed")

        # Prove the visible mouse control can collapse the rail.
        assert await pilot.click("#nav-collapse")
        await pilot.pause()
        assert nav.has_class("collapsed")
        assert str(collapse.label) == ">"
        assert all(not button.display for button in app.query("#wide-nav .nav-button"))

        # Restore through the documented parallel keyboard control. Headless Pilot mouse
        # hit-testing becomes geometry-dependent once a split rail is intentionally tiny.
        await pilot.press("f3")
        await pilot.pause()
        assert not nav.has_class("collapsed")
        assert str(collapse.label) == "<"
        assert all(button.display for button in app.query("#wide-nav .nav-button"))


@pytest.mark.asyncio
async def test_right_key_panel_can_collapse_restore_and_close_for_session(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    init_committed_repo(repo)
    app = CodeSleuthApp(repo, None)

    async with app.run_test(size=(140, 40)) as pilot:
        await pilot.pause()
        app.action_show_help_panel()
        await pilot.pause()
        panel = app.query_one(CodeSleuthHelpPanel)
        assert not panel.has_class("collapsed")

        # The visible side-panel control must collapse the panel.
        assert await pilot.click("#right-collapse")
        await pilot.pause()
        assert panel.has_class("collapsed")
        assert str(panel.query_one("#right-collapse").label) == ">"

        # F4 is the documented geometry-independent restore path.
        await pilot.press("f4")
        await pilot.pause()
        assert not panel.has_class("collapsed")
        assert str(panel.query_one("#right-collapse").label) == "<"

        assert await pilot.click("#right-close")
        await pilot.pause()
        assert not app.query(CodeSleuthHelpPanel)
        assert app.right_panel_closed

        app.action_show_help_panel()
        await pilot.pause()
        assert not app.query(CodeSleuthHelpPanel)


@pytest.mark.asyncio
@pytest.mark.parametrize("size", [(48, 20), (80, 24), (120, 35)])
async def test_active_navigation_surface_is_brought_to_top_of_viewport(tmp_path: Path, size: tuple[int, int]) -> None:
    repo = tmp_path / "target"
    init_committed_repo(repo)
    app = CodeSleuthApp(repo, None)

    async with app.run_test(size=size) as pilot:
        await pilot.pause()
        for route in NAV_SURFACES:
            app.show_surface(route)
            await pilot.pause()
            surface = app.query_one("#surface", Static)
            assert surface.region.y >= 0
            assert surface.region.y < size[1]
            assert surface.region.bottom > 0


@pytest.mark.asyncio
async def test_source_checkout_update_fetches_origin_main_without_branch_tracking(tmp_path: Path) -> None:
    source = tmp_path / "source"
    remote = tmp_path / "remote.git"
    writer = tmp_path / "writer"
    init_committed_repo(source)
    subprocess.run(["git", "init", "--bare", "-b", "main", str(remote)], check=True, capture_output=True)
    git(source, "remote", "add", "origin", str(remote))
    git(source, "push", "-u", "origin", "main")

    subprocess.run(["git", "clone", str(remote), str(writer)], check=True, capture_output=True)
    git(writer, "config", "user.email", "writer@example.invalid")
    git(writer, "config", "user.name", "Writer")
    (writer / "README.md").write_text("remote update\n", encoding="utf-8")
    git(writer, "commit", "-am", "remote update")
    git(writer, "push", "origin", "main")
    remote_head = git(writer, "rev-parse", "HEAD").stdout.strip()

    # Reproduce the user's stale-local-tracking failure. Ordinary `git pull` would try this deleted branch.
    git(source, "config", "branch.main.remote", "origin")
    git(source, "config", "branch.main.merge", "refs/heads/cursor/tui-page-abort-back")
    assert git(source, "rev-parse", "HEAD").stdout.strip() != remote_head

    app = CodeSleuthApp(source, source)
    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.pause()
        status = str(app.query_one("#status").render())
        assert "Update path: source checkout: origin/main" in status

        app.show_surface("tools")
        await pilot.pause()
        update = app.query_one("#update")
        assert update.display
        assert not update.disabled

        # The active Tools context is intentionally kept at the top; lifecycle buttons may
        # sit below a short viewport. Scroll the real button into view before exercising it.
        app.query_one("#body").scroll_to_widget(update, animate=False)
        await pilot.pause()
        assert await pilot.click("#update")
        for _ in range(80):
            await pilot.pause(0.1)
            if git(source, "rev-parse", "HEAD").stdout.strip() == remote_head:
                break

    assert git(source, "rev-parse", "HEAD").stdout.strip() == remote_head
    assert git(source, "config", "branch.main.merge").stdout.strip() == "refs/heads/cursor/tui-page-abort-back"
