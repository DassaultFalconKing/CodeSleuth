# RC6 live-dogfood repair plan

**Status:** implementation plan for the exact `b56ae39d8b98e1a67f933e03544c83869c3377f4` repeat-dogfood failures.  
**Evidence source:** `.codesleuth/reports/20260902T131918Z-rc6-live-dogfood-repeat.md` on the immutable `reports` branch.  
**Scope:** RC6 repair only. This plan does not alter report history, SIB/EHA authority, release refs, or RC7 planning.

## Repair invariants

1. Read-only repository analysis must not execute target-local OpenCode project configuration as host configuration.
2. If host/runtime isolation cannot be proven, analysis fails closed before claiming clean target identity.
3. A failed fresh-child attempt must be recorded durably as `STEP_ISOLATION_UNPROVEN` before same-session fallback work for that Step.
4. Continuation packets must not erase already-bound authoritative obligations to make validation succeed.
5. Authority relations used by a packet must be directionally valid and non-self-referential.
6. Scope patterns represent repository paths, not conceptual labels; a trailing directory literal authorizes descendants while ordinary file literals remain exact.
7. Derived change-surface evidence never expands mutation authority.

## LD-01: target-project runtime isolation

### Root cause

The installed wrappers provide an external writable CodeSleuth runtime through `OPENCODE_CONFIG_DIR`/`OPENCODE_CONFIG`, but that directory is additive in current OpenCode configuration discovery. Target-local `.opencode` project configuration can still be discovered and bootstrapped, allowing a newer host to rewrite tracked target package metadata.

### Changes

- Set `OPENCODE_DISABLE_PROJECT_CONFIG=1` in POSIX and PowerShell CodeSleuth OpenCode launchers.
- Keep the target repository itself as the working directory and readable evidence surface.
- Extend runtime tests to prove the isolation flag is part of both launch paths and to reject regressions that treat `OPENCODE_CONFIG_DIR` as sufficient isolation.
- Preserve exact-clean preflight/postcondition checks in live-dogfood acceptance; target dirtiness remains a fail-closed condition, never a compatibility-repair invitation.

## LD-02: durable isolation ordering

### Root cause

The command contract says to record `STEP_ISOLATION_UNPROVEN` before parent fallback, but the current implementation has no durable primitive whose event ordering can be inspected later. The controller can therefore reconstruct a nicer story in final prose than the execution trace supports.

### Changes

- Add append-only continuation isolation events bound to exact target SHA and Step id.
- Add `development_continuation_state_record_isolation_unproven` for the orchestration boundary to call immediately after fresh-child failure and before parent fallback.
- Automatically bind matching isolation event ids into the final continuation packet and return the resolved events on load.
- Update `/repo-continue` and the continuation Playbook Step instructions so final summaries derive isolation state from durable events.

## LD-03: monotonic packet obligations, relation direction, path semantics

### Root cause

Packet arrays are caller-optional, so retries can omit already-established prerequisites, predecessors, reading, gate obligations, decisions and uncertainty until formal save succeeds. Authority validation matches only relation + object, permitting directionally wrong edges and self-loops. Path validation checks traversal safety but accepts conceptual prose; directory literals do not match descendants.

### Changes

- On same-target/same-active-scope packet retries, preserve previously bound obligations monotonically: prerequisites, accepted predecessors, required reading, forbidden/adjacent restrictions, repo/hosted/live gate obligations, operator decisions, blockers and uncertainties. Narrowing/replacing them requires new authority/scope rather than omission.
- Reject self-loop authority edges used for continuation claims.
- Validate relation endpoints according to continuation relation semantics rather than object-only matching.
- Reject non-path conceptual values from path patterns.
- Give trailing `/` directory patterns descendant semantics; exact file literals stay exact; existing explicit glob patterns remain deterministic.
- Add regression witnesses reproducing the Aleph failure shapes.

## TDD sequence

1. Add regression tests for LD-01, LD-02 and LD-03 and observe failure on the exact candidate behavior.
2. Implement the minimum runtime, state-tool and contract changes.
3. Run focused Python and Bun suites.
4. Run `python -m ruff check .`, contributor anti-pattern scan and repo-wide pytest/Bun acceptance through hosted CI.
5. Re-run live dogfood separately against foreign exact targets before RC6 acceptance is restored. Hosted/unit green is necessary but does not replace this live witness.

## Completion criteria

The repair candidate is ready for a new live-dogfood repeat only when focused regressions and repo-wide hosted acceptance pass at one exact head. RC6 itself remains unaccepted until a new foreign-repository live run demonstrates: no target mutation, correctly ordered durable isolation events, monotonic DCP obligations, directionally valid authority, and faithful path-scope behavior.
