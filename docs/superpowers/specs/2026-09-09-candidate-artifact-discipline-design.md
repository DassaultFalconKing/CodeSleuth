# Candidate Artifact Discipline Design

**Status:** proposed design, user-approved in chat; implementation not yet started  
**Date:** 2026-09-09  
**Target repository:** `DassaultFalconKing/CodeSleuth`  
**Implementation branch:** `feature/rc7-candidate-artifact-discipline`  
**Design predecessor:** `integration/rc7@3dbc2328ed091cbd793983edefc6e64a4c001343`

## 1. Purpose

CodeSleuth already binds acceptance claims to exact Git commit identity. This design extends that evidence discipline across the gap between source identity and built/runtime artifacts.

The feature answers three questions deterministically:

1. Which exact source state produced this candidate artifact?
2. Which exact bytes were executed?
3. Which test/runtime/acceptance evidence belongs to those exact bytes?

The feature must prevent branch labels, artifact filenames, remembered terminal output, generated reports, or convenience refs from substituting for exact identity.

## 2. Architectural classification

This is **feature population and hardening inside existing CodeSleuth capability classes**, not a new execution, persistence, build, or acceptance authority.

The feature may strengthen:

- exact identity capture;
- acceptance infrastructure;
- retained evidence packaging;
- agent handoff discipline;
- read-only/derived candidate registries.

It must not create:

- a second controller or scheduler;
- a general-purpose build runtime;
- a process supervisor that competes with the host;
- a second durable evidence database;
- a second acceptance authority;
- a replacement release-stream promotion authority.

The active host and target project continue to own command execution. Existing CodeSleuth durable review/EHA state remains authoritative for CodeSleuth review and acceptance evidence.

## 3. Core invariant

A built binary is not a candidate merely because it exists.

A candidate is a bound identity envelope:

```text
SourceIdentity
    + BuildIdentity
    + ArtifactIdentity
    + RuntimeIdentity when runtime claims exist
    + TestEvidenceRefs when test claims exist
    + AcceptanceEvidenceRefs when acceptance claims exist
= CandidateArtifactV1
```

Canonical policy:

```text
No manifest, no candidate.
No exact artifact hash, no runtime claim.
No exact source commit, no build/test claim.
No evidence reference, no acceptance claim.
No exact-head evidence, no known-good claim.
```

A manifest is evidence-bearing identity metadata. It is not acceptance authority by itself.

## 4. Authority model

### 4.1 Existing upstream authorities remain unchanged

The feature consumes, but does not replace:

- Git tracked source and exact commit/tree/blob identity;
- CodeSleuth exact-head acceptance semantics;
- release-stream candidate selection semantics;
- existing durable review/EHA evidence;
- project-native build/test/runtime commands.

### 4.2 Derived representations

The following are explicitly non-authoritative derived views:

- `KNOWN-GOOD.md`-style human registries;
- branch ledgers;
- candidate registry JSON generated from manifests/evidence;
- bundle indexes;
- summary tables;
- convenience `freeze/*` refs.

If a derived view disagrees with exact Git identity, manifest digests, or authoritative acceptance evidence, the derived view loses.

### 4.3 Convenience refs

A `freeze/*`, `test/*`, `scratch/*`, or similar branch may improve navigation but never carries acceptance by itself. Acceptance remains attached to exact evidence identity.

## 5. CandidateArtifactV1

The first machine-readable contract is a JSON manifest validated by a checked-in JSON Schema.

Minimum logical shape:

```json
{
  "schemaVersion": 1,
  "project": "Gemmamonster",
  "repository": "DassaultFalconKing/model_server",
  "source": {
    "commitSha": "40-hex",
    "treeSha": "40-hex",
    "branch": "optional mutable display context",
    "dirty": false
  },
  "build": {
    "profile": "project-defined profile id",
    "command": "recorded build command",
    "toolchain": {
      "name": "bazel",
      "version": "exact or bounded recorded identity"
    }
  },
  "artifact": {
    "path": "relative/path/to/artifact",
    "sha256": "64-hex",
    "sizeBytes": 123456789
  },
  "runtime": {
    "launchProfile": "optional project-defined profile",
    "modelIdentity": "optional model/revision identity",
    "runtimeEvidence": "optional relative evidence path"
  },
  "tests": {
    "summary": "optional relative summary path",
    "summarySha256": "optional 64-hex",
    "overall": "NOT_RUN"
  },
  "acceptance": {
    "status": "BUILT_NOT_TESTED",
    "evidenceRefs": []
  }
}
```

