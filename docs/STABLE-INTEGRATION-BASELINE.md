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

`SIB2 -> integration build -> feature population -> acceptance -> RC -> release`

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

A capability class answers **what kind of thing the system can fundamentally do**. A feature answers **which concrete instance, variation, or depth of that ability exists now**.

For example:

- `CLI` is a capability class; adding `verify`, `update`, or `doctor` commands populates that class.
- `profile/extension system` is a capability class; adding Rust, TypeScript, Python, or OSINT profiles populates that class.
- `context graph` is a capability class; adding new relation types, bounded queries, or Mermaid views populates that class.
- `external tool integration` is a capability class; adding another MCP host or adapter through the existing integration seam populates that class.
- `persistent state` is a capability class; adding another stored field or another state consumer normally deepens that class rather than creating a new one.

By contrast:

- adding a second execution runtime alongside the existing controller model;
- introducing a fundamentally different persistence subsystem;
- adding a new orchestration layer with independent lifecycle ownership;

normally changes the architecture itself and therefore changes the capability-class inventory.

This distinction is the foundation of the SIB model: ordinary release growth should deepen or multiply existing capability classes; architectural change introduces, removes, or redefines capability classes.

## Feature population

**Feature population** is the controlled process of adding concrete instances, variants, depth, content, and polish **inside capability classes that already exist in the SIB0 architecture**.

Feature population does not change what fundamental kinds of capabilities the system has. It makes those already-declared capabilities richer and more useful.

Typical feature population includes:

- adding more CLI commands to an existing CLI capability class;
- adding more profiles to an existing profile system;
- adding more tools through an existing tool/plugin mechanism;
- adding more graph relations or graph queries through an existing graph model;
- adding more adapters through an existing adapter seam;
- adding more report types through an existing reporting capability;
- adding more UI actions and workflows inside an existing TUI or GUI capability;
- improving observability, performance, UX, error handling, or domain coverage without changing the architecture's fundamental class inventory.

A useful test is:

> **If this change can be expressed as “one more instance, variant, operation, workflow, or deeper implementation of an already-declared capability class,” it is probably feature population.**

For example, adding ten new CodeSleuth profiles is feature population if they all use the existing profile mechanism. Adding a second independent profile runtime with its own installation, state, and execution ownership would not be feature population; it would reopen the architecture.

Feature population is intentionally a **post-SIB2 activity for release construction**.

**SIB1 is not a safe base for active feature population. SIB2 is.**

Why: at SIB1, every capability class may be individually implemented, but the project has not yet proved that the complete composition works as one system. Beginning broad feature population at SIB1 mixes two different problem classes:

1. unresolved integration defects in the new architecture; and
2. new release functionality being added on top of that architecture.

That destroys the clean stopping condition of post-refactor recovery. SIB2 exists precisely to separate those phases.

Therefore:

`SIB1 -> integration hardening only`

`SIB2 -> feature population may begin`

A narrow change needed to make SIB1 components integrate and reach SIB2 is **integration recovery**, not feature population.

## SIB0 — Stable Initialization Baseline

A **Stable Initialization Baseline (SIB0)** is the point at which the architecture's fundamental capability-class inventory is declared complete for the current architectural generation. The frozen inventory for CodeSleuth lives in [`SIB0-CAPABILITY-INVENTORY.md`](SIB0-CAPABILITY-INVENTORY.md) and is indexed by [`protected-capabilities.json`](protected-capabilities.json).

At SIB0:

1. Every currently intended fundamental capability class is identified.
2. A placeholder, skeleton, interface, module boundary, contract, or equivalent architectural slot exists for each class.
3. The relationships and ownership boundaries between those classes are sufficiently defined for implementation work to proceed without repeatedly changing the architectural shape.
4. The list of fundamental capability classes is frozen.
5. Maintainers deliberately designate the exact repository state as SIB0.

SIB0 **does not** claim that all capability classes are implemented. Placeholders may still exist. End-to-end behavior may still be incomplete. Full-system acceptance is not required yet.

Example: after a major CodeSleuth redesign, the repository may already contain explicit slots for CLI, TUI, profiles, persistent state, update lifecycle, context graph, external-tool integration, and acceptance infrastructure, while several of them are still skeletal. If maintainers agree that no new fundamental class will be added during this architectural generation, that state can be SIB0.

Its claim is narrower and extremely useful:

> **We know what kinds of things this architecture contains, and that list is no longer expected to change during ordinary implementation of this architectural generation.**

This makes SIB0 an architectural initialization freeze.

### SIB0 invalidation rule

If a genuinely new fundamental capability class must be added after SIB0, or an existing fundamental class must be removed or redefined, the current SIB0 is no longer a valid initialization baseline for the resulting architecture.

Example: if SIB0 assumed one OpenCode-controlled execution model and later the project decides it needs a second independent execution runtime, that is not "one more feature." The architectural inventory changed. The existing SIB0 lineage is invalid for the new architecture.

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

Example: the CLI can execute its basic commands, the TUI can navigate its basic surfaces, state can be written/read, the context graph can build/query a minimal graph, and update lifecycle has a real path. Each capability works at its own basic contract. But cross-capability flows may still fail when composed together. That state may be SIB1, but not SIB2.

