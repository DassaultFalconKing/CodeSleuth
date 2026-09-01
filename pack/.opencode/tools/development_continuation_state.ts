import { tool } from "@opencode-ai/plugin"
import { randomUUID } from "node:crypto"
import { mkdir, readFile, rename, rm, writeFile } from "node:fs/promises"
import path from "node:path"

const SHA_RE = /^[0-9a-f]{40}$/
const SAFE_ID_RE = /^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$/
const RESTRICTIONS = ["ADJACENT_TRACK", "FORBIDDEN_BY_ACTIVE_SCOPE"] as const
const PATH_SCOPE_AUTHORITIES = ["DECLARED", "NOT_DECLARED"] as const
const MAX_PROJECTION_ITEMS = 200

type Restriction = (typeof RESTRICTIONS)[number]
type PathScopeAuthority = (typeof PATH_SCOPE_AUTHORITIES)[number]
type RestrictedPath = { pattern: string; classification: Restriction; rationale: string }
type BoundEvidence = { path: string; blobHash: string; locator?: string }
type AuthorityEdge = {
  edgeId: string
  targetSha: string
  relation: string
  confidence: string
  subject?: string
  object?: string
  rationale?: string
  evidence?: BoundEvidence[]
}
type AuthorityState = { mapId: string; targetSha: string }
type GateState = { gateMapId: string; targetSha: string }
type NativeGate = {
  gateId: string
  targetSha: string
  name: string
  gateClass: string
  required: boolean
  command: string | null
  outcome: string
  nativeEvidence: string | null
  evidence: BoundEvidence[]
}
type ChangeSurfaceEntry = { path: string; blobHash: string; kinds: string[]; reasons: string[] }
type ChangeSurfaceProjection = {
  schemaVersion: 1
  surfaceMapId: string
  targetSha: string
  authority: "DERIVED_NON_AUTHORITATIVE"
  seedPaths: string[]
  entries: ChangeSurfaceEntry[]
  truncated: boolean
  recordedAt: string
}
type Packet = {
  schemaVersion: 1
  packetId: string
  targetSha: string
  authorityMapId: string
  nativeGateMapId: string
  changeSurfaceMapId: string
  planningAuthority: string[]
  activeScope: string
  objective: string
  prerequisites: string[]
  acceptedPredecessors: string[]
  requiredReading: string[]
  pathScopeAuthority: PathScopeAuthority
  allowedPaths: string[]
  forbiddenOrAdjacentPaths: RestrictedPath[]
  repoProvableChecks: string[]
  hostedCiProvableChecks: string[]
  liveRuntimeRequiredChecks: string[]
  operatorDecisionRequired: string[]
  blockers: string[]
  uncertainties: string[]
  authorityEdgeIds: string[]
  recordedAt: string
}
type StoredPacket = Omit<Packet, "pathScopeAuthority"> & { pathScopeAuthority?: PathScopeAuthority }

