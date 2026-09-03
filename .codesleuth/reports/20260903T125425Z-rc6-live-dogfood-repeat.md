---
reportType: live-dogfood-repeat
targetSha: 0ae58cb2dc06e3d06e0839040f58d5a853f920ee
provenance: c62-4f866b9207fe
verdict: LIVE_DOGFOOD_ACCEPTABLE
reviewId: 20260903T125425Z-0ae58cb2-c62
---

# RC6 live-dogfood repeat — 0ae58cb (Class A/C repair)

- date: 2026-09-03T12:54:25Z
- tested CodeSleuth candidate: `0ae58cb2dc06e3d06e0839040f58d5a853f920ee`
- actual materialized/runtime candidate identity: same SHA; command blob `9e3bf00a6607ed181b63619c718f708b847813c6` (`pack/.opencode/commands/repo-continue.md`); continuation tool blob `96ace0de492fac8b11795f7d1bb8c24462f6931b`; authority tool blob `ccdc57e894c737ae8c81a8e72a2b35c8e4d9917c`
- hosted acceptance: run `33696889477`, exact `headSha=0ae58cb2dc06e3d06e0839040f58d5a853f920ee`, 7/7 PASS
- prior immutable FAIL on unrepaired SHA: `.codesleuth/reports/20260902T204117Z-rc6-live-dogfood-repeat.md` tested `1de37c75251a1e0d9904cffdb82695e92e3fab23` — **not rewritten**; verdict transfer from that FAIL is **forbidden**
- prior readiness NO-GO on `1de37c`: `.codesleuth/reports/20260902T232718Z-rc6-repeat-dogfood-go-nogo.md`
- repair lineage: PR #116 FF-merged into `feature/rc6-eha-brownfield-bootstrap`; PR #111 head now `0ae58cb...`
- foreign subjects (unchanged): PII_PARSER `9f226013f37c3ca62f8f8a4f2845370e2350f639`; Aleph_Rugent `bf1320a523fb7cf01953d03426403eb049fe5b1a`
- provenance: `c62-4f866b9207fe` (attribution metadata only)
- analysis: **LIVE_DOGFOOD_ACCEPTABLE** (Class A/C closed; findings below do not reopen those classes)
- publication route: new file on append-only `reports`

## Verdict-transfer boundary

The 20260902T204117Z report remains a valid historical FAIL for exact `1de37c...`. This campaign materializes and executes independent candidate `0ae58cb...`. PASS/FAIL does not transfer across SHAs.

## Identity proof recorded before this dogfood

```text
codesleuthCandidateSha            = 0ae58cb2dc06e3d06e0839040f58d5a853f920ee
actualMaterializedCandidateSha    = 0ae58cb2dc06e3d06e0839040f58d5a853f920ee
actualDistributionRoot            = C:\Users\testc\AppData\Local\Temp\codesleuth-rc6-dogfood-0ae58cb-20260903T142903\CodeSleuth-candidate
actualRuntimeConfigRoot PII       = ...\runtime-pii-official
actualRuntimeConfigRoot Aleph     = ...\runtime-aleph-official
actualCommandSurfaceIdentity      = 9e3bf00a6607ed181b63619c718f708b847813c6
continuationToolBlob              = 96ace0de492fac8b11795f7d1bb8c24462f6931b
authorityToolBlob                 = ccdc57e894c737ae8c81a8e72a2b35c8e4d9917c
hostedAcceptanceRunId             = 33696889477
hostedAcceptanceResult            = 7/7 PASS
OPENCODE_CONFIG_DIR               = per-target official runtime mirror
OPENCODE_DISABLE_PROJECT_CONFIG   = 1
OPENCODE_CONFIG                   = unset
```

Launcher: candidate helper `scripts/eha_opencode_runtime.py` prepared official mirrors. Invoked surface: `opencode run --command repo-continue --agent build --auto --format json` with the env above. Worktree `git hash-object` of runtime `commands/repo-continue.md` equals HEAD blob `9e3bf00a...`.

## Host identities

Windows NT 10.0.26200; PowerShell; Git; Python; Bun; OpenCode 1.18.25.

## Target A — PII_PARSER

