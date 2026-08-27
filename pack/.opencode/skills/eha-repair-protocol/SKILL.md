---
name: eha-repair-protocol
description: Execute the minimum EHA repair loop for one recorded SIB blocker and return the fix through the release stream
slash: true
---

# EHA repair protocol

## Atomic contract

**Input:** one failed EHA campaign with recorded SIB level, blocker finding IDs, failing test/path, and reproduction evidence.

**Objective:** produce a minimum repair delta, regression coverage, focused repair tests, and a recorded repair decision without rewriting failed history.

**Output:** repair branch, repair commit SHA, regression/focused test evidence, and the next literal release-stream head SHA after integration.

**Stop:** the blocker classification does not match the failed SIB level, the repair would reopen architecture without explicit classification, or the failed SHA would be relabeled as PASS.

**Must not:** force-push or amend the failed SHA, carry unrelated feature work, start the next EHA campaign on the repair branch alone, or inherit SIB PASS from a predecessor SHA.

Read `docs/EHA-REPAIR-LOOP.md` and `docs/SIB-CANDIDATE-SELECTION.md`. An EHA campaign never repairs its own target. The repair branch is not a parallel SIB integration line.

After focused repair tests pass, integrate through the active `dev/release-X.Y.Z` branch. The resulting literal release-stream head is the next candidate. If integration creates a merge commit, that merge commit is the new EHA target. Tree equality with the repair commit does not transfer evidence.

Record the decision with `eha_state_record_repair`, then start a new EHA campaign on the integrated release-stream SHA.