async function git(root: string, args: string[], allowFailure = false): Promise<{ code: number; stdout: string; stderr: string }> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text(); const stderr = await new Response(proc.stderr).text(); const code = await proc.exited
  if (code !== 0 && !allowFailure) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`)
  return { code, stdout: stdout.trim(), stderr: stderr.trim() }
}
async function readOptional(file: string): Promise<string | undefined> { try { return await readFile(file, "utf8") } catch (error: any) { if (error?.code === "ENOENT") return undefined; throw error } }
async function atomicWrite(file: string, content: string) {
  await mkdir(path.dirname(file), { recursive: true }); const temp = `${file}.${process.pid}.${randomUUID()}.tmp`
  try { await writeFile(temp, content, { encoding: "utf8", flag: "wx" }); await rename(temp, file) } catch (error) { await rm(temp, { force: true }).catch(() => undefined); throw error }
}
async function currentHead(root: string) { return (await git(root, ["rev-parse", "HEAD"])).stdout.toLowerCase() }
async function requireExactClean(root: string, sha: string) {
  if (!SHA_RE.test(sha)) throw new Error("target SHA must be a full lowercase Git SHA")
  const head = await currentHead(root); if (head !== sha) throw new Error(`CONTINUATION INVALIDATED — HEAD CHANGED: expected ${sha}, got ${head}`)
  const status = (await git(root, ["status", "--porcelain=v1", "--untracked-files=no"])).stdout
  if (status) throw new Error(`CONTINUATION INVALIDATED — TRACKED WORKTREE DIRTY:\n${status}`)
}
function baseDir(root: string) { return path.join(root, ".opencode", "state", "development-continuation") }
function packetDir(root: string, id: string) { if (!SAFE_ID_RE.test(id)) throw new Error("invalid continuation packet id"); return path.join(baseDir(root), id) }
function authorityDir(root: string, id: string) { if (!SAFE_ID_RE.test(id)) throw new Error("invalid authority map id"); return path.join(root, ".opencode", "state", "development-authority", id) }
function gateDir(root: string, id: string) { if (!SAFE_ID_RE.test(id)) throw new Error("invalid native gate map id"); return path.join(root, ".opencode", "state", "native-gates", id) }
function surfaceDir(root: string, id: string) { if (!SAFE_ID_RE.test(id)) throw new Error("invalid change surface id"); return path.join(root, ".opencode", "state", "change-surfaces", id) }
function unique(values: string[] | undefined) { return [...new Set((values ?? []).map((item) => item.trim()).filter(Boolean))] }
function validatePattern(input: string): string {
  const value = input.trim().replace(/\\/g, "/")
  if (!value || value.startsWith("/") || value.includes("\0") || value.split("/").includes("..")) throw new Error(`invalid repository path pattern: ${input}`)
  if (value.length > 300) throw new Error("repository path pattern is too long")
  return value
}
function globRegex(pattern: string): RegExp {
  let out = "^"
  for (let i = 0; i < pattern.length; i++) {
    const char = pattern[i]
    if (char === "*" && pattern[i + 1] === "*") { out += ".*"; i++; continue }
    if (char === "*") { out += "[^/]*"; continue }
    if (char === "?") { out += "[^/]"; continue }
    out += char.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
  }
  return new RegExp(out + "$")
}
function matches(pattern: string, candidate: string) { return globRegex(pattern).test(candidate) }
function parseNdjson<T>(raw: string | undefined, label: string): T[] {
  if (!raw?.trim()) return []
  return raw.split("\n").filter(Boolean).map((line, index) => { try { return JSON.parse(line) as T } catch { throw new Error(`${label} invalid JSON at line ${index + 1}`) } })
}
async function verifyBlob(root: string, evidence: BoundEvidence, label: string) {
  if (!evidence.path || !SHA_RE.test(evidence.blobHash)) throw new Error(`${label} contains malformed blob evidence`)
  const current = (await git(root, ["rev-parse", `HEAD:${evidence.path}`])).stdout.toLowerCase()
  if (current !== evidence.blobHash) throw new Error(`${label} blob changed for ${evidence.path}`)
}
async function loadAuthority(root: string, mapId: string, targetSha: string): Promise<{ state: AuthorityState; edges: AuthorityEdge[] }> {
  const dir = authorityDir(root, mapId)
  const state = JSON.parse(await readFile(path.join(dir, "state.json"), "utf8")) as AuthorityState
  if (state.targetSha !== targetSha) throw new Error("Development Authority Map target does not match continuation target")
  const edges = parseNdjson<AuthorityEdge>(await readOptional(path.join(dir, "edges.ndjson")), "authority ledger")
  if (edges.length > MAX_PROJECTION_ITEMS) throw new Error("Development Authority Map exceeds continuation projection bound")
  for (const edge of edges) for (const evidence of edge.evidence ?? []) await verifyBlob(root, evidence, "authority evidence")
  const confirmed = edges.filter((edge) => edge.targetSha === targetSha && edge.confidence === "CONFIRMED")
  if (!confirmed.some((edge) => edge.relation === "CANONICAL_PLANNING_AUTHORITY")) throw new Error("SCOPE AUTHORITY UNPROVEN: no confirmed canonical planning authority")
  if (!confirmed.some((edge) => edge.relation === "ACTIVE_IMPLEMENTATION_SCOPE")) throw new Error("SCOPE AUTHORITY UNPROVEN: no confirmed active implementation scope")
  return { state, edges }
}
async function loadGateMap(root: string, gateMapId: string, targetSha: string): Promise<{ state: GateState; gates: NativeGate[] }> {
  const dir = gateDir(root, gateMapId)
  const state = JSON.parse(await readFile(path.join(dir, "state.json"), "utf8")) as GateState
  if (state.targetSha !== targetSha) throw new Error("Native Gate Map target does not match continuation target")
  const gates = JSON.parse((await readOptional(path.join(dir, "gates.json"))) ?? "[]") as NativeGate[]
  if (!Array.isArray(gates) || gates.length > MAX_PROJECTION_ITEMS) throw new Error("Native Gate Map exceeds continuation projection bound")
  for (const gate of gates) {
    if (gate.targetSha !== targetSha) throw new Error(`native gate target mismatch: ${gate.gateId}`)
    for (const evidence of gate.evidence ?? []) await verifyBlob(root, evidence, "native gate evidence")
  }
  return { state, gates }
}
async function loadChangeSurface(root: string, surfaceMapId: string, targetSha: string): Promise<ChangeSurfaceProjection> {
  const projection = JSON.parse(await readFile(path.join(surfaceDir(root, surfaceMapId), "projection.json"), "utf8")) as ChangeSurfaceProjection
  if (projection.targetSha !== targetSha) throw new Error("Change Surface target does not match continuation target")
  if (projection.authority !== "DERIVED_NON_AUTHORITATIVE") throw new Error("Change Surface must remain derived and non-authoritative")
  if (!Array.isArray(projection.entries) || projection.entries.length > MAX_PROJECTION_ITEMS) throw new Error("Change Surface exceeds continuation projection bound")
  for (const entry of projection.entries) await verifyBlob(root, entry, "change-surface evidence")
  return projection
}
async function resolvePacketId(root: string, explicit?: string) {
  if (explicit) { if (!SAFE_ID_RE.test(explicit)) throw new Error("invalid continuation packet id"); return explicit }
  const latest = await readOptional(path.join(baseDir(root), "latest.txt")); if (!latest?.trim()) throw new Error("no Development Continuation Packet found; create one first"); return latest.trim()
}
async function loadPacket(root: string, id: string): Promise<Packet> {
  const stored = JSON.parse(await readFile(path.join(packetDir(root, id), "packet.json"), "utf8")) as StoredPacket
  const allowedPaths = Array.isArray(stored.allowedPaths) ? stored.allowedPaths : []
  const pathScopeAuthority = stored.pathScopeAuthority ?? (allowedPaths.length > 0 ? "DECLARED" : "NOT_DECLARED")
  if (!PATH_SCOPE_AUTHORITIES.includes(pathScopeAuthority)) throw new Error("invalid continuation path scope authority")
  return { ...stored, allowedPaths, pathScopeAuthority } as Packet
}
async function resolvePacketProjections(root: string, packet: Packet) {
  const authority = await loadAuthority(root, packet.authorityMapId, packet.targetSha)
  const gateMap = await loadGateMap(root, packet.nativeGateMapId, packet.targetSha)
  const changeSurface = await loadChangeSurface(root, packet.changeSurfaceMapId, packet.targetSha)
  const edgeIds = new Set(packet.authorityEdgeIds)
  const authorityEvidence = authority.edges.filter((edge) => edgeIds.has(edge.edgeId))
  if (authorityEvidence.length !== edgeIds.size) throw new Error("one or more continuation authority edges disappeared")
  return { authority, gateMap, changeSurface, authorityEvidence }
}

export const save_packet = tool({
  description: "Persist one exact-head continuation packet only after repository-native planning, active-scope, gate and derived change-surface evidence are confirmed.",
  args: {
    targetSha: tool.schema.string().optional(), authorityMapId: tool.schema.string().min(1), nativeGateMapId: tool.schema.string().min(1), changeSurfaceMapId: tool.schema.string().min(1),
    planningAuthority: tool.schema.array(tool.schema.string()).min(1), activeScope: tool.schema.string().min(1), objective: tool.schema.string().min(1),
    prerequisites: tool.schema.array(tool.schema.string()).optional(), acceptedPredecessors: tool.schema.array(tool.schema.string()).optional(), requiredReading: tool.schema.array(tool.schema.string()).optional(),
    allowedPaths: tool.schema.array(tool.schema.string()).optional(),
    forbiddenOrAdjacentPaths: tool.schema.array(tool.schema.object({ pattern: tool.schema.string().min(1), classification: tool.schema.enum(RESTRICTIONS), rationale: tool.schema.string().min(1) })).optional(),
    repoProvableChecks: tool.schema.array(tool.schema.string()).optional(), hostedCiProvableChecks: tool.schema.array(tool.schema.string()).optional(),
    liveRuntimeRequiredChecks: tool.schema.array(tool.schema.string()).optional(), operatorDecisionRequired: tool.schema.array(tool.schema.string()).optional(), blockers: tool.schema.array(tool.schema.string()).optional(), uncertainties: tool.schema.array(tool.schema.string()).optional(), authorityEdgeIds: tool.schema.array(tool.schema.string()).min(1),
  },
  async execute(args, context) {
    const root = context.worktree; const targetSha = (args.targetSha ?? await currentHead(root)).trim().toLowerCase(); await requireExactClean(root, targetSha)
    const authority = await loadAuthority(root, args.authorityMapId, targetSha); await loadGateMap(root, args.nativeGateMapId, targetSha); await loadChangeSurface(root, args.changeSurfaceMapId, targetSha)
    const edgeIds = unique(args.authorityEdgeIds); const known = new Set(authority.edges.map((edge) => edge.edgeId)); for (const id of edgeIds) if (!known.has(id)) throw new Error(`authority edge not found: ${id}`)
    const allowedPaths = unique(args.allowedPaths).map(validatePattern)
    const pathScopeAuthority: PathScopeAuthority = allowedPaths.length > 0 ? "DECLARED" : "NOT_DECLARED"
    const restricted: RestrictedPath[] = (args.forbiddenOrAdjacentPaths ?? []).map((item) => ({ pattern: validatePattern(item.pattern), classification: item.classification, rationale: item.rationale.trim() }))
    const packetId = `DCP-${new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)}-${targetSha.slice(0, 12)}-${randomUUID().slice(0, 8)}`
    const packet: Packet = {
      schemaVersion: 1, packetId, targetSha, authorityMapId: args.authorityMapId, nativeGateMapId: args.nativeGateMapId, changeSurfaceMapId: args.changeSurfaceMapId,
      planningAuthority: unique(args.planningAuthority), activeScope: args.activeScope.trim(), objective: args.objective.trim(), prerequisites: unique(args.prerequisites), acceptedPredecessors: unique(args.acceptedPredecessors), requiredReading: unique(args.requiredReading),
      pathScopeAuthority, allowedPaths, forbiddenOrAdjacentPaths: restricted, repoProvableChecks: unique(args.repoProvableChecks), hostedCiProvableChecks: unique(args.hostedCiProvableChecks), liveRuntimeRequiredChecks: unique(args.liveRuntimeRequiredChecks), operatorDecisionRequired: unique(args.operatorDecisionRequired), blockers: unique(args.blockers), uncertainties: unique(args.uncertainties), authorityEdgeIds: edgeIds, recordedAt: new Date().toISOString(),
    }
    await mkdir(baseDir(root), { recursive: true }); await mkdir(packetDir(root, packetId), { recursive: false }); await atomicWrite(path.join(packetDir(root, packetId), "packet.json"), `${JSON.stringify(packet, null, 2)}\n`); await atomicWrite(path.join(baseDir(root), "latest.txt"), `${packetId}\n`)
    return JSON.stringify(packet, null, 2)
  },
})

export const load = tool({
  description: "Load and revalidate one Development Continuation Packet and expose bounded resolved authority, gate and change-surface projections.",
  args: { packetId: tool.schema.string().optional() },
  async execute(args, context) {
    const root = context.worktree; const id = await resolvePacketId(root, args.packetId); const packet = await loadPacket(root, id); await requireExactClean(root, packet.targetSha)
    const projections = await resolvePacketProjections(root, packet)
    return JSON.stringify({ ...packet, authorityIntegrity: "PASS", scopeAuthority: "CONFIRMED", changeSurface: projections.changeSurface, nativeGates: projections.gateMap.gates, authorityEvidence: projections.authorityEvidence }, null, 2)
  },
})

export const scope_guard = tool({
  description: "Compare proposed repository paths with one accepted continuation packet. The guard never expands scope.",
  args: { packetId: tool.schema.string().optional(), proposedPaths: tool.schema.array(tool.schema.string()).min(1).max(500) },
  async execute(args, context) {
    const root = context.worktree; const id = await resolvePacketId(root, args.packetId); const packet = await loadPacket(root, id); await requireExactClean(root, packet.targetSha)
    try { await resolvePacketProjections(root, packet) } catch (error) {
      return JSON.stringify({ packetId: id, targetSha: packet.targetSha, overall: "SCOPE_AUTHORITY_UNPROVEN", reason: String(error), paths: [] }, null, 2)
    }
    const results = args.proposedPaths.map((raw) => {
      const candidate = validatePattern(raw)
      const restricted = packet.forbiddenOrAdjacentPaths.find((item) => matches(item.pattern, candidate))
      if (restricted) return { path: candidate, classification: restricted.classification, matchedPattern: restricted.pattern, rationale: restricted.rationale }
      if (packet.pathScopeAuthority === "NOT_DECLARED") return { path: candidate, classification: "SCOPE_AUTHORITY_UNPROVEN", matchedPattern: null, rationale: "active repository authority does not declare positive allowed path patterns" }
      const allowed = packet.allowedPaths.find((pattern) => matches(pattern, candidate))
      if (allowed) return { path: candidate, classification: "IN_SCOPE", matchedPattern: allowed, rationale: "declared by accepted continuation packet" }
      return { path: candidate, classification: "UNDECLARED", matchedPattern: null, rationale: "path is not declared by the active scope; scope is not auto-expanded" }
    })
    const overall = results.some((item) => item.classification === "FORBIDDEN_BY_ACTIVE_SCOPE") ? "FORBIDDEN_BY_ACTIVE_SCOPE" : results.some((item) => item.classification === "ADJACENT_TRACK") ? "ADJACENT_TRACK" : results.some((item) => item.classification === "SCOPE_AUTHORITY_UNPROVEN") ? "SCOPE_AUTHORITY_UNPROVEN" : results.every((item) => item.classification === "IN_SCOPE") ? "IN_SCOPE" : "UNDECLARED"
    return JSON.stringify({ packetId: id, targetSha: packet.targetSha, overall, paths: results }, null, 2)
  },
})
