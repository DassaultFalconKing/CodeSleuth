# RC7 Supervisor State

**Status:** coordination evidence only; not semantic design authority
**Audit date:** 2026-09-04

## Exact baseline

- `main`: `6621c65b868d3e279ddcbd8dee182a95c6fb29f8`
- `SIB`: `6621c65b868d3e279ddcbd8dee182a95c6fb29f8`
- `dev/release-0.4.0`: `4370c0d63173d27556b11d629746afee07f3cf62`
- planning: `af0c5dcd4054cb2eef35d7661125fc939b9e3263`
- current `reviews` tip: `0ee3fcad49a8262ee7cddfa9166a6e9c7cf9ba9c`
- pinned antithesis remains: `be5d158880f649ecb568d9a505c694e87bd76e0e`
- frozen thesis: `1b52c7c72e5294b3a4c145d1bbbd71a1863cb218`
- integration stream: `integration/rc7 @ 6621c65b868d3e279ddcbd8dee182a95c6fb29f8`

Exact SIB2 acceptance evidence: GitHub Actions run `33834589505`, conclusion `success` on exact SHA `6621c65b868d3e279ddcbd8dee182a95c6fb29f8`.

## Accepted micro-freezes

- MF1 `c761e1ebacfebad5a4779da69d9d3a9d7a1d8a51` -> W5
- MF2 `d751b03c52168d59a23a445652cf042aa0e0c239` -> W7
- MF3 `b1e697e7cf8c9409538a20f9449b8ddd8780352e` -> W8
- MF4 `dc3191c11db669e416a3d86af69e7cfae95365af` -> W9
- MF5 `c9fa42dc032a37509534395f577d7069ae75eb56` -> W11

Cross-contract adjudication remains binding: completeness assessments remain external to `AcceptanceProfileSnapshotV1`; `MF4.profileSnapshotDigest = AcceptanceProfileSnapshotV1.semanticDigest`; Finding generation selection remains Finding-domain authority.

## RC6 -> RC7 delta

The accepted SIB2 is 21 commits ahead of old runtime evidence `1de37c75251a1e0d9904cffdb82695e92e3fab23`.

Material changes for RC7 coordination:

1. Development-continuation authority now fail-closes on path-scope fabrication and latches contradictory authority until explicit `SUPERSEDE_CONTRADICTION` adjudication.
2. Portable Rust graph read-side landed with exact-head/freshness checks and projection-payload TOCTOU protection.
3. Portable Obsidian adapter landed as a one-way derived projection consumer. Its RC7 object names are not source-schema authority.
4. Diagnostic TUI User Witness landed as a derived/non-authoritative surface.
5. Hosted acceptance gained portable-Rust and User-Witness coverage.
6. No production `AcceptanceProfileSnapshotV1`, `DiscoveryCompletenessV1`, `FindingGenerationSelectionV1`, or `LedgerIntegrityCore` exists at the SIB2 baseline.
7. No EHA V2 or second EHA authority was introduced; existing `eha.ndjson` contract remains authoritative.

## Authority frontier

`IMPLEMENTABLE`: W1, W3, W5, W7, W8, W9, W11.

`FINAL_FREEZE_BLOCKED`: W2, W4, W6, W10, W12, W13, W14, W15, W16 overall.

No whole W1-W16 workstream is classified POST_RC7. Post-RC7 exclusions remain exclusions rather than implementation authority.

## Initial dependency shape

```text
N1 -> N2 -> N3 -> W16 namespace slice
L1 -> W5
W7 -> W8
W7 -> W9
W11 -> later W14
FF1 -> W2/W4 authority
FF1 -> FF2 -> W6/W10 authority
W2 + W6 -> W13/W14
W9 + W10 -> W12
W6 + W8 + W9 -> W15
```

## Parallel roots established

Production branches, all created from exact accepted SIB2 `6621c65...`:

- `feature/rc7-namespace-foundation` (N1)
- `feature/rc7-ledger-integrity-core` (L1)
- `feature/rc7-acceptance-profile-snapshot` (W7)
- `feature/rc7-repair-packet-host-profile` (W11)

Design branch:

- `docs/rc7-ff1-implementation-ledger-recovery-freeze` from planning `af0c5dcd...`

No package is GREEN or integrated merely because its branch exists. Every production package still requires an honest RED witness, focused GREEN, broad gate, exact-head hosted acceptance, coordinator diff review, then serial integration and fresh acceptance of the resulting integration SHA.

## Coordination rule

This file records coordination state only. It does not override accepted runtime contracts, micro-freezes, final freezes, EHA evidence, or SIB authority.
