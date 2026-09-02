# RC7 DiscoveryCompleteness vs PolicyCompleteness Freeze

**Status:** FROZEN RC7 MICRO-CONTRACT / DESIGN AUTHORITY FOR W8  
**Session:** MF3 — DiscoveryCompleteness vs PolicyCompleteness  
**Branch:** `docs/rc7-freeze-completeness`  
**Scope:** docs-only contract freeze; no runtime implementation  

## 1. Exact inputs

This freeze is based on the following exact identities, re-resolved before the freeze was written:

```text
runtime branch:
feature/rc6-eha-brownfield-bootstrap
runtime SHA:
1de37c75251a1e0d9904cffdb82695e92e3fab23

planning branch:
docs/rc7-ledger-authority-repair-plan
planning SHA:
86218a51345fafb47d0ffec543773846a70ac76a

pinned review / antithesis:
be5d158880f649ecb568d9a505c694e87bd76e0e

frozen thesis:
1b52c7c72e5294b3a4c145d1bbbd71a1863cb218
```

The planning branch had not advanced beyond the supplied planning SHA when this freeze began, so no later planning head was substituted.

Normative/runtime evidence inspected at the exact runtime SHA:

| Source | Exact blob |
| --- | --- |
| `docs/SIB0-CAPABILITY-INVENTORY.md` | `c5c8d87d7d2dcd5f50eab3f76b323c3ca75dbb3b` |
| `docs/protected-capabilities.json` | `9258c070d1af3b5ec0706c905439643aebf929c0` |
| `docs/PROTECTED-CAPABILITY-CONTRACTS.md` | `1e14a26062dc562eef28d84b023539de1d0086a6` |
| `docs/EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md` | `232795994607b09016481846520b9c82554be5eb` |
| `pack/.opencode/skills/target-ownership-map/SKILL.md` | `0683af7936e7deb0b7b74cf13d743088c73449bb` |
| `pack/.opencode/skills/development-authority-discovery/SKILL.md` | `0d784ecbc3a2ae1784e21217a3e8cf1301d05fbe` |

Planning/design inputs inspected at the exact planning SHA:

| Source | Exact blob |
| --- | --- |
| `docs/RC7-THESIS-ANTITHESIS-SYNTHESIS.md` | `a3556ca3bd84546835a3ff66847cfb03da54fc7b` |
| `docs/RC7-IMPLEMENTATION-TRIAGE-TODO.md` | `5e352e0336343d9b4ce5196c5a8309bd0153a531` |
| frozen thesis `docs/RC7-CONSOLIDATED-DESIGN-PROPOSAL.md` | `0f46825308454d9c8d0b3d0b48a2cdcc7845e120` |
| pinned antithesis `docs/reviews/do-not-freeze-RC7.md` | `02a87228ed1b1b989c4e7dd785b0dd9acba8de9b` |

No accepted MF2 `AcceptanceProfileSnapshotV1` micro-freeze was present in the exact planning baseline or in the RC7 freeze branches resolved before this session. Therefore this document is standalone and freezes the MF2 integration point explicitly in section 10.

## 2. Existing authority preserved by this freeze

This document does not redefine the current CodeSleuth architecture.

The following existing rules remain upstream authority:

1. `SIB0-CAPABILITY-INVENTORY.md` is normative for the current architectural generation and explicitly declares the fundamental capability-class set while separately refusing to claim SIB1 implementation completeness or SIB2 integration completeness.
2. `protected-capabilities.json` is the machine-readable protected-contract registry; it is an index over accepted project evidence, not a replacement for source/docs/tests and not a discovery oracle for unknown future surfaces.
3. `PROTECTED-CAPABILITY-CONTRACTS.md` requires exact evidence and says that a source-observed consumer missing from the dependency graph makes the registry incomplete and requires correction; the graph does not override source evidence.
4. EBCA requires exact subject identity, authority before representation, bounded scope, explicit evidence, and preservation of unknown/ambiguous/truncated/unavailable evidence as uncertainty rather than PASS.
5. Development-authority discovery is derived navigation. It must expose unresolved authority rather than choose a convenient winner.
6. Target ownership mapping stops when the owner is ambiguous, duplicate authority would be created, or a new fundamental capability class would be required.
7. The RC7 synthesis already separates `DiscoveryCompleteness` from `PolicyCompleteness` and states that policy adoption creates current policy authority but does not retroactively prove preceding discovery exhaustive.