The schema is intentionally generic. It does not encode OVMS, Bazel, PowerShell, Windows, or Gemmamonster as universal CodeSleuth assumptions.

## 6. Status vocabulary

Candidate status must not be free-form prose.

Initial values:

```text
BUILT_NOT_TESTED
TESTED_FAIL
TESTED_PASS
ACCEPTANCE_PENDING
ACCEPTED
REJECTED
UNKNOWN
```

Rules:

- `ACCEPTED` requires one or more acceptance evidence references whose exact identity can be checked.
- `TESTED_PASS` requires a present test summary digest.
- `TESTED_FAIL` must retain the failing summary/evidence rather than delete or rewrite it.
- missing evidence is not equivalent to failure;
- malformed/unreadable evidence is not equivalent to missing evidence;
- `UNKNOWN` is used when trust cannot be established without inventing a stronger state.

The verifier must distinguish at minimum:

```text
MISSING
MALFORMED
HASH_MISMATCH
SOURCE_IDENTITY_MISMATCH
RUNTIME_IDENTITY_MISMATCH
EVIDENCE_UNTRUSTED
```

from ordinary absent optional fields.

## 7. Exact source identity

Existing exact-target identity remains the source identity primitive.

The additive extension is `treeSha` alongside the exact commit SHA. Mutable branch/ref values remain presentation context only.

No existing no-argument/default output or consumer contract may be broken merely to add tree identity. If the current Skill is documentation-only, its atomic output contract is extended additively. If implementation code exposes a public machine shape, that shape must be versioned or extended compatibly and protected by old-caller tests.

A tree SHA must never be labelled or reported as a commit SHA.

## 8. Build responsibility

CodeSleuth does not become a universal build system.

Project-native wrappers remain responsible for invoking the actual build. They may emit `candidate.manifest.json` directly or provide sufficient outputs for CodeSleuth tooling to assemble/verify the manifest.

The first CodeSleuth implementation owns bounded deterministic operations only:

```text
verify manifest
verify artifact hash
verify referenced evidence hash
inspect candidate
assemble evidence bundle
render bounded handoff
```

It must not infer a build command from project contents and execute it as a new autonomous controller.

## 9. Runtime identity

Runtime claims require evidence binding the running process/invocation to the exact artifact bytes.

A project wrapper may emit a runtime evidence object such as:

```json
{
  "schemaVersion": 1,
  "pid": 12345,
  "artifactPath": "...",
  "artifactSha256": "...",
  "sourceCommitSha": "...",
  "sourceTreeSha": "...",
  "command": "...",
  "port": 8000,
  "modelIdentity": "...",
  "startedAt": "2026-09-09T19:07:00Z"
}
```

CodeSleuth validates this evidence when present. It does not universally own process launch, PID lifecycle, port termination, or model serving.

A project may adopt a stricter local policy such as “never run the managed binary directly; always use `launch-candidate.ps1`.” CodeSleuth expresses the portable invariant instead:

> A runtime claim is inadmissible when the executed artifact identity is not bound to exact bytes and exact source identity.

## 10. Evidence bundle

A candidate bundle is retained evidence packaging, not a new authority plane.

Recommended content:

```text
candidate.manifest.json
candidate.manifest.sha256
test-summary.json
build.log
runtime/
git/
known-failures.md
handoff.json
bundle.sha256
```

The bundle must bind its contents transitively:

```text
bundle digest
 -> manifest digest
 -> artifact digest
 -> source commit/tree identity
 -> test/runtime evidence digests
```

