# RC7 Acceptance Profile Snapshot Freeze

**Status:** NORMATIVE RC7 MICRO-FREEZE  
**Session:** MF2 — `ProjectSibProfileV1` / `AcceptanceProfileSnapshotV1`  
**Scope:** design/contract only; no production implementation  
**Freeze branch:** `docs/rc7-freeze-acceptance-profile`

This document freezes the W7 policy/profile and immutable acceptance-snapshot contract tightly enough for tests-first implementation. It does not reopen RC6, SIB, EHA, protected-capability, or EBCA authority semantics.

---

## 1. Exact inputs

All refs were re-resolved before this freeze.

| Input | Resolved identity | Role |
| --- | --- | --- |
| runtime branch | `feature/rc6-eha-brownfield-bootstrap` | executable evidence only |
| runtime HEAD | `1de37c75251a1e0d9904cffdb82695e92e3fab23` | unchanged from handoff |
| planning branch | `docs/rc7-ledger-authority-repair-plan` | design input |
| planning HEAD | `86218a51345fafb47d0ffec543773846a70ac76a` | unchanged from handoff; freeze base |
| pinned review / antithesis | `be5d158880f649ecb568d9a505c694e87bd76e0e` | adversarial design input |
| frozen thesis | `1b52c7c72e5294b3a4c145d1bbbd71a1863cb218` | thesis input only, not implementation authority |

The planning branch had **not** advanced at freeze time, so no later planning commit was substituted.

Material source identities used by this freeze:

| Source | Exact blob / object identity |
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

The frozen thesis remains historical thesis. The synthesis is a design input. Where either conflicts with already accepted runtime/EBCA/SIB/EHA contracts, the accepted contracts win.

---

## 2. Preserved invariants

This freeze preserves, rather than redefines, the following accepted rules.

### 2.1 Acceptance identity

The minimum acceptance identity remains:

```text
exact subject SHA
+ profile identity
+ required gates / environments
+ concrete run / result identity
```

`AcceptanceProfileSnapshotV1.semanticDigest` is **not** allowed to erase those axes. In particular, a snapshot digest is not a run identity and a run ID is not a profile identity.

### 2.2 Exact-head acceptance

Acceptance belongs to the exact tested Git subject. It does not transfer through ancestry, branch names, rebases, cherry-picks, tree equality, or a later worktree.

### 2.3 SIB semantics

- SIB0 remains architectural completeness for the declared architecture generation.
- SIB1 remains implementation completeness for that frozen architecture.
- SIB2 remains integration completeness for the exact composed candidate.
- SIB claimability remains cumulative on one exact subject.

A project profile supplies project-specific obligations, gates and environments. It MUST NOT redefine the meaning of SIB0/SIB1/SIB2.

### 2.4 EHA authority

Existing `eha.ndjson` remains the EHA domain authority. `AcceptanceProfileSnapshotV1` is immutable campaign input, not a new acceptance ledger and not a verdict authority.

### 2.5 Protected capability authority

`docs/protected-capabilities.json` remains the protected-capability registry authority for CodeSleuth. A snapshot may bind protected contract IDs as required coverage, but it MUST NOT duplicate or supersede the registry's lifecycle or forbidden-regression authority.

### 2.6 Provenance is not claimability

Actor/session attribution, watermark, `recordedAt`, host session identity and similar provenance metadata remain useful metadata but MUST NOT participate in profile or snapshot semantic identity.

---

# 3. Normative decision: exactly one policy owner

There MUST be exactly one upstream owner of project SIB/acceptance policy for one `ProjectSibProfileV1`.

```text
NATIVE_BOUND
    project-native policy authority owns meaning
    ProjectSibProfileV1 binds/maps it

ADOPTED_POLICY
    explicitly adopted ProjectSibProfileV1 owns project-local policy
    adoption decision activates that authority

Either mode
    -> validate / compile
    -> immutable AcceptanceProfileSnapshotV1
    -> EHA campaign
```

There is no independently editable `AcceptanceProfileV1` policy authority in RC7.

## 3.1 `NATIVE_BOUND`

`NATIVE_BOUND` means:

1. project-native tracked architecture/acceptance authorities remain the policy owner;
2. `ProjectSibProfileV1` is a typed binding/mapping of those authorities into SIB obligations, gates and environments;
3. the profile MUST NOT silently add, remove, weaken or reinterpret a required native obligation;
4. every policy-bearing `policyRequirement`, `obligation`, assumption or limitation in the profile MUST carry at least one `sourceAuthorityId` that resolves to a declared native authority;
5. changing the exact native authority content changes the compiled profile identity even when the binding file itself is unchanged;
6. contradiction or missing native authority is a compile failure, never permission to let the binding file become substitute canon.

`NATIVE_BOUND` therefore means **bind, do not replace**.

## 3.2 `ADOPTED_POLICY`

`ADOPTED_POLICY` means:

1. an explicit project/maintainer adjudication adopts this exact `ProjectSibProfileV1` semantic body as project-local policy for the declared `repositoryId` and `architectureGenerationId`;
2. before adoption, the same body is only a proposal and MUST NOT compile into a campaign snapshot;
3. after adoption, the profile body is the policy owner; supporting code/docs/tests remain evidence and may still expose drift, but they do not form a second independently editable acceptance policy;
4. adoption MUST be bound to the profile's exact normalized body digest through a tracked adoption decision;
5. modifying any policy-bearing profile field after adoption produces a new body digest and requires a new adoption decision before it can be campaign input.

