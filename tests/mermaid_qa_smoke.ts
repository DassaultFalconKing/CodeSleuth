import path from "node:path"
import { renderContextGraphMermaid } from "../pack/.opencode/tools/repo_context_graph"
import { renderEhaMermaid } from "../pack/.opencode/tools/eha_state"
import {
  renderProtectedImpactMermaid,
  selectProtectedImpact,
  type ProtectedRegistry,
} from "../pack/.opencode/tools/protected_capability_graph"

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message)
}

async function qa(source: string) {
  const proc = Bun.spawn(["python", "scripts/mermaid_qa.py"], {
    cwd: path.resolve(import.meta.dir, ".."),
    stdin: "pipe",
    stdout: "pipe",
    stderr: "pipe",
  })
  proc.stdin.write(source)
  proc.stdin.end()
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  const code = await proc.exited
  assert(code === 0, `Mermaid QA failed: ${stderr || stdout}`)
  const result = JSON.parse(stdout)
  assert(result.status === "pass" && result.passed === true, "Mermaid QA must report an actual parser/render PASS")
  assert(result.renderedArtifact?.retained === false, "QA SVG must remain disposable")
  return result
}

const projection: any = {
  schemaVersion: 1,
  projectionId: "ctx-test",
  headSha: "a".repeat(40),
  createdAt: "2026-01-01T00:00:00Z",
  scope: { prefix: "src", description: "hostile %%\n<img>" },
  bounds: { nodeLimit: 10, edgeLimit: 10, truncated: false },
  nodes: [
    { nodeId: "n-a", kind: "file", key: "src/a.ts", label: 'A <img> "', origin: "verified_source" },
    { nodeId: "n-b", kind: "symbol", key: "b@src/a.ts", label: "B `tick`", origin: "review_inference" },
  ],
  edges: [
    { edgeId: "e-a", sourceNodeId: "n-a", targetNodeId: "n-b", relation: "defines", origin: "review_inference" },
  ],
}

const registry: ProtectedRegistry = {
  schema_version: 1,
  registry: "codesleuth-protected-capabilities",
  authority: "tracked registry <script>",
  contracts: [
    {
      id: "contract-a",
      capability_class: "graph",
      capability_class_id: "CC-GRAPH",
      status: "protected",
      depends_on: [],
      forbidden_regressions: [{ id: "FR-1", sib_origin: "SIB2", must_not: "regress" }],
    },
  ],
}

const eha: any[] = [
  {
    type: "campaign_started",
    eventId: "event-a",
    campaignId: "EHA-A",
    targetSha: "b".repeat(40),
    scope: "scope",
    recordedAt: "2026-01-01T00:00:00Z",
    recordedHeadSha: "b".repeat(40),
  },
]

const context = renderContextGraphMermaid(projection).mermaid
const protectedSource = renderProtectedImpactMermaid(registry, selectProtectedImpact(registry))
const ehaSource = renderEhaMermaid(eha)
const results = await Promise.all([qa(context), qa(protectedSource), qa(ehaSource)])
assert(new Set(results.map((result) => result.sourceSha256)).size === 3, "all three distinct Mermaid surfaces must be parser/render checked")
console.log("MERMAID QA SMOKE PASS")
