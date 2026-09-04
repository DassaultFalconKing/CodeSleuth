# RC7 FF1 — Implementation Ledger + Recovery Authority Freeze

**Status:** NORMATIVE RC7 FINAL-FREEZE CONTRACT FOR W2 + W4  
**Session:** FF1 — Implementation Ledger + Recovery Authority Freeze  
**Mode:** DESIGN / CONTRACT FREEZE ONLY  
**Branch:** `docs/rc7-ff1-implementation-ledger-recovery-freeze`  
**Exact design base:** `af0c5dcd4054cb2eef35d7661125fc939b9e3263`  
**Implementation:** explicitly out of scope for this session

This document freezes the Implementation Ledger authority, plan/requirement identity, event lifecycle, derived-state rules, recovery-generation model, and active-generation selection tightly enough that W2 and W4 implementation does not need to invent semantic authority.

The compact rule is:

> **An accepted plan is bound by exact identity; implementation history is append-only; current execution state is derived for an exact target; plan revision creates a new ledger identity; damaged implementation history is recovered through domain-owned lineage and explicit generation selection, never by rewriting history or by generic recovery authority.**

---

# 1. Freeze verdict

FF1 freezes one new narrow RC7 authority:

```text
Implementation Ledger
    owns: accepted-plan execution history
    does not own: project planning policy, source truth, Finding truth,
                  EHA/SIB verdicts, acceptance policy, or generic claims
```

The following previously blocked workstreams are unlocked by this contract once it is integrated into the accepted RC7 design stream:

```text
W2  Implementation Ledger core
W4  Implementation Ledger domain recovery
```

This document does **not** authorize W6 EHA V2, W10 `EhaRepairCaseV1` / `LedgerRecoveryCaseV1` permission schemas, W12 learning records, W13 claim views, W14 final renderer parity, W15 integrated context epistemics, or complete W16 lifecycle exposure.

No generic `LedgerIntegrityCore` operation may select an authoritative Implementation generation.

---

# 2. Exact authority inputs

## 2.1 FF1 design identity

The session branch was re-resolved immediately before this freeze and still pointed exactly to:

```text
branch:
docs/rc7-ff1-implementation-ledger-recovery-freeze

exact base:
af0c5dcd4054cb2eef35d7661125fc939b9e3263
```

The base already contains the accepted MF1–MF5 set plus their cross-contract adjudication.

## 2.2 Current accepted SIB runtime contract input

The current `SIB` ref resolves to:

```text
6621c65b868d3e279ddcbd8dee182a95c6fb29f8
```

That exact commit is the accepted RC6/SIB2 runtime predecessor used as current executable-contract authority for FF1. This docs-only branch is not a runtime implementation base and does not move or reinterpret `SIB`, `main`, release refs, tags, releases, or EHA state.

Material current-runtime contracts inspected at that exact SIB commit include:

- `docs/DURABLE-EVIDENCE-STORE.md` — current narrow filesystem evidence-store/write-boundary contract;
- `docs/DEVELOPMENT-CONTINUATION-CONTRACT.md` — current exact-target, planning-authority, active-scope and no-manufactured-authority contract;
- `docs/STABLE-INTEGRATION-BASELINE.md` — current SIB0/SIB1/SIB2 identity and exact-acceptance semantics;
- `docs/RC6-IMPLEMENTATION-LEDGER.md` — current human-readable implementation ledger precedent, explicitly subordinate to executable/normative/durable authority;
- `docs/EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md` — EBCA identity/authority/evidence/uncertainty vocabulary.

## 2.3 Accepted RC7 freeze inputs

Accepted micro-freeze identities consumed by FF1:

| Input | Exact accepted source head | FF1 use |
| --- | --- | --- |
| MF1 Finding recovery | `c761e1ebacfebad5a4779da69d9d3a9d7a1d8a51` | recovery-generation and selection precedent |
| MF2 acceptance profile snapshot | `d751b03c52168d59a23a445652cf042aa0e0c239` | immutable acceptance-policy snapshot boundary; no duplication in Implementation Ledger |
| MF3 completeness | `b1e697e7cf8c9409538a20f9449b8ddd8780352e` | independent completeness axes remain external to Implementation Ledger |
| MF4 repair termination | `dc3191c11db669e416a3d86af69e7cfae95365af` | automatic source-repair control remains separate from ledger recovery |
| MF5 RepairPacket / host profile | `c9fa42dc032a37509534395f577d7069ae75eb56` | downstream typed repair/render boundary; no recovery authority |

The normative cross-contract integration decision is `docs/RC7-MICRO-FREEZE-CROSS-CONTRACT-ADJUDICATION.md` on the FF1 base. In particular:

- MF1 active-generation selection remains domain-owned;
- MF2 immutable snapshot input remains outside evaluated completeness;
- MF4 profile identity is bound to `AcceptanceProfileSnapshotV1.semanticDigest`;
- MF5 packets/profiles do not grant mutation or recovery authority.

Additional design inputs:

- synthesis: `docs/RC7-THESIS-ANTITHESIS-SYNTHESIS.md`, blob `a3556ca3bd84546835a3ff66847cfb03da54fc7b`;
- pinned antithesis: commit `be5d158880f649ecb568d9a505c694e87bd76e0e`, review blob `02a87228ed1b1b989c4e7dd785b0dd9acba8de9b`;
- feature-plan seed: `docs/RC7-FEATURE-PLAN.md`, blob `ddac1c4a34b0c57f7c6ff668cc7e3d99a56f03c5`.

The thesis, synthesis, feature-plan seed and antithesis are inputs/provenance. Where this document makes an explicit FF1 decision inside W2/W4, this freeze is the implementation authority for that scope.

---

# 3. Preserved authority model

FF1 preserves the synthesis axiom that Finding, Implementation and EHA are separate authorities.

```text
PROJECT / REPOSITORY AUTHORITY
│
├─ tracked Git source + exact Git object identity
├─ project-native planning / architecture / acceptance authority
├─ Finding domain authority
│    └─ existing findings + amendments (+ Finding recovery control)
├─ Implementation domain authority
│    └─ accepted-plan execution events (+ Implementation recovery control)
└─ EHA domain authority
     └─ existing eha.ndjson lineage / later V2 evolution

DERIVED / NON-AUTHORITATIVE
│
├─ Markdown implementation ledger
├─ reports / Mermaid / graph / search views
├─ Development Authority Map navigation
├─ AcceptanceProfileSnapshotV1 as immutable campaign input
├─ completeness assessments
├─ RepairPacketV1 / host presentation
└─ LLM context

SHARED MECHANICS ONLY
└─ LedgerIntegrityCore
     framing / bytes / digests / JSON / schema hooks /
     duplicate detection / reference-format primitives /
     generic lineage-shape validation
```

