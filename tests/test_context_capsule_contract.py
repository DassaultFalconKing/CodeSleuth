from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPENCODE = ROOT / "pack" / ".opencode"


def test_context_capsule_is_selected_agent_only() -> None:
    config = json.loads((OPENCODE / "opencode.json").read_text(encoding="utf-8"))
    assert config["permission"]["codesleuth_context_*"] == "deny"
    assert config["agent"]["build"]["permission"]["codesleuth_context_get"] == "allow"

    for agent in ("repo-reviewer.md", "repo-scout.md"):
        text = (OPENCODE / "agents" / agent).read_text(encoding="utf-8")
        assert "codesleuth_context_get: allow" in text

    for agent in ("repo-documenter.md", "repo-profile-architect.md", "repo-prompt-advisor.md"):
        text = (OPENCODE / "agents" / agent).read_text(encoding="utf-8")
        assert "codesleuth_context_get: allow" not in text


def test_context_capsule_reuses_graph_authority_and_canonical_query() -> None:
    tool = (OPENCODE / "tools" / "codesleuth_context.ts").read_text(encoding="utf-8")
    assert "contextGraphLoad.execute" in tool
    assert "contextGraphQuery.execute" in tool
    assert "contextGraphMermaid.execute" in tool
    assert "stale SourceRef" in tool
    assert "does not match current HEAD" in tool
    assert "Mermaid has no cursor window contract" in tool
    assert "sourceAuthority: \"tracked Git source + blob identity\"" in tool
    assert "reviewAuthority: \"review_state\"" in tool


def test_context_capsule_is_in_canonical_bun_gate_and_documented_as_derived() -> None:
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    assert "tests/context_capsule_smoke.ts" in package["scripts"]["test"]
    assert package["scripts"]["test:context-capsule"] == "bun tests/context_capsule_smoke.ts"

    doc = (ROOT / "docs" / "MODEL-CONTEXT-CAPSULE.md").read_text(encoding="utf-8")
    assert "feature population inside `CC-GRAPH`" in doc
    assert "Mermaid" in doc and "secondary" in doc
    assert "not a secrecy boundary" in doc
    assert "does not add a model runtime" in doc
