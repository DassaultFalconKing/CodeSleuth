# RC7 Planning Index

**Status:** RC7 DESIGN DIALECTIC NAVIGATION / MICRO-FREEZE SET ACCEPTED / FINAL IMPLEMENTATION AUTHORITY NOT YET FROZEN  
**Branch:** `docs/rc7-ledger-authority-repair-plan`

## 1. Purpose

This index identifies the current RC7 planning/design set, distinguishes accepted planning inputs from non-normative research, and records the thesis/antithesis/synthesis consolidation path.

RC7 implementation scope is **not yet fully frozen**. The first consolidated design proposal is frozen only as a review baseline so later critique cannot retroactively change the thesis being reviewed. The accepted micro-freeze set below now supplies implementation authority for its explicitly bounded W5/W7/W8/W9/W11 contracts, but it does not authorize the final-freeze-blocked RC7 workstreams.

## 2. Current design dialectic

### Frozen thesis baseline

- [`RC7-CONSOLIDATED-DESIGN-PROPOSAL.md`](RC7-CONSOLIDATED-DESIGN-PROPOSAL.md) — **FROZEN DESIGN PROPOSAL / THESIS BASELINE / NOT IMPLEMENTATION AUTHORITY**. Blob at freeze: `0f46825308454d9c8d0b3d0b48a2cdcc7845e120`; freeze commit: `1b52c7c72e5294b3a4c145d1bbbd71a1863cb218`.

### Independent antithesis

Independent adversarial review is retained on branch `reviews`:

- `reviews:docs/reviews/do-not-freeze-RC7.md`
- review commit: `be5d158880f649ecb568d9a505c694e87bd76e0e`
- review blob: `02a87228ed1b1b989c4e7dd785b0dd9acba8de9b`
- review verdict: **DO NOT FREEZE RC7** until its authority/completeness/termination blockers are resolved.

The review is evidence/input. It does not become RC7 design authority merely by criticizing the planning set.

### Current synthesis candidate

- [`RC7-THESIS-ANTITHESIS-SYNTHESIS.md`](RC7-THESIS-ANTITHESIS-SYNTHESIS.md) — explicit reconciliation of the frozen thesis and independent review. **Current design review candidate; not yet final implementation authority.**

The synthesis resolves the main review blockers by requiring:

1. one project-policy owner plus an immutable derived `AcceptanceProfileSnapshotV1`;
2. shared ledger structural mechanics but domain-owned semantic recovery/generation selection;
3. deterministic bounded repair-loop termination;
4. separation of discovery completeness from project-policy completeness;
5. a reduced renderer/import surface for RC7.

The micro-freezes below now resolve several of those items concretely. The remaining cross-domain durable authority contracts still require final freeze rather than being inferred from the synthesis.

## 3. Accepted RC7 micro-freezes

The five owner micro-freezes were produced from planning baseline `86218a51345fafb47d0ffec543773846a70ac76a` against runtime evidence baseline `1de37c75251a1e0d9904cffdb82695e92e3fab23` and integrated into this planning stream.

- [`RC7-FINDING-RECOVERY-FREEZE.md`](RC7-FINDING-RECOVERY-FREEZE.md) — MF1 / Finding recovery generation authority. Source freeze head: `c761e1ebacfebad5a4779da69d9d3a9d7a1d8a51`. **FROZEN; unlocks W5.**
- [`RC7-ACCEPTANCE-PROFILE-SNAPSHOT-FREEZE.md`](RC7-ACCEPTANCE-PROFILE-SNAPSHOT-FREEZE.md) — MF2 / `ProjectSibProfileV1` and immutable `AcceptanceProfileSnapshotV1`. Source freeze head: `d751b03c52168d59a23a445652cf042aa0e0c239`. **FROZEN; unlocks W7 and supplies prerequisites for W6/W8/W9.**
- [`RC7-COMPLETENESS-MODEL-FREEZE.md`](RC7-COMPLETENESS-MODEL-FREEZE.md) — MF3 / independent `DiscoveryCompleteness` and `PolicyCompleteness` axes. Source freeze head: `b1e697e7cf8c9409538a20f9449b8ddd8780352e`. **FROZEN AS ADJUDICATED; unlocks W8.**
- [`RC7-REPAIR-TERMINATION-FREEZE.md`](RC7-REPAIR-TERMINATION-FREEZE.md) — MF4 / deterministic repair identity, budget, no-progress and cycle termination. Source freeze head: `dc3191c11db669e416a3d86af69e7cfae95365af`. **FROZEN WITH MF2 DIGEST BINDING; unlocks W9.**
- [`RC7-REPAIR-PACKET-HOST-PROFILE-FREEZE.md`](RC7-REPAIR-PACKET-HOST-PROFILE-FREEZE.md) — MF5 / `RepairPacketV1`, `HostExecutionProfileV1`, structured command compilation and Jinja presentation boundary. Source freeze head: `c9fa42dc032a37509534395f577d7069ae75eb56`. **FROZEN; unlocks W11.**