## 3.1 What the Implementation Ledger owns

The Implementation Ledger owns durable statements that an accepted-plan work step, implementation observation, implementation verification, blocker transition, or authority-backed defer/resume action was recorded for the bound plan.

It may answer:

- which exact accepted plan one ledger is bound to;
- which stable requirement identities belong to that plan;
- which implementation work/evidence events were durably recorded;
- which implementation-local verification observations were durably recorded;
- which blockers remain open;
- whether project authority has deferred/resumed a requirement;
- what execution state is derivable for one exact queried Git target;
- which recovery generation is authoritative for this Implementation Ledger.

## 3.2 What it does not own

The Implementation Ledger MUST NOT decide or persist as its own truth:

- which plan is current project planning authority;
- whether a plan is accepted merely because it was bound once;
- current tracked source content except by exact references;
- Finding lifecycle;
- EHA/SIB verdicts;
- acceptance-profile policy;
- DiscoveryCompleteness or PolicyCompleteness;
- source-mutation permission;
- automatic repair-loop policy;
- generic EBCA claim truth;
- graph, report, Markdown or renderer truth.

A referenced EHA run/verdict remains EHA-owned. The Implementation Ledger records the reference, not a competing verdict.

---

# 4. Physical V1 authority layout

V1 uses one new narrow worktree-local state root under the existing `.opencode/state/` capability class:

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

1. `<planId>` is the deterministic `PlanIdentityV1.planId` defined below and is path-safe by construction.
2. `events.ndjson` is the baseline-generation event stream.
3. Absence of `recovery/` means the deterministic baseline generation is active.
4. If `recovery/` exists, `selections.ndjson` is mandatory and is the Implementation-domain generation-selection authority.
5. A generation directory is an immutable candidate until selected. Presence does not create authority.
6. Temporary generation construction uses a non-authoritative temporary path and becomes visible under its final `<generationId>/` only by same-filesystem atomic publication after validation.
7. No `latest.txt`, timestamp, directory sort, model choice, or generated Markdown selects the active plan or generation.
8. V1 performs no garbage collection of published generations or selections. Published historical generations and selection decisions are retained. Unpublished temporary construction directories may be cleaned because they never entered authority.

The active **project plan** is still selected by upstream project/planning authority. This directory layout only answers which generation is authoritative **inside one already-identified plan ledger**.

---

# 5. Canonical identity primitives

## 5.1 Canonical JSON

FF1-owned content identities use RFC 8785 JSON Canonicalization Scheme (JCS):

```text
canonicalBytes = UTF8(JCS(value))
digestHex      = lowercaseHex(SHA256(canonicalBytes))
```

Inputs must conform to their exact V1 schema before canonicalization. Duplicate JSON object keys are invalid. Strings are Unicode NFC before schema validation where the field permits Unicode. Set-valued arrays are deduplicated and sorted by canonical JSON bytes before hashing. Arrays explicitly defined as ordered preserve order.

Volatile timestamps, actor display names, tool versions and host paths do not participate in semantic identities unless a schema below explicitly states otherwise.

## 5.2 Exact Git identities

V1 Git commit and blob identities are the full lowercase 40-hex object IDs used by the current repository contracts. Abbreviated SHAs are invalid in authoritative FF1 records.

## 5.3 Stable cross-domain references

FF1 reuses the MF5 `StableRefV1` principle:

```text
StableRefV1 {
  domain
  id
  digestSha256?
}
```

The `id` is copied from the owning domain. FF1 MUST NOT normalize, regenerate, or reinterpret another domain's ID.

A cross-domain reference is a pointer to another authority/evidence object. Copying a referenced value into an Implementation event does not transfer ownership of that value.

---

# 6. `PlanIdentityV1`

One Implementation Ledger is bound to exactly one accepted plan identity.

```text
PlanIdentityV1 {
  schemaVersion: "PlanIdentityV1"
  planId: "iplan1-" + 64 lowercase hex

  repositoryId: non-empty stable project identifier
  planPath: repository-root-relative tracked path
  planBlobSha: full lowercase Git blob SHA
  planAuthorityRef: StableRefV1
}
```

`planAuthorityRef` MUST resolve to explicit project-owned authority that establishes the exact referenced plan blob/path as accepted, frozen, canonical, or otherwise authorized for the implementation scope. A filename, recency, LLM judgment, Development Authority Map confidence value, or generated report is not sufficient authority.

The Development Authority Map/Continuation machinery may navigate to the owning authority, but the derived map does not become plan policy merely because it found it.

The identity preimage is exactly:

```json
{
  "planAuthorityRef": <StableRefV1>,
  "planBlobSha": "<full blob sha>",
  "planPath": "<repository path>",
  "repositoryId": "<stable repository id>",
  "schemaVersion": "PlanIdentityV1"
}
```

Then:

```text
planId = "iplan1-" + SHA256_HEX(JCS(identityPreimage))
```

`planId` therefore changes when repository identity, authoritative plan path, exact plan bytes, or owning plan-authority identity changes.

## 6.1 Plan revision rule

A plan revision is **not** an Implementation recovery generation.

Any change to a `PlanIdentityV1` identity input creates:

```text
new PlanIdentityV1
-> new planId
-> new implementation-ledger root
```

Recovery generations under `<planId>` MUST preserve the exact same `PlanIdentityV1` and requirement catalog as the baseline. A recovery generation that changes `PLAN_BOUND`, plan identity, or requirement identity is invalid.

A predecessor/successor plan relation may be retained as an outbound authority/navigation reference in the new plan binding, but it does not transfer requirement status or evidence.

---

# 7. Stable `RequirementIdV1`

FF1 rejects generated requirement identity based on prose similarity, heading order, timestamps, or model interpretation.

Every material requirement tracked by the Implementation Ledger MUST expose an explicit plan-local identifier in the exact accepted plan authority.

```text
PlanLocalRequirementIdV1
    = exact case-sensitive plan-owned identifier
    = Unicode NFC
    = 1..128 UTF-8 bytes
    = no leading/trailing Unicode whitespace
    = no C0/C1 controls
```

The plan-local ID is not silently case-folded or rewritten.

For one bound plan:

```text
RequirementIdentityPreimageV1 {
  schemaVersion: "ImplementationRequirementIdentityV1"
  planId: <PlanIdentityV1.planId>
  localRequirementId: <exact plan-owned id>
}

requirementId =
  "ireq1-" + SHA256_HEX(JCS(RequirementIdentityPreimageV1))
```

Consequences:

1. the same plan-local identifier under the same exact plan identity produces the same `requirementId`;
2. the same local identifier under a revised plan produces a different `requirementId` because `planId` changed;
3. old implementation evidence therefore cannot silently attach to a revised plan;
4. cross-plan requirement lineage, when project authority declares it, is navigation/provenance only until new-plan evidence is explicitly recorded.

## 7.1 Requirement binding record

The first event retains a validated binding for every material requirement:

```text
RequirementBindingV1 {
  localRequirementId
  requirementId
  sourceLocator {
    path
    blobSha
    startLine
    endLine
    exactBytesSha256
  }
}
```

The source range MUST contain the exact plan-owned requirement identifier and the material requirement statement it identifies. `exactBytesSha256` is over the exact UTF-8/file bytes in that bounded range; no whitespace or newline normalization occurs before hashing.

Every material requirement in the declared implementation scope must have exactly one binding. Missing, duplicated, ambiguous, inferred-only, or unresolvable identifiers stop plan binding with:

```text
REQUIREMENT_IDENTITY_UNRESOLVED
```

The Implementation Ledger MUST NOT invent an ID to keep working.

---

# 8. `ImplementationEventV1`

Authoritative execution history is one LF-terminated NDJSON object per event.

Common envelope:

```text
ImplementationEventV1 {
  schemaVersion: 1
  kind: "ImplementationEventV1"
  eventId: "ie1-" + 64 lowercase hex

  planId
  eventType
  subjectSha: full exact Git commit SHA
  requirementIds: RequirementIdV1[]
  evidenceRefs: StableRefV1[]
  payload: type-specific object

  provenance {
    recordedAt
    actorRef?
    toolId
    toolVersion?
  }
}
```

`requirementIds` and `evidenceRefs` are set-valued unless an event contract below states otherwise. They are deduplicated and canonically sorted for identity.

Event semantic identity is computed over every field above except `eventId` and `provenance`:

```text
eventId = "ie1-" + SHA256_HEX(JCS(eventSemanticPreimage))
```

Re-recording the same semantic event with a different timestamp/tool version/actor therefore yields the same event ID and is rejected as a duplicate rather than manufacturing new history.

Physical NDJSON append order is domain event order. `recordedAt` is provenance and MUST NOT override physical order.

## 8.1 Allowed V1 event types

The V1 event set is closed. Unknown event types or schema versions fail closed.

### `PLAN_BOUND`

Exactly one `PLAN_BOUND` MUST be the first durable event in the baseline stream and therefore in every recovery generation prefix.

Payload:

```text
PlanBoundV1 {
  planIdentity: PlanIdentityV1
  requirements: RequirementBindingV1[]
  predecessorPlanRefs: StableRefV1[]
}
```

Rules:

- `planId` MUST recompute from `planIdentity`;
- every requirement ID MUST recompute from `planId` + exact local ID;
- requirement bindings MUST validate against the exact plan blob;
- the plan authority reference MUST resolve at bind time;
- `predecessorPlanRefs` are provenance/navigation only and transfer no status;
- `PLAN_BOUND` cannot be invalidated, superseded, corrected by recovery, or repeated inside one plan ledger.

### `WORK_STEP_RECORDED`

Records that bounded implementation work actually occurred for one or more bound requirements on `subjectSha`.

Requirements:

- `requirementIds` non-empty;
- at least one exact material `evidenceRef`;
- payload contains a stable `workUnitId` and bounded operation/changed-surface descriptors;
- intention, TODO prose, or a model statement without observed evidence is not a work event.

This event can establish `IN_PROGRESS`; it cannot establish `IMPLEMENTED` or acceptance.

### `IMPLEMENTATION_EVIDENCE_RECORDED`

Records an evidence-backed implementation-state observation for exactly one requirement on `subjectSha`.

```text
implementationState =
    PARTIAL
    | IMPLEMENTED
    | NOT_IMPLEMENTED
    | INCONCLUSIVE
```

Rules:

- exactly one `requirementId`;
- material evidence references are mandatory;
- `IMPLEMENTED` requires positive evidence sufficient for the bounded implementation claim under the requirement's owning contract;
- changed files alone do not imply `IMPLEMENTED`;
- `INCONCLUSIVE` is preserved as uncertainty and is never promoted by prose.

This is implementation-domain execution state. It is not SIB1/SIB2 acceptance.

### `VERIFICATION_RECORDED`

Two V1 verification forms exist.

#### `LOCAL_CHECK`

```text
LocalVerificationV1 {
  verificationKind: "LOCAL_CHECK"
  oracleId: stable machine check identity
  result: PASS | FAIL | INCONCLUSIVE | UNAVAILABLE | NOT_APPLICABLE
  notApplicableRationaleRef?: StableRefV1
}
```

Rules:

- exactly one requirement ID;
- exact run/evidence references are mandatory;
- `NOT_APPLICABLE` requires explicit authority-backed rationale;
- the event binds the exact `subjectSha` on which the check ran;
- the result is implementation-local verification evidence, not EHA/SIB acceptance.

#### `EHA_REFERENCE`

```text
EhaVerificationReferenceV1 {
  verificationKind: "EHA_REFERENCE"
  ehaEventRef: StableRefV1(domain = EHA)
}
```

Rules:

- the Implementation Ledger stores the exact EHA reference;
- it MUST NOT copy the EHA verdict into a second independently authoritative `result` field;
- any combined display that shows the EHA verdict rehydrates it from EHA authority at read time.

### `BLOCKER_RECORDED`

Creates one open blocker whose identity is the `BLOCKER_RECORDED` event ID.

Payload declares scope:

```text
blockerScope = PLAN | REQUIREMENT
reasonCode
```

Rules:

- `REQUIREMENT` scope requires exactly one requirement ID;
- `PLAN` scope requires no requirement IDs;
- exact evidence/authority refs explaining the blocker are mandatory.

### `BLOCKER_RESOLVED`

References exactly one currently open `BLOCKER_RECORDED.eventId` and records exact resolution evidence.

Rules:

- unknown blocker -> illegal transition;
- already resolved blocker -> illegal transition;
- a recurring condition is recorded as a new blocker event rather than reopening the old blocker ID.

### `DEFER_DECISION_RECORDED`

