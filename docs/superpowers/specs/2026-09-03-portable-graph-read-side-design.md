# Portable Graph Read-Side Design

**Status:** RC6 implementation design
**Base:** `feature/rc6-eha-brownfield-bootstrap` @ `0ae58cb2dc06e3d06e0839040f58d5a853f920ee`
**Core language:** Rust 2024, MSRV 1.88

## Goal

Make model-facing graph reacquisition a bounded, renderer-neutral portable Rust library that CodeSleuth consumes through a narrow JSON/native adapter and that other projects such as Aleph_Rugent or Pii_Parcer can vendor without inheriting CodeSleuth persistence, authority, OpenCode, or ontology contracts.

## Boundaries

The portable core owns only deterministic in-memory graph validation and read operations:

- `describe`
- deterministic `resolve`
- bounded `neighbors`
- bounded `shortest_paths`
- `explain`
- bounded `diff`

It does **not** own persistence, evidence authority, Git freshness, graph construction, rendering, model routing, model execution, or writes.

CodeSleuth remains responsible for loading and validating `RepositoryContextProjection`, exact-HEAD/stale-SourceRef checks, mapping projection nodes/edges into the portable graph shape, and returning the existing derived/non-authoritative policy envelope.

## Rust packaging

The crate lives at `portable/ebca-graph-readside/` and is intentionally independent of Bun/OpenCode. It exposes a Rust library API plus a small stdin/stdout JSON CLI (`ebca-graph-readside`) so non-Rust hosts can reuse exactly the same implementation.

The crate targets Rust 1.88 / edition 2024 to fit the current Aleph_Rugent workspace. Dependencies are intentionally small: `serde`, `serde_json`, and `sha2`.

CodeSleuth must never invoke `cargo run` or compile Rust implicitly during a model tool call. The OpenCode adapter accepts one explicit absolute native binary through `CODESLEUTH_GRAPH_READER_BIN`. Release packaging may later install a verified prebuilt binary at a stable managed path; absence is reported explicitly and does not mutate state.

Existing `repo_context_graph_query` remains the RC6 compatibility/fallback interface until native binary packaging is promoted. The new Rust-backed reader surface therefore adds reacquisition capability without making Rust toolchain availability a hidden ordinary-runtime dependency.

## Portable graph shape

The core accepts arbitrary string node kinds, edge relations, origins, optional JSON source references, and metadata. IDs are caller-owned opaque identities.

Resolver rule:

- node ID: **exact equality only**;
- key/label: deterministic exact, prefix, then substring matching;
- opaque/hash IDs are never tokenized, substring-ranked, or semantically reranked.

This preserves the CodeSleuth prohibition on hash/ID semantic reranking while remaining useful to non-CodeSleuth graphs.

## Boundedness

Every graph expansion has a hard limit inside the Rust core, not only in the adapter. Neighborhood selection is deterministic and uses a graph-bound continuation cursor. A cursor from another graph revision fails closed. Returned edges may never reference omitted nodes. Shortest-path search has hop, path-count, and expansion caps.

## CodeSleuth adapter

`pack/.opencode/tools/context_graph_read.ts`:

1. loads through existing canonical `repo_context_graph_load`;
2. rejects current reads when projection HEAD differs from current HEAD or verified SourceRefs are stale;
3. reads the validated saved projection;
4. maps it to the portable Rust graph input;
5. invokes the exact configured binary via JSON stdin/stdout;
6. rechecks projection identity after the native call;
7. returns a CodeSleuth policy envelope declaring the result derived navigation/context and requiring exact-source reopening for material claims.

Historical `diff` requires explicit projection IDs for both sides and reports their identities/freshness rather than pretending an old graph is current authority.

The older `repo_context_graph_query` and Mermaid surfaces remain compatibility interfaces for RC6. No writer, projection identity, persistence authority, or evidence authority changes in this slice.

## Additional portable function

A second portable function is the deterministic provenance-watermark algorithm. The Rust crate exposes a small `watermark` module whose functions require an explicit domain separator. Golden tests reproduce the existing CodeSleuth `codesleuth-provenance-v1` commit/session vectors without replacing the current Python CLI during RC6. This proves the algorithm is project-portable while avoiding a new runtime dependency for an already-working path.

## Portable tools index

`docs/PORTABLE-TOOLS.md` is the repository-level inventory. `portable/README.md` is the vendoring entry point.

Entries are classified as:

- `READY` — project-neutral source with its own tests/contracts;
- `ADAPTER` — CodeSleuth integration over a portable core;
- `PORTABLE-CANDIDATE` — useful logic still coupled to CodeSleuth/runtime details;
- `NOT-PORTABLE` — authority/persistence semantics that must remain project-owned.

Initial inventory includes the Rust graph reader, Rust provenance watermark core, Mermaid QA as a portability candidate, RepositoryEvidence/MCP read-side as a portability candidate, and Graphify normalization as a CodeSleuth adapter rather than a portable authority.

## Acceptance

The change is acceptable only if:

1. `cargo test --manifest-path portable/ebca-graph-readside/Cargo.toml --locked` passes on exact head;
2. the pure Rust graph reader has no OpenCode/CodeSleuth-state dependency;
3. resolver tests prove opaque IDs are exact-match only;
4. neighborhood tests prove hard bounds, graph-bound cursor rejection, and no dangling returned edges;
5. shortest-path tests prove hop/path/expansion bounds;
6. CodeSleuth integration tests build the Rust binary explicitly, bind it through `CODESLEUTH_GRAPH_READER_BIN`, and reject stale current projections;
7. Rust watermark golden vectors match existing CodeSleuth values;
8. existing `repo_context_graph_query`, Mermaid and provenance tests remain green;
9. the new tests are reachable from canonical GitHub acceptance;
10. the PR is compared against the then-current RC6 target and classified CLEAN or REFIT REQUIRED from actual compare/mergeability evidence.
