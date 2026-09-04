import { tool } from "@opencode-ai/plugin"
import { createHash } from "node:crypto"
import { access, readFile } from "node:fs/promises"
import path from "node:path"

import {
  EDGE_RELATIONS,
  ELEMENT_ORIGINS,
  NODE_KINDS,
  load as contextGraphLoad,
  type ContextEdge,
  type ContextNode,
  type RepositoryContextProjection,
  type SourceRef,
} from "./repo_context_graph"

const GRAPH_READER_ENV = "CODESLEUTH_GRAPH_READER_BIN"
const EXACT_GIT_SHA_RE = /^(?:[0-9a-f]{40}|[0-9a-f]{64})$/
const PROJECTION_ID_RE = /^sha256:[0-9a-f]{64}$/
const BLOB_HASH_RE = /^[0-9a-f]{40}$/
const MAX_HOPS = 3
const MAX_VIEW_NODES = 200
const MAX_VIEW_EDGES = 300
const MAX_RESOLVE_LIMIT = 50
const MAX_PATH_HOPS = 6
const MAX_PATHS = 10
const MAX_PATH_EXPANSIONS = 50_000
const MAX_EXPLAIN_INCIDENT = 50
const MAX_DIFF_LIMIT = 200
const MAX_READ_LINES = 200
const MAX_FILE_BYTES = 1_000_000
const MAX_NATIVE_STDOUT = 8 * 1024 * 1024

type ToolContext = {
  worktree: string
  directory: string
  sessionID: string
  messageID: string
  agent: string
}

type PortableGraph = {
  graphId: string
  nodes: Array<{
    id: string
    kind: string
    key: string
    label?: string
    origin?: string
    sourceRef?: SourceRef
    metadata: Record<string, unknown>
  }>
  edges: Array<{
    id: string
    relation: string
    source: string
    target: string
    origin?: string
    sourceRef?: SourceRef
    metadata: Record<string, unknown>
  }>
}

const POLICY = {
  sourceAuthority: "tracked Git source + blob identity",
  reviewAuthority: "review_state",
  projectionRole: "derived navigation/context",
  portableCoreRole: "bounded deterministic computation, not authority",
  mermaidRole: "secondary derived presentation",
  reopenSourceBeforeEditOrFinding: true,
}

function parseToolJson(value: unknown, label: string): any {
  if (typeof value !== "string") throw new Error(`${label} returned a non-text response`)
  try {
    return JSON.parse(value)
  } catch {
    throw new Error(`${label} returned invalid JSON`)
  }
}

function projectionPayloadDigest(raw: string): string {
  return createHash("sha256").update(raw, "utf8").digest("hex")
}

function projectionPath(root: string, projectionId: string): string {
  if (!PROJECTION_ID_RE.test(projectionId)) throw new Error(`invalid projection id: ${projectionId}`)
  return path.join(root, ".opencode", "state", "context-graphs", `${projectionId.slice("sha256:".length)}.json`)
}

