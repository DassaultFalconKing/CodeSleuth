---
name: development-authority-discovery
description: Reconstruct repository-native planning, implementation-scope, architecture, predecessor, acceptance, archive, and parallel-track authority from exact tracked evidence
slash: true
---

# Development authority discovery

## Atomic contract

**Input:** one clean exact repository SHA and a bounded inventory of repository-native planning, architecture, handoff, acceptance, workflow, and historical documents.

**Objective:** build a `DevelopmentAuthorityMap` that answers what the repository itself says is authoritative for continuing development, without creating a competing roadmap or treating filenames as authority.

**Output:** evidence-bound authority relationships recorded with `development_authority_state_record_edge`, then a bounded map from `development_authority_state_load`.

**Stop:** HEAD changes, tracked bytes are dirty, a claimed relationship lacks a tracked blob and bounded locator, competing authorities cannot be resolved from repository evidence, or determining the next scope requires an operator decision.

**Must not:** infer authority from filenames alone, revive a document explicitly marked superseded/archived, equate newest mtime with authority, invent a missing roadmap, rewrite target documents, turn supporting evidence into planning authority, or combine adjacent parallel tracks merely because they share dependencies.

## Discovery order

1. Freeze exact target with `exact-target-identity`.
2. Inventory likely authority-bearing tracked documents and project-native gate sources. Filename/location is only a discovery hint.
3. Prefer explicit normative statements such as:
   - "only source of truth" / "canonical" / "authoritative";
   - "current implementation session/track";
   - "supersedes" / "superseded by" / "historical" / "archive";
   - "allowed paths" / "exclusions";
   - "prerequisite" / "accepted predecessor";
   - "acceptance criteria" / "definition of done" / required verify commands.
4. Cross-check apparent authority against references from other current documents. A document naming another file as authority is evidence about that relationship, not permission to replace the named source with a summary.
5. Record each relationship separately using one of the canonical relation classes. Use `CONFIRMED` only when repository evidence explicitly supports the relationship; otherwise `PROBABLE` or `UNPROVEN`.
6. Load the finished map and expose unresolved competing authority rather than choosing by narrative plausibility.

## Required relation meanings

- `CANONICAL_PLANNING_AUTHORITY`: repository-declared planning SSOT or equivalent.
- `ACTIVE_IMPLEMENTATION_SCOPE`: currently admissible packet/session/work item.
- `NORMATIVE_ARCHITECTURE`: architecture/ADR authority constraining the active work.
- `ACCEPTANCE_AUTHORITY`: project-native gates or acceptance specification.
- `ACCEPTED_PREDECESSOR`: work explicitly accepted as prerequisite/baseline.
- `SUPPORTING_EVIDENCE`: evidence/current-state material that is not itself the roadmap.
- `SUPERSEDES` / `SUPERSEDED_BY`: explicit authority replacement.
- `HISTORICAL_ARCHIVE`: retained history that must not be revived as current work.
- `ADJACENT_PARALLEL_TRACK`: valid concurrent work outside the selected scope.
- `FORBIDDEN_COMPETING_AUTHORITY`: document/path explicitly forbidden from acting as a second roadmap/authority.

Every recorded edge must carry path, exact Git blob hash, bounded locator, exact target SHA, confidence and rationale. The durable map is derived navigation only. Repository-native documents remain authority.
