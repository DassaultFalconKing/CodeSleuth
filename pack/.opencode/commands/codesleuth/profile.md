---
description: Detect the current repository stack and propose or create its OpenCode profile
agent: build
---

Build or refresh an evidence-backed OpenCode profile for this repository. Stay
on OpenCode's primary `build` agent so the native provider-specific controller
prompt for the selected model remains in effect.

Requested constraints: $ARGUMENTS

Detect the stack locally first. Call `repo_profile` and `repo_inventory`, then
inspect actual manifests, lockfiles, CI, task runners and existing OpenCode
settings. You may Task `repo-profile-architect` for a bounded evidence pass.

Use Exa-backed `websearch` only for uncertain or current facts, and `webfetch`
the primary source before accepting external claims. Show the proposed profile
and conflicts before asking permission to write or merge it.
