---
description: Build or refresh a bounded repository architecture map with optional Mermaid projection
agent: build
---

Build or update the bounded RepositoryContextProjection for the requested scope
using the `repository-deep-review` protocol's architecture-mapping phase. Stay
on OpenCode's primary `build` agent so the native provider-specific controller
prompt for the selected model remains in effect.

Requested scope/focus:

$ARGUMENTS

If the arguments are empty, map the tracked repository at the current
worktree/HEAD.

Route:

1. Establish authority first: capture HEAD/dirty state and start or load a
   durable review checkpoint with `review_state_start` / `review_state_load`.
2. Call `repo_inventory` before opening many files.
3. Persist or refresh a bounded linkage map with `repo_context_graph_save`:
   nodes limited to the closed kinds (file, symbol, component, contract, test,
   workflow, external), edges to the closed relation set. Mark elements
   `verified_source` only when you captured them from tracked source yourself;
   model/scout assertions stay `review_inference` with the `review_inference`
   relation. Never dump an unbounded graph into context.
4. Return a compact bounded summary via `repo_context_graph_query`.
5. Only when a diagram was requested (or materially helps), derive Mermaid
   source with `repo_context_graph_mermaid`. Mermaid is derived presentation,
   not evidence and not a second architecture authority.

Stay read-only for application source; the only writes are the ignored
`.opencode/state/` boundary used by these tools. Graph relations are
navigation/context, not finding evidence: reopen exact source before recording
any material finding. Delegate bounded read-only inspection to `repo-scout`
or `explore` Task subagents where useful.
