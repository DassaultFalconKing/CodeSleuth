---
name: codesleuth-reports
description: Persist and update CodeSleuth analytical reports for later sessions in this worktree
---

# CodeSleuth reports

OpenCode's primary `build` agent owns this work. Do not switch to a custom
supervisor and do not set `agent.prompt` on `build`.

Write assistant-readable markdown under:

```text
.codesleuth/reports/
```

Create the folder if needed. Follow `.opencode/CODESLEUTH-REPORTS.md` and
`.codesleuth/reports/README.md`.

## Before writing

1. Read `.codesleuth/reports/INDEX.md` if it exists.
2. Reuse or supersede an existing report for the same HEAD+scope instead of
   duplicating it. If HEAD moved, write a new file and note the predecessor.
3. Stay out of source trees: the only required writes are
   `.codesleuth/reports/*.md`. Do not edit application code unless the user
   asked.
4. If this is EHA/SIB work, load `eha_state_load` before writing. The structured
   EHA ledger under `.opencode/state/reviews/<reviewId>/eha.ndjson` is the
   durable source for campaign IDs, exact SHAs, SIB verdicts and repair lineage.

## Write

1. Name the file `YYYY-MM-DDTHHMMZ-<slug>.md` in UTC.
2. Include title, date, HEAD, dirty state, scope, findings with `path:line`
   evidence, paths inspected, checks actually run, recommendations, and
   limitations.
3. For EHA reports also include:
   - review ID and EHA campaign ID;
   - exact target SHA;
   - SIB0/SIB1/SIB2 PASS/FAIL/PENDING;
   - whether each SIB degree is actually claimable on that SHA;
   - blocker finding IDs;
   - repair decision/branch/candidate/regression/focused tests when applicable;
   - predecessor/successor campaign relationships.
4. Never describe a repaired SHA as inheriting acceptance from a failed
   predecessor. Report the old failed campaign and the new campaign separately.
5. Update `INDEX.md` (newest first).
6. Do not claim a check passed unless it ran.

Reports are human-readable projections of durable evidence. Do not edit report
prose to contradict `findings.ndjson` or `eha.ndjson`; correct the underlying
record only through the appropriate evidence operation when the record itself
is wrong.

Reports may contain secrets visible to the authorized runtime. Never git-add
them unless the user explicitly asked after sanitizing.
