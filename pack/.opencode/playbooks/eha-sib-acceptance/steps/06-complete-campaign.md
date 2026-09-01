# Step: complete campaign

Use `campaign_started`, the three SIB verdict outputs, and `report_path` from the completed `persist-report` step.

Call `eha_state_complete_campaign` for the same campaign ID with exactly that finalized report path. The completion tool must remain fail-closed: it may append `campaign_completed` only when literal current HEAD still equals the campaign target, SIB0/SIB1/SIB2 are all durably PASS, the report lives under `.codesleuth/reports/`, and the report front matter names the same exact `targetSha`.

Do not wait for or infer completion from a final provider frame after the durable completion event is written. Provider stream shutdown is transport state, not EHA authority.

Return only `campaign_completed`: campaign ID, target SHA, report path, and recorded time.
