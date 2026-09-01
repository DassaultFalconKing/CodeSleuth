# RC6 Implementation Ledger

Status: **ACTIVE IMPLEMENTATION AUTHORITY COMPANION**

Scope authority: `docs/RC6-FEATURE-PLAN.md` as accepted by `docs/RC6-SCOPE-ACCEPTANCE.md`.

Purpose: this file is the compact, durable state ledger for RC6 implementation. It exists so a future CodeSleuth/LLM session can reconstruct what is planned, implemented, missing, tested, or blocked without relying on chat history.

This ledger **does not replace** the accepted feature plan. If this ledger conflicts with the feature plan, the feature plan wins and this ledger must be repaired.

---

## 0. Reading contract for future sessions

### Status enum

Use exactly these statuses:

- `PLANNED` — required by accepted RC6 scope; implementation not yet present.
- `PARTIAL` — some implementation exists, but the accepted contract is not fully satisfied.
- `IMPLEMENTED_UNVERIFIED` — implementation appears complete, but required acceptance evidence is missing.
- `CLOUD_VERIFIED` — required repository/hosted deterministic checks pass on the recorded exact head.
- `LIVE_PENDING` — cloud contract is closed; remaining proof explicitly requires live host/runtime evidence.
- `LIVE_VERIFIED` — live-host acceptance completed with recorded evidence.
- `BLOCKED` — cannot proceed until the stated blocker is resolved.
- `DEFERRED` — explicitly outside RC6 or postponed by accepted authority. Do not silently treat as complete.

### Update rules

For every item:

1. Never mark an item complete from prose, intent, filenames, model confidence, or a PR description.
2. Prefer exact file/tool/test evidence and exact Git SHA.
3. `CLOUD_VERIFIED` requires the relevant test/gate to have actually passed on one exact head.
4. A later source change invalidates prior exact-head acceptance unless the change is proven tree/content irrelevant to that gate.
5. `LIVE_VERIFIED` is forbidden while any required `REPO_PROVABLE` or `HOSTED_CI_PROVABLE` gate remains open.
6. If a requirement from `RC6-FEATURE-PLAN.md` is absent here, add it as `PLANNED`; do not assume omission means cancellation.
7. Any newly discovered useful feature that is not required to satisfy accepted RC6 scope belongs after RC6 unless explicitly re-accepted.

### Current integration baseline

Last audited implementation head before creation of this ledger:

`93c0deffe19d7753f6497435a22d8c5ef2def6e8`

Last audited hosted acceptance run:

`33547907918`

Observed result at that head:

- TUI visual regression: PASS
- Durable state / context graph: PASS
- Graphify enabled runtime: PASS
- Python suite: FAIL due to 3 stale/prose/source-layout assertions
- exact result: `403 passed, 3 failed, 9 skipped` on Python 3.10 Ubuntu

The commit that adds this ledger is a **new head**. Re-run acceptance after implementation changes before assigning `CLOUD_VERIFIED` to the final RC6 candidate.

---

## 1. Executive state

| Slice | Contract | Status | Next blocking action |
| --- | --- | --- | --- |
| RC6-0 | Current cloud-testable defect closure | `PARTIAL` | Remove prose/source-layout tests; finish distribution/docs parity |
| RC6-A | Deterministic EHA authority | `IMPLEMENTED_UNVERIFIED` | Behavioral tests + exact-head hosted pass |
| RC6-B | Brownfield contract bootstrap | `IMPLEMENTED_UNVERIFIED` | Distribution parity + full fixtures + hosted pass |
| RC6-C | Development Authority Map | `IMPLEMENTED_UNVERIFIED` | Fixture coverage + normative docs |
| RC6-D | Continuation packet and scope guard | `PARTIAL` | Derive pre-registry change surface; packet projection parity |
| RC6-E | Native Gate Map / cloud boundary | `IMPLEMENTED_UNVERIFIED` | Fixture and docs parity + hosted pass |
| RC6-F | External evidence manifest | `IMPLEMENTED_UNVERIFIED` | Normative docs + packaging/installed parity |
| Wave 6 | Distribution, docs, fixtures | `PARTIAL` | Main remaining context-loss cluster |
| Wave 7 | Exact-head acceptance and live dogfood | `PLANNED` | Forbidden until Wave 6 + hosted 7/7 close |

---

## 2. RC6-0 — Current defect closure

