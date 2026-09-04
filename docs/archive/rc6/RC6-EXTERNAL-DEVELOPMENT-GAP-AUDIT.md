# RC6 External Development Gap Audit

Status: evidence input to `RC6-FEATURE-PLAN.md`.

Question examined: **what does CodeSleuth lack in order to help continue development of these repositories?**

This is not a code review of either target and does not rank their bugs.

## Targets

### PII Parser

Repository: `DassaultFalconKing/PII_PARSER`

Observed main HEAD during this audit: `9f226013f37c3ca62f8f8a4f2845370e2350f639`.

Key development-authority evidence:

- `docs/current_todo_worklog/TODO.md` explicitly declares itself the only planning source of truth and supersedes older roadmaps/backlogs.
- `docs/current_todo_worklog/INDEX.md` distinguishes canonical TODO, supporting evidence, shipped archives and superseded archives.
- `docs/current_todo_worklog/CURRENT_STATE_AND_CONFLICTS_20260814.md` records runtime-vs-configuration conflicts and explicitly separates observed state from fixed state.
- The TODO defines cross-layer exit gates spanning backend, frontend, Temporal, worker capacity, security, runtime topology and live smoke evidence.

### Rust Aleph Agent

Repository: `DassaultFalconKing/Aleph_Rugent`.

Observed main HEAD during this audit: `bf1320a523fb7cf01953d03426403eb049fe5b1a`.

Key development-authority evidence:

- `ORIENTATION.md` defines architectural ownership, accepted ADR authority, current implementation track and accepted delivery sequence.
- `HANDOFF.md` is deliberately only a pointer and says current work must be resolved through Orientation, one active session packet, its predecessor handoff, Waypoint Plan and Acceptance Gates.
- `docs/session-packets/S09.md` defines the current bounded implementation session with prerequisites, required reading, allowed paths, exclusions and exact acceptance criteria.
- `docs/TOOLING-FEEDBACK.md` records a real CodeSleuth run and explicitly states what worked and what remained blocked.

## What already works well enough

The Aleph feedback gives unusually direct evidence:

1. exact-target identity is useful and reproducible;
2. isolated Playbook steps are useful;
3. contract triangulation can find `AGREE` and drift across code/docs/tests;
4. reports/provenance are useful navigation and audit surfaces;
5. fail-closed behavior when a protected registry is absent is honest;
6. contributor anti-patterns are useful as a narrow static gate.

Therefore RC6 should not replace these mechanisms. The missing layer is **development continuation authority**, not another generic reviewer.

## Gap G1 — CodeSleuth cannot yet resolve the repository's development authority graph

A mature repository frequently has several documents that look like plans, but only one or a small ordered set is authoritative.

PII Parser requires CodeSleuth to understand:

```text
TODO.md = planning SSOT
CURRENT_STATE... = evidence baseline, not roadmap
supporting briefs = evidence
archive_shipped = history
archive_superseded = non-authoritative history
```

Aleph requires:

```text
ORIENTATION
  -> active track
  -> one session packet
  -> accepted predecessor handoff
  -> applicable ADR/contracts
  -> WAYPOINT-PLAN
  -> ACCEPTANCE-GATES
```

Current CodeSleuth can inventory and review these files but does not produce a typed **authority map** that distinguishes:

- canonical/current;
- supporting evidence;
- predecessor/accepted handoff;
- superseded/historical;
- forbidden competing roadmap;
- active packet/track;
- normative acceptance authority.

### Required CodeSleuth capability

`development-authority-map`: evidence-bound discovery of planning/session/ADR/handoff/gate authority and supersession relationships.

It must never decide authority from filename alone. Claims require exact textual evidence and must be represented as discovered/confirmed relationships.

## Gap G2 — CodeSleuth cannot yet answer "what work is actually admissible next?"

Both targets already contain a sequencing discipline.

PII Parser has critical-path ordering and explicit stop-gates. For example, security containment precedes dispatcher/signal/gateway rollout.

Aleph S09 has prerequisites, allowed paths, exclusions and a mandatory W5 handoff boundary. A coding agent that simply selects an interesting TODO can violate the repository contract even while writing technically good code.

### Required CodeSleuth capability

`development-continuation-packet`: derive one bounded next-work packet from the target's own authority graph.

Minimum output:

- exact target SHA;
- selected authoritative planning/session source;
- current objective/work item;
- prerequisites and accepted predecessor evidence;
- required reading;
- allowed/owned paths when declared;
- forbidden/out-of-scope paths or adjacent tracks;
- native tests/gates;
- unresolved blockers;
- explicit statement of what was derived versus directly declared.

This packet is navigation, not a new roadmap. Where the repository already has a session packet, CodeSleuth should select and summarize it rather than manufacture a competing packet.

## Gap G3 — Dependency impact currently becomes weak when no target-local protected registry exists

Aleph's real CodeSleuth feedback reports that absence of `docs/protected-capabilities.json` correctly blocks protected-capability closure, but this also prevents useful SIB2-style impact reasoning until a registry exists.

PII Parser has many implicit cross-layer contracts without a CodeSleuth registry at all.

### Required CodeSleuth capability

The RC6 brownfield contract bootstrap is necessary, but it must be complemented by a **pre-registry change-surface map** derived from repository-native evidence:

- manifests/workspaces;
- migrations/schema ownership;
- API/DTO contracts;
- native test/gate references;
- documentation ownership links;
- explicit allowed paths/session ownership;
- dependency declarations.

