# Repository context graph and Mermaid discipline

**Status:** Accepted for the `mermaid_context_discipline` slice
**Classification:** TOOL-EXTENSION + SKILL-EXTENSION + DOCS
**Adapted from:** Aleph_Rugent ADR 0003 / G1 graph-and-context-projection discipline, re-expressed with repository/Git semantics instead of FollowTheMoney (FtM) semantics. No FtM ontology is introduced.

## One-chain authority

```text
canonical Git source (tracked files + blob identity)
        |
        v
durable review state (.opencode/state/reviews, review_state_*)
        |  evidence/progress authority; survives compaction
        v
bounded RepositoryContextProjection (.opencode/state/context-graphs)
        |  derived, rebuildable linkage/context state
        +--------------------+
        |                    |
        v                    v
compact OpenCode model   deterministic Mermaid source
context (bounded query   (repo_context_graph_mermaid;
 windows, continuation)  docs/reports presentation)
```

Each layer may only be derived from the layer above it. Nothing downstream is
authoritative for anything upstream:

- Git/current source plus blob identity is the **source authority**.
- `review_state` remains the durable review/evidence/progress authority.
- The RepositoryContextProjection is bounded, derived, rebuildable linkage and
  context state. It can be deleted and rebuilt from source plus review state at
  any time.
- Mermaid output is a human-readable rendering of the projection. It is not
  source evidence, not durable model memory, not repository truth, and never
  the only machine-readable architecture representation.
- OpenCode model context stays ephemeral working memory.

## What was implemented

- `pack/.opencode/tools/repo_context_graph.ts` — OpenCode-native tools:
  - `repo_context_graph_save`: validate and persist/update a bounded projection
    under `.opencode/state/context-graphs/` (below the existing ignored OpenCode
    state boundary; no new tracked or project-authoritative format). Semantic
    validation reports all indexed node/edge violations in one pass, and
    `validate_only: true` performs the same validation without writing state.
  - `repo_context_graph_load`: load by id / linked review / session / latest,
    verify identity integrity, and report stale verified linkage against
    current Git blobs.
  - `repo_context_graph_query`: bounded neighborhood queries with strict
    node/edge limits, explicit truncation, and continuation cursors.
  - `repo_context_graph_mermaid`: deterministic Mermaid flowchart SOURCE
    derived from the projection. No mmdc/Puppeteer/Chromium/SVG: rendering is
    explicitly deferred (see below).
- `/repo-map` command routing to this capability.
- Minimal integration notes in the `repository-deep-review` skill,
  `repo-reviewer`, and `repo-documenter`.

## Projection contract

Versioned (`schemaVersion: 1`) and renderer-neutral. Required fields:
`schemaVersion`, `projectionId`, exact `headSha`, optional `reviewId`, `scope`,
`nodes`, `edges`, and explicit bounds/truncation metadata.

- Nodes use stable semantic IDs over a closed kind set: `file`, `symbol`,
  `component`, `contract`, `test`, `workflow`, `external`. The set is
  deliberately small; CodeSleuth does not model every software-engineering
  concept.
- Edges use a closed relation set limited to what real CodeSleuth
  review/documentation needs: `imports`, `calls`, `implements`, `registers`,
  `persists_to`, `reads_from`, `tests`, `configures`, `documents`,
  `depends_on`, `review_inference`. Free-form relation strings are rejected.
- Every source-derived node/edge retains a SourceRef: tracked path, current
  Git blob hash captured server-side at save time, and an optional exact line
  range. Path handling reuses the review_state conventions (worktree escape is
  refused; untracked paths are refused). A lone `startLine` is normalized to a
  single-line range (`endLine = startLine`); `endLine` without `startLine`
  remains invalid.

### Save validation ergonomics

The save tool's schema describes its cross-field origin/evidence constraints,
and execution performs a consolidated semantic pass rather than failing on the
first discoverable rule. Violations identify their payload location, for
example `nodes[3]` or `edges[11]`.

`validate_only: true` is a no-write dry run. It resolves current Git/blob
evidence and computes the would-be projection identity, but it does not create
a projection file or session/latest/review pointer. Invalid dry runs return all
collected semantic violations; ordinary saves reject the same set atomically in
one consolidated error.

This validation convenience does not weaken source authority. It only reduces
iteration cost for callers constructing a projection.

### Identity

All identities are SHA-256 over explicit NUL-separated semantic field lists
(`codesleuth-repo-context-*-v1` tags), mirroring Aleph_Rugent's G1 rule that
identity never depends on presentation. Node IDs cover kind+key; edge IDs cover
relation plus both endpoint identities; the projection ID covers headSha,
review binding, scope prefix, and the sorted node/edge ID sets. Display labels,
Mermaid aliases, layout, and other presentation metadata are never identity
inputs: relabeling a node does not change any identity.

Diagnostic/presentation code avoids re-prepending a kind when a semantic key
already starts with that same `kind:` prefix, so payloads such as
`component:export-pipeline` are not reported as
`component:component:export-pipeline`. This is presentation-only and does not
change identity inputs.

### Verification vs inference

Elements carry exactly one origin:

- `verified_source` — requires a server-captured SourceRef against a tracked
  file. Only elements captured this way may use it.
- `review_inference` — requires an explanatory note, must use the
  `review_inference` relation, and must not attach SourceRefs. A model/scout
  assertion can never become `verified_source` merely because a model emitted
  it; promotion requires re-capture from source by an agent.

Both directions are enforced at save time and re-enforced by integrity checks
at load time (persisted state whose recomputed identities do not match its
declared content fails closed). Graph relations are navigation/context, not
sufficient finding evidence: material findings still require reopening exact
source and recording evidence via `review_state_record_finding`.

### Bounds

Model-visible operations enforce node/edge limits. When available data exceeds
a limit, responses set `truncated=true`, expose totals, and return a
continuation cursor so a later bounded query resumes without ever silently
reporting a complete map or dumping the full repository graph into model
context. Saved projections default to "truncated subset" unless the author
explicitly asserts completeness.

## Mermaid rules

Mermaid source is generated FROM the projection only:

- stable internal aliases (`n0`, `n1`, ...) assigned deterministically;
- untrusted labels escaped (`"` -> `#quot;`, `<`/`>` entity-escaped,
  backticks removed, control characters already rejected at ingestion), so no
  hidden instructions derived from source content can be smuggled into markup
  or comments;
- truncated views render an explicit "bounded subset" marker;
- review-inference nodes/edges are styled dashed and visually distinct from
  verified source linkage, with a static legend comment.

Rendering to SVG (mmdc/Chromium/Puppeteer), interactive graph UIs, and TUI
features are out of scope for this slice and remain deferred, consistent with
Aleph_Rugent's own deferral of its renderer runtime until after typed
contracts.

## Resume flow

During architecture mapping the reviewer persists/updates the bounded
projection bound to the review checkpoint. After compaction or restart the
reviewer loads `review_state` plus a compact relevant projection neighborhood
(`repo_context_graph_load` / `repo_context_graph_query`) instead of
reconstructing repository topology from old chat history. Stale verified
linkage (changed/untracked blobs, moved HEAD) is reported on load so drifted
maps are re-verified instead of trusted.

## Scope guarantees

This slice introduces no independent model runtime, no agent loop, no tool-call
router, no replacement review engine, no renderer daemon, no interactive graph
UI, no TUI feature, and no new source-of-truth database. State lives under the
existing ignored `.opencode/state/` boundary and stays rebuildable.
