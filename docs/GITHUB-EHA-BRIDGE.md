# GitHub -> OpenCode EHA bridge

## Status and purpose

This document defines the remote invocation adapter for CodeSleuth Exact-Head Acceptance (EHA).

The bridge closes one operational gap: GitHub clients and connectors can request an EHA campaign even though they cannot execute the repository-local OpenCode Playbook themselves.

The bridge **does not implement a second acceptance controller**. GitHub Actions selects and freezes an exact release-stream candidate, prepares durable host-local evidence paths, and delegates execution to the existing OpenCode `/eha-test` command. The canonical `eha-sib-acceptance` Playbook and `eha_state_*` tools remain responsible for SIB0/SIB1/SIB2 reasoning and verdict recording.

Normative acceptance semantics remain in:

- [`EXACT-HEAD-ACCEPTANCE.md`](EXACT-HEAD-ACCEPTANCE.md);
- [`SIB-CANDIDATE-SELECTION.md`](SIB-CANDIDATE-SELECTION.md);
- [`EHA-OPERATING-PLAYBOOK.md`](EHA-OPERATING-PLAYBOOK.md);
- [`DURABLE-EVIDENCE-STORE.md`](DURABLE-EVIDENCE-STORE.md).

## Architecture

```text
GitHub owner / connector
        |
        | workflow_dispatch from main
        | or owner-authored issue comment
        | /eha-test dev/release-X.Y.Z <exact SHA> [scope]
        v
.github/workflows/eha.yml
        |
        | owner gate
        | immutable controller SHA from trigger event
        | trusted self-hosted runner: codesleuth-eha
        v
scripts/eha_github_bridge.py
        |
        +--> fetch literal origin/dev/release-X.Y.Z
        |       |
        |       +--> require remote head == requested full SHA
        |       +--> checkout exact SHA detached
        |       +--> require clean worktree
        |
        +--> host-persistent local paths
        |       |
        |       +--> .opencode/state -> <persist-root>/state
        |       +--> .codesleuth/reports -> <persist-root>/reports
        |       +--> private transcript -> <persist-root>/bridge-logs
        |
        +--> exact tracked configuration file
        |       |
        |       +--> OPENCODE_CONFIG=<exact-target>/pack/.opencode/opencode.json
        |
        +--> external per-run OpenCode custom-config mirror
        |       |
        |       +--> exact copy of <exact-target>/pack/.opencode
        |       +--> <persist-root>/bridge-runtime/<run>/opencode-config
        |       +--> writable bootstrap/package metadata stays outside checkout
        |       +--> OPENCODE_CONFIG_DIR=<external mirror>
        |
        +--> opencode-review run --command eha-test
                |
                v
        eha-sib-acceptance Playbook
                |
                +--> review_state
                +--> eha_state_start_campaign
                +--> SIB0 / SIB1 / SIB2 profiles
                +--> eha_state_record_verdict
                +--> codesleuth-reports
                |
                v
<persist-root>/state/reviews/<reviewId>/eha.ndjson
        authoritative durable EHA ledger
```

The workflow conclusion is a derived transport/execution signal. It is not acceptance authority. SIB claimability comes from the canonical EHA ledger for the exact target SHA.

## Why the EHA runner is self-hosted

A normal GitHub-hosted runner is disposable. CodeSleuth review and EHA state is intentionally local and ignored by Git:

```text
.opencode/state/reviews/<reviewId>/
  state.json
  findings.ndjson
  findings-amendments.ndjson
  eha.ndjson
```

Uploading one copy as an Actions artifact would make a temporary artifact store look like durable acceptance authority. Committing the ledger to a branch would create a second repository-backed state model and can expose sensitive evidence. Neither is acceptable.

The canonical bridge therefore runs on a trusted self-hosted runner carrying the label:

```text
codesleuth-eha
```

The runner must preserve `CODESLEUTH_EHA_PERSIST_ROOT` across jobs. When that variable is unset, the workflow uses a repository-specific directory under `RUNNER_WORKSPACE/.codesleuth-eha/`. Operators who require stronger durability should set `CODESLEUTH_EHA_PERSIST_ROOT` to a backed-up host path outside the Actions checkout.

The bridge refuses a persistence root inside the checkout.

## Runner contract

The trusted EHA runner must provide:

1. Git;
2. Python 3.10 or newer;
3. OpenCode in `PATH`;
4. a working OpenCode provider/model configuration and authentication;
5. filesystem access to a persistent local directory outside the checkout;
6. the `codesleuth-eha` self-hosted runner label.

Provider credentials belong to the trusted OpenCode host. The repository workflow does not hard-code a provider and does not turn CodeSleuth into a model runtime. Set `CODESLEUTH_EHA_MODEL` on the runner when an explicit OpenCode model is required; otherwise OpenCode uses its normal configured model selection.

