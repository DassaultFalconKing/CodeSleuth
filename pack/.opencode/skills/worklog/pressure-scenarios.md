# Worklog pressure scenarios

These scenarios define behavior the portable skill must preserve.

## Scenario 1: New agent after context loss

Given only the repository and a vague instruction such as “continue”, the agent must not infer active source/build state from memory. It must discover repository authority, read current/relevant worklog state, then re-resolve Git refs before acting.

Failure pattern: continuing from a stale SHA or obsolete branch because an earlier chat called it “current”.

## Scenario 2: Two agents in parallel

Agent A investigates build provenance while Agent B reviews parser lineage. They must write separate session records. Neither may overwrite the other’s findings. Conflicts are surfaced in `CURRENT.md` with provenance instead of being silently reconciled.

Failure pattern: one shared mutable ledger where the second agent destroys or ambiguously edits the first agent’s evidence.

## Scenario 3: Runtime evidence does not transfer

One source commit passes unit contracts while another package from a related lineage passes live runtime acceptance. The worklog must preserve these as separate facts and must not label a new candidate accepted until that exact identity is tested.

Failure pattern: “same code family, therefore PASS”.

## Scenario 4: Historical hypothesis is disproved

An agent records a suspected parser defect. A later raw trace proves the model never emitted the expected marker. The later session records the contrary evidence and `CURRENT.md` is updated, but the older session remains immutable.

Failure pattern: rewriting history so future agents cannot see why investigation changed direction.

## Scenario 5: Repository already has a planning worklog

The target repository already declares `docs/current_todo_worklog/TODO.md` or another file as canonical planning SSOT. The Worklog skill must not replace, fork, or silently mirror that authority. Its `CURRENT.md` records session state and links to the canonical planning authority.

Failure pattern: creating two competing “current” sources of truth.

## Scenario 6: Newest carrier differs from tested identity

A later documentation/build-only commit carries the same semantic source core as an earlier tested commit. The worklog must distinguish semantic identity, operational carrier, and runtime-tested artifact rather than collapsing them into one SHA.

Failure pattern: assigning runtime evidence to the newest carrier without proof.

## Verification status

These scenarios are portable acceptance criteria for the skill itself. A repository adopting the skill should exercise them through its normal skill/smoke harness before claiming behavioral verification.
