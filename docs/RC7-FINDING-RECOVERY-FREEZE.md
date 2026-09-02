# RC7 Finding Ledger Recovery Generation Freeze

**Status:** NORMATIVE MICRO-FREEZE FOR W5  
**Scope:** Finding-domain structural recovery generations only  
**Branch:** `docs/rc7-freeze-finding-recovery`  
**Does not authorize runtime implementation by itself:** this document freezes the contract that a later W5 implementation must satisfy.

## 1. Exact inputs

This freeze was produced against the following re-resolved repository identities:

```text
repository:
DassaultFalconKing/CodeSleuth

runtime branch:
feature/rc6-eha-brownfield-bootstrap
runtime HEAD:
1de37c75251a1e0d9904cffdb82695e92e3fab23

planning branch:
docs/rc7-ledger-authority-repair-plan
planning HEAD:
86218a51345fafb47d0ffec543773846a70ac76a

pinned review / antithesis:
be5d158880f649ecb568d9a505c694e87bd76e0e
review document blob:
02a87228ed1b1b989c4e7dd785b0dd9acba8de9b

frozen thesis:
1b52c7c72e5294b3a4c145d1bbbd71a1863cb218
thesis document blob:
0f46825308454d9c8d0b3d0b48a2cdcc7845e120
```

The planning branch still resolves to the supplied planning baseline, so no later planning commit needed substitution or adjudication.

Normative/current inputs preserved by this freeze include:

- `docs/DURABLE-EVIDENCE-STORE.md` at runtime blob `bc5e806865226e93f4a5873870401a7bf43c94ea`;
- `docs/protected-capabilities.json` at runtime blob `9258c070d1af3b5ec0706c905439643aebf929c0`;
- `pack/.opencode/tools/review_state.ts` at runtime blob `0131bc9e286a8a28a4e72c9c150efc19dae2ed6f`;
- `pack/.opencode/plugins/review-compaction.ts` at runtime blob `f52441953ea6b9adc3f355878b77444c06c7fdbc`;
- `pack/.opencode/skills/findings-ledger-update/SKILL.md` at runtime blob `a48ef32192ede8cdf8360f56aa9392c4d20f526e`;
- `tests/review_state_amendments.ts` at runtime blob `2fa00326d7b68b986fb233fc7f3f41058bdd80cb`;
- `tests/review_state_smoke.ts` at runtime blob `5dd1291e8435cf61a8bcade8c5058cf4b9228a13`;
- `tests/test_durable_evidence_store_contract.py` at runtime blob `e298273f45f6489b7e7f84906924aaf712f1835a`;
- `docs/EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md` at planning blob `232795994607b09016481846520b9c82554be5eb`;
- `docs/RC7-FEATURE-PLAN.md` at planning blob `ddac1c4a34b0c57f7c6ff668cc7e3d99a56f03c5`;
- `docs/RC7-THESIS-ANTITHESIS-SYNTHESIS.md` at planning blob `a3556ca3bd84546835a3ff66847cfb03da54fc7b`;
- `docs/RC7-IMPLEMENTATION-TRIAGE-TODO.md` at planning blob `5e352e0336343d9b4ce5196c5a8309bd0153a531`.

The frozen thesis and pinned review are design inputs, not implementation authority. Existing accepted Finding/EBCA/SIB/EHA contracts remain stronger where this micro-freeze does not explicitly add Finding-recovery semantics.

---

## 2. Preserved authority model

This freeze does not create a generic ledger authority.

The existing Finding authority remains one Finding-domain authority inside one review directory:

```text
.opencode/state/reviews/<reviewId>/
    findings.ndjson
    findings-amendments.ndjson
```

`findings.ndjson` owns original recorded finding facts. `findings-amendments.ndjson` is its sibling append-only lifecycle/correction ledger. They are not two competing databases.

RC7 Finding recovery extends that same authority with lineage metadata and recovered generations under the same review directory. It does not create a new persistence plane.

The authority split is normative:

```text
LedgerIntegrityCore
    structural framing / digest / corruption mechanics only
            |
            v
Finding-domain recovery
    admissibility
    generation lineage
    active-generation selection
    Finding lifecycle derivation
```

`LedgerIntegrityCore` MUST NOT choose an active Finding generation, decide Finding lifecycle, authorize a recovery generation, or rewrite Finding history.

---

## 3. What one Finding recovery generation is

A **Finding recovery generation** is one lineage successor of the currently selected Finding generation for exactly one `reviewId`.

It contains:

1. an immutable recovery manifest;
2. a recovered prefix for the logical `findings` stream;
3. a recovered prefix for the logical `amendments` stream, or an explicit `ABSENT` state;
4. the exact predecessor/source snapshot digests from which recovery was derived;
5. an exact recovery reason/operation descriptor;
6. enough provenance to audit when and by which declared tool/actor the generation was produced.

The logical Finding material is always the pair:

```text
FindingMaterialV1 =
    findings stream
    + amendments stream
```

Recovery MUST NOT reinterpret only one stream while silently ignoring the other. A generation is selectable only if the complete pair is structurally trustworthy and the existing Finding-domain lifecycle rules can be derived without ambiguity.

### 3.1 Baseline generation

Every existing review has one deterministic legacy baseline generation even though legacy reviews do not contain recovery metadata.

```text
baselineGenerationId =
  "FGB1-" + sha256(
    UTF8("FindingBaselineGenerationV1\nreviewId=" + reviewId + "\n")
  )
```

The baseline generation denotes the existing root `findings.ndjson` / `findings-amendments.ndjson` lineage root for that review. Its identifier is stable across ordinary append-only writes; it is not a content digest.

Before the first recovery selection, ordinary Finding writes continue to the legacy root files.

---

## 4. Physical recovery layout

V1 uses one Finding-domain recovery subtree inside the existing review authority:

```text
.opencode/state/reviews/<reviewId>/
    findings.ndjson
    findings-amendments.ndjson
    finding-recovery/
        selections.ndjson
        generations/
            <generationId>/
                generation.json
                findings.ndjson
                findings-amendments.ndjson   # omitted when recovered-prefix state is ABSENT
```

Rules:

- absence of `finding-recovery/` means a legacy review with the baseline generation active;
- if `finding-recovery/` exists, `selections.ndjson` is mandatory and authoritative for Finding-generation selection;
- generation directories are immutable candidates until selected;
- temporary/incomplete generation construction MUST occur under a non-authoritative temporary name and become visible as `<generationId>/` only after complete validation and same-filesystem atomic publication;
- a generation directory by itself does not claim authority;
- `selections.ndjson` is a sibling control ledger inside the same Finding-domain authority, not a generic recovery database.

If `finding-recovery/` exists but `selections.ndjson` is missing, unreadable, torn, or structurally invalid, the Finding-domain reader MUST fail closed. It MUST NOT silently fall back to the legacy root files.

---

## 5. Exact byte and digest primitives

All SHA-256 values in this contract are lowercase hexadecimal over exact bytes.

For each logical stream, distinguish `ABSENT` from a present zero-byte file.

```text
StreamSnapshotV1 {
  state: ABSENT | PRESENT
  byteLength: non-negative integer
  sha256: lowercase hex | null
}
```

Rules:

- `ABSENT` requires `byteLength = 0` and `sha256 = null`;
- `PRESENT` requires `sha256 = SHA256(exact file bytes)` and exact byte length;
- no newline normalization, Unicode normalization, JSON reserialization, or platform newline conversion occurs before hashing.

The aggregate pair digest is:

```text
pairDigest = SHA256(UTF8(
  "FindingLedgerPairV1\n" +
  "findings.state=" + stateF + "\n" +
  "findings.byteLength=" + decimalLengthF + "\n" +
  "findings.sha256=" + (shaF or "-") + "\n" +
  "amendments.state=" + stateA + "\n" +
  "amendments.byteLength=" + decimalLengthA + "\n" +
  "amendments.sha256=" + (shaA or "-") + "\n"
))
```

