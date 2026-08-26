---
name: feature-porting-discipline
description: Extract the portable contract and source-specific assumptions of one capability at exact source and target revisions
slash: true
---

# Portable contract extraction

## Atomic contract

**Input:** one source capability at an exact source SHA, one target repository at an exact target SHA, and the requested behavior to preserve.

**Objective:** separate portable behavior/invariants from source-only architecture and implementation accidents.

**Output:** source capability statement, portable invariant list, source-specific assumption list, and conflicts classified as `SOURCE_SPECIFIC_OMIT`, `TARGET_NATIVE_REPLACEMENT`, or `REQUIRES_NEW_ADR_OR_PRODUCT_DECISION`.

**Stop:** source or target identity is unproven, the source implementation/tests cannot substantiate the claimed behavior, or the target authority required to judge portability is missing.

**Must not:** copy files, design the whole target implementation, create branches, silently import source ownership/runtime/state assumptions, or introduce duplicate evidence authority outside `review_state` and its append-only ledgers.

Inspect source implementation, contracts, consumers, and tests. Read current target product/architecture authority. Port behavior, not filenames. Model summaries and old handoffs are discovery leads only. No duplicate authority: the durable evidence ledger remains `review_state` plus append-only finding/EHA history.

Whole source-to-target migration sequencing belongs to the `feature-port` Playbook.
