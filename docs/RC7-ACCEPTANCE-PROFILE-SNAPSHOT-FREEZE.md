# RC7 Acceptance Profile Snapshot Freeze

**Status:** NORMATIVE RC7 MICRO-FREEZE  
**Session:** MF2 — `ProjectSibProfileV1` / `AcceptanceProfileSnapshotV1`  
**Scope:** design/contract only; no production implementation  
**Freeze branch:** `docs/rc7-freeze-acceptance-profile`

This document freezes W7 tightly enough for tests-first implementation. It does not reopen RC6, SIB, EHA, protected-capability or EBCA authority semantics.

---

# 1. Exact inputs

All refs were re-resolved before the freeze.

| Input | Resolved identity | Role |
| --- | --- | --- |
| runtime branch | `feature/rc6-eha-brownfield-bootstrap` | executable evidence only |
| runtime HEAD | `1de37c75251a1e0d9904cffdb82695e92e3fab23` | unchanged from handoff |
| planning branch | `docs/rc7-ledger-authority-repair-plan` | design input |
| planning HEAD | `86218a51345fafb47d0ffec543773846a70ac76a` | unchanged from handoff; freeze base |
| pinned review / antithesis | `be5d158880f649ecb568d9a505c694e87bd76e0e` | adversarial design input |
| frozen thesis | `1b52c7c72e5294b3a4c145d1bbbd71a1863cb218` | thesis input only, not implementation authority |

The planning branch had not advanced, so no later planning commit was substituted.

Material source identities:

| Source | Exact blob/object identity |
| --- | --- |
| `docs/EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md` | `232795994607b09016481846520b9c82554be5eb` |
| `docs/EXACT-HEAD-ACCEPTANCE.md` | `3d7ed676c7bea505c3fd75eb921c5fa3d59d6078` |
| `docs/STABLE-INTEGRATION-BASELINE.md` | `866be71e14115cb214419a65388d405079a6be89` |
| `docs/SIB0-CAPABILITY-INVENTORY.md` | `c5c8d87d7d2dcd5f50eab3f76b323c3ca75dbb3b` |
| `docs/PROTECTED-CAPABILITY-CONTRACTS.md` | `1e14a26062dc562eef28d84b023539de1d0086a6` |
| `docs/protected-capabilities.json` | `9258c070d1af3b5ec0706c905439643aebf929c0` |
| `docs/EHA-OPERATING-PLAYBOOK.md` | `8dc68e3f5cfe97bc537cf68d4c8cad373e0b69aa` |
| `docs/PROVENANCE-WATERMARK.md` | `2e2b3927659a407a4aed0404223e69085fe56e5a` |
| `docs/RC7-SIB-EHA-MATURITY-LOOPS.md` | `47cb0f358c8043e7e83bb3f32e8586158372f0b9` |
| `docs/RC7-EBCA-GAP-PLAN.md` | `bbd30ef76be22e040ce320e2673eb0a58e16a3f3` |
| `docs/RC7-THESIS-ANTITHESIS-SYNTHESIS.md` | `a3556ca3bd84546835a3ff66847cfb03da54fc7b` |
| runtime `pack/.opencode/tools/eha_state.ts` | `7a07f6c9ad2e34ef014a39cc9076d71a865ec2c7` |
| runtime `pack/.opencode/tools/provenance_state.ts` | `9aabd37d452740373984da8c865a58325eb82d6f` |

The thesis remains historical thesis. The synthesis remains a design input. Accepted runtime/EBCA/SIB/EHA contracts retain authority where wording differs.

---

# 2. Inherited invariants

The following are preserved unchanged.

## 2.1 Acceptance identity

```text
acceptance identity =
  exact subject SHA
  + profile identity
  + required gates / environments
  + concrete run / result identity
```

A snapshot digest is not a run identity. A run ID is not a profile identity. These axes MUST remain separately inspectable.

## 2.2 Exact-head acceptance

Acceptance belongs only to the exact tested Git subject. It does not transfer through branch names, ancestry, rebases, squashes, cherry-picks, tree equality or later worktrees.

## 2.3 SIB semantics

- SIB0 remains architectural completeness for one architecture generation.
- SIB1 remains implementation completeness for that frozen architecture.
- SIB2 remains integration completeness for the exact composed candidate.
- Claimability remains cumulative on one exact subject.

A project profile supplies project-specific obligations, gates and environments; it MUST NOT redefine SIB0/SIB1/SIB2 into different maturity stages.

## 2.4 Existing authorities

- `eha.ndjson` remains EHA campaign/verdict authority.
- `docs/protected-capabilities.json` remains CodeSleuth protected-capability registry authority.
- `AcceptanceProfileSnapshotV1` is immutable campaign input, not an acceptance ledger or verdict authority.
- provenance watermark/session attribution remains metadata and MUST NOT participate in SIB claimability.

---

# 3. Exactly one acceptance-policy owner

There MUST be exactly one upstream owner of SIB/acceptance policy for one profile.

```text
NATIVE_BOUND
    project-native acceptance/architecture policy owns meaning
    ProjectSibProfileV1 binds/maps it

ADOPTED_POLICY
    explicitly adopted ProjectSibProfileV1 owns project-local policy
    tracked adoption decision activates it

Either mode
    -> validate / compile
    -> immutable AcceptanceProfileSnapshotV1
    -> EHA campaign
```

