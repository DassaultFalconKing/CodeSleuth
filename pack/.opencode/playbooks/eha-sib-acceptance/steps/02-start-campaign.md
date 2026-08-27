# Step: start campaign

Use `candidate_identity`. Start or load `review_state`, then call `eha_state_start_campaign` with the exact SHA and release branch/scope.

If literal HEAD changes before verdict recording, stop with `EHA INVALIDATED — HEAD CHANGED`. Do not modify application source during this Playbook.

Return only `campaign_started`: review ID, campaign ID, exact target SHA, and scope.
