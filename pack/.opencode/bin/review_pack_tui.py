#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TypeVar

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.screen import ModalScreen
from textual.worker import Worker
from textual.widgets import Button, Checkbox, Footer, Header, Input, Label, RichLog, Select, Static, Switch

import codesleuth_project as project_lifecycle
from review_pack_tui_core import (
    AGENT_PROFILE_OPTIONS,
    apply_settings_to_target,
    coerce_self_install_agents_policy,
    config_preview,
    default_settings,
    detect_profiles,
    generate_prompts,
    installation_state,
    load_settings,
    recommended_operation,
    settings_summary,
    validate_settings,
    write_prompts,
)

PERMISSION_OPTIONS = [("Ask before use", "ask"), ("Allow", "allow"), ("Deny", "deny")]
PRESET_OPTIONS = [
    ("Review-safe (recommended)", "review-safe"),
    ("Balanced checks", "balanced"),
    ("Autonomous local work", "autonomous"),
]
ABORT_BUTTON_IDS = frozenset({"abort", "cancel", "close-prompts", "close-help"})
TResult = TypeVar("TResult")


class AbortableModalScreen(ModalScreen[TResult]):
    """Modal page that can be left with no action applied or performed."""

    BINDINGS = [("escape", "abort", "Back")]

    def abort_result(self):
        return None

    def action_abort(self) -> None:
        self.dismiss(self.abort_result())

    def compose_chrome(self, title: str, *, title_id: str = "page-title", abort_label: str = "Back") -> ComposeResult:
        with Horizontal(id="page-chrome"):
            yield Button(abort_label, id="abort")
            yield Label(title, id=title_id)

    def _abort_from_button(self, event: Button.Pressed) -> bool:
        if event.button.id in ABORT_BUTTON_IDS:
            event.stop()
            self.action_abort()
            return True
        return False


class PromptScreen(AbortableModalScreen[None]):
    CSS = """
    PromptScreen { align: center middle; background: rgba(0,0,0,0.45); }
    #prompt-dialog { width: 92%; height: 88%; border: round $accent; background: $surface; padding: 1 2; }
    #page-chrome { height: 3; align: left middle; }
    #page-chrome Label { width: 1fr; height: auto; }
    #page-chrome Button { min-width: 8; width: auto; }
    #prompt-log { height: 1fr; border: solid $panel; }
    #prompt-actions { height: auto; align-horizontal: right; margin-top: 1; }
    """

    def __init__(self, repo: Path, profiles: list[str]) -> None:
        super().__init__()
        self.repo = repo
        self.prompts = generate_prompts(repo, profiles)

    def compose(self) -> ComposeResult:
        with Vertical(id="prompt-dialog"):
            yield from self.compose_chrome("Suggested CodeSleuth prompts")
            yield Static("Generated from the active profile set. /repo-prompts remains the in-OpenCode advisor.")
            yield RichLog(id="prompt-log", wrap=True, markup=True)
            with Horizontal(id="prompt-actions"):
                yield Button("Save to local repo state", id="save-prompts", variant="primary")
                yield Button("Close", id="close-prompts")

    def on_mount(self) -> None:
        log = self.query_one("#prompt-log", RichLog)
        for index, (title, prompt) in enumerate(self.prompts, 1):
            log.write(f"[bold]{index}. {title}[/bold]\n{prompt}\n")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if self._abort_from_button(event):
            return
        if event.button.id == "save-prompts":
            path = write_prompts(self.repo, self.prompts)
            self.notify(f"Saved to {path.relative_to(self.repo)}")


