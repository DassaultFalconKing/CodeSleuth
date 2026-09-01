# RC7 Feature Plan

**Status:** PLANNED INPUT / NOT YET ACCEPTED AS RC7 SCOPE AUTHORITY  
**Branch:** `docs/rc7-ledger-authority-repair-plan`  
**Parent design state:** RC6 evidence-bound continuation and durable-state contracts  

## 1. Purpose

RC7 should make CodeSleuth apply its own evidence discipline to development-plan execution.

Today a human-readable implementation ledger can summarize progress, but that Markdown is not a native CodeSleuth durable authority. RC7 should introduce a bounded implementation-ledger domain whose historical events are append-only, whose current status is derived, and whose presentation can be regenerated.

RC7 must also add an explicit Ledger Repair capability. Repair exists to recover trustworthy read models and preserve lineage when ledger records are semantically amended or structurally damaged. Repair must never become a mechanism for rewriting historical facts, converting FAIL to PASS, deleting inconvenient evidence, or manufacturing acceptance.

Compact rule:

> **Plans are bound; implementation history is appended; current status is derived; damaged history is recovered by lineage, never rewritten in place.**

## 2. RC7-A — Native Implementation Ledger

### Goal

Replace ad-hoc Markdown-as-state for implementation progress with a native CodeSleuth durable ledger for accepted-plan execution.

The ledger records facts about implementation and verification, not model confidence or intent.

### Required authority chain

```text
accepted/frozen plan + exact plan blob identity
        |
        v
append-only implementation events
        |
        v
validated derived requirement status
        |
        +--> implementation status/query tools
        +--> Markdown implementation ledger
        +--> reports / optional Mermaid
```

The Markdown implementation ledger is a derived view and must never outrank the event ledger.

### Minimum event families

Exact schema is deferred to RC7 design, but the domain must distinguish at least:

- plan binding / plan revision identity;
- requirement implementation evidence;
- gate/check execution evidence;
- verification result;
- blocker/defer decisions;
- supersession/amendment events;
- repair/recovery lineage.

Every material event must bind to the relevant exact Git SHA and stable requirement ID. Events that cite tracked source must retain exact blob identity where applicable.

### Explicit non-goals

RC7-A must not introduce:

- generic CRUD over arbitrary ledger rows;
- an independent SQL/database authority;
- silent inference that a requirement is DONE because files merely changed;
- status derived from chat memory;
- automatic lifecycle promotion from implementation to acceptance;
- duplicate authority for existing findings/EHA facts.

Existing review findings and EHA/SIB events remain owned by their established ledgers unless a future accepted migration explicitly replaces that authority.

## 3. RC7-B — Ledger Integrity and Validation

Before repair exists, CodeSleuth needs a deterministic way to decide whether a ledger is trustworthy.

Validation must detect and classify at least:

- torn/missing-newline records;
- invalid JSON or unsupported schema versions;
- duplicate event IDs;
- missing referenced predecessor/target IDs;
- illegal lifecycle transitions;
- broken supersession/amendment chains;
- exact-SHA or blob-identity mismatches where the schema requires them;
- recovery-generation lineage errors;
- derived-view drift where the authoritative events are valid but the projection is stale.

Validation output must distinguish:

- `TRUSTWORTHY`;
- `DEGRADED_BUT_READABLE` where explicitly defined;
- `UNTRUSTED`;
- `REPAIR_REQUIRED`;
- `UNRECOVERABLE_WITHOUT_OPERATOR_DECISION`.

A validator may diagnose corruption. It must not silently repair it.

## 4. RC7-C — Ledger Repair

Ledger Repair is a separate domain workflow, not an extension of ordinary review editing.

### 4.1 Semantic amendment

Use when the historical record is structurally valid but a later fact corrects, closes, reopens, retracts, or supersedes an earlier domain record.

Rules:

- append an amendment/recovery event;
- never rewrite or delete the original record;
- preserve the original event ID and bytes;
- apply only domain-legal transitions;
- derived status is recomputed from the complete trustworthy history.

