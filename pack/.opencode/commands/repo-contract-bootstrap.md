---
description: Discover and user-adjudicate existing brownfield repository contracts before creating or extending the Protected Capability Registry
agent: build
---

Run CodeSleuth Playbook `repository-contract-bootstrap` for:

$ARGUMENTS

This command is for repositories whose contracts are still implicit or scattered through code, documentation, tests, schemas and operator behavior. It does not require an existing `docs/protected-capabilities.json`.

Read the Playbook manifest first and materialize one Step at a time. Keep exact-head identity throughout discovery and triangulation. Discovery outputs are candidates, never authority.

The adjudication Step must stop for explicit user decisions. Do not infer approval from discovery confidence, prior assistant prose, or a generic request to continue. Only record the user's named `adopt`, `adopt_unproven`, `reject`, or `defer` decisions.

Materialization may write `docs/protected-capabilities.json` only through `contract_bootstrap_state_materialize`. It never grants SIB acceptance or `PROTECTED` status, and the resulting tracked diff becomes a new candidate identity once committed.