This map may propose contract candidates and affected surfaces. It must not pretend to be a protected registry or infer accepted lifecycle status.

## Gap G4 — CodeSleuth does not yet bind development plans to project-native acceptance gates

PII Parser's Definition of Done mixes static/focused tests with operational rollback and live smoke requirements.

Aleph has canonical `verify.sh fast`, `postgres`, `contracts`, plus packet-specific tests. Its tooling feedback also notes repository-specific parity checks that generic anti-pattern scanning did not catch.

### Required CodeSleuth capability

`native-gate-map`: discover and classify target-owned verification commands and acceptance evidence.

Classification must include:

- repository deterministic/local;
- GitHub-hosted feasible;
- service/container dependent but reproducible;
- credential/live-system dependent;
- operator/manual acceptance.

CodeSleuth must not replace native gates with a generic green badge. It should assemble a matrix and state what remains unverified.

## Gap G5 — CodeSleuth lacks an explicit cloud-testability boundary

This is the practical bridge between repository analysis and the later Work/Cursor/OpenCode debugging phase.

PII Parser contains facts that only a live deployment can answer reliably: actual llama.cpp slots, Temporal pollers/schedules, worker heartbeats, deployed reranker capability, MCP reachability and credential rotation.

Aleph's own CodeSleuth feedback says exhaustive triage cannot be closed without live PostgreSQL/Qdrant/Infinity/OpenAleph.

### Required CodeSleuth capability

Every development-continuation packet should partition acceptance into:

1. `REPO_PROVABLE`;
2. `HOSTED_CI_PROVABLE`;
3. `LIVE_RUNTIME_REQUIRED`;
4. `OPERATOR_DECISION_REQUIRED`.

The packet must include a stop condition: do not hand off to live debugging while items in the first two categories remain red or untested.

## Gap G6 — Live runtime evidence has no generic typed evidence envelope

When live work finally becomes necessary, CodeSleuth needs to consume runtime facts without confusing them with repository authority.

Examples:

- PII: container command, `/props`, `/slots`, Temporal queue/poller state, worker capability discovery.
- Aleph: PostgreSQL migration/runtime state, Qdrant/Infinity/OpenAleph reachability and live MVP checks.

### Required CodeSleuth capability

A bounded `external-evidence-manifest` contract with:

- source/adapter identity;
- observed-at timestamp and freshness/TTL;
- target repository SHA;
- command/endpoint/test identity without secrets;
- sanitized structured result;
- authority class (`runtime observation`, never repository contract by itself);
- evidence locator/artifact reference;
- PASS/FAIL/UNKNOWN only when the native check itself defines that meaning.

RC6 does not need product-specific PII or Aleph connectors. It needs the generic evidence envelope and adapter boundary so Work/Cursor/OpenCode can supply live observations later.

## Gap G7 — CodeSleuth does not enforce repository-declared allowed paths against a proposed change

Aleph S09 explicitly constrains expected owners and prohibits unrelated graph/W5 work.

PII's critical path similarly makes some work inadmissible before security containment and distinguishes supporting documents from planning authority.

### Required CodeSleuth capability

`scope-guard` derived from the active authority packet:

- compare branch/PR changed paths with declared allowed/owned paths;
- report `IN_SCOPE`, `UNDECLARED`, or `FORBIDDEN/ADJACENT_TRACK`;
- never auto-expand scope because the implementation "needs" another file;
- require explicit authority change when scope must grow.

This is especially valuable before handing code generation to another model.

## Gap G8 — Repository-native contract/gate candidates need promotion, not automatic invention

Aleph feedback identifies concrete parity/watchdog candidates that generic static scanning missed. PII contains similar repository-specific invariants such as "no direct llama.cpp calls outside the gateway".

These are useful discoveries but should not become permanent CodeSleuth global rules.

### Required CodeSleuth capability

A proposal path:

```text
observed repeated invariant
-> evidence-bound candidate
-> triangulation
-> user/repository-owner approval
-> target-local protected contract or native gate
```

This reuses RC6 brownfield adjudication rather than adding a magical lint generator.

## Repository-specific result

### PII Parser

To materially help continue development, CodeSleuth most needs:

1. planning-SSOT/supersession detection;
2. critical-path and prerequisite extraction;
3. cross-layer change-surface mapping before a registry exists;
4. native-gate mapping with cloud/live partition;
5. runtime evidence envelope for later live capacity/security acceptance;
6. target-local contract/gate candidate promotion.

A PII-specific CodeSleuth profile is not required for RC6.

### Aleph Rugent

To materially help continue development, CodeSleuth most needs:

1. Orientation -> waypoint -> session-packet -> handoff authority resolution;
2. allowed-path and adjacent-track enforcement;
3. brownfield registry bootstrap so dependency/FR closure does not stop at registry absence;
4. native verify/packet-specific gate mapping;
5. cloud/live boundary and typed external evidence for PostgreSQL/Qdrant/Infinity/Aleph;
6. target-local promotion of newly discovered parity/contract gates.

An Aleph-specific CodeSleuth profile is not required for RC6.

## Common conclusion

The missing product layer is not "more code review". It is:

> **Evidence-bound development continuation: discover what the repository itself says is authoritative, select the admissible next scope, bind it to exact target and native gates, enforce that scope, and stop at the precise boundary where live evidence is required.**

That becomes the central RC6 feature objective.