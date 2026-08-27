import { mkdtemp, readFile, writeFile, appendFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"
import { amend_finding, get_amendment, get_finding, list_amendments, load, record_finding, start } from "../pack/.opencode/tools/review_state"

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

async function expectReject(action: () => Promise<unknown>, needle: string, message: string): Promise<string> {
  try {
    await action()
  } catch (error: any) {
    const text = String(error?.message ?? error)
    assert(text.includes(needle), `${message}: expected ${JSON.stringify(needle)} in ${JSON.stringify(text)}`)
    return text
  }
  throw new Error(`${message}: expected rejection`)
}

function reviewPaths(root: string, reviewId: string) {
  const dir = path.join(root, ".opencode", "state", "reviews", reviewId)
  return {
    dir,
    findings: path.join(dir, "findings.ndjson"),
    amendments: path.join(dir, "findings-amendments.ndjson"),
  }
}

async function fixture(label: string) {
  const root = await mkdtemp(path.join(tmpdir(), `review-amendments-${label}-`))
  await git(root, ["init"])
  await git(root, ["config", "user.email", "review-pack-ci@example.invalid"])
  await git(root, ["config", "user.name", "Review Pack CI"])
  const lines = Array.from({ length: 90 }, (_, index) => `line-${index + 1}`)
  await writeFile(path.join(root, "tracked.txt"), `${lines.join("\n")}\n`, "utf8")
  await git(root, ["add", "tracked.txt"])
  await git(root, ["commit", "-m", "fixture"])
  const context = {
    worktree: root,
    directory: root,
    sessionID: `amendments-${label}`,
    messageID: "message-1",
    agent: "repo-reviewer",
  } as any
  const started = JSON.parse(await start.execute({ objective: `${label} amendments`, mode: "review" }, context))
  const finding = JSON.parse(await record_finding.execute({
    severity: "high",
    title: `${label}-finding`,
    path: "tracked.txt",
    startLine: 1,
    endLine: 2,
    explanation: "fixture evidence",
  }, context))
  return { root, context, started, finding }
}

function reopenArgs(findingId: string, extra: Record<string, unknown> = {}) {
  return {
    findingId,
    amendmentType: "reopen",
    explanation: extra.explanation ?? "still present in current source",
    path: extra.path ?? "tracked.txt",
    startLine: extra.startLine ?? 3,
    endLine: extra.endLine ?? 4,
    ...Object.fromEntries(Object.entries(extra).filter(([key]) => !["explanation", "path", "startLine", "endLine"].includes(key))),
  }
}

async function main() {
  const { root, context, started, finding } = await fixture("core")
  const files = reviewPaths(root, started.reviewId)
  const originalFindings = await readFile(files.findings)

  const loadedLegacy = JSON.parse(await load.execute({}, context))
  assert(loadedLegacy.amendmentLedgerPresent === false, "legacy review must report no amendment ledger")
  assert(loadedLegacy.trustworthyAmendmentHistory === true, "missing amendment ledger remains trustworthy")
  assert(loadedLegacy.amendmentCount === 0, "legacy review amendment count is zero")
  assert(loadedLegacy.findings[0].lifecycleStatus === "OPEN", "legacy finding lifecycle is OPEN")
  assert(loadedLegacy.findings[0].derivedStatus === "OPEN", "derivedStatus is lifecycle, never CORRECTED")
  assert(loadedLegacy.findings[0].latestAmendmentId === null, "legacy finding has no amendment id")
  assert(loadedLegacy.findings[0].latestAmendmentType === null, "legacy finding has no amendment type")
  const gotLegacy = JSON.parse(await get_finding.execute({ findingId: finding.id }, context))
  assert(gotLegacy.lifecycleStatus === "OPEN" && gotLegacy.derivedStatus === "OPEN", "get_finding agrees with load on OPEN")
  const listedLegacy = JSON.parse(await list_amendments.execute({ findingId: finding.id }, context))
  assert(listedLegacy.count === 0 && listedLegacy.lifecycleStatus === "OPEN", "list_amendments agrees on empty OPEN history")

  const corrected = JSON.parse(await amend_finding.execute({
    findingId: finding.id,
    amendmentType: "correct",
    explanation: "severity/title restatement",
    newSeverity: "medium",
    newTitle: "restated title",
    path: "tracked.txt",
    startLine: 1,
    endLine: 2,
  }, context))
  assert(corrected.lifecycleStatus === "OPEN", "correct on OPEN preserves OPEN")
  assert(corrected.derivedStatus === "OPEN", "derivedStatus follows lifecycle, not amendment type")
  assert(corrected.latestAmendmentType === "correct", "latestAmendmentType remains the metadata axis")
  assert((await readFile(files.findings)).equals(originalFindings), "findings.ndjson is byte-for-byte immutable after correct")

  await expectReject(
    () => amend_finding.execute({
      findingId: finding.id,
      amendmentType: "close",
      explanation: "claimed fix without verification",
    }, context),
    "close requires verification",
    "close without verification",
  )
  assert((await readFile(files.findings)).equals(originalFindings), "failed close must not rewrite findings.ndjson")

  const closed = JSON.parse(await amend_finding.execute({
    findingId: finding.id,
    amendmentType: "close",
    explanation: "fixed and verified",
    verification: "bun tests/review_state_smoke.ts — PASS",
    regressionTests: ["tests/review_state_smoke.ts"],
  }, context))
  assert(closed.lifecycleStatus === "CLOSED", "verified close yields CLOSED")
  assert((await readFile(files.findings)).equals(originalFindings), "findings.ndjson is byte-for-byte immutable after close")

  const closedThenCorrect = JSON.parse(await amend_finding.execute({
    findingId: finding.id,
    amendmentType: "correct",
    explanation: "metadata restatement after close",
    path: "tracked.txt",
    startLine: 1,
    endLine: 2,
  }, context))
  assert(closedThenCorrect.lifecycleStatus === "CLOSED", "close -> correct remains CLOSED")
  assert(closedThenCorrect.latestAmendmentType === "correct", "correct is metadata after close")

  await expectReject(
    () => amend_finding.execute({
      findingId: finding.id,
      amendmentType: "reopen",
      explanation: "remembered reproduction without current source capture",
    }, context),
    "fresh current tracked-source evidence",
    "reopen without path/range",
  )
  await expectReject(
    () => amend_finding.execute({
      findingId: finding.id,
      amendmentType: "reopen",
      explanation: "path without range",
      path: "tracked.txt",
    }, context),
    "fresh current tracked-source evidence",
    "reopen without startLine/endLine",
  )

  const blobBefore = await git(root, ["hash-object", "--", "tracked.txt"])
  const headBefore = await git(root, ["rev-parse", "HEAD"])
  const reopened = JSON.parse(await amend_finding.execute(reopenArgs(finding.id), context))
  assert(reopened.lifecycleStatus === "REOPENED", "valid reopen with fresh evidence yields REOPENED")
  assert(reopened.path === "tracked.txt", "reopen captures explicit path")
  assert(reopened.startLine === 3 && reopened.endLine === 4, "reopen captures explicit range")
  assert(reopened.blobHash === blobBefore, "reopen captures current blob hash")
  assert(reopened.headSha === headBefore, "reopen captures current HEAD")
  assert(typeof reopened.excerpt === "string" && reopened.excerpt.includes("line-3"), "reopen captures current excerpt")
  assert((await readFile(files.findings)).equals(originalFindings), "findings.ndjson is byte-for-byte immutable after reopen")

  await expectReject(
    () => amend_finding.execute(reopenArgs(finding.id), context),
    "illegal finding lifecycle transition: REOPENED + reopen",
    "reopen when already REOPENED",
  )

  const closedAgain = JSON.parse(await amend_finding.execute({
    findingId: finding.id,
    amendmentType: "close",
    explanation: "fixed again",
    verification: "bun tests/review_state_amendments.ts — PASS",
  }, context))
  assert(closedAgain.lifecycleStatus === "CLOSED", "REOPENED -> close is legal")
  await expectReject(
    () => amend_finding.execute({
      findingId: finding.id,
      amendmentType: "close",
      explanation: "repeat close",
      verification: "already closed",
    }, context),
    "illegal finding lifecycle transition: CLOSED + close",
    "repeated close",
  )

  const loadedAgree = JSON.parse(await load.execute({}, context))
  const gotAgree = JSON.parse(await get_finding.execute({ findingId: finding.id }, context))
  const listedAgree = JSON.parse(await list_amendments.execute({ findingId: finding.id }, context))
  assert(loadedAgree.findings[0].lifecycleStatus === "CLOSED", "load lifecycle CLOSED")
  assert(gotAgree.lifecycleStatus === listedAgree.lifecycleStatus, "get/list lifecycle agree")
  assert(gotAgree.latestAmendmentId === listedAgree.latestAmendmentId, "get/list latest amendment id agree")
  assert(gotAgree.latestAmendmentType === listedAgree.latestAmendmentType, "get/list latest amendment type agree")
  assert(loadedAgree.findings[0].latestAmendmentId === gotAgree.latestAmendmentId, "load/get latest amendment id agree")
  assert(loadedAgree.amendmentCount === listedAgree.amendmentCount, "load/list amendment counts agree")
  assert(gotAgree.amendmentCount === listedAgree.count, "get finding amendmentCount agrees with list count")
  const fetched = JSON.parse(await get_amendment.execute({ amendmentId: gotAgree.latestAmendmentId }, context))
  assert(fetched.id === gotAgree.latestAmendmentId, "get_amendment returns the latest id")

  await expectReject(
    () => amend_finding.execute({
      findingId: finding.id,
      amendmentType: "reopen",
      explanation: "untracked evidence",
      path: "missing.txt",
      startLine: 1,
      endLine: 1,
    }, context),
    "not a tracked file",
    "reopen untracked path",
  )
  await expectReject(
    () => amend_finding.execute({
      findingId: finding.id,
      amendmentType: "reopen",
      explanation: "range too large",
      path: "tracked.txt",
      startLine: 1,
      endLine: 81,
    }, context),
    "80 lines",
    "reopen >80 lines",
  )
  await expectReject(
    () => record_finding.execute({
      severity: "low",
      title: "too-wide",
      path: "tracked.txt",
      startLine: 1,
      endLine: 81,
      explanation: "too many lines",
    }, context),
    "80 lines",
    "record_finding >80 lines",
  )

  const replacement = JSON.parse(await record_finding.execute({
    severity: "medium",
    title: "replacement",
    path: "tracked.txt",
    startLine: 5,
    endLine: 6,
    explanation: "better scoped",
  }, context))
  const superseded = JSON.parse(await amend_finding.execute({
    findingId: finding.id,
    amendmentType: "supersede",
    explanation: "replaced after close",
    supersededBy: replacement.id,
  }, context))
  assert(superseded.lifecycleStatus === "SUPERSEDED", "CLOSED -> supersede is legal")
  const afterSupersedeCorrect = JSON.parse(await amend_finding.execute({
    findingId: finding.id,
    amendmentType: "correct",
    explanation: "metadata on superseded finding",
    path: "tracked.txt",
    startLine: 1,
    endLine: 2,
  }, context))
  assert(afterSupersedeCorrect.lifecycleStatus === "SUPERSEDED", "supersede -> correct remains SUPERSEDED")
  await expectReject(
    () => amend_finding.execute({
      findingId: finding.id,
      amendmentType: "supersede",
      explanation: "replace terminal relation",
      supersededBy: replacement.id,
    }, context),
    "illegal finding lifecycle transition: SUPERSEDED + supersede",
    "repeated supersede",
  )
  await expectReject(
    () => amend_finding.execute({
      findingId: finding.id,
      amendmentType: "close",
      explanation: "close superseded",
      verification: "no",
    }, context),
    "illegal finding lifecycle transition: SUPERSEDED + close",
    "close when SUPERSEDED",
  )
  await expectReject(
    () => amend_finding.execute(reopenArgs(finding.id), context),
    "illegal finding lifecycle transition: SUPERSEDED + reopen",
    "reopen when SUPERSEDED",
  )
  assert((await readFile(files.findings)).equals(originalFindings) === false, "second finding appends to findings.ndjson")
  const findingsAfterReplacement = await readFile(files.findings)
  await amend_finding.execute({
    findingId: replacement.id,
    amendmentType: "correct",
    explanation: "metadata on replacement",
    path: "tracked.txt",
    startLine: 5,
    endLine: 6,
  }, context)
  assert((await readFile(files.findings)).equals(findingsAfterReplacement), "later amendments still leave finding lines immutable")

  const cycleRoot = await fixture("cycles")
  const a = cycleRoot.finding
  const b = JSON.parse(await record_finding.execute({
    severity: "high",
    title: "b",
    path: "tracked.txt",
    startLine: 7,
    endLine: 8,
    explanation: "b",
  }, cycleRoot.context))
  const c = JSON.parse(await record_finding.execute({
    severity: "high",
    title: "c",
    path: "tracked.txt",
    startLine: 9,
    endLine: 10,
    explanation: "c",
  }, cycleRoot.context))
  await expectReject(
    () => amend_finding.execute({
      findingId: a.id,
      amendmentType: "supersede",
      explanation: "missing target",
    }, cycleRoot.context),
    "supersede requires supersededBy",
    "supersede without target",
  )
  await expectReject(
    () => amend_finding.execute({
      findingId: a.id,
      amendmentType: "supersede",
      explanation: "unknown target",
      supersededBy: "F-does-not-exist",
    }, cycleRoot.context),
    "supersededBy finding not found",
    "supersede missing same-review target",
  )
  await expectReject(
    () => amend_finding.execute({
      findingId: a.id,
      amendmentType: "supersede",
      explanation: "self",
      supersededBy: a.id,
    }, cycleRoot.context),
    "cannot supersede a finding with itself",
    "self-supersede",
  )
  await amend_finding.execute({
    findingId: a.id,
    amendmentType: "supersede",
    explanation: "a -> b",
    supersededBy: b.id,
  }, cycleRoot.context)
  await expectReject(
    () => amend_finding.execute({
      findingId: b.id,
      amendmentType: "supersede",
      explanation: "b -> a two-node cycle",
      supersededBy: a.id,
    }, cycleRoot.context),
    "supersede would create a cycle",
    "two-node cycle",
  )
  await amend_finding.execute({
    findingId: b.id,
    amendmentType: "supersede",
    explanation: "b -> c",
    supersededBy: c.id,
  }, cycleRoot.context)
  await expectReject(
    () => amend_finding.execute({
      findingId: c.id,
      amendmentType: "supersede",
      explanation: "c -> a longer cycle",
      supersededBy: a.id,
    }, cycleRoot.context),
    "supersede would create a cycle",
    "longer cycle",
  )

  const other = await fixture("other-review")
  await expectReject(
    () => amend_finding.execute({
      findingId: a.id,
      amendmentType: "supersede",
      explanation: "cross-review",
      supersededBy: other.finding.id,
    }, cycleRoot.context),
    "supersededBy finding not found",
    "supersede target in another review",
  )

  const retractRoot = await fixture("retract")
  const retracted = JSON.parse(await amend_finding.execute({
    findingId: retractRoot.finding.id,
    amendmentType: "retract",
    explanation: "invalid finding; contradicted by tests",
  }, retractRoot.context))
  assert(retracted.lifecycleStatus === "RETRACTED", "OPEN -> retract yields RETRACTED")
  const retractCorrect = JSON.parse(await amend_finding.execute({
    findingId: retractRoot.finding.id,
    amendmentType: "correct",
    explanation: "metadata on retracted finding",
    path: "tracked.txt",
    startLine: 1,
    endLine: 2,
  }, retractRoot.context))
  assert(retractCorrect.lifecycleStatus === "RETRACTED", "correct on RETRACTED stays RETRACTED")
  await expectReject(
    () => amend_finding.execute(reopenArgs(retractRoot.finding.id), retractRoot.context),
    "illegal finding lifecycle transition: RETRACTED + reopen",
    "reopen-from-retract is not defined",
  )
  await expectReject(
    () => amend_finding.execute({
      findingId: retractRoot.finding.id,
      amendmentType: "retract",
      explanation: "repeat retract",
    }, retractRoot.context),
    "illegal finding lifecycle transition: RETRACTED + retract",
    "repeated retract",
  )
  await expectReject(
    () => amend_finding.execute({
      findingId: retractRoot.finding.id,
      amendmentType: "close",
      explanation: "close retracted",
      verification: "no",
    }, retractRoot.context),
    "illegal finding lifecycle transition: RETRACTED + close",
    "close when RETRACTED",
  )
  await expectReject(
    () => amend_finding.execute({
      findingId: retractRoot.finding.id,
      amendmentType: "supersede",
      explanation: "supersede retracted",
      supersededBy: retractRoot.finding.id,
    }, retractRoot.context),
    "illegal finding lifecycle transition: RETRACTED + supersede",
    "supersede when RETRACTED",
  )

  const openReopen = await fixture("open-reopen")
  await expectReject(
    () => amend_finding.execute(reopenArgs(openReopen.finding.id), openReopen.context),
    "illegal finding lifecycle transition: OPEN + reopen",
    "reopen when OPEN",
  )

  const rapid = await fixture("rapid-ids")
  const ids = new Set<string>()
  for (let index = 0; index < 20; index++) {
    const amendment = JSON.parse(await amend_finding.execute({
      findingId: rapid.finding.id,
      amendmentType: "correct",
      explanation: `rapid ${index}`,
      path: "tracked.txt",
      startLine: 1,
      endLine: 2,
    }, rapid.context))
    assert(!ids.has(amendment.id), `rapid amendment id collided: ${amendment.id}`)
    ids.add(amendment.id)
  }
  assert(ids.size === 20, "rapid amendment IDs must all be unique")
  const parallel = await Promise.all(Array.from({ length: 8 }, (_, index) => amend_finding.execute({
    findingId: rapid.finding.id,
    amendmentType: "correct",
    explanation: `parallel ${index}`,
    path: "tracked.txt",
    startLine: 1,
    endLine: 2,
  }, rapid.context)))
  const parallelIds = parallel.map((item) => JSON.parse(item).id)
  assert(new Set(parallelIds).size === parallelIds.length, "parallel amendment IDs must not collide")
  assert(parallelIds.every((id) => !ids.has(id)), "parallel IDs must not collide with sequential IDs")

  const corrupt = await fixture("corrupt")
  const first = JSON.parse(await amend_finding.execute({
    findingId: corrupt.finding.id,
    amendmentType: "correct",
    explanation: "valid first amendment",
    path: "tracked.txt",
    startLine: 1,
    endLine: 2,
  }, corrupt.context))
  const corruptFiles = reviewPaths(corrupt.root, corrupt.started.reviewId)
  const findingsBeforeCorrupt = await readFile(corruptFiles.findings)
  await appendFile(corruptFiles.amendments, '{"id":"FA-torn","amends":', "utf8")
  const loadedCorrupt = JSON.parse(await load.execute({}, corrupt.context))
  assert(loadedCorrupt.amendmentLedgerCorrupt === true, "load must surface torn amendment ledger")
  assert(loadedCorrupt.trustworthyAmendmentHistory === false, "torn ledger is untrustworthy")
  assert(loadedCorrupt.corruptAmendmentRecords.length >= 1, "corrupt records are visible")
  assert(
    loadedCorrupt.corruptAmendmentRecords.some((item: any) => String(item.reason).includes("torn") || String(item.reason).includes("unparseable")),
    "torn/unparseable reason must be visible",
  )
  assert(loadedCorrupt.findings[0].lifecycleStatus === "UNTRUSTED", "no trustworthy lifecycle from incomplete history")
  assert(loadedCorrupt.findings[0].derivedStatus === "UNTRUSTED", "derivedStatus must not silently stay OPEN/CORRECTED")
  const gotCorrupt = JSON.parse(await get_finding.execute({ findingId: corrupt.finding.id }, corrupt.context))
  const listedCorrupt = JSON.parse(await list_amendments.execute({ findingId: corrupt.finding.id }, corrupt.context))
  assert(gotCorrupt.lifecycleStatus === "UNTRUSTED" && listedCorrupt.lifecycleStatus === "UNTRUSTED", "load/get/list agree on UNTRUSTED")
  assert(listedCorrupt.amendmentLedgerCorrupt === true, "list surfaces corruption")
  await expectReject(
    () => amend_finding.execute({
      findingId: corrupt.finding.id,
      amendmentType: "close",
      explanation: "must not append onto corrupt history",
      verification: "no",
    }, corrupt.context),
    "corrupt/untrustworthy",
    "mutation blocked on corrupt ledger",
  )
  assert((await readFile(corruptFiles.findings)).equals(findingsBeforeCorrupt), "corrupt ledger mutation attempt must not rewrite findings.ndjson")
  const stillThere = JSON.parse(await get_amendment.execute({ amendmentId: first.id }, corrupt.context))
  assert(stillThere.id === first.id, "parsed prefix records remain visible")
  assert(stillThere.amendmentLedgerCorrupt === true, "get_amendment surfaces ledger corruption")

  console.log("REVIEW STATE AMENDMENTS PASS")
}

await main()
