---
name: repository-deep-review
description: Evidence-first protocol for large-repository mapping, documentation, and in-depth review with durable checkpoints
---

# Repository Deep Review

Use this protocol for whole-repository documentation, architecture analysis,
large PR reviews, and other tasks where correctness depends on understanding
more than a handful of files.

This skill is executed by OpenCode's primary `build` agent. `build` already has
the native provider-specific controller prompt for the selected model
(`codex.txt`, `anthropic.txt`, `kimi.txt`, and so on). Do not invent a second
supervisor or replace that controller. Use OpenCode tools, native `explore` /
`general` Task subagents, and CodeSleuth `repo-scout` as needed.

## Core invariants

1. The selected model's context window is working memory, not the repository.
2. File discovery is not semantic coverage.
3. A scout summary is a lead, not evidence.
4. Material findings require exact current source evidence.
5. Durable review state survives compaction; conversation history does not own
   project truth.
6. Never claim a command/test/check passed unless it actually ran successfully.
7. Review the real target (commit/range/worktree), not a stale summary of it.

## Phase 0: establish authority

Before broad reading:

- capture `git rev-parse HEAD`;
- capture dirty state;
- identify the requested ref/range/scope;
- locate project instruction/authority files (`AGENTS.md`, `README*`, ADRs,
  architecture docs, manifests, CI, build/test scripts);
- read `.codesleuth/reports/INDEX.md` and any matching prior report;
- start or load `review_state_*`.

If the worktree is dirty, distinguish committed evidence from worktree evidence.
If the target moves during review, do not silently mix revisions.

## Phase 1: deterministic inventory

Call `repo_inventory` before opening many files.

Use the manifest to understand:

- top-level ownership boundaries;
- languages/file families;
- tests, migrations, configs, docs, generated/vendor/build areas;
- unusually broad or isolated components.

Do not paste the full manifest into the conversation. Query/scout bounded path
prefixes instead.

## Phase 2: architecture map

Read the smallest authoritative entry points first: package/workspace manifests,
startup code, routing/registration, schemas/contracts, migrations, test/CI
entrypoints, and existing architecture docs.

Delegate independent file-search work to native `explore` and independent
component/contract inspection to `repo-scout`. A scout should receive one
bounded component or contract surface. `build` should retain only the
component summary, exact candidate locations, and cross-component questions.

Build a working map of:

- entry points;
- module/package ownership;
- public contracts and schemas;
- control flow and data flow;
- persistence and external services;
- authorization/scope boundaries;
- background/concurrent work;
- verification and deployment paths.

Persist the working map as a bounded RepositoryContextProjection with
`repo_context_graph_save`: nodes use the closed kind set (file, symbol,
component, contract, test, workflow, external) and edges the closed relation
set. Mark elements `verified_source` only when you captured them from tracked
source yourself; model or scout assertions must stay `review_inference` with
the `review_inference` relation. Graph relations are navigation/context, not
sufficient finding evidence: reopen exact source before recording any material
finding.

Checkpoint when the map is coherent enough to explain how the target works.

## Phase 3: deep review

Review component by component, then perform cross-cutting passes.

High-value cross-cutting passes:

- identity/provenance and canonical-vs-derived data;
- validation and fail-open/fail-closed behavior;
- error propagation and partial failure;
- state transitions, leases, retries, idempotency, recovery;
- concurrency/races and stale state;
- authorization, tenant/scope isolation, secrets;
- persistence/transaction boundaries and migrations;
- API/schema compatibility and downstream consumers;
- resource bounds, pagination, truncation, large inputs;
- tests that prove adversarial boundaries rather than happy paths;
- CI/local verification parity;
- documentation/runtime truth.

For a diff review, follow changed symbols outward to unchanged consumers and
inward to dependencies. A locally correct diff can still violate a repository
contract.

## Phase 4: evidence ledger

Before accepting a material defect, reopen the exact source and call
`review_state_record_finding` with its line range. The tool captures the actual
excerpt plus blob/worktree identity.

Do not record:

- style-only preferences unless requested;
- speculative risks with no concrete failing contract;
- duplicate symptoms of the same root cause as independent high-severity bugs.

A finding should explain:

- observable contract violated;
- concrete path to failure;
- affected scope;
- why existing tests/guards do not prevent it;
- smallest appropriate correction direction.

## Phase 5: context discipline for very large repositories

Even with a 1M-token model:

- search before reading;
- inspect targeted ranges before whole large files;
- avoid generated/build/vendor/lock data unless relevant;
- keep noisy tool output bounded;
- use isolated scouts for independent components;
- persist/update the bounded context-graph projection after each mapping pass;
- checkpoint after each component/cross-cutting pass;
- after compaction, reload state and continue from `next`;
- reload a compact relevant projection neighborhood with
  `repo_context_graph_load` / `repo_context_graph_query` instead of
  reconstructing repository topology from old chat history;
- rehydrate exact evidence only when needed for reasoning/final reporting.

Do not maintain a giant always-loaded project instruction file. Stable rules
belong in concise project instructions; task-specific detail belongs in skills
and durable state.

## Phase 6: documentation mode

For repository documentation, derive statements from verified code/config/tests.
Document:

- purpose and boundaries;
- architecture/components;
- important data/control flows;
- configuration and environment assumptions;
- external integrations;
- persistence and migrations;
- build/test/verification commands;
- deployment/runtime topology;
- known limitations and unresolved contradictions.

Use source paths/symbols as provenance. Clearly label inferred behavior. Never
turn historical handoffs or generated artifacts into current authority unless
the repository declares them authoritative.

Diagrams are optional, never mandatory. When a diagram materially helps,
derive it from the verified projection with `repo_context_graph_mermaid`
instead of hand-writing topology; treat the generated Mermaid source as a
rebuildable presentation of that projection, not as evidence or as a second
source of architecture truth.

## Phase 7: completion contract

Final review/documentation output must include:

- exact target identity;
- scope and coverage achieved;
- verification actually executed;
- material findings or documented architecture;
- evidence/provenance;
- unresolved questions;
- explicit areas not reviewed or not proven.

A review is complete when the requested scope is covered and the remaining
unknowns are honestly bounded, not when the context window is full.

## Phase 8: persist an analytical report

Load `codesleuth-reports` and write a markdown report under
`.codesleuth/reports/` following `.opencode/CODESLEUTH-REPORTS.md`. Update
`INDEX.md`. This is for later CodeSleuth sessions and other coding assistants;
it is not a second supervisor. The only required write during a read-only
review is that reports folder.
