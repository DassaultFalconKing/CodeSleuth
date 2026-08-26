# Repository Deep Review Playbook

Runs a whole-repository, PR, or broad architecture review without loading one giant review prompt. The parent `build` agent reads `playbook.json`, materializes one Step at a time, and prefers a fresh host-native child session for each Step.

The reusable reasoning lives in atomic Skills. Step files contain only campaign-specific glue and output requirements.

Use `/playbook repository-deep-review <scope>` or the `/repo-review` command.
