# Exact-head acceptance

## Status

This document is a **normative acceptance contract** for the CodeSleuth SIB0/SIB1/SIB2 model. It refines the acceptance semantics defined by [`STABLE-INTEGRATION-BASELINE.md`](STABLE-INTEGRATION-BASELINE.md).

## Definition

**Exact-head acceptance** is the rule that an acceptance result belongs only to the exact Git commit on which the required acceptance gates were executed.

A branch name, pull request, ancestor commit, component test, or previously accepted composition does not transfer acceptance to a different commit. If the candidate head changes, acceptance for the new head must be established again using the acceptance profile required for the maturity level being claimed.

The canonical statement is:

> **SIB levels define what is proven; exact-head acceptance defines which repository state the proof applies to.**

The minimum evidence identity is:

`exact commit SHA + required acceptance profile + required gates/environments + successful result`

A branch is therefore not "accepted" in the abstract. A specific commit reachable from that branch may carry acceptance evidence.

## Two independent axes

SIB maturity and exact-head acceptance answer different questions.

**SIB degree** answers:

> What class of maturity claim has been proven?

**Exact-head acceptance** answers:

> For which exact repository state does that proof hold?

These axes must not be collapsed. A stronger test run does not change the definition of a SIB degree, and a SIB label does not make acceptance evidence portable to another commit.

## Acceptance profile and acceptance evidence

An **acceptance profile** defines what must be checked for a maturity claim. It may include architectural contract checks, capability/component checks, full-system integration tests, supported environment matrices, durable-state checks, context-graph checks, or other canonical gates.

**Acceptance evidence** is the recorded successful execution of that profile against one exact commit.

Conceptually:

```text
AcceptanceEvidence {
    commit: <exact SHA>
    profile: <SIB0 | SIB1 | SIB2 | release-specific profile>
    gates: <required checks and environments>
    result: PASS
}
```

Old CI is provenance. It is not acceptance evidence for a different composition.

## SIB0 exact-head acceptance

SIB0 exact-head acceptance proves **architectural completeness** for one exact commit.

The accepted claim is:

> The fundamental capability-class inventory and ownership/boundary model for this architectural generation are represented, coherent, and deliberately frozen at this exact repository state.

SIB0 does not require every capability class to be implemented and does not claim full-system integration.

Canonical shorthand:

`SIB0 exact-head acceptance = architectural completeness proven for SHA`

A descendant of an accepted SIB0 commit does not automatically become a new SIB0. If a descendant adds, removes, or fundamentally redefines a capability class, the architecture has reopened and the SIB0 lineage must be reconsidered.

## SIB1 exact-head acceptance

SIB1 exact-head acceptance proves **implementation completeness** for one exact commit.

The accepted claim is:

> Every capability class frozen at SIB0 has a real basic implementation satisfying its own required contract at this exact repository state.

SIB1 does not claim that the complete system composition is proven across all canonical integration paths.

Canonical shorthand:

`SIB1 exact-head acceptance = implementation completeness proven for SHA`

This is why SIB1 is not the normal base for broad feature population. The architecture may be fully implemented while composition defects still exist.

## SIB2 exact-head acceptance

SIB2 exact-head acceptance proves **integration completeness** for one exact commit.

The accepted claim is:

> The SIB1 implementations work together through the intended end-to-end paths and this exact composed repository state passes the full canonical acceptance profile.

Canonical shorthand:

`SIB2 exact-head acceptance = integration completeness proven for SHA`

For SIB2, the exact composition is the subject of the proof. Individual components being green on other branches or commits cannot establish integration correctness for the candidate composition.

SIB2 is the first normal safe base for broad feature population and release construction.

## Acceptance does not propagate forward

The core invariant is:

> **Acceptance evidence never implicitly propagates to a descendant or divergent commit.**

If:

```text
A = accepted
A -> B
```

then `B` is a new candidate state. `B` may be trivially related to `A`, but it is not accepted merely because `A` was accepted.

The same rule applies to divergence:

```text
    -> B
A
    -> C
```

Acceptance of `B` proves nothing about `C`, and acceptance of `C` proves nothing about `B`. A later composition containing both changes must itself be accepted on its exact resulting SHA.

This remains true even when the new change looks harmless. Projects may define different acceptance profiles for different claims, but any claim that a commit is SIB2, an accepted integration state, an RC, or a release must use evidence attached to that exact commit under the required profile.

## What exact-head acceptance does not mean

Exact-head acceptance does not claim that a commit is perfect, bug-free, or correct outside the scope of its acceptance profile.

It means only that:

1. the candidate repository state is identified by an exact SHA;
2. the required profile for the claimed maturity level is known;
3. the required gates were executed against that SHA;
4. those gates succeeded;
5. the evidence is not silently transferred to another state.

The strength of the engineering claim comes from the combination of **SIB degree + acceptance profile + exact SHA**, not from the phrase "green CI" alone.

## Integration and release consequence

For release construction from SIB2:

```text
accepted head A
    + candidate delta
    = candidate head B
```

`B` must obtain its own exact-head acceptance before it can become the next accepted integration state.

Therefore:

- a feature being green on its source branch is not composition evidence;
- a conflict-free cherry-pick is not composition evidence;
- two independently accepted divergent commits do not make their untested combination accepted;
- moving an integration or baseline ref does not manufacture acceptance;
- the tested SHA and the promoted SHA must be identical.

For stale work, use the semantic-refit discipline in [`SEMANTIC-REFIT.md`](SEMANTIC-REFIT.md), then establish exact-head acceptance for the refitted composition.

## Canonical short definitions

> **Exact-head acceptance:** successful execution of the required acceptance profile against one exact repository commit, where the tested SHA is identical to the candidate head being accepted.

> **SIB degree:** the class of maturity claim being proven: architectural completeness at SIB0, implementation completeness at SIB1, and integration completeness at SIB2.

> **Acceptance profile:** the required checks, gates, and environments for a particular maturity or release claim.

> **Acceptance evidence:** the successful result of that profile attached to one exact commit SHA.

The practical rule is:

> **Prove the right property, on the exact state you intend to promote. If HEAD changes, prove it again.**
