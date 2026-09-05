# CodeSleuth Agent Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a normal CodeSleuth install self-describing to any repository agent and make stored playbooks browsable without memorizing IDs.

**Architecture:** Reuse the existing `AGENTS.md` ownership/lifecycle discipline but keep the new always-on discovery block separate from the existing opt-in workflow-rules block. Extend the sole `codesleuth-naming.json` namespace authority with `/codesleuth/playbooks`, derive catalog output from `playbook_catalog.py`, and make no-argument `/codesleuth/playbook` browse rather than execute.

**Tech Stack:** Python 3.10+, pytest, Markdown host-native OpenCode commands, existing CodeSleuth lifecycle and naming manifests.

**Spec:** `docs/RC7-AGENT-DISCOVERY-DISTRIBUTION-DESIGN.md`

## Global Constraints

- Runtime base is exact accepted `integration/rc7 @ 64c1986ab26c16957c7f126106f7dc2020edfcae`.
- Do not move `main`, `SIB`, `dev/release-0.4.0`, tags, or Releases.
- Do not create a second naming or playbook registry authority.
- Reports and context graphs remain derived; graphs are not material evidence authority.
- Existing `policy.enforceAgentsMdRules` semantics remain opt-in/default-off.
- Normal project install/update must materialize discovery; uninstall/purge must remove only CodeSleuth-owned discovery text.
- OpenCode remains execution authority; browse commands do not execute playbooks.

---

### Task 1: RED contract for installed AGENTS discovery

**Files:**
- Modify: `tests/test_agents_policy.py`
- Later modify: `pack/.opencode/bin/codesleuth_project/agents_policy.py`
- Later modify: `install.py`
- Later modify: `pack/.opencode/bin/codesleuth_project/__init__.py`
- Later create: `pack/.opencode/policy/agents-discovery.md`

**Interfaces:**
- Produces: `DISCOVERY_BEGIN`, `DISCOVERY_END`, `canonical_discovery_text()`, `ensure_agents_discovery(repo)`, `remove_agents_discovery(repo)`.
- Install/update callers invoke `ensure_agents_discovery(repo)` for non-self targets.
- Uninstall invokes `remove_agents_discovery(repo)` before runtime cleanup.

- [ ] Add failing tests proving ordinary install with workflow rules disabled still injects discovery containing `.codesleuth/reports/`, `.opencode/state/reviews/`, `.opencode/state/context-graphs/`, `/codesleuth/playbooks`, `/codesleuth/playbook <id>`, `codesleuth-*`, and `DassaultFalconKing/CodeSleuth`.
- [ ] Add failing test proving uninstall removes discovery while preserving pre-existing user `AGENTS.md` bytes.
- [ ] Run the hosted Python suite on the test-only SHA and record the expected missing discovery API/marker failure as FIRST RED.
- [ ] Implement the minimal separate managed discovery block by reusing/refactoring the existing ownership primitives without changing opt-in workflow-rule semantics.
- [ ] Hook normal install/update and uninstall lifecycle paths.
- [ ] Run focused `python -m pytest -q tests/test_agents_policy.py` and require GREEN.

### Task 2: RED contract for deterministic playbook browse namespace

**Files:**
- Modify: `tests/test_naming_cutover.py`
- Modify: `tests/test_playbook_catalog.py`
- Later modify: `pack/.opencode/codesleuth-naming.json`
- Later modify: `pack/.opencode/bin/playbook_catalog.py`
- Later create: `pack/.opencode/commands/codesleuth/playbooks.md`
- Later create: `pack/.opencode/commands/playbooks.md`
- Later modify: `pack/.opencode/commands/codesleuth/playbook.md`
- Later modify: `pack/.opencode/commands/playbook.md`

**Interfaces:**
- Naming authority operation: `playbooks.path == "/codesleuth/playbooks"`, compatibility alias `/playbooks`.
- Catalog producer: `format_playbook_catalog(records: Iterable[PlaybookRecord]) -> str`.
- Every rendered item includes ID, origin, summary/description and `/codesleuth/playbook <id>`.

- [ ] Add failing naming test for canonical `/codesleuth/playbooks`, alias materialization, and canonical command file.
- [ ] Add failing catalog test for deterministic sorted browse output and overlay origin.
- [ ] Add command-contract test that no-arg singular playbook command uses browse output and does not silently invent an ID.
- [ ] Run hosted tests and retain the test-only RED evidence.
- [ ] Add the new operation only to `codesleuth-naming.json`; let existing derivation consume it.
- [ ] Implement deterministic formatter from actual `discover_playbooks()` records, not a second ID list.
- [ ] Materialize canonical + compatibility browse commands and update singular command no-arg semantics.
- [ ] Run focused `python -m pytest -q tests/test_naming_cutover.py tests/test_playbook_catalog.py` and require GREEN.

### Task 3: Full N2 verification and admission

**Files:**
- Modify only if required by exact current verification failures; no scope expansion.

**Interfaces:**
- N2 final head must remain a descendant of `64c1986ab26c16957c7f126106f7dc2020edfcae` before coordinator integration.

- [ ] Run `python scripts/contributor_antipatterns.py scan --strict`.
- [ ] Run `python -m ruff check .`.
- [ ] Run `python -m pytest -q`.
- [ ] Require current hosted acceptance workflow success on the exact N2 head.
- [ ] Coordinator reviews diff for authority/lifecycle scope.
- [ ] Merge serially into `integration/rc7` without moving protected/release refs.
- [ ] Require fresh hosted acceptance on the resulting integration merge SHA before declaring the next accepted base for N3.
