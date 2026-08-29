# Graph consumption authority contract

**Status:** production hardening contract  
**Classification:** CORE-HARDENING  
**Scope:** repository structural providers, `RepositoryContextProjection`, model-facing graph context, and Mermaid views

## 1. Principle

CodeSleuth has one repository-context authority chain and multiple derived consumers.

```text
tracked Git source + exact blob identity
        |
        v
review_state / durable evidence authority
        |
        v
RepositoryContextProjection
        |  bounded, derived, rebuildable navigation/context state
        |
        +-------------------------------+
        |                               |
        v                               v
codesleuth_context_get              Mermaid source
exact-head bounded capsule          bounded presentation
for coding/review models            for humans/docs/reports
```

Optional structural providers such as Graphify do not sit beside or above this chain.
They feed candidate structure into CodeSleuth validation before anything enters the
`RepositoryContextProjection`.

The invariant is therefore:

> **Provider != projection != model context != presentation.**

These stages may carry related information, but they have different authority and
must never silently substitute for one another.

## 2. Source and evidence authority

The authoritative repository facts are current tracked Git source plus exact blob
identity. Durable review findings and acceptance history remain owned by the existing
`review_state` / EHA evidence discipline.

A graph relation is navigation/context. It is not sufficient evidence for a material
finding, edit, security claim, or acceptance decision.

Before a model edits code or records a material finding based on graph context, it must
reopen the relevant exact current source and verify the claim there.

## 3. RepositoryContextProjection role

`RepositoryContextProjection` is the only CodeSleuth repository-context graph contract.
It is:

- renderer-neutral;
- bounded;
- derived and rebuildable;
- exact-head/provenance aware;
- explicit about verified source versus review inference;
- safe to delete and reconstruct without losing repository truth.

No provider-specific graph identity, cache, database, export, or visualization may
become a parallel model-visible repository-context authority.

## 4. Model-facing consumption

For coding/review model orientation, the preferred interface is
`codesleuth_context_get`, not Mermaid and not raw provider output.

The context capsule must preserve all of these properties:

1. validate the saved projection before use;
2. bind to exact current Git HEAD;
3. fail closed when projection HEAD differs from current HEAD;
4. fail closed when verified SourceRefs are stale;
5. reuse the canonical bounded `repo_context_graph_query` selection;
6. return structured SourceRefs for the selected window;
7. expose explicit truncation/continuation state;
8. state that the projection is derived navigation/context;
9. require reopening exact source before edit or material finding;
10. treat optional Mermaid as secondary derived presentation only.

Raw `repo_context_graph_query` remains a valid lower-level tool, but it is still
bounded derived context and never evidence authority.

## 5. Mermaid role

Mermaid answers a presentation question, not an evidence question.

Mermaid source must:

- derive only from a saved `RepositoryContextProjection` or another explicitly named
  existing authority for a different view class;
- disclose projection/head identity for repository-context views;
- use the same neighborhood selection semantics as the canonical graph query;
- declare bounded/truncated state;
- distinguish review inference visually;
- never alter node/edge/projection identity;
- never become primary machine context merely because a model can read Mermaid text.

For repository context, Mermaid is **secondary derived presentation**. A coding agent
should normally consume the structured exact-head context capsule instead.

Protected-capability and EHA diagrams are separate derived views over their own
existing authorities. They must not be folded into `RepositoryContextProjection` merely
to create one giant graph.

## 6. Graphify role

Graphify is an optional structural extraction provider. Its useful responsibility is
deterministic topology discovery, especially AST-derived candidate nodes and edges.

Graphify output is not directly trusted as CodeSleuth verified source and is not a
parallel model context API.

The provider boundary is:

```text
CodeSleuth-selected tracked files
        |
        v
optional Graphify structural extraction
        |  candidate structure only
        v
CodeSleuth Graphify adapter
        |  exact path/relation/source/Git validation
        v
RepositoryContextProjection
```

Hard requirements:

- builtin repository mapping remains the default provider;
- Graphify remains explicit and optional;
- Graphify semantic/LLM backends remain disabled for this provider path;
- Graphify provider IDs are never canonical CodeSleuth graph IDs;
- Graphify `EXTRACTED` is not automatically `verified_source`;
- `INFERRED` / `AMBIGUOUS` output may only become `review_inference` or be dropped;
- unmapped provider relations fail closed rather than being renamed approximately;
- provider topology/community/centrality data may guide bounded root selection but may
  not change projection identity, evidence origin, or durable source truth;
- provider output must not bypass `RepositoryContextProjection` and become a second
  unbounded graph handed directly to coding/review models.

## 7. Separation of representation

The same repository relationship may have several representations:

```text
Provider candidate     machine extraction result
Projection element     normalized CodeSleuth graph contract
Context capsule        bounded model-facing orientation
Mermaid                human-facing presentation
Exact source           authoritative verification surface
```

Representations may be derived from one another only in the allowed direction. A
renderer label, provider community name, model interpretation, or diagram layout must
never flow backward into graph identity or evidence authority.

## 8. Consumer ordering

The expected model workflow is:

```text
1. obtain bounded exact-head context capsule
2. use adjacency/SourceRefs to choose where to inspect
3. reopen exact tracked source
4. reason about the material claim or edit
5. record evidence through the existing evidence authority
```

Mermaid may be attached for orientation, but does not replace steps 2-4.

The expected human workflow may prefer Mermaid first because visual relationship
presentation is useful to humans. That does not change the machine authority order.

## 9. Regression obligations

Changes touching any of these surfaces must preserve this contract:

- `pack/.opencode/tools/repo_context_graph.ts`
- `pack/.opencode/tools/codesleuth_context.ts`
- Graphify provider/adapter code
- `/repo-map`
- repository review Skills/Playbooks that consume graph context
- Mermaid repository-context rendering

Canonical regression tests must reject at least these drifts:

- context capsule no longer exact-head or stale-link fail-closed;
- Mermaid promoted to primary model context;
- Mermaid no longer declares itself derived presentation;
- Graphify becomes default or authoritative;
- provider result bypasses the CodeSleuth projection contract;
- model-facing instructions stop requiring exact-source reopening;
- query and Mermaid silently diverge into separate selection semantics.

## 10. Architecture boundary

This contract does not create a new SIB0 capability class. It hardens existing
`TOOL-EXTENSION` / graph-context behavior and the already accepted authority chain.

A change that intentionally makes Graphify, Mermaid, a provider cache, or any new graph
store authoritative beside/above `RepositoryContextProjection`, or that makes graph
relations sufficient evidence for findings, is an architecture change and must not be
smuggled through an ordinary provider/renderer refactor.
