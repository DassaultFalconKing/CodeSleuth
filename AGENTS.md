# CodeSleuth agent instructions

CodeSleuth is a discipline layer and control panel around a host coding agent. The host owns the model, primary controller, session, permissions, tool routing, and execution. Do not introduce a second CodeSleuth runtime, supervisor, scheduler, model runtime, general-purpose tool router, or independent execution authority.

## Read the right authority

Before changing the repository, resolve the current authority for the task instead of treating branch names, old PRs, generated reports, or green historical CI as truth.

- Product/manual truth: [`README.md`](README.md).
- Product ownership and extension boundaries: [`docs/CODESLEUTH-PRODUCT-CONTRACT.md`](docs/CODESLEUTH-PRODUCT-CONTRACT.md).
- Stable Baseline model: [`docs/STABLE-INTEGRATION-BASELINE.md`](docs/STABLE-INTEGRATION-BASELINE.md).
- Frozen SIB0 capability-class inventory: [`docs/SIB0-CAPABILITY-INVENTORY.md`](docs/SIB0-CAPABILITY-INVENTORY.md).
- Exact-head acceptance identity: [`docs/EXACT-HEAD-ACCEPTANCE.md`](docs/EXACT-HEAD-ACCEPTANCE.md).
- EHA operating workflow: [`docs/EHA-OPERATING-PLAYBOOK.md`](docs/EHA-OPERATING-PLAYBOOK.md).
- EHA repair discipline: [`docs/EHA-REPAIR-LOOP.md`](docs/EHA-REPAIR-LOOP.md).
- Release-stream candidate selection: [`docs/SIB-CANDIDATE-SELECTION.md`](docs/SIB-CANDIDATE-SELECTION.md).
- Semantic continuity for stale/divergent work: [`docs/SEMANTIC-REFIT.md`](docs/SEMANTIC-REFIT.md).
- Protected capability and forbidden-regression semantics: [`docs/PROTECTED-CAPABILITY-CONTRACTS.md`](docs/PROTECTED-CAPABILITY-CONTRACTS.md).
- Machine-readable Protected Capability Registry: [`docs/protected-capabilities.json`](docs/protected-capabilities.json).
- Playbook/Step/Skill/Command/Tool composition: [`docs/PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md`](docs/PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md).
- Durable review/EHA evidence authority: [`docs/DURABLE-EVIDENCE-STORE.md`](docs/DURABLE-EVIDENCE-STORE.md).
- Install/bind/unbind/uninstall truth: [`docs/PROJECT-LIFECYCLE.md`](docs/PROJECT-LIFECYCLE.md).
- Coding-agent operator workflow: [`docs/LLM-OPERATOR.md`](docs/LLM-OPERATOR.md).

If the user asks you to install, configure unattended, use, update, bind, unbind, remove, or prepare a release-clean repository with CodeSleuth, read `docs/LLM-OPERATOR.md` before changing the target repository.

For multi-step work, use a stored Playbook when one exists. Read only its manifest initially, materialize one Step at a time, and load only the atomic Skills declared for that Step. Prefer fresh host-native child context for Step isolation; retain bounded Step outputs rather than the whole Step prompt. Do not turn a long workflow back into one giant Skill.

For one atomic competence, load the relevant Skill directly. A Skill must have independently decidable input/objective/output/stop/must-not boundaries. User-facing Skills may also be slash-invoked where the host supports it.

## Repository-state vocabulary

Treat these as different things:

- **`SIB`** — the deliberately promoted exact SIB2 baseline. It is an identity/reference point, not a work branch.
- **SIB0** — architecture/capability-class inventory complete and frozen for one exact SHA.
- **SIB1** — every frozen capability class has a real basic implementation on that same exact SHA.
- **SIB2** — the SIB1 implementations compose successfully and the exact SHA passes the canonical full-system acceptance profile.
- **`dev/release-X.Y.Z`** — mutable release/SIB candidate stream. EHA selects its literal exact HEAD; the selected SHA then becomes immutable for that campaign.
- **`main`** — numbered-release line. Do not assume `main` is accepted merely because an ancestor or equal tree was accepted. Exact SHA identity still governs.
- **feature/fix/docs/refit branches** — work/provenance branches, never acceptance authority by themselves.

