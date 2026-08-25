---
description: Resume a checkpointed repository review without repeating completed discovery
agent: build
---

Resume repository review state. Stay on OpenCode's primary `build` agent so the
native provider-specific controller prompt for the selected model remains in
effect.

Load the `repository-deep-review` skill if it is not already in use.

Review ID (optional): $1
Additional instruction: $ARGUMENTS

Call `review_state_load`, using the supplied review ID when present. Confirm the
current HEAD and dirty state against the checkpoint. If repository state changed,
report the drift and re-verify affected evidence before continuing.

Resume from the checkpoint's `next` actions. Do not redo phases/components
already listed as complete unless their source blobs changed or the user
explicitly requests re-review. Stay read-only for application source. At
completion, load `codesleuth-reports` and persist an updated markdown report
under `.codesleuth/reports/`.
