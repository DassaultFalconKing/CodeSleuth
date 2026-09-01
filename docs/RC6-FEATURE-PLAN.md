# RC6 Feature Plan — Evidence-Bound Development Continuation

Status: **ACCEPTED / FROZEN FOR RC6 IMPLEMENTATION**

This document is the accepted RC6 feature-plan authority. Implementation must not silently grow beyond it.

Design baseline examined: RC6 branch at `94c77236e4a5f5100ae4785d246118a6925bcaf7`, plus the planning documents added afterwards.

RC5d base: `4370c0d63173d27556b11d629746afee07f3cf62`.

Supporting historical design inputs:

- `docs/archive/rc6/RC6-CURRENT-DEFECT-FIX-PLAN.md`
- `docs/archive/rc6/RC6-EXTERNAL-DEVELOPMENT-GAP-AUDIT.md`

## 1. RC6 product objective

RC6 adds one coherent capability to CodeSleuth:

> **Evidence-bound development continuation.**
>
> Given an unfamiliar or mature repository, CodeSleuth discovers what that repository itself declares authoritative, determines the admissible next development scope, binds the scope to an exact target and project-native verification gates, prevents accidental scope expansion, and explicitly stops when remaining proof requires a live runtime or operator decision.

RC6 does not turn CodeSleuth into a primary coding agent or project manager. The active host remains the controller and execution owner.

## 2. Why RC6 exists

Existing CodeSleuth is already useful for:

- exact-target identity;
- repository inventory;
- code/docs/tests contract triangulation;
- durable review state;
- protected-capability/forbidden-regression reasoning when a registry exists;
- bounded reports and provenance;
- exact-head acceptance campaigns.

The missing layer appears when the user asks: **"continue developing this repository"**.

A useful answer requires more than a bug list. It requires knowing:

- which roadmap/session/packet is authoritative;
- which documents are only evidence or history;
- which predecessor work is already accepted;
- what is allowed to change now;
- what must not be mixed into this scope;
- which native tests/gates prove the change;
- which proof can run in repository/GitHub CI;
- which proof genuinely requires a live host.

The PII Parser and Aleph Rugent audits demonstrate both forms of this problem without requiring repository-specific CodeSleuth features.

## 3. RC6 scope

RC6 consists of six feature slices plus current-defect closure.

### RC6-0 — Close all current cloud-testable defects

Implement the accepted defect-closure requirements before declaring any new feature slice complete.

Required outcomes:

- one canonical EHA bridge entry point;
- deterministic pre-provider campaign and provenance bootstrap;
- no prose-based behavior tests;
- dirty/blob-safe brownfield evidence;
- generic foreign-repository registry core separated from CodeSleuth self-registry rules;
- resumable user adjudication;
- distribution/install parity;
- current normative docs;
- exact-head hosted acceptance green.

### RC6-A — Deterministic EHA authority before and after provider execution

RC6-A finishes the EHA transport/authority redesign started in the branch.

#### Contract

For trusted GitHub EHA:

```text
freeze exact release SHA
-> wire durable state
-> bind deterministic provenance producer
-> create review checkpoint
-> write campaign_started
-> invoke OpenCode/provider
-> model records SIB evidence/verdicts
-> report persists
-> write campaign_completed
-> bridge may terminate provider transport
```

The provider owns neither campaign existence nor final completion authority.

#### Must preserve

- failed-SHA immutability;
- exact-head discipline;
- trusted owner gating;
- read-only candidate checkout;
- external durable persistence;
- transport outcome separate from EHA verdict;
- provenance as attribution only.

#### Not included

- provider-specific retry intelligence;
- a second EHA implementation in Python;
- relaxing SIB evidence requirements.

### RC6-B — Brownfield contract bootstrap

Purpose: allow a repository with no CodeSleuth Protected Capability Registry to discover and explicitly canonize existing contracts.

#### Pipeline

```text
exact target
-> bounded inventory
-> ephemeral contract archaeology
-> exact code/docs/tests triangulation
-> durable candidate
-> stop for user adjudication
-> explicit decision
-> optional materialization
-> new candidate identity after tracked write
```

#### Legal adoption

- `AGREE + adopt` -> at most `implemented`;
- `UNPROVEN + adopt_unproven` -> at most `experimental`;
- `CODE_AHEAD`, `DOC_AHEAD`, `TEST_AHEAD`, `CONTRADICTED` -> cannot be adopted until resolved/re-triangulated;
- no bootstrap path may infer `sib1_accepted`, `sib2_integrated` or `protected`.

