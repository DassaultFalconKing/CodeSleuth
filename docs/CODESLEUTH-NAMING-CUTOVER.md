# CodeSleuth naming cutover integration plan

**Status:** inventory accepted in 0.4.0; destructive runtime rename deferred  
**Classification:** `CORE-HARDENING`  
**Branch:** `chore/codesleuth-naming-cutover`  
**0.4.0 landing:** the machine-readable inventory, loader, dual-read compatibility, and this plan ship with the numbered release. Persistent state, launchers, updater/Verify filenames, and `REVIEW_PACK_*` environment names remain the live 0.4.0 surfaces so verified self-update/restart and installed compatibility paths are not renamed in the same release. Phases 2–9 stay queued until after `v0.4.0`.

## Goal

Replace the historical `review-pack` product namespace with `codesleuth` without changing legitimate review-domain names such as `repo-review`, `repository-deep-review`, `review_state.ts`, `review-compaction.ts`, `repo-reviewer`, or `opencode-review`.

The difficult part is not renaming files. The difficult part is preserving persistent lifecycle state and allowing an already-running pre-cutover updater to cross into the renamed runtime safely.

## Naming authority

The machine-readable source of truth is:

```text
pack/.opencode/codesleuth-naming.json
```

It contains:

- product display name and slug;
- canonical persistent filenames;
- canonical command and Python entrypoints;
- canonical environment variables;
- canonical CLI option names;
- canonical updater/Verify status strings;
- historical pre-cutover names;
- the exact temporary bootstrap bridge required by an old updater;
- migration policy flags.

Do **not** create a parallel `codesleuth_naming.py` full of string constants and do **not** scatter legacy literals through runtime code. The JSON is data; runtime code may load and validate the portions it needs.

A Python consumer may use a tiny loader such as:

```python
from __future__ import annotations

import json
from pathlib import Path


def load_naming(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 1:
        raise RuntimeError("unsupported CodeSleuth naming schema")
    return data
```

The loader is implementation plumbing, not a second naming authority.

### Shell and PowerShell wrappers

POSIX shell should not gain a JSON parser dependency merely to launch CodeSleuth. Root and installed shell/PowerShell wrappers may contain the few canonical literals they require, but contract tests must compare those literals against `codesleuth-naming.json`.

PowerShell may read the JSON if that makes a wrapper simpler, but it is not required.

## Target namespace

The JSON manifest is authoritative; this table is human-readable orientation only.

| Historical | Canonical |
| --- | --- |
| `review-pack` | `codesleuth` |
| `review-pack-update` | `codesleuth-update` |
| `review-pack-update.py` | `codesleuth_update.py` |
| `review-pack-smoke.py` | `codesleuth-verify.py` |
| `review_pack_tui.py` | `codesleuth_tui_base.py` |
| `review_pack_tui_core.py` | `codesleuth_tui_core.py` |
| `review_pack_tui_bootstrap.py` | `codesleuth_tui_bootstrap.py` |
| `review-pack.json` | `codesleuth.json` |
| `review-pack-user.json` | `codesleuth-user.json` |
| `REVIEW_PACK_DISTRIBUTION_ROOT` | `CODESLEUTH_DISTRIBUTION_ROOT` |
| `REVIEW_PACK_TARGET_ROOT` | `CODESLEUTH_TARGET_ROOT` |
| `--adopt-existing-pack` | `--adopt-existing-codesleuth` |
| `--force-pack-files` | `--force-codesleuth-files` |

The public integrity operation is **Verify**, hence `codesleuth-verify.py`; do not mechanically produce `codesleuth-smoke.py`.

## Integration sequence

The phases are intentionally ordered. Do not begin with repository-wide file renames.

### Phase 0: inventory

- [ ] Inventory maintained-source occurrences of `review-pack`, `review_pack`, and `REVIEW_PACK`.
- [ ] Classify each occurrence as runtime debt, migration data, archived history, or legitimate review-domain terminology.
- [ ] Treat `pack/.opencode/codesleuth-naming.json` as the authoritative whitelist of historical product names during migration.
- [ ] Record the current source-checkout update and pinned-dependency behavior before changing anything.

**Exit:** every retired product-name occurrence has a planned destination.

### Phase 1: make the JSON manifest authoritative

- [x] Add `pack/.opencode/codesleuth-naming.json`.
- [ ] Add a small stdlib-only loader/validator where Python consumers need naming data.
- [ ] Refactor installer, lifecycle, updater, bootstrap, TUI core and Verify logic to obtain lifecycle/product names from the manifest rather than inventing literals.
- [ ] Add schema/required-key tests for the manifest.
- [ ] Add tests that canonical and legacy mappings do not overlap incorrectly.
- [ ] Ensure fresh installation materializes `codesleuth-naming.json` as a managed CodeSleuth file.

**Exit:** Python lifecycle logic no longer owns independent product-name constants.

### Phase 2: persistent state migration

Implement one conflict-safe resolver driven by `canonical.state` and `legacy.state` from the manifest.

Required behavior:

1. canonical only: use canonical state;
2. legacy only: validate it, atomically create canonical state, preserve rollback evidence, retire legacy path;
3. both structurally identical: keep canonical state and retire legacy path;
4. both different: fail closed with an explicit naming/state conflict;
5. neither: normal fresh-install path.

Apply the same discipline to metadata and user settings.

- [ ] Migrate lifecycle authority to `codesleuth.json`.
- [ ] Migrate settings authority to `codesleuth-user.json`.
- [ ] Update install/update detection.
- [ ] Update archive/restore/uninstall.
- [ ] Add malformed-JSON and conflicting-state tests.

**Exit:** normal runtime reads and writes only canonical persistent filenames.

### Phase 3: rename Python modules

