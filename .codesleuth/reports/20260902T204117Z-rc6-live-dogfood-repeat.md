---
reportType: live-dogfood-repeat
targetSha: 1de37c75251a1e0d9904cffdb82695e92e3fab23
provenance: c57-e88c5c858757
verdict: FAIL
reviewId: 20260902T204117Z-1de37c75-c57
---

# RC6 live-dogfood repeat — 1de37c

- date: 2026-09-02T20:41:17Z
- tested CodeSleuth candidate: `1de37c75251a1e0d9904cffdb82695e92e3fab23`
- actual materialized/runtime candidate identity: same SHA; command blob `e5cc9eff64d5cc5d6fafd12a501ebbb45ff4f690` (`pack/.opencode/commands/repo-continue.md`); continuation tool blob `93e2d3796dfe5b07844dd286c80f58dc05cd7c0a`
- hosted acceptance: run `33656390768`, exact `headSha=1de37c75251a1e0d9904cffdb82695e92e3fab23`, 7/7 PASS
- previous failed report: `.codesleuth/reports/20260902T180850Z-rc6-live-dogfood-repeat.md` tested `b56ae39d8b98e1a67f933e03544c83869c3377f4` / hosted `33628677158`
- current run tests `1de37c...`
- verdict transfer = **forbidden**
- foreign subjects: PII_PARSER `9f226013f37c3ca62f8f8a4f2845370e2350f639`; Aleph_Rugent `bf1320a523fb7cf01953d03426403eb049fe5b1a`
- provenance: `c57-e88c5c858757` (attribution metadata only)
- analysis: **FAIL — RC6_REPAIR_REQUIRED**
- publication route: new file on append-only `reports`

## Verdict-transfer boundary

The 20260902T180850Z report is a valid historical FAIL for exact `b56ae39...`. It is not a verdict against `1de37c...`. This run materialized and executed `1de37c...` independently.

## Provenance of the previous FAIL (b56ae39 after 1de37c existed)

Classification: **STALE_TEST_ORCHESTRATION** (not `CODESLEUTH_CANDIDATE_RESOLUTION_DEFECT`).

Evidence:

| Probe | Result |
|---|---|
| `1de37c...` commit time | 2026-09-02 18:40:38 +0200 |
| hosted 7/7 for `1de37c...` | run `33656390768` completed 2026-09-02T16:45:14Z |
| FAIL-run install | `runtime-pii/review-pack.json` `installedAt=2026-09-02T17:36:28Z`, `source.commit=b56ae39...`, `source.ref=null` |
| FAIL-run checkout | `C:\Users\testc\AppData\Local\Temp\codesleuth-rc6-repeat-bf279c6aa1424ed5b8a9f193cab5f7e7\CodeSleuth` detached `b56ae39...` |
| FAIL-run `/repo-continue` blob | SHA-256 `6767EFD4...` matches b56 pack, not 1de37c (`BFC27FE6...`) |
| FAIL report itself | recorded PR #111 head `1de37c...` as navigation metadata while testing detached `b56ae39...` |
| review provenance sidecar | `headSha=b56ae39...`, review `20260902180700-b56ae39d8b98-1Gc6Lw9k-d5546d1e` |

The product did not resolve the wrong GitHub branch head. The dogfood harness/operator froze and installed detached `b56ae39...` after `1de37c...` already existed.

`b56ae39...` is an ancestor of `1de37c...`. The interval contains PR #114 live-dogfood repairs (`02e23fea` tests-first through `f6f67348`) plus PR #115 TUI sync. Those repairs are in the tree that this run actually executed.

## Identity proof recorded before this dogfood

```text
codesleuthCandidateSha            = 1de37c75251a1e0d9904cffdb82695e92e3fab23
actualMaterializedCandidateSha    = 1de37c75251a1e0d9904cffdb82695e92e3fab23
actualDistributionRoot            = C:\Users\testc\AppData\Local\Temp\codesleuth-rc6-dogfood-1de37c75-20260902T184913Z\CodeSleuth-candidate
actualRuntimeConfigRoot PII       = ...\runtime-pii-official
actualRuntimeConfigRoot Aleph     = ...\runtime-aleph-official
actualCommandSurfaceIdentity      = e5cc9eff64d5cc5d6fafd12a501ebbb45ff4f690
hostedAcceptanceRunId             = 33656390768
hostedAcceptanceResult            = 7/7 PASS
OPENCODE_CONFIG_DIR               = per-target official runtime mirror
OPENCODE_DISABLE_PROJECT_CONFIG   = 1
OPENCODE_CONFIG                   = unset
```

