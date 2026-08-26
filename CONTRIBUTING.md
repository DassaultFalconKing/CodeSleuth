# Contributing to CodeSleuth

CodeSleuth uses a three-level **Stable Baseline** discipline for architectural recovery and release construction.

The full concept, its distinction from MVP and release, capability-class criteria, feature population, and post-refactor use are defined in [`docs/STABLE-INTEGRATION-BASELINE.md`](docs/STABLE-INTEGRATION-BASELINE.md). The normative rule that binds acceptance evidence to one exact repository state is defined in [`docs/EXACT-HEAD-ACCEPTANCE.md`](docs/EXACT-HEAD-ACCEPTANCE.md).

The levels are:

- **SIB0 — Stable Initialization Baseline**: the fundamental capability-class inventory is represented and frozen.
- **SIB1 — Stable Implementation Baseline**: every SIB0 capability class has a real implementation satisfying its basic contract.
- **SIB2 — Stable Integration Baseline**: those implementations work together end-to-end and the exact composition passes full canonical acceptance.

The post-refactor model is:

`refactor -> SIB0 -> implementation recovery -> SIB1 -> integration recovery -> acceptance -> SIB2`

The release-construction model is:

`SIB2 -> integration build -> feature population -> acceptance -> RC -> release`

## Current CodeSleuth baseline

The current CodeSleuth `SIB` branch is semantically an **SIB2**. At the time this policy was introduced it points to:

`c5e41a73b84e65645dec5d0a4032b19928291193`

Treat that ref as the proven integrated construction base. Do not push feature work directly onto `SIB`.

## Capability classes and feature population

A **capability class** is a fundamental type of ability the architecture is designed to possess. Multiple similar features may populate one capability class without changing the architecture.

Examples:

- `CLI` is a capability class; adding `verify`, `update`, or `doctor` commands is feature population.
- the profile mechanism is a capability class; adding Rust, TypeScript, Python, or OSINT profiles is feature population.
- the context graph is a capability class; adding relations, bounded queries, or additional Mermaid views is feature population.
- external-tool integration is a capability class; adding another adapter through the same integration seam is feature population.

**Feature population** means adding instances, variants, operations, workflows, depth, content, or polish inside capability classes that already exist, without changing the fundamental capability-class inventory.

Adding a second independent execution runtime or a fundamentally new persistence/orchestration model is not feature population. It changes the architecture.

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

**SIB1 is not a safe base for active feature population.** From SIB1, work should focus on integration recovery, cross-capability correctness, lifecycle/environment compatibility, and reaching SIB2.

Example: if CLI, TUI, persistent state, context graph, and update lifecycle all work independently but their combined paths are not yet proven by full acceptance, adding ten new profiles at this point is premature. First prove the composition and reach SIB2.

## SIB2 — integration completeness

SIB2 is reached when the SIB1 implementations work together through the intended end-to-end paths and the exact composed commit passes the repository's full canonical acceptance gate.

SIB2 proves:

> The implemented architecture works as one system.

**SIB2 is the normal safe starting point for active feature population and for building a new release.**

Example: once CLI/TUI, state, controller/tool paths, lifecycle operations, and context-graph behavior pass the supported acceptance matrix together, it is safe to populate the architecture with additional profiles, tools, relations, workflows, and UX depth.

## Exact-head acceptance

SIB degree and acceptance identity are separate axes:

- **SIB degree** states **what is proven**.
- **Exact-head acceptance** states **which exact repository state the proof applies to**.

The maturity claims are:

| Degree | Exact-head acceptance proves |
| --- | --- |
| **SIB0** | **Architectural completeness**: capability-class inventory and boundaries are coherent and frozen for the exact SHA. |
| **SIB1** | **Implementation completeness**: every SIB0 capability class has a real basic implementation satisfying its contract at the exact SHA. |
| **SIB2** | **Integration completeness**: those implementations work together and the exact composed SHA passes canonical full-system acceptance. |

The core invariant is:

> **Acceptance evidence never implicitly propagates to a descendant or divergent commit.**

If accepted commit `A` changes to candidate commit `B`, `B` requires acceptance evidence under the profile appropriate to the claim being made. A green feature branch, a green ancestor, or two independently green divergent heads are not acceptance evidence for an untested resulting composition.

