# Post-RC6 Capability Expansion Ledger

**Status:** implementation/hardening ledger for `feature/post-rc6-capability-expansion`  
**Classification:** ordinary feature population and core hardening inside the frozen SIB0 capability classes  
**Architecture reopened:** **NO**  
**Integration state:** **NOT INTEGRATED** into `integration/rc7` by this implementation session  
**Acceptance note:** a green feature-branch run proves that exact feature-branch SHA only; it does not transfer SIB2 or integration acceptance.

## 1. Frozen identities and session boundary

The session re-resolved the active refs before modifying the repository:

| Ref | Exact SHA at session start | Role |
| --- | --- | --- |
| `integration/rc7` | `64c1986ab26c16957c7f126106f7dc2020edfcae` | implementation base |
| `main` | `330f4c533bb6a29cc7f762323ac3e64a14a27385` | divergent semantic-refit source only |
| `SIB` | `6621c65b868d3e279ddcbd8dee182a95c6fb29f8` | accepted RC6/SIB2 construction baseline; not moved |

Working branch:

```text
feature/post-rc6-capability-expansion
```

Draft integration vehicle:

```text
PR #121 -> integration/rc7
```

`main`, `SIB`, `dev/release-0.4.0`, tags, releases and `integration/rc7` were not moved by this session.

`main` and `integration/rc7` are divergent. The session therefore did **not** merge `main` wholesale. Main-only behavior was reused only when the current RC7 contracts still required it and the exact source artifacts could be carried over without importing unrelated history.

## 2. Protected-capability classification

The expansion stays inside existing classes:

| Capability class | Impact |
| --- | --- |
| `CC-HOST` | preserved: host still owns model/session/controller/tool execution |
| `CC-TUI` | recovered actionable Home update feedback; no new agent/runtime ownership |
| `CC-LIFE` | reusable stored-extension validation/publication backend |
| `CC-PACK` | Skill adapter plus recovered stored Playbook population |
| `CC-REPORT` | recovered bootstrap Playbooks continue using the existing reports Skill rather than a new persistence plane |
| `CC-PROF` | inspected only; writable profile overlay remains unresolved and was not invented |
| `CC-STATE` | deliberately not changed because RC7 ledger-integrity work is active elsewhere |
| `CC-GRAPH` | no change; existing graph read-side already closes the identified read gap |

No new fundamental capability class, model runtime, scheduler, controller, tool router, evidence authority, database or independently writable state plane was added.

## 3. Functional-gap disposition

| Gap | Disposition in this session | Reality after implementation |
| --- | --- | --- |
| reusable extension-management backend | **CLOSED** | implemented in `pack/.opencode/bin/extension_catalog.py` |
| Skill discovery/inspect/validate/local-load backend | **CLOSED** | implemented and test-covered; no Skill execution |
| generic Playbook adapter | **CLOSED** | implemented by delegation to existing `playbook_catalog.py`; Playbook semantics are not duplicated |
| source/install Verify parity for extension backend | **CLOSED** | `bin/extension_catalog.py` required by both Verify authorities |
| repository bootstrap Playbook population present on divergent `main` but missing from RC7 | **CLOSED** | exact main blobs recovered for `repository-bootstrap` and `repository-task-session` |
| Home update available but not actionable on RC7 TUI | **CLOSED IN CODE** | exact main runtime delta recovered; current acceptance run decides exact-head verification |
| repository graph read ergonomics | **NO GAP** | `context_graph_read.ts` already provides bounded resolve/neighbors/shortest-path/explain/diff and exact SourceRef reopen |
| Skill Catalog/Detail/Load-wizard TUI | **DEFER** | backend exists, but user-facing shared units are not yet extracted from the Playbook-first TUI |
| writable Profile adapter | **UNRESOLVED** | builtin profile resolution exists; no current authority proves a writable profile overlay contract |
| Tool/plugin/host-adapter loading | **DEFER** | wait for the shared product UI phase machine and explicit kind-specific ownership boundaries |
| review-state large-ledger query/pagination | **DEFER** | overlaps active `feature/rc7-ledger-integrity-core`; avoid parallel state semantics |
| external-evidence pagination | **DEFER** | useful hardening, but lower priority than current integrity work and not needed for this closure |