### RC6-0-D1 — One canonical EHA bridge entry point

**Status:** `IMPLEMENTED_UNVERIFIED`

**Required contract:** one production CLI entry point; stable RC5d watchdog/core must not be accidentally forked into competing authorities.

**Implementation evidence:**

- `scripts/eha_github_bridge.py` — canonical public entry point.
- `scripts/eha_github_bridge_controller.py` — RC6 trusted controller.
- `scripts/eha_github_bridge_core.py` — stable bridge/watchdog primitives.
- `.github/workflows/eha.yml` invokes `scripts/eha_github_bridge.py` only.

**Open proof:** replace source-layout/prose assertions with import/behavior tests and obtain hosted PASS.

### RC6-0-D2 — Deterministic provenance before campaign start

**Status:** `IMPLEMENTED_UNVERIFIED`

**Required contract:** trusted controller binds canonical provenance before durable `campaign_started`; provider must not own or rebind that authority.

**Implementation evidence:**

- `scripts/eha_campaign_bootstrap.py`
- `scripts/eha_github_bridge_controller.py`
- `tests/test_eha_campaign_bootstrap.py`

**Acceptance:** behavioral test must prove provider invocation is unreachable when bootstrap fails, and prestarted campaign identity is passed immutably.

### RC6-0-D3 — No prose-based behavior tests

**Status:** `BLOCKED`

**Observed blocker:** hosted run `33547907918` failed three tests that inspect source text rather than behavior:

1. literal prompt phrase `Do not create, restart, replace, or supersede that campaign`;
2. literal command list `"run", "--command", "eha-test", "--format", "json"`;
3. literal identifier `private_transcript_path` in the wrapper source.

**Required fix:** replace them with behavioral/import-level tests proving:

- canonical entry dispatches through trusted controller;
- controller invokes the canonical OpenCode command semantics;
- transcript is written only to private persistence and not streamed to public log;
- provider cannot run before bootstrap authority exists.

**Done condition:** no RC6 acceptance test depends on English prompt text, implementation symbol names, or module layout when the actual contract is behavioral.

### RC6-0-D4 — Dirty/blob-safe brownfield evidence

**Status:** `IMPLEMENTED_UNVERIFIED`

**Implementation evidence:** `pack/.opencode/tools/contract_bootstrap_state.ts` stores and revalidates tracked `(path, blobHash)` evidence and fails closed on tracked dirtiness/head change.

**Open proof:** fixture must mutate tracked evidence at same conceptual candidate and demonstrate rejection before adjudication/materialization.

### RC6-0-D5 — Generic foreign registry semantics

**Status:** `IMPLEMENTED_UNVERIFIED`

**Required contract:** foreign repository bootstrap must not inherit CodeSleuth self-registry/SIB history.

**Expected semantics:**

- foreign profile: `generic`;
- no inferred `SIB1`, `SIB2`, or `PROTECTED` status;
- adopted `AGREE` candidate at most `implemented`;
- explicitly adopted `UNPROVEN` candidate at most `experimental`.

**Open proof:** deterministic foreign-repository fixture + materialization assertion.

### RC6-0-D6 — Resumable human adjudication

**Status:** `IMPLEMENTED_UNVERIFIED`

**Surfaces:**

- `/repo-contract-adjudicate`
- durable bootstrap state/decision machinery

**Required contract:** isolated analytical subagent cannot approve its own discovery; adoption is explicit primary-controller/user authority.

### RC6-0-D7 — Distribution/install parity

**Status:** `PARTIAL`

**Missing at last audit:** no corresponding RC6 updates in:

- `smoke.py`
- `pack/.opencode/bin/review-pack-smoke.py`
- `tests/test_smoke_parity.py`

`pack/.opencode/bin/playbook_catalog.py` had no substantive RC6 alias/catalog change at the audited head.

**Required installed surfaces include at minimum:**

- `/repo-contract-bootstrap`
- `/repo-contract-adjudicate`
- `/repo-continue`
- `repository-contract-bootstrap`
- `repository-development-continuation`
- `contract-archaeology`
- `development-authority-discovery`
- `contract_bootstrap_state`
- `development_authority_state`
- `development_continuation_state`
- `native_gate_state`
- `external_evidence_state`

**Done condition:** source Verify and installed Verify require the same advertised RC6 surfaces and installation smoke proves they survive materialization.

### RC6-0-D8 — Normative documentation current

