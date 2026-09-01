# EHA operating playbook

## Purpose

This document connects CodeSleuth's SIB0/SIB1/SIB2 theory to the product's actual OpenCode workflow and durable evidence tools.

Normative definitions remain in:

- [`STABLE-INTEGRATION-BASELINE.md`](STABLE-INTEGRATION-BASELINE.md);
- [`EXACT-HEAD-ACCEPTANCE.md`](EXACT-HEAD-ACCEPTANCE.md);
- [`SIB-CANDIDATE-SELECTION.md`](SIB-CANDIDATE-SELECTION.md);
- [`EHA-REPAIR-LOOP.md`](EHA-REPAIR-LOOP.md);
- [`SEMANTIC-REFIT.md`](SEMANTIC-REFIT.md);
- [`PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md`](PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md);
- [`GITHUB-EHA-BRIDGE.md`](GITHUB-EHA-BRIDGE.md).

The installed agent-facing implementation is the `eha-sib-acceptance` and `eha-repair` Playbooks composed from atomic Skills and bounded `eha_state_*` tools. The installed command entry points are `/eha-test`, `/eha-repair`, and `/eha-status`.

## Candidate stream

For a numbered release, future SIB candidates are selected from the literal head of the active `dev/release-X.Y.Z` branch.

```text
dev/release-X.Y.Z -> literal exact HEAD -> EHA target
```

The release branch is mutable. The EHA target is not. Candidate selection freezes the SHA recorded in the campaign, not the branch ref.

A PR head, repair-branch head, synthetic PR merge ref, convenience EHA branch, or tree-equivalent commit is not substituted for the selected literal release-stream head.

If the release branch moves while EHA is running, the campaign remains bound to the originally selected SHA. A newer release head requires a new campaign.

## Evidence topology

CodeSleuth keeps one durable review/evidence authority:

```text
.opencode/state/reviews/<reviewId>/
  state.json          review checkpoint / coverage state
  findings.ndjson     exact-source findings
  eha.ndjson          campaigns, SIB verdicts, repairs, completion
```

Repository context graphs remain bounded/rebuildable linkage state. Mermaid remains derived presentation.

The acceptance-event ledger is authority for campaign identity, SIB verdicts, repair lineage, and `campaign_completed`. Provider session state and transport output are not acceptance authority.

## Two legal campaign-start modes

The same `eha-sib-acceptance` Playbook supports two explicitly different authority paths.

### Trusted GitHub bridge: `trusted_prestarted`

The trusted GitHub bridge freezes and validates the exact release SHA before provider execution. It then performs trusted pre-provider bootstrap:

```text
exact target verified
-> durable persistence wired
-> canonical provenance bound
-> review checkpoint created
-> campaign_started appended
-> provider/OpenCode invoked
```

The provider does not own campaign existence in this mode. It loads the matching durable campaign, verifies that target SHA and release branch agree with `candidate_identity`, and reports authority as `trusted_prestarted`.

It must not call `eha_state_start_campaign`, create another review checkpoint, replace the campaign id, reinterpret the scope, or rebind provenance for the bridge-created campaign.

If trusted pre-provider bootstrap fails, provider execution is unreachable.

### Ordinary local/controller execution: `model_started`

Outside trusted-bridge mode there may be no prestarted campaign. After exact-target verification, the primary controller may start/load review state and use the canonical `eha_state_start_campaign` primitive. The resulting campaign is reported as `model_started`.

This compatibility path does not weaken trusted GitHub EHA. A trusted-bridge run must reuse its prestarted campaign rather than silently falling back to model-owned campaign creation.

## Playbook: test an exact target

Use `/eha-test <target/scope>` or `/playbook eha-sib-acceptance`.

For normal future-SIB selection, begin from the active release stream and verify that literal current HEAD is the selected `dev/release-X.Y.Z` head.

The controller/Playbook must:

1. capture and verify literal target HEAD, branch, and dirty state;
2. resolve the campaign:
   - trusted bridge -> load the exact `trusted_prestarted` campaign;
   - ordinary local mode -> create/load the exact `model_started` campaign;
