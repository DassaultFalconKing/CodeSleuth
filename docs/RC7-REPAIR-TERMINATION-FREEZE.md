# RC7 Repair Attempt Identity and Termination Freeze

**Status:** FROZEN MICRO-CONTRACT / MF4 / W9 DESIGN AUTHORITY  
**Scope:** deterministic bounded automatic-repair control only  
**Out of scope:** source-mutation implementation, EHA V2 storage schema, repair authorization policy ownership, repair strategy selection, and learning-record implementation  
**Freeze date:** 2026-09-02

## 1. Purpose

This document freezes the deterministic identity and termination semantics required for RC7 W9.

It does **not** implement automatic source mutation and it does **not** grant permission to mutate source. It defines the machine contract that any later automatic-repair implementation must satisfy before W9 may be considered bounded and deterministic.

The preserved invariant is:

> **No explicit repair budget = no automatic mutation.**

The stronger RC6 EHA invariant also remains unchanged:

> **A failed exact SHA remains failed. Repair creates a new source subject and fresh acceptance evidence.**

Focused repair verification may qualify a new SHA for acceptance evaluation. It does not create acceptance PASS.

---

## 2. Exact freeze inputs

This freeze was prepared after re-resolving the named refs. None of the supplied branch heads moved.

| Input | Exact identity used | Role |
| --- | --- | --- |
| runtime branch | `feature/rc6-eha-brownfield-bootstrap` | executable evidence only; not a design-commit base |
| runtime HEAD | `1de37c75251a1e0d9904cffdb82695e92e3fab23` | current executable contract evidence |
| runtime tree | `5e8acd831d4f64e2f4a9fcba5dd875b918d55c89` | exact runtime tree |
| planning branch | `docs/rc7-ledger-authority-repair-plan` | design input and base for this docs-only freeze branch |
| planning HEAD | `86218a51345fafb47d0ffec543773846a70ac76a` | current planning input; unchanged from triage |
| pinned review / antithesis | `be5d158880f649ecb568d9a505c694e87bd76e0e` | design input; identifies deterministic termination as a blocker |
| frozen thesis | `1b52c7c72e5294b3a4c145d1bbbd71a1863cb218` | thesis input only; not implementation authority |
| RC7 synthesis | `docs/RC7-THESIS-ANTITHESIS-SYNTHESIS.md` blob `a3556ca3bd84546835a3ff66847cfb03da54fc7b` | review candidate / synthesis input |
| RC6 repair protocol | `docs/EHA-REPAIR-LOOP.md` blob `16bbff3c812127e87fb24a3705cda41ac7f8c4d3` | accepted runtime repair invariant |
| RC6 repair Skill | `pack/.opencode/skills/eha-repair-protocol/SKILL.md` blob `19f202fdf87695d9db7862b0146d9f10b95f7bc0` | executable workflow contract evidence |
| EHA state | `pack/.opencode/tools/eha_state.ts` blob `7a07f6c9ad2e34ef014a39cc9076d71a865ec2c7` | current campaign/verdict/repair semantics |
| trusted campaign bootstrap | `scripts/eha_campaign_bootstrap.py` blob `22d3f08936330ef422e5fc46dccbcdf09097a953` | current campaign identity evidence |
| GitHub bridge core | `scripts/eha_github_bridge_core.py` blob `49b8632f5e11c5a7324a63ce095fbabb7371b06e` | transport/watchdog evidence |
| GitHub bridge controller | `scripts/eha_github_bridge_controller.py` blob `91d2aa031165808da271f2925a9ee7cdc9249c00` | trusted-campaign and transport/acceptance separation evidence |
| EHA state smoke | `tests/eha_state_smoke.ts` blob `0f7e9508fb43a2c40727c17134d6c0450bed3626` | existing repair/exact-SHA regression evidence |
| bridge cases | `tests/eha_github_bridge_cases.py` blob `9bb13340131c31221b2a90a20b78dd499cc5aba7` | existing watchdog fail-closed evidence |
| EBCA thesaurus | `docs/EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md` blob `232795994607b09016481846520b9c82554be5eb` | uncertainty/result vocabulary |
| ordinary hosted acceptance | run `33656390768`, conclusion `success`, exact head `1de37c75251a1e0d9904cffdb82695e92e3fab23` | current runtime execution evidence; not transferable to another SHA |

### 2.1 Current campaign identity constraint

Current RC6 trusted campaign creation uses an identity shaped as:

```text
EHA-<UTC timestamp>-<targetSha[0:12]>-<random uuid fragment>
```

and review/event identities also contain volatile timestamp/UUID material.

Those IDs are valid **durable lineage references**. They are intentionally **not** deterministic repair-attempt identity inputs.

The structured EHA state is host-local under `.opencode/state/reviews/**` and is not tracked application source. This freeze therefore does not invent or claim a current live campaign instance that is not present in the tracked repository. It freezes the current campaign-identity **contract** and its relationship to W9.

Normative consequence:

> `campaignId`, `reviewId`, `eventId`, workflow run IDs, timestamps, model/session IDs, and host process identity MAY be retained as lineage metadata, but MUST NOT determine `AttemptId`, `FailureSignature`, `ObligationStateDigest`, no-progress, or cycle identity.

This is necessary because every repaired SHA requires a fresh EHA campaign and therefore a new campaign ID even when the repair loop is reasoning about the same semantic failure lineage.

---

## 3. Authority boundary

MF4 owns only repair-loop **control semantics**:

```text
acceptance evaluation
        |
        v
normalized failed state
        |
        v
bounded repair-control decision
        |
        +--> STOP
        |
        +--> one authorized mutation attempt
                     |
                     v
              new exact subject
                     |
                     v
            fresh acceptance evaluation
```

MF4 does not own:

- what source mutation is executed;
- which strategy is selected;
- which repository paths are authorized for mutation;
- whether architecture may be reopened;
- EHA durable event-schema evolution;
- acceptance-profile policy ownership;
- how a `RepairLearningRecord` is promoted or retained.

Those responsibilities remain with their existing owners or later RC7 workstreams.

