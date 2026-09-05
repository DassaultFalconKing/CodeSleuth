# RC7 Supervisor State

**Status:** coordination evidence only; not semantic design authority  
**Last coordinator update:** 2026-09-05

## Accepted construction predecessor

The accepted RC6/SIB2 construction predecessor remains:

- `SIB`: `6621c65b868d3e279ddcbd8dee182a95c6fb29f8`
- `dev/release-0.4.0`: `4370c0d63173d27556b11d629746afee07f3cf62`
- planning base consumed by initial RC7 coordination: `af0c5dcd4054cb2eef35d7661125fc939b9e3263`
- pinned antithesis: `be5d158880f649ecb568d9a505c694e87bd76e0e`
- frozen thesis: `1b52c7c72e5294b3a4c145d1bbbd71a1863cb218`

Exact predecessor hosted acceptance: GitHub Actions run `33834589505`, conclusion `success` on exact SHA `6621c65b868d3e279ddcbd8dee182a95c6fb29f8`.

## Protected-ref drift discovered during orchestration

`main` is no longer equal to the accepted construction predecessor. It has moved out of the RC7 supervisor integration stream to:

- `main`: `330f4c533bb6a29cc7f762323ac3e64a14a27385`

That head is 9 commits ahead of `6621c65...`. This is recorded as a HIGH supervisor divergence to reconcile before any future RC7 promotion to `main`. It does not rewrite the accepted predecessor because `SIB` remains pinned and `integration/rc7` began from the exact accepted predecessor.

The supervisor must not silently absorb the `main` delta into RC7. It requires explicit later classification/refit before promotion.

## Accepted micro-freezes

- MF1 `c761e1ebacfebad5a4779da69d9d3a9d7a1d8a51` -> W5
- MF2 `d751b03c52168d59a23a445652cf042aa0e0c239` -> W7
- MF3 `b1e697e7cf8c9409538a20f9449b8ddd8780352e` -> W8
- MF4 `dc3191c11db669e416a3d86af69e7cfae95365af` -> W9
- MF5 `c9fa42dc032a37509534395f577d7069ae75eb56` -> W11

Binding cross-contract adjudication:

- completeness assessments remain external to immutable `AcceptanceProfileSnapshotV1`;
- `MF4.profileSnapshotDigest = AcceptanceProfileSnapshotV1.semanticDigest`;
- Finding generation selection remains Finding-domain authority, not `LedgerIntegrityCore`;
- MF5 packets/Jinja presentation do not grant execution or mutation authority.

## FF1 accepted

FF1 is accepted on the planning stream.

- contract: `docs/RC7-IMPLEMENTATION-LEDGER-RECOVERY-FREEZE.md`
- reviewed FF1 contract head: `3a8fc265c4423e4983b9ced5974cce039072e88f`
- indexing branch head observed by coordinator: `d8215866fbc15158d27ddf614ccb61e639d1b783`

FF1 changes the implementation frontier:

- W2 Implementation Ledger core: IMPLEMENTABLE
- W4A recovery read/build/validate: IMPLEMENTABLE after W2 + LedgerIntegrityCore
- W4B authority-changing SELECT write: semantics frozen, mutation authorization BLOCKED until FF2/W10 `LedgerRecoveryCaseV1`

FF1 explicitly reopens RC7 SIB0 for the `CC-STATE` ownership redefinition. RC6/SIB2 remains the construction predecessor, but predecessor SIB0 acceptance does not transfer to the resulting RC7 architecture by ancestry.

## Current integration stream

N1 namespace foundation was coordinator-reviewed at exact green feature head:

- feature head: `fec66c925d7d2cccc4305acdb63eea65790d4f8a`
- exact feature acceptance run: `33882593689`, success
- integration PR: `#120`
- merge SHA: `64c1986ab26c16957c7f126106f7dc2020edfcae`

Current `integration/rc7`:

- `64c1986ab26c16957c7f126106f7dc2020edfcae`

