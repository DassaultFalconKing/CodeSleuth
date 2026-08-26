---
name: repository-deep-review
description: Inspect one bounded repository slice or contract surface and return exact evidence candidates without orchestrating a whole review campaign
slash: true
---

# Repository bounded review

## Atomic contract

**Input:** one bounded component/path set/contract surface, one exact target identity, and one review question.

**Objective:** inspect that slice deeply enough to explain ownership, control/data flow, contracts, tests, and concrete candidate risks.

**Output:** compact slice report with inspected scope, entry points, invariants, exact `path:line` candidate evidence, related tests/docs, and unknowns.

**Stop:** the requested slice expands into a repository-wide campaign, exact target identity is unavailable, or a material claim cannot be reopened in exact source.

**Must not:** claim repository-wide coverage, persist a final report, promote scout/search summaries into findings, or orchestrate later slices.

Use `repo_inventory`, search, exact reads, and bounded host-native scouts as navigation aids. Reopen exact current source before accepting any material claim. Context graphs/Mermaid may summarize verified structure but are not finding evidence.

This Skill is intentionally only one reusable competence. Whole-repository or PR review sequencing belongs to the `repository-deep-review` Playbook.
