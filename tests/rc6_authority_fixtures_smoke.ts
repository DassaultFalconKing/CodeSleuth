import { access, cp, mkdtemp } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"
import { start as authorityStart, record_edge, load as authorityLoad } from "../pack/.opencode/tools/development_authority_state"
import { start as gateStart, record_gate, record_result, load as gateLoad } from "../pack/.opencode/tools/native_gate_state"
import { derive as deriveSurface } from "../pack/.opencode/tools/change_surface_state"
import { save_packet, load as packetLoad, scope_guard } from "../pack/.opencode/tools/development_continuation_state"
import { start as bootstrapStart, record_candidate } from "../pack/.opencode/tools/contract_bootstrap_state"

const FIXTURES = path.join(import.meta.dir, "fixtures", "rc6")
function assert(condition: unknown, message: string): asserts condition { if (!condition) throw new Error(message) }
async function git(root: string, args: string[]): Promise<string> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text(); const stderr = await new Response(proc.stderr).text(); const code = await proc.exited
  if (code !== 0) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`); return stdout.trim()
}
async function fixtureRepo(name: string) {
  const parent = await mkdtemp(path.join(tmpdir(), `rc6-${name}-`)); const root = path.join(parent, "repo")
  await cp(path.join(FIXTURES, name), root, { recursive: true })
  await git(root, ["init", "-b", "main"]); await git(root, ["config", "user.email", "ci@example.invalid"]); await git(root, ["config", "user.name", "CI"])
  await git(root, ["add", "."]); await git(root, ["commit", "-m", "fixture"])
  return { root, sha: await git(root, ["rev-parse", "HEAD"]), context: { worktree: root, directory: root, sessionID: `fixture-${name}`, messageID: "m1", agent: "build" } as any }
}

async function layeredTodoFixture() {
  const { root, sha, context } = await fixtureRepo("layered-todo")
  const authority = JSON.parse(await authorityStart.execute({ objective: "continue declared prerequisite", targetSha: sha }, context))
  const planning = JSON.parse(await record_edge.execute({ mapId: authority.mapId, relation: "CANONICAL_PLANNING_AUTHORITY", subject: "repository planning", object: "TODO.md", confidence: "CONFIRMED", rationale: "TODO explicitly declares itself the only planning source of truth", evidence: [{ path: "TODO.md", locator: "line 3: only planning source of truth" }] }, context))
  const active = JSON.parse(await record_edge.execute({ mapId: authority.mapId, relation: "ACTIVE_IMPLEMENTATION_SCOPE", subject: "TODO.md", object: "docs/SECURITY-STOP.md", confidence: "CONFIRMED", rationale: "planning SSOT declares the security document as the current prerequisite stop-gate", evidence: [{ path: "TODO.md", locator: "line 4: Current prerequisite stop-gate" }, { path: "docs/SECURITY-STOP.md", locator: "line 3: Objective" }] }, context))
  await record_edge.execute({ mapId: authority.mapId, relation: "SUPERSEDED_BY", subject: "docs/ROADMAP-OLD.md", object: "TODO.md", confidence: "CONFIRMED", rationale: "old roadmap explicitly declares itself superseded", evidence: [{ path: "docs/ROADMAP-OLD.md", locator: "line 3: Superseded by TODO.md" }] }, context)
  await record_edge.execute({ mapId: authority.mapId, relation: "SUPPORTING_EVIDENCE", subject: "docs/SECURITY-STOP.md", object: "docs/CURRENT-STATE.md", confidence: "CONFIRMED", rationale: "current-state note explicitly says it is evidence rather than planning authority", evidence: [{ path: "docs/CURRENT-STATE.md", locator: "line 3: evidence, not planning authority" }] }, context)
  await record_edge.execute({ mapId: authority.mapId, relation: "HISTORICAL_ARCHIVE", subject: "TODO.md", object: "docs/archive/SHIPPED.md", confidence: "CONFIRMED", rationale: "shipped work is explicitly historical evidence", evidence: [{ path: "docs/archive/SHIPPED.md", locator: "line 3: historical evidence only" }] }, context)
  const loadedAuthority = JSON.parse(await authorityLoad.execute({ mapId: authority.mapId }, context))
  assert(loadedAuthority.planningAuthorities.length === 1 && loadedAuthority.planningAuthorities[0].object === "TODO.md", "Fixture A must retain only TODO.md as canonical planning SSOT")
  assert(loadedAuthority.activeScopes.length === 1 && loadedAuthority.activeScopes[0].object === "docs/SECURITY-STOP.md", "Fixture A must select the prerequisite security stop-gate")
  assert(!loadedAuthority.planningAuthorities.some((edge: any) => edge.object === "docs/ROADMAP-OLD.md"), "Fixture A must not revive superseded roadmap")
  assert(loadedAuthority.relations.some((edge: any) => edge.relation === "SUPPORTING_EVIDENCE"), "Fixture A must retain supporting evidence separately")
  assert(loadedAuthority.relations.some((edge: any) => edge.relation === "HISTORICAL_ARCHIVE"), "Fixture A must retain shipped archive separately")

  const gates = JSON.parse(await gateStart.execute({ objective: "classify security acceptance", targetSha: sha }, context))
  const repoGate = JSON.parse(await record_gate.execute({ gateMapId: gates.gateMapId, name: "security verify", gateClass: "REPO_PROVABLE", required: true, command: "./verify.sh security", evidence: [{ path: "docs/SECURITY-STOP.md", locator: "line 6: Required repository gate" }, { path: "verify.sh", locator: "security branch" }] }, context))
  await record_gate.execute({ gateMapId: gates.gateMapId, name: "Temporal poller smoke", gateClass: "LIVE_RUNTIME_REQUIRED", required: true, evidence: [{ path: "docs/SECURITY-STOP.md", locator: "line 7: Live-only acceptance" }] }, context)
  let loadedGates = JSON.parse(await gateLoad.execute({ gateMapId: gates.gateMapId }, context))
  assert(loadedGates.handoffState === "CLOUD_TESTABILITY_REMAINING", "Fixture A repo gate must block live handoff until executed")
  await record_result.execute({ gateMapId: gates.gateMapId, gateId: repoGate.gateId, outcome: "PASS", nativeEvidence: "fixture ./verify.sh security exited 0" }, context)
  loadedGates = JSON.parse(await gateLoad.execute({ gateMapId: gates.gateMapId }, context))
  assert(loadedGates.handoffState === "LIVE_HANDOFF_READY", "Fixture A live-only proof must remain separate after cloud gate closes")
  assert(loadedGates.gates.some((gate: any) => gate.gateClass === "LIVE_RUNTIME_REQUIRED" && gate.outcome === "UNEXECUTED"), "Fixture A must preserve unexecuted live proof")

  const surface = JSON.parse(await deriveSurface.execute({ targetSha: sha, seedPaths: ["src/security/auth.py"] }, context))
  const packet = JSON.parse(await save_packet.execute({ targetSha: sha, authorityMapId: authority.mapId, nativeGateMapId: gates.gateMapId, changeSurfaceMapId: surface.surfaceMapId, planningAuthority: ["TODO.md"], activeScope: "docs/SECURITY-STOP.md", objective: "close authorization containment prerequisite", prerequisites: ["security stop-gate before capacity"], acceptedPredecessors: [], requiredReading: ["TODO.md", "docs/SECURITY-STOP.md", "docs/CURRENT-STATE.md"], allowedPaths: ["src/security/**", "tests/security/**"], forbiddenOrAdjacentPaths: [{ pattern: "src/capacity/**", classification: "ADJACENT_TRACK", rationale: "capacity is explicitly adjacent until the security prerequisite closes" }], repoProvableChecks: ["./verify.sh security"], liveRuntimeRequiredChecks: ["Temporal poller smoke"], authorityEdgeIds: [planning.edgeId, active.edgeId] }, context))
  const loadedPacket = JSON.parse(await packetLoad.execute({ packetId: packet.packetId }, context))
  assert(loadedPacket.activeScope === "docs/SECURITY-STOP.md", "Fixture A continuation packet must preserve the declared prerequisite")
  assert(!loadedPacket.acceptedPredecessors.includes("docs/archive/SHIPPED.md"), "Fixture A historical shipped evidence must never become an accepted predecessor")
  const adjacent = JSON.parse(await scope_guard.execute({ packetId: packet.packetId, proposedPaths: ["src/capacity/slots.py"] }, context))
  assert(adjacent.overall === "ADJACENT_TRACK", "Fixture A must reject premature capacity scope expansion")
}

async function waypointSessionFixture() {
  const { root, sha, context } = await fixtureRepo("waypoint-session")
  let registryExists = true
  try { await access(path.join(root, "docs", "protected-capabilities.json")) } catch { registryExists = false }
  assert(!registryExists, "Fixture B must begin without a protected-capability registry")

  const authority = JSON.parse(await authorityStart.execute({ objective: "continue active waypoint session", targetSha: sha }, context))
  const orientation = JSON.parse(await record_edge.execute({ mapId: authority.mapId, relation: "CANONICAL_PLANNING_AUTHORITY", subject: "track selection", object: "ORIENTATION.md", confidence: "CONFIRMED", rationale: "orientation explicitly selects the active track and session packet", evidence: [{ path: "ORIENTATION.md", locator: "lines 3-5: active track and current session" }] }, context))
  const waypoint = JSON.parse(await record_edge.execute({ mapId: authority.mapId, relation: "CANONICAL_PLANNING_AUTHORITY", subject: "work ordering", object: "WAYPOINT-PLAN.md", confidence: "CONFIRMED", rationale: "waypoint plan explicitly orders accepted, active, and later sessions", evidence: [{ path: "WAYPOINT-PLAN.md", locator: "lines 3-6: S01-S04 ordering" }] }, context))
  const active = JSON.parse(await record_edge.execute({ mapId: authority.mapId, relation: "ACTIVE_IMPLEMENTATION_SCOPE", subject: "ORIENTATION.md", object: "sessions/G2-S03.md", confidence: "CONFIRMED", rationale: "orientation explicitly names G2-S03 as current session packet", evidence: [{ path: "ORIENTATION.md", locator: "line 5: Current session packet" }, { path: "sessions/G2-S03.md", locator: "line 3: Objective" }] }, context))
  const predecessor = JSON.parse(await record_edge.execute({ mapId: authority.mapId, relation: "ACCEPTED_PREDECESSOR", subject: "sessions/G2-S03.md", object: "HANDOFF.md", confidence: "CONFIRMED", rationale: "handoff explicitly declares S02 accepted predecessor state", evidence: [{ path: "HANDOFF.md", locator: "line 3: S02 is accepted" }] }, context))
  const architecture = JSON.parse(await record_edge.execute({ mapId: authority.mapId, relation: "NORMATIVE_ARCHITECTURE", subject: "sessions/G2-S03.md", object: "docs/ADR-0003.md", confidence: "CONFIRMED", rationale: "current packet requires the accepted ADR as reading", evidence: [{ path: "ORIENTATION.md", locator: "line 6: Required reading" }, { path: "docs/ADR-0003.md", locator: "line 3: Status Accepted" }] }, context))
  await record_edge.execute({ mapId: authority.mapId, relation: "ADJACENT_PARALLEL_TRACK", subject: "sessions/G2-S03.md", object: "crates/graph/**", confidence: "CONFIRMED", rationale: "session packet explicitly declares graph work adjacent", evidence: [{ path: "sessions/G2-S03.md", locator: "line 5: Adjacent parallel track" }] }, context)
  await record_edge.execute({ mapId: authority.mapId, relation: "ACCEPTANCE_AUTHORITY", subject: "sessions/G2-S03.md", object: "scripts/verify.sh", confidence: "CONFIRMED", rationale: "session packet explicitly names the native verify gate", evidence: [{ path: "sessions/G2-S03.md", locator: "line 7: Required gate" }, { path: "scripts/verify.sh", locator: "fast branch" }] }, context)
  const loadedAuthority = JSON.parse(await authorityLoad.execute({ mapId: authority.mapId }, context))
  assert(loadedAuthority.activeScopes.length === 1 && loadedAuthority.activeScopes[0].object === "sessions/G2-S03.md", "Fixture B must preserve active session packet")
  assert(loadedAuthority.relations.some((edge: any) => edge.relation === "ACCEPTED_PREDECESSOR" && edge.object === "HANDOFF.md"), "Fixture B must preserve accepted predecessor")
  assert(loadedAuthority.relations.some((edge: any) => edge.relation === "NORMATIVE_ARCHITECTURE" && edge.object === "docs/ADR-0003.md"), "Fixture B must preserve required architecture reading")

  const gates = JSON.parse(await gateStart.execute({ objective: "map session native gates", targetSha: sha }, context))
  const fastGate = JSON.parse(await record_gate.execute({ gateMapId: gates.gateMapId, name: "fast verify", gateClass: "REPO_PROVABLE", required: true, command: "./scripts/verify.sh fast", evidence: [{ path: "sessions/G2-S03.md", locator: "line 7: Required gate" }, { path: "scripts/verify.sh", locator: "fast branch" }] }, context))
  await record_result.execute({ gateMapId: gates.gateMapId, gateId: fastGate.gateId, outcome: "PASS", nativeEvidence: "fixture fast gate exited 0" }, context)
  const surface = JSON.parse(await deriveSurface.execute({ targetSha: sha, seedPaths: ["crates/agent/src/lib.rs"] }, context))
  const packet = JSON.parse(await save_packet.execute({ targetSha: sha, authorityMapId: authority.mapId, nativeGateMapId: gates.gateMapId, changeSurfaceMapId: surface.surfaceMapId, planningAuthority: ["ORIENTATION.md", "WAYPOINT-PLAN.md"], activeScope: "sessions/G2-S03.md", objective: "implement bounded agent continuation path", prerequisites: [], acceptedPredecessors: ["HANDOFF.md"], requiredReading: ["ORIENTATION.md", "WAYPOINT-PLAN.md", "HANDOFF.md", "docs/ADR-0003.md"], allowedPaths: ["crates/agent/src/**", "tests/agent_contract.rs"], forbiddenOrAdjacentPaths: [{ pattern: "crates/graph/**", classification: "ADJACENT_TRACK", rationale: "graph work is a separate parallel track" }], repoProvableChecks: ["./scripts/verify.sh fast"], authorityEdgeIds: [orientation.edgeId, waypoint.edgeId, active.edgeId, predecessor.edgeId, architecture.edgeId] }, context))
  const loadedPacket = JSON.parse(await packetLoad.execute({ packetId: packet.packetId }, context))
  assert(loadedPacket.acceptedPredecessors.includes("HANDOFF.md"), "Fixture B continuation packet must preserve accepted predecessor")
  assert(loadedPacket.requiredReading.includes("WAYPOINT-PLAN.md") && loadedPacket.requiredReading.includes("docs/ADR-0003.md"), "Fixture B continuation packet must preserve required reading")
  const adjacent = JSON.parse(await scope_guard.execute({ packetId: packet.packetId, proposedPaths: ["crates/graph/src/lib.rs"] }, context))
  assert(adjacent.overall === "ADJACENT_TRACK", "Fixture B scope guard must reject adjacent graph track")

  const bootstrap = JSON.parse(await bootstrapStart.execute({ objective: "bootstrap target-local contracts without registry", targetSha: sha }, context))
  const candidate = JSON.parse(await record_candidate.execute({ bootstrapId: bootstrap.bootstrapId, contractId: "fixture.agent-packet-identity", statement: "The active agent path preserves the S03 packet identity contract.", capabilityClass: "agent", capabilityClassId: "CC-AGENT", triangulationStatus: "AGREE", codeEvidence: ["crates/agent/src/lib.rs"], docEvidence: ["sessions/G2-S03.md", "HANDOFF.md"], testEvidence: ["tests/agent_contract.rs"], affectedPaths: ["crates/agent/src/**", "tests/agent_contract.rs"], dependsOn: [], forbiddenRegressions: [{ id: "FR-AGENT-001", mustNot: "change packet identity semantics while S03 is active", proof: ["tests/agent_contract.rs"] }] }, context))
  assert(candidate.contractId === "fixture.agent-packet-identity" && /^[0-9a-f]{40}$/.test(candidate.codeEvidence[0].blobHash), "Fixture B registry absence must route cleanly to brownfield candidate bootstrap")
}

await layeredTodoFixture()
await waypointSessionFixture()
console.log("RC6 AUTHORITY FIXTURES SMOKE PASS")