It does **not** yet make the stronger claim that all capability classes are proven to work together across every canonical integration path or supported environment.

That distinction matters. A repository can have every subsystem individually implemented while still containing broken composition boundaries, lifecycle paths, migration behavior, state interactions, or environment-specific failures.

SIB1 therefore marks **implementation completeness**, not integration completeness.

### SIB1 safety rule

**SIB1 is not a safe base for active feature population.**

At SIB1, work should remain focused on integration recovery, cross-capability defects, lifecycle correctness, environment compatibility, and the full acceptance needed to reach SIB2.

Starting broad feature growth from SIB1 makes it impossible to cleanly distinguish whether a failure belongs to the refactored architecture or to newly added release functionality.

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

Example: a user can enter through CLI or TUI, invoke the supported controller/tool path, read/write the expected durable state, traverse the context-graph path where applicable, and complete lifecycle operations across the supported environment matrix while the exact commit passes canonical acceptance. That is the kind of evidence that turns SIB1 into SIB2.

SIB2 is the trusted construction base for a new release and the first baseline from which broad feature population is considered safe.

For CodeSleuth, the branch named `SIB` is a convenience ref for the deliberately promoted exact **SIB2** baseline. Its current target must be resolved from Git when needed and must not be hard-coded into this normative definition. The acceptance authority is the exact SHA recorded in EHA evidence; moving the `SIB` ref does not create, transfer, or strengthen acceptance.

The practical branch name remains `SIB`; the numbered terminology describes the engineering state.

## The post-refactor canon

The SIB model is especially valuable when a major refactor happens at the same time that the project must begin preparing a new release.

The canonical recovery sequence is:

`refactor -> stabilize capability-class inventory -> SIB0 -> restore/implement all capability classes -> capability acceptance -> SIB1 -> integration hardening -> full-system acceptance -> SIB2`

Only after SIB2 should broad release feature population resume.

Each stage has a different stopping condition.

### Refactor

**Refactor** changes the internal structure of the system while preserving or deliberately redefining its intended product role. A major refactor may change module boundaries, ownership, dependency direction, persistence structure, execution paths, controller boundaries, state organization, or other architectural internals.

Example: replacing a monolithic lifecycle script with explicit state, update, and controller boundaries while preserving the product's intended user-facing role is a refactor. Adding five new user-facing profiles after the architecture is stable is feature population, not refactoring.

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

Examples:

- SIB0 acceptance may verify that all declared capability slots/contracts exist and that the capability inventory is coherent and frozen.
- SIB1 acceptance may run focused component/capability tests showing that each declared class performs its minimum real function.
- SIB2 acceptance runs the canonical full-system matrix against the exact composed commit and proves the integrated paths together.

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

Example: a prototype may expose one CLI command that proves the core analysis is useful while having no final persistence, update lifecycle, extension mechanism, or production integration model. That can be a valid MVP and still be nowhere near SIB0/SIB1/SIB2 for the intended architecture.

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

After SIB2, normal release construction should primarily perform **feature population inside existing capability classes**, for example:

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
3. **Feature population proceeds incrementally inside the existing capability classes.**
4. **The full canonical acceptance gate runs after every substantial integration layer.**
5. **Only proven-compatible layers advance the integration state.**
6. **When the planned population is complete and accepted, it becomes a release candidate.**
7. **After release or the next major architectural cycle, maintainers deliberately select the next appropriate baseline state.**

The release-construction model is:

`SIB2 -> integration build -> feature population -> acceptance -> RC -> release`

A release is downstream of SIB2. SIB2 itself is not an RC and does not have to contain enough feature depth to justify a public release.

## Baseline promotion and invalidation

Baseline labels are evidence-backed engineering states, not ceremonial version names.

- A state cannot become **SIB0** until the fundamental capability-class inventory is explicitly frozen.
- A state cannot become **SIB1** until every SIB0 class has a real basic implementation and relevant capability acceptance evidence.
- **SIB1 must not be used as the normal base for active release feature population.** Work from SIB1 should be directed toward integration recovery and promotion to SIB2.
- A state cannot become **SIB2** until the exact integrated composition passes full canonical acceptance.
- **SIB2 is the first normal safe base for active feature population and release construction.**
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

> **Capability class:** a fundamental architectural type of ability. Concrete commands, profiles, adapters, workflows, and similar variants usually populate an existing class rather than create a new one.

> **Feature population:** adding concrete instances, variants, depth, workflows, content, or polish inside capability classes that already exist, without changing the fundamental capability-class inventory.

> **SIB0 — Stable Initialization Baseline:** the exact state in which the fundamental capability-class inventory for an architectural generation is represented and frozen; ordinary implementation work must not change that list.

> **SIB1 — Stable Implementation Baseline:** the exact state in which every SIB0 capability class has a real implementation satisfying its basic contract. SIB1 is not a safe base for active feature population.

> **SIB2 — Stable Integration Baseline:** the exact state in which the SIB1 implementations work together through the intended end-to-end system paths and the composed commit passes canonical full-system acceptance. SIB2 is the normal safe base for feature population and release construction.

The practical rule is simple:

> **Freeze the architectural shape at SIB0, prove its implementation at SIB1, prove its composition at SIB2, and only then populate that stable architecture with the features of the next release.**