Fresh exact-head hosted acceptance for the integration merge is run `33933895432`.

**Admission state at this update:** `IN_PROGRESS`.

Therefore `64c1986...` is physically integrated but MUST NOT yet be treated as the accepted downstream RC7 base until run `33933895432` completes successfully.

## Production workstream state

| Workstream | Branch/head | TDD / evidence | Integration state |
| --- | --- | --- | --- |
| N1 namespace | `feature/rc7-namespace-foundation @ fec66c925...` | FIRST RED proven; exact feature acceptance `33882593689` success | merged as `64c1986...`; integration acceptance IN_PROGRESS |
| L1 LedgerIntegrityCore | `feature/rc7-ledger-integrity-core @ 6621c65...` | no RC7 RED/implementation admitted yet | WAIT accepted integration base |
| W7 snapshot | `feature/rc7-acceptance-profile-snapshot @ 339db73fb9fd70af6ca6ad5a7b99b93f12215ed5` | dedicated RED harness exists; W7 workflow fails because production module `pack/.opencode/tools/acceptance_profile_snapshot` is absent | RED; WAIT semantic refit to accepted integration base before implementation |
| W11 repair packet/host profile | `feature/rc7-repair-packet-host-profile @ 6621c65...` | no RC7 RED/implementation admitted yet | WAIT accepted integration base |
| FF1 | `docs/rc7-ff1-implementation-ledger-recovery-freeze @ d8215866...` | design/freeze, not code gate | ACCEPTED |

The generic acceptance suite being green on a RED-only feature branch does not prove the RC7 capability. Package-specific RED/GREEN evidence remains required.

## Updated authority frontier

`IMPLEMENTABLE / AUTHORIZED DESIGN`:

- W1 namespace foundation
- W2 Implementation Ledger core, after accepted FF1
- W3 LedgerIntegrityCore
- W4A Implementation recovery read/build/validate, after W2 + W3
- W5 Finding Ledger recovery, after W3
- W7 ProjectSibProfile / AcceptanceProfileSnapshot
- W8 discovery vs policy completeness, after W7
- W9 deterministic repair termination, after W7
- W11 RepairPacket / HostExecutionProfile

`SEMANTICS FROZEN / MUTATION AUTHORITY BLOCKED`:

- W4B Implementation recovery SELECT write, waiting FF2/W10 permission authority

`FINAL-FREEZE-BLOCKED`:

- W6 EHA V2
- W10 EhaRepairCaseV1 / LedgerRecoveryCaseV1 permissions
- W12 RepairLearningRecordV1
- W13 EbcaClaimViewV1
- W14 final projection parity/source mapping
- W15 integrated context epistemics
- W16 complete lifecycle/catalog/docs closure

## Dependency / orchestration order

```text
N1 -> N2 -> N3 -> W16 namespace slice

L1 -> W5
FF1 -> W2
L1 + W2 -> W4A
FF2/W10 -> W4B mutation authorization

W7 -> W8
W7 -> W9
W11 -> later W14

FF1 -> FF2 -> W6/W10
W2 + W6 -> W13/W14
W9 + W10 -> W12
W6 + W8 + W9 -> W15
```

## Coordinator operating rule

The supervisor owns branch/session orchestration. The operator is not required to shuttle multipart prompts or reports between implementation sessions.

For each production workstream the coordinator enforces:

```text
accepted exact integration base
-> package FIRST RED
-> minimal implementation
-> focused GREEN
-> broad regression gate
-> exact-head hosted acceptance
-> coordinator diff/authority review
-> serial integration
-> fresh exact-head acceptance of resulting integration SHA
-> only then new downstream base
```

Parallel feature green evidence is historical evidence only after `integration/rc7` advances. Later packages must semantic-refit onto the current accepted integration head and repeat exact-head verification before integration.

This file records coordination state only. It does not override accepted runtime contracts, micro-freezes, final freezes, EHA evidence, or SIB authority.