This freeze supplies the missing machine-visible value models and deterministic derivation/aggregation rules. It does not create a third completeness concept.

## 3. Normative decision

RC7 has **two independent completeness axes**:

```text
DiscoveryCompleteness
PolicyCompleteness
```

They answer different questions.

### 3.1 DiscoveryCompleteness

Question:

> For one exact target and one declared discovery universe, is the evidence sufficient to claim that the bounded discovery procedure covered that universe completely enough to identify/classify every policy-relevant capability subject within it?

This is an empirical/evidence-bound claim.

### 3.2 PolicyCompleteness

Question:

> For one declared policy scope and architecture generation, does an identified project policy authority explicitly and completely define the intended policy treatment for every subject required by that scope?

This is an authority/policy-closure claim.

### 3.3 Non-implication rule

The following implications are forbidden:

```text
DiscoveryCompleteness.COMPLETE
    !=>
PolicyCompleteness.COMPLETE

PolicyCompleteness.COMPLETE
    !=>
DiscoveryCompleteness.COMPLETE
```

A complete discovery inventory cannot create policy. A complete policy declaration cannot prove empirical discovery exhaustive.

Discovery evidence MAY reveal a policy gap and therefore prevent `PolicyCompleteness=COMPLETE` for the same policy scope. This is a **negative counterexample**, not a positive certification path.

No common authoritative field such as the following may exist:

```text
complete: true|false
isComplete: true|false
overallCompleteness: ...
```

A presentation layer may display the two values together, but it MUST preserve both labels and MUST NOT persist or expose a third authoritative combined completeness state.

## 4. Wire values

The only permitted V1 values for both axes are:

```text
UNKNOWN
PARTIAL
COMPLETE
```

`INCOMPLETE` is not a separate wire value in V1. In prose, "incomplete" means `PARTIAL` only when incompleteness is positively evidenced.

The EBCA result values `PASS`, `FAIL`, `INCONCLUSIVE`, `UNAVAILABLE`, and `NOT_APPLICABLE` are not completeness values and MUST NOT be serialized into either completeness field.

### 4.1 UNKNOWN

`UNKNOWN` means:

> The evidence/authority required to determine completeness for the declared scope is missing, invalid, conflicting, stale for the subject, or otherwise insufficient to distinguish complete from known-incomplete.

`UNKNOWN` does not mean empty, absent, false, failed, or not applicable.

### 4.2 PARTIAL

`PARTIAL` means:

> The scope and provenance are sufficiently established to know that coverage is incomplete.

Examples include an explicitly truncated discovery source, a required source known not to have been observed, an unavailable required source, a known unresolved capability classification, or an authoritative policy with one or more known uncovered subjects.

### 4.3 COMPLETE

`COMPLETE` means:

> All axis-specific closure requirements in this document are positively supported for the exact declared scope and subject/policy identity, with no unresolved blocker for that axis.

`COMPLETE` is terminal only for the immutable evaluation tuple to which it is bound. It does not transfer to a different Git SHA, architecture generation, policy identity, universe definition, or scope.

A changed target/policy/universe creates a new assessment. It does not mutate the old one forward by ancestry or narrative similarity.

## 5. Machine-visible V1 models

These are separate wire models. Their similar field shapes do not create a shared semantic superclass.

Reference strings below are opaque stable references owned by the corresponding domain. They MUST be non-empty and resolvable to exact authority/evidence. This freeze intentionally does not create another universal reference database or URI scheme.

### 5.1 `DiscoveryCompletenessV1`

