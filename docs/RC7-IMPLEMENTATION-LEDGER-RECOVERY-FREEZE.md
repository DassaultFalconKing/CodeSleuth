# RC7 FF1 — Implementation Ledger + Recovery Authority Freeze

**Status:** NORMATIVE RC7 FINAL-FREEZE CONTRACT FOR W2 + W4 RECOVERY SEMANTICS  
**Session:** FF1 — Implementation Ledger + Recovery Authority Freeze  
**Mode:** DESIGN / CONTRACT FREEZE ONLY  
**Branch:** `docs/rc7-ff1-implementation-ledger-recovery-freeze`  
**Exact design base:** `af0c5dcd4054cb2eef35d7661125fc939b9e3263`  
**Current accepted runtime predecessor:** `6621c65b868d3e279ddcbd8dee182a95c6fb29f8`  
**Implementation:** explicitly out of scope for this session

This contract freezes the Implementation Ledger authority, plan and requirement identity, event schemas, exact-target derived state, recovery-generation lineage, and active-generation algorithm tightly enough that implementation does not invent semantic authority.

The compact rule is:

> **An accepted plan is bound by exact identity and an authority-backed requirement catalog; implementation history is append-only; current state is derived for one exact target; plan revision creates a new ledger identity; damaged history is recovered through immutable same-plan generations; generation selection remains Implementation-domain authority, while permission to perform an authority-changing selection is supplied by W10/FF2 rather than invented here.**

---

# 1. Freeze verdict and implementation frontier

FF1 freezes one deliberate new RC7 domain authority:

```text
Implementation Ledger
    owns: accepted-plan execution history
    does not own: project planning policy, source truth, Finding truth,
                  EHA/SIB verdicts, acceptance policy, repair permission,
                  or generic claims
```

The implementation frontier after FF1 is:

```text
W2  Implementation Ledger core
    -> IMPLEMENTABLE after this freeze is accepted

W4A Implementation recovery read/build/validate mechanics
    -> IMPLEMENTABLE after W2 + LedgerIntegrityCore

W4B authority-changing SELECT mutation
    -> SEMANTICS FROZEN HERE
    -> MUTATION AUTHORIZATION BLOCKED on FF2/W10 LedgerRecoveryCaseV1
```

FF1 does **not** authorize W6 EHA V2, W10 repair/recovery case permission schemas, W12 learning records, W13 claim views, W14 final renderer parity, W15 integrated context epistemics, or complete W16 lifecycle exposure.

No generic `LedgerIntegrityCore` operation may choose or mutate an authoritative Implementation generation.

---

# 2. Exact authority inputs

FF1 was produced from the accepted RC7 planning stream at:

```text
planning/design base:
af0c5dcd4054cb2eef35d7661125fc939b9e3263
```

The accepted RC6/SIB2 runtime predecessor consumed as executable-contract evidence is:

```text
SIB/runtime predecessor:
6621c65b868d3e279ddcbd8dee182a95c6fb29f8
```

Material runtime contracts include:

- `docs/DURABLE-EVIDENCE-STORE.md`;
- `docs/DEVELOPMENT-CONTINUATION-CONTRACT.md`;
- `docs/STABLE-INTEGRATION-BASELINE.md`;
- `docs/SIB0-CAPABILITY-INVENTORY.md`;
- `docs/PROTECTED-CAPABILITY-CONTRACTS.md`;
- `docs/RC6-IMPLEMENTATION-LEDGER.md`;
- `docs/EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md`.

Accepted RC7 inputs consumed by FF1:

| Input | Exact accepted source head | FF1 use |
| --- | --- | --- |
| MF1 Finding recovery | `c761e1ebacfebad5a4779da69d9d3a9d7a1d8a51` | recovery-generation and selection precedent |
| MF2 acceptance profile snapshot | `d751b03c52168d59a23a445652cf042aa0e0c239` | immutable acceptance-policy snapshot boundary |
| MF3 completeness | `b1e697e7cf8c9409538a20f9449b8ddd8780352e` | completeness stays outside Implementation authority |
| MF4 repair termination | `dc3191c11db669e416a3d86af69e7cfae95365af` | source-repair control stays separate from ledger recovery |
| MF5 RepairPacket / host profile | `c9fa42dc032a37509534395f577d7069ae75eb56` | packets/presentation do not grant authority |

The normative micro-freeze integration input is `docs/RC7-MICRO-FREEZE-CROSS-CONTRACT-ADJUDICATION.md` on the design base. FF1 preserves its decisions that active-generation selection remains domain-owned, acceptance snapshot identity remains distinct from completeness, MF4 repair control does not become ledger-recovery authority, and MF5 packets/presentation do not grant mutation authority.

Additional provenance inputs:

- synthesis blob `a3556ca3bd84546835a3ff66847cfb03da54fc7b`;
- pinned antithesis commit `be5d158880f649ecb568d9a505c694e87bd76e0e`;
- feature-plan seed blob `ddac1c4a34b0c57f7c6ff668cc7e3d99a56f03c5`.

Where this document explicitly decides W2/W4 semantics, this FF1 contract is the implementation authority for that scope.

---

# 3. Authority model and SIB0 architectural disposition

FF1 preserves separate domain owners:

```text
PROJECT / REPOSITORY AUTHORITY
│
├─ tracked Git source + exact Git object identity
├─ project-native planning / architecture / acceptance authority
├─ Finding domain authority
├─ Implementation domain authority
└─ EHA domain authority

DERIVED / NON-AUTHORITATIVE
│
├─ Markdown implementation ledger
├─ reports / Mermaid / graph / search views
├─ Development Authority Map navigation
├─ AcceptanceProfileSnapshotV1
├─ completeness assessments
├─ RepairPacketV1 / host presentation
└─ LLM context

SHARED MECHANICS ONLY
└─ LedgerIntegrityCore
     exact bytes / digests / NDJSON framing / JSON / schema hooks /
     duplicate primitives / reference lexical checks / generic DAG checks
```

## 3.1 Implementation authority ownership

The Implementation Ledger owns durable statements that implementation work, implementation observations, implementation-local verification, blocker transitions, and authority-backed defer/resume decisions were recorded for one exact accepted plan.

It may answer:

- which exact accepted plan is bound;
- which exact requirement catalog belongs to that plan;
- which implementation events were durably recorded;
- what current implementation and local-verification state is supportable for one exact target SHA;
- which blockers are open;
- whether a requirement is ACTIVE or DEFERRED according to upstream authority decisions;
- which recovery generation is selected by the Implementation-domain selection history.

It MUST NOT decide or persist as its own truth:

- which plan is current project planning authority;
- whether a plan is accepted merely because it was once bound;
- Finding lifecycle;
- EHA/SIB verdicts;
- acceptance-profile policy;
- completeness claims;
- source-mutation permission;
- automatic repair-loop policy;
- ledger-recovery permission;
- generic EBCA claim truth;
- graph/report/Markdown truth.

## 3.2 RC7 SIB0 disposition

The accepted predecessor SIB0 inventory defines `CC-STATE` as the existing persistent-review-state capability and explicitly requires a replacement SIB0 lineage when a fundamental ownership/authority boundary is added or redefined.

FF1 deliberately adds a separate durable **Implementation authority** under `.opencode/state/`. That is not silently classified as ordinary RC6 feature population.

The RC7 architectural disposition is therefore frozen as:

