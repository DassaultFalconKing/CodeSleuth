import { tool } from "@opencode-ai/plugin"
import { createHash, randomUUID } from "node:crypto"
import { mkdir, readFile, rename, rm, writeFile } from "node:fs/promises"
import path from "node:path"

// Renderer-neutral RepositoryContextProjection for CodeSleuth.
//
// Authority discipline (adapted from Aleph_Rugent ADR 0003 / G1 with
// repository/Git semantics instead of FollowTheMoney semantics):
//
//   Git/current source + blob identity = source authority
//   review_state                       = durable review/evidence authority
//   RepositoryContextProjection        = bounded, derived, rebuildable
//                                        linkage/context state (this file)
//   Mermaid                            = derived human-readable projection
//   OpenCode model context             = ephemeral working memory
//
// This module never renders SVG, never invokes mmdc/Chromium, and never
// becomes a second source of repository truth. Projections are rebuildable
// state stored below the ignored .opencode/state boundary.

export const CONTEXT_GRAPH_SCHEMA_VERSION = 1

export const NODE_KINDS = [
  "file",
  "symbol",
  "component",
  "contract",
  "test",
  "workflow",
  "external",
] as const
export type NodeKind = (typeof NODE_KINDS)[number]

export const EDGE_RELATIONS = [
  "imports",
  "calls",
  "implements",
  "registers",
  "persists_to",
  "reads_from",
  "tests",
  "configures",
  "documents",
  "depends_on",
  "review_inference",
] as const
export type EdgeRelation = (typeof EDGE_RELATIONS)[number]

export const ELEMENT_ORIGINS = ["verified_source", "review_inference"] as const
export type ElementOrigin = (typeof ELEMENT_ORIGINS)[number]

const ID_RE = /^[A-Za-z0-9._-]+$/
const PROJECTION_ID_RE = /^sha256:[0-9a-f]{64}$/
const KEY_MAX = 300
const LABEL_MAX = 160
const NOTE_MAX = 500
const DESCRIPTION_MAX = 300
const PATH_MAX = 1024
const MAX_SAVE_NODES = 500
const MAX_SAVE_EDGES = 800
const DEFAULT_VIEW_NODES = 40
const DEFAULT_VIEW_EDGES = 60
const MAX_VIEW_NODES = 200
const MAX_VIEW_EDGES = 300
const MAX_HOPS = 3
const MERMAID_LABEL_CLAMP = 120
const STALENESS_AUDIT_PATH_CAP = 200

export type SourceRef = {
  path: string
  blobHash: string
  startLine?: number
  endLine?: number
}

export type ContextNode = {
  nodeId: string
  kind: NodeKind
  key: string
  label?: string
  origin: ElementOrigin
  sourceRef?: SourceRef
  note?: string
}

export type ContextEdge = {
  edgeId: string
  relation: EdgeRelation
  sourceNodeId: string
  targetNodeId: string
  origin: ElementOrigin
  sourceRef?: SourceRef
  note?: string
}

export type RepositoryContextProjectionBounds = {
  nodeLimit: number
  edgeLimit: number
  truncated: boolean
  note?: string
}

export type RepositoryContextProjection = {
  schemaVersion: number
  projectionId: string
  headSha: string
  reviewId?: string
  createdAt: string
  updatedAt: string
  scope: { prefix?: string; description?: string }
  nodes: ContextNode[]
  edges: ContextEdge[]
  bounds: RepositoryContextProjectionBounds
}

type ValidationViolation = {
  path: string
  message: string
}

