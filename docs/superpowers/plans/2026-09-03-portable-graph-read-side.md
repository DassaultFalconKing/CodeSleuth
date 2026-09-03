# Portable Graph Read-Side Implementation Plan

> **For agentic workers:** execute task-by-task with TDD and verify exact branch identity before PR integration.

**Goal:** Ship a portable bounded Rust graph-reader core, a CodeSleuth read-only adapter, one additional portable utility in the same crate, and a maintained portable-tools index.

**Architecture:** The project-neutral source lives at `portable/ebca-graph-readside/` as a Rust 2024 crate with library + JSON CLI. `pack/.opencode/tools/context_graph_read.ts` stays a thin CodeSleuth adapter: canonical projection/freshness ownership remains TypeScript, while graph computation is delegated to an explicitly configured native binary. Existing `repo_context_graph_query` remains compatibility/fallback until release packaging supplies a native binary by default.

**Tech Stack:** Rust 1.88 / edition 2024, serde/serde_json/sha2, TypeScript/Bun OpenCode adapter, existing Python provenance tests.

**Spec:** `docs/superpowers/specs/2026-09-03-portable-graph-read-side-design.md`

## Global Constraints

- Base exact SHA is `0ae58cb2dc06e3d06e0839040f58d5a853f920ee` unless target moves before PR comparison.
- No new persistence/evidence authority.
- No new controller/runtime/router.
- No implicit `cargo run`, background compilation, or PATH-selected graph-reader runtime in model tools.
- Graph reads are derived navigation only.
- Current CodeSleuth graph reads fail closed on stale projection or stale SourceRefs.
- Opaque graph IDs are exact-match only in resolver scoring.
- All graph expansion is bounded inside the Rust library.

### Task 1: RED tests and canonical Rust acceptance reachability

**Files:**
- Create `portable/ebca-graph-readside/Cargo.toml`
- Create `portable/ebca-graph-readside/tests/graph_reader.rs`
- Create `portable/ebca-graph-readside/tests/watermark.rs`
- Modify `.github/workflows/acceptance.yml`

- [ ] Add tests for describe/resolve/neighbors/shortest path/explain/diff, malformed graphs, bounds, graph-bound cursors and CodeSleuth provenance golden vectors.
- [ ] Add a Rust acceptance job pinned to exact checked-out SHA and Rust 1.88.
- [ ] Push the test-only state and verify CI fails because the library target/API does not yet exist.

### Task 2: GREEN portable Rust library + JSON CLI

**Files:**
- Create `portable/ebca-graph-readside/src/lib.rs`
- Create `portable/ebca-graph-readside/src/graph.rs`
- Create `portable/ebca-graph-readside/src/watermark.rs`
- Create `portable/ebca-graph-readside/src/main.rs`
- Generate `portable/ebca-graph-readside/Cargo.lock`

- [ ] Implement the minimal project-neutral graph model and validation.
- [ ] Implement deterministic describe/resolve/neighbors/shortest_paths/explain/diff with hard bounds.
- [ ] Implement explicit-domain provenance watermark functions.
- [ ] Implement stdin/stdout JSON operation dispatch.
- [ ] Verify focused Rust tests and clippy/fmt in CI.

### Task 3: CodeSleuth native adapter

**Files:**
- Create `pack/.opencode/tools/context_graph_read.ts`
- Create `tests/context_graph_reader_smoke.ts`
- Modify `package.json`
- Modify `.github/workflows/acceptance.yml`

- [ ] Add integration tests that build the Rust binary explicitly in CI/test setup and bind its absolute path through `CODESLEUTH_GRAPH_READER_BIN`.
- [ ] Implement status/describe/resolve/neighbors/shortest_paths/explain/diff tools.
- [ ] Reuse `repo_context_graph_load` for validation/freshness and fail closed on stale current projections.
- [ ] Re-read projection identity after native execution to detect replacement races.
- [ ] Register the integration smoke in the default Bun umbrella.

### Task 4: Portable tools index

**Files:**
- Create `docs/PORTABLE-TOOLS.md`
- Create `portable/README.md`
- Modify `docs/README.md`

- [ ] Classify READY, ADAPTER, PORTABLE-CANDIDATE and NOT-PORTABLE components.
- [ ] Record Rust graph read-side and provenance watermark as READY.
- [ ] Record Mermaid QA and RepositoryEvidence/MCP read-side as candidates requiring extraction/parameterization.
- [ ] Record Graphify normalization and CodeSleuth authority stores as adapters/project-owned rather than portable authority.
- [ ] Link the index from the documentation entry point.

### Task 5: Verification and PR integration check

- [ ] Run contributor anti-pattern strict scan in canonical CI.
- [ ] Run Rust fmt/clippy/test.
- [ ] Run focused Bun graph-reader tests and the default Bun umbrella.
- [ ] Run Python provenance and repository tests through existing acceptance.
- [ ] Re-resolve current `feature/rc6-eha-brownfield-bootstrap` head.
- [ ] Compare the feature branch against that exact target.
- [ ] Open a PR into the current RC6 branch and classify integration as CLEAN or REFIT REQUIRED from actual compare/mergeability evidence.
