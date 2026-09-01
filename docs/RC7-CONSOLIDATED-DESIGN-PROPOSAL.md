# RC7 Consolidated Design Proposal

**Status:** FROZEN DESIGN PROPOSAL / THESIS BASELINE / NOT RC7 IMPLEMENTATION AUTHORITY  
**Branch:** `docs/rc7-ledger-authority-repair-plan`  
**Purpose:** preserve the first consolidated RC7 architecture assessment as an immutable review baseline before independent adversarial review is reconciled.  
**Freeze meaning:** this document is frozen as the **thesis** in the RC7 design dialectic. Freezing this proposal does **not** freeze RC7 implementation scope, accept the design for implementation, or supersede existing normative product/evidence/SIB/EHA contracts.

## 1. Executive proposal

RC7 should be implemented as **domain-specific durable histories plus shared evidence mechanics and typed derived workflow objects**, not as a generic workflow/storage/rendering platform.

Compact proposal:

> **RC7 = domain-specific durable histories + first-class acceptance identity + project-adjudicated SIB semantics + evidence-bound repair convergence + renderer-neutral typed projections.**

The design is viable without reopening the current CodeSleuth SIB0 architecture only if every RC7 mechanism remains population inside the existing capability classes and does not introduce a new authority, runtime, persistence plane, or controller.

The required placement is:

| RC7 area | Existing capability class |
| --- | --- |
| implementation ledger / ledger integrity | `CC-STATE` |
| project SIB / acceptance profiles | `CC-ACCEPT` |
| generic EHA mechanics | `CC-ACCEPT` |
| repair Playbooks / host dispatch | `CC-PACK` |
| repair durable workflow artifacts | `CC-STATE`, without a duplicate evidence authority |
| renderer mechanics | shared internal mechanics used by `CC-GRAPH`, `CC-REPORT`, `CC-PACK` |
| Markdown adapters | projection/import adapter, not persistence authority |
| Obsidian compatibility | derived projection only |
| Doris | explicitly outside RC7 |

A shared kernel is allowed only as mechanics/types. It must never become a new semantic owner of project facts.

---

## 2. Proposed authority topology

```text
                        PROJECT / HUMAN AUTHORITY
                                  |
          +-----------------------+-----------------------+
          |                       |                       |
          v                       v                       v
  project contracts       ProjectSibProfile       AcceptanceProfile
  / planning authority       accepted                accepted
          |                       |                       |
          +-----------------------+-----------------------+
                                  |
                                  v
                         CodeSleuth execution
                                  |
       +--------------------------+-------------------------+
       |                          |                         |
       v                          v                         v
Finding authority      Implementation authority      EHA authority
findings*.ndjson       implementation*.ndjson         eha.ndjson
       |                          |                         |
       +--------------------------+-------------------------+
                                  |
                          cross-ledger stable IDs
                                  |
               +------------------+------------------+
               |                  |                  |
               v                  v                  v
         ClaimEnvelope       RepairCase        RepairPacket
          read model       workflow artifact   workflow artifact
               |                  |                  |
               +------------------+------------------+
                                  |
                            typed projections
                                  |
         +------------+-----------+----------+------------+
         v            v                      v            v
       JSON        Markdown               Mermaid       Jinja2
      NDJSON       HTML etc.             Canvas         host prompt
         |            |                      |            |
         +------------+----------------------+------------+
                                  |
                          DERIVED ONLY
```

The governing authority rules are:

1. Git/current tracked content remains source authority.
2. Findings/amendments remain finding-history authority.
3. The implementation ledger owns accepted-plan execution history only.
4. `eha.ndjson` remains EHA campaign/verdict authority and is evolved rather than replaced.
5. Protected capability/contract authority remains with the existing project registry/process.
6. Claim envelopes, Repair Cases, Repair Packets, learning records and renderings are non-authoritative workflow/read-model artifacts unless a domain contract explicitly assigns narrower authority.
7. A derived projection never flows backward and changes authority by convenience.

---

## 3. RC7 capability outcomes

### 3.1 Native Implementation Ledger

RC7 should replace Markdown-as-current-state with a native append-only implementation-history domain.

Required authority flow:

```text
accepted plan identity
        |
        v
append-only implementation events
        |
        v
validated current requirement state
        |
        +--> status/query tools
        +--> generated Markdown implementation ledger
        +--> graph/presentation projections
```

The ledger records facts about plan execution and verification work. It must not infer completion merely from changed files or model prose.

Minimum event families:

- plan binding / revision identity;
- requirement implementation evidence;
- focused gate/check execution evidence;
- verification result/reference;
- blocker/defer decisions;
- supersession/amendment;
- repair/recovery lineage.

The human-readable implementation ledger is derived and rebuildable.

### 3.2 Ledger integrity and structural recovery

RC7 needs reusable integrity mechanics without creating a universal semantic ledger.

Conceptual split:

```text
DomainLedger<TEvent>
    parse / validate syntax
    validate IDs/schema/order/linkage
    classify integrity
    derive domain state through domain rules
```

Structural recovery preserves the damaged generation and creates lineage rather than rewriting bytes:

```text
corrupt generation G0
        |
        +--> preserved exact bytes + digest
        |
        v
RecoveryManifest
        |
        v
new generation G1
        |
        +--> predecessorDigest = digest(G0)
        +--> explicit unresolved gaps
```

No historical generation is edited in place. Missing facts are never manufactured.

### 3.3 EBCA shared transport primitives

RC7 should define small typed non-authoritative primitives sufficient to preserve EBCA dimensions across workflows:

```text
ClaimEnvelopeV1
AuthorityRefV1
EvidenceRefV1
EnvironmentIdentityV1
AcceptanceProfileRefV1
```

These are transport/read-model types, not a generic claim database.

### 3.4 Project-portable SIB maturity

The proposal separates project maturity semantics from the exact acceptance configuration used to test a particular claim.

Two objects are proposed:

```text
ProjectSibProfileV1
AcceptanceProfileV1
```

`ProjectSibProfileV1` describes the project's architecture generation, capability classes, contracts, SIB0/SIB1/SIB2 claims, candidate-selection policy, repair policy and adjudication evidence.

`AcceptanceProfileV1` describes the exact obligations, gates, environment matrix, material tool/runtime identities and aggregation semantics required for a particular acceptance claim.

The two identities must not be conflated with Git subject identity or execution/run identity.

### 3.5 Generic EHA V2

RC7 should evolve the existing EHA authority, not create a second generic EHA store.

A campaign binds:

```text
exact source subject
+ ProjectSibProfile identity
+ AcceptanceProfile identity
+ required environment/tool evidence
+ durable campaign lifecycle
```

The EHA event model must support at least:

```text
PASS
FAIL
INCONCLUSIVE
UNAVAILABLE
NOT_APPLICABLE
```

All maturity claimed for an exact subject remains cumulative and exact-subject-specific. Historical ancestry transfers context, not acceptance.

### 3.6 Evidence-bound repair convergence

Canonical source/EHA repair flow:

```text
failed verdict
-> RepairCaseV1
-> contract/authority triangulation
-> affected-closure trust evaluation
-> RepairPacketV1
-> mutation preflight
-> host-specific structured rendering
-> host-owned mutation
-> postcondition re-observation
-> new exact candidate
-> fresh acceptance
-> derived RepairLearningRecordV1
```

Diagnosis is not permission. Host output is not state authority. The postcondition observer must re-read actual diff/worktree/SHA and required witnesses.

### 3.7 Renderer-neutral structured projections

RC7 should define a renderer contract before multiplying formats.

Every renderer declares at least:

```text
rendererId
rendererVersion
acceptedSchemaIds[]
semanticCoverage
lossProfile
roundTripCapability
orderingPolicy
canonicalizationPolicy
escaping/securityPolicy
requiredFields[]
optionalFields[]
projectionAuthority = none
```

The renderer never independently selects domain semantics. Domain projection/query logic selects the semantic object/window; a renderer only represents that already-selected object.

### 3.8 Projection parity

Parity is tested from the typed domain object outward:

```text
domain object
    +--> renderer A
    +--> renderer B
    +--> renderer C
```

Semantic parity compares identity, provenance, status/result, assumptions, limitations, uncertainty, ordering and graph relations where declared. Renderer-to-renderer textual equality is not the criterion.

