# Stable Baseline Model: SIB0, SIB1, SIB2

## Purpose

The SIB model separates three states that are often collapsed into one vague claim that a refactor is "done" or that a branch is "stable".

The three baselines describe increasing levels of architectural maturity:

- **SIB0 — Stable Initialization Baseline**: the architecture's fundamental capability-class inventory is frozen.
- **SIB1 — Stable Implementation Baseline**: every declared capability class has a real implementation that satisfies its basic contract.
- **SIB2 — Stable Integration Baseline**: those implementations are proven to work together as one system under the canonical acceptance gates.

The sequence is:

`architectural convergence -> SIB0 -> implementation recovery -> SIB1 -> integration recovery -> full acceptance -> SIB2`

Release construction begins from SIB2:

`SIB2 -> integration build -> feature composition -> acceptance -> RC -> release`

The terminology is a project engineering concept, not a claim of industry-standard naming. It gives precise names to states that are otherwise described ambiguously through terms such as *walking skeleton*, *architecture baseline*, *implementation complete*, *integration baseline*, or *pre-release*.

## Capability class

A **capability class** is a fundamental type of ability the system is architected to possess. It is broader than an individual feature, command, adapter, profile, endpoint, or UI action.

Examples can include:

- command-line operation;
- a terminal or graphical operator interface;
- persistent state;
- an extension/profile mechanism;
- lifecycle and update management;
- context or relationship graphs;
- external tool integration;
- report generation;
- a controller/tool execution boundary;
- canonical acceptance infrastructure.

Adding another command to an existing CLI, another profile to an existing profile system, another relation to an existing graph, or another adapter through an existing adapter mechanism normally **populates** an existing capability class. It does not create a new one.

Adding a second execution runtime, a fundamentally new persistence model, or a new orchestration subsystem usually **changes the architecture** and therefore changes the capability-class inventory.

This distinction is the foundation of the SIB model: ordinary release growth should deepen or multiply existing capability classes; architectural change introduces, removes, or redefines capability classes.

## SIB0 — Stable Initialization Baseline

A **Stable Initialization Baseline (SIB0)** is the point at which the architecture's fundamental capability-class inventory is declared complete for the current architectural generation.

At SIB0:

1. Every currently intended fundamental capability class is identified.
2. A placeholder, skeleton, interface, module boundary, contract, or equivalent architectural slot exists for each class.
3. The relationships and ownership boundaries between those classes are sufficiently defined for implementation work to proceed without repeatedly changing the architectural shape.
4. The list of fundamental capability classes is frozen.
5. Maintainers deliberately designate the exact repository state as SIB0.

SIB0 **does not** claim that all capability classes are implemented. Placeholders may still exist. End-to-end behavior may still be incomplete. Full-system acceptance is not required yet.

Its claim is narrower and extremely useful:

> **We know what kinds of things this architecture contains, and that list is no longer expected to change during ordinary implementation of this architectural generation.**

This makes SIB0 an architectural initialization freeze.

### SIB0 invalidation rule

If a genuinely new fundamental capability class must be added after SIB0, or an existing fundamental class must be removed or redefined, the current SIB0 is no longer a valid initialization baseline for the resulting architecture.

The project has reopened architectural design and must establish a new SIB0 before claiming implementation convergence again.

This rule is intentional. A baseline whose defining inventory can silently change is not a baseline.

## SIB1 — Stable Implementation Baseline

A **Stable Implementation Baseline (SIB1)** is the point at which every capability class declared at SIB0 has a real implementation that satisfies its own basic contract.

At SIB1:

1. Every SIB0 capability class has moved beyond a mere placeholder for its required basic path.
2. Each class performs its fundamental function in isolation or through the minimum dependencies required by its own contract.
3. Required interfaces and ownership boundaries are implemented rather than merely sketched.
4. Capability-level, component-level, or focused acceptance for those basic contracts passes.
5. The architectural shape remains the one frozen at SIB0.
6. Maintainers deliberately designate the exact repository state as SIB1.

