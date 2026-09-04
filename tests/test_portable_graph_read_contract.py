from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_portable_graph_reader_adapter_delegates_and_fails_closed() -> None:
    source = (ROOT / "pack" / ".opencode" / "tools" / "context_graph_read.ts").read_text(encoding="utf-8")
    required = [
        'const GRAPH_READER_ENV = "CODESLEUTH_GRAPH_READER_BIN"',
        "path.isAbsolute(configured)",
        "never compiles Rust",
        "contextGraphLoad.execute",
        "stale SourceRef",
        'projectionRole: "derived navigation/context"',
        'portableCoreRole: "bounded deterministic computation, not authority"',
        "reopenSourceBeforeEditOrFinding: true",
        'operation: "describe"',
        'operation: "resolve"',
        'operation: "neighbors"',
        'operation: "shortest_paths"',
        'operation: "explain"',
        'operation: "diff"',
        "source ref blob is stale",
    ]
    for token in required:
        assert token in source, f"missing portable graph adapter invariant: {token}"

    assert "cargo run" not in source
    assert "cargo build" not in source
    assert source.index("contextGraphLoad.execute") < source.index('operation: "describe"')


def test_portable_graph_reader_is_reached_by_canonical_bun_umbrella() -> None:
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    assert "tests/context_graph_reader_smoke.ts" in package["scripts"]["test"]
    assert package["scripts"]["test:context-graph-reader"] == "bun tests/context_graph_reader_smoke.ts"


def test_graph_reader_tools_are_denied_by_default() -> None:
    config = json.loads((ROOT / "pack" / ".opencode" / "opencode.json").read_text(encoding="utf-8"))
    assert config["permission"]["context_graph_read_*"] == "deny"
    assert config["agent"]["build"]["permission"]["context_graph_read_*"] == "allow"


def test_portable_crate_keeps_msrv_and_locked_ci() -> None:
    manifest = (ROOT / "portable" / "ebca-graph-readside" / "Cargo.toml").read_text(encoding="utf-8")
    assert 'edition = "2024"' in manifest
    assert 'rust-version = "1.88"' in manifest
    workflow = (ROOT / ".github" / "workflows" / "acceptance.yml").read_text(encoding="utf-8")
    assert "cargo fmt --manifest-path portable/ebca-graph-readside/Cargo.toml --all -- --check" in workflow
    assert "cargo clippy --manifest-path portable/ebca-graph-readside/Cargo.toml --locked --all-targets -- -D warnings" in workflow
    assert "cargo test --manifest-path portable/ebca-graph-readside/Cargo.toml --locked" in workflow
    assert "CODESLEUTH_GRAPH_READER_BIN" in workflow
    rust_source = (ROOT / "portable" / "ebca-graph-readside" / "src" / "graph.rs").read_text(encoding="utf-8")
    assert "node.id == query" in rust_source
    assert "all_paths" not in rust_source
