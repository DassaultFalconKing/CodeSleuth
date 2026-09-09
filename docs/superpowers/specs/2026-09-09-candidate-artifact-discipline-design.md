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
    + AcceptanceEvidenceRefs when acceptance references exist
= CandidateArtifactV1
```

Canonical policy:

```text
No manifest, no candidate.
No exact artifact hash, no runtime claim.
No exact source commit/tree, no build/test claim.
No evidence digest, no evidence-bound claim.
No domain acceptance evidence, no known-good claim.
```

A manifest is evidence-bearing identity metadata. It is not acceptance authority by itself.

## 4. Authority model

### 4.1 Existing upstream authorities remain unchanged

The feature consumes, but does not replace:

- Git tracked source and exact commit/tree/blob identity;
- CodeSleuth exact-head acceptance semantics where CodeSleuth acceptance applies;
- project-native acceptance policy for external target projects;
- release-stream candidate selection semantics for CodeSleuth itself;
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

If a derived view disagrees with exact Git identity, manifest digests, or authoritative domain acceptance evidence, the derived view loses.

### 4.3 Convenience refs

A `freeze/*`, `test/*`, `scratch/*`, or similar branch may improve navigation but never carries acceptance by itself. Acceptance remains attached to exact evidence identity under the owning domain's acceptance contract.

## 5. CandidateArtifactV1

The first machine-readable contract is a JSON manifest validated by one checked-in JSON Schema shipped with the installed CodeSleuth pack.

The sole machine-readable schema authority for v1 is:

```text
pack/.opencode/contracts/candidate-artifact-v1.schema.json
```

Human documentation points to that schema; it does not maintain a second copy.

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
      "version": "recorded runtime identity"
    }
  },
  "artifact": {
    "path": "ovms.exe",
    "sha256": "64-hex",
    "sizeBytes": 123456789
  },
  "tests": {
    "summary": "test-summary.json",
    "summarySha256": "64-hex",
    "overall": "PASS"
  },
  "runtime": {
    "evidence": "runtime/launch.json",
    "evidenceSha256": "64-hex"
  },
  "candidateStatus": "TESTED_PASS",
  "acceptance": {
    "claim": "PENDING",
    "evidenceRefs": []
  }
}
```

The schema is intentionally generic. It does not encode OVMS, Bazel, PowerShell, Windows, or Gemmamonster as universal CodeSleuth assumptions.

## 6. Candidate status versus acceptance claim

Artifact/test state and domain acceptance are deliberately separate axes.

### 6.1 `candidateStatus`

Initial candidate-status vocabulary:

```text
BUILT_NOT_TESTED
TESTED_FAIL
TESTED_PASS
EVIDENCE_INCOMPLETE
UNKNOWN
```

Rules:

- `TESTED_PASS` requires a present test summary and matching `summarySha256`;
- `TESTED_FAIL` retains the failing summary/evidence rather than deleting or rewriting it;
- `EVIDENCE_INCOMPLETE` means a claimed or required binding is absent, not that tests failed;
- malformed/unreadable evidence is not equivalent to missing evidence;
- `UNKNOWN` is used when trust cannot be established without inventing a stronger state.

### 6.2 `acceptance.claim`

Initial acceptance-reference vocabulary:

```text
NONE
PENDING
FAIL_REFERENCED
PASS_REFERENCED
```

`PASS_REFERENCED` means only that the manifest contains digest-bound references to a PASS produced by the owning acceptance domain. It does **not** mean the manifest or generic verifier has promoted that PASS into a CodeSleuth acceptance decision.

A known-good/accepted projection may be derived only when the owning domain's acceptance adapter or contract validates those references.

This prevents `candidate.manifest.json` from becoming a second acceptance ledger by writing `"status": "ACCEPTED"` into itself.

### 6.3 Failure taxonomy

The verifier must distinguish at minimum:

```text
MISSING
MALFORMED
HASH_MISMATCH
SOURCE_IDENTITY_MISMATCH
RUNTIME_IDENTITY_MISMATCH
EVIDENCE_UNTRUSTED
PATH_ESCAPE
DIRTY_SOURCE
```

from ordinary absent optional fields and from actual test failure.

## 7. Exact source identity

Existing exact-target identity remains the source identity primitive.

The additive extension is `treeSha` alongside the exact commit SHA. Mutable branch/ref values remain presentation context only.

No existing no-argument/default output or consumer contract may be broken merely to add tree identity. If the current Skill is documentation-only, its atomic output contract is extended additively. If implementation code exposes a public machine shape, that shape must be versioned or extended compatibly and protected by old-caller tests.

A tree SHA must never be labelled or reported as a commit SHA.

### 7.1 Clean-source requirement for v1

`CandidateArtifactV1` v1 requires:

```text
source.dirty == false
```

A dirty worktree can still produce useful experimental build logs, but it is not a valid v1 candidate because commit SHA + tree SHA do not identify staged, unstaged, or untracked source bytes.

Future schema versions may define a canonical dirty-source identity using explicit staged/unstaged/untracked content digests. V1 does not pretend that problem is solved.

## 8. Build responsibility

CodeSleuth does not become a universal build system.

Project-native wrappers remain responsible for invoking the actual build. They may emit `candidate.manifest.json` directly or provide sufficient outputs for CodeSleuth tooling to assemble/verify the manifest.

The first CodeSleuth implementation owns bounded deterministic operations only:

```text
verify manifest
verify artifact hash
verify referenced evidence hashes
inspect candidate
assemble evidence bundle
render bounded handoff
```

It must not infer a build command from project contents and execute it as a new autonomous controller.

## 9. Installed portability boundary

The verifier must work in an ordinary installed CodeSleuth target, not only inside the CodeSleuth source checkout.

Therefore the portable runtime helper belongs in the installed pack, for example:

```text
pack/.opencode/bin/candidate_artifact.py
```

The machine schema it consumes belongs beside the installed pack contract:

```text
pack/.opencode/contracts/candidate-artifact-v1.schema.json
```

Repo-level `scripts/` may contain contributor/test wrappers later, but the core user-facing candidate verifier must not depend on source-checkout-only files.

This implementation must preserve the existing install/update/uninstall ownership model; no second installer is introduced.

## 10. Candidate-directory and path confinement

The first implementation uses a candidate directory as its filesystem trust boundary.

All manifest-owned relative paths such as:

```text
artifact.path
tests.summary
runtime.evidence
acceptance.evidenceRefs[*].path
```

must resolve inside that candidate directory.

The verifier fails closed on:

- absolute paths when a relative candidate path is required;
- `..` traversal escaping the candidate directory;
- symlink/reparse-point resolution escaping the candidate directory;
- missing referenced files;
- path/file type mismatch.

An external artifact vault may be supported later through an explicit locator type plus mandatory content digest. V1 does not silently treat arbitrary filesystem paths as trusted candidate contents.

## 11. Runtime identity

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

## 12. Acceptance evidence references

`acceptance.evidenceRefs` are structured digest-bound references, not arbitrary prose strings.

Minimum logical shape:

```json
{
  "kind": "project-native",
  "path": "acceptance/live-summary.json",
  "sha256": "64-hex",
  "sourceCommitSha": "40-hex",
  "artifactSha256": "64-hex"
}
```

The generic verifier proves only:

- the referenced bytes exist inside the candidate boundary;
- their digest matches;
- their declared source/artifact identities match the manifest.

It does not infer that an arbitrary `project-native` file is semantically authoritative. A project-specific/domain adapter is responsible for interpreting its acceptance meaning.

For CodeSleuth's own EHA/SIB acceptance, the existing exact-head/EHA domain remains authority. CandidateArtifactV1 may reference that evidence; it may not replace or rewrite it.

## 13. Evidence bundle

A candidate bundle is retained evidence packaging, not a new authority plane.

Recommended content:

```text
candidate.manifest.json
candidate.manifest.sha256
artifact binary or explicit future locator
test-summary.json
build.log
runtime/
acceptance/
git/
known-failures.md
handoff.json
sha256sums.txt
bundle.sha256
```

The bundle must bind its contents transitively:

```text
bundle digest
 -> manifest digest
 -> artifact digest
 -> source commit/tree identity
 -> test/runtime/acceptance evidence digests
```

V1 expects the managed artifact to live inside the candidate directory. Large external-vault locators are deferred until they have an explicit locator and trust contract.

## 14. Branch-lane discipline

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
 -> domain acceptance
 -> optional navigation freeze ref
```

No diagonal or reverse transition may be interpreted as promotion evidence merely from branch ancestry or naming.

The first implementation does not automatically mutate integration/release/freeze refs.

## 15. Branch ledger and known-good registry

A branch ledger and known-good index are useful operator projections, but they are generated/read-only summaries.

A future renderer may produce:

```text
docs/candidates/BRANCH-LEDGER.md
docs/candidates/KNOWN-GOOD.md
candidate-registry.json
```

from exact refs, manifests, and domain acceptance evidence.

The first implementation may provide rendering hooks or a simple deterministic report, but must not make any of these files writable acceptance authority.

## 16. Agent handoff contract

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

## 17. First implementation slice

The implementation should remain deliberately small:

```text
docs/CANDIDATE-ARTIFACT-DISCIPLINE.md
pack/.opencode/contracts/candidate-artifact-v1.schema.json
pack/.opencode/bin/candidate_artifact.py
pack/.opencode/skills/candidate-artifact-discipline/SKILL.md
existing exact-target-identity Skill additive treeSha contract
tests/test_candidate_artifact_contract.py
relevant skill/publication/lifecycle/smoke-parity test wiring
```

A dedicated Playbook may be added only if existing workflow composition cannot express the sequence cleanly. Prefer reusing current exact-target and acceptance Skills rather than duplicating them.

## 18. Explicitly out of scope for the first slice

Do not implement yet:

- a universal build engine;
- a universal launch/process supervisor;
- automatic branch promotion;
- automatic freeze-ref creation;
- an artifact database/service;
- a generic artifact marketplace;
- external-vault artifact locators;
- dirty-source candidate identity;
- mandatory Gemmamonster/OVMS-specific fields in the portable schema;
- rewriting existing EHA ledger semantics;
- a second candidate persistence ledger competing with existing durable state.

## 19. Validation behavior

The verifier is fail-closed for identity claims.

Examples:

1. manifest missing → `NOT_A_CANDIDATE`;
2. dirty source in v1 → `DIRTY_SOURCE`;
3. artifact missing → invalid artifact claim, not `TESTED_FAIL`;
4. artifact digest mismatch → invalid candidate identity;
5. source commit/tree malformed → invalid candidate identity;
6. test summary missing while `candidateStatus == TESTED_PASS` → invalid claim;
7. acceptance claim `PASS_REFERENCED` without evidence refs → invalid claim;
8. runtime artifact digest differs from manifest artifact digest → runtime claim invalid;
9. branch/ref moved but commit/tree/hash remain exact → mutable label may be stale, exact identity remains primary;
10. malformed evidence is surfaced as untrusted/corrupt, never collapsed into absent evidence;
11. relative path escaping the candidate directory → `PATH_ESCAPE`.

Validation errors must be deterministic and machine-readable enough for tests and agent handoffs.

## 20. Testing strategy

Implementation follows tests-first development.

### Contract/schema tests

Cover:

- valid minimal clean candidate;
- full candidate with runtime/test/acceptance references;
- dirty source rejection;
- bad commit SHA;
- bad tree SHA;
- tree/commit field confusion witness;
- missing artifact;
- wrong artifact SHA-256;
- wrong summary SHA-256;
- `TESTED_PASS` without summary digest;
- `PASS_REFERENCED` without acceptance refs;
- acceptance ref digest mismatch;
- runtime artifact mismatch;
- malformed versus missing evidence;
- mutable branch label change does not replace exact identity;
- `..` path traversal;
- absolute-path rejection;
- symlink/path escape where supported by the test platform.

### Compatibility tests

Protect existing exact-target identity behavior and all old callers while adding `treeSha`.

### Installed-layout tests

Prove that the verifier, schema, and Skill survive normal pack materialization/install/update and are removed/restored through existing lifecycle ownership.

### Canonical reachability

Every new critical Python contract test must be reached by the existing default `python -m pytest -q` acceptance job. No new critical test may exist only as an ad-hoc command.

If a future Bun/TypeScript smoke is added, it must either be in the default `bun run test` umbrella or have a dedicated canonical non-skipped workflow job.

## 21. Contributor error-pattern closure

The design closes the relevant mandatory semantic checklist as follows:

- **SC-01 exact identity:** exact predecessor is pinned; commit/tree/hash are primary identities.
- **SC-02 scope authority:** implemented as hardening of existing identity/acceptance infrastructure; no new architecture authority is introduced.
- **SC-03 old callers:** `treeSha` is additive and old caller/default behavior must remain covered.
- **SC-04 failure vs absence:** explicit missing/malformed/hash-mismatch/untrusted/path-escape states are required.
- **SC-05 support matrix:** portable schema does not advertise project runtime support; target-specific support claims require target evidence.
- **SC-06 canonical gates:** new critical tests must be reachable from the existing canonical umbrella, including installed-layout witnesses.
- **SC-07 execution identity:** build toolchain and runtime/artifact identity are recorded explicitly when they matter.
- **SC-08 evidence wording:** PASS claims require exact evidence; manifest `PASS_REFERENCED` is explicitly weaker than domain acceptance.
- **SC-09 external output:** external build/test/runtime/acceptance metadata remains candidate data until CodeSleuth verifies hashes/identity and the owning domain validates semantics.
- **SC-10 optional lifecycle:** no optional runtime/dependency is introduced by the first slice; the verifier itself is installed/removed through the existing pack lifecycle.

The exact predecessor `3dbc2328ed091cbd793983edefc6e64a4c001343` had a successful hosted `contributor_antipatterns.py scan --strict` during acceptance. In the current tool environment the literal local `prewrite` command could not be executed because the sandbox could not resolve GitHub for a checkout; this design therefore records the hosted mechanical gate evidence and performs the semantic checklist explicitly rather than claiming an unexecuted local command.

## 22. Acceptance and promotion

Feature-branch green tests prove only the feature candidate.

Before integration:

1. run the strict contributor anti-pattern scanner on the changed branch;
2. run focused contract tests;
3. run full Python tests and lint;
4. run lifecycle/smoke-parity and any protected-capability dependency-closure tests;
5. obtain hosted exact-head acceptance for the feature head as required by the active RC7 integration discipline;
6. integrate only through the coordinator-selected RC7 stream;
7. treat the resulting integration commit as a new exact candidate requiring its own evidence when an accepted integration/RC/SIB claim is made.

The feature branch must not self-merge into `integration/rc7`, `main`, `SIB`, `dev/release-0.4.0`, tags, or releases.

## 23. Success criteria

The first implementation is complete when CodeSleuth can deterministically prove or reject all of the following for a candidate artifact:

```text
exact clean source commit identity
exact source tree identity
exact artifact SHA-256
candidate-root path confinement
exact referenced test summary SHA-256
runtime-to-artifact binding when runtime evidence exists
acceptance-reference digest/identity binding without assuming acceptance authority
candidate-status/evidence consistency
bounded machine-readable handoff state
installed-pack availability
```

and when it demonstrably does **not** acquire build-controller, runtime-controller, persistence-authority, or acceptance-authority ownership.
