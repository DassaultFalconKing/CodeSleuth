---
name: codesleuth-reports
description: Sync, persist, and publish one bounded CodeSleuth analytical report from already-verified evidence
slash: true
---

# CodeSleuth reports

## Atomic contract

**Input:** verified findings/results for one scope, exact HEAD/dirty identity,
checks actually run, limitations, and a verified producer watermark.

**Objective:** keep the local `.codesleuth/reports/` mirror current, write or
update one bounded report, then publish that derived Markdown report to the
shared Git `reports` branch.

**Output:** local report path, updated local index, producer provenance, and
shared report commit/status.

**Stop:** evidence identity is missing; provenance is unavailable without being
honestly marked `anon`; the requested report would require inventing unverified
findings; shared sync has a same-name content collision; the `reports` branch
contains non-report paths or diverged history; publication detects a secret
candidate; or remote publication fails.

**Must not:** review the repository, change application source, move the
application branch/HEAD, claim unexecuted checks, turn reports into repository
authority, publish raw structured ledgers, merge `reports` into application
history, raw-rewrite append-only evidence ledgers, or infer producer identity
from Git author metadata.

OpenCode's primary controller owns the work. This Skill only synchronizes and
persists an already-bounded analytical result.

Read `.opencode/CODESLEUTH-REPORTS.md`,
`.opencode/PROVENANCE-WATERMARK.md`, `docs/DURABLE-EVIDENCE-STORE.md`, and
`.codesleuth/reports/README.md` when present. The structured evidence authority
stays under `.opencode/state/reviews/<reviewId>/` and is local-only. Reuse or
supersede an existing report for the same HEAD+scope instead of duplicating it.

## 1. Sync before reading

Use the installed host-native launcher:

```text
Unix:
.opencode/bin/codesleuth-reports sync --repo .

PowerShell:
.opencode/bin/codesleuth-reports.ps1 sync --repo .
```

If no shared branch exists yet, continue from the local mirror. Any other sync
failure is explicit and must not be silently treated as "no reports".

Read `INDEX.md` and the newest matching report before creating a duplicate.

## 2. Write one bounded local report

Name new reports `YYYYMMDDTHHMMSSZ-<slug>.md` in UTC. Include title, date,
exact target HEAD, dirty state, scope, agent label, verified provenance
watermark, findings with exact evidence, paths inspected, checks actually run,
recommendations, and limitations.

For a current durable review, call `provenance_state_load` before writing and
copy its verified `watermark` into `- provenance:`. If the current producer has
not yet been bound, bind it once with `provenance_state_bind` using the stable
opaque session actor. Historical evidence without a sidecar is reported as
unavailable/`anon`, never guessed.

For EHA/SIB work, load `eha_state_load` before writing. The structured EHA
ledger is the durable source for campaign IDs, exact SHAs, SIB verdicts, repair
lineage, and finding IDs; `provenance.json` supplies attribution only. Do not
embed raw `state.json`, `findings.ndjson`,
`findings-amendments.ndjson`, or `eha.ndjson` records in the report.

Update local `INDEX.md` newest first.

## 3. Publish the report

Publish exactly the report body just written:

```text
Unix:
.opencode/bin/codesleuth-reports publish --repo . .codesleuth/reports/<report>.md

PowerShell:
.opencode/bin/codesleuth-reports.ps1 publish --repo . .codesleuth/reports/<report>.md
```

The publisher creates `reports` lazily as an orphan branch, restricts its full
tree to `.codesleuth/reports/**`, regenerates the shared README/index, checks
for name collisions and strong secret candidates, and pushes without checking
the branch out over the application worktree.

Require `applicationHead` in the publisher result to equal the target HEAD
captured for this report. If `publishedRemote` is false, the report is only
shared inside this clone and the result must say so.

Reports are cross-assistant handoff/navigation material. Exact current source,
tests, accepted contracts, and structured exact-head evidence remain stronger.
