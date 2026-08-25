# Cursor Handoff — CodeSleuth production hardening

Use this as the implementation prompt after the current PR contract update.

---

You are working in `DassaultFalconKing/CodeSleuth` on `feature/CodeSleuth_branding` / PR #2.

## Read first

1. `docs/CODESLEUTH-PRODUCT-CONTRACT.md`
2. `docs/CODESLEUTH-BRANDING.md`
3. `docs/CODESLEUTH-COLORMAP.json`
4. `docs/assets/branding/mobile-reference-board.svg`
5. `docs/assets/branding/desktop-reference-board.svg`
6. existing tests and lifecycle scripts on the current branch

Do not infer scope from chat summaries or old review-pack naming.

## Mission

Bring the **existing** CodeSleuth branding/control-shell implementation to production-ready acceptance.

This is a hard feature freeze. Do not invent new core functionality.

CodeSleuth is a control panel over OpenCode. OpenCode and its models own execution, agents, tool calls, Skills, commands, and long-context review. Preserve that boundary.

## Required implementation work

### A. Match the accepted interaction model

Refine the Textual TUI so narrow and wide layouts follow the accepted reference family as far as Textual/terminal constraints reasonably allow.

Navigation semantics:

```text
Home | Review | Evidence | Tools | Settings
```

These are orientation/routing surfaces. Do **not** implement five new engines.

Existing user operations remain centered on:

```text
Configure
Verify
Playbooks
Help
Open CodeSleuth
```

Update/check actions may remain contextual.

### B. Preserve OpenCode-native execution

Audit every CodeSleuth action that launches/uses OpenCode.

Prove that CodeSleuth does not replace or intercept the normal execution model. Existing `/repo-*` commands, Skills, tools, and future OpenCode-native extensions must remain directly usable.

Do not add a CodeSleuth agent loop, tool router, model runtime, or duplicate review engine.

### C. Responsive terminal behavior

Test at minimum:

```text
80x24
120x35
```

Also exercise a narrower mobile/Termux-like viewport.

Requirements:

- no essential horizontal scrolling;
- compact brand identity when full ASCII is too tall/wide;
- repository/readiness/Verify/Help/Open CodeSleuth remain reachable;
- navigation collapses cleanly;
- modal/config screens remain operable.

### D. Production hardening

Review and fix only real defects in:

- install/adopt/update/remove/restore safety;
- managed vs user-owned OpenCode config/theme preservation;
- bootstrap and launcher behavior on POSIX + PowerShell;
- TUI errors/worker lifecycle;
- smoke/Verify correctness;
- extension/profile compatibility paths;
- packaging/path assumptions;
- error messages and recoverability.

### E. Extension seams

Do not build an extension marketplace in this PR.

However, do not close the seams required for later growth of:

- profiles;
- Skills;
- Playbooks;
- OpenCode tools/plugins;
- user-supplied tools installable/loadable through future CLI/TUI extension-management UI.

Any existing code should keep these as OpenCode-owned executable capabilities.

## Tests to run

Discover the current branch's canonical tests rather than assuming only the old lifecycle file exists.

At minimum run all present Python/TUI/project-lifecycle tests plus syntax/JSON checks. Run smoke against a disposable Git repository.

Explicitly add/maintain regression tests for:

1. branding assets/contracts present;
2. narrow/wide TUI composition and critical controls;
3. user-owned theme/tui config preservation;
4. launcher enters OpenCode normally;
5. stable `/repo-*` commands remain installed/addressable;
6. Skills/tools remain OpenCode-native and are not duplicated by CodeSleuth;
7. install -> configure -> Verify -> update -> Verify lifecycle;
8. remove/restore behavior already defined on this branch;
9. no feature-freeze violation in any new code you add.

## Acceptance output

Commit fixes to the branch in small logical commits.

Return a report with:

- exact HEAD;
- changed files/symbols;
- tests run and exact results;
- screenshots/textual snapshots or terminal-size evidence for narrow + wide layouts;
- OpenCode direct-invocation evidence;
- remaining blockers only, not feature suggestions.

If a requirement would need a new core CodeSleuth subsystem, stop and document it instead of implementing it.

---
