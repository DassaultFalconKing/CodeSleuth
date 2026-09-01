# RC7 Structured Object Multi-Renderer Architecture

**Status:** ACCEPTED RC7 PLANNING INPUT  
**Semantic authority:** [`EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md`](EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md)  
**Related:** [`RC7-REPAIR-PACKET-RENDERING.md`](RC7-REPAIR-PACKET-RENDERING.md), [`RC7-FEATURE-PLAN.md`](RC7-FEATURE-PLAN.md)

## 1. Goal

RC7 should treat structured EBCA/domain objects as the stable semantic center and render them into multiple consumer formats without rebuilding domain meaning in every exporter.

Compact rule:

> **One validated typed object, many explicitly bounded renderers. Rendering changes representation, not authority or domain semantics.**

The same principle applies to `EvidenceClaimV1`, `RepairCaseV1`, `RepairPacketV1`, implementation-ledger projections, EHA results, development-continuation packets and future evidence-heavy domain objects.

## 2. Typed structure first

Prefer structured sections over one large free-form JSON blob.

Example `RepairPacketV1` shape:

```text
subject
authority
scope
defect
evidence
assumptions
limitations
repairConstraints
regressionObligations
verificationPlan
stopConditions
```

This aligns naturally with the EBCA claim model:

```text
subject
property
scope
authority
evidence
assumptions
limitations
```

The canonical typed object is validated before rendering. Rendered text, diagrams, HTML, SVG, Obsidian views or prompt files never become the authority for the underlying domain facts.

## 3. Renderer registry

RC7 design should define a renderer registry whose entries declare at least:

```text
rendererId
rendererVersion
acceptedSchemaIds[]
outputMediaType / extension
semanticCoverage
lossProfile
roundTripCapability
orderingPolicy
canonicalizationPolicy
escaping/securityPolicy
requiredFields[]
optionalFields[]
projectionAuthority = none
```

A renderer must fail closed when a required semantic field cannot be represented without loss, unless its declared loss profile explicitly permits that omission and the output visibly records the limitation.

## 4. Renderer classes

### 4.1 Structured interchange

Strong candidates:

- **JSON** — canonical machine interchange/read model;
- **JSONC** — human-editable configuration/read model where comments are useful, never canonical evidence authority unless separately defined;
- **NDJSON/JSONL** — append/stream-friendly event and record transport;
- **YAML** — human-oriented configuration/export, useful for frontmatter and Obsidian/Bases integration;
- **TOML** — bounded configuration-oriented export where project ecosystems prefer TOML;
- **JSON-LD** — optional semantic/linked-data projection for interoperable typed graph identities.

Not every domain must support every structured format. Renderer applicability is schema-declared.

### 4.2 Human-readable

- **Markdown** — primary portable human report/procedure/ledger view;
- **HTML** — standalone rich read model for browsers and publication;
- **plain text** — terminal/operator surfaces where Markdown is inappropriate.

### 4.3 Graph and visual

- **Mermaid** — deterministic human-readable diagram source;
- **Graphviz DOT** — useful interoperable graph/layout input for technical tooling;
- **GraphML** — optional interchange for graph-analysis applications;
- **JSON Canvas (`.canvas`)** — open spatial graph/canvas representation, especially useful for Obsidian and other JSON Canvas consumers;
- **SVG** — final deterministic user-facing visual artifact derived from a graph/diagram renderer;
- optionally **PNG** only as a convenience raster derivative, never when SVG is sufficient.

Graph renderers must preserve stable node/edge IDs and expose bounded-selection/truncation metadata. A pretty diagram with missing evidence edges is still missing evidence, merely with better typography.

### 4.4 Host/model instructions

Jinja2 is the preferred rendering engine for structured prompts/instructions, not a domain authority and not itself the canonical object format.

Examples:

```text
repair-packet.md.jinja2
repair-packet.cursor.jinja2
repair-packet.codex.jinja2
repair-packet.opencode.jinja2
repair-packet.human.jinja2
```

All templates consume the same validated packet. Host-specific phrasing may vary; target identity, authority, allowed/forbidden scope, evidence, regression obligations, verification and stop conditions may not.