### 3.1 Existing authorities remain authorities

This freeze MUST NOT create a new acceptance authority.

- Git exact object identity remains source identity.
- `eha.ndjson` remains EHA campaign/verdict authority.
- current RC6 failed-SHA history remains immutable.
- focused repair tests remain repair evidence, not acceptance evidence.
- host/transport results remain execution observations, not acceptance verdicts.

A W9 state digest is a deterministic **control value**. It is not a ledger of truth and MUST NOT become a replacement EHA store.

---

## 4. Canonical identity encoding

All MF4 identity digests use one encoding contract, `RepairIdentityCanonicalJsonV1`.

### 4.1 `RepairIdentityCanonicalJsonV1`

Before hashing:

1. input must conform to the exact schema being hashed;
2. all strings MUST be valid Unicode and MUST be normalized to NFC;
3. object member names are ASCII schema names;
4. object members MUST be serialized in lexicographic order of their UTF-8 member-name bytes;
5. arrays representing sets MUST be sorted as specified by that schema before serialization;
6. no insignificant whitespace is emitted;
7. JSON strings use JSON escaping for required control characters, `"`, and `\\`; non-ASCII Unicode is emitted as UTF-8 rather than optionally escaped;
8. identity schemas MUST NOT use floating-point numbers;
9. integers are base-10 with no leading zero except literal `0`;
10. duplicate object keys are invalid;
11. an omitted field and an explicit `null` are not interchangeable; identity schemas below specify which form is legal.

Digest algorithm:

```text
sha256(UTF8(RepairIdentityCanonicalJsonV1(value)))
```

Digest text is lowercase hexadecimal.

Typed identities use these prefixes:

```text
FailureSignature        = FS1-<64 lowercase hex>
ObligationStateDigest   = OS1-<64 lowercase hex>
RepairStateDigest       = RS1-<64 lowercase hex>
AttemptId               = RA1-<64 lowercase hex>
CycleId                 = RC1-<64 lowercase hex>
```

Implementations MUST NOT substitute runtime-native default JSON stringification when it can produce different bytes from this contract.

---

# 5. `FailureSignature`

## 5.1 Purpose

`FailureSignature` answers:

> Is this the same **substantive observed failure identity** for repair-control purposes?

It deliberately does not answer whether two human-readable messages look similar.

It is comparable across different exact candidate SHAs.

Therefore the signature MUST NOT include the candidate SHA, campaign ID, timestamp, run ID, raw stack trace, or free-form prose.

## 5.2 Normalized failure atom

A failed acceptance state MUST be represented as one or more `NormalizedFailureAtomV1` values before automatic repair is permitted.

```text
NormalizedFailureAtomV1 {
  failureIdentitySchema: string
  obligationId: string
  oracleId: string
  failureCode: string
  identityFacts: object<string, string | integer | boolean | null>
}
```

Rules:

- `failureIdentitySchema` MUST identify the versioned normalization contract used by the owning acceptance/domain adapter.
- `obligationId` MUST identify the acceptance obligation whose failure is being represented.
- `oracleId` MUST be a stable machine identity for the check/oracle/assertion class. A human sentence is not an `oracleId`.
- `failureCode` MUST be a stable machine failure class/code. A raw error message is not a `failureCode`.
- `identityFacts` MAY contain only facts explicitly declared identity-bearing by the named `failureIdentitySchema`.
- host-local absolute paths, durations, timestamps, process IDs, random temporary names, provider wording, model prose, log ordering, and cosmetic message formatting MUST NOT enter `identityFacts` unless the domain contract explicitly proves that the value is semantically part of the failure identity.
- exact duplicate atoms have set semantics and are collapsed before hashing. If occurrence count is semantically material, the adapter MUST expose that count as an explicit identity fact.

The domain/acceptance adapter owns the mapping from raw observation to `NormalizedFailureAtomV1`; the W9 controller MUST NOT ask a model to choose which words are important.

## 5.3 Signature algorithm

For a current aggregate `FAIL`:

1. collect all normalized failure atoms that materially explain the current failed acceptance state;
2. canonicalize each atom independently with `RepairIdentityCanonicalJsonV1`;
3. collapse exact duplicate canonical atoms;
4. sort the remaining canonical atom byte strings lexicographically;
5. construct:

```json
{
  "failures": [<canonical failure atom objects>],
  "schema": "FailureSignatureV1"
}
```

6. hash the canonical envelope;
7. prefix with `FS1-`.

At least one atom is required for a `FAIL` that may enter automatic repair.

## 5.4 Substantive versus cosmetic change

The following MUST preserve the same `FailureSignature` when the normalized failure identity is otherwise unchanged:

- wording changes;
- punctuation/capitalization changes;
- changed elapsed time;
- changed log timestamps;
- different stack-trace formatting;
- changed provider/model prose;
- duplicate copies of the same normalized failure atom;
- different campaign/review/workflow IDs.

The following MUST change the signature:

- different failed obligation;
- different stable oracle identity;
- different machine failure code/class;
- changed identity-bearing fact declared by the versioned adapter;
- changed failure-identity schema version.

If raw evidence cannot be deterministically normalized into this form, `FailureSignature` is **unavailable**. Automatic mutation MUST NOT start or continue from that state.

A legacy RC6 `repair.failure` free-text field alone is therefore insufficient to authorize RC7 automatic repair.

---

# 6. `ObligationStateDigest`

## 6.1 Purpose

`ObligationStateDigest` answers:

> What is the current complete machine-visible set of acceptance obligations and their current results under the fixed acceptance-profile identity for this repair loop?

It is intentionally independent of candidate SHA so that two different source candidates with the same acceptance state compare equal.

## 6.2 Canonical obligation state

```text
ObligationResultV1 =
  PASS
  | FAIL
  | INCONCLUSIVE
  | UNAVAILABLE
  | NOT_APPLICABLE

ObligationStateEntryV1 {
  obligationId: string
  result: ObligationResultV1
  notApplicableRationaleCode: string | null
}
```

Rules:

1. The state MUST include **every acceptance obligation in the fixed profile snapshot**, not only failing obligations.
2. `obligationId` values MUST be unique within the state.
3. Entries MUST be sorted lexicographically by NFC-normalized UTF-8 `obligationId` bytes.
4. `notApplicableRationaleCode` MUST be non-empty and authority-backed when `result == NOT_APPLICABLE`.
5. `notApplicableRationaleCode` MUST be `null` for all other results.
6. `NOT_APPLICABLE` is obligation-level only. It is not a repair-loop terminal acceptance outcome.
7. The digest MUST NOT include evidence prose, timestamps, duration, environment noise, campaign IDs, run IDs, source SHA, model identity, or host identity.
8. The aggregate acceptance result is supplied by the acceptance authority. W9 MUST NOT silently invent a new aggregation policy from these entries.

Canonical envelope:

```json
{
  "obligations": [
    {
      "notApplicableRationaleCode": null,
      "obligationId": "...",
      "result": "PASS"
    }
  ],
  "schema": "ObligationStateV1"
}
```

`ObligationStateDigest` is `OS1-` plus the SHA-256 digest of the canonical envelope.

## 6.3 Profile identity is a loop invariant

`ObligationStateDigest` does not embed `profileSnapshotDigest` because the digest is intended to compare semantic obligation state across different exact source subjects.

Instead:

> The exact `profileSnapshotDigest` is a fixed invariant of one automatic-repair loop.

If the profile identity changes, the old and new obligation states are not comparable inside the same loop. The current loop MUST terminate fail-closed with repair-control unavailability (`PROFILE_IDENTITY_CHANGED`). It MUST NOT silently reset history or continue with a new policy.

MF4 consumes `profileSnapshotDigest` as an opaque stable identity. The algorithm that constructs `AcceptanceProfileSnapshotV1` and its semantic digest belongs to W7/MF2, not this freeze.

---

# 7. `RepairStateDigest`

A failed semantic repair state is:

```json
{
  "failureSignature": "FS1-...",
  "obligationStateDigest": "OS1-...",
  "schema": "RepairStateV1"
}
```

`RepairStateDigest` is `RS1-` plus the SHA-256 digest of that canonical envelope.

The candidate/source SHA is deliberately excluded.

This is a normative choice: no-progress and cycle detection are about whether the acceptance-relevant failure state changed, not whether a patch changed bytes.

A source diff can be non-zero while `RepairStateDigest` remains identical. In that case the repair has made **no acceptance-relevant progress** for W9.

---

# 8. `AttemptId`

## 8.1 Deterministic identity inputs

An automatic mutation attempt is identified before mutation by the canonical `RepairAttemptIdentityV1`:

```text
RepairAttemptIdentityV1 {
  attemptOrdinal: integer
  failureSignatureBefore: FailureSignature
  maxAutomatedAttempts: integer
  obligationStateDigestBefore: ObligationStateDigest
  profileSnapshotDigest: string
  rootFailingSubjectSha: full lowercase 40-char Git SHA
  sourceSubjectSha: full lowercase 40-char Git SHA
  strategyId: string
}
```

`AttemptId` is:

```text
RA1-<sha256(RepairIdentityCanonicalJsonV1(RepairAttemptIdentityV1))>
```

Normative meaning of the fields:

- `rootFailingSubjectSha` is the immutable exact SHA whose accepted failure opened this repair lineage.
- `sourceSubjectSha` is the exact current subject from which this particular attempt would mutate.
- `profileSnapshotDigest` is the fixed acceptance-profile snapshot identity for the loop.
- `strategyId` is a stable machine identity selected by a validated repair policy/repair case. Free-form strategy prose is forbidden as identity.
- `failureSignatureBefore` and `obligationStateDigestBefore` bind the attempt to the exact pre-mutation semantic failure state.
- `attemptOrdinal` begins at `1` and is monotonic within the bounded loop.
- `maxAutomatedAttempts` is included so silently changing the automatic budget changes attempt identity rather than pretending to continue the same bounded contract.

## 8.2 Explicitly excluded inputs

`AttemptId` MUST NOT include:

- `campaignId`;
- `reviewId`;
- `eventId`;
- wall-clock time or date;
- GitHub Actions run/job/attempt IDs;
- model/provider/session identity;
- host name, PID, temporary directory, transcript path;
- raw prompt text;
- raw patch/diff prose;
- raw stdout/stderr;
- post-mutation SHA;
- resulting diff digest;
- focused-test result;
- post-mutation failure signature or obligation digest.

Post-mutation values cannot be part of a pre-mutation identity and belong in later attempt evidence, not in `AttemptId`.

## 8.3 Replay and collision behavior

Within one repair-loop history:

- there MUST be at most one distinct `AttemptId` for an `attemptOrdinal`;
- re-observing the exact same `AttemptId` after interruption is a **resume/reconciliation**, not a new automatic mutation attempt;
- a second different `AttemptId` for the same ordinal is a history conflict and automatic mutation MUST stop;
- an implementation MUST NOT blindly replay source mutation merely because delivery/transport acknowledgement was lost.

If persisted identity payload and stored `AttemptId` disagree when recomputed, the repair history is unavailable/untrustworthy for automatic continuation.

---

# 9. Repair budget

## 9.1 Meaning of `maxAutomatedAttempts`

`maxAutomatedAttempts` is the maximum number of distinct automatic **source-mutation attempts** that may cross the mutation side-effect boundary in one bounded repair loop.

Machine type:

```text
integer, 0 <= maxAutomatedAttempts <= 9007199254740991
```

The upper bound is the largest exactly representable cross-language JSON integer in the current JavaScript/TypeScript runtime family. It is an interchange bound, not a recommended policy value.

There is **no default**.

Normative cases:

```text
field missing / null     -> no valid explicit budget -> UNAUTHORIZED_REPAIR
negative / fractional    -> invalid contract         -> REPAIR_UNAVAILABLE
0                        -> zero automatic mutations -> BUDGET_EXHAUSTED
N > 0                    -> ordinals 1..N may be attempted, subject to all other stops
```

