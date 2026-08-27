import { tool } from "@opencode-ai/plugin"
import { randomUUID } from "node:crypto"
import { appendFile, mkdir, readFile, rename, rm, writeFile } from "node:fs/promises"
import path from "node:path"

const ID_RE = /^[A-Za-z0-9._-]+$/
const AMENDMENT_TYPES = ["correct", "supersede", "retract", "close", "reopen"] as const
const AMENDMENT_SCHEMA_VERSION = 1
const LIFECYCLE_STATUSES = ["OPEN", "REOPENED", "CLOSED", "RETRACTED", "SUPERSEDED"] as const

type AmendmentType = (typeof AMENDMENT_TYPES)[number]
type LifecycleStatus = (typeof LIFECYCLE_STATUSES)[number]
type DerivedStatus = LifecycleStatus | "UNTRUSTED"

type ReviewedPathEvidence = {
  path: string
  blobHash: string
}

type RangeEvidence = {
  path: string
  startLine: number
  endLine: number
  excerpt: string
  blobHash: string
  worktreeStatus: string
}

type CorruptAmendmentRecord = {
  lineNumber: number
  reason: string
}

type AmendmentLedgerRead = {
  present: boolean
  trustworthy: boolean
  amendments: any[]
  corruptRecords: CorruptAmendmentRecord[]
}

const LEGAL_TRANSITIONS: Record<LifecycleStatus, Record<AmendmentType, LifecycleStatus | null>> = {
  OPEN: {
    correct: "OPEN",
    close: "CLOSED",
    reopen: null,
    retract: "RETRACTED",
    supersede: "SUPERSEDED",
  },
  REOPENED: {
    correct: "REOPENED",
    close: "CLOSED",
    reopen: null,
    retract: "RETRACTED",
    supersede: "SUPERSEDED",
  },
  CLOSED: {
    correct: "CLOSED",
    close: null,
    reopen: "REOPENED",
    retract: "RETRACTED",
    supersede: "SUPERSEDED",
  },
  RETRACTED: {
    correct: "RETRACTED",
    close: null,
    reopen: null,
    retract: null,
    supersede: null,
  },
  SUPERSEDED: {
    correct: "SUPERSEDED",
    close: null,
    reopen: null,
    retract: null,
    supersede: null,
  },
}

