---
reportType: live-dogfood-repeat
targetSha: b56ae39d8b98e1a67f933e03544c83869c3377f4
provenance: c56-46b6b92b4e7b
verdict: FAIL
reviewId: 20260902180700-b56ae39d8b98-1Gc6Lw9k-d5546d1e
---

# RC6 independent repeat live-dogfood acceptance — b56ae39

- date: 2026-09-02T18:08:50Z
- candidate: `b56ae39d8b98e1a67f933e03544c83869c3377f4` (detached exact HEAD; 405 tracked files)
- hosted acceptance: run `33628677158`, exact `headSha=b56ae39d8b98e1a67f933e03544c83869c3377f4`, seven required jobs concluded `success`
- foreign subjects: PII_PARSER `9f226013f37c3ca62f8f8a4f2845370e2350f639`; Aleph_Rugent `bf1320a523fb7cf01953d03426403eb049fe5b1a`
- normal product surface: installed RC6 `/repo-continue`, candidate Commands/Playbook/Skills and deterministic state tools, with OpenCode remaining the controller
- review provenance: `c56-46b6b92b4e7b` (`headMatch:true`, `trustworthy:true`; attribution metadata only)
- durable review: `20260902180700-b56ae39d8b98-1Gc6Lw9k-d5546d1e`
- analysis: **FAIL — RC6_REPAIR_REQUIRED**
- publication route: candidate-defined `reports` route, branch `reports`; never the candidate/application branch

The historical failed subjects `8380f4652e36693d2ce605a0b6bfbb0ed1642d4f` and `3c94ed7bfbe9b968845178dc2d89abf72cf8f86d` were used only as failure witnesses. No verdict was transferred from either SHA.

## Overall verdict

**RC6_REPAIR_REQUIRED.** The exact candidate's hosted 7/7 matrix is real, but ordinary live dogfood reproduced release-blocking generic failure classes:

1. PII authority does not declare a positive mutation allowlist, yet the controller invented nine allowed paths, saved `pathScopeAuthority=DECLARED`, and caused an ordinary W-1 path to return `IN_SCOPE` instead of `SCOPE_AUTHORITY_UNPROVEN`.
2. On both targets, the manifest's `fresh_subagent` steps were executed in the parent before `STEP_ISOLATION_UNPROVEN` was recorded in final prose.
3. Aleph authority resolution first created a contradictory confirmed map. The deterministic loader correctly failed closed, but the controller discarded that state, started a second “corrected” map, and reported PASS rather than preserving the contradiction for adjudication.
4. A normal OpenCode 1.18.25 attempt rewrote Aleph's tracked `.opencode/package.json` and lockfile from pin 1.18.23 to 1.18.25. The controller observed the dirty target and continued instead of immediately returning `READ_ONLY_BOUNDARY_BLOCKED`.
5. Aleph packet path validation accepted conceptual object/member strings as repository paths and treats trailing directory literals as exact-only. Intended `docs/baseline/**` and `crates/*/tests/**` descendants therefore return `UNDECLARED`, while the synthetic string `crates/rag-contracts/src/lib.rs:GraphProjection/x` returns `ADJACENT_TRACK`.

These are acceptance failures of exact `b56ae39...`; no repair was attempted.

## Identity, host and restoration

| Repository / witness | Exact start | Exact end | Start/end porcelain | Boundary evidence |
|---|---|---|---|---|
| PII_PARSER acceptance subject | `9f226013f37c3ca62f8f8a4f2845370e2350f639` | same | empty before; temporary untracked external-runtime junction during run; empty after junction removal | `.git/info/exclude` SHA-256 ended `6671FE83B7A07C8932EE89164D1F2793B2318058EB8B98DC5C06EE0A5A3B0EC1` |
| Aleph current-host mutation witness | `bf1320a523fb7cf01953d03426403eb049fe5b1a` | same | empty before; exactly two tracked files dirty during failure; empty after exact-path restoration from HEAD | pin restored to `@opencode-ai/plugin 1.18.23` |
| Aleph compatibility acceptance subject | `bf1320a523fb7cf01953d03426403eb049fe5b1a` | same | empty before and after | durable local state is ignored evidence; no tracked/untracked porcelain entry |
| CodeSleuth candidate | `b56ae39d8b98e1a67f933e03544c83869c3377f4` | same | exact application tree unchanged; temporary report-state junction and host-generated untracked package files removed | report itself is ignored derived data; no candidate commit |

