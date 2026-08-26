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


def test_sib_candidates_are_selected_from_release_stream() -> None:
    selection = text(ROOT / "docs" / "SIB-CANDIDATE-SELECTION.md")
    release = text(ROOT / "docs" / "RELEASE-PROCESS.md")
    playbook = text(ROOT / "docs" / "EHA-OPERATING-PLAYBOOK.md")
    for token in (
        "dev/release-X.Y.Z",
        "literal exact commit SHA",
        "The release branch supplies candidates; the exact SHA carries the proof",
        "repair branch",
        "new EHA campaign",
    ):
        assert token in selection
    assert "canonical candidate stream" in release
    assert "literal release-stream head" in release
    assert "Candidate stream" in playbook
    assert "repair branch is not the next SIB integration line" in playbook


def test_eha_skill_carries_sib_exact_head_and_release_stream_contract() -> None:
    skill = text(OPENCODE / "skills" / "eha-sib-acceptance" / "SKILL.md")
    for token in (
        "SIB0",
        "SIB1",
        "SIB2",
        "exact SHA",
        "dev/release-X.Y.Z",
        "SIB-CANDIDATE-SELECTION.md",
        "eha_state_start_campaign",
        "eha_state_record_verdict",
        "eha_state_record_repair",
        "eha_state_mermaid",
        "semantic-refit",
    ):
        assert token in skill
    assert "A repair commit inherits code history, not acceptance evidence" in skill
    assert "repair branch is not a parallel SIB integration line" in skill
    assert "resulting literal release-stream head SHA" in skill


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

    eha_test = text(OPENCODE / "commands" / "eha-test.md")
    eha_repair = text(OPENCODE / "commands" / "eha-repair.md")
    assert "dev/release-X.Y.Z" in eha_test
    assert "selected release-stream head" in eha_test
    assert "integrate that repair through the active `dev/release-X.Y.Z` branch" in eha_repair
    assert "merge commit is the new EHA target" in eha_repair


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


def test_docs_index_exposes_eha_playbook_repair_and_selection_contracts() -> None:
    docs_index = text(ROOT / "docs" / "README.md")
    assert "EHA-REPAIR-LOOP.md" in docs_index
    assert "EHA-OPERATING-PLAYBOOK.md" in docs_index
    assert "SIB-CANDIDATE-SELECTION.md" in docs_index
    assert "eha.ndjson" in docs_index
