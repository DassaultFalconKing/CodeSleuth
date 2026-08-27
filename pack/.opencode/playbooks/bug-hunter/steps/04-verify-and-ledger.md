# Step: verify findings and build ledger

Consume `target_identity`, `hunt_scope`, and `pattern_candidates`. Stay read-only for application source. Do not repair findings during this Step.

For every candidate before accepting it as a finding:

1. reopen exact surrounding source at the captured target;
2. trace producer → transformation → consumer and identify the concrete bad state or counterexample;
3. inspect the relevant executable test or prove that none covers the path;
4. prove canonical-gate reachability, including skip/xfail/environment conditions;
5. compare BASE behavior when the claim is a regression or compatibility break;
6. triangulate code/config, normative/public documentation, and tests for protected or user-visible contracts;
7. search the repository for sibling occurrences of the same engineering assumption.

If evidence is insufficient, keep the item as `INVESTIGATE`; confidence or grep density is not a substitute for a witness.

Severity:

- `BLOCKER`: current release scope/authority, acceptance identity, or architecture makes integration inadmissible.
- `HIGH`: wrong authoritative state, destructive behavior, compatibility break, security/boundary failure, or materially false green acceptance.
- `MEDIUM`: portability, lifecycle, determinism, incomplete evidence, or material contract drift.
- `LOW`: local hardening/maintainability without current material correctness impact.

For confirmed findings, use `acceptance-matrix-design` only to state the smallest independent regression obligation. Do not implement tests or fixes.

Return `verified_bug_hunt` in this structure:

```text
HEAD:
TARGET:
MERGE BASE:
CHANGE CLASS:
SCANNER:
OVERALL VERDICT:
```

Then group confirmed findings by severity. Each finding must contain:

```text
[HIGH] EP-XX — short title
Location: path:line / symbol
Witness: concrete execution path or counterexample
Why it is wrong: violated invariant/contract
Why current tests did not catch it: concrete reachability/oracle gap
Repository-wide search: sibling locations or "no siblings found"
Required repair: minimum semantic requirement, not code
Required regression: independent test/oracle that catches the class
```

Finish with:

```text
PATTERN LEDGER
- EP-XX: N confirmed / M investigate

CANONICAL-GATE GAPS
...

SAFE-TO-MERGE
YES | NO

STOP CONDITIONS
...
```

Do not optimize the verdict for merge. PR summaries and historical CI are not substitutes for exact current evidence. The hunt succeeds when a repair agent receives finite verified error classes, witnesses, and regression obligations.
