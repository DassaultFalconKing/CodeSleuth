---
name: feature-porting-discipline
description: Evidence-first recipe for safely porting capabilities, patterns, tools, skills, plugins, and hardening mechanisms between repositories without copying source-specific architecture or creating duplicate runtime authority
---

# Feature Porting Discipline

Use this skill when a contributor is asked to **port**, **adapt**, **extract**, **reuse**,
**re-home**, or **bring over** a feature, subsystem, tool, skill, plugin, reliability
mechanism, workflow, or architectural pattern from another repository or an older
implementation into CodeSleuth.

This is a recipe for turning a source implementation into a **target-native
capability**. It is deliberately stricter than “find similar files and copy them.”
That approach is quick, emotionally satisfying, and responsible for a remarkable
amount of software archaeology.

The central rule is:

> **Port the portable contract and proven invariants. Do not port source-specific
> ownership, ontology, runtime assumptions, filenames, process topology, or
> implementation accidents unless CodeSleuth independently needs them.**

A successful port is not the source feature reproduced verbatim. A successful
port preserves the desired behavior while obeying CodeSleuth's current product,
runtime, security, state, and extension ownership contracts.

---

## 1. When to invoke this skill

Invoke this skill for requests such as:

- “port feature X from repository A to CodeSleuth”;
- “reuse the Mermaid context discipline from Aleph”;
- “bring over the watchdog/recovery design”;
- “extract this tool from the old implementation”;
- “adapt this plugin for CodeSleuth”;
- “make CodeSleuth support the same workflow as project Y”;
- “port the hardening from branch Z”;
- “move an accepted prototype into the production repository”;
- “reuse a subsystem but fit it to OpenCode-native execution”;
- “upstream/downstream a capability between CodeSleuth and a consumer repository.”

Do **not** use this skill when:

- the task is merely a same-repository bug fix with no cross-implementation
  semantic mapping;
- the user asks only for documentation of an existing feature;
- the feature already exists in CodeSleuth and the request is only to expose or
  configure it;
- the task is a whole-repository review with no porting decision. Use
  `repository-deep-review` for that;
- the request is a mechanical vendor/subtree update whose semantics are already
  governed by an accepted dependency/update contract.

If uncertain, use this skill whenever the task contains the hidden question:

> “Which parts of the source thing are actually the thing we want?”

---

# 2. Prime directives

These are non-negotiable unless an accepted target-repository authority explicitly
supersedes them.

## 2.1 Port behavior, not filenames

A source path is evidence about how the source repository implements a capability.
It is not evidence that the target repository needs the same path, language,
process, package, database, state shape, or command name.

Never begin a port by creating target files that mirror source filenames.

First identify:

1. the user-visible or operator-visible behavior;
2. the architectural invariant behind it;
3. the runtime owner in the source;
4. the runtime owner that must own it in CodeSleuth;
5. the minimum mechanism required in the target.

## 2.2 Current accepted target authority wins

The source repository explains the feature being studied.
The **target repository decides how the port may exist**.

For CodeSleuth, always read the current product/architecture authority before
proposing a port. In particular, preserve the accepted ownership split in which
OpenCode remains execution authority and CodeSleuth extends, configures, exposes,
or hardens OpenCode-native infrastructure rather than silently growing a second
agent runtime.

If source semantics conflict with target authority, do not “split the difference.”
Classify the conflict explicitly:

- `SOURCE_SPECIFIC_OMIT`;
- `TARGET_NATIVE_REPLACEMENT`;
- `REQUIRES_NEW_ADR_OR_PRODUCT_DECISION`.

## 2.3 The source summary is not the source

Never port from:

- a chat summary;
- an old handoff alone;
- a PR body alone;
- a branch name;
- a README claim without implementation evidence;
- generated docs alone;
- a previous reviewer’s conclusion alone.

Use summaries to locate evidence, then inspect the actual source implementation,
contracts, tests, and accepted current docs at an exact revision.

## 2.4 A port is a semantic translation

Treat the work as:

```text
source capability
  -> source contract + invariants
  -> remove source-only assumptions
  -> map ownership into target architecture
  -> target-native contract
  -> minimal implementation
  -> adversarial acceptance proof
```

Not:

```text
source directory
  -> copy
  -> rename
  -> test happy path
  -> optimism
```

## 2.5 No duplicate authority

Before adding any runtime component, ask:

> “Who already owns this behavior in CodeSleuth/OpenCode?”

If an existing layer already owns it, prefer:

- configuration;
- a Skill;
- a command;
- a thin tool;
- a plugin hook;
- durable metadata derived from existing truth;
- documentation/UX exposure.

Do not create a second:

- session runtime;
- controller/agent loop;
- tool router;
- model dispatcher;
- filesystem watcher;
- stall detector;
- repository truth store;
- evidence ledger;
- graph/source ontology;
- updater authority;
- acceptance authority.

## 2.6 Derived state must remain derived

If the port introduces caches, projections, diagrams, indexes, watchdog health,
continuation metadata, inventories, or summaries, they must not silently become
canonical truth when the target already has an authority for the underlying
facts.

Document:

```text
canonical input
  -> deterministic/validated derivation
  -> derived state
  -> consumer
  -> invalidation/rebuild rule
```

## 2.7 Model output never upgrades itself into verified state

If an LLM, scout, imported report, or generated artifact proposes a relationship,
finding, state transition, or capability claim, it remains an inference until the
accepted target contract validates it.

A model assertion does not become verified merely because a porting tool stores
it in JSON.

