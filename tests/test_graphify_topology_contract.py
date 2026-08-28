from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_adapter_topology_is_hint_only_and_versioned() -> None:
    adapter = text(ROOT / "pack" / ".opencode" / "bin" / "codesleuth_project" / "graphify_adapter.py")
    for token in (
        '"derivedSelectionHintsOnly": True',
        '"algorithm": "graphify.cluster+undirected_degree_centrality"',
        '"algorithmVersion": 1',
        '"topologyHint"',
        "graphify.build",
        "graphify.cluster",
    ):
        assert token in adapter, token


def test_topology_tool_cannot_write_or_change_projection_identity() -> None:
    tool = text(ROOT / "pack" / ".opencode" / "tools" / "repo_context_graph.ts")
    topology_source = tool[tool.index("export const topology = tool") :]
    assert "derivedSelectionHintsOnly: true" in topology_source
    assert "repo_context_graph_query and repo_context_graph_mermaid" in topology_source
    assert "atomicWrite(" not in topology_source
    assert "projectionIdentity(" not in topology_source
    assert "fallbackReason" in topology_source
    assert "staleHints" in topology_source
