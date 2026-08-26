# Step: verify port

Review the resulting target slice against the portable contract, target ownership map, acceptance matrix, unchanged consumers, protected contracts, and relevant forbidden regressions.

Use `repository-deep-review` only for bounded affected slices. Use `dependency-impact-closure` for the changed path set. Run the applicable executable tests and report only checks that actually ran.

Return `PASS`, `FAIL`, or `NOT_FULLY_PROVEN`, exact candidate identity, findings, affected-contract preservation status, and remaining environment/coverage limitations. Do not call a focused port test SIB/EHA evidence unless the required exact-head profile also ran.
