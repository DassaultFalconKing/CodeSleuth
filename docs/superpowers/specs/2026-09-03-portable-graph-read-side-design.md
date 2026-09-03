# Portable Graph Read-Side Design

**Status:** RC6 implementation design
**Base:** `feature/rc6-eha-brownfield-bootstrap` @ `0ae58cb2dc06e3d06e0839040f58d5a853f920ee`

## Goal

Make model-facing graph reacquisition a bounded, renderer-neutral portable subsystem that CodeSleuth consumes through an adapter and that other projects such as Aleph_Rugent or Pii_Parcer can vendor without inheriting CodeSleuth persistence, authority, OpenCode, or ontology contracts.

## Boundaries

The portable core owns only in-memory graph validation and read operations:

- `describe`
- deterministic `resolve`
- bounded `neighbors`
- bounded `shortestPaths`
- `explain`
- bounded `diff`

It does **not** own persistence, evidence authority, Git freshness, graph construction, rendering, model routing, or writes.

CodeSleuth remains responsible for loading and validating `RepositoryContextProjection`, exact-HEAD/stale-SourceRef checks, mapping projection nodes/edges into the portable graph shape, and returning the existing derived/non-authoritative policy envelope.

## Portable graph shape

The core accepts arbitrary string node kinds, edge relations, origins, optional source references, and metadata. IDs are caller-owned opaque identities. The resolver may match an ID only by exact equality; it must never semantically rerank hash-like or opaque IDs. Fuzzy lookup is limited to deterministic key/label prefix and substring matching.

## Boundedness

All expansion surfaces have hard bounds. Neighborhood pagination uses an opaque graph-bound cursor. A cursor from another graph revision fails closed. Returned edge endpoints always fit inside the returned node bound; no edge may reference an omitted node. Shortest-path search has hop, path-count, and expansion caps.

## CodeSleuth adapter

`context_graph_read.ts` loads through the existing canonical `repo_context_graph_load` tool, rejects current reads when the projection is not exact-head/fresh, maps the projection into the portable shape, and exposes read-only OpenCode tools. Historical `diff` is allowed only for explicit projection IDs and reports freshness for both sides instead of pretending the old projection is current authority.

The older `repo_context_graph_query` and Mermaid surfaces remain compatibility interfaces for RC6. New model reacquisition should prefer the portable-reader-backed tools; no accepted writer or projection identity contract changes in this slice.

## Second portable component

The deterministic provenance watermark algorithm is extracted into `pack/.opencode/lib/portable/provenance_watermark.py`. The portable implementation requires an explicit domain separator. `scripts/provenance_watermark.py` remains the CodeSleuth adapter and supplies `codesleuth-provenance-v1`, preserving all existing values and CLI behavior.

## Portable tools index

`docs/PORTABLE-TOOLS.md` is the repository index. `pack/.opencode/lib/portable/README.md` is the vendorable package index. Entries distinguish ready portable code from candidates that still have CodeSleuth/runtime coupling.

## Acceptance

The change is acceptable only if:

1. the pure graph-reader smoke test passes without `@opencode-ai/plugin` or CodeSleuth state;
2. CodeSleuth graph-reader integration rejects stale current projections;
3. resolver behavior does not fuzzy-match opaque IDs;
4. neighborhood results never contain dangling edges and respect hard bounds/cursor identity;
5. existing CodeSleuth provenance watermark values remain byte-for-byte compatible;
6. the new Bun smoke is reachable from the default `package.json` test umbrella;
7. the PR is compared against the then-current RC6 target and classified CLEAN or REFIT REQUIRED.
