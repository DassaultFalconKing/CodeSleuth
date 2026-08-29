import { mkdtemp, readFile, rm, symlink, writeFile } from "node:fs/promises"
import os from "node:os"
import path from "node:path"

import { graphExportDirectory, writeGraphExportBundle } from "../pack/.opencode/tools/export_bundle"

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message)
}

async function expectFailure(operation: () => Promise<unknown>, contains: string): Promise<void> {
  try {
    await operation()
  } catch (error) {
    assert(String(error).includes(contains), `expected failure containing ${contains}, got ${String(error)}`)
    return
  }
  throw new Error(`expected failure containing ${contains}`)
}

const root = await mkdtemp(path.join(os.tmpdir(), "codesleuth-export-bundle-"))
try {
  let escaped = false
  try {
    graphExportDirectory(root, "../escape")
  } catch {
    escaped = true
  }
  assert(escaped, "unsafe export bundle names must fail closed")

  const result = await writeGraphExportBundle({
    root,
    bundleName: "repo-smoke",
    view: "repository_context",
    machinePayload: {
      kind: "codesleuth-context-capsule",
      target: { currentHeadSha: "a".repeat(40), exactHeadMatch: true },
    },
    machinePayloadRole: "bounded_exact_head_context_capsule",
    exportedAt: "2026-08-29T00:00:00.000Z",
    mermaidEnvelope: {
      schemaVersion: 1,
      view: "repository_context",
      authority: { kind: "tracked_git_source" },
      provenance: { headSha: "a".repeat(40), projectionId: "sha256:" + "b".repeat(64) },
      selection: { totals: { nodes: 2, edges: 1 } },
      truncated: false,
      derivedPresentationOnly: true,
      mermaidSource: "flowchart LR\n  A --> B\n",
    },
    renderSvg: async (_source, outputPath) => {
      await writeFile(outputPath, '<svg xmlns="http://www.w3.org/2000/svg"><text>smoke</text></svg>', "utf8")
      return { renderer: { package: "smoke-renderer", version: "1" } }
    },
  })

  assert(result.exportAuthority === "none", "export must never claim authority")
  assert(result.retainedArtifactOnly === true, "export must declare retained artifact semantics")
  assert(result.outputDirectory === ".codesleuth/exports/graphs/repo-smoke", "export path must stay ignored")
  const dir = path.join(root, result.outputDirectory)
  const manifest = JSON.parse(await readFile(path.join(dir, "manifest.json"), "utf8"))
  assert(manifest.derivedPresentationOnly === true, "manifest must preserve derived-presentation role")
  assert(manifest.artifacts.graphJson.sha256.length === 64, "graph JSON digest must be recorded")
  assert(manifest.artifacts.mermaid.sha256.length === 64, "Mermaid digest must be recorded")
  assert(manifest.artifacts.svg.sha256.length === 64, "SVG digest must be recorded")
  assert((await readFile(path.join(dir, "graph.mmd"), "utf8")).startsWith("flowchart LR"), "Mermaid source missing")
  assert((await readFile(path.join(dir, "graph.svg"), "utf8")).includes("<svg"), "SVG missing")

  await expectFailure(
    () =>
      writeGraphExportBundle({
        root,
        bundleName: "repo-smoke",
        view: "repository_context",
        machinePayload: {},
        machinePayloadRole: "smoke",
        mermaidEnvelope: {
          schemaVersion: 1,
          view: "repository_context",
          authority: {},
          derivedPresentationOnly: true,
          mermaidSource: "flowchart LR\n  X --> Y\n",
        },
      }),
    "export bundle already exists",
  )

  const symlinkRoot = await mkdtemp(path.join(os.tmpdir(), "codesleuth-export-symlink-"))
  const outside = await mkdtemp(path.join(os.tmpdir(), "codesleuth-export-outside-"))
  try {
    await symlink(outside, path.join(symlinkRoot, ".codesleuth"), "dir")
    await expectFailure(
      () =>
        writeGraphExportBundle({
          root: symlinkRoot,
          bundleName: "escape-attempt",
          view: "repository_context",
          machinePayload: {},
          machinePayloadRole: "smoke",
          mermaidEnvelope: {
            schemaVersion: 1,
            view: "repository_context",
            authority: {},
            derivedPresentationOnly: true,
            mermaidSource: "flowchart LR\n  X --> Y\n",
          },
        }),
      "real directory",
    )
  } finally {
    await rm(symlinkRoot, { recursive: true, force: true })
    await rm(outside, { recursive: true, force: true })
  }

  console.log("EXPORT BUNDLE SMOKE PASS")
} finally {
  await rm(root, { recursive: true, force: true })
}