Cross-contract integration authority:

- [`RC7-MICRO-FREEZE-CROSS-CONTRACT-ADJUDICATION.md`](RC7-MICRO-FREEZE-CROSS-CONTRACT-ADJUDICATION.md) — normative integration decision. It supersedes only the MF3 requirement that evaluated completeness objects live inside `AcceptanceProfileSnapshotV1`, preserves completeness as external evidence-derived assessment bound by reference when used in EHA, and binds MF4 `profileSnapshotDigest` exactly to `AcceptanceProfileSnapshotV1.semanticDigest`. Integration tree was finalized by commit `b5b43a430e28de066c83ce8e98cf7c22e946aceb`.

Effective micro-freeze frontier:

```text
W5  Finding Ledger recovery                 READY AFTER MF1
W7  ProjectSibProfile / snapshot            READY AFTER MF2
W8  discovery vs policy completeness        READY AFTER MF2 + adjudicated MF3
W9  deterministic repair termination        READY AFTER MF2 + MF4 binding
W11 RepairPacket / HostExecutionProfile      READY AFTER MF5
```

The micro-freeze set does **not** itself authorize W2, W4, W6, W10, W12, W13, W14, W15 or complete W16 implementation.

## 4. Semantic authority

- [`EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md`](EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md) — canonical EBCA vocabulary and semantic baseline.
- Existing normative product/evidence/SIB/EHA contracts remain authoritative for their current mechanisms until an accepted final RC7 design explicitly changes them.
- The accepted micro-freeze documents and cross-contract adjudication are normative only within their declared scopes; they do not silently replace unrelated existing authorities.

## 5. Original RC7 planning set

### Primary seed

- [`RC7-FEATURE-PLAN.md`](RC7-FEATURE-PLAN.md) — native implementation ledger, ledger integrity/repair, projection parity, portable evidence modules, customizable Markdown↔NDJSON direction.

### Accepted planning addenda

- [`RC7-SIB-EHA-MATURITY-LOOPS.md`](RC7-SIB-EHA-MATURITY-LOOPS.md) — project-portable SIB0/SIB1/SIB2 profile discovery, human adjudication, generic EHA maturity loops and evidence-bound auto-repair.
- [`RC7-REPAIR-PACKET-RENDERING.md`](RC7-REPAIR-PACKET-RENDERING.md) — typed Repair Case / Repair Packet, host-specific Jinja2 rendering, template-policy separation, render provenance and postcondition verification.
- [`RC7-EBCA-GAP-PLAN.md`](RC7-EBCA-GAP-PLAN.md) — EBCA gap audit, mandatory RC7 hardening and explicitly deferred post-RC7 assurance work.
- [`RC7-STRUCTURED-OBJECT-MULTIRENDERER.md`](RC7-STRUCTURED-OBJECT-MULTIRENDERER.md) — typed semantic objects and renderer/parity/loss concepts.
- [`RC7-CONTEXT-EPISTEMICS-DISPOSITION.md`](RC7-CONTEXT-EPISTEMICS-DISPOSITION.md) — maps the existing Context Epistemics ROAD phases into the minimal RC7 epistemic core versus post-RC7 capability tracks; also defines the structured repair lessons-learned direction.
- [`RC7-IMPLEMENTATION-TRIAGE-TODO.md`](RC7-IMPLEMENTATION-TRIAGE-TODO.md) — accepted owner decision for the stable `codesleuth` OpenCode capability namespace plus a tests-first triage contract for separating `READY_NOW`, `MICRO_FREEZE_REQUIRED`, `FINAL_RC7_FREEZE_BLOCKED`, and `POST_RC7_OR_RESEARCH` workstreams before development begins.

