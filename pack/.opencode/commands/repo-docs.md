---
description: Build or refresh repository documentation from verified source evidence
agent: build
---

Document the repository using the repository-deep-review protocol. Stay on
OpenCode's primary `build` agent so the native provider-specific controller
prompt for the selected model remains in effect.

Load the `repository-deep-review` skill and follow its documentation mode.

Requested scope/output:

$ARGUMENTS

If no output path is supplied, propose `docs/REPOSITORY-GUIDE.md` as the default.
Inventory and map first. Verify architecture, entry points, configuration,
external integrations, persistence, tests, CI, and operational commands before
drafting. Use `explore` or `repo-scout` Task subagents only for bounded
components. Checkpoint progress so the work can survive compaction/restart.

Do not overwrite authoritative docs merely because code appears newer. Surface
conflicts and provenance. Request edit approval only after the evidence map is
sufficient to support the document. Also persist a markdown summary under
`.codesleuth/reports/` using the `codesleuth-reports` skill so later assistants
can find the documentation pass.