The bridge records the OpenCode version in its derived bridge-run metadata. OpenCode automatic updates are disabled during the campaign so the executable is not replaced in the middle of acceptance.

The runner should be dedicated and minimally credentialed. The candidate is intentionally allowed to execute its own tests, so an EHA runner is a release-testing trust boundary, not a generic public-PR runner.

## Remote invocation

### GitHub UI / API

Use the `CodeSleuth EHA` workflow from `main` and provide:

- `release_branch`, for example `dev/release-0.4.0`;
- `expected_sha`, always the full 40-character lowercase SHA;
- optional `scope`.

Manual dispatch from any ref other than `main` is rejected. The controller checkout uses the immutable `github.sha` captured by the trigger rather than resolving a movable `main` ref later on the runner.

### GitHub connector or issue comment

A connector that can write issue comments but cannot dispatch workflows can use an owner-authored command:

```text
/eha-test dev/release-0.4.0 0123456789abcdef0123456789abcdef01234567 SIB0/SIB1/SIB2 exact-head acceptance
```

Only a comment whose GitHub actor is the repository owner can allocate the EHA runner. Comments from contributors, pull-request authors, forks, bots, or arbitrary public users do not reach the job.

The issue or pull request carrying the command is only a control-plane message. Its ref, PR head, synthetic merge ref, and issue identity are never used as the EHA target.

## Exact-target checks

Before OpenCode is started, the bridge:

1. validates that the requested branch matches `dev/release-X.Y.Z`;
2. validates a full lowercase 40-character SHA;
3. fetches that literal branch explicitly from `origin`;
4. compares the fetched remote head to the requested SHA;
5. fails closed if the request is stale;
6. checks out the exact SHA detached;
7. verifies literal `git rev-parse HEAD` equality;
8. verifies a clean worktree.

The release branch may move after candidate selection. As with local EHA, the running campaign remains bound to the frozen SHA. A newer release-stream head is a new candidate and requires another campaign.

## Durable evidence wiring

The exact checkout remains disposable. The logical CodeSleuth paths do not change:

```text
.opencode/state
.codesleuth/reports
```

On the trusted runner they are symlinked to host-persistent directories:

```text
<persist-root>/state
<persist-root>/reports
```

Therefore the existing `review_state` and `eha_state` tools continue to use their normal paths and formats. There is no GitHub-specific ledger implementation.

`eha.ndjson` remains the authority. The bridge also writes a small derived record under:

```text
<persist-root>/bridge-runs/<github-run-id>-attempt-<n>.json
```

That record contains target identity, campaign/review IDs, SIB verdict labels, OpenCode version, adapter outcome, and a relative pointer to the private transcript record. It intentionally does not duplicate finding excerpts or EHA evidence payloads.

## Immutable config versus writable OpenCode bootstrap

The EHA candidate contains the CodeSleuth OpenCode pack at:

```text
<exact-target>/pack/.opencode
```

Two different roles must not be conflated:

```text
OPENCODE_CONFIG
    = exact tracked configuration identity

OPENCODE_CONFIG_DIR
    = custom discovery/bootstrap directory
    = may be written by OpenCode runtime/bootstrap
```

The bridge keeps the first role bound directly to the exact target:

```text
OPENCODE_CONFIG=<exact-target>/pack/.opencode/opencode.json
```

For the second role, the workflow allocates a unique external path:

```text
<persist-root>/bridge-runtime/<github-run-id>-attempt-<n>/opencode-config
```

The shipped `opencode-review` / `opencode-review.ps1` wrapper, after the bridge has already frozen and checked out the exact target, invokes `scripts/eha_opencode_runtime.py` to copy that target's `pack/.opencode` tree into the external path. It then sets only:

```text
OPENCODE_CONFIG_DIR=<external exact-target mirror>
```

The helper fails closed when:

- the exact source pack is missing;
- `opencode.json` is missing;
- the requested mirror is inside the candidate repository;
- the per-run mirror already exists and would be reused.

The mirror is a runtime/discovery surface, not repository authority and not EHA evidence authority. Generated `package.json`, `package-lock.json`, plugin bootstrap files, or similar runtime metadata may exist there without changing the candidate.

This separation is necessary because OpenCode legitimately treats a custom configuration directory as a runtime discovery/bootstrap surface. Making the tracked candidate pack serve both as immutable source and writable runtime directory weakens exact-target cleanliness.

## Rc4 negative witness

Rc4 exact target `86a7dc59574fd6e48d8eadc108b60ac3773bee9a` recorded durable SIB0/SIB1/SIB2 PASS verdicts, then the bridge failed the post-EHA cleanliness check because OpenCode bootstrap had created:

```text
?? pack/.opencode/package-lock.json
?? pack/.opencode/package.json
```

The correct classification is:

```text
durable exact-SHA EHA verdict = PASS
bridge transport/postcondition = ERROR
```

