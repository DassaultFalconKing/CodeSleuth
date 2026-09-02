# RC6 Live Dogfood Runbook

Status: **PRE-LIVE RUNBOOK — EXECUTE ONLY AFTER FINAL EXACT-HEAD HOSTED 7/7**

Scope authority: [`RC6-FEATURE-PLAN.md`](RC6-FEATURE-PLAN.md), especially sections 8–10 and the RC6 definition of done.

Normative continuation semantics: [`DEVELOPMENT-CONTINUATION-CONTRACT.md`](DEVELOPMENT-CONTINUATION-CONTRACT.md).

## 1. Purpose

This runbook defines the first live-host acceptance boundary for RC6 evidence-bound development continuation.

The dogfood is deliberately read-only with respect to target project source and target configuration. It validates that the real OpenCode/CodeSleuth host can recover project-native development authority, active scope, change surface and verification boundaries on unfamiliar mature repositories without project-specific CodeSleuth adapters.

Dogfood is not allowed to compensate for missing repository/hosted acceptance. It begins only when one literal CodeSleuth RC6 head has passed the complete hosted acceptance matrix.

## 2. Entry gate

Before touching either dogfood target, record:

```text
codesleuthCandidateSha
hostedAcceptanceRunId
hostedAcceptanceResult = 7/7 PASS
```

Fail closed unless all seven canonical acceptance jobs belong to that exact SHA.

After this entry gate is satisfied, do not modify the CodeSleuth candidate branch. Any tracked CodeSleuth edit creates a new candidate and returns status to `CLOUD_TESTABILITY_REMAINING` until fresh hosted acceptance passes.

## 3. Target isolation

Use a disposable clean clone/worktree or another target environment whose pre-existing local state is understood.

For each target:

1. record target repository exact `HEAD`;
2. record branch/ref only as navigation metadata, never as identity;
3. record `git status --short` before the run;
4. do not modify application source, planning docs, ADRs, tests, workflows, accepted target policy, tracked dependency pins, or target-local Git configuration;
5. if CodeSleuth installation/materialization is required, keep it in a disposable/local integration surface and verify that no unintended tracked target changes result;
6. record `git status --short` after the run and compare it with the pre-run state.

A dogfood run that silently edits the target is invalid.

### Read-only hard stop

Do not repair the target in place during dogfood. A discovery or verification failure is evidence to record, not permission to make the target easier to analyze.

In particular:

- do not change `git config` to alter quoting, path handling, hooks, remotes, line endings, safe-directory state, or other repository behavior; read-only queries such as `git config --get` are observations, not repair;
- do not perform a package-manager or dependency update, install a different project dependency, rewrite a lockfile, or switch a tracked runtime/plugin pin merely to let CodeSleuth continue;
- do not start editing target source/policy to satisfy a gate;
- if the installed host or target dependency is incompatible, report the observed identities and the mismatch rather than mutating one side.

If normal continuation would require any such mutation, stop that path with `READ_ONLY_BOUNDARY_BLOCKED`, preserve the exact failing command/observation and required external remediation, and leave the target unchanged.

Every Playbook Step whose manifest requires `fresh_subagent` must use host-native Step isolation when the host provides it. If the host cannot prove that a fresh child was materialized, record `STEP_ISOLATION_UNPROVEN` before any same-session fallback. Do not claim strict isolation, context eviction, or a fully isolated dogfood path when that status is present.

## 4. Common live workflow

For each repository, execute the normal installed continuation surface, not private test helpers:

```text
/repo-continue
```

The host remains the controller. CodeSleuth supplies bounded Skills, Playbook Steps and deterministic state/tools.

Capture at least:

- exact target SHA;
- `DevelopmentAuthorityMap` or equivalent bounded authority result;
- selected canonical planning authority;
- selected active implementation scope;
- prerequisites and accepted predecessors;
- required reading;
- `pathScopeAuthority` plus any repository-declared allowed paths;
- forbidden or adjacent paths/tracks;
- deterministic pre-registry change surface;
- `NativeGateMap`;
- `repoProvableChecks`;
- `hostedCiProvableChecks`;
- `liveRuntimeRequiredChecks`;
- `operatorDecisionRequired`;
- blockers and uncertainties;
- bounded `authorityEvidence` with exact tracked path/blob/locator identity;
- any `STEP_ISOLATION_UNPROVEN` or `READ_ONLY_BOUNDARY_BLOCKED` condition;
- final cloud/live handoff classification.

No finding is accepted merely because a filename looks canonical or because a model says a document sounds authoritative.

## 5. PII Parser live dogfood

Target repository: `DassaultFalconKing/PII_PARSER`.

### Acceptance intent

The run must demonstrate the layered planning/worklog pattern that motivated Fixture A without containing PII-specific CodeSleuth code.

Expected behavior on the live exact target:

1. identify the exact current target HEAD;
2. discover the repository-declared canonical planning/TODO/worklog authority from tracked evidence;
3. classify older/superseded roadmaps and shipped archives as non-current rather than reviving them as predecessors;
4. preserve supporting current-state evidence as supporting evidence, not competing planning authority;
5. select the earliest unresolved admissible critical-path/stop-gate work item according to current repository authority rather than aggregating later rollout stages;
6. preserve `pathScopeAuthority = NOT_DECLARED` when repository authority does not declare a positive path allowlist instead of inventing one;
7. separate repository/CI-provable checks from service/runtime-only proof;
8. expose uncertainty if the live repository has evolved beyond the pattern captured by the earlier audit instead of forcing the historical answer;
9. produce a continuation packet with no source/configuration modification.

### Failure conditions

Fail the dogfood if CodeSleuth:

- selects a superseded roadmap over explicitly declared current authority;
- promotes historical/shipped material into `acceptedPredecessors` without a confirmed `ACCEPTED_PREDECESSOR` relation;
- aggregates later rollout stages before the current stop-gate closes;
- invents a new roadmap/session packet or positive allowed-path authority;
- treats runtime observations as repository authority;
- reports a live-only gate as cloud-complete without evidence;
- imports CodeSleuth's own protected-capability/SIB history into the foreign target;
- modifies target project source, configuration or policy.

## 6. Aleph Rugent live dogfood

Target repository: `DassaultFalconKing/Aleph_Rugent`.

### Acceptance intent

The run must demonstrate the waypoint/session-packet pattern that motivated Fixture B without containing Aleph-specific CodeSleuth code.

Expected behavior on the live exact target:

1. identify the exact current target HEAD;
2. reconstruct the repository-native authority chain among Orientation/current session packet/handoff/Waypoint/accepted architecture and gate documents;
3. select the active implementation session from evidence;
4. preserve accepted predecessor and required-reading relationships;
5. keep adjacent parallel tracks distinct from accepted predecessors;
6. distinguish allowed paths from exclusions and adjacent parallel tracks;
7. derive a bounded structural change surface including tracked directory seeds, package ownership/reverse consumers, migrations/embedded files, tests and authority-named verification surfaces where exact evidence supports them;
8. enumerate native repository/CI/live gates without replacing them with generic CodeSleuth gates;
9. treat absence of a protected-capability registry as a brownfield-bootstrap opportunity, not permission to substitute CodeSleuth's own registry;
10. produce a continuation packet with no source/configuration modification.

### Failure conditions

Fail the dogfood if CodeSleuth:

- chooses a session based only on filename/recentness without authority evidence;
- mixes an adjacent parallel track into active scope or also labels it an accepted predecessor;
- loses accepted predecessor/handoff constraints;
- claims a protected registry exists when it does not;
- invents native verification commands that the repository does not declare;
- supplies nonexistent future paths as deterministic change-surface seeds;
- modifies target project source, configuration or policy.

## 7. Live evidence recording

Live observations that need durable capture must use `ExternalEvidenceManifestV1` or the accepted RC6 evidence boundary.

Every captured live observation must bind:

```text
repositorySha
observedAt
freshnessTtlSeconds
checkId
sourceKind
sanitizedResult
evidenceLocator
nativeOutcome
notes
```

Do not persist secrets or raw credentials. A runtime observation cannot promote itself into repository contract authority.

## 8. Pass criteria

RC6 live dogfood passes only when both repositories produce useful bounded continuation packets and all of the following remain true:

- exact target identity is explicit;
- planning/scope authority is evidence-bound;
- no competing roadmap/session authority is invented;
- semantic roles such as predecessor/history/adjacent track are not contradictory;
- scope exclusions/adjacent tracks are preserved;
- native gates are separated by cloud/live/operator class;
- deterministic structural change-surface derivation completes without target repair;
- no target-specific CodeSleuth implementation was needed;
- target source/configuration/policy remains unmodified;
- limitations, isolation uncertainty and environment drift are visible rather than guessed away.

Dogfood PASS does not by itself promote refs or assign SIB status. It is an input to the later exact release-stream candidate and fresh EHA defined by RC6 section 10.

## 9. Stop conditions

Stop and report the run as incomplete rather than improvising when:

- the CodeSleuth candidate is not the exact hosted-green SHA;
- target HEAD changes during evidence collection;
- target authority is genuinely contradictory or unproven;
- a required native gate needs credentials/service access that the host does not have;
- completing the check would require source/policy/configuration/dependency edits;
- the host cannot expose the installed RC6 command/Playbook/tool surfaces;
- required `fresh_subagent` isolation cannot be proven and the acceptance claim depends on it;
- required evidence would reveal secrets.

The correct output in these cases is a bounded blocker/uncertainty, not a convenient synthetic PASS.
