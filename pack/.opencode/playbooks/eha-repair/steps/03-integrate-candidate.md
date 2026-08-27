# Step: integrate candidate

Use `repair_result`. Integrate the repair through the active `dev/release-X.Y.Z` branch and capture the resulting literal release-stream head SHA.

If integration creates a merge commit, that merge commit is the next EHA target. Tree equality with the repair commit does not transfer evidence. Start no new EHA campaign in this Step; return the next candidate identity only.

Return only `next_candidate`: integrated release-stream branch, exact head SHA, and predecessor campaign ID.
