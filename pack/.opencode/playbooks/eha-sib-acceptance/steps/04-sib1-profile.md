# Step: SIB1 profile

Use `sib0_verdict` and `campaign_started`. Load `eha-campaign-evidence` and verify every SIB0 capability class has a real basic implementation on the same immutable SHA.

Record blockers with `review_state_record_finding` when needed, then `eha_state_record_verdict` for `SIB1`. A SIB1 PASS is claimable only when SIB0 on the same SHA also passed.

Return only `sib1_verdict`: verdict, claimable flag, profile, and blocker IDs.
