# Contributing to CodeSleuth

CodeSleuth uses a three-level **Stable Baseline** discipline for architectural recovery and release construction.

The full concept, its distinction from MVP and release, capability-class criteria, and post-refactor use are defined in [`docs/STABLE-INTEGRATION-BASELINE.md`](docs/STABLE-INTEGRATION-BASELINE.md).

The levels are:

- **SIB0 — Stable Initialization Baseline**: the fundamental capability-class inventory is represented and frozen.
- **SIB1 — Stable Implementation Baseline**: every SIB0 capability class has a real implementation satisfying its basic contract.
- **SIB2 — Stable Integration Baseline**: those implementations work together end-to-end and the exact composition passes full canonical acceptance.

The post-refactor model is:

`refactor -> SIB0 -> implementation recovery -> SIB1 -> integration recovery -> acceptance -> SIB2`

The release-construction model is:

`SIB2 -> integration build -> feature composition -> acceptance -> RC -> release`

## Current CodeSleuth baseline

The current CodeSleuth `SIB` branch is semantically an **SIB2**. At the time this policy was introduced it points to:

`c5e41a73b84e65645dec5d0a4032b19928291193`

Treat that ref as the proven integrated construction base. Do not push feature work directly onto `SIB`.

## SIB0 — architecture initialization freeze

SIB0 is reached when:

1. every fundamental capability class intended for the current architectural generation has an explicit slot, contract, boundary, module, interface, or placeholder;
2. the capability-class inventory is declared complete;
3. the list is frozen for ordinary implementation work;
4. maintainers designate the exact repository state as SIB0.

SIB0 does **not** require every capability class to be fully implemented.

Adding, removing, or fundamentally redefining a capability class after SIB0 reopens the architecture and invalidates that SIB0 lineage. Establish a new SIB0 before claiming implementation convergence again.

## SIB1 — implementation completeness

SIB1 is reached when every SIB0 capability class has a real basic implementation and satisfies its own relevant capability/component contract.

SIB1 proves:

> We implemented the architecture we froze at SIB0.

It does not yet prove that the whole system works together under every canonical integration path.

## SIB2 — integration completeness

SIB2 is reached when the SIB1 implementations work together through the intended end-to-end paths and the exact composed commit passes the repository's full canonical acceptance gate.

SIB2 proves:

> The implemented architecture works as one system.

Only SIB2 is the normal starting point for building a new release.

## Release construction from SIB2

1. **SIB2 fixes a known-good integrated state.** Its defining property is exact acceptance evidence.
2. **A new release starts from SIB2.** Create the release/integration line from the current SIB2 rather than from an arbitrary development head.
3. **Add changes incrementally.** Each feature, refactor, dependency change, documentation contract change, or other meaningful delta is applied to SIB2 or to a descendant that has already passed acceptance.
4. **Run full acceptance after every substantial layer.** Focused tests are useful during implementation, but they do not promote an integration state.
5. **Only proven-compatible layers advance integration.** Record the exact tested commit SHA and acceptance result. A green result on an older base is not evidence for the current composition.
6. **The completed planned composition becomes a release candidate.** RC status comes after integration is complete and accepted, not before.
7. **Baseline promotion is deliberate.** Do not move SIB refs as a side effect of ordinary feature work.

## Contributor rules

- For post-refactor architectural work, identify which baseline is being pursued: SIB0, SIB1, or SIB2.
- Do not add a new fundamental capability class after SIB0 without explicitly reopening the architectural baseline and planning a replacement SIB0.
- Branch release-bound work from the current SIB2 or from an explicitly accepted descendant.
- Do not merge a stale feature branch wholesale merely because it was once green. Rebase or transplant the intended delta onto the current accepted state and verify the resulting composition.
- Do not weaken, skip, xfail, or rewrite acceptance checks to make a feature appear compatible.
- Keep feature deltas narrow enough that their compatibility can be attributed and reviewed.
- When a change overlaps files that have evolved since the feature branch was created, preserve current semantics and re-apply the intended behavior at the semantic level rather than replacing newer files with stale blobs.
- Promotion requires exact evidence: tested commit SHA, acceptance command/workflow, and result appropriate to the claimed baseline level.
- Do not advance or repoint baseline refs as a side effect of ordinary feature work. Baseline promotion is a separate maintainer decision.

## Terms

**Capability class**: A fundamental type of ability the architecture is designed to possess. Multiple similar features may populate one capability class without changing the architecture.

**SIB0**: Stable Initialization Baseline. The capability-class inventory is represented and frozen for the current architectural generation.

**SIB1**: Stable Implementation Baseline. Every SIB0 capability class has a real basic implementation satisfying its own contract.

**SIB2**: Stable Integration Baseline. The SIB1 implementations are proven to work together and the exact composition passes full canonical acceptance.

**Integration build**: A descendant of SIB2 containing one or more candidate release changes. It is provisional until it passes acceptance.

**Accepted integration state**: An integration build whose exact commit has passed the full canonical acceptance gate. Further features may be layered on top of it.

**RC**: Release candidate. The accepted composition intended to become the release. An RC is downstream of SIB2; SIB2 itself is not an RC.

## Acceptance

Acceptance is attached to an exact commit and its required contract, never to a vague statement that a branch or feature was once green.

For the current CodeSleuth SIB2/release line, full acceptance includes the Python matrix and the durable-state/context-graph Bun smoke checks defined by `.github/workflows/acceptance.yml`.

When documentation and implementation disagree about the gate, the canonical repository workflow is authoritative until the documentation is corrected in the same change.
