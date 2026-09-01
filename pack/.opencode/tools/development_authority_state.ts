import { tool } from "@opencode-ai/plugin"
import { randomUUID } from "node:crypto"
import { mkdir, readFile, rename, rm, writeFile } from "node:fs/promises"
import path from "node:path"

const SHA_RE = /^[0-9a-f]{40}$/
const SAFE_ID_RE = /^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$/
const RELATIONS = [
  "CANONICAL_PLANNING_AUTHORITY",
  "ACTIVE_IMPLEMENTATION_SCOPE",
  "NORMATIVE_ARCHITECTURE",
  "ACCEPTANCE_AUTHORITY",
  "ACCEPTED_PREDECESSOR",
  "SUPPORTING_EVIDENCE",
  "SUPERSEDES",
  "SUPERSEDED_BY",
  "HISTORICAL_ARCHIVE",
  "ADJACENT_PARALLEL_TRACK",
  "FORBIDDEN_COMPETING_AUTHORITY",
] as const
const CONFIDENCE = ["CONFIRMED", "PROBABLE", "UNPROVEN"] as const

type Relation = (typeof RELATIONS)[number]
type Confidence = (typeof CONFIDENCE)[number]
type Evidence = { path: string; blobHash: string; locator: string }
type AuthorityEdge = {
  schemaVersion: 1
  type: "development_authority_edge"
  edgeId: string
  targetSha: string
  relation: Relation
  subject: string
  object: string
  confidence: Confidence
  rationale: string
  evidence: Evidence[]
  recordedAt: string
}
type AuthorityState = {
  schemaVersion: 1
  mapId: string
  targetSha: string
  objective: string
  startedAt: string
  updatedAt: string
}

