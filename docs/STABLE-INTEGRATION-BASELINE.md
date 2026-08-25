# Stable Integration Baseline (SIB)

## Definition

A **Stable Integration Baseline (SIB)** is the smallest architecture-complete state of a system in which every fundamental capability class exists, works end-to-end at its basic contract, and passes the project's canonical acceptance gates.

A SIB is not a release candidate and not merely a development snapshot that happens to be green. It is a deliberately selected, known-good architectural baseline from which construction of a new release begins.

The term is used here as a project engineering concept. It is not claimed to be an industry-standard definition; it names a state that is often described less precisely through terms such as *walking skeleton*, *architecture baseline*, *integration baseline*, or *pre-release*.

## The key distinction: SIB is not MVP

An **MVP** and a **SIB** are minimal along different axes.

An MVP is minimal by **product value**. It asks:

> What is the smallest set of capabilities that is useful enough to validate the product hypothesis?

An MVP may therefore be architecturally incomplete. It may contain temporary shortcuts, a single happy path, partial implementations, missing future capability classes, or components that are expected to be replaced later. That can be acceptable because the purpose of an MVP is to validate usefulness, not to prove the final architecture.

A SIB is minimal by **implementation depth inside an architecture that is already complete in shape**. It asks:

> Do all fundamental parts of the intended system already exist, connect, and work at least at their basic end-to-end contract?

In short:

`MVP = few functions, but already useful`

`SIB = little depth inside each function, but all fundamental capability classes are already represented`

This distinction matters because a SIB is intended to be extended without redesigning the system's fundamental shape.

## Architecture-complete, not feature-complete

A SIB contains the complete set of **architecturally significant capability classes known at the time the baseline is declared**.

The wording is intentionally narrower than “all possible function types.” No project can prove that it will never discover a genuinely new architectural requirement. The relevant claim is that the architecture is complete relative to the accepted product design at the time of the baseline.

For example, if a system's intended architecture includes capability classes such as:

- command-line operation;
- a terminal or graphical operator interface;
- an extension/profile mechanism;
- update and lifecycle management;
- persistent state;
- context or relationship graphs;
- a controller/tool execution boundary;
- canonical acceptance infrastructure;

then a SIB does not require each class to be rich or exhaustive. It does require each declared class to exist, be integrated, and satisfy its basic contract.

After SIB, normal release construction should primarily deepen, multiply, or refine existing capability classes. Examples include:

- adding more profiles of an existing profile type;
- adding more tools through an existing tool mechanism;
- adding relations to an existing graph model;
- improving the UX of an existing interface;
- adding domain-specific operations through an existing execution model;
- strengthening tests and observability;
- improving performance;
- extending existing workflows and adapters.

By contrast, changes such as the following are evidence that the architectural baseline itself has changed:

- introducing a second execution runtime;
- adding a fundamentally new persistence layer;
- introducing a new orchestration class that the architecture did not previously contain;
- replacing a core lifecycle or ownership boundary with a different model.

Such changes are not ordinary feature population. After they are integrated and all fundamental capability classes are restored to working order, the project should establish a **new SIB**.

## SIB and refactoring

The concept is especially useful after a major refactor.

A successful refactor is not complete merely because the code compiles or because individual unit tests pass. The post-refactor architecture becomes a candidate SIB only after all intended capability classes are again present, integrated, and proven by the canonical acceptance gates.

The sequence is therefore:

`refactor -> restore all capability classes -> canonical acceptance -> new SIB`

Only after that point should broad feature growth resume.

This gives the team a concrete stopping condition for architectural work: the architecture is no longer “in transition” once it has a proven, extensible baseline.

## SIB is not a release

A SIB may already be capable of running in production, but it does not have to be product-complete for the intended release scope.

This yields an important distinction:

`architecture-complete != release-complete`

A SIB may already have:

- the correct architecture;
- production-grade base contracts;
- functioning integration boundaries;
- canonical acceptance gates;
- all fundamental capability classes;

while still having too little of the following to justify a release:

- profiles;
- tools;
- workflows;
- adapters;
- domain-specific functionality;
- content;
- UX refinement;
- operational polish.

The architecture is real; the product is still thin.

That is the intended place of SIB in the maturity model.

## Two independent dimensions of maturity

MVP, SIB, and release are easier to understand if product completeness and architectural completeness are treated as separate dimensions.

| | Low product completeness | High product completeness |
| --- | --- | --- |
| **Low architectural completeness** | prototype / MVP | dangerous accumulated system or historical monolith |
| **High architectural completeness** | **SIB** | release |

A SIB therefore occupies a very specific state:

> **The architecture is already real, but the product is still thin.**

This is why a SIB can be a much better basis for release construction than either an old release branch or an arbitrary development head.

## Release construction from SIB

Once a SIB exists, release construction follows a controlled integration sequence:

1. **SIB fixes a known-good state.**
2. **A new release begins from the SIB.**
3. **Each feature or meaningful change is applied to the SIB or to an already accepted descendant.**
4. **The full canonical acceptance gate runs after every substantial integration layer.**
5. **Only proven-compatible layers advance the integration state.**
6. **When the planned composition is complete and accepted, it becomes a release candidate.**
7. **After release, a new proven commit may be deliberately selected as the next SIB.**

The release-construction model is:

`SIB -> integration build -> feature composition -> acceptance -> RC -> release`

A green result on an old feature branch or an older base is not compatibility evidence for the current composition. Promotion belongs to the exact composed commit that passed the canonical gate.

## What makes a state eligible to become a SIB

A repository state is eligible to become a SIB when all of the following are true:

1. The intended architecture for the current generation of the system is no longer in structural transition.
2. Every architecturally significant capability class is present.
3. Every capability class performs its basic end-to-end function.
4. The integration boundaries between those classes work.
5. The exact candidate commit passes the full canonical acceptance gate.
6. The state is suitable for extension without requiring new fundamental architectural classes for ordinary planned feature growth.
7. Maintainers deliberately designate the exact commit/ref as the baseline.

A SIB is therefore an evidence-backed engineering state, not a label applied because development “feels stable.”

## When a new SIB is required

A new SIB should be established when a change alters the architecture rather than merely populating it. Typical triggers include:

- a major architectural refactor;
- introduction or removal of a fundamental capability class;
- a change in execution ownership or orchestration boundaries;
- a change in persistence architecture;
- a major redesign of the extension mechanism;
- replacement of a core runtime or integration model.

The project first restores full basic capability coverage under the new architecture, proves it through acceptance, and only then designates the new SIB.

## Versioning

SIB should not be tied mechanically to semantic-version components. Semantic Versioning describes product/API evolution; SIB describes an engineering and integration state.

A SIB may therefore be represented by:

- an exact commit SHA;
- a dedicated stable branch/ref such as `SIB`;
- an internal marker or tag such as `sib-YYYY-MM-DD` if a project chooses to use one.

A public release version or RC tag remains governed by the project's release policy.

## Canonical short definition

> **Stable Integration Baseline is the smallest architecture-complete state of the system in which every fundamental capability class exists, works end-to-end at its basic contract, and passes the canonical acceptance gates. Future release work should primarily deepen or multiply those existing capability classes rather than introduce new architectural ones.**

The practical purpose of the concept is simple: a new release should not begin from “whatever branch currently has the most work.” It should begin from the last state whose architecture and integration behavior are already known to work.
