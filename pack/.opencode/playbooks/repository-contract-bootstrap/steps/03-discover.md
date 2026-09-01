# Step: discover candidate contracts

Consume `bootstrap_inventory` and load `contract-archaeology`. Inspect one bounded component at a time. Search exact tracked code/config, normative or public documentation, executable tests/CI and durable schemas/operator surfaces for contract-shaped behavior.

Record only plausible candidate contracts through `contract_bootstrap_state_record_candidate`. At this stage use the best evidence-backed provisional triangulation classification, but do not manufacture missing evidence and do not call any discovery a repository contract.

Every candidate requires at least one exact tracked evidence path, affected paths, and at least one concrete forbidden-regression candidate. Repeated implementation behavior alone is insufficient evidence of intended public or architectural meaning.

Return only `candidate_contracts`: bootstrap ID, candidate IDs/contract IDs, evidence-family coverage, unresolved questions, and explicit discovery gaps.