### Identity

- repository: `DassaultFalconKing/PII_PARSER`
- exact SHA before/after: `9f226013f37c3ca62f8f8a4f2845370e2350f639`
- tracked porcelain: empty (only untracked `.opencode/state/...` from durable tools)
- session: `ses_f98bbd038ffeQffWnOB4e0hDrK`
- process exit: `EXIT=0`
- launch UTC: `2026-09-03T12:35:02Z`

### Durable ids

| Artifact | Id |
|---|---|
| Authority map | `DAM-20260903123635-9f226013f37c-06b0bc8c` (single map; load PASS) |
| Contradiction latch | **absent** |
| Change surface | `CSM-20260903123800-9f226013f37c-33b4ea23` |
| Native gates | `NGM-20260903123812-9f226013f37c-ec382215` |
| Continuation packet | `DCP-20260903124113-9f226013f37c-57d9261d` |
| Isolation events | `DCI-097daef9...`, `DCI-91df3acb...`, `DCI-6a02ac6b...`, `DCI-9757b1cc...`, `DCI-0b737cf0...`, `DCI-726607c1...` (bound on packet) |

### Class A — positive path authority fabrication — CLOSED

Repository does not declare a positive mutation allowlist. Packet stored:

```text
pathScopeAuthority=NOT_DECLARED
allowedPaths=[]
```

Direct product `development_continuation_state_scope_guard` on `api_model_health.py` → **`SCOPE_AUTHORITY_UNPROVEN`** (was `IN_SCOPE` on `1de37c`).

Controller briefly attempted non-empty allowlists / wrong authority mode during assembly; `save_packet` rejected those attempts. Final durable packet is fail-closed.

### Class C — authority contradiction reset — CLOSED

Single authority map. No `contradiction-latch.json`. No observed `AUTHORITY CONTRADICTION LATCHED` → discard → clean restart → PASS path. Load of the one map succeeded without operator supersession.

### Finding (non-Class-A/C)

`acceptedPredecessors` stores a conceptual label (“Pre-2026-08-14 shipped baselines…”) rather than a concrete repository-path/SHA predecessor. Packet still validates; quality note only.

## Target B — Aleph_Rugent

### Identity

- repository: `DassaultFalconKing/Aleph_Rugent`
- exact SHA before/after: `bf1320a523fb7cf01953d03426403eb049fe5b1a`
- porcelain before/after: empty (including tracked `.opencode` metadata)
- session: `ses_f98b4fe9fffekYyeu8lFzmGP63`
- process exit: `EXIT=0`
- launch UTC: `2026-09-03T12:42:33Z`

### Tracked `.opencode` metadata

| File | Before | After |
|---|---|---|
| `.opencode/package.json` git blob | `718aed1e8ec735feccac51030308e0b63072b318` | same |
| `.opencode/package-lock.json` git blob | `538be4c1d1d9ac534fdaf4b348825a474ba000b0` | same |

Class D historical mutation **not reproduced**.

### Durable ids

| Artifact | Id |
|---|---|
| Authority map | `DAM-20260903124355-bf1320a523fb-fc4a97af` (single map; load PASS) |
| Contradiction latch | **absent** |
| Change surface | `CSM-20260903124633-bf1320a523fb-7f01eab8` |
| Native gates | `NGM-20260903124722-bf1320a523fb-3f060e34` |
| Continuation packet | `DCP-20260903125220-bf1320a523fb-0ebe882c` |
| Isolation events | six `DCI-*` ids bound on packet |

### Class A — CLOSED (repository-declared allowlist)

`docs/session-packets/S09.md` explicitly lists Allowed paths matching the crate file literals and `docs/baseline/`. Packet:

```text
pathScopeAuthority=DECLARED
allowedPaths=[
  crates/rag-contracts/src/lib.rs,
  crates/rag-core/src/lib.rs,
  crates/rag-infra/src/lib.rs,
  crates/rag-tools/src/lib.rs,
  crates/rag-models/src/lib.rs,
  docs/baseline/,
  docs/session-handoffs/S09.md
]
```

