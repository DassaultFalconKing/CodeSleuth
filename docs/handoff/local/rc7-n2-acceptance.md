# Local N2 acceptance evidence

- provenance: `anon-5cae5ffd6d93`
- session-id: `handoff-local-rc7-n2-acceptance`
- kind: coordinator handoff evidence, not product authority
- tested SHA identity: `dc087ab52211b1605f873777a9306922926b0c4b`
- this branch HEAD after the evidence commit is a **new SHA** and is **not** the accepted N2 head

Do not treat `handoff/local/rc7-n2-acceptance` as Exact-Head Acceptance identity. Acceptance belongs only to the SHA named below. This file exists so the next session can review local gates without relying on chat text, a detached worktree, or terminal logs.

## Identity freeze

```text
SOURCE_BRANCH: origin/feature/rc7-agent-discovery
SOURCE_HEAD_TESTED: dc087ab52211b1605f873777a9306922926b0c4b
INTEGRATION_BASE: 64c1986ab26c16957c7f126106f7dc2020edfcae
MERGE_BASE: 64c1986ab26c16957c7f126106f7dc2020edfcae
ahead: 19
behind: 0
main: 330f4c533bb6a29cc7f762323ac3e64a14a27385
SIB: 6621c65b868d3e279ddcbd8dee182a95c6fb29f8
dev/release-0.4.0: 4370c0d63173d27556b11d629746afee07f3cf62
```

Worktree used for gates: `C:\Users\testc\Documents\CodeSleuth-rc7-n2-local` at detached then branched exact `dc087ab…`, tracked tree clean before this evidence file.

## Local platform

```text
LOCAL_PLATFORM: Microsoft Windows NT 10.0.26200.0
PYTHON_VERSION: 3.12.10
PYTHON_EXECUTABLE: C:\Users\testc\Documents\CodeSleuth-rc7-n2-local\.venv\Scripts\python.exe
PYTHON_BASE: C:\opt\python312\python.exe
RUSTC_PORTABLE: rustup run 1.88.0 -> rustc 1.88.0 (6b00bc388 2025-06-23)
CARGO_PORTABLE: cargo 1.88.0 (873a06493 2025-05-10)
BUN: 1.4.0
NODE: v26.3.0 (C:\Program Files\nodejs\node.exe)
```

`PYTHONHOME=C:\llm\ovms\python` is present in the ambient user environment and breaks non-OVMS CPython. Every Python gate below was run after unsetting `PYTHONHOME` and `PYTHONPATH`.

## Focused N2 tests

Command:

```text
.\.venv\Scripts\python.exe -m pytest -q tests/test_rc7_agent_discovery.py tests/test_agents_pointer.py tests/test_smoke_parity.py tests/test_naming_cutover.py
```

Result: `21 passed in 8.83s`, exit=0, HEAD=`dc087ab52211b1605f873777a9306922926b0c4b`.

## Full pytest

Command:

```text
.\.venv\Scripts\python.exe -m pytest -q
```

Result: `443 passed, 10 skipped in 216.06s`, exit=0.

The 10 skipped include the env-gated TUI visual modules when `CODESLEUTH_UI_VISUAL_REGRESSION` is unset. Those modules were executed separately below.

## Ruff

Command: `.\.venv\Scripts\python.exe -m ruff check .`

Result: `All checks passed!`, exit=0.

## Contributor anti-pattern scan

Command: `.\.venv\Scripts\python.exe scripts\contributor_antipatterns.py scan --strict`

Result: exit=0. Heuristic WARN findings only; none are in the N2 diff versus `64c1986…`. Mechanical ERROR findings: none.

## Install / uninstall / Verify

Disposable target: `%TEMP%\codesleuth-rc7-n2-lifecycle`

| Step | Command | Result |
| --- | --- | --- |
| install | `install.py <target>` | exit=0, `installed CodeSleuth 0.4.0-Rc5c` |
| source-helper smoke | `smoke.py <target>` | `PACK SMOKE PASS`, exit=0 |
| installed Verify | `<target>\.opencode\bin\review-pack-smoke.py <target>` | `PACK SMOKE PASS`, exit=0 |
| uninstall | `install.py <target> --uninstall` | exit=0, `.opencode` removed, user `AGENTS.md` preamble restored |

`python smoke.py .` and `python smoke.py pack` against the source checkout are not product Verify. Root `smoke.py` inspects `<root>/.opencode` and expects install-generated `review-pack.json`. That FAIL is operator misuse, not an N2 defect.

