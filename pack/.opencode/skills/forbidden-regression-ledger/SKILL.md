---
name: forbidden-regression-ledger
description: Derive or audit one contract's forbidden-regression ledger and assign SIB0, SIB1, or SIB2 origin to each negative obligation
slash: true
---

# Forbidden regression ledger

## Atomic contract

**Input:** one contract, exact target SHA, its current contract statement/evidence, and known accepted or observed bad states.

**Objective:** produce or audit that contract's own non-empty `forbidden_regressions` ledger.

**Output:** stable `FR-*` entries with owning contract, `sib_origin`, concrete `must_not`, and proof/evidence paths where available; plus any ledger gap or unjustified weakening.

**Stop:** contract meaning is contradicted/unproven, an accepted FR is being removed without explicit supersession/deprecation/removal authority, or SIB origin cannot be assigned responsibly.

**Must not:** create a vague global regression list, silently delete accepted obligations, infer SIB acceptance from merge status, or claim proof that has not run.

Use SIB0 for architectural forbidden states, SIB1 for capability/basic-contract failures, and SIB2 for composition/integration failures. Every recorded contract owns a non-empty ledger from creation; normative force increases as relevant SIB/EHA evidence accepts the behavior.