The core rule is:

> **SIB degree says what was proven. EHA says which exact repository state the proof belongs to.**

Acceptance never propagates implicitly to a descendant, merge commit, tree-equivalent commit, rebased commit, or divergent branch.

## Default work order

Use this order for repository work unless a narrower accepted contract says otherwise.

### 1. Freeze identities before interpreting the change

Record the exact current target SHA and, when historical/divergent work is involved, the exact source SHA as well.

Before coding, know which state is:

- the last accepted SIB2 (`SIB`);
- the current work target;
- the active `dev/release-X.Y.Z` head when release construction is involved;
- any historical PR/branch/commit being used as evidence.

Do not substitute a PR merge ref, stale local branch, generated report, or remembered summary for exact Git identity.

### 2. Classify the change before choosing the workflow

Every material change starts in one of these classes.

#### A. Ordinary feature population / hardening

Use this when the change adds depth, variants, profiles, Skills, Playbooks, bounded tools, host adapters, UX, tests, reliability, or other behavior **inside the existing frozen SIB0 capability classes**.

Do **not** reopen SIB0 merely because a feature is substantial.

Start from an accepted base chosen by the maintainer, preserve the current architecture, assess protected-capability impact, implement the minimum target-native delta, and run the required focused + dependency-closure gates.

Broad feature population is allowed only from an accepted SIB2 lineage, not from an unresolved SIB1 recovery state.

#### B. Stale/divergent historical work

Use Semantic Refit before implementation or integration.

Do not ask only “which hunks should be cherry-picked?” Ask which evidenced product claims still belong in the current system.

For each material historical claim record separately:

**Semantic status**

- `REQUIRED`
- `SUPERSEDED`
- `RETIRED`
- `UNRESOLVED`
- `CONFLICTED`

**Delivery disposition**

- `REUSE`
- `PORT / ADAPT`
- `REIMPLEMENT`
- `NEW CHANGE`
- `NO CHANGE`
- `DEFER`
- `BLOCK`

`SUPERSEDED` requires positive current coverage evidence. `RETIRED` requires explicit current authority. Implementation difficulty is not evidence that a requirement disappeared.

Preserve provenance and negative knowledge even when none of the old implementation survives.

Historical green CI is provenance only. The refitted composition must earn fresh acceptance on its own exact SHA.

#### C. Architecture change

If the change adds, removes, or fundamentally redefines a capability class, execution authority, persistence authority, orchestration/runtime ownership, or another frozen architectural boundary, record **architecture reopened**.

Do not hide this inside an ordinary feature or refit.

The recovery order becomes:

```text
architectural convergence
    -> SIB0
    -> implementation recovery
    -> SIB1
    -> integration recovery
    -> full exact-head acceptance
    -> SIB2
```

A genuinely new architectural generation must establish a new SIB0 before claiming SIB1/SIB2 again.

### 3. Resolve current contracts before coding

For every affected protected or user-visible behavior, triangulate:

1. current code/configuration;
2. normative/public documentation;
3. executable tests/acceptance.

If they disagree, do not synthesize a convenient contract. Preserve the actual evidence state, including `CODE_AHEAD`, `DOC_AHEAD`, `TEST_AHEAD`, `CONTRADICTED`, or `UNPROVEN` where applicable.

Retrieve affected protected contracts and their `forbidden_regressions[]`. Negative knowledge is part of the engineering input, not decoration for the final review.

For a material negative claim, prefer the stronger form:

```text
forbidden state
+ constructive invariant
+ recognizable violation witness/counterexample
+ bounded scope/oracle
```

Try to produce the violation inside the relevant scope; a finite happy path does not prove a universal negative.

### 4. Assess protected-capability impact

If the task adds/changes a feature after SIB2, reviews a PR for regression, prepares an accepted integration/RC/release candidate, or asks which accepted contracts a diff may affect, use the `protected-capability-assessment` Playbook for broad work.

For a narrow registry lookup use the atomic `protected-capability-registry` Skill.

The ordinary candidate gate is:

```text
new/changed behavior
+ invariant core
+ affected protected-capability reverse-dependency closure
+ focused regression evidence
```

Do not silently remove or weaken a protected contract or one of its forbidden regressions.

### 5. Implement the smallest current-native delta

The current target architecture is semantic authority unless an explicit current contract changes it.

Prefer code that is native to the current architecture over preservation of historical implementation shape.

A successful Semantic Refit may keep most source code, little source code, or none of it. Implementation resemblance is not the success criterion; preserved or explicitly changed semantics are.

Do not create a second controller, scheduler, workflow runtime, model runtime, general tool router, or competing persistence/evidence authority as a shortcut.

Commands are entry points. Playbooks own multi-step order. Skills own atomic reasoning. Tools own bounded execution primitives.

### 6. Run focused development gates before integration

For ordinary Python/documentation changes:

```bash
python -m pytest
ruff check .
```

For durable-state/context-graph changes also run:

```bash
bun install --frozen-lockfile
bun tests/review_state_smoke.ts
bun tests/context_graph_smoke.ts
```

For EHA-state changes also run:

```bash
bun tests/eha_state_smoke.ts
```

For MCP changes, `python -m pytest` includes MCP tests after `python -m pip install -r requirements-dev.txt`. Do not skip MCP tests in release acceptance.

Run additional focused/visual/lifecycle gates required by the affected contracts. Report only checks actually executed successfully.

Focused green tests prove a candidate delta, not an accepted composition.

### 7. Compose accepted-candidate work through the release stream

When preparing a future SIB, accepted integration head, RC, or numbered release, integrate the intended deltas through the active:

```text
dev/release-X.Y.Z
```

Do not accept a repair branch, PR head, convenience EHA branch, or tree-equivalent commit in place of the resulting composition.

After composition, freeze the literal exact `dev/release-X.Y.Z` HEAD. That SHA is the acceptance target.

If a merge creates a new SHA, that merge SHA is the candidate even when its tree equals an already-tested commit.

### 8. EHA is testing, not implementation

Run `/eha-test` or the `eha-sib-acceptance` Playbook only on the frozen exact candidate.

The EHA tester must not repair the target while testing it.

For a SIB campaign the order is:

```text
freeze literal release HEAD
-> start/load durable review state
-> start EHA campaign
-> SIB0 profile
-> record SIB0 PASS|FAIL
-> SIB1 profile
-> record SIB1 PASS|FAIL
-> SIB2 profile
-> record SIB2 PASS|FAIL
-> report exact evidence and limitations
```

All three verdicts belong to the **same immutable SHA**.

Claimability is cumulative:

```text
SIB0 claimable = SIB0 PASS
SIB1 claimable = SIB0 PASS + SIB1 PASS
SIB2 claimable = SIB0 PASS + SIB1 PASS + SIB2 PASS
```

For CodeSleuth SIB2, the full canonical acceptance profile includes the supported Python/OS matrix, durable-state/context-graph gate, and required TUI visual-regression gate defined by current workflow/contracts.

Do not inherit PASS from source branches, ancestors, repair commits, or previous campaigns.

### 9. A failed EHA target stays failed

On the first material EHA failure:

1. record exact failure evidence;
2. record the appropriate SIB FAIL;
3. freeze the failed SHA and campaign;
4. stop acceptance work on that target.

Never turn `FAIL -> PASS` by editing the same target or rewriting the ledger.

Use `/eha-repair` or the `eha-repair` Playbook in a separate repair session.

Repair order:

```text
failed exact SHA
-> new repair branch
-> minimum repair + regression
-> focused verification
-> integrate repair through dev/release-X.Y.Z
-> new literal release HEAD SHA
-> new EHA campaign from SIB0 on that new SHA
```

The failed campaign remains failed forever. Repair creates evidence for a new state; it does not rehabilitate history.

If repair discovers a changed fundamental capability/authority model, mark `architecture_reopened` and re-establish SIB0 explicitly.

### 10. Promote only the SHA that was actually proven

The tested SHA and the promoted SHA must be identical.

For deliberate SIB2 promotion, move the `SIB` ref only to the exact SHA that completed the required SIB0/SIB1/SIB2 campaign successfully.

