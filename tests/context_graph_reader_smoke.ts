import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"

import {
  describe,
  diff,
  explain,
  neighbors,
  read_source_ref,
  resolve,
  shortest_paths,
  status,
} from "../pack/.opencode/tools/context_graph_read"
import { contextNodeId, save } from "../pack/.opencode/tools/repo_context_graph"

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message)
}

async function expectFailure(action: () => Promise<unknown>, contains: string): Promise<string> {
  try {
    await action()
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    assert(message.includes(contains), `expected failure containing ${contains}, got: ${message}`)
    return message
  }
  throw new Error(`expected failure containing ${contains}`)
}

async function git(root: string, args: string[]): Promise<string> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  const code = await proc.exited
  if (code !== 0) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`)
  return stdout.trim()
}

async function buildReader(): Promise<string> {
  const crateDir = path.resolve(import.meta.dir, "..", "portable", "ebca-graph-readside")
  const proc = Bun.spawn(["cargo", "build", "--locked"], {
    cwd: crateDir,
    stdout: "pipe",
    stderr: "pipe",
  })
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  const code = await proc.exited
  assert(code === 0, `cargo build failed: ${stderr || stdout}`)
  const name = process.platform === "win32" ? "ebca-graph-readside.exe" : "ebca-graph-readside"
  return path.resolve(crateDir, "target", "debug", name)
}

async function main(): Promise<void> {
  const previous = process.env.CODESLEUTH_GRAPH_READER_BIN
  delete process.env.CODESLEUTH_GRAPH_READER_BIN

  const unavailable = JSON.parse(await status.execute({}, {} as any))
  assert(unavailable.available === false, "missing binary must be explicit")
  assert(String(unavailable.reason).includes("CODESLEUTH_GRAPH_READER_BIN"), "absence reason must name the env contract")

  process.env.CODESLEUTH_GRAPH_READER_BIN = "ebca-graph-readside"
  const relative = JSON.parse(await status.execute({}, {} as any))
  assert(relative.available === false, "PATH lookup must fail closed")
  assert(String(relative.reason).includes("absolute"), "relative binary path must be rejected")

  const binary = await buildReader()
  const root = await mkdtemp(path.join(tmpdir(), "context-graph-reader-"))
  const context: any = {
    worktree: root,
    directory: root,
    sessionID: "context-graph-reader-smoke",
    messageID: "message-1",
    agent: "build",
  }

  try {
    await git(root, ["init"])
    await git(root, ["config", "user.email", "context-graph-reader-ci@example.invalid"])
    await git(root, ["config", "user.name", "Context Graph Reader CI"])
    await mkdir(path.join(root, "src"), { recursive: true })
    await writeFile(path.join(root, "src", "util.ts"), "export function helper() {\n  return 1\n}\n", "utf8")
    await writeFile(
      path.join(root, "src", "app.ts"),
      'import { helper } from "./util"\nexport function main() {\n  return helper()\n}\n',
      "utf8",
    )
    await writeFile(path.join(root, "README.md"), "# fixture\n", "utf8")
    await git(root, ["add", "."])
    await git(root, ["commit", "-m", "fixture"])
    const head = await git(root, ["rev-parse", "HEAD"])

    const saved = JSON.parse(
      await save.execute(
        {
          complete: true,
          scopePrefix: "src",
          scopeDescription: "portable graph reader smoke",
          nodes: [
            {
              kind: "file",
              key: "src/util.ts",
              label: "utility helpers",
              origin: "verified_source",
              path: "src/util.ts",
              startLine: 1,
              endLine: 3,
            },
            {
              kind: "file",
              key: "src/app.ts",
              origin: "verified_source",
              path: "src/app.ts",
              startLine: 1,
              endLine: 4,
            },
            {
              kind: "symbol",
              key: "helper@src/util.ts",
              origin: "verified_source",
              path: "src/util.ts",
              startLine: 1,
              endLine: 3,
            },
          ],
          edges: [
            {
              relation: "imports",
              origin: "verified_source",
              sourceKind: "file",
              sourceKey: "src/app.ts",
              targetKind: "file",
              targetKey: "src/util.ts",
              path: "src/app.ts",
              startLine: 1,
              endLine: 1,
            },
            {
              relation: "calls",
              origin: "verified_source",
              sourceKind: "file",
              sourceKey: "src/app.ts",
              targetKind: "symbol",
              targetKey: "helper@src/util.ts",
              path: "src/app.ts",
              startLine: 2,
              endLine: 3,
            },
          ],
        },
        context,
      ),
    )

    await expectFailure(
      () => describe.execute({ expectedHeadSha: head, projectionId: saved.projectionId }, context),
      "portable graph reader unavailable",
    )

    process.env.CODESLEUTH_GRAPH_READER_BIN = binary
    const ready = JSON.parse(await status.execute({}, context))
    assert(ready.available === true, "explicit absolute binary must be available")
    assert(ready.binaryPath === binary, "status must echo the exact configured binary")

    const appId = contextNodeId("file", "src/app.ts")
    const utilId = contextNodeId("file", "src/util.ts")
    const described = JSON.parse(
      await describe.execute({ expectedHeadSha: head, projectionId: saved.projectionId }, context),
    )
    assert(described.kind === "codesleuth-context-graph-read", "adapter envelope kind missing")
    assert(described.policy.projectionRole === "derived navigation/context", "graph must remain derived")
    assert(described.policy.reopenSourceBeforeEditOrFinding === true, "source reopening policy missing")
    assert(described.target.exactHeadMatch === true, "current describe must be exact-head")
    assert(described.result.graphId === saved.projectionId, "describe must use projection identity as graph id")
    assert(described.result.nodeCount === 3, "describe node count")
    assert(described.result.edgeCount === 2, "describe edge count")
    assert(described.result.nodeKinds.file === 2, "describe must stay generic over kinds")

    const resolved = JSON.parse(
      await resolve.execute(
        { expectedHeadSha: head, projectionId: saved.projectionId, query: "src/app.ts", limit: 10 },
        context,
      ),
    )
    assert(resolved.result.matches[0].node.id === appId, "resolve should find exact key")
    const opaquePartial = JSON.parse(
      await resolve.execute(
        { expectedHeadSha: head, projectionId: saved.projectionId, query: appId.slice(-12), limit: 10 },
        context,
      ),
    )
    assert(opaquePartial.result.matches.length === 0, "opaque IDs must not participate in fuzzy matching")

    const neighborhood = JSON.parse(
      await neighbors.execute(
        {
          expectedHeadSha: head,
          projectionId: saved.projectionId,
          roots: [appId],
          hops: 1,
          nodeLimit: 10,
          edgeLimit: 10,
        },
        context,
      ),
    )
    const returnedIds = new Set(neighborhood.result.nodes.map((node: any) => node.id))
    assert(returnedIds.has(appId) && returnedIds.has(utilId), "neighbors should include the import window")
    for (const edge of neighborhood.result.edges) {
      assert(returnedIds.has(edge.source) && returnedIds.has(edge.target), "no dangling returned edges")
    }

    const paths = JSON.parse(
      await shortest_paths.execute(
        {
          expectedHeadSha: head,
          projectionId: saved.projectionId,
          source: appId,
          target: utilId,
          maxHops: 2,
          maxPaths: 3,
        },
        context,
      ),
    )
    assert(paths.result.paths.length === 1, "bounded shortest path should exist")

    const explained = JSON.parse(
      await explain.execute(
        {
          expectedHeadSha: head,
          projectionId: saved.projectionId,
          elementId: neighborhood.result.edges[0].id,
        },
        context,
      ),
    )
    assert(explained.result.elementType === "edge", "explain should return the edge")
    assert(explained.result.source.id && explained.result.target.id, "edge explanation must expose endpoints")

    const sourceRef = neighborhood.result.nodes.find((node: any) => node.id === appId)?.sourceRef
    assert(sourceRef?.path === "src/app.ts" && sourceRef.blobHash, "structured SourceRef required for reopening")
    const reopened = JSON.parse(
      await read_source_ref.execute(
        { path: sourceRef.path, blobHash: sourceRef.blobHash, startLine: 1, endLine: 2 },
        context,
      ),
    )
    assert(reopened.kind === "codesleuth-source-ref-read", "source reopening kind")
    assert(reopened.lines.length === 2, "bounded source range")
    assert(reopened.policy.graphRelationIsNotFindingEvidence === true, "graph relation is not evidence")

    const sameDiff = JSON.parse(
      await diff.execute(
        {
          expectedHeadSha: head,
          beforeProjectionId: saved.projectionId,
          afterProjectionId: saved.projectionId,
        },
        context,
      ),
    )
    assert(sameDiff.target.historical === true, "diff remains historical/derived")
    assert(sameDiff.result.totals.addedNodes === 0, "identical projections have empty diff")

    await writeFile(path.join(root, "src", "app.ts"), "export const changed = true\n", "utf8")
    await expectFailure(
      () => describe.execute({ expectedHeadSha: head, projectionId: saved.projectionId }, context),
      "stale SourceRef",
    )
    await expectFailure(
      () =>
        read_source_ref.execute(
          { path: sourceRef.path, blobHash: sourceRef.blobHash, startLine: 1, endLine: 1 },
          context,
        ),
      "stale",
    )
    await git(root, ["checkout", "--", "src/app.ts"])

    await writeFile(path.join(root, "README.md"), "# fixture\n\nnew head\n", "utf8")
    await git(root, ["add", "README.md"])
    await git(root, ["commit", "-m", "move head"])
    const movedHead = await git(root, ["rev-parse", "HEAD"])
    await expectFailure(
      () => describe.execute({ expectedHeadSha: movedHead, projectionId: saved.projectionId }, context),
      "does not match current HEAD",
    )

    console.log("context graph reader smoke: PASS")
  } finally {
    if (previous === undefined) delete process.env.CODESLEUTH_GRAPH_READER_BIN
    else process.env.CODESLEUTH_GRAPH_READER_BIN = previous
    await rm(root, { recursive: true, force: true })
  }
}

await main()
