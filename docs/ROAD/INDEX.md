# CodeSleuth Documentation Lifecycle Index

This index maps CodeSleuth documentation by **role, authority, and lifecycle state**. It is a navigation and lifecycle map, not a new authority over the documents it lists.

## Lifecycle labels

- **CANONICAL** — current normative contract for a product/engineering property.
- **OPERATING** — current procedure/runbook for operators or maintainers.
- **ROAD** — forward-looking theory, roadmap, or proposed discipline; not proof that implementation exists.
- **IMPLEMENTATION REFERENCE** — current technical description tied to live code/tests.
- **RETROSPECTIVE** — intentionally historical analysis whose historical nature is part of its value.
- **RETIRED** — completed/superseded design or evaluation packet retained only for provenance.
- **DERIVED** — generated/reporting/presentation material that is not underlying authority.

A document being old does not make it stale. A retrospective may remain useful indefinitely. A design packet becomes stale when future-tense claims have already landed or been superseded but the document still reads like current instruction.

## 1. ROAD doctrine

| Document | State | Purpose |
| --- | --- | --- |
| [`Whitepaper.md`](Whitepaper.md) | ROAD | Context Epistemics theory: truth/falsehood/unknown, authority boundaries, Negative Claims, forbidden inference, risk-weighted reasoning. |
| [`ROADMAP.md`](ROADMAP.md) | ROAD | Implementation roadmap for Context Epistemics, durable negative knowledge, Skills/Playbooks, long-context degradation tests, and fail-closed mutation gates. |
| [`ROAP.md`](ROAP.md) | ROAD / OPERATING DOCTRINE | Remote Operator Assurance Protocol for disconnected-host work: claim triangulation, authority correlation, mutation accounting, residual uncertainty, and fail-closed continuation. |
| [`DOCUMENT-LIFECYCLE-ASSURANCE.md`](DOCUMENT-LIFECYCLE-ASSURANCE.md) | ROAD / OPERATING DOCTRINE | Safe retirement, movement, archival, semantic-anchor preservation, and verification of disappearing documentation context. |

ROAD documents may guide future implementation but do not silently create a new SIB0 capability, tool authority, or accepted runtime behavior.

## 2. Repository entry points

- [`../../README.md`](../../README.md) — CANONICAL public product/operator entry.
- [`../../README.ru.md`](../../README.ru.md) — maintained Russian translation.
- [`../../README.uk.md`](../../README.uk.md) — maintained Ukrainian translation.
- [`../../AGENTS.md`](../../AGENTS.md) — OPERATING compact cross-agent discovery/instruction surface.
- [`../README.md`](../README.md) — topic-oriented docs entry point; this file adds lifecycle/authority classification.
- [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) — OPERATING contributor workflow.

## 3. Product and architecture contracts

| Document | State | Purpose |
| --- | --- | --- |
| [`../CODESLEUTH-PRODUCT-CONTRACT.md`](../CODESLEUTH-PRODUCT-CONTRACT.md) | CANONICAL | Product scope, host/runtime ownership, extension seams, feature-freeze boundaries. |
| [`../SIB0-CAPABILITY-INVENTORY.md`](../SIB0-CAPABILITY-INVENTORY.md) | CANONICAL | Frozen capability-class inventory and must-never-become boundaries. |
| [`../STABLE-INTEGRATION-BASELINE.md`](../STABLE-INTEGRATION-BASELINE.md) | CANONICAL | SIB0/SIB1/SIB2 baseline model. |
| [`../PROTECTED-CAPABILITY-CONTRACTS.md`](../PROTECTED-CAPABILITY-CONTRACTS.md) | CANONICAL | Preservation obligations and forbidden regressions after acceptance. |
| [`../protected-capabilities.json`](../protected-capabilities.json) | CANONICAL machine-readable | Protected Capability Registry; machine-consumed, therefore not eligible for a pure prose-only verification shortcut. |
| [`../SEMANTIC-REFIT.md`](../SEMANTIC-REFIT.md) | CANONICAL | Semantic continuity/refit discipline across changed implementation and history. |
| [`../CODESLEUTH-NAMING-CUTOVER.md`](../CODESLEUTH-NAMING-CUTOVER.md) | ROAD / active migration contract | Namespace inventory and staged compatibility cutover; remains live while post-0.4 rename work is unfinished. |

## 4. Evidence, acceptance, and engineering vocabulary

