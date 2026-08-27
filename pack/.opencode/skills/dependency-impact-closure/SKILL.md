---
name: dependency-impact-closure
description: Map one changed path set to affected capability contracts and compute the reverse dependency closure from the exact registry
slash: true
---

# Dependency impact closure

## Atomic contract

**Input:** exact target/base-head identity, changed paths, and exact `docs/protected-capabilities.json`.

**Objective:** map direct seed contracts and compute every registered consumer reachable through reverse `depends_on` edges.

**Output:** direct seeds, reverse dependency closure, unmatched changed paths, and any missing/stale registry edge discovered from exact source.

**Stop:** dependency graph is malformed, a known consumer is missing, or exact source contradicts the registry enough that closure would be unsafe.

**Must not:** use an incomplete graph to skip a known consumer, decide final SIB/RC/release acceptance from closure alone, or treat retrieval similarity as a dependency edge.

Ordinary candidate gate selection may consume this output. Full SIB2/accepted-integration/RC/release claims still require their complete canonical profile.
