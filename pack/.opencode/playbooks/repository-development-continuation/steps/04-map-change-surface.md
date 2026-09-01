# Map the bounded change surface

Use the selected active scope and its confirmed repository authority. Produce a bounded change-surface map before any implementation work.

Prefer explicit allowed/excluded paths from the target repository. Supplement them, without claiming protected status, with exact pre-registry ownership evidence from package/workspace definitions, imports/modules, schemas/DTOs, migrations, API definitions, tests referencing the surface, and CI/verify scripts.

If a target-local Protected Capability Registry exists, use dependency-impact closure as the stronger dependency authority. If it does not exist, do not stop solely for that reason and do not use CodeSleuth's own registry as a substitute.

Classify paths outside the selected scope as undeclared, adjacent-track, or explicitly forbidden when repository authority supports that distinction. Do not auto-expand the allowed set because a dependency looks convenient to modify.

Output allowed paths, forbidden/adjacent path patterns, affected/read-only dependency surfaces, and uncertainties. No source edits.
