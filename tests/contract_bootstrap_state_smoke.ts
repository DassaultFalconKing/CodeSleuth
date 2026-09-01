import { mkdtemp, mkdir, readFile, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"
import { load, materialize, record_candidate, record_decision, start } from "../pack/.opencode/tools/contract_bootstrap_state"

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
  const root = await mkdtemp(path.join(tmpdir(), "contract-bootstrap-"))
  await git(root, ["init", "-b", "main"])
  await git(root, ["config", "user.email", "codesleuth-ci@example.invalid"])
  await git(root, ["config", "user.name", "CodeSleuth CI"])
  await mkdir(path.join(root, "docs"), { recursive: true })
  await mkdir(path.join(root, "tests"), { recursive: true })
  await writeFile(path.join(root, "app.py"), "def update():\n    return 'new-source'\n", "utf8")
  await writeFile(path.join(root, "README.md"), "# Fixture\n\nUpdate success means the next start uses updated source.\n", "utf8")
  await writeFile(path.join(root, "tests", "test_update.py"), "def test_update_restart():\n    assert True\n", "utf8")
  await git(root, ["add", "."])
  await git(root, ["commit", "-m", "fixture"])
  const sha = await git(root, ["rev-parse", "HEAD"])
  const context = { worktree: root, directory: root, sessionID: "bootstrap-smoke", messageID: "m1", agent: "build" } as any

  const session = JSON.parse(await start.execute({ objective: "discover existing contracts", targetSha: sha }, context))
  assert(session.targetSha === sha, "bootstrap must bind exact HEAD")

  const agreed = JSON.parse(await record_candidate.execute({
    bootstrapId: session.bootstrapId,
    contractId: "fixture.update-restart",
    statement: "Update success means the next start uses updated source.",
    capabilityClass: "lifecycle",
    capabilityClassId: "CC-LIFE",
    triangulationStatus: "AGREE",
    codeEvidence: ["app.py"],
    docEvidence: ["README.md"],
    testEvidence: ["tests/test_update.py"],
    affectedPaths: ["app.py", "tests/**"],
    dependsOn: [],
    forbiddenRegressions: [{
      id: "FR-UPDATE-001",
      mustNot: "report update success while the next start still uses old source",
      proof: ["tests/test_update.py"],
    }],
  }, context))
  assert(agreed.codeEvidence[0].path === "app.py", "candidate evidence must retain repository path")
  assert(/^[0-9a-f]{40}$/.test(agreed.codeEvidence[0].blobHash), "candidate evidence must bind exact Git blob")

  await writeFile(path.join(root, "app.py"), "def update():\n    return 'dirty-uncommitted'\n", "utf8")
  let dirtyRejected = false
  try {
    await load.execute({ bootstrapId: session.bootstrapId }, context)
  } catch (error) {
    dirtyRejected = String(error).includes("TRACKED WORKTREE DIRTY")
  }
  assert(dirtyRejected, "tracked dirty bytes must invalidate brownfield evidence even when HEAD is unchanged")
  await git(root, ["checkout", "--", "app.py"])

  const contradicted = JSON.parse(await record_candidate.execute({
    bootstrapId: session.bootstrapId,
    contractId: "fixture.ambiguous-errors",
    statement: "Errors have one stable public status.",
    capabilityClass: "api",
    capabilityClassId: "CC-API",
    triangulationStatus: "CONTRADICTED",
    codeEvidence: ["app.py"],
    docEvidence: ["README.md"],
    affectedPaths: ["app.py"],
    forbiddenRegressions: [{ id: "FR-ERR-001", mustNot: "silently change public error semantics", proof: [] }],
  }, context))

  let contradictedAdoptionRejected = false
  try {
    await record_decision.execute({
      bootstrapId: session.bootstrapId,
      candidateId: contradicted.candidateId,
      decision: "adopt",
      rationale: "should fail",
      userApprovalStatement: "adopt it",
    }, context)
  } catch (error) {
    contradictedAdoptionRejected = String(error).includes("adopt requires AGREE") || String(error).includes("must be resolved")
  }
  assert(contradictedAdoptionRejected, "contradicted candidate cannot be adopted")

  await record_decision.execute({
    bootstrapId: session.bootstrapId,
    candidateId: contradicted.candidateId,
    decision: "defer",
    rationale: "sources disagree",
    userApprovalStatement: "defer until drift is resolved",
  }, context)
  await record_decision.execute({
    bootstrapId: session.bootstrapId,
    candidateId: agreed.candidateId,
    decision: "adopt",
    rationale: "code docs and executable test agree",
    userApprovalStatement: "adopt fixture.update-restart as the project contract",
  }, context)

  const before = JSON.parse(await load.execute({ bootstrapId: session.bootstrapId }, context))
  assert(before.candidates.length === 2, "candidate ledger must remain durable")
  assert(before.evidenceIntegrity === "PASS", "all candidate blob identities must be revalidated on resume")
  assert(before.candidates.find((item: any) => item.contractId === agreed.contractId).latestDecision.decision === "adopt", "latest user decision must be visible")

  const result = JSON.parse(await materialize.execute({ bootstrapId: session.bootstrapId }, context))
  assert(result.adoptedContracts.length === 1, "only explicitly adopted candidates materialize")
  assert(result.adoptedContracts[0].status === "implemented", "AGREE adoption materializes only as implemented")
  assert(result.worktreeIdentity === "NEW_UNCOMMITTED_CANDIDATE", "materialization must invalidate the old clean worktree identity")

  const registry = JSON.parse(await readFile(path.join(root, "docs", "protected-capabilities.json"), "utf8"))
  assert(registry.registry === "codesleuth-protected-capabilities", "bootstrap must create canonical registry identity")
  assert(registry.profile === "generic", "foreign bootstrap must use the generic registry profile")
  assert(registry.contracts.length === 1, "deferred candidate must not enter registry")
  assert(registry.contracts[0].protected_at === null, "brownfield bootstrap must never synthesize acceptance")
  assert(registry.contracts[0].bootstrap_provenance.exact_sha === sha, "materialized contract must retain exact discovery SHA")
  assert(registry.contracts[0].bootstrap_provenance.evidence_blobs.code[0].blobHash === agreed.codeEvidence[0].blobHash, "materialized provenance must retain source blob identity")
  assert(registry.contracts[0].forbidden_regressions.length === 1, "materialized contract requires negative obligation")
  assert(registry.contracts[0].forbidden_regressions[0].sib_origin === null, "brownfield bootstrap must not invent SIB origin")

  let duplicateMaterializationRejected = false
  try {
    await materialize.execute({ bootstrapId: session.bootstrapId }, context)
  } catch {
    duplicateMaterializationRejected = true
  }
  assert(duplicateMaterializationRejected, "bootstrap materialization must be append-once")

  await writeFile(path.join(root, "app.py"), "def update():\n    return 'moved-head'\n", "utf8")
  await git(root, ["add", "app.py"])
  await git(root, ["commit", "-m", "move head"])
  let movedHeadRejected = false
  try {
    await load.execute({ bootstrapId: session.bootstrapId }, context)
  } catch (error) {
    movedHeadRejected = String(error).includes("HEAD CHANGED")
  }
  assert(movedHeadRejected, "bootstrap evidence cannot silently transfer to a descendant SHA")

  console.log("CONTRACT BOOTSTRAP STATE SMOKE PASS")
}

await main()
