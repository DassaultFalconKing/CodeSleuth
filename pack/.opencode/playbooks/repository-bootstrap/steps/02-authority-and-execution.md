# Step 2 — map authority, execution, tests, and externals

Use the retained `identity_inventory`. Do not broaden the scope without evidence that the omitted area is required.

Find and read authority candidates when present, including README*, AGENTS.md, CONTRIBUTING*, ARCHITECTURE*, DESIGN*, ADR/*, docs/*, ROADMAP*, SECURITY*, package/build manifests, CI definitions, deployment runbooks, environment files, schema/contracts, and API specs.

For authority candidates record:

- document or artifact;
- claimed role;
- actual scope;
- freshness;
- authority confidence;
- conflicts.

Do not treat README prose as stronger than current executable source/config merely because it is documentation. Preserve contradictions instead of silently selecting a winner.

Establish executable structure from verified evidence:

- build path;
- run path;
- entrypoints;
- runtime components;
- process boundaries;
- network/API boundaries;
- storage/database dependencies;
- external services;
- model/runtime dependencies;
- CLI/TUI/UI/server components;
- deployment paths.

Attach evidence files to each important component or boundary. A directory name alone is not evidence that a component exists.

Find the test and CI model:

- unit, integration, end-to-end, smoke, and acceptance tests;
- gate scripts;
- CI workflows;
- lint/typecheck/static analysis.

Run only safe checks whose required environment is already available. Never report PASS for a check that was not actually executed. Use PASS, FAIL, NOT RUN, BLOCKED, or NOT APPLICABLE.

For every external repository, submodule, binary, or service that matters, record:

- name and source;
- exact revision/version when available;
- why it is required;
- whether it is source authority or runtime dependency;
- whether it is inside the current review scope.

Treat a submodule gitlink SHA as provenance. Treat a merely adjacent/untracked source tree as UNTRACKED EXTERNAL and do not mix its findings with the parent repository.

Output `authority_execution` with the authority map, executable structure, test/CI model, external dependency map, contradictions, executed checks, and remaining UNKNOWN items.
