import { tool } from "@opencode-ai/plugin"
import { randomUUID } from "node:crypto"
import { mkdir, readFile, rename, rm, writeFile } from "node:fs/promises"
import path from "node:path"

const SHA_RE = /^[0-9a-f]{40}$/
const SAFE_ID_RE = /^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$/
const CONTRACT_ID_RE = /^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$/
const TRIANGULATION = ["AGREE", "CODE_AHEAD", "DOC_AHEAD", "TEST_AHEAD", "CONTRADICTED", "UNPROVEN"] as const
const DECISIONS = ["adopt", "adopt_unproven", "reject", "defer"] as const
const REGISTRY_PATH = "docs/protected-capabilities.json"

type TriangulationStatus = (typeof TRIANGULATION)[number]
type Decision = (typeof DECISIONS)[number]
type EvidenceRef = { path: string; blobHash: string }

type BootstrapState = {
  schemaVersion: 1
  bootstrapId: string
  targetSha: string
  objective: string
  startedAt: string
  updatedAt: string
  status: "discovering" | "adjudicating" | "materialized"
  materializedRegistryPath: string | null
}

type Candidate = {
  schemaVersion: 1
  type: "contract_candidate"
  candidateId: string
  contractId: string
  targetSha: string
  statement: string
  capabilityClass: string
  capabilityClassId: string
  triangulationStatus: TriangulationStatus
  codeEvidence: EvidenceRef[]
  docEvidence: EvidenceRef[]
  testEvidence: EvidenceRef[]
  affectedPaths: string[]
  dependsOn: string[]
  forbiddenRegressions: Array<{ id: string; mustNot: string; proof: EvidenceRef[] }>
  recordedAt: string
}

type DecisionEvent = {
  schemaVersion: 1
  type: "bootstrap_decision"
  eventId: string
  candidateId: string
  contractId: string
  targetSha: string
  decision: Decision
  rationale: string
  userApprovalStatement: string
  recordedAt: string
}