There is no independently editable RC7 `AcceptanceProfileV1` policy object.

## 3.1 `NATIVE_BOUND`

`NATIVE_BOUND` means:

1. project-native tracked architecture/acceptance authorities remain the policy owner;
2. `ProjectSibProfileV1` is a typed binding into SIB obligations/gates/environments and does not replace native canon;
3. policy-bearing profile items MUST be sourced to declared native authority;
4. contradictory, absent or ambiguous native authority blocks compilation;
5. changing exact native authority content changes compiled profile identity even when the binding document is unchanged.

A native-bound binding MUST NOT invent a requirement merely because a model considers it reasonable.

## 3.2 `ADOPTED_POLICY`

`ADOPTED_POLICY` means:

1. explicit project/maintainer adjudication adopts the exact normalized profile body as project-local policy for one repository and architecture generation;
2. before adoption the body is only a proposal and MUST NOT compile to campaign input;
3. after adoption the profile body is the acceptance-policy owner;
4. changing a policy-bearing profile field changes its body digest and requires a new matching adoption before campaign use;
5. adoption creates current policy authority; it does not retroactively prove that discovery was exhaustive.

## 3.3 Adoption assertion

The profile names one `adoptionDecisionAuthorityId`. That locator MUST be kind `ADOPTION_DECISION` and MUST resolve at the exact target SHA to a tracked JSON file whose complete parsed content is:

```text
ProjectSibProfileAdoptionV1 {
  schemaVersion: "ProjectSibProfileAdoptionV1"
  decisionId: IdV1
  repositoryId: IdV1
  projectSibProfileId: IdV1
  profileVersion: ProfileVersionV1
  profileBodyDigest: DigestV1
  architectureGenerationId: IdV1
  decision: "ADOPTED"
}
```

The assertion MUST match the profile on repository ID, profile ID, profile version, body digest and architecture-generation ID. Mismatch is `ADOPTION_BINDING_MISMATCH`.

This assertion records adoption authority; it does not duplicate the policy body.

---

# 4. Canonical primitive contracts

## 4.1 IDs

```text
IdV1 = ^[a-z0-9][a-z0-9._:/-]{0,127}$
ProfileVersionV1 = ^[a-z0-9][a-z0-9._+-]{0,63}$
GitShaV1 = ^[0-9a-f]{40}$
DigestV1 = ^sha256:[0-9a-f]{64}$
ConstraintKeyV1 = ^[a-z0-9][a-z0-9._-]{0,127}$
```

IDs are ASCII lowercase. Uppercase/abbreviated values are invalid, not silently case-folded into validity.

A profile-version change is an identity change even if the editor claims no semantic change.

## 4.2 Repository identity

`repositoryId` is an explicit project-authority-assigned stable `IdV1`. It is not derived ad hoc from a mutable branch or current remote URL.

A clone preserves project identity. A fork under independent project authority must establish its own repository/profile policy instead of inheriting acceptance through ancestry.

## 4.3 Repository path

`RepositoryPathV1`:

- repository-root relative;
- `/` separators only;
- no leading/trailing `/`;
- no empty, `.` or `..` segment;
- no U+0000..U+001F or U+007F;
- Unicode NFC.

Path normalization MUST NOT resolve host filesystem symlinks. Authority resolution is against the exact Git tree.

## 4.4 Human statements

`HumanStatementV1` normalization:

1. Unicode NFC;
2. replace every Unicode whitespace run with one ASCII space;
3. trim surrounding ASCII space;
4. reject empty result and C0/C1 control characters.

## 4.5 Constraint values

Constraint values are Unicode NFC, case-sensitive, have no leading/trailing Unicode whitespace, and contain no U+0000..U+001F or U+007F. Internal whitespace is preserved.

---

# 5. `ProjectSibProfileV1` exact schema

The upstream profile contains **no editable digest field**. Identity is calculated from canonical content.

```text
ProjectSibProfileV1 {
  schemaVersion: "ProjectSibProfileV1"
  projectSibProfileId: IdV1
  profileVersion: ProfileVersionV1
  repositoryId: IdV1
  architectureGenerationId: IdV1
  authorityMode: "NATIVE_BOUND" | "ADOPTED_POLICY"
  sourcePolicy: NativeSourcePolicyV1 | AdoptedSourcePolicyV1
  authorityLocators: AuthorityLocatorV1[]
  policyRequirements: PolicyRequirementV1[]
  obligations: AcceptanceObligationV1[]
  gates: GateRequirementV1[]
  environments: EnvironmentRequirementV1[]
  materialTools: ToolRequirementV1[]
  materialRuntimes: RuntimeRequirementV1[]
  coverageRequirements: CoverageRequirementsV1
  aggregationPolicy: AggregationPolicyV1
  candidateSelectionAuthorityIds: IdV1[]
  promotionAuthorityIds: IdV1[]
  architectureReopenAuthorityIds: IdV1[]
  repairPolicyAuthorityIds: IdV1[]
  assumptions: PolicyStatementV1[]
  limitations: PolicyStatementV1[]
  unresolvedPolicyItems: PolicyStatementV1[]
}
```

Every member is required. Unknown members and JSON `null` are invalid.

## 5.1 Required collection cardinality

