# Semantic refit

## Status

This document defines CodeSleuth's **normative semantic-refit concept**.

**Semantic refit is not a new Git operation, merge algorithm, porting technology, or special code-writing process.** It is a target condition and review criterion for product evolution.

Porting, backporting, cherry-picking, rewriting, migration, deletion, or no code change at all may be valid means of reaching that condition.

Semantic refit is also **not a fourth SIB level** and not a new persistence or orchestration authority. It composes existing CodeSleuth contracts, evidence, and host-native execution discipline.

## Definition

A **semantic refit** is successful when a product's relevant **evidenced semantic surface** is preserved or explicitly reconciled across implementation or architectural change.

The central question is not:

> How much of the old patch survived?

It is:

> Which meaningful claims about the product must still be true, where are they represented now, which claims changed deliberately, and what evidence supports those conclusions?

For the user, the desired effect is semantic continuity: supported capabilities and journeys should remain stable unless product behavior intentionally changes.

For the maintainer, every known semantic discontinuity, supersession, retirement, uncertainty, and evidence gap should be visible and reviewable.

The governing principle is:

> **Implementation may change freely. Known reasons why the product was considered correct must not disappear silently.**

## Semantic surface

A product's **semantic surface** is the set of known user-relevant and architecture-relevant claims that characterize what the supported product can do and what must remain true while it does it.

Not every incidental implementation behavior is a product claim. A refit inventory should include material claims for which the repository contains authority, evidence, compatibility reliance, accepted negative knowledge, or an explicit product decision.

### Capability claim

What a user, operator, consumer, or integration **can do**.

Example:

`A user can discover and start an available CodeSleuth update from the TUI.`

### Guarantee / postcondition claim

What **must follow** when a condition holds.

Example:

`After a successful verified update, the managed CodeSleuth instance returns to a usable state.`

### Invariant claim

What must remain true across supported execution paths or valid states.

Example:

`There is one authoritative owner for update/restart decisions.`

### Negative / forbidden-state claim

What the product **must not** do or what failure state must not return.

Example:

`A failed update must not leave a partially installed instance presented as healthy.`

For CodeSleuth recorded contracts, accepted negative knowledge is indexed by each contract's `forbidden_regressions[]` ledger in `docs/protected-capabilities.json`. The index entry is not required to contain the entire proof record; the constructive invariant, violation witness, executable oracle, and provenance may live in the referenced contract/test evidence as long as the chain is recoverable.

