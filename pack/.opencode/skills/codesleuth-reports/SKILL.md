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

## Write

1. Name the file `YYYY-MM-DDTHHMMZ-<slug>.md` in UTC.
2. Include title, date, HEAD, dirty state, scope, findings with `path:line`
   evidence, paths inspected, checks actually run, recommendations, and
   limitations.
3. Update `INDEX.md` (newest first).
4. Do not claim a check passed unless it ran.

Reports may contain secrets visible to the authorized runtime. Never git-add
them unless the user explicitly asked after sanitizing.
