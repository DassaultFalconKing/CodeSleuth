# CodeSleuth Documentation

Start with [`ROAD/INDEX.md`](ROAD/INDEX.md) when you need to know **which document is current, what authority it has, and which historical packets are retired**. This file remains the topic-oriented entry point.

## Canonical product and engineering contracts

- [`CODESLEUTH-PRODUCT-CONTRACT.md`](CODESLEUTH-PRODUCT-CONTRACT.md) — product scope, host/runtime ownership, extension seams, and feature-freeze boundaries.
- [`SIB0-CAPABILITY-INVENTORY.md`](SIB0-CAPABILITY-INVENTORY.md) — frozen capability-class inventory and must-never-become boundaries.
- [`STABLE-INTEGRATION-BASELINE.md`](STABLE-INTEGRATION-BASELINE.md) — SIB0/SIB1/SIB2 baseline model.
- [`EXACT-HEAD-ACCEPTANCE.md`](EXACT-HEAD-ACCEPTANCE.md) — exact-SHA acceptance identity and non-transfer of proof across identities.
- [`EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md`](EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md) — canonical EBCA vocabulary for subject identity, evidence, authority, assurance, negative knowledge, SIB/EHA, and conservative claim language.
- [`DURABLE-EVIDENCE-STORE.md`](DURABLE-EVIDENCE-STORE.md) — durable review/evidence authority and append-only ledger semantics, including append-only EHA history in `eha.ndjson`.
- [`PROTECTED-CAPABILITY-CONTRACTS.md`](PROTECTED-CAPABILITY-CONTRACTS.md) and [`protected-capabilities.json`](protected-capabilities.json) — post-acceptance preservation discipline and machine-readable protected registry.
- [`SEMANTIC-REFIT.md`](SEMANTIC-REFIT.md) — normative **semantic-continuity criterion**: `semantic surface -> claim reconciliation -> evidence`, plus refit discipline across implementation and history changes.
- [`CONTEXT-GRAPH-DISCIPLINE.md`](CONTEXT-GRAPH-DISCIPLINE.md) — source -> durable review state -> bounded RepositoryContextProjection -> derived graph/Mermaid discipline.
- [`GRAPH-CONSUMPTION-CONTRACT.md`](GRAPH-CONSUMPTION-CONTRACT.md) — bounded consumption of derived graph context.
- [`PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md`](PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md) — atomic Skills, isolated Playbook Steps, Commands, and bounded Tools.
- [`EXTENSION-LOAD-UNITS.md`](EXTENSION-LOAD-UNITS.md) — shared Catalog, Detail, and `Source -> Inspect -> Validate -> Confirm -> Result` loader units.

## Acceptance and release operations

- [`EHA-REPAIR-LOOP.md`](EHA-REPAIR-LOOP.md) — failed-target classification, repair, and new-campaign discipline.
- [`EHA-OPERATING-PLAYBOOK.md`](EHA-OPERATING-PLAYBOOK.md) — release-stream EHA operator workflow.
- [`GITHUB-EHA-BRIDGE.md`](GITHUB-EHA-BRIDGE.md) — trusted self-hosted GitHub bridge to canonical OpenCode EHA while durable `eha.ndjson` state remains verdict authority.
- [`SIB-CANDIDATE-SELECTION.md`](SIB-CANDIDATE-SELECTION.md) — literal release-stream candidate selection.
- [`RELEASE-PROCESS.md`](RELEASE-PROCESS.md) — release branch policy and acceptance sequence.
- [`TUI-VISUAL-REGRESSION.md`](TUI-VISUAL-REGRESSION.md) — TUI visual-regression gate and artifact contract.

## User, lifecycle, and maintainer operations

- [`USER-GUIDE.md`](USER-GUIDE.md) — human install/configure/validate/update/use guide.
- [`LLM-OPERATOR.md`](LLM-OPERATOR.md) — coding-agent/LLM operator guide for safe unattended lifecycle work.
- [`PROJECT-LIFECYCLE.md`](PROJECT-LIFECYCLE.md) — install/adopt/bind/unbind/uninstall ownership and reversibility.
- [`SELF-UPDATE.md`](SELF-UPDATE.md) — update, Verify, restart/reload, and pinned update boundaries.
- [`MAINTAINER-SUBREPO.md`](MAINTAINER-SUBREPO.md) — standalone/subrepo maintenance and integration.
- [`CODESLEUTH-BRANDING.md`](CODESLEUTH-BRANDING.md) and [`CODESLEUTH-COLORMAP.json`](CODESLEUTH-COLORMAP.json) — terminal-native UI/interaction identity and semantic colormap.
- [`CODESLEUTH-NAMING-CUTOVER.md`](CODESLEUTH-NAMING-CUTOVER.md) — staged namespace compatibility migration; still active while post-0.4 rename work remains.

## Current implementation references and integrations

