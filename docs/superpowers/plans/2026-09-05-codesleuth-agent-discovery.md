# CodeSleuth Agent Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a normal CodeSleuth install self-describing to any repository agent and make stored playbooks browsable without memorizing IDs.

**Architecture:** Reuse and broaden the existing always-on `AGENTS.md` reports pointer rather than creating another managed block. Keep the opt-in workflow-rules block unchanged. Extend the sole `codesleuth-naming.json` namespace authority with `/codesleuth/playbooks`, derive browse output from `playbook_catalog.py`, and make no-argument `/codesleuth/playbook` browse rather than execute.

**Tech Stack:** Python 3.10+, pytest, Markdown host-native OpenCode commands, existing CodeSleuth lifecycle and naming manifests.

**Spec:** `docs/RC7-AGENT-DISCOVERY-DISTRIBUTION-DESIGN.md`

## Global Constraints

- Runtime base is exact accepted `integration/rc7 @ 64c1986ab26c16957c7f126106f7dc2020edfcae`.
- Do not move `main`, `SIB`, `dev/release-0.4.0`, tags, or Releases.
- Do not create a second naming or playbook registry authority.
- Reports and context graphs remain derived; graphs are not material evidence authority.
- Existing `policy.enforceAgentsMdRules` semantics remain opt-in/default-off.
- Existing `AGENTS_BEGIN` / `AGENTS_END` reports-pointer markers remain the always-on lifecycle-owned discovery markers for compatibility.
- OpenCode remains execution authority; browse commands do not execute playbooks.

---

### Task 1: RED contract for installed AGENTS discovery

**Files:**
- Create: `tests/test_rc7_agent_discovery.py`
- Later modify: `pack/.opencode/bin/codesleuth_project/paths.py`
- Existing callers: `install.py`, `pack/.opencode/bin/codesleuth_project/__init__.py`

**Interfaces:**
- Preserve: `AGENTS_BEGIN`, `AGENTS_END`, `AGENTS_POINTER`, `ensure_agents_reports_pointer(repo)`, `remove_agents_reports_pointer(repo)`.
- Broaden `AGENTS_POINTER` from reports-only pointer to concise CodeSleuth repository discovery map.

- [ ] Add failing test proving ordinary install with workflow rules disabled still injects a managed pointer containing `.codesleuth/reports/`, `.opencode/state/reviews/`, `.opencode/state/context-graphs/`, `.opencode/playbooks/`, `/codesleuth/playbooks`, `/codesleuth/playbook <id>`, `codesleuth-*`, and `DassaultFalconKing/CodeSleuth`.
- [ ] Add failing test proving uninstall removes the managed pointer while preserving pre-existing user `AGENTS.md` content.
- [ ] Run hosted Python suite on the test-only SHA and record the exact missing discovery content failure as FIRST RED.
- [ ] Expand only `AGENTS_POINTER`; retain existing marker/lifecycle functions and opt-in workflow-rules semantics.
- [ ] Run focused `python -m pytest -q tests/test_rc7_agent_discovery.py` and require GREEN.

### Task 2: RED contract for deterministic playbook browse namespace

**Files:**
- Continue in: `tests/test_rc7_agent_discovery.py`
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
- [ ] Add command-contract test that no-arg singular playbook command explicitly browses and performs no implicit execution.
- [ ] Retain test-only RED evidence.
- [ ] Add the new operation only to `codesleuth-naming.json`; let existing namespace derivation consume it.
- [ ] Implement deterministic formatter from actual `discover_playbooks()` records, not a second ID list.
- [ ] Materialize canonical + compatibility browse commands and update singular command no-arg semantics.
- [ ] Run focused `python -m pytest -q tests/test_rc7_agent_discovery.py tests/test_naming_cutover.py tests/test_playbook_catalog.py` and require GREEN.

### Task 3: Full N2 verification and admission

- [ ] Run `python scripts/contributor_antipatterns.py scan --strict`.
- [ ] Run `python -m ruff check .`.
- [ ] Run `python -m pytest -q`.
- [ ] Require current hosted acceptance workflow success on the exact N2 head.
- [ ] Coordinator reviews diff for authority/lifecycle scope.
- [ ] Merge serially into `integration/rc7` without moving protected/release refs.
- [ ] Require fresh hosted acceptance on the resulting integration merge SHA before declaring the next accepted base for N3.
