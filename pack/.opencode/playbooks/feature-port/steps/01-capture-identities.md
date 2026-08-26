# Step: capture source and target identities

Resolve the exact source capability revision and exact target base revision separately using `exact-target-identity`. Record source repository/ref/SHA, target repository/ref/SHA, target dirty state, and whether either moved during analysis.

Do not create/populate a feature branch until both identities are proven. Return `IDENTITY_UNPROVEN` on ambiguity.