async function git(root: string, args: string[]): Promise<string> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  const code = await proc.exited
  if (code !== 0) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`)
  return stdout.trim()
}

function normalizeWorktreePath(root: string, input: string): string {
  const absoluteRoot = path.resolve(root)
  const absolute = path.resolve(root, input)
  const rootPrefix = absoluteRoot + path.sep
  if (absolute !== absoluteRoot && !absolute.startsWith(rootPrefix)) {
    throw new Error(`path escapes worktree: ${input}`)
  }
  const relative = path.relative(absoluteRoot, absolute).replace(/\\/g, "/")
  if (!relative || relative === ".") throw new Error(`source ref must name a tracked file: ${input}`)
  if (relative.split("/").includes("..")) throw new Error(`path escapes worktree: ${input}`)
  return relative
}

async function exists(file: string): Promise<boolean> {
  try {
    await access(file)
    return true
  } catch {
    return false
  }
}

export type ReaderBinaryStatus =
  | { available: true; binaryPath: string }
  | { available: false; reason: string; configuredPath?: string }

export function inspectGraphReaderBinary(env: NodeJS.ProcessEnv = process.env): ReaderBinaryStatus {
  const configured = env[GRAPH_READER_ENV]
  if (!configured) {
    return {
      available: false,
      reason: `${GRAPH_READER_ENV} is not set; ordinary CodeSleuth installs do not compile Rust at tool invocation`,
    }
  }
  if (!path.isAbsolute(configured)) {
    return {
      available: false,
      configuredPath: configured,
      reason: `${GRAPH_READER_ENV} must be an absolute path, not a PATH lookup`,
    }
  }
  return { available: true, binaryPath: configured }
}

async function resolveGraphReaderBinary(): Promise<string> {
  const inspected = inspectGraphReaderBinary()
  if (!inspected.available) throw new Error(`portable graph reader unavailable: ${inspected.reason}`)
  if (!(await exists(inspected.binaryPath))) {
    throw new Error(`portable graph reader binary is missing: ${inspected.binaryPath}`)
  }
  return inspected.binaryPath
}

async function invokeNative(request: Record<string, unknown>): Promise<any> {
  const binary = await resolveGraphReaderBinary()
  const proc = Bun.spawn([binary], {
    stdin: "pipe",
    stdout: "pipe",
    stderr: "pipe",
  })
  proc.stdin.write(JSON.stringify(request))
  proc.stdin.end()
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  const code = await proc.exited
  if (stdout.length > MAX_NATIVE_STDOUT) {
    throw new Error("portable graph reader stdout exceeded the adapter bound")
  }
  let payload: any
  try {
    payload = JSON.parse(stdout)
  } catch {
    throw new Error(`portable graph reader returned non-JSON stdout${stderr.trim() ? `; stderr: ${stderr.trim().slice(0, 500)}` : ""}`)
  }
  if (payload?.ok !== true) {
    const kind = payload?.error?.kind || "native_error"
    const message = payload?.error?.message || stderr.trim() || `graph reader exited ${code}`
    throw new Error(`portable graph reader ${kind}: ${message}`)
  }
  return payload.result
}

function toPortableGraph(projection: RepositoryContextProjection): PortableGraph {
  return {
    graphId: projection.projectionId,
    nodes: projection.nodes.map((node: ContextNode) => ({
      id: node.nodeId,
      kind: node.kind,
      key: node.key,
      ...(node.label ? { label: node.label } : {}),
      origin: node.origin,
      ...(node.sourceRef ? { sourceRef: node.sourceRef } : {}),
      metadata: node.note ? { note: node.note } : {},
    })),
    edges: projection.edges.map((edge: ContextEdge) => ({
      id: edge.edgeId,
      relation: edge.relation,
      source: edge.sourceNodeId,
      target: edge.targetNodeId,
      origin: edge.origin,
      ...(edge.sourceRef ? { sourceRef: edge.sourceRef } : {}),
      metadata: edge.note ? { note: edge.note } : {},
    })),
  }
}

async function loadValidatedProjection(
  context: ToolContext,
  selector: { projectionId?: string; reviewId?: string },
  expectedHeadSha?: string,
  mode: "current" | "historical" = "current",
): Promise<{ loaded: any; projection: RepositoryContextProjection; currentHeadSha: string; payloadDigest: string }> {
  const loaded = parseToolJson(await contextGraphLoad.execute(selector, context), "repo_context_graph_load")
  const currentHeadSha = loaded?.freshness?.currentHeadSha
  if (typeof currentHeadSha !== "string" || !EXACT_GIT_SHA_RE.test(currentHeadSha)) {
    throw new Error("context graph load did not return an exact current Git head")
  }
  if (expectedHeadSha && expectedHeadSha !== currentHeadSha) {
    throw new Error(`context graph target drift: expected ${expectedHeadSha}, current HEAD is ${currentHeadSha}`)
  }
  if (mode === "current") {
    if (loaded.headSha !== currentHeadSha || loaded?.freshness?.headChanged === true) {
      throw new Error(`context projection head ${loaded.headSha} does not match current HEAD ${currentHeadSha}`)
    }
    if (loaded?.freshness?.staleLinkageCount !== 0) {
      throw new Error(`context projection has ${loaded?.freshness?.staleLinkageCount ?? "unknown"} stale SourceRef link(s)`)
    }
  }
  const raw = await readFile(projectionPath(context.worktree, loaded.projectionId), "utf8")
  const projection = JSON.parse(raw) as RepositoryContextProjection
  if (projection.projectionId !== loaded.projectionId || projection.headSha !== loaded.headSha) {
    throw new Error("persisted projection identity changed during graph read")
  }
  return { loaded, projection, currentHeadSha, payloadDigest: projectionPayloadDigest(raw) }
}

async function assertProjectionUnchanged(
  context: ToolContext,
  expected: { projectionId: string; headSha: string; payloadDigest: string },
): Promise<void> {
  const raw = await readFile(projectionPath(context.worktree, expected.projectionId), "utf8")
  const projection = JSON.parse(raw) as RepositoryContextProjection
  if (projection.projectionId !== expected.projectionId || projection.headSha !== expected.headSha) {
    throw new Error("projection identity changed during native graph read")
  }
  if (projectionPayloadDigest(raw) !== expected.payloadDigest) {
    throw new Error("projection payload changed during native graph read")
  }
}

function envelope(input: {
  operation: string
  currentHeadSha: string
  projection: RepositoryContextProjection
  freshness: any
  result: unknown
  historical?: boolean
}): string {
  return JSON.stringify(
    {
      schemaVersion: 1,
      operation: input.operation,
      kind: "codesleuth-context-graph-read",
      target: {
        currentHeadSha: input.currentHeadSha,
        projectionHeadSha: input.projection.headSha,
        projectionId: input.projection.projectionId,
        exactHeadMatch: input.projection.headSha === input.currentHeadSha,
        historical: input.historical === true,
      },
      freshness: {
        staleLinkageCount: input.freshness?.staleLinkageCount ?? 0,
        headChanged: input.freshness?.headChanged === true,
      },
      result: input.result,
      policy: POLICY,
    },
    null,
    2,
  )
}

const selectorArgs = {
  expectedHeadSha: tool.schema
    .string()
    .optional()
    .describe("Optional exact current Git SHA expected by the caller; mismatches fail closed"),
  projectionId: tool.schema.string().optional(),
  reviewId: tool.schema.string().optional(),
}

export const status = tool({
  description:
    "Report whether the portable native graph reader binary is bound. Absence is explicit and fail-closed; this tool never compiles Rust.",
  args: {},
  async execute() {
    const inspected = inspectGraphReaderBinary()
    if (!inspected.available) {
      return JSON.stringify(
        {
          schemaVersion: 1,
          available: false,
          reason: inspected.reason,
          ...(inspected.configuredPath ? { configuredPath: inspected.configuredPath } : {}),
          policy: POLICY,
        },
        null,
        2,
      )
    }
    const present = await exists(inspected.binaryPath)
    return JSON.stringify(
      {
        schemaVersion: 1,
        available: present,
        binaryPath: inspected.binaryPath,
        ...(present ? {} : { reason: `portable graph reader binary is missing: ${inspected.binaryPath}` }),
        policy: POLICY,
      },
      null,
      2,
    )
  },
})

export const describe = tool({
  description:
    "Describe a saved RepositoryContextProjection through the portable bounded graph reader. Current-state reads fail closed on HEAD/SourceRef drift. Graph output is derived navigation/context, not evidence.",
  args: selectorArgs,
  async execute(args, context: ToolContext) {
    if (args.expectedHeadSha && !EXACT_GIT_SHA_RE.test(args.expectedHeadSha)) {
      throw new Error("expectedHeadSha must be one exact lowercase 40- or 64-hex Git object id")
    }
    const { loaded, projection, currentHeadSha, payloadDigest } = await loadValidatedProjection(
      context,
      { projectionId: args.projectionId, reviewId: args.reviewId },
      args.expectedHeadSha,
      "current",
    )
    const result = await invokeNative({ operation: "describe", graph: toPortableGraph(projection) })
    await assertProjectionUnchanged(context, {
      projectionId: projection.projectionId,
      headSha: projection.headSha,
      payloadDigest,
    })
    return envelope({ operation: "describe", currentHeadSha, projection, freshness: loaded.freshness, result })
  },
})

export const resolve = tool({
  description:
    "Deterministically resolve nodes in a saved projection. Opaque/hash-like IDs match only by exact ID; key/label matching never fuzzy-ranks hashes. Derived navigation only.",
  args: {
    ...selectorArgs,
    query: tool.schema.string().min(1).max(300),
    kinds: tool.schema.array(tool.schema.enum(NODE_KINDS)).max(20).optional(),
    origins: tool.schema.array(tool.schema.enum(ELEMENT_ORIGINS)).max(8).optional(),
    limit: tool.schema.number().int().min(1).max(MAX_RESOLVE_LIMIT).optional(),
  },
  async execute(args, context: ToolContext) {
    if (args.expectedHeadSha && !EXACT_GIT_SHA_RE.test(args.expectedHeadSha)) {
      throw new Error("expectedHeadSha must be one exact lowercase 40- or 64-hex Git object id")
    }
    const { loaded, projection, currentHeadSha, payloadDigest } = await loadValidatedProjection(
      context,
      { projectionId: args.projectionId, reviewId: args.reviewId },
      args.expectedHeadSha,
      "current",
    )
    const result = await invokeNative({
      operation: "resolve",
      graph: toPortableGraph(projection),
      options: {
        query: args.query,
        kinds: args.kinds ?? [],
        origins: args.origins ?? [],
        limit: args.limit ?? 20,
      },
    })
    await assertProjectionUnchanged(context, {
      projectionId: projection.projectionId,
      headSha: projection.headSha,
      payloadDigest,
    })
    return envelope({ operation: "resolve", currentHeadSha, projection, freshness: loaded.freshness, result })
  },
})

export const neighbors = tool({
  description:
    "Bounded neighborhood retrieval through the portable graph reader. Hard hop/node/edge bounds, graph-bound cursors, and no dangling returned edges. Derived navigation only.",
  args: {
    ...selectorArgs,
    roots: tool.schema.array(tool.schema.string().min(1).max(200)).min(1).max(20),
    direction: tool.schema.enum(["out", "in", "both"]).optional(),
    relations: tool.schema.array(tool.schema.enum(EDGE_RELATIONS)).max(20).optional(),
    origins: tool.schema.array(tool.schema.enum(ELEMENT_ORIGINS)).max(8).optional(),
    hops: tool.schema.number().int().min(0).max(MAX_HOPS).optional(),
    nodeLimit: tool.schema.number().int().min(1).max(MAX_VIEW_NODES).optional(),
    edgeLimit: tool.schema.number().int().min(1).max(MAX_VIEW_EDGES).optional(),
    cursor: tool.schema.string().max(300).optional(),
  },
  async execute(args, context: ToolContext) {
    if (args.expectedHeadSha && !EXACT_GIT_SHA_RE.test(args.expectedHeadSha)) {
      throw new Error("expectedHeadSha must be one exact lowercase 40- or 64-hex Git object id")
    }
    const { loaded, projection, currentHeadSha, payloadDigest } = await loadValidatedProjection(
      context,
      { projectionId: args.projectionId, reviewId: args.reviewId },
      args.expectedHeadSha,
      "current",
    )
    const result = await invokeNative({
      operation: "neighbors",
      graph: toPortableGraph(projection),
      options: {
        roots: args.roots,
        direction: args.direction ?? "out",
        relations: args.relations ?? [],
        origins: args.origins ?? [],
        hops: args.hops ?? 1,
        nodeLimit: args.nodeLimit ?? 40,
        edgeLimit: args.edgeLimit ?? 60,
        ...(args.cursor ? { cursor: args.cursor } : {}),
      },
    })
    await assertProjectionUnchanged(context, {
      projectionId: projection.projectionId,
      headSha: projection.headSha,
      payloadDigest,
    })
    return envelope({ operation: "neighbors", currentHeadSha, projection, freshness: loaded.freshness, result })
  },
})

export const shortest_paths = tool({
  description:
    "Bounded shortest-path retrieval through the portable graph reader. Hop, path-count, and expansion caps apply; unbounded all-paths search is refused. Derived navigation only.",
  args: {
    ...selectorArgs,
    source: tool.schema.string().min(1).max(200),
    target: tool.schema.string().min(1).max(200),
    direction: tool.schema.enum(["out", "in", "both"]).optional(),
    relations: tool.schema.array(tool.schema.enum(EDGE_RELATIONS)).max(20).optional(),
    origins: tool.schema.array(tool.schema.enum(ELEMENT_ORIGINS)).max(8).optional(),
    maxHops: tool.schema.number().int().min(1).max(MAX_PATH_HOPS).optional(),
    maxPaths: tool.schema.number().int().min(1).max(MAX_PATHS).optional(),
    expansionLimit: tool.schema.number().int().min(1).max(MAX_PATH_EXPANSIONS).optional(),
  },
  async execute(args, context: ToolContext) {
    if (args.expectedHeadSha && !EXACT_GIT_SHA_RE.test(args.expectedHeadSha)) {
      throw new Error("expectedHeadSha must be one exact lowercase 40- or 64-hex Git object id")
    }
    const { loaded, projection, currentHeadSha, payloadDigest } = await loadValidatedProjection(
      context,
      { projectionId: args.projectionId, reviewId: args.reviewId },
      args.expectedHeadSha,
      "current",
    )
    const result = await invokeNative({
      operation: "shortest_paths",
      graph: toPortableGraph(projection),
      options: {
        source: args.source,
        target: args.target,
        direction: args.direction ?? "out",
        relations: args.relations ?? [],
        origins: args.origins ?? [],
        maxHops: args.maxHops ?? 3,
        maxPaths: args.maxPaths ?? 3,
        expansionLimit: args.expansionLimit ?? 1000,
      },
    })
    await assertProjectionUnchanged(context, {
      projectionId: projection.projectionId,
      headSha: projection.headSha,
      payloadDigest,
    })
    return envelope({ operation: "shortest_paths", currentHeadSha, projection, freshness: loaded.freshness, result })
  },
})

export const explain = tool({
  description:
    "Explain one exact node or edge ID from a saved projection, including edge endpoints needed to reopen source. Graph relations remain navigation/context, not finding evidence.",
  args: {
    ...selectorArgs,
    elementId: tool.schema.string().min(1).max(200),
    incidentLimit: tool.schema.number().int().min(1).max(MAX_EXPLAIN_INCIDENT).optional(),
  },
  async execute(args, context: ToolContext) {
    if (args.expectedHeadSha && !EXACT_GIT_SHA_RE.test(args.expectedHeadSha)) {
      throw new Error("expectedHeadSha must be one exact lowercase 40- or 64-hex Git object id")
    }
    const { loaded, projection, currentHeadSha, payloadDigest } = await loadValidatedProjection(
      context,
      { projectionId: args.projectionId, reviewId: args.reviewId },
      args.expectedHeadSha,
      "current",
    )
    const result = await invokeNative({
      operation: "explain",
      graph: toPortableGraph(projection),
      elementId: args.elementId,
      incidentLimit: args.incidentLimit ?? 20,
    })
    await assertProjectionUnchanged(context, {
      projectionId: projection.projectionId,
      headSha: projection.headSha,
      payloadDigest,
    })
    return envelope({ operation: "explain", currentHeadSha, projection, freshness: loaded.freshness, result })
  },
})

export const diff = tool({
  description:
    "ID-based bounded diff of two saved projections. Reports each side's identity and freshness rather than treating a historical graph as current evidence authority.",
  args: {
    expectedHeadSha: tool.schema.string().optional(),
    beforeProjectionId: tool.schema.string(),
    afterProjectionId: tool.schema.string(),
    limit: tool.schema.number().int().min(1).max(MAX_DIFF_LIMIT).optional(),
  },
  async execute(args, context: ToolContext) {
    if (args.expectedHeadSha && !EXACT_GIT_SHA_RE.test(args.expectedHeadSha)) {
      throw new Error("expectedHeadSha must be one exact lowercase 40- or 64-hex Git object id")
    }
    const before = await loadValidatedProjection(
      context,
      { projectionId: args.beforeProjectionId },
      args.expectedHeadSha,
      "historical",
    )
    const after = await loadValidatedProjection(
      context,
      { projectionId: args.afterProjectionId },
      args.expectedHeadSha,
      "historical",
    )
    const result = await invokeNative({
      operation: "diff",
      before: toPortableGraph(before.projection),
      after: toPortableGraph(after.projection),
      options: { limit: args.limit ?? 50 },
    })
    await assertProjectionUnchanged(context, {
      projectionId: before.projection.projectionId,
      headSha: before.projection.headSha,
      payloadDigest: before.payloadDigest,
    })
    await assertProjectionUnchanged(context, {
      projectionId: after.projection.projectionId,
      headSha: after.projection.headSha,
      payloadDigest: after.payloadDigest,
    })
    return JSON.stringify(
      {
        schemaVersion: 1,
        operation: "diff",
        kind: "codesleuth-context-graph-read",
        target: {
          currentHeadSha: after.currentHeadSha,
          before: {
            projectionId: before.projection.projectionId,
            projectionHeadSha: before.projection.headSha,
            exactHeadMatch: before.projection.headSha === before.currentHeadSha,
            staleLinkageCount: before.loaded.freshness?.staleLinkageCount ?? 0,
          },
          after: {
            projectionId: after.projection.projectionId,
            projectionHeadSha: after.projection.headSha,
            exactHeadMatch: after.projection.headSha === after.currentHeadSha,
            staleLinkageCount: after.loaded.freshness?.staleLinkageCount ?? 0,
          },
          historical: true,
        },
        result,
        policy: POLICY,
      },
      null,
      2,
    )
  },
})

export const read_source_ref = tool({
  description:
    "Reopen an exact SourceRef: revalidate tracked path and blob identity, then return a bounded line range. Stale blob identity fails closed. A graph relation is not finding evidence.",
  args: {
    path: tool.schema.string().min(1).max(1024),
    blobHash: tool.schema.string().min(40).max(40),
    startLine: tool.schema.number().int().min(1).optional(),
    endLine: tool.schema.number().int().min(1).optional(),
  },
  async execute(args, context: ToolContext) {
    if (!BLOB_HASH_RE.test(args.blobHash)) {
      throw new Error("blobHash must be one exact lowercase 40-hex Git blob id")
    }
    const relative = normalizeWorktreePath(context.worktree, args.path)
    const trackedRaw = await git(context.worktree, ["ls-files", "-z", "--", relative])
    const tracked = new Set(trackedRaw.split("\0").filter(Boolean).map((item) => item.replace(/\\/g, "/")))
    if (!tracked.has(relative)) {
      throw new Error(`source ref path is not a tracked file: ${relative}`)
    }
    const actualBlob = await git(context.worktree, ["hash-object", "--", relative])
    if (actualBlob !== args.blobHash) {
      throw new Error(
        `source ref blob is stale for ${relative}: expected ${args.blobHash}, current ${actualBlob}`,
      )
    }
    const startLine = args.startLine ?? 1
    const requestedEnd = args.endLine ?? startLine + MAX_READ_LINES - 1
    if (args.endLine !== undefined && args.startLine === undefined) {
      throw new Error("endLine requires startLine")
    }
    if (requestedEnd < startLine) throw new Error("line range must be positive and ordered")
    if (requestedEnd - startLine + 1 > MAX_READ_LINES) {
      throw new Error(`at most ${MAX_READ_LINES} lines may be read at once`)
    }
    const absolute = path.join(context.worktree, ...relative.split("/"))
    const bytes = Buffer.from(await readFile(absolute))
    if (bytes.length > MAX_FILE_BYTES) throw new Error(`file is larger than ${MAX_FILE_BYTES} bytes`)
    if (bytes.includes(0)) throw new Error("binary files cannot be returned as source evidence")
    const lines = bytes.toString("utf8").split(/\r?\n/)
    const selected = lines.slice(startLine - 1, requestedEnd)
    return JSON.stringify(
      {
        schemaVersion: 1,
        kind: "codesleuth-source-ref-read",
        path: relative,
        blobHash: actualBlob,
        startLine,
        endLine: selected.length === 0 ? startLine - 1 : startLine + selected.length - 1,
        lineCount: lines.length,
        truncated: requestedEnd < lines.length,
        lines: selected.map((text, offset) => ({ line: startLine + offset, text })),
        policy: {
          ...POLICY,
          graphRelationIsNotFindingEvidence: true,
        },
      },
      null,
      2,
    )
  },
})