Where an existing domain already has a legal amendment API, Ledger Repair must reuse it rather than inventing a competing repair authority.

### 4.2 Structural corruption recovery

Use when authoritative ledger bytes are damaged, torn, duplicated, schema-incompatible, or otherwise cannot produce a trustworthy read model.

The damaged ledger must be frozen as evidence before recovery:

```text
original ledger bytes
+ content digest
+ path / domain / schema identity
+ observed corruption classification
        |
        v
repair proposal
        |
        v
explicit operator approval when recovery changes authoritative generation
        |
        v
new recovered generation
+ predecessor digest / lineage
+ repair manifest
```

The corrupted original must not be edited in place. Recovery creates a new authoritative generation or equivalent lineage-preserving replacement defined by the accepted RC7 design.

A repaired generation may restore readability and valid derivation. It may not fabricate facts absent from trustworthy evidence.

### 4.3 Historical-fact immutability

The following are prohibited repair outcomes:

- recorded EHA FAIL becoming PASS on the same exact SHA;
- removal of an accepted historical finding solely to make a report green;
- silently dropping an unknown/corrupt event and continuing as trustworthy;
- changing a recorded target SHA to another SHA;
- replacing missing proof with model-generated prose;
- regenerating an event with a new meaning while preserving the old ID.

If evidence is insufficient, the repair result remains `UNTRUSTED`, `UNRESOLVED`, or requires explicit operator adjudication.

## 5. Required RC7 tool surfaces

Names remain provisional until RC7 design acceptance, but the feature plan requires bounded tool primitives equivalent to:

### Inspection / validation

- `ledger_state_inspect`
- `ledger_state_validate`
- `ledger_state_load`

### Repair planning

- `ledger_repair_propose`
- `ledger_repair_validate_proposal`

### Repair execution

- `ledger_repair_apply`
- `ledger_repair_verify`

### Implementation-ledger domain

- `implementation_ledger_bind_plan`
- `implementation_ledger_record_event`
- `implementation_ledger_load`
- `implementation_ledger_render`

These names are planning placeholders, not an API commitment. The accepted design should minimize surface area and reuse existing domain-specific tools where they already provide the required semantics.

No tool may expose arbitrary `update/delete ledger row` behavior.

## 6. Required RC7 Skill / Playbook surfaces

RC7 must include agent-facing orchestration, not merely low-level tools.

### Atomic Skills

At minimum, the design must provide or compose atomic capabilities equivalent to:

- **ledger-integrity-analysis** — classify corruption and trustworthiness without mutation;
- **implementation-ledger-evidence** — bind plan/requirement/gate evidence without deciding acceptance;
- **ledger-repair-protocol** — define legal repair boundaries, evidence requirements, lineage and stop conditions.

### Playbooks

#### `implementation-ledger-maintenance`

Purpose:

1. bind exact accepted plan identity;
2. resolve requirement IDs;
3. inspect existing implementation history;
4. record only evidenced implementation/gate events;
5. derive current statuses;
6. persist/regenerate the human-readable implementation ledger.

It must not infer DONE from prose or changed filenames alone.

#### `ledger-repair`

Purpose:

1. freeze exact ledger bytes/digest and repository identity;
2. validate and classify the defect;
3. determine semantic-amendment vs structural-recovery path;
4. produce a bounded repair proposal;
5. require operator adjudication for authority-generation changes or ambiguous evidence;
6. apply repair only through legal domain tools;
7. revalidate the complete recovered lineage;
8. compare derived state before/after;
9. emit a repair report that remains derived presentation.

The Playbook must stop rather than guess when trustworthy recovery is impossible.

## 7. User-facing command surface

RC7 design should evaluate a minimal command layer, likely equivalent to:

- `/ledger-status` — inspect trust, generations and current derived state;
- `/ledger-repair` — execute the Ledger Repair Playbook;
- an implementation-ledger command or integration into the future development-continuation workflow.