A model MUST NOT choose, infer, extend, or reset the budget.

## 9.2 Initial failing evaluation does not consume budget

The initial failing acceptance evaluation is state index `0`.

It is **not** a mutation attempt and MUST NOT consume `maxAutomatedAttempts`.

Likewise, these do not consume mutation budget:

- failure normalization;
- repair packet rendering;
- authorization checks;
- focused verification;
- fresh EHA/acceptance evaluation;
- durable read/reconciliation that performs no source mutation.

## 9.3 When a mutation attempt is consumed

A distinct `AttemptId` consumes one automatic attempt when execution reaches the abstract **mutation side-effect boundary**:

> the mutation command/request has been accepted by a host execution path that may change repository/source state.

This is a control boundary, not a prescription for how source mutation is implemented.

Rules:

1. Rejection or validation failure provably **before** that boundary does not consume an attempt.
2. Once the boundary is crossed, the attempt is consumed whether mutation succeeds, fails, produces zero effective delta, or later transport fails.
3. If transport is lost and the controller cannot prove whether the boundary was crossed, the attempt is conservatively treated as consumed.
4. Ambiguous dispatch MUST NOT be automatically replayed. Repository state must first be re-observed.
5. Reconciliation of the same `AttemptId` does not consume a second attempt.

This prevents transport ambiguity from creating unbounded duplicate mutations.

## 9.4 Exhaustion

Before starting attempt `i`, the controller MUST require:

```text
i <= maxAutomatedAttempts
```

After a completed attempt and fresh evaluation, if the acceptance result is still `FAIL` and no higher-precedence no-progress/cycle/postcondition stop has fired, then:

```text
attemptsConsumed == maxAutomatedAttempts
```

terminates the loop with:

```text
BUDGET_EXHAUSTED
```

Budget exhaustion does not change the last acceptance result.

If the last exact subject is `FAIL`, it remains `FAIL`.

---

# 10. No-progress rule

No-progress is an exact equality predicate. It is not a model judgement, similarity score, source-diff heuristic, or wall-clock timeout.

For a completed mutation attempt with a fresh post-mutation acceptance evaluation returning `FAIL`, let:

```text
pre  = RepairStateDigest before the attempt
post = RepairStateDigest after the fresh evaluation
```

Then:

```text
NO_PROGRESS := (post == pre)
```

Equivalent expanded rule:

```text
failureSignatureAfter == failureSignatureBefore
AND
obligationStateDigestAfter == obligationStateDigestBefore
```

When true, the loop MUST terminate immediately with `NO_PROGRESS`.

Consequences:

- different patch prose does not count as progress;
- non-zero source diff does not count as progress by itself;
- different timing/log formatting does not count as progress;
- a changed substantive failure signature counts as changed state;
- a changed obligation/result set counts as changed state;
- W9 does not rank a changed state as “better” or “worse”; if it is different, the bounded loop may continue unless another stop applies.

### 10.1 Namespace separation from RC6 watchdog

Current RC6 bridge reason:

```text
NO_PROGRESS_TIMEOUT
```

is a **transport watchdog idle timeout**.

MF4 outcome:

```text
NO_PROGRESS
```

is semantic equality of completed pre/post repair-state digests.

They MUST remain distinct machine states and MUST NOT be mapped to each other automatically.

A timeout is not proof that a repair made no semantic progress.

---

# 11. Cycle detection

## 11.1 History window

Cycle history is the **entire failed semantic-state history of one bounded automatic-repair loop**:

```text
state[0] = initial failing evaluation
state[1] = failing evaluation after attempt 1
state[2] = failing evaluation after attempt 2
...
```

Only states whose fresh acceptance result is `FAIL` enter this history.

The history MUST NOT be truncated or reduced to an arbitrary last-K window.

It is already bounded by policy:

```text
maximum failed states retained <= maxAutomatedAttempts + 1
```

## 11.2 Detection rule

After a completed attempt returns a fresh `FAIL` and after `NO_PROGRESS` has been checked:

1. compute the new `RepairStateDigest`;
2. if it equals the immediately previous state, stop `NO_PROGRESS`;
3. otherwise, if it equals any earlier state in history, stop `CYCLE_DETECTED`;
4. otherwise append it and continue subject to budget/authorization.

Because the loop terminates at the first duplicate, a non-adjacent repeated state has exactly one prior occurrence in a valid nonterminal history.

This detects:

```text
A -> B -> A             cycle length 2
A -> B -> C -> A        cycle length 3
A -> B -> C -> B        cycle length 2 over B,C
```

Immediate:

```text
A -> A
```

is classified as `NO_PROGRESS`, not `CYCLE_DETECTED`.

## 11.3 Cycle identity

Let `j` be the prior index of the repeated state and `k` the current repeated state index.

The canonical cycle body is:

```text
[state[j], state[j+1], ..., state[k-1]]
```

The current `state[k] == state[j]` closes the cycle and is not repeated in the body.

Canonical envelope:

```json
{
  "cycleLength": 2,
  "cycleStates": ["RS1-...", "RS1-..."],
  "schema": "RepairCycleV1"
}
```

`CycleId` is `RC1-` plus the SHA-256 digest of the canonical envelope.

The loop MUST terminate with `CYCLE_DETECTED` and retain the computed `CycleId` as derived repair-control evidence.

`CycleId` is not acceptance authority.

---

# 12. Terminal outcome model

Acceptance truth and repair-control termination are separate axes.

## 12.1 Acceptance result

The latest fresh acceptance evaluation has exactly one of:

```text
PASS
FAIL
INCONCLUSIVE
UNAVAILABLE
```

`NOT_APPLICABLE` remains obligation-level only.

W9 MUST NOT coerce:

```text
INCONCLUSIVE -> FAIL
UNAVAILABLE  -> FAIL
INCONCLUSIVE -> PASS
UNAVAILABLE  -> PASS
```

## 12.2 Repair stop reason

A terminal repair-loop envelope uses:

```text
RepairStopReasonV1 =
  ACCEPTANCE_PASS
  | ACCEPTANCE_INCONCLUSIVE
  | ACCEPTANCE_UNAVAILABLE
  | BUDGET_EXHAUSTED
  | CYCLE_DETECTED
  | NO_PROGRESS
  | UNAUTHORIZED_REPAIR
  | HOST_POSTCONDITION_FAILED
  | REPAIR_UNAVAILABLE
```

`FAIL` is intentionally **not** a repair stop reason.

A `FAIL` is an acceptance result. While the loop is allowed to continue, `FAIL` is nonterminal. When the loop can no longer continue, the last acceptance result remains `FAIL` and the separate stop reason records **why repair stopped**.

This prevents statements such as “budget exhausted, therefore FAIL became PASS” or “transport stopped, therefore acceptance is unavailable.”

## 12.3 Terminal envelope

```text
RepairLoopTerminalV1 {
  schema: "RepairLoopTerminalV1"
  terminal: true
  lastAcceptanceResult: PASS | FAIL | INCONCLUSIVE | UNAVAILABLE
  stopReason: RepairStopReasonV1
  attemptsConsumed: integer
  lastSubjectSha: full lowercase Git SHA
  failureSignature: FailureSignature | null
  obligationStateDigest: ObligationStateDigest | null
  cycleId: CycleId | null
  detailCode: string | null
}
```

Required combinations:

| Situation | `lastAcceptanceResult` | `stopReason` | Mutation may continue? |
| --- | --- | --- | --- |
| fresh exact-subject acceptance PASS | `PASS` | `ACCEPTANCE_PASS` | no |
| acceptance evidence is inconclusive | `INCONCLUSIVE` | `ACCEPTANCE_INCONCLUSIVE` | no |
| required acceptance evidence unavailable | `UNAVAILABLE` | `ACCEPTANCE_UNAVAILABLE` | no |
| still failing and budget reached | `FAIL` | `BUDGET_EXHAUSTED` | no |
| semantic cycle detected | `FAIL` | `CYCLE_DETECTED` | no |
| identical pre/post semantic failure state | `FAIL` | `NO_PROGRESS` | no |
| no valid explicit budget or explicit permission denied | normally `FAIL` | `UNAUTHORIZED_REPAIR` | no |
| host mutation postcondition failed | last known result, normally `FAIL` | `HOST_POSTCONDITION_FAILED` | no |
| repair transport/state/identity cannot be established | last known result, normally `FAIL` | `REPAIR_UNAVAILABLE` | no |

A terminal transport/repair outcome MUST NOT manufacture `PASS`.

## 12.4 `HOST_POSTCONDITION_FAILED`

The RC7 synthesis already requires this terminal class.

W9 consumes it abstractly when the host reports that mutation was attempted but the required effective repository-state postcondition is not satisfied, including zero effective delta where the validated repair operation required a delta.

MF4 does not define how source mutation or postcondition observation is implemented.

The attempt is consumed if the mutation side-effect boundary was crossed.

## 12.5 `REPAIR_UNAVAILABLE`

`REPAIR_UNAVAILABLE` is a repair-control stop, not an acceptance verdict.

Stable detail codes SHOULD distinguish at least:

```text
REPAIR_BUDGET_INVALID
FAILURE_IDENTITY_UNAVAILABLE
OBLIGATION_STATE_INVALID
PROFILE_IDENTITY_CHANGED
ATTEMPT_HISTORY_CONFLICT
ATTEMPT_ID_MISMATCH
MUTATION_DISPATCH_UNCERTAIN
REPAIR_TRANSPORT_UNAVAILABLE
POST_MUTATION_SUBJECT_UNAVAILABLE
FRESH_ACCEPTANCE_UNAVAILABLE
```

When fresh acceptance itself runs and returns `UNAVAILABLE`, use `lastAcceptanceResult=UNAVAILABLE` with `ACCEPTANCE_UNAVAILABLE`.

When repair transport fails **before a fresh acceptance result exists**, preserve the previous acceptance result and use `REPAIR_UNAVAILABLE`.

---

# 13. Deterministic transition algorithm

The following algorithm is normative pseudocode for W9 control semantics.

