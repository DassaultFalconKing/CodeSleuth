# Semantic refit

## Status

This document defines CodeSleuth's **normative semantic-refit concept**.

**Semantic refit is not a new Git operation, merge algorithm, porting technology, or special code-writing process.** It is a target condition and review criterion for product evolution.

Porting, backporting, cherry-picking, rewriting, migration, deletion, or no code change at all may be valid means of reaching that condition.

## Definition

A **semantic refit** is successful when a product's relevant semantic surface is preserved or explicitly reconciled across implementation or architectural change.

The central question is not:

> How much of the old patch survived?

It is:

> Which meaningful claims about the old product must still be true, where are they represented now, which claims changed deliberately, and what evidence supports those conclusions?

For the user, the desired effect is semantic continuity: existing capabilities and supported journeys should remain as inconspicuously stable as reasonably possible unless product behavior intentionally changes.

For the maintainer, the opposite is required: every known semantic discontinuity, supersession, retirement, uncertainty, and evidence gap should be visible and reviewable.

The governing principle is:

> **Implementation may change freely. Known reasons why the product was considered correct must not disappear silently.**

## Semantic surface

A product's **semantic surface** is the set of known user-relevant and architecture-relevant claims that characterize what the product can do and what must remain true while it does it.

A refit inventory may contain several kinds of claims.

### Capability claim

What a user, operator, consumer, or integration **can do**.

Example:

`A user can discover and start an available CodeSleuth update from the TUI.`

### Guarantee

What **must follow** when a condition holds.

Example:

`After a successful verified update, the managed CodeSleuth instance returns to a usable state.`

### Invariant

What must remain true across supported execution paths.

Example:

`There is one authoritative owner for update/restart decisions.`

### Negative claim

What the product **must not** do or what failure state must not return.

Example:

`A failed update must not leave a partially installed instance presented as healthy.`

### Compatibility claim

What an existing supported consumer may continue to rely on.

Example:

`Existing project/user configuration survives an update unless an explicit migration contract says otherwise.`

### Authority claim

Which component owns a decision or source of truth.

Example:

`The host OpenCode controller remains execution authority; CodeSleuth does not introduce a second agent runtime.`

### Ordering or relational claim

A meaningful relationship between actions, states, or authorities.

Example:

`Restart happens only after update verification succeeds.`

Claims are not necessarily independent. Ordering, concurrency, authority, and compatibility properties often exist specifically in the relationship between several otherwise-correct components.

### User-journey claim

A user-visible capability can be stronger than the existence of an internal function.

For example, `update() works` is weaker than:

```text
Given an available update,
the user can discover it,
start it through a supported surface,
understand success or failure,
survive the controlled restart,
and resume use without losing supported configuration.
```

Semantic refit therefore treats important end-to-end journeys as part of the semantic surface where the product contract supports them.

## Semantic refit is not a synonym for porting

Good porting and backporting are already semantic engineering activities. They may require history analysis, architectural adaptation, dependency reconstruction, conflict resolution, and reimplementation of an equivalent fix.

CodeSleuth must not use `semantic refit` as a grander name for thoughtful porting.

A porting task normally begins with a delivery assumption:

```text
change/capability P should be represented in target T
-> determine the correct target-native representation of P
```

Semantic-refit reasoning starts one step earlier:

```text
historical work P exists
-> determine what evidenced product claims P represents or taught us
-> determine which of those claims still belong to target T
-> determine what T already provides
-> only then decide whether the required delivery is a port, adaptation,
   reimplementation, separate current design change, no change, defer, or block
```

A normal cherry-pick or backport can therefore be the correct implementation of a semantic refit. The terms operate at different levels.

Branch age, diff size, conflict count, and whether Git applies a patch cleanly do **not** determine whether semantic-refit reasoning is needed.

## Historical evidence is not current authority

Old code, patches, tests, issues, design notes, review discussion, regressions, and follow-up fixes are historical evidence.

They may reveal capabilities, invariants, temporary mechanisms, rejected alternatives, compatibility requirements, or negative knowledge learned through previous failures.

They are not automatically authority over the current architecture.

Likewise, the **current implementation is not automatically normative authority**. Current code can contain regressions, incomplete migrations, or contradictions.

A refit must identify the current normative authority appropriate to the claim, for example:

- accepted product contracts;
- supported user/API behavior;
- security invariants;
- compatibility and support policy;
- accepted ADRs or architecture ownership rules;
- current lifecycle/persistence contracts;
- executable acceptance and regression evidence.