Rename together with all imports and restart targets:

```text
review_pack_tui.py           -> codesleuth_tui_base.py
review_pack_tui_core.py      -> codesleuth_tui_core.py
review_pack_tui_bootstrap.py -> codesleuth_tui_bootstrap.py
review-pack-update.py        -> codesleuth_update.py
review-pack-smoke.py         -> codesleuth-verify.py
```

- [ ] Update `codesleuth_tui.py` imports.
- [ ] Update installer imports.
- [ ] Update updater and restart tests.
- [ ] Update bootstrap re-exec path.
- [ ] Update Verify required-file checks.
- [ ] Compile each renamed Python file independently.

**Exit:** canonical runtime imports contain no retired product namespace.

### Phase 4: commands and environment

- [ ] Materialize `codesleuth-update` and `codesleuth-update.ps1`.
- [ ] Switch root launchers to `CODESLEUTH_DISTRIBUTION_ROOT` and canonical bootstrap.
- [ ] Switch installed launchers to `CODESLEUTH_TARGET_ROOT` and canonical bootstrap.
- [ ] Make Python consumers use the environment names from the manifest.
- [ ] Keep historical env names readable only at the one-time migration boundary when necessary.
- [ ] Test wrapper literals against the JSON manifest.

**Exit:** newly started CodeSleuth processes use only `CODESLEUTH_*` environment state.

### Phase 5: cross the old-updater boundary

The old updater remains executing after the new installer returns. It then looks for two old paths:

```text
bin/review-pack-smoke.py
bin/review_pack_tui_bootstrap.py
```

Those exact paths are declared in `migration.bridgeEntrypoints` in the JSON manifest.

Required transition:

1. detect that the update began from legacy state;
2. install the complete canonical runtime;
3. temporarily materialize only the bridge entrypoints listed by the manifest;
4. each bridge delegates immediately to canonical Verify/bootstrap;
5. do not record bridge files as canonical managed files;
6. after canonical bootstrap starts, remove them;
7. never create them on fresh install.

- [ ] Test old install -> new installer -> Verify -> restart -> bridge cleanup.
- [ ] Test fresh install contains no bridge files.

**Exit:** current development installations can cross the rename automatically without creating permanent aliases.

### Phase 6: CLI vocabulary and output

- [ ] Expose canonical CLI options from `canonical.cliOptions`.
- [ ] Accept historical option spellings only as hidden migration arguments while required by the old updater.
- [ ] Use `canonical.statusMessages` for updater/Verify output.
- [ ] Use the canonical temporary prefix for update clones.
- [ ] Ensure `--help` contains no retired product name.

**Exit:** normal CLI surface is entirely CodeSleuth-named.

### Phase 7: TUI and lifecycle integration

- [ ] TUI Check Updates invokes canonical updater.
- [ ] TUI Update invokes canonical updater.
- [ ] TUI Verify invokes canonical Verify.
- [ ] Restart supervisor re-execs canonical bootstrap.
- [ ] Installer output names canonical commands.
- [ ] Uninstall/archive handles canonical and migrated dev state safely.
- [ ] Preserve clean-`main`, explicit `origin/main`, fast-forward-only source update behavior.
- [ ] Preserve deliberate pinned `tools/codesleuth` behavior.

**Exit:** install, configure, Verify, update, restart, source-checkout update and uninstall all use canonical names.

### Phase 8: documentation

Update together:

- [ ] `README.md`;
- [ ] `README.ru.md`;
- [ ] `README.uk.md`;
- [ ] `docs/USER-GUIDE.md`;
- [ ] `docs/SELF-UPDATE.md`;
- [ ] TUI Help;
- [ ] installer and Verify examples.

README translation blob parity must remain green.

Archived historical documents may retain historical commands when clearly marked historical.

**Exit:** maintained user-facing material documents only canonical commands.

### Phase 9: enforcement gate

Turn the inventory into a failing contract test.

Scan maintained source for:

```text
review-pack
review_pack
REVIEW_PACK
```

Allowed historical product-name occurrences should be limited to:

- `pack/.opencode/codesleuth-naming.json`, where they are migration data;
- explicit migration-specific tests that verify old installations;
- clearly archived historical documents.

Do not whitelist broad runtime directories.

Also validate wrappers and runtime paths against the canonical section of the JSON manifest.

**Exit:** accidental reintroduction of retired product naming fails tests.

## Acceptance matrix

| Scenario | Expected result |
| --- | --- |
| manifest | valid schema and all required canonical/legacy keys |
| fresh install | canonical files plus `codesleuth-naming.json`; no legacy bridge |
| canonical install | normal operation with no migration activity |
| legacy dev install | state migrates and old updater crosses bridge |
| old/new state identical | canonical wins; legacy safely retired |
| old/new state different | fail closed |
| Verify | canonical Verify passes |
| update check | canonical updater checks without mutation |
| update apply | canonical updater installs, verifies, writes restart request |
| update restart | canonical bootstrap re-execs same target |
| source checkout | guarded `origin/main` fast-forward behavior unchanged |
| pinned dependency | `tools/codesleuth` never moves automatically |
| uninstall | canonical state archives/restores/removes safely |
| translations | RU/UK source-blob parity remains green |
| naming scan | no historical product namespace outside narrow migration/history whitelist |

## Implementation rule

The safe order is:

```text
JSON naming authority
    -> persistent state migration
    -> Python file/import rename
    -> wrappers + env rename
    -> one-time old-updater bridge
    -> TUI/lifecycle integration
    -> docs
    -> no-regression gate
```

Do not solve this with repository-wide textual replacement.

## Deferred

Packaging names, PyPI naming, release versioning, release notes, publishing and release timing remain out of scope until the internal naming cutover is complete and stable.