| Field | V1 cardinality |
| --- | --- |
| `authorityLocators` | non-empty |
| `policyRequirements` | non-empty |
| `obligations` | non-empty; each SIB level has >= 1 `REQUIRED` obligation |
| `gates` | non-empty |
| `environments` | non-empty |
| `materialTools` | may be empty |
| `materialRuntimes` | may be empty |
| `coverageRequirements.capabilityClassIds` | non-empty |
| `coverageRequirements.protectedContractIds` | may be empty |
| `coverageRequirements.policyRequirementIds` | non-empty |
| `candidateSelectionAuthorityIds` | non-empty |
| `promotionAuthorityIds` | non-empty |
| `architectureReopenAuthorityIds` | non-empty |
| `repairPolicyAuthorityIds` | non-empty |
| `assumptions` | may be empty |
| `limitations` | may be empty |
| `unresolvedPolicyItems` | may be non-empty in proposal form; MUST be empty to compile a snapshot |

## 5.2 Source-policy union

For `NATIVE_BOUND`:

```text
NativeSourcePolicyV1 {
  nativeAuthorityIds: IdV1[]   // non-empty
}
```

For `ADOPTED_POLICY`:

```text
AdoptedSourcePolicyV1 {
  adoptionDecisionAuthorityId: IdV1
}
```

The top-level `authorityMode` determines the legal union arm. There is no mode inference or fallback.

## 5.3 Authority locators and resolved refs

```text
AuthorityLocatorV1 {
  authorityId: IdV1
  kind:
    "ARCHITECTURE_POLICY"
    | "ACCEPTANCE_POLICY"
    | "GATE_DEFINITION"
    | "ENVIRONMENT_POLICY"
    | "CAPABILITY_REGISTRY"
    | "CANDIDATE_SELECTION_POLICY"
    | "PROMOTION_POLICY"
    | "ARCHITECTURE_REOPEN_POLICY"
    | "REPAIR_POLICY"
    | "ADOPTION_DECISION"
  path: RepositoryPathV1
}

ResolvedAuthorityRefV1 {
  authorityId: IdV1
  kind: <same enum>
  repositoryId: IdV1
  path: RepositoryPathV1
  blobSha: GitShaV1
}
```

`authorityId` is unique. At compilation every locator MUST resolve at `target.subjectSha` to a Git blob in the same `repositoryId`.

Reference-kind constraints:

- `adoptionDecisionAuthorityId` -> `ADOPTION_DECISION`;
- `candidateSelectionAuthorityIds` -> `CANDIDATE_SELECTION_POLICY`;
- `promotionAuthorityIds` -> `PROMOTION_POLICY`;
- `architectureReopenAuthorityIds` -> `ARCHITECTURE_REOPEN_POLICY`;
- `repairPolicyAuthorityIds` -> `REPAIR_POLICY`.

## 5.4 Policy requirements

```text
PolicyRequirementV1 {
  policyRequirementId: IdV1
  statement: HumanStatementV1
  sourceAuthorityIds: IdV1[]
}
```

In `NATIVE_BOUND`, `sourceAuthorityIds` is non-empty and intersects `sourcePolicy.nativeAuthorityIds`.

In `ADOPTED_POLICY`, it may be empty because the adopted profile body itself owns the statement; any listed IDs must resolve.

## 5.5 Acceptance obligations

```text
AcceptanceObligationV1 {
  obligationId: IdV1
  sibLevel: "SIB0" | "SIB1" | "SIB2"
  property: HumanStatementV1
  applicability: "REQUIRED" | "NOT_APPLICABLE"
  sourceAuthorityIds: IdV1[]
  policyRequirementIds: IdV1[]
  gateIds: IdV1[]
  environmentIds: IdV1[]
  capabilityClassIds: IdV1[]
  protectedContractIds: IdV1[]
  notApplicableRationaleAuthorityIds: IdV1[]
}
```

Rules:

- `policyRequirementIds` is non-empty;
- `capabilityClassIds` may be empty for an obligation, but profile-level capability coverage remains non-empty;
- `protectedContractIds` may be empty;
- a `REQUIRED` obligation has >=1 gate and >=1 environment and has empty N/A rationale refs;
- a `NOT_APPLICABLE` obligation has empty gate/environment lists and >=1 N/A rationale authority ref;
- unavailable evidence/environment is never N/A;
- in `NATIVE_BOUND`, `sourceAuthorityIds` is non-empty and intersects the native owner set;
- all references exist.

## 5.6 Gates

```text
GateRequirementV1 {
  gateId: IdV1
  gateKind: "EXECUTABLE" | "AUTHORITY_CHECK"
  sourceAuthorityIds: IdV1[]
  environmentIds: IdV1[]
  toolRequirementIds: IdV1[]
  runtimeRequirementIds: IdV1[]
}
```

Rules:

- `sourceAuthorityIds` is non-empty;
- `environmentIds` is non-empty;
- all referenced gate/environment pairs are required, not alternatives;
- `toolRequirementIds` / `runtimeRequirementIds` may be empty;
- every gate MUST be referenced by at least one `REQUIRED` obligation; unused gates are invalid profile noise.

W7 freezes stable gate identity/requirements. Host-specific command construction/execution belongs downstream; concrete run/result identity remains EHA evidence.

## 5.7 Environments

```text
EnvironmentRequirementV1 {
  environmentId: IdV1
  sourceAuthorityIds: IdV1[]
  constraints: DimensionConstraintV1[]
}
```