---

# 3. Required porting outputs

Before implementation begins, produce a **Porting Dossier** containing all of the
following.

## 3.1 Exact identities

Record:

- source repository;
- source ref requested by the user;
- exact source full SHA actually studied;
- target repository;
- target base branch;
- exact target base full SHA;
- target dirty state if local;
- planned feature branch;
- whether source and target moved during analysis.

If exact identities are unavailable, stop before implementation and classify the
result `IDENTITY_UNPROVEN`.

## 3.2 Source capability statement

One paragraph answering:

> What does the source feature actually guarantee to its consumers?

This must be based on implementation/contracts/tests, not branding.

## 3.3 Portable invariant list

List behaviors that remain meaningful independent of source product internals.

Example shape:

```text
P1. Derived graph presentation never becomes evidence authority.
P2. Stable edge identity does not depend on renderer layout.
P3. Recovery state advances only after successful verified completion.
P4. A watchdog heartbeat proves liveness, not correctness.
```

## 3.4 Source-specific assumption list

List everything that must **not** be copied blindly, for example:

- domain ontology;
- database schema;
- crate/package names;
- service topology;
- systemd cadence;
- model role names;
- accepted session packet numbering;
- source-specific score thresholds;
- source-only UI;
- historical compatibility wrappers;
- generated artifacts;
- deployment assumptions.

## 3.5 Target ownership map

For each portable behavior, name the target owner.

Example:

| Behavior | Source owner | Target owner | Action |
| --- | --- | --- | --- |
| execution stall detection | Aleph wrapper | existing `opencode-keepalive` | PRESERVE/REUSE |
| durable review checkpoint | review pack | `review_state` | EXTEND |
| renderer-neutral relationship projection | FtM graph contract | CodeSleuth repository context tool | ADAPT |
| SVG rendering | future Mermaid renderer | none required for first slice | DEFER |

Every row must choose one action from:

- `REUSE`;
- `EXTEND`;
- `ADAPT`;
- `REPLACE_WITH_TARGET_NATIVE`;
- `OMIT_SOURCE_SPECIFIC`;
- `DEFER`;
- `REQUIRES_ARCHITECTURE_DECISION`.

## 3.6 Minimum target slice

Name the smallest set of files/components that can prove the desired semantics.

Prefer one vertical slice over a broad port.

## 3.7 Explicit non-goals

A port without non-goals tends to absorb neighboring source architecture because
those files are conveniently nearby.

Write the exclusions before implementation.

## 3.8 Acceptance matrix

Define objective tests before code. Include positive, negative, stale-state,
large-input, cross-boundary, and ownership/non-duplication checks.

---

# 4. Tool-calling protocol: global rules

This section is intentionally operational. Follow it mechanically when possible.

## 4.1 Read before write

Do not create a branch or file merely because the requested feature name is clear.
First establish enough source and target authority to choose the correct port
boundary.

Exception: creating an **empty dedicated feature branch from the verified target
base** is allowed early when the user explicitly asked for branch preparation.
Do not populate it until the Porting Dossier reaches at least the ownership-map
stage.

## 4.2 Every remote read must name a ref when revision matters

When using GitHub/API/connector tools, prefer explicit refs or SHAs.

Bad:

```text
fetch README.md
```

Better:

```text
fetch README.md at source_sha
```

Best for canonical evidence:

```text
fetch exact path at exact full SHA
```

If the tool defaults to the repository default branch, record that fact and then
resolve the branch head before relying on it.

## 4.3 Search discovers; fetch proves

Repository/code search results are leads.

Protocol:

```text
search(feature keyword)
  -> identify candidate path/symbol
  -> fetch exact file/range
  -> inspect surrounding contract/caller/test
  -> only then cite or classify
```

Never treat a search snippet as sufficient implementation evidence when a full
file/range can be fetched.

## 4.4 Bound tool output

For large repositories:

- inventory first;
- search before full-file reads;
- read targeted ranges;
- fetch only relevant PR file patches rather than giant PR diffs when possible;
- avoid lockfiles/vendor/generated outputs unless they are semantically relevant;
- delegate independent source components to bounded exploration tasks;
- retain exact candidate paths/symbols, not giant transcripts.

A one-million-token context is not an instruction to fill one million tokens.

## 4.5 Separate discovery evidence from acceptance evidence

During discovery it is acceptable to use:

- search hits;
- architecture summaries;
- bounded scouts;
- generated diagrams;
- old handoffs;
- prior PR descriptions.

Before making a semantic port decision, promote relevant claims by reopening:

- current source implementation;
- current target authority;
- exact tests/contracts;
- actual target consumers.

## 4.6 Never write through an ambiguous target

Before a repository mutation, establish:

```text
repository
branch
base SHA
intended path
whether path already exists
```

For update/delete operations, fetch the current target file first and use its
current blob/content SHA where the write API requires it.

Do not perform parallel writes to the same path.

## 4.7 Re-read after writes

After creating/updating files:

- fetch the written file from the feature branch;
- verify the branch head moved as expected;
- compare branch against base;
- inspect the actual resulting diff;
- run/inspect applicable tests;
- do not assume a successful API mutation means semantically correct contents.

---

# 5. Tool-calling protocol: local Git

When the target or source repository is locally available, Git is the primary
identity/evidence tool.

## 5.1 Establish repository identity

Run:

```bash
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --porcelain=v1
```

If reviewing or porting against a remote base:

```bash
git fetch origin <base-branch>
git rev-parse origin/<base-branch>
```