If current authorities conflict, do not choose the version most convenient for the proposed implementation. Record the conflict and leave the affected claim unresolved or blocked until the project resolves it.

## Do not rely on mystical `intent`

`Recover the old intent` is useful shorthand, but it is not a sufficient evidence rule.

A historical change can contain conflicting signals: an issue may require immediate revocation, an implementation may use a 60-second TTL, a test may assert the TTL, and a review comment may call that TTL temporary.

There is no reliable process that extracts one metaphysical `true intent` from that record.

Instead, recover **evidenced historical claims, assumptions, constraints, design rationale, and negative knowledge**, and preserve their provenance.

A model summary, old PR description, generated report, or previous review is navigation evidence, not sufficient proof by itself.

## Separate semantic status from delivery decision

Do not collapse `what should be true now?` and `what code should we write now?` into one label.

### Semantic / normative status

Use these states for claims:

- **REQUIRED** — the claim still belongs to the supported product.
- **SUPERSEDED** — current authoritative behavior already satisfies the claim by another mechanism.
- **RETIRED** — an explicit current authority has ended or replaced the obligation.
- **UNRESOLVED** — available evidence is insufficient to determine the claim's current status.
- **CONFLICTED** — current normative authorities disagree and require an explicit product/architecture decision.

`SUPERSEDED` requires positive coverage evidence. `RETIRED` requires an authority that actually retires the obligation. Neither means `this is inconvenient to implement`.

### Delivery disposition

Record separately how the current target handles the claim:

- **REUSE** — existing implementation can be retained as-is.
- **PORT / ADAPT** — equivalent behavior is delivered by normal porting/backporting/adaptation.
- **REIMPLEMENT** — the claim remains required but needs a current-native implementation unrelated to the old code shape.
- **NEW CHANGE** — current product policy intentionally introduces behavior that is not merely a representation of the historical claim.
- **NO CHANGE** — target already satisfies the claim or the claim is retired.
- **DEFER** — the claim remains valid but is deliberately not delivered to this target now, with policy/risk rationale.
- **BLOCK** — work cannot proceed honestly until evidence or normative authority is resolved.

This two-axis model prevents implementation difficulty from silently turning into requirement deletion.

## Evidence and epistemic status

Passing tests are evidence, not omniscience.

Different claims require different oracles. Prefer the cheapest oracle strong enough to exercise the claim honestly.

A useful evidence ladder is:

1. **Code oracle** — type/build/static checks.
2. **Behavioral oracle** — unit, integration, state, API, or contract tests.
3. **Journey oracle** — black-box CLI/TUI/web workflow from supported entry state to observable result.
4. **Presentation oracle** — DOM/accessibility/viewport/screenshot/interaction-state evidence where presentation is part of the claim.
5. **Human UX oracle** — targeted human evaluation for properties automation cannot establish reliably.

Do not report a stronger semantic conclusion than the oracle actually supports.

For claims whose final success criterion is partly human experience, record the evidence honestly, for example:

```text
Claim: update remains understandable through the TUI
Evidence: black-box journey + viewport checks
Confidence: medium
Human UX verification: not run
```

rather than flattening partial evidence into `PASS` for an untested UX property.

## Why this matters for LLM-driven development

Code-generating LLMs can make implementation changes much faster than a human maintainer can manually revalidate the entire product.

The product owner may understand desired behavior and user experience while lacking the time, context budget, or implementation knowledge to inspect every generated change. A later coding model may understand the current task and current code but know nothing about a failure mode or compatibility guarantee that a previous model encoded implicitly months earlier.

That creates a dangerous split:

`semantic ownership != implementation ownership`

CodeSleuth should therefore help repositories retain an **external semantic memory** that survives individual prompts, agents, context windows, refactors, dependency updates, and implementation rewrites.

The goal is not to pretend that an LLM can perfectly infer user experience. It is to give the model a bounded set of evidenced claims and progressively stronger oracles, then make remaining human-only uncertainty explicit.

A human maintainer should ideally be asked to validate the small remainder that automation cannot establish, not to rediscover every historical capability after each generated change.

## Refit-readiness of repository documentation

A repository is **refit-ready** to the extent that a future maintainer or coding model can reconstruct its semantic surface without depending on one person's memory or one old implementation.

Documentation and evidence should make the following recoverable where materially relevant:

