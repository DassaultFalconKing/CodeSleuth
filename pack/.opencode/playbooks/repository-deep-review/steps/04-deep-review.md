# Step: deep review

Consume the bounded `review_map` and `contract_impact`. Review each material component/cross-cutting boundary using the atomic `repository-deep-review` Skill. Reopen exact source before accepting any finding.

Check identity/provenance, validation, failure handling, state transitions, concurrency/staleness, authorization/scope, persistence, compatibility, resource bounds, tests/CI, docs/runtime truth, and relevant forbidden regressions.

Use `forbidden-regression-ledger` only to audit the relevant contract-owned negative obligations; do not turn speculative risks into FR entries.

Return `verified_findings`: severity-grouped findings with exact evidence, violated contract/FR where applicable, checks actually run, praises worth preserving, and explicit coverage limitations.
