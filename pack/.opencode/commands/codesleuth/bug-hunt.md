---
description: Run the read-only bug-hunter Playbook before repair or merge decisions
agent: build
---

Execute the stored `bug-hunter` Playbook for:

$ARGUMENTS

Follow `docs/PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md`: keep OpenCode `build` as the primary controller, read the Playbook manifest first, materialize exactly one Step at a time, and prefer fresh host-native child context for each Step.

Stay read-only for application source. The final `codesleuth-reports` Step may write the normal local `.codesleuth/reports/` derived report. Do not fix findings, rewrite tests, or modify product code during the hunt.

Treat the contributor scanner, search results, PR summaries, generated graphs, and historical CI as candidate/navigation evidence only. Verify material findings against exact current source, consumers, tests, and canonical-gate reachability before assigning severity or `SAFE-TO-MERGE`.
