# CodeSleuth Documentation

## User and operations

- [`USER-GUIDE.md`](USER-GUIDE.md) — install, configure, validate, update, and operate CodeSleuth.
- [`CODESLEUTH-BRANDING.md`](CODESLEUTH-BRANDING.md) — accepted UI branding runbook/playbook, ASCII identity, screen composition, terminology, state semantics, responsive rules, and local visual acceptance gate.
- [`CODESLEUTH-COLORMAP.json`](CODESLEUTH-COLORMAP.json) — machine-readable canonical semantic colormap used by CodeSleuth user-facing surfaces.

## Maintainers

- [`MAINTAINER-SUBREPO.md`](MAINTAINER-SUBREPO.md) — standalone/subrepo maintenance and integration guidance.

## Branding implementation

The accepted branding contract is implemented by:

```text
docs/CODESLEUTH-BRANDING.md
        |
        +--> docs/CODESLEUTH-COLORMAP.json
        |
        +--> pack/.opencode/themes/codesleuth.json
        |
        +--> pack/.opencode/bin/codesleuth_tui.py
```

When intentionally changing CodeSleuth user-facing identity, terminology, state-color semantics, or ASCII presentation, update the branding runbook and colormap in the same change.
