---
description: Test one immutable exact release-stream HEAD through SIB0, SIB1, and SIB2 acceptance profiles
agent: build
---

Run CodeSleuth Playbook `eha-sib-acceptance` for this request:

$ARGUMENTS

Read `docs/EHA-OPERATING-PLAYBOOK.md`, `docs/PROVENANCE-WATERMARK.md`, and `docs/PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md`, then resolve `pack/.opencode/playbooks/eha-sib-acceptance/playbook.json`.

For a trusted GitHub EHA bridge request, run only `python scripts/eha_candidate_status.py` for Step 1 and use its bounded JSON as `candidate_identity`. The bridge has already fetched and frozen `refs/remotes/origin/dev/release-X.Y.Z`; do not rediscover refs, inspect local convenience branches, or enumerate the host persistence root. Outside the bridge, normal future-SIB selection still resolves the literal head of the active `dev/release-X.Y.Z` branch.

Do not preload every Step prompt. Materialize exactly one Step at a time and load only the atomic Skills declared for that Step. Prefer a fresh host-native subagent per Step.

Immediately after the bounded candidate check, start a fresh `review_state` checkpoint, call `provenance_state_bind` once with the stable opaque actor for this producer session, then call `eha_state_start_campaign`. Do not preload later Step prompts before the campaign exists. Run the SIB0, SIB1, and SIB2 profiles against the SAME immutable selected SHA. Do not modify application/source files during this command. A failure is a valid EHA result, not permission to repair the target in place.

If HEAD changes, stop and report `EHA INVALIDATED — HEAD CHANGED`. At completion load `eha_state_load` and `provenance_state_load`, render `eha_state_mermaid` when useful, and use `codesleuth-reports` to persist a human-readable EHA report containing the verified `provenance` watermark. Provenance is attribution metadata only and does not participate in SIB claimability.