---

## 4. Proposed schema boundaries

### 4.1 `ClaimEnvelopeV1`

```text
schemaVersion
claimId
subject
property
scope
assumptions[]
authorityRefs[]
evidenceRefs[]
environment[]
observedAt
result
limitations[]
residualUncertainty[]
```

Allowed result vocabulary:

```text
PASS
FAIL
INCONCLUSIVE
UNAVAILABLE
NOT_APPLICABLE
```

`NOT_APPLICABLE` requires explicit profile rationale.

This type is non-authoritative transport/read-model structure.

### 4.2 `ProjectSibProfileV1`

```text
schemaVersion
projectSibProfileId
version
digest
repositoryIdentity
architectureGenerationId
discoveryCoverage
authorityRefs[]
adjudicationRef
capabilityClasses[]
ownershipModel
contracts[]
sib0Claim
sib1Claim
sib2Claim
candidateSelectionPolicy
architectureReopenPolicy
repairPolicy
preservationPolicy
acceptanceProfileRef
assumptions[]
limitations[]
```

`discoveryCoverage` records at least:

```text
universeMethod
scannedSources[]
unavailableSources[]
truncated
limitations[]
completenessSupportable
```

A discovered count is not a completeness claim.

### 4.3 `AcceptanceProfileV1`

```text
schemaVersion
profileId
profileVersion
profileDigest
projectSibProfileRef
obligations[]
gates[]
environmentMatrix[]
materialToolRequirements[]
materialRuntimeRequirements[]
aggregationPolicy
notApplicablePolicy
completionPolicy
authorityRefs[]
adjudicationRef
assumptions[]
limitations[]
```

The profile digest is over semantic content rather than timestamps, comments or rendering metadata.

Changing a required gate, obligation, environment, material tool/runtime identity, aggregation policy or N/A policy changes acceptance-profile identity without necessarily changing architecture generation.

### 4.4 `EhaVerdictV2`

```text
schemaVersion: 2
eventId
campaignId
targetSha
sibLevel
projectSibProfileRef
acceptanceProfileRef
claim: ClaimEnvelopeV1
result
runRefs[]
actualEnvironment[]
actualToolRuntimeIdentities[]
blockerFindingIds[]
repairCaseRefs[]
recordedAt
recordedHeadSha
```

Legacy EHA records remain historical V1 evidence. RC7 must not silently reinterpret them as profile-aware V2 PASS.

### 4.5 `RepairCaseV1`

```text
schemaVersion
repairCaseId
failedSubject
campaignRef
sibLevel
failedGate
failedClaim
maturityImpact
rootCauseClassification
contractRefs[]
contractEvidenceRefs[]
observedFailure
reproduction
affectedCapabilityRefs[]
changeSurface
recentRelevantDeltaRefs[]
protectedConstraints[]
forbiddenRegressionRefs[]
closureTrust
uncertainty[]
assumptions[]
limitations[]
liveEvidenceRequirements[]
stopConditions[]
```

`maturityImpact` and `rootCauseClassification` are different axes.

Maturity impact:

```text
SIB0 | SIB1 | SIB2
```

Root-cause/triangulation classification:

```text
AGREE
CODE_AHEAD
DOC_AHEAD
TEST_AHEAD
CONTRADICTED
UNPROVEN
```

Neither of these replaces semantic-refit status or delivery disposition.

### 4.6 `RepairPacketV1`

```text
schemaVersion
repairPacketId
repairCaseRef
packetDigest
failedSubject
projectSibProfileRef
acceptanceProfileRef
objective
selectedRepairStrategy
allowedChangeSurface[]
forbiddenChangeSurface[]
affectedClosure
closureTrust
invariantCore[]
requiredRegressionWitnesses[]
verificationPlan[]
postconditionChecks[]
authoritySnapshotRefs[]
sourceFreshnessRefs[]
hostPolicyConstraints[]
assumptions[]
limitations[]
residualUncertainty[]
stopConditions[]
```

Branch/worktree/PR navigation metadata is execution metadata, not mandatory repair semantics.

### 4.7 `RepairLearningRecordV1`