```text
RC7_SIB0_STATUS:
REOPENED

CAPABILITY_CLASS_COUNT:
UNCHANGED

AFFECTED_CLASS:
CC-STATE

RC7_REDEFINITION:
persistent-review-state
    -> persistent-evidence-and-implementation-state
       with separate Finding / Implementation / EHA domain authorities
       and shared structural mechanics only

CONSEQUENCE:
RC6/SIB2 remains the accepted predecessor,
but its SIB0 acceptance does not transfer to the redefined RC7 CC-STATE.
RC7 must establish a replacement exact-head SIB0 before claiming RC7 SIB1/SIB2.
```

W2/W4 implementation may proceed on the RC7 integration stream from the accepted predecessor, but the resulting architecture is not allowed to inherit predecessor SIB0 acceptance by ancestry.

This section is the explicit SIB0 adjudication that prevents the new Implementation authority from being smuggled in as if no architectural boundary changed.

---

# 4. Physical V1 layout

V1 uses one worktree-local Implementation-domain root:

```text
.opencode/state/implementation-ledgers/
    <planId>/
        events.ndjson
        recovery/
            selections.ndjson
            generations/
                <generationId>/
                    generation.json
                    events.ndjson
```

Rules:

1. `<planId>` is path-safe by construction.
2. Root `events.ndjson` is the baseline-generation stream.
3. Absence of `recovery/` means the deterministic baseline generation is active.
4. If `recovery/` exists, `selections.ndjson` is mandatory.
5. A generation directory is a non-authoritative immutable candidate until selected.
6. Temporary construction is non-authoritative and publishes by same-filesystem atomic rename only after validation.
7. No `latest.txt`, timestamp, directory sort, report, model choice, or generation creation selects authority.
8. Published V1 generations and selection records are retained; V1 performs no authoritative-history garbage collection.
9. Upstream project/planning authority still selects the active project plan. This root selects only a generation inside an already-identified plan ledger.

---

# 5. Canonical primitives

## 5.1 Canonical JSON

FF1-owned semantic identities use RFC 8785 JCS:

```text
canonicalBytes = UTF8(JCS(value))
digestHex      = lowercaseHex(SHA256(canonicalBytes))
```

Before hashing:

- duplicate JSON object keys are invalid;
- strings defined as Unicode text are NFC;
- set-valued arrays are duplicate-free and sorted by canonical JSON bytes;
- ordered arrays preserve order;
- timestamps, actor display names, tool versions, host paths, and explanatory prose are excluded unless a schema explicitly includes them.

## 5.2 Common scalar forms

```text
GitShaV1         = exactly 40 lowercase hexadecimal characters
Sha256V1         = exactly 64 lowercase hexadecimal characters
MachineIdV1      = ASCII regex [A-Za-z0-9][A-Za-z0-9._:/-]{0,127}
ReasonCodeV1     = ASCII regex [A-Z][A-Z0-9_]{0,63}
RepoPathV1       = normalized repository-root-relative POSIX path;
                   no absolute path, no empty segment, no '.' or '..'
EventIdV1        = "ie1-" + 64 lowercase hex
RequirementIdV1  = "ireq1-" + 64 lowercase hex
SelectionIdV1    = "igs1-" + 64 lowercase hex
```

## 5.3 Stable references and material-reference binding

FF1 reuses MF5's structural shape:

```text
StableRefV1 {
  domain
  id
  digestSha256?
}
```

The owning domain owns `id`. FF1 never normalizes or regenerates another domain's ID.

For FF1, a reference is **material** when it supports an implementation/local-verification observation or authorizes a blocker/defer/resume/correction/selection action.

A material reference is admissible only when one of these is true:

```text
A. digestSha256 is present and rehydrated bytes/semantic object match it exactly;

OR

B. the owning-domain contract explicitly declares the referenced id immutable
   and content-addressed, and the resolver verifies that invariant.
```

If neither is true, the material reference is unresolved for material use.

Deterministic consequence:

```text
observation event + unresolvable material ref
    -> effective observation is INCONCLUSIVE/UNAVAILABLE by the exact axis rules
       in section 9; the bytes remain historical evidence

control/lifecycle event + unresolvable material authority ref
    -> event is semantically invalid
    -> active Implementation material is UNTRUSTED

selection record + unresolvable permission/material ref
    -> selection history is UNTRUSTED
```

Navigation-only references may omit a digest, but they cannot support `IMPLEMENTED`, `PASS`, `NOT_IMPLEMENTED`, `NOT_APPLICABLE`, lifecycle control, or recovery selection.

---

# 6. Deterministic repository, plan, and requirement identity

## 6.1 `RepositoryIdentityV1`

FF1 does not use a host path, branch name, remote nickname, or report metadata as repository identity.

Repository identity is derived from the Git history bound by the accepted plan's `bindingSha`:

```text
rootSet = sorted ascending full GitShaV1 values for every commit
          reachable from bindingSha that has zero parents

repositoryIdentityBytes = UTF8(
  "GitRepositoryIdentityV1\n" +
  concat("root=" + sha + "\n" for sha in rootSet)
)

repositoryId = "gitrepo1-" + SHA256_HEX(repositoryIdentityBytes)
```

Requirements:

- `rootSet` MUST be non-empty;
- object traversal is over the exact local Git object graph for `bindingSha`;
- shallow/incomplete history that cannot prove the complete root set fails with `REPOSITORY_IDENTITY_UNRESOLVED`;
- adding unrelated history may deliberately change repository identity for a later binding; ordinary descendants with the same reachable roots retain the same repository identity.

## 6.2 `ImplementationRequirementCatalogV1`

The Implementation Ledger does not decide which prose is a material requirement.

A bound plan requires an authority-backed catalog:

```text
ImplementationRequirementCatalogV1 {
  schemaVersion: "ImplementationRequirementCatalogV1"
  planPath: RepoPathV1
  planBlobSha: GitShaV1
  requirements: RequirementCatalogEntryV1[]
}

RequirementCatalogEntryV1 {
  localRequirementId: PlanLocalRequirementIdV1
  sourceLocator: SourceLocatorV1
  requiredLocalOracleIds: MachineIdV1[]
}

SourceLocatorV1 {
  path: RepoPathV1
  blobSha: GitShaV1
  startLine: positive integer
  endLine: integer >= startLine
  exactBytesSha256: Sha256V1
}
```

Catalog rules:

1. `requirements[]` is non-empty and sorted by `localRequirementId`.
2. `localRequirementId` values are unique.
3. Every `sourceLocator.path == planPath` and every `sourceLocator.blobSha == planBlobSha`.
4. Every bounded source range includes the explicit local ID plus the material requirement statement and recomputes `exactBytesSha256` from exact file bytes with no normalization.
5. `requiredLocalOracleIds[]` is a set, duplicate-free and canonically sorted.
6. These oracle IDs are implementation-local verification oracles only; EHA/SIB acceptance obligations remain outside this catalog.
7. The catalog is referenced by a **material**, digest-bound `StableRefV1(domain = PROJECT_POLICY)`.
8. The owning `planAuthorityRef` explicitly adopts this exact catalog as the complete implementation requirement universe for the bound scope.
9. A model, heading scanner, ordinal position, TODO parser, similarity search, or Development Authority Map confidence value MUST NOT create or extend the catalog.

If the project has not supplied/adopted this catalog, binding stops with `REQUIREMENT_CATALOG_UNRESOLVED`.

## 6.3 `PlanIdentityV1`

