# RC7 Thesis / Antithesis / Synthesis

**Status:** SYNTHESIS PROPOSAL / REVIEW CANDIDATE / NOT YET FROZEN RC7 DESIGN AUTHORITY  
**Branch:** `docs/rc7-ledger-authority-repair-plan`  
**Purpose:** reconcile the frozen first Consolidated Design Proposal with the independent adversarial review on branch `reviews` without retroactively rewriting either input.

## 1. Exact dialectic inputs

### Thesis

Frozen first design proposal:

- document: `docs/RC7-CONSOLIDATED-DESIGN-PROPOSAL.md`
- blob: `0f46825308454d9c8d0b3d0b48a2cdcc7845e120`
- freeze commit: `1b52c7c72e5294b3a4c145d1bbbd71a1863cb218`
- status: **FROZEN DESIGN PROPOSAL / THESIS BASELINE / NOT IMPLEMENTATION AUTHORITY**

### Antithesis

Independent adversarial review:

- branch: `reviews`
- review commit: `be5d158880f649ecb568d9a505c694e87bd76e0e`
- document: `docs/reviews/do-not-freeze-RC7.md`
- blob: `02a87228ed1b1b989c4e7dd785b0dd9acba8de9b`
- verdict: **DO NOT FREEZE RC7**

The review was performed against planning head:

`befa2dd182b986bf56c3318bb578150f36c16e40`

### Dialectic rule

Neither input is silently rewritten to make the other appear correct.

```text
thesis     = first consolidated design claim
antithesis = independent adversarial critique
synthesis  = explicit resolution with retained disagreement provenance
```

The thesis can remain a useful historical proposal even where the synthesis changes its design. The review remains review evidence rather than becoming design authority by itself.

---

# 2. Common ground

The review strongly agrees with the thesis on the following invariants. These become **preserved synthesis axioms**:

1. failed exact SHA remains failed under the acceptance claim/profile that failed;
2. repair creates a new source subject and fresh acceptance evidence;
3. ancestry transfers context, not acceptance;
4. Finding Ledger, Implementation Ledger and EHA Ledger remain separate domain authorities;
5. typed validated repair data precedes host rendering;
6. host output is not repository-state authority;
7. postcondition re-observation is mandatory after mutation;
8. material source evidence is rehydrated before mutation;
9. Graphify/Mermaid/search/reports remain navigation/projection, not source authority;
10. host remains execution authority; CodeSleuth does not acquire a supervisor/runtime;
11. regression witnesses survive repair and may become preservation obligations only through existing project authority;
12. Obsidian is one-way/read-model first;
13. generic Negative Claims, R0-R3 mutation assurance, ROAP, long-context assurance and broader Context Epistemics remain post-RC7;
14. existing `eha.ndjson` evolves in place as the EHA authority rather than being shadowed by a second generic EHA store.

The dispute is therefore not about the central EBCA direction. It is about **authority ownership, deterministic termination, completeness semantics and excessive genericity**.

---

# 3. Four BLOCKERs: thesis -> antithesis -> synthesis

## B1. Project SIB policy vs acceptance-profile identity

### Thesis

The frozen proposal separates:

```text
ProjectSibProfileV1
AcceptanceProfileV1
```

so architecture-generation identity and acceptance-configuration identity can change independently.

### Antithesis

If both are independently editable policy-bearing objects, they can encode contradictory obligations and become dual authority.

Example rejected by the review:

```text
ProjectSibProfile: SIB2 requires A+B+C
AcceptanceProfile: SIB2 requires A+B
```

### Synthesis

Keep **two identities**, but only **one policy owner**.

Replace the independently editable `AcceptanceProfileV1` concept with:

```text
AcceptanceProfileSnapshotV1
```

Authority flow:

```text
project-native acceptance authority
        OR
explicitly adopted ProjectSibProfile policy
                |
                v
      compile / validate / freeze
                |
                v
AcceptanceProfileSnapshotV1
                |
                v
           EHA campaign
```

Rules:

1. `ProjectSibProfileV1` has an explicit `authorityMode`:
   - `NATIVE_BOUND` — it binds to project-native architecture/acceptance authorities and does not replace them;
   - `ADOPTED_POLICY` — explicit project/maintainer adjudication makes this profile the project-local policy for the declared architecture generation.
