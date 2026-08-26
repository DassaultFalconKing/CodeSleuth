from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPENCODE = ROOT / "pack" / ".opencode"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_normative_eha_repair_loop_is_documented() -> None:
    repair = text(ROOT / "docs" / "EHA-REPAIR-LOOP.md")
    assert "An EHA campaign never repairs its own target" in repair
    assert "A failing EHA SHA remains failed" in repair
    assert "Acceptance evidence does not inherit across repair commits" in repair
    assert "Tester discovers. Repairer repairs." in repair
    assert "new EHA" in repair


def test_eha_skill_carries_sib_and_exact_head_contract() -> None:
    skill = text(OPENCODE / "skills" / "eha-sib-acceptance" / "SKILL.md")
    for token in (
        "SIB0",
        "SIB1",
        "SIB2",
        "exact SHA",
        "eha_state_start_campaign",
        "eha_state_record_verdict",
        "eha_state_record_repair",
        "eha_state_mermaid",
        "semantic-refit",
    ):
        assert token in skill
    assert "A repair commit inherits code history, not acceptance evidence" in skill


def test_eha_playbooks_are_installed_and_route_to_the_skill() -> None:
    commands = {
        "eha-test.md": "eha_state_start_campaign",
        "eha-repair.md": "eha_state_record_repair",
        "eha-status.md": "eha_state_load",
    }
    for filename, tool_name in commands.items():
        command = text(OPENCODE / "commands" / filename)
        assert "agent: build" in command
        assert "eha-sib-acceptance" in command
        assert tool_name in command


def test_structured_eha_evidence_uses_existing_review_state_boundary() -> None:
    tool_source = text(OPENCODE / "tools" / "eha_state.ts")
    reports = text(OPENCODE / "CODESLEUTH-REPORTS.md")
    assert 'path.join(root, ".opencode", "state", "reviews")' in tool_source
    assert '"eha.ndjson"' in tool_source
    assert "EHA INVALIDATED — HEAD CHANGED" in tool_source
    assert "claimable" in tool_source
    assert "renderMermaid" in tool_source
    assert ".opencode/state/reviews/<reviewId>/" in reports
    assert "eha.ndjson" in reports
    assert "SIB0" in reports and "SIB1" in reports and "SIB2" in reports


def test_eha_state_smoke_is_part_of_the_canonical_bun_gate() -> None:
    package = text(ROOT / "package.json")
    assert "tests/eha_state_smoke.ts" in package
    assert '"test:eha-state"' in package


def test_docs_index_exposes_eha_playbook_and_repair_contract() -> None:
    docs_index = text(ROOT / "docs" / "README.md")
    assert "EHA-REPAIR-LOOP.md" in docs_index
    assert "EHA-OPERATING-PLAYBOOK.md" in docs_index
    assert "eha.ndjson" in docs_index
