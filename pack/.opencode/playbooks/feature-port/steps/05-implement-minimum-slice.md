# Step: implement minimum target slice

Consume the proven identities, portable contract, ownership map, and acceptance matrix. Implement only the smallest target-native slice that can satisfy the requested behavior. Preserve host execution authority and existing CodeSleuth state/extension ownership.

Use `contract-triangulation` when implementation reveals an existing contract conflict. Use `forbidden-regression-ledger` when a newly discovered concrete bad state belongs to a contract. Do not upgrade lifecycle maturity merely because code was added.

Return changed paths, rationale, tests added/updated, exact resulting SHA or dirty-worktree identity, and any stop condition requiring architecture decision.
