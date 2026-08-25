#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Footer, Header, Input, Label, RichLog, Select, Static, Switch

from review_pack_tui_core import (
    apply_settings_to_target,
    config_preview,
    default_settings,
    detect_profiles,
    generate_prompts,
    installation_state,
    load_settings,
    recommended_operation,
    save_settings,
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


class PromptScreen(ModalScreen[None]):
    CSS = """
    PromptScreen { align: center middle; background: rgba(0,0,0,0.45); }
    #prompt-dialog { width: 92%; height: 88%; border: round $accent; background: $surface; padding: 1 2; }
    #prompt-log { height: 1fr; border: solid $panel; }
    #prompt-actions { height: auto; align-horizontal: right; }
    """

    def __init__(self, repo: Path, profiles: list[str]) -> None:
        super().__init__()
        self.repo = repo
        self.prompts = generate_prompts(repo, profiles)

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="prompt-dialog"):
            yield Label("Suggested prompts for this repository")
            yield Static("Generated from the active profile set. /repo-prompts remains the in-OpenCode advisor.")
            yield RichLog(id="prompt-log", wrap=True, markup=True)
            with Horizontal(id="prompt-actions"):
                yield Button("Save to repo state", id="save-prompts", variant="primary")
                yield Button("Close", id="close-prompts")

    def on_mount(self) -> None:
        log = self.query_one("#prompt-log", RichLog)
        for index, (title, prompt) in enumerate(self.prompts, 1):
            log.write(f"[bold]{index}. {title}[/bold]\n{prompt}\n")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-prompts":
            path = write_prompts(self.repo, self.prompts)
            self.notify(f"Saved to {path.relative_to(self.repo)}")
        elif event.button.id == "close-prompts":
            self.dismiss(None)


class ConfigScreen(ModalScreen[bool]):
    CSS = """
    ConfigScreen { align: center middle; background: rgba(0,0,0,0.45); }
    #config-dialog { width: 94%; height: 94%; border: round $accent; background: $surface; padding: 1 2; }
    .section { margin-top: 1; color: $accent; text-style: bold; }
    .hint { color: $text-muted; }
    .row { height: auto; }
    Select { width: 38; }
    Input { width: 18; }
    #summary { border: solid $panel; padding: 1; margin-top: 1; }
    #actions { height: auto; align-horizontal: right; margin-top: 1; }
    """

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

    def operation_options(self) -> tuple[list[tuple[str, str]], str]:
        if self.distribution_root is None:
            return [("Configure installed pack only", "configure")], "configure"
        if self.state == "versioned":
            return [("Update pack + apply settings", "update"), ("Apply settings only", "configure")], "update"
        if self.state == "legacy-pack":
            return [("Adopt legacy pack with backup", "adopt"), ("Overlay without claiming old files", "install")], "adopt"
        return [("Install / safe overlay", "install")], "install"

    def compose(self) -> ComposeResult:
        p = self.settings["permissions"]
        r = self.settings["runtime"]
        ops, selected_op = self.operation_options()
        with VerticalScroll(id="config-dialog"):
            yield Label("Review Pack Setup")
            yield Static(f"Target: {self.repo}\nCurrent state: {self.state}", classes="hint")

            yield Label("1. Installation", classes="section")
            yield Static("This pack targets OpenCode V1 stable. OpenCode V2 is still beta and uses a different plugin API; the TUI will not silently migrate V1 plugins/configuration.", classes="hint")
            yield Select(ops, value=selected_op, allow_blank=False, id="operation")

            yield Label("2. Repository profile", classes="section")
            yield Static("Auto-detection uses tracked manifests/source. You can switch to manual selection for mixed or unusual repositories.", classes="hint")
            yield Switch(value=self.settings.get("profilesMode") == "auto", id="profiles-auto")
            yield Label("Auto-detect profiles", classes="hint")
            with Horizontal(classes="row"):
                for profile in ("generic", "rust", "python", "node", "typescript"):
                    yield Checkbox(profile, value=profile in self.settings["profiles"], id=f"profile-{profile}")

            yield Label("3. Permission policy", classes="section")
            yield Static("Review-safe is least-privilege. Web search/fetch can disclose queries and requested URLs to external services; choose explicit consent behavior.", classes="hint")
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

            yield Label("4. Runtime", classes="section")
            with Horizontal(classes="row"):
                yield Switch(value=r["exaEnabled"], id="exa")
                yield Label("Enable Exa websearch runtime (OPENCODE_ENABLE_EXA=1)")
            with Horizontal(classes="row"):
                yield Switch(value=r["watchdogEnabled"], id="watchdog")
                yield Label("Enable opencode-keepalive watchdog")
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
                yield Label("Check upstream when TUI starts")

            yield Label("5. Planned policy", classes="section")
            yield Static("", id="summary")
            with Horizontal(id="actions"):
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
            profiles = [p for p in ("generic", "rust", "python", "node", "typescript") if self.query_one(f"#profile-{p}", Checkbox).value]
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
        }
        return validate_settings(settings)

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
            text = f"Operation: {operation}\n{settings_summary(settings)}\n\nConfig preview:\n{config_preview(settings)}"
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
            preset = str(event.value)
            suggested = {
                "review-safe": ("ask", "ask", "ask", "ask"),
                "balanced": ("allow", "allow", "ask", "ask"),
                "autonomous": ("allow", "allow", "allow", "ask"),
            }.get(preset)
            if suggested:
                for widget_id, value in zip(("#websearch", "#webfetch", "#edit", "#external"), suggested):
                    self.query_one(widget_id, Select).value = value
        self._refresh_summary()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(False)
            return
        if event.button.id != "apply":
            return
        try:
            settings = self._collect()
        except Exception as exc:
            self.notify(str(exc), severity="error")
            return
        operation = self._select_value("#operation")
        self.query_one("#apply", Button).disabled = True
        self.perform_apply(settings, operation)

    @work(thread=True, exclusive=True)
    def perform_apply(self, settings: dict, operation: str) -> None:
        try:
            if operation == "configure":
                save_settings(self.repo, settings)
                apply_settings_to_target(self.repo, settings)
                output = "Configured installed review pack."
            else:
                if self.distribution_root is None:
                    raise RuntimeError("distribution checkout is required for install/adopt/update")
                installer = self.distribution_root / "install.py"
                if not installer.is_file():
                    raise RuntimeError(f"installer not found: {installer}")
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
                    result = subprocess.run(command, text=True, capture_output=True)
                    if result.returncode != 0:
                        raise RuntimeError((result.stderr or result.stdout or "installer failed").strip())
                    output = result.stdout.strip()
                finally:
                    settings_path.unlink(missing_ok=True)
            self.app.call_from_thread(self.notify, output[-1200:] or "Applied", severity="information")
            self.app.call_from_thread(self.dismiss, True)
        except Exception as exc:
            self.app.call_from_thread(self.notify, str(exc), severity="error")
            self.app.call_from_thread(setattr, self.query_one("#apply", Button), "disabled", False)


