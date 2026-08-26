---
name: eha-candidate-selection
description: Select one literal release-stream head SHA as the immutable EHA target for future SIB acceptance
slash: true
---

# EHA candidate selection

## Atomic contract

**Input:** active numbered release stream `dev/release-X.Y.Z`, requested scope, and exact checkout identity.

**Objective:** capture the literal full SHA at the release-stream head and bind the EHA campaign to that exact identity.

**Output:** release branch ref, selected exact SHA, branch/dirty state, and selection provenance sufficient to start an EHA campaign.

**Stop:** the checkout HEAD does not equal the selected release-stream head, identity is ambiguous, or a substitute ref (PR head, repair branch, synthetic merge ref, tree-equivalent commit) would replace the literal release-stream head.

**Must not:** treat a branch name as acceptance evidence, continue a campaign after HEAD changes, or substitute convenience refs for the selected release-stream head.

Read `docs/SIB-CANDIDATE-SELECTION.md`, `docs/EXACT-HEAD-ACCEPTANCE.md`, and `docs/EHA-OPERATING-PLAYBOOK.md`. For the current line the canonical stream is `dev/release-0.4.0`.

The release branch supplies candidates; the exact SHA carries the proof. If the release branch moves after selection, the running campaign remains bound to the originally selected SHA.
