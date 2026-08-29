import { mkdtemp, readFile, rm } from "node:fs/promises"
import os from "node:os"
import path from "node:path"

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message)
}

const root = path.resolve(import.meta.dir, "..")
const python = Bun.which("python3") ?? Bun.which("python")
assert(python && path.isAbsolute(python), "canonical Mermaid export smoke requires one resolved absolute Python interpreter")
const temporary = await mkdtemp(path.join(os.tmpdir(), "codesleuth-mermaid-export-"))
try {
  const output = path.join(temporary, "graph.svg")
  const proc = Bun.spawn(
    [python, path.join(root, "pack", ".opencode", "bin", "codesleuth_export.py"), "mermaid-svg", "--output", output],
    { cwd: root, stdin: "pipe", stdout: "pipe", stderr: "pipe" },
  )
  proc.stdin.write("flowchart LR\n  A --> B\n")
  proc.stdin.end()
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  const code = await proc.exited
  assert(code === 0, `retained Mermaid export failed: ${stderr || stdout}`)
  const result = JSON.parse(stdout)
  assert(result.status === "pass" && result.retained === true, "renderer must report retained PASS")
  assert(result.renderer?.package === "@mermaid-js/mermaid-cli", "renderer package identity missing")
  assert(result.renderer?.version === "11.16.0", "renderer must use exact pinned Mermaid CLI")
  assert(path.isAbsolute(result.renderer?.python?.path ?? ""), "renderer must record exact Python identity")
  const svg = await readFile(output, "utf8")
  assert(svg.includes("<svg"), "retained Mermaid export must produce SVG")
  assert(typeof result.sha256 === "string" && result.sha256.length === 64, "retained SVG digest missing")
  console.log("MERMAID EXPORT SMOKE PASS")
} finally {
  await rm(temporary, { recursive: true, force: true })
}
