# Step: SIB0 profile

Use `campaign_started`. Load `eha-campaign-evidence` and verify architectural completeness for the frozen SHA: capability inventory, ownership, controller/runtime boundaries, and absence of duplicate authority.

Record material blockers with `review_state_record_finding`, then `eha_state_record_verdict` for `SIB0` with PASS or FAIL, profile summary, evidence, and blocker finding IDs.

Return only `sib0_verdict`: verdict, claimable flag, profile, and blocker IDs.
