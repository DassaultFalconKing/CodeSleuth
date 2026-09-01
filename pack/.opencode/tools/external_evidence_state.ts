import { tool } from "@opencode-ai/plugin"
import { randomUUID } from "node:crypto"
import { mkdir, readFile, writeFile } from "node:fs/promises"
import path from "node:path"

const SHA_RE = /^[0-9a-f]{40}$/
const SAFE_ID_RE = /^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$/
const SOURCE_KINDS = ["COMMAND", "SERVICE_PROBE", "HOST_OBSERVATION", "CI_ARTIFACT", "OPERATOR_ATTESTATION"] as const
const OUTCOMES = ["PASS", "FAIL", "OBSERVED", "UNKNOWN", "NOT_APPLICABLE"] as const
const SECRET_PATTERNS: Array<[RegExp, string]> = [
  [/\b(?:password|passwd|pwd)\s*[:=]\s*\S+/i, "password-like field"],
  [/\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|secret)\s*[:=]\s*\S+/i, "secret/token-like field"],
  [/authorization\s*:\s*bearer\s+\S+/i, "bearer authorization"],
  [/[a-z][a-z0-9+.-]*:\/\/[^\s/@:]+:[^\s/@]+@/i, "credential-bearing URL"],
  [/-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/, "private key material"],
]

type SourceKind = (typeof SOURCE_KINDS)[number]
type NativeOutcome = (typeof OUTCOMES)[number]
type Manifest = {
  schemaVersion: 1
  eventId: string
  adapterId: string
  repositorySha: string
  observedAt: string
  freshnessTtlSeconds: number
  checkId: string
  sourceKind: SourceKind
  sanitizedResult: string
  evidenceLocator: string
  nativeOutcome: NativeOutcome
  nativeDefinesOutcome: boolean
  notes: string
  recordedAt: string
}

