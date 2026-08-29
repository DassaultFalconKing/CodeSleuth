from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("textual")

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BIN))
import codesleuth_project as lifecycle  # noqa: E402
from review_pack_tui import ConfigScreen, ReviewPackApp, UninstallScreen  # noqa: E402
from codesleuth_tui import (  # noqa: E402
    HELP_SECTIONS,
    NAV_SURFACES,
    SURFACE_ACTIONS,
    CodeSleuthApp,
    CodeSleuthConfigScreen,
    CodeSleuthHelpScreen,
    CodeSleuthSuggestedPromptsScreen,
    PlaybookLoadWizard,
)
from textual.widgets import Button, Label, Select, Switch  # noqa: E402
from textual_sync import wait_for_screen_transition  # noqa: E402


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
        assert app.screen.query_one("#abort")
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
        dialog = app.screen.query_one("#config-dialog")
        dialog.scroll_end(animate=False)
        await pilot.pause()
        config_screen = app.screen
        await pilot.click("#apply")
        assert isinstance(config_screen, ConfigScreen)
        assert config_screen._apply_worker is not None
        await config_screen._apply_worker.wait()
        await pilot.pause()
        assert not isinstance(app.screen, ConfigScreen)
        assert not lifecycle.dependency_status(target)["bound"]
        assert runtime.is_file()


