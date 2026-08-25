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
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Footer, Header, Input, Label, RichLog, Select, Static, Switch

from review_pack_tui import ConfigScreen, PromptScreen, ReviewPackApp, launch_opencode
from review_pack_tui_core import (
    apply_settings_to_target,
    config_preview,
    detect_profiles,
    installation_state,
    load_settings,
    recommended_operation,
    save_settings,
    settings_summary,
    validate_settings,
)

PERMISSION_OPTIONS = [("Ask before use", "ask"), ("Allow", "allow"), ("Deny", "deny")]
PRESET_OPTIONS = [
    ("Review-safe (recommended)", "review-safe"),
    ("Balanced checks", "balanced"),
    ("Autonomous local work", "autonomous"),
]

CODESLEUTH_ART = r"""
+-------------------------------------------------+
|  CODE:SLEUTH // EVIDENCE OPERATIONS CONSOLE    |
+----------------------+--------------------------+
                       .-\"\"\"\"-.
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
""".strip("\n")

EVIDENCE_MARK = r"""+-- source --+     +-- evidence --+
| repository | --> | verified    |
+------------+     +--------------+"""

HELP_SECTIONS = [
    (
        "What CodeSleuth is",
        "CodeSleuth is an evidence-first repository intelligence layer running on OpenCode. "
        "The TUI configures the project-local runtime; OpenCode remains the execution environment.",
    ),
    (
        "Quick start",
        "1. Select a Git repository.\n"
        "2. Configure or install CodeSleuth.\n"
        "3. Run Verify after install/update.\n"
        "4. Open CodeSleuth to launch OpenCode with the project-local CodeSleuth theme.\n"
        "5. Start with /repo-prompts for advice or /repo-review for a deep evidence-first review.",
    ),
    (
        "Skills",
        "A Skill is a reusable agent capability/protocol stored under .opencode/skills/. "
        "CodeSleuth currently ships the real OpenCode skill 'repository-deep-review'. "
        "The repo-reviewer agent loads it immediately and follows its inventory, architecture, "
        "evidence-ledger, checkpoint, context-discipline, and completion contracts. "
        "You normally use it through /repo-review or /repo-review-resume rather than invoking the skill manually.",
    ),
    (
        "Playbooks",
        "Playbooks are ready-to-run task recipes generated from the repository profile. "
        "They are intentionally not called Skills because they are prompts/command templates, not reusable OpenCode capabilities. "
        "Open Playbooks from this console, copy a useful recipe into OpenCode, or save the generated set to "
        ".opencode/state/tui/suggested-prompts.md (compatibility path retained for now).",
    ),
    (
        "OpenCode commands",
        "/repo-review          deep repository or PR review\n"
        "/repo-review-resume   continue from durable review state\n"
        "/repo-docs            evidence-first repository documentation\n"
        "/repo-profile         inspect/build repository profile\n"
        "/repo-prompts         in-OpenCode task advisor",
    ),
    (
        "Evidence and durable state",
        "Scout summaries are leads, not proof. Material findings are re-opened against exact current source and recorded with identity/provenance. "
        "Durable review checkpoints live under .opencode/state/ so work can survive compaction or resume without pretending conversation history is project truth.",
    ),
    (
        "Permissions",
        "Review-safe is the recommended least-privilege preset. Web search/fetch, edits, external directories, "
        "and shell execution remain explicit policy choices. Destructive Git commands are denied or require confirmation according to the selected preset.",
    ),
    (
        "Verify and update",
        "Verify runs the installed smoke gate. Check Updates inspects the recorded source. Update uses the safe updater: "
        "unchanged managed files may be replaced, locally modified managed files are preserved and incoming versions are written under "
        ".opencode/state/update-conflicts/.",
    ),
    (
        "Deinstallation",
        "There is no automated uninstaller yet. Do not delete the whole .opencode directory unless it belongs only to CodeSleuth.\n"
        "Safe manual removal:\n"
        "1. Stop CodeSleuth/OpenCode and preserve any review checkpoints you care about.\n"
        "2. Open .opencode/review-pack.json and use managedFiles as the authoritative CodeSleuth-owned file list.\n"
        "3. Remove only managed files whose current content still matches the recorded managed hash; preserve locally modified files for manual review.\n"
        "4. If .opencode/state/installer-backups/opencode.json.before-pack exists and is the desired pre-CodeSleuth config, restore it. Otherwise edit opencode.json manually; do not blindly delete a shared OpenCode config.\n"
        "5. Remove review-pack.json and review-pack-user.json after the managed files/config are handled.\n"
        "6. Remove .opencode/state/ only if you no longer need checkpoints, backups, logs, or conflict evidence.\n"
        "Compatibility filenames still use review-pack* until a separate migration changes those contracts.",
    ),
]


