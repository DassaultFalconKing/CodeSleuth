# RC6 Implementation Ledger

Status: **PRE-LIVE FINALIZATION — FINAL EXACT-HEAD HOSTED ACCEPTANCE REQUIRED**

Scope authority: `docs/RC6-FEATURE-PLAN.md`, accepted by `docs/RC6-SCOPE-ACCEPTANCE.md`.

Final pre-live context audit: `docs/RC6-CONTEXT-LOSS-AUDIT.md`.

Live procedure after cloud closure: `docs/RC6-LIVE-DOGFOOD-RUNBOOK.md`.

This Markdown ledger is the human-readable RC6 execution/status surface. It does not transfer acceptance between Git SHAs and does not outrank executable tests, normative contracts or durable EHA evidence.

## 1. Exact evidence history

Last fully hosted-accepted implementation head before Wave 6 closure:

`34546d19bc9fcf77c3f0a4ec408c3e9c19ab19ad`

Canonical hosted acceptance:

- workflow: `CodeSleuth acceptance`
- run: `33560728115`
- result: **PASS — 7/7**
- exact checkout SHA: `34546d19bc9fcf77c3f0a4ec408c3e9c19ab19ad`

That PASS proves only that literal historical SHA.

Subsequent Wave 6 changes added distribution/catalog parity, deterministic fixtures, normative documentation and live-handoff contracts. Their intermediate hosted runs were intentionally used as RED/GREEN evidence rather than treated as acceptance transfer.

Notable final pre-live diagnostic run:

- exact SHA `645aedb8364977ebb3b227b3af35e13ed440b0f5`
- run `33564295158`
- Durable state/context graph: PASS
- TUI visual regression: PASS
- Graphify enabled runtime: PASS
- all four Python jobs shared one remaining failure in `test_eha_operator_uses_explicit_refit_axes`
- root cause: the rewritten EHA operating guide retained semantic/delivery axes but lost the explicit positive-evidence rule for `SUPERSEDED`
- repaired by restoring `SUPERSEDED` positive current coverage evidence and `RETIRED` explicit-current-authority semantics

The final candidate is the literal head produced by this ledger update. It is not accepted until its own complete hosted matrix is green.

## 2. Status vocabulary

Use only:

- `CLOUD_VERIFIED` — required repository/hosted behavior has passed applicable tests on recorded exact evidence.
- `IMPLEMENTED_PENDING_FINAL_HEAD` — implementation/contract is present, but final literal candidate acceptance has not completed.
- `CLOUD_TESTABILITY_REMAINING` — at least one mandatory repository/hosted gate remains unclosed.
- `LIVE_PENDING` — final cloud boundary is closed and only live-host acceptance remains.
- `LIVE_VERIFIED` — required live-host dogfood passed.
- `DEFERRED` — explicitly outside RC6.

## 3. Executive state

| Slice | State | Evidence / remaining boundary |
| --- | --- | --- |
| RC6-0 defect closure | `IMPLEMENTED_PENDING_FINAL_HEAD` | all identified defects closed; final exact-head hosted matrix pending |
| RC6-A deterministic EHA authority | `IMPLEMENTED_PENDING_FINAL_HEAD` | trusted prestart/controller/core behavior covered; final matrix pending |
| RC6-B brownfield contract bootstrap | `IMPLEMENTED_PENDING_FINAL_HEAD` | exact blob-bound bootstrap + human adjudication + generic registry core |
| RC6-C Development Authority Map | `IMPLEMENTED_PENDING_FINAL_HEAD` | typed authority state + separate deterministic fixtures |
| RC6-D continuation packet / scope guard | `IMPLEMENTED_PENDING_FINAL_HEAD` | deterministic change surface + nativeGates/authorityEvidence projections + guard |
| RC6-E Native Gate Map / cloud boundary | `IMPLEMENTED_PENDING_FINAL_HEAD` | cloud/live/operator gate classes and handoff state implemented |
| RC6-F ExternalEvidenceManifestV1 | `IMPLEMENTED_PENDING_FINAL_HEAD` | exact-SHA/freshness/secret-safe append-only live evidence boundary |
| Wave 6 distribution/docs | `IMPLEMENTED_PENDING_FINAL_HEAD` | source/install smoke parity, catalog exposure, normative docs, fixtures closed |
| Wave 7 hosted exact-head gate | `CLOUD_TESTABILITY_REMAINING` | one fresh 7/7 required on this final tracked head |
| Live dogfood | `BLOCKED UNTIL FINAL 7/7` | runbook prepared; PII Parser + Aleph Rugent remain read-only live acceptance |

## 4. Context-loss register

All implementation omissions previously discovered during RC6 context-loss review are now closed in the tracked tree.

