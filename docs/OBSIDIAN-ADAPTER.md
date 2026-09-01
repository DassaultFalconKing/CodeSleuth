# Obsidian Adapter

**Status:** portable derived-projection adapter implementation
**Implementation:** `tools/obsidian-adapter/`
**Authority:** none

## Architectural position

The Obsidian adapter is a renderer/read-model surface around structured evidence objects. It is not part of the canonical evidence authority chain.

```text
CodeSleuth authority
  -> validated structured object
  -> portable Obsidian adapter
  -> Markdown / Properties / wikilinks / Bases / JSON Canvas
  -> human navigation
```

Nothing on the right-hand side automatically mutates anything on the left-hand side.

Every generated note carries:

```yaml
projectionAuthority: none
```

Every bundle manifest declares:

```text
roundTripCapability = RENDER_ONLY
projectionAuthority = none
```

## Why it is separate from `pack/.opencode/plugins`

`pack/.opencode/plugins/` is an OpenCode host-plugin surface. The Obsidian adapter must also work for projects that do not run CodeSleuth through OpenCode. Its generic renderer therefore lives under `tools/obsidian-adapter/` and consumes structured files, not host internals.

The native Obsidian companion plugin is nested inside the adapter only because it is one optional frontend for the same projection format.

## CodeSleuth projection families

The supplied CodeSleuth profile covers:

- `EvidenceClaimV1`
- `RepairCaseV1`
- `RepairPacketV1`
- `RepairLearningRecordV1`
- Finding
- Contract
- RegressionWitness
- EHA campaign/verdict records represented as `EHACampaign`
- implementation ledger events represented as `ImplementationLedgerEvent`

Stable IDs become note names and wikilink targets. Exact SHA, profile digests, evidence refs, assumptions, limitations, result/status and other scalar/list properties remain visible in frontmatter when present. The full source object is also preserved as JSON in the note body.

## Human workflows

### Repair lineage

Use the generated `graphs/repair-lineage.canvas` plus backlinks/wikilinks to navigate repair cases, packets, regression witnesses, lessons and EHA history.

Canvas relation labels are projection metadata. Canvas node positions and missing off-canvas edges have no authority meaning.

### Contract traceability

`graphs/contract-traceability.canvas` selects Contract/Finding/Repair/Lesson-related objects. Ordinary Graph View supplies exploratory connectivity across all emitted wikilinks, while the Canvas gives a bounded curated lineage.

### Bases

The CodeSleuth profile emits:

1. Open Repairs
2. Failed EHA Campaigns
3. Contracts With Contradictions
4. Lessons By Capability
5. Forbidden Regressions
6. Stale Evidence

These are generated native `.base` files. Their filters operate only on the derived Properties stored in the projected Markdown notes.

## Native plugin boundary

The optional plugin is intentionally read-only. It may inspect `manifest.json`, read generated notes through `Vault.cachedRead`, inspect `MetadataCache`, and navigate using workspace APIs.

It does not call Obsidian file mutation APIs and does not expose EHA, contract, evidence or SIB write actions.

A future plugin feature must justify why native Markdown/Properties/Bases/Canvas navigation is insufficient before adding API surface.

## Forbidden extensions in this adapter

Do not add any of the following without a separate architecture decision and authority/adjudication contract:

- automatic import of edited note Properties;
- note-to-ledger synchronization;
- Canvas-driven repair execution;
- EHA PASS/FAIL calculation inside Obsidian;
- contract adjudication inside Obsidian;
- canonical evidence writes;
- RC6/SIB reference mutation.

A manually edited derived note is merely a manually edited derived note. Regeneration from canonical structured objects is allowed to overwrite it.

## Verification

The adapter test suite verifies deterministic rendering, non-authority markers, stable object identity, duplicate-ID fail-closed behavior, manifest SHA-256 binding, native Bases, Canvas edge IDs/labels, JSON/NDJSON CLI support, and safe regeneration that removes only previously generated outputs.

The native plugin has an explicit static read-only API contract test.

Generation probes are provided for 1k, 10k and opt-in 100k synthetic objects. They measure renderer throughput only; Obsidian Graph/Bases/backlink/Canvas responsiveness remains an application-level performance question.

## RC7 relationship

This implementation realizes the `obsidian-vault` multi-artifact renderer direction described in `RC7-STRUCTURED-OBJECT-MULTIRENDERER.md` without changing RC6 authority, release refs, SIB refs, EHA state or canonical evidence ledgers.

The correct decision remains **PLUGINLESS_SUFFICIENT** for core projection. The bundled native plugin is **PLUGIN_USEFUL** only as a small optional navigation/diagnostic convenience.
