#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Grid, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Checkbox, Footer, Header, Input, Label, RichLog, Select, Static, Switch

import codesleuth_project as project_lifecycle
from constants import AGENT_PROFILE_OPTIONS
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
    "review": ("playbooks", "launch"),
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
)

HELP_SECTIONS = [
    (
        "What CodeSleuth is",
        "CodeSleuth is the control panel, project-local configuration layer, catalog, and safe lifecycle manager around OpenCode. "
        "OpenCode and its models remain responsible for sessions, agents, tool calls, Skills, commands, and repository review execution.",
    ),
    (
        "Quick start",
        "1. Select a Git repository.\n"
        "2. Configure or install CodeSleuth.\n"
        "3. Run Verify after install/update.\n"
        "4. Open CodeSleuth to launch normal OpenCode execution with managed project-local defaults when applicable.\n"
        "5. Start with /repo-prompts for advice or /repo-review for a deep evidence-first review.",
    ),
    (
        "Skills, Playbooks, Tools, and Profiles",
        "Skill = reusable OpenCode capability/protocol. Playbook = task recipe for a concrete repository operation. "
        "Tool/plugin = OpenCode-native executable capability or integration. Profile = repository-specific detection/configuration metadata. "
        "CodeSleuth may discover and manage these surfaces, but OpenCode executes them.",
    ),
    (
        "Playbooks",
        "Playbooks are ready-to-run task recipes generated from the repository profile. "
        "They are intentionally not called Skills because they are prompts/command templates, not reusable OpenCode capabilities. "
        "Open Playbooks from this console, copy a useful recipe into OpenCode, or save the generated set to "
        ".opencode/state/tui/suggested-prompts.md (compatibility path retained for now).",
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
        "/repo-report          persist analysis under .codesleuth/reports/",
    ),
    (
        "Evidence and durable state",
        "Scout summaries are leads, not proof. Material findings are re-opened against exact current source and recorded with identity/provenance. "
        "Durable review checkpoints live under .opencode/state/. Analytical reports live under .codesleuth/reports/ (INDEX.md) for later sessions in this worktree; they stay local-only by default and are not automatically shared with fresh clones. "
        "OpenCode build writes those reports; CodeSleuth does not add a second supervisor.",
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


class CodeSleuthPlaybookScreen(PromptScreen):
    CSS = """
    CodeSleuthPlaybookScreen { align: center middle; background: rgba(0,0,0,0.58); }
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
            yield from self.compose_chrome("CodeSleuth Playbooks", title_id="prompt-title", abort_label="Close")
            yield Static(
                "Ready-to-run review task recipes generated from active repository profiles. "
                "Playbooks are prompts, not OpenCode Skills; OpenCode executes the selected recipe.",
                classes="hint",
            )
            yield RichLog(id="prompt-log", wrap=True, markup=True)
            with Horizontal(id="prompt-actions"):
                yield Button("Save playbooks", id="save-prompts", variant="primary")
                yield Button("Close", id="close-prompts")


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

                yield Label("6. Planned policy", classes="section")
                yield Static("", id="summary")
            with Horizontal(id="page-actions"):
                yield Button("Apply", id="apply", variant="primary")
                yield Button("Cancel", id="cancel")


class CodeSleuthApp(ReviewPackApp):
    TITLE = "CodeSleuth · Evidence Console"
    CSS = """
    Screen { background: #081018; color: #d8e3eb; }
    Header { background: #0e1822; color: #63d5f4; }
    Footer { background: #0e1822; color: #8aa7b8; }
    #body { padding: 1 2; }
    .hint { color: #71879a; }
    #workspace { height: auto; }
    #wide-nav { width: 18; min-width: 18; height: auto; margin-right: 2; padding: 1; border: round #29404f; background: #0e1822; }
    #wide-nav .nav-button { width: 100%; margin-bottom: 1; }
    #compact-nav { display: none; width: 100%; margin-bottom: 1; }
    #main-panel { width: 1fr; height: auto; }
    #brand { color: #63d5f4; height: 15; text-style: bold; }
    #compact-brand { display: none; color: #63d5f4; height: 1; text-style: bold; }
    #tagline { color: #8aa7b8; margin-bottom: 1; }
    #target { width: 100%; }
    #security { color: #f0c36a; margin: 1 0; }
    #surface { border-left: thick #3e718a; padding-left: 1; margin: 0 0 1 0; color: #d8e3eb; }
    #status { border: round #29404f; padding: 1; margin: 1 0; background: #0e1822; }
    #actions { grid-size: 5 1; grid-gutter: 0 1; height: 3; }
    #actions Button { width: 100%; min-width: 0; }
    #activity-title { color: #63d5f4; margin-top: 1; text-style: bold; }
    #log { height: 6; border: solid #29404f; background: #081018; }
    #workspace.compact { layout: vertical; }
    #workspace.compact #wide-nav { display: none; }
    #workspace.compact #compact-nav { display: block; }
    #workspace.compact #actions { grid-size: 2 3; height: 9; }
    """
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "configure", "Configure"),
        ("p", "playbooks", "Playbooks"),
        ("h", "help", "Help"),
        ("v", "verify", "Verify"),
        ("k", "check_updates", "Check Updates"),
        ("u", "uninstall", "Uninstall"),
        ("b", "toggle_brand", "Logo"),
        ("f2", "toggle_keys", "Keys"),
    ]

    def __init__(self, target: Path, distribution_root: Path | None) -> None:
        super().__init__(target, distribution_root)
        self.current_surface = "home"
        self.brand_visible = True
        self.keys_visible = True

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="body"):
            with Horizontal(id="workspace"):
                with Vertical(id="wide-nav"):
                    yield Static("CodeSleuth\nEvidence Console", classes="hint")
                    for route in NAV_SURFACES:
                        yield Button(route.title(), id=f"nav-{route}", classes="nav-button")
                with Vertical(id="main-panel"):
                    yield Select(
                        [(name.title(), name) for name in NAV_SURFACES],
                        value="home",
                        allow_blank=False,
                        id="compact-nav",
                    )
                    # The active navigation surface is intentionally first. Changing Review/Evidence/Tools/Settings
                    # must put the relevant context where the operator can see it without hunting below branding/status.
                    yield Static("", id="surface")
                    yield Static(CODESLEUTH_ART, id="brand")
                    yield Static("CODE:SLEUTH // EVIDENCE CONSOLE", id="compact-brand")
                    yield Static("Evidence-first repository intelligence", id="tagline")
                    yield Label("Repository")
                    yield Input(str(self.target), id="target")
                    yield Static("", id="status")
                    with Grid(id="actions"):
                        yield Button("Configure", id="configure", variant="primary")
                        yield Button("Verify", id="smoke")
                        yield Button("Check Updates", id="check-update")
                        yield Button("Update", id="update")
                        yield Button("Playbooks", id="playbooks")
                        yield Button("Help", id="help")
                        yield Button("Uninstall", id="uninstall", variant="error")
                        yield Button("Open CodeSleuth", id="launch", variant="primary")
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
        self.show_surface("home")
        self.write_ui_log("[dim]Console opened. No CodeSleuth control action has run in this session yet.[/dim]")

    def on_resize(self) -> None:
        if self.is_mounted:
            self._apply_responsive_layout()

    def _apply_responsive_layout(self) -> None:
        compact = self.size.width < 100 or self.size.height < 30
        self.query_one("#workspace").set_class(compact, "compact")
        self.query_one("#brand", Static).display = self.brand_visible and not compact
        self.query_one("#compact-brand", Static).display = self.brand_visible and compact
        self.query_one("#tagline", Static).display = self.brand_visible

    def action_toggle_brand(self) -> None:
        self.brand_visible = not self.brand_visible
        self._apply_responsive_layout()
        state = "shown" if self.brand_visible else "hidden"
        self.notify(f"Logo {state}")

    def action_toggle_keys(self) -> None:
        self.keys_visible = not self.keys_visible
        self.query_one("#keys", Footer).display = self.keys_visible
        if not self.keys_visible:
            self.notify("Keys hidden; press F2 to restore them")

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
        try:
            recent = sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)[:5]
        except OSError:
            recent = files[:5]
        recent_text = ", ".join(str(path.relative_to(repo)) for path in recent) or "no state files"
        return (
            "Durable state root: .opencode/state/ (OpenCode-owned)\n"
            f"State files visible: {len(files)}\n"
            f"Recent state: {recent_text}\n"
            "Resume/inspect through OpenCode commands; CodeSleuth only presents filesystem-visible state and provenance."
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
                "Playbooks are task recipes that route into the same OpenCode execution path."
            )
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
        if selector.value != route:
            selector.value = route
        self.query_one("#body", VerticalScroll).scroll_to_widget(surface, animate=False)

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
        if isinstance(self.screen, PromptScreen):
            return
        try:
            repo = self.validate_target()
            profiles = load_settings(repo, detect_profiles(repo))["profiles"]
            self.push_screen(CodeSleuthPlaybookScreen(repo, profiles))
        except Exception as exc:
            self.notify(str(exc), severity="error")

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
            self.run_source_checkout_action("check")
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
            self.run_source_checkout_action("update")
        else:
            self.run_runtime_action("update")

    def action_uninstall(self) -> None:
        self.query_one("#uninstall", Button).press()

    @work(thread=True, exclusive=False)
    def run_source_checkout_action(self, action: str) -> None:
        try:
            repo = self.validate_target()
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
            self.app.call_from_thread(self.refresh_status)
        except Exception as exc:
            self.app.call_from_thread(self.write_ui_log, f"[red]{action} failed: {exc}[/red]")
            self.app.call_from_thread(self.notify, f"{action} failed", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("nav-"):
            event.stop()
            self.show_surface(event.button.id.removeprefix("nav-"))
        elif event.button.id == "playbooks":
            event.stop()
            self.action_playbooks()
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
            self.show_surface(event.value)

    def _configured(self, changed: bool) -> None:
        if changed:
            self.refresh_status()
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