This exact aggregate algorithm is used for `sourceSnapshotDigest` and `recoveredContentDigest`.

---

## 6. Recovery reason and operation V1

A recovery generation is not an arbitrary edited copy of the ledger.

V1 permits only deterministic **safe reframing** that cannot rewrite the JSON bytes of any complete durable record.

```text
FindingRecoveryOperationV1 {
  schemaVersion: 1
  operationKind: SAFE_REFRAME_V1
  transforms[]
}
```

Allowed transform actions are exactly:

```text
APPEND_TERMINAL_LF
OMIT_EMPTY_RECORD_SEPARATOR
OMIT_INCOMPLETE_TERMINAL_FRAGMENT
```

### `APPEND_TERMINAL_LF`

Allowed only when the final non-newline-terminated byte sequence is a complete JSON object accepted by the current Finding-domain validator for that stream, and the only framing defect is the missing final LF byte (`0x0A`). The recovered stream is the source bytes plus exactly one LF.

### `OMIT_EMPTY_RECORD_SEPARATOR`

Allowed only for an empty NDJSON record created solely by adjacent LF separators. The transform may remove only the redundant separator byte. No non-LF source byte may be removed or changed.

### `OMIT_INCOMPLETE_TERMINAL_FRAGMENT`

Allowed only for the terminal non-newline-terminated fragment that does **not** parse as one complete JSON value/object. The exact fragment range and SHA-256 MUST be retained in the recovery manifest as corruption evidence. It was never a valid durable NDJSON record under the existing newline-terminated record contract.

This transform does not permit reconstruction of the intended missing event. If the omitted fragment suggests that a material event may have been attempted, that fact remains visible in recovery provenance and any claim depending on the unrecorded intent remains `INCONCLUSIVE` until re-established through ordinary Finding-domain evidence.

### Forbidden V1 transformations

V1 MUST NOT:

- omit or change a complete newline-terminated non-empty record;
- omit a complete JSON object merely because its schema version is unknown;
- deduplicate a complete record with a duplicate ID;
- repair an illegal lifecycle transition by deleting the inconvenient event;
- reconstruct missing JSON fields from model prose;
- replace a recorded `F-...`, `FA-...`, SHA, blob, range, or lifecycle fact;
- reorder complete records.

If trustworthy recovery would require any forbidden transformation, V1 returns `OPERATOR_DECISION_REQUIRED` or `UNRECOVERABLE_WITHOUT_EXACT_EVIDENCE` and MUST NOT create a selectable generation.

### 6.1 Recovery-reason descriptor

Every generation records one or more machine reason codes from:

```text
MISSING_TERMINAL_LF
EMPTY_RECORD
INCOMPLETE_TERMINAL_FRAGMENT
```

Each occurrence records:

```text
FindingRecoveryCorruptionV1 {
  stream: findings | amendments
  code
  startByte
  endByteExclusive
  rawSha256
}
```

Occurrences are sorted by `stream` (`findings` before `amendments`), then `startByte`, `endByteExclusive`, `code`, `rawSha256` before their reason digest is computed.

Any other corruption class is a deterministic V1 stop, not permission for an implementation-defined repair algorithm.

---

## 7. Recovery-generation identity

The generation identifier is content-addressed over semantic recovery inputs, not timestamps or actor labels.

A V1 generation manifest contains at least:

```text
FindingRecoveryGenerationV1 {
  schemaVersion: 1
  kind: FindingRecoveryGenerationV1
  domain: finding
  reviewId
  generationId
  sourceGenerationId
  predecessorGenerationId

  sourceSnapshot {
    findings: StreamSnapshotV1
    amendments: StreamSnapshotV1
    aggregateSha256
  }

  recovery {
    reasonCodes[]
    corruption[]: FindingRecoveryCorruptionV1
    reasonDigest
    operation: FindingRecoveryOperationV1
    operationDigest
  }

  recoveredPrefix {
    findings: StreamSnapshotV1
    amendments: StreamSnapshotV1
    aggregateSha256
  }

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

The `reasonDigest` is SHA-256 of the canonical sorted corruption descriptor sequence. The `operationDigest` is SHA-256 of the canonical V1 operation descriptor and ordered transforms. The exact operation descriptor is retained in `generation.json`; digest-only provenance is insufficient.

Generation identity bytes are exactly:

```text
FindingRecoveryGenerationV1\n
reviewId=<reviewId>\n
sourceGenerationId=<sourceGenerationId>\n
predecessorGenerationId=<predecessorGenerationId>\n
sourceSnapshotDigest=<sourceSnapshot.aggregateSha256>\n
reasonDigest=<recovery.reasonDigest>\n
operationDigest=<recovery.operationDigest>\n
recoveredContentDigest=<recoveredPrefix.aggregateSha256>\n
```

Then:

```text
generationId = "FRG1-" + SHA256(identityBytes)
```

### 7.1 Identity inputs

The following **participate** in generation identity:

- `reviewId`;
- source generation identity;
- predecessor generation identity;
- exact source Finding-material snapshot digest;
- exact recovery reason/corruption descriptor digest;
- exact recovery operation digest;
- exact recovered-prefix content digest.

The following **MUST NOT participate** in generation identity:

- `recordedAt` or filesystem mtime;
- actor/session/user display name;
- tool version/build label;
- absolute host path;
- report text, comments, explanation prose;
- generation directory creation order;
- branch name or movable ref.

Time/tool/actor fields remain provenance and audit data. Their exclusion from `generationId` prevents the same semantic recovery from acquiring a different generation identity merely because it was reproduced later or by another declared actor.

---

## 8. Recovered prefix and later append-only continuation

`recoveredContentDigest` binds the recovered **prefix at generation creation**, not every future byte that may legitimately be appended after that generation becomes active.

Before selection:

- a candidate generation's stream files MUST equal the recorded recovered-prefix states, lengths, and digests exactly;
- no ordinary Finding-domain write may append to the candidate.

After selection:

- the recovered prefix is immutable forever;
- ordinary `record_finding` / amendment semantics may append after that prefix through the normal Finding-domain API;
- if a recovered stream was `ABSENT`, a later ordinary append may create that stream; its first byte begins the post-selection continuation at offset zero;
- prefix bytes MUST never be rewritten, compacted, reordered, or normalized;
- a later recovery snapshots the complete then-current active generation, including its recovered prefix plus all valid post-selection appends.

When a successor generation is selected, its predecessor becomes permanently write-fenced.

This gives one stable recovery-generation identity without forcing every ordinary Finding append to create another recovery generation.

---

## 9. Finding generation selection authority

No generation manifest contains an `active: true` flag. Creation is not selection.

Selection is an explicit append-only Finding-domain operation recorded in:

```text
finding-recovery/selections.ndjson
```

The first recovery bootstrap creates one baseline anchor before any generation candidate is published:

```text
FindingGenerationSelectionV1 {
  schemaVersion: 1
  kind: BASELINE
  selectionId
  reviewId
  selectedGenerationId: <baselineGenerationId>
  supersedesSelectionIds: []
  recordedAt
  actorRef
  toolId
}
```

Subsequent records use:

```text
FindingGenerationSelectionV1 {
  schemaVersion: 1
  kind: SELECT
  selectionId
  reviewId
  selectedGenerationId
  supersedesSelectionIds[]
  operatorDecisionRef
  recordedAt
  actorRef
  toolId
  toolVersion?
}
```

Every `SELECT` changes Finding authority and therefore MUST carry an explicit non-empty `operatorDecisionRef` plus declared actor attribution. CodeSleuth attribution is provenance, not a cryptographic identity claim.

### 9.1 Selection identity

`supersedesSelectionIds[]` is deduplicated and lexicographically sorted before hashing.

For `SELECT`:

```text
selectionIdentityBytes = UTF8(
  "FindingGenerationSelectionV1\n" +
  "reviewId=" + reviewId + "\n" +
  "selectedGenerationId=" + selectedGenerationId + "\n" +
  "supersedes=" + supersedesSelectionIds.join(",") + "\n"
)

