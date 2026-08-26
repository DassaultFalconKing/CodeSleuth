# CodeSleuth whole-repository deep review — HEAD 1114389c

- **UTC date:** 2026-08-26T13:58Z
- **Target:** HEAD `1114389c4f6ed416d021f85fdb3d19774fcec8d6` ("fix: semantic-refit Textual bootstrap soft-pin on current head"); version **0.4.0** (unreleased per CHANGELOG)
- **Dirty state:** tracked worktree modified only in `AGENTS.md` (CodeSleuth reports-pointer block added by self-install — benign); `.opencode/` untracked (self-install materialization). One drift note: installed `.opencode/bin/review_pack_tui_bootstrap.py` is a stale older generation (exact-pin bootstrap) vs the tracked `pack/` soft-pin bootstrap (~70-line diff); tracked source is correct and covered by `tests/test_version_contract.py`.
- **Scope:** whole repository (137 tracked files). Deep component review of installer/lifecycle, TUI console runtime, MCP evidence adapter, OpenCode TS durable-state tools/plugin, verification gates, CI; cross-cutting passes over resource bounds, fail-open/closed behavior, thread-safety, evidence integrity, docs/runtime truth.
- **Durable review:** `.opencode/state/reviews/20260826132343-1114389c4f6e-n8rAGFsg/` (10 recorded findings with blob-bound excerpts)
- **Context projection:** `.opencode/state/context-graphs/sha256:42f9fc16…json` (39 nodes / 17 edges)

## Summary

CodeSleuth at this HEAD is architecturally coherent with its own product contract: the host (OpenCode `build`) remains the only controller; CodeSleuth contributes skills, profiles, bounded tools, a control-panel TUI, a read-only MCP evidence adapter, and reversible install/lifecycle machinery. The installer's hash-managed three-way config merge, conflict-safe restore, submodule HEAD guards, and the local-exclude (never rewrite user `.gitignore`) policy are well built and test-backed. CI enforces exact-HEAD checkout before running gates, matching `docs/EXACT-HEAD-ACCEPTANCE.md`.

Review surfaced **4 medium**, **5 low**, and **1 info** findings. The mediums are concentrated in exactly the areas the product claims as its differentiators: resource bounds in the MCP evidence adapter, thread-safety in the TUI action workers, evidence-ledger integrity in the durable review state, and profile-packaging parity in the builtin `generic.json` copies. None blocks the release train alone, but the MCP slurp-before-cap, the findings-ledger reuse gap, and the generic-profile drift both contradict written contracts/packaging assumptions and deserve pre-release fixes.

## Findings

| ID | Severity | Location | Title |
| --- | --- | --- | --- |
| F-c964e6a1 | medium | `codesleuth_mcp/server.py:296-299` | `read_evidence` buffers the entire file before enforcing `MAX_FILE_BYTES` |
| F-eb9b4b4c | medium | `pack/.opencode/bin/review_pack_tui.py:488-497` | TUI thread workers mutate widgets off the main thread; Update workers not exclusive |
| F-7dbb3463 | medium | `pack/.opencode/tools/review_state.ts:162-191` | `start()` leaves stale `findings.ndjson` attached to a reset review on id collision/reuse |
| F-16f3af6b | low | `pack/.opencode/plugins/review-compaction.ts:22-32` | Compaction hook throws on corrupt/torn state instead of degrading |
| F-b4db42a4 | low | `pack/.opencode/bin/review-pack-smoke.py:9-27` | Installed Verify gate omits `/repo-map` command and context-graph tool required by source gate |
| F-21a62f55 | low | `codesleuth_mcp/server.py:257-262` | `overview` silently truncates shape lists without a truncation flag |
| F-ec7ac00f | low | `README.md:30` | README claims version 0.3.0 while VERSION/CHANGELOG say 0.4.0 (unreleased) |
| F-a4227009 | low | `README.md:826-829` | Profile `extends` inheritance documented but no resolver exists in any runtime path |
| F-525364f3 | info | `pack/.opencode/tools/repo_inventory.ts:31-33` | Deterministic inventory hard-fails on zero-commit repositories |
| F-fddf6bb4 | medium | `profiles/generic.json:1-18` | Builtin `generic.json` diverged between `profiles/` and `pack/.opencode/profiles/builtin/` |

Key details:

1. **F-c964e6a1** — `payload = absolute.read_bytes()` precedes the `MAX_FILE_BYTES` check, so peak memory is unbounded even though output is bounded. Fix direction: stat before read / stream with a byte budget; add an adversarial oversize-file test (`tests/test_mcp_server.py` currently has none).
2. **F-eb9b4b4c** — `validate_target()` writes `#target` Input.value (`review_pack_tui.py:496`) while running inside `@work(thread=True)` workers (`review_pack_tui.py:609`, `codesleuth_tui.py:955`); `perform_apply` error path evaluates `query_one("#apply")` in-worker (`review_pack_tui.py:438`); both action workers are `exclusive=False`, allowing interleaved fetch/dirty-check/ff-only merge sequences. Fix direction: marshal all DOM access through `call_from_thread`; make actions exclusive; add cancellation.
3. **F-7dbb3463** — `start()` resets `state.json` but never truncates the per-review `findings.ndjson` (`appendFile` at `review_state.ts:317`); a colliding `reviewId` (second-resolution timestamp + HEAD + session) resurrects old findings as authoritative continuation state after compaction. Fix direction: clear ledger on start or make ids collision-proof.
4. **F-16f3af6b** — unguarded `JSON.parse` on `state.json` and per-line NDJSON in the compaction hook converts a torn append into a throwing host hook on every compaction. Fix direction: bounded try/catch degradation.
5. **F-b4db42a4** — `review-pack-smoke.py` (the gate behind TUI **Verify**) does not require `commands/repo-map.md` or `tools/repo_context_graph.ts`, which `smoke.py:14,:17` requires and README documents as installed surface; the two checklists have drifted in both directions. Fix direction: single shared manifest.
6. **F-21a62f55 / F-ec7ac00f / F-a4227009 / F-525364f3** — see ledger entries; each has a concrete contract citation and smallest-correction direction in the recommendation field.

Positive verification highlights (not findings): MCP git hardening is real and tested (env scrub, null stdin, fsmonitor/textconv off, stage-0 regular-only reads, streamed termination with terminate→kill escalation, exact-truncation semantics on search/diff); lifecycle restore uses genuine three-way baseline comparison; permission defaults in `pack/.opencode/opencode.json` deny destructive git operations by default; commands pin `agent: build` and subagents pin `mode: subagent`, enforced by both smoke gates.

## Cross-agent evidence profile (reusable by other agents)

Detected stack (from `repo_profile` / `detect_profiles` in `review_pack_tui_core.py:106`, HEAD `1114389c`, 137 tracked files): `generic` + `python` (41 `.py`; `pyproject.toml`) + `node` (`package.json` + `bun.lock`) + `typescript` (7 `.ts`).

Evidence (tracked, current blobs at this HEAD):
- `pyproject.toml` — pytest `asyncio_mode=auto`, `testpaths=["tests"]`; ruff `target-version=py310`, `select=["E4","E9","F"]`.
- `package.json` — bun; `test` = `bun tests/review_state_smoke.ts && bun tests/context_graph_smoke.ts`; devDep `@opencode-ai/plugin@^1.14.48`.
- `bun.lock` — bun is the package manager (no npm/pnpm/yarn lock).
- `requirements-dev.txt` → `requirements-mcp.txt` + `pack/.opencode/bin/requirements-tui.txt`; pins `pytest>=8.4,<9`, `pytest-asyncio>=0.23,<2`, `ruff>=0.12,<1`.
- `.github/workflows/acceptance.yml` — asserts exact-HEAD checkout SHA before gates; runs `ruff` + `pytest` (Python 3.10/3.12 × ubuntu/windows) and bun `bun install --frozen-lockfile` + `bun run test`.
- `codesleuth_mcp/server.py`, `pack/.opencode/tools/*.ts` — runtime surfaces.

Recommended verification (derived from manifests/CI, not assumed):
- Python: `python -m pip install -r requirements-dev.txt` → `python -m ruff check .` → `python -m pytest -q` (full gate; includes MCP/TUI/lifecycle suites).
- Durable state / context graph: `bun install --frozen-lockfile` → `bun tests/review_state_smoke.ts` + `bun tests/context_graph_smoke.ts`.
- TypeScript: **no `tsc --noEmit` typecheck gate exists** in CI or `package.json`; verification is bun-runtime-smoke only (documented gap, not a command to invent).

