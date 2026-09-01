# Select the active development scope

Load the exact `DevelopmentAuthorityMap` created by the prior Step. Do not rescan the repository broadly unless a recorded authority edge names a bounded unresolved dependency.

Select the currently admissible implementation scope only from `CONFIRMED` repository authority. Preserve:

- the canonical planning authority that selected it;
- explicit objective/work item/session identity;
- prerequisites;
- accepted predecessor(s);
- required reading;
- explicit allowed paths;
- exclusions and adjacent parallel tracks;
- blockers and operator decisions that prevent work from starting.

If more than one current scope is explicitly allowed in parallel, select only the scope requested by the user or the unique scope designated by repository authority. Do not merge parallel tracks into one larger scope.

If no unique admissible scope can be established, return `SCOPE_AUTHORITY_UNPROVEN`. Output a bounded `active_scope` structure for the next Steps; do not edit repository files and do not create a new roadmap/session packet.
