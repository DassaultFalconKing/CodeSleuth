# Bug Hunter Playbook

Runs a read-only exact-head bug hunt before repair or merge decisions. It combines the contributor anti-pattern catalogue with bounded source review, contract evidence, canonical-gate reachability, and repository-wide sibling searches.

The parent `build` agent reads `playbook.json`, materializes one Step at a time, and prefers a fresh host-native child session for each Step. The hunt must not repair application source. Mechanical scanner output is a candidate signal, not a verified finding.

Use `/bug-hunt <repository|PR|scope>` or `/playbook bug-hunter <scope>`.