async function git(root: string, args: string[]): Promise<string> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text(); const stderr = await new Response(proc.stderr).text(); const code = await proc.exited
  if (code !== 0) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`)
  return stdout.trim()
}
async function currentHead(root: string) { return (await git(root, ["rev-parse", "HEAD"])).toLowerCase() }
async function requireExactClean(root: string, sha: string) {
  if (!SHA_RE.test(sha)) throw new Error("repositorySha must be a full lowercase Git SHA")
  const head = await currentHead(root); if (head !== sha) throw new Error(`EXTERNAL EVIDENCE INVALIDATED — HEAD CHANGED: expected ${sha}, got ${head}`)
  const status = await git(root, ["status", "--porcelain=v1", "--untracked-files=no"])
  if (status) throw new Error(`EXTERNAL EVIDENCE INVALIDATED — TRACKED WORKTREE DIRTY:\n${status}`)
}
function baseDir(root: string, sha: string) { return path.join(root, ".opencode", "state", "external-evidence", sha) }
function ledger(root: string, sha: string) { return path.join(baseDir(root, sha), "manifest.ndjson") }
function safeId(value: string, label: string) { const v = value.trim(); if (!SAFE_ID_RE.test(v)) throw new Error(`${label} must use safe [A-Za-z0-9._-] identity characters`); return v }
function bounded(value: string, label: string, max: number) { const v = value.trim(); if (!v) throw new Error(`${label} must not be empty`); if (v.length > max) throw new Error(`${label} exceeds ${max} characters`); return v }
function rejectSecrets(value: string, label: string) { for (const [pattern, name] of SECRET_PATTERNS) if (pattern.test(value)) throw new Error(`${label} contains forbidden ${name}; external evidence must be sanitized before ingestion`) }
function parseObservedAt(value: string): Date {
  const parsed = new Date(value); if (Number.isNaN(parsed.getTime())) throw new Error("observedAt must be ISO-8601 parseable")
  if (parsed.getTime() > Date.now() + 5 * 60_000) throw new Error("observedAt is implausibly far in the future")
  return parsed
}
async function appendManifest(root: string, sha: string, manifest: Manifest) {
  const file = ledger(root, sha); await mkdir(path.dirname(file), { recursive: true })
  await writeFile(file, `${JSON.stringify(manifest)}\n`, { encoding: "utf8", flag: "a" })
}
async function readManifests(root: string, sha: string): Promise<Manifest[]> {
  let raw = ""; try { raw = await readFile(ledger(root, sha), "utf8") } catch (error: any) { if (error?.code !== "ENOENT") throw error }
  return raw.split("\n").filter(Boolean).map((line, index) => { try { return JSON.parse(line) as Manifest } catch { throw new Error(`external evidence ledger invalid JSON at line ${index + 1}`) } })
}

export const ingest = tool({
  description: "Append one sanitized exact-SHA ExternalEvidenceManifestV1 observation. Runtime evidence is evidence only and never repository/controller authority.",
  args: {
    adapterId: tool.schema.string().min(1), repositorySha: tool.schema.string().optional(), observedAt: tool.schema.string().min(1), freshnessTtlSeconds: tool.schema.number().int().min(1).max(2678400),
    checkId: tool.schema.string().min(1), sourceKind: tool.schema.enum(SOURCE_KINDS), sanitizedResult: tool.schema.string().min(1).max(4000), evidenceLocator: tool.schema.string().min(1).max(1000),
    nativeOutcome: tool.schema.enum(OUTCOMES), nativeDefinesOutcome: tool.schema.boolean(), notes: tool.schema.string().max(2000).optional(),
  },
  async execute(args, context) {
    const root = context.worktree; const repositorySha = (args.repositorySha ?? await currentHead(root)).trim().toLowerCase(); await requireExactClean(root, repositorySha)
    const adapterId = safeId(args.adapterId, "adapterId"); const checkId = safeId(args.checkId, "checkId"); const observedAt = parseObservedAt(args.observedAt).toISOString()
    const sanitizedResult = bounded(args.sanitizedResult, "sanitizedResult", 4000); const evidenceLocator = bounded(args.evidenceLocator, "evidenceLocator", 1000); const notes = args.notes?.trim() ?? ""
    rejectSecrets(sanitizedResult, "sanitizedResult"); rejectSecrets(evidenceLocator, "evidenceLocator"); rejectSecrets(notes, "notes")
    if ((args.nativeOutcome === "PASS" || args.nativeOutcome === "FAIL") && !args.nativeDefinesOutcome) throw new Error("PASS/FAIL may be recorded only when the underlying native check defines that outcome")
    const manifest: Manifest = {
      schemaVersion: 1, eventId: `EE-${randomUUID()}`, adapterId, repositorySha, observedAt, freshnessTtlSeconds: args.freshnessTtlSeconds, checkId, sourceKind: args.sourceKind,
      sanitizedResult, evidenceLocator, nativeOutcome: args.nativeOutcome, nativeDefinesOutcome: args.nativeDefinesOutcome, notes, recordedAt: new Date().toISOString(),
    }
    await appendManifest(root, repositorySha, manifest)
    return JSON.stringify({ ...manifest, authority: false, stale: Date.now() > new Date(observedAt).getTime() + args.freshnessTtlSeconds * 1000 }, null, 2)
  },
})

export const load = tool({
  description: "Load append-only external observations for the current exact SHA and make freshness visible without upgrading them to repository authority.",
  args: { repositorySha: tool.schema.string().optional(), adapterId: tool.schema.string().optional(), checkId: tool.schema.string().optional(), includeStale: tool.schema.boolean().optional() },
  async execute(args, context) {
    const root = context.worktree; const repositorySha = (args.repositorySha ?? await currentHead(root)).trim().toLowerCase(); await requireExactClean(root, repositorySha)
    const adapterId = args.adapterId ? safeId(args.adapterId, "adapterId") : null; const checkId = args.checkId ? safeId(args.checkId, "checkId") : null; const now = Date.now()
    const values = (await readManifests(root, repositorySha)).filter((item) => (!adapterId || item.adapterId === adapterId) && (!checkId || item.checkId === checkId)).map((item) => ({ ...item, stale: now > new Date(item.observedAt).getTime() + item.freshnessTtlSeconds * 1000, authority: false }))
    const visible = args.includeStale === false ? values.filter((item) => !item.stale) : values
    return JSON.stringify({ schemaVersion: 1, repositorySha, authority: "evidence-only", count: visible.length, freshCount: visible.filter((item) => !item.stale).length, staleCount: visible.filter((item) => item.stale).length, observations: visible }, null, 2)
  },
})
