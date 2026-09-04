# GitHub -> OpenCode EHA bridge

## Status and purpose

This document defines the trusted self-hosted GitHub adapter for CodeSleuth Exact-Head Acceptance (EHA).

The bridge is a control-plane adapter, not a second EHA implementation. It freezes and verifies one exact release-stream SHA, wires durable host-local state, performs the **trusted pre-provider** campaign bootstrap, invokes the canonical OpenCode `/eha-test` path, and derives a bounded transport result from the durable EHA ledger.

Normative acceptance semantics remain in:

- [`EXACT-HEAD-ACCEPTANCE.md`](EXACT-HEAD-ACCEPTANCE.md)
- [`SIB-CANDIDATE-SELECTION.md`](SIB-CANDIDATE-SELECTION.md)
- [`EHA-OPERATING-PLAYBOOK.md`](EHA-OPERATING-PLAYBOOK.md)
- [`DURABLE-EVIDENCE-STORE.md`](DURABLE-EVIDENCE-STORE.md)

The bridge never upgrades evidence into an EHA verdict. SIB0/SIB1/SIB2 verdicts and terminal completion remain durable CodeSleuth state.

## RC6 authority lifecycle

Trusted GitHub EHA is deliberately asymmetric with ordinary model execution: campaign existence is established before the provider can run, while SIB reasoning remains model/Playbook work.

```text
owner-gated GitHub request
-> freeze literal release ref + exact SHA
-> detached exact checkout + clean-worktree proof
-> wire external durable state/reports
-> trusted pre-provider provenance bind
-> trusted pre-provider review checkpoint
-> durable campaign_started
-> invoke OpenCode/provider with existing review/campaign identity
-> SIB0/SIB1/SIB2 evidence + verdicts
-> persist canonical report
-> durable campaign_completed
-> bridge may terminate/ignore remaining provider stream
```

The provider does **not** create, restart, replace, or supersede the bridge campaign. It consumes the already-started identity. A failure to start the provider therefore cannot erase the fact that the campaign exists.

`campaign_started` and `campaign_completed` are durable authority events. A provider final frame, session close event, or clean process exit is not acceptance authority.

## Architecture

```text
GitHub owner / connector
        |
        | workflow_dispatch from main
        | or owner-authored /eha-test issue comment
        v
.github/workflows/eha.yml
        |
        | immutable controller checkout
        | trusted self-hosted runner: codesleuth-eha
        v
scripts/eha_github_bridge.py
        |
        +--> exact-target validation
        |      fetch literal origin/dev/release-X.Y.Z
        |      require remote head == requested 40-char SHA
        |      checkout detached exact SHA
        |      require clean worktree
        |
        +--> external durable wiring
        |      .opencode/state -> <persist-root>/state
        |      .codesleuth/reports -> <persist-root>/reports
        |      private transcript -> <persist-root>/bridge-logs
        |
        +--> trusted pre-provider bootstrap
        |      canonical provenance binding
        |      review checkpoint
        |      campaign_started
        |
        +--> external exact-target OpenCode config mirror + scratch
        |
        +--> OpenCode/provider
        |      consumes prestarted review/campaign/provenance
        |      executes canonical eha-sib-acceptance Playbook
        |      records SIB verdicts and report
        |      records campaign_completed
        |
        +--> root transport watchdog + exact-target postconditions
        v
<persist-root>/state/reviews/<reviewId>/eha.ndjson
        authoritative durable EHA ledger
```

## Exact-target checks

Before trusted pre-provider bootstrap, the bridge:

1. requires a release stream matching `dev/release-X.Y.Z`;
2. requires a full lowercase 40-character SHA;
3. fetches that literal remote release ref;
4. requires the remote head to equal the requested SHA;
5. checks out that SHA detached;
6. verifies literal `git rev-parse HEAD` equality;
7. verifies a clean worktree;
8. rejects an exact SHA already carrying a durable FAIL verdict under failed-SHA immutability.

A moving release branch never changes the identity of an in-flight campaign. A newer head is a new candidate.

## Trusted pre-provider bootstrap

After exact-target validation and durable wiring, the trusted controller creates the campaign boundary without asking the model to establish its own authority.

The bootstrap must bind:

- exact target SHA;
- review identity;
- campaign identity;
- canonical producer provenance;
- recorded head SHA.

The canonical provenance implementation is reused. Provenance is attribution metadata only and cannot upgrade claimability or SIB maturity.

The bootstrap writes the review/provenance checkpoint before `campaign_started`. OpenCode then receives those identities as existing state. It must not rebind provenance or create another campaign for the same bridge request.

If trusted bootstrap fails, the provider path is unreachable.

## Durable completion handshake

The Playbook persists the canonical report before recording `campaign_completed`. The completion event is valid only for the exact campaign/target and only after all required SIB verdicts are durable PASS.

Once a valid `campaign_completed` event exists, the bridge may terminate its own OpenCode process tree. A SIGTERM or equivalent caused by this post-completion cleanup is not a transport error, because terminal EHA authority already exists durably.

If all SIB verdicts appear to be PASS but no valid completion event exists, the bridge fails closed rather than treating the provider's final response as completion.