2. `AcceptanceProfileSnapshotV1` is **derived immutable campaign input**, not independently editable policy authority.
3. Snapshot compilation records exact source authority refs/digests.
4. A snapshot may narrow representation into executable obligations only according to the owning policy's declared mapping/aggregation rules. It cannot drop a required obligation by local editing.
5. Changing policy produces a new policy identity; recompiling the same policy deterministically produces the same semantic snapshot digest modulo explicitly excluded metadata.
6. EHA binds to the exact snapshot digest, while policy authority remains upstream.

This preserves the thesis insight that architecture identity and acceptance-configuration identity are different while accepting the review's stronger one-owner rule.

---

## B2. Ledger Recovery must not become a meta-authority

### Thesis

The proposal introduces shared ledger-integrity mechanics plus lineage-preserving recovered generations.

### Antithesis

A generic `ledger_repair_apply` capable of choosing the new authoritative generation for arbitrary domains becomes an authority above findings/EHA/implementation ledgers.

### Synthesis

Split **shared structural mechanics** from **domain semantic recovery**.

```text
LedgerIntegrityCore
  - byte capture
  - digest
  - record framing / JSON/schema checks
  - duplicate/event reference detection primitives
  - generic lineage validation
  - corruption-range reporting
            |
            v
DomainLedgerAdapter<TEvent,TState>
  - domain event validation
  - legal transition validation
  - state derivation
  - recovery admissibility
  - missing-fact consequences
            |
            v
Domain-owned recovery operation
  - findings domain
  - EHA domain
  - implementation domain
```

The generic layer MUST NOT expose:

```text
make_generation_authoritative(anyLedger)
set_current_generation(anyDomain)
rewrite_domain_event(...)
```

Instead each domain owns a generation-selection record/operation through its existing or RC7-specific domain API.

Conceptual type:

```text
DomainGenerationSelectionV1 {
  domain
  previousGenerationRef
  selectedGenerationRef
  recoveryManifestRef
  operatorDecisionRef? 
  selectedAt
}
```

This selection record is part of the **domain authority**, not a generic recovery authority.

Examples:

- findings recovery is applied through finding/review-state recovery semantics;
- EHA recovery is applied through `eha_state` recovery semantics;
- implementation recovery is applied through implementation-ledger recovery semantics.

The shared recovery manifest remains provenance/lineage. It never decides domain truth by itself.

---

## B3. `REPAIR_LOOP_STALLED` must be deterministic

### Thesis

The proposal requires repair-loop stall/oscillation detection but does not freeze the exact state machine.

### Antithesis

A prose concept such as “same topology” or “no evidence increase” allows agents to keep trying indefinitely or disagree on whether progress exists.

### Synthesis

Introduce explicit attempt identity and required automatic-repair policy.

```text
RepairAttemptV1 {
  attemptId
  repairCaseRef
  sourceSubjectSha
  profileSnapshotDigest
  strategyId
  preMutationStateDigest
  resultingDiffDigest
  postMutationStateDigest
  failureSignatureBefore
  failureSignatureAfter
  obligationStateDigestBefore
  obligationStateDigestAfter
  focusedVerificationDigest
  postconditionResult
}
```

`failureSignature` is deterministic over the failed claim/gate/oracle and normalized observed failure identity defined by the domain adapter. It must not depend on free-form model prose.

`obligationStateDigest` is deterministic over the relevant obligation/result states selected by the validated repair policy.

Auto-repair is permitted only when the accepted repair policy defines:

```text
maxAutomatedAttempts > 0
```

If no explicit bound exists, automatic mutation is disabled and the workflow stops with `OPERATOR_DECISION_REQUIRED` before the first auto-repair attempt.

Mandatory terminal rules:

1. `HOST_POSTCONDITION_FAILED` when the host claims mutation but effective repository state does not satisfy required postconditions, including zero effective delta where a delta was required.
2. `REPAIR_LOOP_STALLED` when `maxAutomatedAttempts` is exhausted.
3. `REPAIR_LOOP_STALLED` when two consecutive completed attempts have the same `failureSignatureAfter` and identical `obligationStateDigestAfter` despite different patch prose.
4. `REPAIR_LOOP_STALLED` when a deterministic state cycle is observed, including `A -> B -> A` over `(failureSignature, obligationStateDigest, relevantStateDigest)`.
5. `REPRODUCTION_INCONCLUSIVE` when the original required defect/reproducer cannot be established sufficiently to authorize automatic mutation.
6. Any architecture/scope/evidence stop state terminates the loop immediately and does not consume further automatic attempts.

The exact attempt budget is project/policy data, not model discretion.

---

## B4. SIB0 completeness vs human adjudication

### Thesis

The proposal records `discoveryCoverage`, truncation, unavailable sources and `completenessSupportable` and requires human adjudication of a ProjectSibProfile.

### Antithesis

Human acceptance of a limitation cannot turn an incomplete evidence universe into an empirical completeness proof.

### Synthesis

Separate two materially different claims:

```text
DiscoveryCompleteness
PolicyCompleteness
```

### Discovery completeness

Question:

> Did the archaeology/discovery procedure cover the declared evidence universe sufficiently to claim it found all relevant capability classes within that universe?

This remains evidence-bound. Human optimism cannot change:

```text
INCOMPLETE / TRUNCATED / UNAVAILABLE
```

into complete.

### Policy completeness

Question:

> Has the project authority explicitly declared this capability-class inventory to be the complete intended architecture for this architecture generation?

A maintainer/project authority **can create or adopt policy**. That is not the same act as declaring an incomplete search exhaustive.

Therefore SIB0 may become claimable through either of two honest routes:

#### Route A — existing project policy

```text
exact current project authority
explicitly defines/fixes capability inventory
+ implementation slots/ownership verified
+ contradictions resolved
= policy completeness supported
```

#### Route B — discovery -> proposal -> explicit policy adoption

```text
bounded discovery evidence
-> transparent proposal with limitations
-> maintainer adjudication
-> explicit adoption as architecture policy
-> new policy identity
-> verification that repository state represents that adopted inventory
```

Crucial rule:

> Adoption creates current policy authority; it does not retroactively prove that the preceding discovery was exhaustive.

If neither a complete current policy nor an explicitly adopted complete policy exists, SIB0 remains `INCONCLUSIVE/UNPROVEN`.

A hidden/unreported truncation is always a validation failure.

---

# 4. High-severity synthesis decisions

| Review finding | Synthesis decision |
| --- | --- |
| H1 Implementation Ledger may duplicate EHA truth | **ACCEPT.** Implementation ledger records that a run/work step occurred and references EHA/run IDs. It never owns SIB verdicts. |
| H2 `ClaimEnvelopeV1` risks generic claim database | **ACCEPT WITH RENAMING.** Replace with `EbcaClaimViewV1` (or shared read-only interface). No persistence API, lifecycle, generic claim ledger or generic mutation. |
| H3 generic arbitrary Markdown↔NDJSON adapter is too broad | **ACCEPT.** RC7 requires authoritative-domain -> Markdown. Optional one bounded legacy-import proposal path only if needed. Generic project mapping framework moves post-RC7. |
| H4 renderer scope too broad | **ACCEPT.** RC7 implementation minimum becomes JSON, domain NDJSON, Markdown, Jinja presentation, and reuse of existing Mermaid. Other formats are post-RC7/research. |
| H5 Jinja may control semantic command construction | **ACCEPT.** Introduce structured `HostExecutionProfileV1`; Jinja controls wording/order/escaping only. |
| H6 `closureTrust=DEGRADED` lacks consequence | **ACCEPT.** Deterministic fallback required; model may not choose optimistically. |
| H7 LearningRecord preservation authority risk | **ACCEPT.** Learning record emits proposal only; promotion goes to existing protected-capability/project authority. |
| H8 DAM.CONFIRMED may be mistaken for canon | **ACCEPT.** `CONFIRMED` means evidence-supported mapping relation, never project policy adoption. |
| H9 `NOT_APPLICABLE` needs stronger rules | **ACCEPT.** Obligation-level only, authority-backed rationale, never substitute for unavailable evidence/environment. |
| H10 EHA must evolve existing authority | **ACCEPT / already intended.** V2 is schema evolution of existing `eha.ndjson`, not a parallel store. |

