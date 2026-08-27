from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("textual")

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))
from codesleuth_tui import CodeSleuthApp, CodeSleuthHelpPanel, NAV_SURFACES, PlaybookLoadWizard  # noqa: E402
from textual.containers import VerticalScroll  # noqa: E402
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
async def test_footer_can_be_collapsed_and_restored(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_committed_repo(repo)
    app = CodeSleuthApp(repo, None)

    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.pause()
        keys = app.query_one("#keys", Footer)
        assert keys.display

        await pilot.press("f2")
        await pilot.pause()
        assert not keys.display
        await pilot.press("f2")
        await pilot.pause()
        assert keys.display


@pytest.mark.asyncio
async def test_left_navigation_can_collapse_and_restore(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_committed_repo(repo)
    app = CodeSleuthApp(repo, None)

    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.pause()
        nav = app.query_one("#wide-nav")
        collapse = app.query_one("#nav-collapse")
        assert not nav.has_class("collapsed")

        assert await pilot.click("#nav-collapse")
        await pilot.pause()
        assert nav.has_class("collapsed")
        assert str(collapse.label) == ">"
        assert all(not button.display for button in app.query("#wide-nav .nav-button"))

        assert await pilot.click("#nav-collapse")
        await pilot.pause()
        assert not nav.has_class("collapsed")
        assert str(collapse.label) == "<"
        assert all(button.display for button in app.query("#wide-nav .nav-button"))


@pytest.mark.asyncio
async def test_right_key_panel_can_collapse_and_restore(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_committed_repo(repo)
    app = CodeSleuthApp(repo, None)

    async with app.run_test(size=(140, 40)) as pilot:
        await pilot.pause()
        app.action_show_help_panel()
        await pilot.pause()
        panel = app.query_one(CodeSleuthHelpPanel)
        assert not panel.has_class("collapsed")
        assert not panel.query("#right-close")

        assert await pilot.click("#right-collapse")
        await pilot.pause()
        assert panel.has_class("collapsed")
        assert str(panel.query_one("#right-collapse").label) == ">"

        assert await pilot.click("#right-collapse")
        await pilot.pause()
        assert not panel.has_class("collapsed")
        assert str(panel.query_one("#right-collapse").label) == "<"

        app.action_toggle_right_panel()
        await pilot.pause()
        assert panel.has_class("collapsed")
        app.action_toggle_right_panel()
        await pilot.pause()
        assert not panel.has_class("collapsed")
        assert app.query(CodeSleuthHelpPanel)


@pytest.mark.asyncio
async def test_left_nav_stays_outside_main_scroll(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_committed_repo(repo)
    app = CodeSleuthApp(repo, None)

    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.pause()
        assert app.query_one("#main-scroll", VerticalScroll)
        assert app.query_one("#wide-nav").parent.id == "workspace"
        assert app.query_one("#activity-panel")
        assert not app.query("#brand")


@pytest.mark.asyncio
@pytest.mark.parametrize("size", [(48, 20), (80, 24), (120, 35)])
async def test_active_navigation_surface_is_brought_to_top_of_viewport(tmp_path: Path, size: tuple[int, int], monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
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


ROOT = Path(__file__).resolve().parents[1]


def _assert_clickable(widget, width: int, height: int) -> None:
    assert widget.display
    assert widget.region.x >= 0
    assert widget.region.y >= 0
    assert widget.region.right <= width
    assert widget.region.bottom <= height
    assert widget.region.width > 0
    assert widget.region.height > 0


@pytest.mark.asyncio
@pytest.mark.parametrize("size", [(80, 24), (120, 35)])
async def test_playbooks_catalog_detail_and_wizard_abort_fit_viewport(
    tmp_path: Path, size: tuple[int, int], monkeypatch
) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_committed_repo(repo)
    app = CodeSleuthApp(repo, ROOT)
    async with app.run_test(size=size) as pilot:
        await pilot.pause()
        await pilot.click("#playbooks")
        await pilot.pause()
        assert app.current_surface == "playbooks"
        compact = size[0] < 100 or size[1] < 30
        if not compact:
            _assert_clickable(app.query_one("#nav-playbooks"), size[0], size[1])
        _assert_clickable(app.query_one("#load-playbook"), size[0], size[1])
        _assert_clickable(app.query_one("#copy-playbook"), size[0], size[1])
        _assert_clickable(app.query_one("#launch"), size[0], size[1])
        row = app.query_one("#pb-row-eha-sib-acceptance")
        _assert_clickable(row, size[0], size[1])
        await pilot.click("#pb-row-eha-sib-acceptance")
        await pilot.pause()
        detail = app.query_one("#playbooks-detail")
        assert detail.region.y >= 0
        assert detail.region.bottom <= size[1]
        chips = list(app.query(".skill-chip"))
        assert chips
        _assert_clickable(chips[0], size[0], size[1])

        await pilot.click("#load-playbook")
        await pilot.pause()
        assert isinstance(app.screen, PlaybookLoadWizard)
        abort = app.screen.query_one("#abort")
        _assert_clickable(abort, size[0], size[1])
        await pilot.click("#abort")
        await pilot.pause()
        assert not isinstance(app.screen, PlaybookLoadWizard)
        assert not (repo / ".opencode" / "playbooks").exists()


@pytest.mark.asyncio
async def test_source_checkout_update_fetches_origin_main_without_branch_tracking(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
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
        assert await pilot.click("#update")
        for _ in range(80):
            await pilot.pause(0.1)
            if git(source, "rev-parse", "HEAD").stdout.strip() == remote_head:
                break

    assert git(source, "rev-parse", "HEAD").stdout.strip() == remote_head
    assert git(source, "config", "branch.main.merge").stdout.strip() == "refs/heads/cursor/tui-page-abort-back"
