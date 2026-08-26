import { tool } from "@opencode-ai/plugin"
import { randomUUID } from "node:crypto"
import { appendFile, mkdir, readFile } from "node:fs/promises"
import path from "node:path"

const ID_RE = /^[A-Za-z0-9._-]+$/
const SHA_RE = /^[0-9a-f]{40}$/
const LEVELS = ["SIB0", "SIB1", "SIB2"] as const
const VERDICTS = ["PASS", "FAIL"] as const
const CLASSIFICATIONS = ["architectural", "capability_implementation", "composition_e2e"] as const
const REPAIR_DECISIONS = ["repair", "architecture_reopened", "superseded", "drop"] as const

type SibLevel = (typeof LEVELS)[number]
type Verdict = (typeof VERDICTS)[number]
type DefectClassification = (typeof CLASSIFICATIONS)[number]
type RepairDecision = (typeof REPAIR_DECISIONS)[number]

type CampaignStarted = {
  type: "campaign_started"
  eventId: string
  campaignId: string
  targetSha: string
  targetBranch?: string
  scope: string
  recordedAt: string
  recordedHeadSha: string
}

type VerdictEvent = {
  type: "verdict"
  eventId: string
  campaignId: string
  targetSha: string
  level: SibLevel
  verdict: Verdict
  profile: string
  summary: string
  evidence: string[]
  blockerFindingIds: string[]
  recordedAt: string
  recordedHeadSha: string
}

type RepairEvent = {
  type: "repair"
  eventId: string
  campaignId: string
  failingSha: string
  level: SibLevel
  classification: DefectClassification
  decision: RepairDecision
  failingTest: string
  failure: string
  reproduction: string
  repairBranch: string
  candidateSha?: string
  regressionTests: string[]
  focusedTests: string[]
  notes: string
  recordedAt: string
  recordedHeadSha: string
}

type EhaEvent = CampaignStarted | VerdictEvent | RepairEvent

type CampaignSummary = {
  campaignId: string
  targetSha: string
  targetBranch?: string
  scope: string
  startedAt: string
  verdicts: Record<SibLevel, VerdictEvent | null>
  claimable: Record<SibLevel, boolean>
  failedLevels: SibLevel[]
  repairs: RepairEvent[]
}

