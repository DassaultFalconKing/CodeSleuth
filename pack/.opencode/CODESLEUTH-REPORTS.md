# CodeSleuth analytical reports

OpenCode's primary `build` agent writes durable markdown reports so later
CodeSleuth sessions and other coding assistants can reuse analysis instead of
starting from zero.

Live store (target repository):

```text
.codesleuth/reports/
```

Do not set `prompt` on `build`. This file is discovery and format, not a
replacement controller.

## Who writes, who reads

- **Writer:** OpenCode `build` via `/repo-review`, `/repo-docs`, `/repo-report`,
  and the `codesleuth-reports` skill.
- **Readers:** CodeSleuth, Cursor, Claude, Codex, Copilot, humans.
- Before repeating a review, read `INDEX.md` then the latest matching report.

## Git

`README.md` in the reports folder may be committed. `INDEX.md` and report
bodies are gitignored by default: they may contain secrets, excerpts, or
credentials. Inspect and sanitize before force-adding them to Git.

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
