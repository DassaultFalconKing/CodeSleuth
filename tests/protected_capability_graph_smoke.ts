import path from "node:path"
import {
  mermaid,
  query,
  renderProtectedImpactMermaid,
  selectProtectedImpact,
  type ProtectedRegistry,
} from "../pack/.opencode/tools/protected_capability_graph"

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message)
}

async function expectFailure(operation: () => Promise<unknown>, contains: string) {
  try {
    await operation()
  } catch (error) {
    assert(String(error).includes(contains), `expected failure containing ${contains}, got ${String(error)}`)
    return
  }
  throw new Error(`expected failure containing ${contains}`)
}

async function main() {
  const root = path.join(import.meta.dir, "..")
  const context = { worktree: root, directory: root, sessionID: "protected-graph-smoke", agent: "build" } as any
  const contractId = "codesleuth.durable-review-state"

  const impact = JSON.parse(await query.execute({ contractIds: [contractId] }, context))
  assert(impact.roots[0] === contractId, "query must retain the exact impact root")
  assert(impact.selected.some((item: any) => item.id === "codesleuth.context-graph-evidence-boundary"), "reverse closure must include graph consumer")
  assert(impact.provenance.path === "docs/protected-capabilities.json", "the tracked registry remains the only input authority")
  assert(impact.provenance.indexBlob.length === 40 && impact.provenance.workingBlob.length === 40, "registry provenance carries exact Git blobs")

  const broadRoot = "codesleuth.host-execution-authority"
  const first = JSON.parse(await mermaid.execute({ contractIds: [broadRoot], contractLimit: 3 }, context))
  const second = JSON.parse(await mermaid.execute({ contractIds: [broadRoot], contractLimit: 3 }, context))
  assert(first.schemaVersion === 1 && first.view === "protected_capability_impact", "protected Mermaid must use the shared versioned envelope")
  assert(first.authority.kind === "tracked_protected_capability_registry", "protected Mermaid must declare its separate registry authority")
  assert(first.mermaidSource === second.mermaidSource, "protected impact Mermaid must be deterministic")
  assert(first.derivedPresentationOnly === true, "tool output must disclaim evidence authority")
  assert(first.mermaidSource.includes("not registry or acceptance evidence"), "diagram header must preserve the authority boundary")
  assert(first.selection.truncated === true, "bounded closure must disclose truncation")
  const aliases = new Set<string>()
  for (const line of first.mermaidSource.split("\n")) {
    const node = /^  (c\d+)\["/.exec(line)
    if (node) aliases.add(node[1])
    const edge = /^  (c\d+) -->\|"consumer impact"\| (c\d+)$/.exec(line)
    if (edge) assert(aliases.has(edge[1]) || aliases.has(edge[2]), "edge syntax remains bounded to declared aliases")
  }
  for (const edge of first.selection.edges) {
    assert(first.selection.selected.some((item: any) => item.id === edge.dependency), "returned dependency endpoint must be present")
    assert(first.selection.selected.some((item: any) => item.id === edge.consumer), "returned consumer endpoint must be present")
  }
  await expectFailure(() => query.execute({ contractIds: ["codesleuth.missing"] }, context), "protected contract not found")

  const hostileRegistry: ProtectedRegistry = {
    schema_version: 1,
    registry: "codesleuth-protected-capabilities",
    authority: 'docs/authority%%\n"<script>`',
    contracts: [
      {
        id: 'codesleuth.hostile%%\n"<img>`',
        capability_class: "context-relationship-graph",
        capability_class_id: "CC-GRAPH",
        status: "implemented",
        depends_on: [],
        forbidden_regressions: [{ id: "FR-X", sib_origin: "SIB1", must_not: "remain inert" }],
      },
    ],
  }
  const hostileSelection = selectProtectedImpact(hostileRegistry)
  const hostile = renderProtectedImpactMermaid(hostileRegistry, hostileSelection)
  assert(!hostile.includes("<script>") && !hostile.includes("<img>"), "hostile registry labels cannot emit raw markup")
  for (const line of hostile.split("\n")) {
    if (!line.startsWith("%%")) continue
    assert(!line.slice(2).includes("%") && !line.includes("<") && !line.includes("`"), "hostile metadata cannot forge Mermaid directives")
  }

  console.log("PROTECTED CAPABILITY GRAPH SMOKE PASS")
}

await main()
