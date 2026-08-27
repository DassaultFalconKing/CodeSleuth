# EHA operating playbook

## Purpose

This document connects CodeSleuth's SIB0/SIB1/SIB2 theory to the product's actual OpenCode workflow and durable evidence tools.

Normative definitions remain in:

- [`STABLE-INTEGRATION-BASELINE.md`](STABLE-INTEGRATION-BASELINE.md);
- [`EXACT-HEAD-ACCEPTANCE.md`](EXACT-HEAD-ACCEPTANCE.md);
- [`SIB-CANDIDATE-SELECTION.md`](SIB-CANDIDATE-SELECTION.md);
- [`EHA-REPAIR-LOOP.md`](EHA-REPAIR-LOOP.md);
- [`SEMANTIC-REFIT.md`](SEMANTIC-REFIT.md);
- [`PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md`](PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md).

The installed agent-facing implementation is the `eha-sib-acceptance` and `eha-repair` Playbooks composed from atomic Skills and `eha_state_*` tools. The installed command entry points are `/eha-test`, `/eha-repair`, and `/eha-status`.

## Candidate stream

For a numbered release, future SIB candidates are selected from the literal head of the active `dev/release-X.Y.Z` branch.

For the current release line:

```text
dev/release-0.4.0 -> literal exact HEAD -> EHA target
```

The release branch is mutable. The EHA target is not. Candidate selection freezes the SHA recorded in the campaign, not the branch ref.

A PR head, repair-branch head, synthetic PR merge ref, convenience EHA branch, or tree-equivalent commit is not substituted for the selected literal release-stream head.

If the release branch moves while EHA is running, the campaign remains bound to the originally selected SHA. A newer release head requires a new campaign if it is to become the SIB candidate.

## Evidence topology

CodeSleuth deliberately keeps one durable review/evidence authority rather than inventing a second database for acceptance state:

```text
.opencode/state/reviews/<reviewId>/
  state.json          review checkpoint / coverage state
  findings.ndjson     exact-source findings
  eha.ndjson          EHA campaigns, SIB verdicts, repair decisions
```

Repository context graphs remain separate bounded/rebuildable linkage state. Mermaid remains derived presentation.

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

Use `/eha-test <target/scope>` or `/playbook eha-sib-acceptance`.

For normal future-SIB selection, begin from the active release stream and verify that literal current HEAD is the selected `dev/release-X.Y.Z` head. Record that branch and SHA as selection provenance before starting the campaign.

The build agent must:

1. capture literal HEAD, branch, and dirty state;
2. for future-SIB selection, confirm the target was selected from literal `dev/release-X.Y.Z` HEAD;
3. start/load `review_state`;
4. call `eha_state_start_campaign`;
5. run SIB0 architecture profile;
6. record `SIB0 PASS|FAIL`;
7. run SIB1 capability-implementation profile;
8. record `SIB1 PASS|FAIL`;
9. run SIB2 integration/E2E profile;
10. record `SIB2 PASS|FAIL`;
11. load the structured ledger and write a report.

All three levels belong to the same immutable SHA. If HEAD changes, the campaign is invalidated.

## Playbook: repair a failure

Use `/eha-repair <campaign/finding>` or `/playbook eha-repair` only after a FAIL has been recorded.

The failed SHA is frozen. The repairer creates a branch from it, applies the minimum repair delta, adds regression coverage, runs focused tests, and records that decision with `eha_state_record_repair`.

The repair branch is not the next SIB integration line. After focused repair verification, integrate the repair through the active `dev/release-X.Y.Z` stream. The resulting literal release-stream head is the next SIB candidate and starts a fresh EHA campaign.

If integration creates a merge commit, that merge commit is the candidate. Tree equality with the repair commit does not transfer acceptance evidence.

The repair SHA is not accepted merely because focused tests pass. Neither the repair commit nor the resulting release-stream head inherits SIB0/SIB1/SIB2 PASS from the failed predecessor.

If the repair changes the fundamental capability inventory or authority model, record `architecture_reopened` and re-establish SIB0 rather than hiding the change inside an ordinary fix.

