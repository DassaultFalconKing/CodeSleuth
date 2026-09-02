from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_repo_continue_fails_closed_on_missing_step_isolation_and_read_only_boundary() -> None:
    command = text("pack/.opencode/commands/repo-continue.md")
    assert "STEP_ISOLATION_UNPROVEN" in command
    assert "READ_ONLY_BOUNDARY_BLOCKED" in command
    assert "git config" in command
    assert "dependency install/update" in command
    assert "Do not repair the target in place" in command


def test_playbook_fallback_must_report_isolation_before_same_session_execution() -> None:
    command = text("pack/.opencode/commands/playbook.md")
    assert "before executing the Step in the current session" in command
    assert "STEP_ISOLATION_UNPROVEN" in command
    assert "must not silently fall back" in command


def test_authority_selection_pins_stop_gate_and_relation_exclusivity() -> None:
    resolve_authority = text(
        "pack/.opencode/playbooks/repository-development-continuation/steps/02-resolve-authority.md"
    )
    select_scope = text(
        "pack/.opencode/playbooks/repository-development-continuation/steps/03-select-active-scope.md"
    )
    assert "accepted predecessor and adjacent parallel track are mutually exclusive" in resolve_authority
    assert "historical or superseded material cannot be an accepted predecessor" in resolve_authority
    assert "earliest unresolved admissible stop-gate" in select_scope
    assert "do not aggregate later rollout stages" in select_scope


def test_change_surface_step_invokes_deterministic_closure_and_forbids_future_paths() -> None:
    manifest = json.loads(
        text("pack/.opencode/playbooks/repository-development-continuation/playbook.json")
    )
    step = next(item for item in manifest["steps"] if item["id"] == "map-change-surface")
    assert "change_surface_state_derive" in step["tools"]
    assert "change_surface_state_load" in step["tools"]

    prompt = text(
        "pack/.opencode/playbooks/repository-development-continuation/steps/04-map-change-surface.md"
    )
    assert "tracked files or tracked directories" in prompt
    assert "never pass a nonexistent future handoff" in prompt
    assert "authority-named verification paths" in prompt


def test_live_dogfood_never_repairs_target_during_read_only_acceptance() -> None:
    runbook = text("docs/RC6-LIVE-DOGFOOD-RUNBOOK.md")
    assert "Do not repair the target in place during dogfood" in runbook
    assert "git config" in runbook
    assert "package-manager or dependency update" in runbook
    assert "STEP_ISOLATION_UNPROVEN" in runbook
    assert "READ_ONLY_BOUNDARY_BLOCKED" in runbook