async function git(root: string, args: string[]): Promise<string> {
  const proc = Bun.spawn(["git", "-C", root, ...args], {
    stdout: "pipe",
    stderr: "pipe",
  })
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  const code = await proc.exited
  if (code !== 0) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`)
  return stdout
}

function baseDir(root: string): string {
  return path.join(root, ".opencode", "state", "context-graphs")
}

function safeStateName(value: string): string {
  return value.replace(/[^A-Za-z0-9._-]/g, "_")
}

async function readOptional(file: string): Promise<string | undefined> {
  try {
    return await readFile(file, "utf8")
  } catch (error: any) {
    if (error?.code === "ENOENT") return undefined
    throw error
  }
}

async function atomicWrite(file: string, content: string): Promise<void> {
  await mkdir(path.dirname(file), { recursive: true })
  const temp = `${file}.${process.pid}.${randomUUID()}.tmp`
  try {
    await writeFile(temp, content, { encoding: "utf8", flag: "wx" })
    await rename(temp, file)
  } catch (error) {
    await rm(temp, { force: true }).catch(() => undefined)
    throw error
  }
}

function normalizeWorktreePath(root: string, input: string): string {
  const absoluteRoot = path.resolve(root)
  const absolute = path.resolve(root, input)
  const rootPrefix = absoluteRoot + path.sep
  if (absolute !== absoluteRoot && !absolute.startsWith(rootPrefix)) throw new Error(`path escapes worktree: ${input}`)
  const relative = path.relative(absoluteRoot, absolute).replace(/\\/g, "/")
  if (!relative || relative === ".") throw new Error(`source ref must name a tracked file: ${input}`)
  return relative
}

async function trackedPaths(root: string): Promise<Set<string>> {
  const raw = await git(root, ["ls-files", "-z"])
  return new Set(raw.split("\0").filter(Boolean).map((item) => item.replace(/\\/g, "/")))
}

function makeBlobHasher(root: string) {
  const cache = new Map<string, string>()
  return async function blobHash(relativePath: string): Promise<string> {
    const cached = cache.get(relativePath)
    if (cached) return cached
    const hash = (await git(root, ["hash-object", "--", relativePath])).trim()
    if (!hash) throw new Error(`could not capture blob identity for ${relativePath}`)
    cache.set(relativePath, hash)
    return hash
  }
}

function assertNoControl(value: string, what: string): void {
  if (/[\u0000-\u001f\u007f\u2028\u2029]/.test(value)) throw new Error(`${what} must not contain control characters`)
}

function assertValidKey(key: string): void {
  if (!key || key.length > KEY_MAX) throw new Error(`node key must be 1..${KEY_MAX} characters`)
  assertNoControl(key, "node key")
}

function cleanOptionalText(value: string | undefined, what: string, max: number): string | undefined {
  if (value === undefined || value === null) return undefined
  if (typeof value !== "string") throw new Error(`${what} must be a string`)
  assertNoControl(value, what)
  if (!value.trim()) return undefined
  if (value.length > max) throw new Error(`${what} must be at most ${max} characters`)
  return value
}

function normalizeScopePrefix(input?: string): string {
  if (!input) return ""
  const normalized = input.replace(/\\/g, "/").replace(/^\.\//, "").replace(/^\/+/, "").replace(/\/+$/, "")
  if (normalized.split("/").includes("..")) throw new Error("scope prefix must not contain '..' segments")
  if (normalized.length > PATH_MAX) throw new Error("scope prefix is too long")
  assertNoControl(normalized, "scope prefix")
  return normalized
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

function semanticElementName(kind: NodeKind, key: string): string {
  const prefix = `${kind}:`
  return key.startsWith(prefix) ? key : `${prefix}${key}`
}

function formatValidationFailure(violations: ValidationViolation[]): string {
  const details = violations.map((violation) => `- ${violation.path}: ${violation.message}`).join("\n")
  return `context graph validation failed with ${violations.length} violation(s):\n${details}`
}

// Deterministic identity: SHA-256 over explicit NUL-separated semantic fields.
// Display labels, Mermaid aliases, layout and other presentation metadata are
// deliberately excluded from every identity input.
function sha256Nul(fields: string[]): string {
  const hash = createHash("sha256")
  fields.forEach((field, index) => {
    if (index > 0) hash.update(Buffer.from([0]))
    hash.update(field, "utf8")
  })
  return `sha256:${hash.digest("hex")}`
}

export function contextNodeId(kind: NodeKind, key: string): string {
  return sha256Nul(["codesleuth-repo-context-node-v1", kind, key])
}

export function contextEdgeId(
  relation: EdgeRelation,
  sourceKind: NodeKind,
  sourceKey: string,
  targetKind: NodeKind,
  targetKey: string,
): string {
  return sha256Nul([
    "codesleuth-repo-context-edge-v1",
    relation,
    sourceKind,
    sourceKey,
    targetKind,
    targetKey,
  ])
}

function projectionIdentity(input: {
  headSha: string
  reviewId?: string
  scopePrefix: string
  nodeIds: string[]
  edgeIds: string[]
}): string {
  const nodeIds = [...input.nodeIds].sort()
  const edgeIds = [...input.edgeIds].sort()
  return sha256Nul([
    "codesleuth-repo-context-projection-v1",
    String(CONTEXT_GRAPH_SCHEMA_VERSION),
    input.headSha,
    input.reviewId ?? "",
    input.scopePrefix,
    ...nodeIds,
    ...edgeIds,
  ])
}

function canonicalElementPayload(element: Record<string, any>): string {
  return JSON.stringify(element)
}

type NodeInput = {
  kind: NodeKind
  key: string
  label?: string
  origin: ElementOrigin
  path?: string
  startLine?: number
  endLine?: number
  note?: string
}

type EdgeInput = {
  relation: EdgeRelation
  origin: ElementOrigin
  sourceKey: string
  sourceKind: NodeKind
  targetKey: string
  targetKind: NodeKind
  path?: string
  startLine?: number
  endLine?: number
  note?: string
}

type LineRangeInput = {
  path?: string
  startLine?: number
  endLine?: number
}

function assertKnownKind(kind: NodeKind): void {
  if (!(NODE_KINDS as readonly string[]).includes(kind)) throw new Error(`unknown node kind: ${kind}`)
}

function assertKnownRelation(relation: EdgeRelation): void {
  if (!(EDGE_RELATIONS as readonly string[]).includes(relation)) throw new Error(`unknown edge relation: ${relation}`)
}

function assertKnownOrigin(origin: ElementOrigin): void {
  if (!(ELEMENT_ORIGINS as readonly string[]).includes(origin)) throw new Error(`unknown element origin: ${origin}`)
}

async function captureSourceRef(
  root: string,
  elementLabel: string,
  input: LineRangeInput & { path?: string },
  tracked: Set<string>,
  blobHash: (relativePath: string) => Promise<string>,
): Promise<SourceRef> {
  if (!input.path) throw new Error(`verified_source element requires a tracked source path: ${elementLabel}`)
  const relativePath = normalizeWorktreePath(root, input.path)
  if (!tracked.has(relativePath)) throw new Error(`source ref path is not a tracked file: ${relativePath}`)
  let startLine: number | undefined
  let endLine: number | undefined
  if (input.endLine !== undefined && input.startLine === undefined) {
    throw new Error("endLine requires startLine")
  }
  if (input.startLine !== undefined) {
    if (!Number.isInteger(input.startLine)) throw new Error("startLine must be an integer")
    if (input.endLine !== undefined && !Number.isInteger(input.endLine)) throw new Error("endLine must be an integer")
    startLine = input.startLine
    endLine = input.endLine ?? input.startLine
    if (endLine < startLine) throw new Error("endLine must be >= startLine")
  }
  return {
    path: relativePath,
    blobHash: await blobHash(relativePath),
    ...(startLine !== undefined ? { startLine, endLine } : {}),
  }
}

async function materializeNodes(
  root: string,
  inputs: NodeInput[],
  violations: ValidationViolation[] = [],
): Promise<Map<string, ContextNode>> {
  const tracked = await trackedPaths(root)
  const blobHash = makeBlobHasher(root)
  const nodes = new Map<string, ContextNode>()
  for (const [index, input] of inputs.entries()) {
    try {
      assertKnownKind(input.kind)
      assertValidKey(input.key)
      assertKnownOrigin(input.origin)
      const label = cleanOptionalText(input.label, "node label", LABEL_MAX)
      let sourceRef: SourceRef | undefined
      const note = cleanOptionalText(input.note, "node note", NOTE_MAX)
      const semanticName = semanticElementName(input.kind, input.key)
      if (input.origin === "verified_source") {
        sourceRef = await captureSourceRef(root, semanticName, input, tracked, blobHash)
      } else {
        if (input.path) {
          throw new Error(
            `review_inference element must not claim source evidence (${semanticName}); verify it in source first or record a finding`,
          )
        }
        if (!note) throw new Error(`review_inference node requires a note explaining the assertion: ${semanticName}`)
      }
      const candidate: ContextNode = {
        nodeId: contextNodeId(input.kind, input.key),
        kind: input.kind,
        key: input.key,
        origin: input.origin,
        ...(label ? { label } : {}),
        ...(sourceRef ? { sourceRef } : {}),
        ...(note ? { note } : {}),
      }
      const existing = nodes.get(candidate.nodeId)
      if (existing) {
        if (canonicalElementPayload(existing) !== canonicalElementPayload(candidate)) {
          throw new Error(`conflicting duplicate node identity: ${semanticName}`)
        }
        continue
      }
      nodes.set(candidate.nodeId, candidate)
    } catch (error) {
      violations.push({ path: `nodes[${index}]`, message: errorMessage(error) })
    }
  }
  return nodes
}

async function materializeEdges(
  root: string,
  inputs: EdgeInput[],
  nodes: Map<string, ContextNode>,
  violations: ValidationViolation[] = [],
): Promise<Map<string, ContextEdge>> {
  const tracked = await trackedPaths(root)
  const blobHash = makeBlobHasher(root)
  const edges = new Map<string, ContextEdge>()
  for (const [index, input] of inputs.entries()) {
    try {
      assertKnownRelation(input.relation)
      assertKnownOrigin(input.origin)
      assertKnownKind(input.sourceKind)
      assertKnownKind(input.targetKind)
      assertValidKey(input.sourceKey)
      assertValidKey(input.targetKey)
      const sourceName = semanticElementName(input.sourceKind, input.sourceKey)
      const targetName = semanticElementName(input.targetKind, input.targetKey)
      const sourceNodeId = contextNodeId(input.sourceKind, input.sourceKey)
      const targetNodeId = contextNodeId(input.targetKind, input.targetKey)
      if (!nodes.has(sourceNodeId)) throw new Error(`edge references unknown source node: ${sourceName}`)
      if (!nodes.has(targetNodeId)) throw new Error(`edge references unknown target node: ${targetName}`)
      if (sourceNodeId === targetNodeId) throw new Error("self-referential edges are not supported")
      if (input.origin === "review_inference" && input.relation !== "review_inference") {
        throw new Error(
          `review_inference elements must use the review_inference relation, not "${input.relation}"; model/scout assertions can never become verified_source`,
        )
      }
      if (input.relation === "review_inference" && input.origin !== "review_inference") {
        throw new Error('the review_inference relation is reserved for origin="review_inference"')
      }
      const note = cleanOptionalText(input.note, "edge note", NOTE_MAX)
      let sourceRef: SourceRef | undefined
      if (input.origin === "verified_source") {
        sourceRef = await captureSourceRef(
          root,
          `${input.relation} ${sourceName} -> ${targetName}`,
          input,
          tracked,
          blobHash,
        )
      } else if (!note) {
        throw new Error("review_inference edge requires a note explaining the asserted linkage")
      }
      const candidate: ContextEdge = {
        edgeId: contextEdgeId(input.relation, input.sourceKind, input.sourceKey, input.targetKind, input.targetKey),
        relation: input.relation,
        sourceNodeId,
        targetNodeId,
        origin: input.origin,
        ...(sourceRef ? { sourceRef } : {}),
        ...(note ? { note } : {}),
      }
      const existing = edges.get(candidate.edgeId)
      if (existing) {
        if (canonicalElementPayload(existing) !== canonicalElementPayload(candidate)) {
          throw new Error(
            `conflicting duplicate edge identity: ${input.relation} ${sourceName} -> ${targetName}`,
          )
        }
        continue
      }
      edges.set(candidate.edgeId, candidate)
    } catch (error) {
      violations.push({ path: `edges[${index}]`, message: errorMessage(error) })
    }
  }
  return edges
}

// Fail-closed structural validation used on load/query/mermaid. Unknown kinds,
// relations, origins, dangling endpoints or recomputed-identity mismatches all
// reject the persisted state instead of degrading.
function validateProjection(raw: any): RepositoryContextProjection {
  if (!raw || typeof raw !== "object") throw new Error("context graph projection is malformed")
  if (raw.schemaVersion !== CONTEXT_GRAPH_SCHEMA_VERSION) {
    throw new Error(`unsupported context graph schemaVersion: ${raw.schemaVersion}`)
  }
  if (typeof raw.projectionId !== "string" || !PROJECTION_ID_RE.test(raw.projectionId)) {
    throw new Error("context graph projection has an invalid projectionId")
  }
  if (typeof raw.headSha !== "string" || !/^[0-9a-f]{40}$/.test(raw.headSha)) {
    throw new Error("context graph projection has an invalid headSha")
  }
  const bounds = raw.bounds ?? {}
  if (
    typeof bounds.nodeLimit !== "number" ||
    typeof bounds.edgeLimit !== "number" ||
    typeof bounds.truncated !== "boolean" ||
    bounds.nodeLimit < 1 ||
    bounds.edgeLimit < 1
  ) {
    throw new Error("context graph projection has invalid bounds metadata")
  }

  const nodes = new Map<string, ContextNode>()
  if (!Array.isArray(raw.nodes)) throw new Error("context graph projection nodes must be an array")
  if (raw.nodes.length > MAX_SAVE_NODES) throw new Error("persisted projection exceeds node bound")
  for (const item of raw.nodes) {
    assertKnownKind(item.kind)
    assertKnownOrigin(item.origin)
    assertValidKey(item.key)
    const expected = contextNodeId(item.kind, item.key)
    if (item.nodeId !== expected) throw new Error(`node identity integrity failure for ${semanticElementName(item.kind, item.key)}`)
    if (item.origin === "verified_source" && !item.sourceRef?.path) {
      throw new Error(`verified_source node without source evidence: ${semanticElementName(item.kind, item.key)}`)
    }
    if (item.origin === "review_inference" && item.sourceRef) {
      throw new Error(`review_inference node must not carry sourceRef: ${semanticElementName(item.kind, item.key)}`)
    }
    if (nodes.has(expected)) throw new Error(`duplicate node identity: ${semanticElementName(item.kind, item.key)}`)
    nodes.set(expected, item as ContextNode)
  }

  const edges = new Map<string, ContextEdge>()
  if (!Array.isArray(raw.edges)) throw new Error("context graph projection edges must be an array")
  if (raw.edges.length > MAX_SAVE_EDGES) throw new Error("persisted projection exceeds edge bound")
  for (const item of raw.edges) {
    assertKnownRelation(item.relation)
    assertKnownOrigin(item.origin)
    const source = nodes.get(item.sourceNodeId)
    const target = nodes.get(item.targetNodeId)
    if (!source || !target) throw new Error(`edge references unknown endpoint (${item.relation})`)
    const expected = contextEdgeId(item.relation, source.kind, source.key, target.kind, target.key)
    if (item.edgeId !== expected) throw new Error(`edge identity integrity failure for ${item.relation}`)
    if (item.origin === "review_inference" && item.relation !== "review_inference") {
      throw new Error("review_inference edge must use the review_inference relation")
    }
    if (item.origin === "verified_source" && !item.sourceRef?.path) {
      throw new Error(`verified_source edge without source evidence: ${item.relation}`)
    }
    if (item.origin === "review_inference" && item.sourceRef) {
      throw new Error("review_inference edge must not carry sourceRef")
    }
    if (edges.has(expected)) throw new Error(`duplicate edge identity: ${item.relation}`)
    edges.set(expected, item as ContextEdge)
  }

  const scope = raw.scope ?? {}
  const expectedProjectionId = projectionIdentity({
    headSha: raw.headSha,
    reviewId: raw.reviewId,
    scopePrefix: typeof scope.prefix === "string" ? scope.prefix : "",
    nodeIds: [...nodes.keys()],
    edgeIds: [...edges.keys()],
  })
  if (raw.projectionId !== expectedProjectionId) {
    throw new Error("projection identity integrity failure; state does not match its declared content")
  }

  return {
    schemaVersion: CONTEXT_GRAPH_SCHEMA_VERSION,
    projectionId: raw.projectionId,
    headSha: raw.headSha,
    ...(raw.reviewId !== undefined ? { reviewId: raw.reviewId } : {}),
    createdAt: typeof raw.createdAt === "string" ? raw.createdAt : "",
    updatedAt: typeof raw.updatedAt === "string" ? raw.updatedAt : "",
    scope: {
      ...(typeof scope.prefix === "string" ? { prefix: scope.prefix } : {}),
      ...(typeof scope.description === "string" ? { description: scope.description } : {}),
    },
    nodes: [...nodes.values()].sort((a, b) => a.nodeId.localeCompare(b.nodeId)),
    edges: [...edges.values()].sort((a, b) => a.edgeId.localeCompare(b.edgeId)),
    bounds: {
      nodeLimit: bounds.nodeLimit,
      edgeLimit: bounds.edgeLimit,
      truncated: Boolean(bounds.truncated),
      ...(typeof bounds.note === "string" ? { note: bounds.note } : {}),
    },
  }
}

async function resolveProjectionFile(
  root: string,
  explicit: { projectionId?: string; reviewId?: string },
): Promise<{ file: string; resolvedVia: string }> {
  const dir = baseDir(root)
  if (explicit.projectionId) {
    if (!PROJECTION_ID_RE.test(explicit.projectionId)) throw new Error("invalid projection id format")
    return {
      file: path.join(dir, `${explicit.projectionId.slice("sha256:".length)}.json`),
      resolvedVia: "projectionId",
    }
  }
  if (explicit.reviewId) {
    if (!ID_RE.test(explicit.reviewId)) throw new Error("invalid review id")
    const pointer = await readOptional(path.join(dir, "reviews", `${explicit.reviewId}.txt`))
    if (!pointer?.trim()) throw new Error(`no context graph projection found for review: ${explicit.reviewId}`)
    const candidate = pointer.trim()
    if (!PROJECTION_ID_RE.test(candidate)) throw new Error("review projection pointer is corrupt")
    return { file: path.join(dir, `${candidate.slice("sha256:".length)}.json`), resolvedVia: "reviewId" }
  }
  throw new Error("resolution requires projectionId or reviewId in this helper")
}

async function resolveDefaultProjectionFile(
  root: string,
  sessionID: string,
): Promise<{ file: string; resolvedVia: string }> {
  const dir = baseDir(root)
  const sessionPointer = await readOptional(path.join(dir, "sessions", `${safeStateName(sessionID)}.txt`))
  if (sessionPointer?.trim()) {
    const candidate = sessionPointer.trim()
    if (!PROJECTION_ID_RE.test(candidate)) throw new Error("session projection pointer is corrupt")
    return { file: path.join(dir, `${candidate.slice("sha256:".length)}.json`), resolvedVia: "session" }
  }
  const latest = await readOptional(path.join(dir, "latest.txt"))
  if (latest?.trim()) {
    const candidate = latest.trim()
    if (!PROJECTION_ID_RE.test(candidate)) throw new Error("latest projection pointer is corrupt")
    return { file: path.join(dir, `${candidate.slice("sha256:".length)}.json`), resolvedVia: "latest" }
  }
  throw new Error("no context graph projection found; save one first with repo_context_graph_save")
}

async function loadProjectionByFile(file: string): Promise<RepositoryContextProjection> {
  const raw = await readOptional(file)
  if (!raw) throw new Error("no context graph projection found; save one first with repo_context_graph_save")
  return validateProjection(JSON.parse(raw))
}

type FreshnessAudit = {
  currentHeadSha: string
  headChanged: boolean
  staleLinkage: Array<{ path: string; reason: string; expectedBlobHash?: string; actualBlobHash?: string }>
}

async function freshnessAudit(root: string, projection: RepositoryContextProjection): Promise<FreshnessAudit> {
  const currentHeadSha = (await git(root, ["rev-parse", "HEAD"])).trim()
  const staleLinkage: FreshnessAudit["staleLinkage"] = []

  const expectedByPath = new Map<string, string>()
  for (const element of [...projection.nodes, ...projection.edges]) {
    if (element.origin === "verified_source" && element.sourceRef) {
      expectedByPath.set(element.sourceRef.path, element.sourceRef.blobHash)
    }
  }

  const boundedPaths = [...expectedByPath.keys()].sort().slice(0, STALENESS_AUDIT_PATH_CAP)
  const tracked = await trackedPaths(root)
  const blobHash = makeBlobHasher(root)
  for (const relativePath of boundedPaths) {
    if (!tracked.has(relativePath)) {
      staleLinkage.push({ path: relativePath, reason: "file is no longer tracked" })
      continue
    }
    const expectedBlobHash = expectedByPath.get(relativePath)!
    const actualBlobHash = await blobHash(relativePath)
    if (actualBlobHash !== expectedBlobHash) {
      staleLinkage.push({
        path: relativePath,
        reason: "file content changed since capture",
        expectedBlobHash,
        actualBlobHash,
      })
    }
  }
  if (expectedByPath.size > STALENESS_AUDIT_PATH_CAP) {
    staleLinkage.push({
      path: `<${expectedByPath.size - STALENESS_AUDIT_PATH_CAP} additional paths not audited>`,
      reason: "staleness audit path cap reached",
    })
  }
  return { currentHeadSha, headChanged: currentHeadSha !== projection.headSha, staleLinkage }
}

function compactNode(node: ContextNode): string {
  const label = node.label ? ` (${node.label})` : ""
  const inference = node.origin === "review_inference" ? " [inference]" : ""
  return `${node.kind}:${node.key}${label}${inference}`
}

function compactEdge(projection: RepositoryContextProjection, edge: ContextEdge): string {
  const source = projection.nodes.find((n) => n.nodeId === edge.sourceNodeId)!
  const target = projection.nodes.find((n) => n.nodeId === edge.targetNodeId)!
  const inference = edge.origin === "review_inference" ? " [inference]" : ""
  return `${compactNode(source)} -[${edge.relation}]-> ${compactNode(target)}${inference}`
}

function parseCursor(cursor: string | undefined): { nodeOffset: number; edgeOffset: number } {
  if (!cursor) return { nodeOffset: 0, edgeOffset: 0 }
  const match = /^v1:(\d+):(\d+)$/.exec(cursor)
  if (!match) throw new Error("invalid continuation cursor")
  return { nodeOffset: Number(match[1]), edgeOffset: Number(match[2]) }
}

type NeighborhoodSelection = {
  nodes: ContextNode[]
  edges: ContextEdge[]
  totalSelectedNodes: number
  totalSelectedEdges: number
}

function selectNeighborhood(
  projection: RepositoryContextProjection,
  options: {
    roots?: Array<{ kind: NodeKind; key: string }>
    hops: number
    relationFilter?: EdgeRelation
    originFilter?: ElementOrigin
  },
): NeighborhoodSelection {
  const byNodeId = new Map(projection.nodes.map((node) => [node.nodeId, node]))
  const adjacency = new Map<string, ContextEdge[]>()
  for (const edge of projection.edges) {
    if (options.relationFilter && edge.relation !== options.relationFilter) continue
    if (options.originFilter && edge.origin !== options.originFilter) continue
    for (const endpoint of [edge.sourceNodeId, edge.targetNodeId]) {
      const list = adjacency.get(endpoint) ?? []
      list.push(edge)
      adjacency.set(endpoint, list)
    }
  }
  for (const list of adjacency.values()) list.sort((a, b) => a.edgeId.localeCompare(b.edgeId))

  const selectedNodes: ContextNode[] = []
  const visited = new Set<string>()
  let frontier: string[]
  if (options.roots && options.roots.length > 0) {
    frontier = []
    for (const root of options.roots) {
      assertKnownKind(root.kind)
      assertValidKey(root.key)
      const id = contextNodeId(root.kind, root.key)
      if (!byNodeId.has(id)) throw new Error(`root node not present in saved projection: ${semanticElementName(root.kind, root.key)}`)
      if (!visited.has(id)) {
        visited.add(id)
        frontier.push(id)
      }
    }
    frontier.sort((a, b) => a.localeCompare(b))
  } else {
    frontier = projection.nodes.map((node) => node.nodeId).sort((a, b) => a.localeCompare(b))
    for (const id of frontier) visited.add(id)
  }
  selectedNodes.push(...frontier.map((id) => byNodeId.get(id)!))

  const selectedEdges = new Set<string>()
  for (let hop = 0; hop < Math.max(0, options.hops); hop++) {
    const nextFrontier: string[] = []
    for (const nodeId of frontier) {
      for (const edge of adjacency.get(nodeId) ?? []) {
        selectedEdges.add(edge.edgeId)
        const other = edge.sourceNodeId === nodeId ? edge.targetNodeId : edge.sourceNodeId
        if (!visited.has(other)) {
          visited.add(other)
          nextFrontier.push(other)
        }
      }
    }
    nextFrontier.sort((a, b) => a.localeCompare(b))
    selectedNodes.push(...nextFrontier.map((id) => byNodeId.get(id)!))
    frontier = nextFrontier
    if (frontier.length === 0) break
  }

  const includedIds = new Set(selectedNodes.map((node) => node.nodeId))
  const edgesWithin = projection.edges.filter(
    (edge) => selectedEdges.has(edge.edgeId) && includedIds.has(edge.sourceNodeId) && includedIds.has(edge.targetNodeId),
  )
  return {
    nodes: selectedNodes,
    edges: edgesWithin,
    totalSelectedNodes: selectedNodes.length,
    totalSelectedEdges: edgesWithin.length,
  }
}

// Deterministic Mermaid-source projection. Derived presentation only: stable
// internal aliases, escaped untrusted labels, explicit truncation/subset state
// and visual separation of review inference from verified source linkage. No
// hidden instructions derived from source content are ever emitted.
export function renderContextGraphMermaid(
  projection: RepositoryContextProjection,
  options: { nodeLimit?: number; edgeLimit?: number; direction?: "LR" | "TD" } = {},
): { mermaid: string; aliases: Record<string, string>; truncated: boolean } {
  const nodeLimit = Math.min(Math.max(1, options.nodeLimit ?? DEFAULT_VIEW_NODES), MAX_VIEW_NODES)
  const edgeLimit = Math.min(Math.max(1, options.edgeLimit ?? DEFAULT_VIEW_EDGES), MAX_VIEW_EDGES)
  const direction = options.direction === "TD" ? "TD" : "LR"

  const availableNodes = projection.nodes.length
  const viewNodes = projection.nodes.slice(0, nodeLimit)
  const includedIds = new Set(viewNodes.map((node) => node.nodeId))
  const edgesWithinView = projection.edges.filter(
    (edge) => includedIds.has(edge.sourceNodeId) && includedIds.has(edge.targetNodeId),
  )
  const viewEdges = edgesWithinView.slice(0, edgeLimit)

  const truncated =
    projection.bounds.truncated || availableNodes > viewNodes.length || edgesWithinView.length > viewEdges.length

  const aliases: Record<string, string> = {}
  viewNodes.forEach((node, index) => {
    aliases[node.nodeId] = `n${index}`
  })

  const escapeLabel = (text: string): string => {
    const flattened = text.replace(/[\u0000-\u001f\u007f\u2028\u2029]+/g, " ")
    const escaped = flattened
      .replace(/\\/g, "\\\\")
      .replace(/"/g, "#quot;")
      .replace(/</g, "#lt;")
      .replace(/>/g, "#gt;")
      .replace(/&/g, "#amp;")
      .replace(/`/g, "'")
      .replace(/[{}[\]]/g, "()")
    return escaped.length > MERMAID_LABEL_CLAMP ? `${escaped.slice(0, MERMAID_LABEL_CLAMP)}...` : escaped
  }
  const escapeComment = (text: string): string =>
    text.replace(/[\u0000-\u001f\u007f\u2028\u2029]+/g, " ").replace(/[%]/g, "").slice(0, 200)

  const lines: string[] = []
  lines.push("%% CodeSleuth repository context graph (derived, bounded presentation; not evidence)")
  lines.push(`%% projectionId: ${projection.projectionId}`)
  lines.push(`%% headSha: ${projection.headSha}`)
  lines.push(`%% scope: ${escapeComment(projection.scope.prefix || ".")}`)
  if (projection.scope.description) lines.push(`%% scopeNote: ${escapeComment(projection.scope.description)}`)
  lines.push(`flowchart ${direction}`)
  lines.push("  classDef csInference stroke-dasharray: 4 4")

  const inferenceNodeAliases: string[] = []
  for (const node of viewNodes) {
    const alias = aliases[node.nodeId]
    const display = escapeLabel(node.label ? `${node.kind}: ${node.label}` : semanticElementName(node.kind, node.key))
    lines.push(`  ${alias}["${display}"]`)
    if (node.origin === "review_inference") inferenceNodeAliases.push(alias)
  }

  const inferenceLinkIndices: number[] = []
  viewEdges.forEach((edge, index) => {
    const sourceAlias = aliases[edge.sourceNodeId]
    const targetAlias = aliases[edge.targetNodeId]
    lines.push(`  ${sourceAlias} -->|"${escapeLabel(edge.relation)}"| ${targetAlias}`)
    if (edge.origin === "review_inference") inferenceLinkIndices.push(index)
  })

  if (inferenceNodeAliases.length > 0) lines.push(`  class ${inferenceNodeAliases.join(",")} csInference`)
  if (inferenceLinkIndices.length > 0) lines.push(`  linkStyle ${inferenceLinkIndices.join(",")} stroke-dasharray: 6 6`)

  if (truncated) {
    lines.push(
      `  trunc0[\\"${escapeLabel(
        `bounded subset: showing ${viewNodes.length} of ${availableNodes} nodes and ${viewEdges.length} of ${edgesWithinView.length} links`,
      )}"/]`,
    )
    lines.push("  %% Bounded view: request a scoped repo_context_graph_query for other neighborhoods.")
  }
  lines.push("  %% Legend: solid = verified_source linkage; dashed = review_inference (not verified evidence).")

  return { mermaid: `${lines.join("\n")}\n`, aliases, truncated }
}