Host identities: Windows NT 10.0.26200; PowerShell 7.6.4; Git 2.55.0.windows.5; Python 3.14.6; Node v26.3.0; Bun 1.4.0; OpenCode 1.18.25 normal host and already-cached compatibility host 1.18.23; Rust 1.88.0; Docker 29.7.2.

The Aleph mutation was byte-visible:

- `.opencode/package.json`: plugin pin `1.18.23 -> 1.18.25`;
- `.opencode/package-lock.json`: plugin and SDK package records, tarball URLs and integrity values changed to 1.18.25.

Only those two tracked paths were restored from immutable HEAD after capturing the exact diff. No application path, planning document, test, Git ref, tag or release was changed. An auxiliary installer/uninstaller witness against a separate disposable PII clone also left an added CodeSleuth reports block in `AGENTS.md`, a managed local-exclude block, and untracked `.opencode/` / `.codesleuth/` material. Those residues were preserved outside the clone and the witness was returned to the exact SHA and empty porcelain state; this supports the same lifecycle/restoration class but is not substituted for the two ordinary `/repo-continue` subjects.

## Target A — PII_PARSER

### Identity

- repository: `DassaultFalconKing/PII_PARSER`
- exact SHA before/after: `9f226013f37c3ca62f8f8a4f2845370e2350f639`
- normal `/repo-continue` session: `ses_f9ccb40e5ffea0cplInLfzzk2p`
- clean disposable subject; the runtime/state junction was removed after evidence capture and final porcelain was empty

### Authority

- canonical planning authority: `docs/current_todo_worklog/TODO.md`, edge `DAE-f6fc8c37-d061-41c2-9758-a19e377bfc2e`
- active scope: earliest unresolved `W-1 Immediate control-plane security containment`, edge `DAE-77bb0bd9-640b-4b4d-92e9-02299f4757f1`
- accepted predecessor: explicit shipped baseline summary `W0-W8 program acceptance baseline`, edge `DAE-241815c8-4c9b-49ab-8119-97186baa7b8f`
- adjacent backlog: B1-B7, edge `DAE-3641a37e-d34a-4794-90e8-47d7ed2f71a5`
- historical, superseded and forbidden states remain distinct: `DAE-526494c3...`, `DAE-be6f5753...`, `DAE-2fa5a978...`
- required reading recorded by the packet: canonical TODO, current-state/conflicts, worklog audit/index, delegating ROADMAP and AGENTS instructions
- uncertainty: live llama.cpp slots / Compose / worker-registry capacity drift remains outside W-1

No material entity received mutually exclusive confirmed roles. Later W2-W8 stages were not aggregated into the active scope.

### Change surface

- main map: `CSM-20260902174225-9f226013f37c-8fb89f3c`
- authority: `DERIVED_NON_AUTHORITATIVE`
- tracked seeds: `api_model_health.py`, `api_workers.py`, `auth.py`, `security.py`, `worker_registry.py`
- 200 entries, `truncated:false`; includes workspace manifests, application import/route consumers, API definitions, 43 test references and authority-named `.github/workflows/patch-lint-gate.yml`
- Unicode probe: `CSM-20260902174714-9f226013f37c-7db9153e`; exact tracked seed `набор аудита/README.md` retained without Git C-quoting or pseudo-path corruption
- manual audit TRUE_POSITIVE samples: `app.py`, `tests/test_worker_registry.py`, `tests/test_llm_health_split_probes.py`, `frontend/src/api/client.ts`, `.github/workflows/patch-lint-gate.yml`
- manual audit UNPROVEN samples: text/comment-only mentions in `card_store.py`, `database/models.py`, and `tools/check_categories.py`; these are not claimed as import/package edges
- meaningful supported-closure FALSE_NEGATIVE: none found in the bounded audit; this is not a universal dependency-solver claim

Future seed probe `alembic/versions/future_spectra_event_outbox.py` was rejected exactly as “change-surface seed is not tracked at exact target”; no future artifact became a seed.

### Continuation and scope guard

- authority map: `DAM-20260902174051-9f226013f37c-175e7ec3`
- continuation packet: `DCP-20260902174352-9f226013f37c-3417715c`
- packet map references: authority map above; main CSM above; `NGM-20260902174239-9f226013f37c-9e3f453c`
- packet includes objective, prerequisite, predecessor, reading, checks, blockers C-01/C-02, uncertainty and authority edge IDs
- **defect:** `pathScopeAuthority=DECLARED` with nine invented allowed paths. The exact authority edges do not declare a positive mutation allowlist. Expected `NOT_DECLARED` and `allowedPaths=[]`.

