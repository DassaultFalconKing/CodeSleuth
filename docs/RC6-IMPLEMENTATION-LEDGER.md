# RC6 Implementation Ledger

Status: **CURRENT DEVELOPMENT STATUS**

Scope authority: `docs/RC6-FEATURE-PLAN.md`, accepted by `docs/RC6-SCOPE-ACCEPTANCE.md`.

This ledger is the current RC6 state surface. It records what is implemented, what is actually verified, and what still blocks live-host handoff. It supersedes the earlier implementation-state snapshot that stopped at head `93c0deffe19d7753f6497435a22d8c5ef2def6e8`.

## 1. Exact evidence baseline

Last fully hosted-accepted implementation head before this status/archive-only documentation commit:

`34546d19bc9fcf77c3f0a4ec408c3e9c19ab19ad`

Canonical hosted acceptance:

- workflow: `CodeSleuth acceptance`
- run: `33560728115`
- result: **PASS — 7/7**
- exact checkout SHA: `34546d19bc9fcf77c3f0a4ec408c3e9c19ab19ad`

Verified jobs on that exact head:

- Python 3.10 / Ubuntu: PASS
- Python 3.12 / Ubuntu: PASS
- Python 3.10 / Windows: PASS
- Python 3.12 / Windows: PASS
- Durable state / context graph: PASS
- TUI visual regression / Ubuntu: PASS
- Graphify enabled runtime / Python 3.12 / Ubuntu: PASS

Important: this documentation/archive update creates a new Git head. The PASS above remains evidence for the implementation tree at `34546d19...`; the new documentation head must receive fresh hosted acceptance before it can itself be used as an exact-head candidate.

## 2. Status vocabulary

Use only:

- `CLOUD_VERIFIED` — implementation behavior is covered by repository/hosted checks that passed on the recorded exact head.
- `IMPLEMENTED_UNVERIFIED` — implementation exists but its required acceptance proof is incomplete.
- `PARTIAL` — accepted RC6 contract is only partly implemented.
- `BLOCKED` — work cannot advance to the next authority boundary.
- `LIVE_PENDING` — all required cloud-testable proof is complete and only live-host evidence remains.
- `LIVE_VERIFIED` — required live-host proof completed.
- `DEFERRED` — explicitly outside RC6.

## 3. Executive state

| Slice | State | Exact evidence / blocker |
| --- | --- | --- |
| RC6-A deterministic EHA authority | `CLOUD_VERIFIED` | behavioral EHA tests and hosted Python matrix PASS on `34546d19...` |
| RC6-B brownfield contract bootstrap | `CLOUD_VERIFIED` core | durable bootstrap state passes; distribution parity still belongs to Wave 6 |
| RC6-C Development Authority Map | `CLOUD_VERIFIED` core | durable authority state + deterministic fixtures PASS |
| RC6-D continuation packet / scope guard | `CLOUD_VERIFIED` core | deterministic change-surface derivation, packet projections, scope guard and fixtures PASS |
| RC6-E Native Gate Map / cloud boundary | `CLOUD_VERIFIED` core | durable gate state and continuation smoke PASS |
| RC6-F ExternalEvidenceManifestV1 | `CLOUD_VERIFIED` core | durable external-evidence smoke PASS |
| Wave 6 distribution/docs parity | `PARTIAL` | new RC6 surfaces are not yet required by installed/source smoke contracts; normative docs remain incomplete |
| Wave 7 live dogfood / EHA | `BLOCKED` | forbidden until Wave 6 is closed and the resulting exact head is hosted-green |

## 4. Closed context-loss items

The following previously missing requirements are now implemented and passed inside the hosted acceptance tree at `34546d19...`.

### CL-001 — prose/source-layout EHA tests

State: `CLOUD_VERIFIED`.

The three stale source-string assertions that failed run `33547907918` were replaced by behavioral/import-level coverage. Python 3.10 and 3.12 pass on Ubuntu and Windows.

### CL-004 — layered TODO/worklog fixture

State: `CLOUD_VERIFIED`.

Fixture root: `tests/fixtures/rc6/layered-todo/`.

It models one planning SSOT, superseded roadmap, current-state evidence, archived shipped work, stop-gate and mixed repo/live acceptance.

### CL-005 — waypoint/session-packet fixture

State: `CLOUD_VERIFIED`.

Fixture root: `tests/fixtures/rc6/waypoint-session/`.

It models Orientation -> Waypoint -> session packet -> predecessor handoff -> ADR/native gates plus an adjacent track.

### CL-006 — deterministic pre-registry change surface

