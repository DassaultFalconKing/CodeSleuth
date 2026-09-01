# RC7 Context Epistemics Disposition

**Status:** ACCEPTED RC7 / POST-RC7 PLANNING INPUT  
**Source roadmap:** [`ROAD/ROADMAP.md`](ROAD/ROADMAP.md)  
**Related:** [`RC7-EBCA-GAP-PLAN.md`](RC7-EBCA-GAP-PLAN.md), [`RC7-SIB-EHA-MATURITY-LOOPS.md`](RC7-SIB-EHA-MATURITY-LOOPS.md)

## 1. Purpose

The Context Epistemics roadmap is not abandoned. RC7 now creates a natural place to consume a bounded subset of it, while the larger epistemic-control system remains a separate post-RC7 capability track.

Do not renumber or replace the existing ROAD phases. This document maps them to release responsibility.

Compact split:

```text
RC7
  epistemic minimum required for honest
  SIB/EHA + repair + structured projections

POST-RC7
  general negative knowledge + forbidden inference
  + risk-gated mutation + remote assurance
  + grounding/long-context hardening
```

## 2. RC7 epistemic core

RC7 MUST operationalize these concepts because generic maturity/repair cannot be correct without them:

### Result states

At minimum:

```text
PASS
FAIL
INCONCLUSIVE
UNAVAILABLE
NOT_APPLICABLE
```

and workflow stop states such as:

```text
OPERATOR_DECISION_REQUIRED
SCOPE_EXPANSION_REQUIRED
ARCHITECTURE_REOPEN_REQUIRED
LIVE_EVIDENCE_REQUIRED
EVIDENCE_UNTRUSTED
REPAIR_LOOP_STALLED
```

`UNKNOWN`/conflict semantics may appear where needed but RC7 does not yet need the whole general-purpose epistemic-state subsystem.

### Claim dimensions

Typed RC7 objects preserve:

```text
subject
property
scope
authority
evidence
assumptions
limitations
residual uncertainty
```

### Semantic triangulation

Repair/root-cause analysis must distinguish agreement, stale sides and contradictions rather than assuming the code is always wrong.

### Rehydration

Derived/search/model context may locate evidence, but material action reopens exact source/authority first.

### Repair-specific mutation evidence gate

Before a host mutation, CodeSleuth validates target identity, scope, evidence freshness, constraints and stop conditions.

This is intentionally narrower than the future generic R0-R3 mutation policy engine.

### Postcondition verification

After a host claims a repair, CodeSleuth re-observes actual repository/worktree/diff/SHA state before treating the repair as a new candidate.

### Regression learning

A reproduced and accepted repaired failure should create a regression witness and a candidate preservation/negative obligation rather than disappearing into chat history.

### Projection labels

RC7 renderers must preserve material uncertainty/result/authority labels when rendering Markdown, graphs, prompts and user visuals.

## 3. Existing ROAD phase mapping

### CE-0 Canonical vocabulary

**Disposition:** RC7 uses the canonical EBCA thesaurus and existing CE vocabulary conservatively. No duplicate glossary.

### CE-1 Negative Claim schema

**Disposition:** PARTIAL RC7 BRIDGE, FULL POST-RC7.

RC7 only needs repair-linked candidate negative/preservation obligations with stable IDs and evidence lineage. The generic Negative Claim domain remains post-RC7.

### CE-2 Durable Negative Knowledge ledger

**Disposition:** POST-RC7.

RC7 must preserve hooks/cross-IDs but must not create a second generic negative-knowledge authority during ledger/EHA work.

### CE-3 Atomic epistemic skills

**Disposition:** PARTIAL RC7.

RC7 needs semantics equivalent to:

- epistemic/contract triangulation for repair diagnosis;
- repair-specific evidence gate;
- relevant prior-failure/regression retrieval.

General `negative-claim-assessment`, `forbidden-inference-check`, `negative-knowledge-retrieval` remain post-RC7.

### CE-4 Remote operator assurance

**Disposition:** POST-RC7 / ROAP.

RC7 ExternalEvidence and postcondition checks are prerequisites, not the full remote-operator subsystem.

### CE-5 Remote operator playbooks

**Disposition:** POST-RC7.

### CE-6 Context projection with epistemic labels

**Disposition:** PARTIAL RC7.

RC7 projections preserve result/authority/uncertainty fields for the domains they render. A universal epistemic context projection remains post-RC7.

### CE-7 Negative-edge context graph

**Disposition:** POST-RC7.

