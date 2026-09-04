# Portable User Witness Core Design

Date: 2026-09-04  
Status: design freeze candidate  
Repository: `DassaultFalconKing/CodeSleuth`  
Base runtime branch: `feature/rc6-eha-brownfield-bootstrap`  
Base runtime SHA: `ac341eb78ef849af1fb1dbed89b06b06af9853fa`  
Design branch: `design/portable-user-witness-core`

## 1. Purpose

Refactor the existing CodeSleuth TUI User Witness into a portable, renderer-independent diagnostic toolkit that can be copied, vendored, or packaged into other projects, specifically including PII Parser and Rustagent, without bringing CodeSleuth runtime dependencies or Textual assumptions with it.

The portable core must preserve the strongest property of the current implementation: it records what the user-facing interface actually exposes and keeps that observation distinct from developer-only implementation mapping.

The portable core is diagnostic infrastructure. It is not acceptance authority, evidence authority, SIB authority, or EHA authority.

## 2. Problem statement

The current implementation already separates user-safe output from developer mapping and records deterministic witness bundles, but the implementation still combines three concerns in one module:

1. generic witness semantics and bundle recording;
2. Textual/TUI extraction rules;
3. CodeSleuth-specific identity, paths, journeys, and naming.

Current coupling includes:

- `semantic_snapshot(root)` directly understands Textual-like widget class names and attributes;
- `_validate_journey()` requires `surface == "tui"`;
- `capture_textual_checkpoint()` is colocated with generic recorder logic;
- the manifest kind is `codesleuth-user-witness`;
- CLI wording is explicitly CodeSleuth/TUI-specific.

Copying that module into another project would therefore transfer hidden product and renderer assumptions. That is not portability; it is distributed technical debt wearing a travel hat.

## 3. Goals

The design SHALL provide:

1. a standalone Python package under `portable/user-witness/`;
2. a generic normalized witness contract independent of UI framework;
3. an adapter boundary that converts a concrete UI surface into the normalized contract;
4. a Textual adapter that preserves current CodeSleuth TUI behavior;
5. a compatibility shim so existing CodeSleuth imports and acceptance tests need not migrate atomically;
6. a deterministic bundle format suitable for CI artifacts and human review;
7. explicit project/profile metadata instead of hard-coded CodeSleuth identity;
8. a portability test proving the package works outside the CodeSleuth tree;
9. an extension path for browser/GUI adapters and BrowserUse-like agents without changing the core contracts.

## 4. Non-goals

This change SHALL NOT:

- make User Witness an acceptance authority;
- promote witness output into SIB or EHA evidence automatically;
- introduce browser automation yet;
- parse TypeScript source as a substitute for observing a running UI;
- add React, Vue, Svelte, Electron, Tauri, Playwright, Puppeteer, CDP, or BrowserUse dependencies to the core;
- move CodeSleuth-specific journeys into the portable package;
- change current RC6 product behavior;
- redesign the current User Witness journey vocabulary beyond what is necessary to remove the TUI-only restriction;
- create a separate repository or release process during this refit.

## 5. Architectural invariant

The primary invariant is:

> Source code may explain an observed UI state, but may never substitute for observing the UI state.

The data path is:

```text
running UI / rendered surface
          |
          v
surface adapter
          |
          v
SemanticSnapshotV1
          |
          v
portable User Witness core
          |
          +--> user-safe observation
          +--> semantic UX diff
          +--> diagnostic witness bundle
          |
          v
optional developer mapping
```

Neither the adapter nor the core may claim product acceptance.

## 6. Package layout

Target layout:

```text
portable/user-witness/
  pyproject.toml
  README.md
  src/
    user_witness/
      __init__.py
      schema.py
      core.py
      recorder.py
      cli.py
      adapters/
        __init__.py
        textual.py
  tests/
    test_schema.py
    test_core.py
    test_bundle.py
    test_textual_adapter.py
    test_portability.py

scripts/tui_user_witness.py
  # CodeSleuth compatibility shim

docs/tui-user-witness/
  # CodeSleuth-specific journeys and smoke definitions remain here
```

The package root must be self-contained. A consumer must not need `pack/`, `scripts/`, CodeSleuth modules, repository-relative imports, or Textual to use the core.

## 7. Core contracts

### 7.1 `JourneyV1`

A generic journey describes user intent and expected observable behavior. It must retain the current user-centered fields while removing the hard-coded requirement that `surface == "tui"`.

Required properties:

```text
schema_version
id
surface
user
entry
trajectory
affordances
```

`surface` becomes an opaque adapter/profile identifier such as:

```text
tui
browser
electron
tauri
custom
```

The core validates structure, not framework semantics.

### 7.2 `SemanticSnapshotV1`

The adapter emits a framework-neutral snapshot:

```json
{
  "schema_version": 1,
  "surface": "tui",
  "screen": {
    "title": "Settings",
    "kind": "screen"
  },
  "nodes": [
    {
      "role": "button",
      "text": "Apply",
      "state": {"disabled": false},
      "developer_ref": {
        "adapter": "textual",
        "type": "Button",
        "id": "apply"
      }
    }
  ]
}
```

The portable core may carry `developer_ref`, but user-facing rendering must hide it by default.

The core SHALL NOT depend on concrete widget class names, DOM selectors, React component names, accessibility APIs, or source maps.

### 7.3 `WitnessBundleV1`

The generic manifest kind becomes:

```text
kind: user-witness
```

Required authority fields remain explicit:

```text
diagnostic_only: true
acceptance_authority: false
```

Optional producer/profile metadata identifies the embedding project:

```json
{
  "producer": {
    "project": "CodeSleuth",
    "profile": "codesleuth-tui",
    "version": 1
  }
}
```

This metadata is descriptive only and may not change bundle authority.

The bundle continues to contain deterministic per-state artifacts:

```text
journey.json
trajectory.json
manifest.json
ux-diff.txt
NN-state-name/
  semantic.json
  user-view.txt
  developer-view.txt
  user-probe.txt
  ux-diff.txt
  optional screenshot artifact
```

Screenshot format is adapter-defined metadata. The core must not assume SVG.

## 8. Adapter contract

Adapters own framework-specific observation.

Conceptually:

```python
class SurfaceAdapter(Protocol):
    surface: str

    def snapshot(self, subject: object) -> SemanticSnapshotV1:
        ...

    def capture_artifacts(self, subject: object) -> Mapping[str, Artifact]:
        ...
```

The exact Python shape may use protocols, dataclasses, mappings, or functions, but the architectural rule is fixed:

> The recorder consumes a normalized snapshot. It does not walk UI framework objects itself.

Adapters may emit developer mapping metadata. The portable core controls when that metadata is exposed.

## 9. Textual adapter

The first adapter moves the current Textual-specific logic out of the core:

- visible/display filtering;
- widget-class to semantic-role mapping;
- label/text/placeholder extraction;
- value/disabled/checked/expanded/focus state extraction;
- `walk_children()` traversal;
- Textual SVG screenshot capture.

The adapter SHALL keep Textual as an optional dependency.

Importing `user_witness`, `user_witness.core`, `user_witness.schema`, or `user_witness.recorder` in an environment without Textual must succeed.

Only importing or invoking `user_witness.adapters.textual` may require Textual-compatible behavior.

## 10. CodeSleuth compatibility shim

Existing CodeSleuth imports from:

```text
scripts.tui_user_witness
```

shall continue to work during RC6.

The shim may re-export portable symbols and wrap the Textual adapter, but it SHALL NOT duplicate the portable core implementation.

CodeSleuth-specific defaults may remain in the shim:

- producer project name;
- CodeSleuth profile name;
- existing CLI description compatibility;
- current journey locations;
- Textual screenshot title conventions.

This permits incremental migration and keeps current hosted acceptance meaningful.

## 11. User-safe and developer-facing views

The split remains mandatory.

### User-safe view

May contain:

- visible role;
- visible text;
- observable state;
- visible navigation/state changes;
- semantic UX differences.

Must not expose by default:

- framework class names;
- DOM selectors;
- widget ids;
- component names;
- source files;
- source-map positions;
- event handler names.

### Developer view

May additionally contain adapter-supplied implementation mapping.

This separation is essential for browser agents too: an agent acting as a user must first reason from the rendered application, not from privileged implementation hints.

## 12. Browser and BrowserUse extension path

Browser support is deliberately an adapter, not a second core.

A future browser adapter may collect:

- accessibility tree roles/names/states;
- DOM-visible text and controls;
- focus and keyboard reachability;
- viewport and screenshot artifacts;
- navigation state;
- dialogs and overlays;
- selected network-visible errors;
- stable developer mapping such as DOM locator, source-map ref, or component ref.

A BrowserUse-like agent may then consume the portable bundle or user-safe probe as its observation layer.

The intended relationship is:

```text
Playwright / CDP / BrowserUse / other browser driver
                    |
                    v
             Browser adapter
                    |
                    v
          SemanticSnapshotV1
                    |
                    v
          User Witness core
```

The portable core must not depend on the browser-driving library. This allows the same witness semantics to be used with Playwright today, BrowserUse tomorrow, or some future browser-driving contraption humans invent after deciding the previous three abstractions were insufficient.

## 13. Source-code bridges

Future TypeScript/React/Vue/Svelte/source-map integration belongs in optional developer bridges, not observation core.

Potential future mapping:

```text
observed node
  -> DOM/accessibility node
  -> component
  -> TypeScript source symbol
  -> SourceRef / commit identity
```

The bridge explains observed behavior. It may never fabricate an observation from source code alone.

## 14. Portability requirements

The package is considered portable only if all of the following hold:

1. `portable/user-witness/` can be copied into a fresh temporary repository.
2. Its package installs from that copied directory.
3. Its core tests run without the CodeSleuth repository present.
4. Core tests run without Textual installed.
5. A synthetic adapter can emit `SemanticSnapshotV1` and produce a complete `WitnessBundleV1`.
6. No Python source under the portable package imports from `scripts`, `pack`, or any CodeSleuth module.
7. No portable path is resolved relative to the CodeSleuth repository root.
8. No manifest requires the string `CodeSleuth`.
9. CodeSleuth can still provide its identity through producer/profile metadata.

These are executable acceptance criteria for portability, not merely documentation claims.

## 15. Backward compatibility requirements

After refit, the current CodeSleuth witness behavior must remain valid:

- existing journey JSON files validate;
- current semantic TUI observations remain equivalent in user-visible meaning;
- current user probe still hides implementation identifiers;
- current UX diff still excludes developer ids;
- current real TUI witness bundle is still emitted by the dedicated visual acceptance job;
- `diagnostic_only == true`;
- `acceptance_authority == false`;
- existing current-head acceptance coverage must remain green.

Exact byte identity of generated files is not required if generic schema normalization requires a deliberate versioned change, but semantic compatibility and explicit migration tests are required.

## 16. Error handling

The core should fail closed on malformed witness data.

Examples:

- missing required journey keys -> validation error;
- invalid snapshot shape -> validation error;
- adapter returns non-normalizable state -> adapter error before recording;
- artifact write failure -> bundle finalization failure;
- duplicate or ambiguous state identity -> deterministic naming or explicit error;
- unsupported schema version -> explicit error.

The recorder must not silently write a partial manifest claiming a complete bundle after a failed checkpoint.

Framework-specific failures remain adapter errors and must not be converted into fake user observations.

## 17. Determinism

Given the same normalized journey, snapshots, actions, expectations, and artifacts, the portable core should produce semantically deterministic output.

The core must not add wall-clock time, random ids, host paths, repository paths, environment-specific values, or machine-specific metadata unless explicitly supplied as producer metadata.

This is important for cross-project CI and later cross-renderer comparison.

## 18. Testing strategy

Implementation SHALL be test-driven.

### Core tests

- journey validation independent of surface;
- user-safe rendering hides `developer_ref`;
- developer rendering exposes it when requested;
- semantic diff compares normalized snapshots;
- bundle manifest carries generic `kind: user-witness`;
- authority flags are fixed to diagnostic/non-acceptance;
- screenshot/artifact handling is format-neutral;
- malformed states fail closed.

### Adapter tests

- Textual-like widgets map to the same semantic roles as current RC6;
- layout-only widgets remain filtered;
- visible control state is preserved;
- Textual screenshot capture stays outside the core.

### Portability test

A test copies only `portable/user-witness/` to a temporary standalone project, installs it, and runs a minimal smoke scenario without CodeSleuth imports.

### Compatibility tests

Current `tests/test_tui_user_witness.py` and `tests/test_tui_user_witness_bundle.py` remain passing through the shim, with updates only where the generic manifest schema requires an explicit compatibility assertion.

### Hosted acceptance

The final implementation candidate must pass the full exact-head CodeSleuth hosted acceptance plus the dedicated TUI visual/User Witness job before integration.

## 19. Migration sequence

Implementation should proceed in this order:

1. add failing portable-core contract tests;
2. create package/schema/core primitives;
3. move generic rendering/diff/recording behavior into core;
4. add Textual adapter and its tests;
5. replace `scripts/tui_user_witness.py` implementation with compatibility delegation;
6. run existing TUI witness tests;
7. add standalone-copy portability test;
8. document vendoring/package use for PII Parser and Rustagent;
9. run complete local/canonical gates available to the branch;
10. obtain exact-head hosted acceptance.

No browser adapter is part of this implementation sequence.

## 20. Future portability targets

The design explicitly supports at least these future consumers:

### PII Parser

May define its own journeys and adapter/profile while reusing the core bundle, diff, and probe contracts.

### Rustagent

May use the Python package as external diagnostic tooling initially, or later implement an equivalent adapter/producer around the same JSON contracts. The core contract must therefore avoid Python-object-only semantics in persisted data.

### Browser/GUI agents

May use Browser/Playwright/CDP/BrowserUse-style drivers to create `SemanticSnapshotV1` and let the same core produce user-safe diagnostics and reproducible witness bundles.

## 21. Freeze decision

The accepted architecture is:

```text
portable User Witness core
    + generic schemas
    + generic semantic rendering/diff
    + generic deterministic recorder
    + generic CLI
    + adapter interface
        + Textual adapter now
        + Browser/GUI adapters later
    + CodeSleuth compatibility shim
    + CodeSleuth journeys outside portable package
```

Hard boundaries:

```text
portable core imports from CodeSleuth = 0
portable core imports from Textual = 0
portable core hard-coded project identities = 0
portable core acceptance authority = false
portable core evidence authority = false
```

The implementation is complete only when the portable directory survives extraction into an otherwise empty project and its own core tests still pass.