Prefer a non-force fast-forward when ancestry allows it. Never rewrite `SIB` history merely to make the graph prettier.

Promotion of a ref does not create acceptance; it records a maintainer decision about already-existing exact-head evidence.

### 11. `main` and release promotion still obey exact identity

A numbered release ultimately lands on `main`, but `main` does not bypass EHA semantics.

If an accepted release/SIB2 SHA can be fast-forwarded directly to `main`, that preserves the exact accepted identity and is preferable when it matches the intended history.

If promotion to `main` creates a new merge/squash/rebase commit, the resulting `main` SHA is a **new candidate** and requires the release acceptance profile again before tagging/publishing.

Never claim that tree equality or an accepted parent transfers release acceptance to a new commit.

Tag/publish only the exact accepted `main` release SHA.

### 12. Preserve the accepted baseline while continuing work

After SIB2, the `SIB` ref remains the stable accepted construction baseline while feature population and hardening continue on descendants/branches.

A new ordinary commit does not invalidate the historical SIB2 proof; it simply is not itself SIB2-accepted until separately proven/promoted.

Do not move `SIB` for convenience, documentation cleanup, branch hygiene, or because a descendant “obviously still works.”

### 13. Branch triage happens after semantic extraction

Do not merge or preserve a branch merely because it has commits not reachable from `SIB`; alternative history may already be semantically absorbed.

For old branches:

1. compare exact ancestry/diff against the accepted baseline;
2. extract any surviving claims, negative knowledge, reports, or unique deltas;
3. move surviving work into explicit backlog/refit issues when appropriate;
4. classify the branch as active delta, deferred work, provenance, test carrier, or delete/archive candidate;
5. only then perform repository cleanup.

Branch deletion is hygiene, not Semantic Refit. Never delete the only practical pointer to intentionally retained evidence without recording its exact identity/provenance first.

## Source-development invariants

- Make the smallest change that satisfies the current contract.
- Preserve OpenCode `build` as the primary controller for the full OpenCode integration.
- Preserve pre-existing OpenCode/user configuration and conflict-safe lifecycle behavior.
- Do not treat context graphs, Mermaid, scout summaries, retrieval scores, generated reports, old PR summaries, or old CI as stronger evidence than exact current source and accepted contracts.
- Do not widen permissions, commit, push, reset, clean, force-update protected/baseline refs, or discard user work unless the user explicitly asks for that operation and the operation is consistent with current acceptance identity.
- Never repair an acceptance candidate in place.
- Never weaken, skip, xfail, or rewrite an acceptance test merely to promote a candidate.
- Never silently change a protected contract or erase negative knowledge to make integration easier.
- Keep acceptance evidence and human-readable reports distinct: the durable ledger is authority; reports/Mermaid are derived views.
- Preserve exact SHA, source/provenance, tests actually run, known limitations, and human-only uncertainty in handoffs.

## Compact decision table

| Situation | Correct path |
| --- | --- |
| New profile/Skill/Playbook/tool/UI hardening inside frozen capability classes | Post-SIB2 feature population + protected-capability impact gates |
| Old PR/branch must be recovered onto changed target | Semantic Refit -> minimum target-native delta -> current gates |
| New runtime/authority/persistence/capability class | Architecture reopened -> new SIB0 -> SIB1 -> SIB2 |
| Future SIB/RC/release candidate assembled | Compose on `dev/release-X.Y.Z` -> freeze literal HEAD -> exact-head acceptance |
| EHA finds failure | Record FAIL -> stop -> separate repair -> integrate -> new SHA -> new EHA |
| Candidate passes SIB0/SIB1/SIB2 | Deliberately promote exact tested SHA to `SIB` |
| Accepted SHA can fast-forward to `main` | Prefer exact-identity fast-forward when release history permits |
| Promotion creates a different `main` SHA | Fresh exact-head release acceptance before tag/publish |
| Old branches after promotion | Extract semantics/negative knowledge -> triage -> archive/delete later |

Nested `AGENTS.md` files, if introduced later, may add narrower instructions for their subtree. Direct user instructions still take precedence, but do not silently misreport an unaccepted SHA as accepted merely because the user requested a repository mutation.