#### Generic registry core

Foreign repositories receive only a generic schema core. CodeSleuth's own SIB0 inventory and historical SIB evidence are never copied into another repository.

#### Human authority

Every analytical Playbook Step remains isolated. No subagent may approve its own discovery. Durable adoption requires an explicit current user instruction handled by the primary controller.

### RC6-C — Development Authority Map

Add an atomic reasoning Skill and bounded state representation for repository development authority.

Suggested Skill id: `development-authority-discovery`.

#### Purpose

Discover relationships among repository-native planning and development documents without relying on filenames as authority.

#### Required relationship classes

- `CANONICAL_PLANNING_AUTHORITY`
- `ACTIVE_IMPLEMENTATION_SCOPE`
- `NORMATIVE_ARCHITECTURE`
- `ACCEPTANCE_AUTHORITY`
- `ACCEPTED_PREDECESSOR`
- `SUPPORTING_EVIDENCE`
- `SUPERSEDES`
- `SUPERSEDED_BY`
- `HISTORICAL_ARCHIVE`
- `ADJACENT_PARALLEL_TRACK`
- `FORBIDDEN_COMPETING_AUTHORITY`

Names may differ, but meanings must remain distinct.

#### Evidence rule

Every authority edge must carry exact tracked evidence:

- path;
- blob hash;
- bounded excerpt/line locator;
- exact target SHA;
- classification confidence/status.

Filename conventions may be discovery hints, never authority evidence by themselves.

#### Output

A bounded `DevelopmentAuthorityMap` suitable for human inspection and subsequent Playbook Steps.

It is derived navigation, not a replacement for the target repository's documents.

### RC6-D — Development Continuation Packet and scope guard

Add one user-facing continuation workflow.

Suggested command: `/repo-continue`.

Suggested Playbook: `repository-development-continuation`.

#### Playbook outline

1. `capture-target`
   - exact target identity;
2. `resolve-authority`
   - build Development Authority Map;
3. `select-active-scope`
   - determine the currently admissible work item/session from target authority;
4. `map-change-surface`
   - collect allowed/owned/affected paths and dependency surfaces;
5. `map-native-gates`
   - collect project-native tests/verification/acceptance requirements;
6. `emit-continuation-packet`
   - bounded result only; no source edits.

All analytical Steps use fresh host-native subagents under the existing Playbook contract.

#### Continuation packet schema

Minimum fields:

```text
targetSha
planningAuthority
activeScope
objective
prerequisites
acceptedPredecessors
requiredReading
allowedPaths
forbiddenOrAdjacentPaths
changeSurface
nativeGates
repoProvableChecks
hostedCiProvableChecks
liveRuntimeRequiredChecks
operatorDecisionRequired
blockers
uncertainties
authorityEvidence
```

#### Scope guard

A deterministic tool compares a proposed branch/PR/path set against the continuation packet.

Result classes:

- `IN_SCOPE`
- `UNDECLARED`
- `ADJACENT_TRACK`
- `FORBIDDEN_BY_ACTIVE_SCOPE`
- `SCOPE_AUTHORITY_UNPROVEN`

The guard must not auto-expand the selected scope.

#### Existing packet rule

When a repository already has a canonical coding/session packet, CodeSleuth summarizes/selects it. It does not create a competing roadmap or session authority.

### RC6-E — Native Gate Map and cloud-testability boundary

Add a bounded `NativeGateMap` derived from project-owned evidence.

#### Discoverable gate sources

- CI workflow files;
- verify/build/test scripts;
- package/workspace test commands;
- session packet acceptance criteria;
- definition-of-done documents;
- migration/schema validation commands;
- explicit live smoke/rollback requirements.

#### Gate classes

Every gate must be classified as one of:

1. `REPO_PROVABLE`
2. `HOSTED_CI_PROVABLE`
3. `SERVICE_DEPENDENT_REPRODUCIBLE`
4. `LIVE_RUNTIME_REQUIRED`
5. `OPERATOR_DECISION_REQUIRED`

The first two form the normal CodeSleuth cloud completion boundary.

#### Handoff rule

CodeSleuth must explicitly report:

```text
CLOUD_TESTABILITY_REMAINING
```

while any required `REPO_PROVABLE` or `HOSTED_CI_PROVABLE` gate is red or unexecuted.

Only after those categories are closed may the packet report:

```text
LIVE_HANDOFF_READY
```

