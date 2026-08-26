---
name: protected-capability-registry
description: Discover, query, maintain, and regression-check CodeSleuth capability contracts by triangulating current code, normative documentation, executable tests, dependency impact, and each contract's own forbidden-regression ledger
---

# Protected Capability Registry

Use this skill for post-SIB2 feature work, PR/regression review, contract extraction, Protected Capability Registry maintenance, impact/gate selection, or SIB/EHA/RC/release preparation.

Canonical authority:

- `docs/PROTECTED-CAPABILITY-CONTRACTS.md`
- `docs/protected-capabilities.json`
- `docs/STABLE-INTEGRATION-BASELINE.md`
- `docs/EXACT-HEAD-ACCEPTANCE.md`
- `docs/EHA-REPAIR-LOOP.md`

The registry is a queryable contract index. It is not a second product authority and retrieval scores never define semantics.

## 1. Exact target first

Before extraction/review:

1. pin exact HEAD or PR head SHA;
2. record dirty state where applicable;
3. identify exact base/head diff;
4. read the registry at that exact revision;
5. never mix evidence from moving heads.

Historical `protected_at` evidence does not transfer EHA to descendants.

## 2. Three-source rule

Derive contract meaning from:

```text
current code/config
+ normative/public documentation
+ executable acceptance/regression tests
```

No one family is sufficient alone.

If they disagree, classify drift:

- `CODE_AHEAD`
- `DOC_AHEAD`
- `TEST_AHEAD`
- `CONTRADICTED`
- `UNPROVEN`

Do not invent a compromise or silently edit the manifest to match the easiest source.

## 3. Contract lifecycle

Use only:

```text
experimental
implemented
sib1_accepted
sib2_integrated
protected
deprecated
removed
```

Promotion:

```text
experimental -> implemented -> SIB1 accepted -> SIB2 integrated -> protected
```

A merge or focused green test does not make a contract protected.

## 4. Every contract owns forbidden regressions

**Every contract record, at every lifecycle state, must contain a non-empty `forbidden_regressions` ledger.**

Before protection, entries describe candidate/observed negative states associated with the contract and the proof expected to exclude them. As SIB/EHA accepts the relevant behavior, those entries become normative preservation obligations. At `protected`, later release work must keep the accepted forbidden states absent unless an explicit contract change supersedes them.

Each entry must have:

- stable `FR-*` id;
- `sib_origin` in `SIB0 | SIB1 | SIB2`;
- concrete `must_not` statement;
- proof/evidence paths where available.

Interpretation:

- `SIB0`: architectural bad state;
- `SIB1`: capability/basic-contract bad state;
- `SIB2`: composition/end-to-end bad state.

Not every contract needs an entry from every SIB level, but every contract needs its own ledger.

A repaired EHA defect should leave:

```text
positive proof: accepted behavior works
negative proof: observed bad state must not return
```

Removing or weakening an accepted `FR-*` entry requires explicit deprecation/removal/supersession rationale.

## 5. Querying contracts

For a normal registry:

```text
rg/grep -> candidate record -> paged exact read -> exact evidence
```

Search id, capability class, public contract text, fingerprint fields, affected paths, dependency ids, forbidden-regression text, and SIB origin.

If the registry is genuinely large and host-native retrieval already exists:

```text
BM25 candidates
+ optional embedding candidates
-> optional reranker
-> exact manifest re-read
-> exact code/docs/tests re-read
```

Retrieval is navigation only. Do not add a CodeSleuth search daemon/vector database/model runtime just to query this file.

## 6. Extract or update a contract

### A. Find the promise

Locate the narrowest normative/public statement describing behavior, compatibility, ownership, schema/config, lifecycle, or negative invariant.

### B. Find implementation

Trace it into current code/config. Identify entry point, owner, public surface, dependencies, state/schema, failure behavior, and affected paths.

### C. Find executable proof