SIB1 answers:

> **Have we actually implemented the architecture we said we were going to implement?**

It does **not** yet make the stronger claim that all capability classes are proven to work together across every canonical integration path or supported environment.

That distinction matters. A repository can have every subsystem individually implemented while still containing broken composition boundaries, lifecycle paths, migration behavior, state interactions, or environment-specific failures.

SIB1 therefore marks **implementation completeness**, not integration completeness.

## SIB2 — Stable Integration Baseline

A **Stable Integration Baseline (SIB2)** is the smallest architecture-complete state in which every fundamental capability class exists, performs its basic contract, works with the other classes through the intended end-to-end paths, and the exact composed commit passes the project's canonical full-system acceptance gates.

At SIB2:

1. The SIB0 capability-class inventory remains intact.
2. The SIB1 implementations remain functional.
3. Cross-capability integration boundaries work.
4. Required end-to-end execution paths work.
5. Persistence, lifecycle, controller/runtime, migration, and environment interactions satisfy their declared contracts where applicable.
6. The exact candidate commit passes the full canonical acceptance gate.
7. Maintainers deliberately designate the exact repository state as SIB2.

SIB2 answers:

> **Does the implemented architecture actually work as one system?**

SIB2 is the trusted construction base for a new release.

For CodeSleuth, the branch named `SIB` is semantically an **SIB2**. At the time this model was introduced it points to:

`c5e41a73b84e65645dec5d0a4032b19928291193`

The practical branch name remains `SIB`; the numbered terminology describes the engineering state.

## The post-refactor canon

The SIB model is especially valuable when a major refactor happens at the same time that the project must begin preparing a new release.

The canonical recovery sequence is:

`refactor -> stabilize capability-class inventory -> SIB0 -> restore/implement all capability classes -> capability acceptance -> SIB1 -> integration hardening -> full-system acceptance -> SIB2`

Only after SIB2 should broad release feature population resume.

Each stage has a different stopping condition.

### Refactor

**Refactor** changes the internal structure of the system while preserving or deliberately redefining its intended product role. A major refactor may change module boundaries, ownership, dependency direction, persistence structure, execution paths, controller boundaries, state organization, or other architectural internals.

A refactor being structurally complete does not mean the system is stable. It only means the new architectural form has been created.

### SIB0 stopping condition

The project can declare SIB0 when it can say:

> **All fundamental capability classes for this architectural generation are known, represented by explicit architectural slots, and the list is frozen.**

### SIB1 stopping condition

The project can declare SIB1 when it can say:

> **Every declared capability class has a real basic implementation and satisfies its own capability contract.**

### SIB2 stopping condition

The project can declare SIB2 when it can say:

> **Those implementations work together through the intended system paths, and this exact repository state has passed canonical full-system acceptance.**

This prevents the common failure mode in which post-refactor repair, missing old functionality, new product features, migration fixes, and release-specific work all accumulate in the same branch until nobody can tell whether the architecture itself is stable.

The SIB boundaries force the work into evidence-backed phases.

## Acceptance

**Acceptance** is evidence that a concrete repository state satisfies the contracts relevant to the baseline being claimed.

Acceptance is always attached to an **exact commit**, not to a vague memory that a branch or feature "was green."

Evidence has the form:

`exact commit SHA + canonical gate + successful result`

The scope of acceptance grows through the SIB levels:

- **SIB0** requires architectural/contract validation sufficient to prove the capability inventory and boundaries are coherent and frozen. It does not require full implementation.
- **SIB1** requires implementation-level evidence that each declared capability class performs its basic contract.
- **SIB2** requires full-system canonical acceptance proving the integrated composition.

A green result on an older base is not acceptance evidence for a newer composition.

## SIB and MVP

MVP and the SIB levels are minimal along different axes.

An **MVP** is minimal by **product value**. It asks:

> What is the smallest set of capabilities that is useful enough to validate the product hypothesis?