Records an upstream project/plan-authority decision to defer exactly one requirement.

Rules:

- exactly one requirement ID;
- payload contains non-empty `decisionAuthorityRef`;
- the referenced authority, not the Implementation Ledger, owns the decision;
- deferring an already deferred requirement without an intervening resume is illegal.

### `RESUME_DECISION_RECORDED`

Records an upstream authority decision that resumes exactly one currently deferred requirement.

Rules:

- references the current defer event;
- carries non-empty `decisionAuthorityRef`;
- resume while not deferred is illegal.

### `EVENT_INVALIDATED`

Append-only semantic correction for an incorrectly recorded evidence event.

It may target only:

```text
WORK_STEP_RECORDED
IMPLEMENTATION_EVIDENCE_RECORDED
VERIFICATION_RECORDED
```

Rules:

- payload contains `targetEventId`, non-empty `operatorDecisionRef`, reason code, and correction evidence refs;
- target must currently be `VALID`;
- target becomes `INVALIDATED` for derived-state computation but remains byte-for-byte historical evidence;
- invalidating `PLAN_BOUND`, blockers, defer/resume authority decisions, recovery selections, or another correction-control event is forbidden.

### `EVENT_REINSTATED`

The inverse operator-adjudicated correction when an evidence event was previously invalidated in error.

Rules:

- same target classes as `EVENT_INVALIDATED`;
- target must currently be `INVALIDATED`;
- non-empty `operatorDecisionRef` and re-establishing evidence refs are mandatory;
- target becomes `VALID` again for derivation;
- reinstating an already-valid target is illegal.

The allowed target-disposition lifecycle is therefore exactly:

```text
VALID --EVENT_INVALIDATED--> INVALIDATED
INVALIDATED --EVENT_REINSTATED--> VALID
```

Correction-control events themselves are immutable. An erroneous control decision is represented by the inverse control transition on the original target, not by rewriting or deleting the control event.

---

# 9. Domain lifecycle and deterministic derived state

## 9.1 Validation order

The active generation is interpreted in this order:

1. structural validation through `LedgerIntegrityCore` mechanics;
2. exact `PLAN_BOUND` / identity validation;
3. event-ID and requirement-reference validation;
4. event-disposition control lifecycle validation;
5. blocker lifecycle validation;
6. defer/resume lifecycle validation;
7. cross-domain material-reference validation/resolution status;
8. exact-target derived requirement state.

A structurally readable ledger can still be semantically invalid. Shared mechanics do not decide that semantic validity.

## 9.2 Exact-target rule

Every query for current implementation state MUST name one full exact `targetSha`.

For each requirement, only valid evidence/work/verification events whose `subjectSha` equals the queried `targetSha` may establish positive current implementation or verification state for that target.

Events from ancestor, sibling, tree-equivalent, cherry-picked, rebased, or otherwise different SHAs remain historical execution context. They do not silently transfer current implementation or verification status.

If the queried target has no current evidence for an axis, the result is `UNESTABLISHED`, not inherited PASS and not inferred failure.

## 9.3 Requirement state axes

The authoritative derived read model preserves independent axes instead of collapsing them into one seductive `done=true` bit.

```text
ImplementationRequirementStateV1 {
  planId
  requirementId
  targetSha

  workState:
    UNESTABLISHED
    | IN_PROGRESS
    | PARTIAL
    | IMPLEMENTED
    | NOT_IMPLEMENTED
    | INCONCLUSIVE

  localVerificationResult:
    UNESTABLISHED
    | PASS
    | FAIL
    | INCONCLUSIVE
    | UNAVAILABLE
    | NOT_APPLICABLE

  ehaRefs: StableRefV1[]

  disposition:
    ACTIVE
    | DEFERRED

  openBlockerEventIds: eventId[]

  trustLevel:
    TRUSTWORTHY
    | DEGRADED
    | UNTRUSTED

  limitations: stable machine-readable diagnostics[]
}
```

### Work-state derivation

For the exact queried target and after event validity filtering:

1. if one or more `IMPLEMENTATION_EVIDENCE_RECORDED` events exist, the last valid event in authoritative append order sets `workState` to its declared state;
2. otherwise, if one or more `WORK_STEP_RECORDED` events exist, `workState = IN_PROGRESS`;
3. otherwise `workState = UNESTABLISHED`.

### Verification derivation

For the exact queried target:

1. the last valid `LOCAL_CHECK` event in authoritative append order supplies the recorded local result;
2. `EHA_REFERENCE` events populate `ehaRefs` only and do not become local PASS/FAIL;
3. a required material reference that cannot be resolved or whose bound digest conflicts cannot support a positive result: the effective read model exposes `UNAVAILABLE` or `INCONCLUSIVE` as appropriate and retains the recorded event as historical evidence;
4. no EHA verdict is synthesized or cached as Implementation authority.

### Blocker derivation

Open blockers are the set of valid `BLOCKER_RECORDED` events without a legal matching `BLOCKER_RESOLVED` event. Blocker state is orthogonal to work/verification state. A verified implementation may still be blocked by an unresolved project dependency; a blocker does not rewrite prior evidence.

### Defer derivation

`ACTIVE` and `DEFERRED` follow the legal authority-backed defer/resume event sequence. Defer does not mean `NOT_IMPLEMENTED`, and resume does not establish implementation evidence.

## 9.4 No aggregate acceptance status

The Implementation Ledger MUST NOT persist or derive an authoritative:

```text
SIB0 = PASS
SIB1 = PASS
SIB2 = PASS
releaseAccepted = true
overallAcceptance = PASS
```

It also MUST NOT persist a generic authoritative `done=true` over a plan.

A presentation may summarize execution coverage, but acceptance remains owned by its acceptance/EHA authority and must be shown as a reference-derived view.

---

# 10. Ordinary append/write contract

Implementation history may be written only through the Implementation-domain API. Raw agent/Skill/Playbook/report writes to the authority files are forbidden.

A conforming writer MUST:

1. resolve and validate the current project plan authority before creating or mutating a plan ledger;
2. resolve the Implementation-domain active generation;
3. fail closed if selection history/generation authority is ambiguous or untrusted;
4. serialize writes through an exclusive domain write lock or equivalent compare-and-append mechanism;
5. verify expected active `generationId`, current byte length and current exact stream digest before append;
6. append exactly one complete canonical JSON record plus one terminal LF;
7. never edit, truncate, reorder, compact or normalize prior authoritative bytes;
8. re-read/revalidate the resulting state before returning a successful semantic mutation result.