Review focus for this repository (consolidated from this review):
- durable evidence ledger integrity (`review_state.ts` append/reset semantics vs compaction);
- TUI thread-safety (DOM access only on main thread via `call_from_thread`; exclusive action workers);
- MCP evidence adapter resource bounds (`read_evidence` buffers before `MAX_FILE_BYTES`; `overview` silent truncation);
- installer/lifecycle safety (three-way config merge, conflict-safe restore, local `.git/info/exclude` never rewrites user `.gitignore`, submodule HEAD guards);
- exact-HEAD acceptance (CI asserts checkout SHA == acceptance SHA before gates);
- docs/runtime truth (README/VERSION/CHANGELOG parity; profile `extends` resolver gap F-a4227009);
- fail-open vs fail-closed in compaction hook and smoke gates;
- cross-language contract drift (python ↔ TS tool schemas; smoke-gate parity).

Conflicts / caveats (evidence-backed):
- **C1 / F-fddf6bb4 (medium):** `profiles/generic.json` and `pack/.opencode/profiles/builtin/generic.json` diverged in shape (top-level `compaction`+`watcher` vs `config.compaction`+`reviewFocus`); neither is consumed by the loader today, but the parity drift is a latent hazard.
- **C2:** profile `extends` is inert (no resolver) — F-a4227009.
- **C3:** no TypeScript typecheck gate in CI/package.json.
- **C4:** a `codesleuth`-named profile is outside the valid built-in set (`docs/LLM-OPERATOR.md:168`), so it would not auto-detect; this section is an advisory cross-agent profile, not an installed built-in.

This profile is advisory; no profile files were written (user directive: advisory-only for the profile pass; only the report and finding ledger were updated).

## Paths inspected

Read in full or in targeted verified ranges: `README.md`, `VERSION`, `CHANGELOG.md`, `package.json`, `pyproject.toml`, `.github/workflows/acceptance.yml`, `install.py`, `smoke.py`, `pack/.opencode/opencode.json`, `pack/.opencode/bin/{review_pack_tui,codesleuth_tui,review_pack_tui_core (scout),review_pack_tui_bootstrap (scout+drift diff),codesleuth_tui_runtime (scout),codesleuth_version (scout),codesleuth_naming (scout),review-pack-update,review-pack-smoke}.py`, `pack/.opencode/bin/codesleuth_project/{__init__,paths,tracked_repos}.py`, `codesleuth_mcp/server.py`, `pack/.opencode/tools/{review_state,repo_inventory,repo_profile (scout)}.ts`, `pack/.opencode/plugins/review-compaction.ts`, `tests/test_version_contract.py`; scout-inspected: `tests/test_mcp_server.py`, `tests/test_tui*.py`, `tests/review_state_smoke.ts`, `profiles/*.json`. Inventory manifest: `.opencode/state/inventory/ses_fc1c581a5ffe1RORBGn8rAGFsg.json`.

## Checks actually run

- `python -m pytest -q` → **163 passed** in 80.50s
- `python -m ruff check .` → **All checks passed**
- `bun install --frozen-lockfile` → ok (no changes)
- `bun tests/review_state_smoke.ts` → **REVIEW STATE SMOKE PASS**
- `bun tests/context_graph_smoke.ts` → **CONTEXT GRAPH SMOKE PASS**

Not run: real-terminal TUI sessions; Windows CI matrix; live MCP wire against an external host.

## Recommendations

1. Pre-0.4.0: fix F-c964e6a1, F-7dbb3463, F-16f3af6b (all small, contract-restoring changes) and add the missing adversarial tests (MAX_FILE_BYTES, oversize binary reads, torn NDJSON).
2. Marshal TUI worker→DOM access through `call_from_thread` exclusively and make Verify/Update/Check workers exclusive (F-eb9b4b4c).
3. Unify the two smoke checklists into one generated manifest and add a drift regression test (F-b4db42a4).
4. Sweep docs truth: README version line (+ ru/uk translations), annotate `extends` as inert metadata (or implement it).

## Limitations / not reviewed

- `pack/.opencode/tools/repo_context_graph.ts` (1271 lines) and `tests/context_graph_smoke.ts` were covered only via the Bun smoke run and scout summary; no independent line-level review of the graph tool this session.
- NovaClaw-side registration/name-prefixing is outside this repository slice.
- Host-hook failure policy for `experimental.session.compacting` exceptions is unknown (affects severity of F-16f3af6b).
- Whether the Windows CI runner executes or skips the symlink-swap MCP test (`tests/test_mcp_server.py:175-188`) was not determined.
- Scout-derived statements used in this report were re-verified only where cited as finding evidence; remaining scout leads (e.g., venv cold-start race, `os.execv` quoting on Windows, locale-dependent inventory tie-break) remain open leads in the review ledger conversation, not accepted findings.