Record full SHAs.

## 5.2 Establish divergence

For a candidate feature/source branch:

```bash
git merge-base <base> <head>
git rev-list --left-right --count <base>...<head>
git diff --stat <base>...<head>
git diff --name-status <base>...<head>
```

Use this before claiming a branch is clean, current, rebased, or “only docs.”

## 5.3 Inventory tracked files deterministically

Prefer CodeSleuth `repo_inventory` when available.

Fallback Git commands:

```bash
git ls-files -s -z
git ls-tree -r --name-only HEAD
```

Do not use filesystem recursion as a substitute for tracked repository inventory
when Git is available. Build outputs and ignored files are noise unless the task
explicitly concerns them.

## 5.4 Search source semantically

Preferred order:

```bash
git grep -n '<symbol-or-contract-term>'
git grep -n '<feature-name>'
git log --all --oneline --decorate -- <suspected-path>
git log -S'<important-literal-or-symbol>' --all -- <scope>
```

Use `git show <sha>:<path>` to inspect historical/canonical versions without
switching the worktree.

## 5.5 Bind evidence to content identity

For important target files:

```bash
git hash-object -- <path>
git cat-file -e <sha>^{commit}
```

When CodeSleuth review tools are available, prefer their blob-bound finding and
checkpoint mechanisms for durable evidence.

## 5.6 Never silently mix dirty and committed evidence

A dirty worktree is not automatically a blocker, but every finding/porting claim
must distinguish:

- committed `HEAD` content;
- dirty worktree content;
- staged content if relevant.

Do not claim a port is based on commit X when the behavior inspected only exists
in uncommitted changes.

---

# 6. Tool-calling protocol: CodeSleuth repository tools

Use CodeSleuth-native tools where available.

## 6.1 `repo_inventory`

Call it before broad exploration of the target and, when practical, before broad
exploration of a local source repository.

Use it to learn structure, not to claim semantic coverage.

Protocol:

```text
repo_inventory
  -> capture exact HEAD/dirty state
  -> inspect bounded manifest preview
  -> choose path prefixes/components
  -> search/read those components
```

Do not dump the entire manifest into model context.

## 6.2 `review_state_start`

For a substantial port analysis/review, start durable state with an objective such
as:

```text
Map source feature X and design a target-native CodeSleuth port without duplicate
runtime authority.
```

Use a distinct review ID when concurrently analyzing multiple ports.

## 6.3 `review_state_checkpoint`

Checkpoint at semantic boundaries, especially after:

- source authority mapped;
- source implementation mapped;
- portable invariants extracted;
- target ownership collisions checked;
- acceptance matrix defined;
- implementation diff reviewed;
- final acceptance gates executed.

Store `next` actions that can resume the work without replaying the conversation.

## 6.4 `review_state_record_finding`

Use exact current target/source evidence for material blockers discovered during
port review.

Do not turn general architectural preferences into findings unless they violate a
named contract.

## 6.5 `review_state_load` / explicit resume

After compaction or session interruption:

```text
load durable state
  -> verify current HEAD/dirty state
  -> identify stale reviewed paths
  -> re-open only affected evidence
  -> continue from `next`
```

Do not redo complete source discovery merely because the conversation was
compacted.

---

# 7. Tool-calling protocol: exploration/subagents

Use native bounded exploration for independent questions.

Good scout assignments:

- “Find all runtime callers of source type X; return paths/symbols only.”
- “Trace who owns persistence for source feature Y.”
- “Find target mechanisms that already implement stall detection.”
- “Find tests proving target session resume semantics.”
- “Locate all consumers of target review-state schema.”

Bad scout assignments:

- “Understand the whole repository.”
- “Port the feature.”
- “Tell me if it is correct.”
- “Read everything and summarize.”

Scout output is a lead. Parent protocol:

```text
scout candidate
  -> reopen exact source
  -> inspect caller/consumer/test
  -> classify
```

Never make a blocking port decision solely from a scout summary.

---

# 8. Tool-calling protocol: web and upstream documentation

Use web access only when it materially resolves a current external contract,
version, API, dependency, or compatibility question.

Examples:

- current OpenCode plugin hooks;
- current plugin package behavior;
- Mermaid CLI security options;
- current API deprecation or schema behavior.

Protocol:

```text
web search for discovery
  -> official project/repository/documentation
  -> fetch exact primary source
  -> compare with pinned dependency/version in CodeSleuth
  -> record whether behavior is proven for pinned version or only current upstream
```

Do not silently apply current upstream documentation to an older pinned version.

If CodeSleuth pins dependency version `V`, distinguish:

```text
PINNED_BEHAVIOR_PROVEN
CURRENT_UPSTREAM_ONLY
VERSION_DIFFERENCE_UNRESOLVED
```

Web snippets and search-result summaries are not compatibility proof.

---

# 9. Phase 0: classify the port before studying code

Write a preliminary classification.

## 9.1 Port type

Choose one or more:

- `TOOL_PORT`;
- `SKILL_PORT`;
- `PLUGIN_PORT`;
- `WORKFLOW_PORT`;
- `STATE_MODEL_PORT`;
- `RELIABILITY_HARDENING_PORT`;
- `PRESENTATION_PORT`;
- `CONTRACT_PORT`;
- `ALGORITHM_PORT`;
- `INTEGRATION_PORT`;
- `PROVENANCE_EXTRACTION`.

## 9.2 Target change classification

Under CodeSleuth's current product contract, classify planned work as:

- `CORE-HARDENING`;
- `PROFILE-EXTENSION`;
- `SKILL-EXTENSION`;
- `PLAYBOOK-EXTENSION`;
- `TOOL-EXTENSION`;
- `EXTENSION-MANAGEMENT-UX`;
- `DOCS`.

If the desired work does not fit, stop and identify why it may require a new
product/architecture decision.

## 9.3 Duplication risk

Before detailed design, ask whether the requested feature resembles something
already owned by:

- OpenCode core;
- an installed OpenCode plugin;
- an existing CodeSleuth tool;
- an existing Skill;
- project-local config;
- Git itself;
- a dependency already shipped.

Mark `HIGH_DUPLICATION_RISK` when names differ but responsibilities overlap.

This early warning is especially important for vague terms such as:

- watchdog;
- memory;
- graph;
- cache;
- scheduler;
- router;
- agent;
- index;
- history;
- controller;
- resume;
- sync.

---

# 10. Phase 1: freeze exact source and target identity

Do not proceed from “main as of roughly yesterday.”

## 10.1 Source

Resolve:

```text
source repo
source branch/ref
source full SHA
```

If a source feature is spread over historical branches, record every branch/SHA
and distinguish:

- accepted/merged behavior;
- proposed/unmerged behavior;
- superseded behavior;
- documentation-only branch;
- implementation branch.

A feature name may exist on several branches with different maturity. Do not
collapse them.

## 10.2 Target

Resolve:

```text
CodeSleuth base branch
base full SHA
existing related feature branches
open related PRs
```

Check whether another branch is already implementing overlapping ownership.

## 10.3 Base branch rule

Default new port branches to current accepted `main`, not another feature branch,
unless the user explicitly wants a dependent stack.

Independent features should remain independent until review proves a shared
refactor is necessary.

---

# 11. Phase 2: establish authority hierarchy

Read authoritative files before broad implementation study.

## 11.1 Source authority questions

Find documents answering:

- What problem is the source feature intended to solve?
- Is the design accepted, proposed, deprecated, or historical?
- Which artifacts are canonical vs derived?
- What are explicit non-goals?
- What runtime/component owns the behavior?
- Which tests constitute acceptance?

Do not assume the newest-looking document is authoritative merely because its
file timestamp is newer.

## 11.2 Target authority questions

For CodeSleuth determine:

- current product identity and feature freeze;
- OpenCode/CodeSleuth ownership boundary;
- extension category allowed for the port;
- current state/persistence authority;
- direct OpenCode compatibility requirements;
- update/install lifecycle constraints;
- user-owned configuration preservation rules;
- current accepted tests/gates.

## 11.3 Authority conflict ledger

Create a short table:

| Topic | Source authority | Target authority | Conflict? | Resolution |
| --- | --- | --- | --- | --- |

A conflict must be resolved before implementation. “We will see what happens” is
not a resolution strategy.

---

# 12. Phase 3: reconstruct the actual source capability

Now inspect the implementation.

## 12.1 Trace from consumer to mechanism

For each important behavior, trace:

```text
user/consumer entry
  -> public contract/config
  -> caller
  -> implementation
  -> state/external boundary
  -> returned/visible result
  -> tests
```

Do not infer production capability because a helper/type exists.

## 12.2 Distinguish planned from implemented

Classify source pieces:

- `IMPLEMENTED_AND_USED`;
- `IMPLEMENTED_BUT_ORPHANED`;
- `CONTRACT_ONLY`;
- `DOC_ONLY`;
- `TEST_ONLY`;
- `PROPOSED_FUTURE`;
- `SUPERSEDED`.

This classification prevents porting a roadmap item as though it were already
proven production behavior.

## 12.3 Identify the actual invariant

Ask repeatedly:

> If I replaced the source language/process/UI/database, what guarantee would
> still need to remain true?

That sentence is usually the portable core.

Examples learned from prior ports:

### Graph/context example

Source mechanism:

```text
FollowTheMoney GraphProjection -> Mermaid/static/UI projections
```

Portable core:

```text
one bounded renderer-neutral relationship projection
  -> multiple derived consumers
canonical identity != presentation identity
derived diagram != evidence
```

Non-portable source assumptions:

```text
FtM ontology
OpenAleph identity
Rust graph types
Mermaid renderer roadmap
```

### Watchdog example

Source mechanism:

```text
scheduled shell census
risk scoring
detached worktree
OpenCode run
persist last successful census
```

Portable core:

```text
deterministic health/gate before intervention
exact target identity
bounded recovery
exclusive recovery lock
state advances only after verified success
recovery output != correctness proof
```

Non-portable assumptions:

```text
six-hour systemd cadence
Aleph MVP gate
Rust crate risk weights
product-gap census prompt
```

---

# 13. Phase 4: decompose source behavior into porting units

For each source capability, create a row with:

```text
ID
source behavior
source proof
portable invariant
dependencies
source-only assumptions
target owner
action
acceptance proof
```

Example:

```text
PORT-03
Behavior: successful recovery advances checkpoint state
Source proof: wrapper writes state after clean run/postconditions
Portable invariant: failed recovery cannot advance durable authority
Target owner: review_state/watchdog integration
Action: ADAPT
Acceptance: inject failure before postcondition; checkpoint remains unchanged
```

This table becomes the semantic backbone of the implementation and review.

---

# 14. Phase 5: collision audit in CodeSleuth

This phase is mandatory.

For every proposed target responsibility, search for existing owners.

## 14.1 Search categories

Search target repository for:

- synonymous feature names;
- configuration keys;
- plugin package names;
- existing state directories;
- commands;
- tool exports;
- Skills;
- lifecycle/update code;
- TUI controls;
- tests mentioning equivalent behavior.

## 14.2 Ownership decision tree

Use:

```text
Does OpenCode already own the runtime behavior?
  yes -> configure/expose/hook it; do not recreate runtime
  no
   |
Does an installed plugin own it?
  yes -> preserve plugin ownership; add target-native surrounding state/UX only
  no
   |
Does existing CodeSleuth durable state own the truth?
  yes -> extend/query that state; do not create parallel truth
  no
   |
Is this actually a new extension allowed by product contract?
  yes -> implement smallest extension
  no -> architecture/product decision required
```

## 14.3 Same noun does not imply same responsibility

Two things called “watchdog” may mean:

- process liveness;
- tool stall detection;
- durable-state health;
- architecture drift auditing;
- service restart policy.

Two things called “graph” may mean:

- canonical domain ontology;
- source code dependency graph;
- UI visualization;
- model context projection.

Always compare responsibility, authority, inputs, outputs, and failure semantics,
not names.

---

# 15. Phase 6: design the target-native contract before code

Write the target contract in plain language and, where useful, small typed
pseudocode.

The contract must answer:

1. Who calls it?
2. Who owns it?
3. What are inputs?
4. Which inputs are authoritative?
5. What state can it persist?
6. What state must remain derived?
7. What are hard bounds?
8. What are failure states?
9. What is explicitly not proven by success?
10. How is stale state detected?
11. How is state invalidated/rebuilt?
12. How does it interact with OpenCode-native behavior?
13. What existing behavior must remain directly usable without CodeSleuth wrappers?

## 15.1 Prefer closed enums for semantic states

For critical status/kind fields, prefer a closed set of explicit values over free
strings when the target implementation language makes this practical.

## 15.2 Stable identity must exclude presentation accidents

If the port introduces stable IDs, derive them from canonical semantic fields, not:

- display labels;
- UI positions;
- Mermaid aliases;
- timestamps unless time is part of identity;
- random line order;
- transient model text.

## 15.3 Put bounds in the contract

Every collection or repeated process that can grow should specify:

- item limit;
- byte/token limit where relevant;
- timeout/retry budget;
- truncation indicator;
- continuation or rehydration strategy if required.

An unbounded “temporary” projection has a habit of becoming permanent precisely
when somebody starts relying on it.

---

# 16. Phase 7: design acceptance before implementation

Do not let the coding agent invent acceptance after seeing its own code.

Create gates first.

## 16.1 Gate A: identity

Prove:

- exact source SHA studied;
- exact target base SHA;
- feature branch starts at intended base or dependency is explicit;
- branch did not silently inherit unrelated feature work.

## 16.2 Gate B: source semantics

For every portable invariant, cite exact source implementation/contract/test
showing the behavior exists or classify it as design-only.

## 16.3 Gate C: target ownership

Prove no duplicate authority was introduced.

Explicitly answer:

- What existing owner remains authoritative?
- What new component is derived/thin?
- What tempting source subsystem was deliberately omitted?

## 16.4 Gate D: positive functional semantics

Test normal target behavior end to end across the real boundary that matters.

Do not rely solely on unit tests that begin after the dangerous boundary.

## 16.5 Gate E: negative semantics

Attempt misuse/failure cases such as:

- invalid IDs;
- untracked/path-escape inputs;
- stale blob/revision;
- corrupt persisted state;
- duplicate registration;
- malformed model output;
- missing dependency;
- timeout;
- partial write;
- concurrent recovery;
- unsupported enum/kind;
- oversized inputs;
- renderer/config injection;
- permission denial.

## 16.6 Gate F: stale-state behavior

If the port persists or derives state, prove what happens when underlying authority
changes.

Examples:

```text
file blob changes
HEAD changes
configuration changes
plugin version changes
source ref changes
review/session changes
```

Required outcome must be explicit: invalidate, reverify, rebuild, block, or safely
continue.

## 16.7 Gate G: large-input/boundedness

Use a synthetic large case.

Examples:

- thousands of reviewed paths;
- hundreds of graph nodes/edges;
- many findings;
- long-running session;
- large labels/untrusted strings.

Prove model-visible/tool-visible output remains bounded and truncation is honest.

## 16.8 Gate H: non-regression

Run all existing gates for affected owners, not merely new tests.

If modifying review state, run existing review-state tests.
If modifying installer material, run lifecycle/install/update tests.
If modifying TUI, run TUI tests.
If modifying docs contracts, run docs contract tests.
If modifying OpenCode integration, run the strongest available runtime smoke.

## 16.9 Gate I: exact-head review

After implementation:

- resolve the actual feature-branch full SHA;
- compare to current target base;
- inspect every changed file;
- re-read current target authority;
- verify acceptance against the **new head**, not a coding-agent summary.

If base moved materially, rebase/update first or explicitly review the resulting
divergence.

---

# 17. Phase 8: create the feature branch

Recommended naming:

```text
feature/<capability>
hardening/<capability>
skill/<capability>
tool/<capability>
plugin/<capability>
```

Use a branch dedicated to one semantic owner where possible.

## 17.1 Branch creation protocol

Before creating:

```text
fetch current target main
resolve full SHA
search for same/similar branch
search open PRs for overlap
```

Then create the branch from the exact intended base.

After creation, fetch branch metadata and confirm its head SHA equals the base SHA.

