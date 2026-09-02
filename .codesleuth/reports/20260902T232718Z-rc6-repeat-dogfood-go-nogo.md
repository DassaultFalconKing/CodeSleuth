---
reportType: live-dogfood-readiness
targetSha: 1de37c75251a1e0d9904cffdb82695e92e3fab23
provenance: c62-ae6da7d1b172
verdict: NO-GO
reviewId: 20260902T232718Z-1de37c75-c62
---

# RC6 repeat dogfood — independent go/no-go

- date: 2026-09-02T23:27:18Z
- target: `1de37c75251a1e0d9904cffdb82695e92e3fab23`
- dirty: not applicable (this report did not modify the RC6 candidate worktree)
- scope: independent re-resolve of hosted/identity readiness for a proposed repeat live dogfood on PR #111, without launching a new `/repo-continue`
- agent: Cursor session `ded0197c-2290-42dd-aa4f-a7e89ab4a8c6`
- reviewId: `20260902T232718Z-1de37c75-c62`
- ehaCampaignId: none
- provenance: `c62-ae6da7d1b172` (attribution metadata only)
- publication route: new file on append-only `reports`
- live-dogfood authority for this SHA: `.codesleuth/reports/20260902T204117Z-rc6-live-dogfood-repeat.md`

## Summary

Hosted exact-head identity on `1de37c75251a1e0d9904cffdb82695e92e3fab23` is confirmed: PR #111 head matches canonical run `33656390768` (`success`, 7/7 jobs), and the frozen foreign subjects have not moved. That is not permission to launch a fresh repeat dogfood. The same SHA already has an immutable live-dogfood FAIL at `20260902T204117Z`. A new campaign on `1de37c` cannot become `LIVE_DOGFOOD_ACCEPTABLE`. Status: **NO-GO** / `RC6_REPAIR_REQUIRED`.

## EHA / SIB status

- exact target SHA: `1de37c75251a1e0d9904cffdb82695e92e3fab23`
- SIB0: not run — claimable: no
- SIB1: not run — claimable: no
- SIB2: not run — claimable: no
- blocker finding IDs: live-dogfood Class A (undeclared positive path authority) and Class C (authority-contradiction reset) on the 20260902T204117Z report
- predecessor campaign: none (this is a derived readiness report, not an EHA campaign)
- successor campaign: none

This report does not start, amend, or transfer EHA/SIB evidence.

## Verdict-transfer boundary

The 20260902T204117Z report is the live-dogfood authority for exact `1de37c...`. This file is a derived readiness/go-no-go view. It does not rewrite, rehabilitate, or replace that FAIL.

`b56ae39d8b98e1a67f933e03544c83869c3377f4` remains a separate historical FAIL. Its verdict does not transfer to `1de37c`. The `1de37c` FAIL likewise does not transfer to any later SHA.

## Independent identity re-resolve

Recorded 2026-09-02T22:26Z–23:27Z via `gh`, without checking out or editing PR #111.

| Probe | Result |
|---|---|
| `gh pr view 111` `headRefOid` | `1de37c75251a1e0d9904cffdb82695e92e3fab23` |
| PR URL | https://github.com/DassaultFalconKing/CodeSleuth/pull/111 |
| `gh run view 33656390768` `headSha` | `1de37c75251a1e0d9904cffdb82695e92e3fab23` |
| run `conclusion` / `status` | `success` / `completed` |
| run URL | https://github.com/DassaultFalconKing/CodeSleuth/actions/runs/33656390768 |
| job count / failed jobs | 7 / 0 |
| `PII_PARSER` `main` | `9f226013f37c3ca62f8f8a4f2845370e2350f639` |
| `Aleph_Rugent` `main` | `bf1320a523fb7cf01953d03426403eb049fe5b1a` |
| post-green PR head drift | none: PR head still equals hosted `headSha` |
| PR body "Current tracked candidate" | stale prose: still names `b56ae39d8b98e1a67f933e03544c83869c3377f4` |