- `constraints` may be empty;
- in `NATIVE_BOUND`, `sourceAuthorityIds` is non-empty and intersects native authority;
- in `ADOPTED_POLICY`, `sourceAuthorityIds` may be empty;
- every environment MUST be referenced by a gate or `REQUIRED` obligation.

## 5.8 Material tools/runtimes

```text
ToolRequirementV1 {
  toolRequirementId: IdV1
  toolId: IdV1
  sourceAuthorityIds: IdV1[]
  constraints: DimensionConstraintV1[]
}

RuntimeRequirementV1 {
  runtimeRequirementId: IdV1
  runtimeId: IdV1
  sourceAuthorityIds: IdV1[]
  constraints: DimensionConstraintV1[]
}
```

An entry has >=1 constraint. In `NATIVE_BOUND`, `sourceAuthorityIds` is non-empty and intersects native authority; in `ADOPTED_POLICY` it may be empty.

These are policy constraints. The exact identity observed during execution is separate W6 evidence.

## 5.9 Dimension constraints

```text
DimensionConstraintV1 {
  key: ConstraintKeyV1
  operator: "EQUALS" | "ONE_OF"
  values: string[]
}
```

- values non-empty;
- `EQUALS` has exactly one value;
- `ONE_OF` has >=1 value;
- V1 has no ranges, regexes or arbitrary expressions.

Needing richer constraint semantics requires a future schema version, not local interpretation.

## 5.10 Coverage requirements

```text
CoverageRequirementsV1 {
  capabilityClassIds: IdV1[]
  protectedContractIds: IdV1[]
  policyRequirementIds: IdV1[]
}
```

Compiler invariant:

```text
union(obligations.capabilityClassIds)
  ⊇ coverageRequirements.capabilityClassIds

union(obligations.protectedContractIds)
  ⊇ coverageRequirements.protectedContractIds

union(obligations.policyRequirementIds)
  ⊇ coverageRequirements.policyRequirementIds
```

Failure is `PROFILE_COVERAGE_GAP`.

This is required **policy coverage**, not an evidence-derived completeness verdict.

## 5.11 Aggregation policy

The V1 value is fixed and MUST equal exactly:

```text
AggregationPolicyV1 {
  requiredObligationRule: "ALL_REQUIRED"
  environmentMatrixRule: "ALL_REFERENCED_GATE_ENVIRONMENT_PAIRS"
  notApplicableRule: "AUTHORITY_RATIONALE_REQUIRED"
  missingEvidenceRule: "NON_PASS"
  cumulativeSibRule: "SIB0_SIB1_SIB2_SAME_SUBJECT"
  durableCompletionRule: "CAMPAIGN_COMPLETED_REQUIRED"
}
```

A different aggregation algorithm needs a future schema version. RC7 V1 does not permit majority-vote, best-effort or model-discretion acceptance.

## 5.12 Policy statements

```text
PolicyStatementV1 {
  statementId: IdV1
  text: HumanStatementV1
  sourceAuthorityIds: IdV1[]
}
```

Assumptions and limitations are semantic and participate in identity.

In `NATIVE_BOUND`, non-empty `assumptions`/`limitations` entries require native source authority. In `ADOPTED_POLICY`, they may be owned directly by the adopted profile and therefore may have an empty source list.

Any non-empty `unresolvedPolicyItems` blocks snapshot compilation with `PROFILE_POLICY_UNRESOLVED`.

---

# 6. Profile identity algorithm

Profile identity is content-derived. A filename, branch name or legacy free-form `profile` string is not identity.

## 6.1 `profileBodyDigest`

After exact-schema validation, normalization and canonical ordering:

```text
profileBodyDigest =
  "sha256:" + lowercase_hex(
    SHA256(
      UTF8("codesleuth:project-sib-profile-body:v1\n")
      || canonicalProjectSibProfileJson
    )
  )
```

`schemaVersion` participates.

## 6.2 Resolve source-policy identity

For `NATIVE_BOUND` resolve all `nativeAuthorityIds` against the exact target tree and build:

```text
ResolvedSourcePolicyIdentityV1 {
  authorityMode: "NATIVE_BOUND"
  nativeAuthorityRefs: ResolvedAuthorityRefV1[]
}
```

For `ADOPTED_POLICY`, resolve and validate the adoption assertion and build:

```text
ResolvedSourcePolicyIdentityV1 {
  authorityMode: "ADOPTED_POLICY"
  adoptionDecisionRef: ResolvedAuthorityRefV1
  adoptionAssertion: ProjectSibProfileAdoptionV1
}
```

## 6.3 `profileDigest`

Canonicalize:

```text
AcceptanceProfileIdentityV1 {
  schemaVersion: "AcceptanceProfileIdentityV1"
  profileBodyDigest: DigestV1
  sourcePolicyIdentity: ResolvedSourcePolicyIdentityV1
}
```

Then:

```text
profileDigest =
  "sha256:" + lowercase_hex(
    SHA256(
      UTF8("codesleuth:acceptance-profile-identity:v1\n")
      || canonicalAcceptanceProfileIdentityJson
    )
  )
```

Consequences:

- unchanged policy on a different candidate can retain the same `profileDigest`;
- changed native owner blob changes `profileDigest`;
- changed adopted profile body invalidates old adoption and cannot retain profile identity;
- changed profile version, obligations, gates, required environments, assumptions or limitations changes body/profile identity.

`profileDigest` is the normative profile-identity component of acceptance identity.