---

# 5. Medium/low synthesis decisions

## 5.1 Split repair cases

The thesis used one generic `RepairCaseV1`. The synthesis splits semantic domains:

```text
EhaRepairCaseV1
LedgerRecoveryCaseV1
```

`EhaRepairCaseV1` concerns source/project repair leading to a new Git subject.

`LedgerRecoveryCaseV1` concerns recovering trustworthy history without fabricating project/source facts.

Shared subtypes may be reused, but mutation permissions and authority ownership stay distinct.

## 5.2 Renderer registry is static/internal in RC7

RC7 uses internal capability descriptors, not a runtime-loadable universal renderer plugin system.

No arbitrary project renderer code is loaded merely because a repository declares it.

## 5.3 Root-cause epistemics

`RepairLearningRecordV1.rootCause` and `whyPreviousChecksMissed` must carry epistemic provenance:

```text
assessmentKind = OBSERVED | INFERRED | ADJUDICATED
supportingEvidenceRefs[]
limitations[]
```

A derived lesson may preserve a reasoned conclusion without masquerading as direct observation.

## 5.4 External evidence is referenced, not copied as truth

Repair packets may include bounded excerpts for host usability, but material external truth remains linked to the authoritative evidence record/source locator with freshness/TTL identity.

## 5.5 Parity is always source-object outward

Correct relation:

```text
domain object -> renderer A
domain object -> renderer B
domain object -> renderer C
```

Never infer semantic completeness merely because two lossy renderers agree with each other.

## 5.6 Obsidian generated/user boundary

Obsidian delivery moves out of mandatory RC7. Research fixtures may still prove one-way portability.

Any later O1 vault should separate generated machine-owned output from user-owned annotations, e.g.:

```text
generated/
annotations/
```

or another explicit non-overwrite boundary.

## 5.7 Trust vocabulary normalization

Instead of two unrelated five/three-value “degraded” ladders, use a common trust axis plus domain-specific disposition:

```text
TrustLevel = TRUSTWORTHY | DEGRADED | UNTRUSTED
```

Ledger integrity adds:

```text
RecoveryDisposition =
  NONE
  REPAIR_REQUIRED
  OPERATOR_DECISION_REQUIRED
  UNRECOVERABLE
```

Affected closure adds deterministic verification policy rather than additional trust synonyms.

---

# 6. Synthesized authority model

```text
PROJECT / REPOSITORY AUTHORITY
│
├─ tracked Git source + exact object identity
├─ project-native architecture/acceptance policy
│      OR explicitly adopted ProjectSibProfileV1
├─ existing protected capability / contract registry authority
│
├─ Finding domain authority
│    ├─ findings.ndjson
│    └─ findings-amendments.ndjson
│
├─ Implementation domain authority             [one new narrow RC7 authority]
│    └─ implementation ledger generations
│
└─ EHA domain authority
     └─ existing eha.ndjson evolved to V2

DERIVED / WORKFLOW OBJECTS
│
├─ AcceptanceProfileSnapshotV1
├─ EbcaClaimViewV1
├─ EhaRepairCaseV1
├─ LedgerRecoveryCaseV1
├─ RepairPacketV1
├─ RepairLearningRecordV1
├─ Development Authority Map
├─ context/graph projections
└─ renderer outputs

SHARED MECHANICS, NEVER SEMANTIC AUTHORITY
│
├─ digest/canonicalization primitives
├─ ledger framing/syntax/integrity primitives
├─ renderer descriptors
├─ Markdown generation helpers
└─ host prompt rendering helpers
```

One new durable authority enters RC7: the **Implementation Ledger**, and only for accepted-plan execution history.

RC7 must not introduce a generic claim authority, generic recovery authority, generic EHA authority, renderer authority, graph authority or host-execution authority.

---

# 7. Revised synthesized types

## 7.1 `ProjectSibProfileV1`