```text
INPUT
  rootFailingSubjectSha
  fixedProfileSnapshotDigest
  maxAutomatedAttempts   // may be absent
  initialFreshEvaluation

attemptsConsumed = 0
failedStateHistory = []

function observe(evaluation):
  assert evaluation.profileSnapshotDigest == fixedProfileSnapshotDigest
    else STOP(last acceptance, REPAIR_UNAVAILABLE, PROFILE_IDENTITY_CHANGED)

  compute ObligationStateDigest
    else STOP(last acceptance, REPAIR_UNAVAILABLE, OBLIGATION_STATE_INVALID)

  if evaluation.result == PASS:
    STOP(PASS, ACCEPTANCE_PASS)

  if evaluation.result == INCONCLUSIVE:
    STOP(INCONCLUSIVE, ACCEPTANCE_INCONCLUSIVE)

  if evaluation.result == UNAVAILABLE:
    STOP(UNAVAILABLE, ACCEPTANCE_UNAVAILABLE)

  // only FAIL reaches automatic-repair state handling
  compute FailureSignature
    else STOP(FAIL, REPAIR_UNAVAILABLE, FAILURE_IDENTITY_UNAVAILABLE)

  return RepairStateDigest(FailureSignature, ObligationStateDigest)

state0 = observe(initialFreshEvaluation)
failedStateHistory.append(state0)

if maxAutomatedAttempts is absent:
  STOP(FAIL, UNAUTHORIZED_REPAIR, REPAIR_BUDGET_MISSING)

if maxAutomatedAttempts is invalid:
  STOP(FAIL, REPAIR_UNAVAILABLE, REPAIR_BUDGET_INVALID)

if maxAutomatedAttempts == 0:
  STOP(FAIL, BUDGET_EXHAUSTED)

for ordinal in 1..maxAutomatedAttempts:
  require exact current source subject
  require stable strategyId
  require external repair authorization for this exact attempt context
    if denied:       STOP(FAIL, UNAUTHORIZED_REPAIR)
    if inconclusive: STOP(FAIL, REPAIR_UNAVAILABLE, REPAIR_AUTHORIZATION_INCONCLUSIVE)
    if unavailable:  STOP(FAIL, REPAIR_UNAVAILABLE, REPAIR_AUTHORIZATION_UNAVAILABLE)

  attemptId = AttemptId(
    ordinal,
    maxAutomatedAttempts,
    rootFailingSubjectSha,
    currentSourceSubjectSha,
    fixedProfileSnapshotDigest,
    strategyId,
    currentFailureSignature,
    currentObligationStateDigest
  )

  validate no distinct AttemptId already occupies this ordinal
    else STOP(FAIL, REPAIR_UNAVAILABLE, ATTEMPT_HISTORY_CONFLICT)

  dispatch mutation attempt

  if dispatch provably rejected before side-effect boundary:
    STOP(FAIL, UNAUTHORIZED_REPAIR or REPAIR_UNAVAILABLE according to rejection class)

  if side-effect boundary crossed OR crossing is ambiguous:
    attemptsConsumed = ordinal

  if host postcondition fails:
    STOP(lastAcceptanceResult, HOST_POSTCONDITION_FAILED)

  if exact resulting subject cannot be established:
    STOP(lastAcceptanceResult, REPAIR_UNAVAILABLE, POST_MUTATION_SUBJECT_UNAVAILABLE)

  run fresh acceptance evaluation for the exact resulting subject
  newState = observe(freshEvaluation)

  // observe() already stops PASS / INCONCLUSIVE / UNAVAILABLE
  // therefore reaching here means fresh FAIL

  if newState == failedStateHistory[-1]:
    STOP(FAIL, NO_PROGRESS)

  if newState exists anywhere in failedStateHistory:
    compute CycleId from the prior occurrence through the current cycle body
    STOP(FAIL, CYCLE_DETECTED, cycleId)

  failedStateHistory.append(newState)

  if attemptsConsumed == maxAutomatedAttempts:
    STOP(FAIL, BUDGET_EXHAUSTED)

  continue
```

### 13.1 Stop precedence

When multiple facts become true at the same transition, use this precedence:

```text
1. fresh acceptance PASS / INCONCLUSIVE / UNAVAILABLE
2. state/identity/profile unavailability
3. HOST_POSTCONDITION_FAILED when no valid fresh evaluation exists
4. NO_PROGRESS
5. CYCLE_DETECTED
6. BUDGET_EXHAUSTED
7. authorization for a possible next attempt
8. continue
```

Rationale:

- a real fresh acceptance result outranks repair-control bookkeeping;
- inability to establish exact state fails closed;
- no-progress/cycle explain the semantic termination that was actually observed on the final consumed attempt;
- budget is checked after those stronger semantic stop witnesses;
- authorization for another attempt matters only if another attempt could otherwise begin.

---

# 14. MUST / MUST NOT

## 14.1 MUST

A conforming W9 implementation MUST:

1. require an explicit finite `maxAutomatedAttempts` before any automatic source mutation;
2. treat the initial failing evaluation as state `0`, not as a mutation attempt;
3. assign deterministic `AttemptId` from the exact inputs in section 8;
4. bind every attempt to exact pre-mutation source SHA, profile identity, failure signature, obligation-state digest, strategy ID, ordinal, and immutable budget;
5. use structured/versioned failure normalization rather than free-form failure prose;
6. include the complete current obligation/result set in `ObligationStateDigest`;
7. compare no-progress by exact semantic digest equality;
8. retain the entire bounded failed-state history for cycle detection;
9. detect two-step and longer cycles at the first repeated non-adjacent semantic state;
10. consume a mutation attempt at or after the mutation side-effect boundary, including ambiguous acknowledgement after that boundary;
11. require a new exact source subject and fresh acceptance evidence after mutation before recording acceptance improvement;
12. keep acceptance result and repair stop reason separate;
13. preserve EBCA uncertainty; `INCONCLUSIVE` and `UNAVAILABLE` are terminal for automatic repair unless a later explicit operator action creates a new decision context;
14. fail closed when identity, profile, history, authorization, or exact post-mutation state is ambiguous;
15. keep current RC6 failed-SHA history immutable.

## 14.2 MUST NOT

A conforming W9 implementation MUST NOT:

1. infer a repair budget from model judgement, defaults, prior runs, environment variables, or “reasonable” heuristics;
2. count the initial failing evaluation as a mutation attempt;
3. use campaign UUID/timestamp identity as semantic attempt identity;
4. hash raw error prose as `FailureSignature`;
5. treat changed patch text, changed source bytes, or changed logs alone as repair progress;
6. use a wall-clock timeout as `NO_PROGRESS`;
7. evict older semantic states from cycle history while the bounded loop remains active;
8. retry an ambiguously dispatched mutation automatically without exact repository re-observation;
9. transfer EHA PASS from a predecessor SHA to a repair SHA;
10. treat focused repair tests as EHA PASS;
11. convert `BUDGET_EXHAUSTED`, `CYCLE_DETECTED`, `NO_PROGRESS`, `UNAUTHORIZED_REPAIR`, `HOST_POSTCONDITION_FAILED`, or repair transport failure into acceptance PASS;
12. reinterpret legacy RC6 free-form repair text as deterministic normalized failure identity without a versioned adapter contract;
13. change `profileSnapshotDigest` or `maxAutomatedAttempts` in place while pretending the same bounded loop continues;
14. introduce a new generic repair/evidence authority merely to store these derived control digests.

---

# 15. Ambiguity and error behavior

