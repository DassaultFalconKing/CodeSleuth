# Step 4 — produce the discovery report and stop classification

Use `identity_inventory`, `authority_execution`, and `architecture_risks`. Do not invent facts to make the report look complete.

Produce `bootstrap_report` with:

## Repository identity
- root
- branch
- exact HEAD
- dirty state
- remotes
- submodules

## What this project appears to be
Evidence-backed description only.

## Confidence
HIGH / MEDIUM / LOW with reasons.

## Inventory
Main directories/files/content classes.

## Authority map
Documents and executable artifacts that currently act as sources of truth.

## Architecture
Components and evidence-backed relations.

## Execution model
Build/run/deploy flow.

## Test and CI model
What exists and what was actually executed, classified PASS/FAIL/NOT RUN/BLOCKED/NOT APPLICABLE.

## External dependencies
Submodules/repos/binaries/services and provenance.

## Findings
For each finding: severity, location, evidence, impact, recommendation, confidence.

## Unknowns
Facts that cannot be proven from the checkout.

## Contradictions
Where docs, code, config, or observed behavior disagree.

## Recommended next session
Choose only from:
- implementation
- hardening
- test coverage
- dependency repair
- architecture investigation
- external dependency review
- no action required

Before completion, answer:
1. What is this project?
2. How does it run?
3. Where are the main source boundaries?
4. What is authoritative?
5. What external dependencies exist?
6. What tests/gates exist?
7. Which claims are verified vs inferred?
8. Is evidence sufficient for safe implementation?

If any answer is unsupported, leave it UNKNOWN. Never fill evidence gaps with guesses.

Output only the bounded `bootstrap_report` required by the next report-persistence Step.