**Status:** `PARTIAL`

**Missing normative contracts at last audit:**

- Development Authority Map
- Development Continuation Packet / scope guard
- Native Gate Map
- ExternalEvidenceManifestV1
- brownfield generic-registry lifecycle/adjudication semantics
- updated EHA bridge architecture after trusted prestart split

**Metadata drift:** `docs/RC6-FEATURE-PLAN.md` still declared `PROPOSED FOR SCOPE ACCEPTANCE` while `docs/RC6-SCOPE-ACCEPTANCE.md` declares the scope accepted.

### RC6-0-D9 — Exact-head hosted acceptance

**Status:** `PLANNED`

**Required result:** one final exact RC6 head passes all 7 hosted acceptance jobs. No removal or weakening of existing jobs is allowed.

---

## 3. RC6-A — Deterministic EHA authority

**Status:** `IMPLEMENTED_UNVERIFIED`

### Contract checklist

- [x] exact release SHA frozen before provider execution
- [x] durable state wired before provider execution
- [x] deterministic provenance bound before campaign start
- [x] review checkpoint exists before provider execution
- [x] `campaign_started` exists before provider execution
- [x] provider receives already-started campaign identity
- [x] provider is forbidden from creating/restarting/replacing campaign
- [x] completion authority remains durable `campaign_completed`
- [x] transport outcome remains separate from EHA verdict
- [ ] stale prose/source-layout tests replaced with behavioral tests
- [ ] hosted matrix green on final exact head
- [ ] live self-hosted EHA proves campaign is visible before first provider output
- [ ] live EHA proves SIB0/SIB1/SIB2 + durable completion + clean transport on release candidate

### Live boundary

Do **not** move this slice to `LIVE_PENDING` until all required hosted cloud gates are green.

---

## 4. RC6-B — Brownfield contract bootstrap

**Status:** `IMPLEMENTED_UNVERIFIED`

### Implemented surfaces

- `/repo-contract-bootstrap`
- `/repo-contract-adjudicate`
- `repository-contract-bootstrap` Playbook
- `contract-archaeology` Skill
- `contract_bootstrap_state.ts`

### Required behavior checklist

- [x] no existing protected registry required to begin archaeology
- [x] discovery remains candidate-level, not authority
- [x] code/docs/tests triangulation precedes durable adoption
- [x] evidence binds exact tracked blob hashes
- [x] tracked dirty worktree invalidates authority
- [x] explicit user adjudication boundary
- [x] `AGREE + adopt` cannot exceed `implemented`
- [x] `UNPROVEN + adopt_unproven` cannot exceed `experimental`
- [x] drift/contradiction cannot be silently adopted
- [x] foreign registry does not inherit CodeSleuth SIB history
- [ ] installed-pack parity
- [ ] dedicated deterministic brownfield fixture proving generic foreign materialization
- [ ] normative lifecycle docs

---

## 5. RC6-C — Development Authority Map

**Status:** `IMPLEMENTED_UNVERIFIED`

### Implementation evidence

- `development-authority-discovery` Skill
- `development_authority_state.ts`

### Required relationship classes

Track all meanings distinctly:

- `CANONICAL_PLANNING_AUTHORITY`
- `ACTIVE_IMPLEMENTATION_SCOPE`
- `NORMATIVE_ARCHITECTURE`
- `ACCEPTANCE_AUTHORITY`
- `ACCEPTED_PREDECESSOR`
- `SUPPORTING_EVIDENCE`
- `SUPERSEDES`
- `SUPERSEDED_BY`
- `HISTORICAL_ARCHIVE`
- `ADJACENT_PARALLEL_TRACK`
- `FORBIDDEN_COMPETING_AUTHORITY`

### Evidence contract

Every authority edge must remain exact-head bound with tracked evidence. Filename conventions, timestamps, model confidence, or document length may aid discovery but never establish authority.

### Missing proof

- dedicated layered TODO/worklog fixture;
- dedicated waypoint/session-packet fixture;
- explicit accepted-predecessor / required-reading acceptance;
- normative authority-map doc.

---

## 6. RC6-D — Development continuation and scope guard

**Status:** `PARTIAL`

### Implemented surfaces

- `/repo-continue`
- `repository-development-continuation` Playbook
- `development_continuation_state.ts`
- deterministic scope guard

### Working contracts

