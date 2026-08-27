# CodeSleuth analytical reports

OpenCode's primary `build` agent writes durable Markdown reports so later
CodeSleuth sessions and other coding assistants can reuse analysis instead of
starting from zero.

Local working mirror:

```text
.codesleuth/reports/
```

Shared cross-assistant transport:

```text
Git branch: reports
Tree:       .codesleuth/reports/**
```

The `reports` branch is a derived-report channel, not a second state store and
not a release/integration branch.

## Read and write protocol

Every report-producing or report-consuming CodeSleuth workflow follows this
order:

1. resolve the application repository and exact current HEAD;
2. sync the remote `reports` branch into the local `.codesleuth/reports/`
   mirror;
3. read `INDEX.md` and relevant matching reports;
4. perform the requested review/documentation work against exact current source;
5. write or update one bounded local report and refresh `INDEX.md`;
6. publish that one timestamped report to the `reports` branch.

Host-native launchers:

```text
Unix:
  .opencode/bin/codesleuth-reports sync --repo .
  .opencode/bin/codesleuth-reports publish --repo . .codesleuth/reports/<report>.md

PowerShell:
  .opencode/bin/codesleuth-reports.ps1 sync --repo .
  .opencode/bin/codesleuth-reports.ps1 publish --repo . .codesleuth/reports/<report>.md
```

Publication is performed without checking out `reports` over the application
worktree. The application branch and application HEAD must remain unchanged.

The branch is created lazily on first publication. Its history is orphaned from
the application history and its complete tree is restricted to
`.codesleuth/reports/**`. If a pre-existing `reports` branch contains any other
path, CodeSleuth refuses to use it.

If no `origin` remote exists, CodeSleuth may create the local `reports` branch
but must report `publishedRemote: false`; cross-clone sharing has not happened.

## Who writes, who reads

- **Writer:** OpenCode `build` via `/repo-review`, `/repo-docs`,
  `/repo-report`, `/bug-hunt`, `/eha-test`, `/eha-repair`, and the
  `codesleuth-reports` skill.
- **Readers:** later CodeSleuth/OpenCode sessions, Cursor, Claude, Codex,
  Copilot, humans, and other assistants with access to the repository remote.
- Before repeating analysis, sync the shared branch and read `INDEX.md` plus the
  latest relevant reports.
- Reports are ordinary Markdown handoff material. They never override exact
  current source, tests, accepted contracts, or exact-head acceptance evidence.

## Structured evidence versus shared reports

Structured review/EHA evidence stays local:

```text
.opencode/state/reviews/<reviewId>/
  state.json
  findings.ndjson
  findings-amendments.ndjson
  eha.ndjson
```

Those files remain the durable local authority for finding history, exact
target SHAs, EHA/SIB campaigns, repairs, amendments, and claimability. They are
**never** copied to the `reports` branch.

A shared Markdown report may reference a review ID, finding ID, campaign ID, or
exact SHA, but it must summarize the local ledger rather than embedding or
republishing raw ledger records.

For EHA work, `eha.ndjson` remains authoritative. A report is only a
human-readable projection and cannot transfer PASS from one SHA to another.

## Publication safety

Only one timestamped Markdown report body may be published per publish command.
CodeSleuth regenerates the shared `INDEX.md` and shared branch `README.md`.

Publishing fails closed when:

- the report filename is outside the timestamped report convention;
- the same report filename already exists with different content;
- the report contains a strong secret/credential candidate;
- local and remote `reports` history has diverged;
- any non-`.codesleuth/reports/**` path exists in the branch tree;
- remote fetch/push fails or authentication is unavailable.

The secret scan is a guardrail, not a proof of sanitization. Reports should
contain the minimum source excerpts needed to preserve the analytical result.
Never paste credentials, private keys, access tokens, raw `.env` values, or
private connection strings into a shared report.

## Local Git behavior

The local working mirror remains excluded from the application branch through
the repository-local Git exclude mechanism. This prevents normal application
commits from accidentally absorbing derived reports.

The dedicated publisher uses its own isolated report worktree and a narrow
force-add allowlist for `.codesleuth/reports/**`. This is intentionally
different from allowing the primary coding agent to run arbitrary `git push`.

Do not merge the `reports` branch into application, release, SIB, or feature
branches.

## File names

Preferred form:

```text
YYYYMMDDTHHMMSSZ-<slug>.md
```

The existing minute-resolution compatibility form is also accepted:

```text
YYYY-MM-DDTHHMMZ-<slug>.md
```

Use UTC and lowercase kebab-case slugs.

## Report template

```markdown
# <title>

- date: <UTC ISO-8601>
- target: <exact git SHA>
- dirty: <yes/no; summarize if yes>
- scope: <paths / ref / question>
- agent: OpenCode build
- reviewId: <.opencode/state/reviews/<id> or none>
- ehaCampaignId: <campaign id or none>

## Summary

<one short paragraph>

## EHA / SIB status

- exact target SHA: <full SHA or not an EHA report>
- SIB0: <PASS | FAIL | PENDING> — claimable: <yes/no>
- SIB1: <PASS | FAIL | PENDING> — claimable: <yes/no>
- SIB2: <PASS | FAIL | PENDING> — claimable: <yes/no>
- blocker finding IDs: <ids or none>

## Findings

### <severity>: <title>
- location: `path:start-end`
- evidence: <what exact current source actually does>
- recommendation: <smallest correction direction>

## Paths inspected

- `path` — why

## Checks run

- <command or "not run"> — result

## Recommendations

- <next action>

## Limitations

- <what was not reviewed>
```

For non-EHA work the EHA section may be omitted.

## INDEX.md

The local and shared indexes are newest-first catalogs. They are navigation
aids, not evidence authority. A stale index entry never makes a stale report
current.
