# CodeSleuth Documentation

## Canonical product contracts

- [`CODESLEUTH-PRODUCT-CONTRACT.md`](CODESLEUTH-PRODUCT-CONTRACT.md) — host/runtime ownership boundary, integration model, extension seams, and core feature freeze.
- [`CODESLEUTH-BRANDING.md`](CODESLEUTH-BRANDING.md) — accepted terminal-native UI/interaction runbook, ASCII identity source, documentation graphics rule, and responsive acceptance.
- [`CODESLEUTH-COLORMAP.json`](CODESLEUTH-COLORMAP.json) — machine-readable semantic colormap.
- [`CONTEXT-GRAPH-DISCIPLINE.md`](CONTEXT-GRAPH-DISCIPLINE.md) — Git source -> review state -> bounded RepositoryContextProjection -> shared scoped query/Mermaid selection and provenance discipline.
- [`NOVACLAW-MCP.md`](NOVACLAW-MCP.md) — first external-host MCP integration and its read-only repository-evidence boundary.
- [`CODESLEUTH-NAMING-CUTOVER.md`](CODESLEUTH-NAMING-CUTOVER.md) — naming inventory and staged cutover from historical `review-pack` filenames; 0.4.0 keeps live compatibility names.
- [`STABLE-INTEGRATION-BASELINE.md`](STABLE-INTEGRATION-BASELINE.md) — SIB0/SIB1/SIB2 architecture-recovery model: initialization freeze, implementation completeness, integration completeness, and release construction from SIB2.
- [`SIB0-CAPABILITY-INVENTORY.md`](SIB0-CAPABILITY-INVENTORY.md) — frozen fundamental capability-class inventory, ownership/dependency map, and must-never-become boundaries for the current architectural generation.
- [`EXACT-HEAD-ACCEPTANCE.md`](EXACT-HEAD-ACCEPTANCE.md) — normative SIB acceptance identity: SIB degree defines what is proven; exact-head acceptance binds that proof to one exact commit SHA.
- [`EHA-REPAIR-LOOP.md`](EHA-REPAIR-LOOP.md) — normative repair discipline when an EHA target fails: freeze, classify, repair, and start a new campaign on a new SHA.
- [`EHA-OPERATING-PLAYBOOK.md`](EHA-OPERATING-PLAYBOOK.md) — operator-facing EHA workflow wiring for release-stream candidate selection, testing, repair, and reporting.
- [`SIB-CANDIDATE-SELECTION.md`](SIB-CANDIDATE-SELECTION.md) — normative contract for selecting future SIB candidates from literal `dev/release-X.Y.Z` heads.
- [`DURABLE-EVIDENCE-STORE.md`](DURABLE-EVIDENCE-STORE.md) — accepted durable review/evidence authority: mutable checkpoint snapshots, append-only finding/amendment/EHA ledgers, and derived views.
- [`TUI-VISUAL-REGRESSION.md`](TUI-VISUAL-REGRESSION.md) — canonical SIB2 TUI visual-regression acceptance gate and artifact contract.
- [`PROTECTED-CAPABILITY-CONTRACTS.md`](PROTECTED-CAPABILITY-CONTRACTS.md) — post-SIB2 protection model: protected capabilities, contract-owned forbidden regressions, Mermaid dependency/impact graphs, dependency-aware development gates, and full-suite SIB2/RC/release preservation.
- [`protected-capabilities.json`](protected-capabilities.json) — machine-readable Protected Capability Registry with code/docs/test provenance, contract fingerprints, dependency/impact metadata, and each contract's own forbidden-regression ledger.
- [`PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md`](PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md) — reusable-instruction model: atomic on-demand Skills, isolated Playbook Steps, Playbooks as orchestration, Commands as user entry points, and Tools as bounded execution primitives.
- [`SEMANTIC-REFIT.md`](SEMANTIC-REFIT.md) — normative semantic-continuity criterion: preserve or explicitly reconcile the product's evidenced semantic surface across implementation and architectural change.

## Engineering articles

Long-form explanatory material lives under [`articles/`](articles/). Articles are non-normative: they may explain the motivation, history, examples, or broader engineering context behind an accepted contract, but canonical contracts and executable acceptance remain authoritative.

- [`articles/STABLE-BASELINES-RU.md`](articles/STABLE-BASELINES-RU.md) — Russian-language article explaining the SIB0/SIB1/SIB2 Stable Baselines model. Normative contract: [`STABLE-INTEGRATION-BASELINE.md`](STABLE-INTEGRATION-BASELINE.md).

## Roadmap and evaluated extensions

- [`MERMAID-GRAPHIFY-AUDIT.md`](MERMAID-GRAPHIFY-AUDIT.md) — audit of the current bounded Mermaid/context-graph implementation and gated evaluation of `Graphify-Labs/graphify` as an optional deterministic structural graph provider. This is a roadmap/incubation document, not approval of a production Graphify dependency.

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

Post-SIB2 feature and regression work is additionally routed through the Protected Capability Registry and its atomic Skills/Playbook. Contract lookup, code/docs/test triangulation, forbidden-regression audit, and dependency closure are separate competencies rather than one permanently loaded protocol.

Multi-step CodeSleuth workflows live under `pack/.opencode/playbooks/`. The host reads a manifest, exposes one Step at a time, and loads only the atomic Skills required by that Step. Direct user-facing Skills remain slash-callable where the host supports it; `/playbook` starts a stored multi-step workflow. See [`PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md`](PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md).

## Documentation media policy

CodeSleuth documentation is text-first and terminal-native.

