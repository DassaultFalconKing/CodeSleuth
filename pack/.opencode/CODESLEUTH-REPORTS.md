# CodeSleuth analytical reports

OpenCode's primary `build` agent writes durable markdown reports so later CodeSleuth sessions and other coding assistants in the same worktree can reuse analysis instead of starting from zero.

Live report store (target repository worktree):

```text
.codesleuth/reports/
```

Do not set `prompt` on `build`. This file is discovery and format, not a replacement controller.

For the underlying structured evidence authority and mutation rules, follow `docs/DURABLE-EVIDENCE-STORE.md`. For producer attribution, follow `.opencode/PROVENANCE-WATERMARK.md`.

## Who writes, who reads

- **Writer:** OpenCode `build` via `/repo-review`, `/repo-docs`, `/repo-report`, `/eha-test`, `/eha-repair`, and the relevant CodeSleuth skills.
- **Readers:** CodeSleuth, Cursor, Claude, Codex, Copilot, humans working in the current worktree by default.
- Before repeating a review in that worktree, read `INDEX.md` then the latest matching report.

## Structured evidence versus reports

Markdown reports are human-readable derived views. They are not the structured evidence authority and must never become a competing state store.

Repository-review findings and EHA campaigns are stored under the existing ignored review-state boundary:

```text
.opencode/state/reviews/<reviewId>/
  state.json          # mutable atomic checkpoint snapshot
  findings.ndjson     # append-only finding history
  eha.ndjson          # append-only EHA/SIB/repair history
  provenance.json     # immutable producer/session attribution sidecar
```

For EHA work, `eha.ndjson` is the structured append-only ledger for exact target SHAs, SIB0/SIB1/SIB2 verdicts, and repair-loop decisions. `provenance.json` attributes the producer session but does not alter ledger truth or claimability. A report must summarize that evidence truthfully; it must not replace, rewrite, truncate, delete, or silently contradict it.

Use `review_state_*` / `eha_state_*` to load or change structured evidence and `provenance_state_*` to bind/load producer attribution. Raw `cat`/`grep` is permitted for read-only audit, debugging, recovery, or locating an ID, but it is not a semantic API and cannot by itself establish freshness, blob validity, exact-head identity, producer attribution, or SIB claimability.

## Provenance

Every new report MUST carry a verified producer watermark:

```text
- provenance: <actor>-<12 lowercase hex>
```

For a current review/report session, bind the actor once with `provenance_state_bind` after `review_state_start`, then load it with `provenance_state_load` before writing the report. If historical evidence has no provenance sidecar, record provenance as unavailable/`anon`; never infer it from Git author metadata.

If a renderer summarizes evidence from another producer, keep renderer `provenance` and source `provenance` distinct. A watermark is attribution metadata, not a cryptographic signature or acceptance result.

## Git and cross-clone reuse

`README.md` in the reports folder may be intentionally committed. `INDEX.md` and report bodies are excluded from Git by default because they may contain secrets, source excerpts, or credentials. CodeSleuth writes these default patterns to the repository-local Git exclude file (`.git/info/exclude`, or the worktree-aware path returned by `git rev-parse --git-path info/exclude`). It does **not** silently rewrite the project's tracked `.gitignore` to hide its runtime/report state.

A fresh clone therefore does not automatically receive local report bodies or an installer-created `AGENTS.md` pointer. If analysis should travel between clones, inspect and sanitize it, then deliberately commit the chosen report or shared repository guidance. Do not force-add unsanitized local evidence merely to make assistant state portable.

## File names

```text
YYYY-MM-DDTHHMMZ-<slug>.md
```

Example: `20260825T031200Z-architecture.md`

Use UTC. Slug is lowercase kebab-case from the scope (`architecture`, `pr-main`, `auth-subsystem`, `eha-sib`).

## Report template

```markdown
# <title>

- date: <UTC ISO-8601>
- target: <git rev-parse HEAD>
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

Do not mark a repaired descendant as inheriting PASS from its predecessor. Each new exact SHA receives its own EHA campaign and fresh evidence for every SIB degree claimed.

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

For non-EHA work the EHA section may be omitted or explicitly marked not applicable.

## INDEX.md

Keep newest first:

```text
- `20260825T031200Z-architecture.md` — 2026-08-25T03:12Z — Architecture — HEAD abc1234 — 2 high
- `20260826T140500Z-eha-sib.md` — 2026-08-26T14:05Z — EHA — HEAD def4567 — SIB0 PASS / SIB1 FAIL / SIB2 PENDING
```
