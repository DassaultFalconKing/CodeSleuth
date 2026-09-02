---
reportType: live-dogfood-repeat
targetSha: b56ae39d8b98e1a67f933e03544c83869c3377f4
provenance: c6r-19be9bfa7122
verdict: FAIL
reviewId: 20260902131530-b56ae39d8b98-8TLUvyLd-a1ee2652
---

# RC6 repeat live-dogfood acceptance — b56ae39

- date: 2026-09-02T13:19:18Z
- candidate: `b56ae39d8b98e1a67f933e03544c83869c3377f4` (detached exact HEAD; clean; 405 tracked files)
- candidate parent: `0e6a574`
- hosted acceptance: run `33628677158`, exact `headSha=b56ae39d8b98e1a67f933e03544c83869c3377f4`, seven jobs concluded success
- scope: independent repeat of the normal installed `/repo-continue` workflow against two exact foreign repositories, including R1-R13, durable continuation artifacts, external evidence, deterministic scope guards, current native-gate status, and read-only restoration
- agent: OpenCode `build` controller through the RC6 candidate runtime; fresh child tasks were requested per step and their actual isolation behavior was audited from the trace
- provenance: `c6r-19be9bfa7122` (`headMatch:true`, `trustworthy:true`; attribution only)
- reviewId: `20260902131530-b56ae39d8b98-8TLUvyLd-a1ee2652`
- analysis: **FAIL — RC6_REPAIR_REQUIRED**
- publication intent: on; canonical route `reports` only; publisher result is reported separately by the operator after immutable submission

## Verdict

**RC6_REPAIR_REQUIRED.** The exact candidate has a green seven-job hosted acceptance matrix and its focused RC6 smoke tests pass, but repeat live dogfood reproduced release-relevant generic defects that those gates do not cover:

1. the candidate's external runtime mirror does not isolate a target repository's tracked `.opencode` project configuration from a newer OpenCode host; OpenCode 1.18.25 rewrote two tracked Aleph package-metadata files before analysis, and the controller continued after a fresh child reported the target dirty;
2. after fresh-child failures, the controller executed the same step in the parent before recording `STEP_ISOLATION_UNPROVEN`, on both independent targets;
3. the Aleph continuation packet became formally valid only after the controller dropped already-established prerequisites, accepted predecessor, required reading, operator decision, uncertainties, and most native gates instead of preserving the conflict as a blocker;
4. path-pattern validation accepted a conceptual non-path string and a non-expanding directory literal, so the deterministic guard could not faithfully enforce the repository's intended scope.

The two foreign targets were restored to their exact starting SHAs and clean tracked/untracked state. No candidate source repair was attempted. No pull request was merged, and no application branch, `main`, `SIB`, tag, release, EHA campaign, or RC7 identity was moved or created.

## Exact identities and read-only restoration

| Repository | Exact target | Start | End | Metadata boundary |
|---|---|---|---|---|
| PII_PARSER | `9f226013f37c3ca62f8f8a4f2845370e2350f639` | detached, clean, 2079 tracked, 0 untracked | same SHA, empty porcelain status | `.git/config` SHA-256 remained `34BF106F...38106A`; `.git/info/exclude` remained `6671FE83...B0EC1` |
| Aleph_Rugent | `bf1320a523fb7cf01953d03426403eb049fe5b1a` | detached, clean, 424 tracked, 0 untracked | same SHA, empty porcelain status | `.git/config` SHA-256 remained `EAA653DA...84117`; `.git/info/exclude` remained `6671FE83...B0EC1` |

Durable `.opencode/state` for each run was bound through a temporary junction to an external evidence directory. Each junction was verified, removed without traversing its target, and the disposable repository was rechecked afterward. The one run-created Aleph mutation was limited to `.opencode/package.json` and `.opencode/package-lock.json`; their exact diff showed OpenCode dependency metadata changing from 1.18.23 to 1.18.25. Those two paths alone were restored from the immutable target HEAD, then the full repository identity and metadata boundary were reverified.

## Target A — PII_PARSER