| ID | Requirement | Disposition |
| --- | --- | --- |
| CL-001 | replace prose/source-layout EHA behavior assertions | closed |
| CL-002 | source/install smoke parity for RC6 surfaces | closed |
| CL-003 | catalog/command exposure parity | closed |
| CL-004 | separate layered TODO/worklog Fixture A | closed |
| CL-005 | separate waypoint/session Fixture B | closed |
| CL-006 | deterministic pre-registry change-surface derivation | closed |
| CL-007 | bounded `nativeGates` continuation projection | closed |
| CL-008 | bounded `authorityEvidence` continuation projection | closed |
| CL-009 | normative RC6 authority/continuation/gate/evidence docs | closed for live-readiness contract |
| CL-010 | feature-plan accepted/frozen status metadata | closed |
| CL-011 | PR body reflects RC6-A through RC6-F and handoff boundary | GitHub metadata update; no Git identity effect |
| CL-012 | final context-loss audit against frozen feature plan | closed by `RC6-CONTEXT-LOSS-AUDIT.md` |

No additional cloud-testable implementation omission was found in the final pre-live audit.

## 5. Distribution and product-surface closure

Canonical root `smoke.py` and installed `pack/.opencode/bin/review-pack-smoke.py` now require the same RC6 surface family.

Required commands include:

- `repo-contract-bootstrap`
- `repo-contract-adjudicate`
- `repo-continue`

Required Playbooks include:

- `repository-contract-bootstrap`
- `repository-development-continuation`

Required Skills include:

- `contract-archaeology`
- `development-authority-discovery`

Required bounded tools include:

- `contract_bootstrap_state`
- `development_authority_state`
- `change_surface_state`
- `development_continuation_state`
- `native_gate_state`
- `external_evidence_state`

Clean-install/managed-file and catalog tests cover the same distributed capability set. RC6 did not introduce a separate UI family or execution runtime.

## 6. Normative contract closure

Current RC6 live-readiness authority is distributed across:

- `docs/DEVELOPMENT-CONTINUATION-CONTRACT.md`
- `docs/GITHUB-EHA-BRIDGE.md`
- `docs/EHA-OPERATING-PLAYBOOK.md`
- `docs/RC6-FEATURE-PLAN.md`
- `docs/RC6-SCOPE-ACCEPTANCE.md`
- `docs/RC6-CONTEXT-LOSS-AUDIT.md`
- `docs/RC6-LIVE-DOGFOOD-RUNBOOK.md`

The Development Continuation contract covers authority mapping, continuation packet semantics, pre-registry change surface, scope guard, Native Gate Map/cloud-live boundary, ExternalEvidenceManifestV1 and brownfield lifecycle.

The EHA documents cover deterministic trusted prestart and the separate ordinary `model_started` compatibility path.

A broader root README/i18n command-table refresh may be performed before numbered release publication. It is not an authority dependency for live dogfood. Any later tracked documentation change necessarily creates a new candidate SHA and must receive fresh hosted acceptance before release promotion.

## 7. Current handoff decision

Current decision is still:

```text
CLOUD_TESTABILITY_REMAINING
```

There is exactly one remaining cloud gate: **complete canonical hosted acceptance on the literal final tracked head created by this update**.

Transition is legal only as:

```text
final tracked RC6 pre-live head
-> hosted acceptance 7/7 on that exact SHA
-> no subsequent tracked edits
-> LIVE_HANDOFF_READY
-> read-only PII Parser dogfood
-> read-only Aleph Rugent dogfood
-> LIVE_VERIFIED when both satisfy RC6 criteria
-> select exact release-stream candidate
-> fresh hosted acceptance + fresh EHA SIB0/SIB1/SIB2
```

A green ancestor, tree similarity or partial final matrix does not satisfy this gate.

## 8. Live dogfood acceptance

After `LIVE_HANDOFF_READY`, follow `docs/RC6-LIVE-DOGFOOD-RUNBOOK.md`.

PII Parser must demonstrate evidence-bound selection of current planning authority, exclusion of superseded roadmaps, next critical-path scope and separation of cloud/live proof without source edits.

Aleph Rugent must demonstrate Orientation/session/handoff/Waypoint/gate authority reconstruction, active-scope selection, predecessor/required-reading preservation, adjacent-track rejection and registryless brownfield handling without source edits.

No repository-specific CodeSleuth adapter may be added to make either dogfood pass.

## 9. Active and archived RC6 documents

Active authority/current-state documents:

- `docs/RC6-FEATURE-PLAN.md`
- `docs/RC6-SCOPE-ACCEPTANCE.md`
- `docs/RC6-IMPLEMENTATION-LEDGER.md`
- `docs/RC6-CONTEXT-LOSS-AUDIT.md`
- `docs/RC6-LIVE-DOGFOOD-RUNBOOK.md`

Archived historical inputs:

- `docs/archive/rc6/RC6-CURRENT-DEFECT-FIX-PLAN.md`
- `docs/archive/rc6/RC6-EXTERNAL-DEVELOPMENT-GAP-AUDIT.md`

The archive explains why RC6 exists; it does not control current execution.
