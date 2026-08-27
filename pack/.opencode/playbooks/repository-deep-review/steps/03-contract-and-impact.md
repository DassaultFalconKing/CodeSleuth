# Step: contract and impact

Consume `target_identity` and `review_map`. For a PR/diff, resolve registry seeds and reverse dependency closure. For broad review, query only contracts relevant to mapped components.

Use `protected-capability-registry` for exact record lookup, `contract-triangulation` for material contract meaning, and `dependency-impact-closure` for changed-path impact. Do not edit the registry in read-only review mode.

Return `contract_impact`: matched contract ids, drift classifications, affected closure, relevant `FR-*` ids, and exact evidence locations that the next Step must verify.
