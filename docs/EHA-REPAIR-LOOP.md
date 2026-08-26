# EHA repair loop

## Status

This document is a **normative extension** of [`EXACT-HEAD-ACCEPTANCE.md`](EXACT-HEAD-ACCEPTANCE.md) and the SIB0/SIB1/SIB2 model in [`STABLE-INTEGRATION-BASELINE.md`](STABLE-INTEGRATION-BASELINE.md).

It defines what CodeSleuth maintainers must do when an Exact-Head Acceptance (EHA) target fails and requires repair.

The governing principle is:

> **An EHA campaign never repairs its own target. It only establishes what is true about that exact SHA. Repair produces a new SHA and therefore a new EHA target.**

A failing commit is not edited into passing status retroactively. Its failure remains part of the permanent engineering evidence chain.

## EHA repair loop

When an EHA target fails:

1. **Freeze the failing SHA.**
   - Do not force-push it.
   - Do not rewrite it.
   - Do not amend it.
   - Record the EHA level, failing test or path, observed failure, environment, and reproduction steps.

2. **Classify the defect by the maturity claim it invalidates.**
   - architectural defect -> **SIB0 blocker**;
   - capability implementation defect -> **SIB1 blocker**;
   - composition / integration / end-to-end defect -> **SIB2 blocker**.

3. **Create a repair branch directly from the failing SHA.**

   Example:

   ```text
   fix/eha-sib2-update-restart
   ```

   The branch must start from the exact failing commit unless a stronger reason is documented. Do not silently rebase the repair onto unrelated later work.

4. **Apply the minimum repair delta.**
   - Fix the demonstrated defect and the smallest directly related contract surface.
   - Do not mix opportunistic refactors, unrelated cleanup, feature population, dependency churn, naming work, or cosmetic rewrites into the repair.
   - If a broader architectural change is truly required, classify that honestly rather than disguising it as a local repair.

5. **Add a regression test that reproduces the discovered defect.**
   - The test must fail against the failing SHA for the reason under investigation, or otherwise provide equivalent reproducible evidence when exact historical execution is impractical.
   - The test must exercise the real contract at the appropriate level. A mock-only assertion is not sufficient when the defect occurred in an integrated user-visible path.

6. **Run focused tests on the repair branch.**
   - Run the smallest set that directly proves the repair and guards its immediate boundaries.
   - Focused tests are repair evidence, not full EHA evidence.

7. **Produce a new immutable candidate SHA `B`.**
   - Once the repair delta is committed and ready for acceptance, identify the exact new SHA.
   - Do not continue changing `B` while describing it as the same candidate.

8. **Only `B` becomes the new EHA target.**
   - Start a new EHA campaign against `B`.
   - The previous target remains a failed historical target.
   - No PASS result from the previous SHA is inherited automatically.

The repair sequence is therefore:

```text
EHA target A
    -> EHA test
    -> FAIL
    -> freeze A and record failure
    -> repair branch from A
    -> minimum repair delta
    -> regression test
    -> focused repair tests
    -> new candidate SHA B
    -> NEW EHA campaign on B
```

## A failed SHA remains failed

An EHA target that failed a required profile never becomes accepted retroactively.

Example:

```text
A = abc123

SIB0 EHA: PASS
SIB1 EHA: PASS
SIB2 EHA: FAIL
Reason: update succeeds but restart supervision does not reload the updated source.
```

After repair, `A` remains exactly that historical result. The project must not rewrite its record as if later fixes had changed what was true of `abc123`.

The proper disposition is:

```text
EHA-001
Target: abc123
SIB0: PASS
SIB1: PASS
SIB2: FAIL
Finding: EHA-SIB2-BLOCKER-003
Disposition: superseded by def456
```

The failed SHA is retained as provenance. It is useful evidence explaining why the repair exists.

## Acceptance evidence does not inherit across repair commits

The normal exact-head invariant applies without exception:

