# Step: load failed campaign

Load `eha_state_load` for the requested review/campaign. Confirm a recorded FAIL verdict exists for the blocking SIB level and capture failing SHA, blocker finding IDs, failing test/path, and reproduction.

Return only `failed_campaign`: campaign ID, failing SHA, failed level, classification, and blocker evidence.