```text
schemaVersion
learningId
repairCaseRef
failedSha
acceptedRepairedSha
violatedClaimRef
rootCause
whyPreviousChecksMissed
repairStrategy
repairDeltaRefs[]
regressionWitnessRefs[]
preservationCandidate
applicability
nonApplicability
evidenceRefs[]
acceptanceRefs[]
assumptions[]
limitations[]
```

Status: retained derived analytical artifact, `authority = none`.

A regression witness remains real source/test evidence. A preservation candidate becomes project contract authority only through project-specific promotion/adjudication.

### 4.8 Integrity and closure status

Keep ledger integrity and affected-closure trust as distinct claims:

```text
LedgerIntegrityStatus:
  TRUSTWORTHY
  DEGRADED_BUT_READABLE
  UNTRUSTED
  REPAIR_REQUIRED
  UNRECOVERABLE_WITHOUT_OPERATOR_DECISION
```

```text
ClosureTrust:
  TRUSTWORTHY
  DEGRADED
  UNTRUSTED
```

### 4.9 `LedgerRecoveryManifestV1`

```text
recoveryId
ledgerDomain
predecessorGeneration
predecessorPath
predecessorDigest
originalBytesPreserved
corruptionClassification[]
corruptRanges[]
repairProposal
recoveredGeneration
recoveredDigest
unresolvedGaps[]
resultingIntegrityStatus
evidenceRefs[]
operatorDecisionRef
createdAt
```

The manifest is lineage/provenance. Historical bytes remain frozen.

---

## 5. Current implementation migration pressure

The existing EHA implementation is a V1 authority that must be evolved deliberately.

Known migration points include:

1. verdicts currently support only `PASS | FAIL`;
2. verdict `profile` is currently a free string;
3. SIB claimability is currently derived from cumulative PASS without requiring durable campaign completion;
4. a recorded FAIL currently blocks another campaign on the same SHA regardless of acceptance-profile identity;
5. repair classification is currently mechanically derived from the SIB level;
6. repair branch ancestry is currently embedded in the generic tool semantics.

RC7 must define explicit V1 read compatibility and V2 write semantics before modifying the existing authority.

---

## 6. Markdown import boundary

Normal path:

```text
typed/domain authority
       |
       v
Markdown AST builder
       |
       v
Markdown presentation
```

If controlled migration/import is needed:

```text
known Markdown structure
       |
       v
AST parser
       |
       v
project mapping profile
       |
       v
schema validation
       |
       v
IMPORT PROPOSAL
       |
       v
domain-specific adjudication/write API
```

An edited Markdown file never directly becomes evidence authority.

---

## 7. Proposed RC7 renderer implementation minimum

The renderer registry may classify a wider universe, but first-release implementation should remain bounded.

| Format | Proposed RC7 disposition |
| --- | --- |
| JSON | REQUIRED |
| NDJSON | REQUIRED where domain/interchange requires it |
| Markdown | REQUIRED |
| Jinja2 host prompts | REQUIRED |
| Mermaid | REQUIRED by reuse of existing product surface |
| SVG | only through the already bounded existing exporter |
| JSON Canvas | proposed second graph/parity target |
| YAML/frontmatter | only where Markdown/Obsidian compatibility needs it |
| JSONC/TOML | registry-known, implementation optional |
| JSON-LD/GraphML/DOT | registry-known, later unless a concrete core schema needs them |
| SARIF/JUnit | only for honestly corresponding domain subsets |
| HTML | derived presentation, later unless effectively free |
| PNG | not required |

No renderer may create a parallel selection algorithm for graph/domain subsets.

---

## 8. Obsidian boundary

RC7 may use Obsidian compatibility as evidence that structured projections are portable and human-usable, but Obsidian remains a downstream read model.

Allowed direction:

```text
CodeSleuth authority
    -> typed domain objects
    -> generated vault/projection
    -> Markdown/properties/backlinks/Bases/Canvas
```

No Obsidian edit changes upstream authority in RC7. Import or plugin adjudication is future work and, if implemented later, must produce explicit proposals into domain APIs rather than direct write-back.

---

## 9. Explicit post-RC7 exclusions

The proposal excludes these from RC7 implementation scope:

- generic NegativeClaim database;
- generic `FORBIDDEN_INFERENCE` engine;
- universal R0-R3 mutation-risk framework;
- general destructive-action approval system;
- full Remote Operator Assurance implementation;
- long-context degradation benchmark suite;
- universal grounding benchmark;
- full SACM assurance-case engine;
- bidirectional traceability-completeness certification;
- signed/tamper-resistant provenance subsystem;
- reproducible-build subsystem;
- generic workflow engine/scheduler;
- generic database/CRUD service;
- independent CodeSleuth agent/controller;
- bidirectional Obsidian write-back;
- Doris persistence or Doris search-plane implementation.

Doris remains a future rebuildable analytical/search plane candidate only if real scale justifies it.

---

## 10. Proposed implementation slices

These are design-time slices, not authorization to begin implementation.

| Slice | Scope | Independent acceptance focus |
| --- | --- | --- |
| RC7-0 | consolidated spec + schema/migration rules | docs/schema contracts |
| RC7-1 | EBCA primitives + canonical digests + V1/V2 adapters | schema/adversarial unit tests |
| RC7-2 | Native Implementation Ledger + derived Markdown | append-only, plan binding, projection parity |
| RC7-3 | ledger integrity + recovery generations | torn/duplicate/illegal/corrupt fixtures |
| RC7-4 | ProjectSibProfile discovery + adjudication + AcceptanceProfile | brownfield alternatives/truncation |
| RC7-5 | EHA V2 | profile-bound results, non-binary outcomes, V1 compatibility |
| RC7-6 | RepairCase + triangulation + closure trust | authority-conflict and closure tests |
| RC7-7 | RepairPacket + preflight + Jinja renderers | stale packet, forbidden scope, injection tests |
| RC7-8 | postcondition verification + RepairLearningRecord | false host success, diff re-observation, preservation proposal |
| RC7-9 | renderer registry + Markdown AST + graph parity | round-trip/loss/parity tests |
| RC7-10 | distribution parity + docs + installed smoke + adversarial matrix | hosted exact-head acceptance |

Each implementation slice should begin from a concrete failing witness and close with focused plus affected-surface verification before the next slice is opened.

---

## 11. Adversarial acceptance requirements

At minimum RC7 must fail closed for these conditions:

1. required evidence unavailable;
2. code/docs/tests contradiction;
3. silently truncated SIB0 discovery;
4. unavailable discovery authority source;
5. same SHA with changed acceptance-profile digest;
6. materially different runtime/tool identity;
7. stale RepairPacket or stale source evidence;
8. host claims success while worktree is unchanged;
9. host changes forbidden or adjacent path;
10. untrusted affected closure used to justify narrow verification;
11. required regression witness omitted;
12. unsupported `NOT_APPLICABLE` rationale;
13. failed SHA being rewritten into success;
14. architecture-changing repair hidden as local repair;
15. repair-loop oscillation/stall;
16. corrupt recovered generation that drops bytes/facts silently;
17. predecessor bytes modified during recovery;
18. renderer drops material assumptions/limitations/uncertainty;
19. graph renderers disagree with the domain-selected graph;
20. missing Jinja variable silently disappears;
21. all SIB verdicts appear PASS without durable completion;
22. legacy V1 evidence is silently promoted into new V2 semantics;
23. retired documentation locator is treated as current authority without validation;
24. manual Markdown/Mermaid/Canvas/Obsidian edits flow upstream into authority.

---

## 12. Proposed freeze boundary

This proposal recommends that RC7 implementation begin only after a reviewed final design resolves, explicitly and normatively:

1. authority ownership for ProjectSibProfile and acceptance-profile identity;
2. physical/event schema and recovery-generation ownership for each durable domain;
3. V1 -> V2 EHA migration semantics;
4. non-binary outcome aggregation and durable completion semantics;
5. exact failed-subject/profile immutability semantics;
6. deterministic repair stopping;
7. SIB0 completeness/truncation rules;
8. affected-closure trust consequences;
9. RepairCase/RepairPacket mutation authorization boundaries;
10. renderer minimum scope and one-way import/projection rules;
11. install/smoke/catalog parity and adversarial acceptance.

Until that reviewed final design exists, this document remains a frozen **proposal baseline**, not implementation authority.