const nodeInputShape = {
  kind: tool.schema.enum(NODE_KINDS),
  key: tool.schema.string().min(1).max(KEY_MAX),
  label: tool.schema.string().max(LABEL_MAX).optional(),
  origin: tool.schema
    .enum(ELEMENT_ORIGINS)
    .describe("verified_source requires path; review_inference requires a non-empty note and must not carry path"),
  path: tool.schema
    .string()
    .min(1)
    .max(PATH_MAX)
    .optional()
    .describe("Required for verified_source nodes; must name a tracked file. Forbidden for review_inference nodes."),
  startLine: tool.schema
    .number()
    .int()
    .min(1)
    .optional()
    .describe("Optional 1-based source line. If endLine is omitted, the range is treated as this single line."),
  endLine: tool.schema
    .number()
    .int()
    .min(1)
    .optional()
    .describe("Optional inclusive end line. May only be supplied together with startLine."),
  note: tool.schema
    .string()
    .max(NOTE_MAX)
    .optional()
    .describe("Required and non-empty for review_inference nodes; optional annotation for verified_source nodes."),
}

const edgeInputShape = {
  relation: tool.schema
    .enum(EDGE_RELATIONS)
    .describe("review_inference origin must use relation=review_inference; that relation is reserved for review_inference origin"),
  origin: tool.schema
    .enum(ELEMENT_ORIGINS)
    .describe("verified_source requires path; review_inference requires relation=review_inference, a non-empty note, and no path"),
  sourceKind: tool.schema.enum(NODE_KINDS),
  sourceKey: tool.schema.string().min(1).max(KEY_MAX),
  targetKind: tool.schema.enum(NODE_KINDS),
  targetKey: tool.schema.string().min(1).max(KEY_MAX),
  path: tool.schema
    .string()
    .min(1)
    .max(PATH_MAX)
    .optional()
    .describe("Required for verified_source edges; must name a tracked file. Forbidden for review_inference edges."),
  startLine: tool.schema
    .number()
    .int()
    .min(1)
    .optional()
    .describe("Optional 1-based source line. If endLine is omitted, the range is treated as this single line."),
  endLine: tool.schema
    .number()
    .int()
    .min(1)
    .optional()
    .describe("Optional inclusive end line. May only be supplied together with startLine."),
  note: tool.schema
    .string()
    .max(NOTE_MAX)
    .optional()
    .describe("Required and non-empty for review_inference edges; optional annotation for verified_source edges."),
}