An MVP may be architecturally incomplete, temporary, or intentionally narrow. It can omit future capability classes because its purpose is to validate usefulness.

The SIB sequence is about **architectural maturity**:

- **SIB0**: the architecture's capability-class shape is complete and frozen.
- **SIB1**: that shape is implemented at basic depth.
- **SIB2**: that implementation is proven as an integrated system.

A concise comparison is:

`MVP = little product scope, enough to validate usefulness`

`SIB0 = complete capability-class inventory, implementation may still be skeletal`

`SIB1 = all capability classes basically implemented`

`SIB2 = all capability classes basically implemented and proven integrated`

## Architecture-complete is not release-complete

SIB2 may already be capable of production operation, yet still be too thin to justify the intended public release.

This remains an important distinction:

`architecture-complete != release-complete`

After SIB2, normal release construction should primarily add **similar instances and deeper content inside existing capability classes**, for example:

- more profiles through the existing profile mechanism;
- more tools through the existing tool mechanism;
- more graph relations through the existing graph model;
- more adapters through the existing adapter seam;
- richer workflows through the existing workflow model;
- better UX inside an existing operator interface;
- stronger tests, observability, performance, and operational polish.

If ordinary planned release work requires a genuinely new fundamental capability class, that is evidence that the architecture has reopened and the project must reconsider its SIB0/SIB1/SIB2 chain.

## Release construction from SIB2

Once SIB2 exists, release construction follows a controlled integration sequence:

1. **SIB2 fixes a proven integrated state.**
2. **A new release begins from SIB2.**
3. **Each feature or meaningful change is applied to SIB2 or to an already accepted descendant.**
4. **The full canonical acceptance gate runs after every substantial integration layer.**
5. **Only proven-compatible layers advance the integration state.**
6. **When the planned composition is complete and accepted, it becomes a release candidate.**
7. **After release or the next major architectural cycle, maintainers deliberately select the next appropriate baseline state.**

The release-construction model is:

`SIB2 -> integration build -> feature composition -> acceptance -> RC -> release`

A release is downstream of SIB2. SIB2 itself is not an RC and does not have to contain enough feature depth to justify a public release.

## Baseline promotion and invalidation

Baseline labels are evidence-backed engineering states, not ceremonial version names.

- A state cannot become **SIB0** until the fundamental capability-class inventory is explicitly frozen.
- A state cannot become **SIB1** until every SIB0 class has a real basic implementation and relevant capability acceptance evidence.
- A state cannot become **SIB2** until the exact integrated composition passes full canonical acceptance.
- A later SIB level does not erase the evidence for earlier levels; it builds on it.
- A fundamental architecture change can invalidate the current SIB0 lineage and require a new SIB0 -> SIB1 -> SIB2 progression.
- Ordinary feature population inside existing capability classes does not require restarting the baseline sequence.

## Versioning

The SIB levels should not be tied mechanically to Semantic Versioning components. Semantic Versioning describes product/API evolution; SIB0/SIB1/SIB2 describe engineering states.

A baseline may therefore be represented by:

- an exact commit SHA;
- a dedicated stable branch/ref;
- an internal marker or tag such as `sib0-YYYY-MM-DD`, `sib1-YYYY-MM-DD`, or `sib2-YYYY-MM-DD` if a project chooses to use one.

Public RC and release tags remain governed by the project's release policy.

## Canonical short definitions

> **SIB0 — Stable Initialization Baseline:** the exact state in which the fundamental capability-class inventory for an architectural generation is represented and frozen; ordinary implementation work must not change that list.

> **SIB1 — Stable Implementation Baseline:** the exact state in which every SIB0 capability class has a real implementation satisfying its basic contract.

> **SIB2 — Stable Integration Baseline:** the exact state in which the SIB1 implementations work together through the intended end-to-end system paths and the composed commit passes canonical full-system acceptance.

The practical rule is simple:

> **Freeze the architectural shape at SIB0, prove its implementation at SIB1, prove its composition at SIB2, and only then use that stable integrated state to build the next release.**
