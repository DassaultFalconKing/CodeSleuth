# Post-RC6 Capability Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close safe functional gaps inside the frozen post-RC6 capability classes without adding a new runtime, authority, persistence plane, or capability class.

**Architecture:** Extract reusable extension-management mechanics as a bounded Python library under the installed pack, prove it first with Playbook compatibility and a new Skill adapter, then expose only the product surfaces that have executable acceptance evidence. Refit already-written main-only post-RC6 feature population only when it remains valid on the current `integration/rc7` architecture.

**Tech Stack:** Python stdlib, pytest, existing Textual TUI, existing OpenCode pack/Skill/Playbook conventions.

**Spec:** `docs/EXTENSION-LOAD-UNITS.md`

## Global Constraints

- Base identity: `integration/rc7 @ 64c1986ab26c16957c7f126106f7dc2020edfcae`.
- Accepted construction baseline remains `SIB @ 6621c65b868d3e279ddcbd8dee182a95c6fb29f8` and is not moved.
- Do not move `main`, `SIB`, `dev/release-0.4.0`, tags, or releases.
- Do not merge this branch into `integration/rc7` from this implementation session.
- Preserve host execution authority and the existing Playbook default behavior.
- Extension loading is inspect/validate/write only; it never executes Skills, Playbooks, tools, or plugins.
- Overlay origin is determined by the selected source path, never by byte equality.
- Pack collisions require an explicit opt-in before an overlay may shadow a builtin.
- ZIP input is bounded and rejects traversal, absolute paths, root-level manifests, excessive entries, and excessive uncompressed size.
- Existing usable overlays survive failed replacement.
- Profile overlay remains UNRESOLVED until current authority identifies a real writable overlay contract.
- Documentation must distinguish implemented, integrated, tested, and accepted states.

---

### Task 1: Generic extension-management contract and Skill adapter

**Files:**
- Create: `tests/test_extension_catalog.py`
- Create: `pack/.opencode/bin/extension_catalog.py`

**Interfaces:**
- Produces `ExtensionRecord`, `ExtensionValidation`, `ExtensionKindAdapter`, `discover_extensions()`, `inspect_extension_source()`, `install_extension()`, `skill_adapter()`, and `playbook_adapter()`.
- `playbook_adapter()` reuses the current Playbook parser/validator so generic management cannot silently redefine Playbook semantics.

- [ ] Write RED tests for overlay precedence, truthful origin, Skill metadata validation, bounded ZIP input, explicit pack-shadow confirmation, transactional replacement, no execution, and generic Playbook compatibility.
- [ ] Observe the new tests fail because `extension_catalog` does not exist.
- [ ] Implement the minimum generic core and adapters.
- [ ] Run the focused tests and preserve all existing `test_playbook_catalog.py` behavior.

### Task 2: Refit safe main-only post-RC6 feature population

**Files:**
- Reuse only semantically valid files from the main-only repository bootstrap/task-session Playbooks and their regression tests.
- Refit TUI Home update affordance only if it applies cleanly to current `integration/rc7` lifecycle semantics.

**Interfaces:**
- Repository bootstrap remains a stored Playbook, not a new review runtime.
- Task continuation remains a stored Playbook, not a second controller.

- [ ] Compare each main-only claim with current RC7 contracts and classify REQUIRED/SUPERSEDED/RETIRED/UNRESOLVED.
- [ ] Port only REQUIRED claims whose current dependencies still exist.
- [ ] Preserve bounded Step materialization and report persistence through the existing reports Skill.
- [ ] Keep TUI update work separate if current RC7 has materially changed that surface.

### Task 3: Documentation reality sync

**Files:**
- Modify: `docs/EXTENSION-LOAD-UNITS.md`
- Create: `docs/POST-RC6-CAPABILITY-EXPANSION.md`
- Modify other current docs only where a factual status statement is stale.

**Interfaces:**
- Status tables distinguish `implemented library`, `product-exposed`, `tested`, and `accepted`.

- [ ] Record actual implemented kind adapters and leave unresolved kinds explicitly unresolved/planned.
- [ ] Record the current branch/base identities and protected capability impact.
- [ ] Record deferred gaps with reasons rather than presenting them as implementation.

### Task 4: Verification and handoff

- [ ] Run contributor antipattern strict scan through canonical CI.
- [ ] Run focused Python tests through canonical CI.
- [ ] Run full acceptance jobs triggered by the PR and inspect failures rather than treating workflow existence as PASS.
- [ ] Record exact tested HEAD and CI evidence in `docs/POST-RC6-CAPABILITY-EXPANSION.md`.
- [ ] Leave the branch/PR for coordinator integration; do not self-merge into `integration/rc7`.
