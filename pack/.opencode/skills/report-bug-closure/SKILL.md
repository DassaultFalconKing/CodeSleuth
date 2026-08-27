---
name: report-bug-closure
description: Sync derived CodeSleuth reports and INDEX.md when findings are closed, superseded, or retracted
slash: true
---

# Report bug-closure sync

## Atomic contract

**Input:** one scope/head-bound report set (`.codesleuth/reports/*.md` + `INDEX.md`), one exact fixing `HEAD` (40-char SHA + dirty state), closed/superseded/retracted finding IDs (`F-...` plus their `FA-...` amendments), verification evidence (commands actually run, blob hashes, failing->passing witness), and limitations.

**Objective:** update the *derived* human-readable report layer to reflect that bugs are closed/fixed, without mutating the append-only evidence ledgers.

**Output:** updated report path (reused `YYYY-MM-DDTHHMMZ-<slug>.md` or new one when HEAD/scope changed), refreshed `INDEX.md` entry (newest first), and explicit cross-links `F-...` ↔ `FA-...` ↔ fixing `HEAD`.

**Stop:** closure lacks verification (no test/command actually executed), exact fixing HEAD/dirty identity cannot be pinned, requested report would require inventing unverified findings, or ledger amendment (`FA-...`) for the closed finding is missing.

**Must not:** rewrite `findings.ndjson`/`findings-amendments.ndjson`/`eha.ndjson`/`state.json`, claim unexecuted checks, turn reports into evidence authority, bypass sanitization before committing reports, or duplicate a report for the same HEAD+scope instead of reusing/superseding it.

OpenCode's primary controller owns the work. This Skill only persists an already-bounded, already-verified closure result.

## Authority chain

```
tracked source + blob/SHA (root)
   |
.opencode/state/reviews/<reviewId>/
   findings.ndjson + findings-amendments.ndjson (append-only truth)
   eha.ndjson (append-only, when present)
       |
       +--> .codesleuth/reports/*.md + INDEX.md (derived, rebuildable)
       +--> Mermaid / context projection (derived)
```

Reports are **projections**, not evidence. When report prose and the structured store disagree, the store wins; regenerate the report (see `docs/DURABLE-EVIDENCE-STORE.md` §8, `.opencode/CODESLEUTH-REPORTS.md`).

For EHA/SIB closures, the structured ledger under `.opencode/state/reviews/<reviewId>/eha.ndjson` is authority for campaign IDs, exact SHAs, SIB verdicts, and repair lineage. Reports summarize it truthfully.

## Preconditions

* Each closed finding has a ledger amendment of type `close`/`supersede`/`retract` via `findings-ledger-update` (`FA-...` exists). Do not close a bug in a report while its ledger still says `OPEN`.
* Fixing HEAD is pinned via `exact-target-identity` (`git rev-parse HEAD`, `git status --porcelain=v1`). Record SHA, dirty state, branch, and `reviewId`/`ehaCampaignId` when applicable.
* Verification is real: at least one focused reproduction or regression test that previously failed now passes, or an explicit why-not-automated witness. Finite happy path ≠ universal proof — include bounded scope/oracle.

## Procedure