```text
schemaVersion
projectSibProfileId
version
digest
authorityMode: NATIVE_BOUND | ADOPTED_POLICY
repositoryIdentity
architectureGenerationId
authorityRefs[]
adjudicationRef?

discoveryCoverage {
  universeMethod
  scannedSources[]
  unavailableSources[]
  truncated
  discoveryCompleteness
  limitations[]
}

capabilityClasses[]
ownershipModel
contracts[]

sib0Policy
sib1Policy
sib2Policy

candidateSelectionPolicy
architectureReopenPolicy
repairPolicy
preservationPolicy

assumptions[]
limitations[]
```

There is no independently editable acceptance-policy twin.

## 7.2 `AcceptanceProfileSnapshotV1`

```text
schemaVersion
snapshotId
snapshotDigest
projectSibProfileRef
sourcePolicyRefs[]
compiledFromDigests[]

obligations[]
gates[]
environmentMatrix[]
materialToolRequirements[]
materialRuntimeRequirements[]
aggregationPolicy
notApplicablePolicy
completionPolicy
repairPolicyRef

compiledAt
compilerVersion
```

Authority status: immutable **derived acceptance snapshot**, not project policy authority.

Changing a policy/gate/environment requirement changes the snapshot digest and therefore changes the acceptance claim configuration.

## 7.3 `EbcaClaimViewV1`

```text
schemaVersion
viewId
ownerDomain
ownerRecordRef
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

No generic create/update/delete lifecycle exists for this type.

## 7.4 `EhaVerdictV2`

```text
schemaVersion: 2
eventId
campaignId
targetSha
sibLevel
projectSibProfileRef
acceptanceProfileSnapshotRef
claimView
result
runRefs[]
actualEnvironment[]
actualToolRuntimeIdentities[]
blockerFindingIds[]
repairCaseRefs[]
recordedAt
recordedHeadSha
```

The source acceptance subject is:

```text
exact source SHA + acceptance-profile snapshot digest
```

Environment/tool identities belong to the required supporting run evidence matrix. They are not collapsed into one fictional “single environment subject.”

## 7.5 `EhaRepairCaseV1`

```text
schemaVersion
repairCaseId
failedSubjectSha
campaignRef
acceptanceProfileSnapshotRef
failedSibLevel
failedObligationRef
failedClaimView
maturityImpact
rootCauseClassification
reproductionState
contractRefs[]
evidenceRefs[]
affectedCapabilityRefs[]
changeSurface
forbiddenSurface[]
closureTrust
assumptions[]
limitations[]
residualUncertainty[]
stopConditions[]
```

## 7.6 `LedgerRecoveryCaseV1`

```text
schemaVersion
recoveryCaseId
domain
sourceGenerationRef
sourceDigest
corruptionClassification[]
corruptRanges[]
trustLevel
recoverableFacts[]
unrecoverableFacts[]
proposedRecoveredGeneration
operatorDecisionRequired
limitations[]
```

## 7.7 `HostExecutionProfileV1`

```text
schemaVersion
hostProfileId
hostFamily
hostVersionConstraints
toolMappings
commandMappings
shellConventions
pathConventions
supportedAttachments
executionConstraints
```

This object resolves semantic execution instructions before Jinja rendering.

Jinja does not decide which tests/commands are required.

---

# 8. Deterministic closure-trust consequence

Use common trust levels with policy-defined deterministic consequences:

```text
TRUSTWORTHY
    -> validated narrow affected closure may select focused verification

DEGRADED
    -> mandatory conservative fallback gate set
       chosen by policy, never by model

UNTRUSTED
    -> full/wider policy-defined verification OR explicit STOP
       narrow closure alone is forbidden