selectionId = "FGS1-" + SHA256(selectionIdentityBytes)
```

`recordedAt`, actor/tool provenance, and `operatorDecisionRef` do not participate in selection identity. The state transition itself is the identity; provenance records who/when/under which approval reference performed it.

The baseline anchor uses the same principle with tag `FindingGenerationBaselineSelectionV1` and no parents.

---

## 10. One deterministic active-generation algorithm

The Finding-domain reader MUST use this algorithm and no other selection rule.

### Step 0 — legacy mode

If `finding-recovery/` does not exist, the active generation is the deterministic baseline generation and material comes from the existing root `findings.ndjson` / `findings-amendments.ndjson`.

No timestamp, filename ordering, or recovery guess is involved.

### Step 1 — recovery-control validation

If `finding-recovery/` exists:

1. `selections.ndjson` MUST exist;
2. every line MUST pass `LedgerIntegrityCore` framing/JSON/schema/duplicate-ID checks;
3. every selection ID MUST recompute exactly;
4. there MUST be exactly one valid `BASELINE` anchor for this `reviewId` and its selected generation MUST equal the deterministic baseline generation ID;
5. unknown selection schema versions fail closed.

If any condition fails, return `UNTRUSTED_SELECTION_HISTORY` and no authoritative Finding material.

### Step 2 — generation validation

For every generation referenced by a selection record:

1. `generation.json` MUST exist and use supported schema version 1;
2. `generationId` MUST recompute exactly;
3. predecessor/source generation MUST exist;
4. predecessor links MUST form an acyclic chain reaching the baseline generation;
5. the recorded source snapshot MUST match the exact predecessor bytes captured for that recovery operation;
6. safe-reframe operation replay MUST produce exactly the recorded recovered prefix;
7. recovered-prefix state/length/digests MUST match the generation files;
8. the complete current generation material (prefix plus any later append-only continuation) MUST pass structural and Finding-domain semantic validation.

A selected generation that fails any item is not authoritative and causes a fail-closed reader result. The reader MUST NOT automatically fall back to its predecessor.

An invalid generation that is not referenced by any selection may be reported as a failed/non-authoritative recovery candidate without poisoning an otherwise valid active selection chain.

### Step 3 — selection graph

Build a directed graph where each `supersedesSelectionIds` parent points to the child `SELECT` record.

Requirements:

- every parent ID exists;
- every selection is reachable from the single baseline anchor;
- the selection graph is acyclic;
- for a one-parent `SELECT`, the newly selected generation MUST be a strict descendant of the parent's selected generation;
- a multi-parent `SELECT` is conflict adjudication: it MUST supersede **all current terminal selection claims** and may select one parent-selected generation or a valid descendant of one of them;
- the writer MUST refuse a stale selection whose `supersedesSelectionIds` is not exactly the current terminal set it is intended to replace.

### Step 4 — terminal selection

Compute selection nodes with out-degree zero.

```text
if terminalSelectionCount == 1:
    activeGeneration = that terminal selection's selectedGenerationId
else:
    fail AMBIGUOUS_ACTIVE_GENERATION
```

This is the only active-generation rule.

The reader MUST NOT use:

- largest timestamp;
- newest file mtime;
- last line in `selections.ndjson`;
- lexicographically largest ID;
- deepest generation directory;
- most complete-looking content;
- generation with most records;
- model judgment.

A later timestamp can never break an ambiguity.

---

## 11. Conflict and ambiguity resolution

Two concurrent selections from the same parent create two terminal selection nodes. Neither wins.

Example:

```text
S0 -> S1 selects G1
  \\-> S2 selects G2
```

Result:

```text
AMBIGUOUS_ACTIVE_GENERATION
active authoritative Finding material = none
```

Resolution requires one new explicit operator-approved `SELECT` whose `supersedesSelectionIds` contains **both** terminal IDs:

```text
S1 --+
     +--> S3 selects G1 (or a valid descendant)