Command proliferation is not a goal. If an existing command can expose the capability without semantic ambiguity, prefer composition over another top-level command.

## 8. Repair authority and human boundary

Ledger Repair can diagnose automatically. It cannot always adjudicate automatically.

Explicit operator approval is required when a proposed repair would:

- switch the authoritative ledger generation;
- discard/skip an unreadable historical byte range from the derived history;
- choose between multiple plausible predecessor/reference identities;
- resolve a contradiction where no deterministic evidence establishes one meaning;
- materially change the current derived implementation state.

Pure regeneration of a stale derived Markdown/Mermaid view from an already trustworthy ledger does not require authority-changing approval because the source authority is unchanged.

## 9. Required adversarial tests

RC7 acceptance must include deterministic fixtures for at least:

1. clean append-only ledger;
2. torn final line;
3. invalid JSON in the middle of history;
4. duplicate event ID;
5. illegal lifecycle transition;
6. missing referenced event;
7. supersession cycle;
8. stale derived Markdown with trustworthy ledger;
9. attempted raw historical rewrite;
10. attempted FAIL-to-PASS repair on one exact SHA;
11. structural recovery generation with valid predecessor digest;
12. corrupted original retained byte-for-byte after recovery;
13. ambiguous recovery that correctly stops for operator adjudication;
14. implementation event whose source blob no longer matches evidence;
15. plan revision where old requirement evidence must not silently attach to a new plan identity.

## 10. Acceptance requirements

RC7 Ledger Authority/Repair is acceptable only when:

- implementation progress no longer depends on Markdown as authority;
- all historical implementation events are append-only or lineage-preserved through explicit recovery generations;
- repair cannot silently edit old facts;
- corrupted history cannot be reported as trustworthy;
- deterministic validation precedes repair;
- repair proposals are bounded and reviewable;
- operator adjudication exists at ambiguous authority changes;
- repaired history can be reloaded and independently revalidated;
- derived Markdown can be regenerated from authoritative state;
- existing findings/EHA authorities remain intact and are not duplicated;
- install/smoke/catalog parity covers all accepted RC7 surfaces;
- hosted adversarial fixtures pass on one exact candidate SHA;
- live dogfood demonstrates at least one real interruption/corruption/recovery workflow before release acceptance.

## 11. Architectural constraint

Ledger Repair is not permission to create a generic database subsystem.

The existing durable-evidence rule remains binding:

```text
mutable progress -> atomic snapshot
historical facts -> append-only events
corrections       -> append-only amendments
corruption repair -> lineage-preserving new generation
presentation      -> derived/rebuildable
LLM context       -> never authority
```

If RC7 discovers that a generic transactional persistence engine is genuinely required, that is an architecture-reopen decision and must be evaluated separately rather than smuggled into Ledger Repair.

## 12. Deferred design questions

These are deliberately not decided by this planning seed:

- physical path and naming for implementation-ledger state;
- whether recovery generations use separate files, generation directories, or another lineage representation;
- exact event schema/versioning;
- whether a common ledger-integrity library should serve review, EHA and implementation ledgers without merging their domain authorities;
- minimum command surface;
- retention/garbage-collection policy for superseded recovered generations.

These questions require an RC7 design review before implementation.

## 13. RC7-D — Projection parity and portable evidence modules

RC7 should stop treating Markdown, NDJSON, Graphify and Mermaid as unrelated one-off output formats. They are different projections over evidence-bearing state and should share explicit parity contracts.

The intended topology is:

```text
canonical domain state / append-only events
        |
        +--> NDJSON durable/event representation
        +--> Markdown human-readable representation
        +--> Graphify graph/context projection
        +--> Mermaid deterministic visual projection
```

Parity does **not** mean every format has equal authority. It means every supported projection must preserve the domain fields, identities, provenance, bounds and lifecycle semantics required by its declared contract, and divergence must be detectable.

### 13.1 Markdown ↔ NDJSON adapter

