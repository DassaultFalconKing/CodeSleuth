---
name: contract-triangulation
description: Determine one contract's current meaning by comparing exact code/config, normative documentation, and executable tests
slash: true
---

# Contract triangulation

## Atomic contract

**Input:** one contract/capability question, exact target SHA, and candidate code/docs/test evidence locations.

**Objective:** determine whether the three evidence families agree on one contract.

**Output:** concise contract statement plus evidence triad and one status: `AGREE`, `CODE_AHEAD`, `DOC_AHEAD`, `TEST_AHEAD`, `CONTRADICTED`, or `UNPROVEN`.

**Stop:** a material family cannot be located/read or the evidence is genuinely contradictory.

**Must not:** average contradictory sources, edit them to force agreement, infer acceptance maturity, or expand into unrelated contracts.

Read exact source/config, the narrowest normative/public promise, and executable acceptance/regression tests. Search and generated summaries are navigation only. If a family legitimately does not exist, report that absence instead of manufacturing evidence.