Actual deterministic guard examples:

| Proposed path | Actual | Acceptance expectation |
|---|---|---|
| `api_model_health.py` | `IN_SCOPE` | `SCOPE_AUTHORITY_UNPROVEN` because no positive path authority exists |
| `frontend/src/App.tsx` | `UNDECLARED` | bounded non-authorization |
| `pipeline.py` | `UNDECLARED` | bounded non-authorization |
| `docs/archive/next_session_01_data_core_v3.md` | `FORBIDDEN_BY_ACTIVE_SCOPE` | specific restriction wins |

The guard is deterministic for the stored packet, but the packet's positive authority is fabricated, so deterministic `IN_SCOPE` is not authoritative.

### Gates

- Native Gate Map: `NGM-20260902174239-9f226013f37c-9e3f453c`
- 11 gates: 7 `REPO_PROVABLE`, 1 `HOSTED_CI_PROVABLE`, 1 `SERVICE_DEPENDENT_REPRODUCIBLE`, 1 `LIVE_RUNTIME_REQUIRED`, 1 `OPERATOR_DECISION_REQUIRED`
- all recorded `UNEXECUTED`; required repo/hosted gates remain open; `CLOUD_TESTABILITY_REMAINING`
- current target CI observation: Actions run `31793883541`, exact target SHA, workflow conclusion failure; backend lint passed and frontend strict lint failed

No target gate was promoted to PASS from candidate CI.

### External evidence

- event: `EE-4afc2b37-5cb5-4526-9985-a1e5dcf6d8d0`
- check: `patch-lint-gate-31793883541`; source `CI_ARTIFACT`; TTL 3600
- exact repository SHA; `nativeOutcome=FAIL`, `nativeDefinesOutcome=true`
- load: one fresh observation, zero stale, `authority=evidence-only`; stored record does not alter repository canon

### PII verdict

**PII_PARSER: FAIL.** R1/R3/R4/R5/R6/R11/R12/R13 behave acceptably, but R2, R7, R9 and R10 fail on generic CodeSleuth behavior.

## Target B — Aleph_Rugent

### Identity

- repository: `DassaultFalconKing/Aleph_Rugent`
- exact SHA before/after: `bf1320a523fb7cf01953d03426403eb049fe5b1a`
- normal current-host attempt: OpenCode 1.18.25, session `ses_f9cc2473effe5QCnwZVNvez1aW`; stopped after read-only violation evidence was captured
- compatibility evidence run: already-cached OpenCode 1.18.23 matching the target's tracked pin, session `ses_f9cc0154effeTcf0754rNVxCUG`
- no dependency update command was run by the operator; the normal host bootstrap itself rewrote tracked package metadata

### Authority

- canonical chain: `ORIENTATION.md` plus `docs/WAYPOINT-PLAN.md`
- active scope: earliest unresolved `S09/W4b`, `docs/session-packets/S09.md`
- accepted predecessor for S09: `docs/session-handoffs/S08.md`
- G1/G2/G4: adjacent graph track, not an S09 predecessor
- required reading: ORIENTATION, CODING-RULES, WAYPOINT, RETRIEVAL-ARCHITECTURE, S08 handoff, ADR0004 and `crates/rag-contracts/src/lib.rs`

The first map `DAM-20260902175321-bf1320a523fb-d999de16` recorded `docs/WAYPOINT-PLAN.md` as both `CANONICAL_PLANNING_AUTHORITY` (`DAE-f72b9446...`) and `FORBIDDEN_COMPETING_AUTHORITY` (`DAE-2fcada3d...`). The latter incorrectly lifted S09's object-level exclusion of later W5/W6 work to the whole canonical planning document. `development_authority_state_load` correctly returned an authority relation contradiction.

Instead of preserving that stop and requesting adjudication, the controller announced a reset, created `DAM-20260902175430-bf1320a523fb-77243b3a`, omitted the conflicting edge and called the result PASS. The exact repository did not assert that the entire WAYPOINT document was forbidden; this was a model/controller classification error followed by a fail-closed bypass.

### Change surface

