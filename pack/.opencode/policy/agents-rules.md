# CodeSleuth workflow rules (managed block)

This block is maintained by CodeSleuth when `policy.enforceAgentsMdRules` is enabled. This policy feature owns only the text between its markers. Repository/user instructions and other explicitly managed CodeSleuth blocks outside these markers are outside this feature's ownership and must be preserved.

- Host owns model, controller, session, permissions, tool routing, and execution. CodeSleuth provides discipline and control surfaces; it does not replace the host controller.
- Resolve exact Git identity (exact HEAD/SHA, dirty state, base branch) before interpreting changes or making integration/acceptance claims.
- Classify each material change as: ordinary feature work inside the current architecture; stale/divergent Semantic Refit; or architecture change that reopens convergence. Historical green CI does not transfer to a new SHA.
- Exact-head acceptance (EHA): testing is separate from repair. A failed acceptance target stays failed; repair creates a new SHA and a new campaign.
- SIB0/SIB1/SIB2 claims apply only when the repository has adopted that baseline model; do not assume unproven degrees.
- Preserve user work and configuration. Do not widen permissions, discard work, or run destructive reset/clean/force operations without explicit user authority.
- Do not silently copy historical implementation hunks or treat reports/graphs as stronger evidence than exact current source.
- Managed CodeSleuth instructions do not erase repository-specific sub-tree AGENTS.md files or direct user instructions; direct user instructions take precedence when they conflict with convenience guidance.
