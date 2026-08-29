from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


def test_context_capsule_is_exact_head_primary_machine_context() -> None:
    source = read("pack/.opencode/tools/codesleuth_context.ts")

    required = [
        '"Return a strict exact-head context capsule for selected coding/review agents.',
        "contextGraphLoad.execute",
        "contextGraphQuery.execute",
        'role: "secondary-derived-presentation"',
        'sourceAuthority: "tracked Git source + blob identity"',
        'reviewAuthority: "review_state"',
        'projectionRole: "derived navigation/context"',
        'mermaidRole: "secondary derived presentation"',
        "reopenSourceBeforeEditOrFinding: true",
        "staleLinkageCount: 0",
        "exactHeadMatch: true",
    ]
    for token in required:
        assert token in source, f"missing context-capsule authority invariant: {token}"

    # Freshness validation must occur before the canonical bounded query.
    assert source.index("contextGraphLoad.execute") < source.index("contextGraphQuery.execute")
    # Mermaid may only be attached after canonical query construction.
    assert source.index("contextGraphQuery.execute") < source.index("contextGraphMermaid.execute")


def test_repository_graph_query_and_mermaid_share_one_projection_selection() -> None:
    source = read("pack/.opencode/tools/repo_context_graph.ts")

    assert "function selectNeighborhood(" in source
    assert "const selection = selectNeighborhood(projection" in source
    assert source.count("selectNeighborhood(projection") >= 2
    assert "Selection semantics are never duplicated here" in source

    # Query remains navigation/context rather than evidence.
    assert 'reminder: "graph relations are navigation/context, not sufficient finding evidence"' in source

    # Mermaid carries machine-readable derived-presentation authority metadata.
    required_mermaid = [
        'view: "repository_context"',
        'kind: "saved_repository_context_projection"',
        "Mermaid is derived presentation only",
        "derivedPresentationOnly: true",
        "aliasesArePresentationOnly: true",
    ]
    for token in required_mermaid:
        assert token in source, f"missing Mermaid authority invariant: {token}"


def test_graphify_provider_stays_optional_candidate_extraction() -> None:
    module_path = ROOT / "pack" / ".opencode" / "bin" / "codesleuth_project" / "graphify_adapter.py"
    spec = importlib.util.spec_from_file_location("codesleuth_graphify_contract_adapter", module_path)
    assert spec and spec.loader
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)

    status = adapter.provider_status(ROOT / ".runtime" / "graphify-provider-contract-test-missing")
    assert status["defaultProvider"] is False
    assert status["permissions"]["semanticLlm"] is False
    assert status["permissions"]["gitMutation"] is False
    assert status["permissions"]["trackedWrite"] is False
    assert "bounded_candidate_projection" in status["capabilities"]

    source = module_path.read_text(encoding="utf-8")
    assert 'ALLOWED_RELATIONS = {"imports": "imports", "calls": "calls"}' in source
    assert '"origin": "verified_source" if exact else "review_inference"' in source
    assert '"relation": mapped_relation if exact else "review_inference"' in source
    assert "unmappedRelations" in source


def test_model_facing_routing_prefers_capsule_and_demotes_mermaid() -> None:
    repo_map = read("pack/.opencode/commands/repo-map.md")
    deep_review = read("pack/.opencode/skills/repository-deep-review/SKILL.md")

    for text in (repo_map, deep_review):
        assert "codesleuth_context_get" in text
        assert "exact" in text.lower()
        assert "source" in text.lower()

    assert (
        "Mermaid is optional secondary presentation, not the primary machine context"
        in normalized(repo_map)
    )
    assert "Raw graph queries and Mermaid remain derived navigation/presentation" in normalized(deep_review)
    assert "Reopen exact current source before accepting any material claim" in normalized(deep_review)


def test_product_and_graph_contract_keep_provider_projection_presentation_separate() -> None:
    graph_contract = read("docs/GRAPH-CONSUMPTION-CONTRACT.md")
    product_contract = read("docs/CODESLEUTH-PRODUCT-CONTRACT.md")
    discipline = read("docs/CONTEXT-GRAPH-DISCIPLINE.md")

    assert "Provider != projection != model context != presentation" in graph_contract
    assert "Graphify is an optional structural extraction provider" in graph_contract
    assert "Mermaid is **secondary derived presentation**" in graph_contract
    assert "reopen the relevant exact current source" in graph_contract

    assert "Generated Mermaid remains presentation of verified structure" in product_contract
    assert "RepositoryContextProjection" in discipline
    assert "Graphify is therefore a roadmap candidate/provider implementation detail" in discipline
