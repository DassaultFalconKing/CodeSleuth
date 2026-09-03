# Portable Obsidian Adapter Design

**Status:** Approved implementation design
**Base:** `docs/rc7-ledger-authority-repair-plan` @ `befa2dd182b986bf56c3318bb578150f36c16e40`

## Goal

Extract the Obsidian projection work into a reusable, project-neutral adapter that turns validated structured objects into a derived Obsidian vault while preserving the invariant:

`authority -> structured object -> derived Obsidian projection`

Never the reverse.

## Architecture

The subsystem has two layers.

1. **Portable headless renderer** under `tools/obsidian-adapter/`. It consumes JSON/NDJSON structured objects plus a projection profile and emits Markdown notes, YAML Properties, wikilinks, `.base` views, JSON Canvas and a deterministic manifest. Obsidian is not required to generate the vault.
2. **Optional native Obsidian plugin** under `tools/obsidian-adapter/obsidian-plugin/`. It is read-only and exists only for navigation/diagnostics. It may read vault files and MetadataCache and open generated artifacts, but it must not mutate CodeSleuth authority, EHA state, SIB state, contracts or evidence ledgers.

The portable renderer is the product boundary. The native plugin is an optional UX companion.

## Authority contract

Every generated note MUST contain `projectionAuthority: none`.

Every generated manifest MUST declare:

- `rendererId: obsidian-vault`
- `roundTripCapability: RENDER_ONLY`
- `projectionAuthority: none`
- source object IDs/schema IDs/digests
- output file digests

Manual edits inside the vault are never imported automatically. Regeneration from the same canonical structured input may overwrite machine-owned projection files. There is no `sync`, `push`, `import` or write-back command in v1.

## Portable input contract

The renderer accepts either a JSON array or NDJSON records. A profile defines:

- `profileId` and `profileVersion`;
- schema field candidates;
- per-schema output folder and ID field candidates;
- relation fields that become human-navigation wikilinks;
- Base view definitions.

The generic core does not import CodeSleuth modules. A CodeSleuth profile maps known CodeSleuth object families without forking renderer code.

## Output layout

```text
<output>/
  objects/<kind>/<stable-id>.md
  views/*.base
  graphs/repair-lineage.canvas
  graphs/contract-traceability.canvas
  manifest.json
  README.md
```

Stable IDs are vault-wide unique. Human graph edges use wikilinks. Typed relation names remain explicit in note bodies and Canvas edge labels so Graph View does not become a fake typed graph authority.

## Security and determinism

Repository-provided strings are data. Use JSON serialization for embedded structured bodies and safe YAML scalar serialization for frontmatter/Base files. Reject unsafe path components and duplicate object IDs. Sort objects, relations, views and manifest outputs deterministically before hashing.

The renderer executes no repository-supplied code and resolves no template path outside the adapter profile roots.

## Native Obsidian plugin boundary

Allowed surface in v1:

- `Vault.getMarkdownFiles()` / `Vault.cachedRead()` for projection inspection;
- `MetadataCache.getFileCache()` and resolved/unresolved link metadata for diagnostics;
- `workspace.openLinkText()` for navigation;
- optional Bases custom view registration only if native generated `.base` files prove insufficient.

Forbidden in v1:

- `Vault.modify()` / `Vault.process()`;
- `FileManager.processFrontMatter()`;
- any API that writes authority or emits adjudication/EHA/contract state;
- any bidirectional sync.

## Acceptance

The first implementation is acceptable when:

- same input produces byte-stable projection artifacts;
- duplicate IDs fail closed;
- every note and manifest declares non-authority;
- source and output digests are present;
- CodeSleuth and generic profiles both render without core forks;
- generated wikilinks resolve for declared relations;
- six useful Bases are generated for the CodeSleuth profile;
- two curated JSON Canvases preserve stable node/edge IDs and typed edge labels;
- 1k and 10k synthetic-object generation probes complete successfully in the headless renderer;
- native plugin builds and contains no write path;
- canonical CodeSleuth RC6/SIB/EHA refs and evidence ledgers remain untouched.
