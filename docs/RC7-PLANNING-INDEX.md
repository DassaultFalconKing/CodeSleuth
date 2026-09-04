# RC7 Planning Index

**Status:** RC7 DESIGN DIALECTIC NAVIGATION / MF1–MF5 + FF1 ACCEPTED / FF2 REMAINS  
**Branch:** `docs/rc7-ledger-authority-repair-plan`

## 1. Purpose

This index identifies the current RC7 planning/design authority set, distinguishes accepted freeze contracts from provenance/research, and records the current implementation frontier.

RC7 is not yet one completely frozen implementation authority. The accepted MF1–MF5 micro-freezes plus accepted FF1 now provide bounded implementation authority for W2, W4A, W5, W7, W8, W9 and W11. W4B authority-changing selection has frozen semantics but remains mutation-permission-blocked on FF2/W10. W6, W10, W12, W13, W14, W15 and complete W16 remain final-freeze-blocked.

The accepted RC6/SIB2 predecessor remains:

```text
6621c65b868d3e279ddcbd8dee182a95c6fb29f8
```

FF1 deliberately reopens RC7 SIB0 for the `CC-STATE` ownership redefinition. Predecessor SIB0 acceptance therefore does not transfer to the resulting RC7 architecture by ancestry.

## 2. Current design dialectic

### Frozen thesis baseline

- [`RC7-CONSOLIDATED-DESIGN-PROPOSAL.md`](RC7-CONSOLIDATED-DESIGN-PROPOSAL.md) — **FROZEN DESIGN PROPOSAL / THESIS BASELINE / NOT IMPLEMENTATION AUTHORITY**. Blob at freeze: `0f46825308454d9c8d0b3d0b48a2cdcc7845e120`; freeze commit: `1b52c7c72e5294b3a4c145d1bbbd71a1863cb218`.

### Independent antithesis

Independent adversarial review is retained on branch `reviews`:

- `reviews:docs/reviews/do-not-freeze-RC7.md`
- review commit: `be5d158880f649ecb568d9a505c694e87bd76e0e`
- review blob: `02a87228ed1b1b989c4e7dd785b0dd9acba8de9b`
- original review verdict: **DO NOT FREEZE RC7** until its authority/completeness/termination blockers are resolved.

The review remains pinned design evidence/input. Later movement of the `reviews` branch does not change this antithesis identity.

### Synthesis

- [`RC7-THESIS-ANTITHESIS-SYNTHESIS.md`](RC7-THESIS-ANTITHESIS-SYNTHESIS.md), blob `a3556ca3bd84546835a3ff66847cfb03da54fc7b` — reconciliation of thesis and pinned antithesis.

The synthesis established the governing direction now made concrete by the accepted freezes:

1. one project-policy owner plus immutable derived `AcceptanceProfileSnapshotV1`;
2. shared ledger structural mechanics but domain-owned semantic recovery/generation selection;
3. deterministic bounded repair-loop termination;
4. discovery completeness separated from project-policy completeness;
5. reduced renderer/import scope for RC7;
6. no generic claim database or generic ledger meta-authority.

## 3. Accepted RC7 micro-freezes

The accepted owner micro-freezes are:

- [`RC7-FINDING-RECOVERY-FREEZE.md`](RC7-FINDING-RECOVERY-FREEZE.md) — MF1 / Finding recovery generation authority. Source freeze head: `c761e1ebacfebad5a4779da69d9d3a9d7a1d8a51`. **FROZEN; unlocks W5.**
- [`RC7-ACCEPTANCE-PROFILE-SNAPSHOT-FREEZE.md`](RC7-ACCEPTANCE-PROFILE-SNAPSHOT-FREEZE.md) — MF2 / `ProjectSibProfileV1` and immutable `AcceptanceProfileSnapshotV1`. Source freeze head: `d751b03c52168d59a23a445652cf042aa0e0c239`. **FROZEN; unlocks W7 and supplies prerequisites for W6/W8/W9.**
- [`RC7-COMPLETENESS-MODEL-FREEZE.md`](RC7-COMPLETENESS-MODEL-FREEZE.md) — MF3 / independent `DiscoveryCompleteness` and `PolicyCompleteness`. Source freeze head: `b1e697e7cf8c9409538a20f9449b8ddd8780352e`. **FROZEN AS ADJUDICATED; unlocks W8.**
- [`RC7-REPAIR-TERMINATION-FREEZE.md`](RC7-REPAIR-TERMINATION-FREEZE.md) — MF4 / deterministic repair identity, budget, no-progress and cycle termination. Source freeze head: `dc3191c11db669e416a3d86af69e7cfae95365af`. **FROZEN WITH MF2 DIGEST BINDING; unlocks W9.**
- [`RC7-REPAIR-PACKET-HOST-PROFILE-FREEZE.md`](RC7-REPAIR-PACKET-HOST-PROFILE-FREEZE.md) — MF5 / `RepairPacketV1`, `HostExecutionProfileV1`, structured command compilation and Jinja presentation boundary. Source freeze head: `c9fa42dc032a37509534395f577d7069ae75eb56`. **FROZEN; unlocks W11.**

