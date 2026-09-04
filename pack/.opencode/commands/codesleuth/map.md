---
description: Run the repository-map Playbook for a bounded context graph and optional Mermaid view
agent: build
---

Execute the stored `repository-map` Playbook for:

$ARGUMENTS

Keep OpenCode `build` as primary controller. Read only the Playbook manifest and current Step. The result is a bounded derived RepositoryContextProjection; it is navigation/context, not repository authority or sufficient finding evidence.

Apply [`docs/GRAPH-CONSUMPTION-CONTRACT.md`](../../../../docs/GRAPH-CONSUMPTION-CONTRACT.md) to every provider/query/rendering path. Provider output is candidate structure, `RepositoryContextProjection` is the single normalized repository-context graph contract, the exact-head context capsule is the preferred model-facing consumer, and Mermaid is secondary derived presentation.

When handing graph context to a coding or review model, prefer
`codesleuth_context_get`. It validates the projection against exact current HEAD
and current tracked-file blob identities, then reuses the canonical
`repo_context_graph_query` selection to return a bounded structured SourceRef
capsule with continuation. A stale or wrong-head projection must fail closed.

Provider choice must be explicit in the result. Use an explicit request first; otherwise
read `contextGraph.provider` from `.opencode/review-pack-user.json` when present and
default to `builtin`. If the selected provider
names `graphify`, call `repo_context_provider_status`, require the exact compatible
optional runtime, enumerate a bounded tracked-file manifest, and use
`repo_context_provider_extract`. Never auto-install or silently fall back after an
explicit incompatible Graphify request. Provider candidates still pass through exact
source review and `repo_context_graph_save` validation. Never hand raw Graphify output
to a coding/review model as an alternate repository graph authority.

When a Mermaid view is requested, pass explicit roots/hops/relation/origin and
node/edge bounds when the requested scope supplies them. Mermaid is optional
secondary presentation, not the primary machine context. The Mermaid tool must
reuse the query selection, disclose selection totals/truncation/projection and
Git provenance, and emit no edge whose endpoints are outside the returned
window. A zero-link selection is a valid explicit result; never fill it with
model-invented relationships. Mermaid is not attached to continuation-cursor
pages because the renderer has no cursor-window contract.

For protected-contract impact use `/repo-contracts`, whose Mermaid view is read
directly from `docs/protected-capabilities.json`. For campaign/SIB/repair lineage
use `/eha-status`, whose Mermaid view is read from `eha.ndjson`. Those are
separate authorities and must not be folded into RepositoryContextProjection.
