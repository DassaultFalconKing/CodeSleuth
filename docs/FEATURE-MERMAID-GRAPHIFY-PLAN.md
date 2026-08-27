# Full Mermaid and optional Graphify feature plan

**Feature branch:** `feature/post-sib2-mermaid-full`  
**Base SHA:** `2d62781f70bbf079a84afcb8c429e8d8c5e87413`  
**Change class:** post-SIB2 feature population inside the existing
`context-relationship-graph` capability class  
**Status:** implementation plan; completion is established only by the gates below

## Objective

Complete the Mermaid feature surface without creating a renderer, graph, evidence,
or execution authority beside CodeSleuth. The feature comprises:

1. one structured response/provenance contract for every generated Mermaid view;
2. optional parser/render quality assurance for generated Mermaid source;
3. an isolated, explicitly enabled Graphify structural-provider adapter;
4. a repeatable representative-corpus comparison and hardening harness;
5. optional provider selection in the existing repository-map flow; and
6. topology-assisted bounded presentation selection that cannot change identity,
   provenance, or evidence status.

The implementation remains source-first and renderer-neutral. Generated Mermaid and
provider topology are derived navigation only.

## Non-goals and forbidden shortcuts

- No second controller, scheduler, model runtime, persistence authority, or evidence
  ledger.
- No Graphify Skill installation, `graphify install`, Git hooks, merge drivers, MCP or
  HTTP server, global graph, provider credentials, semantic/LLM extraction, or network
  ingestion.
- No committed `graphify-out/`, generated SVG/PNG, provider cache, or target-repository
  mutation.
- No automatic Graphify installation or update during normal CodeSleuth operation.
- No promotion of `INFERRED` or `AMBIGUOUS` provider output to `verified_source`.
- No Mermaid parsing or rendering requirement when the optional QA dependency is
  absent.
- No provider-specific traversal language beside the existing bounded context-graph
  query contract.

## Deliverables and staged gates

### D0 — branch and baseline

- [x] Isolated clean worktree uses `feature/post-sib2-mermaid-full`.
- [x] Branch is fast-forwarded to the exact requested base SHA.
- [x] Baseline Python and Bun suites are green in this worktree.

Gate:

```text
bun install --frozen-lockfile
bun run test
python -m pytest -q
python -m ruff check .
```

### D1 — uniform Mermaid response and provenance

- [x] `eha_state_mermaid` returns a versioned JSON envelope rather than an unstructured
      source string.
- [x] The envelope reports authority, exact ledger/review identity, selection bounds,
      totals, truncation, and `derivedPresentationOnly`.
- [x] Repository, protected-capability, and EHA Mermaid responses share a documented
      minimum envelope vocabulary without merging their underlying authorities.
- [x] Backward compatibility is explicit; no silent response-shape ambiguity.

Focused gate:

```text
bun tests/eha_state_smoke.ts
bun tests/context_graph_smoke.ts
bun tests/protected_capability_graph_smoke.ts
python -m pytest -q tests/test_eha_contract.py tests/test_durable_evidence_store_contract.py
```

### D2 — optional Mermaid parser/render QA

- [ ] A bounded QA command validates generated Mermaid source with an exact-pinned
      renderer/parser dependency in an isolated subprocess.
- [ ] Normal tool execution never launches Chromium or requires the QA dependency.
- [ ] QA reports tool/version, source digest, exit state, diagnostics, and optional
      disposable SVG output metadata.
- [ ] Hostile-label fixtures and all three Mermaid surfaces are parser-checked.
- [ ] Absence of the optional runtime is reported as `unavailable`, never as PASS.

Focused gate:

```text
bun tests/mermaid_qa_smoke.ts
python -m pytest -q tests/test_mermaid_qa_contract.py
```

### D3 — Graphify structural-provider adapter (M2)

- [ ] Exact provider package/version and upstream commit are pinned and visible.
- [ ] Adapter accepts only a caller-supplied, tracked Git file manifest beneath the
      explicit repository root.
- [ ] Adapter calls a library/API boundary or isolated helper, never Graphify install,
      hooks, MCP, HTML/report, semantic, credential, or network paths.
- [ ] Provider output is normalized into a closed candidate schema before it reaches
      TypeScript/model-visible tools.
- [ ] Unknown node/relation kinds and `INFERRED`/`AMBIGUOUS` data are counted and
      fail closed or remain review inference.
