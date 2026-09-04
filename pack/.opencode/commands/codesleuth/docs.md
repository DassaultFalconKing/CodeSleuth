---
description: Run the repository-documentation Playbook from verified source evidence
agent: build
---

Execute the stored `repository-documentation` Playbook for:

$ARGUMENTS

If no output path is supplied, use `docs/REPOSITORY-GUIDE.md` only as a proposed default. Keep `build` as primary controller, materialize one Step at a time, and prefer fresh host-native child context per Step.

Do not overwrite canonical docs merely because code appears newer. The Playbook must surface contradictions and satisfy any README translation/parity obligations before applying semantic documentation changes.
