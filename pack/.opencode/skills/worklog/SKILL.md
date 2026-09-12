---
name: worklog
description: Preserve engineering continuity across agents, sessions, worktrees, and context resets using immutable session records plus a compact derived current-state view
slash: true
---

# Worklog

## Atomic contract

**Input:** a repository task that may outlive one agent/session, run in parallel, or require later continuation.

**Objective:** preserve exact engineering state, provenance, evidence, decisions, contradictions, and next-safe actions without treating chat memory as authority.

**Output:** immutable per-session records plus a compact derived current-state file under a project-local worklog root.

**Stop:** repository identity cannot be resolved, the declared planning authority conflicts with the proposed worklog state, or required evidence is unavailable.

**Must not:** replace the repository's canonical TODO/roadmap/planning authority, overwrite another agent's session record, transfer PASS across SHAs/packages, convert `UNKNOWN` into a guess, or record private chain-of-thought.

## Portable state root

Use the repository-declared agent/session worklog location when one exists. Otherwise default to:

```text
agent-worklog/
  CURRENT.md
  SESSION-TEMPLATE.md
  sessions/
```

The Worklog is **session provenance**, not the repository's planning SSOT. If the repository already declares a canonical TODO/worklog/roadmap authority, preserve that authority and link to it from `CURRENT.md` rather than replacing it.

If templates are missing, materialize them from this skill's bundled `CURRENT-TEMPLATE.md` and `SESSION-TEMPLATE.md`.

## Start / rehydrate

Before consequential work:

1. Resolve repository root, branch, HEAD, and worktree status from Git.
2. Discover the repository's canonical planning/development authority. Do not infer it from the worklog.
3. Read `<worklog-root>/CURRENT.md` when present.
4. Read only the newest session records relevant to the requested task, branch, files, or unresolved dependency.
5. Re-resolve every recorded ref that matters. A previously true SHA is historical evidence, not current identity.
6. Create a new session record. Never edit another agent's immutable session record.

Record the distinction between:

- `RECORDED`: stated by an earlier worklog entry;
- `RE_RESOLVED`: confirmed against current repository state;
- `CONFLICT`: recorded state and current evidence disagree.

## Checkpoint

Record only externally useful engineering state:

- session id, agent/tool surface, task, repository, branch/base/HEAD;
- authorities and inherited decisions;
- commands/actions actually performed;
- files changed and exact resulting commit SHAs;
- tests with exact command plus `PASS`, `FAIL`, `BLOCKED`, or `NOT_RUN`;
- findings and negative evidence;
- decisions made and their evidence;
- contradictions with earlier sessions;
- unresolved questions, blockers, and next safe actions.

Use evidence labels when material:

```text
PROVEN     direct artifact/tool/runtime evidence
DERIVED    deterministic conclusion from proven evidence
INFERRED   plausible but not directly demonstrated
UNKNOWN    evidence absent or conflicting
```

Never report `INFERRED` as `PROVEN` merely because another agent already wrote it down.

## Handoff

At session end:

1. Re-resolve branch, HEAD, and status.
2. Finish the session record with actual results. Do not claim unrun tests or acceptance.
3. Append or finalize the immutable session file.
4. Update `CURRENT.md` only with facts that remain operationally current.
5. Every important current fact must carry provenance to a session record, commit, report, test artifact, or exact external evidence.
6. Move disproved/superseded hypotheses out of the current operational picture without deleting their historical session records.
7. State the next safe action and what evidence it depends on.

## Parallel agents

Each agent/session writes a distinct session file. Never use one concurrently appended ledger.

When agents disagree:

1. preserve both immutable records;
2. mark the contradiction in `CURRENT.md`;
3. identify the exact evidence required to resolve it;
4. do not silently synthesize a compromise.

A later agent may resolve the conflict with stronger evidence, but must cite the conflicting sessions rather than rewriting them.

## Context-loss discipline

After compaction, model switch, new agent, or new chat, rehydrate from repository state and worklog evidence before continuing. Do not rely on remembered branch names, SHAs, test status, or acceptance state.

Runtime evidence is package-specific. Source-test evidence is source-specific. Documentation assertions are not runtime evidence.

## Semantic commands

Interpret these names semantically even when the host has no dedicated slash-command implementation:

- `/worklog-start`: resolve identity, read current/relevant sessions, and open a new session record.
- `/worklog-checkpoint`: record bounded evidence/results in the current session.
- `/worklog-handoff`: close the session, re-resolve Git, and refresh current state.
- `/worklog-rehydrate`: reload current state and relevant sessions, then re-resolve repository identity before continuing.

When invoked as the `/worklog` Skill, select the matching mode from the user's request or current lifecycle point.

## Fail closed

Do not:

- transfer runtime `PASS` from one SHA, binary, model, package, or environment to another;
- claim a branch is current without resolving it;
- claim a test passed because a previous session says so when the tested identity differs;
- merge planning authority and session-provenance authority;
- erase negative evidence;
- expose secrets or private chain-of-thought in worklog files.

When identity or evidence cannot be established, record `UNKNOWN` or `BLOCKED` and stop the dependent action.
