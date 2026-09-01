# RC6 Scope Acceptance

Status: **ACCEPTED**

Accepted on 2026-09-01 by the repository owner instruction to begin implementation from `docs/RC6-FEATURE-PLAN.md` and later perform a context-loss audit.

`docs/RC6-FEATURE-PLAN.md` is the RC6 implementation authority. No feature may be added merely because it appears useful during implementation. New observations are defects, evidence, or post-RC6 candidates unless they are already required by the accepted plan.

Implementation order remains the plan's Waves 1-7. In particular:

- close repository/GitHub-testable defects before live-host debugging;
- preserve exact-head and failed-SHA immutability;
- do not add repository-specific PII Parser or Aleph Rugent behavior;
- do not let inferred authority, runtime observations, or model confidence override target-repository evidence;
- do not hand work to Work/Cursor/OpenCode for live debugging while any required `REPO_PROVABLE` or `HOSTED_CI_PROVABLE` gate remains red or unexecuted;
- before RC6 acceptance, compare the final implementation against the accepted feature plan and explicitly record anything lost from context or omitted from implementation.