> **Acceptance evidence never implicitly propagates from the failing SHA to the repair SHA.**

If:

```text
A:
SIB0 PASS
SIB1 PASS
SIB2 FAIL

A -> B
```

then this is invalid:

```text
B:
SIB0 inherited PASS
SIB1 inherited PASS
SIB2 retest
```

CodeSleuth has no concept of inherited EHA PASS.

For the new candidate `B`, if the intended final claim is that `B` satisfies SIB0, SIB1, and SIB2, the required evidence is:

```text
B:
SIB0 EHA -> PASS
SIB1 EHA -> PASS
SIB2 EHA -> PASS
```

The previously developed tests, checklists, inventories, and automation may of course be reused. What must be new is the evidence execution attached to `B`.

## Re-running lower SIB levels after repair

A new SHA requires fresh EHA evidence for every SIB degree claimed for that SHA.

This does **not** mean that every repair requires a human to rediscover the entire architecture from zero.

Acceptance profiles should be designed so that re-validation is efficient but still attached to the new commit:

- **SIB0 rerun**: verify capability inventory, architectural slots, ownership, dependency direction, authority boundaries, and absence of architectural drift;
- **SIB1 rerun**: execute the capability implementation matrix and focused basic-path contracts for every SIB0 capability class;
- **SIB2 rerun**: execute the full canonical integration and end-to-end profile for the exact composed commit.

Thus the methodology is reusable, but the evidence identity is not.

## Repair classification and consequences

### SIB0 blocker

A defect is a SIB0 blocker when the architectural claim itself is false, for example:

- a fundamental capability class is missing from the declared inventory;
- two components independently claim authority over the same architectural responsibility;
- state, lifecycle, graph, controller, or runtime ownership is contradictory;
- a new fundamental capability class is required to make the architecture coherent;
- an existing fundamental class must be removed or fundamentally redefined.

A SIB0 repair may reopen architecture. If the capability-class inventory changes, establish a new SIB0 lineage explicitly.

### SIB1 blocker

A defect is a SIB1 blocker when the architectural slot exists but its basic implementation contract is not real or not functional, for example:

- a capability is still a stub or unreachable placeholder;
- the documented basic path does not execute;
- the implementation cannot perform its fundamental function;
- focused capability tests reveal a broken minimum contract.

The repair should remain inside the frozen SIB0 architecture unless evidence proves that the architecture itself was wrong.

### SIB2 blocker

A defect is a SIB2 blocker when implemented capabilities fail in composition or on a required end-to-end path, for example:

- update succeeds but restart does not reload the result;
- TUI dispatch reaches a runtime action but user-visible output disappears;
- CLI and durable state work separately but fail together;
- installer metadata disagrees with runtime version resolution;
- supported operating systems behave differently on a canonical path;
- the full acceptance matrix fails for the exact composition.

SIB2 repair is integration recovery, not feature population.

## Minimum repair delta rule

An EHA repair branch is not a general cleanup branch.

The repair delta should contain only:

1. the correction required by the recorded failure;
2. directly necessary supporting changes;
3. regression coverage for the defect;
4. minimal documentation changes required to keep the affected contract truthful.

Unrelated work must be split out.

This keeps the causal chain reviewable:

```text
observed failure
    -> specific repair
    -> regression proof
    -> new exact candidate
    -> new acceptance campaign
```

When the repair diff becomes large enough that reviewers can no longer explain why every changed line belongs to the failure, the repair scope has probably escaped its contract.

## Regression-test requirement

Every reproducible EHA defect should leave behind a regression test at the lowest level that can faithfully reproduce the failure.

Prefer real contract coverage over implementation-detail assertions.

Examples:

- a TUI click bug should be tested through real Textual interaction where practical, not only by directly invoking the handler method;
- an update/restart defect should verify both the update result and the resulting supervision/restart behavior;
- a persistence defect should verify durable state after the real operation, not merely that a write function was called;
- an exact-head CI defect should verify the literal checked-out SHA, not infer identity from a branch name or equivalent tree.

