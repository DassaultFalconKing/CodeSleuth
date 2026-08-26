#!/usr/bin/env python3
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Grid, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Footer, Header, Input, Label, RichLog, Select, Static

import codesleuth_tui as _base


class CodeSleuthApp(_base.CodeSleuthApp):
    """Runtime console with persistent activity output and explicit control feedback."""

    CSS = _base.CodeSleuthApp.CSS + """
    #center-column { width: 1fr; height: 1fr; }
    #center-column #main-scroll { width: 1fr; height: 1fr; padding: 1 2 0 2; }
    #center-column #activity-panel {
        height: 9;
        min-height: 7;
        margin: 0 2 1 2;
        padding: 1;
        border: round #29404f;
        background: #0e1822;
    }
    #center-column #activity-title { margin-bottom: 1; }
    #center-column #log { height: 1fr; min-height: 3; }
    #workspace.compact { height: 1fr; }
    #workspace.compact #center-column { height: 1fr; }
    #workspace.compact #main-scroll { height: 1fr; max-height: 1fr; }
    #workspace.compact #activity-panel { height: 7; min-height: 6; margin: 0 1; padding: 0 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="workspace"):
            with Vertical(id="wide-nav"):
                with Horizontal(id="nav-chrome"):
                    yield Static("Surfaces", id="nav-title", classes="hint")
                    yield _base._rail_toggle_button("<", "nav-collapse")
                for route in _base.NAV_SURFACES:
                    yield Button(route.title(), id=f"nav-{route}", classes="nav-button")
            with Vertical(id="center-column"):
                with VerticalScroll(id="main-scroll"):
                    with Vertical(id="main-panel"):
                        yield Select(
                            [(name.title(), name) for name in _base.NAV_SURFACES],
                            value="home",
                            allow_blank=False,
                            id="compact-nav",
                        )
                        with Vertical(id="operation"):
                            yield Static("", id="surface")
                            with Grid(id="actions"):
                                yield Button("Configure", id="configure", variant="primary")
                                yield Button("Verify", id="smoke")
                                yield Button("Check Updates", id="check-update")
                                yield Button("Update", id="update")
                                yield Button("Playbooks", id="playbooks")
                                yield Button("Help", id="help")
                                yield Button("Uninstall", id="uninstall", variant="error")
                                yield Button("Open CodeSleuth", id="launch", variant="primary")
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
                        yield Static(
                            "Evidence may contain developer credentials visible to authorized tests/services. "
                            "Local state is ignored by default; inspect reports before sharing or committing them.",
                            id="security",
                        )
                with Vertical(id="activity-panel"):
                    yield Static("Recent activity", id="activity-title")
                    yield RichLog(id="log", wrap=True, markup=True)
        yield Footer(id="keys")

    def write_ui_log(self, text: str) -> None:
        log = self.query_one("#log", RichLog)
        log.write(text)
        log.scroll_end(animate=False)

    def _control_unavailable(self, label: str) -> None:
        self.write_ui_log(f"[yellow]{label} unavailable for the current lifecycle/update mode; see Status.[/yellow]")
        self.notify(f"{label} unavailable; see Status", severity="warning")

    def action_verify(self) -> None:
        self.write_ui_log("[bold #63d5f4]Verify started…[/bold #63d5f4]")
        self.run_runtime_action("smoke")

    def action_check_updates(self) -> None:
        if self.query_one("#check-update", Button).disabled:
            self._control_unavailable("Check Updates")
            return
        self.write_ui_log("[bold #63d5f4]Check Updates started…[/bold #63d5f4]")
        super().action_check_updates()

    def action_update(self) -> None:
        if self.query_one("#update", Button).disabled:
            self._control_unavailable("Update")
            return
        self.write_ui_log("[bold #63d5f4]Update started…[/bold #63d5f4]")
        super().action_update()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "smoke":
            event.stop()
            self.action_verify()
            return
        super().on_button_pressed(event)


launch_opencode = _base.launch_opencode
