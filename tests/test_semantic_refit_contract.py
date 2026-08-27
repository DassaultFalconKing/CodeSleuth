from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "SEMANTIC-REFIT.md"
EHA = ROOT / "docs" / "EHA-OPERATING-PLAYBOOK.md"
RULE = ROOT / ".cursor" / "rules" / "stable-integration-baseline.mdc"
DOCS_INDEX = ROOT / "docs" / "README.md"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_semantic_refit_is_continuity_criterion_not_porting_alias() -> None:
    contract = text(CONTRACT)
    assert "not a new Git operation" in contract
    assert "target condition and review criterion" in contract
    assert "not a fourth SIB level" in contract
    assert "Semantic refit is not a synonym for porting" in contract
    assert "Implementation may change freely" in contract
    assert "do **not** determine semantic correctness" in contract


def test_semantic_refit_separates_claim_status_from_delivery() -> None:
    contract = text(CONTRACT)
    for token in ("REQUIRED", "SUPERSEDED", "RETIRED", "UNRESOLVED", "CONFLICTED"):
        assert token in contract
    for token in ("REUSE", "PORT / ADAPT", "REIMPLEMENT", "NEW CHANGE", "NO CHANGE", "DEFER", "BLOCK"):
        assert token in contract
    assert "Separate semantic status from delivery decision" in contract
    assert "| `DROP` | **ambiguous** |" in contract
    assert "never use `DROP` as a shortcut for `hard to integrate`" in contract


def test_semantic_refit_reuses_existing_codesleuth_authorities() -> None:
    contract = text(CONTRACT)
    for token in (
        "SIB0-CAPABILITY-INVENTORY.md",
        "PROTECTED-CAPABILITY-CONTRACTS.md",
        "protected-capabilities.json",
        "forbidden_regressions[]",
        "CODE_AHEAD",
        "DOC_AHEAD",
        "TEST_AHEAD",
        "CONTRADICTED",
        "UNPROVEN",
        "review_state",
        "EHA",
    ):
        assert token in contract
    assert "does not replace CodeSleuth's existing contract machinery" in contract


def test_semantic_refit_preserves_negative_knowledge_and_oracle_limits() -> None:
    contract = text(CONTRACT)
    for token in (
        "Negative / forbidden-state claim",
        "forbidden regressions",
        "Code oracle",
        "Behavioral oracle",
        "Journey oracle",
        "Presentation oracle",
        "Human UX oracle",
        "Do not report a stronger semantic conclusion than the oracle actually supports",
    ):
        assert token in contract


def test_negative_claims_have_constructive_and_adversarial_protocol() -> None:
    contract = text(CONTRACT)
    for token in (
        "Negative-claim evidence protocol",
        "Representation risk",
        "Execution risk",
        "Verification risk",
        "Forbidden state",
        "Constructive invariant",
        "Violation witness / counterexample predicate",
        "NO COUNTEREXAMPLE FOUND IN INSPECTED SCOPE",
        "STRUCTURALLY GUARDED",
        "Active-context retention",
    ):
        assert token in contract
    assert "finite test suite did not trigger the state" in contract
    assert "attempt the **violation**" in contract


def test_semantic_refit_distinguishes_claims_from_supporting_records() -> None:
    contract = text(CONTRACT)
    for token in ("ASSUMPTION", "RATIONALE", "MECHANISM", "EVIDENCE", "PROVENANCE"):
        assert token in contract
    assert "Claim taxonomy is not a substitute for evidence" in contract
    assert "Use **claim type** to describe the logical shape" in contract
    assert "Use **domain tags** to describe where it belongs" in contract


def test_eha_operator_uses_explicit_refit_axes() -> None:
    eha = text(EHA)
    assert "semantic status" in eha
    assert "delivery disposition" in eha
    assert "positive coverage evidence for `SUPERSEDED`" in eha
    assert "explicit current authority for `RETIRED`" in eha
    assert "classify REAPPLY / SUPERSEDED / REFIT / DROP" not in eha
    assert "A stale branch's green CI never transfers" in eha


def test_always_on_rule_and_docs_index_match_normative_concept() -> None:
    rule = text(RULE)
    docs_index = text(DOCS_INDEX)
    assert "target condition" in rule
    assert "claim status separately from delivery disposition" in rule
    assert "`DROP` is ambiguous" in rule
    assert "semantic-continuity criterion" in docs_index
    assert "semantic surface -> claim reconciliation -> evidence" in docs_index
