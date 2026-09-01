import { mkdtemp, mkdir, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"
import { start as authorityStart, record_edge, load as authorityLoad } from "../pack/.opencode/tools/development_authority_state"
import { start as gateStart, record_gate, record_result, load as gateLoad } from "../pack/.opencode/tools/native_gate_state"
import { derive as deriveSurface } from "../pack/.opencode/tools/change_surface_state"
import { save_packet, load as packetLoad, scope_guard } from "../pack/.opencode/tools/development_continuation_state"

function assert(condition: unknown, message: string): asserts condition { if (!condition) throw new Error(message) }
async function git(root: string, args: string[]): Promise<string> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text(); const stderr = await new Response(proc.stderr).text(); const code = await proc.exited
  if (code !== 0) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`); return stdout.trim()
}

async function main() {
  const root = await mkdtemp(path.join(tmpdir(), "development-continuation-"))
  await git(root, ["init", "-b", "main"]); await git(root, ["config", "user.email", "ci@example.invalid"]); await git(root, ["config", "user.name", "CI"])
  await mkdir(path.join(root, "docs"), { recursive: true }); await mkdir(path.join(root, "src", "core"), { recursive: true }); await mkdir(path.join(root, "src", "graph"), { recursive: true }); await mkdir(path.join(root, ".github", "workflows"), { recursive: true })
  await writeFile(path.join(root, "TODO.md"), "# Current plan\nThis file is the only planning source of truth. Current implementation scope is docs/SESSION.md. OLD_ROADMAP.md is superseded.\n", "utf8")
  await writeFile(path.join(root, "OLD_ROADMAP.md"), "# Historical roadmap\nSuperseded by TODO.md.\n", "utf8")
  await writeFile(path.join(root, "docs", "SESSION.md"), "# Session\nAllowed paths: src/core/**. Adjacent graph track: src/graph/**. Required gate: ./verify.sh fast. Hosted CI is also required.\n", "utf8")
  await writeFile(path.join(root, "Cargo.toml"), "[package]\nname = \"continuation-fixture\"\nversion = \"0.0.0\"\n", "utf8")
  await writeFile(path.join(root, "verify.sh"), "#!/bin/sh\nexit 0\n", "utf8")
  await writeFile(path.join(root, ".github", "workflows", "ci.yml"), "name: ci\non: [push]\njobs: {}\n", "utf8")
  await writeFile(path.join(root, "src", "core", "lib.rs"), "pub fn core() {}\n", "utf8")
  await writeFile(path.join(root, "src", "graph", "lib.rs"), "pub fn graph() {}\n", "utf8")
  await git(root, ["add", "."]); await git(root, ["commit", "-m", "fixture"])
  const sha = await git(root, ["rev-parse", "HEAD"])
  const context = { worktree: root, directory: root, sessionID: "rc6-smoke", messageID: "m1", agent: "build" } as any

  const authority = JSON.parse(await authorityStart.execute({ objective: "continue development", targetSha: sha }, context))
  const planning = JSON.parse(await record_edge.execute({ mapId: authority.mapId, relation: "CANONICAL_PLANNING_AUTHORITY", subject: "repository planning", object: "TODO.md", confidence: "CONFIRMED", rationale: "TODO explicitly declares itself the only planning source of truth", evidence: [{ path: "TODO.md", locator: "line 2: only planning source of truth" }] }, context))
  const active = JSON.parse(await record_edge.execute({ mapId: authority.mapId, relation: "ACTIVE_IMPLEMENTATION_SCOPE", subject: "TODO.md", object: "docs/SESSION.md", confidence: "CONFIRMED", rationale: "TODO explicitly names the current implementation scope", evidence: [{ path: "TODO.md", locator: "line 2: Current implementation scope is docs/SESSION.md" }, { path: "docs/SESSION.md", locator: "line 2: Allowed paths" }] }, context))
  await record_edge.execute({ mapId: authority.mapId, relation: "SUPERSEDED_BY", subject: "OLD_ROADMAP.md", object: "TODO.md", confidence: "CONFIRMED", rationale: "historical roadmap explicitly says it is superseded", evidence: [{ path: "OLD_ROADMAP.md", locator: "line 2: Superseded by TODO.md" }] }, context)
  await record_edge.execute({ mapId: authority.mapId, relation: "ADJACENT_PARALLEL_TRACK", subject: "docs/SESSION.md", object: "src/graph/**", confidence: "CONFIRMED", rationale: "session declares graph work adjacent", evidence: [{ path: "docs/SESSION.md", locator: "line 2: Adjacent graph track" }] }, context)
  const authorityLoaded = JSON.parse(await authorityLoad.execute({ mapId: authority.mapId }, context))
  assert(authorityLoaded.evidenceIntegrity === "PASS", "authority evidence must revalidate")
  assert(authorityLoaded.planningAuthorities.length === 1, "one canonical planning authority expected")
  assert(authorityLoaded.activeScopes.length === 1, "one active scope expected")

  const gateMap = JSON.parse(await gateStart.execute({ objective: "map native gates", targetSha: sha }, context))
  const localGate = JSON.parse(await record_gate.execute({ gateMapId: gateMap.gateMapId, name: "fast verify", gateClass: "REPO_PROVABLE", required: true, command: "./verify.sh fast", evidence: [{ path: "docs/SESSION.md", locator: "line 2: Required gate" }, { path: "verify.sh", locator: "script entry" }] }, context))
  const hostedGate = JSON.parse(await record_gate.execute({ gateMapId: gateMap.gateMapId, name: "hosted CI", gateClass: "HOSTED_CI_PROVABLE", required: true, command: "GitHub Actions ci", evidence: [{ path: ".github/workflows/ci.yml", locator: "workflow definition" }, { path: "docs/SESSION.md", locator: "line 2: Hosted CI is also required" }] }, context))
  await record_gate.execute({ gateMapId: gateMap.gateMapId, name: "live service smoke", gateClass: "LIVE_RUNTIME_REQUIRED", required: true, evidence: [{ path: "docs/SESSION.md", locator: "session acceptance context" }] }, context)
  await record_result.execute({ gateMapId: gateMap.gateMapId, gateId: localGate.gateId, outcome: "PASS", nativeEvidence: "fixture verify command exited 0" }, context)
  let gates = JSON.parse(await gateLoad.execute({ gateMapId: gateMap.gateMapId }, context))
  assert(gates.handoffState === "CLOUD_TESTABILITY_REMAINING", "unexecuted hosted CI must block live handoff")

  const surface = JSON.parse(await deriveSurface.execute({ targetSha: sha, seedPaths: ["src/core/lib.rs"] }, context))
  assert(surface.entries.some((entry: any) => entry.path === "src/core/lib.rs"), "derived change surface must contain active seed")
  assert(surface.entries.some((entry: any) => entry.path === "Cargo.toml"), "derived change surface must include owning workspace manifest")

  const packet = JSON.parse(await save_packet.execute({
    targetSha: sha, authorityMapId: authority.mapId, nativeGateMapId: gateMap.gateMapId, changeSurfaceMapId: surface.surfaceMapId,
    planningAuthority: ["TODO.md"], activeScope: "docs/SESSION.md", objective: "continue current session", prerequisites: [], acceptedPredecessors: [], requiredReading: ["TODO.md", "docs/SESSION.md"],
    allowedPaths: ["src/core/**"], forbiddenOrAdjacentPaths: [{ pattern: "src/graph/**", classification: "ADJACENT_TRACK", rationale: "separate graph track" }],
    repoProvableChecks: ["./verify.sh fast"], hostedCiProvableChecks: ["GitHub Actions ci"], liveRuntimeRequiredChecks: ["live service smoke"], operatorDecisionRequired: [], blockers: [], uncertainties: [], authorityEdgeIds: [planning.edgeId, active.edgeId],
  }, context))
  const loadedPacket = JSON.parse(await packetLoad.execute({ packetId: packet.packetId }, context))
  assert(loadedPacket.scopeAuthority === "CONFIRMED", "packet must require confirmed authority")
  assert(loadedPacket.pathScopeAuthority === "DECLARED", "declared allowed paths must remain explicitly distinguished")
  assert(loadedPacket.changeSurface.surfaceMapId === surface.surfaceMapId, "packet load must resolve exact change-surface projection")
  assert(loadedPacket.changeSurface.entries.some((entry: any) => entry.path === "src/core/lib.rs"), "packet projection must expose derived change surface")
  assert(Array.isArray(loadedPacket.nativeGates) && loadedPacket.nativeGates.length === 3, "packet projection must expose bounded native gates")
  assert(loadedPacket.nativeGates.some((gate: any) => gate.gateId === localGate.gateId), "packet projection must preserve native gate identity")
  assert(Array.isArray(loadedPacket.authorityEvidence) && loadedPacket.authorityEvidence.length === 2, "packet projection must expose selected authority edges")
  assert(loadedPacket.authorityEvidence.every((edge: any) => edge.targetSha === sha && edge.evidence?.length > 0), "authority projection must remain exact-evidence bound")

  const inScope = JSON.parse(await scope_guard.execute({ packetId: packet.packetId, proposedPaths: ["src/core/lib.rs"] }, context))
  assert(inScope.overall === "IN_SCOPE", "declared core path must be in scope")
  const adjacent = JSON.parse(await scope_guard.execute({ packetId: packet.packetId, proposedPaths: ["src/graph/lib.rs"] }, context))
  assert(adjacent.overall === "ADJACENT_TRACK", "adjacent graph path must not be auto-expanded")
  const undeclared = JSON.parse(await scope_guard.execute({ packetId: packet.packetId, proposedPaths: ["README.md"] }, context))
  assert(undeclared.overall === "UNDECLARED", "undeclared path must remain undeclared when an allowlist exists")

  const noPathAuthorityPacket = JSON.parse(await save_packet.execute({
    targetSha: sha, authorityMapId: authority.mapId, nativeGateMapId: gateMap.gateMapId, changeSurfaceMapId: surface.surfaceMapId,
    planningAuthority: ["TODO.md"], activeScope: "docs/SESSION.md", objective: "continue scope whose authority declares no path allowlist", prerequisites: [], acceptedPredecessors: [], requiredReading: ["TODO.md", "docs/SESSION.md"],
    allowedPaths: [], forbiddenOrAdjacentPaths: [{ pattern: "src/graph/**", classification: "ADJACENT_TRACK", rationale: "separate graph track remains explicit even without an allowlist" }],
    repoProvableChecks: ["./verify.sh fast"], hostedCiProvableChecks: ["GitHub Actions ci"], liveRuntimeRequiredChecks: ["live service smoke"], operatorDecisionRequired: ["confirm concrete mutation paths before editing"], blockers: [], uncertainties: ["repository authority does not declare allowed path globs"], authorityEdgeIds: [planning.edgeId, active.edgeId],
  }, context))
  assert(noPathAuthorityPacket.pathScopeAuthority === "NOT_DECLARED", "missing repository path allowlist must remain explicit, never invented")
  const unresolvedPath = JSON.parse(await scope_guard.execute({ packetId: noPathAuthorityPacket.packetId, proposedPaths: ["src/core/lib.rs"] }, context))
  assert(unresolvedPath.overall === "SCOPE_AUTHORITY_UNPROVEN", "a path cannot become IN_SCOPE or merely UNDECLARED when path-level authority was never declared")
  const stillAdjacent = JSON.parse(await scope_guard.execute({ packetId: noPathAuthorityPacket.packetId, proposedPaths: ["src/graph/lib.rs"] }, context))
  assert(stillAdjacent.overall === "ADJACENT_TRACK", "explicit restrictions must still take precedence when positive path authority is absent")

  await record_result.execute({ gateMapId: gateMap.gateMapId, gateId: hostedGate.gateId, outcome: "PASS", nativeEvidence: "hosted workflow exact-head success" }, context)
  gates = JSON.parse(await gateLoad.execute({ gateMapId: gateMap.gateMapId }, context))
  assert(gates.handoffState === "LIVE_HANDOFF_READY", "live-only gate must not keep cloud boundary open after repo+hosted gates PASS")

  await writeFile(path.join(root, "TODO.md"), "dirty\n", "utf8")
  let dirtyRejected = false
  try { await packetLoad.execute({ packetId: packet.packetId }, context) } catch (error) { dirtyRejected = String(error).includes("TRACKED WORKTREE DIRTY") }
  assert(dirtyRejected, "continuation state must fail closed on tracked dirtiness")

  console.log("DEVELOPMENT CONTINUATION STATE SMOKE PASS")
}

await main()
