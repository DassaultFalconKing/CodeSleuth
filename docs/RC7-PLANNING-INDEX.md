# RC7 Planning Index

**Status:** RC7 DESIGN DIALECTIC NAVIGATION / FINAL IMPLEMENTATION AUTHORITY NOT YET FROZEN  
**Branch:** `docs/rc7-ledger-authority-repair-plan`

## 1. Purpose

This index identifies the current RC7 planning/design set, distinguishes accepted planning inputs from non-normative research, and records the thesis/antithesis/synthesis consolidation path.

RC7 implementation scope is **not yet frozen**. The first consolidated design proposal is frozen only as a review baseline so later critique cannot retroactively change the thesis being reviewed.

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

If the synthesis is accepted, the next authority step is a final normative `RC7-CONSOLIDATED-DESIGN.md`. Do not begin runtime implementation merely because the thesis or synthesis exists.

## 3. Semantic authority

- [`EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md`](EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md) — canonical EBCA vocabulary and semantic baseline.
- Existing normative product/evidence/SIB/EHA contracts remain authoritative for their current mechanisms until an accepted final RC7 design explicitly changes them.

## 4. Original RC7 planning set

### Primary seed

- [`RC7-FEATURE-PLAN.md`](RC7-FEATURE-PLAN.md) — native implementation ledger, ledger integrity/repair, projection parity, portable evidence modules, customizable Markdown↔NDJSON direction.

### Accepted planning addenda

- [`RC7-SIB-EHA-MATURITY-LOOPS.md`](RC7-SIB-EHA-MATURITY-LOOPS.md) — project-portable SIB0/SIB1/SIB2 profile discovery, human adjudication, generic EHA maturity loops and evidence-bound auto-repair.
- [`RC7-REPAIR-PACKET-RENDERING.md`](RC7-REPAIR-PACKET-RENDERING.md) — typed Repair Case / Repair Packet, host-specific Jinja2 rendering, template-policy separation, render provenance and postcondition verification.
- [`RC7-EBCA-GAP-PLAN.md`](RC7-EBCA-GAP-PLAN.md) — EBCA gap audit, mandatory RC7 hardening and explicitly deferred post-RC7 assurance work.
- [`RC7-STRUCTURED-OBJECT-MULTIRENDERER.md`](RC7-STRUCTURED-OBJECT-MULTIRENDERER.md) — typed semantic objects and renderer/parity/loss concepts.
- [`RC7-CONTEXT-EPISTEMICS-DISPOSITION.md`](RC7-CONTEXT-EPISTEMICS-DISPOSITION.md) — maps the existing Context Epistemics ROAD phases into the minimal RC7 epistemic core versus post-RC7 capability tracks; also defines the structured repair lessons-learned direction.
- [`RC7-IMPLEMENTATION-TRIAGE-TODO.md`](RC7-IMPLEMENTATION-TRIAGE-TODO.md) — accepted owner decision for the stable `codesleuth` OpenCode capability namespace plus a tests-first triage contract for separating `READY_NOW`, `MICRO_FREEZE_REQUIRED`, `FINAL_RC7_FREEZE_BLOCKED`, and `POST_RC7_OR_RESEARCH` workstreams before development begins.

These documents remain planning provenance and requirement inputs. Where the accepted synthesis deliberately narrows or resolves an ambiguity, the future final consolidated design must record that decision explicitly instead of silently editing history.

## 5. Research / non-normative inputs

- [`RC7-DORIS-EVIDENCE-PLANE-THOUGHT-EXPERIMENT.md`](RC7-DORIS-EVIDENCE-PLANE-THOUGHT-EXPERIMENT.md) — possible large-scale derived evidence analytics/search/AI plane. Doris is not RC7 persistence authority and is not required for Ledger Repair, SIB/EHA, Markdown/NDJSON parity or normal CodeSleuth operation.
- [`RC7-OBSIDIAN-ADAPTER-RESEARCH.md`](RC7-OBSIDIAN-ADAPTER-RESEARCH.md) — research direction for a derived Obsidian vault projection. The synthesis moves Obsidian product delivery out of mandatory RC7; one-way research fixtures may remain useful portability evidence.

## 6. Existing post-RC7 road direction

- [`ROAD/ROADMAP.md`](ROAD/ROADMAP.md) — Context Epistemics, durable generic Negative Claims, forbidden inference, risk classes, mutation evidence gates, long-context degradation and grounding suites.
- [`ROAD/ROAP.md`](ROAD/ROAP.md) — disconnected/live-host Remote Operator Assurance Protocol.

The RC7 synthesis deliberately keeps these broader assurance capabilities outside the core RC7 implementation scope.

## 7. Consolidation requirements before implementation

The final reviewed `RC7-CONSOLIDATED-DESIGN.md` must resolve and freeze at least:

1. exact authority mode for `ProjectSibProfileV1`;
2. immutable derived `AcceptanceProfileSnapshotV1` compilation/digest semantics;
3. physical/event schemas for the Implementation Ledger;
4. domain-specific ledger recovery-generation ownership for findings/EHA/implementation;
5. existing `eha.ndjson` V1 -> V2 schema evolution and compatibility;
6. non-binary EHA result aggregation and durable completion semantics;
7. exact failed-subject/profile immutability semantics;
8. deterministic repair-attempt identity, budgets, cycle/no-progress termination and explicit stop states;
9. discovery completeness vs policy completeness for SIB0;
10. affected-closure trust reasons and deterministic fallback behavior;
11. cross-ledger stable ID/linkage model;
12. `EhaRepairCaseV1`, `LedgerRecoveryCaseV1`, `RepairPacketV1` and host execution profile boundaries;
13. derived RepairLearningRecord and preservation-promotion boundary;
14. read-only EBCA claim-view boundary with no generic claim persistence;
15. generated Markdown and any bounded legacy-import proposal semantics;
16. reduced/static renderer contract and minimum RC7 formats;
17. Jinja presentation-only boundary after structured host/tool resolution;
18. Obsidian/Doris/post-RC7 exclusions;
19. install/smoke/catalog/public-doc exposure;
20. deterministic adversarial and live-dogfood acceptance fixtures;
21. stable CodeSleuth invocation/capability identity: `/codesleuth/<operation>` for canonical user-facing commands, `codesleuth-<id>` for maintained model-facing Skill and Playbook identities, one mapping authority in `pack/.opencode/codesleuth-naming.json`, bounded legacy aliases, and a contract test forbidding new unprefixed public CodeSleuth capability identities after cutover.

Before final freeze, a tests-first implementation triage MAY identify independent `READY_NOW` slices whose semantics are already fixed by existing normative contracts. Such classification does not make the whole RC7 design accepted and must not pre-decide any unresolved authority item above.

Do not implement directly from one seed/addendum or from the frozen thesis while ignoring the synthesis. That would recreate the context-fragmentation problem CodeSleuth is supposed to diagnose in other repositories, with an almost admirable lack of self-awareness.
