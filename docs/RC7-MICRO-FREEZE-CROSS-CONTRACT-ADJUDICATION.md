# RC7 Micro-Freeze Cross-Contract Adjudication

**Status:** NORMATIVE RC7 MICRO-FREEZE INTEGRATION DECISION  
**Scope:** resolves cross-contract collisions among MF1–MF5 without reopening their settled domain semantics  
**Authority:** this document has precedence only for the explicit conflicts and bindings listed below; otherwise the source freeze documents remain normative.

## 1. Exact integrated inputs

The following micro-freeze heads are integrated as design authorities:

| Session | Branch | Exact head | Disposition |
| --- | --- | --- | --- |
| MF1 Finding recovery | `docs/rc7-freeze-finding-recovery` | `c761e1ebacfebad5a4779da69d9d3a9d7a1d8a51` | ACCEPTED |
| MF2 Acceptance profile snapshot | `docs/rc7-freeze-acceptance-profile` | `d751b03c52168d59a23a445652cf042aa0e0c239` | ACCEPTED |
| MF3 completeness | `docs/rc7-freeze-completeness` | `b1e697e7cf8c9409538a20f9449b8ddd8780352e` | ACCEPTED WITH THIS ADJUDICATION |
| MF4 repair termination | `docs/rc7-freeze-repair-termination` | `dc3191c11db669e416a3d86af69e7cfae95365af` | ACCEPTED WITH BINDING CLARIFICATION |
| MF5 repair packet / host profile | `docs/rc7-freeze-repair-packet` | `c9fa42dc032a37509534395f577d7069ae75eb56` | ACCEPTED |

Runtime evidence baseline remains:

`feature/rc6-eha-brownfield-bootstrap @ 1de37c75251a1e0d9904cffdb82695e92e3fab23`

The source planning baseline used by all five sessions remains:

`docs/rc7-ledger-authority-repair-plan @ 86218a51345fafb47d0ffec543773846a70ac76a`

No runtime, SIB, RC, release or EHA durable-state ref is moved or reinterpreted by this integration decision.

## 2. MF2 vs MF3 conflict: adjudicated in favor of immutable snapshot input

MF2 freezes `AcceptanceProfileSnapshotV1` as immutable campaign/policy input and explicitly forbids evaluated fields such as:

```text
discoveryCompleteness
policyCompleteness
completenessSupportable
```

inside the snapshot.

MF3 section 10, written independently before the accepted MF2 result was visible to that session, requires the future snapshot to embed:

```text
discoveryCompleteness: DiscoveryCompletenessV1
policyCompleteness: PolicyCompletenessV1
```

These requirements cannot both hold. MF3 itself requires explicit adjudication rather than silent reconciliation if MF2 later conflicts.

### 2.1 Normative resolution

MF2 wins on snapshot ownership and immutability.

`AcceptanceProfileSnapshotV1` MUST NOT contain evaluated `DiscoveryCompletenessV1` or `PolicyCompletenessV1` objects.

The conflicting MF3 section-10 requirement to embed those assessments in `AcceptanceProfileSnapshotV1` is therefore **SUPERSEDED** by this document.

The following separation is normative:

```text
ProjectSibProfileV1
    -> compile
AcceptanceProfileSnapshotV1
    = immutable policy / campaign input

DiscoveryCompletenessV1
PolicyCompletenessV1
    = evidence-derived assessments
    = external to the immutable snapshot
    = may bind to the snapshot by exact semantic-digest reference
```

A completeness assessment does not mutate, recompile, replace or version-forward an already started campaign snapshot.

### 2.2 Binding rule

Whenever a `DiscoveryCompletenessV1` or `PolicyCompletenessV1` result is used as evidence in an acceptance/EHA context governed by an `AcceptanceProfileSnapshotV1`, the consuming record MUST preserve an exact binding to:

```text
AcceptanceProfileSnapshotV1.semanticDigest
```

The completeness object remains owned by W8. The physical EHA V2 event/storage representation carrying:

- the snapshot semantic digest;
- completeness object/reference identity;
- any content digest required for durable replay;

belongs to W6 final freeze and MUST NOT be invented by W8 implementation.

### 2.3 Digest consequence

