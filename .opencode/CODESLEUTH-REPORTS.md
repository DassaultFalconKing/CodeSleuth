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
  and the `codesleuth-reports` skill.
- **Readers:** CodeSleuth, Cursor, Claude, Codex, Copilot, humans working in the
  current worktree by default.
- Before repeating a review in that worktree, read `INDEX.md` then the latest
  matching report.

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
`pr-main`, `auth-subsystem`).

## Report template

```markdown
# <title>

- date: <UTC ISO-8601>
- target: <git rev-parse HEAD>
- dirty: <yes/no; summarize if yes>
- scope: <paths / ref / question>
- agent: OpenCode build
- reviewId: <.opencode/state/reviews/<id> or none>

## Summary

<one short paragraph>

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

## INDEX.md

Keep newest first:

```text
- `20260825T031200Z-architecture.md` — 2026-08-25T03:12Z — Architecture — HEAD abc1234 — 2 high
```