`ADOPTED_POLICY` therefore means **explicit policy creation by project authority, not retroactive proof that discovery was exhaustive**.

## 3.3 Adopted-policy source binding

An adopted profile MUST name one `adoptionDecisionAuthorityId`. That authority locator MUST resolve to one tracked file whose complete parsed semantic content is exactly `ProjectSibProfileAdoptionV1`:

```text
ProjectSibProfileAdoptionV1 {
  schemaVersion
  decisionId
  repositoryId
  projectSibProfileId
  profileVersion
  profileBodyDigest
  architectureGenerationId
  decision
}
```

Exact values and constraints:

```json
{
  "schemaVersion": "ProjectSibProfileAdoptionV1",
  "decisionId": "<id>",
  "repositoryId": "<repository id>",
  "projectSibProfileId": "<profile id>",
  "profileVersion": "<profile version>",
  "profileBodyDigest": "sha256:<64 lowercase hex>",
  "architectureGenerationId": "<architecture generation id>",
  "decision": "ADOPTED"
}
```

The adoption assertion MUST match the profile body on all five identity fields: repository, profile ID, profile version, profile body digest and architecture generation. Any mismatch is `ADOPTION_BINDING_MISMATCH`.

The adoption decision is authority evidence. It does not duplicate the policy body.

---

# 4. Canonical primitive types

The following lexical contracts are normative for V1.

## 4.1 `IdV1`

```text
^[a-z0-9][a-z0-9._:/-]{0,127}$
```

IDs are ASCII lowercase. Case changes are identity changes; implementations MUST NOT case-fold a nonconforming input into validity.

## 4.2 `ProfileVersionV1`

```text
^[a-z0-9][a-z0-9._+-]{0,63}$
```

A profile-version change is an explicit profile identity change even when all other fields happen to remain equal.

## 4.3 Git SHA V1

```text
^[0-9a-f]{40}$
```

V1 supports the existing 40-character Git object identity used by current CodeSleuth. Uppercase or abbreviated SHA is invalid.

## 4.4 Digest V1

```text
^sha256:[0-9a-f]{64}$
```

## 4.5 Repository path V1

A repository path:

- is relative to repository root;
- uses `/` only;
- has no leading or trailing `/`;
- has no empty segment;
- has no `.` or `..` segment;
- contains no NUL;
- is Unicode NFC.

Path normalization MUST NOT resolve symlinks or consult the host filesystem while computing semantic identity. Source resolution happens against the exact Git tree.

## 4.6 Human statement normalization

Fields explicitly typed as a human statement are normalized by:

1. Unicode NFC;
2. convert every Unicode whitespace run to one ASCII space;
3. trim leading/trailing ASCII space;
4. reject an empty result.

This normalization is for policy statements, not arbitrary command strings or file paths.

## 4.7 Constraint values

Constraint values are Unicode NFC, case-sensitive strings with no NUL and no leading/trailing Unicode whitespace. Internal whitespace is preserved.

---

# 5. `ProjectSibProfileV1` exact schema

`ProjectSibProfileV1` is the editable/adjudicable upstream profile/binding source. It intentionally contains **no user-editable digest field**. Digest fields are computed from canonical content so a document cannot claim an identity inconsistent with its bytes/semantics.

All fields below are required. Empty arrays are permitted only where explicitly stated.

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

## 5.1 Source-policy union

When `authorityMode == "NATIVE_BOUND"`:

```text
NativeSourcePolicyV1 {
  nativeAuthorityIds: IdV1[]   // non-empty
}
```

When `authorityMode == "ADOPTED_POLICY"`:

```text
AdoptedSourcePolicyV1 {
  adoptionDecisionAuthorityId: IdV1
}
```

The wrong union arm is invalid. There is no fallback or implicit mode detection.