class CodeSleuthPlaybookScreen(PromptScreen):
    CSS = """
    CodeSleuthPlaybookScreen { align: center middle; background: rgba(0,0,0,0.58); }
    #prompt-dialog { width: 92%; height: 88%; border: round #31566a; background: #0e1822; padding: 1 2; }
    #prompt-title { color: #63d5f4; text-style: bold; }
    #prompt-log { height: 1fr; border: solid #29404f; }
    #prompt-actions { height: auto; align-horizontal: right; }
    .hint { color: #8298a9; }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="prompt-dialog"):
            yield Label("CodeSleuth Playbooks", id="prompt-title")
            yield Static(
                "Ready-to-run review task recipes generated from active repository profiles. "
                "Playbooks are prompts, not OpenCode Skills.",
                classes="hint",
            )
            yield RichLog(id="prompt-log", wrap=True, markup=True)
            with Horizontal(id="prompt-actions"):
                yield Button("Save playbooks", id="save-prompts", variant="primary")
                yield Button("Close", id="close-prompts")


class CodeSleuthHelpScreen(ModalScreen[None]):
    CSS = """
    CodeSleuthHelpScreen { align: center middle; background: rgba(0,0,0,0.62); }
    #help-dialog { width: 94%; height: 94%; border: round #31566a; background: #0e1822; padding: 1 2; }
    #help-title { color: #63d5f4; text-style: bold; }
    #help-subtitle { color: #8298a9; margin-bottom: 1; }
    #help-log { height: 1fr; border: solid #29404f; background: #0b141d; }
    #help-actions { height: auto; align-horizontal: right; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="help-dialog"):
            yield Label("CodeSleuth Help", id="help-title")
            yield Static("Operation guide, Skills, Playbooks, lifecycle, and safe removal.", id="help-subtitle")
            yield RichLog(id="help-log", wrap=True, markup=True)
            with Horizontal(id="help-actions"):
                yield Button("Close", id="close-help", variant="primary")

    def on_mount(self) -> None:
        log = self.query_one("#help-log", RichLog)
        for title, body in HELP_SECTIONS:
            log.write(f"[bold cyan]{title}[/bold cyan]\n{body}\n")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-help":
            self.dismiss(None)


class CodeSleuthConfigScreen(ConfigScreen):
    CSS = """
    CodeSleuthConfigScreen { align: center middle; background: rgba(0,0,0,0.58); }
    #config-dialog { width: 94%; height: 94%; border: round #31566a; background: #0e1822; padding: 1 2; }
    #config-title { color: #63d5f4; text-style: bold; }
    #evidence-mark { color: #71879a; height: 3; margin-bottom: 1; }
    .section { margin-top: 1; color: #63d5f4; text-style: bold; }
    .hint { color: #8298a9; }
    .row { height: auto; }
    Select { width: 38; }
    Input { width: 18; }
    #summary { border: solid #29404f; padding: 1; margin-top: 1; }
    #actions { height: auto; align-horizontal: right; margin-top: 1; }
    """

    def operation_options(self) -> tuple[list[tuple[str, str]], str]:
        if self.distribution_root is None:
            return [("Configure installed CodeSleuth", "configure")], "configure"
        if self.state == "versioned":
            return [("Update CodeSleuth + apply settings", "update"), ("Apply settings only", "configure")], "update"
        if self.state == "legacy-pack":
            return [("Adopt legacy review-pack with backup", "adopt"), ("Install without claiming legacy files", "install")], "adopt"
        return [("Install CodeSleuth / safe overlay", "install")], "install"

    def compose(self) -> ComposeResult:
        p = self.settings["permissions"]
        r = self.settings["runtime"]
        ops, selected_op = self.operation_options()
        with VerticalScroll(id="config-dialog"):
            yield Label("CodeSleuth Configuration", id="config-title")
            yield Static(EVIDENCE_MARK, id="evidence-mark")
            yield Static(f"Repository: {self.repo}\nInstallation state: {self.state}", classes="hint")

            yield Label("1. Installation", classes="section")
            yield Static(
                "CodeSleuth currently targets OpenCode V1 stable. OpenCode V2 is beta and uses a different plugin API; "
                "this control center will not silently migrate V1 plugins/configuration.",
                classes="hint",
            )
            yield Select(ops, value=selected_op, allow_blank=False, id="operation")

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

            yield Label("3. Evidence permissions", classes="section")
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

            yield Label("4. Runtime", classes="section")
            with Horizontal(classes="row"):
                yield Switch(value=r["exaEnabled"], id="exa")
                yield Label("Enable Exa websearch runtime (OPENCODE_ENABLE_EXA=1)")
            with Horizontal(classes="row"):
                yield Switch(value=r["watchdogEnabled"], id="watchdog")
                yield Label("Enable CodeSleuth keepalive watchdog")
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
                yield Label("Check upstream when CodeSleuth starts")

            yield Label("5. Planned policy", classes="section")
            yield Static("", id="summary")
            with Horizontal(id="actions"):
                yield Button("Apply", id="apply", variant="success")
                yield Button("Cancel", id="cancel")

    @work(thread=True, exclusive=True)
    def perform_apply(self, settings: dict, operation: str) -> None:
        try:
            if operation == "configure":
                save_settings(self.repo, settings)
                apply_settings_to_target(self.repo, settings)
                output = "CodeSleuth configuration applied."
            else:
                if self.distribution_root is None:
                    raise RuntimeError("CodeSleuth distribution checkout is required for install/adopt/update")
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


