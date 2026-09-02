---
description: Resolve repository-native development authority, select the admissible next scope, map native gates, and emit an exact-head continuation packet without editing source
agent: build
---

Run CodeSleuth Playbook `repository-development-continuation` for:

$ARGUMENTS

This command is read-only analysis. It must discover how the target repository itself says development should continue. It must not invent a roadmap, revive superseded work, merge adjacent tracks, or write application/source files.

Read the Playbook manifest first and materialize exactly one `fresh_subagent` Step at a time. All authority and gate claims must be bound to the same clean exact target SHA and tracked Git blobs.

If the host cannot materialize a required fresh child Step, call `development_continuation_state_record_isolation_unproven` and durably record `STEP_ISOLATION_UNPROVEN` for that exact target and Step **before executing that Step in the current session**. Only after the tool returns the durable event id may same-session fallback begin. Do not silently claim fresh-context isolation or reconstruct isolation ordering later from narrative.

Do not repair the target in place. A failure encountered during this read-only command is evidence, not permission to mutate the environment. In particular, do not change `git config`, run a dependency install/update, rewrite lockfiles, switch tracked dependency pins, or modify repository policy merely to make discovery continue. When continuation would require such a repair, stop that path with `READ_ONLY_BOUNDARY_BLOCKED`, preserve the exact failing observation and required external remediation, and leave the target unchanged.

The final result must include:

- canonical planning authority;
- active implementation scope;
- accepted predecessors and required reading;
- allowed paths plus forbidden/adjacent paths;
- project-native verification gates classified by where they can actually be proven;
- a durable Development Continuation Packet id;
- current cloud-testability state from `native_gate_state_load`;
- every durable isolation event returned with the packet by `development_continuation_state_load`;
- any `STEP_ISOLATION_UNPROVEN` or `READ_ONLY_BOUNDARY_BLOCKED` condition encountered.

If planning or active-scope authority remains unproven, stop with `SCOPE_AUTHORITY_UNPROVEN`. Do not choose the most plausible file by filename, recency, prose quality, or model confidence.

If any required `REPO_PROVABLE` or `HOSTED_CI_PROVABLE` gate remains red or unexecuted, report `CLOUD_TESTABILITY_REMAINING`. Only after those gates are PASS may the result report `LIVE_HANDOFF_READY` for remaining live/runtime work.

Use `development_continuation_state_scope_guard` before suggesting or reviewing a proposed changed-path set. `UNDECLARED`, `ADJACENT_TRACK`, and `FORBIDDEN_BY_ACTIVE_SCOPE` never authorize automatic scope expansion. A declared path ending in `/` is a directory boundary and includes descendants; conceptual scope labels are not repository path patterns.
