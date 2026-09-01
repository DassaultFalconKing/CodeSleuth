# Resolve repository development authority

Freeze the exact target from the prior Step. Start one `development_authority_state` map for that SHA.

Use bounded repository inventory to find likely planning, architecture, session/packet, handoff, acceptance, archive and CI/verify sources. Treat names and locations only as discovery hints.

Read only enough exact tracked content to establish explicit authority relationships. Record each supported relationship separately with `development_authority_state_record_edge`, including a bounded locator that states where the relationship is actually asserted. Use `CONFIRMED` only for explicit repository evidence; otherwise `PROBABLE` or `UNPROVEN`.

Pay special attention to explicit source-of-truth, current-scope, supersedes/archive, predecessor, allowed/excluded path and acceptance-language statements. Do not revive superseded material or promote supporting current-state evidence into planning authority.

Load the completed map. If canonical planning authority or the active implementation scope cannot be confirmed from repository evidence, return `SCOPE_AUTHORITY_UNPROVEN` with the competing/unproven relationships. Do not resolve ambiguity by prose quality, recency, filename or model preference.
