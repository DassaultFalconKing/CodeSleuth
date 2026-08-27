---
description: Show durable EHA campaigns, SIB verdicts, and repair lineage
agent: build
---

Load the `eha-campaign-evidence` skill, then load the durable acceptance ledger with `eha_state_load`.

Requested review/campaign:

$ARGUMENTS

Report, without changing repository state:

- review ID;
- every EHA campaign ID and exact target SHA;
- SIB0/SIB1/SIB2 PASS/FAIL/PENDING;
- which SIB degrees are actually claimable on each SHA;
- blocker finding IDs and summaries for failed levels;
- repair decisions, repair branches, candidate SHAs, regression tests and focused-test evidence;
- predecessor/successor campaign relationships.

Render `eha_state_mermaid` after the textual status when there is more than one campaign or any repair lineage. Use its default versioned JSON envelope, report the exact ledger provenance and selection/truncation fields, and present `mermaidSource` to the user. Use explicit campaign/repair bounds for large histories and preserve its omission markers. Treat the Mermaid output as a derived view of the ledger, not as acceptance evidence by itself; a displayed repair/candidate edge never transfers a verdict between exact SHAs. Request `responseFormat: mermaid_source` only for an explicitly legacy caller.