Exact allowlist files are **not** a pure copy of derived change-surface seeds (`allExactInDerived=False`). Scope guard: declared crate path → `IN_SCOPE`; undeclared `crates/graph/src/lib.rs` / `README.md` → `UNDECLARED`; `docs/baseline/hybrid-retrieval.json` → `IN_SCOPE` via directory pattern.

### Finding (non-Class-A)

`docs/session-handoffs/S09.md` is not listed under S09 “Allowed paths” (S09 names `docs/session-packets/S09.md` as scope source and `crates/*/tests/` among allowed). Mild over-declaration / incomplete mirror of the session allowlist — not surface-seed fabrication.

### Class C — CLOSED

No latch; no contradiction-reset restart observed.

## Five historical failure classes on 0ae58cb

| Class | Shape on unrepaired `1de37c` | Result on `0ae58cb` | Notes |
|---|---|---|---|
| A positive path fabrication | PII `DECLARED` + invented allowlist + `IN_SCOPE` | **CLOSED** | PII `NOT_DECLARED` + `SCOPE_AUTHORITY_UNPROVEN`; Aleph DECLARED from S09 |
| B fresh-subagent ordering | UNPROVEN after parent execution | **not fail focus** | both packets bind `STEP_ISOLATION_UNPROVEN` events |
| C contradiction reset | discard failed map, start corrected map | **CLOSED** | single maps; no latch; no reset path |
| D read-only runtime | Aleph pin rewrite | **not reproduced** | package blobs unchanged |
| E path semantics | conceptual/member strings | **acceptable** | repository paths / directory descendants work |

## R1–R13 matrix (this campaign)

| Id | Capability | PII | Aleph | Notes |
|---|---|---|---|---|
| R1 | Unicode / path framing | PASS | PASS | surfaces derived without path corruption |
| R2 | exact target identity | PASS | PASS | HEAD frozen; porcelain tracked-clean |
| R3 | planning/authority capture | PASS | PASS | durable DAM ids |
| R4 | active scope selection | PASS | PASS | W-1 / S09 scopes recorded |
| R5 | change-surface non-authority | PASS | PASS | CSM present; not used as undeclared mutation authority |
| R6 | isolation honesty | PASS | PASS | UNPROVEN recorded and bound |
| R7 | continuation packet durability | PASS | PASS | DCP saved; EXIT=0 |
| R8 | read-only target boundary | PASS | PASS | no tracked mutation |
| R9 | pathScopeAuthority honesty | PASS | PASS | NOT_DECLARED vs S09-DECLARED |
| R10 | deterministic scope_guard | PASS | PASS | fail-closed when undeclared; IN_SCOPE only when declared |
| R11 | NativeGateMap honesty | PASS | PASS | maps reached; no false PASS of unexecuted gates claimed here |
| R12 | ExternalEvidenceManifestV1 | NOT EXERCISED | NOT EXERCISED | no external-evidence dir observed; not claimed PASS |
| R13 | runtime/repository contradiction | PASS | PASS | Class C latch path unused; Class D not reproduced |

## Overall verdict

**LIVE_DOGFOOD_ACCEPTABLE** on exact candidate `0ae58cb2dc06e3d06e0839040f58d5a853f920ee`.

Hosted 7/7 (`33696889477`) remains real for this SHA. Live `/repo-continue` on both frozen foreign subjects:

1. no longer promotes undeclared change-surface seeds into `pathScopeAuthority=DECLARED` / unauthorized `IN_SCOPE` (Class A closed);
2. no longer replaces a contradicted authority map via silent `start()` reset (Class C closed);
3. leaves foreign tracked trees unmodified.

Findings that do **not** reopen Class A/C repair:

- PII conceptual `acceptedPredecessors` label;
- Aleph allowlist includes `docs/session-handoffs/S09.md` beyond the S09 Allowed-paths list;
- R12 external-evidence path not exercised in this automated run.

PII_PARSER: **PASS** (with predecessor-quality finding). Aleph_Rugent: **PASS** (with mild allowlist-fidelity finding). Target mutation: **none**.

SIB0/SIB1/SIB2: **NOT RUN**. EHA: **NOT RUN**. Refs/tags: **not moved**. Historical `1de37c` FAIL report: **not rewritten**.
