---
description: Run an evidence-first in-depth repository or PR review
agent: build
---

Perform an in-depth review using the repository-deep-review protocol. Stay on
OpenCode's primary `build` agent so the native provider-specific controller
prompt for the selected model remains in effect. Do not switch to a custom
supervisor agent.

Load the `repository-deep-review` skill and follow it.

For a diff/PR or any post-SIB2 feature/regression review, also load the
`protected-capability-registry` skill. Pin the exact base/head, query
`docs/protected-capabilities.json`, map changed paths to protected contracts,
compute the affected reverse dependency closure, and inspect every matched
contract's own `forbidden_regressions` ledger. New-feature tests are not enough
when an accepted behavior can regress.

Stay read-only for application source. The required exception is writing
`.codesleuth/reports/` so later sessions in this worktree can reuse the analysis.
Reports stay local-only by default; fresh clones do not receive report bodies unless
a maintainer sanitizes and commits them. Load `codesleuth-reports` at completion and persist a
markdown report plus `INDEX.md`.

Requested scope/ref/question:

$ARGUMENTS

If the arguments are empty, review the tracked repository at the current
worktree/HEAD. Record the exact HEAD and dirty state before drawing conclusions.

Stay read-only; do not modify repository files except `.codesleuth/reports/`. Start a durable review,
inventory the repository, map the relevant architecture, and partition
independent areas into bounded Task subagents (`explore` for file search,
`repo-scout` for a component/contract slice). Verify every accepted finding
against exact source lines, checkpoint after each component, and finish with
explicit coverage and limitations.

For a diff/range review, inspect both the changed code and unchanged consumers,
contracts, tests, migrations, documentation, CI, Protected Capability Registry
entries, and forbidden regressions that can make the change incorrect. Do not
review only the textual diff. If code/docs/tests disagree with a registry entry,
report contract drift rather than editing the manifest in read-only review mode.
