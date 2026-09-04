# Step: prepare user adjudication

Consume `triangulated_candidates` and load the durable bootstrap state. Produce a compact decision table containing candidate id, proposed contract statement, triangulation status, evidence-family coverage, forbidden-regression summary, and the actions that would be legal if the user later chooses them.

This isolated Step prepares information only. It must not ask on behalf of the primary controller, call `contract_bootstrap_state_record_decision`, call `contract_bootstrap_state_materialize`, or infer approval from discovery confidence, prior model prose, repository conventions, or a generic request to continue.

Legal choices to present:

- `AGREE` -> `adopt` may later materialize as `implemented`;
- `UNPROVEN` -> only explicit `adopt_unproven`, later materialized as `experimental`;
- `CODE_AHEAD`, `DOC_AHEAD`, `TEST_AHEAD`, `CONTRADICTED` -> only `reject` or `defer` until drift is resolved and re-triangulated.

Return only `adjudication_packet`: bootstrap ID, exact discovery SHA, one row per durable candidate, allowed actions, and explicit `AWAITING_USER_ADJUDICATION` status.

The Playbook ends here. The primary controller may cross the authority boundary only after receiving an explicit user decision for named candidates.