1. **Capabilities** — what users/operators/consumers can do.
2. **User journeys** — important supported paths from intent to observable result.
3. **Guarantees and invariants** — including relational and ordering properties.
4. **Negative knowledge** — failures and forbidden states that must not return.
5. **Authority boundaries** — who owns state, execution, lifecycle, persistence, security, evidence, and other product decisions.
6. **Compatibility obligations** — what external consumers may rely on and for how long.
7. **Evidence mapping** — which tests/gates/oracles support which claims and what they do not prove.
8. **Provenance** — where important claims came from: contracts, incidents, accepted decisions, issues, tests, or historical work.
9. **Intentional semantic changes** — explicit retirement/supersession/new-policy records rather than silent drift.
10. **Unknowns** — important claims that are only partially verified or require human UX judgment.

This does **not** require one giant specification file. CodeSleuth is evidence-first: the semantic memory may be distributed across contracts, tests, ADRs, user/operator documentation, review evidence, context projections, and reports as long as the authority chain is explicit and recoverable.

## A practical stale-work refit pattern

When useful stale work must be reconciled with a changed target, the following is a practical implementation pattern, not the definition of semantic refit itself:

1. Freeze exact source and target identities.
2. Recover evidenced historical claims and negative knowledge from source code, tests, issues, review history, and follow-up fixes.
3. Identify current normative authority and current architecture for each affected claim.
4. Determine what the target already provides and prove coverage rather than assuming it.
5. Record semantic status and delivery disposition separately.
6. Implement the smallest target-native delta required by the surviving claims.
7. Preserve attribution and provenance even when source code does not survive.
8. Add positive and negative regression evidence at the strongest practical oracle level.
9. Run canonical acceptance on the exact resulting composition.
10. Record residual unknowns and any required targeted human validation.

The historical organization of commits and hunks is not the semantic unit of review. One old commit may contain several claims with different dispositions, and one claim may span several components.

## Acceptance standard

A semantic refit is defensible when a reviewer can answer:

- What material historical claims were considered?
- What evidence establishes each claim's provenance?
- Which claims remain normative, are superseded, are retired, are unresolved, or are conflicted?
- What delivery decision corresponds to each material claim?
- Where is each surviving claim represented in the current product?
- Which historical mechanisms were deliberately not carried forward, and why?
- What negative knowledge or forbidden states remain protected?
- What tests or other oracles support each conclusion?
- What is still not known or not machine-verifiable?
- Which intentional semantic changes have an explicit current authority rather than being disguised as `refit`?

The new implementation should be understandable without keeping the historical patch open forever.

At the same time, the relationship between historical product knowledge and the current semantic surface must remain traceable.

## Anti-patterns

Do not use semantic-refit language to justify:

- ordinary patch movement that needs no semantic reconciliation;
- rewriting somebody else's work until it means something different while retaining their feature label;
- declaring difficult behavior `SUPERSEDED` without coverage evidence;
- declaring behavior `RETIRED` without an authority that retires it;
- copying old tests while discarding newer contracts;
- preserving obsolete implementation-specific tests as if mechanisms were requirements;
- weakening or rewriting acceptance to make a stale implementation pass;
- claiming UX preservation from code/build evidence alone;
- treating a generated summary, Mermaid graph, model report, or context projection as stronger evidence than current verified source and accepted contracts;
- forcing a full semantic-archaeology ritual onto a routine clean port whose meaning and authority have not changed.

## Relationship to SIB and exact-head acceptance

Semantic refit, SIB maturity, and Exact-Head Acceptance are separate concepts.

- **Semantic refit** describes the desired preservation/reconciliation of the product's semantic surface across change.
- **SIB0/SIB1/SIB2** describe architectural maturity states.
- **Exact-Head Acceptance (EHA)** binds acceptance evidence to one exact repository state.

A refit does not promote a SIB ref and does not inherit acceptance from its source work.

For CodeSleuth release construction, stale work recovered onto an accepted SIB2 descendant must satisfy the current semantic surface and then establish fresh acceptance on the exact resulting head.

The practical evidence statement is therefore closer to:

`historical semantic evidence + current normative authority + explicit claim dispositions + target-native implementation + exact-head evidence`

not:

`old PR was green + cherry-pick succeeded`

## Canonical short statement

> **Semantic refit is the preservation or explicit reconciliation of a product's user-relevant semantic surface across implementation and architectural change. For users, the goal is continuity. For maintainers, every known semantic discontinuity and evidence gap must be observable. In LLM-driven development, the same record acts as external semantic memory so a code-generating model does not have to rediscover the product from implementation alone.**