## 5.2 Authority locator

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
```

`authorityId` is unique within the profile.

At snapshot compilation each locator is resolved against the exact target Git tree into:

```text
ResolvedAuthorityRefV1 {
  authorityId: IdV1
  kind: <same enum>
  repositoryId: IdV1
  path: RepositoryPathV1
  blobSha: <40 lowercase hex>
}
```

A missing path, non-blob path, or path that cannot be resolved at the exact target is a hard compile failure.

## 5.3 Policy requirement

```text
PolicyRequirementV1 {
  policyRequirementId: IdV1
  statement: HumanStatementV1
  sourceAuthorityIds: IdV1[]
}
```

In `NATIVE_BOUND`, `sourceAuthorityIds` MUST be non-empty and MUST intersect `sourcePolicy.nativeAuthorityIds`.

In `ADOPTED_POLICY`, the adopted profile body itself owns the statement, so `sourceAuthorityIds` MAY be empty; any listed IDs are supporting authority/evidence references and MUST resolve.

## 5.4 Acceptance obligation

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

- each SIB level MUST contain at least one `REQUIRED` obligation;
- a `REQUIRED` obligation MUST have at least one `gateId` and one `environmentId`;
- a `REQUIRED` obligation MUST have an empty `notApplicableRationaleAuthorityIds`;
- a `NOT_APPLICABLE` obligation MUST have empty `gateIds` and `environmentIds` and non-empty `notApplicableRationaleAuthorityIds`;
- `NOT_APPLICABLE` is valid only when its rationale is authority-backed; unavailable evidence or an unavailable runner is never N/A;
- in `NATIVE_BOUND`, every obligation MUST have non-empty `sourceAuthorityIds` intersecting the native owner set;
- all referenced IDs MUST exist.

## 5.5 Gate requirement

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
- all listed gate/environment combinations are required; an array is not an `ANY OF` shortcut;
- gate command construction/execution is outside W7; the gate's authority and stable ID are frozen here, while W6/host adapters later execute it and record exact run/result identity.

## 5.6 Environment requirement

```text
EnvironmentRequirementV1 {
  environmentId: IdV1
  sourceAuthorityIds: IdV1[]
  constraints: DimensionConstraintV1[]
}
```

`constraints` MAY be empty when the environment ID itself is the complete project-defined environment requirement (for example a repository-only/static authority check).

## 5.7 Tool and runtime requirements

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

These describe **required constraints**. The exact tool/runtime identity actually observed during a run belongs to W6 EHA evidence and MUST be recorded there; it is not guessed into the snapshot after execution.

## 5.8 Dimension constraints

```text
DimensionConstraintV1 {
  key: IdV1
  operator: "EQUALS" | "ONE_OF"
  values: string[]
}
```

Rules:

- `values` is non-empty;
- `EQUALS` requires exactly one value;
- `ONE_OF` requires at least one value;
- V1 deliberately has no range, regex or arbitrary expression language;
- if a project needs semantics not expressible by `EQUALS` / `ONE_OF`, it needs a future schema revision instead of implementation-local interpretation.

## 5.9 Coverage requirements

```text
CoverageRequirementsV1 {
  capabilityClassIds: IdV1[]
  protectedContractIds: IdV1[]
  policyRequirementIds: IdV1[]
}
```

This object is a **required coverage set**, not a completeness result.

The compiler MUST verify:

```text
union(obligations.capabilityClassIds)  contains coverageRequirements.capabilityClassIds
union(obligations.protectedContractIds) contains coverageRequirements.protectedContractIds
union(obligations.policyRequirementIds) contains coverageRequirements.policyRequirementIds
```

A missing required coverage item is `PROFILE_COVERAGE_GAP`.

## 5.10 Aggregation policy

V1 does not permit a project to weaken SIB semantics through a custom majority-vote or best-effort aggregator. The field MUST equal exactly:

```json
{
  "requiredObligationRule": "ALL_REQUIRED",
  "environmentMatrixRule": "ALL_REFERENCED_GATE_ENVIRONMENT_PAIRS",
  "notApplicableRule": "AUTHORITY_RATIONALE_REQUIRED",
  "missingEvidenceRule": "NON_PASS",
  "cumulativeSibRule": "SIB0_SIB1_SIB2_SAME_SUBJECT",
  "durableCompletionRule": "CAMPAIGN_COMPLETED_REQUIRED"
}
```

A different value requires a future schema version, not a local extension.

## 5.11 Policy statement

```text
PolicyStatementV1 {
  statementId: IdV1
  text: HumanStatementV1
  sourceAuthorityIds: IdV1[]
}
```

`assumptions` and `limitations` are semantic and participate in identity.

`unresolvedPolicyItems` is permitted in a proposal/adjudication-stage `ProjectSibProfileV1`, but snapshot compilation requires it to be empty. A profile with an unresolved policy choice is not campaign-ready.

---

# 6. Profile identity algorithm

The acceptance-profile identity is content-derived. No implementation may substitute a filename, branch, free-form `profile` label or timestamp for it.

## 6.1 Step A — normalize and validate profile body

Normalize `ProjectSibProfileV1` according to sections 4, 5 and 8.

Reject before hashing if schema validation, references, ownership mode, adoption preconditions or coverage checks fail.

## 6.2 Step B — `profileBodyDigest`

Canonicalize the normalized `ProjectSibProfileV1` body and compute:

```text
profileBodyDigest =
  "sha256:" + lowercase_hex(
    SHA256(
      UTF8("codesleuth:project-sib-profile-body:v1\n")
      || canonicalProfileJsonBytes
    )
  )
```

`schemaVersion` participates.

## 6.3 Step C — resolve the policy owner

For `NATIVE_BOUND`:

1. resolve every `nativeAuthorityId` against the exact target tree;
2. require all refs to belong to the same `repositoryId` as the profile;
3. sort the resolved refs by `authorityId`;
4. build:

```text
ResolvedSourcePolicyIdentityV1 {
  authorityMode: "NATIVE_BOUND"
  nativeAuthorityRefs: ResolvedAuthorityRefV1[]
}
```

For `ADOPTED_POLICY`:

1. resolve `adoptionDecisionAuthorityId` against the exact target tree;
2. require locator kind `ADOPTION_DECISION`;
3. parse the complete file as `ProjectSibProfileAdoptionV1`;
4. require `decision == "ADOPTED"`;
5. require exact match to repository ID, profile ID, version, `profileBodyDigest` and architecture generation;
6. build:

```text
ResolvedSourcePolicyIdentityV1 {
  authorityMode: "ADOPTED_POLICY"
  adoptionDecisionRef: ResolvedAuthorityRefV1
  adoptionAssertion: ProjectSibProfileAdoptionV1
}
```

No model inference is allowed in this step.

## 6.4 Step D — `profileDigest`

Canonicalize exactly:

```text
AcceptanceProfileIdentityV1 {
  schemaVersion: "AcceptanceProfileIdentityV1"
  profileBodyDigest: <profileBodyDigest>
  sourcePolicyIdentity: <resolved source policy identity>
}
```

Then:

```text
profileDigest =
  "sha256:" + lowercase_hex(
    SHA256(
      UTF8("codesleuth:acceptance-profile-identity:v1\n")
      || canonicalIdentityJsonBytes
    )
  )