- target: `9f226013f37c3ca62f8f8a4f2845370e2350f639`
- `/repo-continue` session: `ses_f9dde3952ffet0IwfGlfx4GnKo`
- NUL-safe Unicode/space witness: `набор аудита/README.md`
- canonical planning authority: `docs/current_todo_worklog/TODO.md`
- active scope: `W-1 Immediate control-plane security containment`
- accepted shipped baselines: preserved in confirmed authority edge `DAE-4b774378...`
- Development Authority Map: `DAM-20260902124516-9f226013f37c-cc2147f4`
- Change Surface Map: `CSM-20260902124710-9f226013f37c-6d0bdaf1` (`DERIVED_NON_AUTHORITATIVE`, 200-item bound reached and explicitly truncated)
- Native Gate Map: `NGM-20260902124724-9f226013f37c-05639a6e` (10 gates; all recorded `UNEXECUTED`; `CLOUD_TESTABILITY_REMAINING`)
- Development Continuation Packet: `DCP-20260902124834-9f226013f37c-dc93a4d4`
- external evidence: fresh `EE-41f682d7-8e19-4139-a2ce-36c6c1de7947` and stale control `EE-bf66c20f-784f-497b-a8fb-985013630311`; load result `count=2`, `fresh=1`, `stale=1`, `authority=evidence-only`

The exact scope guard classified `api_model_health.py`, the frontend path, and the active TODO as `SCOPE_AUTHORITY_UNPROVEN`; an archive path was `FORBIDDEN_BY_ACTIVE_SCOPE`; overall result `FORBIDDEN`. This was an honest consequence of `allowedPaths=[]` and `pathScopeAuthority=NOT_DECLARED`, not a fabricated allowlist.

Current hosted status for this foreign SHA was inspected independently: run `31793883541` has `Backend lint` passed and `Frontend strict lint` failed. That target-specific red gate is not promoted into a generic CodeSleuth finding and is not called PASS.

## Target B — Aleph_Rugent

- target: `bf1320a523fb7cf01953d03426403eb049fe5b1a`
- current-host attempt: OpenCode 1.18.25; stopped before the authority map after the tracked target mutation and fail-open continuation were reproduced
- compatibility evidence attempt: already-cached OpenCode 1.18.23, matching the target's tracked SDK/plugin pin; no package installation or update was performed
- NUL-safe Unicode/space witness: `analytical_skills/аналітична записка версія на віддачу.json`
- canonical planning chain: `ORIENTATION.md` -> `docs/session-packets/S09.md`
- active scope: `S09 working set (Waypoints W4b)`
- Development Authority Map: `DAM-20260902130407-bf1320a523fb-e68bb0c4` (19 confirmed edges)
- Change Surface Map: `CSM-20260902130731-bf1320a523fb-2e9b4114` (`DERIVED_NON_AUTHORITATIVE`; broad baseline/import projection)
- Native Gate Map: `NGM-20260902130752-bf1320a523fb-145a313f` (12 gates, all `UNEXECUTED`; `CLOUD_TESTABILITY_REMAINING`)
- Development Continuation Packet: `DCP-20260902131046-bf1320a523fb-1d1f028d`
- external evidence: `EE-bc24c69d-7f74-4f75-9bfe-d781d5a24d1b`; load result `count=1`, `fresh=1`, `stale=0`, `authority=evidence-only`

The authority map correctly found the S09 chain, but it also accepted a nonsensical `SUPERSEDED_BY` self-loop and encoded the S08 predecessor edge in the opposite direction from the candidate's fixture convention. `development_continuation_state.ts:141-150` validates a selected confirmed relation by matching only its object value; it does not validate direction or relevance beyond that stored edge.

The first packet submissions rejected the edge/packet mismatch. The controller then produced a valid packet by omitting known prerequisites, accepted predecessors, required reading, operator decision, uncertainties, and 9 of 12 mapped gates. This is enabled by the optional arrays at `pack/.opencode/tools/development_continuation_state.ts:199-203`; formal schema validity therefore did not preserve the already-discovered continuation contract.

The accepted packet's path data was also semantically incomplete:

| Probe | Result | Reason |
|---|---|---|
| `crates/rag-core/src/lib.rs` | `IN_SCOPE` | exact allowed file |
| `docs/baseline/hybrid-retrieval.json` | `UNDECLARED` | allowed literal `docs/baseline/` does not expand to descendants |
| `docs/session-packets/G1.md` | `ADJACENT_TRACK` | explicit restriction |
| `crates/rag-contracts/tests/golden.rs` | `UNDECLARED` | intended test path omitted |
| `W5 production toolcaller` | `FORBIDDEN` | conceptual prose was accepted as if it were a repository path |

The guard is deterministic for the stored patterns, but `validatePattern` at `pack/.opencode/tools/development_continuation_state.ts:102-108` checks only basic relative-path safety. It neither requires a path-like entity nor gives a trailing directory literal descendant semantics. The overall result was `FORBIDDEN`, but it cannot be treated as faithful enforcement of the repository's intended W5 boundary.

Current hosted run `33272230534` is on the exact Aleph SHA and has conclusion `failure`, but the `rust`, `postgres-migrations`, and `review-pack` jobs expose `runner_id=0`, empty runner name, and no steps; `authorized-investigation` is skipped. These are recorded as unexecuted host jobs, not semantic test failures and not PASS.

## R1-R13 matrix

| Criterion | Result | Exact repeat evidence |
|---|---|---|
| R1 Unicode/space/NUL-safe inventory | PASS | Both targets yielded a real Unicode/space path through NUL-delimited enumeration without corruption. |
| R2 authority DAG and active branch | FAIL | Canonical authorities were found, but Aleph accepted a self-loop/wrong-direction predecessor and the final packet discarded established branch prerequisites. |
| R3 complete DCP | FAIL | PII packet remained conservative; Aleph's valid packet omitted established reading, predecessor, decisions, uncertainties, and most gates to bypass validation conflict. |
| R4 current native CI truth | PASS | Exact target runs were inspected; PII frontend red and Aleph runnerless jobs were reported without converting either to PASS. |
| R5 deterministic scope guard | FAIL | Calls were deterministic and reasons explicit, but accepted pattern semantics admitted conceptual prose and failed to expand a directory boundary. |
| R6 structural closure | PASS | DAM/CSM/NGM/DCP were persisted and loaded on both targets; broad/truncated CSM projections remained explicitly non-authoritative and were not used as acceptance proof. |
| R7 fresh child isolation | FAIL | On both targets, child command failures were followed by same-session parent work before `STEP_ISOLATION_UNPROVEN`; final prose could retroactively claim isolation handling that the trace disproves. |
| R8 host/runtime portability | FAIL | OpenCode 1.18.25 dirtied the Aleph target; continuation required a pre-existing 1.18.23 host binary to gather further evidence. |
| R9 runtime/target config separation | FAIL | External `OPENCODE_CONFIG_DIR` did not suppress target-local tracked `.opencode`; the host rewrote target package metadata and the controller continued after dirty detection. |
| R10 read-only end state | FAIL | Final restoration succeeded and both targets are exact-clean, but the normal current-host run violated the read-only boundary during execution. |
| R11 gate honesty | PASS | Unexecuted, cloud-remaining, stale, runnerless, and target-red states stayed distinct; no unexecuted gate was called PASS. |
| R12 candidate regression coverage | FAIL | Hosted 7/7 and focused local tests passed, yet they did not cover the reproduced target-config mutation or semantic packet degradation. |
| R13 target/generic separation | PASS | Foreign-repository CI and authority-content issues are separated from reproducible CodeSleuth controller/tool defects. |

## Generic release-blocking findings

### RC6-LD-01 — target-local OpenCode config remains writable and controller fails open

- severity: release-blocking
- reproduced on: Aleph_Rugent with OpenCode 1.18.25
- observed effect: tracked `.opencode/package.json` and `.opencode/package-lock.json` changed from 1.18.23 to 1.18.25 before repository analysis; the fresh identity child reported the worktree dirty, but the parent said identity was confirmed and proceeded toward authority resolution
- candidate surface: `scripts/eha_opencode_runtime.py`, both `pack/.opencode/bin/opencode-review*` wrappers, and `tests/test_eha_opencode_runtime.py`
- coverage gap: the three passing runtime tests prove only that the writable custom runtime mirror is external and single-use. The test itself states that the bridge keeps `OPENCODE_CONFIG` on the exact tracked target config; it does not exercise a real newer OpenCode bootstrap against a target with tracked package metadata.
- required repair property: a normal installed read-only analysis must either prevent target-project bootstrap writes or fail closed before analysis and before any claim of clean identity. A timeout or compatibility pin alone is insufficient.

