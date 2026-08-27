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

**Must not:** claim repository-wide coverage, persist a final report, promote scout/search summaries into findings, orchestrate later slices, or raw-rewrite append-only evidence ledgers.

Use `repo_inventory`, search, exact reads, and bounded host-native scouts as navigation aids. Reopen exact current source before accepting any material claim. Context graphs/Mermaid may summarize verified structure but are not finding evidence.

When the task creates or consumes durable review evidence, read `docs/DURABLE-EVIDENCE-STORE.md`. `state.json` is mutable; `findings.ndjson` and `eha.ndjson` are append-only. Use `review_state_*` and `eha_state_*` rather than raw file edits.

This Skill is intentionally only one reusable competence. Whole-repository or PR review sequencing belongs to the `repository-deep-review` Playbook.
