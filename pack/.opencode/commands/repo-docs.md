---
description: Build or refresh repository documentation from verified source evidence
agent: repo-documenter
---

Document the repository using the repository-deep-review protocol.

Requested scope/output:

$ARGUMENTS

If no output path is supplied, propose `docs/REPOSITORY-GUIDE.md` as the default.
Inventory and map first. Verify architecture, entry points, configuration,
external integrations, persistence, tests, CI, and operational commands before
drafting. Use scout subagents only for bounded components. Checkpoint progress
so the work can survive compaction/restart.

Do not overwrite authoritative docs merely because code appears newer. Surface
conflicts and provenance. Request edit approval only after the evidence map is
sufficient to support the document.
