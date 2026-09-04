---
description: Write or refresh a CodeSleuth analytical report and publish it to the shared reports branch
agent: build
---

Persist an analytical report for this repository. Stay on OpenCode's primary `build` agent so the native provider-specific controller prompt remains in effect.

Read `.opencode/PROVENANCE-WATERMARK.md`, then load the
`codesleuth-reports` skill and follow it completely, including:

1. ensure a durable review checkpoint exists and bind/load the stable producer
   watermark through `provenance_state_*`;
2. sync the shared Git `reports` branch before reading prior reports;
3. write/update one bounded local `.codesleuth/reports/` Markdown report with
   the verified watermark;
4. update the local index;
5. publish exactly that report through the bounded report publisher.

Requested scope/title:

$ARGUMENTS

If arguments are empty, report the current review/documentation result for HEAD, or summarize the latest durable review under `.opencode/state/reviews/` if one exists.

Historical evidence without provenance must be marked unavailable/`anon`,
never attributed by guesswork. Do not modify application source or move the
application branch/HEAD. Structured review/EHA ledgers remain local and must
never be copied to the `reports` branch. A report publication failure is
explicit; do not silently claim the report is shared when it is only local.
