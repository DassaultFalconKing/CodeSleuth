# RC7 Implementation Triage TODO

**Status:** ACCEPTED PLANNING ADDENDUM / TRIAGE TODO / NOT FINAL IMPLEMENTATION AUTHORITY  
**Branch:** `docs/rc7-ledger-authority-repair-plan`  
**Purpose:** identify RC7 slices that may safely enter test-first development before the complete RC7 design is frozen, while keeping unresolved authority semantics blocked.

## 1. Owner decision: stable CodeSleuth invocation namespace

RC7 must introduce one durable product namespace for CodeSleuth-owned capabilities exposed or discoverable through OpenCode.

Canonical product namespace:

```text
codesleuth
```

The intent is both human and model ergonomics: a user should be able to discover CodeSleuth operations under one slash namespace, and an LLM should be able to identify CodeSleuth-owned Skills/Playbooks without guessing ownership from generic global names.

### 1.1 Canonical public command form

User-facing slash commands should use:

```text
/codesleuth/<operation>
```

Examples:

```text
/codesleuth/review
/codesleuth/continue
/codesleuth/contracts
/codesleuth/eha/test
/codesleuth/eha/status
/codesleuth/eha/repair
/codesleuth/playbook
/codesleuth/help
```

The command is a convenience/entrypoint layer. It must not become semantic authority; reusable semantics remain in Skills, workflow ordering in Playbooks, deterministic behavior in Tools, and normative rules in contracts/tests.

### 1.2 Canonical model-facing identities

CodeSleuth-maintained atomic Skills intended for host/model discovery should use:

```text
codesleuth-<skill-id>
```

Examples:

```text
codesleuth-contract-archaeology
codesleuth-dependency-impact-closure
codesleuth-development-authority-discovery
```

CodeSleuth-maintained Playbook identities should use:

```text
codesleuth-<playbook-id>
```

Examples:

```text
codesleuth-repository-deep-review
codesleuth-repository-development-continuation
codesleuth-eha-sib-acceptance
```

The human-facing command name and the internal Skill/Playbook identity do not need to be identical. Their mapping must be explicit and testable.

### 1.3 Naming authority

Do not create a second naming source of truth. The accepted RC7 design should extend the existing machine-readable naming authority:

```text
pack/.opencode/codesleuth-naming.json
```

with concepts equivalent to:

```text
canonical.invocationNamespace = "codesleuth"
canonical.skillPrefix = "codesleuth-"
canonical.playbookPrefix = "codesleuth-"
canonical.commandNamespace = "codesleuth/"
```

Exact schema placement is an implementation-design decision, but one machine-readable authority is mandatory.

### 1.4 Migration constraints

- Do not retrofit or destabilize the frozen RC6 dogfood candidate merely to perform this namespace cutover.
- Existing unprefixed commands may remain as explicitly bounded compatibility aliases during migration.
- Compatibility aliases must not remain the advertised canonical surface indefinitely.
- New public CodeSleuth commands/Skills/Playbooks introduced after the RC7 cutover must not be unprefixed.
- Contract tests should reject accidental new unprefixed public capability identities.
- Directly model-called Tool function names are not automatically part of this rename. Triage must decide separately whether any Tool namespace collision exists; do not create gratuitous API churn.

## 2. RC7 implementation-triage objective

RC7 is not yet one frozen implementation authority, but that does not imply every implementation slice must wait for the final freeze.

The next architecture triage must classify each proposed RC7 slice by whether its semantics are already fixed by existing product/SIB/evidence contracts and therefore safe to develop independently.

Required classes:

```text
READY_NOW
MICRO_FREEZE_REQUIRED
FINAL_RC7_FREEZE_BLOCKED
POST_RC7_OR_RESEARCH
```

### READY_NOW

A slice may be classified `READY_NOW` only when:

- its authority owner is already unambiguous;
- it does not depend on unresolved RC7 schema/authority choices;
- it preserves existing SIB0/product/host boundaries;
- it is additive or compatibility-preserving;
- deterministic tests can define the behavior before production implementation;
- it can land without making a claim that the whole RC7 design is accepted.

### MICRO_FREEZE_REQUIRED

