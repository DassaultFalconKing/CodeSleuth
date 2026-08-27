import { tool } from "@opencode-ai/plugin"
import { randomUUID } from "node:crypto"
import { appendFile, mkdir, readFile, rename, rm, writeFile } from "node:fs/promises"
import path from "node:path"

const ID_RE = /^[A-Za-z0-9._-]+$/

type ReviewedPathEvidence = {
  path: string
  blobHash: string
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
    const coverage = await verifyReviewedPathEvidence(root, state)
    return JSON.stringify(
      {
        ...state,
        coverageEvidenceComplete: coverage.complete,
        staleReviewedPaths: coverage.stale,
        findingCount: findings.length,
        findings: findings.slice(-50).map((finding) => ({
          id: finding.id,
          severity: finding.severity,
          title: finding.title,
          path: finding.path,
          startLine: finding.startLine,
          endLine: finding.endLine,
          blobHash: finding.blobHash,
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
    if (args.endLine < args.startLine) throw new Error("endLine must be >= startLine")
    if (args.endLine - args.startLine + 1 > 80) throw new Error("finding evidence is limited to 80 lines")

    const relativePath = normalizeWorktreePath(root, args.path)
    const tracked = await trackedPaths(root)
    if (!tracked.has(relativePath)) throw new Error(`finding path is not a tracked file: ${relativePath}`)
    const absolute = path.resolve(root, relativePath)
    const text = await readFile(absolute, "utf8")
    if (text.includes("\0")) throw new Error("binary evidence is not supported")
    const lines = text.split(/\r?\n/)
    if (args.startLine > lines.length || args.endLine > lines.length) throw new Error(`line range exceeds file length ${lines.length}`)

    const reviewId = await resolveReviewId(root, context.sessionID, args.reviewId)
    const id = `F-${randomUUID()}`
    const blobHash = (await git(root, ["hash-object", "--", relativePath])).trim()
    const headSha = (await git(root, ["rev-parse", "HEAD"])).trim()
    const fileStatus = (await git(root, ["status", "--porcelain=v1", "--", relativePath])).trim()
    const finding = {
      id,
      severity: args.severity,
      title: args.title,
      path: relativePath,
      startLine: args.startLine,
      endLine: args.endLine,
      excerpt: lines.slice(args.startLine - 1, args.endLine).join("\n"),
      explanation: args.explanation,
      recommendation: args.recommendation ?? "",
      blobHash,
      headSha,
      worktreeStatus: fileStatus,
      recordedAt: new Date().toISOString(),
    }
    const dir = reviewDir(root, reviewId)
    await mkdir(dir, { recursive: true })
    await appendFile(path.join(dir, "findings.ndjson"), `${JSON.stringify(finding)}\n`, "utf8")
    return JSON.stringify(finding, null, 2)
  },
})

export const get_finding = tool({
  description: "Rehydrate one exact recorded finding from the durable evidence ledger by finding ID.",
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
    return JSON.stringify(finding, null, 2)
  },
})