class ReviewPackApp(App[tuple[str, Path] | None]):
    TITLE = "OpenCode Repository Review Pack"
    CSS = """
    Screen { background: $background; }
    #body { padding: 1 2; }
    #target { width: 100%; }
    #status { border: round $panel; padding: 1; margin: 1 0; }
    #actions { height: auto; }
    #actions Button { margin-right: 1; }
    #log { height: 1fr; border: solid $panel; margin-top: 1; }
    """
    BINDINGS = [("q", "quit", "Quit"), ("c", "configure", "Configure"), ("p", "prompts", "Prompts")]

    def __init__(self, target: Path, distribution_root: Path | None) -> None:
        super().__init__()
        self.target = target.resolve()
        self.distribution_root = distribution_root.resolve() if distribution_root else None

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="body"):
            yield Label("Target repository")
            yield Input(str(self.target), id="target")
            yield Static("", id="status")
            with Horizontal(id="actions"):
                yield Button("Configure / install", id="configure", variant="primary")
                yield Button("Smoke", id="smoke")
                yield Button("Check update", id="check-update")
                yield Button("Update", id="update")
                yield Button("Prompts", id="prompts")
                yield Button("Launch OpenCode", id="launch", variant="success")
            yield RichLog(id="log", wrap=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_status()
        try:
            settings = load_settings(self.target, detect_profiles(self.target))
            if installation_state(self.target) == "versioned" and settings["runtime"]["checkUpdatesOnStart"]:
                self.run_action("check")
        except Exception:
            pass

    def current_target(self) -> Path:
        raw = self.query_one("#target", Input).value.strip()
        return Path(raw or ".").expanduser().resolve()

    def validate_target(self) -> Path:
        repo = self.current_target()
        result = subprocess.run(["git", "-C", str(repo), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        if result.returncode != 0:
            raise ValueError(f"Not a Git repository: {repo}")
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
            self.query_one("#status", Static).update(f"State: {state}\nVersion: {version}; complete: {complete}\nDetected profiles: {', '.join(profiles)}\nRecommended operation: {operation}")
        except Exception as exc:
            self.query_one("#status", Static).update(str(exc))

    def write_ui_log(self, text: str) -> None:
        self.query_one("#log", RichLog).write(text)

    def action_configure(self) -> None:
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
        try:
            repo = self.validate_target()
            profiles = load_settings(repo, detect_profiles(repo))["profiles"]
            self.push_screen(PromptScreen(repo, profiles))
        except Exception as exc:
            self.notify(str(exc), severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button = event.button.id
        if button == "configure":
            self.action_configure()
        elif button == "prompts":
            self.action_prompts()
        elif button == "smoke":
            self.run_action("smoke")
        elif button == "check-update":
            self.run_action("check")
        elif button == "update":
            self.run_action("update")
        elif button == "launch":
            try:
                repo = self.validate_target()
                launcher = repo / ".opencode" / "bin" / ("opencode-review.ps1" if os.name == "nt" else "opencode-review")
                if not launcher.is_file():
                    raise FileNotFoundError("review pack launcher is not installed")
                self.exit(("launch", repo))
            except Exception as exc:
                self.notify(str(exc), severity="error")

    @work(thread=True, exclusive=False)
    def run_action(self, action: str) -> None:
        try:
            repo = self.current_target()
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
            else:
                self.app.call_from_thread(self.refresh_status)
        except Exception as exc:
            self.app.call_from_thread(self.write_ui_log, f"[red]{action} failed: {exc}[/red]")


def launch_opencode(repo: Path) -> int:
    if os.name == "nt":
        return subprocess.call(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(repo / ".opencode" / "bin" / "opencode-review.ps1")], cwd=repo)
    return subprocess.call([str(repo / ".opencode" / "bin" / "opencode-review")], cwd=repo)


def main() -> int:
    parser = argparse.ArgumentParser(description="Interactive setup/control TUI for the OpenCode repository review pack")
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
