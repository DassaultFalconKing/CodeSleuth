# Step: map bounded projection

Use exact target identity. Call `repo_inventory` before broad reading. For each bounded component needed by the requested scope, use `repository-deep-review` to establish verified entry points, ownership, contracts, tests, and relationships.

Provider selection is explicit. If no provider is requested, use `builtin`. Report
availability with `repo_context_provider_status`. For `builtin`, retain the existing
exact-source mapping flow. For explicitly requested `graphify`, first construct a
bounded tracked-file manifest from Git/repository inventory, then call
`repo_context_provider_extract` with `provider: graphify`. Do not scan untracked files.
Review its diagnostics and candidate `projectionInput` values, reopen exact source for
material relationships, and pass the chosen bounded candidates through
`repo_context_graph_save`; the provider never writes projection state directly.
If topology-assisted presentation is requested, save/validate the projection first,
then pass provider hints to `repo_context_graph_topology`. Use its exact returned roots
for both query and Mermaid rendering, report stale/omitted/fallback metadata, and never
feed community or centrality into projection identity or evidence origin.

Persist/update only a bounded RepositoryContextProjection with `repo_context_graph_save`. Mark tracked-source facts `verified_source`; model/scout assertions remain inference. Query a compact neighborhood with `repo_context_graph_query`.

Generate Mermaid with `repo_context_graph_mermaid` only when requested or materially useful. Return projection scope, provenance/truncation state, and optional Mermaid. Graph relations remain navigation/context, not finding evidence.