### RC6-LD-02 — failed fresh child falls back before isolation truth is recorded

- severity: release-blocking
- reproduced on: PII_PARSER and Aleph_Rugent, multiple steps
- contract: `pack/.opencode/commands/repo-continue.md:14` requires `STEP_ISOLATION_UNPROVEN` before executing that step in the current session
- observed effect: a child failed on a compound shell command; the parent immediately invoked repository tools/fallback analysis and only later described isolation as unproven. The PII final narrative retroactively claimed the marker preceded steps 2-6, contrary to the trace.
- required repair property: the orchestration boundary must emit a durable marker before any parent fallback, and final summaries must derive from that durable event rather than narrative reconstruction.

### RC6-LD-03 — packet schema/controller can erase discovered continuation obligations

- severity: release-blocking
- reproduced on: Aleph_Rugent
- candidate surface: optional packet arrays at `pack/.opencode/tools/development_continuation_state.ts:199-203`, plus relation matching at lines 141-150 and path validation at lines 102-108
- observed effect: after validation errors, the controller omitted previously established prerequisites, predecessor, required reading, operator decisions, uncertainties, and most gates until save succeeded, then treated the stripped packet as a basis for enrichment rather than preserving the conflict as a blocker
- required repair property: a packet must be monotonic with respect to already-bound authoritative obligations, or the conflict must remain explicit and block a ready-to-continue claim. Path scope must distinguish repository path patterns from conceptual scope labels and define descendant semantics.

## Candidate gates actually run

- hosted acceptance run `33628677158`: PASS, seven of seven jobs, literal candidate SHA
- `bun tests/development_continuation_smoke.ts`: PASS
- `bun tests/rc6_authority_fixtures_smoke.ts`: PASS
- `bun tests/external_evidence_state_smoke.ts`: PASS
- `python -m pytest -q tests/test_eha_opencode_runtime.py`: PASS, 3 tests
- `python scripts/contributor_antipatterns.py scan --strict`: exit 0 with warnings only
- an earlier `python -m unittest tests.test_eha_opencode_runtime` invocation selected zero tests and is **NOT RUN**, not PASS; the later pytest invocation is the valid evidence

Candidate HEAD and porcelain status were rechecked after these gates and remained exact-clean.

## Comparison with prior witnesses

The local prior RC6 witness on earlier candidate `8380f...` and the older `Verdict.md` host-boundary witness were used only as derived navigation. They did not transfer acceptance to `b56ae39`. Compared with those witnesses, RC6 now demonstrates real NUL-safe Unicode inventory, durable DAM/CSM/NGM/DCP state, deterministic scope-guard results, and fresh/stale external-evidence accounting. The repeat nevertheless exposes new current-candidate blockers at the host bootstrap boundary, isolation-event ordering, and packet semantic preservation. Historical green or red prose is therefore neither the source nor a substitute for this exact repeat trace.

## Limitations and next action

- The disposable runs intentionally did not execute application test suites inside the foreign targets; current hosted evidence was inspected instead and its execution status was preserved literally.
- No live service credentials or production resources were used. External observations were synthetic evidence-only records with explicit freshness and non-authority semantics.
- CSM projections are bounded derived read models, not proof of coverage or repository authority.
- The cached OpenCode 1.18.23 attempt is compatibility evidence only; it does not waive the 1.18.25 failure.
- This is not EHA/SIB promotion and does not authorize merge or release movement.

Repair should create a new candidate SHA and a fresh acceptance campaign. The minimum regression needs a real disposable target containing tracked `.opencode` package metadata under a newer host, production-path fresh-child failure ordering, and a packet monotonicity/path-pattern test that cannot become green by dropping discovered obligations.
