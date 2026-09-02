import { mkdtemp, mkdir, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"
import { start as authorityStart, record_edge, load as authorityLoad } from "../pack/.opencode/tools/development_authority_state"
import { start as gateStart, record_gate } from "../pack/.opencode/tools/native_gate_state"
import { derive as deriveSurface } from "../pack/.opencode/tools/change_surface_state"
import { save_packet, load as packetLoad, scope_guard, record_isolation_unproven } from "../pack/.opencode/tools/development_continuation_state"

function assert(condition: unknown, message: string): asserts condition { if (!condition) throw new Error(message) }
async function git(root: string, args: string[]): Promise<string> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text(); const stderr = await new Response(proc.stderr).text(); const code = await proc.exited
  if (code !== 0) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`)
  return stdout.trim()
}

async function main() {
  const root = await mkdtemp(path.join(tmpdir(), "rc6-live-dogfood-repair-"))
  await git(root, ["init", "-b", "main"]); await git(root, ["config", "user.email", "ci@example.invalid"]); await git(root, ["config", "user.name", "CI"])
  await mkdir(path.join(root, "docs", "baseline"), { recursive: true }); await mkdir(path.join(root, "src"), { recursive: true })
  await writeFile(path.join(root, "TODO.md"), "# Plan\nCurrent scope: docs/SESSION.md\n", "utf8")
  await writeFile(path.join(root, "docs", "SESSION.md"), "# Session\nContinue after docs/S08.md. Read baseline docs.\n", "utf8")
  await writeFile(path.join(root, "docs", "S08.md"), "# Accepted predecessor\n", "utf8")
  await writeFile(path.join(root, "docs", "baseline", "hybrid-retrieval.json"), "{}\n", "utf8")
  await writeFile(path.join(root, "src", "lib.rs"), "pub fn live() {}\n", "utf8")
  await git(root, ["add", "."]); await git(root, ["commit", "-m", "fixture"])
  const sha = await git(root, ["rev-parse", "HEAD"])
  const context = { worktree: root, directory: root, sessionID: "rc6-live-dogfood", messageID: "m1", agent: "build" } as any

  const authority = JSON.parse(await authorityStart.execute({ objective: "continue exact target", targetSha: sha }, context))
  const planning = JSON.parse(await record_edge.execute({ mapId: authority.mapId, relation: "CANONICAL_PLANNING_AUTHORITY", subject: "repository", object: "TODO.md", confidence: "CONFIRMED", rationale: "plan", evidence: [{ path: "TODO.md", locator: "line 2" }] }, context))
  const active = JSON.parse(await record_edge.execute({ mapId: authority.mapId, relation: "ACTIVE_IMPLEMENTATION_SCOPE", subject: "TODO.md", object: "docs/SESSION.md", confidence: "CONFIRMED", rationale: "active", evidence: [{ path: "TODO.md", locator: "line 2" }] }, context))
  const predecessor = JSON.parse(await record_edge.execute({ mapId: authority.mapId, relation: "ACCEPTED_PREDECESSOR", subject: "docs/SESSION.md", object: "docs/S08.md", confidence: "CONFIRMED", rationale: "accepted predecessor", evidence: [{ path: "docs/SESSION.md", locator: "line 2" }] }, context))

  const wrongDirection = JSON.parse(await record_edge.execute({ mapId: authority.mapId, relation: "ACCEPTED_PREDECESSOR", subject: "wrong-scope", object: "docs/S08.md", confidence: "CONFIRMED", rationale: "wrong direction witness", evidence: [{ path: "docs/SESSION.md", locator: "line 2" }] }, context))

  const gateMap = JSON.parse(await gateStart.execute({ objective: "map gates", targetSha: sha }, context))
  await record_gate.execute({ gateMapId: gateMap.gateMapId, name: "repo verify", gateClass: "REPO_PROVABLE", required: true, command: "./verify.sh fast", evidence: [{ path: "docs/SESSION.md", locator: "line 2" }] }, context)
  await record_gate.execute({ gateMapId: gateMap.gateMapId, name: "hosted CI", gateClass: "HOSTED_CI_PROVABLE", required: true, command: "hosted ci", evidence: [{ path: "docs/SESSION.md", locator: "line 2" }] }, context)
  await record_gate.execute({ gateMapId: gateMap.gateMapId, name: "live smoke", gateClass: "LIVE_RUNTIME_REQUIRED", required: true, evidence: [{ path: "docs/SESSION.md", locator: "line 2" }] }, context)
  const surface = JSON.parse(await deriveSurface.execute({ targetSha: sha, seedPaths: ["src/lib.rs"] }, context))

  const isolation = JSON.parse(await record_isolation_unproven.execute({ targetSha: sha, stepId: "R2", attemptedIsolation: "fresh_subagent", reason: "fresh child command failed before the step ran" }, context))
  assert(isolation.outcome === "STEP_ISOLATION_UNPROVEN", "fresh-child failure must become a durable isolation event")

  const first = JSON.parse(await save_packet.execute({
    targetSha: sha, authorityMapId: authority.mapId, nativeGateMapId: gateMap.gateMapId, changeSurfaceMapId: surface.surfaceMapId,
    planningAuthority: ["TODO.md"], activeScope: "docs/SESSION.md", objective: "continue", prerequisites: ["bootstrap control plane"], acceptedPredecessors: ["docs/S08.md"], requiredReading: ["TODO.md", "docs/SESSION.md", "docs/S08.md"],
    allowedPaths: ["docs/baseline/", "src/lib.rs"], forbiddenOrAdjacentPaths: [{ pattern: "docs/archive/", classification: "ADJACENT_TRACK", rationale: "archive is adjacent" }],
    repoProvableChecks: ["./verify.sh fast"], hostedCiProvableChecks: ["hosted ci"], liveRuntimeRequiredChecks: ["live smoke"], operatorDecisionRequired: ["confirm production handoff"], blockers: ["known blocker"], uncertainties: ["known uncertainty"], authorityEdgeIds: [planning.edgeId, active.edgeId, predecessor.edgeId],
  }, context))

  const stripped = JSON.parse(await save_packet.execute({
    targetSha: sha, authorityMapId: authority.mapId, nativeGateMapId: gateMap.gateMapId, changeSurfaceMapId: surface.surfaceMapId,
    planningAuthority: ["TODO.md"], activeScope: "docs/SESSION.md", objective: "retry after validation conflict", prerequisites: [], acceptedPredecessors: [], requiredReading: [],
    allowedPaths: ["src/lib.rs"], forbiddenOrAdjacentPaths: [], repoProvableChecks: [], hostedCiProvableChecks: [], liveRuntimeRequiredChecks: [], operatorDecisionRequired: [], blockers: [], uncertainties: [], authorityEdgeIds: [planning.edgeId, active.edgeId],
  }, context))
  const loaded = JSON.parse(await packetLoad.execute({ packetId: stripped.packetId }, context))
  for (const [field, expected] of Object.entries({
    prerequisites: "bootstrap control plane", acceptedPredecessors: "docs/S08.md", requiredReading: "docs/S08.md", repoProvableChecks: "./verify.sh fast", hostedCiProvableChecks: "hosted ci", liveRuntimeRequiredChecks: "live smoke", operatorDecisionRequired: "confirm production handoff", blockers: "known blocker", uncertainties: "known uncertainty",
  })) assert(loaded[field].includes(expected), `packet retry must preserve prior ${field}`)
  assert(loaded.authorityEdgeIds.includes(predecessor.edgeId), "packet retry must retain authority edge needed by preserved predecessor")
  assert(loaded.isolationEventIds.includes(isolation.eventId), "packet must bind prior exact-target isolation events")
  assert(loaded.isolationEvents.some((event: any) => event.eventId === isolation.eventId), "packet load must expose durable isolation truth")

  const descendant = JSON.parse(await scope_guard.execute({ packetId: first.packetId, proposedPaths: ["docs/baseline/hybrid-retrieval.json"] }, context))
  assert(descendant.overall === "IN_SCOPE", "trailing directory literal must include descendants")

  let conceptualRejected = false
  try {
    await save_packet.execute({
      targetSha: sha, authorityMapId: authority.mapId, nativeGateMapId: gateMap.gateMapId, changeSurfaceMapId: surface.surfaceMapId,
      planningAuthority: ["TODO.md"], activeScope: "docs/SESSION.md", objective: "reject conceptual path", allowedPaths: ["W5 production toolcaller"], authorityEdgeIds: [planning.edgeId, active.edgeId],
    }, context)
  } catch (error) { conceptualRejected = String(error).includes("invalid repository path pattern") }
  assert(conceptualRejected, "conceptual scope labels must not be accepted as repository path patterns")

  let wrongDirectionRejected = false
  try {
    await save_packet.execute({
      targetSha: sha, authorityMapId: authority.mapId, nativeGateMapId: gateMap.gateMapId, changeSurfaceMapId: surface.surfaceMapId,
      planningAuthority: ["TODO.md"], activeScope: "docs/SESSION.md", objective: "reject wrong relation direction", acceptedPredecessors: ["docs/S08.md"], allowedPaths: ["src/lib.rs"], authorityEdgeIds: [planning.edgeId, active.edgeId, wrongDirection.edgeId],
    }, context)
  } catch (error) { wrongDirectionRejected = String(error).includes("direction") || String(error).includes("subject") }
  assert(wrongDirectionRejected, "accepted predecessor authority must be bound from the active scope, not any matching object")

  const selfLoopMap = JSON.parse(await authorityStart.execute({ objective: "reject self loop", targetSha: sha }, context))
  await record_edge.execute({ mapId: selfLoopMap.mapId, relation: "CANONICAL_PLANNING_AUTHORITY", subject: "repository", object: "TODO.md", confidence: "CONFIRMED", rationale: "plan", evidence: [{ path: "TODO.md", locator: "line 2" }] }, context)
  await record_edge.execute({ mapId: selfLoopMap.mapId, relation: "ACTIVE_IMPLEMENTATION_SCOPE", subject: "TODO.md", object: "docs/SESSION.md", confidence: "CONFIRMED", rationale: "active", evidence: [{ path: "TODO.md", locator: "line 2" }] }, context)
  let selfLoopRejected = false
  try {
    await record_edge.execute({ mapId: selfLoopMap.mapId, relation: "SUPERSEDED_BY", subject: "docs/S08.md", object: "docs/S08.md", confidence: "CONFIRMED", rationale: "nonsensical self-loop witness", evidence: [{ path: "docs/S08.md", locator: "line 1" }] }, context)
    await authorityLoad.execute({ mapId: selfLoopMap.mapId }, context)
  } catch (error) { selfLoopRejected = String(error).includes("SELF-LOOP") }
  assert(selfLoopRejected, "confirmed semantic authority self-loops must fail closed")

  console.log("RC6 LIVE DOGFOOD REPAIR REGRESSIONS PASS")
}

await main()