3. preserve one immutable campaign SHA and scope;
4. run the SIB0 architecture profile and record `SIB0 PASS|FAIL`;
5. run the SIB1 capability-implementation profile and record `SIB1 PASS|FAIL`;
6. run the SIB2 integration/E2E profile and record `SIB2 PASS|FAIL`;
7. load the structured ledger and persist the canonical report;
8. only after the report exists and all required SIB verdicts are durable PASS, append `campaign_completed`.

All three SIB levels belong to the same immutable SHA. If literal HEAD changes, stop with `EHA INVALIDATED — HEAD CHANGED`.

`campaign_started` establishes campaign identity. `campaign_completed` establishes durable terminal completion. A provider final frame, clean process exit, or session close does not substitute for either event.

## Transport outcome is separate

Transport outcome is diagnostic/runtime state, not EHA verdict authority.

Examples:

```text
campaign exists + SIBs pending + provider stalls
    EHA state: incomplete/pending
    transport outcome: ERROR

campaign exists + SIB0/1/2 PASS + campaign_completed
    EHA state: PASS
    transport outcome: PASS or post-completion bridge termination

any durable SIB FAIL
    EHA state: FAIL
    exact SHA becomes immutable failed evidence
```

In trusted mode, a provider stall after bootstrap must not be reported as `campaign=None` or `NOT_RUN`: `campaign_started` already exists.

## Playbook: repair a failure

Use `/eha-repair <campaign/finding>` or `/playbook eha-repair` only after a FAIL has been recorded.

The failed SHA is frozen. The repairer creates a branch from it, applies the minimum repair delta, adds regression coverage, runs focused tests, and records that decision with `eha_state_record_repair`.

The repair branch is not the next SIB integration line. Integrate the repair through the active `dev/release-X.Y.Z` stream. The resulting literal release-stream head is a new candidate and starts a fresh EHA campaign.

If integration creates a merge commit, that merge commit is the candidate. Tree equality with the repair commit does not transfer acceptance evidence.

If a repair changes the fundamental capability inventory or authority model, record `architecture_reopened` and re-establish SIB0 rather than hiding it inside an ordinary fix.

## Inspect history

Use `/eha-status`.

`eha_state_load` returns campaign summaries including exact target SHA, campaign start/completion, SIB0/SIB1/SIB2 verdicts, claimability, failed levels, and repair decisions. `eha_state_mermaid` renders a bounded derived history view from that same ledger.

The diagram is useful for navigation but is not acceptance authority and never transfers a verdict to another SHA.

## Claimability

For one exact SHA:

```text
SIB0 claimable = SIB0 PASS
SIB1 claimable = SIB0 PASS + SIB1 PASS
SIB2 claimable = SIB0 PASS + SIB1 PASS + SIB2 PASS
```

A component-level SIB1 run or integration-only SIB2 run cannot silently manufacture the lower maturity claims.

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
       | minimum repair
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
  campaign_completed
```

The first campaign remains failed forever. The second campaign proves the new release-stream composition.

## Semantic refit before EHA

When a candidate delta derives from historical or divergent work:

1. freeze exact historical/source and current target identities;
2. recover material evidenced claims, compatibility obligations, and negative knowledge;
3. resolve current normative authority by triangulating current code/config, normative/public docs, and executable tests;
4. preserve `UNPROVEN`/conflict states rather than averaging contradictions;
5. record semantic status separately from delivery disposition;
6. preserve accepted forbidden regressions and current ownership/authority contracts;
7. integrate only the minimum target-native delta through the active release stream;
8. identify the resulting literal release-stream head SHA;
9. start fresh EHA on that resulting SHA.

Historical green CI never transfers to the refitted composition.

## Reporting

The structured ledger is machine-readable evidence. `.codesleuth/reports/` provides the human-readable account.

EHA reports must include campaign ID, campaign authority (`trusted_prestarted` or `model_started`), exact SHA, release-stream selection provenance, all three SIB verdicts, claimability, `campaign_completed` state, blockers, repair lineage, checks actually run, transport outcome, and limitations.

The practical operating rule is:

> **Compose on the release stream. Select its literal HEAD. Establish one durable campaign. Test one SHA. Persist the report. Complete durably. Freeze failures. Repair back through the release stream. Select and test again.**