The first implementation does not require CodeSleuth to store arbitrary large binaries in Git. Manifest paths may refer to an external/project artifact vault, but hashes remain mandatory for claims about those bytes.

## 11. Branch-lane discipline

CodeSleuth supports a lane vocabulary without hard-coding one repository's exact branch names into core logic:

```text
scratch
work/test
integration
release
freeze/navigation
```

A project profile may map these to names such as:

```text
scratch/<agent>/<topic>-<date>
test/<project>-gateXX-<date>-<base>
integration/<topic>
dev/release-X.Y.Z
freeze/<project>-<date>-known-good-<sha>
```

The portable semantic direction is:

```text
work/test
 -> verified artifact/evidence
 -> integration/release composition
 -> exact-head acceptance
 -> optional navigation freeze ref
```

No diagonal or reverse transition may be interpreted as promotion evidence merely from branch ancestry or naming.

The first implementation does not automatically mutate integration/release/freeze refs.

## 12. Branch ledger and known-good registry

A branch ledger and known-good index are useful operator projections, but they are generated/read-only summaries.

A future renderer may produce:

```text
docs/candidates/BRANCH-LEDGER.md
docs/candidates/KNOWN-GOOD.md
candidate-registry.json
```

from exact refs, manifests, and acceptance evidence.

The first implementation may provide rendering hooks or a simple deterministic report, but must not make any of these files writable acceptance authority.

## 13. Agent handoff contract

A machine/human handoff should use one stable vocabulary:

```text
BRANCH:
BASE_SHA:
HEAD_SHA:
TREE_SHA:
COMMITS:
FILES_CHANGED:

BUILD:
BINARY_SHA256:

TESTS:
TEST_SUMMARY_SHA256:

RUNTIME:
RUNTIME_ARTIFACT_SHA256:

KNOWN_FAILURES:
ARTIFACTS:
BUNDLE_SHA256:

ACCEPTANCE:
PROMOTION_RECOMMENDATION:
```

Allowed evidence states:

```text
PASS
FAIL
NOT_RUN
UNKNOWN
BLOCKED
```

A `PASS` line must identify the command/profile and retained evidence sufficient to support the claim. Unsupported wording such as “probably works”, “should be fine”, “tests passed earlier”, or equivalent is non-evidence.

## 14. First implementation slice

The implementation should remain deliberately small:

```text
docs/CANDIDATE-ARTIFACT-DISCIPLINE.md
docs/schemas/candidate-artifact-v1.schema.json
scripts/candidate_artifact.py
pack/.opencode/skills/candidate-artifact-discipline/SKILL.md
existing exact-target-identity Skill additive treeSha contract
tests/test_candidate_artifact_contract.py
relevant Skill/publication/umbrella test wiring
```

A dedicated Playbook may be added only if existing workflow composition cannot express the sequence cleanly. Prefer reusing current exact-target and acceptance Skills rather than duplicating them.

## 15. Explicitly out of scope for the first slice

Do not implement yet:

- a universal build engine;
- a universal launch/process supervisor;
- automatic branch promotion;
- automatic freeze-ref creation;
- an artifact database/service;
- binary uploads to Git;
- a generic artifact marketplace;
- mandatory Gemmamonster/OVMS-specific fields in the portable schema;
- rewriting existing EHA ledger semantics;
- a second candidate persistence ledger competing with existing durable state.

## 16. Validation behavior

The verifier is fail-closed for identity claims.

Examples:

1. manifest missing → `NOT_A_CANDIDATE`;
2. artifact missing → invalid artifact claim, not `TESTED_FAIL`;
3. artifact digest mismatch → invalid candidate identity;
4. source commit/tree malformed → invalid candidate identity;
5. test summary missing while status says `TESTED_PASS` → invalid claim;
6. acceptance evidence absent while status says `ACCEPTED` → invalid claim;
7. runtime artifact digest differs from manifest artifact digest → runtime claim invalid;
8. branch/ref moved but commit/tree/hash remain exact → mutable label may be stale, exact identity remains primary;
9. malformed evidence is surfaced as untrusted/corrupt, never collapsed into absent evidence.