async function git(root: string, args: string[], allowFailure = false): Promise<{ code: number; stdout: string; stderr: string }> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  const code = await proc.exited
  if (code !== 0 && !allowFailure) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`)
  return { code, stdout, stderr }
}

async function currentHead(root: string): Promise<string> {
  return (await git(root, ["rev-parse", "HEAD"])).stdout.trim()
}

function reviewsBaseDir(root: string): string {
  return path.join(root, ".opencode", "state", "reviews")
}

function reviewDir(root: string, reviewId: string): string {
  if (!ID_RE.test(reviewId)) throw new Error("invalid review id")
  return path.join(reviewsBaseDir(root), reviewId)
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
  const base = reviewsBaseDir(root)
  const mapped = await readOptional(path.join(base, "sessions", `${sessionID}.txt`))
  if (mapped?.trim()) return mapped.trim()
  const latest = await readOptional(path.join(base, "latest.txt"))
  if (latest?.trim()) return latest.trim()
  throw new Error("no review checkpoint found; start review_state first")
}

function ledgerPath(root: string, reviewId: string): string {
  return path.join(reviewDir(root, reviewId), "eha.ndjson")
}

async function events(root: string, reviewId: string): Promise<EhaEvent[]> {
  const raw = await readOptional(ledgerPath(root, reviewId))
  if (!raw?.trim()) return []
  return raw
    .trim()
    .split("\n")
    .filter(Boolean)
    .map((line) => JSON.parse(line) as EhaEvent)
}

async function appendEvent(root: string, reviewId: string, event: EhaEvent): Promise<void> {
  const dir = reviewDir(root, reviewId)
  await mkdir(dir, { recursive: true })
  await appendFile(ledgerPath(root, reviewId), `${JSON.stringify(event)}\n`, "utf8")
}

function validateSha(value: string, what: string): string {
  const normalized = value.trim().toLowerCase()
  if (!SHA_RE.test(normalized)) throw new Error(`${what} must be a full 40-character lowercase Git SHA`)
  return normalized
}

function classificationFor(level: SibLevel): DefectClassification {
  if (level === "SIB0") return "architectural"
  if (level === "SIB1") return "capability_implementation"
  return "composition_e2e"
}

function campaignById(all: EhaEvent[], campaignId?: string): CampaignStarted {
  const starts = all.filter((event): event is CampaignStarted => event.type === "campaign_started")
  if (starts.length === 0) throw new Error("no EHA campaign found; start one first")
  if (!campaignId) return starts[starts.length - 1]
  const found = starts.find((event) => event.campaignId === campaignId)
  if (!found) throw new Error(`EHA campaign not found: ${campaignId}`)
  return found
}

function verdictForCampaignLevel(all: EhaEvent[], campaignId: string, level: SibLevel): VerdictEvent | undefined {
  return all.find(
    (event): event is VerdictEvent =>
      event.type === "verdict" && event.campaignId === campaignId && event.level === level,
  )
}

function targetShaHasRecordedFail(all: EhaEvent[], targetSha: string): boolean {
  return all.some(
    (event): event is VerdictEvent =>
      event.type === "verdict" && event.targetSha === targetSha && event.verdict === "FAIL",
  )
}

function summarize(all: EhaEvent[]): CampaignSummary[] {
  const starts = all.filter((event): event is CampaignStarted => event.type === "campaign_started")
  return starts.map((start) => {
    const verdictsForCampaign = all.filter(
      (event): event is VerdictEvent => event.type === "verdict" && event.campaignId === start.campaignId,
    )
    const verdicts = Object.fromEntries(
      LEVELS.map((level) => [level, [...verdictsForCampaign].reverse().find((event) => event.level === level) ?? null]),
    ) as Record<SibLevel, VerdictEvent | null>
    const sib0Pass = verdicts.SIB0?.verdict === "PASS"
    const sib1Pass = sib0Pass && verdicts.SIB1?.verdict === "PASS"
    const sib2Pass = sib1Pass && verdicts.SIB2?.verdict === "PASS"
    return {
      campaignId: start.campaignId,
      targetSha: start.targetSha,
      targetBranch: start.targetBranch,
      scope: start.scope,
      startedAt: start.recordedAt,
      verdicts,
      claimable: { SIB0: sib0Pass, SIB1: sib1Pass, SIB2: sib2Pass },
      failedLevels: LEVELS.filter((level) => verdicts[level]?.verdict === "FAIL"),
      repairs: all.filter(
        (event): event is RepairEvent => event.type === "repair" && event.campaignId === start.campaignId,
      ),
    }
  })
}

function mermaidEscape(value: string): string {
  return value
    .replace(/\\/g, "\\\\")
    .replace(/"/g, "&quot;")
    .replace(/[\r\n]+/g, " ")
    .replace(/[<>]/g, "")
    .slice(0, 220)
}

function statusLabel(summary: CampaignSummary, level: SibLevel): string {
  const event = summary.verdicts[level]
  return `${level}: ${event?.verdict ?? "PENDING"}`
}

function renderMermaid(all: EhaEvent[]): string {
  const campaigns = summarize(all).slice(-50)
  const lines = ["flowchart TD"]
  const bySha = new Map(campaigns.map((campaign, index) => [campaign.targetSha, `C${index}`]))

  campaigns.forEach((campaign, index) => {
    const node = `C${index}`
    const label = [
      campaign.campaignId,
      campaign.targetSha.slice(0, 12),
      statusLabel(campaign, "SIB0"),
      statusLabel(campaign, "SIB1"),
      statusLabel(campaign, "SIB2"),
    ].join(" | ")
    lines.push(`  ${node}["${mermaidEscape(label)}"]`)
    for (const [repairIndex, repair] of campaign.repairs.entries()) {
      const edgeLabel = mermaidEscape(`${repair.level} ${repair.decision}: ${repair.failure}`)
      if (repair.candidateSha && bySha.has(repair.candidateSha)) {
        lines.push(`  ${node} -->|"${edgeLabel}"| ${bySha.get(repair.candidateSha)}`)
      } else {
        const repairNode = `R${index}_${repairIndex}`
        const candidate = repair.candidateSha ? repair.candidateSha.slice(0, 12) : "candidate pending"
        lines.push(`  ${repairNode}["${mermaidEscape(`${repair.repairBranch} | ${candidate}`)}"]`)
        lines.push(`  ${node} -->|"${edgeLabel}"| ${repairNode}`)
      }
    }
  })
  return `${lines.join("\n")}\n`
}

export const start_campaign = tool({
  description: "Start an Exact-Head Acceptance campaign inside the current durable review evidence ledger. The target must equal literal current HEAD.",
  args: {
    reviewId: tool.schema.string().optional(),
    targetSha: tool.schema.string().optional().describe("Full 40-character SHA; defaults to current HEAD"),
    targetBranch: tool.schema.string().optional(),
    scope: tool.schema.string().optional(),
  },
  async execute(args, context) {
    const root = context.worktree
    const reviewId = await resolveReviewId(root, context.sessionID, args.reviewId)
    const headSha = validateSha(await currentHead(root), "current HEAD")
    const targetSha = validateSha(args.targetSha ?? headSha, "target SHA")
    if (targetSha !== headSha) throw new Error(`EHA target ${targetSha} does not equal literal current HEAD ${headSha}`)

    const all = await events(root, reviewId)
    if (targetShaHasRecordedFail(all, targetSha)) {
      throw new Error(
        `EHA target ${targetSha} already has a recorded FAIL verdict; repair on a new exact SHA instead of starting another campaign on the same target`,
      )
    }

    const stamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)
    const campaignId = `EHA-${stamp}-${targetSha.slice(0, 12)}-${randomUUID().slice(0, 8)}`
    const event: CampaignStarted = {
      type: "campaign_started",
      eventId: `E-${randomUUID()}`,
      campaignId,
      targetSha,
      targetBranch: args.targetBranch?.trim() || undefined,
      scope: args.scope?.trim() || "SIB0/SIB1/SIB2 exact-head acceptance",
      recordedAt: new Date().toISOString(),
      recordedHeadSha: headSha,
    }
    await appendEvent(root, reviewId, event)
    return JSON.stringify(event, null, 2)
  },
})

export const record_verdict = tool({
  description: "Record a SIB0/SIB1/SIB2 PASS or FAIL for an EHA campaign. Refuses to write if literal current HEAD differs from the campaign target SHA.",
  args: {
    reviewId: tool.schema.string().optional(),
    campaignId: tool.schema.string().optional(),
    level: tool.schema.enum(LEVELS),
    verdict: tool.schema.enum(VERDICTS),
    profile: tool.schema.string().min(1),
    summary: tool.schema.string().min(1),
    evidence: tool.schema.array(tool.schema.string()).optional(),
    blockerFindingIds: tool.schema.array(tool.schema.string()).optional(),
  },
  async execute(args, context) {
    const root = context.worktree
    const reviewId = await resolveReviewId(root, context.sessionID, args.reviewId)
    const all = await events(root, reviewId)
    const campaign = campaignById(all, args.campaignId)
    const headSha = validateSha(await currentHead(root), "current HEAD")
    if (headSha !== campaign.targetSha) {
      throw new Error(`EHA INVALIDATED — HEAD CHANGED: campaign target ${campaign.targetSha}, current HEAD ${headSha}`)
    }
    const existingVerdict = verdictForCampaignLevel(all, campaign.campaignId, args.level)
    if (existingVerdict) {
      throw new Error(
        `EHA verdict already recorded for ${args.level} in campaign ${campaign.campaignId}: ${existingVerdict.verdict}`,
      )
    }
    const event: VerdictEvent = {
      type: "verdict",
      eventId: `E-${randomUUID()}`,
      campaignId: campaign.campaignId,
      targetSha: campaign.targetSha,
      level: args.level,
      verdict: args.verdict,
      profile: args.profile,
      summary: args.summary,
      evidence: [...new Set(args.evidence ?? [])],
      blockerFindingIds: [...new Set(args.blockerFindingIds ?? [])],
      recordedAt: new Date().toISOString(),
      recordedHeadSha: headSha,
    }
    await appendEvent(root, reviewId, event)
    return JSON.stringify(event, null, 2)
  },
})

export const record_repair = tool({
  description: "Record the EHA repair-loop decision and lineage for a failed campaign. The defect classification must match the blocking SIB level.",
  args: {
    reviewId: tool.schema.string().optional(),
    campaignId: tool.schema.string().optional(),
    level: tool.schema.enum(LEVELS),
    classification: tool.schema.enum(CLASSIFICATIONS),
    decision: tool.schema.enum(REPAIR_DECISIONS),
    failingTest: tool.schema.string().min(1),
    failure: tool.schema.string().min(1),
    reproduction: tool.schema.string().min(1),
    repairBranch: tool.schema.string().min(1),
    candidateSha: tool.schema.string().optional(),
    regressionTests: tool.schema.array(tool.schema.string()).optional(),
    focusedTests: tool.schema.array(tool.schema.string()).optional(),
    notes: tool.schema.string().optional(),
  },
  async execute(args, context) {
    const root = context.worktree
    const reviewId = await resolveReviewId(root, context.sessionID, args.reviewId)
    const all = await events(root, reviewId)
    const campaign = campaignById(all, args.campaignId)
    const expectedClassification = classificationFor(args.level)
    if (args.classification !== expectedClassification) {
      throw new Error(`${args.level} blockers must be classified as ${expectedClassification}`)
    }
    const verdict = [...all]
      .reverse()
      .find((event): event is VerdictEvent => event.type === "verdict" && event.campaignId === campaign.campaignId && event.level === args.level)
    if (verdict?.verdict !== "FAIL") throw new Error(`cannot enter EHA repair loop for ${args.level} without a recorded FAIL verdict`)

    const headSha = validateSha(await currentHead(root), "current HEAD")
    const candidateSha = args.candidateSha ? validateSha(args.candidateSha, "candidate SHA") : undefined
    if (candidateSha) {
      const ancestry = await git(root, ["merge-base", "--is-ancestor", campaign.targetSha, candidateSha], true)
      if (ancestry.code !== 0) throw new Error(`candidate ${candidateSha} is not descended from failing SHA ${campaign.targetSha}`)
    }

    const event: RepairEvent = {
      type: "repair",
      eventId: `E-${randomUUID()}`,
      campaignId: campaign.campaignId,
      failingSha: campaign.targetSha,
      level: args.level,
      classification: args.classification,
      decision: args.decision,
      failingTest: args.failingTest,
      failure: args.failure,
      reproduction: args.reproduction,
      repairBranch: args.repairBranch,
      candidateSha,
      regressionTests: [...new Set(args.regressionTests ?? [])],
      focusedTests: [...new Set(args.focusedTests ?? [])],
      notes: args.notes ?? "",
      recordedAt: new Date().toISOString(),
      recordedHeadSha: headSha,
    }
    await appendEvent(root, reviewId, event)
    return JSON.stringify(event, null, 2)
  },
})

export const load = tool({
  description: "Load EHA campaigns, SIB0/SIB1/SIB2 PASS/FAIL state, and repair-loop decisions from the durable review evidence ledger.",
  args: {
    reviewId: tool.schema.string().optional(),
  },
  async execute(args, context) {
    const root = context.worktree
    const reviewId = await resolveReviewId(root, context.sessionID, args.reviewId)
    const all = await events(root, reviewId)
    const campaigns = summarize(all)
    return JSON.stringify(
      {
        reviewId,
        eventCount: all.length,
        campaignCount: campaigns.length,
        campaigns,
        latestCampaign: campaigns[campaigns.length - 1] ?? null,
      },
      null,
      2,
    )
  },
})

export const mermaid = tool({
  description: "Render a bounded Mermaid flowchart of EHA targets, SIB verdicts, and repair lineage. This is a derived presentation of the evidence ledger, never acceptance authority itself.",
  args: {
    reviewId: tool.schema.string().optional(),
  },
  async execute(args, context) {
    const root = context.worktree
    const reviewId = await resolveReviewId(root, context.sessionID, args.reviewId)
    const all = await events(root, reviewId)
    return renderMermaid(all)
  },
})