```text
PlanIdentityV1 {
  schemaVersion: "PlanIdentityV1"
  planId: "iplan1-" + 64 lowercase hex

  repositoryId
  bindingSha: GitShaV1
  planPath: RepoPathV1
  planBlobSha: GitShaV1
  planAuthorityRef: StableRefV1(domain = PROJECT_POLICY)
  requirementCatalogRef: StableRefV1(domain = PROJECT_POLICY)
}
```

At bind time:

- `repositoryId` recomputes from `bindingSha` by section 6.1;
- `planPath` at `bindingSha` resolves exactly to `planBlobSha`;
- `planAuthorityRef` is material/digest-bound and resolves to explicit project-owned authority establishing this exact `bindingSha` + `planPath` + `planBlobSha` as accepted/frozen/canonical for implementation;
- the same authority explicitly adopts `requirementCatalogRef` as the complete implementation requirement catalog for this bound scope;
- the catalog's `planPath` and `planBlobSha` match the plan identity exactly.

The plan identity preimage is exactly:

```json
{
  "bindingSha": "<GitShaV1>",
  "planAuthorityRef": <StableRefV1>,
  "planBlobSha": "<GitShaV1>",
  "planPath": "<RepoPathV1>",
  "repositoryId": "<repositoryId>",
  "requirementCatalogRef": <StableRefV1>,
  "schemaVersion": "PlanIdentityV1"
}
```

```text
planId = "iplan1-" + SHA256_HEX(JCS(identityPreimage))
```

## 6.4 Plan revision

Any change to an identity input creates a new plan identity and new ledger root:

```text
changed bindingSha / plan bytes / path / authority / catalog / repository identity
    -> new PlanIdentityV1
    -> new planId
    -> new implementation-ledger root
```

A recovery generation MUST preserve the exact same plan identity and catalog. Plan revision is never recovery.

## 6.5 `RequirementIdV1`

```text
PlanLocalRequirementIdV1
    = exact case-sensitive plan-owned identifier
    = Unicode NFC
    = 1..128 UTF-8 bytes
    = no leading/trailing Unicode whitespace
    = no C0/C1 controls
```

```text
RequirementIdentityPreimageV1 {
  schemaVersion: "ImplementationRequirementIdentityV1"
  planId
  localRequirementId
}

requirementId = "ireq1-" + SHA256_HEX(JCS(RequirementIdentityPreimageV1))
```

The `PLAN_BOUND` event retains the validated catalog bindings and deterministic requirement IDs. Old-plan evidence never silently attaches to a revised plan.

---

# 7. `ImplementationEventV1` exact envelope

Every authoritative event is one canonical JSON object followed by one LF byte.

```text
ImplementationEventV1 {
  schemaVersion: 1
  kind: "ImplementationEventV1"
  eventId: EventIdV1

  planId
  eventType
  subjectSha: GitShaV1
  requirementIds: RequirementIdV1[]
  evidenceRefs: StableRefV1[]
  payload: exact event-type payload

  provenance {
    recordedAt
    actorRef?
    toolId: MachineIdV1
    toolVersion?
  }
}
```

`requirementIds` and `evidenceRefs` are set-valued and canonically sorted. `provenance` and `eventId` are excluded from the semantic preimage.

```text
eventId = "ie1-" + SHA256_HEX(JCS(eventSemanticPreimage))
```

Physical append order is authoritative event order. `recordedAt` never reorders history.

The V1 event-type set is closed:

```text
PLAN_BOUND
WORK_STEP_RECORDED
IMPLEMENTATION_EVIDENCE_RECORDED
VERIFICATION_RECORDED
BLOCKER_RECORDED
BLOCKER_RESOLVED
DEFER_DECISION_RECORDED
RESUME_DECISION_RECORDED
EVENT_INVALIDATED
EVENT_REINSTATED
```

Unknown type/schema fails closed.

---

# 8. Exact V1 event payload schemas

## 8.1 `PLAN_BOUND`

Envelope rules:

- exactly first event;
- exactly once;
- `subjectSha == PlanIdentityV1.bindingSha`;
- `requirementIds == []`;
- `evidenceRefs` is exactly the canonical set `{planAuthorityRef, requirementCatalogRef}`.

Payload:

```text
PlanBoundV1 {
  planIdentity: PlanIdentityV1
  requirements: BoundRequirementV1[]
  predecessorPlanRefs: StableRefV1[]
}

BoundRequirementV1 {
  localRequirementId
  requirementId
  sourceLocator: SourceLocatorV1
  requiredLocalOracleIds: MachineIdV1[]
}
```

`requirements[]` MUST exactly equal the adopted catalog after deterministic requirement-ID derivation. `predecessorPlanRefs` are navigation only and transfer no status.

## 8.2 `WORK_STEP_RECORDED`

```text
WorkStepRecordedV1 {
  workUnitId: MachineIdV1
  operationId: MachineIdV1
  changedSurfaces: ChangedSurfaceV1[]
}

ChangedSurfaceV1 {
  path: RepoPathV1
  changeKind: ADDED | MODIFIED | DELETED | RENAMED | TYPE_CHANGED
  beforeBlobSha?: GitShaV1
  afterBlobSha?: GitShaV1
  previousPath?: RepoPathV1
}
```

Rules:

- `requirementIds` non-empty;
- `evidenceRefs` non-empty and material;
- `changedSurfaces` non-empty, duplicate-free, sorted by `(path, changeKind, previousPath-or-empty)`;
- `ADDED` requires `afterBlobSha`, forbids `beforeBlobSha` and `previousPath`;
- `DELETED` requires `beforeBlobSha`, forbids `afterBlobSha` and `previousPath`;
- `MODIFIED`/`TYPE_CHANGED` require distinct before/after blob SHA and forbid `previousPath`;
- `RENAMED` requires `previousPath != path`, before blob SHA, and after blob SHA;
- changed files alone establish only that bounded work occurred, never `IMPLEMENTED`.

## 8.3 `IMPLEMENTATION_EVIDENCE_RECORDED`

```text
ImplementationEvidenceRecordedV1 {
  observationKind: "REQUIREMENT_IMPLEMENTATION"
  implementationState: PARTIAL | IMPLEMENTED | NOT_IMPLEMENTED | INCONCLUSIVE
}
```

Rules:

- exactly one requirement ID;
- material evidence refs non-empty;
- every non-INCONCLUSIVE observation requires all material refs to resolve exactly;
- if any material ref cannot resolve, effective current `workState = INCONCLUSIVE` with limitation `MATERIAL_EVIDENCE_UNAVAILABLE`;
- if a ref resolves but its digest/content-addressed identity conflicts, effective current `workState = INCONCLUSIVE` with limitation `MATERIAL_EVIDENCE_CONFLICT`;
- this is implementation-domain state, not acceptance.

## 8.4 `VERIFICATION_RECORDED / LOCAL_CHECK`

```text
LocalVerificationV1 {
  verificationKind: "LOCAL_CHECK"
  oracleId: MachineIdV1
  result: PASS | FAIL | INCONCLUSIVE | UNAVAILABLE | NOT_APPLICABLE
  notApplicableRationaleRef?: StableRefV1(domain = PROJECT_POLICY)
}
```

Rules:

- exactly one requirement ID;
- material run/evidence refs non-empty;
- `oracleId` must occur in the bound requirement's `requiredLocalOracleIds`, unless retained as non-required historical evidence; only required-oracle events participate in the required aggregate;
- `NOT_APPLICABLE` requires material `notApplicableRationaleRef` and exact authority-backed waiver/rationale;
- `notApplicableRationaleRef` is forbidden for other results;
- event is exact-target bound by `subjectSha`;
- unresolvable material run/evidence ref yields effective oracle result `UNAVAILABLE`;
- resolved material ref with digest/content identity conflict yields effective oracle result `INCONCLUSIVE`.

## 8.5 `VERIFICATION_RECORDED / EHA_REFERENCE`

```text
EhaVerificationReferenceV1 {
  verificationKind: "EHA_REFERENCE"
  ehaEventRef: StableRefV1(domain = EHA)
}
```

Rules:

- requirement IDs may be empty or non-empty according to the referenced EHA scope;
- `ehaEventRef` must be material/immutable for a trustworthy display;
- no copied EHA verdict field is permitted;
- EHA verdict is rehydrated from EHA authority at read time.

## 8.6 `BLOCKER_RECORDED`

```text
BlockerRecordedV1 {
  blockerScope: PLAN | REQUIREMENT
  reasonCode: ReasonCodeV1
}
```

Rules:

- PLAN scope requires zero requirement IDs;
- REQUIREMENT scope requires exactly one requirement ID;
- material evidence/authority refs non-empty;
- blocker identity is this event ID;
- an unresolvable material authority/evidence ref makes the active Implementation history untrusted rather than silently dropping the blocker.

## 8.7 `BLOCKER_RESOLVED`

```text
BlockerResolvedV1 {
  blockerEventId: EventIdV1
  resolutionCode: ReasonCodeV1
}
```

Rules:

- material resolution evidence refs non-empty;
- referenced blocker must exist and be open;
- `requirementIds` must exactly match the referenced blocker scope;
- `subjectSha` is the exact target where resolution is evidenced;
- double resolve is illegal; recurrence creates a new blocker event;
- unresolved material resolution authority/evidence makes the active history untrusted.

## 8.8 `DEFER_DECISION_RECORDED`

```text
DeferDecisionRecordedV1 {
  decisionAuthorityRef: StableRefV1(domain = PROJECT_POLICY)
  reasonCode: ReasonCodeV1
}
```

Rules:

- exactly one requirement ID;
- `decisionAuthorityRef` is material;
- referenced authority owns the decision;
- deferring an already deferred requirement is illegal;
- unresolved authority ref makes active history untrusted.

## 8.9 `RESUME_DECISION_RECORDED`

```text
ResumeDecisionRecordedV1 {
  deferEventId: EventIdV1
  decisionAuthorityRef: StableRefV1(domain = PROJECT_POLICY)
  reasonCode: ReasonCodeV1
}
```

Rules:

- exactly one requirement ID;
- `deferEventId` references the currently effective defer event for that requirement;
- `decisionAuthorityRef` is material;
- resume while not deferred is illegal;
- unresolved authority ref makes active history untrusted.

## 8.10 `EVENT_INVALIDATED`

```text
EventInvalidatedV1 {
  targetEventId: EventIdV1
  operatorDecisionRef: StableRefV1(domain = PROJECT_POLICY)
  reasonCode: ReasonCodeV1
}
```

Rules:

- envelope `evidenceRefs` contains material correction evidence;
- target class is `WORK_STEP_RECORDED`, `IMPLEMENTATION_EVIDENCE_RECORDED`, or `VERIFICATION_RECORDED`;
- `subjectSha` and `requirementIds` exactly match the target event;
- target must currently be VALID;
- target becomes INVALIDATED for derivation but historical bytes remain unchanged;
- unresolved decision/evidence material ref makes active history untrusted.

## 8.11 `EVENT_REINSTATED`

```text
EventReinstatedV1 {
  targetEventId: EventIdV1
  operatorDecisionRef: StableRefV1(domain = PROJECT_POLICY)
  reasonCode: ReasonCodeV1
}
```

Rules:

- envelope `evidenceRefs` contains material re-establishing evidence;
- same target classes as invalidation;
- `subjectSha` and `requirementIds` exactly match the target event;
- target must currently be INVALIDATED;
- target becomes VALID again;
- unresolved decision/evidence material ref makes active history untrusted.

Correction lifecycle is exactly:

```text
VALID --EVENT_INVALIDATED--> INVALIDATED
INVALIDATED --EVENT_REINSTATED--> VALID
```

Correction-control events themselves are immutable.

---

# 9. Deterministic domain lifecycle and exact-target read model

## 9.1 Validation order

Active material is interpreted in this order:

1. structural validation through `LedgerIntegrityCore`;
2. exact `PLAN_BOUND` / repository / plan / catalog validation;
3. event-ID validation;
4. requirement/reference/cardinality validation;
5. event-disposition lifecycle;
6. blocker lifecycle;
7. defer/resume lifecycle;
8. material-reference resolution and digest/content-addressed validation;
9. exact-target per-requirement derivation.

Structurally readable does not imply semantically trusted.

## 9.2 Exact-target rule

Every current-state query names one full exact `targetSha`.

Only valid events whose `subjectSha == targetSha` may establish current implementation or local-verification observations for that target.

Ancestor, sibling, tree-equivalent, rebased, cherry-picked, or otherwise different SHAs remain historical context only. If no same-SHA evidence exists for an axis, that axis is `UNESTABLISHED`/`UNAVAILABLE` as defined below, never inherited success or failure.

## 9.3 Requirement read model

```text
ImplementationRequirementStateV1 {
  planId
  requirementId
  targetSha

  workState:
    UNESTABLISHED | IN_PROGRESS | PARTIAL |
    IMPLEMENTED | NOT_IMPLEMENTED | INCONCLUSIVE

  localVerificationByOracle: LocalOracleStateV1[]
  localVerificationResult:
    UNESTABLISHED | PASS | FAIL | INCONCLUSIVE |
    UNAVAILABLE | NOT_APPLICABLE

  ehaRefs: StableRefV1[]

  disposition: ACTIVE | DEFERRED
  openBlockerEventIds: EventIdV1[]

  trustLevel: TRUSTWORTHY | DEGRADED | UNTRUSTED
  limitations: ReasonCodeV1[]
}

LocalOracleStateV1 {
  oracleId: MachineIdV1
  result: PASS | FAIL | INCONCLUSIVE | UNAVAILABLE | NOT_APPLICABLE
  sourceEventId: EventIdV1
}
```

### Work-state derivation

For the exact target after validity filtering:

1. take the last valid `IMPLEMENTATION_EVIDENCE_RECORDED` for the requirement;
2. if it exists and every material ref resolves exactly, use its declared state;
3. if it exists and any material ref is unavailable or conflicts, `workState = INCONCLUSIVE` with the exact limitation from section 8.3;
4. otherwise, if any valid `WORK_STEP_RECORDED` exists, `workState = IN_PROGRESS`;
5. otherwise `UNESTABLISHED`.

### Per-oracle verification derivation

For every `requiredLocalOracleId` in the bound catalog:

1. select only valid same-target `LOCAL_CHECK` events with that exact oracle ID;
2. the last such event in append order determines that oracle's recorded result;
3. if none exists, effective result is `UNAVAILABLE`;
4. if material run/evidence cannot resolve, effective result is `UNAVAILABLE`;
5. if material ref resolves with digest/content identity conflict, effective result is `INCONCLUSIVE`;
6. otherwise use the recorded result.

Different oracle IDs **never overwrite one another**.

### Required aggregate local-verification result

Let `R` be the exact bound `requiredLocalOracleIds` set.

