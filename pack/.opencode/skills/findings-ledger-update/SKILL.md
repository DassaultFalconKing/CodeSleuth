---
name: findings-ledger-update
description: Append versioned amendments to the durable findings ledger without rewriting history
slash: true
---

# Findings ledger update

## Atomic contract

**Input:** one existing finding ID (`F-...`), one exact target `reviewId` (or current session), amendment intent (`correct | supersede | retract | close | reopen`), human explanation, and the extra evidence required by that intent. `reopen` and `correct` require verified current source evidence (`path` + `startLine`/`endLine` + current blob SHA/HEAD). `close` requires verification of tests/commands actually run. `supersede` requires an existing same-review replacement `F-...`.

**Objective:** append a versioned amendment event to the sibling `findings-amendments.ndjson` ledger inside the one durable review/evidence authority, updating the *read model* of a finding while preserving the immutable original line in `findings.ndjson`.

**Output:** amendment ID (`FA-...`), original finding ID, `amendmentType`, `lifecycleStatus` (and compatibility alias `derivedStatus`), `latestAmendmentType` / `latestAmendmentId`, new excerpt/blob/HEAD evidence when applicable, and ledger path.

**Stop:** original finding not found, requested transition is illegal, `reopen`/`correct` lack fresh tracked path/range/current blob/HEAD evidence, `path` is not a tracked file, line range exceeds file length or 80-line limit, blob/HEAD cannot be captured, `supersede` target is missing/self/cyclic/already-terminal, amendment history is corrupt/untrustworthy, amendment would require raw-rewriting `findings.ndjson`/`findings-amendments.ndjson`/`eha.ndjson`, or competitive evidence (code vs docs vs tests) is contradictory and unresolved.

**Must not:** delete or edit any existing line in `findings.ndjson`/`eha.ndjson`, invent blob/SHA/excerpt without reading exact current source, treat grep/Mermaid/report prose as finding evidence, claim verification that did not run, derive lifecycle from the last amendment type alone, silently skip torn amendment records, or turn reports into ledger authority.

OpenCode's primary controller owns the work. This Skill only appends already-verified amendment evidence through the supported tool boundary.

## Authority and ledgers

Read `docs/DURABLE-EVIDENCE-STORE.md` and `.opencode/CODESLEUTH-REPORTS.md` before mutating.

```
tracked Git source + exact blob/SHA
        |
        v
.opencode/state/reviews/<reviewId>/
   state.json                     mutable checkpoint (atomic replace)
   findings.ndjson                append-only original findings (never rewritten)
   findings-amendments.ndjson     sibling append-only amendment events (this Skill)
   eha.ndjson                     append-only EHA/SIB/repair ledger (not touched)
        |
        +--> derived: reports / Mermaid / context projection
```

`findings-amendments.ndjson` is a sibling ledger **within one durable review/evidence authority**. It is not a second persistence authority.

* `state.json` is snapshot; `findings.ndjson` is append-only. Correction/supersession is an explicit versioned evidence operation, not history editing (DURABLE-EVIDENCE-STORE §4).
* Reports under `.codesleuth/reports/` are derived views; they never overwrite ledger truth.
* LLM context is ephemeral; after compaction reload via `review_state_load`.
* A review with no amendment file is compatible: findings remain `OPEN`.

## Write boundary

Use the CodeSleuth tool API only:

```
review_state_load
review_state_get_finding
review_state_record_finding        (for supersede -> new F-... + amendment linkage)
review_state_amend_finding         (this Skill's primary writer -> findings-amendments.ndjson)
review_state_get_amendment
review_state_list_amendments
```

Raw `cat`/`grep`/editor inspection is allowed for audit/debug/locating an ID, but is not semantic proof of freshness, blob validity, or exact-head claimability. Do not bypass identity capture, validation, staleness checks, or future schema migrations by opening ledger files and rewriting JSON/NDJSON directly.

If `review_state_load` / `get_finding` / `list_amendments` reports `amendmentLedgerCorrupt` or `lifecycleStatus: UNTRUSTED`, stop. Mutation is refused until the ledger is trustworthy. Do not append onto torn history.

## Lifecycle vs metadata

These are separate axes. Do not map lifecycle from only the last `amendmentType`.

Lifecycle states: `OPEN | REOPENED | CLOSED | RETRACTED | SUPERSEDED`.

Lifecycle operations: `close`, `reopen`, `retract`, `supersede`.

Metadata: `correct` never changes lifecycle.

- `close -> correct` remains `CLOSED`
- `supersede -> correct` remains `SUPERSEDED`
- `reopen -> correct` remains `REOPENED`

`derivedStatus` is a compatibility alias of `lifecycleStatus`. It is lifecycle state, never `CORRECTED`.

`latestAmendmentType` / `latestAmendmentId` carry the metadata axis.

## Amendment taxonomy

| `amendmentType` | axis | when to use | required extra evidence |
|---|---|---|---|
| `correct` | metadata | excerpt/severity/title/recommendation was slightly wrong but lifecycle is unchanged | verified explicit `path:start-end` + current excerpt + `blobHash`/`headSha` |
| `supersede` | lifecycle | finding is replaced by a better-scoped finding | existing same-review `F-...` already recorded, then `supersededBy`; target ≠ source; no cycle; no existing terminal supersession |
| `retract` | lifecycle | finding was invalid (contradicted, doc/test ahead, duplicate) | explanation with exact contradictory evidence; no new excerpt required |
| `close` | lifecycle | bug fixed in current HEAD, verified | `verification` of tests/commands actually run; no new excerpt unless location evidence is supplied |
| `reopen` | lifecycle | previously `CLOSED` finding proven still present | fresh reproduction: explicit `path` + `startLine`/`endLine` (≤80), current blob hash, exact current HEAD/worktree identity |

