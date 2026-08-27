# Model context capsule

**Status:** operational feature population inside `CC-GRAPH`
**Authority:** [`CONTEXT-GRAPH-DISCIPLINE.md`](CONTEXT-GRAPH-DISCIPLINE.md)

CodeSleuth gives selected coding/review agents a bounded machine-facing context
capsule through `codesleuth_context_get`. The capsule is not another graph,
ledger, controller, or persistence plane. It is a strict read-only handoff over
the already accepted `RepositoryContextProjection`.

## Authority chain

```text
tracked Git source + blob identity
        |
        v
review_state
        |
        v
RepositoryContextProjection
        |
        +--> codesleuth_context_get --> selected model context
        |
        +--> Mermaid source ----------> optional secondary presentation
```

The capsule never promotes Mermaid, model output, or projection linkage into
source evidence. Material edits/findings still require reopening exact source.

## Exact-head rule

Before returning model context, `codesleuth_context_get` delegates to
`repo_context_graph_load`, which validates persisted projection identity and
audits current tracked-file blob identities. The tool fails closed when:

- the caller's optional `expectedHeadSha` differs from current Git `HEAD`;
- the projection's captured `headSha` differs from current `HEAD`;
- any verified `SourceRef` is stale against current tracked-file content.

A clean capsule therefore proves only that the derived projection window is
bound to the current head and its referenced blobs. It does not prove the
projection is complete or that a relationship is sufficient finding evidence.

## Selection and bounds

The capsule does not implement graph traversal. It delegates neighborhood
selection to `repo_context_graph_query`, preserving the accepted
roots/hops/relation/origin semantics, node/edge limits, truncation flags, and
continuation cursor. Returned compact members are resolved back to their
validated projection records so the coding model receives structured
`SourceRef` path/blob/line metadata rather than only display strings.

`coverage.savedMapTruncatedByAuthor`, `coverage.truncated`,
`coverage.fullyComplete`, and `coverage.nextCursor` must be honored. A model
must not infer repository-wide completeness from one bounded capsule.

## Mermaid

`includeMermaid` is opt-in. Mermaid is derived from the same projection and same
selection arguments and is labelled `secondary-derived-presentation`.

Mermaid is refused on continuation-cursor pages because the Mermaid tool has no
cursor-window contract. Returning a first-page diagram beside a later query
page would falsely imply correspondence, which is precisely the sort of tidy
lie software systems manufacture when nobody stops them.

## Access policy

`pack/.opencode/opencode.json` denies `codesleuth_context_*` globally and allows
`codesleuth_context_get` for OpenCode `build`. The bounded `repo-reviewer` and
`repo-scout` agents receive explicit per-agent permission in their frontmatter.
Other agents do not receive this capability by default.

This is an execution-policy boundary, not a secrecy boundary. If future context
must be cryptographically or repository-access confidential, use a separately
permissioned private repository/service rather than pretending a Git branch has
independent read ACLs.

## Non-goals

This feature does not add a model runtime, supervisor, agent loop, general tool
router, second evidence authority, shared context database, or hidden branch.
It is feature population inside the frozen `CC-GRAPH` capability class.
