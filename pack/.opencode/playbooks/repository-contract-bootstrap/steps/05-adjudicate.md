# Step: user adjudication boundary

Consume `triangulated_candidates` and load the durable bootstrap state. Present a compact decision table containing candidate id, proposed contract statement, triangulation status, evidence-family coverage, forbidden-regression summary, and allowed actions.

This Step is an authority boundary. **Do not call `contract_bootstrap_state_record_decision` unless the user has explicitly instructed the current controller to adopt, adopt-unproven, reject, or defer the named candidate(s).** Silence, a generic request to continue, prior model prose, or discovery confidence is not approval.

Legal adoption rules are enforced again by the state tool:

- `AGREE` -> `adopt` may later materialize as `implemented`;
- `UNPROVEN` -> only explicit `adopt_unproven`, later materialized as `experimental`;
- `CODE_AHEAD`, `DOC_AHEAD`, `TEST_AHEAD`, `CONTRADICTED` -> no adoption until the drift is explicitly resolved and re-triangulated.

Record the user's actual approval instruction in `userApprovalStatement`; do not fabricate a stronger statement.

If user decisions are incomplete, stop with `AWAITING_USER_ADJUDICATION` and the bootstrap ID. Do not proceed to materialization.

Return `user_adjudication` only when every candidate selected for adoption has an explicit durable decision and the user has asked to materialize or continue with those decisions.