```text
if R is empty:
    localVerificationResult = NOT_APPLICABLE
else if any required oracle == FAIL:
    localVerificationResult = FAIL
else if any required oracle == INCONCLUSIVE:
    localVerificationResult = INCONCLUSIVE
else if any required oracle == UNAVAILABLE:
    localVerificationResult = UNAVAILABLE
else if all required oracles == NOT_APPLICABLE:
    localVerificationResult = NOT_APPLICABLE
else if every required oracle is PASS or authority-backed NOT_APPLICABLE
        and at least one required oracle == PASS:
    localVerificationResult = PASS
else:
    localVerificationResult = UNESTABLISHED
```

A later PASS from oracle B can never erase FAIL from required oracle A.

`EHA_REFERENCE` events populate only `ehaRefs`; they never become local PASS/FAIL.

### Blocker and defer derivation

Open blockers are blocker-record events without legal matching resolution events. Blocker state is orthogonal to work/verification.

`ACTIVE`/`DEFERRED` follows the legal authority-backed defer/resume sequence. Defer does not mean NOT_IMPLEMENTED; resume does not establish implementation.

## 9.4 No aggregate acceptance authority

The Implementation Ledger MUST NOT persist or derive authoritative:

```text
SIB0 PASS
SIB1 PASS
SIB2 PASS
releaseAccepted
acceptance PASS
plan done=true
```

Acceptance remains owned by the acceptance/EHA authority.

---

# 10. Ordinary append/write contract

Implementation history may be written only through the Implementation-domain API.

A conforming writer MUST:

1. re-resolve current project plan authority;
2. re-resolve the exact bound requirement catalog;
3. resolve the Implementation-domain active generation;
4. fail closed on ambiguous/untrusted selection or active material;
5. serialize writes with an exclusive domain lock or compare-and-append equivalent;
6. verify expected active generation ID, exact current byte length, and exact stream digest;
7. validate the proposed event against the complete V1 schema and current legal lifecycle;
8. append exactly one canonical JSON record plus one LF;
9. never rewrite/truncate/reorder/compact prior authoritative bytes;
10. re-read and revalidate before reporting successful mutation.

Concurrent change invalidates the stale write precondition. The writer retries only from freshly resolved state.

After a recovery successor is selected, ordinary writes target only the selected generation; predecessors are permanently write-fenced.

If upstream planning authority no longer establishes this exact plan as active implementation scope, ordinary new work/evidence writes fail closed. Historical reads remain allowed.

---

# 11. Implementation recovery generations

Recovery is domain-owned W4 behavior for **one fixed PlanIdentityV1 and fixed requirement catalog**. It repairs trustworthy representation; it does not revise the plan, source, or acceptance outcome.

## 11.1 Baseline generation

```text
baselineGenerationId =
  "igb1-" + SHA256_HEX(UTF8(
    "ImplementationBaselineGenerationV1\n" +
    "planId=" + planId + "\n"
  ))
```

The baseline ID is lineage-root identity, not stream-content digest.

## 11.2 Exact snapshots

```text
ImplementationStreamSnapshotV1 {
  byteLength: non-negative integer
  sha256: Sha256V1
}
```

Digest is over exact bytes with no normalization.

## 11.3 Allowed V1 safe-reframe operation schema

Allowed corruption/action mapping is exactly:

```text
MISSING_TERMINAL_LF          -> APPEND_TERMINAL_LF
EMPTY_RECORD                 -> OMIT_EMPTY_RECORD_SEPARATOR
INCOMPLETE_TERMINAL_FRAGMENT -> OMIT_INCOMPLETE_TERMINAL_FRAGMENT
```

Exact transform union:

```text
ImplementationRecoveryTransformV1 =
  AppendTerminalLfV1 {
    action: "APPEND_TERMINAL_LF"
    startByte: non-negative integer
    endByteExclusive: non-negative integer
  }

  | OmitSourceRangeV1 {
    action: "OMIT_EMPTY_RECORD_SEPARATOR" | "OMIT_INCOMPLETE_TERMINAL_FRAGMENT"
    startByte: non-negative integer
    endByteExclusive: integer > startByte
    rawSha256: Sha256V1
  }

ImplementationRecoveryOperationV1 {
  schemaVersion: 1
  operationKind: "SAFE_REFRAME_V1"
  transforms: ImplementationRecoveryTransformV1[]
}
```

Transform rules:

1. every offset is against the immutable **sourceSnapshot bytes**, never a progressively rewritten buffer;
2. `transforms[]` is non-empty, duplicate-free, and sorted by `(startByte, endByteExclusive, action)`;
3. source ranges of omit transforms MUST NOT overlap;
4. `APPEND_TERMINAL_LF` requires `startByte == endByteExclusive == sourceSnapshot.byteLength`, appears at most once, and carries no `rawSha256`;
5. `OMIT_EMPTY_RECORD_SEPARATOR` requires exactly one source byte (`endByteExclusive == startByte + 1`), that byte is `0x0A`, and `rawSha256` matches it;
6. `OMIT_INCOMPLETE_TERMINAL_FRAGMENT` requires `endByteExclusive == sourceSnapshot.byteLength`, the source range is non-empty/non-LF-terminated, the exact range does not parse as one complete JSON event, and `rawSha256` matches it;
7. replay is one deterministic source-coordinate pass: copy every non-omitted source byte in original order, then append one LF iff the APPEND transform exists;
8. transform combinations that would overlap or contradict are invalid.

Operation identity is exact:

```text
operationDigest = SHA256_HEX(JCS(ImplementationRecoveryOperationV1))
```

`APPEND_TERMINAL_LF` is allowed only when the terminal bytes form one complete domain-valid event and the sole terminal defect is missing LF.

V1 MUST NOT:

- alter/omit a complete LF-terminated non-empty record;
- drop a complete unknown-schema record;
- deduplicate a duplicate event ID;
- delete an illegal lifecycle transition;
- rewrite plan/requirement/subject/evidence/result identity;
- reorder complete events;
- transfer events to a revised plan;
- manufacture a missing event from prose/logs/timestamps/likely intent.

Defects requiring those operations stop with operator/unrecoverable diagnostics and produce no selectable hiding generation.

## 11.4 Torn terminal semantic-loss rule

Any selected generation using `OMIT_INCOMPLETE_TERMINAL_FRAGMENT` records:

```text
semanticLossRisk = UNKNOWN_TERMINAL_EVENT
```

V1 does **not** attempt partial-JSON requirement attribution.

The consequence is deterministically **plan-wide**:

- generation/read trust remains `DEGRADED` as permanent recovery provenance;
- pre-recovery current positive `IMPLEMENTED` and local PASS values are historical prefix evidence only;
- a requirement/axis may regain a positive current value only after a post-selection same-target evidence event re-establishes that exact axis;
- re-observation may restore an axis result but does not erase the generation-level `UNKNOWN_TERMINAL_EVENT` limitation;
- a model may not guess which requirement the fragment probably concerned.

---

# 12. `ImplementationRecoveryGenerationV1`

