from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("textual")

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))
from review_pack_tui import ReviewPackApp, UninstallScreen  # noqa: E402


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
