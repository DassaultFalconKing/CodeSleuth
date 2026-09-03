# RC6 Pre-SIB Feature Refit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refit the two useful non-authoritative feature deltas onto the current hosted-green RC6 line, verify each exact resulting identity, integrate them sequentially, and preserve/archive stale source branches without importing obsolete ancestry.

**Architecture:** Treat `feature/rc6-eha-brownfield-bootstrap` as the only runtime integration authority. Rebuild useful deltas as target-native commits whose parent is the current RC6 head. Preserve derived/read-only boundaries: Obsidian remains `RENDER_ONLY` with `projectionAuthority:none`; TUI User Witness remains diagnostic with `acceptance_authority:false`. Do not import RC7 planning commits or old graph/execution semantics.

**Tech Stack:** Python 3.10/3.12, Node 22.23.2, Textual, GitHub Actions, Obsidian plugin TypeScript, existing CodeSleuth canonical acceptance matrix.

**Spec:** `docs/RC7-STRUCTURED-OBJECT-MULTIRENDERER.md`, `docs/PORTABLE-TOOLS.md`, `docs/GRAPH-CONSUMPTION-CONTRACT.md`, `docs/CODESLEUTH-PRODUCT-CONTRACT.md`.

## Global Constraints

- Runtime base must be re-resolved immediately before each refit and merge.
- No SIB, EHA, main, release, tag, or GitHub Release movement during this sweep.
- No wholesale merge from `docs/rc7-ledger-authority-repair-plan` or stale release branches.
- Derived projections must never become evidence/acceptance authority.
- Every integrated commit must receive fresh exact-head hosted acceptance; prior source-branch PASS does not transfer.
- Archive branches preserve exact historical source SHAs before any active stale branch is retired.

---

### Task 1: Refit portable Obsidian adapter

**Files:**
- Add only the 30 paths currently changed by PR #112 under `tools/obsidian-adapter/**`, `docs/OBSIDIAN-ADAPTER.md`, its spec/plan, and `.github/workflows/obsidian-adapter.yml`.
- Do not add RC7 planning-set documents from the source branch ancestry.

**Interfaces:**
- Consumes structured JSON/NDJSON objects supplied by a caller.
- Produces deterministic Markdown/Bases/Canvas projection plus manifest.
- Must preserve `roundTripCapability: RENDER_ONLY` and `projectionAuthority: none`.

- [ ] Create target-native branch from exact current RC6 head.
- [ ] Apply only the PR #112 changed-file blobs.
- [ ] Harden dedicated workflow to bind and verify exact checkout identity using the current repository pattern.
- [ ] Run/refetch dedicated adapter CI and full canonical CodeSleuth acceptance.
- [ ] Review exact diff for forbidden authority/write-back behavior.
- [ ] Open PR to `feature/rc6-eha-brownfield-bootstrap` and merge only after all exact-head jobs pass.

### Task 2: Refit TUI User Witness

**Files:**
- Add `scripts/tui_user_witness.py`.
- Add `docs/TUI-USER-WITNESS.md`, `docs/USER-WITNESS-PROTOCOL.md`, `docs/tui-user-witness/**`.
- Add `tests/test_tui_user_witness.py`, `tests/test_tui_user_witness_bundle.py`.
- Integrate the witness tests into the current TUI visual job without reverting newer acceptance workflow behavior.

**Interfaces:**
- Produces diagnostic UI trajectory/snapshot bundles.
- Manifest must retain `diagnostic_only: true` and `acceptance_authority: false`.
- Model-as-user representation must not expose implementation identifiers by default.

- [ ] Re-resolve the post-Task-1 RC6 head.
- [ ] Create a new target-native refit branch from that head.
- [ ] Apply only the User Witness feature files; manually merge current acceptance workflow wiring.
- [ ] Run focused Python/TUI tests and full canonical exact-head acceptance.
- [ ] Open PR and merge only after fresh PASS.

### Task 3: Archive stale branches

- [ ] Preserve each stale active branch at `archive/2026-09-03/<original-name>` pointing to its exact current SHA.
- [ ] Treat branches already fully contained in the new RC6 as stale integration sources, not merge candidates.
- [ ] Archive obsolete divergent branches whose unique deltas conflict with current architecture (old atomic Skill stack, raw scoped Mermaid implementation, old Playbooks source branches, superseded RC6 repair/refit carriers).
- [ ] Keep planning authority branches and `SIB` untouched.
- [ ] Close superseded open PRs whose active source is fully represented elsewhere, with a disposition note where appropriate.

### Task 4: Final verification

- [ ] Re-resolve final `feature/rc6-eha-brownfield-bootstrap` SHA.
- [ ] Require fresh exact-head CodeSleuth acceptance success on that SHA.
- [ ] Compare final RC6 against both refit source heads to prove intended functionality was preserved without source ancestry.
- [ ] Record archive map: original branch -> source SHA -> archive ref -> disposition.
- [ ] Stop feature intake before SIB/EHA; no further authority-changing work enters this candidate.
