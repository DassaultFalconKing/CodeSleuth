# TUI User Witness

Status: **experimental**

This adapter applies `docs/USER-WITNESS-PROTOCOL.md` to the CodeSleuth Textual TUI.

It deliberately builds on the existing TUI visual-regression path instead of introducing a second screenshot system. `tests/test_tui_visual_regression.py` already provides headless Textual execution, deterministic viewport sizes, SVG export, event logging, UI logging and `analysis.json`. TUI User Witness adds the missing semantic and user-intent layers.

## Goals

The experiment should make a coding model reason in this order:

1. identify the operator goal;
2. inspect the relevant user journey;
3. inspect what is visible and actionable;
4. state the natural next action and likely confusion points;
5. only then use implementation mapping and source code;
6. produce a before/after user-experience diff with deterministic evidence.

## Non-goals

TUI User Witness does not:

- replace existing tests;
- replace TUI visual regression;
- create a new SIB0 capability class;
- make LLM judgment canonical acceptance evidence;
- introduce a second controller or runtime;
- require the user-facing representation to expose selectors, callback names or internal configuration keys.

## Semantic adapter

`scripts/tui_user_witness.py` contains a compact semantic extractor. It walks the current Textual screen and retains user-relevant nodes while filtering layout-only containers.

The default text rendering hides machine ids. This is the representation intended for a model-as-user probe.

A coding model may explicitly request machine ids during the implementation phase so that a visible control can be mapped back to source selectors without polluting the initial user perspective.

Example default view:

```text
SCREEN CodeSleuthApp
[button] Home
[button] Review
[button] Tools
[button] Settings
[button] Verify
[static] Recent activity
```

Developer mapping may later expose ids:

```text
[button] Settings id=#nav-settings
```

## Journey files

Initial experimental journeys live under:

```text
docs/tui-user-witness/journeys/
```

The first set intentionally covers different UX failure modes:

- `configure-repository.json`: discoverability, configuration completeness and validation;
- `self-install.json`: disabled-policy semantics and ownership boundaries;
- `inspect-playbook.json`: catalog/detail affordance without accidental execution semantics.

These are examples, not a frozen inventory. The experiment should prove the format before broadening coverage.

## Recommended artifact bundle

A mature witness capture should eventually produce this shape without duplicating the current visual regression harness:

```text
artifacts/tui-witness/<journey>/
  00-main.svg
  00-semantic.json
  00-user-view.txt
  01-settings.svg
  01-semantic.json
  01-user-view.txt
  trace.json
  ux-diff.txt
```

The visual file answers what the interface looked like. The semantic file answers what was visible/actionable. The trace answers what the user did and expected. `ux-diff.txt` explains the before/after experience in user terms.

## Coding-agent workflow

Before touching TUI code, the agent should receive only the relevant journey and a user-view semantic state, then emit:

```text
USER GOAL:
...

WHAT USER SEES NOW:
...

EXPECTED NEXT ACTION:
...

WHAT WOULD CONFUSE USER:
...
```

After that checkpoint it may inspect `implementation_mapping` and source.

For review, ask for both:

1. source diff;
2. user-experience diff.

A source change that cannot explain its user-visible effect should be treated as suspicious even if the implementation is technically tidy.

## LLM User Probe

The default probe input must omit `implementation_mapping` and machine ids. The probe should not be told the expected implementation fix.

Suggested prompt:

```text
You are the operator, not the developer.

Use only the stated user goal and the visible/semantic UI evidence.
Do not reason about Python classes, selectors, handlers or tests.

1. What are you trying to accomplish?
2. What would you do next?
3. What do you believe each relevant visible control does?
4. What is confusing or misleading?
5. Can you complete the stated goal from this interface?
```

A disagreement between this probe and deterministic tests is a diagnostic finding, not authority to override the tests.

## Relationship to future GUI User Witness

The future GUI branch should reuse `USER-WITNESS-PROTOCOL.md` unchanged where possible. It should replace only framework-specific capture and accessibility adapters.

If TUI and GUI need different meanings for `goal`, `trajectory`, `affordances` or `must_not_imply`, that is a protocol-design problem to resolve before either experiment is promoted.
