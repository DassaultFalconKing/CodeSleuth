#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from textual import events, work
from textual.app import ComposeResult
from textual.containers import Grid, Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    HelpPanel,
    Input,
    KeyPanel,
    Label,
    Markdown,
    RichLog,
    Select,
    Static,
    Switch,
)

import codesleuth_project as project_lifecycle
from constants import AGENT_PROFILE_OPTIONS
from playbook_catalog import (
    PlaybookCatalogError,
    PlaybookRecord,
    discover_playbooks,
    inspect_playbook_source,
    install_playbook,
    known_skill_ids,
    pack_playbook_ids,
    skill_contract_excerpt,
    tool_purpose,
    unpack_workspace,
    validate_playbook_dir,
)
from review_pack_tui import AbortableModalScreen, ConfigScreen, PromptScreen, ReviewPackApp, launch_opencode
from review_pack_tui_core import (
    detect_profiles,
    installation_state,
    load_settings,
    recommended_operation,
)

PERMISSION_OPTIONS = [("Ask before use", "ask"), ("Allow", "allow"), ("Deny", "deny")]
PRESET_OPTIONS = [
    ("Review-safe (recommended)", "review-safe"),
    ("Balanced checks", "balanced"),
    ("Autonomous local work", "autonomous"),
]

CODESLEUTH_ART = r'''
+-------------------------------------------------+
|  CODE:SLEUTH // EVIDENCE OPERATIONS CONSOLE    |
+----------------------+--------------------------+
                       .-""""-.
                     .'  ____  '.
                    /   /_  _\   \
                   |   |o || o|   |
                   |   |__||__|   |
                   |      /\      |
                    \   .____.   /
                 ____'.\____/.'____
               .' ___/|  /\  |\___ '.
              /__/    | /  \ |    \__\
                   [ TARGET : SOURCE ]
                   [ EVIDENCE : LIVE ]
'''.strip("\n")

# Documentation identity only; the live TUI does not render brand chrome.
DOC_TAGLINE = "Evidence-first repository intelligence"

EVIDENCE_MARK = r"""+-- source --+     +-- evidence --+
| repository | --> | inspect     |
+------------+     +--------------+"""

NAV_SURFACES = {
    "home": (
        "Home · Evidence Console",
        "Repository readiness, active profiles/runtime policy, safe next action, and recent control-shell activity.",
    ),
    "review": (
        "Review · OpenCode execution",
        "Discover and invoke repository review commands and Playbooks. OpenCode owns the model session, agent loop, and review execution; CodeSleuth does not run a second review engine.",
    ),
    "playbooks": (
        "Playbooks · stored workflows",
        "Inspect installed overlay and pack Playbooks. Copy /playbook <id> or Open CodeSleuth; this console does not run Steps.",
    ),
    "evidence": (
        "Evidence · OpenCode state",
        "Inspect durable review state, findings/coverage hints, and checkpoint provenance where available. CodeSleuth only presents this state.",
    ),
    "tools": (
        "Tools · OpenCode-native capabilities",
        "Discover installed commands, Skills, tools/plugins, Verify, and update utilities. Execution remains OpenCode-native.",
    ),
    "settings": (
        "Settings · Project-local configuration",
        "Configure profiles, explicit evidence permissions, OpenCode runtime policy, and CodeSleuth lifecycle/dependency state.",
    ),
}

SURFACE_ACTIONS = {
    "home": ("configure", "smoke", "playbooks", "help", "launch"),
    "review": ("suggested-prompts", "launch"),
    "playbooks": ("load-playbook", "copy-playbook", "launch"),
    "evidence": ("help", "launch"),
    "tools": ("smoke", "check-update", "update", "launch"),
    "settings": ("configure", "uninstall"),
}

OPEN_CODE_COMMANDS = (
    "/repo-prompts",
    "/repo-profile",
    "/repo-review",
    "/repo-docs",
    "/repo-review-resume",
    "/repo-map",
    "/repo-contracts",
    "/eha-status",
)


def _rail_toggle_button(label: str, button_id: str, **kwargs) -> Button:
    """Collapse/restore controls must accept a second click immediately.

    Textual Button swallows clicks while the default 0.2s ``-active`` effect is
    applied, which makes a toggle appear stuck after a fast collapse->restore.
    """

    button = Button(label, id=button_id, compact=True, **kwargs)
    button.active_effect_duration = 0
    return button

HELP_SECTIONS = [
    (
        "What CodeSleuth is",
        "CodeSleuth is the control panel, project-local configuration layer, catalog, and safe lifecycle manager around OpenCode. "
        "OpenCode and its models remain responsible for sessions, agents, tool calls, Skills, commands, and repository review execution.",
    ),
    (
        "Quick start",
        "1. Point the Repository field at a Git root, or pick a host-tracked path.\n"
        "2. Configure or install CodeSleuth (self-install of this source checkout uses --self-install automatically).\n"
        "3. Run Verify after install/update.\n"
        "4. Open CodeSleuth to launch normal OpenCode execution with managed project-local defaults when applicable.\n"
        "5. Start with /repo-prompts for advice or /repo-review for a deep evidence-first review.\n"
        "6. Use /repo-map for bounded repository topology, /repo-contracts for protected impact, and /eha-status for exact-head lineage.\n"
        "7. List host-tracked repos anytime with codesleuth-project --list.",
    ),
    (
        "Self-install",
        "When the target is the CodeSleuth source checkout, install/update requires an explicit --self-install flag. "
        "The console passes that flag for you. --bind-dependency is invalid for self-install because it would create a "
        "recursive tools/codesleuth submodule. Ordinary project installs continue to use install.py <repo> with optional --bind-dependency.",
    ),
    (
        "Skills, Playbooks, Tools, and Profiles",
        "Skill = reusable OpenCode capability/protocol. Playbook = ordered/DAG orchestration of stored Steps. "
        "Tool/plugin = OpenCode-native executable capability or integration. Profile = repository-specific detection/configuration metadata. "
        "CodeSleuth may discover and manage these surfaces, but OpenCode executes them.",
    ),
    (
        "Playbooks",
        "The Playbooks surface lists stored workflows from .opencode/playbooks (overlay) and pack/.opencode/playbooks. "
        "Select a row to inspect steps, Skills, and declared tools. Copy /playbook <id> or Open CodeSleuth to run them; "
        "this console does not run Playbook Steps or load Skills. Suggested prompts remain under Review.",
    ),
    (
        "Agent profile",
        "Agent profile chooses an OpenCode model family so the native controller prompt is used: "
        "Codex models -> codex.txt, Claude -> anthropic.txt, Kimi/open-weight -> kimi.txt, otherwise OpenCode's default. "
        "It does not inject a CodeSleuth supervisor prompt. Setting agent.prompt on build would replace OpenCode's controller entirely.",
    ),
    (
        "OpenCode commands",
        "/repo-review          deep repository or PR review\n"
        "/repo-review-resume   continue from durable review state\n"
        "/repo-docs            evidence-first repository documentation\n"
        "/repo-profile         inspect/build repository profile\n"
        "/repo-prompts         in-OpenCode task advisor\n"
        "/repo-report          persist analysis under .codesleuth/reports/\n"
        "/repo-map             bounded repository graph + optional Mermaid\n"
        "/repo-contracts       protected impact + optional Mermaid\n"
        "/eha-status           exact-head campaign/repair lineage",
    ),
    (
        "Evidence and durable state",
        "Scout summaries are leads, not proof. Material findings are re-opened against exact current source and recorded with identity/provenance. "
        "Durable review checkpoints live under .opencode/state/. Analytical reports live under .codesleuth/reports/ (INDEX.md) for later sessions in this worktree; they stay local-only by default and are not automatically shared with fresh clones. "
        "Repository, protected-impact, and EHA Mermaid diagrams are bounded derived views of separate exact authorities; none is finding or acceptance evidence. "
        "OpenCode build writes reports; CodeSleuth does not add a second supervisor.",
    ),
    (
        "Permissions",
        "Review-safe is the recommended least-privilege preset. Web search/fetch, edits, external directories, "
        "and shell execution remain explicit policy choices. Destructive Git commands are denied or require confirmation according to the selected preset.",
    ),
    (
        "Verify and update",
        "Verify runs the installed smoke/integrity gate. Check Updates inspects the recorded source. "
        "For the CodeSleuth source checkout itself, Check Updates and Update explicitly fetch origin/main and never trust stale local branch tracking metadata. "
        "Installed targets continue to use their recorded safe update source and preserve locally modified managed files as conflicts rather than overwriting them.",
    ),
    (
        "Extension management",
        "Profiles, Skills, Playbooks, tools, plugins, and supported integrations may be added over time. "
        "CodeSleuth may provide discovery/install/update/remove UX, while execution after installation remains OpenCode-native.",
    ),
    (
        "Deinstallation",
        "Use the explicit Uninstall action or .opencode/bin/codesleuth-project --uninstall. "
        "Preserve archives known CodeSleuth settings/profile/review/TUI state; purge removes ordinary CodeSleuth traces/backups. "
        "Neither mode guesses at unrelated project reports or configuration. If a pre-existing file changed after installation, "
        "its current version stays in place and baseline/current recovery copies plus a conflict manifest remain under ignored "
        ".codesleuth/restore-conflicts/. Dependency binding is independent: --keep-dependency leaves dependency-only state, "
        "while codesleuth-project --unbind removes only the dependency. Compatibility filenames remain documented interfaces.",
    ),
]


