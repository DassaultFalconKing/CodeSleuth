---
description: Resume one durable brownfield contract-bootstrap session by id, apply only explicit user decisions, and optionally materialize them
agent: build
---

Resume a previously completed `repository-contract-bootstrap` session for:

$ARGUMENTS

This command is a **primary-controller human-authority boundary**, not an analytical Playbook. It must not dispatch an isolated subagent to decide repository contracts.

Required procedure:

1. Require the user to name the `bootstrapId` being resumed. If it is absent, load only the latest id for navigation and present it; do not silently apply decisions to it.
2. Call `contract_bootstrap_state_load` for that exact bootstrap id. Stop if exact HEAD, tracked-worktree cleanliness, or evidence blob integrity fails.
3. Show the candidate ids, contract ids, triangulation states and current latest decisions before mutation.
4. Apply only decisions explicitly present in the user's current instruction using `contract_bootstrap_state_record_decision`:
   - `adopt` only for `AGREE`;
   - `adopt_unproven` only for `UNPROVEN`;
   - `reject` or `defer` where explicitly requested.
5. Preserve the user's actual decision text in `userApprovalStatement`. Do not strengthen, generalize or infer an approval.
6. Do **not** materialize merely because decisions were recorded. Call `contract_bootstrap_state_materialize` only when the same current user instruction explicitly requests materialization.
7. If materialization occurs, report that `docs/protected-capabilities.json` is now a tracked/untracked worktree change representing `NEW_UNCOMMITTED_CANDIDATE`; the old bootstrap SHA remains the evidence identity until that change is committed and re-accepted.

Never infer SIB1, SIB2 or `PROTECTED` maturity from brownfield adoption. Never use CodeSleuth's own self-registry as authority for the target repository.