If concurrent state changed after the writer's precondition snapshot, the write is rejected and retried from fresh state. It MUST NOT append an event whose legal transition was checked against stale state.

After a recovery successor is selected, all ordinary writes target only that selected generation. Its predecessor is permanently write-fenced.

If upstream planning authority no longer establishes this exact plan as the active implementation scope, ordinary new work/evidence writes fail closed for that plan. Historical reads remain allowed.

---

# 11. Implementation recovery generations

Implementation recovery is domain-owned W4 behavior. It repairs trustworthy representation of **one fixed `PlanIdentityV1` history**. It does not revise the plan and does not repair project source.

## 11.1 Baseline generation

Every bound plan has one deterministic baseline generation:

```text
baselineGenerationId =
  "igb1-" + SHA256_HEX(UTF8(
    "ImplementationBaselineGenerationV1\n" +
    "planId=" + planId + "\n"
  ))
```

The baseline ID is stable across ordinary append-only writes. It is a lineage-root identity, not the event-stream content digest.

Before the first recovery selection, ordinary writes append to root `events.ndjson`.

## 11.2 Exact stream snapshots

```text
ImplementationStreamSnapshotV1 {
  byteLength: non-negative integer
  sha256: 64 lowercase hex
}
```

The digest is SHA-256 over exact file bytes. No newline conversion, Unicode normalization, JSON reserialization or whitespace normalization occurs before hashing.

## 11.3 Recovery reason and V1 operation

V1 structural recovery intentionally follows the accepted MF1 safe-reframe precedent.

Allowed reason codes / transforms are exactly:

```text
MISSING_TERMINAL_LF          -> APPEND_TERMINAL_LF
EMPTY_RECORD                 -> OMIT_EMPTY_RECORD_SEPARATOR
INCOMPLETE_TERMINAL_FRAGMENT -> OMIT_INCOMPLETE_TERMINAL_FRAGMENT
```

### `APPEND_TERMINAL_LF`

Allowed only when the terminal non-LF bytes are one complete JSON event accepted by the current Implementation-domain validator and the sole framing defect is the missing final LF byte. Recovery appends exactly one `0x0A`.

### `OMIT_EMPTY_RECORD_SEPARATOR`

Allowed only for an empty NDJSON record created solely by adjacent LF separators. Only the redundant separator byte may be omitted.

### `OMIT_INCOMPLETE_TERMINAL_FRAGMENT`

Allowed only for a terminal non-LF fragment that does not parse as one complete JSON event. Recovery records the exact byte range and SHA-256 of the omitted fragment and retains the damaged predecessor bytes forever.

The transform does not reconstruct the intended event.

### Forbidden V1 recovery transformations

V1 recovery MUST NOT:

- alter or omit a complete LF-terminated non-empty record;
- omit a complete event merely because its schema version is unknown;
- deduplicate a duplicate event ID;
- delete an illegal lifecycle transition;
- rewrite `PLAN_BOUND`, `planId`, a requirement ID, subject SHA, evidence reference, or recorded result;
- reorder complete events;
- copy events into a revised plan identity;
- manufacture a missing event from model prose, logs, timestamps or likely intent.

A complete unsupported-schema event, duplicate ID, semantic lifecycle violation, unresolved identity collision, or corrupt complete middle record therefore yields:

```text
OPERATOR_DECISION_REQUIRED
or
UNRECOVERABLE_WITHOUT_EXACT_EVIDENCE
```

and V1 MUST NOT create/select a recovery generation that hides the defect.

## 11.4 Semantic-loss consequence

`APPEND_TERMINAL_LF` and `OMIT_EMPTY_RECORD_SEPARATOR` preserve all complete event semantics. After complete validation and selection, they may yield `TRUSTWORTHY` state.

`OMIT_INCOMPLETE_TERMINAL_FRAGMENT` proves only that the fragment was not one complete durable event. It does not prove what operation may have been attempted before interruption.

A generation using that transform MUST record:

```text
semanticLossRisk = UNKNOWN_TERMINAL_EVENT
```

and its current read model is `DEGRADED` until exact-target evidence is re-established after selection.

For every requirement, pre-recovery positive `IMPLEMENTED` or local `PASS` evidence may still be shown as historical prefix evidence, but it MUST NOT be presented as a fresh positive current claim after an `UNKNOWN_TERMINAL_EVENT` recovery until a post-selection evidence-bearing event re-establishes the corresponding axis for the queried exact target.

If the torn fragment cannot safely identify an affected requirement, the uncertainty is plan-wide. The implementation MUST NOT ask a model to guess which requirement the fragment probably concerned.

This is the FF1 application of EBCA's `unknown remains unknown` rule.

---

# 12. `ImplementationRecoveryGenerationV1`

