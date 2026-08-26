# CodeSleuth analytical reports

OpenCode's primary `build` agent writes durable markdown reports so later
CodeSleuth sessions and other coding assistants in the same worktree can reuse
analysis instead of starting from zero.

Live store (target repository worktree):

```text
.codesleuth/reports/
```

Do not set `prompt` on `build`. This file is discovery and format, not a
replacement controller.

## Who writes, who reads

- **Writer:** OpenCode `build` via `/repo-review`, `/repo-docs`, `/repo-report`,
  `/eha-test`, `/eha-repair`, and the relevant CodeSleuth skills.
- **Readers:** CodeSleuth, Cursor, Claude, Codex, Copilot, humans working in the
  current worktree by default.
- Before repeating a review in that worktree, read `INDEX.md` then the latest
  matching report.

## Structured evidence versus reports

Markdown reports are human-readable summaries. They are not the only durable
evidence authority.

Repository-review findings and EHA campaigns are stored under the existing
ignored review-state boundary:

```text
.opencode/state/reviews/<reviewId>/
  state.json
  findings.ndjson
  eha.ndjson
```

For EHA work, `eha.ndjson` is the structured append-only ledger for exact target
SHAs, SIB0/SIB1/SIB2 verdicts, and repair-loop decisions. A report must summarize
that ledger truthfully; it must not replace, rewrite, or silently contradict it.

## Git and cross-clone reuse

`README.md` in the reports folder may be intentionally committed. `INDEX.md`
and report bodies are excluded from Git by default because they may contain
secrets, source excerpts, or credentials. CodeSleuth writes these default
patterns to the repository-local Git exclude file (`.git/info/exclude`, or the
worktree-aware path returned by `git rev-parse --git-path info/exclude`). It
does **not** silently rewrite the project's tracked `.gitignore` to hide its
runtime/report state.

A fresh clone therefore does not automatically receive local report bodies or
an installer-created `AGENTS.md` pointer. If analysis should travel between
clones, inspect and sanitize it, then deliberately commit the chosen report or
shared repository guidance. Do not force-add unsanitized local evidence merely
to make assistant state portable.

## File names

```text
YYYY-MM-DDTHHMMZ-<slug>.md
```

Example: `20260825T031200Z-architecture.md`

Use UTC. Slug is lowercase kebab-case from the scope (`architecture`,
`pr-main`, `auth-subsystem`, `eha-sib`).

## Report template

```markdown
# <title>

- date: <UTC ISO-8601>
- target: <git rev-parse HEAD>
- dirty: <yes/no; summarize if yes>
- scope: <paths / ref / question>
- agent: OpenCode build
- reviewId: <.opencode/state/reviews/<id> or none>
- ehaCampaignId: <campaign id or none>

## Summary

<one short paragraph>

## EHA / SIB status

- exact target SHA: <full SHA or not an EHA report>
- SIB0: <PASS | FAIL | PENDING> — claimable: <yes/no> — <profile/evidence summary>
- SIB1: <PASS | FAIL | PENDING> — claimable: <yes/no> — <profile/evidence summary>
- SIB2: <PASS | FAIL | PENDING> — claimable: <yes/no> — <profile/evidence summary>
- blocker finding IDs: <ids or none>
- predecessor campaign: <id or none>
- successor campaign: <id or none>

If an EHA repair loop was entered, also record:

- failing SHA and SIB level;
- defect classification;
- failing test/path and reproduction;
- repair decision and branch;
- new candidate SHA, if known;
- regression tests added;
- focused repair tests actually run and their results.

Do not mark a repaired descendant as inheriting PASS from its predecessor. Each
new exact SHA receives its own EHA campaign and fresh evidence for every SIB
degree claimed.

## Findings

### <severity>: <title>
- location: `path:start-end`
- evidence: <what the current source actually does>
- recommendation: <smallest correction direction>

## Paths inspected

- `path` — why

## Checks run

- <command or "not run"> — result

## Recommendations

- <next action for a coding assistant>

## Limitations

- <what was not reviewed>
```

For non-EHA work the EHA section may be omitted or explicitly marked not
applicable.

## INDEX.md

Keep newest first:

```text
- `20260825T031200Z-architecture.md` — 2026-08-25T03:12Z — Architecture — HEAD abc1234 — 2 high
- `20260826T140500Z-eha-sib.md` — 2026-08-26T14:05Z — EHA — HEAD def4567 — SIB0 PASS / SIB1 FAIL / SIB2 PENDING
```