```text
ImplementationRecoveryGenerationV1 {
  schemaVersion: 1
  kind: "ImplementationRecoveryGenerationV1"
  domain: "implementation"

  planId
  generationId
  sourceGenerationId
  predecessorGenerationId
  sourceSnapshot: ImplementationStreamSnapshotV1

  recovery {
    reasonCodes: ReasonCodeV1[]
    corruption: ImplementationRecoveryCorruptionV1[]
    reasonDigest: Sha256V1
    operation: ImplementationRecoveryOperationV1
    operationDigest: Sha256V1
    semanticLossRisk: NONE | UNKNOWN_TERMINAL_EVENT
  }

  recoveredPrefix: ImplementationStreamSnapshotV1

  provenance {
    recordedAt
    toolId: MachineIdV1
    toolVersion?
    actorRef?
  }
}

ImplementationRecoveryCorruptionV1 {
  code: MISSING_TERMINAL_LF | EMPTY_RECORD | INCOMPLETE_TERMINAL_FRAGMENT
  startByte: non-negative integer
  endByteExclusive: integer >= startByte
  rawSha256?: Sha256V1
}
```

Corruption descriptor rules:

- descriptors are duplicate-free and sorted by `(startByte, endByteExclusive, code, rawSha256-or-empty)`;
- `reasonCodes` is exactly the unique sorted set of `corruption[].code`;
- `MISSING_TERMINAL_LF` uses an empty EOF range and omits `rawSha256`;
- `EMPTY_RECORD` binds the exact redundant LF range and digest;
- `INCOMPLETE_TERMINAL_FRAGMENT` binds the exact terminal fragment range and digest.

Reason identity is exact:

```text
reasonDigest = SHA256_HEX(JCS({
  "schemaVersion": "ImplementationRecoveryReasonSetV1",
  "corruption": <canonical corruption array>
}))
```

For V1:

```text
sourceGenerationId == predecessorGenerationId
```

Generation identity bytes are exactly:

```text
ImplementationRecoveryGenerationV1\n
planId=<planId>\n
sourceGenerationId=<sourceGenerationId>\n
predecessorGenerationId=<predecessorGenerationId>\n
sourceSnapshotSha256=<sourceSnapshot.sha256>\n
sourceSnapshotByteLength=<sourceSnapshot.byteLength>\n
reasonDigest=<reasonDigest>\n
operationDigest=<operationDigest>\n
semanticLossRisk=<semanticLossRisk>\n
recoveredContentSha256=<recoveredPrefix.sha256>\n
recoveredContentByteLength=<recoveredPrefix.byteLength>\n
```

```text
generationId = "irg1-" + SHA256_HEX(UTF8(identityBytes))
```

Timestamp, actor/tool labels, host paths, branch names, prose, and directory creation order are excluded.

Before selection, candidate bytes must exactly equal `recoveredPrefix`. After selection, the prefix is immutable and ordinary valid events may append. A future recovery snapshots the complete then-current selected generation.

---

# 13. Generation-selection authority and W10 permission boundary

Creation is never selection. No generation manifest has `active: true`.

Selection history lives at:

```text
recovery/selections.ndjson
```

## 13.1 Exact selection schema

```text
ImplementationGenerationSelectionV1 =
  BaselineSelectionV1 {
    schemaVersion: 1
    kind: "BASELINE"
    selectionId: SelectionIdV1
    planId
    selectedGenerationId: <baselineGenerationId>
    supersedesSelectionIds: []
    recordedAt
    actorRef
    toolId
  }

  | SelectGenerationV1 {
    schemaVersion: 1
    kind: "SELECT"
    selectionId: SelectionIdV1
    planId
    selectedGenerationId
    supersedesSelectionIds: SelectionIdV1[]
    recoveryCaseRef: StableRefV1(domain = LEDGER_RECOVERY_CASE)
    operatorDecisionRef: StableRefV1(domain = PROJECT_POLICY)
    recordedAt
    actorRef
    toolId
    toolVersion?
  }
```

For both record types, `supersedesSelectionIds` is duplicate-free and lexicographically sorted.

Exact identity preimage:

```text
ImplementationGenerationSelectionV1\n
kind=<BASELINE|SELECT>\n
planId=<planId>\n
selectedGenerationId=<selectedGenerationId>\n
supersedes=<comma-separated sorted selection ids>\n
```

```text
selectionId = "igs1-" + SHA256_HEX(UTF8(selectionIdentityBytes))
```

BASELINE rules:

- exactly one per recovery control history;
- selected generation equals deterministic baseline generation ID;
- supersedes set is empty.

SELECT rules:

- supersedes set is non-empty;
- `recoveryCaseRef` and `operatorDecisionRef` are material;
- permission/provenance refs are excluded from transition identity but MUST validate before mutation/read trust;
- duplicate transition identity is a duplicate selection ID and is invalid.

## 13.2 W10 boundary

FF1 freezes **what SELECT means and how it participates in authority**, but does not invent who may create `LEDGER_RECOVERY_CASE` or approve the operator decision.

Until FF2/W10 freezes `LedgerRecoveryCaseV1` and approval rules:

```text
read / validate existing conforming selection history = allowed
build / validate recovery candidates               = allowed
preview selection transition                       = allowed
append production SELECT                           = fail
result                                              = SELECTION_AUTHORITY_NOT_AVAILABLE
```

W10 MUST consume this exact selection model. It may strengthen permission validation, but it may not move active-generation authority into a generic recovery layer or make candidate creation equal selection.

---

# 14. Deterministic active-generation algorithm

The Implementation-domain reader uses this algorithm only.

## Step 0 — baseline mode

If `recovery/` does not exist:

```text
activeGeneration = deterministic baseline
material = root events.ndjson
```

Root material must pass structural and domain validation.

## Step 1 — selection-history validation

If `recovery/` exists:

1. `selections.ndjson` exists;
2. all records pass framing/JSON/schema/duplicate checks;
3. every `selectionId` recomputes using section 13.1;
4. every SELECT material permission ref resolves according to section 5.3;
5. exactly one valid BASELINE anchor exists for this `planId`;
6. anchor selects the deterministic baseline ID;
7. unknown selection schema fails closed.

Failure => `UNTRUSTED_SELECTION_HISTORY`; no root fallback.

## Step 2 — referenced generation validation

For every generation referenced by selection history:

1. manifest exists and uses supported V1;
2. generation ID recomputes;
3. reason and operation digests recompute from sections 11/12;
4. manifest plan ID matches baseline `PLAN_BOUND`;
5. predecessor exists;
6. lineage is acyclic and reaches baseline;
7. source snapshot matches exact predecessor bytes captured for recovery;
8. permitted operation replay reproduces the recovered prefix exactly;
9. recovered-prefix length/digest match;
10. `PLAN_BOUND` and requirement catalog equal baseline binding exactly;
11. complete current generation including later appends passes structural/domain validation.

Selected invalid generation => fail closed, no predecessor fallback.

Invalid unselected candidate is diagnostic only.

## Step 3 — selection graph

Each `supersedesSelectionIds` parent points to its child SELECT.

Requirements:

- every parent exists;
- every selection is reachable from the single baseline anchor;
- graph is acyclic;
- one-parent SELECT may select only a strict descendant generation of the parent's selected generation;
- multi-parent SELECT is explicit conflict adjudication and supersedes all current terminal claims;
- multi-parent adjudication may select one parent-selected generation or a valid descendant of one parent;
- stale supersedes set is rejected.

## Step 4 — unique terminal

```text
if terminalSelectionCount == 1:
    activeGeneration = terminal.selectedGenerationId
else:
    fail AMBIGUOUS_ACTIVE_GENERATION
```

Never select by line position, timestamp, mtime, lexicographic ID, depth, record count, apparent completeness, or model judgment.

---

# 15. Conflict and concurrency

