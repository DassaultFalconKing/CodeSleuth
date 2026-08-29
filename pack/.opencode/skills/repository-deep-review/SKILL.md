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

Use `repo_inventory`, search, exact reads, and bounded host-native scouts as navigation aids. When an accepted RepositoryContextProjection exists, selected agents should prefer `codesleuth_context_get` for machine-facing orientation because it requires an exact current-head, non-stale projection and returns structured SourceRefs from the canonical bounded query. Raw graph queries and Mermaid remain derived navigation/presentation. Reopen exact current source before accepting any material claim.

Graph consumption follows [`docs/GRAPH-CONSUMPTION-CONTRACT.md`](../../../docs/GRAPH-CONSUMPTION-CONTRACT.md): provider output is candidate structure, `RepositoryContextProjection` is the single normalized repository-context graph contract, `codesleuth_context_get` is the preferred bounded model-facing view, and Mermaid is secondary derived presentation. Never use Graphify output, graph adjacency, or Mermaid text as sufficient material finding evidence.

When the task creates or consumes durable review evidence, read `docs/DURABLE-EVIDENCE-STORE.md`. `state.json` is mutable; `findings.ndjson` and `eha.ndjson` are append-only. Use `review_state_*` and `eha_state_*` rather than raw file edits.

This Skill is intentionally only one reusable competence. Whole-repository or PR review sequencing belongs to the `repository-deep-review` Playbook.
