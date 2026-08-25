import { mkdtemp, readFile, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"
import { checkpoint, load, record_finding, start } from "../pack/.opencode/tools/review_state"

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
  await git(root, ["config", "user.email", "codesleuth-ci@example.invalid"])
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
  console.log("REVIEW STATE SMOKE PASS")
}

await main()
