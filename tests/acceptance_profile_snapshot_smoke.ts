import { mkdir, mkdtemp, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"
import {
  AcceptanceProfileError,
  compileAcceptanceProfileSnapshotV1,
  computeProjectSibProfileBodyDigestV1,
  validateConstraintKeyV1,
  validateDigestV1,
  validateGitShaV1,
  validateHumanStatementV1,
  validateIdV1,
  validateProfileVersionV1,
  validateRepositoryPathV1,
  verifyAcceptanceProfileSnapshotV1,
} from "../pack/.opencode/tools/acceptance_profile_snapshot"

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message)
}

function clone<T>(value: T): T {
  return structuredClone(value)
}

function errorCode(error: unknown): string | undefined {
  return error instanceof AcceptanceProfileError ? error.code : undefined
}

async function expectCode(expected: string, action: () => unknown | Promise<unknown>, message: string): Promise<void> {
  try {
    await action()
  } catch (error) {
    assert(errorCode(error) === expected, `${message}: expected ${expected}, got ${String(error)}`)
    return
  }
  throw new Error(`${message}: expected ${expected}, but operation succeeded`)
}

async function git(root: string, args: string[], env: Record<string, string> = {}): Promise<string> {
  const proc = Bun.spawn(["git", "-C", root, ...args], {
    stdout: "pipe",
    stderr: "pipe",
    env: { ...process.env, ...env },
  })
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  const code = await proc.exited
  if (code !== 0) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`)
  return stdout.trim()
}

const AGGREGATION = {
  requiredObligationRule: "ALL_REQUIRED",
  environmentMatrixRule: "ALL_REFERENCED_GATE_ENVIRONMENT_PAIRS",
  notApplicableRule: "AUTHORITY_RATIONALE_REQUIRED",
  missingEvidenceRule: "NON_PASS",
  cumulativeSibRule: "SIB0_SIB1_SIB2_SAME_SUBJECT",
  durableCompletionRule: "CAMPAIGN_COMPLETED_REQUIRED",
}

function nativeProfile() {
  return {
    schemaVersion: "ProjectSibProfileV1",
    projectSibProfileId: "codesleuth.project-sib-profile",
    profileVersion: "rc7-v1",
    repositoryId: "dassaultfalconking/codesleuth",
    architectureGenerationId: "rc7",
    authorityMode: "NATIVE_BOUND",
    sourcePolicy: { nativeAuthorityIds: ["native.acceptance"] },
    authorityLocators: [
      { authorityId: "native.acceptance", kind: "ACCEPTANCE_POLICY", path: "native.txt" },
      { authorityId: "gate.policy", kind: "GATE_DEFINITION", path: "gate.txt" },
      { authorityId: "environment.policy", kind: "ENVIRONMENT_POLICY", path: "env.txt" },
      { authorityId: "capability.registry", kind: "CAPABILITY_REGISTRY", path: "capability.json" },
      { authorityId: "candidate.policy", kind: "CANDIDATE_SELECTION_POLICY", path: "candidate.txt" },
      { authorityId: "promotion.policy", kind: "PROMOTION_POLICY", path: "promotion.txt" },
      { authorityId: "reopen.policy", kind: "ARCHITECTURE_REOPEN_POLICY", path: "reopen.txt" },
      { authorityId: "repair.policy", kind: "REPAIR_POLICY", path: "repair.txt" },
    ],
    policyRequirements: [{
      policyRequirementId: "policy.core",
      statement: "Preserve exact authority semantics",
      sourceAuthorityIds: ["native.acceptance"],
    }],
    obligations: ["SIB0", "SIB1", "SIB2"].map((sibLevel, index) => ({
      obligationId: `sib${index}.core`,
      sibLevel,
      property: ["Architecture policy is bound", "Capability implementation is verified", "Composition is verified"][index],
      applicability: "REQUIRED",
      sourceAuthorityIds: ["native.acceptance"],
      policyRequirementIds: ["policy.core"],
      gateIds: ["gate.core"],
      environmentIds: ["env.hosted"],
      capabilityClassIds: ["CC-PACK"],
      protectedContractIds: [],
      notApplicableRationaleAuthorityIds: [],
    })),
    gates: [{
      gateId: "gate.core",
      gateKind: "EXECUTABLE",
      sourceAuthorityIds: ["gate.policy"],
      environmentIds: ["env.hosted"],
      toolRequirementIds: ["tool.bun"],
      runtimeRequirementIds: ["runtime.bun"],
    }],
    environments: [{
      environmentId: "env.hosted",
      sourceAuthorityIds: ["native.acceptance"],
      constraints: [{ key: "os", operator: "ONE_OF", values: ["ubuntu", "windows"] }],
    }],
    materialTools: [{
      toolRequirementId: "tool.bun",
      toolId: "bun",
      sourceAuthorityIds: ["native.acceptance"],
      constraints: [{ key: "version", operator: "EQUALS", values: ["1.2.22"] }],
    }],
    materialRuntimes: [{
      runtimeRequirementId: "runtime.bun",
      runtimeId: "bun",
      sourceAuthorityIds: ["native.acceptance"],
      constraints: [{ key: "arch", operator: "ONE_OF", values: ["x64", "arm64"] }],
    }],
    coverageRequirements: {
      capabilityClassIds: ["CC-PACK"],
      protectedContractIds: [],
      policyRequirementIds: ["policy.core"],
    },
    aggregationPolicy: clone(AGGREGATION),
    candidateSelectionAuthorityIds: ["candidate.policy"],
    promotionAuthorityIds: ["promotion.policy"],
    architectureReopenAuthorityIds: ["reopen.policy"],
    repairPolicyAuthorityIds: ["repair.policy"],
    assumptions: [{ statementId: "assumption.one", text: "Café policy is stable", sourceAuthorityIds: ["native.acceptance"] }],
    limitations: [{ statementId: "limitation.one", text: "Only exact target blobs are authoritative", sourceAuthorityIds: ["native.acceptance"] }],
    unresolvedPolicyItems: [],
  }
}

const AUTHORITY_FILES: Record<string, string> = {
  "native.txt": "native acceptance policy v1\n",
  "gate.txt": "gate policy v1\n",
  "env.txt": "environment policy v1\n",
  "capability.json": "{\"classes\":[\"CC-PACK\"]}\n",
  "candidate.txt": "candidate selection v1\n",
  "promotion.txt": "promotion policy v1\n",
  "reopen.txt": "architecture reopen v1\n",
  "repair.txt": "repair policy v1\n",
}

async function makeRepository(extra: Record<string, string> = {}) {
  const root = await mkdtemp(path.join(tmpdir(), "w7-profile-"))
  await git(root, ["init", "-b", "main"])
  await git(root, ["config", "user.email", "codesleuth-ci@example.invalid"])
  await git(root, ["config", "user.name", "CodeSleuth CI"])
  for (const [file, content] of Object.entries({ ...AUTHORITY_FILES, ...extra })) {
    const absolute = path.join(root, file)
    await mkdir(path.dirname(absolute), { recursive: true })
    await writeFile(absolute, content, "utf8")
  }
  await git(root, ["add", "."])
  await git(root, ["commit", "-m", "authority fixture"], {
    GIT_AUTHOR_DATE: "2000-01-01T00:00:00Z",
    GIT_COMMITTER_DATE: "2000-01-01T00:00:00Z",
  })
  return { root, subjectSha: await git(root, ["rev-parse", "HEAD"]) }
}

async function scalarValidation() {
  const validCases: Array<[string, (value: string) => string, string]> = [
    ["a.b_c:d/e-f", validateIdV1, "a.b_c:d/e-f"],
    ["rc7+v1.0", validateProfileVersionV1, "rc7+v1.0"],
    ["0123456789abcdef0123456789abcdef01234567", validateGitShaV1, "0123456789abcdef0123456789abcdef01234567"],
    [`sha256:${"a".repeat(64)}`, validateDigestV1, `sha256:${"a".repeat(64)}`],
    ["runtime.version", validateConstraintKeyV1, "runtime.version"],
    ["docs/Cafe\u0301.md", validateRepositoryPathV1, "docs/Café.md"],
    ["  Cafe\u0301\t policy\n is stable  ", validateHumanStatementV1, "Café policy is stable"],
  ]
  for (const [input, validator, expected] of validCases) assert(validator(input) === expected, `scalar normalization failed for ${input}`)

  const invalidCases: Array<[(value: string) => string, string[]]> = [
    [validateIdV1, ["", "A", "-a", "a b", "a".repeat(129)]],
    [validateProfileVersionV1, ["", "RC7", "+rc7", "a/b", "a".repeat(65)]],
    [validateGitShaV1, ["A".repeat(40), "0".repeat(39), "0".repeat(41), "g".repeat(40)]],
    [validateDigestV1, ["a".repeat(64), `SHA256:${"a".repeat(64)}`, `sha256:${"A".repeat(64)}`]],
    [validateConstraintKeyV1, ["", "Runtime", "-runtime", "runtime/version", "a".repeat(129)]],
    [validateRepositoryPathV1, ["/docs/a", "docs/a/", "docs//a", "docs/./a", "docs/../a", "docs\\a", "docs/\u0000a"]],
    [validateHumanStatementV1, ["", " \t\n ", "bad\u0000statement", "bad\u0085statement"]],
  ]
  for (const [validator, values] of invalidCases) {
    for (const value of values) await expectCode("PROFILE_SCHEMA_INVALID", () => validator(value), `invalid scalar ${JSON.stringify(value)}`)
  }
}

async function authorityModesAndResolution() {
  const { root, subjectSha } = await makeRepository()
  assert(subjectSha === "5b4b3eb7161a4486d0781cda506d80cffa5be6de", "authority fixture commit must remain golden")
  const profile = nativeProfile()
  const snapshot = await compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile })
  assert(snapshot.target.subjectSha === subjectSha, "snapshot binds exact subject SHA")
  assert(snapshot.sourcePolicyIdentity.authorityMode === "NATIVE_BOUND", "native mode remains explicit")
  assert(snapshot.authorityRefs.every((ref: any) => /^[0-9a-f]{40}$/.test(ref.blobSha)), "authority refs bind exact Git blobs")
  assert(!("DiscoveryCompletenessV1" in snapshot) && !("PolicyCompletenessV1" in snapshot), "completeness state stays outside snapshot")

  const inferred = clone(profile) as any
  delete inferred.authorityMode
  await expectCode("PROFILE_SCHEMA_INVALID", () => compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile: inferred }), "mode inference is forbidden")
  const mismatched = clone(profile) as any
  mismatched.authorityMode = "ADOPTED_POLICY"
  await expectCode("PROFILE_SCHEMA_INVALID", () => compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile: mismatched }), "strict tagged union")
  const missing = clone(profile) as any
  missing.authorityLocators.find((x: any) => x.authorityId === "repair.policy").path = "missing-repair.txt"
  await expectCode("AUTHORITY_BLOB_MISSING", () => compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile: missing }), "missing authority blob")
  const wrongKind = clone(profile) as any
  wrongKind.candidateSelectionAuthorityIds = ["gate.policy"]
  await expectCode("PROFILE_REFERENCE_KIND_INVALID", () => compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile: wrongKind }), "wrong-kind authority")
  const contradictory = clone(profile) as any
  contradictory.authorityLocators.push({ authorityId: "candidate.policy", kind: "GATE_DEFINITION", path: "gate.txt" })
  await expectCode("PROFILE_DUPLICATE_ID", () => compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile: contradictory }), "contradictory authority")
  await expectCode("PROFILE_TARGET_INVALID", () => compileAcceptanceProfileSnapshotV1({ root, subjectSha: "0".repeat(40), profile }), "wrong target")

  await writeFile(path.join(root, "native.txt"), "dirty working tree must not matter\n", "utf8")
  const dirty = await compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile })
  assert(dirty.semanticDigest === snapshot.semanticDigest, "working-tree volatility cannot affect exact target")
}

async function adoptionBinding() {
  const profile = nativeProfile() as any
  profile.authorityMode = "ADOPTED_POLICY"
  profile.sourcePolicy = { adoptionDecisionAuthorityId: "adoption.decision" }
  profile.authorityLocators.push({ authorityId: "adoption.decision", kind: "ADOPTION_DECISION", path: "adoption.json" })
  for (const field of ["policyRequirements", "obligations", "environments", "materialTools", "materialRuntimes", "assumptions", "limitations"]) {
    for (const item of profile[field]) item.sourceAuthorityIds = []
  }
  const profileBodyDigest = computeProjectSibProfileBodyDigestV1(profile)
  const adoption = {
    schemaVersion: "ProjectSibProfileAdoptionV1",
    decisionId: "adoption.decision",
    repositoryId: profile.repositoryId,
    projectSibProfileId: profile.projectSibProfileId,
    profileVersion: profile.profileVersion,
    profileBodyDigest,
    architectureGenerationId: profile.architectureGenerationId,
    decision: "ADOPTED",
  }
  const { root, subjectSha } = await makeRepository({ "adoption.json": `${JSON.stringify(adoption)}\n` })
  const snapshot = await compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile })
  assert(snapshot.sourcePolicyIdentity.authorityMode === "ADOPTED_POLICY", "adopted mode remains explicit")
  assert(snapshot.sourcePolicyIdentity.adoptionAssertion.profileBodyDigest === profileBodyDigest, "adoption binds exact body digest")

  for (const field of ["repositoryId", "projectSibProfileId", "profileVersion", "profileBodyDigest", "architectureGenerationId"] as const) {
    const bad = { ...adoption, [field]: field === "profileBodyDigest" ? `sha256:${"f".repeat(64)}` : "mismatch" }
    const fixture = await makeRepository({ "adoption.json": `${JSON.stringify(bad)}\n` })
    await expectCode("ADOPTION_BINDING_MISMATCH", () => compileAcceptanceProfileSnapshotV1({ root: fixture.root, subjectSha: fixture.subjectSha, profile }), `adoption ${field}`)
  }
}

async function determinismAndGoldenVectors() {
  const { root, subjectSha } = await makeRepository()
  const profile = nativeProfile()
  assert(computeProjectSibProfileBodyDigestV1(profile) === "sha256:d3d9213a0df104ec64b6cc54f08c15813a842722c26a6f96c4547f019edec92f", "profile body golden vector")
  const first = await compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile })
  const second = await compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile: clone(profile) })
  assert(first.semanticDigest === second.semanticDigest, "same input same semanticDigest")
  assert(first.profileIdentity.profileDigest === "sha256:012637ad377fbea8320d0ba47c38973523262e41b88d4651fa7dfbcc895a7356", "profile digest golden vector")
  assert(first.semanticDigest === "sha256:2d0f8af59e51cd4e361092c20953fd4ab421653d2b8fb46182ccba494f07cbf6", "snapshot digest golden vector")

  const reordered = Object.fromEntries(Object.entries(profile).reverse())
  assert((await compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile: reordered })).semanticDigest === first.semanticDigest, "field order is irrelevant")
  const decomposed = clone(profile)
  decomposed.assumptions[0].text = "Cafe\u0301   policy is stable"
  assert((await compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile: decomposed })).semanticDigest === first.semanticDigest, "NFC-equivalent input")
  const changed = clone(profile)
  changed.policyRequirements[0].statement = "Preserve exact authority semantics and policy change"
  assert((await compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile: changed })).semanticDigest !== first.semanticDigest, "policy change changes digest")

  await writeFile(path.join(root, "native.txt"), "native acceptance policy v2\n", "utf8")
  await git(root, ["add", "native.txt"])
  await git(root, ["commit", "-m", "authority fixture B"], {
    GIT_AUTHOR_DATE: "2000-01-02T00:00:00Z",
    GIT_COMMITTER_DATE: "2000-01-02T00:00:00Z",
  })
  const subjectB = await git(root, ["rev-parse", "HEAD"])
  const authorityChanged = await compileAcceptanceProfileSnapshotV1({ root, subjectSha: subjectB, profile })
  assert(authorityChanged.profileIdentity.profileDigest !== first.profileIdentity.profileDigest, "native owner blob changes compiled identity")

  const volatile = clone(profile) as any
  volatile.compiledAt = "2026-09-04T00:00:00Z"
  await expectCode("PROFILE_SCHEMA_INVALID", () => compileAcceptanceProfileSnapshotV1({ root, subjectSha: subjectB, profile: volatile }), "volatile fields are illegal under MF2")
  assert(Object.isFrozen(first) && Object.isFrozen(first.obligations), "snapshot is deeply immutable")
  const tampered = clone(first) as any
  tampered.semanticDigest = `sha256:${"0".repeat(64)}`
  await expectCode("SNAPSHOT_DIGEST_MISMATCH", () => verifyAcceptanceProfileSnapshotV1(tampered), "tampered digest")
  const completeness = clone(first) as any
  completeness.DiscoveryCompletenessV1 = { status: "COMPLETE" }
  await expectCode("PROFILE_SCHEMA_INVALID", () => verifyAcceptanceProfileSnapshotV1(completeness), "completeness is not snapshot field")
}

async function unresolvedAndCardinality() {
  const { root, subjectSha } = await makeRepository()
  const base = nativeProfile()
  const unresolved = clone(base)
  unresolved.unresolvedPolicyItems = ["policy.todo"]
  await expectCode("PROFILE_POLICY_UNRESOLVED", () => compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile: unresolved }), "unresolved policy")

  const cases: Array<[string, (p: any) => void, string]> = [
    ["PROFILE_SCHEMA_INVALID", p => { p.authorityLocators = [] }, "authority locator cardinality"],
    ["PROFILE_SCHEMA_INVALID", p => { p.policyRequirements = [] }, "policy requirement cardinality"],
    ["PROFILE_SCHEMA_INVALID", p => { p.obligations = [] }, "obligation cardinality"],
    ["PROFILE_SCHEMA_INVALID", p => { p.gates = [] }, "gate cardinality"],
    ["PROFILE_SCHEMA_INVALID", p => { p.environments = [] }, "environment cardinality"],
    ["PROFILE_SCHEMA_INVALID", p => { p.coverageRequirements.capabilityClassIds = [] }, "coverage class cardinality"],
    ["PROFILE_SCHEMA_INVALID", p => { p.coverageRequirements.policyRequirementIds = [] }, "coverage policy cardinality"],
    ["PROFILE_SCHEMA_INVALID", p => { p.candidateSelectionAuthorityIds = [] }, "candidate authority cardinality"],
    ["PROFILE_SCHEMA_INVALID", p => { p.promotionAuthorityIds = [] }, "promotion authority cardinality"],
    ["PROFILE_SCHEMA_INVALID", p => { p.architectureReopenAuthorityIds = [] }, "reopen authority cardinality"],
    ["PROFILE_SCHEMA_INVALID", p => { p.repairPolicyAuthorityIds = [] }, "repair authority cardinality"],
    ["PROFILE_SIB_LEVEL_EMPTY", p => { p.obligations = p.obligations.filter((x: any) => x.sibLevel !== "SIB2") }, "required SIB level"],
    ["PROFILE_DANGLING_REF", p => { p.obligations[0].policyRequirementIds = ["policy.missing"] }, "policy ref"],
    ["PROFILE_DANGLING_REF", p => { p.obligations[0].gateIds = ["gate.missing"] }, "gate ref"],
    ["PROFILE_DANGLING_REF", p => { p.gates[0].environmentIds = ["env.missing"] }, "environment ref"],
    ["PROFILE_DANGLING_REF", p => { p.gates[0].toolRequirementIds = ["tool.missing"] }, "tool ref"],
    ["PROFILE_DANGLING_REF", p => { p.gates[0].runtimeRequirementIds = ["runtime.missing"] }, "runtime ref"],
    ["PROFILE_COVERAGE_GAP", p => { p.coverageRequirements.capabilityClassIds = ["CC-REVIEW"] }, "capability coverage"],
    ["PROFILE_AGGREGATION_INVALID", p => { p.aggregationPolicy.missingEvidenceRule = "PASS" }, "aggregation exactness"],
    ["PROFILE_DUPLICATE_ID", p => { p.gates.push(clone(p.gates[0])) }, "duplicate ID"],
  ]
  for (const [code, mutate, label] of cases) {
    const candidate = clone(base) as any
    mutate(candidate)
    await expectCode(code, () => compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile: candidate }), label)
  }

  const requiredNoGate = clone(base)
  requiredNoGate.obligations[0].gateIds = []
  await expectCode("PROFILE_SCHEMA_INVALID", () => compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile: requiredNoGate }), "REQUIRED needs gate")
  const requiredNoEnv = clone(base)
  requiredNoEnv.obligations[0].environmentIds = []
  await expectCode("PROFILE_SCHEMA_INVALID", () => compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile: requiredNoEnv }), "REQUIRED needs environment")
  const notApplicable = clone(base) as any
  Object.assign(notApplicable.obligations[0], { applicability: "NOT_APPLICABLE", gateIds: [], environmentIds: [], notApplicableRationaleAuthorityIds: [] })
  await expectCode("PROFILE_NOT_APPLICABLE_INVALID", () => compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile: notApplicable }), "NOT_APPLICABLE needs rationale")
  const unsourced = clone(base)
  unsourced.policyRequirements[0].sourceAuthorityIds = ["gate.policy"]
  await expectCode("NATIVE_BINDING_UNSOURCED", () => compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile: unsourced }), "native owner intersection")
  const unknown = clone(base) as any
  unknown.extraField = true
  await expectCode("PROFILE_SCHEMA_INVALID", () => compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile: unknown }), "unknown fields")
  const nullable = clone(base) as any
  nullable.limitations = null
  await expectCode("PROFILE_SCHEMA_INVALID", () => compileAcceptanceProfileSnapshotV1({ root, subjectSha, profile: nullable }), "null fields")
}

async function main() {
  await scalarValidation()
  await authorityModesAndResolution()
  await adoptionBinding()
  await determinismAndGoldenVectors()
  await unresolvedAndCardinality()
  console.log("acceptance profile snapshot smoke: ok")
}

await main()
