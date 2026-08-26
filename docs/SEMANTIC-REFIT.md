# Semantic refit

## Definition

A **semantic refit** is the integration process used when an older branch or pull request contains behavior that is still wanted, but its original patch was authored against a repository state whose implementation or contracts have since changed.

A semantic refit does **not** preserve the old diff. It preserves the old change's **intended behavior, invariants, and useful design decisions**, then re-implements the smallest equivalent delta on top of the current accepted repository state.

The governing rule is:

> Preserve current accepted semantics first; re-apply the stale change's still-valid intent second; prove the resulting composition on its exact commit.

This is stronger than resolving merge conflicts and safer than a mechanical cherry-pick. Conflict-free application is not evidence of semantic compatibility.

## When semantic refit is required

Use semantic refit when any of the following is true:

- the source branch is materially behind the current accepted integration head;
- touched files have changed their ownership, persistence, lifecycle, naming, security, or compatibility contracts since the source work was authored;
- the old patch would overwrite newer behavior even if Git can apply it cleanly;
- the source PR was green only on an older base;
- the desired result is a narrow subset of a stacked or scope-drifted branch;
- the current architecture requires a different implementation shape to preserve the original intent safely.

If the source change is already based on the current accepted head and its touched contracts are unchanged, an ordinary rebase/cherry-pick may be sufficient. Do not call routine patch movement a semantic refit merely because the phrase sounds impressive.

## Required inputs

A semantic refit starts from four concrete inputs:

1. **Current accepted base** — exact target commit SHA and the acceptance evidence attached to it.
2. **Source change** — PR/branch/commit containing the behavior to recover.
3. **Intent inventory** — the behavior, invariants, boundaries, and tests that made the source change valuable.
4. **Current-semantic inventory** — the newer behavior now present in every overlapping file or subsystem.

The source branch is evidence about intent, not authority over the current tree.

## Procedure

1. **Freeze the target base.** Record the exact accepted SHA before editing.
2. **Extract intent from the stale work.** Identify what the source change was trying to achieve independently of its exact hunks, filenames, or module layout.
3. **Inspect current semantics.** For every overlapping path, identify changes made after the source branch diverged, especially security, lifecycle, persistence, naming, compatibility, and user-data-preservation rules.
4. **Classify source hunks.** Mark each meaningful part as still required, already superseded, incompatible with current semantics, or obsolete.
5. **Re-implement the minimal valid delta.** Apply only the still-required behavior using the current architecture and contracts. Do not replace a newer file with a stale blob merely to make the old patch fit.
6. **Preserve current contracts deliberately.** When the current tree has added a compatibility surface or stronger invariant since the source work, retain it unless the refit explicitly and separately changes that contract.
7. **Add or retain executable evidence.** Existing tests must continue to cover preserved semantics; add focused regression coverage for any new integration seam introduced by the refit.
8. **Run canonical acceptance on the exact refit head.** Old CI is provenance, not acceptance for the new composition.
9. **Record divergences from the source patch.** The integration PR must explain which old implementation details were intentionally not carried forward and why.

## Patch classification

Use this vocabulary during review:

- **REAPPLY** — the old behavior is still required and is implemented against current semantics.
- **SUPERSEDED** — current code already provides the intended behavior; no new delta is needed.
- **REFIT** — the intent remains valid, but the implementation must differ to preserve newer contracts.
- **DROP** — the old behavior is obsolete or conflicts with accepted current architecture.

This classification keeps a semantic refit reviewable. A refit should be explainable as a set of deliberate decisions, not as a mysterious hand-edited merge.

## Acceptance standard

A semantic refit is acceptable only when all of the following are true:

- the refit is based on the exact current accepted integration state or an explicitly accepted descendant;
- no newer accepted behavior was lost merely because the source branch predated it;
- the desired source intent is present in the new implementation;
- compatibility differences from the source patch are documented;
- focused tests cover the refit seam where appropriate;
- the repository's full canonical acceptance gate passes on the exact resulting commit.

The evidence statement is:

`source intent + current accepted semantics + refit delta + exact-head acceptance`

not:

`old PR was green + cherry-pick succeeded`

## Anti-patterns

Do not use these as substitutes for semantic refit:

- taking `--theirs` for overlapping files from the stale branch;
- replacing a newer module wholesale with the old branch version;
- considering a conflict-free cherry-pick semantically safe;
- weakening tests until the stale implementation passes;
- copying only the old tests while dropping newer contract tests;
- declaring success from CI that ran before the current integration base existed;
- silently carrying unrelated scope drift from the source branch.

## CodeSleuth release use

For CodeSleuth release construction, semantic refit is the preferred recovery method for valuable stale PRs layered onto SIB2 descendants. It is especially important for lifecycle, update, naming, persistence, evidence, controller, and security boundaries because those areas can acquire stronger contracts while an older feature branch remains open.

A semantic refit does not promote or move SIB refs by itself. It produces a candidate integration state. Only exact-head canonical acceptance can make that candidate an accepted integration state.