## 17.2 Independent branch rule

Do not base independent ports on each other just because they were requested in
one conversation.

Example:

```text
main
  +-- mermaid/context port
  +-- long-session watchdog port
  +-- porting-discipline skill
```

This is preferable to:

```text
main -> mermaid -> watchdog -> contributor skill -> mystery dependency stack
```

Shared refactors can be extracted later if review proves they are genuinely
shared.

---

# 18. Phase 9: implementation dispatch protocol

When handing implementation to a coding agent, give it a bounded contract, not a
vague “port X.”

The implementation prompt must contain:

1. exact repository;
2. exact branch;
3. exact base SHA;
4. source references and exact SHAs;
5. required target authority files to read first;
6. one-sentence goal;
7. portable invariants;
8. source-specific pieces that must not be ported;
9. target ownership mapping;
10. exact first-slice files/components;
11. non-goals;
12. acceptance tests to implement/run;
13. existing gates to preserve;
14. commit/PR requirements;
15. explicit stop condition.

## 18.1 Coding-agent prompt template

Use this skeleton:

```text
REPOSITORY
<target repo>

BRANCH
<feature branch>

BASE
<full target base SHA>

SOURCE PROVENANCE
<source repo/ref/full SHA/files/PRs>

GOAL
<one semantic goal>

READ FIRST
<target authority>
<target relevant runtime/state/tests>
<source authority>
<source actual implementation/tests>

PORTABLE INVARIANTS
P1 ...
P2 ...

TARGET OWNERSHIP
<behavior -> existing/new owner>

DO NOT PORT
<source-specific assumptions>

IMPLEMENT
<minimum vertical slice>

NON-GOALS
<explicit exclusions>

ACCEPTANCE
<deterministic positive/negative/stale/large/non-regression gates>

PROCESS
- verify exact branch/base before editing;
- do not expand scope silently;
- run actual tests;
- one logical commit unless task explicitly requires staged commits;
- push feature branch;
- open PR;
- do not merge.

RETURN
- full head SHA;
- changed files;
- exact ownership boundary;
- tests actually executed and results;
- unresolved external/runtime proof.

STOP.
```

## 18.2 Why “DO NOT PORT” is mandatory

Coding agents optimize for completion. If they see a coherent source subsystem,
they often bring neighboring machinery because it appears to reduce uncertainty.

Explicit exclusions are therefore part of the specification, not decorative
prose.

---

# 19. Phase 10: implementation tool discipline

For the coding session itself:

## 19.1 Modify the smallest owner first

If target behavior can be achieved by extending one existing state/tool layer,
start there before touching agents, TUI, installer, or docs.

## 19.2 Tests travel with behavior

Add deterministic tests in the same logical change as the behavior.

Do not leave critical acceptance only as manual instructions when it can be tested
cheaply.

## 19.3 No drive-by refactors

A porting PR is not permission to normalize unrelated naming, formatting,
architecture, or old compatibility code.

If a prerequisite refactor is necessary, either:

- keep it very small and explain why it is prerequisite; or
- split it into a separately reviewable PR.

## 19.4 Preserve target-native compatibility

After the port, direct OpenCode-native capabilities must still work where the
CodeSleuth product contract requires them.

Do not force users through a CodeSleuth wrapper merely because the port introduced
one.

## 19.5 Persist only what must persist

Prefer:

```text
existing durable truth
+ small schema-compatible extension
+ derived rebuildable metadata
```

over:

```text
new database/state tree with duplicated facts
```

---

# 20. Phase 11: review the actual new head

Do not review from the coding agent’s summary.

## 20.1 Resolve current identities again

Capture:

```text
current main SHA
PR head SHA
merge base
commit divergence
changed filenames
CI/check status
```

If the PR head moved since the implementation report, review the new head.

## 20.2 Review line by line where semantics are dense

Line-by-line review is especially warranted for:

- validation;
- identity/hash construction;
- persistence transitions;
- recovery;
- authorization/permissions;
- path handling;
- plugin hooks;
- untrusted-string rendering;
- state migration;
- boundedness/truncation;
- concurrency/locking.

## 20.3 Re-run the ownership audit

Implementation may accidentally create authority that the design did not intend.

Check actual code for:

- parallel state;
- duplicated runtime loops;
- fallback behavior that bypasses target owner;
- implicit source-specific assumptions;
- new public APIs not required by the port;
- UI/config claiming authority it does not have.

## 20.4 Trace every claimed capability through consumers

For each port invariant:

```text
entry/caller
  -> implementation
  -> state/external boundary
  -> consumer/result
  -> test
```

A type existing in a file is not proof that production uses it.

## 20.5 Attack counterexamples

A reviewer should actively try to break the contract.

Examples:

- changed reviewed file after checkpoint;
- duplicate semantic edge with different display label;
- malformed Mermaid label;
- missing plugin package;
- two concurrent watchdog recoveries;
- explicit resume to review A while session is bound to review B;
- source branch moved/rebased;
- partial file write;
- huge context projection;
- untracked file inserted into verified state.

---

# 21. Evidence levels for acceptance claims

Do not call all green tests equivalent.

For each important claim, record the strongest evidence actually obtained.

Suggested levels:

```text
L0 STATIC
source/docs/config inspection only

L1 UNIT/CONTRACT
isolated deterministic logic tested

L2 INTEGRATION
real target components wired together

L3 RUNTIME
actual OpenCode/plugin/tool runtime exercised

L4 LIVE/EXTERNAL
real external boundary exercised where relevant
```

