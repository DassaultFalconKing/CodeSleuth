# Step: materialize user-approved contracts

Consume `user_adjudication` and reload the durable bootstrap state. Verify literal HEAD still equals the bootstrap target SHA before any write.

Call `contract_bootstrap_state_materialize` exactly once. It may create or extend `docs/protected-capabilities.json`, but it must refuse untracked collisions, duplicate existing contract ids, unresolved dependency ids, incompatible adoption decisions, moved HEAD, or a second materialization attempt.

Materialization records only the user's accepted brownfield contract meaning. It does **not** backdate acceptance:

- `AGREE + adopt` -> at most `implemented`;
- `UNPROVEN + adopt_unproven` -> at most `experimental`;
- `protected_at` remains null;
- no SIB1/SIB2/PROTECTED status may be inferred.

After the write, inspect the exact diff and report the new/changed tracked registry as a proposed repository change requiring the repository's normal review/commit process. Do not claim the bootstrap target itself has already accepted the newly materialized registry, because the write changes the worktree and therefore creates a new candidate identity once committed.

Return only `registry_materialization`: bootstrap id, old exact discovery SHA, registry path, adopted contract ids/statuses, and the explicit reminder that a committed registry requires fresh exact-head acceptance before any higher lifecycle claim.