A published generation manifest contains at least:

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
    reasonCodes[]
    corruption[] {
      code
      startByte
      endByteExclusive
      rawSha256
    }
    reasonDigest
    operation {
      schemaVersion: 1
      operationKind: "SAFE_REFRAME_V1"
      transforms[]
    }
    operationDigest
    semanticLossRisk: NONE | UNKNOWN_TERMINAL_EVENT
  }

  recoveredPrefix: ImplementationStreamSnapshotV1

  provenance {
    recordedAt
    toolId
    toolVersion?
    actorRef?
  }
}
```

For V1:

```text
sourceGenerationId == predecessorGenerationId
```

Corruption descriptors are sorted by `startByte`, `endByteExclusive`, `code`, `rawSha256` before `reasonDigest` is computed. The operation descriptor and transforms are retained in full; digest-only provenance is insufficient.

Generation identity preimage is exactly:

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

Then:

```text
generationId = "irg1-" + SHA256_HEX(UTF8(identityPreimage))
```

Identity includes the fixed `planId` and exact source/recovered bytes. It excludes timestamp, filesystem mtime, actor display name, tool version, absolute host path, explanatory prose, branch name, generation-directory creation order, and mutable refs.

## 12.1 Recovered prefix and post-selection continuation

`recoveredPrefix` binds exact bytes at generation creation, not every future legitimate append.

Before selection:

- candidate `events.ndjson` must exactly match the recorded prefix length/digest;
- no ordinary event may append to the candidate.

After selection:

- recovered prefix bytes are immutable forever;
- ordinary domain events may append after that prefix;
- a future recovery snapshots the complete then-current active generation, including its recovered prefix plus all post-selection appends;
- once a successor is selected, its predecessor is permanently write-fenced.

---

# 13. Implementation generation-selection authority

No generation manifest has an `active: true` field. Generation creation is not authority selection.

Selection is one explicit append-only Implementation-domain control history:

```text
recovery/selections.ndjson
```

## 13.1 Bootstrap baseline anchor

Before the first recovery candidate is selected, creation of the recovery control subtree records exactly one baseline anchor:

```text
ImplementationGenerationSelectionV1 {
  schemaVersion: 1
  kind: "BASELINE"
  selectionId
  planId
  selectedGenerationId: <baselineGenerationId>
  supersedesSelectionIds: []
  recordedAt
  actorRef
  toolId
}
```

## 13.2 Selection event

```text
ImplementationGenerationSelectionV1 {
  schemaVersion: 1
  kind: "SELECT"
  selectionId
  planId
  selectedGenerationId
  supersedesSelectionIds[]
  operatorDecisionRef
  recordedAt
  actorRef
  toolId
  toolVersion?
}
```

Every `SELECT` changes Implementation-domain authority and therefore requires non-empty explicit `operatorDecisionRef` and actor/tool attribution.

`supersedesSelectionIds[]` is deduplicated and lexicographically sorted before identity hashing.

Selection identity is:

```text
ImplementationGenerationSelectionV1\n
planId=<planId>\n
selectedGenerationId=<selectedGenerationId>\n
supersedes=<comma-separated sorted selection ids>\n
```

then:

```text
selectionId = "igs1-" + SHA256_HEX(UTF8(selectionIdentityBytes))
```

Timestamp, actor/tool provenance and `operatorDecisionRef` do not participate in selection identity. The state transition is the identity; provenance records who/when/under which explicit approval reference performed it.

---

# 14. One deterministic active-generation algorithm

The Implementation-domain reader MUST use this algorithm and no competing rule.

## Step 0 — legacy/baseline mode

If `<planId>/recovery/` does not exist:

```text
activeGeneration = deterministic baseline generation
material = root events.ndjson
```

The root stream MUST still pass structural/domain validation.

## Step 1 — recovery-control validation

If `recovery/` exists:

1. `selections.ndjson` MUST exist;
2. every record passes structural framing/JSON/schema/duplicate-ID checks;
3. every `selectionId` recomputes exactly;
4. there is exactly one valid `BASELINE` anchor for this `planId`;
5. the anchor selects the deterministic baseline generation ID;
6. unknown selection schema versions fail closed.

Any failure returns:

```text
UNTRUSTED_SELECTION_HISTORY
```

with no fallback to root `events.ndjson`.

## Step 2 — referenced-generation validation

For every generation referenced by selection history:

1. `generation.json` exists and uses supported V1 schema;
2. `generationId` recomputes exactly;
3. manifest `planId` exactly matches this ledger's baseline `PLAN_BOUND.planId`;
4. source/predecessor generation exists;
5. predecessor links are acyclic and reach the deterministic baseline;
6. source snapshot matches the exact predecessor bytes captured for recovery;
7. replaying the permitted safe-reframe operation produces exactly the recorded recovered prefix;
8. recovered-prefix length/digest match generation bytes;
9. `PLAN_BOUND` and requirement catalog are byte/semantically identical to the fixed baseline binding;
10. the complete current generation material, including post-selection continuation, passes structural and Implementation-domain lifecycle validation.

A selected generation failing any item is not authoritative and causes fail-closed state. The reader MUST NOT fall back to its predecessor.

An invalid generation that no selection references is a non-authoritative failed candidate and does not poison an otherwise valid active selection chain.

## Step 3 — selection graph

Build the directed graph where each `supersedesSelectionIds` parent points to its child `SELECT`.

Requirements:

- every parent selection ID exists;
- every selection is reachable from the single baseline anchor;
- the selection graph is acyclic;
- a one-parent `SELECT` may select only a strict descendant generation of the parent's selected generation;
- a multi-parent `SELECT` is explicit conflict adjudication and MUST supersede all current terminal selection claims;
- a multi-parent adjudication may select one parent-selected generation or a valid descendant of one of them;
- a writer rejects a stale `SELECT` whose supersedes set is not exactly the current terminal set it is intended to replace.

## Step 4 — unique terminal selection

Compute selection nodes with out-degree zero.

```text
if terminalSelectionCount == 1:
    activeGeneration = terminal.selectedGenerationId
else:
    fail AMBIGUOUS_ACTIVE_GENERATION
```

This is the only active-generation rule.

The reader MUST NOT select by:

- last NDJSON line;
- largest/newest timestamp;
- filesystem mtime;
- lexicographically largest ID;
- deepest generation directory;
- most records;
- most complete-looking content;
- model confidence/judgment.

A later timestamp never breaks an authority conflict.

---

# 15. Conflict resolution

Two concurrent selections from one parent create two terminal claims. Neither wins.

```text
S0 -> S1 selects G1
  \-> S2 selects G2

