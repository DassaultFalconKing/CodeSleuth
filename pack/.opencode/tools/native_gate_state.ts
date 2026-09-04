import { tool } from "@opencode-ai/plugin"
import { randomUUID } from "node:crypto"
import { mkdir, readFile, rename, rm, writeFile } from "node:fs/promises"
import path from "node:path"

const SHA_RE = /^[0-9a-f]{40}$/
const SAFE_ID_RE = /^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$/
const GATE_CLASSES = ["REPO_PROVABLE", "HOSTED_CI_PROVABLE", "SERVICE_DEPENDENT_REPRODUCIBLE", "LIVE_RUNTIME_REQUIRED", "OPERATOR_DECISION_REQUIRED"] as const
const OUTCOMES = ["UNEXECUTED", "PASS", "FAIL", "BLOCKED", "WAIVED"] as const

type GateClass = (typeof GATE_CLASSES)[number]
type Outcome = (typeof OUTCOMES)[number]
type Evidence = { path: string; blobHash: string; locator: string }
type Gate = {
  schemaVersion: 1
  gateId: string
  targetSha: string
  name: string
  gateClass: GateClass
  required: boolean
  command: string | null
  outcome: Outcome
  nativeEvidence: string | null
  evidence: Evidence[]
  recordedAt: string
  updatedAt: string
}
type State = { schemaVersion: 1; gateMapId: string; targetSha: string; objective: string; startedAt: string }

