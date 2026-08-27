# Contributor error-pattern prevention

**Status:** normative contributor hardening guidance  
**Scope:** all CodeSleuth source, tests, documentation, workflow, packaging, lifecycle, and agent-authored changes  
**Origin:** recurring failure classes observed while triaging open PRs #77 and #78 against `dev/release-0.4.0`

This document turns repeated review findings into prevention rules. The objective is not to ban difficult changes. It is to stop the same class of mistake from being rediscovered after implementation, after CI, or after a feature has already become product-visible.

The repository-side scanner is:

```bash
python scripts/contributor_antipatterns.py prewrite
python scripts/contributor_antipatterns.py scan --strict
```

Run `prewrite` before the first repository modification in a work session. Run `scan --strict` after the change and before ordinary tests. The canonical acceptance workflow also runs the strict scanner.

## Error-pattern catalogue

### EP-01 — mutable identity replaces exact identity

**Failure shape:** a display or state path substitutes `remote`, branch/ref, label, filename, or another mutable locator for an exact commit/blob/content identity.

**Observed witness:** PR #77 formatted CodeSleuth source as `remote@ref` while the installed metadata also contained exact `source.commit`. A movable ref is useful context, but it is not the identity of the installed source.

**Rule:** when an exact commit/hash/blob/content digest exists, it is the primary identity. Mutable names are supplemental presentation only.

**Prevention:** tests must cover detached/null-ref states and movement of branch/ref names. A formatter that claims source identity must not become less precise than its authoritative metadata.

### EP-02 — failure is collapsed into absence

**Failure shape:** a probe exception, parse failure, permission error, conflict, or temporary unreadability is represented by the same state as "does not exist", after which cleanup code prunes or deletes the object.

**Observed witness:** PR #77 used a `reachable=false` outcome both for a missing repository path and for lifecycle/dependency probe failures, allowing an existing but unprobeable repository to disappear from the host catalog.

**Rule:** destructive cleanup requires positive evidence of absence. `missing`, `degraded`, `unreadable`, `conflicted`, and `probe_error` are different states.

**Prevention:** preserve an existing object with explicit degraded/error metadata when probing fails. Add a regression case where the path exists but the probe raises.

### EP-03 — a new default is called backward compatibility

**Failure shape:** an existing no-argument/default behavior changes, while the old behavior remains reachable only through a newly introduced opt-in flag.

**Observed witness:** PR #78 changed the default `eha_state_mermaid` result from Mermaid source to a JSON envelope and called a new `responseFormat: mermaid_source` option compatibility. Existing callers cannot send an option that did not previously exist.

**Rule:** preserving an old behavior behind a new flag does not preserve old callers. Existing defaults remain stable unless the contract is deliberately versioned or an explicit breaking-change decision and migration are recorded.

**Prevention:** every public/default contract change needs an old-caller regression test that invokes the API exactly as the old caller did.

### EP-04 — product exposure outruns the supported runtime matrix

**Failure shape:** settings/TUI/CLI expose a feature as normally selectable before installability and execution have been proven on the platforms/interpreters the product claims to support.

**Observed witness:** PR #78 exposed Graphify in normal settings/TUI while the exact transitive runtime lock was documented only for Windows/Python 3.14 and hosted acceptance exercised Python 3.10/3.12 with the provider absent.

**Rule:** the product-visible support matrix must be a subset of the proven runtime matrix. Incubating or developer-only functionality must stay behind an explicit incubation boundary until the intended normal profiles execute successfully.

**Prevention:** test both dependency-absent and dependency-enabled profiles. A selectable normal feature must have at least one non-skipped enabled-path acceptance job for every advertised support profile or an explicitly narrower support statement.

### EP-05 — green CI does not execute the feature path

**Failure shape:** the suite is green because the critical test skips when an optional runtime is absent, or because a newly added smoke script is not reached by the canonical umbrella command/workflow.

**Observed witness:** PR #78 added provider/topology/Mermaid QA smoke commands but the default `bun run test` did not call them; Python provider execution tests skipped when `.runtime/graphify-provider` was absent.

**Rule:** a green gate is evidence only for paths it actually executed. Critical enabled feature paths must be non-skippable in at least one canonical job.

**Prevention:** all `tests/*_smoke.ts` scripts exposed through `test:*` package commands must remain reachable from the default `test` umbrella unless a separate canonical workflow job executes them. Skipped tests must be reported as unsupported/unexecuted evidence, never as feature acceptance.

### EP-06 — ambient executable identity

**Failure shape:** runtime code launches a bare `python`, `python3`, or another ambient executable from `PATH` when the behavior depends on using a particular interpreter/runtime.

**Observed witness:** PR #78 launched the Graphify adapter through bare `python`, even though the feature depended on an isolated exact runtime profile.

**Rule:** runtime identity must be explicit when identity matters. Python child processes should normally use the current interpreter (`sys.executable`) or an explicit configured runtime path. Optional external runtimes need an explicit compatibility/identity contract.

**Prevention:** do not assume the executable named `python` is the interpreter that launched CodeSleuth. Exact package versions are not enough if the executing interpreter itself is ambient.

### EP-07 — deferred or rejected scope silently returns as implementation