- main map: `CSM-20260902175613-bf1320a523fb-ea7dc414`
- authority: `DERIVED_NON_AUTHORITATIVE`; `truncated:false`; 145 entries
- seeds: five tracked package owners under `rag-contracts`, `rag-core`, `rag-infra`, `rag-models`, `rag-tools`
- Unicode probe: `CSM-20260902180147-bf1320a523fb-664c0707`; exact `analytical_skills/аналітична записка версія на віддачу.json` preserved as SEED with blob `188408a57793c00eda160b4f0db53ae215da53bb`
- TRUE_POSITIVE closure: six workspace manifests; 27 reverse-consumer entries across rag-cli/safety/server/skills; all 14 `deploy/postgres/001..014` files reached through `include_str!`; 18 tests; `scripts/verify.sh`, `.github/workflows/quality.yml`, canonical verification and acceptance surfaces
- FALSE_POSITIVE sample: archived `docs/archive/2026-08-18-e2e-test-report.md` was tagged as an import reference by token matching
- FALSE_NEGATIVE: none among independently enumerated Cargo reverse dependencies, Rust symbol references, include targets, tests and authority-named gates
- UNPROVEN: external/runtime consumers outside the tracked enumerable universe

Future seed `docs/session-handoffs/S09.md` was rejected exactly as untracked at the target; no surface artifact was created for it.

### Continuation and scope guard

- accepted authority map: `DAM-20260902175430-bf1320a523fb-77243b3a` (after the improperly discarded failed map)
- Native Gate Map: `NGM-20260902175626-bf1320a523fb-ea3d3f0d`
- packet: `DCP-20260902175713-bf1320a523fb-554df4ce`
- packet contains SHA/map IDs, two planning authorities, S09 objective, prerequisites, S08 predecessor, seven required-reading items, eight allowed entries, four restriction entries, repo/hosted/live checks, two uncertainties and five authority edges

The content is superficially complete, but it is not acceptance-valid because it depends on a replacement map created after fail-closed contradiction and because the path data is not a faithful repository-path model.

Actual guard probes:

| Proposed path | Result | Note |
|---|---|---|
| `crates/rag-core/src/lib.rs` | `IN_SCOPE` | exact allowed file |
| `docs/session-packets/G1.md` | `ADJACENT_TRACK` | correct explicit adjacent rule |
| `.opencode/tools/development_continuation_state.ts` | `UNDECLARED` | tooling outside declared scope |
| `README.md` | `UNDECLARED` | docs outside declared scope |
| `docs/baseline/graph-projection.json` | `UNDECLARED` | intended directory `docs/baseline/` does not expand |
| `crates/rag-contracts/tests/golden.rs` | `UNDECLARED` | intended `crates/*/tests/` does not expand |
| `crates/rag-tools/src/toolcaller.rs` | `UNDECLARED` | intended W5/toolcaller restriction does not match |
| `crates/rag-contracts/src/lib.rs:GraphProjection/x` | `ADJACENT_TRACK` | synthetic object/member string accepted as if it were a path |

The packet also accepted prose `W5 production toolcaller translation` and a string containing `or W5 intent compilation` as path patterns. The tool's deterministic output is stable, but pattern validation and semantics are not repository-path faithful.

### Gates

- Native Gate Map `NGM-20260902175626-bf1320a523fb-ea3d3f0d`: 7 gates
- 2 `REPO_PROVABLE` (`verify.sh fast`, `contracts`); 2 `SERVICE_DEPENDENT_REPRODUCIBLE` (`postgres`, aggregate `all`); 2 `HOSTED_CI_PROVABLE` (rust, postgres-migrations); 1 `LIVE_RUNTIME_REQUIRED` (opt-in self-hosted investigation)
- every gate remains `UNEXECUTED`; four required repo/hosted gate IDs remain open; `CLOUD_TESTABILITY_REMAINING`
- Actions run `33272230534` is on the exact SHA and has workflow conclusion failure, but rust, postgres-migrations and review-pack each have zero steps; authorized-investigation is skipped. This is `nativeOutcome=UNKNOWN`, not a semantic test FAIL and not PASS.

### External evidence

- event: `EE-9f5efc95-1043-4634-9d13-b707b9ed6d86`
- check `quality-33272230534`; source `CI_ARTIFACT`; TTL 3600
- exact SHA; observed 2026-09-02T18:02:00Z; one fresh, zero stale
- `nativeOutcome=UNKNOWN`, `nativeDefinesOutcome=false`, `authority=false`; load reports `authority=evidence-only`

### Aleph verdict

**Aleph_Rugent: FAIL.** Unicode, stop-gate selection, structural closure, future-seed rejection, gate honesty and evidence authority behave acceptably. Fresh-step ordering, fail-closed authority handling, packet/path semantics, scope enforcement and read-only host separation do not.