This is the formal boundary for handing remaining debugging to Work/Cursor/OpenCode on a live host.

### RC6-F — Generic external evidence manifest

Add a typed evidence envelope for later live-host observations without adding product-specific service integrations.

Suggested schema: `ExternalEvidenceManifestV1`.

Minimum fields:

```text
schemaVersion
adapterId
repositorySha
observedAt
freshnessTtlSeconds
checkId
sourceKind
sanitizedResult
evidenceLocator
nativeOutcome
notes
```

#### Rules

- secrets/raw credentials are forbidden;
- runtime observations never override repository contracts by themselves;
- stale observations are visibly stale;
- `PASS`/`FAIL` is recorded only when the underlying native check defines that outcome;
- exact repository SHA linkage is mandatory;
- manifest ingestion is append-only/durable evidence, not controller authority.

#### RC6 implementation boundary

RC6 implements the schema, validation and ingestion/navigation boundary only.

It does **not** implement PII-specific llama.cpp/Temporal adapters or Aleph-specific PostgreSQL/Qdrant/Infinity/OpenAleph probes. Those remain host/tool adapters that can be loaded later.

## 4. Pre-registry change-surface mapping

The Development Continuation workflow must remain useful before a Protected Capability Registry exists.

It may derive a non-authoritative change-surface graph from:

- language/package workspaces;
- import/module ownership;
- migrations;
- schemas/DTOs;
- API definitions;
- CI/verify scripts;
- tests referencing changed surfaces;
- explicit docs ownership and allowed-path declarations.

This graph can propose brownfield contracts and dependencies, but it cannot claim protected status.

Once a target-local registry exists, protected-capability dependency closure becomes the stronger authority.

## 5. Repository-specific invariant promotion

RC6 must not turn every discovered pattern into a global CodeSleuth lint.

Required promotion lifecycle:

```text
observed invariant
-> evidence-bound candidate
-> triangulation
-> explicit user/maintainer adjudication
-> target-local contract or native gate
```

This reuses RC6-B rather than introducing automatic policy invention.

## 6. Product surfaces

RC6 may add or extend only normal CodeSleuth control-surface units:

- Skills;
- Playbooks;
- bounded tools/state;
- commands;
- adapter/evidence schemas;
- CLI/TUI catalog exposure;
- tests/docs.

No new primary agent runtime or execution engine is permitted.

### Expected user-facing surfaces

- `/repo-contract-bootstrap`
- a resumable contract-bootstrap continuation/adjudication surface
- `/repo-continue`
- existing `/eha-test` with deterministic trusted prestart under GitHub bridge

TUI may expose the new Playbooks through the existing catalog/detail/load architecture. No separate RC6 UI family is required.

## 7. Acceptance fixtures

Private external repositories must not become CI dependencies.

Create small deterministic fixture repositories that encode the authority patterns observed in the audits.

### Fixture A — layered TODO/worklog repository

Model the structural problem demonstrated by PII Parser:

- one explicit planning SSOT;
- superseded roadmaps;
- supporting current-state evidence;
- archived shipped work;
- a critical-path stop-gate;
- mixed repository and live-runtime acceptance requirements.

Acceptance:

- CodeSleuth selects only the declared SSOT;
- does not revive superseded plans;
- selects the prerequisite stop-gate as next scope;
- classifies live runtime proof separately.

### Fixture B — waypoint/session-packet repository

Model the structural problem demonstrated by Aleph Rugent:

- Orientation selects active track;
- Waypoint plan defines order;
- session packet defines objective, allowed paths and exclusions;
- accepted predecessor handoff;
- adjacent parallel track;
- native verify gates;
- no protected-capability registry initially.

Acceptance:

- CodeSleuth selects the active session packet;
- preserves predecessor and required reading;
- scope guard rejects adjacent-track paths;
- absence of registry does not prevent continuation mapping;
- brownfield bootstrap can later create target-local contract candidates.

## 8. Hosted acceptance matrix

Before live-host testing, one exact RC6 head must pass:

### Python

- Python 3.10 Ubuntu;
- Python 3.12 Ubuntu;
- Python 3.10 Windows;
- Python 3.12 Windows;
- ruff;
- full pytest;
- contributor anti-pattern gate.

### Bun/state

- existing durable review/provenance/EHA state;
- brownfield bootstrap state;
- Development Authority Map state/validation;
- scope guard;
- Native Gate Map;
- ExternalEvidenceManifest validation;
- existing context graph and Mermaid QA.

### Existing protected features