Two concurrent child selections from one parent create ambiguity; neither wins.

```text
S0 -> S1 selects G1
  \-> S2 selects G2

AMBIGUOUS_ACTIVE_GENERATION
```

Resolution requires one explicitly authorized multi-parent SELECT superseding **all** current terminal selection IDs. Losing evidence remains durable.

A recovery candidate binds the exact active source-generation bytes captured at proposal time. Immediately before an authorized SELECT mutation, the writer re-resolves active generation and exact byte length/digest. If the source changed:

```text
SOURCE_CHANGED_DURING_RECOVERY
```

The candidate cannot be selected and recovery restarts from a fresh snapshot.

---

# 16. Fail-closed matrix

| Condition | Required result |
| --- | --- |
| shallow/incomplete Git history prevents root-set proof | `REPOSITORY_IDENTITY_UNRESOLVED` |
| plan authority absent/ambiguous/unresolvable | `PLAN_BINDING_UNRESOLVED` |
| adopted requirement catalog absent/ambiguous | `REQUIREMENT_CATALOG_UNRESOLVED` |
| material requirement lacks explicit unique local ID | `REQUIREMENT_IDENTITY_UNRESOLVED` |
| plan identity input changes | `NEW_PLAN_IDENTITY_REQUIRED` |
| event payload/cardinality violates exact V1 schema | `UNTRUSTED_ACTIVE_GENERATION` |
| unknown requirement reference | `UNTRUSTED_ACTIVE_GENERATION` |
| observation material ref unavailable | effective observation `INCONCLUSIVE`/`UNAVAILABLE` by section 9 |
| observation material ref identity conflicts | effective observation `INCONCLUSIVE` |
| control/lifecycle material authority ref unavailable/conflicts | `UNTRUSTED_ACTIVE_GENERATION` |
| illegal blocker/defer/correction lifecycle | `UNTRUSTED_ACTIVE_GENERATION` |
| required oracle A FAIL then oracle B PASS | aggregate remains FAIL while A remains effective FAIL |
| required oracle never observed | aggregate `UNAVAILABLE` |
| duplicate complete event ID | no V1 deduplication; operator/unrecoverable stop |
| complete unsupported/corrupt middle record | no omission; operator/unrecoverable stop |
| invalid/ambiguous recovery transform schema | no candidate selection |
| recovery reason/operation digest mismatch | `DIGEST_MISMATCH` |
| missing final LF on complete domain-valid event | LF-only candidate permitted |
| empty separator | redundant-LF omission candidate permitted |
| incomplete terminal fragment | candidate permitted; permanent generation limitation + plan-wide re-observation rule |
| recovery directory exists but selection history corrupt/missing | `UNTRUSTED_SELECTION_HISTORY`; no root fallback |
| malformed/unrecomputable BASELINE selection ID | `UNTRUSTED_SELECTION_HISTORY` |
| two or more terminal selections | `AMBIGUOUS_ACTIVE_GENERATION` |
| broken selection cycle/lineage | fail closed |
| selected generation digest/predecessor mismatch | fail closed; no predecessor fallback |
| invalid unselected candidate | diagnostic only |
| source changed during recovery | `SOURCE_CHANGED_DURING_RECOVERY` |
| SELECT attempted before W10 authorization authority exists | `SELECTION_AUTHORITY_NOT_AVAILABLE` |
| active planning authority moves to new plan identity | old ledger historical; no new ordinary writes |
| EHA reference exists | reference only; no copied Implementation verdict |

---

# 17. `LedgerIntegrityCore` boundary

Shared structural core MAY provide:

```text
exact raw byte capture
sha256 digest
NDJSON framing
line / byte corruption location
JSON syntax validation
schema hook invocation
duplicate-ID primitives
reference lexical-format primitives
generic DAG / lineage-shape primitives
```

It MUST NOT decide:

```text
project plan authority
repository/plan requirement completeness policy
legal Implementation transitions
positive/negative evidence sufficiency
per-oracle policy membership
active Implementation generation
recovery permission
EHA verdict
source mutation permission
```

The section 14 algorithm belongs to the Implementation-domain adapter/API even when graph traversal uses shared primitives.

Generic APIs equivalent to these are forbidden:

```text
make_generation_authoritative(anyLedger)
set_current_generation(anyDomain)
repair_and_select_generic(...)
```

---

# 18. Relationship to other freezes

## MF2 / MF3

Acceptance snapshots and completeness objects remain external. They may be referenced but are not editable Implementation truth.

## MF4

Implementation ledger recovery is not automatic source repair. Repair-attempt budgets and `REPAIR_LOOP_STALLED` do not determine Implementation generation identity or selection.

## MF5

RepairPacket/Jinja/HostExecutionProfile may represent an already-authorized operation. They never choose authority.

## FF2 / W10

W10 owns recovery-case and approval permission semantics. It MUST preserve:

```text
fixed PlanIdentity
fixed adopted requirement catalog
safe-reframe V1 operation
immutable candidate generation
material recoveryCaseRef
material operatorDecisionRef
Implementation-domain SELECT
unique-terminal active-generation algorithm
no predecessor fallback
```

---

# 19. Required deterministic tests for W2/W4

Implementation may not claim FF1 conformance without adversarial tests covering at least:

## SIB0 / identity

1. RC7 acceptance metadata does not inherit predecessor SIB0 after CC-STATE redefinition;
2. same binding root-set -> same repository ID;
3. incomplete/shallow root proof -> repository identity unresolved;
4. same exact plan/authority/catalog inputs -> same plan ID;
5. changed binding SHA/path/blob/authority/catalog/repository identity -> different plan ID;
6. missing/ad-hoc/inferred requirement catalog -> bind fails;
7. catalog locator path/blob mismatch -> bind fails;
8. same local requirement ID under revised plan -> different requirement ID;
9. old-plan events never attach to new-plan requirement identities.

## Exact event schemas

10. every V1 event payload accepts only its frozen fields/types/cardinalities;
11. unknown payload field/type/schema fails closed;
12. `PLAN_BOUND` is first/once, evidence-ref set exact, and catalog equal;
13. work event requires bounded changed surfaces and never yields IMPLEMENTED alone;
14. modified surface with equal before/after blob or malformed rename fails;
15. implementation observation with unavailable/conflicting material ref becomes INCONCLUSIVE;
16. blocker resolve requires an existing open blocker and matching scope;
17. defer/resume requires material project-policy authority refs and legal sequence;
18. invalidation/reinstatement requires exact target event, matching subject/requirements, material decision/evidence refs;
19. unresolved material control ref makes active history untrusted rather than silently ignoring the event.

## Exact target / oracle semantics

20. same-SHA implementation evidence affects only that exact target;
21. ancestor/different-SHA evidence does not inherit state;
22. per-oracle state keeps oracle A and B independent;
23. oracle A FAIL followed by oracle B PASS does not aggregate to PASS;
24. missing required oracle aggregates UNAVAILABLE;
25. unresolved oracle evidence aggregates UNAVAILABLE;
26. digest-conflicting oracle evidence aggregates INCONCLUSIVE;
27. PASS requires every required oracle PASS or authority-backed N/A and at least one PASS;
28. EHA reference does not materialize a second stored verdict.

## Structural recovery

