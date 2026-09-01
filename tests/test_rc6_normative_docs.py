from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def test_development_continuation_contract_is_normative_and_complete() -> None:
    path = DOCS / "DEVELOPMENT-CONTINUATION-CONTRACT.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    for required in (
        "Development Authority Map",
        "CANONICAL_PLANNING_AUTHORITY",
        "ACTIVE_IMPLEMENTATION_SCOPE",
        "ADJACENT_PARALLEL_TRACK",
        "Development Continuation Packet",
        "authorityEvidence",
        "nativeGates",
        "IN_SCOPE",
        "UNDECLARED",
        "ADJACENT_TRACK",
        "FORBIDDEN_BY_ACTIVE_SCOPE",
        "pre-registry change surface",
        "non-authoritative",
        "REPO_PROVABLE",
        "HOSTED_CI_PROVABLE",
        "SERVICE_DEPENDENT_REPRODUCIBLE",
        "LIVE_RUNTIME_REQUIRED",
        "OPERATOR_DECISION_REQUIRED",
        "CLOUD_TESTABILITY_REMAINING",
        "LIVE_HANDOFF_READY",
        "ExternalEvidenceManifestV1",
        "freshness",
        "AGREE",
        "implemented",
        "UNPROVEN",
        "experimental",
        "PROTECTED",
    ):
        assert required in text, required


def test_docs_index_and_feature_plan_expose_accepted_rc6_contract() -> None:
    index = (DOCS / "README.md").read_text(encoding="utf-8")
    assert "DEVELOPMENT-CONTINUATION-CONTRACT.md" in index

    plan = (DOCS / "RC6-FEATURE-PLAN.md").read_text(encoding="utf-8")
    assert "Status: **ACCEPTED / FROZEN FOR RC6 IMPLEMENTATION**" in plan
    assert "PROPOSED FOR SCOPE ACCEPTANCE" not in plan


def test_eha_bridge_doc_describes_trusted_pre_provider_campaign_authority() -> None:
    text = (DOCS / "GITHUB-EHA-BRIDGE.md").read_text(encoding="utf-8")
    for required in (
        "trusted pre-provider",
        "provenance",
        "campaign_started",
        "campaign_completed",
        "transport outcome",
        "provider",
    ):
        assert required in text, required
    assert "provider creates the campaign" not in text.lower()
