# EHA / SIB acceptance Playbook

Runs one Exact-Head Acceptance campaign against a single immutable SHA using atomic Skills and `eha_state_*` tools. Use `/eha-test` or `/playbook eha-sib-acceptance`.

The parent reads the manifest only; each Step is materialized separately. Do not repair the target during this Playbook.