State: `CLOUD_VERIFIED`.

`change_surface_state` derives bounded tracked surfaces from repository-native evidence and binds entries to exact Git blobs rather than accepting an arbitrary LLM-supplied string list as authority.

### CL-007 / CL-008 — continuation packet projections

State: `CLOUD_VERIFIED`.

`development_continuation_state` now resolves bounded semantic projections for native gates and authority evidence instead of exposing only opaque IDs.

## 5. Open cloud-testable work

These items remain mandatory before any Work/Cursor/OpenCode live-host handoff.

### CL-002 — source/install smoke parity

State: `PARTIAL`.

Current evidence: root `smoke.py` still does not require the RC6 surfaces below. Therefore canonical hosted acceptance can be green while an installed pack silently omits them.

Required installed surfaces:

- commands: `repo-contract-bootstrap`, `repo-contract-adjudicate`, `repo-continue`
- playbooks: `repository-contract-bootstrap`, `repository-development-continuation`
- skills: `contract-archaeology`, `development-authority-discovery`
- tools: `contract_bootstrap_state`, `development_authority_state`, `change_surface_state`, `development_continuation_state`, `native_gate_state`, `external_evidence_state`

Done condition: source smoke, installed `review-pack-smoke.py`, install/update lifecycle inventory and parity tests all require the same RC6 surface set.

### CL-003 — catalog/command exposure parity

State: `PARTIAL`.

New Playbooks/commands must be discoverable through the normal catalog/control surface without introducing a separate RC6 UI family.

### CL-009 — normative RC6 docs

State: `PARTIAL`.

Still required as stable operator/product contracts:

- Development Authority Map
- Development Continuation Packet and scope guard
- pre-registry change-surface derivation
- Native Gate Map and cloud/live boundary
- ExternalEvidenceManifestV1
- brownfield generic registry/adjudication lifecycle
- trusted EHA prestart architecture

### CL-010 — feature-plan status metadata

State: `PARTIAL`.

`docs/RC6-FEATURE-PLAN.md` still contains the historical header `PROPOSED FOR SCOPE ACCEPTANCE`. Authority is nevertheless unambiguous because `docs/RC6-SCOPE-ACCEPTANCE.md` records acceptance. Correct the stale header during the normative-doc pass; do not treat it as reopening scope.

### CL-011 — PR metadata

State: `PARTIAL`.

PR #111 description still describes only RC6-A/RC6-B. It must summarize RC6-A through RC6-F and the current cloud/live boundary.

## 6. Current handoff decision

Current decision: **CLOUD_TESTABILITY_REMAINING**.

Reason: the implementation core is hosted-green, but RC6-specific distribution/catalog/doc contracts are still repository-testable and have not all been closed. A 7/7 result from the existing matrix is necessary evidence, not permission to skip missing acceptance coverage.

`LIVE_HANDOFF_READY` is allowed only after:

1. CL-002, CL-003 and CL-009 are closed;
2. CL-010 and CL-011 metadata drift are repaired;
3. the resulting exact head passes the full hosted acceptance matrix;
4. no required repository/hosted RC6 gate remains unexecuted.

## 7. Next execution queue

Execute in this order:

1. wire RC6 commands/playbooks/skills/tools into root and installed smoke contracts;
2. update managed-file/install/update parity tests;
3. prove catalog exposure for `/repo-contract-bootstrap`, `/repo-contract-adjudicate`, `/repo-continue`;
4. write normative RC6 authority/continuation/gate/evidence contracts;
5. correct `RC6-FEATURE-PLAN.md` status metadata and PR #111 body;
6. run full exact-head hosted acceptance;
7. re-run final context-loss audit against `RC6-FEATURE-PLAN.md`;
8. only then move to read-only live dogfood on PII Parser and Aleph Rugent;
9. finally run fresh RC6 EHA on one release-stream exact SHA.

## 8. Active and archived RC6 documents

Active authority/current-state documents:

- `docs/RC6-FEATURE-PLAN.md` — accepted feature-scope authority
- `docs/RC6-SCOPE-ACCEPTANCE.md` — acceptance record
- `docs/RC6-IMPLEMENTATION-LEDGER.md` — current implementation status and queue

Archived planning/evidence inputs:

- `docs/archive/rc6/RC6-CURRENT-DEFECT-FIX-PLAN.md`
- `docs/archive/rc6/RC6-EXTERNAL-DEVELOPMENT-GAP-AUDIT.md`

The archived files remain evidence for why RC6 was designed as it was, but they no longer control implementation order or current status.