1. **Load truth.** `review_state_load` (+ `eha_state_load` for EHA work) and `review_state_get_finding` for each `F-...`. Collect `FA-...` amendments from `findings-amendments.ndjson`. Confirm `amendmentType` ∈ {`close`,`supersede`,`retract`} and `headSha` equals fixing HEAD (or is ancestor when HEAD moved forward via `dev/release-X.Y.Z` integration).
2. **Read existing report.** Open `.opencode/CODESLEUTH-REPORTS.md`, `.codesleuth/reports/README.md` when present, and the latest report for the same `HEAD+scope`. Reuse/supersede it instead of duplicating (naming: `YYYY-MM-DDTHHMMZ-<slug>.md` in UTC, kebab-case slug).
3. **Patch report sections.** Keep template shape from `CODESLEUTH-REPORTS.md`:
   * Header: `date`, `target`, `dirty`, `scope`, `agent: OpenCode build`, `reviewId`, `ehaCampaignId`.
   * `Summary` — one paragraph: what was closed, fixing HEAD, verification.
   * `EHA / SIB status` — when applicable: exact SHAs, SIB0/SIB1/SIB2 claimability, blocker IDs, predecessor/successor campaign, repair lineage (failing SHA, classification, `failingTest`/`failure`/`reproduction`, `repairBranch`, new candidate SHA, regressions, focused tests). Never mark a repaired descendant as inheriting PASS.
   * `Findings` — for each closed finding add amendment annotation, e.g. `### closed: <title> (F-... → FA-...)` with `location: path:start-end`, `closedAt: <ISO>`, `fixingHead: <SHA>`, `verification: <cmd — result>`, `evidence: <what source now does>`, `supersededBy: <F-...>` when relevant.
   * `Paths inspected` / `Checks run` — list **actually executed** focused verification and regression gates (from `findings-ledger-update`'s `verification`/`regressionTests`). Do not claim `python -m pytest` with full profile unless it ran.
   * `Recommendations` — next closure or gate (`invariant-core + affected-closure + new-feature-tests` for ordinary work, full canonical for SIB2/RC).
   * `Limitations` — what was *not* re-verified, stale paths, human-only uncertainty.
4. **Update INDEX.md.** Keep newest first, e.g. `- \`20260826T140500Z-eha-sib.md\` — 2026-08-26T14:05Z — EHA — HEAD def4567 — SIB0 PASS / SIB1 FAIL / SIB2 PENDING` → refresh counts/status for closed bugs (`2 high → 0 high (2 closed FA-...)` or `SIB1 FAIL → PASS after FA-...`). Do not reorder history or delete predecessor entries.
5. **Persist atomically.** Atomic write for report + atomic replace for `INDEX.md`. Reports may contain excerpts/secrets; never `git add` them unless user explicitly requested a sanitized commit.

## Stop conditions (do not proceed)

* No `FA-...` amendment for a claimed closed `F-...`.
* Fixing HEAD cannot be pinned or differs from amendment's `headSha` without documented integration lineage.
* Verification string would be invented (no command/log actually produced).
* Scope would require repository-wide re-review (use `repository-deep-review` Playbook instead).
* User asks to commit unsanitized local report without explicit sanitized decision.

## Must not (hard constraints)

* Raw-rewrite append-only ledgers (`findings.ndjson`, `findings-amendments.ndjson`, `eha.ndjson`).
* Claim SIB claimability that `eha_state_load` does not show for that exact SHA.
* Collapse two distinct HEADs/scopes into one report file.
* Treat report `INDEX.md` ordering or prose as acceptance authority.

## Minimal example

```md
# Auth subsystem — bug closure 2026-08-27

- date: 2026-08-27T14:03Z
- target: a1b2c3d4e5f6... (HEAD)
- dirty: no
- scope: auth-subsystem
- agent: OpenCode build
- reviewId: 20260827T140300Z-a1b2c3d4e5f6-abc12345-1a2b3c4d
- ehaCampaignId: none

## Summary
Closed F-... (null-check) via FA-... on fixing HEAD a1b2c...; `tests/auth.test.ts -k test_login_null` PASS.

## Findings
### closed: null-check bypass (F-abc → FA-def)
- location: `src/auth/login.ts:42-48`
- fixingHead: a1b2c...
- verification: `python -m pytest tests/auth.test.ts -k test_login_null — PASS`
- supersededBy: none

## Checks run
- python -m pytest tests/auth.test.ts -k test_login_null — PASS
- ruff check src/auth/login.ts — PASS

## Limitations
- Full SIB2 not re-run; only affected closure + invariant core.
```

After writing, return one report path plus updated index entry; do not claim ledger mutation.
