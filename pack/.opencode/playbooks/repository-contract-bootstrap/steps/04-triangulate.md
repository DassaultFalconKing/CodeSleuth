# Step: triangulate discovered contracts

Consume `candidate_contracts`. For each material proposal, use `contract-triangulation` against the exact target SHA and the narrowest exact code/config, normative/public documentation, and executable test evidence available.

Classify each proposal as exactly one of `AGREE`, `CODE_AHEAD`, `DOC_AHEAD`, `TEST_AHEAD`, `CONTRADICTED`, or `UNPROVEN`. Never average disagreement into a synthetic contract and never invent a missing evidence family.

Only **after** that classification is established, call `contract_bootstrap_state_record_candidate` exactly once for the proposed contract id with the final statement, final evidence paths/family absences, final triangulation status, affected paths/dependencies, and concrete forbidden-regression candidates. Do not record provisional classifications and do not create suffixed duplicates merely to correct earlier model output.

If exact evidence materially changes the proposed contract meaning rather than merely its wording, report the proposal as needing renewed discovery instead of silently substituting a different contract. Do not edit application source or the tracked registry in this Step.

Return only `triangulated_candidates`: durable candidate id, contract id, exact status, evidence triad or explicit absence, and the user decision choices that are actually legal. `AGREE` may be offered for `adopt`; `UNPROVEN` may be offered only for explicit `adopt_unproven`; drift or contradiction may only be rejected/deferred until resolved.