Also record boundary quality:

```text
REAL_BOUNDARY
MIXED
INJECTED
STATIC_ONLY
```

Example:

```text
Claim: explicit resume binds a new OpenCode session to existing review state
Evidence: Bun tool integration test
Level: L2
Boundary: INJECTED session context, real filesystem/Git state
Unproven: real OpenCode restart/reconnect event path
```

This prevents “tests are green” from becoming a substitute for understanding what
they actually proved.

---

# 22. Acceptance gate catalog

A production-ready port should select all applicable gates below.

## G0: exact identity gate

PASS only if:

- source full SHA recorded;
- target base full SHA recorded;
- feature head full SHA recorded;
- branch ancestry/divergence understood;
- no review is based on stale coding-agent summary.

## G1: authority gate

PASS only if:

- source authoritative status established;
- target authoritative contract re-read;
- source/target conflicts resolved explicitly;
- no superseded source document silently governs the port.

## G2: portable-contract gate

PASS only if:

- portable invariants are written;
- each invariant has source evidence;
- source-specific assumptions are listed;
- target-native behavior is defined independently of source filenames.

## G3: ownership/non-duplication gate

PASS only if:

- every behavior has one target owner;
- existing OpenCode/plugin/CodeSleuth owners remain authoritative;
- no second runtime, router, watcher, evidence store, ontology, or acceptance
  authority is introduced unintentionally.

## G4: deterministic semantics gate

PASS only if:

- normal behavior is tested;
- stable identities/state transitions are deterministic where required;
- errors fail in the intended direction;
- status/kind semantics cannot silently widen.

## G5: stale-state gate

PASS only if relevant authority changes are detected and handled explicitly.

## G6: adversarial/negative gate

PASS only if meaningful malformed, stale, oversized, duplicate, unauthorized, or
concurrent cases are tested or objectively demonstrated.

## G7: boundedness gate

PASS only if:

- large synthetic case tested;
- model/tool output remains bounded;
- truncation is explicit;
- no full durable store is accidentally injected into active context.

## G8: lifecycle/update gate

Required when installed managed files/config/profile/plugin material changes.

PASS only if:

- fresh install works;
- adopt/update semantics remain safe;
- user-owned configuration is preserved;
- local managed-file conflicts follow existing policy;
- installed target smoke recognizes the new material where applicable.

## G9: OpenCode compatibility gate

Required when commands, Skills, tools, plugins, launcher, permissions, watcher, or
compaction integration changes.

PASS only if direct OpenCode usage remains valid and no custom CodeSleuth
controller/runtime replaces native ownership.

## G10: documentation truth gate

PASS only if docs describe actual merged behavior, limitations, provenance,
ownership, and acceptance accurately.

Do not document future behavior as current behavior merely because the port plan
contains it.

## G11: exact-head re-review gate

PASS only if the final review inspected the actual PR head after all requested
changes/rebases and all blocking findings were rechecked against that head.

---

# 23. Common failure modes and how to detect them

## 23.1 Cargo-cult directory copy

Symptom:

- target receives source folder names/types/processes with little target mapping.

Detection:

- contributor cannot state portable invariants without naming source internals.

Correction:

- stop implementation;
- reconstruct source capability and target ownership map.

## 23.2 Porting the renderer instead of the projection

Symptom:

- visible output mechanism is copied before the data/semantic contract exists.

Example:

- importing Mermaid/Chromium rendering when the real reusable idea is a bounded
  renderer-neutral context projection.

Correction:

- establish the renderer-neutral contract first;
- defer presentation runtime until demanded by a proven consumer.

## 23.3 Porting the wrapper instead of the invariant

Symptom:

- shell/systemd/scheduler logic copied into a target whose runtime already provides
  the underlying supervision.

Example:

- adding another stall watchdog when `opencode-keepalive` already owns execution
  liveness.

Correction:

- identify the missing higher-level invariant, such as durable continuity safety.

## 23.4 Source ontology leakage

Symptom:

- domain-specific source node/edge/status kinds appear in generic CodeSleuth
  contracts.

Correction:

- replace with target-domain semantics and preserve only structural invariants.

## 23.5 Generated artifact becomes authority

Symptom:

- diagram, model summary, cache, or watchdog status is treated as canonical
  evidence/state.

Correction:

- restore canonical/derived split and explicit rebuild/invalidation rules.

## 23.6 Happy-path-only acceptance

Symptom:

- tests prove feature creation but not stale input, malformed state, retries,
  duplicates, concurrency, or large cases.

Correction:

- write adversarial matrix before accepting.

## 23.7 Branch contamination

Symptom:

- feature depends on unrelated previous feature branch accidentally.

Detection:

```bash
git merge-base main feature
git diff --name-status main...feature
```

Correction:

- recreate/rebase onto intended base or explicitly document dependency.

## 23.8 Review from summary

Symptom:

- reviewer verifies bullet points in implementation handoff but never inspects new
  head.

Correction:

- resolve head SHA, changed files, actual diff, current consumers, tests.

## 23.9 Current-upstream confusion

Symptom:

- design relies on latest external documentation while CodeSleuth pins an older
  package/API.

Correction:

- prove pinned behavior or mark runtime behavior unproven and keep scope narrow.

## 23.10 Context-growth hardening that grows context

Symptom:

- compaction/resume mechanism injects expanding durable arrays or evidence excerpts
  back into every summary.

Correction:

- persist full state off-context; inject bounded continuation pointers/counts;
  selectively rehydrate exact material.

