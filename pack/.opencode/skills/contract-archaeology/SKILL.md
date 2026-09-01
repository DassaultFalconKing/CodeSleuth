---
name: contract-archaeology
description: Discover candidate repository contracts from exact code/config, public or normative documentation, tests/CI, schemas and operator surfaces without promoting discoveries to authority
slash: true
---

# Contract archaeology

## Atomic contract

**Input:** one immutable repository SHA, a bounded component/surface map, and exact tracked source locations.

**Objective:** discover plausible existing behavioral, architectural, compatibility, lifecycle, persistence, protocol, CLI/API/config, or operator contracts that the repository already appears to rely on.

**Output:** bounded candidate contracts with exact evidence locations and a proposed negative obligation for each. Candidates are navigation/adjudication material only and are not repository contract authority.

**Stop:** exact HEAD moves; relevant evidence cannot be read exactly; the requested surface becomes unbounded; or a candidate cannot be stated without inventing intent.

**Must not:** create or edit `docs/protected-capabilities.json`, infer SIB/PROTECTED lifecycle state, treat retrieval score as authority, silently resolve contradictory sources, or promote implementation accidents merely because they are repeated.

## Discovery surfaces

Search narrowly across the mapped component for contract-shaped evidence in:

- public README/user/operator promises;
- ADRs, architecture and design documents;
- CLI commands, flags, exit behavior and help text;
- public APIs, interfaces, schemas and serialized formats;
- configuration keys/defaults and environment variables;
- persistence, migration and compatibility behavior;
- install/update/start/restart lifecycle behavior;
- executable acceptance/regression tests and CI gates;
- documented error behavior, deprecations and compatibility guarantees.

Generated summaries, embeddings, BM25, Graphify and Mermaid may locate candidates. They do not establish contract meaning.

## Candidate discipline

For every candidate, produce:

- stable proposed contract id;
- one concise contract statement;
- capability class and class id proposal;
- exact `code_evidence[]`, `doc_evidence[]`, `test_evidence[]` paths that actually exist;
- affected path patterns and dependency hypotheses;
- at least one concrete `must_not` forbidden-regression candidate;
- the question that `contract-triangulation` must answer next.

Do not force three evidence families to exist. Missing evidence is itself information and may result in `UNPROVEN` during triangulation.

A candidate remains a candidate until exact evidence is triangulated and a user explicitly adjudicates it.
