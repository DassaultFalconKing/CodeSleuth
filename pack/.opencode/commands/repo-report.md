---
description: Write or refresh a CodeSleuth analytical report and publish it to the shared reports branch
agent: build
---

Persist an analytical report for this repository. Stay on OpenCode's primary
`build` agent so the native provider-specific controller prompt remains in
effect.

Load the `codesleuth-reports` skill and follow it completely, including:

1. sync the shared Git `reports` branch before reading prior reports;
2. write/update one bounded local `.codesleuth/reports/` Markdown report;
3. update the local index;
4. publish exactly that report through the bounded report publisher.

Requested scope/title:

$ARGUMENTS

If arguments are empty, report the current review/documentation result for
HEAD, or summarize the latest durable review under `.opencode/state/reviews/`
if one exists.

Do not modify application source or move the application branch/HEAD. Structured
review/EHA ledgers remain local and must never be copied to the `reports`
branch. A report publication failure is explicit; do not silently claim the
report is shared when it is only local.