---

# 7. `AcceptanceProfileSnapshotV1` exact schema

```text
AcceptanceProfileSnapshotV1 {
  schemaVersion: "AcceptanceProfileSnapshotV1"
  profileIdentity: ProfileIdentityV1
  sourcePolicyIdentity: ResolvedSourcePolicyIdentityV1
  target: SnapshotTargetV1
  authorityRefs: ResolvedAuthorityRefV1[]
  policyRequirements: PolicyRequirementV1[]
  obligations: AcceptanceObligationV1[]
  gates: GateRequirementV1[]
  environments: EnvironmentRequirementV1[]
  materialTools: ToolRequirementV1[]
  materialRuntimes: RuntimeRequirementV1[]
  coverageRequirements: CoverageRequirementsV1
  aggregationPolicy: AggregationPolicyV1
  assumptions: PolicyStatementV1[]
  limitations: PolicyStatementV1[]
  semanticDigest: DigestV1
}
```

```text
ProfileIdentityV1 {
  projectSibProfileId: IdV1
  profileVersion: ProfileVersionV1
  architectureGenerationId: IdV1
  authorityMode: "NATIVE_BOUND" | "ADOPTED_POLICY"
  profileBodyDigest: DigestV1
  profileDigest: DigestV1
}

SnapshotTargetV1 {
  repositoryId: IdV1
  subjectSha: GitShaV1
}
```

The snapshot copies normalized policy requirements, obligations, gates, environments, material tool/runtime constraints, coverage requirements, aggregation policy, assumptions and limitations from the accepted profile.

`authorityRefs` contains one resolved ref for **every** `authorityLocator`, sorted by `authorityId`. Every locator therefore has exact target-tree blob evidence.

Branch/ref names MUST NOT appear in the snapshot.

## 7.1 Completeness fields deliberately excluded

V1 MUST NOT contain evaluated fields such as:

```text
discoveryCompleteness
policyCompleteness
completenessSupportable
```

`coverageRequirements` says what policy requires coverage of. W8 owns evidence-derived `DiscoveryCompleteness` / `PolicyCompleteness` claims.

A later W8 conclusion may reference the profile/snapshot identity. It MUST NOT mutate a started campaign's snapshot.

---

# 8. Canonical serialization

Digest equality MUST NOT depend on host-language map order or JSON library defaults.

## 8.1 Validate before hash

Before hashing:

1. exact-schema project the object;
2. reject unknown fields;
3. reject absent required fields;
4. reject every JSON `null`;
5. normalize strings by declared type;
6. reject duplicate IDs/scalar values;
7. validate all references and cardinalities;
8. sort collections as below.

Malformed data is never hashed into apparent validity.

## 8.2 Object field ordering

Canonical JSON emits object members in the **exact declaration order of each type definition in this document**.

Input member order has no effect.

Top-level snapshot order is:

```text
schemaVersion
profileIdentity
sourcePolicyIdentity
target
authorityRefs
policyRequirements
obligations
gates
environments
materialTools
materialRuntimes
coverageRequirements
aggregationPolicy
assumptions
limitations
```

`semanticDigest` is omitted from its own preimage and emitted last in a stored/rendered snapshot.

Top-level profile order is the section-5 declaration order.

## 8.3 Collection ordering

| Collection | Canonical order |
| --- | --- |
| `authorityLocators`, `authorityRefs` | `authorityId` |
| `policyRequirements` | `policyRequirementId` |
| `obligations` | `obligationId` |
| `gates` | `gateId` |
| `environments` | `environmentId` |
| `materialTools` | `toolRequirementId` |
| `materialRuntimes` | `runtimeRequirementId` |
| policy-statement arrays | `statementId` |
| `DimensionConstraintV1[]` | `key`, then `operator`, then canonical joined `values` |
| arrays of `IdV1` | ASCII byte lexicographic |
| constraint `values` | normalized UTF-8 byte lexicographic |
| native authority refs | `authorityId` |

Duplicate IDs or duplicate scalar entries are errors, never silently deduplicated.

## 8.4 Exact JSON string escaping

Canonical JSON uses UTF-8, no BOM, no insignificant whitespace and no final newline.

String emission is exact:

- `"` is emitted as `\"`;
- `\` is emitted as `\\`;
- U+0008 -> `\b`;
- U+0009 -> `\t`;
- U+000A -> `\n`;
- U+000C -> `\f`;
- U+000D -> `\r`;
- other U+0000..U+001F -> `\u00xx` with lowercase hex;
- all other Unicode scalar values are emitted directly as UTF-8;
- `/` is never escaped as `\/`;
- non-ASCII characters are not replaced with `\uXXXX` escapes.

V1 semantic schemas forbid control characters in paths/constraint values and normalize human statements, so control escapes normally occur only if a future allowed string subtype explicitly permits them. The serializer behavior is nevertheless frozen to avoid cross-language ambiguity.

Surrogate code points are invalid Unicode input and MUST be rejected.

## 8.5 JSON tokens

- object punctuation: `{`, `}`, `:`, `,` with no spaces;
- arrays: `[`, `]`, `,` with no spaces;
- booleans are not used by V1 semantic types;
- JSON numbers are not used by V1 semantic types;
- JSON `null` is forbidden.

This removes number-format and truthy/null ambiguities across Python/TypeScript implementations.

---

# 9. Snapshot semantic digest

Construct the normalized snapshot with `semanticDigest` absent and calculate:

```text
semanticDigest =
  "sha256:" + lowercase_hex(
    SHA256(
      UTF8("codesleuth:acceptance-profile-snapshot:v1\n")
      || canonicalSnapshotJsonWithoutSemanticDigest
    )
  )
