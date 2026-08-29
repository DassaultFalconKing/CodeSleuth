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

Do not set `prompt` on `build`. This file is discovery and format, not a replacement controller.

For the structured evidence authority and mutation rules, follow
`docs/DURABLE-EVIDENCE-STORE.md`. For producer attribution, follow
`.opencode/PROVENANCE-WATERMARK.md`.

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
  provenance.json
```

Those files remain the durable local authority for finding history, exact
target SHAs, EHA/SIB campaigns, repairs, amendments, and claimability. They are
**never** copied to the `reports` branch.

A shared Markdown report may reference a review ID, finding ID, campaign ID, or
exact SHA, but it must summarize the local ledger rather than embedding or
republishing raw ledger records.

For EHA work, `eha.ndjson` is the structured append-only ledger for exact target SHAs, SIB0/SIB1/SIB2 verdicts, and repair-loop decisions. `provenance.json` attributes the producer session but does not alter ledger truth or claimability. A report must summarize that evidence truthfully; it must not replace, rewrite, truncate, delete, or silently contradict it.

Use `review_state_*` / `eha_state_*` to load or change structured evidence and `provenance_state_*` to bind/load producer attribution. Raw `cat`/`grep` is permitted for read-only audit, debugging, recovery, or locating an ID, but it is not a semantic API and cannot by itself establish freshness, blob validity, exact-head identity, producer attribution, or SIB claimability.

## Provenance

Every new report MUST carry a verified producer watermark:

```text
- provenance: <actor>-<12 lowercase hex>
```

For a current review/report session, bind the actor once with `provenance_state_bind` after `review_state_start`, then load it with `provenance_state_load` before writing the report. If historical evidence has no provenance sidecar, record provenance as unavailable/`anon`; never infer it from Git author metadata.

If a renderer summarizes evidence from another producer, keep renderer `provenance` and source `provenance` distinct. A watermark is attribution metadata, not a cryptographic signature or acceptance result.

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

`README.md` in the reports folder may be intentionally committed. `INDEX.md`
and report bodies remain excluded from the application branch by default
because they may contain secrets, source excerpts, or credentials. CodeSleuth
uses the worktree-aware repository-local Git exclude path and does not silently
rewrite the project's tracked `.gitignore`.

The dedicated publisher uses its own isolated report worktree and a narrow
force-add allowlist for `.codesleuth/reports/**`. This is intentionally
different from allowing the primary coding agent to run arbitrary `git push`.

Analytical Skill results use the same publisher through one CodeSleuth-owned
route registry (`.opencode/publication-routes.json`). The only canonical route
is `reports`. Skills declare `publicationRoute: reports` or inherit
`publication_route` from a Playbook. They must not supply a Git branch name.
Unknown routes fail closed. Publication results are `NOT_REQUESTED`, `PASS`,
or `FAILED` and never rewrite a local analysis PASS into a remote-success claim.

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

Example: `20260825T031200Z-architecture.md`

Use UTC. Slug is lowercase kebab-case from the scope (`architecture`, `pr-main`, `auth-subsystem`, `eha-sib`).

## Report template

New reports SHOULD include this machine-readable header. It is a strict
`key: value` block, not YAML. Critical identity is never inferred from prose.

```markdown
---
reportType: eha
targetSha: <40-character lowercase git SHA>
provenance: <actor>-<12 lowercase hex>
verdict: PASS
reviewId: <optional>
ehaCampaignId: <optional>
findingIds: <optional comma-separated ids>
supersedes: <optional timestamped report filename>
supersededBy: <optional timestamped report filename>
closedBySha: <optional 40-character SHA>
regressionTest: <optional path or path::test>
---

# <title>
```

Required structured fields are `reportType`, `targetSha`, and `provenance`.
Malformed SHAs, conflicting duplicate keys, ambiguous identity fields, and
invalid lifecycle references fail closed. Legacy reports without this block
remain readable; their catalog metadata is `legacy` / `unknown` / `UNKNOWN`.

Lifecycle fields (`supersedes`, `supersededBy`, `closedBySha`,
`regressionTest`) are navigation only. They do not rewrite structured
review/EHA ledgers or transfer acceptance.

```markdown
# <title>

- date: <UTC ISO-8601>
- target: <exact git SHA>
- dirty: <yes/no; summarize if yes>
- scope: <paths / ref / question>
- agent: <host-visible agent/controller label>
- provenance: <actor>-<12 lowercase hex>
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

Do not mark a repaired descendant as inheriting PASS from its predecessor. Each new exact SHA receives its own EHA campaign and fresh evidence for every SIB degree claimed.

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

For non-EHA work the EHA section may be omitted or explicitly marked not applicable.

## INDEX.md

The local and shared indexes are newest-first catalogs rebuilt only from
timestamped report files that physically exist beside them. Ghost entries are
dropped. `README.md` and `INDEX.md` are not report entries.

When machine-readable metadata is present, a row includes report type, exact
target SHA, verdict/status, and the derived relationship of that target to the
current application HEAD (`EXACT`, `ANCESTOR`, `DESCENDANT`, `DIVERGED`, or
`UNKNOWN`). Relationship is computed from Git ancestry, not timestamps.

PASS on exact SHA A is never displayed as PASS on a different current HEAD B.
The catalog may say that A is an ancestor and that acceptance is not transferred.

They are navigation aids, not evidence authority. A stale index entry never makes
a stale report current.
