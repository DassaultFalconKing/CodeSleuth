import { mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"
import { ReviewCompaction } from "../pack/.opencode/plugins/review-compaction"
import { amend_finding, checkpoint, get_finding, list_amendments, load, record_finding, start } from "../pack/.opencode/tools/review_state"

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message)
}

async function git(root: string, args: string[]): Promise<void> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stderr = await new Response(proc.stderr).text()
  const code = await proc.exited
  if (code !== 0) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`)
}

async function main() {
  const root = await mkdtemp(path.join(tmpdir(), "review-state-smoke-"))
  await git(root, ["init"])
  await git(root, ["config", "user.email", "review-pack-ci@example.invalid"])
  await git(root, ["config", "user.name", "Review Pack CI"])
  await writeFile(path.join(root, "tracked.txt"), "alpha\nbeta\n", "utf8")
  await git(root, ["add", "tracked.txt"])
  await git(root, ["commit", "-m", "fixture"])

  const context = {
    worktree: root,
    directory: root,
    sessionID: "state-smoke-session",
    messageID: "message-1",
    agent: "repo-reviewer",
  } as any

  const started = JSON.parse(await start.execute({ objective: "state smoke", mode: "review" }, context))
  assert(started.schemaVersion === 2, "new checkpoints must use schemaVersion 2")

  const firstCheckpoint = JSON.parse(await checkpoint.execute({
    phase: "source-review",
    reviewedPaths: ["tracked.txt"],
    completed: ["inventory"],
  }, context))
  assert(firstCheckpoint.reviewedPaths.length === 1, "tracked path must be recorded")
  assert(firstCheckpoint.reviewedPathEvidence.length === 1, "tracked path must carry blob evidence")
  assert(firstCheckpoint.reviewedPathEvidence[0].blobHash, "blob evidence must not be empty")

  const finding1 = JSON.parse(await record_finding.execute({
    severity: "high",
    title: "first",
    path: "tracked.txt",
    startLine: 1,
    endLine: 1,
    explanation: "first evidence",
  }, context))
  const finding2 = JSON.parse(await record_finding.execute({
    severity: "medium",
    title: "second",
    path: "tracked.txt",
    startLine: 2,
    endLine: 2,
    explanation: "second evidence",
  }, context))
  assert(finding1.id !== finding2.id, "finding IDs must not depend on a racy line count")

  await writeFile(path.join(root, "tracked.txt"), "alpha changed\nbeta\n", "utf8")
  const resumed = JSON.parse(await load.execute({}, context))
  assert(resumed.coverageEvidenceComplete === true, "schema v2 checkpoint must have complete coverage evidence")
  assert(resumed.staleReviewedPaths.length === 1, "changed reviewed file must be reported stale")
  assert(resumed.staleReviewedPaths[0].path === "tracked.txt", "stale path must identify the changed file")

  await writeFile(path.join(root, "untracked.txt"), "not tracked\n", "utf8")
  let rejected = false
  try {
    await checkpoint.execute({ phase: "source-review", reviewedPaths: ["untracked.txt"] }, context)
  } catch {
    rejected = true
  }
  assert(rejected, "untracked reviewedPaths must be rejected")

  const statePath = path.join(root, ".opencode", "state", "reviews", started.reviewId, "state.json")
  JSON.parse(await readFile(statePath, "utf8"))

  const restarted = JSON.parse(await start.execute({ objective: "second state smoke", mode: "review" }, context))
  assert(restarted.reviewId !== started.reviewId, "each review start must allocate a fresh collision-safe review ID")
  const currentReview = JSON.parse(await load.execute({}, context))
  assert(currentReview.reviewId === restarted.reviewId, "session pointer must move to the newly started review")
  assert(currentReview.findingCount === 0, "new review history must not inherit findings from a prior review directory")
  const originalReview = JSON.parse(await load.execute({ reviewId: started.reviewId }, context))
  assert(originalReview.findingCount === 2, "prior review evidence must remain available under its original ID")
  assert(originalReview.amendmentLedgerPresent === false, "reviews with no amendment ledger remain compatible")
  assert(originalReview.findings[0].lifecycleStatus === "OPEN", "findings without amendments stay OPEN")
  assert(originalReview.findings[0].derivedStatus === "OPEN", "derivedStatus is lifecycle state, not last amendment type")

  const findingsPath = path.join(root, ".opencode", "state", "reviews", started.reviewId, "findings.ndjson")
  const originalFindingBytes = await readFile(findingsPath)
  const correctedOpen = JSON.parse(await amend_finding.execute({
    reviewId: started.reviewId,
    findingId: finding1.id,
    amendmentType: "correct",
    explanation: "restated without changing lifecycle",
    path: "tracked.txt",
    startLine: 1,
    endLine: 1,
  }, context))
  assert(correctedOpen.lifecycleStatus === "OPEN", "correct on OPEN preserves OPEN")
  assert((await readFile(findingsPath)).equals(originalFindingBytes), "amendments must not rewrite original finding lines")

  let closeRejected = false
  try {
    await amend_finding.execute({
      reviewId: started.reviewId,
      findingId: finding1.id,
      amendmentType: "close",
      explanation: "no verification",
    }, context)
  } catch {
    closeRejected = true
  }
  assert(closeRejected, "close requires real verification")

  const closed = JSON.parse(await amend_finding.execute({
    reviewId: started.reviewId,
    findingId: finding1.id,
    amendmentType: "close",
    explanation: "verified fix",
    verification: "bun tests/review_state_smoke.ts — PASS",
  }, context))
  assert(closed.lifecycleStatus === "CLOSED", "verified close yields CLOSED")
  const closedThenCorrect = JSON.parse(await amend_finding.execute({
    reviewId: started.reviewId,
    findingId: finding1.id,
    amendmentType: "correct",
    explanation: "metadata after close",
    path: "tracked.txt",
    startLine: 1,
    endLine: 1,
  }, context))
  assert(closedThenCorrect.lifecycleStatus === "CLOSED", "close -> correct remains CLOSED")

  let reopenRejected = false
  try {
    await amend_finding.execute({
      reviewId: started.reviewId,
      findingId: finding1.id,
      amendmentType: "reopen",
      explanation: "remembered evidence only",
    }, context)
  } catch {
    reopenRejected = true
  }
  assert(reopenRejected, "reopen without fresh tracked-source evidence must fail")

  const reopened = JSON.parse(await amend_finding.execute({
    reviewId: started.reviewId,
    findingId: finding1.id,
    amendmentType: "reopen",
    explanation: "still present",
    path: "tracked.txt",
    startLine: 2,
    endLine: 2,
  }, context))
  assert(reopened.lifecycleStatus === "REOPENED", "reopen with current path/range/blob/HEAD evidence succeeds")
  assert(reopened.blobHash, "reopen must capture current blob hash")
  assert(reopened.headSha, "reopen must capture current HEAD")

  const loadedLifecycle = JSON.parse(await load.execute({ reviewId: started.reviewId }, context))
  const gotLifecycle = JSON.parse(await get_finding.execute({ reviewId: started.reviewId, findingId: finding1.id }, context))
  const listedLifecycle = JSON.parse(await list_amendments.execute({ reviewId: started.reviewId, findingId: finding1.id }, context))
  const finding1Loaded = loadedLifecycle.findings.find((item: any) => item.id === finding1.id)
  assert(finding1Loaded.lifecycleStatus === "REOPENED", "load reports REOPENED")
  assert(gotLifecycle.lifecycleStatus === "REOPENED", "get_finding reports REOPENED")
  assert(listedLifecycle.lifecycleStatus === "REOPENED", "list_amendments reports REOPENED")
  assert(finding1Loaded.latestAmendmentId === gotLifecycle.latestAmendmentId, "load/get latest amendment ids agree")
  assert(gotLifecycle.latestAmendmentType === "reopen", "latestAmendmentType stays on the metadata axis")
  assert((await readFile(findingsPath)).equals(originalFindingBytes), "original finding lines stay byte-for-byte immutable after reopen")

  const compaction = await ReviewCompaction({ worktree: root } as any)
  const compact = (compaction as any)["experimental.session.compacting"]
  assert(typeof compact === "function", "review compaction hook must be registered")
  const reviewsBase = path.join(root, ".opencode", "state", "reviews")
  const sessionsDir = path.join(reviewsBase, "sessions")
  await mkdir(sessionsDir, { recursive: true })

  const corruptStateReview = "compaction-corrupt-state"
  await mkdir(path.join(reviewsBase, corruptStateReview), { recursive: true })
  await writeFile(path.join(sessionsDir, "compaction-corrupt-session.txt"), `${corruptStateReview}\n`, "utf8")
  await writeFile(path.join(reviewsBase, corruptStateReview, "state.json"), "{not valid json\n", "utf8")
  const corruptStateOutput = { context: [] as string[] }
  await compact({ sessionID: "compaction-corrupt-session" }, corruptStateOutput)
  assert(corruptStateOutput.context.length === 1, "corrupt checkpoint must degrade to one explicit compaction warning")
  assert(
    corruptStateOutput.context[0].includes("checkpoint unavailable") &&
      corruptStateOutput.context[0].includes("not valid JSON"),
    "corrupt checkpoint must not abort compaction or masquerade as authoritative state",
  )

  const partialLedgerReview = "compaction-partial-ledger"
  await mkdir(path.join(reviewsBase, partialLedgerReview), { recursive: true })
  await writeFile(path.join(sessionsDir, "compaction-ledger-session.txt"), `${partialLedgerReview}\n`, "utf8")
  await writeFile(
    path.join(reviewsBase, partialLedgerReview, "state.json"),
    JSON.stringify({
      objective: "compaction evidence",
      target: "HEAD",
      headSha: "abc123",
      phase: "source-review",
      completed: ["inventory"],
      reviewedPaths: ["tracked.txt"],
      openQuestions: [],
      next: ["continue"],
      note: "",
    }),
    "utf8",
  )
  await writeFile(
    path.join(reviewsBase, partialLedgerReview, "findings.ndjson"),
    `${JSON.stringify({ id: "F-valid", severity: "high", title: "valid", path: "tracked.txt", startLine: 1, endLine: 1, blobHash: "blob" })}\n{broken-json\n`,
    "utf8",
  )
  const partialLedgerOutput = { context: [] as string[] }
  await compact({ sessionID: "compaction-ledger-session" }, partialLedgerOutput)
  assert(partialLedgerOutput.context.length === 1, "partially corrupt finding ledger must still yield bounded continuation context")
  assert(partialLedgerOutput.context[0].includes('"id": "F-valid"'), "valid finding evidence must survive a corrupt neighboring line")
  assert(partialLedgerOutput.context[0].includes('"corruptFindingsSkipped": 1'), "compaction must disclose skipped corrupt finding lines")
  assert(partialLedgerOutput.context[0].includes("corrupt finding ledger line"), "degraded finding completeness must be visible to the model")

  console.log("REVIEW STATE SMOKE PASS")
}

await main()