Use when a narrow subdesign can be frozen independently without resolving the whole RC7 architecture. The triage must identify the exact micro-contract that needs owner approval before coding.

### FINAL_RC7_FREEZE_BLOCKED

Use when implementation would prematurely decide an unresolved authority, schema, recovery-generation, lifecycle, acceptance, or completeness question belonging to the final consolidated design.

### POST_RC7_OR_RESEARCH

Use for non-normative experiments, deferred formats/adapters, broad generic frameworks, Doris/Obsidian delivery, or other work the synthesis deliberately excludes from mandatory RC7.

## 3. Tests-first architecture triage

Treat the existing test suite as executable architecture evidence, not merely CI plumbing.

The triage agent must inspect the current tests and map them to RC7 claims, including relevant existing families such as:

```text
tests/development_continuation_smoke.ts
tests/eha_state_smoke.ts
tests/eha_campaign_bootstrap_cases.py
tests/eha_github_bridge_cases.py
tests/context_graph_smoke.ts
tests/context_graph_provider_smoke.ts
tests/context_graph_topology_smoke.ts
tests/change_surface_state_smoke.ts
tests/contract_bootstrap_state_smoke.ts
```

It must also inventory Python contract/install/catalog/TUI tests that constrain command, Skill, Playbook and pack exposure.

For every RC7 workstream, produce:

```text
existing behavior / authority
existing protecting tests
missing contract test
first deterministic RED witness
implementation boundary
cross-workstream dependencies
acceptance gate
```

Do not label a workstream `READY_NOW` merely because code can be written. It must have a bounded testable contract whose semantics are already decided.

## 4. Required triage outputs

The architecture triage must produce a development plan containing at least:

1. RC7 requirement-to-test matrix;
2. unresolved design-decision ledger;
3. dependency graph among RC7 workstreams;
4. `READY_NOW` work packages that can be handed to implementation agents immediately;
5. `MICRO_FREEZE_REQUIRED` packages with the exact small design decisions that must be approved first;
6. `FINAL_RC7_FREEZE_BLOCKED` packages and their blockers;
7. `POST_RC7_OR_RESEARCH` exclusions;
8. proposed branch boundaries so independent packages do not share mutable state unnecessarily;
9. tests-first order for each implementable package;
10. integration order and exact-head acceptance checkpoints;
11. specific handling of the `codesleuth` invocation namespace cutover;
12. risks of implementing a supposedly independent package before the final consolidated design.

The plan should prefer several small independently reviewable workstreams over one giant RC7 feature branch.

## 5. Early-development rule

No agent may use this TODO as permission to implement unresolved RC7 authority semantics.

However, a workstream explicitly classified `READY_NOW` by evidence and tests may be developed on its own feature branch before the final RC7 freeze if it:

- remains within already accepted product boundaries;
- does not move release/SIB/EHA refs;
- does not claim RC7 acceptance;
- preserves compatibility with the current release stream;
- has its own focused RED -> GREEN evidence;
- returns to full hosted acceptance before integration into an RC7 candidate stream.

The purpose of triage is to avoid two equally bad extremes: prematurely coding disputed architecture, or freezing all useful work because one corner of RC7 still needs philosophical litigation.

## 6. Branch/base discipline

The RC7 planning branch is a design-input branch, not a runtime implementation base.

At the time this TODO was updated, comparison against the hosted-green RC6 dogfood candidate showed:

```text
runtime candidate:
1de37c75251a1e0d9904cffdb82695e92e3fab23

RC7 planning branch:
docs/rc7-ledger-authority-repair-plan

merge base:
645aedb8364977ebb3b227b3af35e13ed440b0f5

planning branch relative to runtime candidate:
16 commits ahead
39 commits behind
status: diverged
```

Therefore:

- read RC7 planning/design documents from this branch as planning inputs;
- do not create RC7 implementation branches from this stale planning branch;
- before handing out any `READY_NOW` package, resolve the current exact hosted-green/release-stream runtime base and branch from that exact commit;
- carry the required RC7 design/test delta into the implementation branch explicitly;
- if the runtime base changes during RC6 completion, re-evaluate affected tests and assumptions before coding;
- never infer implementation readiness from a green status on the planning branch alone.
