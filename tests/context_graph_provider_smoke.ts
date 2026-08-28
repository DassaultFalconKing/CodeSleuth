import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises"
import os from "node:os"
import path from "node:path"
import { extract, status } from "../pack/.opencode/tools/repo_context_provider"
import { save } from "../pack/.opencode/tools/repo_context_graph"

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message)
}

async function git(root: string, args: string[]) {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  assert((await proc.exited) === 0, stderr)
  return stdout.trim()
}

const root = await mkdtemp(path.join(os.tmpdir(), "codesleuth-graphify-provider-"))
try {
  await git(root, ["init", "-q"])
  await git(root, ["config", "user.email", "test@example.invalid"])
  await git(root, ["config", "user.name", "CodeSleuth Test"])
  await writeFile(path.join(root, "app.py"), "def run():\n    return 1\n", "utf8")
  await writeFile(path.join(root, "main.py"), "from app import run\nrun()\n", "utf8")
  await git(root, ["add", "app.py", "main.py"])
  await git(root, ["commit", "-qm", "fixture"])
  const sourceRoot = path.resolve(import.meta.dir, "..")
  const context = { worktree: sourceRoot, sessionID: "provider-smoke", directory: sourceRoot }
  const builtinStatus = JSON.parse(await status.execute({}, context))
  assert(builtinStatus.provider === "builtin" && builtinStatus.defaultProvider === true, "builtin must remain the default provider")
  const builtin = JSON.parse(await extract.execute({ provider: "builtin" }, context))
  assert(builtin.status === "delegate_to_existing_repository_map", "builtin extraction must retain the existing map flow")
  const graphifyStatus = JSON.parse(await status.execute({ provider: "graphify" }, context))
  if (graphifyStatus.status === "unavailable") {
    let failedClosed = false
    try {
      await extract.execute({ provider: "graphify", files: ["scripts/graphify_adapter.py"] }, context)
    } catch (error) {
      failedClosed = String(error).includes("runtime identity manifest") || String(error).includes("runtime interpreter")
    }
    assert(failedClosed, "an unavailable optional runtime must fail closed without ambient interpreter fallback")
  } else {
    assert(graphifyStatus.compatible === true, "tool must expose exact optional-provider status")
    const runtime = path.join(sourceRoot, ".runtime", "graphify-provider")
    const manifestPath = path.join(runtime, "codesleuth-runtime.json")
    const manifestText = await readFile(manifestPath, "utf8")
    const manifest = JSON.parse(manifestText)
    assert(path.isAbsolute(manifest.pythonExecutable), "runtime manifest must bind an absolute interpreter")
    try {
      await writeFile(manifestPath, JSON.stringify({ ...manifest, pythonExecutable: "python" }), "utf8")
      const tamperedStatus = JSON.parse(await status.execute({ provider: "graphify" }, context))
      assert(tamperedStatus.status === "unavailable", "a tampered interpreter identity must fail closed")
    } finally {
      await writeFile(manifestPath, manifestText, "utf8")
    }
    const request = JSON.stringify({ root, files: ["app.py", "main.py"], nodeLimit: 20, edgeLimit: 20 })
    const proc = Bun.spawn([manifest.pythonExecutable, "scripts/graphify_adapter.py", "--runtime", runtime], {
      cwd: sourceRoot,
      stdin: "pipe",
      stdout: "pipe",
      stderr: "pipe",
    })
    proc.stdin.write(request)
    proc.stdin.end()
    const stdout = await new Response(proc.stdout).text()
    const stderr = await new Response(proc.stderr).text()
    assert((await proc.exited) === 0, `Graphify adapter failed: ${stderr || stdout}`)
    const result = JSON.parse(stdout)
    assert(result.status === "ok" && result.provider.version === "0.9.50", "exact provider must execute")
    assert(
      path.resolve(result.execution.pythonExecutable) === path.resolve(manifest.pythonExecutable) &&
        result.execution.pythonVersion === manifest.pythonVersion,
      "adapter must attest the exact installed interpreter identity",
    )
    assert(result.authority.kind === "candidate_structural_provider", "provider cannot become evidence authority")
    assert(result.input.files.every((file: any) => file.exactIndexMatch), "tracked fixture inputs must retain exact blob identity")
    assert(result.selection.returned.nodes > 0, "provider must return bounded structural candidates")
    assert(result.providerDiagnostics.stdout.length < 4001, "provider diagnostics must remain bounded")
    const viaTool = JSON.parse(
      await extract.execute(
        { provider: "graphify", files: ["scripts/graphify_adapter.py", "scripts/mermaid_qa.py"], nodeLimit: 50, edgeLimit: 50 },
        context,
      ),
    )
    assert(viaTool.status === "ok" && viaTool.provider.id === "graphify", "explicit graphify selection must use the isolated adapter")
    assert(viaTool.nodes.every((node: any) => node.projectionInput), "provider candidates must be ready for consolidated save validation")
    assert(
      viaTool.edges.every((edge: any) => edge.projectionInput.origin === "verified_source" || edge.projectionInput.relation === "review_inference"),
      "non-exact provider edges must use the existing review_inference save contract",
    )
    const validated = JSON.parse(
      await save.execute(
        {
          validate_only: true,
          nodes: viaTool.nodes.map((node: any) => node.projectionInput),
          edges: viaTool.edges.map((edge: any) => edge.projectionInput),
        },
        context,
      ),
    )
    assert(validated.valid === true, "provider projectionInput must pass consolidated context-graph validation")
  }
  console.log("CONTEXT GRAPH PROVIDER SMOKE PASS")
} finally {
  await rm(root, { recursive: true, force: true })
}
