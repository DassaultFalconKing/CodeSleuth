---
name: findings-ledger-update
description: Append versioned amendments to the durable findings ledger without rewriting history
slash: true
---

# Findings ledger update

## Atomic contract

**Input:** one existing finding ID (`F-...`), one exact target `reviewId` (or current session), verified current source evidence (`path:startLine-endLine` + current blob SHA/HEAD), amendment intent (`correct | supersede | retract | close | reopen`), and human explanation/verification.

**Objective:** append a versioned amendment event to the durable evidence store that updates the *read model* of a finding while preserving the immutable original line in `findings.ndjson` (or its versioned successor ledger).

**Output:** amendment ID (`FA-...`), original finding ID, amendment type, new excerpt/blob/HEAD evidence when applicable, ledger path, and derived read-model status (`OPEN | CORRECTED | SUPERSEDED | RETRACTED | CLOSED | REOPENED`).

**Stop:** original finding not found, `path` is not a tracked file, line range exceeds file length or 80-line limit, blob/HEAD cannot be captured, amendment would require raw-rewriting `findings.ndjson`/`findings-amendments.ndjson`/`eha.ndjson`, or competitive evidence (code vs docs vs tests) is contradictory and unresolved.

**Must not:** delete or edit any existing line in `findings.ndjson`/`eha.ndjson`, invent blob/SHA/excerpt without reading exact current source, treat grep/Mermaid/report prose as finding evidence, claim verification that did not run, or turn reports into ledger authority.

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
   findings-amendments.ndjson     append-only amendment events (this Skill)
   eha.ndjson                     append-only EHA/SIB/repair ledger (not touched)
        |
        +--> derived: reports / Mermaid / context projection
```

* `state.json` is snapshot; `findings.ndjson` is append-only. Future correction/supersession must be an explicit versioned evidence operation, not history editing (DURABLE-EVIDENCE-STORE §4).
* Reports under `.codesleuth/reports/` are derived views; they never overwrite ledger truth.
* LLM context is ephemeral; after compaction reload via `review_state_load`.

## Write boundary

Use the CodeSleuth tool API only:

```
review_state_load
review_state_get_finding
review_state_record_finding        (for supersede -> new F-... + amendment linkage)
review_state_amend_finding         (this Skill's primary writer -> findings-amendments.ndjson)
```

Raw `cat`/`grep`/editor inspection is allowed for audit/debug/locating an ID, but is not semantic proof of freshness, blob validity, or exact-head claimability. Do not bypass identity capture, validation, staleness checks, or future schema migrations by opening ledger files and rewriting JSON/NDJSON directly.

## Amendment taxonomy

| `amendmentType` | when to use | required extra evidence |
|---|---|---|
| `correct` | excerpt/severity/title/recommendation was slightly wrong but finding still stands | verified `path:start-end` + new excerpt + `blobHash`/`headSha` |
| `supersede` | finding is replaced by a better-scoped finding (often split/merged) | new finding `F-...` already recorded via `review_state_record_finding`, then amendment links `supersededBy: F-...` |
| `retract` | finding was invalid (contradicted, doc/test ahead, duplicate) | explanation with exact contradictory evidence, no new excerpt required |
| `close` | bug fixed in current HEAD, verified | fixing `headSha`, verification evidence (`focusedTests`, blob hashes, `verification` text), no new excerpt unless fix changed the location |
| `reopen` | previously closed/retracted finding proven still present | fresh reproduction excerpt + blob/HEAD |

`close` does **not** delete the finding. It adds a negative-proof obligation (`must_not return`) that later candidates preserve. See `docs/PROTECTED-CAPABILITY-CONTRACTS.md`.

## Procedure

1. **Pin identity.** Resolve exact `reviewId` via `review_state_load` (session-bound or explicit). Record `headSha` and dirty state. If `report-bug-closure` will follow, share the same `reviewId`/`headSha`.
2. **Rehydrate original.** `review_state_get_finding { findingId }`. If not found, stop. Keep `_path`, `blobHash`, `headSha` from the stored finding for provenance.
3. **Reopen current source.** Read `path:startLine-endLine` from *current* worktree (not remembered prose). Validate tracked file, `lines.length`, 80-line limit, blob via `git hash-object`. If new location differs, capture new `path:start-end` + excerpt separately.
4. **Classify intent.** Pick exactly one `amendmentType`. For `supersede`, first record the replacement finding via `review_state_record_finding` and capture its new `F-...`; for `close`, ensure verification actually ran (do not claim unexecuted checks).
5. **Append amendment.** Call `review_state_amend_finding` with `{ findingId, amendmentType, explanation, newPath?, startLine?, endLine?, newSeverity?, newTitle?, supersededBy?, verification?, regressionTests? }`. Tool appends one JSON line to `findings-amendments.ndjson` with `id: FA-...`, `amends: F-...`, `recordedAt`, `blobHash`, `headSha`, `worktreeStatus`.
6. **Verify read model.** Reload via `review_state_load` (which now surfaces `findingCount`, `amendmentCount`, and last amendments). Confirm `FA-...` appears and original `F-...` still present.
7. **Hand off to reports.** If intent was `close`/`retract`/`supersede`, invoke `report-bug-closure` (separate Skill) to sync derived `.codesleuth/reports/*.md` + `INDEX.md`. Never let report prose rewrite ledger history.

## Output shape

Return compact JSON plus human line:

```json
{
  "amendmentId": "FA-...",
  "amends": "F-...",
  "amendmentType": "close",
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
* New `path` escapes worktree or is untracked.
* `startLine > endLine` or range >80 or exceeds file length.
* Amendment would require `git push --force`, amending the failed EHA SHA, or editing ledger lines in place.
* Verification for `close` is synthetic (no test/command actually executed).

## Must not (hard constraints)

* Raw-edit `findings.ndjson`, `findings-amendments.ndjson`, `eha.ndjson`, or `state.json`.
* Treat Mermaid, context graphs, scout summaries, retrieval scores, or prior reports as stronger than exact current source/blob.
* Inherit SIB PASS across SHAs or convert a failed EHA SHA to PASS by ledger editing.
* Split truth into a second durable evidence database/ledger for the same facts (would reopen SIB0 per DURABLE-EVIDENCE-STORE §11).

## Minimal example

```ts
// 1. load + rehydrate
await review_state_load({ reviewId })
await review_state_get_finding({ reviewId, findingId: "F-..." })

// 2. verify current source + capture evidence
// 3. append
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