```

## 9.1 Included

Every legal snapshot field except `semanticDigest` itself participates, including:

- `schemaVersion`;
- profile/body/source-policy identity;
- repository ID and exact subject SHA;
- exact authority blob refs;
- obligations/gates/environments;
- material tool/runtime requirements;
- required capability/contract/policy coverage;
- aggregation policy;
- assumptions and limitations.

Any normalized change to these fields MUST change the snapshot digest.

## 9.2 Excluded volatile data

The only snapshot member excluded from its own preimage is `semanticDigest`.

Volatile data is excluded by being **illegal snapshot schema**, including:

```text
generatedAt / compiledAt / recordedAt
actor / user / model / watermark
host session ID / PID / hostname / cwd
branch or movable ref
workflow run/job ID
observed gate result / transport outcome
report path
renderer/template metadata
working-tree dirty state
```

Those belong to campaign/run/provenance evidence where applicable.

## 9.3 Absent/null/unknown

- absent required field -> invalid;
- `null` -> invalid;
- unresolved policy -> `ProjectSibProfileV1.unresolvedPolicyItems`, which blocks compilation;
- no generic `"UNKNOWN"` token exists in snapshot V1;
- execution outcomes such as `INCONCLUSIVE` / `UNAVAILABLE` are EHA result evidence, not snapshot placeholders.

## 9.4 Semantic equality

Two snapshots are semantically identical for V1 **iff their normalized digest preimages are byte-identical**.

Therefore object/collection input order and permitted Unicode/whitespace normalization do not change the digest; target, policy authority, gate, environment, assumption or limitation changes do.

This is the only V1 equality rule. Model judgment is not part of digest equality.

---

# 10. Deterministic compilation algorithm

```text
INPUT:
  exact repository context
  exact Git targetSha
  ProjectSibProfileV1

1. Parse exact schema.
2. Normalize lexical fields.
3. Reject unknown/missing/null/duplicate/dangling data.
4. Enforce collection cardinalities and reference-kind constraints.
5. Require unresolvedPolicyItems == [].
6. Require exact V1 aggregation policy.
7. Validate every SIB level has >=1 REQUIRED obligation.
8. Validate obligation -> gate -> environment/tool/runtime graph.
9. Validate coverageRequirements.
10. Compute profileBodyDigest.
11. Resolve every authorityLocator at targetSha.
12. Resolve exactly one policy owner:
      NATIVE_BOUND -> exact native authority refs;
      ADOPTED_POLICY -> exact matching adoption assertion.
13. Compute profileDigest.
14. Build normalized AcceptanceProfileSnapshotV1.
15. Sort all collections canonically.
16. Compute snapshot semanticDigest.
17. Canonicalize again and verify stored digest from the produced object.
18. Return snapshot.

ANY FAILURE:
  return deterministic error;
  return no campaign-ready snapshot;
  do not infer missing policy;
  do not fall back to legacy profile strings;
  mutate no source/EHA/registry state.
