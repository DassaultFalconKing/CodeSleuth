# CodeSleuth Documentation

## Canonical product contracts

- [`CODESLEUTH-PRODUCT-CONTRACT.md`](CODESLEUTH-PRODUCT-CONTRACT.md) — architecture boundary, OpenCode ownership, extension model, and core feature freeze.
- [`CODESLEUTH-BRANDING.md`](CODESLEUTH-BRANDING.md) — accepted UI/interaction runbook, responsive navigation, screen semantics, ASCII identity, and production visual gate.
- [`CODESLEUTH-COLORMAP.json`](CODESLEUTH-COLORMAP.json) — machine-readable semantic colormap.

## Approved visual references

- [`assets/branding/mobile-reference-board.svg`](assets/branding/mobile-reference-board.svg) — Home, Configuration, Verify, Playbooks, Help at narrow/mobile-oriented widths.
- [`assets/branding/desktop-reference-board.svg`](assets/branding/desktop-reference-board.svg) — same surfaces and menu semantics at wide/desktop widths.

These are reference layouts, not claims that every pixel is already implemented.

## Implementation handoff

- [`CURSOR-PRODUCTION-HANDOFF.md`](CURSOR-PRODUCTION-HANDOFF.md) — frozen-scope implementation/testing prompt for the production-hardening pass.

## User and operations

- [`USER-GUIDE.md`](USER-GUIDE.md) — install, configure, validate, update, and operate CodeSleuth.

## Maintainers

- [`MAINTAINER-SUBREPO.md`](MAINTAINER-SUBREPO.md) — standalone/subrepo maintenance and integration guidance.

## Contract map

```text
CODESLEUTH-PRODUCT-CONTRACT.md
        |
        +--> CODESLEUTH-BRANDING.md
        |       +--> CODESLEUTH-COLORMAP.json
        |       +--> assets/branding/*-reference-board.svg
        |
        +--> pack/.opencode/themes/codesleuth.json
        +--> pack/.opencode/bin/codesleuth_tui.py
        +--> OpenCode runtime / commands / Skills / tools
```

Core CodeSleuth is feature-frozen. Growth continues through profiles, Skills, Playbooks, OpenCode-native tools/plugins, and extension-management UX.
