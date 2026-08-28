from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_helper():
    path = ROOT / "scripts" / "provenance_watermark.py"
    spec = importlib.util.spec_from_file_location("provenance_watermark", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_commit_watermark_is_deterministic_and_normalizes_subject() -> None:
    helper = load_helper()
    parent = "1" * 40
    expected_digest = hashlib.sha256(
        f"codesleuth-provenance-v1|commit|s56|{parent}|fix: one thing".encode()
    ).hexdigest()[:12]
    expected = f"s56-{expected_digest}"
    assert helper.commit_watermark("s56", parent, "  FIX:   One\tThing  \nignored body") == expected
    assert helper.commit_watermark("s56", parent, "fix: one thing") == expected


def test_session_watermark_is_bound_to_actor_head_and_session() -> None:
    helper = load_helper()
    head = "2" * 40
    first = helper.session_watermark("agent1", head, "session-a")
    assert first.startswith("agent1-")
    assert len(first.rsplit("-", 1)[1]) == 12
    assert helper.session_watermark("agent1", head, "session-b") != first
    assert helper.session_watermark("agent2", head, "session-a") != first


def test_packaged_contract_matches_normative_document() -> None:
    normative = (ROOT / "docs" / "PROVENANCE-WATERMARK.md").read_text(encoding="utf-8")
    packaged = (ROOT / "pack" / ".opencode" / "PROVENANCE-WATERMARK.md").read_text(encoding="utf-8")
    assert packaged == normative


def test_all_coder_policy_surfaces_require_the_contract() -> None:
    managed = (ROOT / "pack" / ".opencode" / "policy" / "agents-rules.md").read_text(encoding="utf-8")
    cursor = (ROOT / ".cursor" / "rules" / "provenance-watermark.mdc").read_text(encoding="utf-8")
    assert ".opencode/PROVENANCE-WATERMARK.md" in managed
    assert "Before the first repository write" in managed
    assert "Trace-Id:" in managed
    assert "`anon`" in managed
    assert "alwaysApply: true" in cursor
    assert "PROVENANCE-WATERMARK.md" in cursor


def test_reports_and_eha_require_verified_provenance_without_promoting_it_to_authority() -> None:
    reports = (ROOT / "pack" / ".opencode" / "CODESLEUTH-REPORTS.md").read_text(encoding="utf-8")
    report_skill = (ROOT / "pack" / ".opencode" / "skills" / "codesleuth-reports" / "SKILL.md").read_text(encoding="utf-8")
    eha_skill = (ROOT / "pack" / ".opencode" / "skills" / "eha-campaign-evidence" / "SKILL.md").read_text(encoding="utf-8")
    eha_command = (ROOT / "pack" / ".opencode" / "commands" / "eha-test.md").read_text(encoding="utf-8")
    assert "- provenance: <actor>-<12 lowercase hex>" in reports
    assert "provenance_state_load" in report_skill
    assert "provenance_state_bind" in eha_skill
    assert "does not" in eha_skill.lower() and "claimability" in eha_skill.lower()
    assert "provenance_state_bind" in eha_command
    assert "provenance_state_load" in eha_command


def test_provenance_sidecar_tool_is_present_and_immutable_by_contract() -> None:
    tool = (ROOT / "pack" / ".opencode" / "tools" / "provenance_state.ts").read_text(encoding="utf-8")
    assert "provenance.json" in tool
    assert 'const DOMAIN = "codesleuth-provenance-v1"' in tool
    assert "provenance already bound to a different producer/session/HEAD" in tool
    assert "headMatch" in tool
