# Step: triangulate discovered contracts

Consume `candidate_contracts`. For each material candidate, use `contract-triangulation` against the exact target SHA and the narrowest exact code/config, normative/public documentation, and executable test evidence available.

Classify each candidate as exactly one of `AGREE`, `CODE_AHEAD`, `DOC_AHEAD`, `TEST_AHEAD`, `CONTRADICTED`, or `UNPROVEN`. Never average disagreement into a synthetic contract and never invent a missing evidence family.

If the provisional candidate record needs correction after exact triangulation, record a new candidate with a new contract id suffix only when the prior candidate cannot be safely represented; otherwise stop and report the mismatch for repair of the bootstrap proposal. Do not edit application source or the tracked registry in this Step.

Return only `triangulated_candidates`: candidate id, contract id, exact status, evidence triad or explicit absence, and the user decision choices that are actually legal. `AGREE` may be offered for `adopt`; `UNPROVEN` may be offered only for explicit `adopt_unproven`; drift or contradiction may only be rejected/deferred until resolved.
