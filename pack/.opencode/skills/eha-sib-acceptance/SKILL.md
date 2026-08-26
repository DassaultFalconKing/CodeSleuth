---
name: eha-sib-acceptance
description: Exact-Head Acceptance discipline for SIB0/SIB1/SIB2 testing, evidence recording, and repair-loop lineage
---

# EHA / SIB acceptance

Use this skill whenever a task asks whether an exact CodeSleuth repository state
is architecturally complete, implementation complete, integration complete,
ready to become a SIB, or ready to continue release construction from a proven
baseline.

This is an evidence protocol, not a second supervisor. OpenCode's primary
`build` agent remains the controller. Use CodeSleuth's durable review state and
EHA tools to persist what was actually proven.

## Canonical model

Read the installed copies of:

- `docs/STABLE-INTEGRATION-BASELINE.md`;
- `docs/EXACT-HEAD-ACCEPTANCE.md`;
- `docs/EHA-REPAIR-LOOP.md`;
- `docs/DURABLE-EVIDENCE-STORE.md`;
- `docs/SEMANTIC-REFIT.md` when stale/divergent work is involved.

The compact rule is:

> SIB levels define **what** is proven; EHA defines **which exact SHA** the proof belongs to.

The maturity claims are:

- **SIB0** — architectural completeness: the fundamental capability-class
  inventory and ownership/boundary model are represented, coherent, and frozen;
- **SIB1** — implementation completeness: every SIB0 capability class has a
  real basic implementation satisfying its own required contract;
- **SIB2** — integration completeness: those implementations work together
  through intended end-to-end paths and the exact composition passes the full
  canonical acceptance profile.

Acceptance evidence never implicitly propagates to an ancestor, descendant,
divergent branch, synthetic PR merge commit, or merely equivalent-looking
composition.

## Durable evidence authority

Start or load `review_state_*` before an EHA campaign. EHA records are stored in
the same durable review evidence boundary under:

```text
.opencode/state/reviews/<reviewId>/eha.ndjson
```

The storage semantics are inherited from `docs/DURABLE-EVIDENCE-STORE.md`:

- `state.json` is a mutable atomic checkpoint snapshot;
- `findings.ndjson` is append-only finding history;
- `eha.ndjson` is append-only EHA/SIB/repair history;
- reports and Mermaid are derived views;
- raw state-file rewrites are forbidden.

Use the tools exported from `eha_state`:

- `eha_state_start_campaign` — bind a new campaign to literal current HEAD;
- `eha_state_record_verdict` — record SIB0/SIB1/SIB2 PASS or FAIL;
- `eha_state_record_repair` — record the repair-loop decision and lineage;
- `eha_state_load` — reload campaign/verdict/repair history;
- `eha_state_mermaid` — derive a bounded Mermaid history view.

The NDJSON ledger is acceptance evidence state. Mermaid is only a human-readable
projection of it and never becomes authority by itself.

Do not raw-rewrite, truncate, delete, or edit old `eha.ndjson` lines to make a
later campaign look cleaner. Later events may change the current read model, but
historical events remain recorded. Raw `cat`/`grep` is allowed only for read-only
audit/debug/recovery/discovery; reload through `eha_state_load` before making a
material acceptance claim because raw text search does not enforce exact-head,
claimability, classification, or schema semantics.

## Starting an EHA campaign

1. Capture literal `git rev-parse HEAD`.
2. Confirm the requested EHA target SHA equals that literal HEAD.
3. Capture branch and dirty state.
4. Start/load the durable `review_state` checkpoint.
5. Call `eha_state_start_campaign` with the exact SHA and useful branch/scope.
6. From this point, do not change HEAD during the test campaign.

If HEAD changes before a verdict is recorded, the campaign is invalidated. Do
not continue under the old target identity.

## SIB0 profile

SIB0 asks whether the architectural generation is coherent and frozen, not
whether all code is finished.

Derive the actual capability inventory from authoritative docs and source.
Verify at minimum:

- every fundamental capability class has an explicit architectural slot;
- ownership and dependency direction are coherent;
- controller/runtime ownership is unambiguous;
- lifecycle/update ownership is unambiguous;
- persistent-state authority is unambiguous;
- context graph remains bounded derived linkage state, not a second source of
  repository truth;
- Mermaid remains a presentation projection, not graph/evidence authority;
- CLI/TUI/profile/tool/report/external-integration seams fit the declared model;
- no accidental second runtime, controller, persistence authority, graph
  authority, or orchestration layer has appeared;
- code/docs/tests do not materially contradict the claimed architecture.

Record material blockers as ordinary `review_state_record_finding` findings
against exact source evidence.

