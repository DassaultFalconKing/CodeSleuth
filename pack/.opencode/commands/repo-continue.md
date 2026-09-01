---
description: Resolve repository-native development authority, select the admissible next scope, map native gates, and emit an exact-head continuation packet without editing source
agent: build
---

Run CodeSleuth Playbook `repository-development-continuation` for:

$ARGUMENTS

This command is read-only analysis. It must discover how the target repository itself says development should continue. It must not invent a roadmap, revive superseded work, merge adjacent tracks, or write application/source files.

Read the Playbook manifest first and materialize exactly one `fresh_subagent` Step at a time. All authority and gate claims must be bound to the same clean exact target SHA and tracked Git blobs.

The final result must include:

- canonical planning authority;
- active implementation scope;
- accepted predecessors and required reading;
- allowed paths plus forbidden/adjacent paths;
- project-native verification gates classified by where they can actually be proven;
- a durable Development Continuation Packet id;
- current cloud-testability state from `native_gate_state_load`.

If planning or active-scope authority remains unproven, stop with `SCOPE_AUTHORITY_UNPROVEN`. Do not choose the most plausible file by filename, recency, prose quality, or model confidence.

If any required `REPO_PROVABLE` or `HOSTED_CI_PROVABLE` gate remains red or unexecuted, report `CLOUD_TESTABILITY_REMAINING`. Only after those gates are PASS may the result report `LIVE_HANDOFF_READY` for remaining live/runtime work.

Use `development_continuation_state_scope_guard` before suggesting or reviewing a proposed changed-path set. `UNDECLARED`, `ADJACENT_TRACK`, and `FORBIDDEN_BY_ACTIVE_SCOPE` never authorize automatic scope expansion.
