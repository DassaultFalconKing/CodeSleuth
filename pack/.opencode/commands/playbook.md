---
description: Run a stored CodeSleuth Playbook one isolated Step at a time
agent: build
---

Run CodeSleuth Playbook `$1` for this request:

$2

Read `docs/PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md`, then resolve `.opencode/playbooks/$1/playbook.json` first, then `pack/.opencode/playbooks/$1/playbook.json`. The overlay wins when both exist.

Do not preload every Step prompt. Keep OpenCode `build` as the primary controller. Determine the next runnable Step from the manifest and retained outputs. Materialize exactly one Step at a time. For `execution=skill`, load only the named Skill. For `execution=step`, read only the named Step prompt and load only its declared Skills.

Prefer a fresh host-native subagent for each Step so the child receives fresh context and the parent retains only the bounded Step result. The child must not launch another orchestration layer. After completion, retain/checkpoint only the declared output and advance to the next Step.

If the host cannot provide fresh-Step isolation, execute at most one Step in the current context at a time and do not claim strict eviction; report `STEP_ISOLATION_UNPROVEN` when relevant.

Stop on a Playbook/Skill stop condition. Do not improvise around exact-head, contract, architecture, or acceptance blockers.
