from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPENCODE = ROOT / "pack" / ".opencode"
CONTRACT = ROOT / "docs" / "DURABLE-EVIDENCE-STORE.md"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_contract_defines_snapshot_ledgers_and_derived_views() -> None:
    contract = text(CONTRACT)
    for token in (
        "state.json",
        "mutable atomic checkpoint snapshot",
        "findings.ndjson",
        "append-only finding ledger",
        "eha.ndjson",
        "append-only EHA event ledger",
        "RepositoryContextProjection",
        "Mermaid",
        "Raw `cat`, `grep`",
        "read-only discovery mechanism",
        "Direct raw writes are forbidden",
        "duplicate authority",
    ):
        assert token in contract


def test_report_contract_points_back_to_durable_store_contract() -> None:
    reports = text(OPENCODE / "CODESLEUTH-REPORTS.md")
    skill = text(OPENCODE / "skills" / "codesleuth-reports" / "SKILL.md")
    assert "DURABLE-EVIDENCE-STORE.md" in reports
    assert "DURABLE-EVIDENCE-STORE.md" in skill
    assert "derived" in skill.lower()


def test_review_skill_uses_tool_mediated_evidence_access() -> None:
    skill = text(OPENCODE / "skills" / "repository-deep-review" / "SKILL.md")
    assert "DURABLE-EVIDENCE-STORE.md" in skill
    assert "append-only" in skill
    assert "raw" in skill.lower() and "write" in skill.lower()


def test_eha_skill_inherits_append_only_store_contract() -> None:
    skill = text(OPENCODE / "skills" / "eha-campaign-evidence" / "SKILL.md")
    assert "DURABLE-EVIDENCE-STORE.md" in skill
    assert "append-only" in skill
    assert "eha.ndjson" in skill
    assert "raw" in skill.lower() and "rewrite" in skill.lower()


def test_feature_porting_skill_already_forbids_duplicate_evidence_authority() -> None:
    skill = text(OPENCODE / "skills" / "feature-porting-discipline" / "SKILL.md")
    assert "evidence ledger" in skill
    assert "review_state" in skill
    assert "No duplicate authority" in skill


def test_docs_index_exposes_durable_evidence_contract() -> None:
    docs_index = text(ROOT / "docs" / "README.md")
    assert "DURABLE-EVIDENCE-STORE.md" in docs_index