The tested SHA and the SHA promoted as an accepted integration state, SIB state, RC, or release must be identical.

See [`docs/EXACT-HEAD-ACCEPTANCE.md`](docs/EXACT-HEAD-ACCEPTANCE.md) for the full normative contract.

## Release construction from SIB2

1. **SIB2 fixes a known-good integrated state.** Its defining property is exact acceptance evidence.
2. **A new release starts from SIB2.** Create the release/integration line from the current SIB2 rather than from an arbitrary development head.
3. **Feature population proceeds incrementally.** Add concrete release functionality inside existing capability classes.
4. **Run full acceptance after every substantial layer.** Focused tests are useful during implementation, but they do not promote an integration state.
5. **Only proven-compatible layers advance integration.** Record the exact tested commit SHA and acceptance result. A green result on an older base is not evidence for the current composition.
6. **The completed planned population becomes a release candidate.** RC status comes after integration is complete and accepted, not before.
7. **Baseline promotion is deliberate.** Do not move SIB refs as a side effect of ordinary feature work.

## Contributor rules

- For post-refactor architectural work, identify which baseline is being pursued: SIB0, SIB1, or SIB2.
- Do not add a new fundamental capability class after SIB0 without explicitly reopening the architectural baseline and planning a replacement SIB0.
- Do not begin broad release feature population from SIB1.
- Branch release-bound feature population from the current SIB2 or from an explicitly accepted descendant.
- Do not merge a stale feature branch wholesale merely because it was once green. Rebase or transplant the intended delta onto the current accepted state and verify the resulting composition.
- Do not weaken, skip, xfail, or rewrite acceptance checks to make a feature appear compatible.
- Keep feature deltas narrow enough that their compatibility can be attributed and reviewed.
- When a change overlaps files that have evolved since the feature branch was created, preserve current semantics and re-apply the intended behavior at the semantic level rather than replacing newer files with stale blobs.
- Promotion requires exact evidence: tested commit SHA, acceptance command/workflow, and result appropriate to the claimed baseline level.
- If the candidate head changes after acceptance, treat the new SHA as a new candidate and establish acceptance again under the required profile.
- Do not advance or repoint baseline refs as a side effect of ordinary feature work. Baseline promotion is a separate maintainer decision.

## Terms

**Capability class**: A fundamental type of ability the architecture is designed to possess. Multiple similar features may populate one capability class without changing the architecture.

**Feature population**: Adding concrete instances, variants, depth, workflows, content, or polish inside capability classes that already exist, without changing the fundamental capability-class inventory.

**SIB0**: Stable Initialization Baseline. The capability-class inventory is represented and frozen for the current architectural generation.

**SIB1**: Stable Implementation Baseline. Every SIB0 capability class has a real basic implementation satisfying its own contract. It is not a safe base for active feature population.

**SIB2**: Stable Integration Baseline. The SIB1 implementations are proven to work together and the exact composition passes full canonical acceptance. It is the normal safe base for feature population.

**Exact-head acceptance**: Successful execution of the required acceptance profile against one exact repository commit, where the tested SHA is identical to the candidate head being accepted.

**Acceptance profile**: The required checks, gates, and environments for a particular SIB maturity, integration, RC, or release claim.

**Acceptance evidence**: The successful result of an acceptance profile attached to one exact commit SHA.

**Integration build**: A descendant of SIB2 containing one or more candidate release changes. It is provisional until it passes acceptance.

**Accepted integration state**: An integration build whose exact commit has passed the full canonical acceptance gate. Further features may be layered on top of it, but those descendants require their own acceptance before promotion.

**RC**: Release candidate. The accepted composition intended to become the release. An RC is downstream of SIB2; SIB2 itself is not an RC.

## Acceptance

Acceptance is attached to an exact commit and its required contract, never to a vague statement that a branch or feature was once green.

For the current CodeSleuth SIB2/release line, full acceptance includes the Python matrix and the durable-state/context-graph Bun smoke checks defined by `.github/workflows/acceptance.yml`.

When documentation and implementation disagree about the gate, the canonical repository workflow is authoritative until the documentation is corrected in the same change.