Launcher: candidate `pack/.opencode/bin/opencode-review.ps1` helper `scripts/eha_opencode_runtime.py` prepared the mirrors. Invoked surface: `opencode run --command repo-continue --agent build --auto` with the env above. Worktree `git hash-object` of runtime `commands/repo-continue.md` equals HEAD blob `e5cc9eff...`.

## Host identities

Windows NT 10.0.26200; PowerShell 7.7.0-preview.4 (and Windows PowerShell 5.1.26100 for some wrappers); Git 2.55.0.windows.5; Python 3.14.6; Node v26.3.0; Bun 1.4.0; OpenCode 1.18.25.

## Target A — PII_PARSER

### Identity

- repository: `DassaultFalconKing/PII_PARSER`
- exact SHA before/after: `9f226013f37c3ca62f8f8a4f2845370e2350f639`
- porcelain before/after: empty (`git status --porcelain=v1 --untracked-files=all`)
- session: `ses_f9c3a6932ffeMj42byjG8LtJel`
- disposable clone: `...\PII_RUN2`

### Durable ids

| Artifact | Id |
|---|---|
| Authority maps | `DAM-20260902201904-9f226013f37c-eed6c502` (contradiction); `DAM-20260902201950-9f226013f37c-52638083` (contradiction); `DAM-20260902202017-9f226013f37c-65191f5f` (used) |
| Change surface | `CSM-20260902202119-9f226013f37c-437d8343` (`DERIVED_NON_AUTHORITATIVE`) |
| Native gates | `NGM-20260902202133-9f226013f37c-8bad8913` (`CLOUD_TESTABILITY_REMAINING`, all `UNEXECUTED`) |
| Continuation packet | `DCP-20260902202502-9f226013f37c-03df2d90` |
| Isolation events | `DCI-09a09f42...` capture-target; `DCI-ec493a39...` resolve-authority; `DCI-0496f8b9...` select-active-scope; `DCI-99f49a1c...` map-change-surface; `DCI-23a579f8...` map-native-gates; `DCI-a195919b...` emit-continuation-packet |

Isolation events: `targetSha=9f226013...`, `outcome=STEP_ISOLATION_UNPROVEN`, `recordedAt` 20:18:49Z–20:19:02Z, **before** first `development_authority_state_start` at 20:19:04Z. Packet binds those event ids. Loader returned them. Class B ordering on this PII run is satisfied.

### Class A — positive path authority fabrication — REPRODUCED

Repository authority does not declare a positive mutation allowlist. Packet stored:

```text
pathScopeAuthority=DECLARED
allowedPaths=[api_model_health.py, api_workers.py, worker_registry.py, auth.py, security.py, api_discovery.py, app.py]
```

Those paths match derived change-surface seeds, not a declared allowlist.

Direct product `development_continuation_state_scope_guard`:

| Path | Actual | Expected |
|---|---|---|
| `api_model_health.py` | `IN_SCOPE` | `SCOPE_AUTHORITY_UNPROVEN` |
| `pipeline.py` | `UNDECLARED` | fail-closed non-authorization |
| `docs/archive/plan_docling_fix_FU-1_done.md` | `ADJACENT_TRACK` via `docs/archive/` | directory descendant semantics (this part is correct) |
| `docs/BACKLOG.md` | `FORBIDDEN_BY_ACTIVE_SCOPE` | specific restriction |

`save_packet` still infers `DECLARED` from any non-empty `allowedPaths` array. Derived change surface remains a mutation authority when the controller copies seeds into the packet.

### Class C — authority contradiction reset — REPRODUCED on PII

1. `development_authority_state_load` of `DAM-...eed6c502` failed closed: `AUTHORITY RELATION CONTRADICTION: repository is confirmed as both CANONICAL_PLANNING_AUTHORITY and HISTORICAL_ARCHIVE`.
2. Controller called `development_authority_state_start` (`retry clean map`).
3. Load of `DAM-...52638083` failed closed: `TODO.md is confirmed as both ACTIVE_IMPLEMENTATION_SCOPE and FORBIDDEN_COMPETING_AUTHORITY`.
4. Controller started `clean v3` `DAM-...65191f5f`, saved a packet, and reported continuation without operator adjudication.

`start()` overwrites `latest.txt` with no sticky contradiction latch. Failed maps remain on disk but do not block replacement PASS.

## Target B — Aleph_Rugent

### Identity