```

`AcceptanceProfileSnapshotV1` / repair policy must contain the fallback rule.

If no deterministic degraded/untrusted fallback is defined for an operation requiring mutation, stop with:

```text
AFFECTED_CLOSURE_UNTRUSTED
```

or `OPERATOR_DECISION_REQUIRED` as appropriate.

---

# 9. `NOT_APPLICABLE` synthesis rule

`NOT_APPLICABLE` is allowed only for a specific obligation and requires:

```text
obligationRef
policy authority ref
rationale
declared applicability predicate
```

It MUST NOT substitute for:

- missing evidence;
- unavailable service;
- unavailable credential;
- failed runner;
- unsupported required environment;
- inconvenient platform;
- skipped required gate.

A whole SIB level is never made `NOT_APPLICABLE` merely to reach PASS.

---

# 10. Reduced RC7 implementation scope

## RC7 MUST

- one narrow Implementation Ledger authority;
- ledger integrity primitives + domain-owned recovery;
- ProjectSibProfile discovery/binding/adjudication;
- immutable AcceptanceProfileSnapshot compilation;
- existing EHA authority V2 schema evolution;
- non-binary result states;
- exact profile/source/run binding;
- EhaRepairCase / RepairPacket;
- deterministic auto-repair stopping;
- source rehydration;
- affected-closure trust/fallback;
- postcondition verification;
- regression witness handling;
- preservation proposal into existing contract authority;
- cross-ledger stable IDs;
- JSON structured representation;
- domain NDJSON where required by the authority/interchange contract;
- generated Markdown;
- Jinja host presentation over validated host execution data;
- existing Mermaid integration where already part of CodeSleuth product behavior;
- install/smoke/catalog/docs parity;
- deterministic adversarial fixtures + controlled live dogfood.

## RC7 SHOULD, only if bounded

- derived RepairLearningRecord;
- small read-only EBCA claim view/interface;
- one bounded legacy Markdown-import **proposal** path only if migration requires it.

## POST-RC7 / RESEARCH

- generic arbitrary-project Markdown↔NDJSON mapping framework;
- runtime-loadable renderer framework;
- JSONC/YAML/TOML/JSON-LD general renderer suite;
- DOT/GraphML/JSON Canvas general product surfaces;
- SARIF/JUnit/CSV integrations;
- Obsidian O1 product adapter beyond a research fixture;
- Obsidian import/plugin bridge;
- generic Negative Claims / forbidden inference;
- universal R0-R3 mutation policy;
- ROAP implementation;
- traceability-completeness auditor;
- long-context/grounding assurance suite;
- assurance-case/SACM implementation;
- SLSA/attestation/reproducible-build subsystems;
- Doris analytical plane implementation.

## REMOVE / PROHIBIT

- generic claim database;
- generic semantic super-ledger;
- generic recovery authority capable of switching arbitrary domain truth;
- parallel generic EHA store;
- independently editable acceptance-policy authority beside ProjectSibProfile/project-native policy;
- bidirectional Obsidian sync in RC7;
- generic workflow scheduler/runtime;
- CodeSleuth-owned primary coding/controller runtime.

---

# 11. Revised renderer boundary

RC7 should freeze the renderer **contract**, not a museum of formats.

Required implementation:

| Surface | RC7 synthesis |
| --- | --- |
| JSON | MUST |
| authoritative/domain NDJSON | MUST where that domain already uses/needs it |
| Markdown | MUST |
| Jinja host presentation | MUST |
| existing Mermaid | SHOULD / reuse existing |
| SVG | no new framework; existing bounded exporter only |
| Graphify | existing provider/projection boundary only |
| JSON Canvas | research/post-RC7 |
| Obsidian bundle | research/post-RC7 |
| all remaining interchange/ecosystem formats | post-RC7 unless a later explicit scope decision promotes one |

Renderer descriptors remain static/internal in RC7.

---

# 12. Revised Markdown boundary

RC7 normal path:

```text
authoritative domain state
        -> typed view
        -> Markdown AST/render
        -> generated Markdown
```

No generic arbitrary-project import framework is required for RC7.

If one legacy migration requires Markdown ingestion:

```text
specific known legacy Markdown
        -> parser
        -> migration-specific candidate records
        -> validation
        -> IMPORT PROPOSAL
        -> explicit domain adjudication/write API
```

The importer is scoped to the migration contract and cannot become a general upstream authority path.

---

# 13. Revised repair state machine

```text
FAILED ACCEPTANCE CLAIM
        |
        v
REPRODUCE / REHYDRATE
        |
        +--> cannot establish defect -> REPRODUCTION_INCONCLUSIVE
        |
        v
EhaRepairCaseV1
        |
        v
