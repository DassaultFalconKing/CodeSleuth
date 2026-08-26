---
description: Test one immutable exact HEAD through SIB0, SIB1, and SIB2 acceptance profiles
agent: build
---

Load the `eha-sib-acceptance` skill and perform an Exact-Head Acceptance campaign.

Requested target/scope:

$ARGUMENTS

Before testing, capture literal `git rev-parse HEAD`, branch, and dirty state.
The requested target SHA must equal literal current HEAD. Start or load
`review_state`, then call `eha_state_start_campaign`.

Run the SIB0, SIB1, and SIB2 profiles against the SAME immutable SHA. Do not
modify application/source files during this command. A failure is a valid EHA
result, not permission to repair the target in place.

For each level:

- verify the appropriate architecture/implementation/integration claim;
- record exact-source blockers with `review_state_record_finding`;
- persist PASS or FAIL with `eha_state_record_verdict`;
- include the actual profile/checks and blocker finding IDs.

If HEAD changes, stop and report `EHA INVALIDATED — HEAD CHANGED`.

At completion load `eha_state_load`, render `eha_state_mermaid` when useful,
and use `codesleuth-reports` to persist a human-readable EHA report containing
all three verdicts, claimable SIB degrees, evidence, limitations, and any failed
repair entry point. Do not merge, repair, skip, xfail, weaken, or reinterpret a
failing canonical contract during the EHA test campaign.