Locate tests that prove the actual boundary. Prefer integration/black-box proof for user-visible or cross-component behavior.

### D. Triangulate

```text
AGREE -> create/update record
DRIFT -> CODE_AHEAD/DOC_AHEAD/TEST_AHEAD/CONTRADICTED/UNPROVEN
```

### E. Build the forbidden-regression ledger

Ask:

```text
SIB0: which architectural bad state must not return?
SIB1: which capability bad state must not return?
SIB2: which integration bad state must not return?
```

Record every concrete applicable state. The ledger exists immediately, even if the capability has not yet reached protected status.

### F. Write minimally

Edit `docs/protected-capabilities.json` without reordering unrelated records. Preserve stable ids.

Do not mark `protected` without exact SIB1/SIB2 acceptance evidence.

## 7. Impact graph

Use `affected_paths` to map a diff to seed contracts.

`depends_on` means the current contract relies on another registered contract. When a dependency changes, compute the **reverse dependency closure** to identify consumers that may regress.

If exact source reading reveals a missing consumer, the graph is wrong. Correct the registry; do not use an incomplete graph as permission to skip evidence.

## 8. Gate selection

Ordinary development candidate:

```text
candidate gate
= always-run invariant core
+ affected contract reverse-dependency closure
+ new-feature acceptance
```

This keeps PR feedback bounded.

For a claim requiring full acceptance:

```text
SIB2 / accepted integration head / RC / release
= FULL canonical protected-capability suite
+ claim-specific gates
```

Dependency-aware development gates never water down EHA. If HEAD changes, rerun the profile required for the new exact SHA.

## 9. Diff/PR review

1. pin base/head;
2. list changed paths;
3. map seeds;
4. compute affected reverse dependency closure;
5. read every matched contract and its own `forbidden_regressions`;
6. inspect unchanged consumers and tests;
7. identify paths by which forbidden states can return;
8. distinguish deliberate contract change from accidental regression;
9. identify missing manifest edges/tests/gates.

The review question is:

> **Does this exact candidate add the intended behavior while preserving every affected accepted contract and keeping its applicable forbidden states absent?**

In `/repo-review` read-only mode, report registry drift rather than modifying source. Update the registry only when contract maintenance is explicitly authorized.

## 10. New feature discipline

A post-SIB2 feature needs:

```text
A. new-feature proof
B. affected-contract preservation proof
```

If it introduces a genuinely new capability class, architecture has reopened. Stop calling it ordinary feature population and classify it as SIB0-impacting.

If it stays inside the existing architecture, record the contract honestly at its current lifecycle state and promote it through SIB acceptance.

## 11. Contract fingerprints

Record concise fingerprint values when useful for:

- CLI commands/options;
- config keys;
- schemas/version fields;
- persisted state paths/formats;
- environment variables;
- plugin/adapter interfaces;
- public paths;
- ownership/authority values.

A fingerprint change is a review trigger, not automatic proof of a breaking change. Never semantic-rerank contracts by opaque hash/id.

## 12. Output format

For queries/reviews report:

```text
Target SHA:
Query / diff:
Matched contracts:
- id
  lifecycle status
  why matched
  public contract
  forbidden regressions
  code/docs/test evidence
Affected closure:
Required gate:
Drift / unproven areas:
```

For registry maintenance also list every lifecycle change and every added/removed/modified `FR-*` entry.

## 13. Stop conditions

Stop and surface the problem when:

- code/docs/tests materially contradict;
- a protected contract lacks executable proof;
- a new feature needs a new capability class;
- an accepted forbidden regression is being removed without contract decision;
- the dependency graph excludes a known consumer;
- SIB2/RC/release is proposed with only a dependency-selected partial gate;
- target SHA moved during acceptance.

## Canonical rule

> **Find the contract in code, promises, and tests; give every contract its own forbidden-regression ledger from the moment it is recorded; promote those negative obligations through SIB/EHA with the capability; and preserve the accepted ones on every relevant descendant.**