const rootInputShape = {
  kind: tool.schema.enum(NODE_KINDS),
  key: tool.schema.string().min(1).max(KEY_MAX),
}

export const save = tool({
  description:
    "Validate and optionally persist a bounded, rebuildable RepositoryContextProjection under .opencode/state/context-graphs. Semantic validation is consolidated across all nodes/edges and reports indexed violations. Set validate_only=true for a no-write dry run. verified_source elements require tracked path evidence; review_inference nodes require notes and review_inference edges require relation=review_inference plus notes.",
  args: {
    reviewId: tool.schema.string().optional().describe("Review checkpoint to bind this projection to"),
    scopePrefix: tool.schema.string().optional().describe("Tracked path prefix this map covers"),
    scopeDescription: tool.schema.string().max(DESCRIPTION_MAX).optional(),
    complete: tool.schema
      .boolean()
      .optional()
      .describe("Assert the saved map deliberately covers the full requested scope (default false: treated as a bounded subset)"),
    note: tool.schema.string().max(NOTE_MAX).optional().describe("Bounds/coverage note recorded on the projection"),
    validate_only: tool.schema
      .boolean()
      .optional()
      .describe("Dry-run semantic validation only. Returns every indexed violation and never writes projection or pointer state."),
    nodes: tool.schema
      .array(tool.schema.object(nodeInputShape))
      .max(MAX_SAVE_NODES)
      .describe("Context nodes. Semantic constraints are validated together and returned as nodes[index] violations."),
    edges: tool.schema
      .array(tool.schema.object(edgeInputShape))
      .max(MAX_SAVE_EDGES)
      .describe("Context edges. Semantic constraints are validated together and returned as edges[index] violations."),
  },
  async execute(args, context) {
    const root = context.worktree
    const violations: ValidationViolation[] = []

    if (args.reviewId !== undefined && !ID_RE.test(args.reviewId)) {
      violations.push({ path: "reviewId", message: "invalid review id" })
    }

    let scopePrefix = ""
    try {
      scopePrefix = normalizeScopePrefix(args.scopePrefix)
    } catch (error) {
      violations.push({ path: "scopePrefix", message: errorMessage(error) })
    }

    let scopeDescription: string | undefined
    try {
      scopeDescription = cleanOptionalText(args.scopeDescription, "scope description", DESCRIPTION_MAX)
    } catch (error) {
      violations.push({ path: "scopeDescription", message: errorMessage(error) })
    }

    let boundsNote: string | undefined
    try {
      boundsNote = cleanOptionalText(args.note, "bounds note", NOTE_MAX)
    } catch (error) {
      violations.push({ path: "note", message: errorMessage(error) })
    }

    const headSha = (await git(root, ["rev-parse", "HEAD"])).trim()
    const nodes = await materializeNodes(root, args.nodes ?? [], violations)
    const edges = await materializeEdges(root, args.edges ?? [], nodes, violations)

    if (violations.length > 0) {
      if (args.validate_only) {
        return JSON.stringify(
          {
            valid: false,
            validationOnly: true,
            wroteState: false,
            violationCount: violations.length,
            violations,
          },
          null,
          2,
        )
      }
      throw new Error(formatValidationFailure(violations))
    }

    const now = new Date().toISOString()
    const projectionId = projectionIdentity({
      headSha,
      reviewId: args.reviewId,
      scopePrefix,
      nodeIds: [...nodes.keys()],
      edgeIds: [...edges.keys()],
    })
    const file = path.join(baseDir(root), `${projectionId.slice("sha256:".length)}.json`)
    const previousRaw = args.validate_only ? undefined : await readOptional(file)
    const createdAt = previousRaw ? JSON.parse(previousRaw).createdAt ?? now : now

    const projection: RepositoryContextProjection = {
      schemaVersion: CONTEXT_GRAPH_SCHEMA_VERSION,
      projectionId,
      headSha,
      ...(args.reviewId ? { reviewId: args.reviewId } : {}),
      createdAt,
      updatedAt: now,
      scope: {
        ...(scopePrefix ? { prefix: scopePrefix } : {}),
        ...(scopeDescription ? { description: scopeDescription } : {}),
      },
      nodes: [...nodes.values()].sort((a, b) => a.nodeId.localeCompare(b.nodeId)),
      edges: [...edges.values()].sort((a, b) => a.edgeId.localeCompare(b.edgeId)),
      bounds: {
        nodeLimit: MAX_SAVE_NODES,
        edgeLimit: MAX_SAVE_EDGES,
        truncated: !Boolean(args.complete),
        ...(boundsNote ? { note: boundsNote } : {}),
      },
    }
    validateProjection(projection)

    if (args.validate_only) {
      return JSON.stringify(
        {
          valid: true,
          validationOnly: true,
          wroteState: false,
          violationCount: 0,
          violations: [],
          projectionId,
          headSha,
          nodeCount: projection.nodes.length,
          edgeCount: projection.edges.length,
          truncated: projection.bounds.truncated,
          reviewId: args.reviewId,
        },
        null,
        2,
      )
    }

    await atomicWrite(file, `${JSON.stringify(projection, null, 2)}\n`)

    const dir = baseDir(root)
    await atomicWrite(path.join(dir, "sessions", `${safeStateName(context.sessionID)}.txt`), `${projectionId}\n`)
    await atomicWrite(path.join(dir, "latest.txt"), `${projectionId}\n`)
    if (args.reviewId) {
      await mkdir(path.join(dir, "reviews"), { recursive: true })
      await atomicWrite(path.join(dir, "reviews", `${args.reviewId}.txt`), `${projectionId}\n`)
    }

    return JSON.stringify(
      {
        projectionId,
        headSha,
        savedPath: path.relative(root, file).replace(/\\/g, "/"),
        nodeCount: projection.nodes.length,
        edgeCount: projection.edges.length,
        truncated: projection.bounds.truncated,
        reviewId: args.reviewId,
        note: "bounded derived context state; reopen exact source before treating any linkage as finding evidence",
      },
      null,
      2,
    )
  },
})