| Document | State | Purpose |
| --- | --- | --- |
| [`../EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md`](../EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md) | CANONICAL | EBCA vocabulary for identity, claims, evidence, authority, assurance, negative knowledge, and acceptance. |
| [`../EXACT-HEAD-ACCEPTANCE.md`](../EXACT-HEAD-ACCEPTANCE.md) | CANONICAL | Exact-SHA acceptance identity and non-transfer of evidence across identities. |
| [`../DURABLE-EVIDENCE-STORE.md`](../DURABLE-EVIDENCE-STORE.md) | CANONICAL | Durable review/evidence authority and append-only ledger semantics. |
| [`../EHA-REPAIR-LOOP.md`](../EHA-REPAIR-LOOP.md) | CANONICAL / OPERATING | Failure classification, repair, and new-campaign discipline. |
| [`../EHA-OPERATING-PLAYBOOK.md`](../EHA-OPERATING-PLAYBOOK.md) | OPERATING | Release-stream EHA campaign workflow. |
| [`../GITHUB-EHA-BRIDGE.md`](../GITHUB-EHA-BRIDGE.md) | IMPLEMENTATION REFERENCE / OPERATING | Owner-gated remote trigger and trusted self-hosted bridge while durable EHA state remains authority. |
| [`../SIB-CANDIDATE-SELECTION.md`](../SIB-CANDIDATE-SELECTION.md) | CANONICAL | Literal release-stream candidate selection for SIB/EHA. |
| [`../PROVENANCE-WATERMARK.md`](../PROVENANCE-WATERMARK.md) | CANONICAL | Provenance watermark discipline for agent/code contribution claims. |
| [`../CONTRIBUTOR-ERROR-PATTERNS.md`](../CONTRIBUTOR-ERROR-PATTERNS.md) | OPERATING / negative knowledge | Recurrent contributor/agent failure patterns and preventive discipline. |

## 5. Context, graph, Mermaid, and providers

| Document | State | Purpose |
| --- | --- | --- |
| [`../CONTEXT-GRAPH-DISCIPLINE.md`](../CONTEXT-GRAPH-DISCIPLINE.md) | CANONICAL | Git source -> durable review state -> bounded RepositoryContextProjection -> derived graph/Mermaid discipline. |
| [`../GRAPH-CONSUMPTION-CONTRACT.md`](../GRAPH-CONSUMPTION-CONTRACT.md) | CANONICAL | Consumption of derived graph context without evidence-authority escalation. |
| [`../MODEL-CONTEXT-CAPSULE.md`](../MODEL-CONTEXT-CAPSULE.md) | IMPLEMENTATION REFERENCE | Bounded model-visible context capsule. |
| [`../GRAPHIFY-PROVIDER.md`](../GRAPHIFY-PROVIDER.md) | IMPLEMENTATION REFERENCE | Current optional Graphify provider boundary, exact runtime identity, and fail-closed adapter rules. |
| [`../GRAPHIFY-CORPUS.md`](../GRAPHIFY-CORPUS.md) | IMPLEMENTATION REFERENCE | Representative corpus/hardening scope for the optional provider. |
| [`../MERMAID-QA.md`](../MERMAID-QA.md) | IMPLEMENTATION REFERENCE | Isolated Mermaid parser/render QA; normal runtime remains browser-free. |
| [`../EXPORT-SURFACES.md`](../EXPORT-SURFACES.md) | CANONICAL / IMPLEMENTATION REFERENCE | Explicit retained derived exports and their non-authority status. |

Retired Graphify planning/evaluation packets are listed below. Current implementation contracts take precedence for present behavior.

## 6. TUI, lifecycle, extensions, and operator surfaces

| Document | State | Purpose |
| --- | --- | --- |
| [`../CODESLEUTH-BRANDING.md`](../CODESLEUTH-BRANDING.md) | CANONICAL | Terminal-native UI/interaction and branding contract. |
| [`../CODESLEUTH-COLORMAP.json`](../CODESLEUTH-COLORMAP.json) | CANONICAL machine-readable | Semantic TUI colormap. |
| [`../PROJECT-LIFECYCLE.md`](../PROJECT-LIFECYCLE.md) | CANONICAL | Install/adopt/bind/unbind/uninstall ownership and reversibility. |
| [`../SELF-UPDATE.md`](../SELF-UPDATE.md) | OPERATING | Update, Verify, restart/reload, and pinned update boundaries. |
| [`../USER-GUIDE.md`](../USER-GUIDE.md) | OPERATING | Human install/configure/validate/update/use guide. |
| [`../LLM-OPERATOR.md`](../LLM-OPERATOR.md) | OPERATING | Coding-agent/LLM operator guide for safe unattended lifecycle work. |
| [`../PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md`](../PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md) | CANONICAL | Atomic Skills, isolated Playbook Steps, Commands, and bounded Tools. |
| [`../EXTENSION-LOAD-UNITS.md`](../EXTENSION-LOAD-UNITS.md) | CANONICAL | Shared Catalog / Detail / Source -> Inspect -> Validate -> Confirm -> Result loader units. |
| [`../TUI-VISUAL-REGRESSION.md`](../TUI-VISUAL-REGRESSION.md) | CANONICAL / ACCEPTANCE | TUI visual regression gate and artifact contract. |
| [`../MAINTAINER-SUBREPO.md`](../MAINTAINER-SUBREPO.md) | OPERATING | Standalone/subrepo maintenance and integration. |
| [`../RELEASE-PROCESS.md`](../RELEASE-PROCESS.md) | OPERATING / CANONICAL | Release-branch policy and release acceptance sequence. |