```text
DiscoveryCompletenessV1 {
  schemaVersion: 1
  value: UNKNOWN | PARTIAL | COMPLETE

  scopeId: string
  targetSha: full immutable Git commit SHA
  universeRef: string | null

  requiredSourceIds: string[]
  sourceCoverage: DiscoverySourceCoverageV1[]

  unresolvedClassificationRefs: string[]
  limitationRefs: string[]

  authorityRefs: string[]
  evidenceRefs: string[]
}

DiscoverySourceCoverageV1 {
  sourceId: string
  outcome:
    COVERED
    | TRUNCATED
    | UNAVAILABLE
    | NOT_OBSERVED
    | CONFLICTING
  evidenceRefs: string[]
}
```

Constraints:

1. `scopeId` and `targetSha` are mandatory for every value.
2. `universeRef` is mandatory for `PARTIAL` and `COMPLETE`.
3. `requiredSourceIds` is the machine-visible source set declared by the referenced discovery universe for this scope. It MUST be checked against that authority, not accepted merely because the assessment listed it.
4. Every `requiredSourceId` MUST have exactly one `sourceCoverage` entry.
5. Additional source entries not present in the authoritative universe are allowed as supplementary evidence but do not satisfy a missing required source.
6. `COVERED` requires non-empty exact evidence references.
7. `TRUNCATED`, `UNAVAILABLE`, and `NOT_OBSERVED` require evidence describing the limitation/failed availability/known omission.
8. `CONFLICTING` requires references to the conflicting evidence.
9. A discovered runtime surface not present in `protected-capabilities.json` MUST remain visible as a discovery/registry mismatch. It MUST NOT be silently dropped merely to preserve the frozen registry view.
10. A registry mismatch does not by itself prove discovery incomplete if discovery fully observed and classified the surface. It is separately a registry/architecture/policy-conformance issue.

### 5.2 `PolicyCompletenessV1`

```text
PolicyCompletenessV1 {
  schemaVersion: 1
  value: UNKNOWN | PARTIAL | COMPLETE

  scopeId: string
  architectureGenerationId: string

  policyAuthorityRefs: string[]
  policyIdentityRefs: string[]
  policyClosureClaimRef: string | null

  requiredSubjectRefs: string[]
  coveredSubjectRefs: string[]
  uncoveredSubjectRefs: string[]
  conflictRefs: string[]

  limitationRefs: string[]
  evidenceRefs: string[]
}
```

Constraints:

1. `scopeId` and `architectureGenerationId` are mandatory for every value.
2. `policyAuthorityRefs` and `policyIdentityRefs` are mandatory for `PARTIAL` and `COMPLETE`.
3. `requiredSubjectRefs` MUST be derived from or explicitly bound by the named policy authority. A discovery result may propose or expose a subject; discovery alone MUST NOT insert that subject into authoritative policy.
4. `coveredSubjectRefs` MUST be a subset of `requiredSubjectRefs` unless an explicit policy adoption/update creates a new policy identity containing the new subject.
5. `uncoveredSubjectRefs` identifies known subjects required by the policy scope but not yet given complete authoritative policy treatment.
6. `conflictRefs` identifies incompatible policy authorities/obligations/dispositions. Conflicts are never averaged or resolved by recency alone.
7. `policyClosureClaimRef` is mandatory for `COMPLETE` and MUST resolve to an explicit authority-backed statement that the policy scope is closed/complete for the named architecture generation.
8. Counting rules for known subjects or observing that every currently listed subject has some policy text MUST NOT substitute for `policyClosureClaimRef`.
9. Policy granularity is part of the scope. If the accepted policy is capability-class-level, individual runtime surfaces may be covered by a class only when their class mapping is established. A mapping ambiguity is not silently resolved by the completeness model.
10. `NOT_APPLICABLE` remains obligation-level only under existing RC7 synthesis rules. It cannot be used as a policy-completeness shortcut for a missing subject or unavailable evidence.

## 6. Deterministic derivation

A stored `value` is not trusted merely because it is present. A validator MUST derive the safe value from the axis-specific inputs and require equality with the stored value.

### 6.1 Discovery derivation

For a valid `DiscoveryCompletenessV1`:

```text
if scopeId or targetSha is missing/invalid:
    UNKNOWN

else if universeRef is missing/unresolvable:
    UNKNOWN

else if requiredSourceIds cannot be validated against universeRef:
    UNKNOWN

else if any required source has no sourceCoverage entry:
    UNKNOWN

else if duplicate required source entries disagree:
    UNKNOWN

else if any required source outcome == CONFLICTING:
    UNKNOWN

else if any required source outcome in
        {TRUNCATED, UNAVAILABLE, NOT_OBSERVED}:
    PARTIAL

else if unresolvedClassificationRefs is non-empty:
    PARTIAL

else if every required source outcome == COVERED
        and every COVERED entry has exact evidence
        and no hidden truncation/unavailability is observed:
    COMPLETE

else:
    UNKNOWN
```

Additional rules:

- A declared empty discovery universe is not vacuously complete. `COMPLETE` is allowed only if the `universeRef` explicitly and authoritatively proves that the scope intentionally has zero required sources.
- If exact evidence reveals truncation/unavailability that the object failed to report, the object is semantically invalid and cannot support `COMPLETE`.
- A new target SHA starts as a new assessment. An ancestor's `COMPLETE` is historical context only.

### 6.2 Policy derivation

For a valid `PolicyCompletenessV1`:

```text
if scopeId or architectureGenerationId is missing/invalid:
    UNKNOWN

else if policyAuthorityRefs or policyIdentityRefs are missing/unresolvable:
    UNKNOWN

else if requiredSubjectRefs cannot be derived from/bound to the policy authority:
    UNKNOWN

else if conflictRefs is non-empty:
    UNKNOWN

else if the policy explicitly declares limited/partial coverage:
    PARTIAL

else if uncoveredSubjectRefs is non-empty:
    PARTIAL

else if any requiredSubjectRef lacks authoritative policy treatment:
    PARTIAL

else if policyClosureClaimRef is missing/unresolvable:
    UNKNOWN

else if policyClosureClaimRef does not explicitly close the declared scope:
    UNKNOWN

else if every required subject has authority-backed policy treatment
        and the closure claim is valid for the architecture generation:
    COMPLETE

else:
    UNKNOWN
```

Additional rules:

- `PolicyCompleteness` may move from `UNKNOWN`/`PARTIAL` to `COMPLETE` only because authoritative policy evidence changed or previously missing authoritative policy evidence became available.
- Discovery evidence alone MUST NOT perform that promotion.
- Explicit project adoption may create a new complete policy identity even when preceding discovery remains `PARTIAL`; the discovery record is not rewritten.
- A maintainer comment, model conclusion, report, graph, or renderer output is not a policy closure claim unless the existing project authority process explicitly makes it one.

## 7. Evidence needed to move between values

The models are immutable assessments bound to exact identities. "Move" below means a new/recomputed assessment after additional valid evidence, not in-place mutation of a frozen snapshot.

### DiscoveryCompleteness

| From | To | Required evidence |
| --- | --- | --- |
| `UNKNOWN` | `PARTIAL` | valid scope/universe plus positive evidence of at least one known coverage limitation (`TRUNCATED`, `UNAVAILABLE`, `NOT_OBSERVED`, or unresolved classification) |
| `UNKNOWN` | `COMPLETE` | valid universe definition plus exact `COVERED` evidence for every required source and no unresolved classification/gap |
| `PARTIAL` | `COMPLETE` | new exact evidence closes every previously recorded coverage/classification gap for the same immutable target/universe/scope |
| `COMPLETE` | `UNKNOWN/PARTIAL` | never mutate the original assessment; invalidate its provenance if corrupt, or create a new assessment for changed target/universe/evidence state |

### PolicyCompleteness

| From | To | Required evidence |
| --- | --- | --- |
| `UNKNOWN` | `PARTIAL` | identified policy authority plus positive evidence that the declared policy scope is known incomplete |
| `UNKNOWN` | `COMPLETE` | exact policy identity, explicit closure claim, and authority-backed policy treatment for every required subject |
| `PARTIAL` | `COMPLETE` | accepted policy update/adoption with a new or validated policy identity that closes every known gap and explicitly closes the scope |
| `COMPLETE` | `UNKNOWN/PARTIAL` | never mutate the original policy assessment; invalidate bad provenance or assess a new policy identity/architecture generation |

