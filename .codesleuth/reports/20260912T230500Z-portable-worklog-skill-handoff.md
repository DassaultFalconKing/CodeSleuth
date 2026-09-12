---
reportType: agent-handoff
targetSha: dc65c106d33157e8de46797a783d8dbf6b965e98
provenance: anon
---

# Portable Agent Worklog skill handoff

Date: 2026-09-12T23:05Z
Target implementation HEAD: `dc65c106d33157e8de46797a783d8dbf6b965e98`
Implementation branch: `feature/portable-worklog-skill`
PR: `#126` — `feat(skills): add portable agent worklog`
Status: IMPLEMENTED ON FEATURE BRANCH; NOT MERGED; BEHAVIORAL PRESSURE REPLAY NOT YET CLAIMED PASS

## Why agents should care

A portable `worklog` Skill now exists for engineering work that spans multiple agents, sessions, worktrees, context resets, or parallel investigations. Its purpose is to stop chat memory from becoming an accidental source of truth.

When a task may outlive the current agent/session, load the Worklog skill before consequential work.

## Skill location

```text
pack/.opencode/skills/worklog/SKILL.md
```

Bundled support files:

```text
pack/.opencode/skills/worklog/CURRENT-TEMPLATE.md
pack/.opencode/skills/worklog/SESSION-TEMPLATE.md
pack/.opencode/skills/worklog/pressure-scenarios.md
```

The skill is also allowlisted in:

```text
pack/.opencode/opencode.json
```

## Core contract

Repository state is authority, not chat memory.

The Worklog preserves engineering continuity as:

```text
immutable per-session records
        +
compact derived CURRENT.md
        +
exact Git/evidence provenance
```

It MUST NOT replace an existing repository planning/TODO/roadmap authority. It records session provenance and links to the planning SSOT when one already exists.

Default project-local state when the repository declares no other location:

```text
agent-worklog/
  CURRENT.md
  SESSION-TEMPLATE.md
  sessions/
```

## Expected agent behavior

At session start / rehydrate:

1. Resolve repository root, branch, HEAD, and worktree status from Git.
2. Read the repository-declared planning/TODO/worklog authority first when one exists.
3. Read `agent-worklog/CURRENT.md` when present.
4. Read only the newest relevant immutable session records.
5. Re-resolve every recorded SHA/ref that matters before acting.
6. Create a new session record; never rewrite another agent's record.

At checkpoints/handoff record only externally useful engineering state:

- exact task and Git identity;
- authorities and inherited decisions;
- actions actually performed;
- files/commits actually changed;
- tests as `PASS`, `FAIL`, `BLOCKED`, or `NOT_RUN` with commands/evidence;
- findings and negative evidence;
- contradictions between agents;
- unresolved questions;
- next safe action.

Use evidence strength labels where useful:

```text
PROVEN
DERIVED
INFERRED
UNKNOWN
```

Never convert `UNKNOWN` into a guess and never transfer a runtime/test PASS between different source SHAs, packages, artifacts, or environments.

## Semantic commands

Even if the host has no literal slash-command implementation, interpret these operations semantically:

```text
/worklog-start
/worklog-checkpoint
/worklog-handoff
/worklog-rehydrate
```

## Pressure cases covered

The bundled scenarios explicitly cover:

- new agent after context loss;
- parallel agents writing separate immutable records;
- cross-SHA/cross-package PASS contamination;
- later evidence disproving an earlier hypothesis;
- repositories that already have their own planning/worklog SSOT;
- distinction between semantic source identity and a newer carrier commit.

## Relationship to existing CodeSleuth architecture

CodeSleuth already treats Skills as an extension/control surface and already has repository-development continuation logic that discovers canonical TODO/worklog authority. The portable Worklog complements that architecture: it does not create a second controller, runtime, planning authority, or durable evidence ledger.

## Source lineage

This portable Skill was adapted from the Agent Worklog discipline created during the Gemmamonster RC2 semantic-refit session on 2026-09-12. The CodeSleuth version removes Gemmamonster-specific branches, SHAs, runtime paths, and assumptions.

## Agent instruction

For any future CodeSleuth task that is multi-session, multi-agent, parallel, provenance-sensitive, or likely to survive context compaction:

> Load `worklog`, rehydrate exact repository state, and create a new immutable session record before consequential work.

Do not treat this report as source or acceptance authority. The implementation branch/PR and exact repository state remain authoritative. Re-check PR #126 and the exact current target HEAD before merge/release claims.
