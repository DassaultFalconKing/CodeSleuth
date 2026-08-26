# CodeSleuth Documentation

## Canonical product contracts

- [`CODESLEUTH-PRODUCT-CONTRACT.md`](CODESLEUTH-PRODUCT-CONTRACT.md) — host/runtime ownership boundary, integration model, extension seams, and core feature freeze.
- [`CODESLEUTH-BRANDING.md`](CODESLEUTH-BRANDING.md) — accepted terminal-native UI/interaction runbook, ASCII identity source, documentation graphics rule, and responsive acceptance.
- [`CODESLEUTH-COLORMAP.json`](CODESLEUTH-COLORMAP.json) — machine-readable semantic colormap.
- [`DURABLE-EVIDENCE-STORE.md`](DURABLE-EVIDENCE-STORE.md) — canonical filesystem evidence-store authority: mutable review checkpoint, append-only findings/EHA ledgers, tool-mediated writes, read-only grep/audit, and derived report/Mermaid/context views.
- [`CONTEXT-GRAPH-DISCIPLINE.md`](CONTEXT-GRAPH-DISCIPLINE.md) — Git source -> review state -> bounded RepositoryContextProjection -> compact context/Mermaid authority chain.
- [`NOVACLAW-MCP.md`](NOVACLAW-MCP.md) — first external-host MCP integration and its read-only repository-evidence boundary.
- [`CODESLEUTH-NAMING-CUTOVER.md`](CODESLEUTH-NAMING-CUTOVER.md) — naming inventory and staged cutover from historical `review-pack` filenames; 0.4.0 keeps live compatibility names.
- [`STABLE-INTEGRATION-BASELINE.md`](STABLE-INTEGRATION-BASELINE.md) — SIB0/SIB1/SIB2 architecture-recovery model: initialization freeze, implementation completeness, integration completeness, and release construction from SIB2.
- [`EXACT-HEAD-ACCEPTANCE.md`](EXACT-HEAD-ACCEPTANCE.md) — normative SIB acceptance identity: SIB degree defines what is proven; exact-head acceptance binds that proof to one exact commit SHA.
- [`SIB-CANDIDATE-SELECTION.md`](SIB-CANDIDATE-SELECTION.md) — normative candidate-stream rule: future SIB candidates are selected from the literal exact head of `dev/release-X.Y.Z`; repairs return through that stream before a new EHA campaign.
- [`EHA-REPAIR-LOOP.md`](EHA-REPAIR-LOOP.md) — normative failure/repair discipline: freeze failed SHA, minimally repair into a new SHA, retain failed provenance, and start a new EHA campaign.
- [`EHA-OPERATING-PLAYBOOK.md`](EHA-OPERATING-PLAYBOOK.md) — operational mapping from SIB/EHA theory to CodeSleuth Skills, commands, durable evidence, release-stream selection, repair lineage, and Mermaid status views.
- [`TUI-VISUAL-REGRESSION.md`](TUI-VISUAL-REGRESSION.md) — canonical interface-regression evidence: real Textual screenshots, UI/event logs, semantic render analysis, and SIB2 visual-gate requirements.
- [`SEMANTIC-REFIT.md`](SEMANTIC-REFIT.md) — integration discipline for recovering still-valid intent from stale PRs without overwriting newer accepted semantics.

## Engineering articles

Long-form explanatory material lives under [`articles/`](articles/). Articles are non-normative: they may explain the motivation, history, examples, or broader engineering context behind an accepted contract, but canonical contracts and executable acceptance remain authoritative.

- [`articles/STABLE-BASELINES-RU.md`](articles/STABLE-BASELINES-RU.md) — Russian-language article explaining the SIB0/SIB1/SIB2 Stable Baselines model. Normative contract: [`STABLE-INTEGRATION-BASELINE.md`](STABLE-INTEGRATION-BASELINE.md).

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

- The canonical ASCII brand lives in `pack/.opencode/bin/codesleuth_tui.py` as `CODESLEUTH_ART` (documentation identity; not rendered by the live TUI); the root README may copy it verbatim.
- UI manuals use terminal/text snapshots captured from the real application and exact implemented labels.
- Maintained PNG/JPEG/WebP/SVG UI mockups/reference boards are not part of the documentation contract.
- Mermaid is the allowed diagram format when relationships are materially clearer as encoded text. Mermaid source is reviewable presentation, not a second source of repository truth.

For EHA history, `eha_state_mermaid` derives campaign/SIB/repair lineage from the structured `eha.ndjson` ledger. That diagram is a presentation of acceptance evidence, not the evidence authority itself and not part of the repository context-graph authority.

The same authority rule applies to repository diagrams and analytical reports: they are rebuildable/readable projections of structured evidence and verified source, never write-back formats for the durable evidence store.

## Completed implementation packets

- [`archive/CURSOR-PRODUCTION-HANDOFF.md`](archive/CURSOR-PRODUCTION-HANDOFF.md) — completed PR #2 production-hardening packet, retained for historical evidence only. It is not an active task or branch instruction.

## User and operations

