---
description: Run the repository-deep-review Playbook for a repository, PR, or broad review
agent: build
---

Execute the stored `repository-deep-review` Playbook for:

$ARGUMENTS

Follow `docs/PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md`: keep `build` as primary controller, read the Playbook manifest first, materialize one Step at a time, and prefer fresh host-native child context for each Step.

Stay read-only for application source. The existing `.codesleuth/reports/` report write is allowed by the Playbook. Do not replace the Playbook with the legacy monolithic review Skill; the current `repository-deep-review` Skill is only a bounded-slice competence.
