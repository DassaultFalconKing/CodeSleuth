# CodeSleuth Documentation

## Canonical product contracts

- [`CODESLEUTH-PRODUCT-CONTRACT.md`](CODESLEUTH-PRODUCT-CONTRACT.md) — host/runtime ownership boundary, integration model, extension seams, and core feature freeze.
- [`CODESLEUTH-BRANDING.md`](CODESLEUTH-BRANDING.md) — accepted terminal-native UI/interaction runbook, ASCII identity source, documentation graphics rule, and responsive acceptance.
- [`CODESLEUTH-COLORMAP.json`](CODESLEUTH-COLORMAP.json) — machine-readable semantic colormap.
- [`CONTEXT-GRAPH-DISCIPLINE.md`](CONTEXT-GRAPH-DISCIPLINE.md) — Git source -> review state -> bounded RepositoryContextProjection -> compact context/Mermaid authority chain.
- [`NOVACLAW-MCP.md`](NOVACLAW-MCP.md) — first external-host MCP integration and its read-only repository-evidence boundary.
- [`CODESLEUTH-NAMING-CUTOVER.md`](CODESLEUTH-NAMING-CUTOVER.md) — naming inventory and staged cutover from historical `review-pack` filenames; 0.4.0 keeps live compatibility names.

## README language maintenance

The public README is maintained in three complete language versions:

- [`../README.md`](../README.md) — canonical English source;
- [`../README.ru.md`](../README.ru.md) — Russian translation;
- [`../README.uk.md`](../README.uk.md) — Ukrainian translation.

Every semantic change to `README.md` must update both translations in the same change. Each translated README records the Git blob identity of the English source in a `README-SOURCE-BLOB` comment, and `tests/test_docs_contract.py` fails when either translation is stale. The language selector at the top of every README must continue to link the other two versions.

## Cross-agent documentation

Root [`../AGENTS.md`](../AGENTS.md) is the compact cross-agent discovery and repository-instruction entry point. Keep it short and broadly applicable so agents do not spend permanent context on task-specific operating detail.

[`LLM-OPERATOR.md`](LLM-OPERATOR.md) is the maintained task-specific LLM/coding-agent operator README. It explains how another agent should install, configure unattended, verify, use, bind, unbind, and remove CodeSleuth without violating the product/lifecycle contracts.

`LLM-OPERATOR.md` records the canonical English `README.md` Git blob identity with `README-SOURCE-BLOB`. A README change therefore requires an explicit operator-guide parity review before that marker can be advanced. The guide only needs textual changes when agent-operational behavior changed, but its marker must not be refreshed without reviewing the current README and relevant implementation contracts.

The executable docs contract checks that `AGENTS.md` continues to route operator tasks to `LLM-OPERATOR.md`, that the operator guide retains the critical unattended-install and lifecycle surfaces, and that internal relative links resolve.

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
- [`LLM-OPERATOR.md`](LLM-OPERATOR.md) — task-specific cross-agent operator manual for safe installation, unattended configuration, verification, use, and removal.
- [`SELF-UPDATE.md`](SELF-UPDATE.md) — floating update, post-update Verify, controlled CodeSleuth process restart, source-checkout reload, and pinned-update boundaries.
- [`_includes/build-controller-blurb.md`](_includes/build-controller-blurb.md) — canonical OpenCode `build` controller blurb. Public copy: [root README](../README.md#opencode-build-controller).

## Maintainers

- [`STABLE-INTEGRATION-BASELINE.md`](STABLE-INTEGRATION-BASELINE.md) — canonical definition of Stable Integration Baseline (SIB), its distinction from MVP and release, eligibility criteria, refactor boundary, and release-construction model.
- [`MAINTAINER-SUBREPO.md`](MAINTAINER-SUBREPO.md) — standalone/subrepo maintenance and integration guidance.
- [`RELEASE-PROCESS.md`](RELEASE-PROCESS.md) — numbered release branch policy and acceptance gates.
- [`CODESLEUTH-NAMING-CUTOVER.md`](CODESLEUTH-NAMING-CUTOVER.md) — product-namespace inventory; runtime rename remains post-0.4.0 work.
- [`LESSONS-LEARNED-VIEWPORT-HARDENING.md`](LESSONS-LEARNED-VIEWPORT-HARDENING.md) — TUI collapse/Tools viewport acceptance lessons and anti-patterns (paired with `.cursor/rules/tui-viewport-acceptance.mdc`).

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
        +--> ../AGENTS.md                                 (compact cross-agent entry point)
        +--> LLM-OPERATOR.md                              (task-specific operator surface)
        |
        +--> pack/.opencode/themes/codesleuth.json
        +--> pack/.opencode/CODESLEUTH-REPORTS.md
        +--> host runtime / commands / Skills / tools
        +--> .codesleuth/reports/ (host-written analysis where supported)
```

Core CodeSleuth is feature-frozen. Growth continues through profiles, Skills, Playbooks, small tools, host integrations, and extension-management UX without adding a second execution runtime.
