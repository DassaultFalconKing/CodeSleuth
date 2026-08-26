---
name: acceptance-matrix-design
description: Design one objective acceptance matrix for a bounded capability or port before implementation or promotion
slash: true
---

# Acceptance matrix design

## Atomic contract

**Input:** one bounded contract/capability, its intended behavior, known forbidden regressions, and target environment constraints.

**Objective:** define the smallest objective proof matrix that distinguishes correct behavior from known failure states.

**Output:** positive, negative, stale-state, boundary/large-input, ownership/non-duplication, and environment checks with expected outcomes and evidence source.

**Stop:** the contract is contradicted/unproven or expected behavior cannot be stated objectively enough to test.

**Must not:** implement the tests, weaken existing canonical gates, substitute mocks for the only meaningful boundary, or call a proposed matrix acceptance evidence.

The matrix is a design artifact. Actual acceptance exists only after the required checks execute against the exact candidate identity.