Cross-contract integration authority:

- [`RC7-MICRO-FREEZE-CROSS-CONTRACT-ADJUDICATION.md`](RC7-MICRO-FREEZE-CROSS-CONTRACT-ADJUDICATION.md) — normative integration decision. It keeps completeness external to immutable `AcceptanceProfileSnapshotV1`, binds MF4 `profileSnapshotDigest` to `AcceptanceProfileSnapshotV1.semanticDigest`, preserves domain-owned generation selection, and prevents MF5 packets/presentation from becoming mutation authority. Integration tree was finalized by commit `b5b43a430e28de066c83ce8e98cf7c22e946aceb`.

## 4. Accepted FF1 — Implementation Ledger + Recovery Authority

- [`RC7-IMPLEMENTATION-LEDGER-RECOVERY-FREEZE.md`](RC7-IMPLEMENTATION-LEDGER-RECOVERY-FREEZE.md)
- final reviewed FF1 source head: `3a8fc265c4423e4983b9ced5974cce039072e88f`
- accepted runtime predecessor consumed by FF1: `6621c65b868d3e279ddcbd8dee182a95c6fb29f8`
- status: **FROZEN WITH EXPLICIT W10 PERMISSION BOUNDARY**

FF1 freezes:

- deterministic `RepositoryIdentityV1`;
- exact `PlanIdentityV1`;
- authority-backed `ImplementationRequirementCatalogV1`;
- deterministic plan-scoped `RequirementIdV1`;
- the closed `ImplementationEventV1` event family and exact payload/cardinality schemas;
- exact-target implementation-state derivation;
- per-oracle local-verification derivation and deterministic aggregation;
- material-reference digest/content-addressed requirements;
- immutable Implementation recovery generations;
- exact safe-reframe transforms, corruption/reason identity and generation identity;
- exact BASELINE/SELECT selection identity;
- unique-terminal active-generation selection;
- fail-closed ambiguity/no predecessor fallback;
- source-change-before-selection protection.

### FF1 SIB0 disposition

FF1 explicitly determines that the new separate Implementation authority redefines the existing `CC-STATE` ownership boundary:

```text
RC7_SIB0_STATUS:
REOPENED

CAPABILITY_CLASS_COUNT:
UNCHANGED

AFFECTED_CLASS:
CC-STATE

REDEFINITION:
persistent-review-state
-> persistent-evidence-and-implementation-state
   with separate Finding / Implementation / EHA domain authorities
```

Therefore the RC6/SIB2 predecessor remains the construction predecessor, but its SIB0 acceptance does not transfer to RC7 after this architectural redefinition. RC7 must establish a replacement exact-head SIB0 before claiming RC7 SIB1/SIB2.

### FF1 implementation boundary

```text
W2  Implementation Ledger core
    IMPLEMENTABLE after accepted FF1

W4A Implementation recovery read/build/validate
    IMPLEMENTABLE after W2 + LedgerIntegrityCore

W4B Implementation recovery SELECT mutation
    semantics FROZEN by FF1
    production mutation BLOCKED until FF2/W10 supplies
    LedgerRecoveryCaseV1 + approval authority
```

FF2/W10 may define who may authorize a recovery case/selection. It must not move active-generation ownership into a generic recovery layer or change the FF1 selection algorithm.

## 5. Current implementation frontier

```text
IMPLEMENTABLE / AUTHORIZED DESIGN

W1  namespace foundation                         READY by accepted naming decision
W2  Implementation Ledger core                  READY AFTER FF1
W3  LedgerIntegrityCore                         READY by synthesis structural boundary
W4A Implementation recovery read/build/validate READY AFTER FF1 + W2 + W3
W5  Finding Ledger recovery                     READY AFTER MF1 (+ W3 structural core)
W7  ProjectSibProfile / snapshot                READY AFTER MF2
W8  discovery vs policy completeness            READY AFTER MF2 + adjudicated MF3
W9  deterministic repair termination            READY AFTER MF2 + MF4 binding
W11 RepairPacket / HostExecutionProfile         READY AFTER MF5

SEMANTICS FROZEN / MUTATION AUTHORITY BLOCKED

W4B Implementation recovery SELECT write        WAIT FF2/W10 permission authority

FINAL-FREEZE-BLOCKED

W6  EHA V2
W10 EhaRepairCaseV1 / LedgerRecoveryCaseV1 permissions
W12 RepairLearningRecordV1
W13 EbcaClaimViewV1
W14 final projection parity/source mapping
W15 integrated context epistemics
W16 complete lifecycle/catalog/docs closure
```

This frontier supersedes the earlier statement that W2/W4 were wholly final-freeze-blocked. W4 is now deliberately split because read/build/validate semantics are frozen while authority-changing mutation permission is not.

## 6. Semantic authority

- [`EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md`](EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md) — canonical EBCA vocabulary and semantic baseline.
- Existing accepted product/evidence/SIB/EHA contracts remain authoritative for their current mechanisms unless an accepted RC7 freeze explicitly changes their scope.
- MF1–MF5, their cross-contract adjudication, and FF1 are normative only within their declared scopes.
- FF1's explicit `CC-STATE` redefinition opens a new RC7 SIB0 lineage; it does not rewrite the historical validity of the accepted RC6/SIB2 predecessor.