- The canonical ASCII brand lives in `pack/.opencode/bin/codesleuth_tui.py` as `CODESLEUTH_ART` (documentation identity; not rendered by the live TUI); the root README may copy it verbatim.
- UI manuals use terminal/text snapshots captured from the real application and exact implemented labels.
- Maintained PNG/JPEG/WebP/SVG UI mockups/reference boards are not part of the documentation contract.
- Mermaid is the allowed diagram format when relationships are materially clearer as encoded text. Repository context, protected-capability impact, and EHA history each retain their separate underlying authority; Mermaid source is bounded reviewable presentation, not a second source of truth or an acceptance-transfer mechanism.

## Completed implementation packets

- [`archive/CURSOR-PRODUCTION-HANDOFF.md`](archive/CURSOR-PRODUCTION-HANDOFF.md) — completed PR #2 production-hardening packet, retained for historical evidence only. It is not an active task or branch instruction.

## User and operations

- [`USER-GUIDE.md`](USER-GUIDE.md) — install, configure, validate, update, and operate CodeSleuth.
- [`LLM-OPERATOR.md`](LLM-OPERATOR.md) — task-specific cross-agent operator manual for safe installation, unattended configuration, verification, use, and removal.
- [`SELF-UPDATE.md`](SELF-UPDATE.md) — floating update, post-update Verify, controlled CodeSleuth process restart, source-checkout reload, and pinned-update boundaries.
- [`_includes/build-controller-blurb.md`](_includes/build-controller-blurb.md) — canonical OpenCode `build` controller blurb. Public copy: [root README](../README.md#opencode-build-controller).

## Maintainers

- [`MAINTAINER-SUBREPO.md`](MAINTAINER-SUBREPO.md) — standalone/subrepo maintenance and integration guidance.
- [`RELEASE-PROCESS.md`](RELEASE-PROCESS.md) — numbered release branch policy and acceptance gates.
- [`CODESLEUTH-NAMING-CUTOVER.md`](CODESLEUTH-NAMING-CUTOVER.md) — product-namespace inventory; runtime rename remains post-0.4.0 work.
- [`EXACT-HEAD-ACCEPTANCE.md`](EXACT-HEAD-ACCEPTANCE.md) — required acceptance identity contract for SIB promotion, accepted integration states, RCs, and releases.
- [`EHA-REPAIR-LOOP.md`](EHA-REPAIR-LOOP.md) — required repair discipline when exact-head acceptance fails.
- [`EHA-OPERATING-PLAYBOOK.md`](EHA-OPERATING-PLAYBOOK.md) — required operator workflow for EHA campaigns on the release stream.
- [`SIB-CANDIDATE-SELECTION.md`](SIB-CANDIDATE-SELECTION.md) — required candidate-selection contract for future SIB promotion.
- [`DURABLE-EVIDENCE-STORE.md`](DURABLE-EVIDENCE-STORE.md) — required durable evidence authority and append-only ledger semantics.
- [`TUI-VISUAL-REGRESSION.md`](TUI-VISUAL-REGRESSION.md) — required SIB2 TUI visual-regression gate and artifact contract.
- [`PROTECTED-CAPABILITY-CONTRACTS.md`](PROTECTED-CAPABILITY-CONTRACTS.md) — required preservation discipline for accepted capabilities and their contract-owned forbidden regressions during release feature population.
- [`protected-capabilities.json`](protected-capabilities.json) — queryable machine contract/forbidden-regression registry used for impact selection and preservation review.
- [`PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md`](PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md) — required design contract for atomic Skills and step-isolated Playbooks.
- [`SEMANTIC-REFIT.md`](SEMANTIC-REFIT.md) — semantic-refit authority and refit-readiness criteria for preserving product claims across future change.
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
        |       +--> MERMAID-GRAPHIFY-AUDIT.md            (roadmap/incubation only)
        +--> NOVACLAW-MCP.md                              (external host seam)
        +--> ../AGENTS.md                                 (compact cross-agent entry point)
        +--> LLM-OPERATOR.md                              (task-specific operator surface)
        +--> PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md      (Playbook/Step/Skill/Command/Tool composition)
        +--> STABLE-INTEGRATION-BASELINE.md               (SIB0 -> SIB1 -> SIB2)
        |       +--> SIB0-CAPABILITY-INVENTORY.md         (frozen capability-class inventory)
        |       +--> EXACT-HEAD-ACCEPTANCE.md             (what is proven -> exact SHA carrying the proof)
        |       +--> EHA-REPAIR-LOOP.md                   (failed EHA target -> repair -> new campaign)
        |       +--> EHA-OPERATING-PLAYBOOK.md            (release-stream EHA operator workflow)
        |       +--> SIB-CANDIDATE-SELECTION.md           (literal release-stream head -> EHA target)
        |       +--> DURABLE-EVIDENCE-STORE.md            (checkpoint + append-only ledgers + derived views)
        |       +--> TUI-VISUAL-REGRESSION.md             (canonical SIB2 interface evidence)
        |       +--> PROTECTED-CAPABILITY-CONTRACTS.md    (accepted behavior -> preservation obligations)
        |               +--> protected-capabilities.json  (contracts + impact graph + per-contract FR registry)
        +--> SEMANTIC-REFIT.md                            (semantic surface -> claim reconciliation -> evidence)
        |
        +--> pack/.opencode/themes/codesleuth.json
        +--> pack/.opencode/CODESLEUTH-REPORTS.md
        +--> pack/.opencode/playbooks/                    (stored workflow manifests + isolated Steps)
        +--> pack/.opencode/skills/                       (atomic on-demand competencies)
        +--> .opencode/state/reviews/<reviewId>/eha.ndjson (append-only EHA/SIB/repair ledger)
        +--> host runtime / commands / tools
        +--> .codesleuth/reports/                         (host-written analysis where supported)
```

Core CodeSleuth is feature-frozen. Growth continues through profiles, Skills, Playbooks, small tools, host integrations, and extension-management UX without adding a second execution runtime.
