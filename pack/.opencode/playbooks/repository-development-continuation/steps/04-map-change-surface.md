# Map the bounded change surface

Use the selected active scope and its confirmed repository authority. Produce a bounded change-surface map before any implementation work.

Load the exact authority map first. Build `seedPaths` only from implementation owners that repository authority or exact source evidence currently identifies and that exist at the target SHA. Seeds may be tracked files or tracked directories; never pass a nonexistent future handoff, planned output file, or guessed path as a seed.

Collect exact tracked authority-named verification paths such as native verify scripts, workflow definitions, contract fixtures, schema/migration entry points or other read-only acceptance surfaces explicitly named by the selected authority. Pass those as `authorityPaths`; they expand the derived inspection surface but never grant mutation authority.

Call `change_surface_state_derive` with the exact target SHA, tracked `seedPaths`, and bounded `authorityPaths`. Then call `change_surface_state_load` and use the revalidated projection. The deterministic projection may include package/workspace ownership, reverse package consumers, import/use references, `include_str!`/`include_bytes!` targets, migrations, tests and authority-named verification paths. It remains `DERIVED_NON_AUTHORITATIVE`.

Prefer explicit allowed/excluded paths from the target repository for mutation authority. The derived change surface is evidence for impact inspection only. It cannot create positive allowed-path authority or auto-expand the accepted scope.

If a target-local Protected Capability Registry exists, use dependency-impact closure as the stronger dependency authority. If it does not exist, do not stop solely for that reason and do not use CodeSleuth's own registry as a substitute.

Classify paths outside the selected scope as undeclared, adjacent-track, or explicitly forbidden when repository authority supports that distinction. Preserve unresolved structural/runtime/external-consumer edges as uncertainty rather than manufacturing closure.

Output the change-surface map id, allowed paths, forbidden/adjacent path patterns, affected/read-only dependency surfaces, authority-named verification paths, and uncertainties. No source edits.
