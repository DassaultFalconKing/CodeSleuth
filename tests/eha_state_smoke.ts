import { mkdtemp, readFile, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"
import { start as startReview } from "../pack/.opencode/tools/review_state"
import { load, mermaid, record_repair, record_verdict, start_campaign } from "../pack/.opencode/tools/eha_state"

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
  const root = await mkdtemp(path.join(tmpdir(), "eha-state-smoke-"))
  await git(root, ["init", "-b", "main"])
  await git(root, ["config", "user.email", "codesleuth-ci@example.invalid"])
  await git(root, ["config", "user.name", "CodeSleuth CI"])
  await writeFile(path.join(root, "tracked.txt"), "alpha\n", "utf8")
  await git(root, ["add", "tracked.txt"])
  await git(root, ["commit", "-m", "fixture A"])
  const shaA = await git(root, ["rev-parse", "HEAD"])

  const context = {
    worktree: root,
    directory: root,
    sessionID: "eha-smoke-session",
    messageID: "message-1",
    agent: "build",
  } as any

  const review = JSON.parse(await startReview.execute({ objective: "EHA smoke", mode: "review" }, context))
  const campaignA = JSON.parse(await start_campaign.execute({ targetSha: shaA, targetBranch: "main" }, context))
  assert(campaignA.targetSha === shaA, "campaign must bind to literal current HEAD")

  await record_verdict.execute({
    campaignId: campaignA.campaignId,
    level: "SIB0",
    verdict: "PASS",
    profile: "architecture inventory",
    summary: "capability inventory coherent",
    evidence: ["architecture contract inspected"],
  }, context)
  await record_verdict.execute({
    campaignId: campaignA.campaignId,
    level: "SIB1",
    verdict: "FAIL",
    profile: "capability implementation",
    summary: "one capability path is broken",
    evidence: ["focused capability test failed"],
    blockerFindingIds: ["F-test-blocker"],
  }, context)

  let state = JSON.parse(await load.execute({}, context))
  assert(state.latestCampaign.verdicts.SIB0.verdict === "PASS", "SIB0 PASS must persist")
  assert(state.latestCampaign.verdicts.SIB1.verdict === "FAIL", "SIB1 FAIL must persist")
  assert(state.latestCampaign.claimable.SIB0 === true, "SIB0 should be claimable")
  assert(state.latestCampaign.claimable.SIB1 === false, "failed SIB1 must not be claimable")
  assert(state.latestCampaign.claimable.SIB2 === false, "SIB2 cannot be inherited or implied")

  let failToPassRejected = false
  try {
    await record_verdict.execute({
      campaignId: campaignA.campaignId,
      level: "SIB1",
      verdict: "PASS",
      profile: "capability implementation",
      summary: "must not rehabilitate recorded FAIL in same campaign",
      evidence: ["attempted overwrite"],
    }, context)
  } catch {
    failToPassRejected = true
  }
  assert(failToPassRejected, "SIB1 FAIL must not become SIB1 PASS in the same campaign")

  let secondCampaignRejected = false
  try {
    await start_campaign.execute({ targetSha: shaA, targetBranch: "main" }, context)
  } catch {
    secondCampaignRejected = true
  }
  assert(secondCampaignRejected, "second campaign must not rehabilitate a SHA with recorded EHA FAIL")

  let mismatchRejected = false
  try {
    await record_repair.execute({
      campaignId: campaignA.campaignId,
      level: "SIB1",
      classification: "composition_e2e",
      decision: "repair",
      failingTest: "capability smoke",
      failure: "broken basic path",
      reproduction: "run capability smoke",
      repairBranch: "fix/eha-sib1-capability",
    }, context)
  } catch {
    mismatchRejected = true
  }
  assert(mismatchRejected, "repair classification must match blocking SIB level")

  await writeFile(path.join(root, "tracked.txt"), "alpha\nrepair\n", "utf8")
  await git(root, ["add", "tracked.txt"])
  await git(root, ["commit", "-m", "repair B"])
  const shaB = await git(root, ["rev-parse", "HEAD"])

  let movedHeadRejected = false
  try {
    await record_verdict.execute({
      campaignId: campaignA.campaignId,
      level: "SIB2",
      verdict: "PASS",
      profile: "invalid old campaign",
      summary: "must not record against moved HEAD",
    }, context)
  } catch (error) {
    movedHeadRejected = String(error).includes("EHA INVALIDATED")
  }
  assert(movedHeadRejected, "old EHA target must reject verdicts after HEAD changes")

  const repair = JSON.parse(await record_repair.execute({
    campaignId: campaignA.campaignId,
    level: "SIB1",
    classification: "capability_implementation",
    decision: "repair",
    failingTest: "capability smoke",
    failure: "broken basic path",
    reproduction: "run capability smoke",
    repairBranch: "fix/eha-sib1-capability",
    candidateSha: shaB,
    regressionTests: ["tests/capability_regression.ts"],
    focusedTests: ["bun tests/capability_regression.ts"],
    notes: "minimum repair delta",
  }, context))
  assert(repair.failingSha === shaA, "repair must retain failing SHA")
  assert(repair.candidateSha === shaB, "repair must retain candidate SHA")

  const campaignB = JSON.parse(await start_campaign.execute({ targetSha: shaB, targetBranch: "fix/eha-sib1-capability" }, context))
  for (const level of ["SIB0", "SIB1", "SIB2"] as const) {
    await record_verdict.execute({
      campaignId: campaignB.campaignId,
      level,
      verdict: "PASS",
      profile: `${level} profile`,
      summary: `${level} accepted on repaired exact head`,
      evidence: [`${level} checks passed on ${shaB}`],
    }, context)
  }

  state = JSON.parse(await load.execute({}, context))
  assert(state.campaignCount === 2, "repair SHA must start a new EHA campaign")
  assert(state.campaigns[0].verdicts.SIB1.verdict === "FAIL", "failing SHA must remain failed in history")
  assert(state.latestCampaign.targetSha === shaB, "latest campaign must target repaired SHA")
  assert(state.latestCampaign.claimable.SIB2 === true, "new SHA must become SIB2 claimable only after fresh SIB0/SIB1/SIB2 PASS")

  state = JSON.parse(await load.execute({}, context))
  assert(state.campaigns[0].verdicts.SIB1.verdict === "FAIL", "failed SHA must remain failed after later repair events")
  assert(state.campaigns[0].claimable.SIB1 === false, "failed SHA must not become claimable after later events")

  const diagram = await mermaid.execute({}, context)
  assert(diagram.includes("flowchart TD"), "EHA ledger must render Mermaid")
  assert(diagram.includes(shaA.slice(0, 12)), "diagram must contain failing target")
  assert(diagram.includes(shaB.slice(0, 12)), "diagram must contain repaired target")
  assert(diagram.includes("SIB1: FAIL"), "diagram must retain failed SIB verdict")
  assert(diagram.includes("SIB2: PASS"), "diagram must show accepted repaired target")

  const ledger = path.join(root, ".opencode", "state", "reviews", review.reviewId, "eha.ndjson")
  const raw = await readFile(ledger, "utf8")
  assert(raw.includes('"type":"campaign_started"'), "ledger must persist campaign events")
  assert(raw.includes('"type":"repair"'), "ledger must persist repair events")

  console.log("EHA STATE SMOKE PASS")
}

await main()