- [x] packet requires confirmed canonical planning authority
- [x] packet requires confirmed active implementation scope
- [x] guard classifies `IN_SCOPE`
- [x] guard classifies `UNDECLARED`
- [x] guard classifies `ADJACENT_TRACK`
- [x] guard classifies `FORBIDDEN_BY_ACTIVE_SCOPE`
- [x] authority failure yields `SCOPE_AUTHORITY_UNPROVEN`
- [x] guard never auto-expands scope

### RC6-D-GAP1 — Pre-registry change-surface derivation

**Status:** `PLANNED`

**Context-loss finding:** current packet accepts `changeSurface: string[]` supplied by caller. The accepted plan requires CodeSleuth to derive a non-authoritative pre-registry change-surface map from repository evidence such as:

- language/package workspaces;
- import/module ownership;
- migrations;
- schemas / DTOs;
- API definitions;
- CI / verify scripts;
- tests referencing affected surfaces;
- explicit docs ownership / allowed-path declarations.

**Required principle:** LLM may classify or summarize the derived surface, but it must not be able to manufacture the entire change surface as an unverified string list.

**Done condition:** deterministic bounded derivation exists, carries evidence, and is used by continuation packet creation when no protected registry exists.

### RC6-D-GAP2 — Frozen packet projection parity

**Status:** `PARTIAL`

Accepted minimum packet schema includes semantic outputs `nativeGates` and `authorityEvidence`.

Current implementation stores references such as:

- `nativeGateMapId`
- `authorityEdgeIds`

This is acceptable internally only if packet load/output exposes bounded resolved projections equivalent to the frozen semantic fields.

**Done condition:** loaded continuation packet contains human/model-readable bounded `nativeGates` and `authorityEvidence`, derived from the referenced exact state rather than copied unverified strings.

---

## 7. RC6-E — Native Gate Map and cloud/live boundary

**Status:** `IMPLEMENTED_UNVERIFIED`

### Implementation evidence

- `native_gate_state.ts`
- continuation smoke exercises repo/hosted/live classifications

### Required classes

- `REPO_PROVABLE`
- `HOSTED_CI_PROVABLE`
- `SERVICE_DEPENDENT_REPRODUCIBLE`
- `LIVE_RUNTIME_REQUIRED`
- `OPERATOR_DECISION_REQUIRED`

### Required boundary

- any required repo/hosted gate not PASS -> `CLOUD_TESTABILITY_REMAINING`
- all required repo/hosted gates PASS -> `LIVE_HANDOFF_READY`

### Open proof

- dedicated fixture discovery from project-native workflow/verify/acceptance evidence;
- installed-pack parity;
- normative documentation;
- final exact-head hosted PASS.

---

## 8. RC6-F — Generic external evidence manifest

**Status:** `IMPLEMENTED_UNVERIFIED`

### Implementation evidence

- `external_evidence_state.ts`
- `tests/external_evidence_state_smoke.ts`

### Required contract

- append-only durable evidence
- exact repository SHA
- observation timestamp
- freshness TTL
- stale remains visible as stale
- secrets/raw credentials forbidden
- runtime observation cannot override repository authority by itself
- PASS/FAIL only if native underlying check defines that outcome
- no PII-specific or Aleph-specific adapter logic in RC6 core

### Open proof

- installed-pack parity;
- normative schema/authority documentation;
- final hosted PASS;
- later live evidence ingestion during dogfood.

---

## 9. Wave 6 — Fixtures, distribution, documentation

**Status:** `PARTIAL`

This is the largest remaining context-loss cluster.

### FIXTURE-A — Layered TODO/worklog authority repository

**Status:** `PLANNED`

Must encode:

- one explicit planning SSOT;
- superseded roadmaps;
- supporting current-state evidence;
- archived shipped work;
- critical-path stop-gate;
- mixed repository and live-runtime acceptance.

Must prove:

- only declared SSOT selected;
- superseded roadmap never revived;
- prerequisite stop-gate selected as next admissible scope;
- runtime-only proof separated from cloud proof.

### FIXTURE-B — Waypoint/session-packet authority repository

**Status:** `PLANNED`

Must encode:

- Orientation selecting active track;
- Waypoint plan ordering work;
- session packet defining objective/allowed paths/exclusions;
- accepted predecessor/handoff;
- required reading;
- adjacent parallel track;
- native verify gates;
- initially absent protected-capability registry.

Must prove:

- active session packet selected;
- predecessor and required reading preserved;
- adjacent path rejected by scope guard;
- registry absence does not block continuation mapping;
- later brownfield bootstrap can produce target-local contract candidates.

### Distribution parity

**Status:** `PARTIAL`

See `RC6-0-D7`.

### Normative documentation

**Status:** `PARTIAL`

See `RC6-0-D8`.

### PR metadata

**Status:** `PARTIAL`

PR #111 description at last audit described RC6-A/B only while implementation already contained C/D/E/F. Before review readiness, update PR body to the accepted complete RC6 scope and current exact-head acceptance state.

---

## 10. Wave 7 — Acceptance sequence

**Status:** `PLANNED`

Required order, no shortcuts:

1. Close every required `PLANNED`, `PARTIAL`, or `BLOCKED` cloud item above.
2. Produce one exact RC6 feature head.
3. Run complete hosted acceptance on that exact SHA.
4. Require 7/7 green.
5. Re-run this implementation ledger against `docs/RC6-FEATURE-PLAN.md` and record any remaining context loss.
6. Only then mark live-dependent slices `LIVE_PENDING`.
7. Perform read-only PII Parser dogfood.
8. Perform read-only Aleph Rugent dogfood.
9. Repair any generic CodeSleuth defect discovered by dogfood; repository-specific behavior remains forbidden.
10. Create/freeze exact release-stream candidate SHA.
11. Run hosted acceptance again on the exact release candidate if its SHA differs from the feature-head proof.
12. Run fresh canonical EHA SIB0/SIB1/SIB2 on the exact candidate.
13. Require durable prestart identity, SIB0 PASS, SIB1 PASS, SIB2 PASS, durable `campaign_completed`, clean checkout, and acceptable transport outcome.
14. Only then consider SIB/tag/release promotion.

---

## 11. Context-loss register

This section exists specifically to answer: **"what fell out of context?"**

| ID | Lost/omitted obligation | Current status | Recovery |
| --- | --- | --- | --- |
| CL-001 | Replace prose/source-layout EHA tests with behavioral tests | `BLOCKED` | Rewrite 3 failing Python tests |
| CL-002 | Source/install smoke parity for new RC6 surfaces | `PARTIAL` | Update source + installed required lists and parity tests |
| CL-003 | Playbook catalog aliases/exposure for new RC6 workflows | `PARTIAL` | Add semantic catalog assertions and aliases |
| CL-004 | Separate layered TODO/worklog deterministic fixture | `PLANNED` | Implement Fixture A |
| CL-005 | Separate waypoint/session-packet deterministic fixture | `PLANNED` | Implement Fixture B |
| CL-006 | Deterministic pre-registry change-surface derivation | `PLANNED` | Add bounded evidence-backed derivation tool/state |
| CL-007 | Continuation packet semantic `nativeGates` projection | `PARTIAL` | Resolve from gate map on load/output |
| CL-008 | Continuation packet semantic `authorityEvidence` projection | `PARTIAL` | Resolve from authority map on load/output |
| CL-009 | Normative RC6-C/D/E/F documentation | `PARTIAL` | Write/update contracts after runtime shape stabilizes |
| CL-010 | Feature-plan status still says PROPOSED despite acceptance | `PARTIAL` | Update to ACCEPTED without changing frozen scope text |
| CL-011 | PR #111 body only describes A/B | `PARTIAL` | Refresh before review readiness |
| CL-012 | Final context-loss audit before live handoff | `PLANNED` | Compare plan ↔ ledger ↔ PR diff ↔ tests on final cloud-green head |

Do not delete a context-loss row when fixed. Change its status to `CLOUD_VERIFIED` and add exact evidence so future sessions can see that it was intentionally recovered.

---

## 12. Next execution queue

Execute in this order unless a failing gate proves a different dependency:

1. `CL-001` behavioral EHA tests.
2. `CL-006` deterministic pre-registry change-surface derivation.
3. `CL-007` + `CL-008` resolved continuation-packet projections.
4. `CL-004` Fixture A.
5. `CL-005` Fixture B.
6. `CL-002` + `CL-003` distribution/catalog parity.
7. `CL-009` + `CL-010` normative/document status cleanup.
8. `CL-011` PR metadata refresh.
9. full hosted acceptance on one exact head.
10. `CL-012` context-loss audit.
11. live dogfood only after cloud green.

The queue is implementation ordering, not new scope authority.