`CLOSED` here means implemented on this feature branch with an executable contract. It does not mean merged, promoted, SIB-accepted, or released.

## 4. Generic extension-management backend

New implementation:

```text
pack/.opencode/bin/extension_catalog.py
```

Implemented API surface:

```text
ExtensionCatalogError
ExtensionValidation
ExtensionRecord
ExtensionKindAdapter
pack_extension_ids()
discover_extensions()
resolve_extension_source()
inspect_extension_source()
install_extension()
skill_adapter()
playbook_adapter()
```

### Shared invariants implemented

- overlay wins over pack for the same id;
- `origin` follows the selected source path, not byte equality;
- local directory and ZIP source support only;
- ZIP extraction is bounded to 200 entries and 8 MiB total uncompressed bytes;
- traversal and absolute/root-escaping archive paths are rejected;
- root-level manifests are rejected; one top-level package directory is required;
- validation occurs before publication and again on the staged copy;
- shadowing a pack builtin requires explicit `allow_pack_shadow`;
- replacing an existing overlay requires explicit `replace_overlay`;
- replacement is staged before the previous usable overlay is moved;
- failed stage/publish attempts preserve or restore the prior overlay;
- extension installation copies stored bytes only and never invokes the loaded object;
- manifests are bounded before parsing.

### Skill adapter

The Skill adapter currently understands the active CodeSleuth `SKILL.md` contract needed for safe package management:

- frontmatter must exist and be terminated;
- `name` is required and must use a safe id;
- `name` must equal the package directory name;
- `description` is required;
- `slash`, when present, must resolve to `true` or `false`;
- a bounded `## Atomic contract` excerpt is exposed for inspection;
- absence of an Atomic Contract is a warning, not invented metadata;
- no Skill is loaded or executed by the adapter.

This is a **backend adapter**, not a claim that a Skill catalog screen or Skill load wizard exists.

### Playbook adapter

The generic Playbook adapter intentionally delegates parsing and validation to the existing `playbook_catalog.py` implementation. The expansion therefore reuses the accepted Playbook semantics rather than creating a second parser/validator that could drift.

## 5. Distribution parity

The first generic backend GREEN exposed a real packaging risk: unit tests could import `extension_catalog.py` from a source checkout while product Verify did not require the file to exist after installation.

That gap received its own RED/GREEN cycle. Both Verify authorities now require:

```text
bin/extension_catalog.py
```

Authorities:

```text
smoke.py
pack/.opencode/bin/review-pack-smoke.py
```

`tests/test_smoke_parity.py` asserts the new path exists in both required sets and that the source/installed required sets remain identical.

## 6. Semantic refit of main-only Playbook population

Two post-RC6 stored Playbooks existed on divergent `main` and remained valid under the current architecture:

```text
repository-bootstrap
repository-task-session
```

They were classified `REQUIRED / REUSE`, not merged from `main` as a branch.

The recovery used the exact Git blobs from current `main`, including the already-bounded Step decomposition and the verbatim bootstrap prompt. This avoids re-generation and preserves provenance.

Pinned content hashes remain:

```text
repository-bootstrap/PROMPT.verbatim.md
sha256 = cfdfb0b1fba6978088a256682ec935a7b4e2cc0ed9342eee1f3825c8a0834ab8

repository-task-session/steps/01-task-specific-session.md
sha256 = b9b0d48f5bc41ed898db97082baf18c795060a898532c0381deb470aa697df7b
```

The Playbooks remain stored host workflows. They do not create a CodeSleuth controller. Long-form outputs continue through the existing CodeSleuth reports persistence Skill.

## 7. Semantic refit of actionable Home update

The base `codesleuth_tui.py` blob was identical between the current RC7 lineage and `main`, allowing the main-only runtime delta to be evaluated without dragging unrelated branch history into RC7.

The recovered runtime behavior:

- Home exposes the existing update control as **Update CodeSleuth**;
- the action remains disabled until lifecycle evidence says an update is available;
- update availability highlights the existing control rather than creating another lifecycle path;
- lifecycle output containing an update-available witness marks the action available;
- `REVIEW PACK CURRENT` / `CODESLEUTH SOURCE CURRENT` clears the highlight;
- starting an update clears the stale available state;
- dispatch remains through the existing single-flight runtime feedback layer.