ROOT-CAUSE TRIANGULATION
        |
        +--> contradiction -> OPERATOR_DECISION_REQUIRED
        +--> architecture change -> ARCHITECTURE_REOPEN_REQUIRED
        +--> scope expansion -> SCOPE_EXPANSION_REQUIRED
        +--> live-only evidence -> LIVE_EVIDENCE_REQUIRED
        +--> evidence stale/corrupt -> EVIDENCE_UNTRUSTED
        |
        v
RepairPacketV1 + HostExecutionProfileV1
        |
        v
PRE-MUTATION VALIDATION
        |
        v
HOST MUTATION
        |
        v
POSTCONDITION OBSERVER
        |
        +--> invalid/no effective state -> HOST_POSTCONDITION_FAILED
        |
        v
FOCUSED OBLIGATION RECHECK
        |
        +--> deterministic no-progress/cycle/budget -> REPAIR_LOOP_STALLED
        |
        v
NEW EXACT SHA
        |
        v
FRESH EHA
```

A failed old claim remains historical evidence forever.

---

# 14. Adversarial additions from the synthesis

The final RC7 acceptance design should explicitly include these review-derived cases in addition to the thesis matrix:

1. independently edited acceptance snapshot contradicts source policy -> rejected as stale/invalid snapshot;
2. generic recovery primitive attempts to select EHA generation -> forbidden API/contract failure;
3. automatic repair enabled without `maxAutomatedAttempts` -> preflight STOP;
4. repeated same failure signature + unchanged obligation state -> `REPAIR_LOOP_STALLED`;
5. deterministic A->B->A repair state cycle -> `REPAIR_LOOP_STALLED`;
6. failure cannot be reproduced strongly enough -> `REPRODUCTION_INCONCLUSIVE`;
7. user accepts discovery limitation without creating/adopting project policy -> no SIB0 PASS;
8. explicit adopted architecture policy with incomplete earlier archaeology -> new policy may govern future SIB0, but archaeology is still recorded incomplete;
9. `NOT_APPLICABLE` without authority-backed obligation rationale -> validation failure;
10. Jinja template tries to omit a required verification command -> impossible because commands are resolved before template rendering;
11. `closureTrust=DEGRADED` -> deterministic conservative fallback, not model choice;
12. Claim-view persistence/lifecycle API appears -> contract failure;
13. learning record attempts to create a second preservation ledger -> contract failure;
14. `DAM.CONFIRMED` used as policy adoption evidence without adjudication/native authority -> rejected;
15. renderer A and renderer B agree while both omit a required domain field -> parity still FAIL against source object.

---

# 15. Logical synthesis summary

The thesis was directionally correct but left four choices too open:

```text
separate profiles
shared ledger repair
repair stall semantics
human SIB0 adjudication
```

The antithesis correctly showed that those open choices could be implemented as duplicate authorities or optimistic inference.

The synthesis keeps the useful separation while removing the ambiguity:

```text
one policy owner
+ immutable derived acceptance snapshot
+ shared structural ledger mechanics
+ domain-owned semantic recovery
+ bounded deterministic repair state machine
+ discovery completeness distinct from policy completeness
+ one new narrow implementation-history authority only
+ smaller renderer/import surface
```

Compact synthesized architecture:

> **Domain authorities stay explicit. Shared mechanics never choose truth. Project policy owns maturity semantics. Acceptance uses an immutable compiled snapshot. Repair authorization is deterministic and bounded. Recovery is domain-owned. Unknown evidence remains unknown. Presentation stays downstream.**

---

# 16. Disposition of the three dialectic artifacts

### Thesis

`RC7-CONSOLIDATED-DESIGN-PROPOSAL.md` remains frozen unchanged as the first consolidated proposal baseline.

### Antithesis

`reviews:docs/reviews/do-not-freeze-RC7.md` remains independent review evidence on its own branch/commit.

### Synthesis

This document is the current **design review candidate**. It is not yet final RC7 implementation authority.

If accepted by the owner/maintainer, the next design-authority step should be to create one final normative `RC7-CONSOLIDATED-DESIGN.md` from this synthesis, with explicit replacement/retirement status for the planning seeds/addenda as implementation instructions while retaining them as design provenance.

No runtime implementation should begin merely because this synthesis exists.
