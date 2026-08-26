---
name: protected-capability-registry
description: Discover, query, maintain, and regression-check CodeSleuth protected capability contracts by triangulating current code, normative documentation, executable tests, dependency impact, and contract-owned forbidden regressions
---

# Protected Capability Registry

Use this skill whenever a task asks to:

- add or change a post-SIB2 feature;
- determine which accepted contracts a diff can affect;
- review a PR for regression against previously accepted behavior;
- extract a contract from current implementation, documentation, and tests;
- update or query the Protected Capability Registry;
- answer questions such as “which contracts concern persisted state/restart/controller ownership?”;
- classify a regression as SIB0-, SIB1-, or SIB2-origin;
- prepare an SIB/EHA, RC, or release acceptance plan.

Canonical authority:

- `docs/PROTECTED-CAPABILITY-CONTRACTS.md`
- `docs/protected-capabilities.json`
- `docs/STABLE-INTEGRATION-BASELINE.md`
- `docs/EXACT-HEAD-ACCEPTANCE.md`
- `docs/EHA-REPAIR-LOOP.md`

The registry is an index of accepted contracts and proof obligations. It is not a second source of product truth and it is not an excuse to infer semantics from ids or retrieval scores.

## 1. Core rule

A protected contract must be grounded in three evidence families:

```text
current code/config
+ normative/public documentation
+ executable acceptance/regression tests
= contract candidate
```

Do not promote a statement to `protected` from one evidence family alone.

If the sources disagree, classify drift instead of inventing a compromise:

- `CODE_AHEAD`
- `DOC_AHEAD`
- `TEST_AHEAD`
- `CONTRADICTED`
- `UNPROVEN`

The next action is to repair the stale source or make an explicit contract decision. Never silently edit the manifest to whichever source is most convenient.

## 2. Exact target first

Before contract extraction, impact analysis, or regression review:

1. record exact `git rev-parse HEAD` or exact PR head SHA;
2. record dirty state when working in a worktree;
3. identify the diff/range being evaluated;
4. read the exact manifest at that revision;
5. do not mix evidence from moving heads.

A registry entry may record historical `protected_at` evidence. That does not transfer exact-head acceptance to the current candidate.

## 3. Contract lifecycle

Use only these lifecycle states:

```text
experimental
implemented
sib1_accepted
sib2_integrated
protected
deprecated
removed
```

Promotion discipline:

```text
experimental
  -> implemented
  -> SIB1 accepted
  -> SIB2 integrated
  -> protected
```

Do not jump a capability to `protected` because its PR merged or its focused tests are green.

A `protected` record must include:

- stable id;
- capability class;
- public/architectural contract statements;
- code evidence;
- documentation evidence;
- test evidence;
- affected paths;
- dependency relations;
- exact/historical protection evidence;
- at least one contract-owned forbidden regression.

## 4. Every contract owns forbidden regressions

There is no substitute global bucket.

For every protected contract, inspect and maintain:

```text
forbidden_regressions[]
```

Each entry must have:

- stable `FR-*` id;
- `sib_origin` in `SIB0 | SIB1 | SIB2`;
- a concrete `must_not` statement;
- proof/evidence paths where available.

Interpretation:

- `SIB0` origin = architectural state that must not silently return;
- `SIB1` origin = capability/basic-contract state that must not return;
- `SIB2` origin = composition/end-to-end state that must not return.

A discovered EHA regression that is repaired and later accepted should leave behind both:

```text
positive proof: accepted behavior works
negative proof: the observed bad state is now a forbidden regression
```

Removing an `FR-*` entry is a contract change. Require explicit deprecation/removal/supersession rationale.

## 5. Querying the registry

The manifest is intentionally file-based.

### Normal/small registry

Prefer simple repository-native retrieval:

```text
rg/grep -> candidate ids/phrases -> paged read -> exact entry -> exact evidence
```

Search by:

- contract id;
- capability class;
- `public_contract` terms;
- `contract_fingerprint` keys/values;
- affected path;
- dependency id;
- `forbidden_regressions.must_not` text;
- SIB origin.

### Large registry with retrieval components already available

If the registry is genuinely large and the host already exposes suitable local retrieval, use:

```text
BM25 candidate retrieval
  + optional embedding retrieval
  -> optional reranker
  -> exact manifest re-read
  -> exact source/docs/tests re-read
```

BM25/embeddings/reranking are navigation only. They do not decide contract meaning.

Do not add a new heavyweight CodeSleuth search daemon, vector database, or model runtime merely to search this manifest. If retrieval infrastructure is absent, use grep plus bounded reads.

## 6. Contract extraction workflow

When asked to discover or update a contract:

### A. Locate the promise

Read the narrowest normative/public docs that describe what users/maintainers are entitled to rely on.

Capture exact statements, commands, schema keys, ownership rules, lifecycle promises, compatibility promises, or negative invariants.

### B. Locate implementation

Trace the promise into current code/config. Identify:

- entry point;
- owner;
- public surface;
- persisted state/schema where relevant;
- dependencies;
- failure behavior;
- affected paths.

