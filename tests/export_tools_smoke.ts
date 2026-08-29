import { readFile, rm } from "node:fs/promises"
import path from "node:path"

import { protected_graph } from "../pack/.opencode/tools/codesleuth_export"

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message)
}

const root = path.resolve(import.meta.dir, "..")
const python = Bun.which("python3") ?? Bun.which("python")
assert(python && path.isAbsolute(python), "export tool smoke needs one explicit Python interpreter")
process.env.CODESLEUTH_PYTHON_EXECUTABLE = python
const bundleName = "ci-protected-export-tool"
const output = path.join(root, ".codesleuth", "exports", "graphs", bundleName)
await rm(output, { recursive: true, force: true })
try {
  const context = {
    worktree: root,
    directory: root,
    sessionID: "export-tool-smoke",
    messageID: "export-tool-message",
    agent: "build",
  } as any
  const result = JSON.parse(
    await protected_graph.execute(
      {
        contractIds: ["codesleuth.durable-review-state"],
        contractLimit: 6,
        bundleName,
        includeSvg: true,
      },
      context,
    ),
  )
  assert(result.kind === "codesleuth-graph-export", "production export tool must return graph export manifest")
  assert(result.exportAuthority === "none", "production export tool must remain non-authoritative")
  assert(result.view === "protected_capability_impact", "production export tool returned wrong view")
  assert(result.renderer?.package === "@mermaid-js/mermaid-cli", "production SVG path must report renderer identity")
  assert(path.isAbsolute(result.renderer?.python?.path ?? ""), "production SVG path must report Python identity")
  const manifest = JSON.parse(await readFile(path.join(output, "manifest.json"), "utf8"))
  assert(manifest.provenance?.contentSha256?.length === 64, "production export must retain authority provenance")
  assert((await readFile(path.join(output, "graph.mmd"), "utf8")).includes("flowchart"), "production export Mermaid missing")
  assert((await readFile(path.join(output, "graph.svg"), "utf8")).includes("<svg"), "production export SVG missing")
  console.log("EXPORT TOOLS SMOKE PASS")
} finally {
  await rm(output, { recursive: true, force: true })
}
