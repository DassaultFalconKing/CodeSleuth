---
description: Query one protected contract or run the full protected-capability assessment Playbook
agent: build
---

Requested contract query / diff / maintenance task:

$ARGUMENTS

For one narrow registry lookup, load the atomic `protected-capability-registry` Skill directly.

For a diff/PR, contract maintenance, forbidden-regression audit, impact closure, or SIB/EHA/RC/release preparation, execute the stored `protected-capability-assessment` Playbook one isolated Step at a time under `docs/PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md`.

Pin the exact target before conclusions. In read-only review mode report registry drift rather than editing it. Do not promote lifecycle status without the required exact SIB evidence.
