# Step: audit regressions and affected closure

Consume only contracts whose current meaning is sufficiently proven. Audit each contract's own `forbidden_regressions` using `forbidden-regression-ledger`. For a diff/path query, compute direct seeds and reverse dependency closure with `dependency-impact-closure`.

Return relevant `FR-*` ids, missing/weak ledger entries, affected consumer contracts, unmatched changed paths, and any stale dependency edge. A known consumer missing from the graph is a blocker to using that graph for gate reduction.