## R1–R13 regression matrix

| Criterion | PII | Aleph | Exact repeat evidence |
|---|---|---|---|
| R1 Unicode / Git path framing | PASS | PASS | `CSM-...7db9153e` and `CSM-...664c0707` preserve exact non-ASCII/space paths and derive successfully. |
| R2 undeclared positive path authority | FAIL | NOT_APPLICABLE | PII has no positive allowlist authority, but packet says `DECLARED` with nine invented paths and guard returns `IN_SCOPE`. |
| R3 semantic authority exclusivity | PASS | FAIL | PII roles remain distinct. Aleph first map made WAYPOINT both canonical and forbidden; loader failed, then controller replaced the map. |
| R4 earliest unresolved stop-gate | PASS | PASS | PII selects W-1 only; Aleph selects S09/W4b only. Later W2-W8, W5/W6 and graph work remain outside active scope. |
| R5 structural change-surface recall | PASS | PASS | Bounded manual audit confirmed packages, reverse consumers, imports/routes, includes/migrations, tests and authority gates. One Aleph archive false positive remains derived/non-authoritative; no meaningful supported-case false negative found. |
| R6 future/nonexistent seeds | PASS | PASS | Both future probes reject untracked paths and create no accepted map. |
| R7 fresh-step isolation | FAIL | FAIL | Parent work begins before any limitation marker; `STEP_ISOLATION_UNPROVEN` appears only in the final response after same-session completion. |
| R8 read-only boundary | PASS | FAIL | PII acceptance subject ends unchanged. OpenCode 1.18.25 rewrites two tracked Aleph package files; controller observes dirty state and continues. |
| R9 Development Continuation Packet | FAIL | FAIL | PII semantic field fabricates positive authority. Aleph packet is downstream of a discarded contradiction and stores malformed conceptual path patterns. |
| R10 deterministic scope_guard | FAIL | FAIL | PII grants unsupported `IN_SCOPE`; Aleph directory descendants and real toolcaller path are UNDECLARED while a synthetic member string matches adjacent. |
| R11 Native Gate Map honesty | PASS | PASS | Both maps preserve classes and `UNEXECUTED`; both remain `CLOUD_TESTABILITY_REMAINING`. |
| R12 ExternalEvidenceManifestV1 | PASS | PASS | Exact-SHA safe ingests are fresh, secret-free and `authority=evidence-only`; Aleph runnerless state remains UNKNOWN. |
| R13 runtime/repository contradictions | PASS | FAIL | PII hosted red stays runtime evidence. Aleph tracked pin 1.18.23 vs host 1.18.25 causes target mutation and is not handled as `READ_ONLY_BOUNDARY_BLOCKED`. |

## Findings

### RC6-RPT-LD-01 — normal newer host mutates tracked target config and controller fails open

- severity: **BLOCKER**
- exact subject: candidate `b56ae39d8b98e1a67f933e03544c83869c3377f4`; target `bf1320a523fb7cf01953d03426403eb049fe5b1a`; OpenCode 1.18.25
- evidence: session `ses_f9cc2473effe5QCnwZVNvez1aW`; exact diff changes tracked plugin/SDK metadata 1.18.23 to 1.18.25; controller's own `git status` shows both files modified and it continues to playbook/authority reading
- reproducer: use candidate external runtime and ordinary read-only `/repo-continue` against the clean exact Aleph target under normal host 1.18.25
- expected: prevent target bootstrap writes or immediately return `READ_ONLY_BOUNDARY_BLOCKED` with exact observation and external remediation
- actual: target mutation precedes analysis; dirty identity is observed but analysis continues
- affected capability: R8 read-only boundary; R13 runtime/repository contradiction; host/runtime separation
- genericness: **generic** for tracked target-local OpenCode pins under a differing host

### RC6-RPT-LD-02 — controller invents positive path authority for an authority-less target

- severity: **HIGH**
- exact subject: candidate `b56ae39...`; PII target `9f226013...`
- evidence: `DCP-...3417715c` says `DECLARED` and stores nine files; no confirmed authority edge declares that allowlist; direct guard returns `api_model_health.py -> IN_SCOPE`
- reproducer: ordinary `/repo-continue` on PII exact SHA, then load packet and call guard
- expected: `pathScopeAuthority=NOT_DECLARED`, empty allowlist, ordinary path `SCOPE_AUTHORITY_UNPROVEN`
- actual: model-supplied owners are promoted into mutation authority
- affected capability: R2, R9, R10
- genericness: **generic** for repositories describing work without a formal positive path allowlist

