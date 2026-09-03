# Portable Obsidian Adapter

A project-neutral, one-way renderer for turning structured domain objects into a useful Obsidian vault without making Obsidian an evidence authority.

The invariant is deliberately boring and therefore valuable:

```text
authority -> structured object -> derived Obsidian projection
```

Never:

```text
edited Obsidian note -> canonical truth
```

## Status

- Renderer: `0.1.0`
- Authority mode: `projectionAuthority: none`
- Round trip: `RENDER_ONLY`
- Native Obsidian plugin: optional, read-only companion
- Write-back/import/sync: intentionally absent

## What it generates

```text
EvidenceVault/
├── README.md
├── manifest.json
├── objects/
│   └── <kind>/<stable-id>.md
├── views/
│   └── *.base
└── graphs/
    ├── repair-lineage.canvas
    └── contract-traceability.canvas
```

Each object note contains YAML Properties, a stable object ID, schema ID, source digest, selected scalar/list fields, typed relation labels, wikilinks for human navigation, and the complete source object as canonicalized JSON in the note body.

The manifest binds source object digests to output file digests and always declares `RENDER_ONLY` and `projectionAuthority: none`.

## Install the headless renderer

From the CodeSleuth repository checkout:

```bash
python -m pip install -e tools/obsidian-adapter
```

The package has no runtime dependencies outside the Python standard library.

## Render a vault

JSON array:

```bash
codesleuth-obsidian render \
  --input objects.json \
  --profile tools/obsidian-adapter/profiles/codesleuth.json \
  --output EvidenceVault
```

NDJSON works with the same command:

```text
{"schemaId":"Contract","contractId":"C-1"}
{"schemaId":"Finding","findingId":"F-1","contractIds":["C-1"]}
```

Validate the generated bundle:

```bash
codesleuth-obsidian validate --vault EvidenceVault
```

Print its manifest:

```bash
codesleuth-obsidian manifest --vault EvidenceVault
```

Validation checks the non-authority contract and all output SHA-256 digests recorded by the manifest.

## Profiles

The renderer core knows nothing about CodeSleuth modules. Mapping is data-driven.

Minimal profile:

```json
{
  "profileId": "my-project",
  "profileVersion": 1,
  "schemaFieldCandidates": ["schemaId", "type"],
  "defaultIdFields": ["id"],
  "kinds": {
    "Incident": {
      "folder": "incidents",
      "idFields": ["incidentId", "id"],
      "relations": {
        "causedBy": ["causeIds"]
      }
    }
  }
}
```

A relation target is emitted as a wikilink, for example `[[INC-42]]`, while the relation name remains visible beside it. Obsidian Graph View therefore provides navigation, not pretend typed-graph semantics.

The bundled profiles are:

- `profiles/generic.json` for ordinary `schemaId` + `id` records;
- `profiles/codesleuth.json` for CodeSleuth evidence/repair/EHA families.

## CodeSleuth mapping

The CodeSleuth profile currently maps:

| Structured object | Note folder |
| --- | --- |
| `EvidenceClaimV1` | `objects/claims/` |
| `RepairCaseV1` | `objects/repair-cases/` |
| `RepairPacketV1` | `objects/repair-packets/` |
| `RepairLearningRecordV1` | `objects/lessons/` |
| `Finding` | `objects/findings/` |
| `Contract` | `objects/contracts/` |
| `RegressionWitness` | `objects/regression-witnesses/` |
| `EHACampaign` | `objects/eha-campaigns/` |
| `ImplementationLedgerEvent` | `objects/implementation-events/` |

It also emits six native Bases:

- Open Repairs
- Failed EHA Campaigns
- Contracts With Contradictions
- Lessons By Capability
- Forbidden Regressions
- Stale Evidence

Bases are ordinary `.base` YAML files. No Dataview or adapter-specific database is required.

## Regeneration semantics

On regeneration the adapter reads the previous valid `manifest.json` and removes only files listed as outputs of that previous `RENDER_ONLY` projection. Unrelated user files are not removed.

Generated object notes are machine-owned projection artifacts. Manual edits to them may be overwritten by regeneration and never flow back into canonical source objects.

## Optional native Obsidian plugin

The folder `obsidian-plugin/` contains a deliberately small companion plugin. It is **not required** to use the vault.

It provides commands to:

- show derived projection status;
- open projection home;
- open the repair-lineage Canvas;
- count indexed projection links through `MetadataCache`.

The v1 plugin uses read/navigation APIs only:

- `Vault.getAbstractFileByPath()`
- `Vault.cachedRead()`
- `Vault.getMarkdownFiles()`
- `MetadataCache.getFileCache()`
- `workspace.openLinkText()`

A static contract test rejects source code that calls common Obsidian write APIs such as `modify`, `process`, `processFrontMatter`, `create`, `delete`, or `rename`.

Build it using the normal Obsidian plugin toolchain:

```bash
cd tools/obsidian-adapter/obsidian-plugin
npm install
npm run test
npm run typecheck
npm run build
```

Then place `manifest.json` and the built `main.js` in:

```text
<Vault>/.obsidian/plugins/derived-structured-object-projection/
```

The plugin is optional because native Markdown, Properties, backlinks, Graph View, Bases and JSON Canvas already supply the primary user experience.

## Performance probe

The included probe measures **headless projection generation**, not Obsidian UI performance:

```bash
python tools/obsidian-adapter/scripts/perf_probe.py 1000
python tools/obsidian-adapter/scripts/perf_probe.py 10000
python tools/obsidian-adapter/scripts/perf_probe.py 100000
```

Observed in the implementation environment:

| Objects | Time | Generated bytes | Objects/s |
| ---: | ---: | ---: | ---: |
| 1,000 | 0.171 s | 603,720 | 5,836.4 |
| 10,000 | 2.132 s | 6,034,805 | 4,691.3 |
| 100,000 | 20.977 s | 60,345,646 | 4,767.1 |

These numbers prove the renderer itself is not the obvious bottleneck. They do **not** claim that Graph View, backlinks, Bases or Canvas stay equally responsive at those sizes. UI-scale performance must be measured inside the target Obsidian build on representative hardware.

## Security and semantic-loss rules

- Duplicate stable IDs fail closed.
- IDs that can escape paths or are invalid portable file names fail closed.
- Repository strings are serialized as data, not executed.
- The complete structured source remains in each note body so YAML Properties do not become a lossy substitute for nested semantics.
- Graph View edges are untyped visual links; relation labels in notes and Canvas remain the human-readable typed relation projection.
- Canvas includes only relationships whose target exists in that selected Canvas set; this is a bounded visualization, not the canonical evidence graph.
- `.base` views filter derived Properties; they do not adjudicate contracts or EHA results.

## Development

Run Python tests:

```bash
cd tools/obsidian-adapter
pytest -q
```

Run the plugin read-only contract:

```bash
cd tools/obsidian-adapter/obsidian-plugin
node tests/read_only_contract.test.mjs
```

The adapter is intentionally reusable. Add project behavior through a profile before considering a core fork or a new Obsidian API dependency.