## 7. External host/integration seams

- [`../NOVACLAW-MCP.md`](../NOVACLAW-MCP.md) — IMPLEMENTATION REFERENCE for the external-host MCP/read-only repository-evidence boundary.
- [`ROAP.md`](ROAP.md) — ROAD / OPERATING doctrine for assurance when execution is observable only through another agent/operator plus external anchors.

## 8. Executable and agent-facing instruction surfaces outside `docs/`

These are operational context and must not be mistaken for ordinary prose documentation.

- [`../../AGENTS.md`](../../AGENTS.md) — repository-wide agent instruction/discovery surface.
- [`../../.github/copilot-instructions.md`](../../.github/copilot-instructions.md) — Copilot-specific instructions.
- [`../../.cursor/rules/`](../../.cursor/rules/) — Cursor-specific rules.
- [`../../pack/.opencode/commands/`](../../pack/.opencode/commands/) — user command entry points.
- [`../../pack/.opencode/playbooks/`](../../pack/.opencode/playbooks/) — stored workflow manifests and isolated Step prompts.
- [`../../pack/.opencode/skills/`](../../pack/.opencode/skills/) — atomic on-demand competencies.
- [`../../pack/.opencode/tools/`](../../pack/.opencode/tools/) — bounded execution primitives.
- [`../../pack/.opencode/CODESLEUTH-REPORTS.md`](../../pack/.opencode/CODESLEUTH-REPORTS.md) — derived analysis publication/metadata contract.

A prompt located inside the repository does not gain general instruction authority merely because it is related to the target. Instruction authority is assigned by host/repository contract, not persuasive content.

## 9. Retrospectives and historical knowledge

These remain intentionally historical rather than being retired as stale:

- [`../LESSONS-LEARNED-SIB2-SEMANTIC-REFIT.md`](../LESSONS-LEARNED-SIB2-SEMANTIC-REFIT.md) — SIB2 assembly, exact-head identity, semantic refit, branch archaeology, preserved negative knowledge.
- [`../LESSONS-LEARNED-VIEWPORT-HARDENING.md`](../LESSONS-LEARNED-VIEWPORT-HARDENING.md) — TUI viewport/collapse hardening lessons and anti-patterns.
- [`../articles/`](../articles/) — non-normative explanatory articles.

Historical knowledge is useful when its scope is explicit. The danger is historical prose masquerading as current procedure.

## 10. Retirement ledger

### RETIRED: Graphify evaluation audit

Compatibility path: [`../MERMAID-GRAPHIFY-AUDIT.md`](../MERMAID-GRAPHIFY-AUDIT.md)  
Archived exact historical blob: [`../archive/MERMAID-GRAPHIFY-AUDIT.md.retired`](../archive/MERMAID-GRAPHIFY-AUDIT.md.retired)

Reason: it evaluates a future optional provider against an old baseline and recommends an implementation spike. The provider now exists. Current behavior is owned by [`../GRAPHIFY-PROVIDER.md`](../GRAPHIFY-PROVIDER.md), [`../GRAPHIFY-CORPUS.md`](../GRAPHIFY-CORPUS.md), and [`../CONTEXT-GRAPH-DISCIPLINE.md`](../CONTEXT-GRAPH-DISCIPLINE.md).

### RETIRED: Mermaid/Graphify feature plan

Compatibility path: [`../FEATURE-MERMAID-GRAPHIFY-PLAN.md`](../FEATURE-MERMAID-GRAPHIFY-PLAN.md)  
Archived exact historical blob: [`../archive/FEATURE-MERMAID-GRAPHIFY-PLAN.md.retired`](../archive/FEATURE-MERMAID-GRAPHIFY-PLAN.md.retired)

