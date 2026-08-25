# CodeSleuth Documentation

## Canonical product contracts

- [`CODESLEUTH-PRODUCT-CONTRACT.md`](CODESLEUTH-PRODUCT-CONTRACT.md) — architecture boundary, OpenCode ownership, extension model, and core feature freeze.
- [`CODESLEUTH-BRANDING.md`](CODESLEUTH-BRANDING.md) — accepted UI/interaction runbook, responsive navigation, screen semantics, ASCII identity, and production visual gate.
- [`CODESLEUTH-COLORMAP.json`](CODESLEUTH-COLORMAP.json) — machine-readable semantic colormap.

## Approved visual references

- [`assets/branding/mobile-reference-board.svg`](assets/branding/mobile-reference-board.svg) — Home, Configuration, Verify, Playbooks, Help at narrow/mobile-oriented widths.
- [`assets/branding/desktop-reference-board.svg`](assets/branding/desktop-reference-board.svg) — same surfaces and menu semantics at wide/desktop widths.

These are reference layouts, not claims that every pixel is already implemented.

## Completed implementation packets

- [`archive/CURSOR-PRODUCTION-HANDOFF.md`](archive/CURSOR-PRODUCTION-HANDOFF.md) — completed PR #2 production-hardening packet, retained for historical evidence only. It is not an active task or branch instruction.

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
        +--> pack/.opencode/CODESLEUTH-REPORTS.md
        +--> OpenCode runtime / commands / Skills / tools
        +--> .codesleuth/reports/ (OpenCode-written analysis)
```

Core CodeSleuth is feature-frozen. Growth continues through profiles, Skills, Playbooks, OpenCode-native tools/plugins, and extension-management UX.