**Failure shape:** a PR implements a feature that current planning/issue/contract authority already marked deferred, not planned, retired, or requiring a new adoption decision.

**Observed witness:** PR #78 implemented Graphify M2-M5 for the 0.4.0 line after the current-release issue had recorded those milestones as deferred/not planned.

**Rule:** before coding, resolve current scope authority. Historical plans and attractive unfinished branches do not override a later disposition.

**Prevention:** record the current issue/plan/contract decision in the change plan. A deferred feature requires a new explicit adoption decision against the current baseline before product integration.

### EP-08 — claims are stronger than the evidence

**Failure shape:** documentation, CHANGELOG, PR checklists, or status text says `complete`, `PASS`, `supported`, `compatible`, or equivalent while the relevant exact-head/runtime/platform gate did not execute.

**Rule:** distinguish implementation state from acceptance state. `implemented`, `tested locally`, `CI passed with provider absent`, `incubating`, and `accepted on exact SHA` are materially different claims.

**Prevention:** every acceptance/support claim names the exact evidence scope. Skipped environments and untested profiles are listed as limitations, not silently absorbed into PASS.

### EP-09 — provider provenance is promoted without re-verification

**Failure shape:** an external parser/provider's confidence or provenance label is treated as sufficient proof for CodeSleuth `verified_source`.

**Rule:** external output is candidate data. Promotion requires CodeSleuth-side checks of the exact tracked path/blob and any line/range contract, plus exact semantic mapping. Inferred/ambiguous provider output remains inference or is dropped.

**Prevention:** test malformed/out-of-range source locations, dirty tracked files, unknown relations, ambiguous edges, and disagreement between provider metadata and current Git/source.

### EP-10 — lifecycle is asymmetric

**Failure shape:** a feature can be selected, shown as available, configured, or removed, but a normal installed CodeSleuth instance lacks a reproducible way to install/activate the exact dependency profile it needs.

**Observed witness:** PR #78 added normal provider selection and runtime removal, while the exact installation lock lived in development-checkout `tools/...` state rather than the ordinary installed pack.

**Rule:** product-visible optional dependencies need a complete lifecycle contract: absent status, explicit installation/activation, compatible status, use, update policy, removal, and disposable-install coverage.

**Prevention:** test lifecycle from an actual disposable installed target, not only from the CodeSleuth source checkout.

## Mandatory pre-write review

Before the first modification in a work session, establish all of the following:

1. **Exact target identity:** current HEAD and intended target/base are known.
2. **Current scope authority:** the feature is not currently deferred/retired/rejected and does not require a new architecture/adoption decision.
3. **Existing caller contract:** no-argument/default behavior and public output/input shapes are known before changing them.
4. **Identity/provenance authority:** exact SHA/blob/hash fields are identified and mutable labels are classified as presentation only.
5. **Failure-state model:** absence is distinct from probe/read/parse/dependency failure before any cleanup or pruning is written.
6. **Support matrix:** product exposure is no broader than the runtime/platform profiles that will actually execute in acceptance.
7. **Execution identity:** subprocess/interpreter/provider identity is explicit where correctness depends on it.
8. **Canonical gate reachability:** every new critical test path is reached by the real umbrella workflow and is non-skippable in at least one evidence-producing profile.
9. **Evidence wording:** planned docs/CHANGELOG/PR claims will not outrun the tests actually executed.
10. **Lifecycle completeness:** optional dependencies have an installed-target path for status/install-or-activation/use/removal before normal UI exposure.

If one of these cannot be established, stop implementation of that part and record it as `UNRESOLVED`, `DEFER`, or `BLOCK` rather than guessing a convenient contract.

## Repository scanner

The scanner intentionally separates **hard mechanical findings** from **semantic review prompts**.

Hard checks currently include:

- orphaned Bun smoke tests that are exposed as `test:*` commands but are not reached by the default `test` umbrella;
- ambient `python`/`python3` child-process launch in CodeSleuth runtime code where the current interpreter or an explicit runtime should be used.

Heuristic warnings include:

- optional/runtime-dependent pytest skips that may create green-by-skip evidence;
- source/identity label functions that consume mutable refs without an obvious exact commit/hash;
- broad exception handling in state/catalog code combined with pruning/deletion signals.

Warnings require review, not blind mechanical rewriting. The point is to surface the dangerous decision before it becomes a merge blocker.

## Fix strategy for this class of defects

Prefer repairing the **state model or contract boundary**, not just the line that triggered review:

- replace mutable identity with exact identity plus optional display context;
- introduce an explicit degraded/error state instead of deleting on failure;
- preserve old defaults and add a new opt-in/versioned contract;
- narrow product exposure until the enabled path is genuinely supported;
- wire critical tests into canonical gates and add at least one non-skipped enabled profile;
- replace ambient runtime lookup with explicit interpreter/provider identity;
- reopen scope explicitly instead of smuggling deferred work through implementation;
- downgrade claims to the evidence actually available;
- keep third-party structural claims as candidates until CodeSleuth re-verifies them;
- complete install/status/use/remove lifecycle before normal UX exposure.

These are preservation rules. They are intended to make difficult feature work easier to integrate, not to make the repository allergic to change.
