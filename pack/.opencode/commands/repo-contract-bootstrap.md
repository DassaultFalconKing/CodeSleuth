---
description: Discover and user-adjudicate existing brownfield repository contracts before creating or extending the Protected Capability Registry
agent: build
---

Run CodeSleuth Playbook `repository-contract-bootstrap` for:

$ARGUMENTS

This command is for repositories whose contracts are still implicit or scattered through code, documentation, tests, schemas and operator behavior. It does not require an existing `docs/protected-capabilities.json`.

Read the Playbook manifest first and materialize exactly one isolated Step at a time. Keep exact-head identity throughout discovery and triangulation. Discovery outputs are candidates, never authority.

The Playbook ends with an `adjudication_packet`. Present that packet to the user from the primary controller and stop with `AWAITING_USER_ADJUDICATION`. Do not infer approval from discovery confidence, prior assistant prose, repository conventions, or a generic request to continue.

Only after the user explicitly names decisions may the primary controller call `contract_bootstrap_state_record_decision` for those candidate ids using one of `adopt`, `adopt_unproven`, `reject`, or `defer`. Preserve the user's actual instruction in `userApprovalStatement`; do not strengthen it.

If the user explicitly asks to materialize the accepted decisions, reload the exact bootstrap state and call `contract_bootstrap_state_materialize`. That bounded tool is the only route allowed to create or extend `docs/protected-capabilities.json`. It never grants SIB acceptance or `PROTECTED` status, and the resulting tracked diff becomes a new candidate identity once committed.