## Playbook: inspect history

Use `/eha-status`.

`eha_state_load` returns campaign summaries including:

- exact target SHA;
- SIB0/SIB1/SIB2 verdicts;
- claimable levels;
- failed levels;
- repair decisions and candidate SHAs.

`eha_state_mermaid` renders a bounded history diagram from that same ledger.
Operators may choose campaign and per-campaign repair limits plus direction;
headers and omission nodes report the shown/total window explicitly. Failed
campaigns, pending levels, claimable levels, repair decisions, and candidate
transitions remain visibly distinct. The diagram is useful for humans but is not
acceptance authority and never transfers a verdict to another SHA.

## Claimability

A recorded PASS and a claimable SIB degree are deliberately different concepts.

For one exact SHA:

```text
SIB0 claimable = SIB0 PASS
SIB1 claimable = SIB0 PASS + SIB1 PASS
SIB2 claimable = SIB0 PASS + SIB1 PASS + SIB2 PASS
```

This prevents a component-level SIB1 run or integration-only SIB2 run from silently manufacturing the lower maturity claims.

## Repair lineage example

```text
dev/release-X.Y.Z -> SHA A
                       |
                       v
EHA-001 / SHA A
  SIB0 PASS
  SIB1 FAIL
  SIB2 PENDING
       |
       | minimum SIB1 repair on fix/eha-*
       v
repair commit R
       |
       | integrate into dev/release-X.Y.Z
       v
SHA B = new literal release-stream head
       |
       v
EHA-002 / SHA B
  SIB0 PASS
  SIB1 PASS
  SIB2 PASS
```

The first campaign remains failed forever. The second campaign proves the new release-stream composition. This history is exactly what `eha.ndjson` and the Mermaid projection are intended to preserve.

## Semantic refit before EHA

When a candidate delta derives from historical or divergent work, satisfy semantic-refit continuity before acceptance:

1. freeze exact historical/source and current target identities;
2. recover material evidenced claims, compatibility obligations, and negative knowledge rather than relying on one summary of `intent`;
3. resolve current normative authority by triangulating current code/config, normative/public docs, and executable tests; preserve `UNPROVEN`/conflict states when evidence does not resolve them;
4. record **semantic status** for each material claim (`REQUIRED`, `SUPERSEDED`, `RETIRED`, `UNRESOLVED`, or `CONFLICTED`) separately from its **delivery disposition** (`REUSE`, `PORT / ADAPT`, `REIMPLEMENT`, `NEW CHANGE`, `NO CHANGE`, `DEFER`, or `BLOCK`);
5. require positive coverage evidence for `SUPERSEDED` and explicit current authority for `RETIRED`; do not use implementation difficulty as semantic evidence;
6. preserve accepted forbidden regressions and current ownership/authority contracts while integrating only the minimum target-native delta required by surviving claims;
7. integrate the resulting composition into the active release stream;
8. identify the resulting literal `dev/release-X.Y.Z` head SHA;
9. start fresh EHA on that resulting SHA and report residual oracle/UX uncertainty honestly.

Historical `REAPPLY / SUPERSEDED / REFIT / DROP` labels may appear in source handoffs, but they are shorthand only; new material evidence follows the explicit two-axis model in `SEMANTIC-REFIT.md`.

A stale branch's green CI never transfers to the refitted composition.

## Reporting

The structured ledger is machine-readable evidence. `.codesleuth/reports/` provides the human-readable account. EHA reports must include campaign ID, exact SHA, release-stream selection provenance, all three SIB verdicts, claimability, blockers, repair lineage, checks actually run, and limitations.

When semantic refit materially shaped the candidate, the human-readable report should additionally identify the historical/source identity, material claim dispositions, explicit supersession/retirement authority, preserved forbidden regressions, and residual human/UX uncertainty. This reporting requirement does not create a second durable authority; the report remains a derived view of exact evidence and reviewed source.

The practical operating rule is:

> **Compose on the release stream. Select its literal HEAD. Test one SHA. Freeze failures. Repair back through the release stream. Select and test again.**