- [`USER-GUIDE.md`](USER-GUIDE.md) — install, configure, validate, update, and operate CodeSleuth.
- [`LLM-OPERATOR.md`](LLM-OPERATOR.md) — task-specific cross-agent operator manual for safe installation, unattended configuration, verification, use, and removal.
- [`SELF-UPDATE.md`](SELF-UPDATE.md) — floating update, post-update Verify, controlled CodeSleuth process restart, source-checkout reload, and pinned-update boundaries.
- [`EHA-OPERATING-PLAYBOOK.md`](EHA-OPERATING-PLAYBOOK.md) — `/eha-test`, `/eha-repair`, `/eha-status`, structured EHA evidence, release-stream candidate selection, and repair history.
- [`SIB-CANDIDATE-SELECTION.md`](SIB-CANDIDATE-SELECTION.md) — exact operational rule for selecting a future SIB from `dev/release-X.Y.Z` and returning repairs through the same integration stream.
- [`TUI-VISUAL-REGRESSION.md`](TUI-VISUAL-REGRESSION.md) — exact-SHA TUI screenshot/log regression evidence and the SIB2 interface-gate contract.
- [`DURABLE-EVIDENCE-STORE.md`](DURABLE-EVIDENCE-STORE.md) — evidence storage/read/write/search semantics for review, EHA, reporting and derived views.
- [`_includes/build-controller-blurb.md`](_includes/build-controller-blurb.md) — canonical OpenCode `build` controller blurb. Public copy: [root README](../README.md#opencode-build-controller).

## Maintainers

- [`MAINTAINER-SUBREPO.md`](MAINTAINER-SUBREPO.md) — standalone/subrepo maintenance and integration guidance.
- [`RELEASE-PROCESS.md`](RELEASE-PROCESS.md) — numbered release branch policy, SIB candidate-stream role, and acceptance gates.
- [`CODESLEUTH-NAMING-CUTOVER.md`](CODESLEUTH-NAMING-CUTOVER.md) — product-namespace inventory; runtime rename remains post-0.4.0 work.
- [`DURABLE-EVIDENCE-STORE.md`](DURABLE-EVIDENCE-STORE.md) — persistence authority boundary; changing canonical evidence storage or introducing destructive generic CRUD normally reopens SIB0.
- [`EXACT-HEAD-ACCEPTANCE.md`](EXACT-HEAD-ACCEPTANCE.md) — required acceptance identity contract for SIB promotion, accepted integration states, RCs, and releases.
- [`SIB-CANDIDATE-SELECTION.md`](SIB-CANDIDATE-SELECTION.md) — required rule for choosing future SIB candidates from the active release stream rather than PR/repair/EHA side branches.
- [`EHA-REPAIR-LOOP.md`](EHA-REPAIR-LOOP.md) — required repair-loop behavior after an EHA FAIL.
- [`EHA-OPERATING-PLAYBOOK.md`](EHA-OPERATING-PLAYBOOK.md) — executable product workflow and evidence topology for EHA campaigns.
- [`TUI-VISUAL-REGRESSION.md`](TUI-VISUAL-REGRESSION.md) — required interface evidence contract for canonical acceptance and SIB2 EHA.
- [`SEMANTIC-REFIT.md`](SEMANTIC-REFIT.md) — required method when useful stale work overlaps newer accepted contracts.
- [`LESSONS-LEARNED-VIEWPORT-HARDENING.md`](LESSONS-LEARNED-VIEWPORT-HARDENING.md) — TUI collapse/Tools viewport acceptance lessons and anti-patterns (paired with `.cursor/rules/tui-viewport-acceptance.mdc`).

## Contract map

```text
CODESLEUTH-PRODUCT-CONTRACT.md
        |
        +--> DURABLE-EVIDENCE-STORE.md                    (review/evidence persistence authority)
        |       +--> .opencode/state/reviews/*/state.json
        |       +--> .opencode/state/reviews/*/findings.ndjson
        |       +--> .opencode/state/reviews/*/eha.ndjson
        |       +--> CODESLEUTH-REPORTS.md                (derived human-readable view)
        |       +--> CONTEXT-GRAPH-DISCIPLINE.md          (derived bounded linkage view)
        |
        +--> CODESLEUTH-BRANDING.md
        |       +--> CODESLEUTH-COLORMAP.json
        |       +--> TUI-VISUAL-REGRESSION.md             (render/log interface evidence)
        |       +--> pack/.opencode/bin/codesleuth_tui.py  (canonical ASCII/TUI)
        |
        +--> NOVACLAW-MCP.md                              (external host seam)
        +--> ../AGENTS.md                                 (compact cross-agent entry point)
        +--> LLM-OPERATOR.md                              (task-specific operator surface)
        +--> STABLE-INTEGRATION-BASELINE.md               (SIB0 -> SIB1 -> SIB2)
        |       +--> EXACT-HEAD-ACCEPTANCE.md             (what is proven -> exact SHA carrying the proof)
        |               +--> SIB-CANDIDATE-SELECTION.md   (dev/release -> exact candidate SHA)
        |               +--> EHA-REPAIR-LOOP.md           (FAIL -> frozen SHA -> repair -> release-stream reintegration)
        |               +--> EHA-OPERATING-PLAYBOOK.md    (Skill/commands/eha.ndjson/Mermaid)
        |               +--> TUI-VISUAL-REGRESSION.md     (SIB2 interface composition evidence)
        +--> SEMANTIC-REFIT.md                            (stale intent -> current semantics -> accepted refit)
        |
        +--> pack/.opencode/themes/codesleuth.json
        +--> host runtime / commands / Skills / tools
        +--> .codesleuth/reports/                         (human-readable local analysis)
```

Core CodeSleuth is feature-frozen. Growth continues through profiles, Skills, Playbooks, small tools, host integrations, and extension-management UX without adding a second execution runtime.
