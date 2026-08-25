---
description: Resume a checkpointed repository review without repeating completed discovery
agent: repo-reviewer
---

Resume repository review state.

Review ID (optional): $1
Additional instruction: $ARGUMENTS

Call `review_state_load`, using the supplied review ID when present. Confirm the
current HEAD and dirty state against the checkpoint. If repository state changed,
report the drift and re-verify affected evidence before continuing.

Resume from the checkpoint's `next` actions. Do not redo phases/components
already listed as complete unless their source blobs changed or the user
explicitly requests re-review.