class CodeSleuthApp(ReviewPackApp):
    TITLE = "CodeSleuth · Evidence Console"
    CSS = """
    Screen { background: #081018; color: #d8e3eb; }
    Header { background: #0e1822; color: #63d5f4; }
    Footer { background: #0e1822; color: #8aa7b8; }
    #body { padding: 1 2; }
    #brand { color: #63d5f4; height: 15; text-style: bold; }
    #tagline { color: #8aa7b8; margin-bottom: 1; }
    #target { width: 100%; }
    #status { border: round #29404f; padding: 1; margin: 1 0; background: #0e1822; }
    #actions { height: auto; }
    #actions Button { margin-right: 1; }
    #log { height: 1fr; border: solid #29404f; margin-top: 1; background: #0b141d; }
    #configure { background: #155e75; }
    #launch { background: #166534; }
    """
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "configure", "Configure"),
        ("p", "playbooks", "Playbooks"),
        ("h", "help", "Help"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="body"):
            yield Static(CODESLEUTH_ART, id="brand")
            yield Static("Evidence-first repository intelligence", id="tagline")
            yield Label("Repository")
            yield Input(str(self.target), id="target")
            yield Static("", id="status")
            with Horizontal(id="actions"):
                yield Button("Configure", id="configure", variant="primary")
                yield Button("Verify", id="smoke")
                yield Button("Check Updates", id="check-update")
                yield Button("Update", id="update")
                yield Button("Playbooks", id="playbooks")
                yield Button("Help", id="help")
                yield Button("Open CodeSleuth", id="launch", variant="success")
            yield RichLog(id="log", wrap=True, markup=True)
        yield Footer()

    def refresh_status(self) -> None:
        try:
            self.target = self.validate_target()
            profiles = detect_profiles(self.target)
            state = installation_state(self.target)
            meta_path = self.target / ".opencode" / "review-pack.json"
            version = "not installed"
            complete = None
            if meta_path.is_file():
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                version = str(meta.get("version") or "unknown")
                complete = bool(meta.get("complete"))
            operation = recommended_operation(self.target, self.distribution_root is not None)
            readiness = "READY" if state == "versioned" and complete else ("ATTENTION" if state == "versioned" else "SETUP")
            complete_text = "yes" if complete is True else ("no" if complete is False else "n/a")
            self.query_one("#status", Static).update(
                f"{readiness}  CodeSleuth {version}\n"
                f"Installation: {state}; complete: {complete_text}\n"
                f"Profiles: {', '.join(profiles)}\n"
                f"Next action: {operation}"
            )
        except Exception as exc:
            self.query_one("#status", Static).update(f"ATTENTION\n{exc}")

    def action_configure(self) -> None:
        try:
            repo = self.validate_target()
        except Exception as exc:
            self.notify(str(exc), severity="error")
            return
        self.push_screen(CodeSleuthConfigScreen(repo, self.distribution_root), self._configured)

    def action_playbooks(self) -> None:
        try:
            repo = self.validate_target()
            profiles = load_settings(repo, detect_profiles(repo))["profiles"]
            self.push_screen(CodeSleuthPlaybookScreen(repo, profiles))
        except Exception as exc:
            self.notify(str(exc), severity="error")

    def action_help(self) -> None:
        self.push_screen(CodeSleuthHelpScreen())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "playbooks":
            self.action_playbooks()
        elif event.button.id == "help":
            self.action_help()
        else:
            super().on_button_pressed(event)

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