export const load = tool({
  description:
    "Load a bounded RepositoryContextProjection by id, linked review checkpoint, current session, or latest; verifies identity integrity and reports stale verified linkage against current Git blobs. Model-visible preview is bounded with explicit truncation.",
  args: {
    projectionId: tool.schema.string().optional(),
    reviewId: tool.schema.string().optional(),
    nodeLimit: tool.schema.number().int().min(1).max(MAX_VIEW_NODES).optional(),
    edgeLimit: tool.schema.number().int().min(1).max(MAX_VIEW_EDGES).optional(),
  },
  async execute(args, context) {
    const root = context.worktree
    const resolution = args.projectionId || args.reviewId
      ? await resolveProjectionFile(root, { projectionId: args.projectionId, reviewId: args.reviewId })
      : await resolveDefaultProjectionFile(root, context.sessionID)
    const projection = await loadProjectionByFile(resolution.file)
    const freshness = await freshnessAudit(root, projection)

    const nodeLimit = Math.min(args.nodeLimit ?? DEFAULT_VIEW_NODES, MAX_VIEW_NODES)
    const edgeLimit = Math.min(args.edgeLimit ?? DEFAULT_VIEW_EDGES, MAX_VIEW_EDGES)
    const previewNodes = projection.nodes.slice(0, nodeLimit)
    const previewEdges = projection.edges.slice(0, edgeLimit)

    return JSON.stringify(
      {
        resolvedVia: resolution.resolvedVia,
        projectionId: projection.projectionId,
        headSha: projection.headSha,
        reviewId: projection.reviewId,
        scope: projection.scope,
        bounds: projection.bounds,
        counts: { nodes: projection.nodes.length, edges: projection.edges.length },
        freshness: {
          currentHeadSha: freshness.currentHeadSha,
          headChanged: freshness.headChanged,
          staleLinkageCount: freshness.staleLinkage.length,
          staleLinkage: freshness.staleLinkage.slice(0, 20),
        },
        preview: {
          truncated:
            projection.bounds.truncated || previewNodes.length < projection.nodes.length || previewEdges.length < projection.edges.length,
          nodes: previewNodes.map(compactNode),
          edges: previewEdges.map((edge) => compactEdge(projection, edge)),
        },
        reminder: "derived navigation context only; exact source evidence must still be reopened for material findings",
      },
      null,
      2,
    )
  },
})