class CodeSleuthSuggestedPromptsScreen(PromptScreen):
    CSS = """
    CodeSleuthSuggestedPromptsScreen { align: center middle; background: rgba(0,0,0,0.58); }
    #prompt-dialog { width: 92%; height: 88%; border: round #3e718a; background: #0e1822; padding: 1 2; }
    #page-chrome { height: 3; align: left middle; }
    #page-chrome Label { width: 1fr; height: auto; color: #63d5f4; text-style: bold; }
    #page-chrome Button { min-width: 8; width: auto; }
    #prompt-log { height: 1fr; border: solid #29404f; }
    #prompt-actions { height: auto; align-horizontal: right; margin-top: 1; }
    .hint { color: #71879a; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="prompt-dialog"):
            yield from self.compose_chrome("Suggested prompts", title_id="prompt-title", abort_label="Close")
            yield Static(
                "Profile-generated /repo-* recipes. Save writes suggested-prompts.md. "
                "Stored Playbooks live on the Playbooks surface and run through OpenCode /playbook.",
                classes="hint",
            )
            yield RichLog(id="prompt-log", wrap=True, markup=True)
            with Horizontal(id="prompt-actions"):
                yield Button("Save prompts", id="save-prompts", variant="primary")
                yield Button("Close", id="close-prompts")


WIZARD_PHASES = ("source", "inspect", "validate", "confirm", "result")


class PlaybookLoadWizard(AbortableModalScreen[bool]):
    CSS = """
    PlaybookLoadWizard { align: center middle; background: rgba(0,0,0,0.62); }
    #wizard-dialog { width: 92%; height: 88%; border: round #3e718a; background: #0e1822; padding: 1 2; }
    PlaybookLoadWizard.compact #wizard-dialog { width: 100%; height: 100%; padding: 1; }
    #page-chrome { height: 3; align: left middle; }
    #page-chrome Label { width: 1fr; height: auto; color: #63d5f4; text-style: bold; }
    #page-chrome Button { min-width: 8; width: auto; }
    #wizard-phase { color: #63d5f4; text-style: bold; }
    #wizard-body { height: 1fr; border: solid #29404f; padding: 1; }
    #wizard-source { width: 100%; }
    #wizard-actions { height: auto; align-horizontal: right; margin-top: 1; }
    .hint { color: #71879a; }
    .warning { color: #f0c36a; }
    """

    def abort_result(self) -> bool:
        return False

    def __init__(self, repo: Path, distribution_root: Path | None) -> None:
        super().__init__()
        self.repo = repo
        self.distribution_root = distribution_root
        self.phase = "source"
        self.source_path = ""
        self.record: PlaybookRecord | None = None
        self.package_dir: Path | None = None
        self.validation_text = ""
        self.can_install = False
        self.pack_collision = False
        self.overlay_exists = False
        self.result_text = ""
        self._unpack = unpack_workspace()

    def compose(self) -> ComposeResult:
        with Vertical(id="wizard-dialog"):
            yield from self.compose_chrome("Load playbook", title_id="wizard-title", abort_label="Abort")
            yield Static("Source → Inspect → Validate → Confirm → Result", id="wizard-phase")
            yield Static("", id="wizard-body")
            yield Input(placeholder="Local Playbook directory or .zip", id="wizard-source")
            with Horizontal(id="wizard-actions"):
                next_btn = Button("Next", id="wizard-next", variant="primary")
                next_btn.active_effect_duration = 0
                yield next_btn
                confirm = Button("Install", id="wizard-confirm", variant="primary")
                confirm.active_effect_duration = 0
                yield confirm
                close = Button("Close", id="wizard-close")
                close.active_effect_duration = 0
                yield close

    def on_mount(self) -> None:
        self.set_class(self.app.size.width < 80 or self.app.size.height < 24, "compact")
        self._render_phase()

    def on_unmount(self) -> None:
        self._unpack.cleanup()

    def _set_action_visibility(self) -> None:
        next_btn = self.query_one("#wizard-next", Button)
        confirm = self.query_one("#wizard-confirm", Button)
        close = self.query_one("#wizard-close", Button)
        source = self.query_one("#wizard-source", Input)
        if self.phase == "source":
            next_btn.display = True
            confirm.display = False
            close.display = False
            source.display = True
        elif self.phase in {"inspect", "validate"}:
            next_btn.display = True
            next_btn.disabled = self.phase == "validate" and not self.can_install
            confirm.display = False
            close.display = False
            source.display = False
        elif self.phase == "confirm":
            next_btn.display = False
            confirm.display = True
            close.display = False
            source.display = False
        else:
            next_btn.display = False
            confirm.display = False
            close.display = True
            source.display = False

    def _render_phase(self) -> None:
        body = self.query_one("#wizard-body", Static)
        phase = self.query_one("#wizard-phase", Static)
        labels = " → ".join(item.upper() if item == self.phase else item for item in WIZARD_PHASES)
        phase.update(labels)
        if self.phase == "source":
            body.update(
                "Choose a local Playbook folder (contains playbook.json) or a .zip. "
                "Remote registry install is not in this slice. Abort writes nothing."
            )
        elif self.phase == "inspect" and self.record is not None:
            step_lines = "\n".join(
                f"  {step.id} · {step.execution} · skills={', '.join(step.skills) or 'none'} · "
                f"tools={', '.join(step.tools) or 'none'}"
                for step in self.record.steps
            )
            body.update(
                f"id: {self.record.id}\n{self.record.description}\n"
                f"steps: {len(self.record.steps)}\n{step_lines}"
            )
        elif self.phase == "validate":
            body.update(self.validation_text)
        elif self.phase == "confirm":
            warnings = []
            if self.pack_collision:
                warnings.append(
                    f"Pack already has {self.record.id if self.record else 'this id'}. "
                    "Installing writes the overlay and shadows the pack copy. Confirm or Abort."
                )
            if self.overlay_exists:
                warnings.append("An overlay copy already exists and will be replaced if you confirm.")
            extra = "\n".join(warnings) or "Install into .opencode/playbooks/<id>/. This does not start /playbook."
            body.update(extra)
        else:
            body.update(self.result_text)
        self._set_action_visibility()

    def _advance_from_source(self) -> None:
        raw = (self.query_one("#wizard-source", Input).value or "").strip()
        if not raw:
            self.notify("Enter a Playbook directory or .zip", severity="error")
            return
        self.source_path = raw
        unpack = Path(self._unpack.name)
        try:
            self.record = inspect_playbook_source(Path(raw), unpack)
            self.package_dir = self.record.path
        except PlaybookCatalogError as exc:
            self.notify(str(exc), severity="error")
            return
        self.phase = "inspect"
        self._render_phase()

    def _advance_from_inspect(self) -> None:
        if self.package_dir is None:
            return
        skills = known_skill_ids(self.repo, self.distribution_root)
        report = validate_playbook_dir(self.package_dir, skill_ids=skills)
        lines = []
        if report.errors:
            lines.append("Errors:")
            lines.extend(f"  - {item}" for item in report.errors)
        if report.warnings:
            lines.append("Warnings:")
            lines.extend(f"  - {item}" for item in report.warnings)
        if report.ok:
            lines.append("Validation passed. Missing skills and empty tools[] are warnings only.")
        self.validation_text = "\n".join(lines) or "Validation passed."
        self.can_install = report.ok
        self.phase = "validate"
        self._render_phase()

    def _advance_from_validate(self) -> None:
        if not self.can_install or self.record is None:
            self.notify("Fix validation errors before installing", severity="error")
            return
        self.pack_collision = self.record.id in pack_playbook_ids(self.repo, self.distribution_root)
        overlay = self.repo / ".opencode" / "playbooks" / self.record.id
        self.overlay_exists = overlay.exists()
        self.phase = "confirm"
        self._render_phase()

    def _install(self) -> None:
        if self.record is None or self.package_dir is None or not self.can_install:
            return
        if self.pack_collision or self.overlay_exists:
            overwrite = True
        else:
            overwrite = False
        try:
            dest = install_playbook(
                self.package_dir,
                self.repo,
                overwrite=overwrite or self.overlay_exists,
                unpack_dir=Path(self._unpack.name),
            )
        except PlaybookCatalogError as exc:
            self.notify(str(exc), severity="error")
            return
        self.result_text = (
            f"Installed overlay copy at {dest}.\n"
            "Open CodeSleuth and run /playbook "
            f"{self.record.id}. This wizard does not start /playbook."
        )
        self.phase = "result"
        self._render_phase()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if self._abort_from_button(event):
            return
        if event.button.id == "wizard-next":
            event.stop()
            if self.phase == "source":
                self._advance_from_source()
            elif self.phase == "inspect":
                self._advance_from_inspect()
            elif self.phase == "validate":
                self._advance_from_validate()
        elif event.button.id == "wizard-confirm":
            event.stop()
            self._install()
        elif event.button.id == "wizard-close":
            event.stop()
            self.dismiss(self.phase == "result")


def compose_surface_operation() -> ComposeResult:
    with Vertical(id="operation"):
        yield Static("", id="surface")
        with Grid(id="actions"):
            yield Button("Configure", id="configure", variant="primary")
            yield Button("Verify", id="smoke")
            yield Button("Check Updates", id="check-update")
            yield Button("Update", id="update")
            yield Button("Playbooks", id="playbooks")
            yield Button("Load playbook", id="load-playbook")
            yield Button("Copy /playbook", id="copy-playbook")
            yield Button("Suggested prompts", id="suggested-prompts")
            yield Button("Help", id="help")
            yield Button("Uninstall", id="uninstall", variant="error")
            yield Button("Open CodeSleuth", id="launch", variant="primary")
        with Vertical(id="playbooks-panel"):
            with Horizontal(id="playbooks-body"):
                with VerticalScroll(id="playbooks-catalog"):
                    yield Static("No stored Playbooks discovered.", id="playbooks-empty")
                with VerticalScroll(id="playbooks-detail"):
                    yield Static("Select a Playbook to inspect its steps.", id="playbooks-detail-body")
                    yield Vertical(id="playbooks-steps")
                    yield Static("", id="chip-contract")


class CodeSleuthHelpScreen(AbortableModalScreen[None]):
    CSS = """
    CodeSleuthHelpScreen { align: center middle; background: rgba(0,0,0,0.62); }
    #help-dialog { width: 94%; height: 94%; border: round #3e718a; background: #0e1822; padding: 1 2; }
    #page-chrome { height: 3; align: left middle; }
    #page-chrome Label { width: 1fr; height: auto; color: #63d5f4; text-style: bold; }
    #page-chrome Button { min-width: 8; width: auto; }
    #help-subtitle { color: #71879a; margin-bottom: 1; }
    #help-log { height: 1fr; border: solid #29404f; background: #081018; }
    #help-actions { height: auto; align-horizontal: right; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            yield from self.compose_chrome("CodeSleuth Help", title_id="help-title", abort_label="Close")
            yield Static("Product model, OpenCode ownership, extensions, evidence, lifecycle, and safe operations.", id="help-subtitle")
            yield RichLog(id="help-log", wrap=True, markup=True)
            with Horizontal(id="help-actions"):
                yield Button("Close", id="close-help", variant="primary")

    def on_mount(self) -> None:
        log = self.query_one("#help-log", RichLog)
        for title, body in HELP_SECTIONS:
            log.write(f"[bold #63d5f4]{title}[/bold #63d5f4]\n{body}\n")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self._abort_from_button(event)


class CodeSleuthHelpPanel(HelpPanel):
    """Textual key/help side panel with explicit collapse and session-close controls."""

    DEFAULT_CSS = """
    CodeSleuthHelpPanel {
        split: right;
        width: 33%;
        min-width: 30;
        max-width: 60;
        border-left: vkey #8aa7b8 30%;
        padding: 0 1;
        height: 1fr;
        layout: vertical;
    }
    #right-panel-controls { height: 3; align-horizontal: right; }
    #right-panel-controls Button { min-width: 5; width: 5; margin-left: 1; }
    CodeSleuthHelpPanel #widget-help {
        height: auto;
        max-height: 50%;
        width: 1fr;
        padding: 1 0;
        margin-top: 1;
        display: none;
        background: #0e1822;
    }
    CodeSleuthHelpPanel.-show-help #widget-help { display: block; }
    CodeSleuthHelpPanel KeyPanel#keys-help {
        width: 1fr;
        height: 1fr;
        min-width: initial;
        split: initial;
        border-left: none;
        padding: 0;
    }
    CodeSleuthHelpPanel.collapsed {
        width: 8;
        min-width: 8;
        max-width: 8;
        padding: 0;
        overflow: hidden;
    }
    CodeSleuthHelpPanel.collapsed #widget-help,
    CodeSleuthHelpPanel.collapsed #keys-help { display: none; }
    CodeSleuthHelpPanel.collapsed #right-panel-controls { width: 100%; align-horizontal: center; }
    CodeSleuthHelpPanel.collapsed #right-collapse { width: 5; min-width: 5; max-width: 5; margin: 0; }
    """

    def compose(self) -> ComposeResult:
        with Horizontal(id="right-panel-controls"):
            yield _rail_toggle_button("<", "right-collapse")
        yield Markdown(id="widget-help")
        yield KeyPanel(id="keys-help")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "right-collapse":
            event.stop()
            self.app.action_toggle_right_panel()


class CodeSleuthConfigScreen(ConfigScreen):
    CSS = """
    CodeSleuthConfigScreen { align: center middle; background: rgba(0,0,0,0.58); }
    #config-dialog { width: 94%; height: 94%; border: round #3e718a; background: #0e1822; padding: 1 2; }
    #page-chrome { height: 3; align: left middle; }
    #page-chrome Label { width: 1fr; height: auto; color: #63d5f4; text-style: bold; }
    #page-chrome Button { min-width: 8; width: auto; }
    #page-body { height: 1fr; }
    #evidence-mark { color: #71879a; height: 3; margin-bottom: 1; }
    .section { margin-top: 1; color: #63d5f4; text-style: bold; }
    .hint { color: #71879a; }
    .row { height: auto; }
    Select { width: 38; }
    Input { width: 18; }
    #agent-model { width: 42; }
    #summary { border: solid #29404f; padding: 1; margin-top: 1; }
    #page-actions { height: auto; align-horizontal: right; margin-top: 1; }
    CodeSleuthConfigScreen.compact #config-dialog { width: 100%; height: 100%; padding: 1; }
    CodeSleuthConfigScreen.compact #page-chrome { height: auto; }
    CodeSleuthConfigScreen.compact .row { layout: vertical; height: auto; }
    CodeSleuthConfigScreen.compact Select { width: 100%; }
    CodeSleuthConfigScreen.compact Input { width: 100%; }
    CodeSleuthConfigScreen.compact #evidence-mark { display: none; }
    """

    def operation_options(self) -> tuple[list[tuple[str, str]], str]:
        if self.distribution_root is None:
            return [("Configure installed CodeSleuth", "configure")], "configure"
        if self.state == "versioned":
            return [("Update CodeSleuth + apply settings", "update"), ("Apply settings only", "configure")], "update"
        if self.state == "legacy-pack":
            return [("Adopt legacy review-pack with backup", "adopt"), ("Install without claiming old files", "install")], "adopt"
        return [("Install CodeSleuth / safe overlay", "install")], "install"

    def on_mount(self) -> None:
        super().on_mount()
        self._apply_responsive_layout()
        if project_lifecycle.is_self_target(self.repo, source_root=self.distribution_root):
            bind = self.query_one("#bind-dependency", Switch)
            bind.value = False
            bind.disabled = True

    def on_resize(self) -> None:
        if self.is_mounted:
            self._apply_responsive_layout()

    def _apply_responsive_layout(self) -> None:
        self.set_class(self.app.size.width < 80 or self.app.size.height < 24, "compact")

    def compose(self) -> ComposeResult:
        p = self.settings["permissions"]
        r = self.settings["runtime"]
        ops, selected_op = self.operation_options()
        with Vertical(id="config-dialog"):
            yield from self.compose_chrome("CodeSleuth Configuration", title_id="config-title")
            with VerticalScroll(id="page-body"):
                yield Static(EVIDENCE_MARK, id="evidence-mark")
                yield Static(f"Repository: {self.repo}\nInstallation state: {self.state}", classes="hint")

                yield Label("1. Installation", classes="section")
                yield Static(
                    "CodeSleuth currently targets OpenCode V1 stable. OpenCode V2 is beta and uses a different plugin API; "
                    "this control center will not silently migrate V1 plugins/configuration.",
                    classes="hint",
                )
                yield Static(
                    "Self-install: if this target is the CodeSleuth source checkout, Apply passes --self-install and "
                    "rejects --bind-dependency. Ordinary projects may bind tools/codesleuth independently of the runtime.",
                    classes="hint",
                )
                yield Select(ops, value=selected_op, allow_blank=False, id="operation")
                with Horizontal(classes="row"):
                    yield Switch(value=bool(self.dependency["bound"]), id="bind-dependency")
                    yield Label("Bind/unbind tools/codesleuth independently of the installed runtime")

                yield Label("2. Repository profile", classes="section")
                yield Static(
                    "Auto-detection uses tracked manifests/source. Switch to manual selection for mixed or unusual repositories.",
                    classes="hint",
                )
                yield Switch(value=self.settings.get("profilesMode") == "auto", id="profiles-auto")
                yield Label("Auto-detect profiles", classes="hint")
                with Horizontal(classes="row"):
                    for profile in ("generic", "rust", "python", "node", "typescript"):
                        yield Checkbox(profile, value=profile in self.settings["profiles"], id=f"profile-{profile}")

                yield Label("3. Agent profile", classes="section")
                yield Static(
                    "Chooses an OpenCode model family so native build controller behavior is used. "
                    "CodeSleuth never writes agent.build.prompt; that would replace OpenCode's provider prompt.",
                    classes="hint",
                )
                yield Select(
                    AGENT_PROFILE_OPTIONS,
                    value=self.settings.get("agent", {}).get("profile") or "native",
                    allow_blank=False,
                    id="agent-profile",
                )
                with Horizontal(classes="row"):
                    yield Label("OpenCode model id (optional)")
                    yield Input(str(self.settings.get("agent", {}).get("model") or ""), id="agent-model")

                yield Label("4. Evidence permissions", classes="section")
                yield Static(
                    "Review-safe is least-privilege. Web search/fetch can disclose queries and requested URLs to external services; "
                    "choose explicit consent behavior.",
                    classes="hint",
                )
                yield Select(PRESET_OPTIONS, value=p["preset"], allow_blank=False, id="preset")
                with Horizontal(classes="row"):
                    yield Label("websearch")
                    yield Select(PERMISSION_OPTIONS, value=p["websearch"], allow_blank=False, id="websearch")
                    yield Label("webfetch")
                    yield Select(PERMISSION_OPTIONS, value=p["webfetch"], allow_blank=False, id="webfetch")
                with Horizontal(classes="row"):
                    yield Label("edit/write")
                    yield Select(PERMISSION_OPTIONS, value=p["edit"], allow_blank=False, id="edit")
                    yield Label("external dirs")
                    yield Select(PERMISSION_OPTIONS, value=p["externalDirectory"], allow_blank=False, id="external")

                yield Label("5. Runtime", classes="section")
                yield Static(
                    "These controls write project-local OpenCode configuration. OpenCode remains the runtime and execution owner.",
                    classes="hint",
                )
                with Horizontal(classes="row"):
                    yield Switch(value=r["exaEnabled"], id="exa")
                    yield Label("Enable OpenCode Exa websearch runtime (OPENCODE_ENABLE_EXA=1)")
                with Horizontal(classes="row"):
                    yield Switch(value=r["watchdogEnabled"], id="watchdog")
                    yield Label("Enable OpenCode keepalive plugin managed by CodeSleuth")
                with Horizontal(classes="row"):
                    yield Label("Global stall seconds")
                    yield Input(str(r["stallSeconds"]), type="integer", id="stall")
                    yield Label("Web stall seconds")
                    yield Input(str(r["webStallSeconds"]), type="integer", id="web-stall")
                    yield Label("Max recoveries")
                    yield Input(str(r["maxStallRecoveries"]), type="integer", id="recoveries")
                with Horizontal(classes="row"):
                    yield Label("OpenCode compaction reserved tokens")
                    yield Input(str(r["compactionReserved"]), type="integer", id="reserved")
                    yield Switch(value=r["checkUpdatesOnStart"], id="check-updates")
                    yield Label("Check CodeSleuth upstream when console starts")

                yield Label("6. Repository policy", classes="section")
                with Horizontal(classes="row"):
                    yield Switch(
                        value=False
                        if self._self_install_target
                        else bool(self.settings.get("policy", {}).get("enforceAgentsMdRules", False)),
                        id="enforce-agents",
                        disabled=self._self_install_target,
                    )
                    yield Label("Maintain CodeSleuth workflow rules in root AGENTS.md")
                if self._self_install_target:
                    yield Static(
                        "Self-install: this switch is disabled. CodeSleuth will not rewrite the maintainer AGENTS.md.",
                        classes="hint",
                    )

                yield Label("7. Context graph provider", classes="section")
                yield Static(
                    "Builtin is the safe default. Graphify remains an optional derived provider and does not own canonical evidence.",
                    classes="hint",
                )
                yield Select(
                    [
                        ("Builtin exact-source mapping", "builtin"),
                        ("Graphify incubating (Ubuntu/Python 3.12 canonical)", "graphify"),
                    ],
                    value=self.settings.get("contextGraph", {}).get("provider") or "builtin",
                    allow_blank=False,
                    id="context-graph-provider",
                )

                yield Label("8. Planned policy", classes="section")
                yield Static("", id="summary")
            with Horizontal(id="page-actions"):
                yield Button("Apply", id="apply", variant="primary")
                yield Button("Cancel", id="cancel")


class CodeSleuthApp(ReviewPackApp):
    TITLE = "CodeSleuth"
    CSS = """
    Screen { background: #081018; color: #d8e3eb; }
    Header { background: #0e1822; color: #63d5f4; }
    Footer { background: #0e1822; color: #8aa7b8; }
    .hint { color: #71879a; }
    #workspace { height: 1fr; width: 100%; }
    #wide-nav { width: 18; min-width: 18; height: 1fr; margin: 1 0 1 2; padding: 1; border: round #29404f; background: #0e1822; }
    #nav-chrome { height: 3; width: 100%; }
    #nav-title { width: 1fr; }
    #nav-collapse { min-width: 5; width: 5; margin-left: 1; }
    #wide-nav .nav-button { width: 100%; margin-bottom: 0; height: 3; }
    #wide-nav.collapsed { width: 8; min-width: 8; max-width: 8; padding: 1 1; margin-right: 1; overflow: hidden; }
    #wide-nav.collapsed #nav-title,
    #wide-nav.collapsed .nav-button { display: none; }
    #wide-nav.collapsed #nav-chrome { width: 100%; align-horizontal: center; }
    #wide-nav.collapsed #nav-collapse { width: 5; min-width: 5; max-width: 5; margin: 0; }
    #main-scroll { width: 1fr; height: 1fr; padding: 1 2; }
    #compact-nav { display: none; width: 100%; margin-bottom: 1; }
    #main-panel { width: 1fr; height: auto; }
    #operation { height: auto; }
    #repo-row { height: auto; margin-bottom: 1; }
    #repo-row #target { width: 1fr; }
    #track-repo { min-width: 10; margin-left: 1; }
    #tracked-repos { width: 100%; margin-bottom: 1; }
    #security { color: #f0c36a; margin: 1 0; }
    #surface { border-left: thick #3e718a; padding-left: 1; margin: 0 0 1 0; color: #d8e3eb; }
    #playbooks-panel { display: none; height: 10; margin: 0 0 1 0; }
    #playbooks-panel.surface-visible { display: block; }
    #playbooks-body { height: 1fr; }
    #playbooks-catalog { width: 42%; height: 1fr; border: solid #29404f; background: #0e1822; padding: 0 1; }
    #playbooks-detail { width: 1fr; height: 1fr; border: solid #29404f; background: #0e1822; padding: 0 1; }
    .playbook-row { width: 100%; min-width: 0; margin: 0; height: 1; }
    .chip-row { height: auto; }
    .skill-chip, .tool-chip { min-width: 0; margin: 0 1 1 0; }
    #status { border: round #29404f; padding: 1; margin: 1 0; background: #0e1822; }
    #actions { grid-size: 5 1; grid-gutter: 0 1; height: 3; margin-bottom: 1; }
    #actions Button { width: 100%; min-width: 0; }
    #activity-panel { border: round #29404f; background: #0e1822; padding: 1; margin: 1 0; }
    #activity-title { color: #63d5f4; text-style: bold; margin-bottom: 1; }
    #log { height: 8; border: solid #29404f; background: #081018; }
    #workspace.compact { layout: vertical; height: auto; }
    #workspace.compact #wide-nav { display: none; }
    #workspace.compact #main-scroll { height: auto; max-height: 1fr; }
    #workspace.compact #compact-nav { display: block; }
    #workspace.compact #actions { grid-size: 5; height: auto; }
    #workspace.compact #playbooks-panel { height: 7; }
    #workspace.compact #playbooks-body { layout: vertical; }
    #workspace.compact #playbooks-catalog { width: 100%; height: 1fr; }
    #workspace.compact #playbooks-detail { width: 100%; height: 1fr; }
    #workspace.compact #playbooks-detail-body { display: none; }
    """
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "configure", "Configure"),
        ("p", "playbooks", "Playbooks"),
        ("h", "help", "Help"),
        ("v", "verify", "Verify"),
        ("k", "check_updates", "Check Updates"),
        ("u", "uninstall", "Uninstall"),
        ("f2", "toggle_keys", "Footer"),
        ("f3", "toggle_left_nav", "Left panel"),
        ("f4", "toggle_right_panel", "Right panel"),
    ]

    def __init__(self, target: Path, distribution_root: Path | None) -> None:
        super().__init__(target, distribution_root)
        self.current_surface = "home"
        self.keys_visible = True
        self.left_nav_collapsed = False
        self.right_panel_collapsed = False
        self.selected_playbook_id: str | None = None
        self._playbook_records: dict[str, PlaybookRecord] = {}
        self._syncing_nav = False
        self._detail_id: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="workspace"):
            with Vertical(id="wide-nav"):
                with Horizontal(id="nav-chrome"):
                    yield Static("Surfaces", id="nav-title", classes="hint")
                    yield _rail_toggle_button("<", "nav-collapse")
                for route in NAV_SURFACES:
                    yield Button(route.title(), id=f"nav-{route}", classes="nav-button")
            with VerticalScroll(id="main-scroll"):
                with Vertical(id="main-panel"):
                    yield Select(
                        [(name.title(), name) for name in NAV_SURFACES],
                        value="home",
                        allow_blank=False,
                        id="compact-nav",
                    )
                    # Surface copy and the actions for that surface stay together so Tools/Review
                    # controls are reachable without scrolling past status.
                    yield from compose_surface_operation()
                    yield Label("Repository")
                    with Horizontal(id="repo-row"):
                        yield Input(str(self.target), id="target")
                        yield Button("Remember", id="track-repo")
                    yield Select(
                        [],
                        id="tracked-repos",
                        prompt="Tracked repositories on this host…",
                        allow_blank=True,
                    )
                    yield Static("", id="status")
                    with Vertical(id="activity-panel"):
                        yield Static("Recent activity", id="activity-title")
                        yield RichLog(id="log", wrap=True, markup=True)
                    yield Static(
                        "Evidence may contain developer credentials visible to authorized tests/services. "
                        "Local state is ignored by default; inspect reports before sharing or committing them.",
                        id="security",
                    )
        yield Footer(id="keys")

    def on_mount(self) -> None:
        super().on_mount()
        self._apply_responsive_layout()
        self._refresh_tracked_repos()
        self.show_surface("home")
        self.write_ui_log("[dim]Console opened. No CodeSleuth control action has run in this session yet.[/dim]")

    def on_resize(self) -> None:
        if self.is_mounted:
            self._apply_responsive_layout()

    def _apply_responsive_layout(self) -> None:
        compact = self.size.width < 100 or self.size.height < 30
        self.query_one("#workspace").set_class(compact, "compact")

    def _tracked_select_options(self) -> list[tuple[str, str]]:
        options: list[tuple[str, str]] = []
        for entry in project_lifecycle.list_tracked_repositories(refresh=True):
            path = str(entry.get("path") or "")
            if not path:
                continue
            # list_tracked_repositories already pruned missing paths; degraded existing repos stay reachable or not but visible
            label = project_lifecycle.format_tracked_label(entry)
            options.append((label, path))
        return options

    def _refresh_tracked_repos(self) -> None:
        selector = self.query_one("#tracked-repos", Select)
        options = self._tracked_select_options()
        selector.set_options(options)
        current = Path(self.query_one("#target", Input).value or ".").expanduser().resolve()
        matched = next((value for _, value in options if Path(value).resolve() == current), None)
        if matched is not None:
            selector.value = matched
        else:
            selector.clear()

    def action_toggle_keys(self) -> None:
        self.keys_visible = not self.keys_visible
        self.query_one("#keys", Footer).display = self.keys_visible
        if not self.keys_visible:
            self.notify("Footer hidden; press F2 to restore it")

    def action_toggle_left_nav(self) -> None:
        self.left_nav_collapsed = not self.left_nav_collapsed
        nav = self.query_one("#wide-nav")
        nav.set_class(self.left_nav_collapsed, "collapsed")
        self.query_one("#nav-collapse", Button).label = ">" if self.left_nav_collapsed else "<"

    def action_show_help_panel(self) -> None:
        try:
            panel = self.screen.query_one(CodeSleuthHelpPanel)
        except NoMatches:
            panel = CodeSleuthHelpPanel()
            self.screen.mount(panel)
        panel.set_class(self.right_panel_collapsed, "collapsed")
        try:
            panel.query_one("#right-collapse", Button).label = ">" if self.right_panel_collapsed else "<"
        except NoMatches:
            pass

    def action_hide_help_panel(self) -> None:
        """Textual's normal hide action becomes a reversible collapse in CodeSleuth."""
        try:
            panel = self.screen.query_one(CodeSleuthHelpPanel)
        except NoMatches:
            return
        self.right_panel_collapsed = True
        panel.add_class("collapsed")
        panel.query_one("#right-collapse", Button).label = ">"

    def action_toggle_right_panel(self) -> None:
        try:
            panel = self.screen.query_one(CodeSleuthHelpPanel)
        except NoMatches:
            self.right_panel_collapsed = False
            self.action_show_help_panel()
            return
        self.right_panel_collapsed = not self.right_panel_collapsed
        panel.set_class(self.right_panel_collapsed, "collapsed")
        panel.query_one("#right-collapse", Button).label = ">" if self.right_panel_collapsed else "<"

    def action_track_repository(self) -> None:
        try:
            repo = self.validate_target()
        except Exception as exc:
            self.notify(str(exc), severity="error")
            return
        entry = project_lifecycle.record_tracked_repository(repo)
        self._refresh_tracked_repos()
        self.write_ui_log(f"[green]Tracked repository:[/green] {entry['path']}")
        self.notify("Repository remembered on this host")

    @staticmethod
    def _catalog_entries(root: Path, subdir: str) -> list[str]:
        directory = root / ".opencode" / subdir
        if not directory.is_dir():
            return []
        entries: list[str] = []
        for path in sorted(directory.iterdir(), key=lambda item: item.name.lower()):
            if path.name.startswith("."):
                continue
            entries.append(path.name if path.is_dir() else path.stem)
        return entries

    @staticmethod
    def _short_list(values: list[str], limit: int = 6) -> str:
        if not values:
            return "none discovered"
        shown = values[:limit]
        suffix = f" (+{len(values) - limit} more)" if len(values) > limit else ""
        return ", ".join(shown) + suffix

    def _plugin_entries(self, repo: Path) -> list[str]:
        config = repo / ".opencode" / "opencode.json"
        if not config.is_file():
            return []
        try:
            data = json.loads(config.read_text(encoding="utf-8"))
        except Exception:
            return []
        plugins: list[str] = []
        for entry in data.get("plugin") or []:
            package = entry[0] if isinstance(entry, list) and entry else entry
            if isinstance(package, str):
                plugins.append(package)
        return plugins

    def _evidence_state_summary(self, repo: Path) -> str:
        state_root = repo / ".opencode" / "state"
        if not state_root.is_dir():
            return (
                "Durable state: .opencode/state/ not present yet.\n"
                "OpenCode creates/uses review state when the invoked workflow needs it. "
                "Use /repo-review or /repo-review-resume in OpenCode; CodeSleuth does not create a parallel evidence store."
            )
        files = [path for path in state_root.rglob("*") if path.is_file()]
        context_graphs = list((state_root / "context-graphs").glob("*.json")) if (state_root / "context-graphs").is_dir() else []
        eha_ledgers = list((state_root / "reviews").glob("*/eha.ndjson")) if (state_root / "reviews").is_dir() else []
        try:
            recent = sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)[:5]
        except OSError:
            recent = files[:5]
        recent_text = ", ".join(str(path.relative_to(repo)) for path in recent) or "no state files"
        return (
            "Durable state root: .opencode/state/ (OpenCode-owned)\n"
            f"State files visible: {len(files)}\n"
            f"Derived repository projections: {len(context_graphs)}; authoritative EHA ledgers: {len(eha_ledgers)}\n"
            f"Recent state: {recent_text}\n"
            "Use /repo-map, /repo-contracts, or /eha-status for bounded derived diagrams. CodeSleuth only presents filesystem-visible state and provenance."
        )

    def _settings_summary(self, repo: Path) -> str:
        try:
            settings = load_settings(repo, detect_profiles(repo))
        except Exception as exc:
            return f"Settings unavailable: {exc}"
        permissions = settings["permissions"]
        runtime = settings["runtime"]
        return (
            f"Profiles: {', '.join(settings['profiles'])} ({settings.get('profilesMode', 'unknown')})\n"
            f"Permission preset: {permissions['preset']}\n"
            f"Evidence permissions: search={permissions['websearch']}, fetch={permissions['webfetch']}, "
            f"edit={permissions['edit']}, external={permissions['externalDirectory']}\n"
            f"OpenCode runtime: Exa={'on' if runtime['exaEnabled'] else 'off'}; "
            f"keepalive plugin={'on' if runtime['watchdogEnabled'] else 'off'}; "
            f"compaction reserved={runtime['compactionReserved']}"
        )

    def _surface_detail(self, route: str) -> str:
        title, detail = NAV_SURFACES[route]
        try:
            repo = self.validate_target()
        except Exception as exc:
            return f"[bold #63d5f4]{title}[/bold #63d5f4]\n{detail}\n\n[bold #f07178]Target error:[/bold #f07178] {exc}"

        if route == "home":
            extra = "Core actions stay intentionally small. Update/remove controls live under Tools/Settings when relevant."
        elif route == "review":
            extra = (
                "OpenCode commands:\n  " + "\n  ".join(OPEN_CODE_COMMANDS) + "\n"
                "Suggested prompts are profile-generated recipes. Stored Playbooks are on the Playbooks surface."
            )
        elif route == "playbooks":
            extra = "Overlay wins over pack. Chips inspect contracts only."
        elif route == "evidence":
            extra = self._evidence_state_summary(repo)
        elif route == "tools":
            commands = self._catalog_entries(repo, "commands")
            skills = self._catalog_entries(repo, "skills")
            tools = self._catalog_entries(repo, "tools")
            plugins = self._plugin_entries(repo)
            extra = (
                "Execution owner: OpenCode\n"
                f"Commands: {self._short_list(commands)}\n"
                f"Skills: {self._short_list(skills)}\n"
                f"Tools: {self._short_list(tools)}\n"
                f"Plugins: {self._short_list(plugins)}\n"
                "Verify/update below are CodeSleuth lifecycle utilities; installed commands/Skills/tools execute through OpenCode."
            )
        else:
            dependency = project_lifecycle.dependency_status(repo)
            extra = (
                self._settings_summary(repo)
                + "\n"
                + f"CodeSleuth dependency: {'pinned at ' + str(dependency['commit']) if dependency['bound'] else 'not pinned'}"
            )
        return f"[bold #63d5f4]{title}[/bold #63d5f4]\n{detail}\n\n{extra}"

    def show_surface(self, route: str) -> None:
        if route not in NAV_SURFACES:
            return
        self.current_surface = route
        surface = self.query_one("#surface", Static)
        surface.update(self._surface_detail(route))
        visible = set(SURFACE_ACTIONS[route])
        for button_id in {item for actions in SURFACE_ACTIONS.values() for item in actions}:
            self.query_one(f"#{button_id}", Button).display = button_id in visible
        for name in NAV_SURFACES:
            self.query_one(f"#nav-{name}", Button).variant = "primary" if name == route else "default"
        selector = self.query_one("#compact-nav", Select)
        self._syncing_nav = True
        try:
            if selector.value != route:
                selector.value = route
        finally:
            self._syncing_nav = False
        panel = self.query_one("#playbooks-panel")
        panel.set_class(route == "playbooks", "surface-visible")
        if route == "playbooks":
            self._refresh_playbooks_catalog()
        else:
            try:
                self.query_one("#copy-playbook", Button).disabled = True
            except NoMatches:
                pass
        self.query_one("#main-scroll", VerticalScroll).scroll_to_widget(
            self.query_one("#operation"), animate=False
        )

    def _source_checkout_root(self, repo: Path) -> Path | None:
        if self.distribution_root is None:
            return None
        proc = subprocess.run(
            ["git", "-C", str(self.distribution_root), "rev-parse", "--show-toplevel"],
            text=True,
            capture_output=True,
        )
        if proc.returncode != 0:
            return None
        root = Path(proc.stdout.strip()).resolve()
        return root if root == repo.resolve() else None

    @staticmethod
    def _has_origin(repo: Path) -> bool:
        proc = subprocess.run(
            ["git", "-C", str(repo), "remote", "get-url", "origin"],
            text=True,
            capture_output=True,
        )
        return proc.returncode == 0 and bool(proc.stdout.strip())

    def _source_checkout_update_mode(self, repo: Path) -> bool:
        root = self._source_checkout_root(repo)
        return root is not None and self._has_origin(root)

    def refresh_status(self) -> None:
        try:
            self.target = self.validate_target()
            profiles = detect_profiles(self.target)
            settings = load_settings(self.target, profiles)
            runtime = settings["runtime"]
            permissions = settings["permissions"]
            state = installation_state(self.target)
            meta_path = self.target / ".opencode" / "review-pack.json"
            version = "not installed"
            complete = None
            meta: dict = {}
            if meta_path.is_file():
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                version = str(meta.get("version") or "unknown")
                complete = bool(meta.get("complete"))
            operation = recommended_operation(self.target, self.distribution_root is not None)
            dependency = project_lifecycle.dependency_status(self.target)
            lifecycle = project_lifecycle.lifecycle_state(self.target)
            source = meta.get("source", {})
            source_checkout = self._source_checkout_update_mode(self.target)
            if dependency["bound"]:
                update_mode = "pinned: advance/revert the gitlink, then materialize that checkout"
            elif source_checkout:
                update_mode = "source checkout: origin/main"
            elif source.get("remote") and source.get("ref"):
                update_mode = f"floating: {source['remote']} {source['ref']}"
            else:
                update_mode = "unavailable: no explicit floating source ref"
            unavailable = update_mode.startswith("unavailable")
            self.query_one("#check-update", Button).disabled = dependency["bound"] or unavailable
            self.query_one("#update", Button).disabled = dependency["bound"] or unavailable
            readiness = "READY" if state == "versioned" and complete else ("ATTENTION" if state == "versioned" else "SETUP")
            readiness_markup = {
                "READY": "[bold #62d394]READY[/bold #62d394]",
                "ATTENTION": "[bold #f0c36a]ATTENTION[/bold #f0c36a]",
                "SETUP": "[bold #63d5f4]SETUP[/bold #63d5f4]",
            }[readiness]
            complete_text = "yes" if complete is True else ("no" if complete is False else "n/a")
            try:
                settings = load_settings(self.target, profiles)
                agent = settings.get("agent") or {}
                agent_model = agent.get("model") or "OpenCode current model"
                agent_line = f"Agent profile: {agent.get('profile', 'native')} ({agent_model})"
            except Exception:
                agent_line = "Agent profile: native (OpenCode current model)"
            self.query_one("#status", Static).update(
                f"{readiness_markup}  CodeSleuth {version}\n"
                f"Installation: {state}; lifecycle: {lifecycle}; complete: {complete_text}\n"
                f"Profiles: {', '.join(profiles)}\n"
                f"Runtime policy: permissions={permissions['preset']}; Exa={'on' if runtime['exaEnabled'] else 'off'}; "
                f"keepalive={'on' if runtime['watchdogEnabled'] else 'off'}\n"
                f"Dependency: {dependency['commit'] if dependency['bound'] else 'not pinned'}\n"
                f"Update path: {update_mode}\n"
                f"{agent_line}\n"
                f"Reports: .codesleuth/reports/\n"
                f"Next action: {operation}"
            )
            if self.is_mounted:
                self.show_surface(self.current_surface)
        except Exception as exc:
            self.query_one("#status", Static).update(f"[bold #f07178]ATTENTION[/bold #f07178]\n{exc}")

    def action_configure(self) -> None:
        if isinstance(self.screen, ConfigScreen):
            return
        try:
            repo = self.validate_target()
        except Exception as exc:
            self.notify(str(exc), severity="error")
            return
        self.push_screen(CodeSleuthConfigScreen(repo, self.distribution_root), self._configured)

    def action_playbooks(self) -> None:
        if isinstance(self.screen, AbortableModalScreen):
            return
        if self.current_surface == "playbooks":
            self.selected_playbook_id = None
            self._detail_id = None
        self.show_surface("playbooks")

    def action_suggested_prompts(self) -> None:
        if isinstance(self.screen, PromptScreen):
            return
        try:
            repo = self.validate_target()
            profiles = load_settings(repo, detect_profiles(repo))["profiles"]
            self.push_screen(CodeSleuthSuggestedPromptsScreen(repo, profiles))
        except Exception as exc:
            self.notify(str(exc), severity="error")

    def action_load_playbook(self) -> None:
        if isinstance(self.screen, AbortableModalScreen):
            return
        try:
            repo = self.validate_target()
        except Exception as exc:
            self.notify(str(exc), severity="error")
            return
        self.push_screen(PlaybookLoadWizard(repo, self.distribution_root), self._playbook_loaded)

    def action_copy_playbook(self) -> None:
        record = self._selected_playbook()
        if record is None:
            self.notify("Select a Playbook first", severity="warning")
            return
        self.copy_to_clipboard(record.playbook_command)
        self.notify(f"Copied {record.playbook_command}")

    def _playbook_loaded(self, changed: bool) -> None:
        if changed:
            self._refresh_playbooks_catalog()
            self.write_ui_log("[green]Playbook installed into overlay catalog.[/green]")

    def _selected_playbook(self) -> PlaybookRecord | None:
        if not self.selected_playbook_id:
            return None
        return self._playbook_records.get(self.selected_playbook_id)

    def _highlight_playbook_rows(self) -> None:
        for button in self.query(".playbook-row"):
            button.variant = "primary" if button.id == f"pb-row-{self.selected_playbook_id}" else "default"
        try:
            self.query_one("#copy-playbook", Button).disabled = self.selected_playbook_id is None
        except NoMatches:
            pass

    def _refresh_playbooks_catalog(self) -> None:
        try:
            repo = self.validate_target()
            records = discover_playbooks(repo, self.distribution_root)
        except Exception as exc:
            records = []
            self.notify(str(exc), severity="error")
        self._playbook_records = {record.id: record for record in records}
        if self.selected_playbook_id not in self._playbook_records:
            self.selected_playbook_id = None
        catalog = self.query_one("#playbooks-catalog", VerticalScroll)
        empty = self.query_one("#playbooks-empty", Static)
        empty.display = not records
        seen: set[str] = set()
        for record in records:
            widget_id = f"pb-row-{record.id}"
            seen.add(widget_id)
            alias = record.command_alias or "/playbook"
            label = f"{record.id} · {len(record.steps)} steps · {alias} · {record.origin}"
            try:
                button = self.query_one(f"#{widget_id}", Button)
                button.label = label
                button.display = True
            except NoMatches:
                button = Button(label, id=widget_id, classes="playbook-row", compact=True)
                catalog.mount(button)
        for button in list(catalog.query(".playbook-row")):
            if button.id not in seen:
                button.display = False
        compact = self.size.width < 100 or self.size.height < 30
        catalog.display = not (compact and self.selected_playbook_id)
        self._highlight_playbook_rows()
        self._render_playbook_detail()

    def _render_playbook_detail(self) -> None:
        body = self.query_one("#playbooks-detail-body", Static)
        steps_box = self.query_one("#playbooks-steps", Vertical)
        record = self._selected_playbook()
        if record is None:
            for child in steps_box.children:
                child.display = False
            body.update("Select a Playbook to inspect its steps.")
            self.query_one("#chip-contract", Static).update("")
            self._detail_id = None
            return
        body.update(
            f"{record.id}\n{record.description}\n"
            f"origin: {record.origin} · {record.command_alias or record.playbook_command}\n{record.summary}"
        )
        if self._detail_id == record.id and any(child.display for child in steps_box.children):
            return
        self._detail_id = record.id
        for child in steps_box.children:
            child.display = False
        for chip in steps_box.query(".skill-chip, .tool-chip"):
            chip.remove_class("skill-chip")
            chip.remove_class("tool-chip")
        first_chip: Button | None = None
        for step in record.steps:
            steps_box.mount(Static(f"{step.id} · {step.execution} · {step.isolation} · {step.output}", classes="hint"))
            row = Horizontal(classes="chip-row")
            steps_box.mount(row)
            for skill in step.skills:
                chip = Button(f"skill:{skill}", classes="skill-chip", compact=True)
                first_chip = first_chip or chip
                row.mount(chip)
            for tool in step.tools:
                chip = Button(f"tool:{tool}", classes="tool-chip", compact=True)
                first_chip = first_chip or chip
                row.mount(chip)
            if not step.skills and not step.tools:
                row.mount(Static("no declared skills/tools", classes="hint"))
        self.query_one("#chip-contract", Static).update("")
        if self.size.width >= 100 and self.size.height >= 30:
            self.query_one("#main-scroll", VerticalScroll).scroll_to_widget(
                self.query_one("#playbooks-detail"), animate=False
            )
        else:
            main_scroll = self.query_one("#main-scroll", VerticalScroll)
            self.call_after_refresh(main_scroll.scroll_home, animate=False)
            if first_chip is not None:
                detail = self.query_one("#playbooks-detail", VerticalScroll)
                self.call_after_refresh(detail.scroll_to_widget, first_chip, animate=False)

    def _show_chip_contract(self, button: Button) -> None:
        label = str(button.label)
        repo = self.target
        if label.startswith("skill:"):
            skill_id = label.split(":", 1)[1]
            text = skill_contract_excerpt(skill_id, repo, self.distribution_root)
        elif label.startswith("tool:"):
            text = tool_purpose(label.split(":", 1)[1])
        else:
            return
        try:
            self.query_one("#chip-contract", Static).update(text)
        except NoMatches:
            pass
        self.notify("Catalog chips do not invoke Skills or tools")

    def _select_playbook(self, playbook_id: str) -> None:
        self.selected_playbook_id = playbook_id
        compact = self.size.width < 100 or self.size.height < 30
        self.query_one("#playbooks-catalog").display = not compact
        self._highlight_playbook_rows()
        self._render_playbook_detail()

    def on_click(self, event: events.Click) -> None:
        if self.current_surface != "playbooks":
            return
        for row in self.query(".playbook-row"):
            if row.region.contains(event.screen_x, event.screen_y):
                event.stop()
                self._select_playbook(row.id.removeprefix("pb-row-"))
                return

    def action_help(self) -> None:
        if isinstance(self.screen, CodeSleuthHelpScreen):
            return
        self.push_screen(CodeSleuthHelpScreen())

    def action_verify(self) -> None:
        self.run_runtime_action("smoke")

    def action_check_updates(self) -> None:
        if self.query_one("#check-update", Button).disabled:
            return
        try:
            repo = self.validate_target()
        except Exception as exc:
            self.notify(str(exc), severity="error")
            return
        if self._source_checkout_update_mode(repo):
            self.run_source_checkout_action("check", repo)
        else:
            self.run_runtime_action("check")

    def action_update(self) -> None:
        if self.query_one("#update", Button).disabled:
            return
        try:
            repo = self.validate_target()
        except Exception as exc:
            self.notify(str(exc), severity="error")
            return
        if self._source_checkout_update_mode(repo):
            self.run_source_checkout_action("update", repo)
        else:
            self.run_runtime_action("update")

    def action_uninstall(self) -> None:
        self.query_one("#uninstall", Button).press()

    def run_source_checkout_action(self, action: str, repo: Path | None = None) -> bool:
        selected = repo if repo is not None else self._begin_runtime_action(action)
        if repo is not None:
            if self._runtime_action_active:
                self.write_ui_log(f"[yellow]{action} ignored: another lifecycle action is already running.[/yellow]")
                self.notify("A lifecycle action is already running", severity="warning")
                return False
            self._runtime_action_active = True
            for button_id in ("smoke", "check-update", "update", "uninstall"):
                matches = self.query(f"#{button_id}")
                if matches:
                    self.query_one(f"#{button_id}", Button).disabled = True
        if selected is None:
            return False
        self._run_source_checkout_action_worker(action, selected)
        return True

    @work(thread=True, exclusive=True)
    def _run_source_checkout_action_worker(self, action: str, repo: Path) -> None:
        try:
            source_root = self._source_checkout_root(repo)
            if source_root is None or not self._has_origin(source_root):
                raise RuntimeError("CodeSleuth source checkout is not bound to an origin remote")

            fetch = subprocess.run(
                [
                    "git",
                    "-C",
                    str(source_root),
                    "fetch",
                    "--prune",
                    "origin",
                    "+refs/heads/main:refs/remotes/origin/main",
                ],
                text=True,
                capture_output=True,
            )
            if fetch.returncode != 0:
                raise RuntimeError((fetch.stderr or fetch.stdout or "git fetch origin main failed").strip())

            local = subprocess.run(
                ["git", "-C", str(source_root), "rev-parse", "HEAD"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            upstream = subprocess.run(
                ["git", "-C", str(source_root), "rev-parse", "refs/remotes/origin/main"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            lines = [f"source checkout: {source_root}", f"local HEAD: {local}", f"origin/main: {upstream}"]
            if local == upstream:
                lines.append("CODESLEUTH SOURCE CURRENT")
            else:
                lines.append("CODESLEUTH SOURCE UPDATE AVAILABLE")

            if action == "update" and local != upstream:
                branch = subprocess.run(
                    ["git", "-C", str(source_root), "branch", "--show-current"],
                    text=True,
                    capture_output=True,
                    check=True,
                ).stdout.strip()
                if branch != "main":
                    raise RuntimeError(
                        f"source checkout update requires branch 'main'; current branch is {branch or 'detached HEAD'}"
                    )
                dirty = subprocess.run(
                    ["git", "-C", str(source_root), "status", "--porcelain", "--untracked-files=no"],
                    text=True,
                    capture_output=True,
                    check=True,
                ).stdout.strip()
                if dirty:
                    raise RuntimeError("source checkout has tracked local changes; refusing to update origin/main")
                merge = subprocess.run(
                    ["git", "-C", str(source_root), "merge", "--ff-only", "refs/remotes/origin/main"],
                    text=True,
                    capture_output=True,
                )
                if merge.returncode != 0:
                    raise RuntimeError((merge.stderr or merge.stdout or "fast-forward update failed").strip())
                lines.append((merge.stdout or "fast-forwarded to origin/main").strip())
                lines.append("Restart CodeSleuth to load the updated source checkout.")

            self.app.call_from_thread(self.write_ui_log, f"[green]{action}[/]:\n" + "\n".join(lines))
        except Exception as exc:
            self.app.call_from_thread(self.write_ui_log, f"[red]{action} failed: {exc}[/red]")
            self.app.call_from_thread(self.notify, f"{action} failed", severity="error")
        finally:
            self.app.call_from_thread(self._finish_runtime_action)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "nav-collapse":
            event.stop()
            self.action_toggle_left_nav()
        elif event.button.id and event.button.id.startswith("nav-"):
            event.stop()
            self.show_surface(event.button.id.removeprefix("nav-"))
        elif event.button.id == "track-repo":
            event.stop()
            self.action_track_repository()
        elif event.button.id == "playbooks":
            event.stop()
            self.action_playbooks()
        elif event.button.id == "suggested-prompts":
            event.stop()
            self.action_suggested_prompts()
        elif event.button.id == "load-playbook":
            event.stop()
            self.action_load_playbook()
        elif event.button.id == "copy-playbook":
            event.stop()
            self.action_copy_playbook()
        elif event.button.id and event.button.id.startswith("pb-row-"):
            event.stop()
            self._select_playbook(event.button.id.removeprefix("pb-row-"))
        elif event.button.has_class("skill-chip") or event.button.has_class("tool-chip"):
            event.stop()
            self._show_chip_contract(event.button)
        elif event.button.id == "help":
            event.stop()
            self.action_help()
        elif event.button.id == "check-update":
            event.stop()
            self.action_check_updates()
        elif event.button.id == "update":
            event.stop()
            self.action_update()
        else:
            super().on_button_pressed(event)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "compact-nav" and isinstance(event.value, str):
            if self._syncing_nav:
                return
            self.show_surface(event.value)
        elif event.select.id == "tracked-repos" and isinstance(event.value, str):
            self.query_one("#target", Input).value = event.value
            self.refresh_status()

    def _configured(self, changed: bool) -> None:
        if changed:
            self.refresh_status()
            self._refresh_tracked_repos()
            self.write_ui_log("[green]CodeSleuth configuration applied.[/green]")


def main() -> int:
    parser = argparse.ArgumentParser(description="CodeSleuth Evidence Console for repository review and runtime control")
    parser.add_argument("repo", nargs="?", help="target Git repository")
    parser.add_argument("--target", help="target Git repository (same as positional repo)")
    args = parser.parse_args()
    distribution = os.environ.get("REVIEW_PACK_DISTRIBUTION_ROOT")
    target = args.target or args.repo or os.environ.get("REVIEW_PACK_TARGET_ROOT") or "."
    app = CodeSleuthApp(Path(target), Path(distribution) if distribution else None)
    result = app.run()
    if result and result[0] == "launch":
        return launch_opencode(result[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
