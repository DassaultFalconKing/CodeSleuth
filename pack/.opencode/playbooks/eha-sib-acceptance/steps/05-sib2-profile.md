# Step: SIB2 profile

Use prior verdict outputs and `campaign_started`. Load `eha-campaign-evidence` and run the full canonical integration profile on the same immutable SHA, including the `TUI visual regression / Ubuntu` job from `docs/TUI-VISUAL-REGRESSION.md` when applicable.

Record blockers with `review_state_record_finding` when needed, then `eha_state_record_verdict` for `SIB2`. SIB2 becomes claimable only when SIB0, SIB1, and SIB2 all passed on that SHA.

Return only `sib2_verdict`: verdict, claimable flags for all three levels, profile, artifact references, and blocker IDs.