29. clean baseline stays baseline active;
30. operation transform identity is deterministic across implementations;
31. transform order is canonical and overlapping ranges fail;
32. missing final LF uses one EOF append transform only;
33. empty separator transform binds exactly one LF source byte;
34. incomplete terminal fragment transform binds exact terminal range/digest;
35. reasonCodes exactly equal corruption-code set and reasonDigest recomputes;
36. torn-fragment recovery keeps permanent generation limitation and requires per-axis post-selection re-observation for positive current claims;
37. invalid complete middle record cannot be omitted;
38. duplicate event cannot be deduplicated by recovery;
39. unknown complete schema cannot be omitted;
40. damaged predecessor bytes remain unchanged;
41. generation identity is stable across timestamps/actors/tool versions;
42. candidate publication without selection does not become active;
43. source append during recovery prevents selection;
44. selected successor write-fences predecessor.

## Selection authority

45. BASELINE selection ID recomputes from exact kind/plan/generation/supersedes preimage;
46. SELECT ID recomputes from exact kind/plan/generation/supersedes preimage;
47. SELECT with empty supersedes set is invalid;
48. one valid terminal selection chooses its generation on read;
49. two terminals yield ambiguity regardless of timestamps;
50. multi-parent adjudication superseding all terminals resolves conflict;
51. stale supersedes set is rejected;
52. missing predecessor/cycle/digest mismatch fails closed without fallback;
53. corrupt/unresolvable selection permission history fails closed without root fallback;
54. invalid unselected candidate does not poison valid current selection;
55. generation with changed PLAN_BOUND/catalog is invalid;
56. plan revision cannot be smuggled through recovery;
57. before W10 authority exists, production SELECT mutation fails `SELECTION_AUTHORITY_NOT_AVAILABLE`.

## EBCA uncertainty

58. material ref digest mismatch never upgrades to implementation/local-verification/control authority;
59. no aggregate SIB/release acceptance value is writable/derivable as Implementation authority.

---

# 20. MUST / MUST NOT summary

## MUST

- treat RC7 `CC-STATE` as architecturally reopened and require replacement SIB0 lineage;
- bind one ledger to one exact `PlanIdentityV1`;
- derive repository identity deterministically from the complete Git root set reachable from binding SHA;
- require an exact project-authority-adopted requirement catalog;
- use explicit plan-owned local requirement IDs and deterministic requirement IDs;
- use the exact closed V1 event/payload schemas;
- bind every event to one exact subject SHA;
- require material digest/content-addressed binding for observations and control references;
- apply deterministic unavailable-vs-conflict consequences;
- retain append-only history;
- derive local verification per oracle before deterministic aggregation;
- keep EHA as a reference, not copied verdict authority;
- preserve plan revision as a new ledger root;
- preserve recovery as immutable same-plan generation lineage;
- use exact recovery-transform/reason/generation identities;
- use exact BASELINE/SELECT identities and unique-terminal selection on read;
- keep production SELECT mutation blocked until W10 supplies validated recovery-case/approval authority;
- fail closed on ambiguity/broken selected history;
- preserve unknown torn intent as permanent generation limitation with plan-wide re-observation discipline.

## MUST NOT

- inherit predecessor SIB0 across the RC7 CC-STATE authority redefinition;
- use Markdown/model confidence/filename recency as plan or requirement authority;
- invent the requirement universe from prose scanning;
- use host path/remote nickname/branch name as repository identity;
- leave event payload or recovery-transform identity to implementation discretion;
- let the last LOCAL_CHECK from a different oracle overwrite another oracle's result;
- accept mutable-by-reference evidence/control refs;
- silently ignore invalid lifecycle/control authority refs;
- transfer state across plan identities or Git SHAs;
- write SIB/EHA verdicts as Implementation-owned truth;
- make generation creation equal selection;
- let LedgerIntegrityCore choose domain authority;
- let W4 invent recovery permission before W10;
- select by timestamp, file position, mtime, depth, record count, or model judgment;
- fall back to a predecessor after selected-state failure;
- rewrite/delete/compact historical authoritative events;
- deduplicate/drop complete records to obtain a cleaner recovery;
- treat plan revision as recovery;
- garbage-collect published V1 authority history.

---

# 21. Freeze closure / stop-condition audit

FF1's stop condition is satisfied for **Implementation-domain generation/lifecycle semantics** because the previously ambiguous choices are now explicit:

| Question | Frozen decision |
| --- | --- |
| RC7 SIB0 impact | `CC-STATE` redefinition reopens SIB0; replacement RC7 SIB0 required |
| physical durable location | `.opencode/state/implementation-ledgers/<planId>/` |
| repository identity | deterministic complete reachable Git root-set digest |
| plan identity | exact binding SHA/path/blob/project authority/catalog identity |
| requirement universe | exact project-authority-adopted `ImplementationRequirementCatalogV1` |
| requirement identity | explicit local ID -> plan-scoped deterministic ID |
| event families | closed V1 set |
| payload schemas | exact type/cardinality schemas in section 8 |
| material refs | digest-bound or owning-domain content-addressed, with deterministic failure consequences |
| exact-target status | same-target observations only |
| local verification | independent per-oracle state + frozen required-oracle aggregation |
| EHA overlap | reference only |
| correction lifecycle | VALID <-> INVALIDATED through explicit control events |
| blocker lifecycle | open once -> resolve once |
| defer lifecycle | material authority-backed ACTIVE <-> DEFERRED |
| recovery scope | fixed plan identity + fixed adopted catalog |
| allowed recovery | exact safe-reframe transform union only |
| recovery operation identity | exact canonical transform array + JCS digest |
| recovery reason identity | exact canonical corruption set + JCS digest |
| torn-fragment uncertainty | permanent generation limitation + plan-wide re-observation rule |
| generation identity | deterministic content/lineage `irg1-*` |
| publication | immutable candidate; candidate != authority |
| BASELINE/SELECT identity | exact kind/plan/generation/supersedes preimage |
| active-generation read algorithm | unique terminal selection only |
| concurrent selections | ambiguity; no recency winner |
| selected invalid generation | fail closed; no predecessor fallback |
| source changes during recovery | candidate cannot select |
| production SELECT permission | blocked until FF2/W10 validates recovery case + approval refs |
| generic structural core | mechanics only |

No Implementation generation, event-payload, requirement-universe, repository-identity, recovery-transform, selection-identity, exact-target, or oracle-aggregation choice is intentionally deferred to W2/W4 implementation.

The remaining permission question belongs explicitly to FF2/W10 and therefore does not authorize W4 to guess.

---

```text
FF1_STATUS:
FROZEN_WITH_EXPLICIT_W10_PERMISSION_BOUNDARY

RC7_SIB0_STATUS:
REOPENED_FOR_CC_STATE_REDEFINITION

UNLOCKS:
W2 Implementation Ledger core
W4A Implementation recovery read/build/validate

SEMANTICS_FROZEN_BUT_MUTATION_BLOCKED:
W4B Implementation recovery SELECT write
    until FF2/W10 LedgerRecoveryCaseV1 authorization exists

DOES_NOT_UNLOCK:
W6 W10 W12 W13 W14 W15 overall-W16

CURRENT_SIB_RUNTIME_INPUT:
6621c65b868d3e279ddcbd8dee182a95c6fb29f8

FF1_DESIGN_BASE:
af0c5dcd4054cb2eef35d7661125fc939b9e3263

GENERATION_AUTHORITY_RULE:
Implementation-domain unique-terminal explicit selection only

PLAN_REVISION_RULE:
new PlanIdentity -> new ledger root; never recovery generation

STOP_CONDITION:
SATISFIED FOR FF1 OWNED SEMANTICS
```