No background worker was allowed to mutate widgets directly and no new update authority was introduced.

## 8. TDD evidence ledger

The implementation deliberately recorded RED states before their corresponding production changes.

| Cycle | Exact RED SHA | Canonical run | Expected witness |
| --- | --- | --- | --- |
| generic extension backend | `e66ae784c38422a256b6d5d5e7440aed390e2fc0` | `34021589186` | `ModuleNotFoundError: extension_catalog` |
| source/install Verify parity | `b42c8933706395ee7c62538e49cd5cee88ea6755` | `34021793667` | `bin/extension_catalog.py` absent from Verify required set; `1 failed, 443 passed` on Ubuntu 3.10 |
| bootstrap Playbook recovery | `445cfcde3b06302f37d70fe862a42e127c73285e` | `34021943230` | missing builtin ids / missing exact Git blob; `2 failed, 444 passed` |
| actionable Home update | `202c6a4b8c7860413297455f81a2457298287b83` | `34022222199` | exactly three new TUI behavior failures; `3 failed, 446 passed, 10 skipped` on Ubuntu 3.12 |

Known implementation GREEN evidence before the final documentation head:

- `334cda7728b463e1b8325dd95c755f5f2b394cf2`: generic extension implementation reached green Linux Python/lint/MCP/anti-pattern jobs before later commits superseded the run;
- `a879ee796b744e53b9c1d7f11575d85db531290d`: recovered bootstrap Playbooks reached green Ubuntu Python 3.10/3.12 plus Rust, Graphify, durable-state/context-graph and TUI visual jobs; Windows jobs were cancelled only when a newer branch head superseded that run;
- `3518a4cf73fafa117d3955487cceceda0068e518`: actionable Home update GREEN candidate; later documentation commits create newer exact heads and therefore require their own acceptance.

The final branch head must still pass the canonical acceptance workflow after all documentation changes. A historical/intermediate green run is not transferred to a newer documentation commit.

## 9. Documentation reality corrections

[`EXTENSION-LOAD-UNITS.md`](EXTENSION-LOAD-UNITS.md) now distinguishes:

```text
backend implemented
!= user-facing TUI implemented
!= integrated into integration/rc7
!= exact-head accepted / SIB2
```

In particular:

- Skill backend adapter: implemented;
- Skill Catalog/Detail/Load-wizard TUI: pending;
- Profile writable overlay: unresolved, not assumed;
- Playbook remains the first complete user-facing shared-unit instance.

The Protected Capability Registry is deliberately **not** given a new SIB-origin forbidden regression by this feature session. SIB-origin history belongs to accepted evidence, not to a development branch that merely implemented a candidate invariant.

## 10. Explicit non-closures

The following work is intentionally not disguised as completed:

### Skill TUI

The next UI slice should extract a shared Catalog/Detail/Load phase machine from the current Playbook-first implementation and supply Playbook/Skill adapters to it. Copying `PlaybookLoadWizard` into `SkillLoadWizard` is explicitly rejected because it would create parallel install semantics.

### Profile loading

`repo_profile.ts` currently proves builtin profile detection/resolution. It does not prove the writable overlay destination, replacement semantics, or ownership boundary required for a safe Profile adapter. The correct status is `UNRESOLVED`, not “planned path guessed from naming”.

### Ledger readers

`review_state` already has exact finding lookup and amendment integrity, but bounded large-ledger query/pagination would overlap the active RC7 ledger-integrity implementation stream. This session leaves that state surface alone rather than manufacture a merge conflict with semantic consequences.

### Tool/plugin/host adapter loading

These remain extensions of the same backend/UI model, but their package and configuration ownership boundaries differ from directory-based Skills/Playbooks. They should be added only after the shared product UI exists and each kind’s write contract is explicit.

## 11. Handoff condition

This branch is suitable for coordinator review only after its literal final HEAD completes the canonical acceptance workflow without failures or cancellations.

The implementation session will not merge PR #121 into `integration/rc7` itself.

After integration, the resulting merge/composition SHA is a new exact candidate. Feature-branch acceptance does not automatically transfer to that composition.
