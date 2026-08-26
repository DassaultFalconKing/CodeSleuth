# Step: execute repair

Use `failed_campaign`. Load `eha-repair-protocol`. Branch from the failing SHA, apply the minimum repair delta, add a faithful regression test, run focused repair tests, and obtain the repair commit SHA.

Record the repair with `eha_state_record_repair`. Do not relabel the failed SHA as PASS.

Return only `repair_result`: repair branch, repair SHA, regression tests, focused test evidence, and recorded repair event ID.
