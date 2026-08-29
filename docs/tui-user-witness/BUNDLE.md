# TUI User Witness capture bundle

Status: experimental developer evidence.

This directory defines the concrete artifact emitted by the TUI User Witness recorder. The bundle is intentionally separate from canonical acceptance evidence: it helps a coding model reason from operator intent and visible behavior, but it never decides whether a commit is accepted.

## Bundle layout

A recorder run writes:

```text
<bundle>/
  journey.json
  manifest.json
  trajectory.json
  ux-diff.txt
  00-<state>/
    screen.svg
    semantic.json
    user-view.txt
    developer-view.txt
    user-probe.txt
    ux-diff.txt
  01-<state>/
    ...
```

`screen.svg`
: Exact Textual render exported at the checkpoint when screenshot capture is enabled.

`semantic.json`
: Compact accessibility-like state. It keeps machine ids and widget types for later implementation mapping.

`user-view.txt`
: User-safe semantic view. Widget ids, selectors, class names and handler names are deliberately absent.

`developer-view.txt`
: The same semantic state with widget type and id mapping. This is for the coding pass after the model-as-user pass.

`user-probe.txt`
: Prompt that asks a model to reason as the operator from the journey contract and current user-safe semantic state.

`trajectory.json`
: What was actually captured: ordered checkpoints, the user-facing action associated with each checkpoint, expectation text and artifact paths.

`ux-diff.txt`
: User-facing semantic change between adjacent checkpoints. It reports visible additions, removals and state changes without leaking machine ids.

`manifest.json`
: Bundle index. It permanently declares `diagnostic_only: true` and `acceptance_authority: false`.

## Two-pass use

The intended coding workflow is deliberately asymmetric.

### Pass 1: operator

Give the model:

- the relevant journey;
- `screen.svg`;
- `user-view.txt`;
- `ux-diff.txt`;
- `user-probe.txt`.

Do not give it selectors, Python classes or handler names unless the task specifically requires debugging an implementation detail.

The model answers:

1. What am I trying to accomplish?
2. What would I do next?
3. What do I believe the visible controls do?
4. What is confusing or misleading?
5. Can I complete the goal?

### Pass 2: developer

Only after the operator interpretation is recorded, give the coding model:

- the operator interpretation;
- `developer-view.txt`;
- implementation code;
- deterministic tests and protected contracts.

This ordering is the point of the experiment. If implementation mapping is supplied first, the model tends to explain what the code means instead of noticing what the user experiences.

## Recorder API

```python
journey = load_journey(Path("docs/tui-user-witness/smoke/home-orient.json"))
recorder = WitnessRecorder(journey, artifact_dir)

async with app.run_test(size=(120, 35)) as pilot:
    await pilot.pause()
    capture_textual_checkpoint(
        app,
        recorder,
        "home",
        action={"kind": "observe", "label": "Open CodeSleuth"},
        user_expects="Repository identity and navigation are understandable.",
    )

manifest = recorder.finalize()
```

`capture_textual_checkpoint()` intentionally does not import Textual. It only requires an app with `screen` and `export_screenshot()`. That keeps the common witness representation portable to a future GUI adapter.

## GUI follow-on

The future GUI User Witness should reuse:

- journey user-intent fields;
- manifest and trajectory semantics;
- user/developer view separation;
- user-facing UX diff;
- model-as-user probe contract.

It should replace only the capture adapter:

```text
TUI:
Textual screen -> semantic_snapshot -> SVG

GUI:
accessibility tree / DOM -> semantic_snapshot -> screenshot
```

If the GUI implementation requires a different user-intent schema, that is evidence the common protocol is wrong and should be revised explicitly rather than forked silently.

## Non-goals

The bundle is not:

- a new CodeSleuth runtime;
- a controller;
- a replacement for Textual tests;
- a replacement for visual regression;
- a replacement for SIB/EHA;
- permission to accept a probabilistic LLM opinion as a gate.

The deterministic UI and repository contracts remain authoritative. User Witness adds a second question: even when the code is valid, does the interface make sense to the person operating it?
