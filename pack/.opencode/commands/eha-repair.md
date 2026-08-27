---
description: Repair a recorded EHA blocker and return it through the release stream
agent: build
---

Run CodeSleuth Playbook `eha-repair` for this request:

$ARGUMENTS

Read `docs/EHA-REPAIR-LOOP.md` and resolve `pack/.opencode/playbooks/eha-repair/playbook.json`. Load the durable EHA ledger with `eha_state_load` before editing.

Materialize exactly one Step at a time. Prefer a fresh host-native subagent per Step.

Follow the normative EHA repair loop: preserve the exact failed SHA, make the minimum repair delta, add regression coverage, run focused repair tests, record with `eha_state_record_repair`, integrate through the active `dev/release-X.Y.Z` branch, and capture the resulting literal release-stream head SHA as the next candidate.

Do not amend, force-push, rewrite, or relabel the failed SHA as PASS. The repair branch is not a parallel SIB integration line. If integration creates a merge commit, the merge commit is the new EHA target.