## 7. Original RC7 planning set

### Primary seed

- [`RC7-FEATURE-PLAN.md`](RC7-FEATURE-PLAN.md) — native implementation ledger, ledger integrity/repair, projection parity and portability directions.

### Accepted planning addenda

- [`RC7-SIB-EHA-MATURITY-LOOPS.md`](RC7-SIB-EHA-MATURITY-LOOPS.md) — project-portable SIB0/SIB1/SIB2 profile discovery, human adjudication, EHA maturity loops and evidence-bound auto-repair.
- [`RC7-REPAIR-PACKET-RENDERING.md`](RC7-REPAIR-PACKET-RENDERING.md) — typed Repair Case / Repair Packet, host-specific Jinja2 rendering, template-policy separation, render provenance and postcondition verification.
- [`RC7-EBCA-GAP-PLAN.md`](RC7-EBCA-GAP-PLAN.md) — EBCA gap audit, mandatory RC7 hardening and deferred assurance work.
- [`RC7-STRUCTURED-OBJECT-MULTIRENDERER.md`](RC7-STRUCTURED-OBJECT-MULTIRENDERER.md) — typed semantic objects and renderer/parity/loss concepts.
- [`RC7-CONTEXT-EPISTEMICS-DISPOSITION.md`](RC7-CONTEXT-EPISTEMICS-DISPOSITION.md) — minimal RC7 context epistemics versus post-RC7 capability tracks.
- [`RC7-IMPLEMENTATION-TRIAGE-TODO.md`](RC7-IMPLEMENTATION-TRIAGE-TODO.md) — accepted `codesleuth` namespace decision plus tests-first implementation triage rules.

These remain provenance/requirement inputs. Where an accepted freeze deliberately narrows or resolves them, implementation follows the accepted freeze.

## 8. Research / non-normative inputs

- [`RC7-DORIS-EVIDENCE-PLANE-THOUGHT-EXPERIMENT.md`](RC7-DORIS-EVIDENCE-PLANE-THOUGHT-EXPERIMENT.md) — possible derived analytics/search/AI plane; not RC7 authority.
- [`RC7-OBSIDIAN-ADAPTER-RESEARCH.md`](RC7-OBSIDIAN-ADAPTER-RESEARCH.md) — research direction for a derived Obsidian projection; not evidence authority.

## 9. Remaining final-freeze work

FF1 closes the former Implementation Ledger schema/recovery blockers. The remaining design work is now:

1. existing `eha.ndjson` V1 -> V2 schema evolution and compatibility;
2. exact carriage of immutable `AcceptanceProfileSnapshotV1.semanticDigest` and completeness evidence in EHA V2 without mutating the snapshot;
3. non-binary EHA obligation/result aggregation and durable campaign completion semantics;
4. exact failed-subject/profile immutability and campaign/repair lineage semantics;
5. `EhaRepairCaseV1` vs `LedgerRecoveryCaseV1` permission/approval boundaries, including authority required before W4B SELECT mutation;
6. cross-ledger stable ID/linkage rules needed by downstream read-only views;
7. derived `RepairLearningRecordV1` and its proposal-only preservation-promotion boundary;
8. read-only `EbcaClaimViewV1` with no generic claim persistence/lifecycle;
9. generated Markdown/static renderer parity for frozen source objects;
10. minimal context epistemics integration with acceptance/repair without another state authority;
11. install/smoke/catalog/public-doc exposure for the final accepted RC7 surface set;
12. deterministic adversarial, replacement-SIB0 and live-dogfood acceptance fixtures.

Accepted MF1–MF5 and FF1 decisions MUST NOT be reopened by later sessions unless a concrete contradiction with stronger existing authority is demonstrated and explicitly adjudicated.

## 10. Next authority step

The next final-freeze design session is:

```text
FF2 — EHA V2 + Repair/Recovery Permission Freeze
```

FF2 must consume, rather than redesign:

- FF1 exact contract head `3a8fc265c4423e4983b9ced5974cce039072e88f`;
- MF2 snapshot identity;
- adjudicated MF3 completeness separation;
- MF4 repair termination identity;
- MF5 RepairPacket/HostExecutionProfile boundary;
- existing accepted EHA authority and exact-head SIB contracts on predecessor `6621c65b868d3e279ddcbd8dee182a95c6fb29f8`.

FF2 owns EHA V2 evolution and the permission/approval schemas for `EhaRepairCaseV1` / `LedgerRecoveryCaseV1`. It MUST NOT change FF1's Implementation generation identity, safe-reframe semantics, selection identity, unique-terminal active-generation rule, or no-predecessor-fallback rule.

After FF2, the remaining derived-surface/final-integration freeze can bind W12–W16 to the frozen durable authorities.

Implementation branches continue to start from the current accepted runtime/integration stream, never from this planning branch. Planning commits are design authority inputs, not runtime implementation bases. Apparently this distinction needs to be written down repeatedly because branches, like humans, develop ambitions when unsupervised.
