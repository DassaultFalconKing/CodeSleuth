# EHA operating playbook

## Purpose

This playbook connects CodeSleuth's SIB0/SIB1/SIB2 theory to the product's
actual OpenCode workflow and durable evidence tools.

Normative definitions remain in:

- [`STABLE-INTEGRATION-BASELINE.md`](STABLE-INTEGRATION-BASELINE.md);
- [`EXACT-HEAD-ACCEPTANCE.md`](EXACT-HEAD-ACCEPTANCE.md);
- [`EHA-REPAIR-LOOP.md`](EHA-REPAIR-LOOP.md);
- [`SEMANTIC-REFIT.md`](SEMANTIC-REFIT.md).

The installed agent-facing implementation is the `eha-sib-acceptance` Skill.
The installed command playbooks are `/eha-test`, `/eha-repair`, and
`/eha-status`.

## Evidence topology

CodeSleuth deliberately keeps one durable review/evidence authority rather than
inventing a second database for acceptance state:

```text
.opencode/state/reviews/<reviewId>/
  state.json          review checkpoint / coverage state
  findings.ndjson     exact-source findings
  eha.ndjson          EHA campaigns, SIB verdicts, repair decisions
```

Repository context graphs remain separate bounded/rebuildable linkage state.
Mermaid remains derived presentation.

```text
tracked Git source + blob identity
        |
        +--> review_state findings/coverage      durable evidence authority
        |       |
        |       +--> eha.ndjson                  acceptance-event ledger
        |               |
        |               +--> EHA Mermaid         derived history view
        |
        +--> RepositoryContextProjection         bounded derived linkage
                |
                +--> repository Mermaid          derived topology view
```

Do not merge these authorities merely because both can render Mermaid.

## Playbook: test an exact target

Use `/eha-test <target/scope>`.

The build agent must:

1. capture literal HEAD, branch, and dirty state;
2. start/load `review_state`;
3. call `eha_state_start_campaign`;
4. run SIB0 architecture profile;
5. record `SIB0 PASS|FAIL`;
6. run SIB1 capability-implementation profile;
7. record `SIB1 PASS|FAIL`;
8. run SIB2 integration/E2E profile;
9. record `SIB2 PASS|FAIL`;
10. load the structured ledger and write a report.

All three levels belong to the same immutable SHA. If HEAD changes, the
campaign is invalidated.

## Playbook: repair a failure

Use `/eha-repair <campaign/finding>` only after a FAIL has been recorded.

The failed SHA is frozen. The repairer creates a branch from it, applies the
minimum repair delta, adds regression coverage, runs focused tests, and records
that decision with `eha_state_record_repair`.

The repair SHA is not accepted merely because focused tests pass. It starts a
new EHA campaign and receives fresh SIB0/SIB1/SIB2 evidence for every maturity
degree claimed.

If the repair changes the fundamental capability inventory or authority model,
record `architecture_reopened` and re-establish SIB0 rather than hiding the
change inside an ordinary fix.

## Playbook: inspect history

Use `/eha-status`.

`eha_state_load` returns campaign summaries including:

- exact target SHA;
- SIB0/SIB1/SIB2 verdicts;
- claimable levels;
- failed levels;
- repair decisions and candidate SHAs.

`eha_state_mermaid` renders a bounded history diagram from that same ledger.
The diagram is useful for humans but is not acceptance authority.

## Claimability

A recorded PASS and a claimable SIB degree are deliberately different concepts.

For one exact SHA:

```text
SIB0 claimable = SIB0 PASS
SIB1 claimable = SIB0 PASS + SIB1 PASS
SIB2 claimable = SIB0 PASS + SIB1 PASS + SIB2 PASS
```

This prevents a component-level SIB1 run or integration-only SIB2 run from
silently manufacturing the lower maturity claims.

## Repair lineage example

```text
EHA-001 / SHA A
  SIB0 PASS
  SIB1 FAIL
  SIB2 PENDING
       |
       | minimum SIB1 repair + regression
       v
EHA-002 / SHA B
  SIB0 PASS
  SIB1 PASS
  SIB2 PASS
```

The first campaign remains failed forever. The second campaign proves the new
SHA. This history is exactly what `eha.ndjson` and the Mermaid projection are
intended to preserve.

## Semantic refit before EHA

When the candidate delta comes from stale or divergent work, use semantic refit
before acceptance:

1. recover still-valid intent/invariants;
2. preserve current accepted semantics;
3. classify REAPPLY / SUPERSEDED / REFIT / DROP;
4. build the minimum current-semantic composition;
5. identify its exact SHA;
6. start EHA on that resulting SHA.

A stale branch's green CI never transfers to the refitted composition.

## Reporting

The structured ledger is machine-readable evidence. `.codesleuth/reports/`
provides the human-readable account. EHA reports must include campaign ID,
exact SHA, all three SIB verdicts, claimability, blockers, repair lineage,
checks actually run, and limitations.

The practical operating rule is:

> **Test one SHA. Record what is true. Freeze failures. Repair into a new SHA. Test again.**