## 8. Aggregation and mixed sub-scopes

Aggregation is **axis-local**. `DiscoveryCompleteness` values aggregate only with other `DiscoveryCompleteness` values. `PolicyCompleteness` values aggregate only with other `PolicyCompleteness` values.

No algorithm may aggregate one discovery child and one policy child into a shared completeness result.

### 8.1 Exhaustive-scope precondition

A parent completeness value may be derived from child scopes only when exact authority/evidence proves that the child set is an exhaustive coverage of the parent scope.

Call that evidence `scopeClosureRef` in the aggregation operation. It is not a third completeness value and need not be persisted inside either axis object if the owning domain already has an equivalent exact scope/partition authority.

Deterministic parent aggregation:

```text
aggregate(axis, parentScope, children, scopeClosureRef):

  if scopeClosureRef is missing, invalid, conflicting,
     or does not establish exhaustive child coverage of parentScope:
      UNKNOWN

  if children is empty:
      COMPLETE only if scopeClosureRef explicitly proves
      that parentScope is intentionally empty;
      otherwise UNKNOWN

  if any child has a different axis:
      ERROR AXIS_CONFLATION

  if any child is bound to an incompatible target/policy generation/scope:
      UNKNOWN

  if any child.value == UNKNOWN:
      UNKNOWN

  if any child.value == PARTIAL:
      PARTIAL

  if every child.value == COMPLETE:
      COMPLETE

  otherwise:
      UNKNOWN
```

Overlapping children are not assumed to form an exhaustive partition. Unless `scopeClosureRef` explicitly defines valid overlap semantics, overlap makes aggregation `UNKNOWN`.

### 8.2 Why UNKNOWN dominates PARTIAL in mixed children

For `COMPLETE + PARTIAL`, the parent is known incomplete, so the result is `PARTIAL`.

For `COMPLETE + UNKNOWN` or `PARTIAL + UNKNOWN`, the parent cannot be honestly characterized as known incomplete versus potentially complete because one required sub-scope has uncharacterized evidence/authority. The aggregate is therefore `UNKNOWN`; the known child-level `PARTIAL` remains visible in child data.

This is deliberately fail-closed and preserves EBCA's rule that unknown remains unknown.

## 9. Relationship with SIB0 inventory and protected capability registry

### 9.1 SIB0 inventory

The current `SIB0-CAPABILITY-INVENTORY.md` is an explicit policy statement for the current CodeSleuth architecture generation:

- it declares the fundamental capability-class inventory normative;
- it says maintainers designate that inventory as the complete fundamental capability-class set for that architecture generation;
- it separately refuses to claim SIB1 implementation completeness or SIB2 integration completeness.

Therefore, for the exact **capability-class policy scope** represented by that accepted inventory, the inventory can be valid evidence toward `PolicyCompleteness=COMPLETE` when its policy identity/authority requirements are satisfied.

It is not evidence that repository discovery was exhaustive and does not set `DiscoveryCompleteness`.

### 9.2 Protected capability registry

`protected-capabilities.json` is authoritative for its own contract records, statuses, dependency metadata, and forbidden regressions. It is also a mandatory reconciliation source for CodeSleuth capability discovery where the protected-capability scope applies.

However:

```text
registry enumerates known/protected policy objects
!=
registry proves no undiscovered runtime surface exists
```

Consequences:

1. Registry membership MUST NOT set `DiscoveryCompleteness=COMPLETE` by itself.
2. Discovery MUST NOT silently discard an observed surface because it is absent from the registry.
3. If discovery identifies a consumer/path/capability relationship missing from the registry, that mismatch is surfaced for registry/architecture adjudication.
4. A fully observed mismatch may coexist with `DiscoveryCompleteness=COMPLETE`; completeness means discovery coverage, not repository conformance to the frozen architecture.
5. If the mismatch creates a policy-relevant subject that the declared policy scope is supposed to cover but for which no authoritative policy treatment exists, that counterexample prevents `PolicyCompleteness=COMPLETE` for that scope until authority adjudicates it.
6. If the discovered surface maps cleanly to an already-declared capability class and the accepted policy is class-level, no new per-surface policy is invented merely because discovery found another population instance.