@pytest.mark.asyncio
@pytest.mark.parametrize("size", [(48, 20), (80, 24), (120, 35)])
async def test_console_is_operable_at_supported_sizes(tmp_path: Path, size: tuple[int, int], monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    app = CodeSleuthApp(repo, None)
    async with app.run_test(size=size) as pilot:
        await pilot.pause()
        assert app.query_one("#activity-panel")
        assert app.query_one("#activity-title")
        assert app.query_one("#tracked-repos", Select)
        assert app.query_one("#track-repo", Button)
        assert app.query_one("#security")
        assert {button.id.removeprefix("nav-") for button in app.query(".nav-button")} == set(NAV_SURFACES)
        compact = size[0] < 100 or size[1] < 30
        assert app.query_one("#compact-nav", Select).display is compact
        assert app.query_one("#wide-nav").display is not compact
        for control_id in SURFACE_ACTIONS["home"]:
            control = app.query_one(f"#{control_id}", Button)
            assert control.display
            assert control.region.x >= 0
            assert control.region.right <= size[0]
        for contextual_id in ("check-update", "update", "uninstall"):
            assert not app.query_one(f"#{contextual_id}", Button).display
        status = str(app.query_one("#status").render())
        assert "Runtime policy:" in status
        assert "Next action:" in status
        await pilot.press("h")
        await pilot.pause()
        assert isinstance(app.screen, CodeSleuthHelpScreen)
        help_text = "\n".join(body for _, body in HELP_SECTIONS)
        assert "control panel" in help_text
        assert "OpenCode executes them" in help_text
        assert "codesleuth-project --uninstall" in help_text
        assert "--self-install" in help_text
        assert "codesleuth-project --list" in help_text


@pytest.mark.asyncio
async def test_navigation_surfaces_expose_existing_opencode_owned_capabilities(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    oc = repo / ".opencode"
    (oc / "commands").mkdir(parents=True)
    (oc / "commands" / "repo-review.md").write_text("review\n", encoding="utf-8")
    (oc / "skills" / "repository-deep-review").mkdir(parents=True)
    (oc / "skills" / "repository-deep-review" / "SKILL.md").write_text("skill\n", encoding="utf-8")
    (oc / "tools").mkdir(parents=True)
    (oc / "tools" / "sample_tool.py").write_text("pass\n", encoding="utf-8")
    (oc / "state" / "review").mkdir(parents=True)
    (oc / "state" / "review" / "checkpoint.json").write_text("{}\n", encoding="utf-8")
    (oc / "opencode.json").write_text('{"plugin":["sample-plugin@1"]}\n', encoding="utf-8")

    app = CodeSleuthApp(repo, None)
    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.click("#nav-review")
        await pilot.pause()
        review = str(app.query_one("#surface").render())
        assert "/repo-review" in review
        assert "/repo-review-resume" in review
        assert "does not run a second review engine" in review
        assert app.query_one("#suggested-prompts", Button).display
        assert app.query_one("#launch", Button).display
        assert not app.query_one("#smoke", Button).display
        assert not app.query_one("#playbooks", Button).display

        await pilot.click("#nav-evidence")
        await pilot.pause()
        evidence = str(app.query_one("#surface").render())
        assert ".opencode/state/" in evidence
        assert "checkpoint.json" in evidence
        assert "OpenCode-owned" in evidence

        await pilot.click("#nav-tools")
        await pilot.pause()
        tools = str(app.query_one("#surface").render())
        assert "Execution owner: OpenCode" in tools
        assert "repo-review" in tools
        assert "repository-deep-review" in tools
        assert "sample_tool" in tools
        assert "sample-plugin@1" in tools
        assert app.query_one("#smoke", Button).display
        assert app.query_one("#check-update", Button).display
        assert app.query_one("#update", Button).display

        await pilot.click("#nav-settings")
        await pilot.pause()
        settings = str(app.query_one("#surface").render())
        assert "Permission preset:" in settings
        assert "OpenCode runtime:" in settings
        assert app.query_one("#configure", Button).display
        assert app.query_one("#uninstall", Button).display
        assert not app.query_one("#launch", Button).display


@pytest.mark.asyncio
async def test_branded_configuration_keeps_dependency_control_and_runtime_ownership(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    app = CodeSleuthApp(repo, None)
    async with app.run_test(size=(120, 140)) as pilot:
        await pilot.click("#configure")
        await pilot.pause()
        assert isinstance(app.screen, CodeSleuthConfigScreen)
        assert app.screen.query_one("#bind-dependency", Switch)
        labels = "\n".join(str(label.render()) for label in app.screen.query(Label))
        assert "OpenCode keepalive plugin managed by CodeSleuth" in labels
        assert "OpenCode compaction reserved tokens" in labels
        assert "CodeSleuth keepalive watchdog" not in labels


@pytest.mark.asyncio
async def test_branded_configuration_is_operable_at_mobile_size(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    app = CodeSleuthApp(repo, None)
    async with app.run_test(size=(48, 20)) as pilot:
        app.query_one("#main-scroll").scroll_to_widget(app.query_one("#configure"), animate=False)
        await pilot.pause()
        await pilot.pause()
        await pilot.click("#configure")
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, CodeSleuthConfigScreen)
        assert screen.has_class("compact")
        for control_id in ("operation", "preset", "websearch", "webfetch", "edit", "external", "agent-profile"):
            control = screen.query_one(f"#{control_id}")
            assert control.region.x >= 0
            assert control.region.right <= 48
        dialog = screen.query_one("#config-dialog")
        dialog.scroll_end(animate=False)
        await pilot.pause()
        apply = screen.query_one("#apply", Button)
        assert apply.region.x >= 0
        assert apply.region.right <= 48
        abort = screen.query_one("#abort", Button)
        assert abort.region.x >= 0
        assert abort.region.right <= 48
        assert abort.region.y >= 0
        assert abort.region.bottom <= 20


def _assert_visible_within(widget: Button, width: int, height: int) -> None:
    assert widget.region.x >= 0
    assert widget.region.y >= 0
    assert widget.region.right <= width
    assert widget.region.bottom <= height


@pytest.mark.asyncio
async def test_config_back_and_escape_abort_without_applying(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    settings_path = repo / ".opencode" / "review-pack-user.json"
    app = CodeSleuthApp(repo, None)
    async with app.run_test(size=(120, 140)) as pilot:
        await pilot.pause()
        await pilot.click("#configure")
        await pilot.pause()
        assert isinstance(app.screen, CodeSleuthConfigScreen)
        assert sum(isinstance(screen, ConfigScreen) for screen in app.screen_stack) == 1
        abort = app.screen.query_one("#abort", Button)
        _assert_visible_within(abort, 120, 140)
        await pilot.click("#bind-dependency")
        await pilot.click("#abort")
        await wait_for_screen_transition(pilot)
        assert not isinstance(app.screen, CodeSleuthConfigScreen)
        assert not settings_path.exists()

        await pilot.click("#configure")
        await wait_for_screen_transition(pilot)
        assert isinstance(app.screen, CodeSleuthConfigScreen)
        await pilot.click("#bind-dependency")
        await pilot.press("escape")
        await wait_for_screen_transition(pilot)
        assert not isinstance(app.screen, CodeSleuthConfigScreen)
        assert not settings_path.exists()

        await pilot.click("#configure")
        await wait_for_screen_transition(pilot)
        assert isinstance(app.screen, CodeSleuthConfigScreen)
        await pilot.click("#cancel")
        await wait_for_screen_transition(pilot)
        assert not isinstance(app.screen, CodeSleuthConfigScreen)
        assert not settings_path.exists()


@pytest.mark.asyncio
async def test_help_playbooks_and_uninstall_abort_without_performing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    app = CodeSleuthApp(repo, None)
    async with app.run_test(size=(120, 140)) as pilot:
        await pilot.pause()
        await pilot.click("#help")
        await wait_for_screen_transition(pilot)
        assert isinstance(app.screen, CodeSleuthHelpScreen)
        _assert_visible_within(app.screen.query_one("#abort", Button), 120, 140)
        await pilot.click("#abort")
        await wait_for_screen_transition(pilot)
        assert not isinstance(app.screen, CodeSleuthHelpScreen)

        await pilot.click("#playbooks")
        await pilot.pause()
        assert app.current_surface == "playbooks"
        assert not isinstance(app.screen, CodeSleuthSuggestedPromptsScreen)
        assert not isinstance(app.screen, PlaybookLoadWizard)
        _assert_visible_within(app.query_one("#load-playbook", Button), 120, 140)
        await pilot.press("escape")
        await pilot.pause()
        assert app.current_surface == "playbooks"
        assert not (repo / ".opencode" / "state" / "tui" / "suggested-prompts.md").exists()

        await pilot.click("#nav-settings")
        await pilot.pause()
        app.query_one("#main-scroll").scroll_to_widget(app.query_one("#uninstall"), animate=False)
        await pilot.pause()
        await pilot.click("#uninstall")
        await wait_for_screen_transition(pilot)
        assert isinstance(app.screen, UninstallScreen)
        _assert_visible_within(app.screen.query_one("#abort", Button), 120, 140)
        await pilot.click("#abort")
        await wait_for_screen_transition(pilot)
        assert not isinstance(app.screen, UninstallScreen)


@pytest.mark.asyncio
async def test_uninstall_abort_repeats_without_lifecycle_side_effects(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    uninstall_calls: list[object] = []

    def forbid_uninstall(self, *args: object, **kwargs: object) -> None:
        uninstall_calls.append((args, kwargs))
        raise AssertionError("uninstall must not run after abort")

    monkeypatch.setattr(ReviewPackApp, "perform_uninstall", forbid_uninstall)
    app = CodeSleuthApp(repo, None)
    async with app.run_test(size=(120, 140)) as pilot:
        await wait_for_screen_transition(pilot)
        await pilot.click("#nav-settings")
        await wait_for_screen_transition(pilot)
        app.query_one("#main-scroll").scroll_to_widget(app.query_one("#uninstall"), animate=False)
        await wait_for_screen_transition(pilot)
        for _ in range(5):
            await pilot.click("#uninstall")
            await wait_for_screen_transition(pilot)
            assert isinstance(app.screen, UninstallScreen)
            await pilot.click("#abort")
            await wait_for_screen_transition(pilot)
            assert not isinstance(app.screen, UninstallScreen)
    assert uninstall_calls == []
    assert not (repo / ".codesleuth" / "archive").exists()


@pytest.mark.asyncio
async def test_playbooks_surface_opens_catalog_not_suggested_prompts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    copied: list[str] = []
    launched: list[Path] = []
    monkeypatch.setattr(CodeSleuthApp, "copy_to_clipboard", lambda self, text: copied.append(text))
    monkeypatch.setattr("codesleuth_tui.launch_opencode", lambda repo: launched.append(repo))
    app = CodeSleuthApp(repo, ROOT)
    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.pause()
        await pilot.click("#playbooks")
        await pilot.pause()
        assert app.current_surface == "playbooks"
        assert app.query_one("#playbooks-panel").has_class("surface-visible")
        assert app.query_one("#pb-row-eha-sib-acceptance")
        assert not isinstance(app.screen, CodeSleuthSuggestedPromptsScreen)
        assert not (repo / ".opencode" / "state" / "tui" / "suggested-prompts.md").exists()

        await pilot.click("#pb-row-eha-sib-acceptance")
        await pilot.pause()
        detail = str(app.query_one("#playbooks-detail-body").render())
        assert "eha-sib-acceptance" in detail
        assert len(app._playbook_records["eha-sib-acceptance"].steps) == 6
        assert app.query(".skill-chip")
        await pilot.click(".skill-chip")
        await pilot.pause()
        assert launched == []
        assert copied == []

        await pilot.click("#copy-playbook")
        await pilot.pause()
        assert copied == ["/playbook eha-sib-acceptance"]


@pytest.mark.asyncio
async def test_suggested_prompts_remain_on_review_surface(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    app = CodeSleuthApp(repo, ROOT)
    async with app.run_test(size=(120, 140)) as pilot:
        await pilot.click("#nav-review")
        await pilot.pause()
        await pilot.click("#suggested-prompts")
        await wait_for_screen_transition(pilot)
        assert isinstance(app.screen, CodeSleuthSuggestedPromptsScreen)
        _assert_visible_within(app.screen.query_one("#abort", Button), 120, 140)
        labels = " ".join(str(button.label) for button in app.screen.query(Button))
        assert "Save prompts" in labels
        assert "Save playbooks" not in labels
        await pilot.press("escape")
        await wait_for_screen_transition(pilot)
        assert not isinstance(app.screen, CodeSleuthSuggestedPromptsScreen)
        assert not (repo / ".opencode" / "state" / "tui" / "suggested-prompts.md").exists()


@pytest.mark.asyncio
async def test_load_wizard_abort_writes_nothing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    app = CodeSleuthApp(repo, ROOT)
    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.pause()
        app.show_surface("playbooks")
        await pilot.pause()
        await pilot.click("#load-playbook")
        await wait_for_screen_transition(pilot)
        assert isinstance(app.screen, PlaybookLoadWizard)
        _assert_visible_within(app.screen.query_one("#abort", Button), 120, 35)
        await pilot.press("escape")
        await wait_for_screen_transition(pilot)
        assert not isinstance(app.screen, PlaybookLoadWizard)
        assert not (repo / ".opencode" / "playbooks").exists()


def _fixture_playbook(root: Path, playbook_id: str) -> Path:
    playbook_dir = root / playbook_id
    playbook_dir.mkdir(parents=True)
    (playbook_dir / "PLAYBOOK.md").write_text(f"# {playbook_id}\n\nfixture playbook\n", encoding="utf-8")
    (playbook_dir / "playbook.json").write_text(
        '{"schema_version": 1, "id": "%s", "description": "fixture", "steps": ['
        '{"id": "capture", "execution": "skill", "skill": "exact-target-identity",'
        ' "depends_on": [], "output": "target_identity", "isolation": "fresh_subagent"}]}'
        "\n" % playbook_id,
        encoding="utf-8",
    )
    return playbook_dir


@pytest.mark.asyncio
async def test_load_wizard_installs_overlay_without_starting_playbook(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    source = _fixture_playbook(tmp_path / "pkg", "sample-load")
    launched: list[object] = []
    monkeypatch.setattr("codesleuth_tui.launch_opencode", lambda target: launched.append(target))
    app = CodeSleuthApp(repo, ROOT)
    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.pause()
        app.show_surface("playbooks")
        await pilot.pause()
        await pilot.click("#load-playbook")
        await pilot.pause()
        wizard = app.screen
        assert isinstance(wizard, PlaybookLoadWizard)
        wizard.query_one("#wizard-source").value = str(source)
        await pilot.click("#wizard-next")
        await pilot.pause()
        assert wizard.phase == "inspect"
        await pilot.click("#wizard-next")
        await pilot.pause()
        assert wizard.phase == "validate"
        await pilot.click("#wizard-next")
        await pilot.pause()
        assert wizard.phase == "confirm"
        await pilot.click("#wizard-confirm")
        await pilot.pause()
        assert wizard.phase == "result"
        assert "does not start /playbook" in wizard.result_text
        await pilot.click("#wizard-close")
        await pilot.pause()
    assert (repo / ".opencode" / "playbooks" / "sample-load" / "playbook.json").is_file()
    assert launched == []


@pytest.mark.asyncio
async def test_load_wizard_pack_collision_requires_confirm(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "host-state"))
    repo = tmp_path / "target"
    init_repo(repo)
    source = tmp_path / "pkg" / "eha-repair"
    shutil.copytree(ROOT / "pack" / ".opencode" / "playbooks" / "eha-repair", source)
    app = CodeSleuthApp(repo, ROOT)
    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.pause()
        app.show_surface("playbooks")
        await pilot.pause()
        await pilot.click("#load-playbook")
        await pilot.pause()
        wizard = app.screen
        assert isinstance(wizard, PlaybookLoadWizard)
        wizard.query_one("#wizard-source").value = str(source)
        await pilot.click("#wizard-next")
        await pilot.pause()
        await pilot.click("#wizard-next")
        await pilot.pause()
        await pilot.click("#wizard-next")
        await pilot.pause()
        assert wizard.phase == "confirm"
        assert wizard.pack_collision is True
        body = str(wizard.query_one("#wizard-body").render())
        assert "Pack already has" in body
        await pilot.click("#abort")
        await wait_for_screen_transition(pilot)
        assert not isinstance(app.screen, PlaybookLoadWizard)
        assert not (repo / ".opencode" / "playbooks" / "eha-repair").exists()