---

# 24. Practical tips

## Tip 1: Ask “what would still be true if this were written in another language?”

The answer is often the portable invariant.

## Tip 2: Search for target collisions before designing new APIs

Discovering an existing plugin after writing a replacement is technically
educational, but there are cheaper forms of education.

## Tip 3: Keep source and target notes in separate sections

Do not interleave them while reasoning. Use:

```text
SOURCE FACTS
TARGET FACTS
PORTING INFERENCES
```

This makes assumption leakage visible.

## Tip 4: Prefer one semantic owner per PR

If one source subsystem spans several target owners, split the port.

For example:

```text
projection contract
renderer
interactive UI
model-context integration
```

can be separate slices even if source repository presents them as one feature
family.

## Tip 5: Preserve an explicit “not yet” list

Deferred source capabilities are not bugs merely because they exist upstream.

## Tip 6: Treat branch names as navigation, not evidence

`feature/mermaid-renderer` may contain only a design brief.
Always inspect actual contents.

## Tip 7: Distinguish reusable code from reusable architecture

Sometimes zero lines of source code should be copied even though the architecture
is highly reusable.

## Tip 8: Make the test encode the semantic contract, not source implementation

Bad test:

```text
expect target file to contain source helper name
```

Good test:

```text
changing canonical source identity invalidates derived verified relationship
```

## Tip 9: Force the final reviewer to name omissions

A good port review includes:

```text
Source mechanisms deliberately not ported
```

This proves omission was intentional rather than accidental.

## Tip 10: A successful tool call is not a successful gate

A branch-create API returning 200 proves a branch was created.
It does not prove:

- correct base;
- correct content;
- passing tests;
- semantic acceptance.

Verify postconditions.

---

# 25. Required Porting Dossier template

Use this template before implementation:

```markdown
# Porting Dossier: <feature>

## Identity
- Source repo:
- Source requested ref:
- Source exact SHA:
- Target repo:
- Target base:
- Target exact base SHA:
- Planned branch:

## User goal
<what outcome is actually wanted>

## Source capability proven
<implementation-backed description>

## Source maturity
- accepted/merged:
- proposed/unmerged:
- obsolete/superseded:

## Portable invariants
- P1:
- P2:
- P3:

## Source-specific assumptions to omit
- S1:
- S2:

## Target ownership map
| Behavior | Existing target owner | Port action | Reason |
| --- | --- | --- | --- |

## Minimum vertical slice
- files/components:
- interfaces:
- durable/derived state:

## Explicit non-goals
- ...

## Risks
- duplicate authority:
- stale state:
- external version dependency:
- large-input/context:
- security/untrusted input:
- lifecycle/update:

## Acceptance matrix
| Gate | Scenario | Expected result | Evidence level |
| --- | --- | --- | --- |

## Implementation dispatch
<bounded coding-agent prompt>
```

---

# 26. Required final review report template

```markdown
# Port Review: <feature>

## Verdict
ACCEPT / REQUEST CHANGES / BLOCKED ON RUNTIME EVIDENCE

## Exact identities
- base SHA:
- reviewed head SHA:
- merge base:
- divergence:

## Portable invariants
| Invariant | Implemented where | Evidence | Result |
| --- | --- | --- | --- |

## Ownership/non-duplication
<who owns what after the port>

## Source mechanisms deliberately omitted
- ...

## Findings
<exact path/symbol/evidence>

## Acceptance gates
| Gate | Command/test/evidence | Result | Boundary |
| --- | --- | --- | --- |

## Runtime behavior not proven
- ...

## Base drift / rebase status
- ...

## Merge recommendation
<only after exact-head evidence>
```

---

# 27. Stop conditions

Stop implementation and report the reason if any of these occurs:

1. source exact revision cannot be established;
2. target base cannot be established;
3. source feature is only a summary/roadmap and the user expected proven runtime;
4. source and target authority conflict requires a new architecture decision;
5. requested port would create a prohibited duplicate CodeSleuth runtime owner;
6. an existing target component already owns the behavior and the requested work
   would merely duplicate it;
7. pinned external dependency behavior required for correctness cannot be proven
   and no safe compatibility layer exists;
8. port requires unrelated architectural rewrite to proceed;
9. security or authorization semantics are ambiguous at the target boundary;
10. implementation branch no longer corresponds to the reviewed head/base.

A stop condition is not failure to help. It is preferable to a confidently merged
second source of truth.

---

# 28. Completion contract

A porting task is complete only when all applicable statements below are true:

- exact source and target revisions are recorded;
- the actual source implementation was inspected;
- portable invariants are explicit;
- source-specific assumptions are explicit;
- target ownership is explicit;
- no unintended duplicate authority exists;
- target-native contract is defined;
- implementation scope stayed within the planned vertical slice or deviations are
  documented;
- deterministic positive tests passed;
- meaningful negative/adversarial tests passed;
- stale-state behavior is proven where applicable;
- large-input/boundedness behavior is proven where applicable;
- existing affected-owner regression gates passed;
- direct OpenCode compatibility remains intact where required;
- documentation matches actual behavior;
- final review used the actual new head;
- unproven runtime/external behavior is explicitly listed;
- the reviewer can explain both **what was ported** and **what was deliberately
  not ported**.

The strongest final sentence for a good port is not:

> “It now looks like the source repository.”

It is:

> **“The target now preserves the required source invariants using target-native
> ownership, with the source-specific machinery intentionally excluded and the
> remaining behavior objectively bounded by acceptance evidence.”**