The purpose of the regression test is not merely to make the repair branch green. It is to prevent the same false acceptance in later EHA campaigns.

## Focused tests versus EHA

Focused repair tests answer:

> Did the proposed repair fix the demonstrated defect without immediately breaking its direct boundaries?

EHA answers:

> What maturity claims are proven for this exact new repository state?

These are different evidence classes.

A repair branch may have all focused tests green and still fail SIB0, SIB1, or SIB2 EHA for another reason.

Therefore:

> **Focused repair tests may qualify a commit to become an EHA candidate; they do not make it accepted.**

## Tester and repairer roles

The EHA campaign and the repair loop should be treated as separate roles even when the same human or agent performs them sequentially.

### EHA tester

The tester:

- freezes the target identity;
- executes the required profile;
- records evidence;
- classifies findings;
- issues PASS or FAIL;
- does not modify the target to obtain a better result.

### Repairer

The repairer:

- starts from the recorded failing SHA;
- fixes the specific finding;
- adds regression coverage;
- runs focused repair tests;
- produces a new candidate SHA.

### Next EHA campaign

The next tester then evaluates the new SHA independently.

Canonical rule:

> **Tester discovers. Repairer repairs. The next EHA campaign accepts or rejects the new exact SHA.**

This prevents acceptance from turning into an iterative edit-until-green session whose target identity changes underneath the evidence.

## Evidence ledger across repair cycles

Each EHA campaign should remain separately identifiable.

Example:

```text
EHA-001
Target: abc123
SIB0: PASS
SIB1: PASS
SIB2: FAIL
Blocker: update/restart composition

Repair:
Branch: fix/eha-sib2-update-restart
Parent: abc123
Candidate: def456
Regression: tests/test_update_restart.py
Focused repair tests: PASS

EHA-002
Target: def456
SIB0: PASS
SIB1: PASS
SIB2: PASS
```

This ledger makes the progression auditable without pretending that `abc123` was ever SIB2-accepted.

## When the repair itself changes architecture

Sometimes a failure reveals that the defect cannot be repaired within the existing architecture.

If fixing a SIB1 or SIB2 finding requires:

- adding a new fundamental capability class;
- changing ownership of a fundamental responsibility;
- introducing a second runtime, controller, graph authority, persistence authority, or orchestration layer;
- fundamentally redefining an existing capability class;

then the work is no longer an ordinary repair.

The architecture has reopened. Classify the issue as SIB0-impacting, update the capability inventory deliberately, and establish a new SIB0 claim before proceeding through SIB1 and SIB2 again.

Do not smuggle an architectural generation change through a patch labelled "fix".

## Branch and history discipline

For EHA repairs:

- keep the failing SHA reachable and unchanged;
- branch directly from it when practical;
- avoid force-pushing accepted or failed evidence-bearing SHAs;
- do not rewrite historical EHA results after later repairs;
- do not merge unrelated divergent green work into the repair candidate without treating the result as a new composition requiring its own acceptance;
- prefer a small, reviewable repair commit or series whose causal relationship to the finding is obvious.

If the repair candidate later receives additional changes, its old evidence no longer describes the new head. Assign the new head a new candidate identity and test it accordingly.

## Canonical repair-loop statements

> **A failing EHA SHA remains failed. Repair never changes history; it creates a new candidate.**

> **An EHA campaign never repairs its own target. It only issues a verdict for that exact SHA.**

> **A repair commit inherits code history, not acceptance evidence.**

> **Every SIB degree claimed for the repair SHA requires fresh evidence attached to that repair SHA.**

> **Focused repair tests qualify a candidate for EHA; they do not replace EHA.**

> **If repair changes the fundamental capability-class inventory or authority model, architecture has reopened and SIB0 must be re-established.**

The practical loop is:

```text
freeze -> classify -> branch -> minimally repair -> regress -> focus-test -> new SHA -> new EHA
```