Installed `AGENTS.md` contained the N2 discovery map, including `.codesleuth/reports/`, `.codesleuth/reports/INDEX.md`, `.opencode/state/reviews/`, `.opencode/state/context-graphs/`, `.opencode/playbooks/`, `/codesleuth/playbooks`, `/codesleuth/playbook <id>`, `codesleuth-*`, `DassaultFalconKing/CodeSleuth`, literal `this worktree`, and sanitized-publication wording.

## Rust graph read-side

Identity: `rustup run 1.88.0 rustc --version` = `rustc 1.88.0 (6b00bc388 2025-06-23)`.

Commands:

```text
rustup run 1.88.0 cargo fmt --manifest-path portable/ebca-graph-readside/Cargo.toml --all -- --check
rustup run 1.88.0 cargo clippy --manifest-path portable/ebca-graph-readside/Cargo.toml --locked --all-targets -- -D warnings
rustup run 1.88.0 cargo test --manifest-path portable/ebca-graph-readside/Cargo.toml --locked
```

Result: all exit=0. Tests: 5 CLI + 7 graph_reader + 4 watermark passed. Ambient `rustc` on PATH was 1.96 and is not this evidence.

## Graphify enabled (local Windows / Python 3.12)

Install: `PYTHONPATH=pack/.opencode/bin` then `python -m codesleuth_project --install-graphify-runtime .`

Result: `"installed": true`, lock `tools/graphify-provider/requirements-lock.txt`, interpreter = venv 3.12.10, exit=0.

Then:

```text
python -m pytest -q tests/test_graphify_adapter.py tests/test_graphify_corpus.py
python scripts/graphify_corpus_compare.py --fixtures tests/fixtures/graphify-corpus --check
```

Result: `14 passed in 9.55s`, corpus `"passed": true`, `"failures": []`, exit=0.

`bun tests/context_graph_provider_smoke.ts` initially failed while `PYTHONHOME` was set (`unavailable` / ambient-interpreter latch). After unsetting `PYTHONHOME` and putting the venv first on `PATH`: `CONTEXT GRAPH PROVIDER SMOKE PASS`, exit=0.

This is **not** the Ubuntu Graphify job. Hosted Ubuntu Graphify remains the canonical OS evidence.

## TUI / User Witness

Hosted job is Ubuntu. Local Windows run with:

```text
CODESLEUTH_UI_VISUAL_REGRESSION=1
CODESLEUTH_UI_ARTIFACT_DIR=artifacts/tui-regression
TEXTUAL_LOG=artifacts/tui-regression/textual.log
TEXTUAL_ANIMATIONS=none
python -m pytest -q tests/test_tui_visual_regression.py tests/test_tui_config_contract_controls.py tests/test_tui_user_witness_bundle.py
```

Result: `11 passed in 23.23s`, exit=0. Local SVG/log artifacts were generated under untracked `artifacts/` and are **not** committed (Windows visual artifacts are not the Ubuntu gate). Hosted TUI job SUCCESS remains canonical for that OS.

## Durable state / context graph (bun)

`bun install --frozen-lockfile` exit=0. Graph reader bound:

```text
CODESLEUTH_GRAPH_READER_BIN=...\portable\ebca-graph-readside\target\debug\ebca-graph-readside.exe
```

`bun run test` did **not** complete as a local PASS. It stopped at `tests/mermaid_qa_smoke.ts`:

```text
cannot identify CODESLEUTH_MERMAID_BROWSER=...\chrome.exe:
Command '['...\chrome.exe', '--version']' timed out after 10 seconds
status: unavailable
```

Smokes that actually printed PASS before that stop:

```text
REPO INVENTORY SMOKE PASS
PROFILE SMOKE PASS
REVIEW STATE SMOKE PASS
REVIEW STATE AMENDMENTS PASS
provenance state smoke: PASS
CONTEXT GRAPH SMOKE PASS
context capsule smoke: PASS
context graph reader smoke: PASS
EHA STATE SMOKE PASS
CONTRACT BOOTSTRAP STATE SMOKE PASS
CHANGE SURFACE STATE SMOKE PASS
DEVELOPMENT CONTINUATION STATE SMOKE PASS
RC6 LIVE DOGFOOD REPAIR REGRESSIONS PASS
RC6 AUTHORITY FIXTURES SMOKE PASS
EXTERNAL EVIDENCE STATE SMOKE PASS
PROTECTED CAPABILITY GRAPH SMOKE PASS
```

After the mermaid stop, separately:

