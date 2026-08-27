---
name: target-ownership-map
description: Map one set of portable behaviors into existing target owners without creating duplicate runtime, state, or authority
slash: true
---

# Target ownership map

## Atomic contract

**Input:** portable behavior/invariant list, exact target SHA, and current target product/architecture authority.

**Objective:** assign each portable behavior to the target layer that should own it.

**Output:** one row per behavior with source owner, target owner, evidence, and action: `REUSE`, `EXTEND`, `ADAPT`, `REPLACE_WITH_TARGET_NATIVE`, `OMIT_SOURCE_SPECIFIC`, `DEFER`, or `REQUIRES_ARCHITECTURE_DECISION`.

**Stop:** the target owner is ambiguous, two layers would own the same authority, or the behavior requires a new fundamental capability class.

**Must not:** implement the port, create a second controller/runtime/tool router/source of truth, or import source topology merely because it already exists there.

Prefer existing host-native execution and CodeSleuth extension seams: configuration, Skills, Commands, Playbooks, bounded Tools, plugins, profiles, derived state, and UX exposure.