Hosted jobs observed successful on that exact SHA:

1. Graphify enabled runtime / Python 3.12 / Ubuntu
2. Python 3.10 / ubuntu-latest
3. Durable state / context graph
4. TUI visual regression / Ubuntu
5. Python 3.12 / windows-latest
6. Python 3.10 / windows-latest
7. Python 3.12 / ubuntu-latest

## Entry-gate table

| Gate | Independent result |
|---|---|
| Hosted exact-head readiness | PASS |
| Current-head identity | PASS |
| Post-green head drift | NONE |
| PII target drift | NONE |
| Aleph target drift | NONE |
| Known first-wave repair regressions in hosted CI | COVERED (hosted 7/7 on this SHA) |
| PR body vs Git ref | STALE PROSE (not a dogfood blocker) |
| Repeat live dogfood as a fresh campaign | NO-GO |
| Existing live dogfood on `1de37c` | FAIL — `RC6_REPAIR_REQUIRED` |

```text
RC6_REPEAT_DOGFOOD = NO-GO as a fresh campaign
confidence = HIGH
```

The A/B freeze (same PII, same Aleph, new CodeSleuth SHA) is valid. It already served the 20260902T204117Z campaign.

## Findings

### high: fresh repeat dogfood proposed after an exact-SHA live FAIL
- location: proposed operator decision against PR #111 / `1de37c75251a1e0d9904cffdb82695e92e3fab23`
- evidence: [20260902T204117Z-rc6-live-dogfood-repeat.md](https://github.com/DassaultFalconKing/CodeSleuth/blob/reports/.codesleuth/reports/20260902T204117Z-rc6-live-dogfood-repeat.md) tested the same SHA, produced continuation packets and gate maps, and recorded Class A and Class C as generic release blockers. PII_PARSER and Aleph_Rugent were both FAIL as a composition. Target mutation: none.
- recommendation: do not launch another `/repo-continue` on `1de37c` as if untested. Repair Class A and Class C on a new branch from this frozen SHA.

### high: Class A — undeclared positive path authority (already reproduced)
- location: PII packet `DCP-20260902202502-9f226013f37c-03df2d90`; `development_continuation_state_scope_guard`
- evidence: live-dogfood report stored `pathScopeAuthority=DECLARED` and `allowedPaths` copied from derived change-surface seeds. Guard returned `IN_SCOPE` for `api_model_health.py` where repository authority does not declare a positive allowlist.
- recommendation: fail closed to `NOT_DECLARED` / `SCOPE_AUTHORITY_UNPROVEN` unless repository evidence declares the allowlist. Do not promote derived seeds into mutation authority.

### high: Class C — authority contradiction reset (already reproduced)
- location: PII maps `DAM-20260902201904-9f226013f37c-eed6c502`, `DAM-20260902201950-9f226013f37c-52638083`, then replacement `DAM-20260902202017-9f226013f37c-65191f5f`
- evidence: two fail-closed loads (`CANONICAL_PLANNING_AUTHORITY` vs `HISTORICAL_ARCHIVE`; `ACTIVE_IMPLEMENTATION_SCOPE` vs `FORBIDDEN_COMPETING_AUTHORITY`) were followed by `development_authority_state_start` overwrite and packet emission without operator adjudication.
- recommendation: latch contradiction; do not let `start()` mint a successor PASS map for the same continuation.

### medium: PR prose drift
- location: GitHub PR #111 body, section "Current tracked candidate"
- evidence: body names `b56ae39d8b98e1a67f933e03544c83869c3377f4` / run `33628677158` while `headRefOid` is `1de37c...` / run `33656390768`.
- recommendation: update PR body after the next exact candidate exists, not by rewriting Git identity to match stale prose.

## Requested R1–R13 vs already-recorded 1de37c evidence

This table is a read of the 20260902T204117Z live-dogfood report. It is not a new sweep.

| ID | Surface | 1de37c recorded result |
|---|---|---|
| R1 | Unicode / C-quoted paths | not reproduced |
| R2 | undeclared positive path authority | FAIL (Class A) |
| R3 | mutually exclusive semantic roles | FAIL (Class C) |
| R4 | earliest unresolved stop-gate | not the fail focus; not claimed PASS |
| R5 | structural change-surface recall | reached (`CSM-...437d8343`, `CSM-...44662947`) |
| R6 | nonexistent / future seeds | not reproduced in stored packets |
| R7 | fresh-step isolation reporting | not reproduced on PII |
| R8 | read-only boundary | not reproduced; targets unmodified |
| R9 | DevelopmentContinuationPacket | reached, contaminated by Class A |
| R10 | `scope_guard` | FAIL (Class A) |
| R11 | NativeGateMap | reached (`NGM-...8bad8913`, `NGM-...717daf17`) |
| R12 | ExternalEvidenceManifestV1 | not the fail focus; not claimed PASS |
| R13 | runtime ↔ repository contradiction | FAIL (Class C) |

R9–R12 were the stated reason to launch. On `1de37c` they were reached. That is why Class A/C are product defects rather than “did not get there”.

## Paths inspected

- GitHub PR #111 JSON (`headRefOid`, body, commits list)
- GitHub Actions run `33656390768` JSON (conclusion, `headSha`, seven jobs)
- `repos/DassaultFalconKing/PII_PARSER/commits/main`
- `repos/DassaultFalconKing/Aleph_Rugent/commits/main`
- `.codesleuth/reports/20260902T204117Z-rc6-live-dogfood-repeat.md` on `reports`
- `.codesleuth/reports/INDEX.md` on `reports`
- `docs/RC6-LIVE-DOGFOOD-RUNBOOK.md` from the previously materialized `1de37c` candidate tree (read-only)

## Checks run

- `gh pr view 111 --repo DassaultFalconKing/CodeSleuth` — PASS (identity)
- `gh run view 33656390768 --repo DassaultFalconKing/CodeSleuth` — PASS (`success`, exact SHA, 7/7)
- `gh api repos/DassaultFalconKing/PII_PARSER/commits/main` — PASS (SHA match)
- `gh api repos/DassaultFalconKing/Aleph_Rugent/commits/main` — PASS (SHA match)
- read published 20260902T204117Z live-dogfood FAIL — PASS (exists on `reports`, blob reachable)
- `/repo-continue` on PII or Aleph — **not run**
- hosted acceptance — **not re-executed**; existing run `33656390768` was inspected
- EHA/SIB — **not run**

## Recommendations

- Do not launch another live dogfood on `1de37c75251a1e0d9904cffdb82695e92e3fab23`.
- Do not start EHA/SIB0/SIB1/SIB2 on this SHA.
- Do not edit RC6 in place to flip the existing FAIL to PASS.
- Keep `1de37c` frozen as a failed live-dogfood subject.
- Repair Class A and Class C tests-first on a new branch from this SHA, then: new exact SHA → hosted 7/7 → new dogfood.
- Update PR #111 body only as bookkeeping after the next exact candidate is identified.

Honest next path:

```text
failed exact 1de37c
    ↓
repair branch (Class A + Class C, tests-first)
    ↓
new SHA
    ↓
hosted 7/7
    ↓
new dogfood
    ↓
only then EHA → SIB0 → SIB1
```

## Limitations

- This session did not re-materialize `/repo-continue`, did not re-open OpenCode sessions `ses_f9c3a6932ffeMj42byjG8LtJel` / `ses_f9c3209a8ffeuhPMAYHjmNh3l4`, and did not re-hash runtime command blobs.
- Class A/C details are cited from the 20260902T204117Z report, not re-derived from packet files in this session.
- Local Cursor canvas `rc6-repeat-dogfood-go-nogo.canvas.tsx` is a UI projection only and is not repository authority.
- PR #111 commit list was retrieved but not exhaustively audited beyond head OID vs hosted SHA.
- No refs, tags, SIB state, or RC6 application files were changed by this report.
