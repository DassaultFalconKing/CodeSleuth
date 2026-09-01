---
description: Test one immutable exact release-stream HEAD through SIB0, SIB1, and SIB2 acceptance profiles
agent: build
---

Run CodeSleuth Playbook `eha-sib-acceptance` for this request:

$ARGUMENTS

Read `docs/EHA-OPERATING-PLAYBOOK.md`, `docs/PROVENANCE-WATERMARK.md`, and `docs/PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md`, then resolve `pack/.opencode/playbooks/eha-sib-acceptance/playbook.json`.

For a trusted GitHub EHA bridge request, run only `python scripts/eha_candidate_status.py` for Step 1 and use its bounded JSON as `candidate_identity`. The bridge has already fetched and frozen `refs/remotes/origin/dev/release-X.Y.Z`, created a fresh durable review checkpoint, bound its verified `provenance_state` sidecar through the canonical watermark implementation, and appended the exact-target `campaign_started` event before provider/model execution. Do not rediscover refs, inspect local convenience branches, enumerate the host persistence root, rebind provenance, or create a second campaign.

Outside the trusted bridge, normal future-SIB selection still resolves the literal head of the active `dev/release-X.Y.Z` branch and starts a fresh review/EHA campaign through the normal state tools.

Do not preload every Step prompt. Materialize exactly one Step at a time and load only the atomic Skills declared for that Step. Prefer a fresh host-native subagent per Step.

Immediately after the bounded candidate check, load `review_state`, `provenance_state`, and `eha_state`. In trusted-bridge mode, require the existing provenance sidecar and fresh incomplete campaign to match the supplied exact target and consume them without mutation. Outside trusted-bridge mode, when no matching campaign exists, start a new review checkpoint, call `provenance_state_bind` once for that producer session, then call `eha_state_start_campaign`.

Run the SIB0, SIB1, and SIB2 profiles against the SAME immutable selected SHA. Do not modify application/source files during this command. A failure is a valid EHA result, not permission to repair the target in place.

If HEAD changes, stop and report `EHA INVALIDATED — HEAD CHANGED`. At completion load `eha_state_load` and `provenance_state_load`, render `eha_state_mermaid` when useful, and use `codesleuth-reports` to persist a human-readable EHA report containing the verified `provenance` watermark. Then append the durable `campaign_completed` handshake. Provenance is attribution metadata only and does not participate in SIB claimability.
