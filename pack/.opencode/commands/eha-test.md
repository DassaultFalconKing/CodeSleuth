---
description: Test one immutable exact release-stream HEAD through SIB0, SIB1, and SIB2 acceptance profiles
agent: build
---

Run CodeSleuth Playbook `eha-sib-acceptance` for this request:

$ARGUMENTS

Read `docs/EHA-OPERATING-PLAYBOOK.md` and `docs/PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md`, then resolve `pack/.opencode/playbooks/eha-sib-acceptance/playbook.json`.

For normal future-SIB selection, the target must be selected from the literal head of the active `dev/release-X.Y.Z` branch. For the current line this means `dev/release-0.4.0`. Capture the release branch ref and its full SHA, then verify the checkout's literal `git rev-parse HEAD` equals that selected SHA.

Do not preload every Step prompt. Materialize exactly one Step at a time and load only the atomic Skills declared for that Step. Prefer a fresh host-native subagent per Step.

Before testing, start or load `review_state`, then call `eha_state_start_campaign`. Run the SIB0, SIB1, and SIB2 profiles against the SAME immutable SHA. Do not modify application/source files during this command. A failure is a valid EHA result, not permission to repair the target in place.

If HEAD changes, stop and report `EHA INVALIDATED — HEAD CHANGED`. At completion load `eha_state_load`, render `eha_state_mermaid` when useful, and use `codesleuth-reports` to persist a human-readable EHA report.
