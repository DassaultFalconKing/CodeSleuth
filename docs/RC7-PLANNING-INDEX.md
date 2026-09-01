# RC7 Planning Index

**Status:** RC7 PLANNING NAVIGATION / NOT YET FROZEN IMPLEMENTATION AUTHORITY  
**Branch:** `docs/rc7-ledger-authority-repair-plan`

## 1. Purpose

This index identifies the current RC7 planning set and distinguishes accepted planning inputs from non-normative research. It is navigation, not a substitute for the documents themselves.

RC7 scope must be frozen deliberately before implementation. Until then, the accepted addenda below are requirements to preserve during design consolidation, while `RC7-FEATURE-PLAN.md` remains the primary planning seed rather than an independently frozen implementation contract.

## 2. Semantic authority

- [`EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md`](EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md) — canonical EBCA vocabulary and semantic baseline.
- Existing normative product/evidence/SIB/EHA contracts remain authoritative for their current mechanisms until an accepted RC7 design explicitly changes them.

## 3. RC7 planning set

### Primary seed

- [`RC7-FEATURE-PLAN.md`](RC7-FEATURE-PLAN.md) — native implementation ledger, ledger integrity/repair, projection parity, portable evidence modules, customizable Markdown↔NDJSON adapter.

### Accepted planning addenda

- [`RC7-SIB-EHA-MATURITY-LOOPS.md`](RC7-SIB-EHA-MATURITY-LOOPS.md) — project-portable SIB0/SIB1/SIB2 profile discovery, human adjudication, generic EHA maturity loops and evidence-bound auto-repair.
- [`RC7-REPAIR-PACKET-RENDERING.md`](RC7-REPAIR-PACKET-RENDERING.md) — typed `RepairCaseV1` / `RepairPacketV1`, host-specific Jinja2 rendering, template-policy separation, render provenance and postcondition verification.
- [`RC7-EBCA-GAP-PLAN.md`](RC7-EBCA-GAP-PLAN.md) — EBCA gap audit, mandatory RC7 hardening and explicitly deferred post-RC7 assurance work.

These addenda are accepted inputs to the eventual consolidated RC7 design. Consolidation must preserve their material requirements unless a later explicit owner decision supersedes them.

## 4. Non-normative thought experiment

- [`RC7-DORIS-EVIDENCE-PLANE-THOUGHT-EXPERIMENT.md`](RC7-DORIS-EVIDENCE-PLANE-THOUGHT-EXPERIMENT.md) — possible large-scale derived evidence analytics/search/AI plane. Doris is not RC7 persistence authority and is not required for Ledger Repair, SIB/EHA, Markdown/NDJSON parity or normal CodeSleuth operation.

## 5. Existing post-RC7 road direction

- [`ROAD/ROADMAP.md`](ROAD/ROADMAP.md) — Context Epistemics, durable generic Negative Claims, forbidden inference, risk classes, mutation evidence gates, long-context degradation and grounding suites.
- [`ROAD/ROAP.md`](ROAD/ROAP.md) — disconnected/live-host Remote Operator Assurance Protocol.

`RC7-EBCA-GAP-PLAN.md` identifies which minimal pieces of those doctrines are required inside RC7 and which remain deliberately post-RC7.

## 6. Consolidation rule

Before RC7 implementation begins, produce one reviewed design/spec that resolves at least:

1. physical/event schemas for implementation ledger and repair generations;
2. common-but-non-authoritative EBCA claim envelope;
3. `ProjectSibProfileV1` / acceptance-profile identity and digest semantics;
4. generic EHA outcome aggregation including non-binary states;
5. regression-witness / negative-preservation promotion boundary;
6. affected-closure trust and completeness/truncation handling;
7. cross-ledger stable ID/linkage model;
8. `RepairCaseV1` / `RepairPacketV1` schemas;
9. Jinja2 host/project template trust and customization boundary;
10. Markdown↔NDJSON adapter/profile schema;
11. NDJSON/Markdown/Graphify/Mermaid semantic parity contract;
12. install/smoke/catalog/public-doc exposure;
13. deterministic and live-dogfood acceptance fixtures.

Do not implement directly from one addendum while ignoring the others. That would recreate the exact context-fragmentation problem CodeSleuth is supposed to diagnose in other repositories, which would at least be thematically consistent but not useful.
