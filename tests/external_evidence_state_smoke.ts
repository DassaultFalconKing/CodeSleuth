import { mkdtemp, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"
import { ingest, load } from "../pack/.opencode/tools/external_evidence_state"

function assert(condition: unknown, message: string): asserts condition { if (!condition) throw new Error(message) }
async function git(root: string, args: string[]): Promise<string> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text(); const stderr = await new Response(proc.stderr).text(); const code = await proc.exited
  if (code !== 0) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`); return stdout.trim()
}

async function main() {
  const root = await mkdtemp(path.join(tmpdir(), "external-evidence-"))
  await git(root, ["init", "-b", "main"]); await git(root, ["config", "user.email", "ci@example.invalid"]); await git(root, ["config", "user.name", "CI"])
  await writeFile(path.join(root, "README.md"), "fixture\n", "utf8"); await git(root, ["add", "."]); await git(root, ["commit", "-m", "fixture"])
  const sha = await git(root, ["rev-parse", "HEAD"])
  const context = { worktree: root, directory: root, sessionID: "external-smoke", messageID: "m1", agent: "build" } as any

  const fresh = JSON.parse(await ingest.execute({
    adapterId: "generic-host", repositorySha: sha, observedAt: new Date().toISOString(), freshnessTtlSeconds: 3600, checkId: "runtime-capacity", sourceKind: "HOST_OBSERVATION",
    sanitizedResult: "one inference slot observed; no credential material included", evidenceLocator: "local host probe /props summary", nativeOutcome: "OBSERVED", nativeDefinesOutcome: false, notes: "runtime observation only",
  }, context))
  assert(fresh.authority === false, "external observation must never become authority")
  assert(fresh.stale === false, "fresh observation should be fresh")

  const old = new Date(Date.now() - 7200_000).toISOString()
  const stale = JSON.parse(await ingest.execute({
    adapterId: "generic-host", repositorySha: sha, observedAt: old, freshnessTtlSeconds: 60, checkId: "old-health", sourceKind: "SERVICE_PROBE",
    sanitizedResult: "service answered its native health probe", evidenceLocator: "host probe health summary", nativeOutcome: "PASS", nativeDefinesOutcome: true, notes: "native check defines PASS",
  }, context))
  assert(stale.stale === true, "expired observation must be visibly stale")

  let fakePassRejected = false
  try {
    await ingest.execute({ adapterId: "generic-host", repositorySha: sha, observedAt: new Date().toISOString(), freshnessTtlSeconds: 60, checkId: "not-a-gate", sourceKind: "HOST_OBSERVATION", sanitizedResult: "looks okay", evidenceLocator: "manual observation", nativeOutcome: "PASS", nativeDefinesOutcome: false, notes: "" }, context)
  } catch (error) { fakePassRejected = String(error).includes("underlying native check defines") }
  assert(fakePassRejected, "PASS cannot be invented for an observation without native outcome semantics")

  let secretRejected = false
  try {
    await ingest.execute({ adapterId: "generic-host", repositorySha: sha, observedAt: new Date().toISOString(), freshnessTtlSeconds: 60, checkId: "secret", sourceKind: "COMMAND", sanitizedResult: "api_key=supersecret", evidenceLocator: "command output", nativeOutcome: "UNKNOWN", nativeDefinesOutcome: false, notes: "" }, context)
  } catch (error) { secretRejected = String(error).includes("forbidden") }
  assert(secretRejected, "obvious secret-bearing evidence must be rejected")

  const all = JSON.parse(await load.execute({ repositorySha: sha, adapterId: "generic-host" }, context))
  assert(all.authority === "evidence-only", "loaded observations remain evidence-only")
  assert(all.count === 2 && all.freshCount === 1 && all.staleCount === 1, "freshness summary must remain explicit")
  const onlyFresh = JSON.parse(await load.execute({ repositorySha: sha, includeStale: false }, context))
  assert(onlyFresh.count === 1 && onlyFresh.observations[0].checkId === "runtime-capacity", "stale observations can be excluded without deleting history")

  await writeFile(path.join(root, "README.md"), "dirty\n", "utf8")
  let dirtyRejected = false
  try { await load.execute({ repositorySha: sha }, context) } catch (error) { dirtyRejected = String(error).includes("TRACKED WORKTREE DIRTY") }
  assert(dirtyRejected, "external evidence navigation must remain exact-clean-head bound")

  console.log("EXTERNAL EVIDENCE STATE SMOKE PASS")
}

await main()