## 10. `AcceptanceProfileSnapshotV1` integration point

MF2 was not accepted/merged into the planning baseline at this session, so this freeze does not pretend to import a nonexistent final MF2 schema.

The future accepted `AcceptanceProfileSnapshotV1` MUST nevertheless integrate these exact semantic fields:

```text
AcceptanceProfileSnapshotV1 {
  ...
  discoveryCompleteness: DiscoveryCompletenessV1
  policyCompleteness: PolicyCompletenessV1
  ...
}
```

Integration obligations:

1. Both fields are mandatory for newly compiled RC7 snapshots.
2. The two fields remain separately addressable and machine-visible.
3. A snapshot MUST NOT add an authoritative common `complete`/`overallCompleteness` boolean derived from them.
4. The semantic value, scope identity, and authority/evidence provenance of both completeness assessments MUST be covered by the snapshot's semantic identity/digest once MF2 freezes canonical digest inputs. Volatile presentation timestamps, if any, are not made semantic merely by this requirement.
5. If a change to either completeness assessment would not change the snapshot's semantic identity, the MF2 integration is invalid because two materially different acceptance configurations would share one identity.
6. Claim-level policy decides which axis is required for a particular SIB/EHA claim. The implementation MUST NOT invent a global `AND`, `OR`, or precedence rule between the two axes.
7. If the claim-level policy does not specify how a required completeness precondition is satisfied, the consumer fails closed rather than choosing the more favorable axis.
8. Legacy snapshots/records with no axis-specific completeness fields remain readable for historical provenance but are interpreted by RC7 completeness-aware consumers as:

```text
DiscoveryCompleteness = UNKNOWN
PolicyCompleteness    = UNKNOWN
```

unless the owning domain re-evaluates them from exact axis-specific evidence. A legacy `complete=true` field MUST NOT be imported as either axis.

## 11. Fail-closed and error behavior

The following conditions are normative errors/stop conditions:

| Code | Condition | Safe behavior |
| --- | --- | --- |
| `COMPLETENESS_SCHEMA_INVALID` | unknown schema version, enum, missing mandatory structural field | assessment cannot support acceptance; treat completeness as unknown to downstream logic |
| `COMPLETENESS_VALUE_MISMATCH` | stored `value` differs from deterministic derivation | reject the asserted value; do not rewrite source bytes |
| `COMPLETENESS_SCOPE_MISMATCH` | evidence/child assessment belongs to another target, architecture generation, or incompatible scope | no transfer; `UNKNOWN` for requested aggregate/claim |
| `DISCOVERY_UNIVERSE_UNPROVEN` | discovery universe or required source set cannot be validated | `DiscoveryCompleteness=UNKNOWN` |
| `DISCOVERY_HIDDEN_LIMITATION` | exact evidence shows truncation/unavailability omitted by the assessment | asserted `COMPLETE` is invalid; no PASS based on it |
| `POLICY_AUTHORITY_UNPROVEN` | no resolvable policy authority/identity | `PolicyCompleteness=UNKNOWN` |
| `POLICY_CLOSURE_UNPROVEN` | known policies exist but no authority-backed closure statement for the claimed scope | `PolicyCompleteness=UNKNOWN` unless evidence positively proves partial coverage |
| `POLICY_COVERAGE_GAP` | a required policy subject is known uncovered | `PolicyCompleteness=PARTIAL` |
| `COMPLETENESS_PARTITION_UNPROVEN` | child list is not proved exhaustive for parent | parent aggregate `UNKNOWN` |
| `COMPLETENESS_AXIS_CONFLATION` | consumer tries to aggregate/substitute discovery and policy values | hard validation error; no combined value |

Consumers MAY expose the safely re-derived `UNKNOWN`/`PARTIAL` value for diagnostics. They MUST NOT silently edit the durable source that contained the invalid assertion.

## 12. MUST / MUST NOT

### MUST

