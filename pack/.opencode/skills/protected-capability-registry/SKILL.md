---
name: protected-capability-registry
description: Resolve one exact Protected Capability Registry query to matching contract records and exact evidence locations
slash: true
---

# Protected capability registry query

## Atomic contract

**Input:** exact target SHA plus one contract id, capability query, path set, or narrow diff seed.

**Objective:** resolve matching records in `docs/protected-capabilities.json` and return their current lifecycle status, dependencies, evidence paths, fingerprints, and contract-owned forbidden regressions.

**Output:** matched contract ids with why each matched and exact registry/evidence locations to inspect next.

**Stop:** target identity is moving, the registry is malformed, or retrieval cannot be confirmed by exact manifest reads.

**Must not:** promote lifecycle status, edit the registry, decide contract meaning from retrieval score, compute an entire release gate, or synthesize code/docs/test agreement.

Use grep/ripgrep and bounded exact reads by default. Existing host-native BM25/embeddings/reranking may retrieve candidates only; exact manifest and source evidence remain authoritative.

Triangulation, forbidden-regression maintenance, dependency closure, and acceptance orchestration are separate Skills/Playbooks.