| Condition | Required behavior |
| --- | --- |
| repair budget missing | no mutation; terminal `UNAUTHORIZED_REPAIR` / `REPAIR_BUDGET_MISSING` |
| budget is `0` | no mutation; terminal `BUDGET_EXHAUSTED`, attempts `0` |
| budget negative/fractional/out of range | no mutation; terminal `REPAIR_UNAVAILABLE` / `REPAIR_BUDGET_INVALID` |
| aggregate `FAIL` has no deterministic normalized failure atom | no mutation; `REPAIR_UNAVAILABLE` / `FAILURE_IDENTITY_UNAVAILABLE` |
| duplicate `obligationId` | digest invalid; no mutation; `REPAIR_UNAVAILABLE` |
| `NOT_APPLICABLE` without authority-backed rationale code | digest invalid; no mutation; `REPAIR_UNAVAILABLE` |
| profile digest changes mid-loop | stop; `REPAIR_UNAVAILABLE` / `PROFILE_IDENTITY_CHANGED` |
| same ordinal has two different AttemptIds | stop; `REPAIR_UNAVAILABLE` / `ATTEMPT_HISTORY_CONFLICT` |
| stored AttemptId does not recompute | stop; `REPAIR_UNAVAILABLE` / `ATTEMPT_ID_MISMATCH` |
| dispatch failed provably before mutation boundary | no attempt consumed; stop according to explicit denial/unavailability |
| dispatch may have crossed mutation boundary but acknowledgement lost | attempt consumed; do not auto-replay; re-observe exact state; if unresolved stop `REPAIR_UNAVAILABLE` |
| host reports zero effective delta when delta was required | attempt consumed; `HOST_POSTCONDITION_FAILED` |
| focused verification is PASS but fresh acceptance not yet available | no acceptance upgrade; previous result retained; automatic loop cannot claim PASS |
| fresh acceptance is `INCONCLUSIVE` | terminal `ACCEPTANCE_INCONCLUSIVE`; no further auto mutation |
| fresh acceptance is `UNAVAILABLE` | terminal `ACCEPTANCE_UNAVAILABLE`; no further auto mutation |
| source changes but FS+OS digest pair is unchanged | `NO_PROGRESS` |
| FS+OS state returns to an earlier non-adjacent state | `CYCLE_DETECTED` |
| state changes but is not demonstrably “better” | may continue if budget/authorization remain; W9 has no model-scored improvement predicate |

Unknown remains unknown. An ambiguity never becomes implicit permission to mutate.

---

# 16. Adversarial examples

## A1. Cosmetic message churn is not progress

Pre:

```text
oracleId    = tests/update::restart_reload
failureCode = ASSERT_MISMATCH
identityFacts = { expected: "new-version", actual: "old-version" }
raw message = "Expected new-version, got old-version in 0.43s"
```

Post:

```text
same structured fields
raw message = "expected: new-version; actual: old-version [duration 0.81s]"
```

Result:

```text
FailureSignatureBefore == FailureSignatureAfter
ObligationStateDigestBefore == ObligationStateDigestAfter
=> NO_PROGRESS
```

The changed wording and duration are irrelevant.

## A2. Substantive failure class changes

Pre:

```text
failureCode = PROCESS_TIMEOUT
```

Post:

```text
failureCode = ASSERT_MISMATCH
```

with the same obligation result `FAIL`.

Result:

```text
FailureSignature changes
ObligationStateDigest may remain unchanged
RepairStateDigest changes
=> not NO_PROGRESS
```

The loop may continue if bounded budget and authorization remain.

## A3. Obligation state changes while failure code remains

Pre:

```text
A=FAIL, B=FAIL, C=PASS
```

Post:

```text
A=FAIL, B=PASS, C=PASS
```

Even if the remaining normalized failure atom for `A` is unchanged:

```text
ObligationStateDigest changes
=> RepairStateDigest changes
=> not NO_PROGRESS
```

W9 does not need a prose judgement that this is “better.”

## A4. Immediate semantic no-op

```text
state[0] = RS1-A
attempt 1 produces a different Git SHA
state[1] = RS1-A
```

Result:

```text
NO_PROGRESS
```

Different source bytes do not override acceptance-state equality.

## A5. Two-step oscillation

```text
state[0] = A
attempt 1 -> B
attempt 2 -> A
```

Result:

```text
CYCLE_DETECTED
cycleLength = 2
cycleStates = [A, B]
```

No third mutation is permitted automatically.

## A6. Multi-step oscillation

```text
A -> B -> C -> A
```

Result:

```text
CYCLE_DETECTED
cycleLength = 3
cycleStates = [A, B, C]
```

## A7. Missing budget

Input:

```text
initial acceptance = FAIL
maxAutomatedAttempts = absent
```

Result:

```text
attemptsConsumed = 0
lastAcceptanceResult = FAIL
stopReason = UNAUTHORIZED_REPAIR
```

No automatic source mutation is dispatched.

## A8. Explicit zero budget

Input:

```text
initial acceptance = FAIL
maxAutomatedAttempts = 0
```

Result:

```text
attemptsConsumed = 0
lastAcceptanceResult = FAIL
stopReason = BUDGET_EXHAUSTED
```

The distinction from a missing budget is intentional.

## A9. Transport ambiguity after dispatch

Attempt 1 crosses the mutation boundary and the host connection disappears before a result is returned.

Required behavior:

```text
attempt 1 is consumed
same AttemptId is not blindly re-mutated
repository/source identity is re-observed
if exact resulting state cannot be established:
  lastAcceptanceResult remains previous FAIL
  stopReason = REPAIR_UNAVAILABLE
```

Transport failure does not produce acceptance `UNAVAILABLE` unless a fresh acceptance evaluation itself ran and returned `UNAVAILABLE`.

## A10. Focused tests pass without fresh EHA

```text
A = failed EHA exact SHA
A -> mutation -> B
focused repair tests on B = PASS
fresh acceptance for B = not yet run
```

Required behavior:

```text
A remains FAIL
B is not acceptance PASS
W9 may retain focused evidence but cannot terminalize ACCEPTANCE_PASS
```

This preserves RC6 exact-head acceptance.

## A11. Fresh campaign UUID does not perturb semantic identity

A repaired SHA is evaluated in a new campaign with a different timestamp/UUID-derived `campaignId`.

If the same normalized failure and obligation state is observed, campaign-ID churn does not change `FailureSignature`, `ObligationStateDigest`, or `RepairStateDigest`.