async function git(root: string, args: string[], allowFailure = false): Promise<{ code: number; stdout: string; stderr: string }> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  const code = await proc.exited
  if (code !== 0 && !allowFailure) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`)
  return { code, stdout: stdout.trim(), stderr: stderr.trim() }
}

function baseDir(root: string) { return path.join(root, ".opencode", "state", "development-authority") }
function mapDir(root: string, mapId: string) {
  if (!SAFE_ID_RE.test(mapId)) throw new Error("invalid authority map id")
  return path.join(baseDir(root), mapId)
}
async function currentHead(root: string) { return (await git(root, ["rev-parse", "HEAD"])).stdout.toLowerCase() }
async function requireExactClean(root: string, targetSha: string) {
  if (!SHA_RE.test(targetSha)) throw new Error("target SHA must be a full lowercase Git SHA")
  const head = await currentHead(root)
  if (head !== targetSha) throw new Error(`DEVELOPMENT AUTHORITY INVALIDATED — HEAD CHANGED: expected ${targetSha}, got ${head}`)
  const status = (await git(root, ["status", "--porcelain=v1", "--untracked-files=no"])).stdout
  if (status) throw new Error(`DEVELOPMENT AUTHORITY INVALIDATED — TRACKED WORKTREE DIRTY:\n${status}`)
}
async function readOptional(file: string): Promise<string | undefined> {
  try { return await readFile(file, "utf8") } catch (error: any) { if (error?.code === "ENOENT") return undefined; throw error }
}
async function atomicWrite(file: string, content: string) {
  await mkdir(path.dirname(file), { recursive: true })
  const temp = `${file}.${process.pid}.${randomUUID()}.tmp`
  try { await writeFile(temp, content, { encoding: "utf8", flag: "wx" }); await rename(temp, file) }
  catch (error) { await rm(temp, { force: true }).catch(() => undefined); throw error }
}
function normalizeRepoPath(root: string, input: string): string {
  const absoluteRoot = path.resolve(root)
  const absolute = path.resolve(root, input)
  if (absolute !== absoluteRoot && !absolute.startsWith(absoluteRoot + path.sep)) throw new Error(`path escapes worktree: ${input}`)
  const relative = path.relative(absoluteRoot, absolute).replace(/\\/g, "/")
  if (!relative || relative === ".") throw new Error("evidence path must name a repository file")
  return relative
}
async function bindEvidence(root: string, raw: { path: string; locator: string }, label: string): Promise<Evidence> {
  const relative = normalizeRepoPath(root, raw.path)
  const tracked = await git(root, ["ls-files", "--error-unmatch", "--", relative], true)
  if (tracked.code !== 0) throw new Error(`${label} is not tracked: ${relative}`)
  const blobHash = (await git(root, ["rev-parse", `HEAD:${relative}`])).stdout.toLowerCase()
  if (!SHA_RE.test(blobHash)) throw new Error(`${label} is not a regular tracked blob: ${relative}`)
  const locator = raw.locator.trim()
  if (!locator || locator.length > 240) throw new Error(`${label} requires a bounded non-empty locator`)
  return { path: relative, blobHash, locator }
}
async function verifyEvidence(root: string, evidence: Evidence) {
  const rebound = await bindEvidence(root, evidence, "authority evidence")
  if (rebound.blobHash !== evidence.blobHash) throw new Error(`authority evidence blob changed for ${evidence.path}`)
}
function parseLines<T>(raw: string | undefined, label: string): T[] {
  if (!raw?.trim()) return []
  return raw.split("\n").filter(Boolean).map((line, index) => {
    try { return JSON.parse(line) as T } catch { throw new Error(`${label} contains invalid JSON at line ${index + 1}`) }
  })
}
async function loadState(root: string, mapId: string): Promise<AuthorityState> {
  return JSON.parse(await readFile(path.join(mapDir(root, mapId), "state.json"), "utf8")) as AuthorityState
}
async function resolveMapId(root: string, explicit?: string) {
  if (explicit) { if (!SAFE_ID_RE.test(explicit)) throw new Error("invalid authority map id"); return explicit }
  const latest = await readOptional(path.join(baseDir(root), "latest.txt"))
  if (!latest?.trim()) throw new Error("no Development Authority Map found; start one first")
  return latest.trim()
}
async function edges(root: string, mapId: string) {
  return parseLines<AuthorityEdge>(await readOptional(path.join(mapDir(root, mapId), "edges.ndjson")), "authority edge ledger")
}
async function appendEdge(root: string, mapId: string, edge: AuthorityEdge) {
  const file = path.join(mapDir(root, mapId), "edges.ndjson")
  const existing = await readOptional(file)
  await atomicWrite(file, `${existing ?? ""}${JSON.stringify(edge)}\n`)
}

export const start = tool({
  description: "Start one exact-head Development Authority Map. It is derived navigation, never a replacement for repository-native authority.",
  args: { objective: tool.schema.string().min(1), targetSha: tool.schema.string().optional() },
  async execute(args, context) {
    const root = context.worktree
    const targetSha = (args.targetSha ?? await currentHead(root)).trim().toLowerCase()
    await requireExactClean(root, targetSha)
    const mapId = `DAM-${new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)}-${targetSha.slice(0, 12)}-${randomUUID().slice(0, 8)}`
    await mkdir(baseDir(root), { recursive: true })
    await mkdir(mapDir(root, mapId), { recursive: false })
    const now = new Date().toISOString()
    const state: AuthorityState = { schemaVersion: 1, mapId, targetSha, objective: args.objective.trim(), startedAt: now, updatedAt: now }
    await atomicWrite(path.join(mapDir(root, mapId), "state.json"), `${JSON.stringify(state, null, 2)}\n`)
    await atomicWrite(path.join(baseDir(root), "latest.txt"), `${mapId}\n`)
    return JSON.stringify(state, null, 2)
  },
})

export const record_edge = tool({
  description: "Record one evidence-bound repository development-authority relationship. Filenames alone are never sufficient evidence.",
  args: {
    mapId: tool.schema.string().optional(),
    relation: tool.schema.enum(RELATIONS),
    subject: tool.schema.string().min(1).max(300),
    object: tool.schema.string().min(1).max(300),
    confidence: tool.schema.enum(CONFIDENCE),
    rationale: tool.schema.string().min(1).max(1200),
    evidence: tool.schema.array(tool.schema.object({ path: tool.schema.string().min(1), locator: tool.schema.string().min(1).max(240) })).min(1).max(12),
  },
  async execute(args, context) {
    const root = context.worktree
    const mapId = await resolveMapId(root, args.mapId)
    const state = await loadState(root, mapId)
    await requireExactClean(root, state.targetSha)
    const bound: Evidence[] = []
    for (const item of args.evidence) bound.push(await bindEvidence(root, item, "authority evidence"))
    const edge: AuthorityEdge = {
      schemaVersion: 1,
      type: "development_authority_edge",
      edgeId: `DAE-${randomUUID()}`,
      targetSha: state.targetSha,
      relation: args.relation,
      subject: args.subject.trim(),
      object: args.object.trim(),
      confidence: args.confidence,
      rationale: args.rationale.trim(),
      evidence: bound,
      recordedAt: new Date().toISOString(),
    }
    await appendEdge(root, mapId, edge)
    return JSON.stringify(edge, null, 2)
  },
})

export const load = tool({
  description: "Load and revalidate a Development Authority Map against the same clean exact HEAD.",
  args: { mapId: tool.schema.string().optional() },
  async execute(args, context) {
    const root = context.worktree
    const mapId = await resolveMapId(root, args.mapId)
    const state = await loadState(root, mapId)
    await requireExactClean(root, state.targetSha)
    const all = await edges(root, mapId)
    for (const edge of all) for (const evidence of edge.evidence) await verifyEvidence(root, evidence)
    const confirmed = all.filter((edge) => edge.confidence === "CONFIRMED")
    return JSON.stringify({
      ...state,
      edgeCount: all.length,
      confirmedEdgeCount: confirmed.length,
      evidenceIntegrity: "PASS",
      relations: all,
      planningAuthorities: confirmed.filter((edge) => edge.relation === "CANONICAL_PLANNING_AUTHORITY"),
      activeScopes: confirmed.filter((edge) => edge.relation === "ACTIVE_IMPLEMENTATION_SCOPE"),
      acceptanceAuthorities: confirmed.filter((edge) => edge.relation === "ACCEPTANCE_AUTHORITY"),
      competingAuthorities: confirmed.filter((edge) => edge.relation === "FORBIDDEN_COMPETING_AUTHORITY"),
    }, null, 2)
  },
})