class UninstallScreen(AbortableModalScreen[str | None]):
    CSS = """
    UninstallScreen { align: center middle; background: rgba(0,0,0,0.45); }
    #uninstall-dialog { width: 82%; height: auto; border: round $error; background: $surface; padding: 1 2; }
    #page-chrome { height: 3; align: left middle; }
    #page-chrome Label { width: 1fr; height: auto; }
    #page-chrome Button { min-width: 8; width: auto; }
    #uninstall-actions { height: auto; align-horizontal: right; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="uninstall-dialog"):
            yield from self.compose_chrome("Remove CodeSleuth from this repository?")
            yield Static(
                "CodeSleuth restores the pre-install .opencode snapshot when available and removes its bound submodule. "
                "Preserve archives known CodeSleuth settings, profiles, review state and TUI state under .codesleuth/archive (gitignored). "
                "Purge deletes CodeSleuth traces/backups after a conflict-safe restore; unrelated project files are not archived or deleted. "
                "If a pre-existing file changed after installation, the worktree version wins and explicit recovery evidence is retained."
            )
            yield Static(
                "SECURITY: archived review evidence can contain development credentials or secrets. "
                "It stays gitignored by default; inspect it before sharing or force-adding it."
            )
            with Horizontal(id="uninstall-actions"):
                yield Button("Preserve traces", id="preserve", variant="warning")
                yield Button("Purge traces", id="purge", variant="error")
                yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "preserve":
            self.dismiss("preserve")
        elif event.button.id == "purge":
            self.dismiss("purge")
        elif self._abort_from_button(event):
            return


class ConfigScreen(AbortableModalScreen[bool]):
    CSS = """
    ConfigScreen { align: center middle; background: rgba(0,0,0,0.45); }
    #config-dialog { width: 94%; height: 94%; border: round $accent; background: $surface; padding: 1 2; }
    #page-chrome { height: 3; align: left middle; }
    #page-chrome Label { width: 1fr; height: auto; }
    #page-chrome Button { min-width: 8; width: auto; }
    #page-body { height: 1fr; }
    .section { margin-top: 1; color: $accent; text-style: bold; }
    .hint { color: $text-muted; }
    .warning { color: $warning; }
    .row { height: auto; }
    Select { width: 38; }
    Input { width: 18; }
    #agent-model { width: 36; }
    #summary { border: solid $panel; padding: 1; margin-top: 1; }
    #page-actions { height: auto; align-horizontal: right; margin-top: 1; }
    """

    def abort_result(self) -> bool:
        return False

    def __init__(self, repo: Path, distribution_root: Path | None) -> None:
        super().__init__()
        self.repo = repo
        self.distribution_root = distribution_root
        try:
            self.detected = detect_profiles(repo)
        except Exception:
            self.detected = ["generic"]
        try:
            self.settings = load_settings(repo, self.detected)
        except Exception:
            self.settings = default_settings(self.detected)
        self.state = installation_state(repo)
        self.dependency = project_lifecycle.dependency_status(repo)
        self._apply_worker: Worker[None] | None = None
        self._self_install_target = False
        if distribution_root is not None:
            self._self_install_target = project_lifecycle.is_self_target(repo, source_root=distribution_root)
        if not self._self_install_target:
            meta = repo / ".opencode" / "review-pack.json"
            if meta.is_file():
                try:
                    self._self_install_target = bool(json.loads(meta.read_text(encoding="utf-8")).get("selfInstall"))
                except json.JSONDecodeError:
                    self._self_install_target = False

    def operation_options(self) -> tuple[list[tuple[str, str]], str]:
        if self.distribution_root is None:
            return [("Configure installed CodeSleuth", "configure")], "configure"
        if self.state == "versioned":
            return [("Update CodeSleuth + apply settings", "update"), ("Apply settings only", "configure")], "update"
        if self.state == "legacy-pack":
            return [("Adopt legacy pack with backup", "adopt"), ("Overlay without claiming old files", "install")], "adopt"
        return [("Install / safe overlay", "install")], "install"

    def compose(self) -> ComposeResult:
        p = self.settings["permissions"]
        r = self.settings["runtime"]
        ops, selected_op = self.operation_options()
        with Vertical(id="config-dialog"):
            yield from self.compose_chrome("CodeSleuth Setup")
            with VerticalScroll(id="page-body"):
                yield Static(f"Target: {self.repo}\nCurrent state: {self.state}", classes="hint")
                yield Static(
                    "CodeSleuth backs up pre-existing project OpenCode settings before first install. "
                    "Local backups/review state are gitignored; tools/codesleuth is intentionally NOT ignored when pinned.",
                    classes="hint",
                )
                yield Static(
                    "Credential warning: OpenCode may legitimately use development credentials for local tests. "
                    "CodeSleuth does not blindly redact evidence, so reports may contain credentials or secrets. "
                    "Review before sharing or committing reports.",
                    classes="warning",
                )

                yield Label("1. Installation and persistence", classes="section")
                yield Select(ops, value=selected_op, allow_blank=False, id="operation")
                with Horizontal(classes="row"):
                    yield Switch(value=bool(self.dependency["bound"]), id="bind-dependency")
                    yield Label("Bind/unbind tools/codesleuth independently of the installed runtime")

                yield Label("2. Repository profile", classes="section")
                yield Switch(value=self.settings.get("profilesMode") == "auto", id="profiles-auto")
                yield Label("Auto-detect profiles", classes="hint")
                with Horizontal(classes="row"):
                    for profile in ("generic", "rust", "python", "node", "typescript"):
                        yield Checkbox(profile, value=profile in self.settings["profiles"], id=f"profile-{profile}")

                yield Label("3. Agent profile", classes="section")
                yield Static(
                    "Selects the OpenCode model family so the native build controller prompt is used. "
                    "CodeSleuth never sets agent.build.prompt; a custom prompt would replace OpenCode's controller.",
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

                yield Label("4. Permission policy", classes="section")
                yield Static("Profiles never widen project permissions. Permission changes come only from this explicit policy layer.", classes="hint")
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
                with Horizontal(classes="row"):
                    yield Switch(value=r["exaEnabled"], id="exa")
                    yield Label("Enable Exa websearch runtime")
                with Horizontal(classes="row"):
                    yield Switch(value=r["watchdogEnabled"], id="watchdog")
                    yield Label("Enable current OpenCode keepalive watchdog")
                with Horizontal(classes="row"):
                    yield Label("Global stall seconds")
                    yield Input(str(r["stallSeconds"]), type="integer", id="stall")
                    yield Label("Web stall seconds")
                    yield Input(str(r["webStallSeconds"]), type="integer", id="web-stall")
                    yield Label("Max recoveries")
                    yield Input(str(r["maxStallRecoveries"]), type="integer", id="recoveries")
                with Horizontal(classes="row"):
                    yield Label("Compaction reserved tokens")
                    yield Input(str(r["compactionReserved"]), type="integer", id="reserved")
                    yield Switch(value=r["checkUpdatesOnStart"], id="check-updates")
                    yield Label("Check updates on TUI start")

                yield Label("6. Repository policy", classes="section")
                with Horizontal(classes="row"):
                    yield Switch(
                        value=False if self._self_install_target else bool(self.settings.get("policy", {}).get("enforceAgentsMdRules", False)),
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
                    "Builtin is the safe default. Graphify is incubating, local-only, separately installed, and canonically enabled-tested on Ubuntu/Python 3.12.",
                    classes="hint",
                )
                yield Select(
                    [("Builtin exact-source mapping", "builtin"), ("Graphify incubating (Ubuntu/Python 3.12 canonical)", "graphify")],
                    value=self.settings.get("contextGraph", {}).get("provider") or "builtin",
                    allow_blank=False,
                    id="context-graph-provider",
                )

                yield Label("8. Planned policy", classes="section")
                yield Static("", id="summary")
            with Horizontal(id="page-actions"):
                yield Button("Apply", id="apply", variant="success")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self._sync_profile_controls()
        self._refresh_summary()

    def _select_value(self, widget_id: str) -> str:
        return str(self.query_one(widget_id, Select).value)

    def _collect(self) -> dict:
        auto = self.query_one("#profiles-auto", Switch).value
        if auto:
            profiles = self.detected
            mode = "auto"
        else:
            profiles = [
                p
                for p in ("generic", "rust", "python", "node", "typescript")
                if self.query_one(f"#profile-{p}", Checkbox).value
            ]
            mode = "manual"
        settings = {
            "schemaVersion": 1,
            "profiles": profiles,
            "profilesMode": mode,
            "permissions": {
                "preset": self._select_value("#preset"),
                "websearch": self._select_value("#websearch"),
                "webfetch": self._select_value("#webfetch"),
                "externalDirectory": self._select_value("#external"),
                "edit": self._select_value("#edit"),
                "question": "allow",
                "doomLoop": "ask",
                "managePolicy": True,
            },
            "runtime": {
                "exaEnabled": self.query_one("#exa", Switch).value,
                "watchdogEnabled": self.query_one("#watchdog", Switch).value,
                "stallSeconds": int(self.query_one("#stall", Input).value or 0),
                "webStallSeconds": int(self.query_one("#web-stall", Input).value or 0),
                "maxStallRecoveries": int(self.query_one("#recoveries", Input).value or 0),
                "compactionReserved": int(self.query_one("#reserved", Input).value or 0),
                "checkUpdatesOnStart": self.query_one("#check-updates", Switch).value,
            },
            "agent": {
                "profile": self._select_value("#agent-profile"),
                "model": (self.query_one("#agent-model", Input).value or "").strip(),
            },
            "policy": {
                "enforceAgentsMdRules": bool(self.query_one("#enforce-agents", Switch).value),
            },
            "contextGraph": {
                "provider": self._select_value("#context-graph-provider"),
            },
        }
        return coerce_self_install_agents_policy(validate_settings(settings), is_self=self._self_install_target)

    def _sync_profile_controls(self) -> None:
        auto = self.query_one("#profiles-auto", Switch).value
        for profile in ("generic", "rust", "python", "node", "typescript"):
            checkbox = self.query_one(f"#profile-{profile}", Checkbox)
            if auto:
                checkbox.value = profile in self.detected
            checkbox.disabled = auto or profile == "generic"

    def _refresh_summary(self) -> None:
        try:
            settings = self._collect()
            operation = self._select_value("#operation")
            bind = self.query_one("#bind-dependency", Switch).value
            text = (
                f"Operation: {operation}\nPinned dependency: {'yes' if bind else 'no'}\n"
                f"{settings_summary(settings)}\n\nConfig preview:\n{config_preview(settings)}"
            )
        except Exception as exc:
            text = f"Settings are not valid yet: {exc}"
        self.query_one("#summary", Static).update(text)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        if event.switch.id == "profiles-auto":
            self._sync_profile_controls()
        self._refresh_summary()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if not self.query_one("#profiles-auto", Switch).value:
            self._refresh_summary()

    def on_input_changed(self, event: Input.Changed) -> None:
        self._refresh_summary()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "preset":
            suggested = {
                "review-safe": ("ask", "ask", "ask", "ask"),
                "balanced": ("allow", "allow", "ask", "ask"),
                "autonomous": ("allow", "allow", "allow", "ask"),
            }.get(str(event.value))
            if suggested:
                for widget_id, value in zip(("#websearch", "#webfetch", "#edit", "#external"), suggested):
                    self.query_one(widget_id, Select).value = value
        self._refresh_summary()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if self._abort_from_button(event):
            return
        if event.button.id != "apply":
            return
        try:
            settings = self._collect()
        except Exception as exc:
            self.notify(str(exc), severity="error")
            return
        operation = self._select_value("#operation")
        bind_dependency = self.query_one("#bind-dependency", Switch).value
        self.query_one("#apply", Button).disabled = True
        self._apply_worker = self.perform_apply(settings, operation, bind_dependency)

    def _installed_source(self) -> dict | None:
        meta = self.repo / ".opencode" / "review-pack.json"
        if not meta.is_file():
            return None
        return json.loads(meta.read_text(encoding="utf-8")).get("source")

    @work(thread=True, exclusive=True)
    def perform_apply(self, settings: dict, operation: str, bind_dependency: bool) -> None:
        try:
            if operation == "configure":
                apply_settings_to_target(self.repo, settings, source_root=self.distribution_root)
                if bind_dependency and not project_lifecycle.dependency_status(self.repo)["bound"]:
                    project_lifecycle.bind_dependency(self.repo, source_metadata=self._installed_source())
                elif not bind_dependency and project_lifecycle.dependency_status(self.repo)["bound"]:
                    project_lifecycle.remove_dependency(self.repo)
                output = "Configured CodeSleuth."
            else:
                if self.distribution_root is None:
                    raise RuntimeError("distribution checkout is required for install/adopt/update")
                installer = self.distribution_root / "install.py"
                with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
                    json.dump(settings, handle, indent=2)
                    settings_path = Path(handle.name)
                try:
                    command = [sys.executable, str(installer), str(self.repo), "--settings-file", str(settings_path)]
                    for profile in settings["profiles"]:
                        command += ["--profile", profile]
                    if operation == "update":
                        command.append("--update")
                    elif operation == "adopt":
                        command.append("--adopt-existing-pack")
                    if bind_dependency:
                        command.append("--bind-dependency")
                    if project_lifecycle.is_self_target(self.repo, source_root=self.distribution_root):
                        command.append("--self-install")
                    result = subprocess.run(command, text=True, capture_output=True)
                    if result.returncode != 0:
                        raise RuntimeError((result.stderr or result.stdout or "installer failed").strip())
                    output = result.stdout.strip()
                finally:
                    settings_path.unlink(missing_ok=True)
                if not bind_dependency and project_lifecycle.dependency_status(self.repo)["bound"]:
                    project_lifecycle.remove_dependency(self.repo)
            actual_bound = bool(project_lifecycle.dependency_status(self.repo)["bound"])
            if actual_bound != bind_dependency:
                requested = "bound" if bind_dependency else "unbound"
                actual = "bound" if actual_bound else "unbound"
                raise RuntimeError(f"dependency transition did not complete: requested {requested}, observed {actual}")
            project_lifecycle.record_tracked_repository(self.repo)
            self.app.call_from_thread(self._apply_succeeded, output)
        except Exception as exc:
            self.app.call_from_thread(self._apply_failed, str(exc))

    def _apply_succeeded(self, output: str) -> None:
        self.notify(output[-1200:] or "Applied", severity="information")
        self.dismiss(True)

    def _apply_failed(self, message: str) -> None:
        self.notify(message, severity="error")
        self.query_one("#apply", Button).disabled = False


class ReviewPackApp(App[tuple[str, Path] | None]):
    TITLE = "CodeSleuth"
    CSS = """
    Screen { background: $background; }
    #body { padding: 1 2; }
    #target { width: 100%; }
    #status { border: round $panel; padding: 1; margin: 1 0; }
    #security { color: $warning; margin-bottom: 1; }
    #actions { height: auto; }
    #actions Button { margin-right: 1; }
    #log { height: 1fr; border: solid $panel; margin-top: 1; }
    """
    BINDINGS = [("q", "quit", "Quit"), ("c", "configure", "Configure"), ("p", "prompts", "Prompts")]

    def __init__(self, target: Path, distribution_root: Path | None) -> None:
        super().__init__()
        self.target = target.resolve()
        self.distribution_root = distribution_root.resolve() if distribution_root else None
        self._runtime_action_active = False

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="body"):
            yield Label("Target repository")
            yield Input(str(self.target), id="target")
            yield Static(
                "Reports/evidence may contain development credentials that OpenCode was allowed to use. "
                "CodeSleuth local state is gitignored by default; inspect before sharing or force-adding it.",
                id="security",
            )
            yield Static("", id="status")
            with Horizontal(id="actions"):
                yield Button("Configure / install", id="configure", variant="primary")
                yield Button("Smoke", id="smoke")
                yield Button("Check update", id="check-update")
                yield Button("Update", id="update")
                yield Button("Prompts", id="prompts")
                yield Button("Uninstall", id="uninstall", variant="error")
                yield Button("Launch OpenCode", id="launch", variant="success")
            yield RichLog(id="log", wrap=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_status()

    def current_target(self) -> Path:
        return Path(self.query_one("#target", Input).value or ".").expanduser().resolve()

    def validate_target(self) -> Path:
        repo = self.current_target()
        result = subprocess.run(["git", "-C", str(repo), "rev-parse", "--show-toplevel"], text=True, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(f"not a Git repository: {repo}")
        top = Path(result.stdout.strip()).resolve()
        if top != repo:
            repo = top
            self.query_one("#target", Input).value = str(repo)
        return repo

    def refresh_status(self) -> None:
        try:
            self.target = self.validate_target()
            profiles = detect_profiles(self.target)
            state = installation_state(self.target)
            meta_path = self.target / ".opencode" / "review-pack.json"
            version = "not installed"
            complete = "n/a"
            if meta_path.is_file():
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                version = str(meta.get("version") or "unknown")
                complete = str(bool(meta.get("complete")))
            operation = recommended_operation(self.target, self.distribution_root is not None)
            dependency = project_lifecycle.dependency_status(self.target)
            dep_text = f"{dependency['path']} @ {dependency['commit']}" if dependency["bound"] else "not pinned"
            lifecycle = project_lifecycle.lifecycle_state(self.target)
            source = meta.get("source", {}) if meta_path.is_file() else {}
            update_mode = "pinned: advance/revert the gitlink, then materialize that checkout" if dependency["bound"] else (
                "floating" if source.get("remote") and source.get("ref") else "unavailable: no explicit floating source ref"
            )
            pinned = dependency["bound"]
            self.query_one("#check-update", Button).disabled = pinned or update_mode.startswith("unavailable")
            self.query_one("#update", Button).disabled = pinned or update_mode.startswith("unavailable")
            backup = self.target / project_lifecycle.LOCAL_ROOT / "preinstall.json"
            self.query_one("#status", Static).update(
                f"State: {state}; lifecycle: {lifecycle}\nVersion: {version}; complete: {complete}\n"
                f"Dependency: {dep_text}\nUpdate path: {update_mode}\nPre-install backup: {'yes' if backup.is_file() else 'no'}\n"
                f"Detected profiles: {', '.join(profiles)}\nRecommended operation: {operation}"
            )
        except Exception as exc:
            self.query_one("#status", Static).update(str(exc))

    def write_ui_log(self, text: str) -> None:
        self.query_one("#log", RichLog).write(text)

    def action_configure(self) -> None:
        if isinstance(self.screen, ConfigScreen):
            return
        try:
            repo = self.validate_target()
        except Exception as exc:
            self.notify(str(exc), severity="error")
            return
        self.push_screen(ConfigScreen(repo, self.distribution_root), self._configured)

    def _configured(self, changed: bool) -> None:
        if changed:
            self.refresh_status()
            self.write_ui_log("[green]Configuration applied.[/green]")

    def action_prompts(self) -> None:
        if isinstance(self.screen, PromptScreen):
            return
        try:
            repo = self.validate_target()
            profiles = load_settings(repo, detect_profiles(repo))["profiles"]
            self.push_screen(PromptScreen(repo, profiles))
        except Exception as exc:
            self.notify(str(exc), severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button = event.button.id
        if button == "configure":
            event.stop()
            self.action_configure()
        elif button == "prompts":
            event.stop()
            self.action_prompts()
        elif button == "smoke":
            event.stop()
            self.run_runtime_action("smoke")
        elif button == "check-update":
            event.stop()
            self.run_runtime_action("check")
        elif button == "update":
            event.stop()
            self.run_runtime_action("update")
        elif button == "uninstall":
            event.stop()
            if isinstance(self.screen, UninstallScreen):
                return
            self.push_screen(UninstallScreen(), self._uninstall_choice)
        elif button == "launch":
            event.stop()
            try:
                repo = self.validate_target()
                launcher = repo / ".opencode" / "bin" / ("opencode-review.ps1" if os.name == "nt" else "opencode-review")
                if not launcher.is_file():
                    raise FileNotFoundError("CodeSleuth OpenCode launcher is not installed")
                self.exit(("launch", repo))
            except Exception as exc:
                self.notify(str(exc), severity="error")

    def _uninstall_choice(self, choice: str | None) -> None:
        if choice:
            repo = self._begin_runtime_action("uninstall")
            if repo is not None:
                self.perform_uninstall(choice, repo)

    @work(thread=True, exclusive=True)
    def perform_uninstall(self, choice: str, repo: Path) -> None:
        try:
            result = project_lifecycle.uninstall_project(repo, preserve_traces=choice == "preserve")
            self.app.call_from_thread(self.write_ui_log, f"[green]uninstall[/]:\n{json.dumps(result, indent=2)}")
        except Exception as exc:
            self.app.call_from_thread(self.write_ui_log, f"[red]uninstall failed: {exc}[/red]")
        finally:
            self.app.call_from_thread(self._finish_runtime_action)

    def _begin_runtime_action(self, action: str) -> Path | None:
        if self._runtime_action_active:
            self.write_ui_log(f"[yellow]{action} ignored: another lifecycle action is already running.[/yellow]")
            self.notify("A lifecycle action is already running", severity="warning")
            return None
        try:
            repo = self.validate_target()
        except Exception as exc:
            self.notify(str(exc), severity="error")
            return None
        self._runtime_action_active = True
        for button_id in ("smoke", "check-update", "update", "uninstall"):
            matches = self.query(f"#{button_id}")
            if matches:
                self.query_one(f"#{button_id}", Button).disabled = True
        return repo

    def _finish_runtime_action(self) -> None:
        self._runtime_action_active = False
        if not self.is_mounted:
            return
        try:
            for button_id in ("smoke", "check-update", "update", "uninstall"):
                matches = self.query(f"#{button_id}")
                if matches:
                    self.query_one(f"#{button_id}", Button).disabled = False
            self.refresh_status()
        except NoMatches:
            # A background subprocess may finish while Textual is dismantling
            # the screen. There is then no operator surface left to update.
            return

    def run_runtime_action(self, action: str) -> bool:
        repo = self._begin_runtime_action(action)
        if repo is None:
            return False
        self._run_runtime_action_worker(action, repo)
        return True

    @work(thread=True, exclusive=True)
    def _run_runtime_action_worker(self, action: str, repo: Path) -> None:
        try:
            ocbin = repo / ".opencode" / "bin"
            if action == "smoke":
                command = [sys.executable, str(ocbin / "review-pack-smoke.py"), str(repo)]
            elif action == "check":
                command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ocbin / "review-pack-update.ps1"), "--check"] if os.name == "nt" else [str(ocbin / "review-pack-update"), "--check"]
            elif action == "update":
                command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ocbin / "review-pack-update.ps1")] if os.name == "nt" else [str(ocbin / "review-pack-update")]
            else:
                raise ValueError(action)
            result = subprocess.run(command, text=True, capture_output=True)
            text = (result.stdout + ("\n" + result.stderr if result.stderr else "")).strip()
            prefix = "green" if result.returncode == 0 else "red"
            self.app.call_from_thread(self.write_ui_log, f"[{prefix}]{action}[/]:\n{text or '(no output)'}")
            if result.returncode != 0:
                self.app.call_from_thread(self.notify, f"{action} failed", severity="error")
        except Exception as exc:
            self.app.call_from_thread(self.write_ui_log, f"[red]{action} failed: {exc}[/red]")
        finally:
            self.app.call_from_thread(self._finish_runtime_action)


def launch_opencode(repo: Path) -> int:
    if os.name == "nt":
        return subprocess.call(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(repo / ".opencode" / "bin" / "opencode-review.ps1")], cwd=repo)
    return subprocess.call([str(repo / ".opencode" / "bin" / "opencode-review")], cwd=repo)


def main() -> int:
    parser = argparse.ArgumentParser(description="CodeSleuth interactive setup/control TUI")
    parser.add_argument("repo", nargs="?", help="target Git repository")
    parser.add_argument("--target", help="target Git repository (same as positional repo)")
    args = parser.parse_args()
    distribution = os.environ.get("REVIEW_PACK_DISTRIBUTION_ROOT")
    target = args.target or args.repo or os.environ.get("REVIEW_PACK_TARGET_ROOT") or "."
    app = ReviewPackApp(Path(target), Path(distribution) if distribution else None)
    result = app.run()
    if result and result[0] == "launch":
        return launch_opencode(result[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
