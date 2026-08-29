# Export surfaces

**Status:** feature implementation on `feature/export-surfaces`; not acceptance evidence until an exact candidate head passes the canonical gates.

CodeSleuth exports are explicit retained copies of already existing views. They do not create a renderer authority, graph authority, evidence store, or acceptance ledger.

## 1. Export root

Retained exports live below the already ignored boundary:

```text
.codesleuth/exports/
  graphs/
  ui/
```

Normal graph query, Mermaid rendering, TUI navigation, and review execution must not write retained exports as a side effect. A retained artifact exists only after an explicit export operation.

## 2. Graph bundle

Every graph export is one directory:

```text
.codesleuth/exports/graphs/<bundle>/
  manifest.json
  graph.json
  graph.mmd
  graph.svg        # optional; only when explicitly requested and renderer succeeds
```

`manifest.json` is written last and is the completion marker for the bundle. Existing bundle directories are never silently overwritten.

All graph manifests declare:

- `kind: codesleuth-graph-export`;
- `exportAuthority: none`;
- `retainedArtifactOnly: true`;
- `derivedPresentationOnly: true`;
- source authority/provenance copied from the originating view;
- bounded selection/truncation state;
- SHA-256 and byte size for every retained artifact.

The export is not repository truth, finding evidence, review authority, or EHA acceptance evidence.

## 3. Repository-context export

The repository export tool must consume `codesleuth_context_get` with `includeMermaid=true`.

This preserves the hardened consumption order:

```text
exact tracked source
  -> RepositoryContextProjection
  -> exact-head bounded context capsule
  -> retained graph.json / graph.mmd / optional graph.svg
```

The export module must not call Graphify directly. Graphify remains only an optional candidate structural provider upstream of `RepositoryContextProjection`.

`graph.json` contains the bounded exact-head context capsule used for model orientation. `graph.mmd` contains the secondary Mermaid presentation attached to that same capsule.

## 4. Protected-capability export

The protected export combines:

- the bounded query result from the tracked Protected Capability Registry; and
- the Mermaid envelope derived from the same selection arguments.

`docs/protected-capabilities.json` remains registry authority.

## 5. EHA export

The EHA export combines:

- the durable EHA ledger summary; and
- a bounded Mermaid lineage selection.

`.opencode/state/reviews/<review>/eha.ndjson` remains append-only EHA authority. No exported file may be cited as proof that a SHA passed SIB0/SIB1/SIB2.

## 6. SVG rendering

SVG is optional. JSON and Mermaid export do not depend on Chromium or Mermaid CLI.

When SVG is explicitly requested, `pack/.opencode/bin/codesleuth_export.py` performs a retained render using:

- exact `@mermaid-js/mermaid-cli` version `11.16.0`;
- explicit absolute Python interpreter identity at the TypeScript tool boundary;
- explicit absolute Node and Chromium executable identities inside the renderer;
- Mermaid `securityLevel: strict`;
- Chromium host resolution disabled;
- bounded Mermaid source size;
- atomic final SVG write.

The runtime identity variables are:

```text
CODESLEUTH_PYTHON_EXECUTABLE=/absolute/path/to/python
CODESLEUTH_MERMAID_NODE=/absolute/path/to/node
CODESLEUTH_MERMAID_BROWSER=/absolute/path/to/chrome-or-chromium
```

The Mermaid CLI source is either the exact-pinned `tools/mermaid-qa` runtime in a CodeSleuth source checkout or an explicitly configured absolute runtime path:

```text
CODESLEUTH_MERMAID_RUNTIME=/absolute/path/to/runtime
# or
CODESLEUTH_MERMAID_CLI=/absolute/path/to/mermaid-cli/src/cli.js
```

Relative executable/runtime settings and ambient PATH lookup are not part of the renderer correctness contract. If an exact runtime identity is unavailable, SVG export fails closed. It must never report a successful image export merely because Mermaid source was generated.

## 7. TUI image export

`export_tui_svg(app, repo_root, name)` is the framework adapter for a retained Textual screenshot.

It writes:

```text
.codesleuth/exports/ui/<name>/
  manifest.json
  screen.svg
```

It uses Textual's real `app.export_screenshot()` output. It does not create synthetic mockups and does not change the documentation graphics contract.

The adapter is deliberately separate from TUI navigation. A later UI action may call it, but merely opening a screen must never create an export.

## 8. Formats

Current module contract:

| Surface | JSON | Mermaid | SVG | PNG/JPEG/WebP |
| --- | --- | --- | --- | --- |
| repository graph | yes | yes | optional | no |
| protected graph | yes | yes | optional | no |
| EHA graph | yes | yes | optional | no |
| TUI current view | manifest | n/a | yes | no |

Raster formats can be added later as derivatives of an already retained SVG. They must not gain separate graph selection or authority semantics.
