# Step: discover candidate contracts

Consume `bootstrap_inventory` and load `contract-archaeology`. Inspect one bounded component at a time. Search exact tracked code/config, normative or public documentation, executable tests/CI and durable schemas/operator surfaces for contract-shaped behavior.

Produce candidate **proposals only** in this Step. Do not call `contract_bootstrap_state_record_candidate` yet: discovery has not established the final triangulation status, and an append-only candidate ledger must not preserve a provisional classification as if it were adjudication-ready evidence.

Every proposal must contain a stable proposed contract id, concise statement, capability class/id proposal, exact candidate code/doc/test evidence paths or explicit family absence, affected paths, dependency hypotheses, at least one concrete forbidden-regression candidate, and the question that exact triangulation must answer next. Repeated implementation behavior alone is insufficient evidence of intended public or architectural meaning.

Return only `candidate_contracts`: bootstrap ID, proposed contract ids/statements, evidence-family coverage, triangulation questions, unresolved questions, and explicit discovery gaps. These proposals are Step output, not durable repository contract authority.
