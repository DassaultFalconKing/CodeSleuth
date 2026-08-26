---
description: Repair a recorded EHA blocker without rewriting the failed exact target
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
7. obtain the new candidate SHA;
8. record the repair decision/branch/candidate/regression/focused evidence with
   `eha_state_record_repair` against the failed campaign.

Do not amend, force-push, rewrite, or relabel the failed SHA as PASS. Do not
carry unrelated cleanup or feature work into the repair. If the repair changes
the fundamental capability inventory or authority model, record
`architecture_reopened` rather than pretending it is a local repair.

After the repair is committed, the new SHA is only an EHA candidate. Start a
new EHA campaign for it with `eha_state_start_campaign`; do not inherit SIB0,
SIB1, or SIB2 PASS from the predecessor. Do not merge the repair merely because
focused tests pass.