export const query = tool({
  description:
    "Bounded neighborhood query over the saved RepositoryContextProjection. Returns compact adjacency within strict node/edge limits with explicit truncation and a continuation cursor; never returns the complete repository map unbounded.",
  args: {
    projectionId: tool.schema.string().optional(),
    reviewId: tool.schema.string().optional(),
    roots: tool.schema
      .array(tool.schema.object(rootInputShape))
      .max(20)
      .optional()
      .describe("Semantic roots to expand from; omit to walk the saved map in deterministic order"),
    hops: tool.schema.number().int().min(0).max(MAX_HOPS).optional(),
    relation: tool.schema.enum(EDGE_RELATIONS).optional().describe("Only traverse edges with this relation"),
    origin: tool.schema.enum(ELEMENT_ORIGINS).optional().describe("Only traverse edges with this origin"),
    nodeLimit: tool.schema.number().int().min(1).max(MAX_VIEW_NODES).optional(),
    edgeLimit: tool.schema.number().int().min(1).max(MAX_VIEW_EDGES).optional(),
    cursor: tool.schema.string().max(200).optional().describe("Continuation cursor from a previous bounded query"),
  },
  async execute(args, context) {
    const root = context.worktree
    const resolution = args.projectionId || args.reviewId
      ? await resolveProjectionFile(root, { projectionId: args.projectionId, reviewId: args.reviewId })
      : await resolveDefaultProjectionFile(root, context.sessionID)
    const projection = await loadProjectionByFile(resolution.file)
    const selection = selectNeighborhood(projection, {
      roots: args.roots,
      hops: args.hops ?? 1,
      relationFilter: args.relation,
      originFilter: args.origin,
    })

    const { nodeOffset, edgeOffset } = parseCursor(args.cursor)
    const nodeLimit = Math.min(args.nodeLimit ?? DEFAULT_VIEW_NODES, MAX_VIEW_NODES)
    const edgeLimit = Math.min(args.edgeLimit ?? DEFAULT_VIEW_EDGES, MAX_VIEW_EDGES)
    const windowNodes = selection.nodes.slice(nodeOffset, nodeOffset + nodeLimit)
    const windowEdges = selection.edges.slice(edgeOffset, edgeOffset + edgeLimit)
    const moreNodes = nodeOffset + windowNodes.length < selection.totalSelectedNodes
    const moreEdges = edgeOffset + windowEdges.length < selection.totalSelectedEdges

    const includedIds = new Set(windowNodes.map((node) => node.nodeId))
    const visibleEdges = windowEdges.filter(
      (edge) => includedIds.has(edge.sourceNodeId) && includedIds.has(edge.targetNodeId),
    )
    const windowExceedsLimits = moreNodes || moreEdges

    return JSON.stringify(
      {
        projectionId: projection.projectionId,
        headSha: projection.headSha,
        savedMapTruncatedByAuthor: projection.bounds.truncated,
        returnedNodes: windowNodes.map(compactNode),
        returnedEdges: visibleEdges.map((edge) => compactEdge(projection, edge)),
        totalsForSelection: { nodes: selection.totalSelectedNodes, edges: selection.totalSelectedEdges },
        limits: { nodeLimit, edgeLimit },
        truncated: windowExceedsLimits || projection.bounds.truncated,
        fullyComplete: !windowExceedsLimits && !projection.bounds.truncated,
        nextCursor: windowExceedsLimits
          ? `v1:${nodeOffset + windowNodes.length}:${edgeOffset + windowEdges.length}`
          : undefined,
        reminder: "graph relations are navigation/context, not sufficient finding evidence",
      },
      null,
      2,
    )
  },
})