- [`GRAPHIFY-PROVIDER.md`](GRAPHIFY-PROVIDER.md) — current optional Graphify structural-provider boundary and runtime identity.
- [`GRAPHIFY-CORPUS.md`](GRAPHIFY-CORPUS.md) — representative provider corpus/hardening reference.
- [`MERMAID-QA.md`](MERMAID-QA.md) — isolated Mermaid QA; normal runtime remains browser-free.
- [`MODEL-CONTEXT-CAPSULE.md`](MODEL-CONTEXT-CAPSULE.md) — bounded model-visible context capsule.
- [`EXPORT-SURFACES.md`](EXPORT-SURFACES.md) — explicit retained derived exports and their non-authority status.
- [`NOVACLAW-MCP.md`](NOVACLAW-MCP.md) — external-host MCP/read-only repository-evidence boundary.
- [`PROVENANCE-WATERMARK.md`](PROVENANCE-WATERMARK.md) — contribution provenance watermark discipline.
- [`CONTRIBUTOR-ERROR-PATTERNS.md`](CONTRIBUTOR-ERROR-PATTERNS.md) — recurrent agent/contributor failure patterns and negative knowledge.

## ROAD: theory and future discipline

The `ROAD/` directory is forward-looking doctrine, not proof that the proposed runtime mechanisms already exist.

- [`ROAD/Whitepaper.md`](ROAD/Whitepaper.md) — Context Epistemics theory for true/false/unknown claims, authority, Negative Claims, and forbidden inference.
- [`ROAD/ROADMAP.md`](ROAD/ROADMAP.md) — implementation roadmap for durable negative knowledge and fail-closed context/mutation discipline.
- [`ROAD/ROAP.md`](ROAD/ROAP.md) — Remote Operator Assurance Protocol for disconnected-host work.
- [`ROAD/INDEX.md`](ROAD/INDEX.md) — full documentation lifecycle/authority index and retirement ledger.

## Engineering articles and retrospectives

Long-form explanatory material under [`articles/`](articles/) is non-normative. Contracts and executable acceptance remain authoritative.

- [`articles/STABLE-BASELINES-RU.md`](articles/STABLE-BASELINES-RU.md) — Russian explanation of SIB0/SIB1/SIB2.
- [`LESSONS-LEARNED-SIB2-SEMANTIC-REFIT.md`](LESSONS-LEARNED-SIB2-SEMANTIC-REFIT.md) — SIB2/semantic-refit retrospective and preserved negative knowledge.
- [`LESSONS-LEARNED-VIEWPORT-HARDENING.md`](LESSONS-LEARNED-VIEWPORT-HARDENING.md) — TUI viewport/collapse hardening retrospective.

## Retired documentation

Retired design/evaluation packets keep compatibility tombstones at their old paths so stale links fail safe into an explicit `RETIRED` state rather than silently presenting historical plans as current instruction.

- [`MERMAID-GRAPHIFY-AUDIT.md`](MERMAID-GRAPHIFY-AUDIT.md) — RETIRED historical provider evaluation; current provider contract is `GRAPHIFY-PROVIDER.md`.
- [`FEATURE-MERMAID-GRAPHIFY-PLAN.md`](FEATURE-MERMAID-GRAPHIFY-PLAN.md) — RETIRED historical implementation plan.
- [`PLAYBOOKS-CATALOG-TUI.md`](PLAYBOOKS-CATALOG-TUI.md) — RETIRED historical UI design sketch; current behavior is owned by `EXTENSION-LOAD-UNITS.md`, implementation, and tests.

Exact historical blobs are retained under [`archive/`](archive/) with `.retired` suffixes. See [`ROAD/INDEX.md`](ROAD/INDEX.md) for reasons and replacement authorities.

## Cross-agent documentation

Root [`../AGENTS.md`](../AGENTS.md) is the compact cross-agent discovery and repository-instruction entry point. Keep it short enough that agents do not spend permanent context on task-specific operating detail.

[`LLM-OPERATOR.md`](LLM-OPERATOR.md) is the maintained task-specific agent operator guide. Multi-step CodeSleuth workflows live under `pack/.opencode/playbooks/`; atomic competencies under `pack/.opencode/skills/`; execution remains owned by the host.

A document or prompt does not gain instruction authority merely because it is in the repository or relevant to the target. See [`ROAD/ROAP.md`](ROAD/ROAP.md) and [`ROAD/Whitepaper.md`](ROAD/Whitepaper.md).

## README language maintenance

The public README is maintained in three complete language versions:

- [`../README.md`](../README.md) — canonical English source;
- [`../README.ru.md`](../README.ru.md) — Russian translation;
- [`../README.uk.md`](../README.uk.md) — Ukrainian translation.

Every semantic change to the root English README must update both translations in the same change. Each translation records the Git blob identity of the English source via `README-SOURCE-BLOB`.

## Documentation media policy

CodeSleuth documentation is text-first and terminal-native. Mermaid is allowed when relationships are materially clearer as encoded text, but remains bounded presentation rather than repository/evidence/acceptance authority. Historical Canvas sketches are design artifacts, not live-TUI manuals.

## Completed implementation packets

- [`archive/CURSOR-PRODUCTION-HANDOFF.md`](archive/CURSOR-PRODUCTION-HANDOFF.md) — completed PR #2 production-hardening packet, retained for **historical evidence only**. It is not an active task or branch instruction.

## Documentation verification

Pure human-readable documentation changes may use the reduced **DOCUMENTATION-ONLY** profile described in [`ROAD/INDEX.md`](ROAD/INDEX.md). That result is deliberately narrower than full repository acceptance or EHA.