The repair does not add those paths to `.gitignore`, does not add them to `.git/info/exclude`, and does not relax the post-EHA cleanliness check. It removes the incorrect writable-runtime role from the tracked pack.

## Private transcript boundary

`opencode run --format json` can contain repository snippets, tool output, findings, prompts, and other evidence that does not belong in a public Actions log. The bridge therefore never streams the OpenCode process output to Actions stdout/stderr.

The combined OpenCode stdout/stderr is stored with host-local restricted permissions under:

```text
<persist-root>/bridge-logs/<github-run-id>-attempt-<n>.log
```

Public Actions output is intentionally bounded to controller/runtime identity, exact candidate SHA, campaign/review identity, SIB verdict labels, and the adapter outcome. Operators inspect detailed evidence through the normal durable CodeSleuth state/report interfaces or directly on the trusted host.

This transcript is diagnostic provenance, not acceptance authority. `eha.ndjson` remains authoritative.

## Failed SHA immutability

Before delegating a new remote campaign, the bridge scans all persisted review EHA ledgers for an existing FAIL verdict on the requested SHA. If one exists, the bridge refuses the request and requires repair to a new exact SHA.

This cross-review guard exists because a remote control plane must not manufacture a fresh review directory and thereby appear to rehabilitate an exact SHA that is already known to have failed acceptance.

A failure is evidence, not permission to rerun history until the dashboard becomes green.

## Headless OpenCode boundary

The exact candidate remains the source of configuration, commands, Skills, Playbooks, Tools, and wrappers. The external runtime mirror is created only after exact-target checkout and from that exact target.

The wrapper then invokes:

```text
opencode-review run --command eha-test --format json ...
```

The workflow checks out with `persist-credentials: false` and repository permission `contents: read`. OpenCode may inspect and test the candidate, but the EHA command contract forbids application/source mutation. The bridge additionally denies Git mutation commands in the headless permission overlay and re-checks worktree cleanliness after OpenCode exits. It fails closed if tracked or untracked repository state was changed outside the explicitly bound evidence/report paths.

Only `.codesleuth/reports/**` is granted through OpenCode's edit permission override. The persistent state itself is written by the existing bounded CodeSleuth tools.

## Workflow result versus EHA result

The bridge derives a compact status from the **new campaign recorded after invocation**:

```text
PASS       SIB0 PASS + SIB1 PASS + SIB2 PASS, OpenCode exited cleanly
FAIL       at least one canonical EHA verdict is FAIL
INCOMPLETE one or more levels remain PENDING
ERROR      identity, persistence, OpenCode, ledger, or cleanliness invariant failed
```

A GitHub job marked successful therefore means the delegated canonical campaign reached all three PASS verdicts on the exact SHA and the adapter itself completed cleanly.

A failed GitHub job does not erase the ledger. In particular:

```text
GitHub/bridge ERROR after durable PASS
    -/-> EHA FAIL
```

Likewise an EHA FAIL remains durable evidence even if some later transport layer also errors.

Ordinary `.github/workflows/acceptance.yml` runs are useful exact-head development gates. They do not substitute for this EHA workflow and do not write SIB verdicts.

## Promotion boundary

This bridge does not move `SIB`, `main`, release refs, tags, or release objects.

Promotion remains a separate explicit operation after the exact candidate is claimable at the required level. This preserves the fundamental rule:

> test the exact state first; promotion may point at that exact state, but promotion never creates the proof.

## Security boundary for the public repository

Self-hosted Actions runners and public repositories are an entertaining combination only if one enjoys incident response. The EHA workflow therefore has a deliberately narrow allocation boundary:

- owner-only job condition;
- no pull-request trigger;
- manual dispatch only from `main`;
- immutable event SHA for bridge/controller checkout;
- no checkout of contributor code as bridge/controller source;
- the candidate must be a literal numbered release-stream head;
- `GITHUB_TOKEN` repository permission is read-only;
- checkout credentials are not persisted;
- Git mutation commands are denied to headless OpenCode;
- detailed OpenCode transcript never enters public Actions logs;
- runs are serialized per repository;
- no automatic SIB/ref promotion.

Do not broaden this workflow to arbitrary PR heads or public comment authors.

## Operator sequence

For a new future-SIB candidate:

```text
1. Integrate work into dev/release-X.Y.Z.
2. Capture its literal full head SHA.
3. Run ordinary exact-head development gates as required.
4. Dispatch CodeSleuth EHA from main, or post the owner-only /eha-test command.
5. The bridge freezes that release head.
6. The exact target's OpenCode pack is mirrored to a unique external runtime dir.
7. OpenCode executes canonical /eha-test against the frozen target.
8. Inspect the durable campaign with /eha-status or eha_state_load.
9. If any level FAILs, preserve the failed SHA and use /eha-repair.
10. If SIB2 is claimable, promotion is a separate explicit action.
```

This is the same EHA discipline as a local OpenCode session, with GitHub acting only as a remote trigger and execution envelope.