export const mermaid = tool({
  description:
    "Render deterministic Mermaid flowchart SOURCE derived from the saved RepositoryContextProjection (stable aliases, escaped labels, explicit subset/truncation state, dashed review-inference styling). Text output only; never invokes mmdc/Chromium and never produces SVG.",
  args: {
    projectionId: tool.schema.string().optional(),
    reviewId: tool.schema.string().optional(),
    direction: tool.schema.enum(["LR", "TD"]).optional(),
    nodeLimit: tool.schema.number().int().min(1).max(MAX_VIEW_NODES).optional(),
    edgeLimit: tool.schema.number().int().min(1).max(MAX_VIEW_EDGES).optional(),
  },
  async execute(args, context) {
    const root = context.worktree
    const resolution = args.projectionId || args.reviewId
      ? await resolveProjectionFile(root, { projectionId: args.projectionId, reviewId: args.reviewId })
      : await resolveDefaultProjectionFile(root, context.sessionID)
    const projection = await loadProjectionByFile(resolution.file)
    const rendered = renderContextGraphMermaid(projection, {
      nodeLimit: args.nodeLimit,
      edgeLimit: args.edgeLimit,
      direction: args.direction,
    })
    return JSON.stringify(
      {
        derivedFrom: {
          projectionId: projection.projectionId,
          headSha: projection.headSha,
          schemaVersion: CONTEXT_GRAPH_SCHEMA_VERSION,
        },
        truncated: rendered.truncated,
        aliasCount: Object.keys(rendered.aliases).length,
        aliasesArePresentationOnly: true,
        renderingDeferred: "SVG/mmdc rendering is intentionally out of scope; consume this Mermaid source directly",
        mermaidSource: rendered.mermaid,
      },
      null,
      2,
    )
  },
})