- [ ] `EXTRACTED` candidates require CodeSleuth path/blob/source validation before
      promotion to `verified_source`.
- [ ] Disabled/default operation has no Graphify import or runtime requirement.

Focused gate:

```text
python -m pytest -q tests/test_graphify_adapter.py
bun tests/context_graph_provider_smoke.ts
```

### D4 — representative corpus comparison and hardening (M3)

- [ ] Harness covers CodeSleuth, Python, TypeScript/Node, Rust, mixed-language,
      over-limit, dirty tracked, rename/delete, symlink/gitlink/non-regular, malicious
      label, odd-encoding, and Windows-path cases.
- [ ] Results report precision samples, useful-structure recall proxy, wall time,
      peak memory where available, output size, truncation, unmapped semantics, and
      provider/model-visible size.
- [ ] Fixtures are deterministic and do not require network access.
- [ ] A machine-readable comparison artifact is disposable/ignored, not authority.

Focused gate:

```text
python -m pytest -q tests/test_graphify_corpus.py
python scripts/graphify_corpus_compare.py --fixtures tests/fixtures/graphify-corpus --check
```

### D5 — optional provider in repository-map flow (M4)

- [ ] Existing builtin behavior remains the default.
- [ ] Provider selection is explicit: `builtin` or `graphify`.
- [ ] Status exposes installed/available state, exact version/origin, capabilities,
      permission boundary, and compatibility state.
- [ ] Provider cache is local, ignored, rebuildable, bounded, and removable through
      the existing lifecycle.
- [ ] `/repo-map`, playbook steps, operator docs, packaging and Verify describe and
      test the same behavior.

Focused gate:

```text
bun tests/context_graph_provider_smoke.ts
python -m pytest -q tests/test_graphify_lifecycle.py tests/test_smoke_parity.py
python smoke.py
```

### D6 — topology-assisted bounded selection (M5)

- [ ] Communities/centrality are optional selection hints over already validated
      CodeSleuth nodes, never identity or evidence.
- [ ] Selection is deterministic, bounded before model exposure, and reports provider,
      algorithm/version, totals, omissions, and fallback reason.
- [ ] Unknown/stale/incomplete provider topology falls back or fails closed without
      changing the underlying projection.
- [ ] Rendered edges still reference only rendered nodes and preserve inference style.
- [ ] No-filter/native output remains compatible with the accepted M1 behavior.

Focused gate:

```text
bun tests/context_graph_topology_smoke.ts
bun tests/context_graph_smoke.ts
python -m pytest -q tests/test_graphify_topology_contract.py
```

### D7 — final integration and handoff

- [ ] Every focused gate above is rerun after integration.
- [ ] Full Python, Bun, Ruff, lifecycle/packaging, documentation-contract, and Mermaid
      parser QA gates are green.
- [ ] Optional-dependency-absent and optional-dependency-enabled profiles both pass.
- [ ] `pack/.opencode` and installed/runtime parity are verified from a disposable
      installation, not by editing the source checkout's `.opencode` mirror.
- [ ] Exact branch head, ordered logical commits, executed evidence, skipped platform
      coverage, and residual limitations are recorded for supervisor transplant.
- [ ] No merge, baseline promotion, EHA PASS, tag, or release claim is made here.

## Commit and test discipline

Each D1–D6 deliverable is one reviewable logical commit unless a focused repair is
required. Run and record the focused gate before starting the next deliverable. Run the
full integration gate only after all focused gates are green. A green focused gate proves
the feature delta only; it does not transfer SIB/EHA acceptance to the feature head.

## Completion evidence table

| Deliverable | Implementation evidence | Test evidence | Status |
| --- | --- | --- | --- |
| D0 baseline | exact Git base/worktree | full baseline gate | complete |
| D1 envelope | tool schemas and docs | EHA + graph smoke/contracts | complete |
| D2 Mermaid QA | isolated QA helper/tool | parser and hostile-source tests | pending |
| D3 Graphify adapter | pinned adapter and closed schema | adapter/provider contracts | pending |
| D4 corpus | deterministic harness/fixtures | corpus check | pending |
| D5 provider UX | config/playbook/lifecycle integration | provider/lifecycle/parity | pending |
| D6 topology | bounded hint selection | topology + M1 regression | pending |
| D7 handoff | exact-head audit | all gates rerun | pending |
