---
description: Resume the repository-deep-review Playbook from existing durable checkpoint state
agent: build
---

Review ID (optional): $1
Additional instruction: $2

Load the existing review checkpoint and verify current exact target identity before resuming. If HEAD/dirty evidence moved, mark affected previous outputs stale and re-run only the Steps/slices whose evidence identity changed.

Resume the stored `repository-deep-review` Playbook from its first incomplete or stale Step. Do not reload completed Step prompts merely to recreate conversation context. Keep only bounded prior outputs/checkpoints plus the next Step materialized.