Do not infer implementation from docs alone.

### C. Locate executable proof

Find focused acceptance/regression tests that prove the real contract boundary. Prefer black-box or integration coverage when the contract is user-visible or cross-component.

A mock-only unit test is not sufficient evidence for an integration promise merely because it contains the same noun.

### D. Triangulate

Classify:

```text
AGREE -> record/update contract candidate
DRIFT -> report CODE_AHEAD/DOC_AHEAD/TEST_AHEAD/CONTRADICTED/UNPROVEN
```

### E. Extract forbidden regressions

Ask separately for each SIB axis:

```text
SIB0: Which architectural state did acceptance establish must not return?
SIB1: Which capability failure state did acceptance establish must not return?
SIB2: Which integration/composition failure state did acceptance establish must not return?
```

Not every contract needs an entry from all three levels, but every protected contract needs at least one concrete forbidden regression.

### F. Write the manifest

Make the smallest semantic edit to `docs/protected-capabilities.json`.

Preserve stable ids. Do not reorder unrelated records merely for aesthetics.

For new features that have not yet completed SIB1/SIB2 promotion, record them as `implemented` (or the actual lifecycle state) rather than lying with `protected`.

## 7. Impact graph and affected closure

Use `affected_paths` to map the candidate diff to seed contracts.

`depends_on` means the current contract relies on another registered contract. Therefore when a dependency changes, compute the reverse dependency closure to find possible consumers.

Example:

```text
runtime.host <- cli <- update
            <- tui <- menu
            <- skills <- profiles
```

A runtime change seeds `runtime.host`; affected closure includes its consumers.

Do not rely only on path globs when exact code reading shows a semantic dependency missing from the graph. Correct the graph/manifest.

## 8. Gate selection

For ordinary development candidates:

```text
candidate gate
= always-run invariant core
+ affected protected-capability closure
+ new feature acceptance
```

The always-run core remains small and high value.

For a head being promoted under a claim that requires full acceptance:

```text
SIB2 / accepted integration head / RC / release
= FULL canonical protected-capability suite
+ claim-specific gates
```

Dependency-aware selection is an optimization for development. It must never be used to water down full SIB2 EHA or release acceptance.

If exact HEAD changes, rerun the profile required for the claim on the new exact SHA.

## 9. PR/review mode

For a diff or PR:

1. pin the exact base/head;
2. list changed paths;
3. query affected contracts;
4. compute reverse dependency closure;
5. read every affected contract's `forbidden_regressions`;
6. inspect unchanged consumers and tests, not only changed lines;
7. report any path by which a forbidden state can return;
8. identify missing tests/gates;
9. distinguish contract change from accidental regression.

A PR is not safe merely because the new feature tests pass.

The review question is:

> **Does this exact candidate add the intended behavior while preserving every affected protected contract and keeping its forbidden regressions absent?**

In `repo-review` read-only mode, do not edit source or the registry. Report manifest drift or missing entries as findings. Update the registry only when the user/task explicitly authorizes contract maintenance.

## 10. New feature acceptance

For a post-SIB2 feature, require two proof sets:

```text
A. new-feature proof
B. protected-contract preservation proof
```

If the feature creates a genuinely new fundamental capability class, stop treating it as ordinary feature population. Architecture has reopened; classify it as SIB0-impacting and establish a new SIB0 lineage.

If it stays inside an existing capability class, add its contract record at the honest lifecycle state and promote it only through the accepted SIB path.

## 11. Contract fingerprint checks

For properties that are structurally public, record concise fingerprint keys where useful:

- CLI commands/options;
- config keys;
- schema/version fields;
- persisted state paths/formats;
- environment variables;
- plugin/adapter interfaces;
- public paths;
- ownership/authority values.

A fingerprint change is a review trigger, not automatic proof of a breaking change.

Do not semantic-rerank or compare contracts by hash/id. Opaque ids identify records/blobs; meaning comes from exact contract statements and evidence.

## 12. Output format

When answering a contract query, report:

```text
Target SHA:
Query:
Matched contracts:
- id
  status
  why matched
  exact public contract
  forbidden regressions
  evidence: code / docs / tests
Affected closure (if a diff exists):
Required gate:
Unproven/drift:
```

When updating the registry, additionally report lifecycle/status changes and every added/removed/modified `FR-*` entry.

## 13. Stop conditions

Stop and escalate instead of silently editing when:

- code/docs/tests contradict one another materially;
- an alleged protected contract has no executable proof;
- a new feature requires a new capability class;
- a forbidden regression is being removed without an accepted contract decision;
- the dependency graph would exclude a known affected consumer;
- a candidate seeks SIB2/RC/release status with only a dependency-selected partial gate;
- the exact target SHA moved during acceptance.

## Canonical rule

> **Find the contract in code, promises, and tests; give every protected contract its own forbidden-regression ledger; use dependency-aware gates to stay efficient; and use full exact-head acceptance whenever the maturity/release claim requires the whole system.**
