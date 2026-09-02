# Resolve repository development authority

Freeze the exact target from the prior Step. Start one `development_authority_state` map for that SHA.

Use bounded repository inventory to find likely planning, architecture, session/packet, handoff, acceptance, archive and CI/verify sources. Treat names and locations only as discovery hints.

Read only enough exact tracked content to establish explicit authority relationships. Record each supported relationship separately with `development_authority_state_record_edge`, including a bounded locator that states where the relationship is actually asserted. Use `CONFIRMED` only for explicit repository evidence; otherwise `PROBABLE` or `UNPROVEN`.

Pay special attention to explicit source-of-truth, current-scope, supersedes/archive, predecessor, allowed/excluded path and acceptance-language statements. Do not revive superseded material or promote supporting current-state evidence into planning authority.

Treat these as hard semantic invariants: accepted predecessor and adjacent parallel track are mutually exclusive for the same semantic entity; historical or superseded material cannot be an accepted predecessor; active scope cannot simultaneously be historical, forbidden, or adjacent. If exact repository evidence genuinely asserts incompatible roles, preserve both evidence records and stop for operator adjudication rather than choosing whichever wording looks newer or more persuasive.

Load the completed map. `development_authority_state_load` must fail closed on contradictory confirmed roles. If it returns `AUTHORITY RELATION CONTRADICTION`, stop for operator adjudication. Do not call `development_authority_state_start` to mint a replacement map; that contradiction is latched until `operatorAdjudication.decision = SUPERSEDE_CONTRADICTION` is recorded. If canonical planning authority or the active implementation scope cannot be confirmed from repository evidence, return `SCOPE_AUTHORITY_UNPROVEN` with the competing/unproven relationships. Do not resolve ambiguity by prose quality, recency, filename or model preference.
