# User Witness Protocol

Status: **experimental developer evidence**

User Witness is a compact, machine-readable description of a user experience intended for coding models, reviewers, and UX probes. It does **not** create a new CodeSleuth capability class, runtime authority, evidence authority, or acceptance authority. Canonical CodeSleuth contracts and exact-head acceptance remain authoritative.

The protocol exists to stop coding agents from reconstructing UX intent only from implementation details. A model should first be able to answer: **what is the user trying to accomplish, what can they see, what action looks natural, and what visible result means success?**

## Core rule

> Every significant UI state should be understandable from user intent + visible state + semantic affordances + interaction outcome without reading the implementation.

Implementation identifiers may be attached later as a mapping layer, but they are not part of the default user view.

## Quad-view witness

Each witness combines four views.

### 1. Intent

Describe the operator rather than the implementation:

- role;
- goal;
- entry condition;
- what the user expects to notice first;
- what the user believes the natural next action is;
- what the user must not need to know;
- visible success conditions;
- confusion conditions;
- misleading inferences the interface must not create.

The user section must avoid implementation names such as Python classes, callback names, CSS selectors, database keys, or internal command routing.

### 2. Visual state

Capture the rendered UI at meaningful checkpoints. For Textual this is an SVG screenshot. A future GUI adapter may use screenshots produced by its own deterministic capture path.

Visual state answers: **what does the interface look like?** It does not by itself explain meaning.

### 3. Semantic state

Capture a compact accessibility-like representation of the visible, user-relevant controls and text:

- buttons;
- inputs;
- selects;
- switches and checkboxes;
- tabs and selectable rows;
- headings and labels;
- important help/status text;
- modal/dialog identity;
- focus, value and disabled state where relevant.

Exclude layout-only containers and CSS plumbing. The default representation should omit machine identifiers. A coding pass may request a second representation with implementation identifiers enabled.

Semantic state answers: **what can the user understand and act on?**

### 4. Trajectory

A witness is not only a final screenshot. Record the path:

1. state the user sees;
2. user interpretation or expectation;
3. user-facing action;
4. next visible state;
5. success or confusion signal.

The default user trajectory names controls by their displayed meaning, not selectors. Selectors belong in `implementation_mapping` only.

## Affordances

A witness should record what a control appears to allow and what it must not imply.

Example:

```json
{
  "surface": "Playbook row",
  "appears_as": "selectable catalog item",
  "user_expects": ["inspect details"],
  "user_does_not_expect": ["execute immediately"]
}
```

This is intentionally stronger than asserting that a widget exists. It lets a coding model detect a semantic UX regression before a handler-level test fails.

## Wrong-inference checks

A useful UI can still be wrong if it leads a reasonable user to a false conclusion. Each journey may declare `must_not_imply`, for example:

- an optional provider appears mandatory;
- selecting an informational item appears to execute it;
- CodeSleuth appears to own OpenCode execution;
- self-install appears able to rewrite maintainer policy.

These are diagnostic UX claims, not replacement acceptance contracts.

## THINK-AS-USER checkpoint

Before changing a user-facing surface, a coding agent should produce this short checkpoint from the relevant witness:

```text
USER GOAL:

WHAT USER SEES NOW:

EXPECTED NEXT ACTION:

WHAT WOULD CONFUSE USER:
```

Only after this checkpoint should the model use `implementation_mapping` and inspect the code that realizes the surface.

## Before/after UX diff

Code review should be able to show a semantic difference in addition to a source diff:

```text
USER EXPERIENCE DIFF

BEFORE
Goal: ...
Visible: ...
Problem: ...

AFTER
Goal: ...
Visible: ...
Result: ...
```

The point is not prose volume. The point is to bind a code change to a change in what a user can understand or accomplish.

## Model-as-user probe

A separate model may receive only:

- user goal;
- visual state;
- semantic state without machine identifiers;
- trajectory to the current checkpoint.

It should answer as an operator, not as a developer:

1. What are you trying to accomplish?
2. What would you do next?
3. What do you believe the visible controls do?
4. What is confusing or misleading?
5. Can the stated goal be completed from the visible interface?

This probe is probabilistic diagnostic evidence. It must never silently become canonical acceptance authority.

## Journey format

Journeys are UTF-8 JSON so the base implementation requires no YAML dependency.

Top-level fields:

- `id`: stable journey identifier;
- `surface`: TUI, GUI, or another future adapter;
- `user`: user-only intent contract;
- `entry`: initial user-facing state;
- `trajectory`: ordered checkpoints/actions;
- `affordances`: semantic expectations;
- `implementation_mapping`: optional developer mapping kept out of the default user view.

The `user` object should include:

- `role`;
- `goal`;
- `notice_first`;
- `natural_next_action`;
- `must_not_need_to_know`;
- `success_visible_as`;
- `confusion_if`;
- `must_not_imply`.

## Layering discipline

The intended information flow is:

```text
request
  -> relevant user journey
  -> user goal
  -> visible + semantic state
  -> expected user action/outcome
  -> implementation mapping
  -> code change
  -> before/after witness
  -> deterministic tests
  -> optional model-as-user probe
```

This keeps the model from starting with class names and retrofitting a fictional user story afterward.

## TUI and future GUI adapters

The protocol is intentionally UI-framework-neutral.

- `TUI User Witness` maps Textual screenshots, DOM semantics, Pilot interactions and existing visual-regression artifacts into this protocol.
- A future `GUI User Witness` should reuse this protocol while providing its own visual capture and accessibility/semantic adapter.

Do not fork the meaning of `user`, `trajectory`, `affordances`, or `must_not_imply` between TUI and GUI. Framework-specific details belong in adapter documentation and `implementation_mapping`.