```

Consequences:

- changing a native policy blob changes `profileDigest`;
- changing the adopted profile body changes `profileBodyDigest`, invalidates the old adoption assertion and therefore cannot silently retain `profileDigest`;
- moving only the candidate SHA while policy sources remain byte-identical leaves `profileDigest` unchanged;
- changing `profileVersion`, architecture generation, obligation semantics, gates, required environments, assumptions or limitations changes `profileBodyDigest` and therefore `profileDigest`.

This digest is the normative **profile identity** used by the acceptance-identity invariant.

---

# 7. `AcceptanceProfileSnapshotV1` exact schema

The snapshot is a compiled immutable campaign input.

```text
AcceptanceProfileSnapshotV1 {
  schemaVersion: "AcceptanceProfileSnapshotV1"
  profileIdentity: ProfileIdentityV1
  sourcePolicyIdentity: SnapshotSourcePolicyIdentityV1
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

## 7.1 Profile identity

```text
ProfileIdentityV1 {
  projectSibProfileId: IdV1
  profileVersion: ProfileVersionV1
  architectureGenerationId: IdV1
  authorityMode: "NATIVE_BOUND" | "ADOPTED_POLICY"
  profileBodyDigest: DigestV1
  profileDigest: DigestV1
}
```

`profileDigest` is the acceptance profile identity. `profileBodyDigest` is retained for audit/adoption verification.

## 7.2 Target binding

```text
SnapshotTargetV1 {
  repositoryId: IdV1
  subjectSha: <40 lowercase hex>
}
```

`repositoryId` is an explicit project-authority-assigned stable identifier. It is **not inferred from a mutable branch name or normalized ad hoc from the current remote URL**.

Cloning a repository preserves its declared project identity. A fork under independent project authority must establish a different repository/profile policy rather than silently inheriting acceptance because it shares Git ancestry.

`subjectSha` is semantic snapshot content and participates in `semanticDigest`.

Branch/ref names MUST NOT appear in the snapshot. They remain candidate-selection provenance/navigation and may move.

## 7.3 Snapshot source-policy identity

`sourcePolicyIdentity` is the already-resolved source-policy object used to calculate `profileDigest`.

For native binding it contains the exact native authority refs. For adopted policy it contains the exact adoption-decision ref and matching adoption assertion.

It is copied into the snapshot so the profile owner can be audited without recovering hidden chat/session state.

## 7.4 Authority refs

`authorityRefs` contains the exact `ResolvedAuthorityRefV1` for **every** `authorityLocator` in the accepted profile, sorted by `authorityId`.

The compiler MUST resolve them against the snapshot target SHA. A profile with a declared authority path not present at the target cannot compile.

This makes authority drift visible rather than letting the implementation quietly use whatever file exists in the current worktree.

## 7.5 Completeness fields deliberately excluded

`AcceptanceProfileSnapshotV1` MUST NOT contain evaluated fields such as:

```text
discoveryCompleteness
policyCompleteness
completenessSupportable
```

V1 contains `coverageRequirements`, which says **what policy requires coverage of**. It does not contain the evidence-derived answer to whether archaeology/discovery was complete.

Reason: `DiscoveryCompleteness` and `PolicyCompleteness` are W8 evidence/claim semantics. Embedding their changing evaluation into immutable policy input would merge policy with evidence and recreate the authority problem this freeze is removing.

W8 may reference `profileDigest` / `semanticDigest` when it records completeness claims. It MUST NOT mutate a started campaign's snapshot to store a later completeness conclusion.

---

# 8. Canonicalization and collection ordering

The digest algorithm is self-contained and does not depend on host-language object iteration order.

## 8.1 Exact-schema projection first

Before serialization:

1. reject every unknown object member;
2. require every declared member;
3. reject every JSON `null`;
4. validate every lexical type and cross-reference;
5. normalize strings by their declared type;
6. de-duplicate and sort collections according to this section.

Hashing malformed input and then validating it is forbidden.

## 8.2 Object field order

Canonical JSON emits object fields in **the declaration order shown by this document's type definitions**.

Input object-key order has no semantic effect.

For the top-level snapshot the exact order is:

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

`semanticDigest` is omitted from its own digest preimage and is emitted last in the stored/rendered snapshot.

For the top-level profile the exact order is the order in section 5.

## 8.3 Collection ordering

Canonical sort rules:

| Collection | Sort key |
| --- | --- |
| `authorityLocators` / `authorityRefs` | `authorityId` |
| `policyRequirements` | `policyRequirementId` |
| `obligations` | `obligationId` |
| `gates` | `gateId` |
| `environments` | `environmentId` |
| `materialTools` | `toolRequirementId` |
| `materialRuntimes` | `runtimeRequirementId` |
| `assumptions`, `limitations`, `unresolvedPolicyItems` | `statementId` |
| `DimensionConstraintV1[]` | `key`, then `operator`, then canonical joined `values` |
| arrays of IDs | normalized ASCII byte lexicographic order |
| `DimensionConstraintV1.values` | normalized UTF-8 byte lexicographic order |

Duplicate IDs or duplicate scalar values are validation errors; they are not silently discarded.

## 8.4 JSON encoding

Canonical JSON uses:

- UTF-8;
- no BOM;
- no insignificant whitespace;
- `:` and `,` with no surrounding spaces;
- JSON escaping required by the JSON grammar only;
- no trailing newline in digest bytes;
- no JSON numbers in any V1 semantic type;
- no JSON `null`.

This deliberately avoids cross-language number-format ambiguity.

---

# 9. Snapshot semantic digest

After successful compilation, construct the normalized snapshot with `semanticDigest` omitted.

Then:

```text
semanticDigest =
  "sha256:" + lowercase_hex(
    SHA256(
      UTF8("codesleuth:acceptance-profile-snapshot:v1\n")
      || canonicalSnapshotJsonBytesWithoutSemanticDigest
    )
  )
```

## 9.1 Included fields

Every semantic field in section 7 participates, including:

- `schemaVersion`;
- profile ID/version/body digest/profile digest;
- authority mode/source-policy identity;
- repository ID and exact subject SHA;
- exact authority blob refs;
- policy requirements;
- obligations and applicability;
- required gates;
- environment requirements;
- material tool/runtime requirements;
- coverage requirements;
- aggregation policy;
- assumptions;
- limitations.

A change to any of those normalized values MUST change `semanticDigest`.

## 9.2 Excluded fields

The only member of `AcceptanceProfileSnapshotV1` excluded from its digest preimage is `semanticDigest` itself.

Volatile metadata is excluded by a stronger rule: it is **not legal snapshot schema**.

The following MUST NOT appear in V1 snapshot content:

```text
generatedAt / compiledAt / recordedAt
actor / user / model / provenance watermark
host session id
process id / hostname / cwd
branch name / movable ref
GitHub workflow run id / job id
observed PASS/FAIL result
transport outcome
report path
renderer/template metadata
current working-tree dirty state
```

Those values belong to campaign/run/provenance evidence where appropriate.

## 9.3 Absent, null and unknown

- A required field absent from the exact schema is invalid.
- `null` is invalid everywhere in V1 semantic objects.
- Unknown policy semantics MUST NOT be represented by omission or `null`.
- An unresolved policy decision belongs in `ProjectSibProfileV1.unresolvedPolicyItems`; any non-empty value blocks snapshot compilation.
- Empty arrays mean explicitly “none” only where the schema permits them.
- Execution-time epistemic outcomes such as `INCONCLUSIVE` / `UNAVAILABLE` are EHA result data, not snapshot placeholders.

There is no generic string `"UNKNOWN"` in `AcceptanceProfileSnapshotV1` V1.

## 9.4 Semantic identity consequence

Within this contract, two snapshots are semantically identical **iff their normalized digest preimages are byte-identical**.

Therefore:

- JSON key order differences do not matter;
- source collection order differences do not matter;
- allowed whitespace/Unicode normalization differences in statement input do not matter;
- changing a target SHA matters;
- changing policy authority identity matters;
- changing a gate, environment, obligation, assumption or limitation matters.

This definition is intentionally machine-testable rather than model-judged.

---

# 10. Compilation algorithm

The W7 compiler MUST implement this deterministic sequence and MUST NOT choose an alternative ordering or fallback policy.

```text
INPUT:
  exact target repository context
  exact 40-char targetSha
  ProjectSibProfileV1

1. Parse exact ProjectSibProfileV1 schema.
2. Normalize V1 lexical fields.
3. Reject unknown fields / null / duplicate IDs / dangling references.
4. Require unresolvedPolicyItems == [].
5. Validate aggregationPolicy equals the V1 constant.
6. Validate SIB0/SIB1/SIB2 each has >= 1 REQUIRED obligation.
7. Validate obligation/gate/environment/tool/runtime graph.
8. Validate coverageRequirements are covered by obligations.
9. Compute profileBodyDigest.
10. Resolve every authorityLocator against targetSha.
11. Resolve and validate exactly one policy owner:
      NATIVE_BOUND -> exact native authority refs;
      ADOPTED_POLICY -> exact adoption assertion matching profileBodyDigest.
12. Compute profileDigest.
13. Build AcceptanceProfileSnapshotV1 from normalized profile content,
    resolved authority refs, resolved source-policy identity and exact target.
14. Canonically sort every collection.
15. Compute snapshot semanticDigest.
16. Re-canonicalize the produced object and verify the digest a second time.
17. Return snapshot.

ANY FAILED STEP:
  return a deterministic error;
  produce no campaign-ready snapshot;
  do not fall back to legacy profile labels;
  do not infer missing policy with a model.
```

Compilation is a pure semantic operation with exact Git reads. It MUST NOT mutate source, policy, EHA state or protected-capability state.

---

# 11. Deterministic errors and ambiguity behavior

The implementation MAY expose richer diagnostic detail, but the following machine-level error categories are frozen.

| Error | Required condition |
| --- | --- |
| `PROFILE_SCHEMA_UNSUPPORTED` | unknown `schemaVersion` or union shape |
| `PROFILE_SCHEMA_INVALID` | missing field, unknown field, `null`, invalid lexical value |
| `PROFILE_DUPLICATE_ID` | duplicate entity/scalar ID in a uniqueness domain |
| `PROFILE_DANGLING_REF` | referenced authority/policy/gate/environment/tool/runtime/coverage ID missing |
| `PROFILE_POLICY_UNRESOLVED` | `unresolvedPolicyItems` non-empty |
| `PROFILE_POLICY_OWNER_INVALID` | zero, multiple or mode-incompatible policy owners |
| `NATIVE_AUTHORITY_MISSING` | required native authority cannot resolve at target |
| `NATIVE_BINDING_UNSOURCED` | native-bound policy-bearing item has no native authority support |
| `ADOPTION_DECISION_MISSING` | adopted mode cannot resolve decision authority |
| `ADOPTION_BINDING_MISMATCH` | adoption assertion does not bind exact profile body identity |
| `AUTHORITY_BLOB_MISSING` | declared authority path does not resolve to a blob at target |
| `PROFILE_COVERAGE_GAP` | required capability/contract/policy coverage is not mapped to obligations |
| `PROFILE_SIB_LEVEL_EMPTY` | a SIB level has no `REQUIRED` obligation |
| `PROFILE_NOT_APPLICABLE_INVALID` | N/A lacks authority rationale or carries executable gate/env refs |
| `PROFILE_AGGREGATION_INVALID` | V1 aggregation constants changed/weakened |
| `PROFILE_TARGET_INVALID` | repository binding or target SHA invalid |
| `SNAPSHOT_DIGEST_MISMATCH` | loaded snapshot does not recompute to stored digest |
| `SNAPSHOT_IMMUTABLE` | attempted mutation after campaign binding |
| `LEGACY_CAMPAIGN_NO_SNAPSHOT` | caller requests V1 snapshot identity from an RC6 legacy campaign |
| `LEGACY_CAMPAIGN_V2_APPEND_FORBIDDEN` | caller attempts to upgrade/mix V2 snapshot semantics into an old campaign |

Ambiguity is fail-closed:

- multiple plausible native policy owners -> no snapshot;
- conflicting source policy -> no snapshot;
- adoption assertion that cannot be established exactly -> no snapshot;
- missing environment requirement -> no snapshot;
- inability to determine whether an obligation is required vs N/A -> no snapshot.

Implementation-local “best guess” semantics are forbidden.

---

# 12. Immutability contract

## 12.1 Freeze point

`AcceptanceProfileSnapshotV1` MUST be fully compiled and digest-verified **before** `campaign_started` establishes the campaign.

At campaign start the campaign binds:

```text
exact target subjectSha
+ profileIdentity.profileDigest
+ snapshot semanticDigest
```

W6 will freeze the physical EHA V2 event/storage representation of that binding. W7 freezes the semantic tuple now.

## 12.2 After campaign start

After `campaign_started`:

- snapshot bytes are immutable;
- `semanticDigest` is immutable;
- target SHA is immutable;
- profile identity is immutable;
- gate/environment requirement set is immutable;
- policy source identity is immutable.

No API may “refresh” a running campaign to a newer profile.

## 12.3 Upstream profile changes

If `ProjectSibProfileV1` or any material source authority changes after campaign start:

```text
old campaign -> keeps old snapshot forever
new profile/source -> compiles to new profile/snapshot identity
new acceptance claim -> requires a new campaign
```

The historical campaign does not become invalid merely because later policy exists. It remains evidence for the exact subject/profile/snapshot under which it ran.

It also does not become evidence for the new profile.

## 12.4 Snapshot loss/corruption

If a V1 campaign claims a snapshot digest but the corresponding snapshot cannot be loaded and verified, V1 profile-aware claimability is not supportable from that record set. The reader MUST report the missing/corrupt evidence; it MUST NOT reconstruct the snapshot from today's profile and pretend it was original campaign input.

---

# 13. RC6 compatibility contract

Current RC6 EHA events have no `AcceptanceProfileSnapshotV1`; verdict events contain a free-form/string `profile` field and campaign identity is established by current `campaign_started` fields.

RC7 MUST read those records without rewriting them.

## 13.1 Legacy classification

A campaign whose original `campaign_started` is an RC6 event with no V1 snapshot binding is classified:

```text
campaignSchema = "RC6_LEGACY"
profileBinding = "LEGACY_UNBOUND"
acceptanceProfileSnapshot = absent at the reader/view layer
```

This classification is derived reader state. It is not appended retroactively to the ledger.

## 13.2 Historical semantics preserved

For RC6 legacy campaigns:

- preserve original target SHA, scope, verdicts, repairs and completion exactly;
- preserve the original verdict `profile` string as `legacyProfileLabel` when rendered;
- preserve historical RC6 claimability according to the accepted RC6 rules that created that evidence;
- do not weaken, strengthen or recompute old verdicts using current policy.

An RC6 SIB PASS remains historical RC6 acceptance evidence for its exact subject under its original contract. It does **not** acquire `AcceptanceProfileSnapshotV1` identity.

## 13.3 No retroactive upgrade

RC7 MUST NOT:

- synthesize `profileDigest` from the old `profile` string;
- compile today's project profile and attach it to the old campaign;
- infer old gate/environment identity that was not durably recorded;
- rewrite old `campaign_started` or verdict events;
- append a V2 snapshot binding into an already-started RC6 campaign;
- describe an RC6 campaign as V1-snapshot-bound.

If a current profile-aware acceptance claim is needed for the same exact source SHA, start a **new campaign** with a fresh V1 snapshot. Same SHA does not make old and new profile identities interchangeable.

## 13.4 Legacy access behavior

A reader request for V1-specific fields on a legacy campaign returns an explicit legacy/unavailable state, not a fabricated object.

A writer request to append V2 snapshot-aware events to a legacy campaign fails `LEGACY_CAMPAIGN_V2_APPEND_FORBIDDEN`.

This prevents mixed-semantic campaigns.

---

# 14. Adversarial examples

These are normative acceptance examples for W7 tests.

## A1 — object key order

Two inputs contain identical fields in different JSON object key orders.

**Required:** same normalized snapshot and same digest.

## A2 — collection order

The same obligations, gates and environments arrive in reverse order.

**Required:** canonical sort; same digest.

## A3 — duplicate ID

Two obligations use `sib2.integration`.

**Required:** `PROFILE_DUPLICATE_ID`; no silent de-duplication.

## A4 — target changes only

Profile and authority blobs are identical, but target changes from SHA A to SHA B.

**Required:** same `profileDigest`, different snapshot `semanticDigest`.

This proves target identity and profile identity remain separate axes.

## A5 — native policy changes only

The binding profile file is unchanged, but one native policy path resolves to a different blob at the target.

**Required:** different `profileDigest` and different snapshot digest.

## A6 — provenance changes only

Actor/session/watermark/recording time changes while the snapshot semantic object is unchanged.

**Required:** no snapshot/profile digest change because those values are not legal snapshot fields.

## A7 — profile version changes only

`profileVersion` changes while every other profile field is byte/semantically equal.

**Required:** new body/profile/snapshot digests. Version is an identity-bearing semantic declaration, not decorative metadata.

## A8 — adopted profile edited after adoption

Adoption assertion binds profile body digest X. Profile is edited and now normalizes to digest Y.

**Required:** `ADOPTION_BINDING_MISMATCH`; no snapshot.

## A9 — adoption missing

`authorityMode=ADOPTED_POLICY`, but the adoption decision path is unavailable at the target.

**Required:** `ADOPTION_DECISION_MISSING`; profile remains proposal/non-campaign-ready.

## A10 — native mapping invents policy

A `NATIVE_BOUND` obligation has no `sourceAuthorityIds` intersecting `nativeAuthorityIds`.

**Required:** `NATIVE_BINDING_UNSOURCED`; no shadow-policy fallback.

## A11 — unavailable runner represented as N/A

An obligation is marked `NOT_APPLICABLE` merely because its runner/credential is unavailable.

**Required:** invalid N/A unless a project authority explicitly supplies N/A rationale. Runtime unavailability is an EHA evidence outcome, not profile applicability.

## A12 — protected coverage silently dropped

`coverageRequirements.protectedContractIds` contains contract C but no obligation covers C.

**Required:** `PROFILE_COVERAGE_GAP`.

## A13 — environment matrix weakened

A gate references environments linux and windows, but an implementation executes only linux and tries to treat the gate as complete.

**Required:** the snapshot still requires both. W6 result aggregation must not produce profile PASS from the partial matrix.

## A14 — profile changed during campaign

Campaign starts on snapshot D1. Project profile later compiles to D2.

**Required:** running/historical campaign remains bound to D1. No refresh. New profile-aware claim needs a new campaign.

## A15 — legacy RC6 profile string resembles current ID

An RC6 verdict has `profile="sib2-full"`, and current V1 profile happens to use ID `sib2-full`.

**Required:** no identity transfer. The old string remains `legacyProfileLabel`; V1 profile binding remains unavailable.

## A16 — legacy campaign on same SHA

An RC6 campaign PASS exists for SHA A; RC7 compiles a V1 snapshot for SHA A.

**Required:** old PASS is not retroactively V1-bound. A new V1 campaign is required for a V1 profile-aware acceptance claim.

## A17 — branch moves

Snapshot target SHA is A; the release branch later points to B.

**Required:** snapshot remains A. Existing EHA exact-head invalidation/selection rules decide whether execution may continue; branch name never changes the snapshot digest.

## A18 — semantic statement whitespace

A policy statement differs only by Unicode whitespace runs and NFC-equivalent Unicode spelling.

**Required:** statement normalization makes the digest equal.

## A19 — constraint value changes

`python.version EQUALS "3.12.7"` becomes `"3.12.8"`.

**Required:** profile and snapshot digest change.

## A20 — unknown field injected

Snapshot contains `"generatedAt": "..."` or an implementation-private `"notes"` member.

**Required:** `PROFILE_SCHEMA_INVALID`; unknown members are not tolerated as pseudo-extensions.

---

# 15. Compatibility obligations

W7 implementation MUST preserve all of the following.

1. **Exact-head identity:** exact target SHA remains an independent acceptance axis.
2. **One policy owner:** no second editable acceptance-policy object is introduced.
3. **Existing SIB meanings:** profile customization cannot redefine SIB0/SIB1/SIB2.
4. **Existing EHA authority:** snapshot does not replace `eha.ndjson`.
5. **Current campaign start modes:** `trusted_prestarted` vs `model_started` ownership remains an EHA/W6 concern; either mode must bind the same immutable snapshot semantics before campaign start.
6. **Protected registry:** protected contract IDs are references to existing registry authority, not copied lifecycle truth.
7. **Provenance separation:** watermark/session attribution stays outside claimability and digest.
8. **Host ownership:** W7 performs schema/identity/compilation, not source editing or controller execution.
9. **Non-binary evidence compatibility:** snapshot defines policy/applicability, but W6 retains distinct execution outcomes such as PASS, FAIL, INCONCLUSIVE and UNAVAILABLE; missing/non-PASS evidence cannot be upgraded by snapshot logic.
10. **Fresh campaign after changed profile:** historical evidence remains historical; a changed profile requires fresh acceptance evidence for a current claim.
11. **Reader compatibility:** RC6 records remain readable without mutation.
12. **Fail closed on unsupported future schemas:** a V1 reader MUST NOT treat V2 as V1 by dropping fields.

---

# 16. MUST / MUST NOT summary

## MUST

- have exactly one policy owner;
- compute `profileBodyDigest`, `profileDigest` and snapshot `semanticDigest` exactly as frozen here;
- include `schemaVersion` in all digest preimages;
- bind the snapshot to exact `repositoryId + subjectSha`;
- resolve exact authority blobs from the target Git tree;
- freeze gates, environments, material tool/runtime requirements and coverage requirements before campaign start;
- canonicalize field and collection ordering;
- reject unresolved policy choices;
- require explicit authority-backed N/A rationale;
- keep old campaigns immutable when policy changes;
- read RC6 campaigns as legacy without upgrading them;
- preserve actual gate/environment/run/result evidence as separate acceptance dimensions.

## MUST NOT

- create a second independently editable acceptance-policy authority;
- infer profile identity from a filename or free-form profile string;
- include actor/session/timestamp/branch/run result in snapshot digest;
- infer missing native policy from model reasoning;
- treat discovery completeness as policy completeness;
- store evaluated completeness statuses in V1 snapshot;
- use `null`/missing fields as unknown policy semantics;
- silently sort-and-deduplicate duplicates into validity;
- mutate a snapshot after `campaign_started`;
- refresh an existing campaign to a changed profile;
- retroactively attach V1 snapshots to RC6 campaigns;
- let a partial environment matrix satisfy an all-required profile;
- treat N/A as a synonym for unavailable.

---

# 17. Explicit non-goals

This freeze deliberately does **not** decide or implement:

- production TypeScript/Python W7 code;
- physical file path for persisted snapshot instances;
- exact EHA V2 event field/storage layout carrying the snapshot binding — W6 owns that physical schema while preserving the semantic tuple frozen here;
- EHA V2 non-binary event serialization beyond the inherited rule that non-PASS/missing evidence cannot become PASS;
- W8 `DiscoveryCompleteness` / `PolicyCompleteness` value model or evidence algorithm;
- W9 repair-attempt identity/termination digest;
- W10 repair-vs-ledger-recovery permissions;
- host command rendering or Jinja execution semantics;
- a generic policy language, regex/range constraint engine or arbitrary expression evaluator;
- cross-repository policy authority in V1;
- Git SHA-256 object-format support in V1;
- generic attestation/signature infrastructure;
- retroactive migration of RC6 durable EHA history.

These are exclusions, not unresolved W7 semantics.

---

# 18. Tests-first implementation contract for W7

A W7 implementation can begin with RED tests for at least:

1. exact schema acceptance/rejection;
2. NATIVE vs ADOPTED single-owner validation;
3. adoption assertion exact-body binding;
4. authority path -> exact target blob resolution;
5. profile-body digest canonicalization;
6. source-policy-sensitive `profileDigest`;
7. snapshot digest canonicalization;
8. object-key and collection-order invariance;
9. target-SHA change changes only snapshot identity when policy is unchanged;
10. native policy blob change changes profile identity;
11. duplicate/dangling ref failure;
12. coverage-gap failure;
13. invalid N/A failure;
14. unresolved-policy compile block;
15. immutable post-start snapshot binding;
16. RC6 legacy read with `LEGACY_UNBOUND` profile state;
17. refusal to synthesize/append a V1 binding into a legacy campaign;
18. exclusion of provenance/run/timestamp data from profile/snapshot identity.

W7 tests MUST treat the digest vectors produced by this contract as compatibility vectors. Once W7 ships, changing canonicalization or digest preimages requires a schema-version change rather than modifying V1 in place.

---

# 19. Downstream workstreams unlocked

This freeze resolves the semantic choices W7 would otherwise have to invent during implementation:

- one policy owner;
- exact NATIVE/ADOPTED semantics;
- adopted-policy source/adjudication binding;
- exact ProjectSibProfile V1 policy shape;
- exact immutable snapshot V1 shape;
- exact profile and snapshot digest algorithms;
- exact normalization/ordering/null/unknown behavior;
- exact campaign immutability rule;
- exact RC6 reader compatibility/no-upgrade rule.

Therefore it unlocks:

- **W7 ProjectSibProfile / AcceptanceProfileSnapshot** tests-first implementation;
- prerequisite profile/snapshot identity for **W6 EHA V2**;
- stable policy/coverage identity prerequisite for **W8 completeness**;
- stable profile snapshot identity prerequisite for **W9 repair termination**.

---

# 20. Unresolved items

There are **no unresolved W7 semantic decisions** in the scope of this micro-freeze.

The remaining questions listed as non-goals are owned by downstream freezes/workstreams. An implementation of W7 does not need to choose their semantics in order to implement the schemas, compiler, canonicalization, digests, immutability guard and RC6 compatibility behavior frozen here.

---

FREEZE STATUS:
FROZEN

UNLOCKS:
W7 ProjectSibProfile / AcceptanceProfileSnapshot
provides prerequisite for W6 EHA V2
provides prerequisite for W8 completeness
provides prerequisite for W9 repair termination
