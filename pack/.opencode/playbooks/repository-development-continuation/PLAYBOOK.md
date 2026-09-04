# Repository Development Continuation Playbook

Reconstructs the target repository's own development authority, active scope and native verification gates, then emits a durable exact-head continuation packet without editing application/source files.

Use through `/repo-continue`. Every analytical Step declares `fresh_subagent` isolation; durable typed state carries authority and gate evidence between Steps. The Playbook fails closed when planning/active-scope authority is unproven and never expands a scope merely because another path appears relevant.

## Fresh-subagent fallback contract

`fresh_subagent` is an execution claim. If the host cannot prove that a required fresh child was materialized, the controller must call `development_continuation_state_record_isolation_unproven` for the exact target SHA and Step id and receive the durable `STEP_ISOLATION_UNPROVEN` event **before executing that Step in the current session**.

Same-session fallback may continue useful read-only analysis only after that durable event exists. The resulting continuation packet must bind the event and final reporting must derive isolation status from `development_continuation_state_load`, not reconstruct it later from prose.

A fallback Step with `STEP_ISOLATION_UNPROVEN` must never be described as fresh-context isolated.