- TUI visual regression;
- Graphify enabled runtime;
- install/update/uninstall smoke parity;
- Playbook/Skill/Command/Tool contracts.

No existing acceptance job may be removed to make RC6 green.

## 9. Live-host acceptance after cloud completion

Only after hosted acceptance is fully green, perform read-only development-continuation dogfood on the two audited repositories.

### PII Parser live dogfood

Expected result:

- exact current HEAD identified;
- canonical planning SSOT identified as the current TODO/worklog authority;
- superseded roadmaps excluded;
- next admissible critical-path item selected from repository evidence;
- repository/CI work separated from runtime-only evidence;
- no source modification.

### Aleph Rugent live dogfood

Expected result:

- exact current HEAD identified;
- Orientation/current packet/handoff/Waypoint/Gates authority chain reconstructed;
- active implementation session selected;
- allowed paths and adjacent parallel tracks distinguished;
- native verify gates listed;
- target-local registry absence routed to brownfield bootstrap rather than treated as permission to use CodeSleuth's own registry;
- no source modification.

These dogfood runs validate usefulness and host integration. They are not substitutes for hosted deterministic tests.

## 10. RC6 EHA/release acceptance

After implementation, hosted acceptance and live dogfood:

1. create one exact release-stream candidate SHA;
2. run canonical hosted acceptance on that exact SHA;
3. run fresh EHA SIB0/SIB1/SIB2 on the same SHA;
4. require durable prestart identity and durable completion handshake;
5. preserve failed-SHA immutability;
6. only then consider release/SIB ref promotion.

## 11. Explicit non-goals

RC6 does not include:

- autonomous coding or merge decisions;
- autonomous modification of foreign roadmaps/session packets/ADRs;
- a second controller or model runtime;
- project-specific PII Parser adapters;
- project-specific Aleph adapters;
- live-service orchestration inside GitHub-hosted CI;
- automatic SIB status assignment to foreign repositories;
- automatic promotion of discovered behavior into protected contracts;
- semantic reranking of repository authority based on hashes/IDs;
- replacing project-native verification with CodeSleuth-specific generic gates.

## 12. Implementation order after scope acceptance

### Wave 1 — repair and authority foundations

- RC6-0 D1-D4;
- canonical EHA bridge/prestart/provenance;
- dirty/blob-bound brownfield state.

### Wave 2 — brownfield completion

- generic registry core;
- resumable human adjudication;
- materialization tests.

### Wave 3 — continuation intelligence

- Development Authority Map;
- authority evidence model;
- pre-registry change-surface map.

### Wave 4 — actionable continuation

- `/repo-continue` Playbook;
- continuation packet;
- scope guard;
- Native Gate Map;
- cloud/live classification.

### Wave 5 — live-evidence boundary

- ExternalEvidenceManifestV1;
- adapter ingestion contract;
- stale/fresh/exact-SHA tests.

### Wave 6 — distribution and documentation

- install/update/smoke parity;
- command/catalog/TUI exposure;
- normative docs;
- fixture repositories.

### Wave 7 — exact-head acceptance

- 7/7 hosted acceptance;
- only then live dogfood on PII Parser and Aleph Rugent;
- fresh EHA on release-stream exact SHA.

## 13. RC6 definition of done

RC6 is complete only when all statements below are true:

1. Trusted EHA campaign identity exists durably before provider execution and completion authority is durable after evidence/reporting.
2. Brownfield repositories can bootstrap contracts without importing CodeSleuth-specific acceptance history.
3. User authority is required before a discovered contract becomes tracked repository policy.
4. CodeSleuth can identify a repository's development/planning authority without filename-only inference.
5. CodeSleuth can produce one evidence-bound continuation packet without creating a competing roadmap.
6. Repository-declared allowed/forbidden scope can be checked against proposed changes.
7. Project-native gates are discovered and divided into cloud-testable versus live-only proof.
8. CodeSleuth explicitly refuses live handoff while cloud-testable required gates remain unresolved.
9. Live observations have a typed, freshness-aware, exact-SHA-bound evidence envelope and do not become repository authority automatically.
10. Existing CodeSleuth protected capability contracts remain green.
11. One final exact RC6 candidate passes the complete hosted acceptance matrix before any live dogfood.
12. Read-only dogfood on both audited repositories produces useful next-development packets without repository-specific CodeSleuth code.

Acceptance of this document freezes RC6 feature scope. Any additional feature belongs to a later release unless required to satisfy one of the above contracts.