- repository: `DassaultFalconKing/Aleph_Rugent`
- exact SHA before/after: `bf1320a523fb7cf01953d03426403eb049fe5b1a`
- porcelain before/after: empty
- session: `ses_f9c3209a8ffeuhPMAYHjmNh3l4` (parent); child Task sessions including `ses_f9c317e9dffe` / inventory `ses_f9c3100daffeX3rlR8OgAGZo6o`
- runtime: `...\runtime-aleph-official`

### Tracked `.opencode` metadata

| File | Before | After |
|---|---|---|
| `.opencode/package.json` git blob | `718aed1e8ec735feccac51030308e0b63072b318` | same |
| `.opencode/package-lock.json` git blob | `538be4c1d1d9ac534fdaf4b348825a474ba000b0` | same |
| SHA-256 package.json | `678858089D4C45776705B898640B08BF417F68AD8C305518359761D8AD32B519` | same |
| SHA-256 lockfile | `528580A1488429D90566AF33850605F9E37A7D08CBAD3D2FA77FA2440A67598B` | same |
| plugin pin | `@opencode-ai/plugin 1.18.23` | unchanged under host 1.18.25 |

Class D historical mutation **not reproduced** on this current-host path with `OPENCODE_CONFIG_DIR` + `OPENCODE_DISABLE_PROJECT_CONFIG=1`. No `READ_ONLY_BOUNDARY_BLOCKED` because the target stayed byte-identical.

### Durable ids

| Artifact | Id |
|---|---|
| Authority map | `DAM-20260902202834-bf1320a523fb-18270428` (single map; load PASS) |
| Change surface | `CSM-20260902203143-bf1320a523fb-44662947` (`DERIVED_NON_AUTHORITATIVE`) |
| Native gates | `NGM-20260902203236-bf1320a523fb-717daf17` |
| Continuation packet | `DCP-20260902203709-bf1320a523fb-d834a030` |
| Isolation event ids in packet | `[]` |

Controller used OpenCode `task` for playbook Steps and claimed host-native fresh children, so it did not record `STEP_ISOLATION_UNPROVEN`. That is a different path from PII. No Aleph contradiction-load failure was observed; the controller did add “direction-mirrored” edges so packet direction validation would succeed.

### Class E — repository-path semantics

Stored Aleph patterns are repository paths (`crates/rag-contracts/src/lib.rs`, `docs/baseline/`, `crates/*/tests/`), not the historical conceptual strings `W5 production toolcaller` or `crates/rag-contracts/src/lib.rs:GraphProjection/x`.

PII live guard showed trailing directory `docs/archive/` covering `docs/archive/<child>`. Exact file literals remained exact. `validatePattern` still does not reject colon-member forms if a controller later stores them; this run did not store those shapes.

## Five historical failure classes on 1de37c

| Class | Historical b56 shape | Result on 1de37c | Notes |
|---|---|---|---|
| A positive path fabrication | PII `DECLARED` + invented allowlist + `IN_SCOPE` | **REPRODUCED** | PII packet/guard |
| B fresh-subagent ordering | UNPROVEN recorded after parent execution | **not reproduced on PII** | events before first fallback start; Aleph used Task children and left isolation ids empty |
| C contradiction reset | discard failed map, start corrected map, continue | **REPRODUCED** | PII two failed loads then `clean v3` packet |
| D read-only runtime | OpenCode 1.18.25 rewrote Aleph pin 1.18.23→1.18.25 | **not reproduced** | tracked package metadata byte-identical |
| E path semantics | conceptual/member strings; directory literals exact-only | **not reproduced in stored packets** | directory descendants worked for `docs/archive/` |

## Overall verdict

**RC6_REPAIR_REQUIRED** on exact candidate `1de37c75251a1e0d9904cffdb82695e92e3fab23`.

Hosted 7/7 remains real for this SHA. Live `/repo-continue` still:

1. promotes derived change-surface seeds into `pathScopeAuthority=DECLARED` / `IN_SCOPE`;
2. allows `development_authority_state_start` to replace a map after deterministic `AUTHORITY RELATION CONTRADICTION`.

PII_PARSER: **FAIL**. Aleph_Rugent: **FAIL** as a composition (packet exists and target was unmodified, but class A/C are generic controller+tool defects already witnessed on PII; Aleph also stored `DECLARED` allowlist copied from session-owned paths). Target mutation: **none**.

SIB0/SIB1/SIB2: **NOT RUN**. EHA: **NOT RUN**. Refs/tags: **not moved**. Historical reports: **not rewritten**.