async function git(root: string, args: string[], allowFailure = false): Promise<{ code: number; stdout: string; stderr: string }> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  const code = await proc.exited
  if (code !== 0 && !allowFailure) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`)
  return { code, stdout: stdout.trim(), stderr: stderr.trim() }
}

async function currentHead(root: string): Promise<string> {
  return (await git(root, ["rev-parse", "HEAD"])).stdout
}

function baseDir(root: string): string {
  return path.join(root, ".opencode", "state", "contract-bootstrap")
}

function bootstrapDir(root: string, bootstrapId: string): string {
  if (!SAFE_ID_RE.test(bootstrapId)) throw new Error("invalid bootstrap id")
  return path.join(baseDir(root), bootstrapId)
}

async function readOptional(file: string): Promise<string | undefined> {
  try {
    return await readFile(file, "utf8")
  } catch (error: any) {
    if (error?.code === "ENOENT") return undefined
    throw error
  }
}

async function atomicWrite(file: string, content: string): Promise<void> {
  await mkdir(path.dirname(file), { recursive: true })
  const temp = `${file}.${process.pid}.${randomUUID()}.tmp`
  try {
    await writeFile(temp, content, { encoding: "utf8", flag: "wx" })
    await rename(temp, file)
  } catch (error) {
    await rm(temp, { force: true }).catch(() => undefined)
    throw error
  }
}

function parseNdjson<T>(raw: string | undefined, label: string): T[] {
  if (!raw?.trim()) return []
  const rows: T[] = []
  for (const [index, line] of raw.split("\n").entries()) {
    if (!line) continue
    try {
      rows.push(JSON.parse(line) as T)
    } catch {
      throw new Error(`${label} contains invalid JSON at line ${index + 1}`)
    }
  }
  return rows
}

async function loadState(root: string, bootstrapId: string): Promise<BootstrapState> {
  const raw = await readFile(path.join(bootstrapDir(root, bootstrapId), "state.json"), "utf8")
  return JSON.parse(raw) as BootstrapState
}

async function saveState(root: string, state: BootstrapState): Promise<void> {
  state.updatedAt = new Date().toISOString()
  await atomicWrite(path.join(bootstrapDir(root, state.bootstrapId), "state.json"), `${JSON.stringify(state, null, 2)}\n`)
}

async function resolveBootstrapId(root: string, explicit?: string): Promise<string> {
  if (explicit) {
    if (!SAFE_ID_RE.test(explicit)) throw new Error("invalid bootstrap id")
    return explicit
  }
  const latest = await readOptional(path.join(baseDir(root), "latest.txt"))
  if (!latest?.trim()) throw new Error("no contract bootstrap session found; start one first")
  return latest.trim()
}

async function candidates(root: string, bootstrapId: string): Promise<Candidate[]> {
  return parseNdjson<Candidate>(await readOptional(path.join(bootstrapDir(root, bootstrapId), "candidates.ndjson")), "candidate ledger")
}

async function decisions(root: string, bootstrapId: string): Promise<DecisionEvent[]> {
  return parseNdjson<DecisionEvent>(await readOptional(path.join(bootstrapDir(root, bootstrapId), "decisions.ndjson")), "decision ledger")
}

async function appendJsonLine(file: string, value: unknown): Promise<void> {
  await mkdir(path.dirname(file), { recursive: true })
  const existing = await readOptional(file)
  await atomicWrite(file, `${existing ?? ""}${JSON.stringify(value)}\n`)
}

function uniqueStrings(values: string[] | undefined, label: string): string[] {
  const result = [...new Set((values ?? []).map((value) => value.trim()).filter(Boolean))]
  for (const value of result) {
    if (value.includes("\0")) throw new Error(`${label} contains NUL`)
  }
  return result
}

function normalizeRepoPath(root: string, input: string): string {
  const absoluteRoot = path.resolve(root)
  const absolute = path.resolve(root, input)
  const prefix = absoluteRoot + path.sep
  if (absolute !== absoluteRoot && !absolute.startsWith(prefix)) throw new Error(`path escapes worktree: ${input}`)
  const relative = path.relative(absoluteRoot, absolute).replace(/\\/g, "/")
  if (!relative || relative === ".") throw new Error("evidence path must name a repository file")
  return relative
}

async function requireCleanTrackedWorktree(root: string): Promise<void> {
  const status = await git(root, ["status", "--porcelain=v1", "--untracked-files=no"])
  if (status.stdout) {
    throw new Error(`CONTRACT BOOTSTRAP INVALIDATED — TRACKED WORKTREE DIRTY:\n${status.stdout}`)
  }
}

async function trackedBlob(root: string, relative: string, label: string): Promise<string> {
  const tracked = await git(root, ["ls-files", "--error-unmatch", "--", relative], true)
  if (tracked.code !== 0) throw new Error(`${label} path is not tracked: ${relative}`)
  const blob = (await git(root, ["rev-parse", `HEAD:${relative}`], true)).stdout.toLowerCase()
  if (!SHA_RE.test(blob)) throw new Error(`${label} path is not a regular tracked blob at exact HEAD: ${relative}`)
  return blob
}

async function validateEvidencePaths(root: string, values: string[], label: string): Promise<EvidenceRef[]> {
  const result: EvidenceRef[] = []
  for (const relative of uniqueStrings(values, label).map((value) => normalizeRepoPath(root, value))) {
    result.push({ path: relative, blobHash: await trackedBlob(root, relative, label) })
  }
  return result
}

async function verifyEvidenceRef(root: string, evidence: EvidenceRef, label: string): Promise<void> {
  if (!evidence || typeof evidence.path !== "string" || !SHA_RE.test(evidence.blobHash)) {
    throw new Error(`${label} contains invalid blob-bound evidence`)
  }
  const relative = normalizeRepoPath(root, evidence.path)
  const current = await trackedBlob(root, relative, label)
  if (current !== evidence.blobHash) {
    throw new Error(`${label} blob changed for ${relative}: expected ${evidence.blobHash}, got ${current}`)
  }
}

async function verifyCandidateEvidence(root: string, candidate: Candidate): Promise<void> {
  if (candidate.targetSha !== await currentHead(root)) {
    throw new Error(`candidate ${candidate.contractId} no longer matches exact HEAD`)
  }
  for (const evidence of candidate.codeEvidence) await verifyEvidenceRef(root, evidence, "code evidence")
  for (const evidence of candidate.docEvidence) await verifyEvidenceRef(root, evidence, "doc evidence")
  for (const evidence of candidate.testEvidence) await verifyEvidenceRef(root, evidence, "test evidence")
  for (const item of candidate.forbiddenRegressions) {
    for (const evidence of item.proof) await verifyEvidenceRef(root, evidence, `proof for ${item.id}`)
  }
}

async function requireExactHead(root: string, targetSha: string): Promise<void> {
  if (!SHA_RE.test(targetSha)) throw new Error("target SHA must be a full lowercase Git SHA")
  const head = await currentHead(root)
  if (head !== targetSha) throw new Error(`CONTRACT BOOTSTRAP INVALIDATED — HEAD CHANGED: expected ${targetSha}, got ${head}`)
}

async function requireExactCleanTarget(root: string, targetSha: string): Promise<void> {
  await requireExactHead(root, targetSha)
  await requireCleanTrackedWorktree(root)
}

function latestDecisionFor(candidateId: string, all: DecisionEvent[]): DecisionEvent | undefined {
  return [...all].reverse().find((item) => item.candidateId === candidateId)
}

function adoptedStatus(candidate: Candidate, decision: DecisionEvent): "implemented" | "experimental" {
  if (decision.decision === "adopt" && candidate.triangulationStatus === "AGREE") return "implemented"
  if (decision.decision === "adopt_unproven" && candidate.triangulationStatus === "UNPROVEN") return "experimental"
  throw new Error(`${candidate.contractId} cannot be materialized: ${decision.decision} is incompatible with ${candidate.triangulationStatus}`)
}

async function readRegistry(root: string): Promise<any | null> {
  const absolute = path.join(root, ...REGISTRY_PATH.split("/"))
  const raw = await readOptional(absolute)
  if (raw === undefined) return null
  const tracked = await git(root, ["ls-files", "--error-unmatch", "--", REGISTRY_PATH], true)
  if (tracked.code !== 0) throw new Error(`${REGISTRY_PATH} exists but is untracked; refusing to overwrite it`)
  const parsed = JSON.parse(raw)
  if (parsed?.schema_version !== 1 || parsed?.registry !== "codesleuth-protected-capabilities" || !Array.isArray(parsed?.contracts)) {
    throw new Error(`${REGISTRY_PATH} is not a supported Protected Capability Registry`)
  }
  return parsed
}

function evidencePaths(items: EvidenceRef[]): string[] {
  return items.map((item) => item.path)
}

function evidenceBlobMap(candidate: Candidate) {
  return {
    code: candidate.codeEvidence,
    docs: candidate.docEvidence,
    tests: candidate.testEvidence,
    forbidden_regression_proof: candidate.forbiddenRegressions.flatMap((item) => item.proof.map((proof) => ({ regression_id: item.id, ...proof }))),
  }
}

function contractFromCandidate(candidate: Candidate, decision: DecisionEvent, targetSha: string) {
  return {
    id: candidate.contractId,
    capability_class: candidate.capabilityClass,
    capability_class_id: candidate.capabilityClassId,
    status: adoptedStatus(candidate, decision),
    introduced: `brownfield-bootstrap:${targetSha.slice(0, 12)}`,
    protected_at: null,
    public_contract: [candidate.statement],
    code_evidence: evidencePaths(candidate.codeEvidence),
    doc_evidence: evidencePaths(candidate.docEvidence),
    test_evidence: evidencePaths(candidate.testEvidence),
    affected_paths: candidate.affectedPaths,
    depends_on: candidate.dependsOn,
    forbidden_regressions: candidate.forbiddenRegressions.map((item) => ({
      id: item.id,
      sib_origin: null,
      must_not: item.mustNot,
      proof: evidencePaths(item.proof),
    })),
    bootstrap_provenance: {
      candidate_id: candidate.candidateId,
      triangulation_status: candidate.triangulationStatus,
      decision_event_id: decision.eventId,
      exact_sha: targetSha,
      evidence_blobs: evidenceBlobMap(candidate),
      note: "Brownfield adoption records observed/user-approved contract meaning; it does not confer SIB acceptance or PROTECTED status.",
    },
  }
}

export const start = tool({
  description: "Start a durable exact-head brownfield contract-discovery session. Discovery records candidates only; it does not create repository contracts.",
  args: {
    objective: tool.schema.string().min(1),
    targetSha: tool.schema.string().optional(),
  },
  async execute(args, context) {
    const root = context.worktree
    const head = await currentHead(root)
    const targetSha = (args.targetSha ?? head).trim().toLowerCase()
    await requireExactCleanTarget(root, targetSha)
    const stamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)
    const bootstrapId = `CB-${stamp}-${targetSha.slice(0, 12)}-${randomUUID().slice(0, 8)}`
    await mkdir(baseDir(root), { recursive: true })
    const dir = bootstrapDir(root, bootstrapId)
    await mkdir(dir, { recursive: false })
    const now = new Date().toISOString()
    const state: BootstrapState = {
      schemaVersion: 1,
      bootstrapId,
      targetSha,
      objective: args.objective.trim(),
      startedAt: now,
      updatedAt: now,
      status: "discovering",
      materializedRegistryPath: null,
    }
    await saveState(root, state)
    await atomicWrite(path.join(baseDir(root), "latest.txt"), `${bootstrapId}\n`)
    return JSON.stringify(state, null, 2)
  },
})

export const record_candidate = tool({
  description: "Record one exact-blob-bound possible brownfield contract. Candidate status is not contract authority and never changes the tracked registry.",
  args: {
    bootstrapId: tool.schema.string().optional(),
    contractId: tool.schema.string().min(1),
    statement: tool.schema.string().min(1),
    capabilityClass: tool.schema.string().min(1),
    capabilityClassId: tool.schema.string().min(1),
    triangulationStatus: tool.schema.enum(TRIANGULATION),
    codeEvidence: tool.schema.array(tool.schema.string()).optional(),
    docEvidence: tool.schema.array(tool.schema.string()).optional(),
    testEvidence: tool.schema.array(tool.schema.string()).optional(),
    affectedPaths: tool.schema.array(tool.schema.string()).min(1),
    dependsOn: tool.schema.array(tool.schema.string()).optional(),
    forbiddenRegressions: tool.schema.array(tool.schema.object({
      id: tool.schema.string().min(1),
      mustNot: tool.schema.string().min(1),
      proof: tool.schema.array(tool.schema.string()).optional(),
    })).min(1),
  },
  async execute(args, context) {
    const root = context.worktree
    const bootstrapId = await resolveBootstrapId(root, args.bootstrapId)
    const state = await loadState(root, bootstrapId)
    if (state.status === "materialized") throw new Error("bootstrap session is already materialized")
    await requireExactCleanTarget(root, state.targetSha)
    const contractId = args.contractId.trim()
    if (!CONTRACT_ID_RE.test(contractId)) throw new Error("contract id contains unsupported characters")
    const all = await candidates(root, bootstrapId)
    if (all.some((item) => item.contractId === contractId)) throw new Error(`candidate contract already exists: ${contractId}`)
    const codeEvidence = await validateEvidencePaths(root, args.codeEvidence ?? [], "code evidence")
    const docEvidence = await validateEvidencePaths(root, args.docEvidence ?? [], "doc evidence")
    const testEvidence = await validateEvidencePaths(root, args.testEvidence ?? [], "test evidence")
    if (codeEvidence.length + docEvidence.length + testEvidence.length === 0) throw new Error("candidate requires at least one exact tracked evidence path")
    const affectedPaths = uniqueStrings(args.affectedPaths, "affected paths")
    const forbiddenRegressions = []
    const frIds = new Set<string>()
    for (const raw of args.forbiddenRegressions) {
      const id = raw.id.trim()
      if (!SAFE_ID_RE.test(id)) throw new Error(`invalid forbidden-regression id: ${id}`)
      if (frIds.has(id)) throw new Error(`duplicate forbidden-regression id: ${id}`)
      frIds.add(id)
      forbiddenRegressions.push({
        id,
        mustNot: raw.mustNot.trim(),
        proof: await validateEvidencePaths(root, raw.proof ?? [], `proof for ${id}`),
      })
    }
    const candidate: Candidate = {
      schemaVersion: 1,
      type: "contract_candidate",
      candidateId: `C-${randomUUID()}`,
      contractId,
      targetSha: state.targetSha,
      statement: args.statement.trim(),
      capabilityClass: args.capabilityClass.trim(),
      capabilityClassId: args.capabilityClassId.trim(),
      triangulationStatus: args.triangulationStatus,
      codeEvidence,
      docEvidence,
      testEvidence,
      affectedPaths,
      dependsOn: uniqueStrings(args.dependsOn, "dependencies"),
      forbiddenRegressions,
      recordedAt: new Date().toISOString(),
    }
    await appendJsonLine(path.join(bootstrapDir(root, bootstrapId), "candidates.ndjson"), candidate)
    state.status = "adjudicating"
    await saveState(root, state)
    return JSON.stringify(candidate, null, 2)
  },
})

export const record_decision = tool({
  description: "Record an explicit user adjudication for one discovered contract candidate. The approval statement must quote or summarize the user's current instruction.",
  args: {
    bootstrapId: tool.schema.string().optional(),
    candidateId: tool.schema.string().min(1),
    decision: tool.schema.enum(DECISIONS),
    rationale: tool.schema.string().min(1),
    userApprovalStatement: tool.schema.string().min(1),
  },
  async execute(args, context) {
    const root = context.worktree
    const bootstrapId = await resolveBootstrapId(root, args.bootstrapId)
    const state = await loadState(root, bootstrapId)
    if (state.status === "materialized") throw new Error("bootstrap session is already materialized")
    await requireExactCleanTarget(root, state.targetSha)
    const candidate = (await candidates(root, bootstrapId)).find((item) => item.candidateId === args.candidateId)
    if (!candidate) throw new Error(`candidate not found: ${args.candidateId}`)
    await verifyCandidateEvidence(root, candidate)
    if (args.decision === "adopt" && candidate.triangulationStatus !== "AGREE") throw new Error(`adopt requires AGREE triangulation; ${candidate.contractId} is ${candidate.triangulationStatus}`)
    if (args.decision === "adopt_unproven" && candidate.triangulationStatus !== "UNPROVEN") throw new Error(`adopt_unproven requires UNPROVEN triangulation; ${candidate.contractId} is ${candidate.triangulationStatus}`)
    if (["CODE_AHEAD", "DOC_AHEAD", "TEST_AHEAD", "CONTRADICTED"].includes(candidate.triangulationStatus) && ["adopt", "adopt_unproven"].includes(args.decision)) throw new Error(`contract drift ${candidate.triangulationStatus} must be resolved before adoption`)
    const event: DecisionEvent = {
      schemaVersion: 1,
      type: "bootstrap_decision",
      eventId: `D-${randomUUID()}`,
      candidateId: candidate.candidateId,
      contractId: candidate.contractId,
      targetSha: state.targetSha,
      decision: args.decision,
      rationale: args.rationale.trim(),
      userApprovalStatement: args.userApprovalStatement.trim(),
      recordedAt: new Date().toISOString(),
    }
    await appendJsonLine(path.join(bootstrapDir(root, bootstrapId), "decisions.ndjson"), event)
    return JSON.stringify(event, null, 2)
  },
})

export const load = tool({
  description: "Load and revalidate one durable brownfield contract-bootstrap session with candidate and latest user-decision state.",
  args: { bootstrapId: tool.schema.string().optional() },
  async execute(args, context) {
    const root = context.worktree
    const bootstrapId = await resolveBootstrapId(root, args.bootstrapId)
    const state = await loadState(root, bootstrapId)
    await requireExactCleanTarget(root, state.targetSha)
    const allCandidates = await candidates(root, bootstrapId)
    for (const candidate of allCandidates) await verifyCandidateEvidence(root, candidate)
    const allDecisions = await decisions(root, bootstrapId)
    return JSON.stringify({
      ...state,
      candidates: allCandidates.map((candidate) => ({ ...candidate, latestDecision: latestDecisionFor(candidate.candidateId, allDecisions) ?? null })),
      decisionCount: allDecisions.length,
      evidenceIntegrity: "PASS",
    }, null, 2)
  },
})

export const materialize = tool({
  description: "Materialize only explicitly user-adopted brownfield candidates into the tracked Protected Capability Registry. Never confers SIB acceptance or PROTECTED status.",
  args: { bootstrapId: tool.schema.string().optional() },
  async execute(args, context) {
    const root = context.worktree
    const bootstrapId = await resolveBootstrapId(root, args.bootstrapId)
    const state = await loadState(root, bootstrapId)
    if (state.status === "materialized") throw new Error("bootstrap session is already materialized")
    await requireExactCleanTarget(root, state.targetSha)
    const allCandidates = await candidates(root, bootstrapId)
    for (const candidate of allCandidates) await verifyCandidateEvidence(root, candidate)
    const allDecisions = await decisions(root, bootstrapId)
    const adopted = allCandidates.flatMap((candidate) => {
      const decision = latestDecisionFor(candidate.candidateId, allDecisions)
      if (!decision || !["adopt", "adopt_unproven"].includes(decision.decision)) return []
      return [{ candidate, decision }]
    })
    if (adopted.length === 0) throw new Error("no explicitly adopted contract candidates to materialize")

    const existing = await readRegistry(root)
    const existingContracts = existing?.contracts ?? []
    const existingIds = new Set(existingContracts.map((item: any) => item.id))
    for (const { candidate } of adopted) {
      if (existingIds.has(candidate.contractId)) throw new Error(`refusing to overwrite existing contract: ${candidate.contractId}`)
    }
    const futureIds = new Set([...existingIds, ...adopted.map(({ candidate }) => candidate.contractId)])
    for (const { candidate } of adopted) {
      for (const dependency of candidate.dependsOn) {
        if (!futureIds.has(dependency)) throw new Error(`${candidate.contractId} depends on non-materialized contract ${dependency}`)
      }
    }

    const newContracts = adopted.map(({ candidate, decision }) => contractFromCandidate(candidate, decision, state.targetSha))
    const registry = existing ?? {
      schema_version: 1,
      registry: "codesleuth-protected-capabilities",
      profile: "generic",
      authority: "target-local user-approved brownfield contract bootstrap",
      target_authority: {
        kind: "brownfield-bootstrap",
        bootstrap_id: bootstrapId,
        exact_sha: state.targetSha,
      },
      bootstrap_note: "Discovered behavior becomes a tracked contract only after explicit user adjudication. Brownfield bootstrap never grants SIB acceptance or PROTECTED status.",
      status_values: ["experimental", "implemented", "sib1_accepted", "sib2_integrated", "protected", "deprecated", "removed"],
      capability_classes: [],
      contracts: [],
    }
    registry.contracts = [...existingContracts, ...newContracts].sort((a: any, b: any) => String(a.id).localeCompare(String(b.id)))
    registry.capability_classes = [...new Set([
      ...(Array.isArray(registry.capability_classes) ? registry.capability_classes : []),
      ...registry.contracts.map((item: any) => item.capability_class).filter(Boolean),
    ])].sort()
    registry.last_brownfield_bootstrap = {
      bootstrap_id: bootstrapId,
      exact_sha: state.targetSha,
      adopted_contracts: newContracts.map((item: any) => item.id),
    }
    await atomicWrite(path.join(root, ...REGISTRY_PATH.split("/")), `${JSON.stringify(registry, null, 2)}\n`)
    state.status = "materialized"
    state.materializedRegistryPath = REGISTRY_PATH
    await saveState(root, state)
    return JSON.stringify({
      bootstrapId,
      targetSha: state.targetSha,
      registryPath: REGISTRY_PATH,
      adoptedContracts: newContracts.map((item: any) => ({ id: item.id, status: item.status })),
      worktreeIdentity: "NEW_UNCOMMITTED_CANDIDATE",
      reminder: "Materialization records user-approved brownfield contracts only; it does not confer SIB1/SIB2 acceptance or PROTECTED status. Commit the tracked registry change before treating it as a new exact target.",
    }, null, 2)
  },
})
