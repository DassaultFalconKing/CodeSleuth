# Step 3 — build evidence, architecture, and risk map

Use `identity_inventory` and `authority_execution`. Keep all conclusions evidence-classified.

If CodeSleuth is available:

1. inspect `.codesleuth/reports/` and its index;
2. reuse an existing report only when its target HEAD and scope match;
3. otherwise treat older reports as predecessor/stale evidence and use them only for history or delta analysis;
4. create or refresh a bounded repository inventory when useful;
5. build a bounded RepositoryContextProjection when useful;
6. preserve durable findings with file/blob evidence references;
7. distinguish verified graph edges from REVIEW_INFERENCE;
8. never treat Mermaid or another renderer as evidence authority.

After inventory and authority discovery, construct an architecture map covering:

- COMPONENTS;
- ENTRYPOINTS;
- DATA FLOWS;
- CONTROL FLOWS;
- DEPENDENCIES;
- CONFIGURATION;
- EXTERNAL BOUNDARIES;
- TEST/GATE BOUNDARIES.

Every important node or edge needs an evidence source. If multiple architectures remain plausible, present competing interpretations rather than inventing certainty.

Perform a bounded risk review at least across:

- correctness;
- portability;
- reproducibility;
- dependency/version coherence;
- supply chain;
- unsafe path handling;
- config drift;
- state corruption;
- concurrency;
- error handling;
- observability;
- test coverage;
- documentation/code divergence;
- external dependency assumptions.

Do not repair findings in this bootstrap Playbook.

Output `architecture_risks` containing the evidence-aware architecture map, risk findings with severity/location/evidence/impact/recommendation/confidence, competing interpretations, and unresolved UNKNOWN items.
