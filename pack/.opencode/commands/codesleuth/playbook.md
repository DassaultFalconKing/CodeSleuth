---
description: Run a stored CodeSleuth Playbook one isolated Step at a time
agent: build
---

If `$1` is empty, do not execute a Playbook. Resolve and show the same deterministic overlay-over-pack catalog exposed by `/codesleuth/playbooks`, including each Playbook ID, origin, one-line summary, and exact `/codesleuth/playbook <id>` invocation. Then stop so the operator can select an ID.

Run CodeSleuth Playbook `$1` for this request:

$2

Read `docs/PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md`, then resolve `.opencode/playbooks/$1/playbook.json` first, then `pack/.opencode/playbooks/$1/playbook.json`. The overlay wins when both exist.

Do not preload every Step prompt. Keep OpenCode `build` as the primary controller. Determine the next runnable Step from the manifest and retained outputs. Materialize exactly one Step at a time. For `execution=skill`, load only the named Skill. For `execution=step`, read only the named Step prompt and load only its declared Skills.

Prefer a fresh host-native subagent for each Step so the child receives fresh context and the parent retains only the bounded Step result. The child must not launch another orchestration layer. After completion, retain/checkpoint only the declared output and advance to the next Step.

The controller must not silently fall back. If the host cannot materialize the required fresh child, emit `STEP_ISOLATION_UNPROVEN` before executing the Step in the current session. Execute at most one Step in the current context at a time, do not claim strict eviction, and preserve the isolation limitation in the bounded Step result whenever it matters to acceptance.

Stop on a Playbook/Skill stop condition. Do not improvise around exact-head, contract, architecture, host-boundary, or acceptance blockers.