result:
AMBIGUOUS_ACTIVE_GENERATION
active authoritative implementation material = none
```

Resolution requires one new explicit operator-approved `SELECT` whose `supersedesSelectionIds` contains **all** current terminal IDs.

The losing selection/generation and its evidence remain durable history. Conflict adjudication never deletes them.

---

# 16. Source-change and recovery concurrency

A recovery candidate is bound to the exact source generation bytes captured at proposal time.

Immediately before selection the domain writer MUST re-resolve the active generation and compare its exact byte length/digest to the candidate's recorded source snapshot.

If ordinary legitimate events were appended after the recovery snapshot, selection fails:

```text
SOURCE_CHANGED_DURING_RECOVERY
```

The candidate is not selected. Recovery must restart from a fresh snapshot.

This prevents an authority-changing recovery from silently discarding events that arrived while the candidate was being prepared.

---

# 17. Fail-closed matrix

| Condition | Required FF1 result |
| --- | --- |
| plan authority absent/ambiguous/unresolvable at bind time | `PLAN_BINDING_UNRESOLVED`; do not create ledger |
| material plan requirement lacks one explicit unique local ID | `REQUIREMENT_IDENTITY_UNRESOLVED`; do not bind |
| plan identity input changes | `NEW_PLAN_IDENTITY_REQUIRED`; create new ledger, never recovery generation |
| event references unknown requirement | `UNTRUSTED_ACTIVE_GENERATION`; no derived current state |
| unknown Implementation event type/schema in active history | `UNTRUSTED_ACTIVE_GENERATION`; fail closed |
| illegal blocker/defer/correction lifecycle | `UNTRUSTED_ACTIVE_GENERATION`; fail closed |
| duplicate complete event ID | no V1 deduplication; `OPERATOR_DECISION_REQUIRED` / no selectable hiding generation |
| complete unsupported/corrupt middle record | no V1 omission; `UNRECOVERABLE_WITHOUT_EXACT_EVIDENCE` or operator stop |
| complete semantic event would need deletion/rewrite to become valid | no V1 structural recovery; operator stop |
| missing final LF on complete domain-valid event | `APPEND_TERMINAL_LF` candidate permitted; selection still explicit |
| empty NDJSON record separator | `OMIT_EMPTY_RECORD_SEPARATOR` candidate permitted |
| incomplete terminal fragment | `OMIT_INCOMPLETE_TERMINAL_FRAGMENT` candidate permitted; selected read model `DEGRADED` until re-observed |
| recovery directory exists but selection ledger missing/corrupt | `UNTRUSTED_SELECTION_HISTORY`; no root fallback |
| two or more terminal selections | `AMBIGUOUS_ACTIVE_GENERATION`; no authoritative material |
| selection graph cycle/zero terminal due broken graph | `BROKEN_SELECTION_LINEAGE`; fail closed |
| selected generation missing predecessor | `MISSING_PREDECESSOR`; no fallback |
| selected generation lineage cycle | `BROKEN_RECOVERY_LINEAGE`; fail closed |
| generation/source/recovered digest mismatch | `DIGEST_MISMATCH`; fail closed |
| selected generation later becomes structurally/semantically corrupt | `UNTRUSTED_ACTIVE_GENERATION`; no predecessor fallback |
| unselected invalid candidate exists | candidate diagnostic only; current active selection may remain usable |
| temporary unpublished candidate exists | non-authoritative; previous active remains active |
| source changed between recovery snapshot and selection | `SOURCE_CHANGED_DURING_RECOVERY`; candidate cannot select |
| active plan authority has moved to a different PlanIdentity | old ledger is historical; no new ordinary writes under old plan |
| old-plan evidence exists for same local requirement name in new plan | no transfer; different `requirementId` by construction |
| EHA reference exists | reference only; never copied into Implementation-owned verdict |

A reader may expose corrupt ranges, candidate identities, historical prefixes and diagnostics for audit, but MUST label them non-authoritative where authority resolution failed.

---

# 18. `LedgerIntegrityCore` boundary

The shared structural core MAY provide:

```text
exact raw byte capture
sha256 digest
NDJSON framing
line / byte corruption locations
JSON syntax validation
schema hook invocation
duplicate-ID primitives
reference lexical-format primitives
generic DAG / lineage-shape checks
```

It MUST NOT provide or decide:

```text
bind this plan as project authority
invent requirement IDs
legal Implementation event transitions
whether a defer/blocker/correction is semantically valid
whether missing evidence still supports IMPLEMENTED/PASS
which Implementation generation is active
whether recovery may change plan identity
whether an EHA verdict is PASS
whether source mutation is authorized
```

The final active-generation algorithm in section 14 belongs to the Implementation-domain adapter/API even if structural graph traversal uses shared primitives.

No API named or behaving like the following is permitted:

```text
make_generation_authoritative(anyLedger)
set_current_generation(anyDomain)
repair_and_select_generic(...)
```

---

# 19. Relationship to MF2–MF5 and later freezes

## MF2 / MF3

`AcceptanceProfileSnapshotV1`, DiscoveryCompleteness and PolicyCompleteness remain separate objects owned by their accepted contracts. They may be referenced where relevant; they are not embedded as editable Implementation Ledger truth.

## MF4

Implementation ledger recovery is not automatic source repair.

`FailureSignature`, `AttemptId`, repair budgets and `REPAIR_LOOP_STALLED` belong to W9 source-repair control and do not determine Implementation recovery generation identity or selection.

A failed exact source SHA remains failed. Recovering ledger readability does not repair source or create acceptance.

## MF5

A later `RepairPacketV1` may carry a reference to an already-authorized ledger-recovery case/operation. Neither the packet nor Jinja/host presentation chooses the active Implementation generation.

## FF2 / W10

FF1 intentionally freezes recovery semantics before the generic workflow case schema.

A later `LedgerRecoveryCaseV1` may authorize/orchestrate a recovery proposal, but it MUST consume these fixed FF1 semantics:

```text
fixed PlanIdentity
fixed requirement catalog
safe-reframe V1 operation
immutable candidate generation
explicit Implementation-domain SELECT
operatorDecisionRef
unique-terminal active-generation algorithm
no predecessor fallback
```

W10 may strengthen who is permitted to issue/approve `operatorDecisionRef`; it MUST NOT move selection authority into a generic recovery layer or make generation creation equivalent to selection.

---

# 20. Required deterministic tests for W2/W4

Implementation may not claim FF1 conformance without adversarial tests covering at least:

## Plan / requirement identity

1. same plan inputs -> same `planId`;
2. changed plan blob/path/authority/repository -> different `planId`;
3. same local requirement ID under revised plan -> different `requirementId`;
4. missing/duplicate/ambiguous plan-local requirement ID -> bind fails;
5. old-plan events never attach to new-plan requirement identities.

## Event history / lifecycle

6. `PLAN_BOUND` is exactly first/once;
7. unknown requirement reference fails closed;
8. work event alone yields `IN_PROGRESS`, never `IMPLEMENTED`;
9. exact-target implementation evidence yields its state only for that exact SHA;
10. ancestor evidence on a different SHA yields `UNESTABLISHED` for current target, not inherited success;
11. local verification result remains implementation-local and exact-target bound;
12. EHA reference does not materialize a second stored verdict;
13. blocker open/resolve state machine rejects double resolve;
14. defer/resume requires exact authority refs and rejects illegal transitions;
15. evidence event invalidation removes it from derivation without deleting bytes;
16. reinstatement restores it and illegal repeated control transitions fail closed;
17. raw historical rewrite is detected/forbidden.

## Structural recovery

18. clean baseline ledger remains baseline active with no recovery subtree;
19. complete final event missing LF can recover only by appending one LF;
20. empty separator can recover only by omitting the redundant LF;
21. torn incomplete terminal fragment retains exact corruption range/digest and creates `UNKNOWN_TERMINAL_EVENT` risk;
22. invalid complete middle record cannot be silently omitted;
23. duplicate event ID cannot be deduplicated by recovery;
24. unknown complete schema cannot be omitted;
25. original damaged bytes remain byte-for-byte unchanged;
26. generation identity is stable across different timestamps/actors/tool versions;
27. candidate directory without selection does not become active;
28. partial temporary generation publication has no authority;
29. source append during recovery prevents selection with `SOURCE_CHANGED_DURING_RECOVERY`;
30. selected successor write-fences predecessor.

## Selection authority

31. one valid terminal selection chooses its generation;
32. two concurrent terminal selections yield `AMBIGUOUS_ACTIVE_GENERATION` regardless of timestamps;
33. multi-parent operator adjudication superseding all terminals resolves the conflict;
34. stale supersedes set is rejected;
35. missing predecessor/cycle/digest mismatch fails closed without predecessor fallback;
36. corrupt `selections.ndjson` fails closed without root fallback;
37. invalid unselected candidate does not poison valid current selection;
38. recovery generation whose `PLAN_BOUND`/requirement catalog differs from baseline is invalid;
39. plan revision cannot be smuggled through recovery generation selection.

## EBCA uncertainty

40. selected `UNKNOWN_TERMINAL_EVENT` generation exposes historical prefix evidence but cannot emit fresh positive current implementation/verification claim until post-selection exact-target evidence re-establishes that axis;
41. unresolvable material evidence reference never upgrades to PASS/IMPLEMENTED;
42. no aggregate SIB/release acceptance value is writable or derivable as Implementation authority.

---

# 21. MUST / MUST NOT summary

## MUST

- keep one Implementation Ledger authority per exact accepted `PlanIdentityV1`;
- use explicit plan-owned local requirement IDs and deterministic plan-scoped `RequirementIdV1`;
- bind every material event to one exact Git subject SHA;
- retain append-only event history;
- derive current execution state for an explicitly queried exact target;
- keep blocker/defer/verification axes semantically separate;
- reference EHA rather than duplicate its verdict;
- preserve plan revision as a new plan identity/ledger root;
- preserve recovery as immutable same-plan generation lineage;
- require explicit operator-approved domain selection for every authority-generation switch;
- use the unique-terminal selection algorithm;
- fail closed on ambiguous/broken selected history;
- preserve all published generations, selections and predecessor evidence;
- preserve unknown/torn intent as uncertainty;
- keep structural mechanics subordinate to domain semantics.

## MUST NOT

- use Markdown as Implementation authority;
- infer plan authority from filename/recency/model confidence;
- invent requirement IDs from prose similarity or ordinal position;
- transfer implementation/verification status across plan identities;
- transfer positive exact-target status across Git SHAs by ancestry;
- write SIB/EHA verdicts as Implementation-owned truth;
- make recovery generation creation equal authority selection;
- select by timestamp, file order in the selection ledger, mtime, depth, count or model judgment;
- fall back to a predecessor after a selected generation becomes invalid;
- rewrite/delete/compact historical authoritative events;
- deduplicate or drop complete records to obtain a prettier recovery;
- let generic LedgerIntegrityCore choose domain authority;
- let `RepairPacketV1`, Jinja, graph, report or LLM context choose authority;
- treat a plan revision as a recovery generation;
- garbage-collect published V1 recovery history.

---

# 22. Freeze closure / stop-condition audit

FF1's stop condition was:

> stop if any unresolved semantic generation/lifecycle question remains.

The following questions are now explicitly closed:

| Question | Frozen FF1 decision |
| --- | --- |
| physical durable location | `.opencode/state/implementation-ledgers/<planId>/` |
| authority owner | Implementation domain only, accepted-plan execution history only |
| plan identity | deterministic `PlanIdentityV1` over repository/path/blob/plan-authority ref |
| requirement identity | explicit plan-local ID -> plan-scoped deterministic `ireq1-*` |
| missing/ambiguous requirement identity | fail closed; no model-generated ID |
| plan revision | new `PlanIdentityV1`, new ledger root; no status transfer |
| baseline history | one LF-terminated append-only `events.ndjson` |
| event families | closed V1 set in section 8 |
| event correction lifecycle | `VALID <-> INVALIDATED` through explicit operator-adjudicated control events |
| blocker lifecycle | open once -> resolve once; recurrence gets new blocker |
| defer lifecycle | authority-backed `ACTIVE <-> DEFERRED` transitions |
| exact-target status | only same-SHA evidence establishes positive current state |
| EHA overlap | reference only; no duplicate verdict authority |
| derived status | independent work / verification / defer / blocker / trust axes; no authoritative global DONE/PASS |
| recovery scope | fixed plan identity and requirement catalog only |
| allowed V1 recovery | safe reframing only: terminal LF, empty separator, incomplete terminal fragment |
| unsupported semantic/complete-record corruption | deterministic fail-closed/operator stop; no hiding generation |
| recovery generation identity | deterministic content/lineage identity `irg1-*` |
| recovery publication | immutable candidate, atomic publication, candidate != authority |
| authority selection owner | Implementation domain `selections.ndjson` |
| selection approval | explicit non-empty `operatorDecisionRef` |
| active selection | exactly one terminal selection claim |
| concurrent selections | ambiguity; no winner by recency |
| conflict resolution | one explicit selection superseding all current terminal claims |
| selected invalid generation | fail closed; no predecessor fallback |
| source changes during recovery | candidate cannot select; restart from fresh snapshot |
| torn-fragment semantic uncertainty | `DEGRADED`; exact-target positive axes require post-selection re-observation |
| published-history retention | no V1 garbage collection |
| generic structural core | mechanics only; never semantic selection/lifecycle authority |

No Implementation-ledger generation or lifecycle choice is intentionally deferred to implementation.

The remaining RC7 questions belong to other owner domains, especially EHA V2 and W10 repair/recovery authorization schemas. They do not alter the FF1 domain-generation rules frozen here.

---

```text
FF1_STATUS:
FROZEN

UNLOCKS:
W2 Implementation Ledger
W4 Implementation Ledger recovery

DOES_NOT_UNLOCK:
W6 W10 W12 W13 W14 W15 overall-W16

CURRENT_SIB_RUNTIME_INPUT:
6621c65b868d3e279ddcbd8dee182a95c6fb29f8

FF1_DESIGN_BASE:
af0c5dcd4054cb2eef35d7661125fc939b9e3263

GENERATION_AUTHORITY_RULE:
Implementation-domain explicit selection only

PLAN_REVISION_RULE:
new PlanIdentity -> new ledger root; never recovery generation

STOP_CONDITION:
SATISFIED — no unresolved Implementation generation/lifecycle semantic question remains
```
