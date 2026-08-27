import { mkdtemp, rm, writeFile } from "node:fs/promises"
import os from "node:os"
import path from "node:path"
import { mermaid, query, save, topology } from "../pack/.opencode/tools/repo_context_graph"

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message)
}

async function git(root: string, args: string[]) {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stderr = await new Response(proc.stderr).text()
  assert((await proc.exited) === 0, stderr)
}

const root = await mkdtemp(path.join(os.tmpdir(), "codesleuth-topology-"))
try {
  await git(root, ["init", "-q"])
  await git(root, ["config", "user.email", "test@example.invalid"])
  await git(root, ["config", "user.name", "CodeSleuth Test"])
  for (const file of ["a.ts", "b.ts", "c.ts", "d.ts"]) await writeFile(path.join(root, file), `export const ${file[0]} = 1\n`)
  await git(root, ["add", "a.ts", "b.ts", "c.ts", "d.ts"])
  await git(root, ["commit", "-qm", "fixture"])
  const context = { worktree: root, sessionID: "topology-smoke", directory: root }
  const nodes = ["a.ts", "b.ts", "c.ts", "d.ts"].map((file) => ({
    kind: "file" as const,
    key: file,
    label: file,
    origin: "verified_source" as const,
    path: file,
  }))
  const edges = [
    ["a.ts", "b.ts", "a.ts"],
    ["b.ts", "c.ts", "b.ts"],
    ["c.ts", "d.ts", "c.ts"],
  ].map(([sourceKey, targetKey, evidence]) => ({
    relation: "calls" as const,
    origin: "verified_source" as const,
    sourceKind: "file" as const,
    sourceKey,
    targetKind: "file" as const,
    targetKey,
    path: evidence,
  }))
  const saved = JSON.parse(await save.execute({ nodes, edges, complete: true }, context))
  const hints = [
    { kind: "file" as const, key: "a.ts", community: "left", centrality: 0.2 },
    { kind: "file" as const, key: "b.ts", community: "left", centrality: 0.9 },
    { kind: "file" as const, key: "c.ts", community: "right", centrality: 0.8 },
    { kind: "file" as const, key: "d.ts", community: "right", centrality: 0.1 },
    { kind: "file" as const, key: "stale.ts", community: "ghost", centrality: 1.0 },
  ]
  const common = {
    projectionId: saved.projectionId,
    provider: "graphify" as const,
    providerVersion: "0.9.50",
    upstreamCommit: "43d54acbfa9e731f7a592bb582c1f4b9d48ed73e",
    hints,
    rootLimit: 2,
  }
  const hubsOnce = JSON.parse(await topology.execute({ ...common, strategy: "community_hubs" }, context))
  const hubsTwice = JSON.parse(await topology.execute({ ...common, strategy: "community_hubs" }, context))
  assert(JSON.stringify(hubsOnce) === JSON.stringify(hubsTwice), "topology root selection must be deterministic")
  assert(hubsOnce.derivedSelectionHintsOnly === true, "topology cannot become identity or evidence")
  assert(hubsOnce.selection.staleHints === 1 && hubsOnce.selection.returnedRoots === 2, "stale and bounded totals must be explicit")
  assert(hubsOnce.roots[0].key === "b.ts" && hubsOnce.roots[1].key === "c.ts", "community hubs must rank deterministically")

  const cross = JSON.parse(await topology.execute({ ...common, strategy: "cross_community" }, context))
  assert(cross.roots.some((item: any) => item.key === "b.ts") && cross.roots.some((item: any) => item.key === "c.ts"), "cross-community strategy must select validated bridge endpoints")
  const scopedQuery = JSON.parse(await query.execute({ projectionId: saved.projectionId, roots: cross.roots, hops: 1 }, context))
  const scopedMermaid = JSON.parse(await mermaid.execute({ projectionId: saved.projectionId, roots: cross.roots, hops: 1 }, context))
  assert(scopedQuery.totalsForSelection.nodes === scopedMermaid.selection.totals.nodes, "topology roots must retain shared query/Mermaid traversal")
  const declaredAliases = new Set(
    scopedMermaid.mermaidSource
      .split("\n")
      .map((line: string) => /^\s+(n\d+)\[/.exec(line)?.[1])
      .filter(Boolean),
  )
  for (const line of scopedMermaid.mermaidSource.split("\n")) {
    if (!line.includes("-->")) continue
    const aliases = [...line.matchAll(/\bn\d+\b/g)].map((match) => match[0])
    assert(aliases.every((alias) => declaredAliases.has(alias)), "topology-assisted Mermaid edges cannot reference omitted nodes")
  }

  const noCross = JSON.parse(
    await topology.execute(
      { ...common, strategy: "cross_community", hints: hints.map((hint) => ({ ...hint, community: "one" })) },
      context,
    ),
  )
  assert(noCross.selection.fallbackReason?.includes("used community_hubs"), "missing cross-community topology must report deterministic fallback")
  console.log("CONTEXT GRAPH TOPOLOGY SMOKE PASS")
} finally {
  await rm(root, { recursive: true, force: true })
}
