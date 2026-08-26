---
name: codesleuth-reports
description: Persist one bounded CodeSleuth analytical report and update the local report index from already-verified evidence
slash: true
---

# CodeSleuth reports

## Atomic contract

**Input:** verified findings/results for one scope, exact HEAD/dirty identity, checks actually run, and limitations.

**Objective:** write or update one assistant-readable report under `.codesleuth/reports/` and keep `INDEX.md` coherent.

**Output:** one report path plus updated index entry.

**Stop:** evidence identity is missing, the requested report would require inventing unverified findings, or the user asks to commit sensitive/local report material without an explicit sanitized commit decision.

**Must not:** review the repository, change application source, claim unexecuted checks, or turn reports into repository authority.

OpenCode's primary controller owns the work. This Skill only persists an already-bounded result.

Read `.opencode/CODESLEUTH-REPORTS.md` and `.codesleuth/reports/README.md` when present. Reuse or supersede an existing report for the same HEAD+scope instead of duplicating it.

Name new reports `YYYY-MM-DDTHHMMZ-<slug>.md` in UTC. Include title, date, HEAD, dirty state, scope, findings with exact evidence, paths inspected, checks actually run, recommendations, and limitations. Update `INDEX.md` newest first.

Reports may contain information visible to the authorized runtime. Never git-add them unless the user explicitly requested a sanitized commit.
