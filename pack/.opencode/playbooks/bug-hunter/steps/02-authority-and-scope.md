# Step: authority and scope

Consume exact `target_identity`. Stay read-only for application source.

Record the exact HEAD, target/base SHA, merge-base when relevant, and current release/integration ref as context only. Classify the work as ordinary feature population/hardening, Semantic Refit, or architecture change.

Read the current authority needed for the scope, including at least `AGENTS.md`, `CONTRIBUTING.md`, `docs/CONTRIBUTOR-ERROR-PATTERNS.md`, `docs/PROTECTED-CAPABILITY-CONTRACTS.md`, `docs/protected-capabilities.json`, affected product/component/lifecycle contracts, and `.github/workflows/acceptance.yml`.

Resolve current issue/roadmap/contract scope authority before treating historical work as active. A branch name, PR body, old review, generated report, or historical green CI is provenance, not current authority.

If `scripts/contributor_antipatterns.py` exists, execute:

```bash
python scripts/contributor_antipatterns.py scan --strict
```

Record its exact result and warnings. Scanner output starts the hunt; it is not by itself a verified semantic finding.

Use `protected-capability-registry` and `contract-triangulation` only for bounded affected questions. Do not expand every registry entry merely because it exists.

Return only `hunt_scope`: exact identities, change class, relevant scope decisions, affected/protected contracts, changed or seed paths, scanner result, and explicit unreviewed/unknown areas.
