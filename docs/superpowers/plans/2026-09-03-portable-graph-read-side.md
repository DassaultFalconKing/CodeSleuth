# Portable Graph Read-Side Implementation Plan

> **For agentic workers:** execute task-by-task with TDD and verify exact branch identity before PR integration.

**Goal:** Ship a portable bounded graph-reader core, a CodeSleuth read-only adapter, one additional extracted portable utility, and a maintained portable-tools index.

**Architecture:** Pure portable libraries live under `pack/.opencode/lib/portable/` so they travel with installed CodeSleuth but depend on neither OpenCode nor CodeSleuth state. `pack/.opencode/tools/context_graph_read.ts` is the CodeSleuth adapter that performs canonical projection load/freshness checks and maps to the portable graph shape.

**Tech Stack:** TypeScript/Bun, Python 3, existing OpenCode tool SDK.

**Spec:** `docs/superpowers/specs/2026-09-03-portable-graph-read-side-design.md`

## Global Constraints

- Base exact SHA is `0ae58cb2dc06e3d06e0839040f58d5a853f920ee` unless target moves before PR comparison.
- No new persistence/evidence authority.
- No new controller/runtime/router.
- Graph reads are derived navigation only.
- Current CodeSleuth graph reads fail closed on stale projection or stale SourceRefs.
- Opaque graph IDs are exact-match only in resolver scoring.
- All graph expansion is bounded.

### Task 1: Pure graph-reader core

**Files:**
- Create `pack/.opencode/lib/portable/graph_reader.ts`
- Create `tests/portable_graph_reader_smoke.ts`

- [ ] Add a failing smoke test for describe/resolve/neighbors/shortest path/explain/diff and invalid graph/bounds behavior.
- [ ] Implement the smallest dependency-free reader core.
- [ ] Verify the smoke test independently.

### Task 2: CodeSleuth adapter

**Files:**
- Create `pack/.opencode/tools/context_graph_read.ts`
- Create `tests/context_graph_reader_smoke.ts`
- Modify `package.json`

- [ ] Add failing integration tests against a temporary Git repository and saved `RepositoryContextProjection`.
- [ ] Implement canonical load + exact-head freshness adapter.
- [ ] Register the smoke under default `scripts.test` and a focused `test:context-graph-reader` command.
- [ ] Verify stale projection rejection and bounded graph reads.

### Task 3: Extract provenance watermark algorithm

**Files:**
- Create `pack/.opencode/lib/portable/__init__.py`
- Create `pack/.opencode/lib/portable/provenance_watermark.py`
- Modify `scripts/provenance_watermark.py`
- Create `tests/test_portable_provenance_watermark.py`

- [ ] Add tests proving domain separation and deterministic normalization.
- [ ] Extract the project-neutral algorithm with explicit domain separator.
- [ ] Keep the existing CodeSleuth helper API/CLI and `codesleuth-provenance-v1` outputs unchanged.
- [ ] Run existing provenance contract tests plus the new portable tests.

### Task 4: Portable tools indexes and contracts

**Files:**
- Create `docs/PORTABLE-TOOLS.md`
- Create `pack/.opencode/lib/portable/README.md`
- Modify `docs/README.md`

- [ ] Document READY portable tools, adapters, authority boundaries, vendoring contract, and identified candidates that still need extraction.
- [ ] Link the index from the documentation entry point.

### Task 5: Verification and PR integration check

- [ ] Run contributor anti-pattern strict scan in available CI/host evidence.
- [ ] Run focused Bun graph-reader tests.
- [ ] Run Python provenance tests.
- [ ] Run default test umbrella/CI where available.
- [ ] Re-resolve the current `feature/rc6-eha-brownfield-bootstrap` head.
- [ ] Compare the feature branch against that exact target.
- [ ] Open a PR into the current RC6 branch and classify the integration as CLEAN or REFIT REQUIRED from actual compare/mergeability evidence.