Then call `eha_state_record_verdict` for `SIB0` with:

- `PASS` only if the architectural completeness claim is actually proven;
- otherwise `FAIL` with blocker finding IDs and concrete evidence.

## SIB1 profile

SIB1 asks whether every SIB0 capability class has a real basic implementation.

For every capability class, establish:

- reachable implementation entry point;
- real basic successful path;
- relevant failure behavior;
- focused tests/verification;
- ownership boundary remains the SIB0 boundary.

A file, stub, interface, mock-only path, documentation promise, or unreachable
command does not count as implementation.

Record `SIB1 PASS` or `SIB1 FAIL` with the actual capability profile and blocker
finding IDs.

A SIB1 PASS is claimable only when SIB0 on the same SHA also passed. The durable
EHA summary enforces this distinction rather than inferring maturity from a
single green component test.

## SIB2 profile

SIB2 asks whether the exact composed system works together.

Exercise the real integrated paths required by the current canonical contract,
including applicable combinations of:

- install/configure/verify/update/restart/uninstall;
- source-checkout and installed-runtime modes;
- CLI and TUI entry paths;
- real TUI interaction and visible activity feedback;
- OpenCode controller/tool execution;
- durable review state;
- context graph save/query/Mermaid projection;
- MCP repository evidence;
- profile/tool/Skill integration;
- report workspace;
- supported Python/OS matrix;
- Bun durable-state/context-graph/EHA gates.

The acceptance workflow must verify the literal target SHA. A synthetic PR
merge SHA is not the target merely because its tree happens to be equivalent.

Record `SIB2 PASS` only after the full required profile passed on the same SHA.
SIB2 becomes claimable only when SIB0, SIB1, and SIB2 have all passed on that
same target.

## EHA repair loop

An EHA campaign never repairs its own target.

If a required profile fails:

1. freeze the failing SHA; never force-push/amend/rewrite it;
2. record the EHA level, failing test/path, observed failure, environment, and
   reproduction;
3. classify the blocker:
   - architectural -> SIB0;
   - capability implementation -> SIB1;
   - composition/E2E -> SIB2;
4. branch from the failing SHA;
5. make the minimum repair delta;
6. add a regression test faithful to the discovered failure;
7. run focused repair tests;
8. obtain a new candidate SHA;
9. call `eha_state_record_repair` on the failed campaign;
10. start a **new** EHA campaign on the new SHA.

The old SHA remains failed in history. Never edit its verdict into PASS because
its descendant was repaired.

A repair commit inherits code history, not acceptance evidence. If the project
wants to claim SIB0/SIB1/SIB2 for repaired SHA `B`, execute fresh SIB0, SIB1,
and SIB2 profiles against `B`.

If the repair requires a new fundamental capability class or changes a
fundamental ownership/authority model, classify it as architecture reopened and
return to SIB0 rather than smuggling an architecture generation change through
a patch labelled `fix`.

## Semantic refit interaction

Stale or divergent work is not repaired by replaying stale files wholesale.
Use the semantic-refit discipline first:

- recover still-valid intent/invariants;
- preserve current accepted semantics;
- apply the minimum current-semantic delta;
- produce a new exact candidate SHA;
- run a new EHA campaign on that composition.

Old green CI is provenance only.

## Mermaid history

Use `eha_state_mermaid` when a human-readable campaign/repair graph is useful.
It should make the lineage obvious, for example:

```text
SHA A | SIB0 PASS | SIB1 FAIL | SIB2 PENDING
                |
                | repair SIB1
                v
SHA B | SIB0 PASS | SIB1 PASS | SIB2 PASS
```

Do not manually edit the diagram to make history look cleaner. Regenerate it
from the ledger. Never parse edited Mermaid back into EHA evidence.

## Reporting contract

Every EHA report must include:

- review ID and EHA campaign ID;
- literal target SHA and branch;
- dirty state/environment;
- SIB0 verdict and profile/evidence;
- SIB1 verdict and profile/evidence;
- SIB2 verdict and profile/evidence;
- blocker finding IDs for every FAIL;
- whether each SIB degree is actually claimable on that SHA;
- repair decision/branch/candidate/regression/focused tests when a repair loop
  was entered;
- predecessor/successor campaign IDs when applicable;
- checks actually run and explicit limitations.

Load `codesleuth-reports` at completion and persist the report. The report is a
human-readable summary; `eha.ndjson` remains the structured durable ledger.

## Completion rule

An EHA task is complete when it has truthfully recorded what the exact target
proved, including failures. It is not complete merely because someone found a
way to make the latest branch green.

Canonical operational rule:

> **Tester discovers. Repairer repairs. The next EHA campaign accepts or rejects the new exact SHA.**