async function git(root: string, args: string[]): Promise<string> {
  const proc = Bun.spawn(["git", "-C", root, ...args], {
    stdout: "pipe",
    stderr: "pipe",
  })
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  const code = await proc.exited
  if (code !== 0) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`)
  return stdout
}

function baseDir(root: string): string {
  return path.join(root, ".opencode", "state", "reviews")
}

function reviewDir(root: string, reviewId: string): string {
  if (!ID_RE.test(reviewId)) throw new Error("invalid review id")
  return path.join(baseDir(root), reviewId)
}

function amendmentLedgerPath(root: string, reviewId: string): string {
  return path.join(reviewDir(root, reviewId), "findings-amendments.ndjson")
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

async function resolveReviewId(root: string, sessionID: string, explicit?: string): Promise<string> {
  if (explicit) {
    if (!ID_RE.test(explicit)) throw new Error("invalid review id")
    return explicit
  }
  const base = baseDir(root)
  const mapped = await readOptional(path.join(base, "sessions", `${sessionID}.txt`))
  if (mapped?.trim()) return mapped.trim()
  const latest = await readOptional(path.join(base, "latest.txt"))
  if (latest?.trim()) return latest.trim()
  throw new Error("no review checkpoint found; start a review first")
}

async function loadState(root: string, reviewId: string): Promise<any> {
  const raw = await readFile(path.join(reviewDir(root, reviewId), "state.json"), "utf8")
  return JSON.parse(raw)
}

async function saveState(root: string, reviewId: string, state: any): Promise<void> {
  const dir = reviewDir(root, reviewId)
  await mkdir(dir, { recursive: true })
  state.updatedAt = new Date().toISOString()
  await atomicWrite(path.join(dir, "state.json"), `${JSON.stringify(state, null, 2)}\n`)
}

async function findingLines(root: string, reviewId: string): Promise<any[]> {
  const raw = await readOptional(path.join(reviewDir(root, reviewId), "findings.ndjson"))
  if (!raw?.trim()) return []
  return raw
    .trim()
    .split("\n")
    .filter(Boolean)
    .map((line) => JSON.parse(line))
}

function isAmendmentType(value: unknown): value is AmendmentType {
  return typeof value === "string" && (AMENDMENT_TYPES as readonly string[]).includes(value)
}

function relatedAmendments(amendments: any[], findingId: string): any[] {
  return amendments.filter((item) => item && item.amends === findingId)
}

function walkLifecycle(amendments: any[]): { status: LifecycleStatus; illegal?: string } {
  let status: LifecycleStatus = "OPEN"
  for (const item of amendments) {
    if (!isAmendmentType(item.amendmentType)) {
      return { status, illegal: `unknown amendmentType ${item.amendmentType}` }
    }
    const next = LEGAL_TRANSITIONS[status][item.amendmentType]
    if (!next) return { status, illegal: `${status} + ${item.amendmentType}` }
    status = next
  }
  return { status }
}

function supersedeEdges(amendments: any[]): { edges: Map<string, string>; duplicateSources: string[] } {
  const edges = new Map<string, string>()
  const duplicateSources: string[] = []
  for (const item of amendments) {
    if (item.amendmentType !== "supersede") continue
    if (typeof item.amends !== "string" || typeof item.supersededBy !== "string") continue
    if (edges.has(item.amends)) duplicateSources.push(item.amends)
    else edges.set(item.amends, item.supersededBy)
  }
  return { edges, duplicateSources }
}

function cycleFrom(edges: Map<string, string>, from: string, to: string): boolean {
  const seen = new Set<string>()
  let current: string | undefined = to
  while (current) {
    if (current === from) return true
    if (seen.has(current)) return true
    seen.add(current)
    current = edges.get(current)
  }
  return false
}

function existingSupersessionCycles(edges: Map<string, string>): string[] {
  const cyclic: string[] = []
  for (const from of edges.keys()) {
    const target = edges.get(from)
    if (target && cycleFrom(edges, from, target)) cyclic.push(from)
  }
  return cyclic
}

function parseAmendmentLedgerText(raw: string | undefined): AmendmentLedgerRead {
  if (raw === undefined) {
    return { present: false, trustworthy: true, amendments: [], corruptRecords: [] }
  }

  const corruptRecords: CorruptAmendmentRecord[] = []
  const amendments: any[] = []
  const seenIds = new Set<string>()
  const endsWithNewline = raw.endsWith("\n")
  const parts = raw.split("\n")

  for (let i = 0; i < parts.length; i++) {
    const isLast = i === parts.length - 1
    const text = parts[i]
    if (isLast && text === "") continue
    const lineNumber = i + 1
    if (text === "") {
      corruptRecords.push({ lineNumber, reason: "empty line in amendment ledger" })
      continue
    }
    if (isLast && !endsWithNewline) {
      corruptRecords.push({ lineNumber, reason: "torn amendment record (missing terminating newline)" })
      continue
    }
    let parsed: any
    try {
      parsed = JSON.parse(text)
    } catch {
      corruptRecords.push({ lineNumber, reason: "unparseable amendment JSON" })
      continue
    }
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      corruptRecords.push({ lineNumber, reason: "amendment record is not a JSON object" })
      continue
    }
    const schemaVersion = parsed.schemaVersion === undefined ? 1 : parsed.schemaVersion
    if (schemaVersion !== AMENDMENT_SCHEMA_VERSION) {
      corruptRecords.push({ lineNumber, reason: `unsupported amendment schemaVersion ${schemaVersion}` })
      continue
    }
    if (typeof parsed.id !== "string" || !parsed.id.startsWith("FA-")) {
      corruptRecords.push({ lineNumber, reason: "amendment id missing or not FA-..." })
      continue
    }
    if (seenIds.has(parsed.id)) {
      corruptRecords.push({ lineNumber, reason: `duplicate amendment id ${parsed.id}` })
      continue
    }
    seenIds.add(parsed.id)
    if (typeof parsed.amends !== "string" || !parsed.amends.startsWith("F-")) {
      corruptRecords.push({ lineNumber, reason: "amends missing or not F-..." })
      continue
    }
    if (!isAmendmentType(parsed.amendmentType)) {
      corruptRecords.push({ lineNumber, reason: `unknown amendmentType ${parsed.amendmentType}` })
      continue
    }
    if (typeof parsed.explanation !== "string" || !parsed.explanation.trim()) {
      corruptRecords.push({ lineNumber, reason: "explanation missing" })
      continue
    }
    if (typeof parsed.recordedAt !== "string" || !parsed.recordedAt.trim()) {
      corruptRecords.push({ lineNumber, reason: "recordedAt missing" })
      continue
    }
    amendments.push({ ...parsed, schemaVersion })
  }

  return {
    present: true,
    trustworthy: corruptRecords.length === 0,
    amendments,
    corruptRecords,
  }
}

function assessAmendmentSemantics(findings: any[], ledger: AmendmentLedgerRead): AmendmentLedgerRead {
  if (!ledger.trustworthy) return ledger
  const extra: CorruptAmendmentRecord[] = []
  const findingIds = new Set(findings.map((item) => item.id))

  for (const finding of findings) {
    const walked = walkLifecycle(relatedAmendments(ledger.amendments, finding.id))
    if (walked.illegal) {
      extra.push({ lineNumber: 0, reason: `illegal persisted transition for ${finding.id}: ${walked.illegal}` })
    }
  }

  const { edges, duplicateSources } = supersedeEdges(ledger.amendments)
  for (const source of duplicateSources) {
    extra.push({ lineNumber: 0, reason: `duplicate terminal supersession for ${source}` })
  }
  for (const item of ledger.amendments) {
    if (item.amendmentType !== "supersede") continue
    if (typeof item.supersededBy !== "string" || !item.supersededBy.startsWith("F-")) {
      extra.push({ lineNumber: 0, reason: `supersede ${item.id} missing same-review target` })
      continue
    }
    if (item.supersededBy === item.amends) {
      extra.push({ lineNumber: 0, reason: `supersede ${item.id} is a self-cycle` })
      continue
    }
    if (!findingIds.has(item.supersededBy) || !findingIds.has(item.amends)) {
      extra.push({ lineNumber: 0, reason: `supersede ${item.id} linkage is not in this review` })
    }
  }
  for (const source of existingSupersessionCycles(edges)) {
    extra.push({ lineNumber: 0, reason: `supersession cycle involving ${source}` })
  }

  if (!extra.length) return ledger
  return {
    ...ledger,
    trustworthy: false,
    corruptRecords: [...ledger.corruptRecords, ...extra],
  }
}

async function loadAmendmentLedger(root: string, reviewId: string, findings: any[]): Promise<AmendmentLedgerRead> {
  const raw = await readOptional(amendmentLedgerPath(root, reviewId))
  return assessAmendmentSemantics(findings, parseAmendmentLedgerText(raw))
}

function findingDerivedFields(finding: any, ledger: AmendmentLedgerRead): {
  lifecycleStatus: DerivedStatus
  derivedStatus: DerivedStatus
  latestAmendmentId: string | null
  latestAmendmentType: AmendmentType | null
  amendmentCount: number
} {
  const related = relatedAmendments(ledger.amendments, finding.id)
  const latest = related.length ? related[related.length - 1] : undefined
  if (!ledger.trustworthy) {
    return {
      lifecycleStatus: "UNTRUSTED",
      derivedStatus: "UNTRUSTED",
      latestAmendmentId: latest?.id ?? null,
      latestAmendmentType: isAmendmentType(latest?.amendmentType) ? latest.amendmentType : null,
      amendmentCount: related.length,
    }
  }
  const walked = walkLifecycle(related)
  return {
    lifecycleStatus: walked.status,
    derivedStatus: walked.status,
    latestAmendmentId: latest?.id ?? null,
    latestAmendmentType: isAmendmentType(latest?.amendmentType) ? latest.amendmentType : null,
    amendmentCount: related.length,
  }
}

function ledgerPublicFields(ledger: AmendmentLedgerRead) {
  return {
    amendmentCount: ledger.amendments.length,
    amendmentLedgerPresent: ledger.present,
    amendmentLedgerCorrupt: !ledger.trustworthy && ledger.present,
    trustworthyAmendmentHistory: ledger.trustworthy,
    corruptAmendmentRecords: ledger.corruptRecords,
  }
}

function illegalTransitionMessage(from: LifecycleStatus, op: AmendmentType): string {
  return `illegal finding lifecycle transition: ${from} + ${op}`
}

function normalizeWorktreePath(root: string, input: string): string {
  const absoluteRoot = path.resolve(root)
  const absolute = path.resolve(root, input)
  const rootPrefix = absoluteRoot + path.sep
  if (absolute !== absoluteRoot && !absolute.startsWith(rootPrefix)) throw new Error(`path escapes worktree: ${input}`)
  const relative = path.relative(absoluteRoot, absolute).replace(/\\/g, "/")
  if (!relative || relative === ".") throw new Error("reviewed path must name a tracked file")
  return relative
}

async function trackedPaths(root: string): Promise<Set<string>> {
  const raw = await git(root, ["ls-files", "-z"])
  return new Set(raw.split("\0").filter(Boolean).map((item) => item.replace(/\\/g, "/")))
}

async function captureReviewedPathEvidence(root: string, inputs: string[]): Promise<ReviewedPathEvidence[]> {
  const tracked = await trackedPaths(root)
  const unique = [...new Set(inputs.map((item) => normalizeWorktreePath(root, item)))]
  const evidence: ReviewedPathEvidence[] = []
  for (const relativePath of unique) {
    if (!tracked.has(relativePath)) throw new Error(`reviewed path is not a tracked file: ${relativePath}`)
    const blobHash = (await git(root, ["hash-object", "--", relativePath])).trim()
    evidence.push({ path: relativePath, blobHash })
  }
  return evidence
}

async function captureExactRangeEvidence(
  root: string,
  inputPath: string,
  startLine: number,
  endLine: number,
  limitMessage: string,
): Promise<RangeEvidence> {
  if (endLine < startLine) throw new Error("endLine must be >= startLine")
  if (endLine - startLine + 1 > 80) throw new Error(limitMessage)
  const relativePath = normalizeWorktreePath(root, inputPath)
  const tracked = await trackedPaths(root)
  if (!tracked.has(relativePath)) throw new Error(`finding path is not a tracked file: ${relativePath}`)
  const absolute = path.resolve(root, relativePath)
  const text = await readFile(absolute, "utf8")
  if (text.includes("\0")) throw new Error("binary evidence is not supported")
  const lines = text.split(/\r?\n/)
  if (startLine > lines.length || endLine > lines.length) throw new Error(`line range exceeds file length ${lines.length}`)
  const blobHash = (await git(root, ["hash-object", "--", relativePath])).trim()
  const worktreeStatus = (await git(root, ["status", "--porcelain=v1", "--", relativePath])).trim()
  return {
    path: relativePath,
    startLine,
    endLine,
    excerpt: lines.slice(startLine - 1, endLine).join("\n"),
    blobHash,
    worktreeStatus,
  }
}

async function verifyReviewedPathEvidence(root: string, state: any): Promise<{ complete: boolean; stale: any[] }> {
  const stored = Array.isArray(state.reviewedPathEvidence) ? state.reviewedPathEvidence : []
  const reviewed = Array.isArray(state.reviewedPaths) ? state.reviewedPaths : []
  if (stored.length !== reviewed.length) return { complete: false, stale: [] }
  const byPath = new Map<string, string>()
  for (const item of stored) {
    if (item && typeof item.path === "string" && typeof item.blobHash === "string") byPath.set(item.path, item.blobHash)
  }
  if (byPath.size !== reviewed.length) return { complete: false, stale: [] }

  const tracked = await trackedPaths(root)
  const stale: any[] = []
  for (const rawPath of reviewed) {
    if (typeof rawPath !== "string") {
      stale.push({ path: String(rawPath), reason: "invalid checkpoint path" })
      continue
    }
    const relativePath = normalizeWorktreePath(root, rawPath)
    const expected = byPath.get(relativePath)
    if (!expected) {
      stale.push({ path: relativePath, reason: "missing blob evidence" })
      continue
    }
    if (!tracked.has(relativePath)) {
      stale.push({ path: relativePath, expectedBlobHash: expected, reason: "file is no longer tracked" })
      continue
    }
    const actual = (await git(root, ["hash-object", "--", relativePath])).trim()
    if (actual !== expected) stale.push({ path: relativePath, expectedBlobHash: expected, actualBlobHash: actual, reason: "file content changed since checkpoint" })
  }
  return { complete: true, stale }
}

function requireTrustworthyLedger(ledger: AmendmentLedgerRead): void {
  if (!ledger.trustworthy) {
    throw new Error("amendment history is corrupt/untrustworthy; mutation refused")
  }
}

export const start = tool({
  description: "Start a durable repository review/documentation checkpoint and bind it to the current OpenCode session.",
  args: {
    objective: tool.schema.string().min(1),
    target: tool.schema.string().optional().describe("Commit, range, path scope, PR, or logical target"),
    mode: tool.schema.enum(["review", "documentation"]).optional(),
  },
  async execute(args, context) {
    const root = context.worktree
    const headSha = (await git(root, ["rev-parse", "HEAD"])).trim()
    const status = (await git(root, ["status", "--porcelain=v1"])).trim()
    const tracked = await trackedPaths(root)
    const stamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)
    const sessionSuffix = context.sessionID.replace(/[^A-Za-z0-9]/g, "").slice(-8) || "session"
    const reviewId = `${stamp}-${headSha.slice(0, 12)}-${sessionSuffix}-${randomUUID().slice(0, 8)}`
    const base = baseDir(root)
    await mkdir(path.join(base, "sessions"), { recursive: true })
    await mkdir(reviewDir(root, reviewId), { recursive: false })

    const state = {
      schemaVersion: 2,
      reviewId,
      sessionID: context.sessionID,
      mode: args.mode ?? "review",
      objective: args.objective,
      target: args.target ?? "current tracked worktree/HEAD",
      startedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      headSha,
      trackedFileCountAtStart: tracked.size,
      dirtyAtStart: status.length > 0,
      phase: "authority",
      completed: [],
      reviewedPaths: [],
      reviewedPathEvidence: [],
      openQuestions: [],
      next: ["capture authority and deterministic repository inventory"],
      note: "",
    }
    await saveState(root, reviewId, state)
    await atomicWrite(path.join(base, "sessions", `${context.sessionID}.txt`), `${reviewId}\n`)
    await atomicWrite(path.join(base, "latest.txt"), `${reviewId}\n`)
    return JSON.stringify(state, null, 2)
  },
})

export const load = tool({
  description: "Load the durable review checkpoint for this session, an explicit review ID, or the latest review, including stale coverage evidence after file changes.",
  args: {
    reviewId: tool.schema.string().optional(),
  },
  async execute(args, context) {
    const root = context.worktree
    const reviewId = await resolveReviewId(root, context.sessionID, args.reviewId)
    const state = await loadState(root, reviewId)
    const findings = await findingLines(root, reviewId)
    const ledger = await loadAmendmentLedger(root, reviewId, findings)
    const coverage = await verifyReviewedPathEvidence(root, state)
    return JSON.stringify(
      {
        ...state,
        coverageEvidenceComplete: coverage.complete,
        staleReviewedPaths: coverage.stale,
        findingCount: findings.length,
        ...ledgerPublicFields(ledger),
        findings: findings.slice(-50).map((finding) => ({
          id: finding.id,
          severity: finding.severity,
          title: finding.title,
          path: finding.path,
          startLine: finding.startLine,
          endLine: finding.endLine,
          blobHash: finding.blobHash,
          ...findingDerivedFields(finding, ledger),
        })),
        amendments: ledger.amendments.slice(-50).map((item) => ({
          id: item.id,
          amends: item.amends,
          amendmentType: item.amendmentType,
          path: item.path ?? null,
          startLine: item.startLine ?? null,
          endLine: item.endLine ?? null,
          blobHash: item.blobHash ?? null,
          headSha: item.headSha,
          supersededBy: item.supersededBy ?? null,
        })),
      },
      null,
      2,
    )
  },
})

export const checkpoint = tool({
  description: "Persist incremental review progress. reviewedPaths must be tracked files and are bound to their current worktree blob hashes for safe resume after compaction/restart.",
  args: {
    reviewId: tool.schema.string().optional(),
    phase: tool.schema.string().min(1),
    completed: tool.schema.array(tool.schema.string()).optional(),
    reviewedPaths: tool.schema.array(tool.schema.string()).optional(),
    openQuestions: tool.schema.array(tool.schema.string()).optional(),
    next: tool.schema.array(tool.schema.string()).optional(),
    note: tool.schema.string().optional(),
  },
  async execute(args, context) {
    const root = context.worktree
    const reviewId = await resolveReviewId(root, context.sessionID, args.reviewId)
    const state = await loadState(root, reviewId)
    state.phase = args.phase
    if (args.completed) state.completed = [...new Set([...(state.completed ?? []), ...args.completed])]
    if (args.reviewedPaths) {
      const captured = await captureReviewedPathEvidence(root, args.reviewedPaths)
      const existing = new Map<string, string>()
      for (const item of Array.isArray(state.reviewedPathEvidence) ? state.reviewedPathEvidence : []) {
        if (item && typeof item.path === "string" && typeof item.blobHash === "string") existing.set(item.path, item.blobHash)
      }
      for (const item of captured) existing.set(item.path, item.blobHash)
      state.reviewedPaths = [...existing.keys()].sort()
      state.reviewedPathEvidence = state.reviewedPaths.map((reviewedPath: string) => ({ path: reviewedPath, blobHash: existing.get(reviewedPath) }))
    }
    if (args.openQuestions) state.openQuestions = args.openQuestions
    if (args.next) state.next = args.next
    if (args.note !== undefined) state.note = args.note
    state.lastCheckpointHeadSha = (await git(root, ["rev-parse", "HEAD"])).trim()
    state.dirtyNow = (await git(root, ["status", "--porcelain=v1"])).trim().length > 0
    const coverage = await verifyReviewedPathEvidence(root, state)
    state.coverageEvidenceComplete = coverage.complete
    state.staleReviewedPaths = coverage.stale
    await saveState(root, reviewId, state)
    return JSON.stringify(state, null, 2)
  },
})

export const record_finding = tool({
  description: "Record a verified review finding using exact current file lines; captures excerpt, blob hash, HEAD, and worktree status automatically.",
  args: {
    reviewId: tool.schema.string().optional(),
    severity: tool.schema.enum(["blocker", "high", "medium", "low", "info"]),
    title: tool.schema.string().min(1),
    path: tool.schema.string().min(1),
    startLine: tool.schema.number().int().min(1),
    endLine: tool.schema.number().int().min(1),
    explanation: tool.schema.string().min(1),
    recommendation: tool.schema.string().optional(),
  },
  async execute(args, context) {
    const root = context.worktree
    const evidence = await captureExactRangeEvidence(
      root,
      args.path,
      args.startLine,
      args.endLine,
      "finding evidence is limited to 80 lines",
    )
    const reviewId = await resolveReviewId(root, context.sessionID, args.reviewId)
    const id = `F-${randomUUID()}`
    const headSha = (await git(root, ["rev-parse", "HEAD"])).trim()
    const finding = {
      id,
      severity: args.severity,
      title: args.title,
      path: evidence.path,
      startLine: evidence.startLine,
      endLine: evidence.endLine,
      excerpt: evidence.excerpt,
      explanation: args.explanation,
      recommendation: args.recommendation ?? "",
      blobHash: evidence.blobHash,
      headSha,
      worktreeStatus: evidence.worktreeStatus,
      recordedAt: new Date().toISOString(),
    }
    const dir = reviewDir(root, reviewId)
    await mkdir(dir, { recursive: true })
    await appendFile(path.join(dir, "findings.ndjson"), `${JSON.stringify(finding)}\n`, "utf8")
    return JSON.stringify(finding, null, 2)
  },
})

export const get_finding = tool({
  description: "Rehydrate one exact recorded finding from the durable evidence ledger by finding ID, including lifecycle and amendment metadata.",
  args: {
    reviewId: tool.schema.string().optional(),
    findingId: tool.schema.string().min(1),
  },
  async execute(args, context) {
    const root = context.worktree
    const reviewId = await resolveReviewId(root, context.sessionID, args.reviewId)
    const findings = await findingLines(root, reviewId)
    const finding = findings.find((item) => item.id === args.findingId)
    if (!finding) throw new Error(`finding not found: ${args.findingId}`)
    const ledger = await loadAmendmentLedger(root, reviewId, findings)
    const related = relatedAmendments(ledger.amendments, args.findingId)
    return JSON.stringify(
      {
        ...finding,
        ...findingDerivedFields(finding, ledger),
        ...ledgerPublicFields(ledger),
        amendments: related,
      },
      null,
      2,
    )
  },
})

export const amend_finding = tool({
  description: "Append a versioned amendment to an existing finding without rewriting findings.ndjson history. Lifecycle operations: close/reopen/retract/supersede. Metadata: correct (never changes lifecycle).",
  args: {
    reviewId: tool.schema.string().optional(),
    findingId: tool.schema.string().min(1).describe("Original F-... to amend"),
    amendmentType: tool.schema.enum(AMENDMENT_TYPES as unknown as [string, ...string[]]),
    explanation: tool.schema.string().min(1).describe("Why amendment and what changed/verified"),
    newSeverity: tool.schema.enum(["blocker", "high", "medium", "low", "info"]).optional(),
    newTitle: tool.schema.string().optional(),
    path: tool.schema.string().optional().describe("Tracked path for current evidence. Required for correct and reopen; not defaulted from the original finding."),
    startLine: tool.schema.number().int().min(1).optional(),
    endLine: tool.schema.number().int().min(1).optional(),
    supersededBy: tool.schema.string().optional().describe("Existing same-review F-... that replaces this finding (supersede only)"),
    verification: tool.schema.string().optional().describe("Commands/tests actually run and their result; required for close"),
    regressionTests: tool.schema.array(tool.schema.string()).optional(),
  },
  async execute(args, context) {
    const root = context.worktree
    const reviewId = await resolveReviewId(root, context.sessionID, args.reviewId)
    const findings = await findingLines(root, reviewId)
    const original = findings.find((item) => item.id === args.findingId)
    if (!original) throw new Error(`original finding not found: ${args.findingId}`)
    const ledger = await loadAmendmentLedger(root, reviewId, findings)
    requireTrustworthyLedger(ledger)

    const current = findingDerivedFields(original, ledger)
    if (current.lifecycleStatus === "UNTRUSTED") {
      throw new Error("amendment history is corrupt/untrustworthy; mutation refused")
    }
    const from = current.lifecycleStatus
    const op = args.amendmentType as AmendmentType
    const next = LEGAL_TRANSITIONS[from][op]
    if (!next) throw new Error(illegalTransitionMessage(from, op))

    if (args.supersededBy && op !== "supersede") {
      throw new Error("supersededBy is only valid for amendmentType supersede")
    }
    if ((args.startLine !== undefined) !== (args.endLine !== undefined)) {
      throw new Error("provide both startLine and endLine or neither")
    }

    if (op === "close" && !args.verification?.trim()) {
      throw new Error("close requires verification: tests/commands actually run")
    }
    if (op === "reopen") {
      if (!args.path || args.startLine === undefined || args.endLine === undefined) {
        throw new Error("reopen requires fresh current tracked-source evidence: explicit path, startLine, and endLine")
      }
    }
    if (op === "correct") {
      if (!args.path || args.startLine === undefined || args.endLine === undefined) {
        throw new Error("correct requires path + startLine + endLine with verified current excerpt")
      }
    }
    if (op === "supersede") {
      if (!args.supersededBy) throw new Error("supersede requires supersededBy: existing same-review F-... id")
      if (args.supersededBy === args.findingId) throw new Error("cannot supersede a finding with itself")
      const replacement = findings.find((item) => item.id === args.supersededBy)
      if (!replacement) throw new Error(`supersededBy finding not found: ${args.supersededBy}`)
      const { edges } = supersedeEdges(ledger.amendments)
      if (edges.has(args.findingId)) throw new Error("cannot replace an existing terminal supersession relation")
      if (cycleFrom(edges, args.findingId, args.supersededBy)) {
        throw new Error("supersede would create a cycle")
      }
    }

    let range: RangeEvidence | undefined
    if (args.path !== undefined || args.startLine !== undefined) {
      if (!args.path || args.startLine === undefined || args.endLine === undefined) {
        throw new Error("path amendment requires explicit path, startLine, and endLine")
      }
      range = await captureExactRangeEvidence(
        root,
        args.path,
        args.startLine,
        args.endLine,
        "amendment evidence is limited to 80 lines",
      )
    }

    if ((op === "reopen" || op === "correct") && !range) {
      throw new Error(`${op} requires fresh current tracked-source evidence: explicit path, startLine, and endLine`)
    }

    const headSha = (await git(root, ["rev-parse", "HEAD"])).trim()
    let blobHash = range?.blobHash ?? null
    let worktreeStatus = range?.worktreeStatus ?? (await git(root, ["status", "--porcelain=v1"])).trim()
    if (!range && original.path) {
      const tracked = await trackedPaths(root)
      if (tracked.has(original.path)) {
        blobHash = (await git(root, ["hash-object", "--", original.path])).trim()
        worktreeStatus = (await git(root, ["status", "--porcelain=v1", "--", original.path])).trim()
      }
    }

    const id = `FA-${randomUUID()}`
    const amendment = {
      schemaVersion: AMENDMENT_SCHEMA_VERSION,
      id,
      amends: args.findingId,
      amendmentType: op,
      explanation: args.explanation,
      newSeverity: args.newSeverity ?? null,
      newTitle: args.newTitle ?? null,
      path: range?.path ?? null,
      startLine: range?.startLine ?? null,
      endLine: range?.endLine ?? null,
      excerpt: range?.excerpt ?? null,
      supersededBy: op === "supersede" ? args.supersededBy : null,
      verification: args.verification ?? "",
      regressionTests: [...new Set(args.regressionTests ?? [])],
      blobHash,
      headSha,
      worktreeStatus,
      recordedAt: new Date().toISOString(),
    }
    await mkdir(reviewDir(root, reviewId), { recursive: true })
    await appendFile(amendmentLedgerPath(root, reviewId), `${JSON.stringify(amendment)}\n`, "utf8")
    return JSON.stringify(
      {
        ...amendment,
        lifecycleStatus: next,
        derivedStatus: next,
        latestAmendmentId: id,
        latestAmendmentType: op,
      },
      null,
      2,
    )
  },
})

export const get_amendment = tool({
  description: "Rehydrate one amendment event by FA-... id from findings-amendments.ndjson.",
  args: {
    reviewId: tool.schema.string().optional(),
    amendmentId: tool.schema.string().min(1),
  },
  async execute(args, context) {
    const root = context.worktree
    const reviewId = await resolveReviewId(root, context.sessionID, args.reviewId)
    const findings = await findingLines(root, reviewId)
    const ledger = await loadAmendmentLedger(root, reviewId, findings)
    const found = ledger.amendments.find((item) => item.id === args.amendmentId)
    if (!found) {
      if (!ledger.trustworthy) {
        throw new Error(`amendment not found or unreadable due to corrupt ledger: ${args.amendmentId}`)
      }
      throw new Error(`amendment not found: ${args.amendmentId}`)
    }
    return JSON.stringify({ ...found, ...ledgerPublicFields(ledger) }, null, 2)
  },
})

export const list_amendments = tool({
  description: "List amendment events for a finding or all findings in the review, including lifecycle metadata and visible ledger corruption.",
  args: {
    reviewId: tool.schema.string().optional(),
    findingId: tool.schema.string().optional(),
  },
  async execute(args, context) {
    const root = context.worktree
    const reviewId = await resolveReviewId(root, context.sessionID, args.reviewId)
    const findings = await findingLines(root, reviewId)
    const ledger = await loadAmendmentLedger(root, reviewId, findings)
    const filtered = args.findingId ? relatedAmendments(ledger.amendments, args.findingId) : ledger.amendments
    const finding = args.findingId ? findings.find((item) => item.id === args.findingId) : undefined
    if (args.findingId && !finding) throw new Error(`finding not found: ${args.findingId}`)
    return JSON.stringify(
      {
        reviewId,
        count: filtered.length,
        amendments: filtered.slice(-50),
        ...ledgerPublicFields(ledger),
        ...(finding ? findingDerivedFields(finding, ledger) : {}),
      },
      null,
      2,
    )
  },
})
