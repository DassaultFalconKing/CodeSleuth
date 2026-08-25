# Lessons learned — TUI viewport / acceptance hardening

**Status:** maintainer evidence from the `dev/release-0.4.0` acceptance pass  
**Scope:** CORE-HARDENING + DOCS  
**Primary surfaces:** `pack/.opencode/bin/codesleuth_tui.py`, `tests/test_tui_viewport_hardening.py`, docs controller backlinks

This note records what failed during local acceptance, why earlier “green” commits were insufficient, and what maintainers must not repeat.

## Summary

Four regressions appeared together after collapsible side panels and the rewritten README landed:

1. docs contracts missing canonical `../README.md#opencode-build-controller` backlinks;
2. left-nav collapse worked, restore via mouse did not;
3. right help-panel collapse worked, restore via mouse did not;
4. Tools `#update` was displayed/enabled but off-screen at `120x35`.

An intermediate commit made the suite green by weakening the tests (keyboard restore; test-local `scroll_to_widget(#update)`). That hid the product defects. The durable fix restored the mouse/layout assertions and corrected the TUI.

## Failure → root cause → durable fix

| Symptom | Wrong diagnosis / shortcut | Actual root cause | Durable fix |
|---|---|---|---|
| Docs contract fail | N/A (missing links) | Product/branding contracts did not point at the single README controller section | Add contextual backlinks; do not copy the controller diagram |
| Second `#nav-collapse` / `#right-collapse` click leaves rail collapsed | “Pilot hit-testing fails on a 5-column rail” → switch restore to F3/F4 | Textual `Button._on_click` ignores presses while `-active` is set; default `active_effect_duration` is 0.2s, so a fast restore click never calls `press()` | Toggle controls: `compact=True`, `active_effect_duration=0`; enlarge collapsed rails so the control remains a reliable hit target |
| `#update` `OutOfBounds` after `show_surface("tools")` | Scroll `#update` only inside the test | Layout put branding/status between surface copy and `#actions`; `show_surface` scrolled only `#surface` | Group `#surface` + `#actions` as `#operation` and scroll that block; branding/status stay below the operational surface |

## Lessons

### 1. Do not weaken acceptance tests to match broken UI

If a regression test fails, the product under test is the suspect. Keyboard shortcuts and test-only scrolling may exist as *parallel* affordances, but they must not replace the mouse/layout contract the test was written to protect.

Bad pattern:

```python
# collapses with click, restores with F3 because "Pilot is geometry-dependent"
await pilot.click("#nav-collapse")
await pilot.press("f3")
```

Required pattern:

```python
await pilot.click("#nav-collapse")  # collapse
await pilot.click("#nav-collapse")  # restore — same control
```

### 2. Instrument before guessing geometry

For Textual Pilot failures, log:

- widget `region` / `size` / `display`;
- `pilot.click` return value;
- whether `Button.Pressed` / action handlers fire;
- whether the widget still has class `-active`.

In this incident the second click *did* land on the button. Geometry was a secondary concern; the `-active` swallow was decisive.

### 3. Toggle controls must accept an immediate second press

Any control that collapses and restores on the same widget must disable or zero the Textual active-effect window, or the second press within ~200ms is a no-op. Prefer a small helper over sprinkling timers in tests.

### 4. Navigation must surface the *operational* block, not only copy

`show_surface(route)` must make the active surface useful: descriptive copy **and** the contextual actions for that route. Scrolling a headline while leaving Verify / Update / Launch below the fold fails the operator contract even if a “surface is visible” assertion passes.

### 5. Canonical docs stay singular; contracts link, they do not duplicate

Controller explanation lives under README `### OpenCode \`build\` controller` (`#opencode-build-controller`). Product/branding/maintainer docs link with `../README.md#opencode-build-controller` and must not paste the provider-prompt diagram.

### 6. Optional extras must not abort default collection

MCP belongs in `requirements-dev` for release acceptance *and* individual modules that need `mcp` at import time should `pytest.importorskip("mcp")` so a partial local env still runs the core suite. Prefer skip-at-import over collection errors.

### 7. Acceptance is multi-viewport, not one happy size

Exercise at least `80x24`, `120x35`, and `140x40` for TUI changes that touch layout, collapse rails, or surface actions. Compact mode may hide `#wide-nav`; that is intentional — do not “fix” it by forcing the wide rail at narrow widths.

## Residual limitations (honest)

- Compact viewports hide left `#wide-nav` and use `#compact-nav`; only the right help rail remains for side-panel collapse.
- Branding, repository field, and status still live below `#operation` and may require scrolling when the operator leaves Tools for Home/status work.
- F3/F4 remain valid parallel bindings; they are not substitutes for clickable collapse controls.

## Related coding rules

See [`.cursor/rules/tui-viewport-acceptance.mdc`](../.cursor/rules/tui-viewport-acceptance.mdc) for the agent-facing rules derived from this incident.
