# Step: collect documentation evidence

Use exact target identity and deterministic inventory. Bound the requested documentation scope into components, then use `repository-deep-review` on each relevant slice. For public/normative behavior, use `contract-triangulation` so code, docs, and executable tests are compared instead of silently choosing one.

Return a compact `documentation_evidence` packet: purpose/boundaries, architecture, important flows, configuration, integrations, persistence, build/test/deployment paths, exact provenance, and explicit contradictions/unknowns. Do not draft the final document in this Step.