RC7 should provide a configurable adapter layer based on mature Markdown AST tooling rather than implementing Markdown grammar itself. The preferred research direction is MDAST/remark (`remark-parse`/`remark-stringify`, `remark-gfm`, `remark-frontmatter`) plus a small CodeSleuth NDJSON envelope/validation layer.

The adapter MUST be reusable outside CodeSleuth and customizable for arbitrary repositories/projects. CodeSleuth-specific field names, headings, ledger schemas or path conventions must not be hard-coded into the generic codec.

A project adapter/profile must be able to declare at least:

- input Markdown dialect/extensions;
- frontmatter schema and preserved metadata;
- heading/section-to-record mapping rules;
- stable logical IDs and identity extraction;
- record type discrimination;
- required/optional fields;
- ordering and ordinal rules;
- project-specific schema version;
- provenance/digest fields;
- unknown-field/unknown-section behavior;
- validation severity and fail-closed boundaries;
- render policy back to Markdown;
- semantic round-trip expectations and explicitly unsupported byte-perfect guarantees.

The generic adapter must expose extension hooks rather than require forks for each project.

### 13.2 Documentation requirement

The portable adapter is not acceptable as an undocumented internal utility. It requires a full operator/developer contract covering:

1. conceptual model and authority boundaries;
2. adapter/profile schema reference;
3. Markdown AST and NDJSON envelope examples;
4. a minimal custom-project adapter walkthrough;
5. a complex example with frontmatter, tables, nested lists and GFM constructs;
6. identity/provenance rules;
7. semantic round-trip vs byte-round-trip limitations;
8. error/corruption handling;
9. migration/versioning rules;
10. testing a project adapter;
11. security considerations for untrusted Markdown/JSON;
12. integration with Graphify/Mermaid projections;
13. recipes for using the module independently of CodeSleuth.

A third-party project should be able to implement and validate its own mapping from this documentation without reading CodeSleuth internals.

### 13.3 Cross-projection parity contract

For a domain that opts into all four surfaces, RC7 should be able to test a canonical fixture through:

```text
NDJSON -> domain model -> Markdown
                  |
                  +-> Graphify
                  +-> Mermaid
```

and, where Markdown import is enabled:

```text
Markdown -> AST -> domain records -> NDJSON
```

Tests must compare semantic identity/provenance/status fields, not raw textual formatting. Markdown normalization is allowed; loss of declared domain meaning is not.

At minimum parity tests should detect:

- missing record IDs;
- dropped provenance/SHA/blob identity;
- reordered events where order is semantic;
- lifecycle/status disagreement;
- graph nodes/edges that refer to absent records;
- Mermaid rendering whose bounded selection disagrees with Graphify/domain selection;
- Markdown that presents a status not derivable from the same canonical state;
- NDJSON import that silently discards an unknown required field.

### 13.4 Portable module architecture

RC7 should investigate extracting the evidence machinery as composable modules/tooling that other projects can reuse without adopting the whole CodeSleuth product.

Candidate reusable units include:

- exact Git/source identity primitives;
- append-only NDJSON ledger primitives;
- atomic snapshot primitives;
- ledger validation and repair primitives;
- Markdown/MDAST ↔ domain-record adapters;
- projection parity validators;
- bounded graph projection primitives;
- Mermaid projection/render contracts;
- provenance/digest utilities;
- fixture/adversarial-test harnesses.

Project-specific behavior should arrive through schemas/profiles/adapters, while the generic mechanics remain shared. The goal is that a new evidence-heavy project configures domain vocabulary and mappings rather than rewriting storage, Markdown conversion, graphing, provenance, repair and parity infrastructure from scratch.

This is a transliterable/portable tooling direction, not permission to merge all domain authorities into one generic schema. Reuse mechanics; preserve domain semantics.

### 13.5 Scope restraint

This section is a required RC7 design topic, not an instruction to retrofit RC6. The RC7 design must decide which modules become stable reusable APIs and which remain CodeSleuth-internal. External packaging, registry publication or a separate SDK is not automatically in scope until explicitly accepted.
