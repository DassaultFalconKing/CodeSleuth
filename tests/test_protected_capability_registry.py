from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "protected-capabilities.json"
AUTHORITY = ROOT / "docs" / "PROTECTED-CAPABILITY-CONTRACTS.md"
AGENTS = ROOT / "AGENTS.md"
REVIEW_COMMAND = ROOT / "pack" / ".opencode" / "commands" / "repo-review.md"
CONTRACT_COMMAND = ROOT / "pack" / ".opencode" / "commands" / "repo-contracts.md"
CURSOR_RULE = ROOT / ".cursor" / "rules" / "stable-integration-baseline.mdc"
DOC_INDEX = ROOT / "docs" / "README.md"

ALLOWED_STATUS = {
    "experimental",
    "implemented",
    "sib1_accepted",
    "sib2_integrated",
    "protected",
    "deprecated",
    "removed",
}
ALLOWED_SIB_ORIGIN = {"SIB0", "SIB1", "SIB2"}


def _load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_registry_has_normative_authority_and_query_policy() -> None:
    registry = _load_registry()
    assert registry["schema_version"] == 1
    assert registry["authority"] == "docs/PROTECTED-CAPABILITY-CONTRACTS.md"
    assert AUTHORITY.is_file()

    policy = registry["query_policy"]
    assert policy["small_registry"] == "grep_or_ripgrep_then_paged_exact_read"
    assert "bm25" in policy["large_registry"]
    assert policy["semantic_retrieval_is_authority"] is False
    assert policy["allow_new_search_runtime"] is False


def test_contract_ids_and_forbidden_regression_ids_are_unique() -> None:
    registry = _load_registry()
    contract_ids = [contract["id"] for contract in registry["contracts"]]
    assert len(contract_ids) == len(set(contract_ids)), "contract ids must be globally unique"

    forbidden_ids: list[str] = []
    for contract in registry["contracts"]:
        forbidden_ids.extend(item["id"] for item in contract["forbidden_regressions"])

    assert len(forbidden_ids) == len(set(forbidden_ids)), "FR-* ids must be globally unique"


def test_every_contract_owns_a_forbidden_regression_registry() -> None:
    registry = _load_registry()
    assert registry["contracts"], "registry must contain at least one contract"

    for contract in registry["contracts"]:
        assert contract["status"] in ALLOWED_STATUS
        regressions = contract.get("forbidden_regressions")
        assert isinstance(regressions, list) and regressions, (
            f"{contract['id']} must own a non-empty forbidden_regressions registry"
        )
        for regression in regressions:
            assert regression["id"].startswith("FR-")
            assert regression["sib_origin"] in ALLOWED_SIB_ORIGIN
            assert regression["must_not"].strip()
            assert isinstance(regression.get("proof"), list)


def test_protected_contracts_have_three_source_evidence_and_protection_identity() -> None:
    registry = _load_registry()

    for contract in registry["contracts"]:
        if contract["status"] != "protected":
            continue

        for key in ("code_evidence", "doc_evidence", "test_evidence"):
            evidence = contract.get(key)
            assert isinstance(evidence, list) and evidence, (
                f"protected contract {contract['id']} requires non-empty {key}"
            )

        protected_at = contract.get("protected_at")
        assert isinstance(protected_at, dict), (
            f"protected contract {contract['id']} requires protected_at evidence"
        )
        assert protected_at["sib_level"] == "SIB2"
        sha = protected_at["sha"]
        assert isinstance(sha, str) and len(sha) == 40


def test_registered_dependencies_reference_registered_contracts() -> None:
    registry = _load_registry()
    known = {contract["id"] for contract in registry["contracts"]}

    for contract in registry["contracts"]:
        for dependency in contract.get("depends_on", []):
            assert dependency in known, (
                f"{contract['id']} depends on unknown contract {dependency}"
            )


def test_contract_discipline_is_wired_into_agent_prompts() -> None:
    agents = AGENTS.read_text(encoding="utf-8")
    review = REVIEW_COMMAND.read_text(encoding="utf-8")
    contract_command = CONTRACT_COMMAND.read_text(encoding="utf-8")
    cursor = CURSOR_RULE.read_text(encoding="utf-8")
    docs_index = DOC_INDEX.read_text(encoding="utf-8")

    assert "PROTECTED-CAPABILITY-CONTRACTS.md" in agents
    assert "protected-capabilities.json" in agents
    assert "protected-capability-registry" in review
    assert "protected-capability-registry" in contract_command
    assert "forbidden regressions" in cursor.lower()
    assert "PROTECTED-CAPABILITY-CONTRACTS.md" in docs_index
    assert "protected-capabilities.json" in docs_index