### 4.5 Ecosystem/integration renderers

Useful bounded adapters to evaluate:

- **SARIF** for verified findings/diagnostics that should interoperate with code-scanning/review systems;
- **JUnit XML** for gate/test-result projections where the domain maps honestly to test cases/suites;
- **CSV/TSV** for deliberately tabular, explicitly lossy exports;
- project-specific issue/CI formats only through adapters with declared schema mappings.

These are projection targets, not reasons to distort the source domain object.

## 5. Multi-artifact renderers

A renderer may emit a coherent artifact bundle rather than one file.

Examples:

```text
ObsidianVaultProjection/
  objects/*.md
  views/*.base
  graphs/*.canvas
  manifest.json
```

or:

```text
report/
  report.md
  graph.mmd
  graph.svg
  manifest.json
```

Every bundle requires a manifest identifying source schema/object IDs, renderer identity/version, source digests, outputs/hashes, selection/truncation and explicit non-authority status.

## 6. Semantic parity

For renderers declared as semantically complete for a schema, parity tests must compare domain meaning, not raw formatting.

Minimum checks include:

- stable object/record identity;
- subject SHA/blob/profile IDs where material;
- authority/evidence references;
- lifecycle/result state;
- assumptions/limitations/residual uncertainty;
- semantic ordering when order matters;
- graph node/edge identity;
- regression obligations/stop conditions for repair objects;
- visible truncation/loss declarations.

Cross-renderer parity examples:

```text
RepairPacketV1
  -> JSON
  -> Markdown
  -> Cursor prompt
  -> Codex prompt
  -> OpenCode prompt
```

must preserve the same material repair semantics.

Likewise:

```text
Evidence/Lineage domain
  -> NDJSON
  -> Markdown
  -> Graphify projection
  -> Mermaid
  -> DOT
  -> JSON Canvas
  -> SVG
```

must not invent or silently drop authority-bearing relations.

## 7. Import and round-trip boundary

Rendering is one-way unless a renderer explicitly implements an importer with its own validation contract.

Possible classes:

- `RENDER_ONLY`;
- `SEMANTIC_ROUND_TRIP`;
- `BYTE_ROUND_TRIP` where actually achievable;
- `LOSSY_EXPORT`.

Markdown/Obsidian imports should use AST/frontmatter adapters and retain source digests. Mermaid, SVG, HTML and other presentation surfaces are not reverse authorities.

## 8. Custom project adapters

The renderer framework must be reusable for arbitrary projects. Project profiles may specify:

- domain schema mapping;
- field aliases;
- frontmatter conventions;
- graph relation mapping;
- renderer enable/disable policy;
- custom templates;
- output paths/naming;
- acceptable lossy projections;
- project-specific validation rules.

Customization must not require forking the generic renderer core.

## 9. Security

Repository-provided strings are data, not renderer policy.

Required protections:

- Jinja2 `StrictUndefined` or equivalent;
- escaped HTML/SVG where required;
- safe YAML/JSON serialization instead of string concatenation;
- explicit quoting of repository excerpts in model prompts;
- no template path escape outside approved profile roots;
- no renderer may execute arbitrary repository-supplied code merely to render an object.

## 10. Acceptance additions

RC7 acceptance should cover at least:

1. one canonical typed fixture rendered to JSON, NDJSON, Markdown, Mermaid, DOT, JSON Canvas and SVG where applicable;
2. cross-host Jinja2 prompt parity;
3. required field omission fails closed;
4. declared lossy CSV export exposes loss metadata;
5. malicious Markdown/YAML/template-like text remains data;
6. Graphify/Mermaid/DOT/Canvas node and edge identities agree;
7. bundle manifests bind renderer/source/output digests;
8. user-facing SVG is regenerable from the same structured source;
9. an Obsidian-style vault projection remains derived/non-authoritative;
10. custom project profile changes mapping without forking renderer code.

## 11. Scope restraint

RC7 should implement the renderer kernel and the formats needed to prove portability/parity. It need not ship every candidate renderer in the first release.

A renderer belongs in RC7 when it validates the architecture or supports a core workflow. More specialized ecosystem formats can land later as adapters.
