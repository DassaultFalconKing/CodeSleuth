# Map project-native verification gates

Start one `native_gate_state` map on the same exact target SHA.

Discover only gates owned by the target repository or explicitly required by its active scope. Sources may include CI workflows, verify/build/test scripts, package/workspace commands, migration/schema checks, session acceptance criteria, definition-of-done text, rollback requirements and explicit live smoke requirements.

Record each gate with exact tracked evidence and classify where its result can truthfully be proven:

- `REPO_PROVABLE`: deterministic local/repository test or static check;
- `HOSTED_CI_PROVABLE`: canonical hosted workflow/job evidence;
- `SERVICE_DEPENDENT_REPRODUCIBLE`: requires a service fixture or reproducible dependency environment;
- `LIVE_RUNTIME_REQUIRED`: depends on the actual deployed host/runtime state;
- `OPERATOR_DECISION_REQUIRED`: requires an explicit human choice/waiver rather than a technical probe.

Do not mark a discovered gate PASS merely because its command exists or a health endpoint returns 200. This Step discovers requirements; execution results are separate evidence.

Load the gate map and return the bounded native-gate inventory plus its current cloud-testability state. No source edits.
