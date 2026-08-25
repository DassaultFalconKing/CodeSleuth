---
description: Run an evidence-first in-depth repository or PR review
agent: repo-reviewer
---

Perform an in-depth review using the repository-deep-review protocol.

Requested scope/ref/question:

$ARGUMENTS

If the arguments are empty, review the tracked repository at the current
worktree/HEAD. Record the exact HEAD and dirty state before drawing conclusions.

Start a durable review, inventory the repository, map the relevant architecture,
partition independent areas into bounded scout tasks, verify every accepted
finding against exact source lines, checkpoint after each component, and finish
with explicit coverage and limitations.

For a diff/range review, inspect both the changed code and unchanged consumers,
contracts, tests, migrations, documentation, and CI that can make the change
incorrect. Do not review only the textual diff.