## Transport outcome versus EHA outcome

The bridge keeps **transport outcome** separate from EHA verdict authority.

Examples:

```text
campaign exists + SIBs pending + provider silence
    EHA: INCOMPLETE/PENDING
    transport outcome: ERROR

campaign exists + SIB0/1/2 PASS + campaign_completed
    EHA: PASS
    transport outcome: PASS, or clean post-completion termination

any durable SIB FAIL
    EHA: FAIL
    exact SHA becomes immutable failed evidence
```

Under RC6, a provider stall after trusted bootstrap must not be represented as `campaign=None` or `NOT_RUN`. The campaign already exists. If no provider output appears, the correct derived state is an existing campaign with pending SIBs, `completion=false`, and a transport error such as `FIRST_RESPONSE_TIMEOUT`.

`NOT_RUN` is reserved for failure before a durable campaign exists, for example exact-target or trusted-bootstrap failure.

## Root-session watchdog

Provider/process liveness is transport containment, not acceptance authority.

After trusted bootstrap the bridge monitors:

- first provider response deadline;
- transcript/ledger progress deadline;
- durable completion observation.

A pre-provider campaign-start timeout is no longer part of the RC6 critical path because `campaign_started` exists before provider invocation.

On a transport fuse expiry the bridge terminates only the process group it created, preserves all durable state, re-checks candidate cleanliness, and records an error without upgrading any verdict.

## Durable persistence boundary

A GitHub-hosted ephemeral artifact must not masquerade as EHA authority. The canonical EHA bridge therefore runs on a trusted self-hosted runner labeled:

```text
codesleuth-eha
```

The runner preserves `CODESLEUTH_EHA_PERSIST_ROOT` outside the disposable checkout. Logical paths remain:

```text
.opencode/state
.codesleuth/reports
```

and are wired to host-persistent storage. The bridge refuses a persistence root inside the candidate checkout.

Detailed OpenCode stdout/stderr is private diagnostic provenance stored under the persistence root. Public Actions logs expose only bounded controller/runtime identity, candidate identity, review/campaign identity, verdict labels, and bridge outcome.

The private transcript is not EHA authority. `eha.ndjson` remains authoritative.

## OpenCode configuration and scratch

The exact candidate remains the source of tracked CodeSleuth configuration:

```text
OPENCODE_CONFIG=<exact-target>/pack/.opencode/opencode.json
```

OpenCode's writable discovery/bootstrap directory is a unique external mirror of that exact target:

```text
OPENCODE_CONFIG_DIR=<persist-root>/bridge-runtime/<run>/opencode-config
```

Temporary/scratch paths are also external and unique per run. The candidate checkout remains subject to strict post-run cleanliness checks. Runtime bootstrap metadata must never be hidden with new ignore rules merely to make EHA green.

## Provider/model boundary

The runner must provide one explicit host-qualified `provider/model` id. Automatic OpenCode updates are disabled during a campaign so the executable/runtime identity does not change mid-acceptance.

The provider performs analytical Playbook work only after the trusted pre-provider campaign exists. It may record SIB evidence/verdicts through canonical bounded tools and persist the report through the normal reports surface. It does not own exact-target selection, provenance identity, campaign existence, failed-SHA policy, or terminal completion authority.

## Security and mutation boundary

The workflow is owner-gated and uses repository read permissions. The candidate is read-only except for the explicitly bound report/state surfaces whose logical paths are redirected to durable storage.

Headless shell permissions are fail-closed. Unknown commands do not inherit permission to run. The bridge retains a strict post-EHA exact-target and cleanliness check.

This keeps EHA failure evidence honest: a green SIB ledger cannot conceal checkout mutation or a transport/postcondition error.

## Historical negative witnesses

Pre-RC6 campaigns remain useful negative evidence:

- Rc4 showed why tracked OpenCode configuration cannot double as writable bootstrap storage.
- Rc5a showed why tester scratch residue must fail the cleanliness oracle rather than be ignored after the fact.
- Rc5b showed that child-session keepalive cannot be root provider authority and motivated bridge-owned transport fuses.
- Rc5c showed the opposite end of the lifecycle: SIB0/SIB1/SIB2 could be durably PASS while the provider stream hung after useful work, motivating the durable `campaign_completed` handshake.
- the first Rc5d GitHub run stalled before durable campaign creation, demonstrating that model-mediated `start_campaign` still left provider liveness in the authority critical path. RC6 removes that dependency with trusted pre-provider bootstrap.

Historical outcomes stay attached to their exact SHAs. Repairs create new identities and new evidence.

## Operator acceptance

A trustworthy remote EHA result therefore requires all of the following for one exact candidate:

1. literal remote release ref and requested SHA agree;
2. detached checkout is exact and clean;
3. no immutable prior FAIL blocks the SHA;
4. canonical provenance/review/campaign are durably prestarted before provider execution;
5. provider records required SIB evidence/verdicts without creating a competing campaign;
6. canonical report persists;
7. valid `campaign_completed` exists;
8. bridge transport/postconditions are reported separately and honestly;
9. final checkout remains exact and clean.

GitHub is only the remote trigger and execution envelope. Durable CodeSleuth state remains acceptance authority.