- keep `DiscoveryCompleteness` and `PolicyCompleteness` as separate machine-visible fields;
- bind discovery completeness to exact target SHA, scope, universe, and evidence;
- bind policy completeness to exact policy authority/identity, architecture generation, scope, and closure evidence;
- preserve explicit truncation, unavailability, conflicts, limitations, and unresolved classifications;
- require positive closure evidence for `COMPLETE`;
- fail closed on missing/ambiguous provenance;
- aggregate only within one axis and only over a proven exhaustive parent scope;
- retain axis-specific provenance in snapshots and derived views;
- allow policy adoption to create policy completeness without rewriting historical discovery completeness;
- allow discovery evidence to expose policy gaps without granting discovery the authority to repair/adopt policy.

### MUST NOT

- create `complete: true/false`, `overallCompleteness`, or an equivalent authoritative combined state;
- infer policy completeness from a complete runtime inventory;
- infer discovery completeness from a complete policy declaration or protected registry;
- treat registry enumeration as an exhaustive discovery oracle;
- treat `UNKNOWN` as empty, absent, false, or PASS;
- treat `UNAVAILABLE`, `INCONCLUSIVE`, or `NOT_APPLICABLE` as aliases for a completeness wire value;
- upgrade `PARTIAL`/`UNKNOWN` because a human/model accepts the limitation without creating/adopting an explicit policy identity;
- transfer `COMPLETE` through Git ancestry, branch movement, policy version change, or architecture-generation change;
- infer parent `COMPLETE` from "all known children complete" without exhaustive-scope evidence;
- let a renderer/report/graph become completeness authority;
- silently mutate protected-capability registry or SIB0 inventory during completeness evaluation.

## 13. Adversarial examples

### A. Full discovery, no policy closure

```text
all declared runtime discovery sources = COVERED
no classification gaps
no policy authority/closure claim

DiscoveryCompleteness = COMPLETE
PolicyCompleteness    = UNKNOWN
```

Forbidden conclusion: `policy complete because inventory complete`.

### B. Truncated discovery, explicit adopted architecture policy

```text
one required discovery source = TRUNCATED
project authority explicitly adopts a complete capability-class policy

DiscoveryCompleteness = PARTIAL
PolicyCompleteness    = COMPLETE
```

Adoption does not rewrite discovery history or make the truncated source exhaustive.

### C. Hidden truncation

Stored object says:

```text
DiscoveryCompleteness = COMPLETE
```

but a referenced source report records truncation.

Result:

```text
COMPLETENESS_VALUE_MISMATCH
DISCOVERY_HIDDEN_LIMITATION
```

The stored `COMPLETE` cannot support acceptance.

### D. All known children complete, parent partition unknown

```text
child A = COMPLETE
child B = COMPLETE
scopeClosureRef = missing
```

Parent result:

```text
UNKNOWN
```

"All known children" is not an exhaustive-universe proof.

### E. Mixed known-incomplete children

```text
child A = COMPLETE
child B = PARTIAL
valid exhaustive scope closure
```

Parent result:

```text
PARTIAL
```

### F. Mixed unknown child

```text
child A = PARTIAL
child B = UNKNOWN
valid exhaustive scope closure
```

Parent result:

```text
UNKNOWN
```

The child-level `PARTIAL` remains visible, but the parent cannot be honestly characterized as known-incomplete versus uncharacterized overall.

### G. Discovery finds a new surface inside an existing capability class

Discovery covers the universe completely and finds one additional command population that maps unambiguously to `CC-PACK`.

Possible result:

```text
DiscoveryCompleteness = COMPLETE
PolicyCompleteness    = COMPLETE
```

when class-level policy is explicitly complete. The new population does not require inventing a new policy subject merely because it was newly observed.

### H. Discovery finds an apparent new fundamental capability class

Discovery may still be empirically complete for its universe, but the repository now contradicts the frozen SIB0 architecture unless authority adjudicates the new class.

```text
DiscoveryCompleteness = COMPLETE   # possible
PolicyCompleteness    = COMPLETE   # possible for the old intended class inventory
architecture/policy-conformance claim = FAIL / REOPEN REQUIRED
```

Completeness is not conformance. Neither axis is allowed to hide the architecture contradiction.

