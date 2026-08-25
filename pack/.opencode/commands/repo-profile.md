---
description: Detect the current repository stack and propose or create its OpenCode profile
agent: repo-profile-architect
---

Build or refresh an evidence-backed OpenCode profile for this repository.

Requested constraints: $ARGUMENTS

Detect the stack locally first. Use Exa-backed `websearch` only for uncertain or
current facts, and `webfetch` the primary source before accepting external
claims. Show the proposed profile and conflicts before asking permission to
write or merge it.
