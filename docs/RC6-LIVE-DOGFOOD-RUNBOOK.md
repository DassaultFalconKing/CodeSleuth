# RC6 Live Dogfood Runbook

Status: **PRE-LIVE RUNBOOK — EXECUTE ONLY AFTER FINAL EXACT-HEAD HOSTED 7/7**

Scope authority: [`RC6-FEATURE-PLAN.md`](RC6-FEATURE-PLAN.md), especially sections 8–10 and the RC6 definition of done.

Normative continuation semantics: [`DEVELOPMENT-CONTINUATION-CONTRACT.md`](DEVELOPMENT-CONTINUATION-CONTRACT.md).

## 1. Purpose

This runbook defines the first live-host acceptance boundary for RC6 evidence-bound development continuation.

The dogfood is deliberately read-only with respect to target project source. It validates that the real OpenCode/CodeSleuth host can recover project-native development authority, active scope, change surface and verification boundaries on unfamiliar mature repositories without project-specific CodeSleuth adapters.

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
4. do not modify application source, planning docs, ADRs, tests, workflows or accepted target policy;
5. if CodeSleuth installation/materialization is required, keep it in a disposable/local integration surface and verify that no unintended tracked target changes result;
6. record `git status --short` after the run and compare it with the pre-run state.

A dogfood run that silently edits the target is invalid.

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
- allowed paths;
- forbidden or adjacent paths/tracks;
- deterministic pre-registry change surface;
- `NativeGateMap`;
- `repoProvableChecks`;
- `hostedCiProvableChecks`;
- `liveRuntimeRequiredChecks`;
- `operatorDecisionRequired`;
- blockers and uncertainties;
- bounded `authorityEvidence` with exact tracked path/blob/locator identity;
- final cloud/live handoff classification.

No finding is accepted merely because a filename looks canonical or because a model says a document sounds authoritative.

## 5. PII Parser live dogfood

Target repository: `DassaultFalconKing/PII_PARSER`.

### Acceptance intent

The run must demonstrate the layered planning/worklog pattern that motivated Fixture A without containing PII-specific CodeSleuth code.

Expected behavior on the live exact target:

1. identify the exact current target HEAD;
2. discover the repository-declared canonical planning/TODO/worklog authority from tracked evidence;
3. classify older/superseded roadmaps as non-current rather than reviving them;
4. preserve supporting current-state evidence as supporting evidence, not competing planning authority;
5. select the next admissible critical-path/stop-gate work item according to current repository authority;
6. separate repository/CI-provable checks from service/runtime-only proof;
7. expose uncertainty if the live repository has evolved beyond the pattern captured by the earlier audit instead of forcing the historical answer;
8. produce a continuation packet with no source modification.

### Failure conditions

Fail the dogfood if CodeSleuth:

- selects a superseded roadmap over explicitly declared current authority;
- invents a new roadmap/session packet;
- treats runtime observations as repository authority;
- reports a live-only gate as cloud-complete without evidence;
- imports CodeSleuth's own protected-capability/SIB history into the foreign target;
- modifies target project source or policy.

## 6. Aleph Rugent live dogfood

Target repository: `DassaultFalconKing/Aleph_Rugent`.

### Acceptance intent

The run must demonstrate the waypoint/session-packet pattern that motivated Fixture B without containing Aleph-specific CodeSleuth code.

Expected behavior on the live exact target:

1. identify the exact current target HEAD;
2. reconstruct the repository-native authority chain among Orientation/current session packet/handoff/Waypoint/accepted architecture and gate documents;
3. select the active implementation session from evidence;
4. preserve accepted predecessor and required-reading relationships;
5. distinguish allowed paths from exclusions and adjacent parallel tracks;
6. enumerate native repository/CI/live gates without replacing them with generic CodeSleuth gates;
7. treat absence of a protected-capability registry as a brownfield-bootstrap opportunity, not permission to substitute CodeSleuth's own registry;
8. produce a continuation packet with no source modification.

### Failure conditions

Fail the dogfood if CodeSleuth:

- chooses a session based only on filename/recentness without authority evidence;
- mixes an adjacent parallel track into active scope;
- loses accepted predecessor/handoff constraints;
- claims a protected registry exists when it does not;
- invents native verification commands that the repository does not declare;
- modifies target project source or policy.

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
- scope exclusions/adjacent tracks are preserved;
- native gates are separated by cloud/live/operator class;
- no target-specific CodeSleuth implementation was needed;
- target source/policy remains unmodified;
- limitations and environment drift are visible rather than guessed away.

Dogfood PASS does not by itself promote refs or assign SIB status. It is an input to the later exact release-stream candidate and fresh EHA defined by RC6 section 10.

## 9. Stop conditions

Stop and report the run as incomplete rather than improvising when:

- the CodeSleuth candidate is not the exact hosted-green SHA;
- target HEAD changes during evidence collection;
- target authority is genuinely contradictory or unproven;
- a required native gate needs credentials/service access that the host does not have;
- completing the check would require source/policy edits;
- the host cannot expose the installed RC6 command/Playbook/tool surfaces;
- required evidence would reveal secrets.

The correct output in these cases is a bounded blocker/uncertainty, not a convenient synthetic PASS.
