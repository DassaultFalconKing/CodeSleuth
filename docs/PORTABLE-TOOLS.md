# Portable Tools Index

**Status:** inventory for vendorable/reusable CodeSleuth machinery  
**Not:** a relicensing grant, a second runtime, or an authority transfer

This index classifies CodeSleuth components by how much of their behavior can be reused outside this repository. Classification is about **technical coupling**, not about permission to copy the code into another licensed product.

```text
technical portability
    ≠
automatic relicensing permission
```

CodeSleuth is licensed under AGPL-3.0-or-later. A portable crate or algorithm in this tree remains under that license unless a later explicit license change says otherwise. Downstream projects such as Aleph_Rugent or Pii_Parcer may have different licenses; vendoring still requires a separate license-compatible decision. This branch does not copy CodeSleuth code into those repositories.

## Classification

| Class | Meaning |
| --- | --- |
| `READY` | Project-neutral source with its own tests/contracts and no CodeSleuth runtime/persistence/authority dependency. |
| `PORTABLE AFTER EXTRACTION` | Useful deterministic/bounded logic that still knows CodeSleuth paths, env names, ontology, or runtime. |
| `CODESLEUTH ADAPTER ONLY` | Integration over a portable core, or project-owned policy that must stay here. |
| `NOT-PORTABLE` | Persistence, evidence, Git freshness, OpenCode control, or other authority that must remain project-owned. |

## READY

### `ebca-graph-readside`

- **Purpose:** bounded deterministic graph reads over a caller-supplied generic graph.
- **Location:** `portable/ebca-graph-readside/`
- **Surface:** Rust library + JSON stdin/stdout CLI `ebca-graph-readside`
- **Operations:** `describe`, `resolve`, `neighbors`, `shortest_paths`, `explain`, `diff`
- **MSRV:** Rust 1.88 / edition 2024
- **Does not own:** persistence, Git, evidence, OpenCode, `.opencode/state`, CodeSleuth ontology, Mermaid, model routing, or writes
- **Safety:** opaque/hash-like IDs match only by exact ID; neighborhood/path/diff expansion is hard-bounded; cursors are graph/query-bound; returned edges cannot dangle
- **Runtime:** ordinary CodeSleuth installs do not compile this crate. Hosts bind an explicit absolute native binary.

### Portable provenance watermark algorithm

- **Purpose:** deterministic `Trace-Id` / session watermark digest with an explicit domain separator.
- **Location:** `portable/ebca-graph-readside/src/watermark.rs`
- **CodeSleuth domain:** `codesleuth-provenance-v1` (byte-for-byte with `scripts/provenance_watermark.py` and `pack/.opencode/tools/provenance_state.ts`)
- **Portable boundary:** callers must supply the domain. The algorithm does not default to CodeSleuth.
- **Not replaced:** the Python CLI and TypeScript sidecar remain the CodeSleuth runtime path. The Rust module proves the algorithm is project-portable.

## CODESLEUTH ADAPTER ONLY

### Context graph read adapter

- **Purpose:** map a validated `RepositoryContextProjection` into the portable graph, invoke the native reader, and return a derived-navigation envelope.
- **Location:** `pack/.opencode/tools/context_graph_read.ts`
- **Tools:** `context_graph_read_status`, `context_graph_read_describe`, `context_graph_read_resolve`, `context_graph_read_neighbors`, `context_graph_read_shortest_paths`, `context_graph_read_explain`, `context_graph_read_diff`, `context_graph_read_source_ref`
- **Owns:** projection load/freshness, exact-HEAD / stale-SourceRef policy, SourceRef reopening, native binary identity via `CODESLEUTH_GRAPH_READER_BIN`
- **Must not:** duplicate Rust traversal, compile Rust at tool invocation, or promote graph relations to evidence

### Graphify normalization

- **Purpose:** convert optional Graphify extraction into CodeSleuth projection candidates.
- **Location:** `pack/.opencode/bin/codesleuth_project/graphify_adapter.py`, `pack/.opencode/tools/repo_context_provider.ts`
- **Why adapter-only:** CodeSleuth kinds/relations, `verified_source` vs `review_inference`, tracked-path/Git blob recapture, and `.runtime/graphify-provider` identity are project policy.

## PORTABLE AFTER EXTRACTION

These are investigated candidates, not READY. Do not vendor them as-is.

### MCP `RepositoryEvidence` bounded Git reader

- **Purpose:** bounded read-only Git evidence: overview, inventory, line reads, search, test-map, diff.
- **Current location:** `codesleuth_mcp/server.py` (`RepositoryEvidence`)
- **Portable blockers:** FastMCP server wrapper; CodeSleuth tool names/instructions; CodeSleuth-specific env (`CODESLEUTH_MCP_DEBUG`); Git environment sanitization is useful but currently inlined with the MCP process-stdio contract; return shapes are CodeSleuth evidence vocabulary.
- **Portable boundary:** a generic “bounded tracked-file Git reader” could be extracted; MCP serving, NovaClaw registration, and CodeSleuth evidence envelopes must stay out.
- **Recommended extraction path:** isolate path/blob/line/search primitives behind an explicit repository-root + byte/line budget API, then keep `codesleuth_mcp` as the CodeSleuth/MCP adapter.

### Mermaid QA machinery

- **Purpose:** isolated mermaid-cli parse/render QA with explicit Node/Chromium identity.
- **Current location:** `scripts/mermaid_qa.py`, `tools/mermaid-qa/`
- **Portable blockers:** `CODESLEUTH_MERMAID_NODE` / `CODESLEUTH_MERMAID_BROWSER` env names; CodeSleuth result schema (`qa: mermaid_cli_parse_render`); default runtime path `tools/mermaid-qa`; Chromium host-resolver policy is reusable but currently documented as a CodeSleuth QA gate.
- **Portable boundary:** the exact-pinned mermaid-cli invocation plus absolute executable identity is potentially portable. The CodeSleuth acceptance wiring is not.
- **Recommended extraction path:** parameterize runtime root, package pin, and executable env names; keep CodeSleuth workflow binding as an adapter.

### Repository context identity hashing

- **Purpose:** deterministic node/edge/projection IDs from NUL-separated semantic fields.
- **Current location:** `pack/.opencode/tools/repo_context_graph.ts` (`sha256Nul`, `codesleuth-repo-context-*-v1` tags)
- **Portable blockers:** CodeSleuth identity domain tags, closed kind/relation enums, SourceRef Git capture.
- **Recommended extraction path:** only if a downstream project wants the same identity function with its own domain tags. Do not export CodeSleuth ontology as generic.

## NOT-PORTABLE

These remain CodeSleuth-owned authority or host integration:

- durable review/EHA ledgers (`review_state`, `eha_state`, `.opencode/state/reviews`)
- `RepositoryContextProjection` persistence and Git freshness
- OpenCode tool routing, agent permissions, and session control
- Development Authority Map / continuation packet / Native Gate Map
- Protected Capability Registry
- install/bind/unbind/uninstall lifecycle
- TUI / branding / host catalog

## Runtime rule

```text
portable crate + native CLI binary + JSON stdin/stdout
        ↑
explicit absolute executable identity
        ↑
CodeSleuth adapter / other host adapter
```

Absence of the native binary is a first-class unavailable state. Tool invocation must not run `cargo` or search `PATH` for a graph reader.

## License reminder

Vendoring `portable/ebca-graph-readside` into another product is a licensing event as well as a technical one. This inventory does not authorize relicensing, sublicensing, or publication under a different license.