Validation errors must be deterministic and machine-readable enough for tests and agent handoffs.

## 17. Testing strategy

Implementation follows tests-first development.

### Contract/schema tests

Cover:

- valid minimal candidate;
- full candidate with runtime/test/acceptance evidence;
- bad commit SHA;
- bad tree SHA;
- tree/commit field confusion witness;
- missing artifact;
- wrong artifact SHA-256;
- wrong summary SHA-256;
- `TESTED_PASS` without summary digest;
- `ACCEPTED` without acceptance refs;
- runtime artifact mismatch;
- malformed versus missing evidence;
- mutable branch label change does not replace exact identity.

### Compatibility tests

Protect existing exact-target identity behavior and all old callers while adding `treeSha`.

### Canonical reachability

Every new critical Python contract test must be reached by the existing default `python -m pytest -q` acceptance job. No new critical test may exist only as an ad-hoc command.

If a future Bun/TypeScript smoke is added, it must either be in the default `bun run test` umbrella or have a dedicated canonical non-skipped workflow job.

## 18. Contributor error-pattern closure

The design closes the relevant mandatory semantic checklist as follows:

- **SC-01 exact identity:** exact predecessor is pinned; commit/tree/hash are primary identities.
- **SC-02 scope authority:** implemented as hardening of existing identity/acceptance infrastructure; no new architecture authority is introduced.
- **SC-03 old callers:** `treeSha` is additive and old caller/default behavior must remain covered.
- **SC-04 failure vs absence:** explicit missing/malformed/hash-mismatch/untrusted states are required.
- **SC-05 support matrix:** portable schema does not advertise project runtime support; target-specific support claims require target evidence.
- **SC-06 canonical gates:** new critical tests must be reachable from the existing canonical umbrella.
- **SC-07 execution identity:** build toolchain and runtime/artifact identity are recorded explicitly when they matter.
- **SC-08 evidence wording:** PASS/ACCEPTED claims require exact evidence; otherwise use NOT_RUN/UNKNOWN/BLOCKED/FAIL as appropriate.
- **SC-09 external output:** external build/test/runtime metadata remains candidate data until CodeSleuth verifies hashes and exact identity.
- **SC-10 optional lifecycle:** no optional runtime/dependency is introduced by the first slice; project-specific wrappers retain their own lifecycle contracts.

The exact predecessor `3dbc2328ed091cbd793983edefc6e64a4c001343` had a successful hosted `contributor_antipatterns.py scan --strict` during acceptance. In the current tool environment the literal local `prewrite` command could not be executed because the sandbox could not resolve GitHub for a checkout; this design therefore records the hosted mechanical gate evidence and performs the semantic checklist explicitly rather than claiming an unexecuted local command.

## 19. Acceptance and promotion

Feature-branch green tests prove only the feature candidate.

Before integration:

1. run the strict contributor anti-pattern scanner on the changed branch;
2. run focused contract tests;
3. run full Python tests and lint;
4. run any dependency-closure tests required by protected capabilities;
5. obtain hosted exact-head acceptance for the feature head as required by the active RC7 integration discipline;
6. integrate only through the coordinator-selected RC7 stream;
7. treat the resulting integration commit as a new exact candidate requiring its own evidence when an accepted integration/RC/SIB claim is made.

The feature branch must not self-merge into `integration/rc7`, `main`, `SIB`, `dev/release-0.4.0`, tags, or releases.

## 20. Success criteria

The first implementation is complete when CodeSleuth can deterministically prove or reject all of the following for a candidate artifact:

```text
exact source commit identity
exact source tree identity
clean/dirty source claim when supplied
exact artifact SHA-256
exact referenced summary SHA-256
runtime-to-artifact binding when runtime evidence exists
status/evidence consistency
bounded machine-readable handoff state
```

and when it demonstrably does **not** acquire build-controller, runtime-controller, persistence-authority, or acceptance-authority ownership.