Material negative claims require the stronger protocol defined in [Negative-claim evidence protocol](#negative-claim-evidence-protocol).

### Compatibility claim

What an existing supported consumer may continue to rely on.

Example:

`Existing project/user configuration survives an update unless an explicit migration contract says otherwise.`

### Authority / ownership claim

Which component owns a decision or source of truth.

Example:

`The host OpenCode controller remains execution authority; CodeSleuth does not introduce a second agent runtime.`

### Ordering / relational claim

A meaningful relationship between actions, states, identities, or authorities.

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

Important end-to-end journeys are part of the semantic surface when supported product contracts make them material.

### Bound claim

A user-relevant, compatibility-relevant, safety-relevant, or architecture-relevant bound that must hold.

Examples include:

- latency or responsiveness bounds that materially affect a supported workflow;
- memory, storage, request-size, or concurrency limits exposed as product behavior;
- retry, timeout, lease, or expiry bounds that define correctness rather than a private tuning detail.

Example:

`A stalled child review is detected within the documented watchdog bound rather than waiting indefinitely.`

Do not promote every incidental benchmark number or implementation constant into a semantic claim. A bound belongs in the semantic surface only when consumers, accepted architecture, safety, compatibility, or product behavior rely on it.

## Claim taxonomy is not a substitute for evidence

The claim types above are a compact review vocabulary, not an ontology that must classify every sentence exactly once.

A material statement may legitimately have several dimensions. For example:

```text
Revoked credentials cannot authorize a write after revocation becomes authoritative.
```

can be recorded as:

- a negative claim about forbidden authorization;
- a security-domain claim;
- an ordering/authority claim about when revocation becomes authoritative.

Use **claim type** to describe the logical shape of the obligation. Use **domain tags** to describe where it belongs, for example:

`security`, `persistence`, `lifecycle`, `update`, `UX`, `API`, `compatibility`, `performance`, `concurrency`, `evidence`, `controller`, or `state`.

Do not invent a new claim type merely because a new subsystem exists.

Keep these records distinct from claims:

- **ASSUMPTION** — a condition under which a claim or historical implementation was believed to hold;
- **RATIONALE** — why a design or claim was adopted;
- **MECHANISM** — how an implementation currently realizes a claim;
- **EVIDENCE** — what observation, test, contract, source, or authority supports a conclusion;
- **PROVENANCE** — where the claim, rationale, or negative knowledge came from.

This distinction matters during refit because assumptions and mechanisms may expire while the claim survives.

## Negative-claim evidence protocol

Material negative claims deserve stronger handling than storing a sentence containing `must not`.

There are three distinct risks:

1. **Representation risk.** Negated requirements may be less robust for an LLM to retain and apply than an equivalent constructive formulation, especially in long or competing context.
2. **Execution risk.** A prohibition such as `do not create a second update authority` names the forbidden concept without directly specifying the valid state that should exist instead.
3. **Verification risk.** A positive capability can often be supported by an executable witness. A universal negative normally cannot be established by one successful happy path; review must actively seek a counterexample inside a stated scope.

Therefore a material negative claim SHOULD be represented by more than a naked prohibition.

### Required negative-claim record

Use this shape where practical:

```text
ID: N17

Forbidden state:
    Failed verification triggers restart into the candidate installation.

Constructive invariant:
    After failed verification, the current known-good installation remains
    authoritative and no restart into the failed candidate is initiated.

Violation witness / counterexample predicate:
    verification == FAIL
    AND restart(candidate_installation) == TRUE

Scope:
    supported self-update/restart paths

Oracle:
    fault-injected update/restart integration test

Provenance:
    contract / regression / incident / accepted review evidence
```

The **forbidden state** preserves the negative knowledge.

The **constructive invariant** tells a coding model what valid state should exist instead of forcing it to reason only by suppressing the forbidden concept.

The **violation witness** turns the claim into an adversarial search target.

The **scope** prevents a bounded review from pretending to prove an unbounded universal statement.

The **oracle** identifies how the project currently attempts to detect violation.

The **provenance** preserves why this prohibition exists, which is often the first thing lost after the original incident or prompt disappears from active context.

### Adversarial review mode

For a positive capability claim, a reviewer often searches for a valid witness:

> Can the supported path succeed?

For a negative claim, invert the posture:

> Can I make the forbidden state happen through any supported or materially adjacent path inside the stated scope?

Inspect alternate entry points, failure paths, retries, concurrency, persistence/restart boundaries, compatibility paths, background jobs, administrative paths, and bypasses where relevant to the claim.

A positive happy-path PASS is not evidence that a negative claim was tested unless that path actually exercises the forbidden-state boundary.

### Evidence wording for negative claims

Do not report `VERIFIED: impossible` merely because a finite test suite did not trigger the state.

Prefer language that matches the evidence actually obtained:

- **COUNTEREXAMPLE FOUND** — the negative claim is violated;
- **NO COUNTEREXAMPLE FOUND IN INSPECTED SCOPE** — bounded review/testing found none;
- **STRUCTURALLY GUARDED** — an explicit architecture/type/state-machine boundary prevents the state, with the guard identified;
- **FORMALLY PROVEN** — only when an actual formal proof justifies that wording.

Most repository reviews should use one of the first three. Testing does not acquire universal quantification merely because the CI checkmark is green and cheerful.

### Active-context retention

When a change touches a subsystem or boundary associated with a material negative claim, retrieve the claim back into active review context together with its constructive invariant and violation witness.

Do not rely on a prohibition written once in a large instruction file remaining perfectly salient tens of thousands of tokens later.

The practical pattern is:

```text
changed boundary
    -> retrieve related positive + negative claims
    -> retrieve constructive invariant
    -> attempt violation witness
    -> implement/review
    -> re-run the strongest practical oracle
```

This is especially important in LLM-driven work, where a later coding agent may have no memory of the incident or previous prompt that originally produced the negative knowledge.

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
-> only then decide whether delivery is reuse, port/adaptation,
   reimplementation, a separate current change, no change, defer, or block
```

A normal cherry-pick or backport can therefore be the correct delivery mechanism for a semantic refit. The terms operate at different levels.

Branch age, diff size, conflict count, and whether Git applies a patch cleanly do **not** determine semantic correctness.

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

## CodeSleuth authority and evidence mapping

Semantic refit does not replace CodeSleuth's existing contract machinery.

For CodeSleuth itself:

- `docs/SIB0-CAPABILITY-INVENTORY.md` freezes the fundamental capability-class and ownership model for the current architectural generation;
- `docs/PROTECTED-CAPABILITY-CONTRACTS.md` defines preservation obligations after acceptance;
- `docs/protected-capabilities.json` indexes recorded contracts, provenance, dependencies, fingerprints, and per-contract forbidden regressions;
- contract meaning is triangulated from current code/config, normative/public documentation, and executable tests;
- disagreements remain explicitly classified as `CODE_AHEAD`, `DOC_AHEAD`, `TEST_AHEAD`, `CONTRADICTED`, or `UNPROVEN` rather than being silently reconciled for convenience;
- `review_state` and append-only finding/EHA ledgers provide durable evidence/progress authority;
- reports, Mermaid, context projections, old PR summaries, and model prose are derived/navigation surfaces, not stronger authority than exact evidence;
- EHA binds maturity claims to one exact SHA and never transfers acceptance from historical source work to the refitted composition.

Semantic status such as `REQUIRED` or `RETIRED` is about a product claim. It does **not** replace capability lifecycle status such as `implemented`, `sib1_accepted`, `sib2_integrated`, or `protected`, and it does not replace contract-drift classifications.

## Do not rely on mystical `intent`

`Recover the old intent` is useful shorthand, but it is not a sufficient evidence rule.

A historical change can contain conflicting signals: an issue may require immediate revocation, an implementation may use a 60-second TTL, a test may assert the TTL, and a review comment may call that TTL temporary.

There is no reliable process that extracts one metaphysical `true intent` from that record.

Instead, recover **evidenced historical claims, assumptions, constraints, design rationale, and negative knowledge**, and preserve their provenance.

A model summary, old PR description, generated report, or previous review is navigation evidence, not sufficient proof by itself.

## Separate semantic status from delivery decision

Do not collapse `what should be true now?` and `what code should we write now?` into one label.

### Semantic / normative status

Use these states for material claims:

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

## Compatibility with the earlier stale-work shorthand

Existing CodeSleuth history and handoffs frequently use `REAPPLY / SUPERSEDED / REFIT / DROP`. They remain understandable as a compact stale-work review shorthand, but they must not erase the two-axis distinction above.

A typical mapping is:

| Legacy shorthand | Semantic status | Typical delivery |
| --- | --- | --- |
| `REAPPLY` | `REQUIRED` | `REUSE` or `PORT / ADAPT` |
| `REFIT` | `REQUIRED` | `PORT / ADAPT` or `REIMPLEMENT` |
| `SUPERSEDED` | `SUPERSEDED` | `NO CHANGE` |
| `DROP` | **ambiguous** | only valid after resolving to `RETIRED`, `UNRESOLVED`, or `CONFLICTED` plus an explicit delivery decision |

New material refit evidence should prefer the explicit two-axis model. In particular, never use `DROP` as a shortcut for `hard to integrate`.

## Evidence and epistemic status

Passing tests are evidence, not omniscience.

Different claims require different oracles. Prefer the cheapest oracle strong enough to exercise the claim honestly.

A useful evidence ladder is:

1. **Code oracle** — type/build/static checks.
2. **Behavioral oracle** — unit, integration, state, API, or contract tests.
3. **Journey oracle** — black-box CLI/TUI/web workflow from supported entry state to observable result.
4. **Presentation oracle** — accessibility/viewport/screenshot/interaction-state evidence where presentation is part of the claim.
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

Negative claims add a second axis to oracle selection: the evidence must attempt the **violation**, not merely replay the positive happy path. See [Negative-claim evidence protocol](#negative-claim-evidence-protocol).

## Why this matters for LLM-driven development

Code-generating LLMs can make implementation changes much faster than a maintainer can manually revalidate the entire product.

A later coding model may understand the current task and current code but know nothing about a failure mode or compatibility guarantee that a previous model encoded implicitly months earlier.

That creates a dangerous split:

`semantic ownership != implementation ownership`

CodeSleuth should therefore help repositories retain **external semantic memory** that survives individual prompts, agents, context windows, refactors, dependency updates, and implementation rewrites.

The goal is not to pretend that an LLM can perfectly infer user experience. It is to give the model a bounded set of evidenced claims and progressively stronger oracles, then make remaining human-only uncertainty explicit.

A human maintainer should ideally validate the small remainder automation cannot establish, not rediscover every historical capability after each generated change.

## Refit-readiness of repository documentation

A repository is **refit-ready** to the extent that a future maintainer or coding model can reconstruct its material semantic surface without depending on one person's memory or one old implementation.

Refit-readiness is a documentation/evidence quality property, **not a promotion status and not an additional SIB degree**.

Documentation and evidence should make the following recoverable where materially relevant:

1. **Capabilities** — what users/operators/consumers can do.
2. **User journeys** — important supported paths from intent to observable result.
3. **Guarantees and invariants** — including relational and ordering properties.
4. **Negative knowledge** — forbidden states, their constructive invariants, useful violation witnesses, and provenance that explains why they must not return.
5. **Authority boundaries** — who owns state, execution, lifecycle, persistence, security, evidence, and other product decisions.
6. **Compatibility obligations** — what external consumers may rely on and for how long.
7. **Evidence mapping** — which tests/gates/oracles support which claims and what they do not prove.
8. **Provenance** — where important claims came from: contracts, incidents, accepted decisions, issues, tests, or historical work.
9. **Intentional semantic changes** — explicit retirement/supersession/new-policy records rather than silent drift.
10. **Unknowns** — important claims that are only partially verified or require human UX judgment.

This does **not** require one giant specification file. The semantic memory may be distributed across contracts, tests, ADRs, user/operator documentation, review evidence, context projections, and reports as long as the authority chain is explicit and recoverable.

## A practical stale-work refit pattern

When useful stale work must be reconciled with a changed target, the following is a practical implementation pattern, not the definition of semantic refit itself:

1. Freeze exact source and target identities.
2. Recover evidenced historical claims and negative knowledge from source code, tests, issues, review history, and follow-up fixes.
3. Identify current normative authority and current architecture for each affected claim.
4. Determine what the target already provides and prove coverage rather than assuming it.
5. Record semantic status and delivery disposition separately.
6. For each material negative claim, record the forbidden state, constructive invariant, violation witness, scope, and adversarial oracle.
7. Implement the smallest target-native delta required by surviving claims.
8. Preserve attribution and provenance even when source code does not survive.
9. Add positive and negative regression evidence at the strongest practical oracle level.
10. Run canonical acceptance on the exact resulting composition.
11. Record residual unknowns and any required targeted human validation.

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
- For each material negative claim, what valid state should hold instead, what constitutes a violation witness, and what adversarial evidence searched for that violation?
- What tests or other oracles support each conclusion?
- What is still not known or not machine-verifiable?
- Which intentional semantic changes have an explicit current authority rather than being disguised as `refit`?

The new implementation should be understandable without keeping the historical patch open forever. At the same time, the relationship between historical product knowledge and the current semantic surface must remain traceable.

## Anti-patterns

Do not use semantic-refit language to justify:

- ordinary patch movement that needs no semantic reconciliation;
- rewriting somebody else's work until it means something different while retaining their feature label;
- declaring difficult behavior `SUPERSEDED` without coverage evidence;
- declaring behavior `RETIRED` without an authority that retires it;
- copying old tests while discarding newer contracts;
- preserving obsolete implementation-specific tests as if mechanisms were requirements;
- weakening or rewriting acceptance to make a stale implementation pass;
- storing a material negative claim only as `DO NOT X` without a constructive valid-state invariant or a way to recognize violation;
- declaring a universal negative `VERIFIED` merely because finite happy-path testing found no failure;
- claiming UX preservation from code/build evidence alone;
- treating a generated summary, Mermaid graph, model report, or context projection as stronger evidence than current verified source and accepted contracts;
- forcing a full semantic-archaeology ritual onto a routine clean port whose meaning and authority have not changed.

## Relationship to SIB and exact-head acceptance

Semantic refit, SIB maturity, and Exact-Head Acceptance are separate concepts.

- **Semantic refit** describes the desired preservation/reconciliation of the product's evidenced semantic surface across change.
- **SIB0/SIB1/SIB2** describe architectural maturity states.
- **Exact-Head Acceptance (EHA)** binds acceptance evidence to one exact repository state.

A refit does not promote a SIB ref and does not inherit acceptance from its source work.

For CodeSleuth release construction, historical or divergent work recovered onto the current integration line must satisfy the current semantic surface and then establish fresh acceptance on the exact resulting release-stream head.

The practical evidence statement is:

`historical semantic evidence + current normative authority + explicit claim dispositions + target-native implementation + exact-head evidence`

not:

`old PR was green + cherry-pick succeeded`

## Canonical short statement

> **Semantic refit is the preservation or explicit reconciliation of a product's evidenced user-relevant and architecture-relevant semantic surface across implementation and architectural change. For users, the goal is continuity. For maintainers, every known semantic discontinuity and evidence gap must be observable. In LLM-driven development, the same record acts as external semantic memory so a code-generating model does not have to rediscover the product from implementation alone.**
