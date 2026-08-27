---
description: Run the repository-map Playbook for a bounded context graph and optional Mermaid view
agent: build
---

Execute the stored `repository-map` Playbook for:

$ARGUMENTS

Keep OpenCode `build` as primary controller. Read only the Playbook manifest and current Step. The result is a bounded derived RepositoryContextProjection; it is navigation/context, not repository authority or sufficient finding evidence.

When handing graph context to a coding or review model, prefer
`codesleuth_context_get`. It validates the projection against exact current HEAD
and current tracked-file blob identities, then reuses the canonical
`repo_context_graph_query` selection to return a bounded structured SourceRef
capsule with continuation. A stale or wrong-head projection must fail closed.

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