Reason: it names a historical feature branch/base/refit target and describes future deliverables that now exist. Current provider/graph/QA/corpus/export contracts supersede it.

### RETIRED: Playbooks Catalog TUI design sketch

Compatibility path: [`../PLAYBOOKS-CATALOG-TUI.md`](../PLAYBOOKS-CATALOG-TUI.md)  
Archived exact historical blob: [`../archive/PLAYBOOKS-CATALOG-TUI.md.retired`](../archive/PLAYBOOKS-CATALOG-TUI.md.retired)

Reason: it explicitly identifies itself as a feature request/design sketch. The catalog, validation, and load implementation plus tests now exist. Current contracts are [`../EXTENSION-LOAD-UNITS.md`](../EXTENSION-LOAD-UNITS.md) and [`../PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md`](../PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md), with live implementation in `pack/.opencode/bin/playbook_catalog.py` and tests in `tests/test_playbook_catalog.py`.

The Canvas files under [`../sketches/`](../sketches/) remain historical design artifacts, not live-TUI documentation.

### Existing archive

- [`../archive/CURSOR-PRODUCTION-HANDOFF.md`](../archive/CURSOR-PRODUCTION-HANDOFF.md) — completed production-hardening handoff retained as historical evidence.

## 11. Retirement policy

Retire a document when one or more are true:

1. a design/feature packet describes work that has already landed;
2. its target branch/SHA/baseline is historical and it still reads as current instruction;
3. a newer canonical contract owns the same present-tense behavior;
4. following the old document today would create an incorrect action or authority claim.

Do **not** retire a retrospective merely because it is old. Mark its historical scope instead.

Retirement procedure:

```text
identify current replacement authority
        ↓
preserve historical content
        ↓
replace old live path with a RETIRED tombstone
        ↓
record it in this ledger
        ↓
update navigation
        ↓
run documentation verification
```

## 12. Documentation-only verification profile

Pure prose/documentation changes may use a reduced, explicitly scoped verification profile when full runtime acceptance would not add material evidence.

A change is eligible only when the diff is limited to human-readable documentation and archival/tombstone material and does **not** change:

- runtime/source code;
- `.github/workflows/**`;
- dependency or version manifests;
- OpenCode commands, agents, Skills, Playbooks, tools, or policy/config;
- machine-consumed acceptance/evidence registries such as `protected-capabilities.json`;
- executable scripts or generated runtime data.

Minimum reduced profile:

```text
1. freeze exact documentation head SHA
2. prove changed-path eligibility
3. run internal-link/docs contract checks
4. run any contract test directly owned by the edited normative document
5. verify retired paths resolve to tombstones and archived historical material
6. verify no runtime/pack/workflow/config delta exists
7. report the result as DOCUMENTATION-ONLY verification
```

Recommended existing gate for ordinary Markdown reorganization:

```text
python -m pytest -q tests/test_docs_contract.py
```

Add focused tests when the edited document has a dedicated contract test (for example EBCA/EHA/SIB doctrine).

Critical scope rule:

```text
DOCUMENTATION-ONLY PASS
    -/-> full repository acceptance
    -/-> EHA PASS
    -/-> SIB promotion
```

The reduced profile is an explicitly narrower claim, not a cheaper way to obtain a broader green label.

Escalate to targeted/full acceptance whenever documentation changes machine-consumed behavior, changes an accepted operational contract whose implementation may now be inconsistent, or accompanies any runtime/configuration delta.

## 13. Disappearing-document assurance

The detailed retirement/reorganization doctrine is [`DOCUMENT-LIFECYCLE-ASSURANCE.md`](DOCUMENT-LIFECYCLE-ASSURANCE.md).

The key negative claim is:

```text
"I cannot find this document/concept in the new navigation"
    -/->
"the document/concept is obsolete"
```

A document can disappear physically, navigationally, semantically, as an authority pointer, or as a recoverable historical identity. Verification must distinguish those cases.

The ROAD/index cleanup itself supplied a regression witness: shortening `docs/README.md` initially dropped required semantic anchors (`eha.ndjson`, `semantic-continuity criterion`, and `semantic surface -> claim reconciliation -> evidence`) while the underlying documents still existed. That was semantic/navigational disappearance, not physical deletion and not a runtime regression.

Accordingly, document retirement and index cleanup require both path continuity checks and semantic contract checks. A clean link graph alone is insufficient evidence of context continuity.
