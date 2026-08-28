---
description: Write or refresh a CodeSleuth analytical report for later sessions in this worktree
agent: build
---

Persist an analytical report for this repository. Stay on OpenCode's primary `build` agent so the native provider-specific controller prompt remains in effect.

Read `.opencode/PROVENANCE-WATERMARK.md`, then load the `codesleuth-reports` skill and follow it.

Requested scope/title:

$ARGUMENTS

If arguments are empty, report the current review/documentation result for HEAD, or summarize the latest durable review under `.opencode/state/reviews/` if one exists.

For a current report session, ensure a durable review checkpoint exists, bind the stable opaque actor once with `provenance_state_bind`, then verify it with `provenance_state_load`. Include the resulting watermark as `- provenance:` in the report. Historical evidence without provenance must be marked unavailable/`anon`, never attributed by guesswork.

Write markdown under `.codesleuth/reports/` and update `INDEX.md`. Do not modify application source. Read existing reports first so later assistants in this worktree can reuse them. Report bodies stay local-only by default; do not assume a fresh clone will see them.