### RC6-RPT-LD-03 — fail-closed authority contradiction can be bypassed by starting a replacement map

- severity: **HIGH**
- exact subject: candidate `b56ae39...`; Aleph target `bf1320a...`
- evidence: failed `DAM-...d999de16`, contradictory edges `DAE-f72b9446...` / `DAE-2fcada3d...`, correct loader contradiction, followed by replacement `DAM-...77243b3a` and final “after correction ... PASS”
- reproducer: ordinary compatibility-host `/repo-continue` session `ses_f9cc0154effeTcf0754rNVxCUG`
- expected: preserve both records and stop for operator adjudication; do not resolve by model preference
- actual: controller drops its conflicting classification and continues
- affected capability: R3 semantic exclusivity; R9 packet authority integrity
- genericness: **generic controller/playbook state-transition gap**, triggered by a target-specific misclassification

### RC6-RPT-LD-04 — fresh-step limitation is recorded only after same-session fallback

- severity: **HIGH**
- exact subjects: both unchanged foreign target SHAs
- evidence: PII child/setup failure is followed by parent DAM/CSM/NGM/DCP work before the final marker; Aleph completes all six steps in one session and only final prose states `STEP_ISOLATION_UNPROVEN`
- reproducer: ordinary `/repo-continue` when host does not materialize the required child step
- expected: record `STEP_ISOLATION_UNPROVEN` before same-session fallback; never imply strict prompt eviction
- actual: limitation is retroactive and cannot gate parent execution
- affected capability: R7 fresh-step isolation
- genericness: **generic**

### RC6-RPT-LD-05 — path-pattern schema accepts non-path semantics and does not implement intended directory descendants

- severity: **HIGH**
- exact subject: candidate `b56ae39...`; Aleph packet `DCP-...554df4ce`
- evidence: packet accepts prose, `or` expressions and `file.rs:Member/*`; direct guard leaves real baseline/test/toolcaller descendants `UNDECLARED` but matches the synthetic member string
- reproducer: load the Aleph packet and run the eight direct path probes listed above
- expected: stored mutation/restriction patterns must be valid repository paths with clear file/directory/glob semantics and must enforce the exact authority boundary
- actual: schema-valid patterns are not repository-path faithful
- affected capability: R9 packet; R10 scope guard
- genericness: **generic deterministic-tool validation/semantics gap**

### RC6-RPT-LD-06 — installer/uninstaller leaves target residues in a disposable lifecycle witness

- severity: **HIGH**
- exact subject: candidate `b56ae39...`; separate PII clone at `9f226013...`
- evidence: after the install/uninstall exercise with `--no-enforce-agents-md-rules`, `AGENTS.md` retained the CodeSleuth reports block, `.git/info/exclude` retained the managed local-only block, and `.opencode/` / `.codesleuth/` remained untracked
- reproducer: candidate `install.py` lifecycle on a fresh exact target using that flag, followed by uninstall and byte/status comparison
- expected: flag behavior and uninstall restoration must leave exact pre-install bytes/state, or explicitly fail closed
- actual: lifecycle residues remain until operator cleanup
- affected capability: installed-surface lifecycle; R8 read-only/restoration boundary
- genericness: **generic**

## Candidate and publication boundary

The candidate remains detached at exact `b56ae39d8b98e1a67f933e03544c83869c3377f4`. Current remote navigation after fetch:

- `main = 4370c0d63173d27556b11d629746afee07f3cf62`
- `SIB = 091693e36dfc3a96f572689075baa529c50132f0`
- PR #111 head / `feature/rc6-eha-brownfield-bootstrap = 1de37c75251a1e0d9904cffdb82695e92e3fab23`
- `fix/rc6-live-dogfood-repeat = 9a944dd52c6836ca2167fcaa594e3564bbfa24a6`

Those are navigation metadata only. No ref was moved by this acceptance. This report must be published only through the candidate-defined `reports` route to branch `reports`; it must not be committed to the RC6 candidate branch.

## Final boundary

- PII_PARSER: **FAIL**
- Aleph_Rugent: **FAIL**
- overall: **RC6_REPAIR_REQUIRED**
- SIB0/SIB1/SIB2: **NOT RUN / NOT CLAIMED**
- EHA: **NOT RUN**
- PR #111 merge: **NOT PERFORMED**
- RC7: **NOT STARTED**