S2 --+
```

After S3 validates, it is the unique terminal selection and therefore active.

The losing generation, losing selection, corruption evidence, and decision provenance remain durable history. Resolution never deletes them.

---

## 12. Fail-closed behavior

The following behavior is normative.

| Condition | Required result |
| --- | --- |
| two or more terminal selections | `AMBIGUOUS_ACTIVE_GENERATION`; return no authoritative Finding material |
| zero terminal selections due to cycle/corrupt graph | `BROKEN_SELECTION_LINEAGE`; fail closed |
| selected generation has missing predecessor | `MISSING_PREDECESSOR`; fail closed; no predecessor fallback |
| selected generation lineage cycle | `BROKEN_RECOVERY_LINEAGE`; fail closed |
| generation ID, source snapshot, operation, recovered prefix, or preserved prefix digest mismatch | `DIGEST_MISMATCH`; fail closed |
| active generation structural corruption | `UNTRUSTED_ACTIVE_GENERATION`; diagnostic salvage may be exposed only as non-authoritative |
| active amendment schema unsupported | existing unsupported-schema fail-closed semantics remain; recovery selection does not weaken them |
| generation schema version unsupported and generation is selected | `UNSUPPORTED_RECOVERY_SCHEMA`; fail closed |
| unknown schema only in an unselected candidate | candidate is invalid/non-authoritative; current active selection may remain usable |
| `selections.ndjson` torn/unparseable/unknown-version/duplicate-ID | `UNTRUSTED_SELECTION_HISTORY`; no legacy fallback |
| recovery candidate partially written but never atomically published and never selected | ignore as non-authoritative temporary state; previous active remains active |
| published generation exists but no selection references it | candidate only; previous active remains active |
| selection references an incomplete/unvalidated generation | fail closed; do not ignore the bad selection |
| predecessor changes after source snapshot but before selection | `SOURCE_CHANGED_DURING_RECOVERY`; candidate cannot be selected; new recovery must start from a fresh snapshot |
| recovery would require changing/omitting a complete durable record | `OPERATOR_DECISION_REQUIRED` or `UNRECOVERABLE_WITHOUT_EXACT_EVIDENCE`; no selectable V1 generation |
| recovery directory exists but selection history is missing | `UNTRUSTED_SELECTION_HISTORY`; no root fallback |

A reader MAY expose parsed prefixes, corrupt ranges, candidate IDs, and diagnostics for audit/disaster recovery, but MUST label them non-authoritative and MUST NOT derive a trustworthy lifecycle from them.

---

## 13. Immutability and evidence preservation

These rules are absolute for W5:

1. Existing original `findings.ndjson` bytes are never rewritten, deleted, compacted, reordered, or normalized by recovery.
2. Existing `findings-amendments.ndjson` bytes are never rewritten, deleted, compacted, reordered, or normalized by recovery.
3. A recovery creates a new lineage generation. It does not edit the predecessor generation.
4. Corruption/failure evidence remains preserved in the predecessor exact bytes plus source snapshot digests and corruption descriptors.
5. A selected successor freezes its predecessor from future writes.
6. Recovery does not convert finding lifecycle by itself. Existing lifecycle is derived from the complete active Finding material using existing Finding rules.
7. Recovery does not create, delete, close, reopen, retract, correct, or supersede a finding. Those remain ordinary Finding-domain amendment operations.
8. No recovery action may turn absent, corrupt, conflicting, or unknown evidence into a positive fact.

---

## 14. Reader and writer compatibility obligations

W5 implementation is not complete until every material Finding-domain reader/writer uses the same active-generation resolver.

At minimum this includes the semantics exposed by:

```text
review_state_load
review_state_get_finding
review_state_get_amendment
review_state_list_amendments
review_state_record_finding
review_state_amend_finding
review compaction / rehydration
```

Obligations:

- legacy reviews with no `finding-recovery/` remain readable exactly as before;
- a review with no amendment stream still means zero amendments and `OPEN` lifecycle where otherwise valid;
- existing `F-...` and `FA-...` identities remain unchanged;
- implicit amendment `schemaVersion: 1` compatibility remains unchanged;
- existing lifecycle transition rules remain unchanged;
- existing 80-line current-source evidence bounds, fresh reopen/correct evidence, and close verification rules remain unchanged;
- raw human audit remains possible, but raw filesystem order/path discovery does not select authority;
- `review-compaction` may continue to expose bounded degraded salvage, but it MUST obtain active-generation identity from the domain resolver and MUST NOT independently choose a root/generation;
- reports, Mermaid, context projection, export, or grep remain downstream/non-authoritative;
- all ordinary post-selection writes go through existing Finding-domain APIs and target only the selected active generation;
- no API caller is required to know the physical generation path.

A legacy reader that keeps reading root `findings.ndjson` after a recovered generation has been selected is a correctness bug, not a compatibility mode.

---

## 15. Adversarial examples required by the frozen contract

Downstream W5 tests MUST cover at least these cases.

### A. Candidate does not equal active

- baseline G0 active;
- valid G1 generation directory exists;
- no `SELECT` references G1.

Expected: G0 remains active.

### B. Timestamp cannot decide

- S1 selects G1;
- S2 selects sibling G2 from the same parent;
- S2 has a later `recordedAt`.

Expected: `AMBIGUOUS_ACTIVE_GENERATION`, not G2.

### C. Explicit conflict adjudication

- S1 and S2 conflict;
- S3 references both terminal selections and chooses G1.

Expected: G1 active only after S3 validates.

### D. Missing predecessor

- selected G2 claims predecessor G1;
- G1 is absent.

Expected: `MISSING_PREDECESSOR`; no fallback to G0.

### E. Digest tampering

- selected G1 recovered prefix differs by one byte from its recorded digest.

Expected: `DIGEST_MISMATCH`; no authoritative lifecycle.

### F. Complete final JSON without LF

- source final fragment is a complete domain-valid JSON record but lacks final LF;
- operation is `APPEND_TERMINAL_LF`.

Expected: recovered prefix is source plus one LF; generation identity stable from semantic inputs; selection still requires explicit operator approval.

### G. Incomplete torn suffix

- source ends with non-JSON partial bytes after the last LF;
- operation records exact range/digest and uses `OMIT_INCOMPLETE_TERMINAL_FRAGMENT`.

Expected: predecessor retains exact damaged bytes; recovered generation contains only complete durable records; corruption evidence remains visible.

### H. Invalid complete middle record

- a newline-terminated non-empty record is invalid JSON or domain-invalid.

Expected: SAFE_REFRAME_V1 refuses to omit it; no selectable generation is created.

### I. Unknown schema

- a complete amendment object has unsupported schema version.

Expected: it cannot be omitted merely to make the generation parse; selected history remains fail-closed.

### J. Duplicate event ID

- two complete framed records share an ID.

Expected: no V1 deduplication; recovery stops rather than choosing one.

### K. Incomplete recovery operation

- temporary generation files exist but atomic publication/selection never completed.

Expected: previous active generation remains active; temporary state has no authority.

### L. Source changes during recovery

- candidate source snapshot captured;
- active predecessor receives a legitimate append before selection.

Expected: source digest recheck fails with `SOURCE_CHANGED_DURING_RECOVERY`; candidate is not selected.

### M. Active generation later corrupts

- G1 is selected and then its append-only continuation becomes torn.

Expected: G1 becomes `UNTRUSTED_ACTIVE_GENERATION`; reader does not fall back to G0. A new recovery must explicitly descend from G1.

### N. Volatile provenance changes

- identical semantic recovery is reproduced with a different timestamp/tool version/actor attribution.

Expected: same `generationId`; provenance differs.

---

## 16. MUST / MUST NOT summary

### MUST

- preserve Finding authority inside the Finding domain;
- represent recovery as lineage, never in-place repair;
- bind source bytes, reason, operation, predecessor, and recovered prefix by digest;
- use the exact generation/selection identity algorithms in this document;
- require explicit operator approval for every authority-changing `SELECT`;
- select active material only by the unique-terminal selection-graph rule;
- fail closed on ambiguous selection, broken selected lineage, selected digest mismatch, selected unknown schema, or active structural corruption;
- preserve corrupt predecessor bytes and failure evidence;
- keep legacy no-recovery reviews compatible;
- route all material Finding reads/writes through one domain active-generation resolver.

### MUST NOT

- move active-generation choice into `LedgerIntegrityCore`;
- choose `latest`, `newest`, `best`, `largest`, `most complete`, or highest timestamp;
- rewrite `findings.ndjson` or `findings-amendments.ndjson`;
- silently skip a complete durable record to regain trustworthiness;
- manufacture a missing amendment/finding from prose;
- treat a recovery manifest, report, Mermaid, or graph as a generic authority above Finding history;
- fall back to a predecessor automatically after an active selected generation fails validation;
- change EHA semantics or EHA durable state as part of W5.

---

## 17. Compatibility with accepted EBCA/SIB/EHA invariants

This freeze preserves:

- **identity before claim**: each recovery selection is scoped to one exact `reviewId`, lineage, and content digest;
- **authority precedes representation**: recovery metadata stays inside Finding authority and derived views remain downstream;
- **unknown remains unknown**: complete invalid/unknown records are never deleted to manufacture a trustworthy history;
- **append-only historical evidence**: original and amendment bytes survive;
- **existing protected `CC-STATE` boundary**: recovery is feature population inside persistent review state, not a new capability class or persistence authority;
- **EHA exact-subject rules**: unchanged and outside this freeze.

The current protected regressions `FR-STATE-006`, `FR-STATE-009`, and `FR-STATE-010` remain binding: the amendment sibling must not become a second authority, corrupt amendment history must not silently derive trustworthy lifecycle or accept mutation, and amendment operations must not rewrite original finding lines.

---

## 18. Explicit non-goals

This micro-freeze does not design or authorize:

- Implementation Ledger storage, events, recovery, or generation selection;
- EHA V2 events, EHA recovery generations, or EHA acceptance semantics;
- generic cross-domain `make_generation_authoritative` APIs;
- generic SQL/SQLite/Postgres/Doris persistence;
- arbitrary record reconstruction from external/model prose;
- deduplication or semantic deletion of complete Finding/amendment events;
- retention/garbage collection of old recovery generations;
- report/Mermaid/Obsidian authority;
- a universal ledger-repair plugin framework.

Safe recovery operations beyond `SAFE_REFRAME_V1` require a later explicit Finding-domain contract version. Their absence is not an implementation ambiguity in W5: V1 must stop.

---

## 19. Downstream work unlocked

This freeze removes the Finding-domain architecture choice that previously blocked W5.

W5 may now implement, tests first:

1. the Finding baseline/recovery identity primitives;
2. Finding recovery manifest validation;
3. `SAFE_REFRAME_V1` generation creation;
4. append-only selection history;
5. deterministic active-generation resolution;
6. fail-closed reader/writer routing across the existing Finding APIs;
7. adversarial fixtures in §15;
8. compatibility coverage for legacy reviews and existing amendment lifecycle rules.

W5 still depends on/reuses structural `LedgerIntegrityCore` mechanics for framing/digest/schema primitives, but `LedgerIntegrityCore` receives no generation-selection authority from this document.

---

## 20. Unresolved items

No unresolved semantic decision remains inside the W5 V1 scope defined by this freeze.

Unsupported recovery classes have a frozen deterministic outcome: **stop, preserve evidence, and do not select an implementation-defined repaired generation**. That is an explicit V1 boundary, not a deferred implementation choice.

```text
FREEZE STATUS:
FROZEN

UNLOCKS:
W5 Finding Ledger recovery

DOES NOT AUTHORIZE:
W2 Implementation Ledger
W4 Implementation Ledger recovery
W6 EHA V2
```
