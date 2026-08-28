---
name: codesleuth-reports
description: Persist one bounded CodeSleuth analytical report and update the local report index from already-verified evidence
slash: true
---

# CodeSleuth reports

## Atomic contract

**Input:** verified findings/results for one scope, exact HEAD/dirty identity, checks actually run, limitations, and a verified producer watermark.

**Objective:** write or update one assistant-readable report under `.codesleuth/reports/` and keep `INDEX.md` coherent.

**Output:** one report path plus updated index entry carrying producer provenance.

**Stop:** evidence identity is missing, provenance is unavailable without being honestly marked `anon`, the requested report would require inventing unverified findings, or the user asks to commit sensitive/local report material without an explicit sanitized commit decision.

**Must not:** review the repository, change application source, claim unexecuted checks, turn reports or provenance into repository authority, raw-rewrite append-only evidence ledgers, or infer producer identity from Git author metadata.

OpenCode's primary controller owns the work. This Skill only persists an already-bounded result.

Read `.opencode/CODESLEUTH-REPORTS.md`, `.opencode/PROVENANCE-WATERMARK.md`, `docs/DURABLE-EVIDENCE-STORE.md`, and `.codesleuth/reports/README.md` when present. Reuse or supersede an existing report for the same HEAD+scope instead of duplicating it.

For a current durable review, call `provenance_state_load` before writing and copy its verified `watermark` into `- provenance:`. If the current producer has not yet been bound, bind it once with `provenance_state_bind` using the stable opaque session actor. Historical evidence without a sidecar is reported as unavailable/`anon`, never guessed.

For EHA/SIB work, load `eha_state_load` before writing. The structured EHA ledger under `.opencode/state/reviews/<reviewId>/eha.ndjson` is the durable source for campaign IDs, exact SHAs, SIB verdicts, and repair lineage. `provenance.json` attributes the producer session only. Reports are derived human-readable projections, not evidence authority.

Name new reports `YYYY-MM-DDTHHMMZ-<slug>.md` in UTC. Include title, date, HEAD, dirty state, scope, agent label, provenance watermark, review/campaign IDs where applicable, findings with exact evidence, paths inspected, checks actually run, recommendations, and limitations. Update `INDEX.md` newest first.

Reports may contain information visible to the authorized runtime. Never git-add them unless the user explicitly requested a sanitized commit.
