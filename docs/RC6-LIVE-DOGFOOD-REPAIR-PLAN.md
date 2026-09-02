# RC6 live-dogfood repair plan

**Status:** IMPLEMENTED / HOSTED VERIFICATION IN PROGRESS / LIVE RE-DOGFOOD REQUIRED  
**Original candidate:** `b56ae39d8b98e1a67f933e03544c83869c3377f4`  
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

### Implemented repair

- `OPENCODE_DISABLE_PROJECT_CONFIG=1` is set by POSIX and PowerShell CodeSleuth launchers whenever the external read-only runtime (`CODESLEUTH_EHA_RUNTIME_CONFIG`) is active.
- The target repository remains the working directory and readable evidence surface; package metadata writes are redirected outside the tracked target.
- Regression tests require the project-config-disable flag in both launcher paths.
- Exact-clean preflight/postcondition remains the live acceptance boundary. A dirty target is evidence and a fail-closed condition, never a compatibility-repair invitation.

### Remaining proof

Hosted tests prove the launch contract, not the behavior of every real OpenCode host/version. A new foreign-repository live run must prove that tracked target `.opencode` metadata remains byte-clean before and after analysis.

## LD-02: durable isolation ordering

### Root cause

The command contract said to record `STEP_ISOLATION_UNPROVEN` before parent fallback, but the original implementation had no durable primitive whose event ordering could be inspected later. The controller could therefore reconstruct a nicer story in final prose than the execution trace supported.

### Implemented repair

- Added append-only continuation isolation events under `.opencode/state/development-continuation/isolation-events.ndjson`.
- Added `development_continuation_state_record_isolation_unproven`, bound to exact target SHA and Step id.
- `/repo-continue` and the repository-development-continuation Playbook require the durable event before same-session fallback begins.
- Matching exact-target isolation event ids are bound into the continuation packet; `development_continuation_state_load` exposes resolved events and fails if a referenced event disappears.

## LD-03: monotonic packet obligations, relation direction, path semantics

### Root cause

Packet arrays were caller-optional, so retries could omit already-established prerequisites, predecessors, reading, gate obligations, decisions and uncertainty until formal save succeeded. Authority validation matched only relation + object, permitting directionally wrong edges and self-loops. Path validation checked traversal safety but accepted conceptual prose; directory literals did not match descendants.

### Implemented repair

- Same-target/same-active-scope retries preserve previously bound obligations monotonically: planning/authority refs required by preserved claims, prerequisites, accepted predecessors, required reading, forbidden/adjacent restrictions, repo/hosted/live gate obligations, operator decisions, blockers and uncertainties.
- Positive `allowedPaths` are deliberately **not** unioned automatically. Mutation authority may narrow or become `NOT_DECLARED`; it must never expand because an earlier packet mentioned another path.
- Confirmed irreflexive semantic authority relations reject self-loops.
- Continuation authority validates directional endpoints, including `planning authority -> active scope` and `active scope -> accepted predecessor`.
- Non-path conceptual values fail closed as path patterns.
- Trailing `/` directory patterns include descendants; exact file literals remain exact; explicit glob patterns remain deterministic.
- Derived change-surface evidence remains non-authoritative and cannot grant positive path scope.

## TDD evidence

The tests-first regression commit was `02e23fea6114ed94ab714be5b2e555e828f21432`.

Hosted run `33643073832` captured the intentional RED phase: existing continuation smokes passed, while the new RC6 repeat-dogfood smoke failed because the durable `record_isolation_unproven` primitive did not exist on the original behavior.

The implementation was then introduced without rewriting that red evidence. Subsequent failures were debugged individually: one assertion was over-coupled to diagnostic wording, one wrong-direction fixture was contaminated by the newly correct monotonic predecessor history, and one existing wrapper contract required the literal `package metadata` documentation phrase. Those witnesses were corrected without weakening the production safety rules.

## Hosted completion criteria

Before this branch is eligible for another live run, one exact final head must pass:

1. contributor anti-pattern scan;
2. repo-wide Ruff;
3. Python 3.10/3.12 on Linux and Windows;
4. durable-state/context-graph smokes including `rc6_live_dogfood_repairs_smoke.ts`;
5. Graphify enabled-runtime acceptance;
6. TUI visual regression.

Any tracked documentation or test update creates a new exact head and requires fresh hosted acceptance.

## Live completion criteria

Hosted green changes status only to `READY_FOR_LIVE_DOGFOOD`.

RC6 itself remains unaccepted until a new foreign-repository live run demonstrates on exact targets:

- no target source/config/package-metadata mutation;
- `STEP_ISOLATION_UNPROVEN` is durably recorded before any fallback execution and is visible in the final packet;
- repeated packet saves cannot erase already-bound continuation obligations;
- wrong-direction/self-loop authority fails closed;
- trailing directory scope includes real descendants while conceptual labels do not become paths;
- target-native gates and uncertainties remain faithful rather than being simplified into a synthetic PASS.