### I. Maintainer optimism without adopted policy

A comment says "this looks complete" but there is no project-native policy authority record/adoption.

```text
PolicyCompleteness != COMPLETE
```

Human authority can create policy only through the project's accepted authority process; informal optimism is not retroactive evidence.

### J. Legacy boolean migration

Legacy data contains:

```text
complete: true
```

and no axis-specific evidence.

RC7 interpretation:

```text
DiscoveryCompleteness = UNKNOWN
PolicyCompleteness    = UNKNOWN
```

### K. Exact-target mismatch

Discovery evidence is complete for SHA `A`; snapshot target is SHA `B`.

Result:

```text
COMPLETENESS_SCOPE_MISMATCH
DiscoveryCompleteness for B = UNKNOWN until re-evaluated
```

Ancestry is context, not completeness transfer.

### L. NOT_APPLICABLE as an evidence escape hatch

A required discovery source is unavailable and an implementation attempts to mark it `NOT_APPLICABLE` to reach completeness.

Rejected. Discovery source outcome remains `UNAVAILABLE`, producing `DiscoveryCompleteness=PARTIAL` when the unavailability is positively evidenced. `NOT_APPLICABLE` is not a completeness/source-coverage bypass.

## 14. Compatibility obligations

1. Existing SIB0 capability-class inventory remains unchanged.
2. Existing protected-capability registry remains unchanged and remains authoritative only for the facts it already owns.
3. Existing EBCA result vocabulary remains unchanged.
4. Existing EHA/finding ledgers are not modified by this freeze.
5. Existing discovery/ownership tools remain derived evidence/navigation; this freeze does not promote them to policy authority.
6. Historical records without these axes remain readable but cannot be silently upgraded to V1 completeness.
7. Any later MF2 snapshot freeze must incorporate this contract without collapsing the axes or weakening the digest/identity obligations in section 10.
8. Any later W6 EHA V2 or W15 epistemics work must consume these axis values as scoped evidence/policy metadata, not redefine them locally.
9. A future UI/renderer may provide convenience labels but must preserve the two underlying values and clearly mark any presentation summary as non-authoritative.

## 15. Explicit non-goals

This freeze does **not**:

- define or implement the runtime discovery engine;
- enumerate every discovery source for every target repository;
- redefine the current SIB0 class inventory;
- change the protected-capability registry schema;
- define SIB1/SIB2 acceptance completion algorithms;
- define EHA V2 event schema or verdict aggregation;
- define the final `AcceptanceProfileSnapshotV1` canonical digest serialization (MF2 owns that), except that both completeness assessments and their semantic provenance must be digest-covered;
- create a generic claim database, completeness ledger, or policy registry;
- define policy adoption/adjudication workflow beyond requiring an existing accepted authority process;
- equate completeness with trust, confidence, test PASS, architecture conformance, implementation completeness, or integration completeness;
- add production TypeScript/Python or tests in this session.

## 16. Downstream work unlocked

This freeze resolves the semantic choices that previously blocked:

```text
W8 discovery completeness vs policy completeness
```

W8 implementation may now add the two machine-visible value models, validators/aggregation, and snapshot integration once the corresponding implementation branch is opened from the current executable runtime stream and MF2's snapshot container/digest contract is available.

This freeze does not itself authorize W6 EHA V2 or other final-freeze-blocked workstreams.

## 17. Unresolved items

There are **no unresolved W8 semantic decisions** within the scope of MF3.

The only pending dependency is mechanical integration with the future accepted MF2 `AcceptanceProfileSnapshotV1` container/canonical digest contract. MF2 is not permitted to choose different completeness semantics; it must consume the two models and obligations frozen here.

If an MF2 freeze already exists elsewhere when integration begins, any conflict must be surfaced as a design conflict and adjudicated. It MUST NOT be reconciled by silently collapsing or renaming the two axes.

---

# FREEZE STATUS

```text
FROZEN
```

# UNLOCKS

```text
W8 discovery completeness vs policy completeness
```

# CONSTRAINT

```text
discovery completeness MUST NOT certify policy completeness
```
