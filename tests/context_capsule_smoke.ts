import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"

import { get } from "../pack/.opencode/tools/codesleuth_context"
import { save } from "../pack/.opencode/tools/repo_context_graph"

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message)
}

async function expectFailure(action: () => Promise<unknown>, contains: string): Promise<void> {
  try {
    await action()
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    assert(message.includes(contains), `expected failure containing ${contains}, got: ${message}`)
    return
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

async function main(): Promise<void> {
  const root = await mkdtemp(path.join(tmpdir(), "context-capsule-"))
  const context: any = {
    worktree: root,
    directory: root,
    sessionID: "context-capsule-smoke",
    messageID: "message-1",
    agent: "build",
  }

  try {
    await git(root, ["init"])
    await git(root, ["config", "user.email", "context-capsule-ci@example.invalid"])
    await git(root, ["config", "user.name", "Context Capsule CI"])
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
          scopeDescription: "context capsule smoke",
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
          ],
        },
        context,
      ),
    )

    const capsule = JSON.parse(
      await get.execute(
        {
          expectedHeadSha: head,
          projectionId: saved.projectionId,
          roots: [{ kind: "file", key: "src/app.ts" }],
          hops: 1,
          nodeLimit: 20,
          edgeLimit: 20,
        },
        context,
      ),
    )
    assert(capsule.capsuleVersion === 1, "capsule version missing")
    assert(capsule.kind === "codesleuth-context-capsule", "capsule kind missing")
    assert(capsule.target.currentHeadSha === head, "capsule target must be exact current HEAD")
    assert(capsule.target.projectionHeadSha === head, "projection head must match current HEAD")
    assert(capsule.target.exactHeadMatch === true, "exact-head proof missing")
    assert(capsule.freshness.staleLinkageCount === 0, "fresh capsule must have no stale linkage")
    assert(capsule.adjacency.nodes.length === 2, "root neighborhood should contain two file nodes")
    assert(capsule.adjacency.edges.length === 1, "root neighborhood should contain import edge")
    assert(capsule.adjacency.nodes.every((node: any) => node.sourceRef?.blobHash), "SourceRefs must be structured")
    assert(capsule.mermaid === undefined, "Mermaid must be opt-in")
    assert(capsule.policy.mermaidRole === "secondary derived presentation", "Mermaid role must stay secondary")

    const withMermaid = JSON.parse(
      await get.execute(
        {
          expectedHeadSha: head,
          projectionId: saved.projectionId,
          roots: [{ kind: "file", key: "src/app.ts" }],
          hops: 1,
          includeMermaid: true,
        },
        context,
      ),
    )
    assert(withMermaid.mermaid.role === "secondary-derived-presentation", "Mermaid role missing")
    assert(withMermaid.mermaid.mermaidSource.includes("flowchart"), "Mermaid source missing")

    const firstPage = JSON.parse(
      await get.execute(
        { expectedHeadSha: head, projectionId: saved.projectionId, nodeLimit: 1, edgeLimit: 1 },
        context,
      ),
    )
    assert(firstPage.coverage.nextCursor, "bounded first page should expose continuation")
    await expectFailure(
      () =>
        get.execute(
          {
            expectedHeadSha: head,
            projectionId: saved.projectionId,
            nodeLimit: 1,
            edgeLimit: 1,
            cursor: firstPage.coverage.nextCursor,
            includeMermaid: true,
          },
          context,
        ),
      "Mermaid has no cursor window contract",
    )

    await expectFailure(
      () => get.execute({ expectedHeadSha: "0".repeat(40), projectionId: saved.projectionId }, context),
      "target drift",
    )

    await writeFile(path.join(root, "src", "app.ts"), "export const changed = true\n", "utf8")
    await expectFailure(
      () => get.execute({ expectedHeadSha: head, projectionId: saved.projectionId }, context),
      "stale SourceRef",
    )
    await git(root, ["checkout", "--", "src/app.ts"])

    await writeFile(path.join(root, "README.md"), "# fixture\n\nnew head\n", "utf8")
    await git(root, ["add", "README.md"])
    await git(root, ["commit", "-m", "move head"])
    const movedHead = await git(root, ["rev-parse", "HEAD"])
    await expectFailure(
      () => get.execute({ expectedHeadSha: movedHead, projectionId: saved.projectionId }, context),
      "does not match current HEAD",
    )

    console.log("context capsule smoke: PASS")
  } finally {
    await rm(root, { recursive: true, force: true })
  }
}

await main()
