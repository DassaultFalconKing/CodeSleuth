# RC7 / Post-RC7 Obsidian Adapter Research

**Status:** RESEARCH INPUT / NOT YET ACCEPTED AS RC7 DELIVERY SCOPE  
**Purpose:** evaluate Obsidian as an external human knowledge/read-model surface for CodeSleuth structured evidence without making Obsidian a source/evidence authority.

## 1. Finding

Obsidian is unusually compatible with the planned CodeSleuth multi-renderer architecture because its user-visible data model is already built from open/local artifacts:

- Markdown notes;
- YAML properties/frontmatter;
- internal links/backlinks;
- Graph View over note links;
- Bases database-like views over file/note properties;
- `.base` YAML view definitions;
- `.canvas` files using the open JSON Canvas format;
- a TypeScript plugin API with Vault, FileManager, MetadataCache and Bases APIs.

Official references inspected:

- https://obsidian.md/help/properties
- https://obsidian.md/help/bases
- https://obsidian.md/help/bases/syntax
- https://obsidian.md/help/Plugins/Graph%20view
- https://obsidian.md/help/Plugins/Backlinks
- https://obsidian.md/help/Plugins/Canvas
- https://docs.obsidian.md/Plugins/Vault
- https://docs.obsidian.md/plugins/guides/bases-view
- https://jsoncanvas.org/spec/1.0/

## 2. Strongest architectural opportunity: pluginless derived vault export

The first useful adapter does not require an Obsidian plugin.

CodeSleuth can render structured domain objects into a dedicated derived vault:

```text
CodeSleuth typed objects / ledgers
        |
        v
ObsidianVaultRenderer
        |
        +--> objects/*.md
        +--> YAML properties
        +--> wikilinks/backlinks
        +--> views/*.base
        +--> graphs/*.canvas
        +--> manifest.json
```

This gives the user:

- readable/editable Markdown;
- structured property browsing;
- database-like filtering/sorting/grouping through Bases;
- graph exploration through internal links;
- spatial curated lineage views through JSON Canvas;
- ordinary filesystem ownership/backup/versioning.

The exported vault remains a rebuildable read model. Manual edits do not flow back into CodeSleuth authority unless a separately defined import/adjudication workflow explicitly accepts them.

## 3. Mapping CodeSleuth objects to Obsidian

### One note per stable object

Candidate note families:

```text
claims/
findings/
repairs/
lessons/
contracts/
capabilities/
eha-campaigns/
implementation-events-or-summaries/
```

Each note should have stable frontmatter such as:

```yaml
---
codesleuth_schema: RepairCaseV1
codesleuth_id: RC-008
subject_sha: ...
result: FAIL
profile_id: project-sib1
profile_digest: ...
authority: eha-ledger
projection_authority: none
---
```

Obsidian Properties do not support arbitrary nested structured properties cleanly in the normal UI, so deep objects should remain in note bodies or referenced child records rather than being flattened beyond recognition merely to satisfy a property table.

### Relations

Use wikilinks only for relations that are useful as human graph edges, for example:

```text
RepairCase -> violated Contract
RepairCase -> Finding
RepairCase -> RepairPacket
RepairPacket -> Candidate SHA note
Candidate -> EHA Campaign
Repair -> Regression Witness
Repair -> Lessons Learned
```

Typed relation metadata should remain available in frontmatter/body or a manifest because Obsidian Graph View lines represent links, not arbitrary CodeSleuth edge semantics.

### Bases

Generate `.base` views for useful user workflows, for example:

- Open repair cases;
- EHA campaigns by result/profile;
- contracts with unresolved contradictions;
- lessons learned by capability;
- regressions by contract;
- evidence freshness/staleness;
- implementation requirements by status.

Bases keeps source data in Markdown/properties and stores view/filter/formula definitions separately, making it a natural database-like **projection** rather than a competing database authority.

### Canvas

JSON Canvas can render curated spatial views from the same stable object IDs.

Useful canvases:

- failed SHA -> RepairCase -> repair delta -> regression witness -> accepted SHA;
- capability -> contracts -> tests -> findings -> repairs;
- SIB0/SIB1/SIB2 maturity path;
- authority map / active development scope.

JSON Canvas edges support labels, which is useful where ordinary Obsidian Graph View cannot express typed edge meaning strongly enough.

