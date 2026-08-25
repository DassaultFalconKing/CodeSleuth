import { mkdir, mkdtemp, readdir, readFile, rm, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"
import {
  CONTEXT_GRAPH_SCHEMA_VERSION,
  contextEdgeId,
  contextNodeId,
  load,
  mermaid,
  query,
  renderContextGraphMermaid,
  save,
} from "../pack/.opencode/tools/repo_context_graph"
import { checkpoint, record_finding, start } from "../pack/.opencode/tools/review_state"

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message)
}

async function expectFailure(action: () => Promise<unknown>, message: string): Promise<void> {
  let failed = false
  try {
    await action()
  } catch {
    failed = true
  }
  assert(failed, message)
}

async function captureFailure(action: () => Promise<unknown>): Promise<string> {
  try {
    await action()
  } catch (error) {
    return error instanceof Error ? error.message : String(error)
  }
  throw new Error("expected action to fail")
}

async function listedGraphState(root: string): Promise<string[]> {
  const dir = path.join(root, ".opencode", "state", "context-graphs")
  try {
    return (await readdir(dir, { recursive: true })).filter((name) => String(name).length > 0)
  } catch (error) {
    if (error && typeof error === "object" && "code" in error && error.code === "ENOENT") return []
    throw error
  }
}

async function git(root: string, args: string[]): Promise<string> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  const code = await proc.exited
  if (code !== 0) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`)
  return stdout
}

type Fixture = {
  root: string
  context: any
  cleanup: () => Promise<void>
}

async function makeFixture(name: string, sessionId: string): Promise<Fixture> {
  const root = await mkdtemp(path.join(tmpdir(), `context-graph-${name}-`))
  await git(root, ["init"])
  await git(root, ["config", "user.email", "context-graph-ci@example.invalid"])
  await git(root, ["config", "user.name", "Context Graph CI"])
  await mkdir(path.join(root, "src"), { recursive: true })
  await writeFile(path.join(root, "src", "util.ts"), "export function helper() {\n  return 1\n}\n", "utf8")
  await writeFile(path.join(root, "src", "app.ts"), 'import { helper } from "./util"\nexport function main() {\n  return helper()\n}\n', "utf8")
  await writeFile(path.join(root, "README.md"), "# fixture\n", "utf8")
  await git(root, ["add", "."])
  await git(root, ["commit", "-m", "fixture"])
  return {
    root,
    context: { worktree: root, directory: root, sessionID: sessionId, messageID: "message-1", agent: "repo-reviewer" },
    cleanup: () => rm(root, { recursive: true, force: true }),
  }
}

function baseNodes() {
  return [
    {
      kind: "file" as const,
      key: "src/util.ts",
      origin: "verified_source" as const,
      path: "src/util.ts",
      label: "utility helpers",
    },
    {
      kind: "file" as const,
      key: "src/app.ts",
      origin: "verified_source" as const,
      path: "src/app.ts",
    },
    {
      kind: "symbol" as const,
      key: "helper@src/util.ts",
      origin: "verified_source" as const,
      path: "src/util.ts",
      startLine: 1,
      endLine: 3,
    },
  ]
}

function baseEdges() {
  return [
    {
      relation: "imports" as const,
      origin: "verified_source" as const,
      sourceKind: "file" as const,
      sourceKey: "src/app.ts",
      targetKind: "file" as const,
      targetKey: "src/util.ts",
      path: "src/app.ts",
      startLine: 1,
      endLine: 1,
    },
    {
      relation: "review_inference" as const,
      origin: "review_inference" as const,
      sourceKind: "symbol" as const,
      sourceKey: "helper@src/util.ts",
      targetKind: "file" as const,
      targetKey: "src/app.ts",
      note: "scout claims helper exists to serve app entrypoint",
    },
  ]
}

async function main() {
  // --- deterministic identity -------------------------------------------------
  assert(
    contextNodeId("file", "src/app.ts") === contextNodeId("file", "src/app.ts"),
    "node identity must be deterministic",
  )
  assert(contextNodeId("file", "src/app.ts") !== contextNodeId("symbol", "src/app.ts"), "kind participates in identity")
  assert(contextNodeId("file", "src/app.ts").startsWith("sha256:"), "identities use explicit sha256 encoding")
  assert(
    contextEdgeId("imports", "file", "a", "file", "b") === contextEdgeId("imports", "file", "a", "file", "b"),
    "edge identity must be deterministic",
  )
  assert(
    contextEdgeId("calls", "file", "a", "file", "b") !== contextEdgeId("calls", "file", "b", "file", "a"),
    "edge direction participates in identity",
  )

  // --- consolidated save validation + dry run ---------------------------------
  const validation = await makeFixture("validation", "graph-validation-session")
  try {
    const invalidNodes = [
      ...baseNodes(),
      {
        kind: "component" as const,
        key: "component:export-pipeline",
        origin: "verified_source" as const,
      },
      {
        kind: "external" as const,
        key: "model-guessed-runtime",
        origin: "review_inference" as const,
      },
    ]
    const invalidEdges = [
      {
        relation: "depends_on" as const,
        origin: "review_inference" as const,
        sourceKind: "file" as const,
        sourceKey: "src/app.ts",
        targetKind: "file" as const,
        targetKey: "src/util.ts",
        note: "model assertion deliberately uses the wrong relation for validation coverage",
      },
      {
        relation: "imports" as const,
        origin: "verified_source" as const,
        sourceKind: "file" as const,
        sourceKey: "src/app.ts",
        targetKind: "file" as const,
        targetKey: "src/util.ts",
      },
      {
        relation: "imports" as const,
        origin: "verified_source" as const,
        sourceKind: "file" as const,
        sourceKey: "src/app.ts",
        targetKind: "symbol" as const,
        targetKey: "helper@src/util.ts",
        path: "src/app.ts",
        endLine: 2,
      },
    ]

    const dryInvalid = JSON.parse(
      await save.execute({ nodes: invalidNodes, edges: invalidEdges, validate_only: true }, validation.context),
    )
    assert(dryInvalid.valid === false, "dry-run validation reports invalid input without throwing")
    assert(dryInvalid.validationOnly === true && dryInvalid.wroteState === false, "validation-only mode never writes state")
    assert(dryInvalid.violationCount === 5, "all independent semantic violations are returned in one round trip")
    const indexedMessages = dryInvalid.violations.map((item: any) => `${item.path}: ${item.message}`).join("\n")
    assert(indexedMessages.includes("nodes[3]"), "verified_source node violation carries its array index")
    assert(indexedMessages.includes("nodes[4]"), "review_inference node violation carries its array index")
    assert(indexedMessages.includes("edges[0]"), "review_inference edge violation carries its array index")
    assert(indexedMessages.includes("edges[1]"), "verified_source edge violation carries its array index")
    assert(indexedMessages.includes("edges[2]"), "endLine-without-startLine violation carries its array index")
    assert(indexedMessages.includes("requires a tracked source path"), "missing verified source paths are self-describing")
    assert(indexedMessages.includes("requires a note"), "missing inference notes are self-describing")
    assert(indexedMessages.includes("must use the review_inference relation"), "inference relation constraint is self-describing")
    assert(indexedMessages.includes("endLine requires startLine"), "endLine without startLine remains invalid")
    assert(!indexedMessages.includes("component:component:export-pipeline"), "semantic labels do not duplicate their kind prefix")
    assert((await listedGraphState(validation.root)).length === 0, "invalid dry-run writes no projection or pointer files")

    const thrown = await captureFailure(
      async () => save.execute({ nodes: invalidNodes, edges: invalidEdges }, validation.context),
    )
    assert(thrown.includes("5 violation(s)"), "normal save throws one consolidated validation error")
    assert(thrown.includes("nodes[3]") && thrown.includes("edges[1]"), "consolidated error preserves indexed locations")
    assert((await listedGraphState(validation.root)).length === 0, "invalid normal save remains atomic and writes no state")

    const validDry = JSON.parse(
      await save.execute({ scopePrefix: "src", nodes: baseNodes(), edges: baseEdges(), validate_only: true }, validation.context),
    )
    assert(validDry.valid === true && validDry.violationCount === 0, "valid dry run returns an explicit clean result")
    assert(validDry.wroteState === false && validDry.projectionId.startsWith("sha256:"), "valid dry run computes identity without persisting")
    await expectFailure(
      async () => load.execute({}, validation.context),
      "a successful validation-only call must not create session/latest projection pointers",
    )
    assert((await listedGraphState(validation.root)).length === 0, "valid dry-run still writes no projection or pointer files")

    const singleLineNodes = baseNodes().map((node, index) =>
      index === 2 ? { ...node, startLine: 1, endLine: undefined } : node,
    )
    const singleLineSaved = JSON.parse(
      await save.execute({ nodes: singleLineNodes, edges: baseEdges(), complete: true }, validation.context),
    )
    const singleLineProjection = JSON.parse(
      await readFile(path.join(validation.root, singleLineSaved.savedPath), "utf8"),
    )
    const helperNode = singleLineProjection.nodes.find((node: any) => node.key === "helper@src/util.ts")
    assert(helperNode.sourceRef.startLine === 1 && helperNode.sourceRef.endLine === 1, "startLine alone becomes a single-line range")
    const loaded = JSON.parse(await load.execute({}, validation.context))
    assert(loaded.projectionId === singleLineSaved.projectionId, "load returns the saved projection after a successful write")
    const neighborhood = JSON.parse(await query.execute({ nodeLimit: 20, edgeLimit: 20 }, validation.context))
    assert(neighborhood.returnedNodes.length >= 1 && neighborhood.returnedEdges.length >= 1, "query returns a bounded neighborhood from the saved projection")
    const diagram = JSON.parse(await mermaid.execute({}, validation.context))
    assert(diagram.mermaidSource.includes("flowchart"), "mermaid derives flowchart source from the saved projection")
  } finally {
    await validation.cleanup()
  }

  const primary = await makeFixture("primary", "graph-session-a")
  try {
    const REVIEW_ID = "20260825T000000Z-fixture0001-sessio"
    // --- save + persisted identity --------------------------------------------
    const saved = JSON.parse(
      await save.execute({ scopePrefix: "src", nodes: baseNodes(), edges: baseEdges(), reviewId: REVIEW_ID }, primary.context),
    )
    assert(saved.projectionId.startsWith("sha256:"), "projection id is sha256-encoded")
    assert(saved.nodeCount === 3 && saved.edgeCount === 2, "save reports bounded element counts")
    assert(saved.truncated === true, "an unasserted map must be treated as a bounded subset")

    // duplicate identity behavior is deterministic: identical re-save is idempotent
    const resaved = JSON.parse(
      await save.execute({ scopePrefix: "src", nodes: [...baseNodes(), ...baseNodes()], edges: [...baseEdges(), ...baseEdges()], reviewId: REVIEW_ID }, primary.context),
    )
    assert(resaved.projectionId === saved.projectionId, "identical semantic content must reuse one projection id")
    assert(resaved.nodeCount === 3 && resaved.edgeCount === 2, "duplicate elements dedupe idempotently")
    await expectFailure(
      async () =>
        save.execute(
          {
            scopePrefix: "src",
            reviewId: REVIEW_ID,
            nodes: [baseNodes()[0], { ...baseNodes()[0], note: "conflicting annotation" }],
            edges: [],
          },
          primary.context,
        ),
      "conflicting duplicate node identity must fail closed",
    )

    // presentation-only changes do not move identity
    const relabeled = JSON.parse(
      await save.execute(
        {
          scopePrefix: "src",
          reviewId: REVIEW_ID,
          nodes: baseNodes().map((n, i) => (i === 0 ? { ...n, label: "different presentation label" } : n)),
          edges: baseEdges(),
        },
        primary.context,
      ),
    )
    assert(relabeled.projectionId === saved.projectionId, "labels are presentation metadata and never identity inputs")

    // --- fail-closed validation -----------------------------------------------
    await expectFailure(
      async () => save.execute({ nodes: [{ ...(baseNodes()[0] as any), kind: "database" }], edges: [] }, primary.context),
      "unknown node kinds must fail closed",
    )
    await expectFailure(
      async () =>
        save.execute(
          { nodes: [], edges: [{ ...(baseEdges()[0] as any), relation: "some_free_form_relation" }] },
          primary.context,
        ),
      "free-form relation strings must fail closed",
    )
    await expectFailure(
      async () =>
        save.execute(
          { nodes: [{ ...baseNodes()[0], path: "../outside-secret.txt" }], edges: [] },
          primary.context,
        ),
      "path traversal in source refs must fail closed",
    )
    await writeFile(path.join(primary.root, "untracked.txt"), "not tracked\n", "utf8")
    await expectFailure(
      async () => save.execute({ nodes: [{ ...baseNodes()[0], path: "untracked.txt" }], edges: [] }, primary.context),
      "untracked source refs must fail closed",
    )
    await expectFailure(
      async () => save.execute({ nodes: [{ ...baseNodes()[0], path: undefined }], edges: [] }, primary.context),
      "verified_source without captured evidence must fail closed",
    )
    await expectFailure(
      async () =>
        save.execute(
          { nodes: [], edges: [{ ...baseEdges()[1], origin: "verified_source" as const }] },
          primary.context,
        ),
      "review_inference relation must reject verified_source origin",
    )
    await expectFailure(
      async () =>
        save.execute(
          {
            nodes: [],
            edges: [
              {
                relation: "depends_on" as const,
                origin: "review_inference" as const,
                sourceKind: "file" as const,
                sourceKey: "src/app.ts",
                targetKind: "external" as const,
                targetKey: "some-runtime",
              },
            ],
          },
          primary.context,
        ),
      "model assertions can never masquerade as ordinary verified relations",
    )
    await expectFailure(
      async () =>
        save.execute(
          { nodes: [{ kind: "external" as const, key: "some-runtime", origin: "review_inference" as const, path: "README.md" }], edges: [] },
          primary.context,
        ),
      "review_inference elements must not attach source evidence claims",
    )

    // --- staleness against Git blobs -------------------------------------------
    await writeFile(path.join(primary.root, "src", "util.ts"), "export function helper() {\n  return 2\n}\n", "utf8")
    const staleLoaded = JSON.parse(await load.execute({}, primary.context))
    assert(staleLoaded.freshness.staleLinkageCount >= 1, "changed source blob must stale verified linkage")
    assert(
      staleLoaded.freshness.staleLinkage.some((item: any) => item.path === "src/util.ts"),
      "stale linkage must identify the changed file",
    )
    assert(staleLoaded.preview.truncated === true || staleLoaded.counts.nodes <= 40, "load preview stays bounded")

    // --- bounded queries with continuation --------------------------------------
    const manyNodes = Array.from({ length: 12 }, (_, index) => ({
      kind: "component" as const,
      key: `module-${String(index).padStart(2, "0")}`,
      origin: "verified_source" as const,
      path: "README.md",
    }))
    const manyEdges = manyNodes.slice(1).map((node) => ({
      relation: "depends_on" as const,
      origin: "verified_source" as const,
      sourceKind: "component" as const,
      sourceKey: node.key,
      targetKind: "component" as const,
      targetKey: "module-00",
      path: "README.md",
    }))
    const big = JSON.parse(await save.execute({ nodes: [...baseNodes(), ...manyNodes], edges: [...baseEdges(), ...manyEdges] }, primary.context))

    const firstPage = JSON.parse(await query.execute({ nodeLimit: 5, edgeLimit: 4 }, primary.context))
    assert(firstPage.returnedNodes.length === 5, "node limits are enforced on model-visible queries")
    assert(firstPage.returnedEdges.length <= 4, "edge limits are enforced on model-visible queries")
    assert(firstPage.truncated === true, "exceeding a limit must set truncated=true instead of reporting a complete map")
    assert(typeof firstPage.nextCursor === "string", "bounded queries preserve continuation state")
    assert(firstPage.totalsForSelection.nodes > firstPage.returnedNodes.length, "query must not require returning the full graph")

    const secondPage = JSON.parse(await query.execute({ nodeLimit: 5, edgeLimit: 4, cursor: firstPage.nextCursor }, primary.context))
    assert(secondPage.returnedNodes.length === 5, "continuation resumes at its recorded offset")
    const overlap = firstPage.returnedNodes.filter((node: string) => secondPage.returnedNodes.includes(node))
    assert(overlap.length === 0, "continuation windows do not repeat elements")

    let collected = [...firstPage.returnedNodes, ...secondPage.returnedNodes]
    let cursor = secondPage.nextCursor
    while (cursor) {
      const page = JSON.parse(await query.execute({ nodeLimit: 5, edgeLimit: 4, cursor }, primary.context))
      collected = [...collected, ...page.returnedNodes]
      cursor = page.nextCursor
    }
    assert(collected.length === big.nodeCount, "paging eventually covers exactly the saved map")
    assert(new Set(collected).size === collected.length, "paged results never duplicate identities")

    // --- Mermaid derivation -----------------------------------------------------
    const cleanProjectionState = await makeFixture("mermaid", "graph-session-b")
    try {
      const cleanSaved = JSON.parse(
        await save.execute({ scopePrefix: "src", nodes: baseNodes(), edges: baseEdges(), complete: true }, cleanProjectionState.context),
      )
      assert(cleanSaved.truncated === false, "author-asserted completeness records bounds explicitly")
      const renderedOnce = JSON.parse(await mermaid.execute({}, cleanProjectionState.context))
      const renderedTwice = JSON.parse(await mermaid.execute({}, cleanProjectionState.context))
      assert(renderedOnce.mermaidSource === renderedTwice.mermaidSource, "Mermaid output is deterministic for one projection")
      assert(renderedOnce.mermaidSource.includes("flowchart LR"), "Mermaid output is derived flowchart source")
      assert(!renderedOnce.truncated, "complete maps are not marked truncated")
      assert(renderedOnce.derivedFrom.projectionId === cleanSaved.projectionId, "Mermaid declares the projection it was derived from")

      // escaping: hostile label content cannot inject markup or instructions
      await expectFailure(
        async () =>
          save.execute(
            {
              scopePrefix: "src",
              nodes: [{ ...baseNodes()[0], label: "line one\n%% forged mermaid comment" }],
              edges: [],
              complete: true,
            },
            cleanProjectionState.context,
          ),
        "control characters in labels must be rejected before rendering",
      )
      const hostileLabel = 'x" <img src=x onerror=alert(1)> `tick` %% inline comment attempt'
      await save.execute(
        {
          scopePrefix: "src",
          nodes: baseNodes().map((n, i) => (i === 0 ? { ...n, label: hostileLabel } : n)),
          edges: baseEdges(),
          complete: true,
        },
        cleanProjectionState.context,
      )
      const escapedRender = JSON.parse(await mermaid.execute({}, cleanProjectionState.context))
      const source = escapedRender.mermaidSource
      assert(!source.includes("<img"), "raw HTML must never reach Mermaid output")
      assert(source.includes("#lt;img"), "angle brackets are entity-escaped")
      assert(source.includes("#quot;"), "double quotes are entity-escaped")
      assert(!source.includes("`tick`"), "backticks must not survive into labels")
      assert(
        !source.split("\n").some((line) => line.trimStart().startsWith("%%") && line.includes("img")),
        "hostile label content cannot forge Mermaid comment lines",
      )
      assert(
        source.split("\n").some((line) => /^  n\d+\["/.test(line) && line.includes("#lt;img")),
        "escaped label stays inside its quoted statement",
      )

      // derived-only: same identities, different label -> same ids, different presentation
      const relabeledRender = JSON.parse(
        await (async () => {
          const before = JSON.parse(await load.execute({ nodeLimit: 200, edgeLimit: 300 }, cleanProjectionState.context))
          await save.execute(
            {
              scopePrefix: "src",
              nodes: baseNodes().map((n, i) => (i === 0 ? { ...n, label: "presentation changed again" } : n)),
              edges: baseEdges(),
              complete: true,
            },
            cleanProjectionState.context,
          )
          const after = JSON.parse(await load.execute({ nodeLimit: 200, edgeLimit: 300 }, cleanProjectionState.context))
          assert(before.projectionId === after.projectionId, "relabeling keeps projection identity stable")
          return mermaid.execute({}, cleanProjectionState.context)
        })(),
      )
      assert(relabeledRender.derivedFrom.projectionId === cleanSaved.projectionId, "Mermaid remains bound to one projection identity")
      assert(relabeledRender.mermaidSource.includes("presentation changed again"), "Mermaid reflects current projection presentation")

      // subset rendering marks truncation
      const subset = renderContextGraphMermaid(
        {
          schemaVersion: CONTEXT_GRAPH_SCHEMA_VERSION,
          projectionId: cleanSaved.projectionId,
          headSha: "a".repeat(40),
          createdAt: "",
          updatedAt: "",
          scope: {},
          nodes: baseNodes().map((n) => ({
            nodeId: contextNodeId(n.kind, n.key),
            kind: n.kind,
            key: n.key,
            origin: n.origin,
            label: n.label,
          })),
          edges: baseEdges().map((e) => ({
            edgeId: contextEdgeId(e.relation, e.sourceKind, e.sourceKey, e.targetKind, e.targetKey),
            relation: e.relation,
            sourceNodeId: contextNodeId(e.sourceKind, e.sourceKey),
            targetNodeId: contextNodeId(e.targetKind, e.targetKey),
            origin: e.origin,
          })),
          bounds: { nodeLimit: 500, edgeLimit: 800, truncated: false },
        },
        { nodeLimit: 2, edgeLimit: 10 },
      )
      assert(subset.truncated, "clipped views must report subset state")
      assert(subset.mermaid.includes("bounded subset"), "subset diagrams say so explicitly")

      // inference is visually distinguishable
      const styled = JSON.parse(await mermaid.execute({}, cleanProjectionState.context))
      assert(styled.mermaidSource.includes("stroke-dasharray"), "review-inference linkage is visually distinct")

      // --- tampered state fails closed -------------------------------------------
      const graphDir = path.join(cleanProjectionState.root, ".opencode", "state", "context-graphs")
      const projectionFile = path.join(graphDir, `${cleanSaved.projectionId.slice("sha256:".length)}.json`)
      const rawProjection = JSON.parse(await readFile(projectionFile, "utf8"))
      const masqueraded = {
        ...rawProjection,
        edges: rawProjection.edges.map((edge: any) =>
          edge.origin === "review_inference" ? { ...edge, origin: "verified_source" } : edge,
        ),
      }
      await writeFile(projectionFile, JSON.stringify(masqueraded), "utf8")
      await expectFailure(async () => load.execute({}, cleanProjectionState.context), "tampered projections must fail identity validation")

      const reidentified = {
        ...rawProjection,
        nodes: [...rawProjection.nodes, { ...rawProjection.nodes[0], nodeId: "sha256:" + "f".repeat(64), key: "forged.ts" }],
      }
      await writeFile(projectionFile, JSON.stringify(reidentified), "utf8")
      await expectFailure(async () => load.execute({}, cleanProjectionState.context), "forged node identities must fail recomputation")

      // --- review resume consumes persisted state ---------------------------------
      await rm(projectionFile, { force: true })
      const resumedSession = { ...cleanProjectionState.context, sessionID: "fresh-session-after-compaction" }
      const reviewStart = JSON.parse(await start.execute({ objective: "resume smoke", mode: "review" }, resumedSession))
      const resavedForReview = JSON.parse(
        await save.execute({ reviewId: reviewStart.reviewId, scopePrefix: "src", nodes: baseNodes(), edges: baseEdges() }, resumedSession),
      )
      const resumed = JSON.parse(await load.execute({ reviewId: reviewStart.reviewId }, { ...resumedSession, sessionID: "another-new-session" }))
      assert(resumed.projectionId === resavedForReview.projectionId, "review-linked projections reload by review id across sessions")
      assert(resumed.counts.nodes === 3, "resumed projections keep their bounded contents")

      // checkpoint interop: review_state remains intact alongside the graph state
      const checked = JSON.parse(
        await checkpoint.execute({ phase: "architecture-map", reviewedPaths: ["src/util.ts"], completed: ["map"] }, resumedSession),
      )
      assert(checked.schemaVersion === 2, "existing review_state checkpoints stay on schemaVersion 2")
      assert(checked.reviewedPathEvidence.length === 1, "existing review_state evidence capture still works")
      const finding = JSON.parse(
        await record_finding.execute(
          {
            severity: "low",
            title: "interop probe",
            path: "src/util.ts",
            startLine: 1,
            endLine: 1,
            explanation: "proves review_state still functions beside context graphs",
          },
          resumedSession,
        ),
      )
      assert(finding.blobHash, "recorded findings still carry blob evidence")
    } finally {
      await cleanProjectionState.cleanup()
    }
  } finally {
    await primary.cleanup()
  }

  console.log("CONTEXT GRAPH SMOKE PASS")
}

await main()
