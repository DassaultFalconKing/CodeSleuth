# Step: select candidate

Use `candidate_identity` from the Playbook request and the prior Step outputs as needed.

Load `exact-target-identity` and `eha-candidate-selection`. For a trusted GitHub EHA bridge request, run only `python scripts/eha_candidate_status.py` and use its bounded JSON output. Do not enumerate the persistence root or inspect local convenience branches. Otherwise resolve the active `dev/release-X.Y.Z` literal head SHA and verify the checkout's literal `git rev-parse HEAD` equals that selected SHA.

Record release branch ref, selected exact SHA, branch, and dirty state. Do not substitute a PR head, repair branch, synthetic merge ref, or tree-equivalent commit.

Return only `candidate_identity`: selected SHA, release branch, dirty state, and selection provenance.