## 4. Adapter modes

### Mode O1 — `obsidian-export` renderer

**Recommended first experiment.**

- one-way;
- no Obsidian installation required to generate artifacts;
- outputs Markdown/YAML/Bases/JSON Canvas bundle;
- rebuildable from canonical CodeSleuth objects;
- explicit `projectionAuthority: none`;
- deterministic manifest/hashes;
- safe to delete/regenerate.

This fits the RC7 multi-renderer architecture and may be cheap enough to use as a portability/dogfood fixture without making Obsidian a required dependency.

### Mode O2 — `obsidian-import` / semantic round-trip adapter

**Post-RC7 candidate unless a concrete RC7 need appears.**

Potential use:

- ingest user annotations/decisions from specifically managed note fields;
- validate source export digest/generation;
- convert edits into proposed CodeSleuth adjudication records.

Rules:

- no arbitrary vault edits become authority;
- imported changes are proposals until domain validation/adjudication;
- preserve source note/path/digest and adapter version;
- conflicts remain explicit.

### Mode O3 — Obsidian plugin bridge

**Post-RC7 research/implementation candidate.**

A TypeScript plugin can use official APIs for live integration:

- `Vault` for file access;
- `FileManager.processFrontMatter` for safe property modification;
- `MetadataCache` for resolved/unresolved link information;
- Bases API/custom Bases views for CodeSleuth-specific presentations;
- workspace/URI integration to navigate exact notes/views.

Possible value:

- live refresh after CodeSleuth export;
- click-through from evidence note to source locator/tool action;
- dedicated CodeSleuth Bases view;
- explicit user adjudication actions that emit a bounded proposal file/request rather than silently mutating authority.

The plugin must not independently calculate EHA PASS, repair legality, source authority or contract truth.

## 5. Why not make Obsidian the database

Obsidian Bases is deliberately database-like while keeping data in files/properties. That is attractive precisely because CodeSleuth does not need to hand evidence authority to another storage engine.

Correct relation:

```text
CodeSleuth authorities
        ↓
structured domain objects
        ↓
Obsidian projection bundle
        ↓
Graph / Backlinks / Bases / Canvas / user navigation
```

Not:

```text
user edited an Obsidian property
        ↓
therefore EHA/contract state changed
```

## 6. Useful research questions for a dedicated agent

A future host-capable research session should test, on a disposable Obsidian vault:

1. deterministic generation of hundreds/thousands of notes with properties and links;
2. Graph View usefulness and limitations for typed CodeSleuth relations;
3. Bases performance/filtering/grouping over realistic evidence counts;
4. `.base` generation compatibility and stability across Obsidian versions;
5. JSON Canvas generation and stable layout strategies;
6. whether Bases custom-view API is mature enough for a CodeSleuth plugin view;
7. MetadataCache link refresh behavior after external generated-file changes;
8. safe frontmatter update patterns and conflict behavior;
9. whether Obsidian URI is sufficient for click-through navigation without a plugin;
10. what minimum plugin surface, if any, materially improves O1 export;
11. mobile behavior of generated vault/Bases/Canvas;
12. performance at 10k, 100k and higher evidence-note/link scales;
13. how to preserve typed edge semantics without polluting notes with artificial links;
14. how user annotations can be separated from regenerated machine-owned sections;
15. how to prove regeneration does not destroy user-owned annotations.

## 7. Agent task candidate

A strong research task is:

> Build a disposable CodeSleuth evidence vault from synthetic `EvidenceClaimV1`, `RepairCaseV1`, `RepairLearningRecordV1`, EHA and contract fixtures; generate Markdown/frontmatter/wikilinks, `.base` database-like views and JSON Canvas lineage views; measure usability/performance; then implement the smallest read-only Obsidian plugin prototype only if native vault artifacts cannot provide required navigation. Treat all Obsidian state as derived/non-authoritative and report exactly which capabilities require plugin APIs.

The output should be a research report and prototype on an isolated branch, not automatic adoption into RC7.

## 8. Recommendation

Adopt **Obsidian export compatibility as a renderer design target**, because it validates that RC7 structured objects are genuinely portable and human-usable.

Do not yet make an Obsidian plugin a required RC7 deliverable. Start with O1 pluginless export; use the research session to decide whether O2/O3 deserve post-RC7 implementation.
