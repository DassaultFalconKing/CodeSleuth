# Step: triangulate matched contracts

For each matched contract that matters to the query/diff, invoke `contract-triangulation` independently against the exact target identity. Do not batch unrelated contracts into one invented compromise.

Return one row per contract: current contract statement, code/docs/test evidence, `AGREE` or drift classification, and whether registry maintenance is justified. In read-only mode, report drift without editing the manifest.
