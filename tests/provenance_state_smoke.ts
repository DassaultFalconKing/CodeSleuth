import { mkdtemp, readFile, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"
import { start as startReview } from "../pack/.opencode/tools/review_state"
import { bind, load } from "../pack/.opencode/tools/provenance_state"

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message)
}

async function git(root: string, args: string[]): Promise<string> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  const code = await proc.exited
  if (code !== 0) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`)
  return stdout.trim()
}

async function main() {
  const root = await mkdtemp(path.join(tmpdir(), "provenance-state-smoke-"))
  await git(root, ["init", "-b", "main"])
  await git(root, ["config", "user.email", "codesleuth-ci@example.invalid"])
  await git(root, ["config", "user.name", "CodeSleuth CI"])
  await writeFile(path.join(root, "tracked.txt"), "alpha\n", "utf8")
  await git(root, ["add", "tracked.txt"])
  await git(root, ["commit", "-m", "fixture"])
  const headA = await git(root, ["rev-parse", "HEAD"])

  const context = {
    worktree: root,
    directory: root,
    sessionID: "provenance-smoke-session",
    messageID: "message-1",
    agent: "build",
  } as any

  const review = JSON.parse(await startReview.execute({ objective: "provenance smoke", mode: "review" }, context))
  const bound = JSON.parse(await bind.execute({ actor: "tst1" }, context))
  assert(bound.reviewId === review.reviewId, "provenance must bind to the active review")
  assert(bound.headSha === headA, "provenance must bind to exact current HEAD")
  assert(/^tst1-[0-9a-f]{12}$/.test(bound.watermark), "watermark must use actor + 12 lowercase hex")
  assert(bound.trustworthy === true && bound.headMatch === true, "fresh bound sidecar must verify")

  const sidecar = JSON.parse(await readFile(path.join(root, ".opencode", "state", "reviews", review.reviewId, "provenance.json"), "utf8"))
  assert(sidecar.watermark === bound.watermark, "sidecar must persist exact watermark")

  const rebound = JSON.parse(await bind.execute({ actor: "tst1" }, context))
  assert(rebound.watermark === bound.watermark, "idempotent same-session bind must preserve watermark")

  let conflictingActorRejected = false
  try {
    await bind.execute({ actor: "other" }, context)
  } catch {
    conflictingActorRejected = true
  }
  assert(conflictingActorRejected, "same review must not be rebound to another actor")

  await writeFile(path.join(root, "tracked.txt"), "beta\n", "utf8")
  await git(root, ["add", "tracked.txt"])
  await git(root, ["commit", "-m", "move head"])
  const loaded = JSON.parse(await load.execute({ reviewId: review.reviewId }, context))
  assert(loaded.trustworthy === true, "stored watermark must remain verifiable after HEAD moves")
  assert(loaded.headMatch === false, "load must expose moved-HEAD freshness mismatch")

  let movedHeadRebindRejected = false
  try {
    await bind.execute({ actor: "tst1", reviewId: review.reviewId }, context)
  } catch {
    movedHeadRebindRejected = true
  }
  assert(movedHeadRebindRejected, "moved HEAD must not rewrite an existing provenance sidecar")

  console.log("provenance state smoke: PASS")
}

await main()
