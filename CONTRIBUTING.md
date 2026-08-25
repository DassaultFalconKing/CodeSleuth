# Contributing to CodeSleuth

CodeSleuth uses a **Stable Integration Baseline (SIB)** discipline for release construction.

The full concept, its distinction from MVP and release, architectural eligibility criteria, and post-refactor use are defined in [`docs/STABLE-INTEGRATION-BASELINE.md`](docs/STABLE-INTEGRATION-BASELINE.md).

The SIB is not a release candidate, not a general development branch, and not a place where feature work accumulates. It is an exact repository state that has already passed the project's full acceptance gate and is therefore trusted as the starting point for building a new release.

## Stable Integration Baseline

The current CodeSleuth SIB is the `SIB` branch. At the time this policy was introduced it points to:

`c5e41a73b84e65645dec5d0a4032b19928291193`

Treat that ref as a stable construction base. Do not push feature work directly onto `SIB`.

The release-construction model is:

`SIB -> integration build -> feature composition -> acceptance -> RC -> release`

The process is:

1. **SIB fixes a known-good state.** Its defining property is evidence: the exact commit has passed the full acceptance gate.
2. **A new release starts from SIB.** Create the release/integration line from the current SIB rather than from an arbitrary development head.
3. **Add changes incrementally.** Each feature, refactor, dependency change, documentation contract change, or other meaningful delta is applied to SIB or to a descendant that has already passed acceptance.
4. **Run full acceptance after every substantial layer.** Focused tests are useful during implementation, but they do not promote an integration state.
5. **Only proven-compatible layers advance integration.** Record the exact tested commit SHA and the acceptance result. A green result on an older base is not evidence for the current composition.
6. **The completed planned composition becomes a release candidate.** RC status comes after integration is complete and accepted, not before.
7. **After release, select the next SIB deliberately.** A released or post-release commit may become the next SIB only after it is demonstrated to be a suitable known-good baseline.

## Contributor rules

- Branch from the current SIB or from an explicitly accepted descendant when working on release-bound changes.
- Do not merge a stale feature branch wholesale merely because it was once green. Rebase or transplant the intended delta onto the current accepted state and verify the resulting composition.
- Do not weaken, skip, xfail, or rewrite acceptance checks to make a feature appear compatible.
- Keep feature deltas narrow enough that their compatibility can be attributed and reviewed.
- When a change overlaps files that have evolved since the feature branch was created, preserve current semantics and re-apply the intended behavior at the semantic level rather than replacing newer files with stale blobs.
- Promotion requires exact evidence: tested commit SHA, acceptance command/workflow, and result.
- Do not advance or repoint `SIB` as a side effect of ordinary feature work. SIB promotion is a separate maintainer decision.

## Terms

**SIB**: Stable Integration Baseline. A proven, known-good starting state for construction of a new release.

**Integration build**: A descendant of SIB containing one or more candidate changes. It is provisional until it passes acceptance.

**Accepted integration state**: An integration build whose exact commit has passed the full acceptance gate. Further features may be layered on top of it.

**RC**: Release candidate. The accepted composition intended to become the release. An RC is downstream of SIB; SIB itself is not an RC.

## Acceptance

Use the repository's canonical acceptance workflow and local gates. For the current CodeSleuth release line this includes the Python matrix and the durable-state/context-graph Bun smoke checks defined by `.github/workflows/acceptance.yml`.

When documentation and implementation disagree about the gate, the canonical repository workflow is authoritative until the documentation is corrected in the same change.
