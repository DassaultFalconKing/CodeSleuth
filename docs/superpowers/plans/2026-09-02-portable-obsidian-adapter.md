# Portable Obsidian Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable one-way Obsidian vault renderer plus a minimal read-only native Obsidian companion plugin.

**Architecture:** A stdlib-only Python renderer consumes JSON/NDJSON structured objects and a JSON projection profile, then emits deterministic Markdown/YAML/Bases/JSON Canvas artifacts and a digest-bound manifest. A separate TypeScript Obsidian plugin only inspects generated projections and navigates them; it never writes canonical state.

**Tech Stack:** Python 3.11+, pytest, TypeScript, Obsidian plugin API, esbuild.

**Spec:** `docs/superpowers/specs/2026-09-02-portable-obsidian-adapter-design.md`

## Global Constraints

- `projectionAuthority` is always `none` in generated projection artifacts.
- Renderer round trip is `RENDER_ONLY`.
- No import, sync, write-back, SIB/EHA mutation or canonical evidence-ledger mutation.
- Generic core must not import CodeSleuth modules.
- Repository strings are data and must be safely serialized.
- Duplicate stable IDs fail closed.

---

### Task 1: Profile and normalization contract

**Files:**
- Create: `tools/obsidian-adapter/src/codesleuth_obsidian_adapter/profile.py`
- Create: `tools/obsidian-adapter/profiles/generic.json`
- Create: `tools/obsidian-adapter/profiles/codesleuth.json`
- Test: `tools/obsidian-adapter/tests/test_profile.py`

**Interfaces:**
- Produces: `ProjectionProfile.load(path)`, `ProjectionProfile.classify(record)`, `ProjectionProfile.object_id(schema_id, record)`, `ProjectionProfile.relations(schema_id, record)`.

- [ ] Write tests for profile loading, CodeSleuth schema classification, ID selection, relation extraction and duplicate/unsafe ID rejection.
- [ ] Run the focused tests and verify RED.
- [ ] Implement immutable profile parsing and normalization with stdlib JSON only.
- [ ] Run focused tests and verify GREEN.

### Task 2: Deterministic note rendering

**Files:**
- Create: `tools/obsidian-adapter/src/codesleuth_obsidian_adapter/render.py`
- Create: `tools/obsidian-adapter/src/codesleuth_obsidian_adapter/serialization.py`
- Test: `tools/obsidian-adapter/tests/test_render_notes.py`

**Interfaces:**
- Consumes Task 1 profile APIs.
- Produces: `render_note(normalized_object) -> str`, `render_projection(records, profile, output_dir) -> ProjectionManifest`.

- [ ] Write tests proving `projectionAuthority: none`, stable IDs/schema IDs/source digests, deterministic bytes, escaped YAML values and wikilinks for declared relations.
- [ ] Run focused tests and verify RED.
- [ ] Implement safe YAML scalars, canonical JSON source digests and Markdown note rendering.
- [ ] Run focused tests and verify GREEN.

### Task 3: Bases, Canvas and manifest

**Files:**
- Create: `tools/obsidian-adapter/src/codesleuth_obsidian_adapter/bases.py`
- Create: `tools/obsidian-adapter/src/codesleuth_obsidian_adapter/canvas.py`
- Create: `tools/obsidian-adapter/src/codesleuth_obsidian_adapter/manifest.py`
- Test: `tools/obsidian-adapter/tests/test_bundle.py`

**Interfaces:**
- Produces generated `.base` files, `repair-lineage.canvas`, `contract-traceability.canvas`, `manifest.json`.

- [ ] Write tests for six CodeSleuth Bases, stable Canvas node/edge IDs, typed edge labels, `RENDER_ONLY`, source/output hashes and deterministic manifest ordering.
- [ ] Run focused tests and verify RED.
- [ ] Implement the minimum Base/Canvas/manifest generators.
- [ ] Run focused tests and verify GREEN.

### Task 4: CLI and validation

**Files:**
- Create: `tools/obsidian-adapter/src/codesleuth_obsidian_adapter/cli.py`
- Create: `tools/obsidian-adapter/src/codesleuth_obsidian_adapter/__init__.py`
- Create: `tools/obsidian-adapter/pyproject.toml`
- Test: `tools/obsidian-adapter/tests/test_cli.py`

**Interfaces:**
- Produces commands `render`, `validate`, `manifest`.

- [ ] Write tests for JSON array and NDJSON input, duplicate-ID failure, validation of non-authority markers and manifest digest verification.
- [ ] Run focused tests and verify RED.
- [ ] Implement argparse CLI and validation.
- [ ] Run focused tests and verify GREEN.

### Task 5: Performance fixtures

**Files:**
- Create: `tools/obsidian-adapter/scripts/perf_probe.py`
- Test: `tools/obsidian-adapter/tests/test_perf_fixture.py`

- [ ] Write a deterministic synthetic fixture test generating 1k objects.
- [ ] Run and verify RED before the probe exists.
- [ ] Implement synthetic 1k/10k/100k generation with timing and output-size reporting; keep 100k opt-in.
- [ ] Run 1k and 10k probes and record results in README.

### Task 6: Read-only native Obsidian plugin

**Files:**
- Create: `tools/obsidian-adapter/obsidian-plugin/manifest.json`
- Create: `tools/obsidian-adapter/obsidian-plugin/package.json`
- Create: `tools/obsidian-adapter/obsidian-plugin/tsconfig.json`
- Create: `tools/obsidian-adapter/obsidian-plugin/esbuild.config.mjs`
- Create: `tools/obsidian-adapter/obsidian-plugin/src/main.ts`
- Create: `tools/obsidian-adapter/obsidian-plugin/tests/read_only_contract.test.mjs`

- [ ] Write a static contract test that rejects Obsidian write APIs (`modify`, `process`, `processFrontMatter`, create/delete/rename).
- [ ] Run it and verify RED before plugin source exists.
- [ ] Implement a plugin that locates `manifest.json`, validates `projectionAuthority: none`, shows projection status and opens generated Home/Base/Canvas files.
- [ ] Build/lint and run the read-only contract test.

### Task 7: Documentation and CodeSleuth integration notes

**Files:**
- Create: `tools/obsidian-adapter/README.md`
- Create: `docs/OBSIDIAN-ADAPTER.md`
- Modify: `docs/RC7-OBSIDIAN-ADAPTER-RESEARCH.md`

- [ ] Document portable input/profile contracts, CLI, vault layout, authority boundary, native plugin install and extension guidance.
- [ ] Mark the research spike disposition as accepted implementation direction while preserving pluginless-first conclusions.
- [ ] Document CodeSleuth mappings and explicitly forbid RC6/SIB/EHA/write-back changes.

### Task 8: Verification

- [ ] Run all adapter pytest tests.
- [ ] Run the native plugin read-only contract test and TypeScript build.
- [ ] Run 1k and 10k performance probes.
- [ ] Compare the feature branch against `docs/rc7-ledger-authority-repair-plan` and verify changes are limited to adapter/docs/test files.
- [ ] Confirm no RC6, SIB ref, EHA state or canonical evidence ledger file changed.
