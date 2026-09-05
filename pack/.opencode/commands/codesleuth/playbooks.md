---
description: Browse resolved CodeSleuth Playbooks without executing them
agent: build
---

Browse the available CodeSleuth Playbooks for this repository. Do not execute a Playbook.

Use the existing CodeSleuth playbook catalog as the source of discovery: project overlay `.opencode/playbooks/` wins over the installed distribution pack for the same ID. Do not invent IDs from memory, command documentation, or model guesses, and do not maintain a second catalog.

Render the deterministic browse view produced from the resolved catalog: for every Playbook show its ID, origin (`overlay` or `pack`), one-line summary/description, and exact invocation:

`/codesleuth/playbook <id>`

If no Playbooks are discovered, say so explicitly. Stop after the catalog so the operator can choose what to run.