async function git(root: string, args: string[], allowFailure = false): Promise<{ code: number; stdout: string; stderr: string }> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text(); const stderr = await new Response(proc.stderr).text(); const code = await proc.exited
  if (code !== 0 && !allowFailure) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`)
  return { code, stdout: stdout.trim(), stderr: stderr.trim() }
}
function baseDir(root: string) { return path.join(root, ".opencode", "state", "native-gates") }
function mapDir(root: string, id: string) { if (!SAFE_ID_RE.test(id)) throw new Error("invalid gate map id"); return path.join(baseDir(root), id) }
async function currentHead(root: string) { return (await git(root, ["rev-parse", "HEAD"])).stdout.toLowerCase() }
async function requireExactClean(root: string, sha: string) {
  if (!SHA_RE.test(sha)) throw new Error("target SHA must be a full lowercase Git SHA")
  const head = await currentHead(root); if (head !== sha) throw new Error(`NATIVE GATE MAP INVALIDATED — HEAD CHANGED: expected ${sha}, got ${head}`)
  const status = (await git(root, ["status", "--porcelain=v1", "--untracked-files=no"])).stdout
  if (status) throw new Error(`NATIVE GATE MAP INVALIDATED — TRACKED WORKTREE DIRTY:\n${status}`)
}
async function readOptional(file: string): Promise<string | undefined> { try { return await readFile(file, "utf8") } catch (error: any) { if (error?.code === "ENOENT") return undefined; throw error } }
async function atomicWrite(file: string, content: string) {
  await mkdir(path.dirname(file), { recursive: true }); const temp = `${file}.${process.pid}.${randomUUID()}.tmp`
  try { await writeFile(temp, content, { encoding: "utf8", flag: "wx" }); await rename(temp, file) } catch (error) { await rm(temp, { force: true }).catch(() => undefined); throw error }
}
function normalizeRepoPath(root: string, input: string) {
  const r = path.resolve(root); const a = path.resolve(root, input); if (a !== r && !a.startsWith(r + path.sep)) throw new Error(`path escapes worktree: ${input}`)
  const rel = path.relative(r, a).replace(/\\/g, "/"); if (!rel || rel === ".") throw new Error("gate evidence must name a repository file"); return rel
}
async function bindEvidence(root: string, raw: { path: string; locator: string }): Promise<Evidence> {
  const rel = normalizeRepoPath(root, raw.path); const tracked = await git(root, ["ls-files", "--error-unmatch", "--", rel], true)
  if (tracked.code !== 0) throw new Error(`gate evidence is not tracked: ${rel}`)
  const blobHash = (await git(root, ["rev-parse", `HEAD:${rel}`])).stdout.toLowerCase(); if (!SHA_RE.test(blobHash)) throw new Error(`gate evidence is not a regular tracked blob: ${rel}`)
  const locator = raw.locator.trim(); if (!locator || locator.length > 240) throw new Error("gate evidence requires a bounded locator")
  return { path: rel, blobHash, locator }
}
async function verifyEvidence(root: string, evidence: Evidence) { const current = await bindEvidence(root, evidence); if (current.blobHash !== evidence.blobHash) throw new Error(`gate evidence blob changed for ${evidence.path}`) }
async function resolveId(root: string, explicit?: string) {
  if (explicit) { if (!SAFE_ID_RE.test(explicit)) throw new Error("invalid gate map id"); return explicit }
  const latest = await readOptional(path.join(baseDir(root), "latest.txt")); if (!latest?.trim()) throw new Error("no Native Gate Map found; start one first"); return latest.trim()
}
async function state(root: string, id: string): Promise<State> { return JSON.parse(await readFile(path.join(mapDir(root, id), "state.json"), "utf8")) as State }
async function gates(root: string, id: string): Promise<Gate[]> { const raw = await readOptional(path.join(mapDir(root, id), "gates.json")); return raw ? JSON.parse(raw) as Gate[] : [] }
async function saveGates(root: string, id: string, values: Gate[]) { await atomicWrite(path.join(mapDir(root, id), "gates.json"), `${JSON.stringify(values, null, 2)}\n`) }

export const start = tool({
  description: "Start one exact-head map of project-native verification and acceptance gates.",
  args: { objective: tool.schema.string().min(1), targetSha: tool.schema.string().optional() },
  async execute(args, context) {
    const root = context.worktree; const targetSha = (args.targetSha ?? await currentHead(root)).trim().toLowerCase(); await requireExactClean(root, targetSha)
    const gateMapId = `NGM-${new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)}-${targetSha.slice(0, 12)}-${randomUUID().slice(0, 8)}`
    await mkdir(baseDir(root), { recursive: true }); await mkdir(mapDir(root, gateMapId), { recursive: false })
    const result: State = { schemaVersion: 1, gateMapId, targetSha, objective: args.objective.trim(), startedAt: new Date().toISOString() }
    await atomicWrite(path.join(mapDir(root, gateMapId), "state.json"), `${JSON.stringify(result, null, 2)}\n`); await atomicWrite(path.join(baseDir(root), "latest.txt"), `${gateMapId}\n`)
    return JSON.stringify(result, null, 2)
  },
})

export const record_gate = tool({
  description: "Record one project-native gate with exact tracked evidence. Discovery does not imply the gate has run.",
  args: {
    gateMapId: tool.schema.string().optional(), name: tool.schema.string().min(1).max(300), gateClass: tool.schema.enum(GATE_CLASSES), required: tool.schema.boolean(), command: tool.schema.string().max(1000).optional(),
    evidence: tool.schema.array(tool.schema.object({ path: tool.schema.string().min(1), locator: tool.schema.string().min(1).max(240) })).min(1).max(12),
  },
  async execute(args, context) {
    const root = context.worktree; const id = await resolveId(root, args.gateMapId); const s = await state(root, id); await requireExactClean(root, s.targetSha)
    const all = await gates(root, id); if (all.some((g) => g.name === args.name.trim())) throw new Error(`gate already recorded: ${args.name.trim()}`)
    const evidence: Evidence[] = []; for (const item of args.evidence) evidence.push(await bindEvidence(root, item))
    const now = new Date().toISOString(); const gate: Gate = { schemaVersion: 1, gateId: `G-${randomUUID()}`, targetSha: s.targetSha, name: args.name.trim(), gateClass: args.gateClass, required: args.required, command: args.command?.trim() || null, outcome: "UNEXECUTED", nativeEvidence: null, evidence, recordedAt: now, updatedAt: now }
    all.push(gate); await saveGates(root, id, all); return JSON.stringify(gate, null, 2)
  },
})

export const record_result = tool({
  description: "Record the observed outcome of one already-discovered native gate. This stores evidence; it does not execute the command.",
  args: { gateMapId: tool.schema.string().optional(), gateId: tool.schema.string().min(1), outcome: tool.schema.enum(["PASS", "FAIL", "BLOCKED", "WAIVED"]), nativeEvidence: tool.schema.string().min(1).max(2000) },
  async execute(args, context) {
    const root = context.worktree; const id = await resolveId(root, args.gateMapId); const s = await state(root, id); await requireExactClean(root, s.targetSha)
    const all = await gates(root, id); const gate = all.find((item) => item.gateId === args.gateId); if (!gate) throw new Error(`gate not found: ${args.gateId}`)
    gate.outcome = args.outcome; gate.nativeEvidence = args.nativeEvidence.trim(); gate.updatedAt = new Date().toISOString(); await saveGates(root, id, all); return JSON.stringify(gate, null, 2)
  },
})

export const load = tool({
  description: "Load and revalidate one Native Gate Map and compute the CodeSleuth cloud-testability boundary.",
  args: { gateMapId: tool.schema.string().optional() },
  async execute(args, context) {
    const root = context.worktree; const id = await resolveId(root, args.gateMapId); const s = await state(root, id); await requireExactClean(root, s.targetSha); const all = await gates(root, id)
    for (const gate of all) for (const evidence of gate.evidence) await verifyEvidence(root, evidence)
    const cloudRequired = all.filter((g) => g.required && (g.gateClass === "REPO_PROVABLE" || g.gateClass === "HOSTED_CI_PROVABLE"))
    const cloudOpen = cloudRequired.filter((g) => g.outcome !== "PASS")
    const handoffState = cloudOpen.length > 0 ? "CLOUD_TESTABILITY_REMAINING" : "LIVE_HANDOFF_READY"
    return JSON.stringify({ ...s, evidenceIntegrity: "PASS", gates: all, cloudRequiredCount: cloudRequired.length, cloudOpenGateIds: cloudOpen.map((g) => g.gateId), handoffState }, null, 2)
  },
})