The future graph must distinguish `NO_EDGE` from explicit `FORBIDS_INFERENCE`. RC7 graph parity should leave compatible relation-extension hooks.

### CE-8 Retrieval policy

**Disposition:** POST-RC7.

RC7 repair may retrieve prior failures and forbidden regressions, but general retrieval ranking over positive/negative/authority/risk/freshness is a later capability.

### CE-9 Risk classes

**Disposition:** POST-RC7.

RC7 repair gets a bounded mutation guard, not the universal R0-R3 policy engine.

### CE-10 Mutation preflight

**Disposition:** PARTIAL RC7 for repair only; general framework POST-RC7.

### CE-11 Postcondition verification

**Disposition:** RC7 MUST.

This is directly required by evidence-bound auto-repair.

### CE-12 Negative regression corpus

**Disposition:** PARTIAL RC7 + FULL POST-RC7.

RC7 acceptance needs adversarial cases for exact-head non-transfer, unavailable evidence, stale packets, host false-success, regression witness omission and authority conflict. The broad forbidden-inference corpus remains post-RC7.

### CE-13 Code-generator grounding suite

**Disposition:** POST-RC7.

### CE-14 Long-context degradation tests

**Disposition:** POST-RC7.

### CE-15 Fail-closed tool integration

**Disposition:** PARTIAL RC7 repair guard; full dangerous-tool framework POST-RC7.

### CE-16 Human-readable presentation

**Disposition:** PARTIAL RC7 via structured multi-renderer.

RC7 user surfaces can expose EBCA states consistently. A universal epistemic TUI is post-RC7.

### CE-17 EBCA thesaurus integration

**Disposition:** RC7 MUST for any new stable term that survives implementation and acceptance.

### CE-18 Acceptance

**Disposition:** each implemented CE-derived capability follows normal protected-capability/SIB/EHA discipline.

## 4. RC7 learning artifact: `RepairLearningRecordV1`

The repeated practice of asking a model to write a lessons-learned note after a difficult fix should become structured and reproducible.

After a repair is verified and fresh acceptance establishes the relevant claim, CodeSleuth should be able to derive a `RepairLearningRecordV1` equivalent containing:

```text
learningId
repairCaseId
subject / failed SHA
accepted repaired SHA
violated claim / contract
failure symptom
root cause
why previous checks missed it
repair strategy
repair delta refs
regression witness
new preservation/negative obligation candidate
applicability
non-applicability / limitations
assumptions
evidence refs
EHA / gate refs
```

This is a **derived learning artifact**, not a new authority.

It can render to:

- `LESSONS-LEARNED.md`;
- Markdown report sections;
- NDJSON/JSON records;
- Graphify/Mermaid lineage;
- Obsidian notes/backlinks/Bases;
- future assurance-case views.

Promotion of any lesson into project canon, protected-contract wording or durable Negative Claim authority still follows project policy/human adjudication.

## 5. Why lessons learned matter operationally

A useful repair loop should not end at:

```text
FAIL -> PATCH -> PASS
```

It should be able to produce:

```text
FAIL
 -> diagnosis
 -> repair
 -> regression witness
 -> fresh acceptance
 -> preservation candidate
 -> structured lesson
```

This preserves not merely that a bug happened, but the reasoning boundary that prevented recurrence.

## 6. Post-RC7 recommended capability tracks

Rather than one giant release, the remaining Context Epistemics roadmap can be delivered as separate coherent tracks:

### Track E1 — Durable Negative Knowledge

- generic NegativeClaim schema/ledger;
- supersession/reopen semantics;
- forbidden inference;
- negative-edge graph;
- negative-context retrieval.

### Track E2 — Mutation Assurance

- R0-R3 operation classes;
- structured preflight;
- mutation evidence gates;
- fail-closed dangerous tools;
- generic postcondition correlation.

### Track E3 — Remote Operator Assurance

- ROAP;
- disconnected host claims;
- external anchors;
- mutation accounting;
- residual uncertainty and recovery playbooks.

### Track E4 — Model Grounding Assurance

- negative regression corpus;
- code-generator grounding benchmark;
- long-context degradation/adversarial context tests;
- authority-selection and unknown-preservation metrics.

### Track E5 — Assurance/Traceability Hardening

- bidirectional traceability completeness audit;
- structured assurance-case projection;
- producer/verifier independence;
- authenticated provenance/reproducible-build integrations where projects need them.

These tracks may become RC8+ slices or independent post-RC7 capability releases; they should not be smuggled into RC7 implementation by dependency creep.
