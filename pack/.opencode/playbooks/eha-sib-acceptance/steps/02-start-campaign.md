# Step: resolve campaign

Use `candidate_identity`, then call `eha_state_load` before attempting any campaign mutation.

If the trusted GitHub bridge has already created a fresh incomplete campaign whose exact target SHA and release branch match `candidate_identity`, reuse that campaign. Its `campaign_started` ledger event is controller authority established before provider/model execution. Do **not** call `eha_state_start_campaign`, create another review checkpoint, replace the campaign id, or reinterpret its scope.

Outside trusted-bridge mode, when no matching fresh campaign exists, start or load `review_state` and call `eha_state_start_campaign` with the exact SHA and release branch/scope as before.

Fail closed instead of reusing a campaign that targets another SHA/branch, already contains a FAIL, is already completed, or cannot be confirmed from durable state. If literal HEAD changes before verdict recording, stop with `EHA INVALIDATED — HEAD CHANGED`. Do not modify application source during this Playbook.

Return only `campaign_started`: review ID, campaign ID, exact target SHA, target branch, scope, and whether authority was `trusted_prestarted` or `model_started`.