Campaign ID remains a lineage reference only.

## A12. Raw free-text legacy repair event

Legacy RC6 contains:

```text
failure = "broken basic path"
```

with no versioned failure identity adapter output.

Required behavior:

```text
FailureSignature = unavailable
no automatic mutation
```

A model MUST NOT hash the sentence and call the result deterministic semantics.

## A13. Watchdog timeout is not semantic no-progress

RC6 bridge emits:

```text
NO_PROGRESS_TIMEOUT
```

because no transport activity occurred before its idle deadline.

Required behavior:

```text
W9 NO_PROGRESS is NOT emitted
```

unless a completed mutation and fresh `FAIL` evaluation establish equal pre/post semantic digests.

## A14. Budget reaches zero on the same attempt that closes a cycle

If the final allowed attempt returns an earlier semantic state:

```text
attemptsConsumed == maxAutomatedAttempts
AND cycle detected
```

Required stop:

```text
CYCLE_DETECTED
```

not `BUDGET_EXHAUSTED`, because cycle detection has higher stop precedence and is the stronger observed termination witness.

---

# 17. Compatibility obligations

## 17.1 RC6 EHA repair compatibility

This freeze preserves all current RC6 rules:

- the failing SHA remains immutable and failed;
- repair produces a new SHA;
- the new SHA is evaluated in a fresh campaign;
- predecessor PASS is not inherited;
- focused repair tests are not EHA;
- architecture-reopening defects remain architecture-reopening defects.

## 17.2 Existing campaign IDs remain valid lineage

Current timestamp/UUID campaign IDs, review IDs, and event IDs remain valid durable EHA lineage identifiers.

RC7 MUST NOT rewrite historical ledgers to replace them with deterministic repair IDs.

W9 simply does not use volatile campaign identity as semantic comparison identity.

## 17.3 Existing legacy EHA result vocabulary

Current runtime EHA durable verdicts are `PASS`/`FAIL`, while the trusted bridge also exposes transport-oriented states such as `INCOMPLETE`, `NOT_RUN`, and explicit transport error reasons.

W9 MUST NOT reinterpret those transport/controller values as acceptance PASS.

The future W6 EHA V2 adapter may expose EBCA `INCONCLUSIVE` and `UNAVAILABLE` explicitly. MF4 freezes how W9 consumes those outcomes; it does not rewrite the current EHA ledger schema.

## 17.4 Watchdog compatibility

Current bridge watchdogs remain independent fail-closed transport controls:

```text
FIRST_RESPONSE_TIMEOUT
CAMPAIGN_START_TIMEOUT
NO_PROGRESS_TIMEOUT
```

They do not become W9 semantic no-progress/cycle evidence.

## 17.5 Acceptance-profile dependency

W9 consumes one immutable `profileSnapshotDigest`.

Until W7 provides the accepted snapshot identity contract, an implementation MUST NOT manufacture a profile digest from current free-form EHA `profile` strings merely to enable automatic mutation.

This is an integration dependency, not an unresolved MF4 semantic decision.

---

# 18. Explicit non-goals

MF4 does **not** freeze or authorize:

1. source editing/patch application mechanics;
2. branch creation, commit creation, or merge mechanics for automatic repair;
3. strategy generation or strategy ranking;
4. model prompts for repair;
5. mutation scope/permission ownership (`EhaRepairCaseV1`, W10);
6. `RepairPacketV1` or `HostExecutionProfileV1` rendering (W11);
7. EHA V2 event storage or schema migration (W6);
8. `AcceptanceProfileSnapshotV1` digest construction (W7/MF2);
9. `RepairLearningRecordV1` storage/promotion (W12);
10. generic “evidence improvement” scores;
11. source-diff similarity as progress;
12. model-based “one more try” decisions;
13. automatic budget extension after exhaustion;
14. a generic persistent repair-control ledger or new claim database.

---

# 19. Downstream contracts now unblocked

## 19.1 W9 bounded deterministic repair

W9 may now implement/test a repair-control evaluator against this contract because implementation no longer needs to choose:

- identity inputs;
- failure comparison semantics;
- obligation-state representation;
- budget counting;
- no-progress equality;
- history window;
- cycle detection;
- stop precedence;
- acceptance/repair result separation.

W9 implementation still depends on upstream/downstream components supplying their own owned inputs, especially a fixed profile snapshot identity and explicit repair authorization. That does not reopen MF4 semantics.

## 19.2 W10 `EhaRepairCaseV1`

W10 may use this freeze as the required control contract for:

- stable strategy ID input;
- explicit authorization result;
- attempt lineage;
- mutation-scope permission;
- exact postcondition obligations.

W10 MUST NOT redefine W9 attempt/budget/no-progress/cycle semantics.

## 19.3 W12 `RepairLearningRecordV1`

W12 may reference:

- terminal `AttemptId` lineage;
- final `FailureSignature`;
- final `ObligationStateDigest`;
- `CycleId` where applicable;
- exact stop reason;
- last acceptance result.

A learning record remains derived and cannot convert a stopped/failed loop into acceptance PASS.

---

# 20. Unresolved items

No unresolved decision remains **inside MF4** that would require a W9 implementation to invent repair-loop identity or termination semantics.

The following are explicit dependencies owned elsewhere and are not MF4 ambiguity:

- exact `AcceptanceProfileSnapshotV1` construction/digest: W7/MF2;
- EHA V2 persistence/result representation: W6;
- mutation permission and repair-case schema: W10;
- RepairPacket/host rendering: W11;
- RepairLearningRecord: W12;
- source-mutation mechanics: implementation work after authority permits it.

If any future workstream changes the assumptions consumed here, it must explicitly reopen this freeze rather than silently changing W9 behavior.

---

# 21. Freeze verdict

The deterministic decisions required by MF4 are complete.

```text
FREEZE STATUS:
FROZEN

UNLOCKS:
W9 bounded deterministic repair

PREREQUISITE FOR:
W10 EhaRepairCase
W12 RepairLearningRecord
```