`close` does **not** delete the finding. It adds a negative-proof obligation (`must_not return`) that later candidates preserve. See `docs/PROTECTED-CAPABILITY-CONTRACTS.md`.

## Legal transition table

```
from \ op     correct           close        reopen         retract       supersede
OPEN          stay OPEN         ->CLOSED     illegal        ->RETRACTED   ->SUPERSEDED
REOPENED      stay REOPENED     ->CLOSED     illegal        ->RETRACTED   ->SUPERSEDED
CLOSED        stay CLOSED       illegal      ->REOPENED     ->RETRACTED   ->SUPERSEDED
RETRACTED     stay RETRACTED    illegal      illegal        illegal       illegal
SUPERSEDED    stay SUPERSEDED   illegal      illegal        illegal       illegal
```

`reopen` from `RETRACTED` is not defined; record a new finding instead of reopening a retraction. Repeated terminal operations fail.

## Supersession graph

For `supersede`:

- target `F-...` must exist in the **same** review;
- target ≠ source;
- reject direct and transitive cycles;
- fail closed on ambiguous/corrupt linkage;
- do not silently replace an existing terminal supersession relation.

## Procedure

1. **Pin identity.** Resolve exact `reviewId` via `review_state_load` (session-bound or explicit). Record `headSha` and dirty state. If the amendment ledger is corrupt/`UNTRUSTED`, stop.
2. **Rehydrate original.** `review_state_get_finding { findingId }`. If not found, stop. Read `lifecycleStatus` (not last amendment type) before choosing an operation.
3. **Check the transition table.** Reject illegal/repeated terminal operations instead of appending them.
4. **Capture current source when required.** For `reopen` and `correct`, read explicit `path:startLine-endLine` from *current* worktree (not remembered prose). Validate tracked file, `lines.length`, 80-line limit, blob via `git hash-object`, and current HEAD/worktree identity.
5. **Classify intent.** Pick exactly one `amendmentType`. For `supersede`, first record the replacement finding via `review_state_record_finding` and capture its new `F-...`; for `close`, ensure verification actually ran.
6. **Append amendment.** Call `review_state_amend_finding`. Tool appends one JSON line to `findings-amendments.ndjson` with `id: FA-...`, `schemaVersion: 1`, `amends: F-...`, `recordedAt`, `blobHash`, `headSha`, `worktreeStatus`.
7. **Verify read model.** Reload via `review_state_load` / `get_finding` / `list_amendments`. Confirm they agree on `lifecycleStatus`, `latestAmendmentId`, `latestAmendmentType`, and counts. Confirm original `F-...` line is unchanged.
8. **Hand off to reports.** If lifecycle is now `CLOSED`/`RETRACTED`/`SUPERSEDED`, invoke `report-bug-closure` (separate Skill) to sync derived `.codesleuth/reports/*.md` + `INDEX.md`. Never let report prose rewrite ledger history.

## Output shape

Return compact JSON plus human line:

```json
{
  "amendmentId": "FA-...",
  "amends": "F-...",
  "amendmentType": "close",
  "lifecycleStatus": "CLOSED",
  "derivedStatus": "CLOSED",
  "latestAmendmentType": "close",
  "reviewId": "...",
  "path": "src/auth/login.ts:42-48",
  "blobHash": "...",
  "headSha": "...",
  "supersededBy": null,
  "ledger": ".opencode/state/reviews/<reviewId>/findings-amendments.ndjson"
}
```

## Stop conditions (do not proceed)

* `reviewId` cannot be resolved (no checkpoint, invalid ID).
* Original `F-...` not in `findings.ndjson` for that `reviewId`.
* Requested `from + op` is illegal per the transition table.
* `reopen` lacks explicit path/range/current blob/HEAD evidence.
* New `path` escapes worktree or is untracked.
* `startLine > endLine` or range >80 or exceeds file length.
* Amendment history is corrupt, torn, or otherwise untrustworthy.
* Amendment would require `git push --force`, amending the failed EHA SHA, or editing ledger lines in place.
* Verification for `close` is synthetic (no test/command actually executed).

## Must not (hard constraints)

* Raw-edit `findings.ndjson`, `findings-amendments.ndjson`, `eha.ndjson`, or `state.json`.
* Treat Mermaid, context graphs, scout summaries, retrieval scores, or prior reports as stronger than exact current source/blob.
* Inherit SIB PASS across SHAs or convert a failed EHA SHA to PASS by ledger editing.
* Split truth into a second durable evidence database/ledger for the same facts (would reopen SIB0 per DURABLE-EVIDENCE-STORE §11).
* Derive lifecycle by mapping only the last amendment type.

## Minimal example

```ts
await review_state_load({ reviewId })
await review_state_get_finding({ reviewId, findingId: "F-..." })

await review_state_amend_finding({
  reviewId,
  findingId: "F-abc",
  amendmentType: "close",
  explanation: "Fixed null-check, verified by tests/auth.test.ts:88-102",
  verification: "python -m pytest tests/auth.test.ts -k test_login_null — PASS",
  regressionTests: ["tests/auth.test.ts"]
})
```

Preserve exact SHA, blob, tests actually run, and limitations in handoff.
