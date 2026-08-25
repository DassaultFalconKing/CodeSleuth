# CodeSleuth Documentation

## Canonical product contracts

- [`CODESLEUTH-PRODUCT-CONTRACT.md`](CODESLEUTH-PRODUCT-CONTRACT.md) — host/runtime ownership boundary, integration model, extension seams, and core feature freeze.
- [`CODESLEUTH-BRANDING.md`](CODESLEUTH-BRANDING.md) — accepted terminal-native UI/interaction runbook, ASCII identity source, documentation graphics rule, and responsive acceptance.
- [`CODESLEUTH-COLORMAP.json`](CODESLEUTH-COLORMAP.json) — machine-readable semantic colormap.
- [`CONTEXT-GRAPH-DISCIPLINE.md`](CONTEXT-GRAPH-DISCIPLINE.md) — Git source -> review state -> bounded RepositoryContextProjection -> compact context/Mermaid authority chain.
- [`NOVACLAW-MCP.md`](NOVACLAW-MCP.md) — first external-host MCP integration and its read-only repository-evidence boundary.

## README language maintenance

The public README is maintained in three complete language versions:

- [`../README.md`](../README.md) — canonical English source;
- [`../README.ru.md`](../README.ru.md) — Russian translation;
- [`../README.uk.md`](../README.uk.md) — Ukrainian translation.

Every semantic change to `README.md` must update both translations in the same change. Each translated README records the Git blob identity of the English source in a `README-SOURCE-BLOB` comment, and `tests/test_docs_contract.py` fails when either translation is stale. The language selector at the top of every README must continue to link the other two versions.

## Cross-agent operator guide

Root [`../AGENTS.md`](../AGENTS.md) is the maintained LLM/coding-agent operator surface. It is not a second product specification. It tells coding agents how to install, configure, verify, use, bind, unbind, and remove CodeSleuth without violating the product/lifecycle contracts.

`AGENTS.md` records the same canonical English `README.md` Git blob identity with `README-SOURCE-BLOB`. A README change therefore requires an explicit agent-guide parity review before that marker can be advanced. The guide only needs textual changes when agent-operational behavior changed, but its marker must not be refreshed without reviewing the current README and relevant implementation contracts.

The executable docs contract also checks that `AGENTS.md` retains the critical unattended-install and lifecycle surfaces and that its internal relative links resolve.

## Documentation media policy

CodeSleuth documentation is text-first and terminal-native.

- The canonical ASCII brand lives in `pack/.opencode/bin/codesleuth_tui.py` as `CODESLEUTH_ART`; the root README may copy it verbatim.
- UI manuals use terminal/text snapshots captured from the real application and exact implemented labels.
- Maintained PNG/JPEG/WebP/SVG UI mockups/reference boards are not part of the documentation contract.
- Mermaid is the allowed diagram format when relationships are materially clearer as encoded text. Mermaid source is reviewable presentation, not a second source of repository truth.

## Completed implementation packets

- [`archive/CURSOR-PRODUCTION-HANDOFF.md`](archive/CURSOR-PRODUCTION-HANDOFF.md) — completed PR #2 production-hardening packet, retained for historical evidence only. It is not an active task or branch instruction.

## User and operations

- [`USER-GUIDE.md`](USER-GUIDE.md) — install, configure, validate, update, and operate CodeSleuth.
- [`_includes/build-controller-blurb.md`](_includes/build-controller-blurb.md) — canonical OpenCode `build` controller blurb. Public copy: [root README](../README.md#opencode-build-controller).
- [`../AGENTS.md`](../AGENTS.md) — cross-agent operator instructions for safe installation, unattended configuration, verification, use, and removal.

## Maintainers

- [`MAINTAINER-SUBREPO.md`](MAINTAINER-SUBREPO.md) — standalone/subrepo maintenance and integration guidance.

## Contract map

```text
CODESLEUTH-PRODUCT-CONTRACT.md
        |
        +--> CODESLEUTH-BRANDING.md
        |       +--> CODESLEUTH-COLORMAP.json
        |       +--> pack/.opencode/bin/codesleuth_tui.py  (canonical ASCII/TUI)
        |
        +--> CONTEXT-GRAPH-DISCIPLINE.md                  (Mermaid when useful)
        +--> NOVACLAW-MCP.md                              (external host seam)
        +--> ../AGENTS.md                                 (cross-agent operator surface)
        |
        +--> pack/.opencode/themes/codesleuth.json
        +--> pack/.opencode/CODESLEUTH-REPORTS.md
        +--> host runtime / commands / Skills / tools
        +--> .codesleuth/reports/ (host-written analysis where supported)
```

Core CodeSleuth is feature-frozen. Growth continues through profiles, Skills, Playbooks, small tools, host integrations, and extension-management UX without adding a second execution runtime.