MF3 assessments are **not** members of the MF2 snapshot `semanticDigest` preimage.

MF2 snapshot digest covers policy/campaign input only.

Completeness evidence may have its own exact evidence/content identity as defined by its producer/consumer contract, but that identity MUST NOT be folded retrospectively into an existing `AcceptanceProfileSnapshotV1.semanticDigest`.

### 2.4 Preserved MF3 semantics

This adjudication changes no other MF3 rule.

In particular, the following remain frozen:

- `DiscoveryCompleteness` and `PolicyCompleteness` are separate axes;
- V1 wire values remain `UNKNOWN | PARTIAL | COMPLETE`;
- neither axis positively certifies the other;
- discovery may expose a negative policy counterexample without creating policy authority;
- unknown/incomplete evidence remains non-PASS and non-complete;
- no combined authoritative `complete: true|false` field is created.

MF3 is therefore accepted for W8 after this explicit integration correction.

## 3. MF4 to MF2 digest binding

MF4 uses the local field name:

```text
profileSnapshotDigest
```

as an opaque fixed identity for one automatic-repair loop.

MF2 now provides the exact accepted snapshot digest field and lexical contract.

The normative binding is:

```text
MF4.profileSnapshotDigest
    := AcceptanceProfileSnapshotV1.semanticDigest
```

The value MUST be copied exactly, including the MF2 `DigestV1` lexical form:

```text
sha256:<64 lowercase hexadecimal characters>
```

It MUST NOT refer to or be substituted with:

- `profileDigest`;
- `profileBodyDigest`;
- repository tree digest;
- campaign ID;
- run ID;
- a newly computed digest over a subset of snapshot fields.

Future implementation MAY rename the local field to `profileSnapshotSemanticDigest` for clarity, but if it retains `profileSnapshotDigest`, the value semantics above are mandatory.

Changing the snapshot semantic digest terminates comparability inside the same bounded repair loop exactly as MF4 already requires.

## 4. MF1 and LedgerIntegrityCore boundary

MF1 is accepted unchanged.

Its `finding-recovery/selections.ndjson` is Finding-domain control authority. Structural framing/schema/digest/duplicate checks may be delegated to `LedgerIntegrityCore`, but active Finding-generation selection, recovery admissibility and Finding lifecycle derivation remain Finding-domain semantics.

This integration MUST NOT be interpreted as permission to move MF1 generation selection into W3.

## 5. MF5 and repair authority boundary

MF5 is accepted unchanged.

`RepairPacketV1` and `HostExecutionProfileV1` only narrow an already-authorized repair. They do not grant source-mutation authority and do not replace the later W10 distinction between `EhaRepairCase` and `LedgerRecoveryCase`.

Jinja remains derived presentation and MUST NOT become executable command authority.

## 6. Effective micro-freeze frontier

After this adjudication the effective RC7 micro-freeze state is:

```text
MF1 FROZEN -> unlocks W5
MF2 FROZEN -> unlocks W7; prerequisite for W6/W8/W9
MF3 FROZEN AS ADJUDICATED -> unlocks W8
MF4 FROZEN WITH MF2 DIGEST BINDING -> unlocks W9
MF5 FROZEN -> unlocks W11
```

No unresolved semantic conflict among MF1–MF5 remains inside the scopes frozen above.

This does not authorize W2, W4, W6, W10, W12, W13, W14, W15 or overall W16 implementation before their respective final-freeze dependencies are satisfied.

## 7. Next freeze dependency

The next design session may proceed to:

```text
FF1 — Implementation Ledger + Recovery Authority Freeze
```

FF2 must consume the accepted MF2/MF4 bindings and the resulting FF1 recovery terminology rather than re-inventing them.

---

```text
MICRO_FREEZE_INTEGRATION_STATUS:
ACCEPTED

EFFECTIVE_ACCEPTED_FREEZES:
MF1 MF2 MF3 MF4 MF5

SUPERSEDES:
MF3 section 10 only where it requires completeness assessments inside AcceptanceProfileSnapshotV1
MF3 statements requiring those assessments to participate in AcceptanceProfileSnapshotV1.semanticDigest

BINDS:
MF4.profileSnapshotDigest = AcceptanceProfileSnapshotV1.semanticDigest
```
