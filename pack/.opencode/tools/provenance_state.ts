import { tool } from "@opencode-ai/plugin"
import { createHash, randomUUID } from "node:crypto"
import { mkdir, readFile, rename, rm, writeFile } from "node:fs/promises"
import path from "node:path"

const ID_RE = /^[A-Za-z0-9._-]+$/
const ACTOR_RE = /^[a-z0-9][a-z0-9._-]{1,31}$/
const SHA_RE = /^[0-9a-f]{40}$/
const DOMAIN = "codesleuth-provenance-v1"

type Provenance = {
  schemaVersion: 1
  actor: string
  watermark: string
  kind: "session-attribution"
  headSha: string
  reviewId: string
  sessionID: string
  recordedAt: string
}

async function git(root: string, args: string[]): Promise<string> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  const code = await proc.exited
  if (code !== 0) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`)
  return stdout.trim()
}

function baseDir(root: string): string {
  return path.join(root, ".opencode", "state", "reviews")
}

function reviewDir(root: string, reviewId: string): string {
  if (!ID_RE.test(reviewId)) throw new Error("invalid review id")
  return path.join(baseDir(root), reviewId)
}

function provenancePath(root: string, reviewId: string): string {
  return path.join(reviewDir(root, reviewId), "provenance.json")
}

async function readOptional(file: string): Promise<string | undefined> {
  try {
    return await readFile(file, "utf8")
  } catch (error: any) {
    if (error?.code === "ENOENT") return undefined
    throw error
  }
}

async function resolveReviewId(root: string, sessionID: string, explicit?: string): Promise<string> {
  if (explicit) {
    if (!ID_RE.test(explicit)) throw new Error("invalid review id")
    return explicit
  }
  const mapped = await readOptional(path.join(baseDir(root), "sessions", `${sessionID}.txt`))
  if (mapped?.trim()) return mapped.trim()
  const latest = await readOptional(path.join(baseDir(root), "latest.txt"))
  if (latest?.trim()) return latest.trim()
  throw new Error("no review checkpoint found; start review_state first")
}

function normalizeActor(input: string): string {
  const actor = input.trim().toLowerCase()
  if (!ACTOR_RE.test(actor)) throw new Error("actor must be 2-32 lowercase [a-z0-9._-] characters")
  return actor
}

function watermark(actor: string, headSha: string, sessionID: string): string {
  if (!SHA_RE.test(headSha)) throw new Error("HEAD must be a full lowercase Git SHA")
  if (!sessionID.trim()) throw new Error("host session id is empty")
  const digest = createHash("sha256")
    .update(`${DOMAIN}|session|${actor}|${headSha}|${sessionID}`, "utf8")
    .digest("hex")
    .slice(0, 12)
  return `${actor}-${digest}`
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

function parseStored(raw: string): Provenance {
  const value = JSON.parse(raw)
  if (!value || value.schemaVersion !== 1 || value.kind !== "session-attribution") {
    throw new Error("unsupported provenance sidecar")
  }
  if (!ACTOR_RE.test(value.actor) || !SHA_RE.test(value.headSha) || !ID_RE.test(value.reviewId)) {
    throw new Error("invalid provenance sidecar identity")
  }
  const expected = watermark(value.actor, value.headSha, value.sessionID)
  if (value.watermark !== expected) throw new Error("provenance sidecar watermark mismatch")
  return value as Provenance
}

export const bind = tool({
  description: "Bind one immutable attribution watermark to the active durable review session. This is provenance metadata, not acceptance authority.",
  args: {
    actor: tool.schema.string().min(2).max(32).describe("Stable opaque producer code for this logical coding/review session, or anon when unknown"),
    reviewId: tool.schema.string().optional(),
  },
  async execute(args, context) {
    const root = context.worktree
    const reviewId = await resolveReviewId(root, context.sessionID, args.reviewId)
    const actor = normalizeActor(args.actor)
    const headSha = (await git(root, ["rev-parse", "HEAD"])).toLowerCase()
    const file = provenancePath(root, reviewId)
    const existing = await readOptional(file)
    if (existing !== undefined) {
      const stored = parseStored(existing)
      const expected = watermark(actor, headSha, context.sessionID)
      if (stored.actor !== actor || stored.headSha !== headSha || stored.sessionID !== context.sessionID || stored.watermark !== expected) {
        throw new Error("provenance already bound to a different producer/session/HEAD; start a new review checkpoint")
      }
      return JSON.stringify({ ...stored, currentHeadSha: headSha, headMatch: true, trustworthy: true }, null, 2)
    }
    const record: Provenance = {
      schemaVersion: 1,
      actor,
      watermark: watermark(actor, headSha, context.sessionID),
      kind: "session-attribution",
      headSha,
      reviewId,
      sessionID: context.sessionID,
      recordedAt: new Date().toISOString(),
    }
    await atomicWrite(file, `${JSON.stringify(record, null, 2)}\n`)
    return JSON.stringify({ ...record, currentHeadSha: headSha, headMatch: true, trustworthy: true }, null, 2)
  },
})

export const load = tool({
  description: "Load and verify the immutable provenance sidecar for a durable review. Does not establish freshness or EHA claimability.",
  args: { reviewId: tool.schema.string().optional() },
  async execute(args, context) {
    const root = context.worktree
    const reviewId = await resolveReviewId(root, context.sessionID, args.reviewId)
    const raw = await readOptional(provenancePath(root, reviewId))
    if (raw === undefined) {
      return JSON.stringify({ reviewId, present: false, trustworthy: false, reason: "provenance sidecar absent" }, null, 2)
    }
    const stored = parseStored(raw)
    const currentHeadSha = (await git(root, ["rev-parse", "HEAD"])).toLowerCase()
    return JSON.stringify({
      ...stored,
      present: true,
      trustworthy: true,
      currentHeadSha,
      headMatch: currentHeadSha === stored.headSha,
    }, null, 2)
  },
})
