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

  // --- scoped Mermaid rendering (M1) -------------------------------------------
  const scoping = await makeFixture("scoping", "graph-session-scoped")
  try {
    const scopeNodes = [
      ...baseNodes(),
      { kind: "component" as const, key: "mod-a", origin: "verified_source" as const, path: "README.md" },
      {
        kind: "component" as const,
        key: "mod-b",
        origin: "verified_source" as const,
        path: "README.md",
        label: 'x" <img src=x> %% forged',
      },
      { kind: "component" as const, key: "mod-c", origin: "verified_source" as const, path: "README.md" },
      { kind: "component" as const, key: "loner", origin: "verified_source" as const, path: "README.md" },
      { kind: "component" as const, key: "idea-x", origin: "review_inference" as const, note: "suspected abstraction" },
      { kind: "component" as const, key: "idea-y", origin: "review_inference" as const, note: "suspected implementation" },
    ]
    const scopeEdges = [
      ...baseEdges(),
      {
        relation: "depends_on" as const,
        origin: "verified_source" as const,
        sourceKind: "component" as const,
        sourceKey: "mod-a",
        targetKind: "component" as const,
        targetKey: "mod-b",
        path: "README.md",
      },
      {
        relation: "depends_on" as const,
        origin: "verified_source" as const,
        sourceKind: "component" as const,
        sourceKey: "mod-c",
        targetKind: "component" as const,
        targetKey: "mod-b",
        path: "README.md",
      },
      {
        relation: "review_inference" as const,
        origin: "review_inference" as const,
        sourceKind: "component" as const,
        sourceKey: "idea-x",
        targetKind: "component" as const,
        targetKey: "idea-y",
        note: "scout suspects idea-x abstracts idea-y",
      },
    ]
    const scopeSaved = JSON.parse(
      await save.execute({ scopePrefix: "src", nodes: scopeNodes, edges: scopeEdges, complete: true }, scoping.context),
    )
    assert(scopeSaved.nodeCount === 9 && scopeSaved.edgeCount === 5, "scoping fixture saves its full topology")
    assert(scopeSaved.truncated === false, "scoping fixture asserts completeness so view bounds are isolated")

    const unscoped = JSON.parse(await mermaid.execute({}, scoping.context))
    assert(unscoped.scoped === false, "unscoped requests report themselves as unscoped")
    assert(unscoped.truncated === false && unscoped.aliasCount === 9, "complete maps render fully without truncation")
    assert(!unscoped.mermaidSource.includes("%% selection"), "unscoped output does not claim a scoped selection")
    assert(unscoped.mermaidSource.includes("class n"), "inference styling survives in unscoped rendering")

    // current no-filter behavior stays compatible: identical request twice and a
    // pinned exact rendering for a tiny synthetic projection.
    const unscopedAgain = JSON.parse(await mermaid.execute({}, scoping.context))
    assert(unscoped.mermaidSource === unscopedAgain.mermaidSource, "unscoped rendering stays deterministic")
    const legacyPinned = renderContextGraphMermaid(
      {
        schemaVersion: CONTEXT_GRAPH_SCHEMA_VERSION,
        projectionId: "sha256:" + "0".repeat(64),
        headSha: "b".repeat(40),
        createdAt: "",
        updatedAt: "",
        scope: {},
        nodes: [
          { nodeId: contextNodeId("file", "a.ts"), kind: "file" as const, key: "a.ts", origin: "verified_source" as const },
          { nodeId: contextNodeId("file", "b.ts"), kind: "file" as const, key: "b.ts", origin: "verified_source" as const },
        ],
        edges: [
          {
            edgeId: contextEdgeId("imports", "file", "a.ts", "file", "b.ts"),
            relation: "imports" as const,
            sourceNodeId: contextNodeId("file", "a.ts"),
            targetNodeId: contextNodeId("file", "b.ts"),
            origin: "verified_source" as const,
          },
        ],
        bounds: { nodeLimit: 500, edgeLimit: 800, truncated: false },
      },
      {},
    )
    assert(
      legacyPinned.mermaid ===
        `%% CodeSleuth repository context graph (derived, bounded presentation; not evidence)\n` +
        `%% projectionId: sha256:${"0".repeat(64)}\n` +
        `%% headSha: ${"b".repeat(40)}\n` +
        `%% scope: .\n` +
        `flowchart LR\n` +
        `  classDef csInference stroke-dasharray: 4 4\n` +
        `  n0["file:a.ts"]\n` +
        `  n1["file:b.ts"]\n` +
        `  n0 -->|"imports"| n1\n` +
        `  %% Legend: solid = verified_source linkage; dashed = review_inference (not verified evidence).\n`,
      "no-filter Mermaid output remains byte-compatible with the historical prefix rendering",
    )

    // explicit root + hops semantics
    const rootHops0 = JSON.parse(
      await mermaid.execute({ roots: [{ kind: "file", key: "src/app.ts" }], hops: 0 }, scoping.context),
    )
    assert(rootHops0.selection.scoped === true && rootHops0.selection.hops === 0, "scoped requests echo their selection")
    assert(rootHops0.aliasCount === 1 && !rootHops0.mermaidSource.includes("-->|"), "hops=0 renders only the roots")
    assert(!rootHops0.truncated, "an exact root-only view is not truncated")
    assert(rootHops0.mermaidSource.includes("selectionRoots: file:src/app.ts"), "roots are declared in diagram metadata")

    const rootHops1 = JSON.parse(
      await mermaid.execute({ roots: [{ kind: "file", key: "src/app.ts" }], hops: 1 }, scoping.context),
    )
    assert(rootHops1.selection.totals.nodes === 3 && rootHops1.selection.totals.edges === 2, "hop expansion matches query neighborhood totals")
    assert(rootHops1.aliasCount === 3, "root plus one-hop neighbors are rendered")
    assert(rootHops1.mermaidSource.includes('selectionHops: 1'), "hop depth is declared in diagram metadata")
    assert(
      rootHops1.mermaidSource.includes("linkStyle") && rootHops1.mermaidSource.includes("csInference"),
      "review-inference styling survives scoped filtering",
    )

    // multiple roots and duplicate roots
    const multiRoot = JSON.parse(
      await mermaid.execute(
        {
          roots: [
            { kind: "file", key: "src/app.ts" },
            { kind: "file", key: "src/util.ts" },
          ],
          hops: 0,
        },
        scoping.context,
      ),
    )
    assert(multiRoot.aliasCount === 2, "multiple roots render together")
    const dupRoot = JSON.parse(
      await mermaid.execute(
        {
          roots: [
            { kind: "file", key: "src/app.ts" },
            { kind: "file", key: "src/app.ts" },
          ],
          hops: 0,
        },
        scoping.context,
      ),
    )
    assert(dupRoot.aliasCount === 1, "duplicate roots deduplicate deterministically")

    // relation filter agrees with query traversal semantics
    const relFiltered = JSON.parse(
      await mermaid.execute(
        { roots: [{ kind: "component", key: "mod-a" }], hops: 1, relation: "depends_on" },
        scoping.context,
      ),
    )
    assert(relFiltered.selection.totals.nodes === 2 && relFiltered.selection.totals.edges === 1, "relation filtering narrows traversal edges only")
    assert(relFiltered.mermaidSource.includes('-->|"depends_on"|'), "filtered relation is rendered")
    assert(!relFiltered.mermaidSource.includes('"imports"') && !relFiltered.mermaidSource.includes('"review_inference"'), "non-matching relations are excluded")
    assert(relFiltered.mermaidSource.includes("selectionRelation: depends_on"), "relation scope is declared in metadata")
    assert(!/linkStyle \d/.test(relFiltered.mermaidSource), "verified-only scoped views carry no dashed links")

    // origin filter, both directions
    const inferenceOnly = JSON.parse(
      await mermaid.execute({ roots: [{ kind: "component", key: "idea-x" }], hops: 1, origin: "review_inference" }, scoping.context),
    )
    assert(inferenceOnly.selection.totals.nodes === 2 && inferenceOnly.selection.totals.edges === 1, "inference-only neighborhoods stay renderable")
    assert(inferenceOnly.mermaidSource.includes("stroke-dasharray: 6 6"), "dashed link styling applied to filtered inference edges")
    const verifiedOnly = JSON.parse(
      await mermaid.execute({ origin: "verified_source", hops: 1 }, scoping.context),
    )
    assert(verifiedOnly.selection.totals.edges === 3, "origin filtering walks only verified linkage from every node")
    assert(!/linkStyle \d/.test(verifiedOnly.mermaidSource), "no dashed links remain in verified-only views")

    // missing root fails closed with the query-tool error contract
    await expectFailure(
      async () => mermaid.execute({ roots: [{ kind: "file", key: "ghost.ts" }] }, scoping.context),
      "roots absent from the saved projection must fail closed",
    )

    // deterministic repeated scoped invocation
    const scopedOnce = JSON.parse(
      await mermaid.execute({ roots: [{ kind: "symbol", key: "helper@src/util.ts" }], hops: 1 }, scoping.context),
    )
    const scopedTwice = JSON.parse(
      await mermaid.execute({ roots: [{ kind: "symbol", key: "helper@src/util.ts" }], hops: 1 }, scoping.context),
    )
    assert(scopedOnce.mermaidSource === scopedTwice.mermaidSource, "scoped Mermaid output is deterministic across invocations")

    // node/edge bounds + truthful truncation marker + dangling-edge exclusion
    const boundedNodes = JSON.parse(
      await mermaid.execute({ relation: "depends_on", nodeLimit: 2, edgeLimit: 50 }, scoping.context),
    )
    assert(boundedNodes.truncated === true, "selection larger than the node limit reports truncation")
    assert(
      boundedNodes.mermaidSource.includes("bounded subset: showing 2 of 9 nodes"),
      "node-bound marker states the true selection size (relation filters narrow edges, not the walk frontier)",
    )
    const boundedEdges = JSON.parse(
      await mermaid.execute({ roots: [{ kind: "component", key: "mod-c" }], hops: 2, edgeLimit: 1 }, scoping.context),
    )
    assert(boundedEdges.truncated === true, "selection larger than the edge limit reports truncation")
    assert(boundedEdges.mermaidSource.includes("and 1 of 2 links"), "edge-bound marker states the true link count")
    const declaredAliases = new Set<string>()
    const scopedEdgeAliases: string[] = []
    for (const line of boundedEdges.mermaidSource.split("\n")) {
      const nodeMatch = /^  (n\d+)\["/.exec(line)
      if (nodeMatch) declaredAliases.add(nodeMatch[1])
      const edgeMatch = /^  (n\d+) -->\|"([^"]*)"\| (n\d+)$/.exec(line)
      if (edgeMatch) scopedEdgeAliases.push(edgeMatch[1], edgeMatch[3])
    }
    assert(
      declaredAliases.size > 0 && scopedEdgeAliases.length > 0 && scopedEdgeAliases.every((alias) => declaredAliases.has(alias)),
      "rendered edges never reference omitted nodes",
    )

    // saved-map author truncation propagates into scoped views
    const partialSaved = JSON.parse(
      await save.execute(
        { scopePrefix: "src", nodes: scopeNodes.slice(0, 4), edges: scopeEdges.slice(0, 1), reviewId: "20260825T000000Z-fixture0002-sessio" },
        scoping.context,
      ),
    )
    assert(partialSaved.truncated === true, "fixture saves an author-truncated map")
    const scopedOnPartial = JSON.parse(
      await mermaid.execute(
        { reviewId: "20260825T000000Z-fixture0002-sessio", roots: [{ kind: "file", key: "src/app.ts" }], hops: 1 },
        scoping.context,
      ),
    )
    assert(scopedOnPartial.savedMapTruncatedByAuthor === true, "author truncation stays visible through scoped rendering")
    assert(scopedOnPartial.truncated === true, "scoped views of author-truncated maps remain marked truncated")

    // hostile labels stay escaped under scoped rendering
    const hostileScoped = JSON.parse(
      await mermaid.execute(
        { projectionId: scopeSaved.projectionId, roots: [{ kind: "component", key: "mod-a" }], hops: 1 },
        scoping.context,
      ),
    )
    const hostileSource = hostileScoped.mermaidSource
    assert(!hostileSource.includes("<img"), "scoped rendering never emits raw HTML from labels")
    assert(hostileSource.includes("#lt;img") && hostileSource.includes("#quot;"), "scoped rendering escapes markup-sensitive label content")
    assert(
      !hostileSource.split("\n").some((line: string) => line.trimStart().startsWith("%%") && line.includes("img")),
      "hostile label content cannot forge scoped diagram comments",
    )

    // hostile KEYS are legal identity inputs and must stay inert in the scoped
    // selection metadata comments (they reach %% selectionRoots verbatim-ish).
    const hostileKey = 'k"x<img src=javascript:>y%%z`w'
    const hostileKeySaved = JSON.parse(
      await save.execute(
        {
          scopePrefix: "src",
          scopeDescription: 'scope note with %% percents, "quotes", <b>markup</b> and `backticks`',
          complete: true,
          nodes: [{ kind: "symbol", key: hostileKey, origin: "review_inference", note: "hostile key holder" }],
          edges: [],
        },
        scoping.context,
      ),
    )
    const hostileKeyScoped = JSON.parse(
      await mermaid.execute(
        { projectionId: hostileKeySaved.projectionId, roots: [{ kind: "symbol", key: hostileKey }], hops: 0 },
        scoping.context,
      ),
    )
    const hostileKeySource = hostileKeyScoped.mermaidSource
    for (const line of hostileKeySource.split("\n")) {
      if (!line.trimStart().startsWith("%%")) continue
      const body = line.trimStart().slice(2)
      assert(!body.includes("%"), "scoped selection comments contain no % after the marker")
      assert(!body.includes("<") && !body.includes(">"), "scoped selection comments never carry raw angle brackets")
      assert(!body.includes("`") && !body.includes('"'), "scoped selection comments never carry quotes or backticks")
    }
    assert(hostileKeySource.includes("#lt;img"), "hostile root keys remain recognizable in escaped selection metadata")
    assert(!hostileKeySource.includes("<img"), "hostile root keys cannot emit raw markup anywhere")
    const hostileKeyUnscoped = JSON.parse(await mermaid.execute({ projectionId: hostileKeySaved.projectionId }, scoping.context))
    for (const line of hostileKeyUnscoped.mermaidSource.split("\n")) {
      if (!line.trimStart().startsWith("%%")) continue
      const body = line.trimStart().slice(2)
      assert(!body.includes("<") && !body.includes(">") && !body.includes("`") && !body.includes('"') && !body.includes("%"),
        "unscoped scope/description comments get the same comment hardening")
    }

    // query and Mermaid selection semantics agree for the same request
    const agreementQuery = JSON.parse(
      await query.execute(
        {
          projectionId: scopeSaved.projectionId,
          roots: [{ kind: "symbol", key: "helper@src/util.ts" }],
          hops: 1,
          nodeLimit: 200,
          edgeLimit: 300,
        },
        scoping.context,
      ),
    )
    const agreementMermaid = JSON.parse(
      await mermaid.execute(
        { projectionId: scopeSaved.projectionId, roots: [{ kind: "symbol", key: "helper@src/util.ts" }], hops: 1 },
        scoping.context,
      ),
    )
    assert(
      agreementMermaid.selection.totals.nodes === agreementQuery.totalsForSelection.nodes &&
        agreementMermaid.selection.totals.edges === agreementQuery.totalsForSelection.edges,
      "query and Mermaid report identical neighborhood totals for one request",
    )
    assert(agreementMermaid.aliasCount === agreementQuery.returnedNodes.length, "query and Mermaid expose the same node set size")

    // compactNode format: `kind:key (label)? [inference]?`; diagram display is
    // `kind: label` for labeled nodes and `kind:key` otherwise.
    function expectedDisplay(compact: string): string {
      const colon = compact.indexOf(":")
      const kind = compact.slice(0, colon)
      let rest = compact.slice(colon + 1)
      const inference = rest.endsWith(" [inference]")
      if (inference) rest = rest.slice(0, -" [inference]".length)
      let label: string | undefined
      const labelMatch = / \((.*)\)$/.exec(rest)
      if (labelMatch) {
        label = labelMatch[1]
        rest = rest.slice(0, rest.length - labelMatch[0].length)
      }
      return label ? `${kind}: ${label}` : `${kind}:${rest}`
    }
    const aliasByDisplay = new Map<string, string>()
    for (const line of agreementMermaid.mermaidSource.split("\n")) {
      const decl = /^  (n\d+)\["(.*)"\]$/.exec(line)
      if (decl) aliasByDisplay.set(decl[2], decl[1])
    }
    assert(aliasByDisplay.size === agreementQuery.returnedNodes.length, "diagram declares exactly the queried node set")
    for (const compact of agreementQuery.returnedNodes) {
      assert(aliasByDisplay.has(expectedDisplay(compact)), `every queried node appears in the scoped diagram: ${compact}`)
    }
    const renderedEdgeLines = new Set(
      agreementMermaid.mermaidSource
        .split("\n")
        .map((line: string) => /^  (n\d+) -->\|"([^"]*)"\| (n\d+)$/.exec(line))
        .filter(Boolean)
        .map((m: any) => `${m[1]}|${m[2]}|${m[3]}`),
    )
    for (const compactEdge of agreementQuery.returnedEdges) {
      const match = /^(.*) -\[(.*)\]-> (.*)$/.exec(compactEdge)
      assert(match, "query edges parse for agreement comparison")
      const [, src, rel, dst] = match!
      const srcAlias = aliasByDisplay.get(expectedDisplay(src))
      const dstAlias = aliasByDisplay.get(expectedDisplay(dst))
      assert(srcAlias && dstAlias, "agreement edge endpoints resolve to diagram aliases")
      assert(
        renderedEdgeLines.has(`${srcAlias}|${rel}|${dstAlias}`),
        `every queried edge appears in the scoped diagram: ${compactEdge}`,
      )
    }
  } finally {
    await scoping.cleanup()
  }

  console.log("CONTEXT GRAPH SMOKE PASS")
}

await main()