These documents remain planning provenance and requirement inputs. Where the accepted synthesis or later freeze authority deliberately narrows or resolves an ambiguity, implementation must follow the stronger accepted freeze instead of silently editing history.

## 6. Research / non-normative inputs

- [`RC7-DORIS-EVIDENCE-PLANE-THOUGHT-EXPERIMENT.md`](RC7-DORIS-EVIDENCE-PLANE-THOUGHT-EXPERIMENT.md) — possible large-scale derived evidence analytics/search/AI plane. Doris is not RC7 persistence authority and is not required for Ledger Repair, SIB/EHA, Markdown/NDJSON parity or normal CodeSleuth operation.
- [`RC7-OBSIDIAN-ADAPTER-RESEARCH.md`](RC7-OBSIDIAN-ADAPTER-RESEARCH.md) — research direction for a derived Obsidian vault projection. The synthesis moves Obsidian product delivery out of mandatory RC7; one-way research fixtures may remain useful portability evidence.

## 7. Existing post-RC7 road direction

- [`ROAD/ROADMAP.md`](ROAD/ROADMAP.md) — Context Epistemics, durable generic Negative Claims, forbidden inference, risk classes, mutation evidence gates, long-context degradation and grounding suites.
- [`ROAD/ROAP.md`](ROAD/ROAP.md) — disconnected/live-host Remote Operator Assurance Protocol.

The RC7 synthesis deliberately keeps these broader assurance capabilities outside the core RC7 implementation scope.

## 8. Remaining consolidation requirements before final implementation freeze

The remaining final-freeze work must resolve and freeze at least:

1. physical/event schemas for the Implementation Ledger, including `PlanIdentity`, stable `RequirementId`, derived status and cross-references;
2. Implementation Ledger domain-specific recovery generation and active-generation selection;
3. existing `eha.ndjson` V1 -> V2 schema evolution and compatibility;
4. exact carriage of immutable `AcceptanceProfileSnapshotV1.semanticDigest` and completeness evidence in EHA V2 without mutating the snapshot;
5. non-binary EHA result aggregation and durable completion semantics;
6. `EhaRepairCaseV1` vs `LedgerRecoveryCaseV1` permission boundaries;
7. exact failed-subject/profile immutability semantics across EHA repair lineage;
8. cross-ledger stable ID/linkage model for downstream read-only views;
9. derived `RepairLearningRecordV1` and preservation-promotion boundary;
10. read-only `EbcaClaimViewV1` boundary with no generic claim persistence;
11. generated Markdown/static renderer parity for the now-frozen source objects;
12. minimal context epistemics integration with acceptance/repair without creating another state authority;
13. install/smoke/catalog/public-doc exposure for the final accepted RC7 surface set;
14. deterministic adversarial and live-dogfood acceptance fixtures.

The already accepted micro-freeze decisions MUST NOT be reopened by those final sessions unless a concrete contradiction with stronger existing authority is demonstrated.

## 9. Next authority step

The next design session is:

```text
FF1 — Implementation Ledger + Recovery Authority Freeze
```

FF1 must consume the accepted structural/domain boundary established by the synthesis and MF1 precedent without moving active-generation selection into generic `LedgerIntegrityCore`.

After FF1, FF2 may freeze EHA V2 plus `EhaRepairCase` / `LedgerRecoveryCase` permissions using the already accepted MF2/MF4 identities. The final derived-surfaces freeze follows after those durable authorities exist.

Implementation branches continue to start from the current hosted-green runtime integration stream, never from this planning branch.

Do not implement directly from one seed/addendum or from the frozen thesis while ignoring the accepted micro-freezes and their adjudication. That would recreate the context-fragmentation problem CodeSleuth is supposed to diagnose in other repositories, with an almost admirable lack of self-awareness.
