---
name: exact-target-identity
description: Pin and report one exact repository target identity before review, mutation, or acceptance work
slash: true
---

# Exact target identity

## Atomic contract

**Input:** repository/worktree plus requested branch, ref, PR, range, or SHA.

**Objective:** resolve the exact commit identity and distinguish committed, staged, and dirty worktree evidence.

**Output:** repository, requested ref, exact full SHA, branch when applicable, dirty state, and base/head identities for a range.

**Stop:** the requested target cannot be resolved unambiguously or moves while exact-head acceptance is being claimed.

**Must not:** mutate, rebase, merge, reset, clean, or silently substitute `main`/default branch for the requested target.

Prefer `git rev-parse`, `git status --porcelain=v1`, `git merge-base`, and explicit-ref remote fetches. For connector/API reads, use the exact SHA once resolved.

A search result, PR title, branch name, or chat summary is not commit identity. If exact identity is unavailable, return `IDENTITY_UNPROVEN`.
