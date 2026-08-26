# TUI visual regression acceptance

## Status

This document defines the canonical interface-regression evidence used by the
CodeSleuth acceptance workflow and SIB2 EHA profile.

The TUI is not accepted only because widget-level unit tests pass. The canonical
Ubuntu visual-regression job drives the real Textual application headlessly,
records rendered screens and interaction traces, and analyzes the resulting
render against stable interface invariants.

## Canonical artifacts

For each exercised UI state the test suite records:

```text
screen.svg       Textual-rendered screenshot of the exact state
ui.log           CodeSleuth Recent activity / control feedback transcript
events.log       Textual message/event trace for the driven interaction
analysis.json    machine-readable screenshot-analysis summary
```

The workflow also records `textual.log` when Textual emits framework diagnostics.
The CI job uploads the artifact directory even when the visual test fails.

These artifacts are diagnostic acceptance evidence for one exact tested SHA.
They are not a second product-state database, do not replace `review_state`, and
do not become repository or EHA authority by themselves.

## Required scenarios

The canonical visual suite covers at minimum:

- compact and wide Home rendering;
- visible persistent Recent activity console;
- Verify click -> exactly one dispatch + immediate visible feedback;
- Tools/Update click -> exactly one dispatch + immediate visible feedback;
- left navigation collapse and restore;
- right Textual help/key panel collapse and restore.

Each scenario must combine rendered-screen analysis with live widget/layout
assertions. A screenshot existing on disk is not sufficient acceptance evidence.

## Screenshot analysis

The suite exports Textual's SVG render and verifies at minimum:

1. the SVG parses as a real render and is non-empty;
2. expected user-visible strings are present in the rendered screen;
3. critical widgets stay within the declared terminal viewport;
4. collapse/restore state matches the live widget tree;
5. the screen does not contain a traceback;
6. the UI activity log contains the expected immediate control feedback;
7. one user action dispatches one runtime action where the interaction contract
   requires single dispatch.

The suite intentionally avoids a raw pixel-perfect PNG golden. Font rendering,
terminal metrics, and supported Textual 8.x patch/minor versions can otherwise
turn harmless rendering differences into false failures. Stable semantic and
layout invariants are the acceptance boundary.

## Exact-head rule

The visual job checks out and explicitly verifies
`CODESLEUTH_ACCEPTANCE_SHA`, exactly like the other canonical acceptance jobs.
Screenshots and logs therefore belong only to that exact SHA.

A screenshot from an ancestor, PR synthetic merge ref, repair branch, or
otherwise tree-similar commit does not transfer visual acceptance to the
selected SIB candidate.

## SIB2 consequence

For a CodeSleuth SIB2 claim, the canonical TUI visual-regression job is part of
the interface composition evidence. A failing visual scenario is a composition
or interface blocker and is handled through the normal EHA repair loop.