```

---

# 11. Deterministic errors / ambiguity behavior

| Error | Condition |
| --- | --- |
| `PROFILE_SCHEMA_UNSUPPORTED` | unknown schema version/union arm |
| `PROFILE_SCHEMA_INVALID` | missing/unknown/null/lexically invalid field |
| `PROFILE_DUPLICATE_ID` | duplicate ID or duplicate scalar in uniqueness domain |
| `PROFILE_DANGLING_REF` | referenced entity missing |
| `PROFILE_POLICY_UNRESOLVED` | unresolved policy items remain |
| `PROFILE_POLICY_OWNER_INVALID` | zero/multiple/mode-incompatible owner |
| `PROFILE_REFERENCE_KIND_INVALID` | authority ID used under wrong authority kind |
| `NATIVE_AUTHORITY_MISSING` | native owner authority cannot resolve at target |
| `NATIVE_BINDING_UNSOURCED` | native-bound policy-bearing item lacks native source |
| `ADOPTION_DECISION_MISSING` | adopted decision cannot resolve |
| `ADOPTION_BINDING_MISMATCH` | adoption assertion does not bind exact profile body |
| `AUTHORITY_BLOB_MISSING` | locator does not resolve to blob at target |
| `PROFILE_COVERAGE_GAP` | required coverage not mapped into obligations |
| `PROFILE_SIB_LEVEL_EMPTY` | SIB0/1/2 lacks a required obligation |
| `PROFILE_NOT_APPLICABLE_INVALID` | invalid N/A/rationale/gate combination |
| `PROFILE_AGGREGATION_INVALID` | V1 aggregation weakened/changed |
| `PROFILE_TARGET_INVALID` | invalid repository binding / target SHA |
| `SNAPSHOT_DIGEST_MISMATCH` | recomputed digest differs |
| `SNAPSHOT_IMMUTABLE` | mutation attempted after campaign binding |
| `LEGACY_CAMPAIGN_NO_SNAPSHOT` | V1 snapshot requested from legacy RC6 campaign |
| `LEGACY_CAMPAIGN_V2_APPEND_FORBIDDEN` | V2 snapshot semantics appended to legacy campaign |

Ambiguity is fail-closed. Multiple plausible owners, conflicting policy, uncertain N/A or missing environment semantics produce no snapshot. Implementation-local “best guess” behavior is forbidden.

---

# 12. Immutability

## 12.1 Freeze point

The snapshot MUST be fully compiled and digest-verified **before** `campaign_started` establishes a campaign.

At campaign start the semantic binding tuple is:

```text
exact target subjectSha
+ profileIdentity.profileDigest
+ snapshot semanticDigest
```

W6 owns the physical EHA V2 event/storage representation of this tuple; W7 freezes its semantics here.

## 12.2 After campaign start

After start, snapshot bytes, semantic digest, target SHA, profile identity, source-policy identity, gates and environments are immutable.

There is no “refresh campaign to current profile” operation.

## 12.3 Later profile/policy changes

```text
old campaign -> remains bound to old snapshot/profile
changed profile/source -> compiles new identity
current acceptance claim under changed policy -> new campaign
```

A historical campaign remains evidence for the exact subject/profile under which it ran; it does not become evidence for the newer profile.

## 12.4 Snapshot unavailable/corrupt

If a V1 campaign claims a snapshot digest but the corresponding snapshot cannot be loaded and verified, profile-aware claimability is not supportable from that evidence set. Reader MUST report missing/corrupt evidence and MUST NOT reconstruct the supposed historical snapshot from today's profile.

---

# 13. RC6 compatibility

Current RC6 campaign events have no snapshot V1 binding; verdicts carry only a free-form/string `profile` field.

RC7 reads them without rewriting.

## 13.1 Legacy reader classification

A campaign started under the RC6 event shape is derived/read as:

```text
campaignSchema = "RC6_LEGACY"
profileBinding = "LEGACY_UNBOUND"
acceptanceProfileSnapshot = unavailable
```

This is reader state only; it is not appended to the old ledger.

## 13.2 Preserve historical semantics

For legacy campaigns:

- preserve target SHA, scope, verdicts, repair history and completion exactly;
- render old verdict `profile` only as `legacyProfileLabel`;
- preserve historical RC6 claimability under the RC6 contract that produced it;
- do not recompute old verdicts using current profile policy.

RC6 PASS remains historical RC6 evidence for its exact subject. It does **not** acquire snapshot-V1 identity.

## 13.3 No retroactive upgrade

RC7 MUST NOT:

- synthesize `profileDigest` from an RC6 `profile` string;
- compile today's profile and attach it to an old campaign;
- infer unrecorded old gate/environment identity;
- rewrite old campaign/verdict events;
- append a V2 snapshot binding into an already-started RC6 campaign;
- label an RC6 campaign “snapshot bound”.

If a current V1/profile-aware acceptance claim is needed for the same source SHA, start a **new campaign** with a fresh snapshot.

Reader request for V1-only fields on RC6 yields explicit unavailable/legacy state. Writer request to mix V2 semantics into it fails `LEGACY_CAMPAIGN_V2_APPEND_FORBIDDEN`.

---

# 14. Adversarial examples

1. **Object keys reordered:** same digest.
2. **Obligation/gate/environment arrays reversed:** canonical sort; same digest.
3. **Duplicate obligation ID:** `PROFILE_DUPLICATE_ID`, no silent dedup.
4. **Only target SHA changes:** same `profileDigest`, different snapshot digest.
5. **Native policy blob changes:** different `profileDigest` and snapshot digest.
6. **Only actor/session/watermark/time changes:** no profile/snapshot digest effect because fields are outside schema.
7. **Only `profileVersion` changes:** new body/profile/snapshot identity.
8. **Adopted profile edited after adoption:** old assertion mismatches; no snapshot.
9. **Adoption assertion missing:** no campaign-ready adopted profile.
10. **NATIVE obligation has no native source:** `NATIVE_BINDING_UNSOURCED`.
11. **Runner unavailable and obligation marked N/A:** invalid unless policy authority explicitly supplies N/A rationale.
12. **Required protected-contract coverage has no obligation:** `PROFILE_COVERAGE_GAP`.
13. **Gate requires linux+windows but only linux executed:** profile remains incomplete; W6 cannot aggregate partial matrix to PASS.
14. **Profile changes during campaign:** old campaign remains on old digest; no refresh.
15. **RC6 profile string equals current profile ID:** still `LEGACY_UNBOUND`; no identity transfer.
16. **RC6 PASS and V1 snapshot exist for same SHA:** old PASS is not retroactively V1-bound; new V1 campaign required.
17. **Release branch moves A->B:** snapshot stays on exact A; branch is navigation only.
18. **NFC/whitespace-equivalent human statement:** same normalized digest.
19. **Constraint `3.12.7` -> `3.12.8`:** digest changes.
20. **Unknown `generatedAt` member injected:** exact-schema rejection.
21. **JSON serializer emits `\/` or `\u00e9` instead of required literal `/`/UTF-8:** non-canonical bytes; digest implementation test fails.
22. **Future schema passed to V1 reader:** `PROFILE_SCHEMA_UNSUPPORTED`, never “drop unknown fields and continue”.

---

# 15. Compatibility obligations

W7 implementation MUST preserve:

1. exact subject SHA as independent acceptance axis;
2. one acceptance-policy owner;
3. existing SIB0/SIB1/SIB2 meanings;
4. `eha.ndjson` as EHA authority;
5. existing protected-capability registry authority;
6. provenance/session attribution outside claimability/digest;
7. host execution ownership;
8. non-binary EHA evidence semantics: missing/INCONCLUSIVE/UNAVAILABLE cannot become PASS;
9. fresh campaign requirement after profile identity changes;
10. RC6 legacy readability without mutation;
11. fail-closed handling of unsupported future schema versions;
12. separate concrete run/result identity in EHA evidence.

`trusted_prestarted` versus `model_started` remains an EHA start-ownership concern; either path MUST bind the same immutable snapshot semantics before campaign start.

---

# 16. MUST / MUST NOT

## MUST

- resolve exactly one policy owner;
- compute body/profile/snapshot digests exactly as frozen;
- include every `schemaVersion` in its digest preimage;
- bind snapshot to `repositoryId + exact subjectSha`;
- resolve exact authority blobs at the target tree;
- freeze obligations/gates/environments/tool/runtime requirements before campaign start;
- use exact canonical ordering and string emission;
- reject unresolved policy;
- require authority-backed N/A;
- keep started campaigns immutable;
- read RC6 as legacy without upgrading it;
- keep actual gate/environment/run/result evidence separately inspectable.

## MUST NOT

- introduce a second editable acceptance-policy authority;
- infer profile identity from filename/free-form label;
- include provenance/timestamp/branch/run result in snapshot digest;
- infer missing native policy with model reasoning;
- equate discovery completeness with policy completeness;
- store evaluated completeness status in snapshot V1;
- use null/omission/`UNKNOWN` as policy semantics;
- silently deduplicate invalid input;
- mutate/refresh a started snapshot;
- retroactively attach V1 snapshot to RC6 campaign;
- treat partial environment matrix as full profile PASS;
- treat unavailable as N/A;
- depend on language-specific JSON serializer defaults.

---

# 17. Explicit non-goals

This freeze does not decide or implement:

- production W7 TypeScript/Python;
- physical persistence path for snapshot instances;
- exact EHA V2 event/storage field layout carrying the frozen binding tuple — W6 owns the physical schema;
- EHA V2 non-binary event serialization beyond inherited non-PASS rules;
- W8 `DiscoveryCompleteness` / `PolicyCompleteness` value model/evidence algorithm;
- W9 repair-attempt/termination digest;
- W10 repair-vs-ledger-recovery permissions;
- host/Jinja command rendering;
- generic policy expression/range/regex language;
- cross-repository policy authority in V1;
- Git SHA-256 object-format support in V1;
- generic attestation/signature infrastructure;
- retroactive RC6 ledger migration.

These are downstream ownership boundaries, not unresolved W7 semantics.

---

# 18. Tests-first contract for W7

Initial RED coverage can be written deterministically for:

1. exact schema and cardinalities;
2. NATIVE vs ADOPTED single-owner validation;
3. exact adoption-body binding;
4. authority path -> exact target blob resolution;
5. `profileBodyDigest` canonicalization;
6. source-policy-sensitive `profileDigest`;
7. snapshot digest canonicalization;
8. exact JSON escaping/UTF-8 golden vectors;
9. key/collection order invariance;
10. target-SHA-only change leaves profile digest and changes snapshot digest;
11. native policy blob change changes profile identity;
12. duplicate/dangling/kind-invalid refs;
13. coverage gaps;
14. invalid N/A;
15. unresolved policy compile block;
16. post-start immutability;
17. RC6 `LEGACY_UNBOUND` reading;
18. refusal to append/synthesize V1 into RC6 campaign;
19. exclusion of provenance/run/timestamp data from snapshot identity.

W7 tests MUST create and retain golden digest fixtures from the exact algorithms in this document. Once W7 ships, changing canonicalization, domain prefixes or digest preimages requires a new schema version; V1 MUST NOT be silently redefined.

---

# 19. Downstream workstreams unlocked

This freeze resolves the W7 decisions implementation would otherwise have to invent:

- one policy owner;
- exact `NATIVE_BOUND` / `ADOPTED_POLICY` semantics;
- exact adoption source assertion;
- exact ProjectSibProfile V1 schema/cardinalities;
- exact immutable snapshot V1 schema;
- profile-body/profile/snapshot digest algorithms;
- exact normalization, ordering, escaping, null/unknown behavior;
- target/policy/gate/environment identity separation;
- campaign immutability;
- RC6 reader compatibility/no-upgrade behavior.

Therefore it unlocks:

- **W7 ProjectSibProfile / AcceptanceProfileSnapshot** tests-first implementation;
- prerequisite profile/snapshot identity for **W6 EHA V2**;
- stable policy/coverage identity prerequisite for **W8 completeness**;
- stable profile-snapshot identity prerequisite for **W9 repair termination**.

---

# 20. Unresolved items

There are **no unresolved W7 semantic decisions** inside this micro-freeze.

Physical EHA V2 carriage, W8 completeness results, W9 termination and the other explicit non-goals remain downstream contracts. W7 can implement schema validation, authority resolution, compilation, canonicalization, digests, immutability binding and RC6 compatibility without choosing their semantics.

---

FREEZE STATUS:
FROZEN

UNLOCKS:
W7 ProjectSibProfile / AcceptanceProfileSnapshot
provides prerequisite for W6 EHA V2
provides prerequisite for W8 completeness
provides prerequisite for W9 repair termination
