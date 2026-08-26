---
description: Repair a recorded EHA blocker and return it through the release stream
agent: build
---

Load the `eha-sib-acceptance` skill and the current durable EHA ledger with
`eha_state_load`.

Requested failed campaign/finding:

$ARGUMENTS

Follow the normative EHA repair loop:

1. identify and preserve the exact failed SHA and recorded SIB blocker;
2. confirm the blocker classification matches the failed level;
3. create/use a repair branch derived from the failed SHA;
4. make the minimum repair delta only;
5. add a regression test faithful to the observed failure;
6. run focused repair tests;
7. obtain the repair commit SHA;
8. record the repair decision/branch/repair SHA/regression/focused evidence with
   `eha_state_record_repair` against the failed campaign;
9. integrate that repair through the active `dev/release-X.Y.Z` branch;
10. capture the resulting literal release-stream head SHA; that exact
    integration SHA is the next SIB candidate.

Do not amend, force-push, rewrite, or relabel the failed SHA as PASS. Do not
carry unrelated cleanup or feature work into the repair. If the repair changes
the fundamental capability inventory or authority model, record
`architecture_reopened` rather than pretending it is a local repair.

The repair branch is not a parallel SIB integration line. Do not start the next
future-SIB EHA campaign directly on the repair branch merely because focused
tests pass. First integrate the repair into `dev/release-X.Y.Z`; then start a
new EHA campaign on the resulting literal release-stream head.

If integration creates a merge commit, the merge commit is the new EHA target.
Tree equality with the repair commit does not transfer evidence. The new target
inherits no SIB0, SIB1, or SIB2 PASS from the predecessor.