```text
export_bundle_smoke.ts: EXPORT BUNDLE SMOKE PASS
context_graph_topology_smoke.ts: CONTEXT GRAPH TOPOLOGY SMOKE PASS
export_tools_smoke.ts: NOT_RUN / FAIL locally (Mermaid SVG path requires explicit Node/browser identity; Chrome --version times out)
mermaid_qa_smoke.ts: NOT_RUN locally (Chrome --version timeout)
mermaid_export_smoke.ts: NOT_RUN locally (same mermaid identity surface)
```

Hosted Durable-state / context graph job SUCCESS on this SHA remains the canonical mermaid/SVG evidence.

## Hosted exact-head evidence for the tested SHA

```text
HOSTED_RUN: 33990685186
URL: https://github.com/DassaultFalconKing/CodeSleuth/actions/runs/33990685186
HOSTED_RESULT: success
attempt: 1
event: push
exact_sha: dc087ab52211b1605f873777a9306922926b0c4b
jobs: 8/8 SUCCESS
```

Jobs: Durable state / context graph; Graphify enabled runtime / Python 3.12 / Ubuntu; TUI visual regression / Ubuntu; Portable Rust graph read-side / 1.88; Python 3.10 / ubuntu-latest; Python 3.10 / windows-latest; Python 3.12 / ubuntu-latest; Python 3.12 / windows-latest.

Independent `gh run view 33990685186` confirmed `headSha` equals `SOURCE_HEAD_TESTED`.

## Surfaces marked NOT_RUN locally

| Surface | Reason | Canonical substitute |
| --- | --- | --- |
| Python 3.10 Windows | no 3.10 interpreter on this machine | hosted job SUCCESS |
| Python 3.10 Ubuntu | this host is Windows | hosted job SUCCESS |
| Python 3.12 Ubuntu | this host is Windows | hosted job SUCCESS |
| TUI visual / Ubuntu | this host is Windows | hosted job SUCCESS |
| Mermaid QA / SVG export | Chrome `--version` timeout 10s | hosted Durable-state job SUCCESS |
| bun `test` umbrella | stopped at mermaid_qa | hosted Durable-state job SUCCESS |

Do not read any NOT_RUN row as PASS.

## N2 scope versus `64c1986…`

`git diff --stat 64c1986ab26c16957c7f126106f7dc2020edfcae...dc087ab52211b1605f873777a9306922926b0c4b`:

```text
 docs/RC7-AGENT-DISCOVERY-DISTRIBUTION-DESIGN.md
 docs/superpowers/plans/2026-09-05-codesleuth-agent-discovery.md
 pack/.opencode/bin/codesleuth_project/paths.py
 pack/.opencode/bin/playbook_catalog.py
 pack/.opencode/bin/review-pack-smoke.py
 pack/.opencode/codesleuth-naming.json
 pack/.opencode/commands/codesleuth/playbook.md
 pack/.opencode/commands/codesleuth/playbooks.md
 pack/.opencode/commands/playbook.md
 pack/.opencode/commands/playbooks.md
 smoke.py
 tests/test_rc7_agent_discovery.py
 12 files changed, 336 insertions(+), 8 deletions(-)
```

No second evidence, ledger, EHA, command-router, or persistence authority. No second playbook ID table. Always-on `AGENTS.md` lifecycle reused. `policy.enforceAgentsMdRules` remains default-off.

Historical N2 FIRST_RED (not re-executed in the local acceptance session): `2792fc786c3de9d4dda5895306b3309073caf3f2` (`test(rc7): define agent discovery and playbook browse contract`). Prior record: 5 failed, 437 passed, 10 skipped.

## Protected refs

This local session did not move `main`, `SIB`, `dev/release-0.4.0`, `integration/rc7`, tags, or GitHub Releases.

## Verdict

```text
LOCAL_ACCEPTANCE: ACCEPTED_LOCAL
HOSTED_ACCEPTANCE: SUCCESS on exact dc087ab52211b1605f873777a9306922926b0c4b / run 33990685186
OVERALL: INTEGRATION_READY
N3: NOT STARTED
integration/rc7: NOT MOVED
```

Coordinator next: integrate N2 from exact `dc087ab52211b1605f873777a9306922926b0c4b` onto current `integration/rc7` = `64c1986ab26c16957c7f126106f7dc2020edfcae` with history preserved, then require fresh hosted acceptance of the **resulting merge SHA**. Do not transfer run `33990685186` by ancestry.

N3 may start only from that new accepted integration SHA. First N3 production action must be test-only RED on `handoff/local/rc7-n3-distribution` or `feature/rc7-portable-skill-distribution` as the coordinator directs.
