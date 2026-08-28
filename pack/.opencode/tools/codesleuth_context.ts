import { tool } from "@opencode-ai/plugin"
import { readFile } from "node:fs/promises"
import path from "node:path"

import {
  EDGE_RELATIONS,
  ELEMENT_ORIGINS,
  NODE_KINDS,
  load as contextGraphLoad,
  mermaid as contextGraphMermaid,
  query as contextGraphQuery,
  type ContextEdge,
  type ContextNode,
  type RepositoryContextProjection,
} from "./repo_context_graph"

const CAPSULE_VERSION = 1
const EXACT_GIT_SHA_RE = /^(?:[0-9a-f]{40}|[0-9a-f]{64})$/
const PROJECTION_ID_RE = /^sha256:[0-9a-f]{64}$/
const MAX_HOPS = 3
const MAX_VIEW_NODES = 200
const MAX_VIEW_EDGES = 300

type ToolContext = {
  worktree: string
  directory: string
  sessionID: string
  messageID: string
  agent: string
}

function parseToolJson(value: unknown, label: string): any {
  if (typeof value !== "string") throw new Error(`${label} returned a non-text response`)
  try {
    return JSON.parse(value)
  } catch {
    throw new Error(`${label} returned invalid JSON`)
  }
}

function projectionPath(root: string, projectionId: string): string {
  if (!PROJECTION_ID_RE.test(projectionId)) throw new Error(`invalid projection id: ${projectionId}`)
  return path.join(root, ".opencode", "state", "context-graphs", `${projectionId.slice("sha256:".length)}.json`)
}

function compactNode(node: ContextNode): string {
  const label = node.label ? ` (${node.label})` : ""
  const inference = node.origin === "review_inference" ? " [inference]" : ""
  return `${node.kind}:${node.key}${label}${inference}`
}

function compactEdge(projection: RepositoryContextProjection, edge: ContextEdge): string {
  const byId = new Map(projection.nodes.map((node) => [node.nodeId, node]))
  const source = byId.get(edge.sourceNodeId)
  const target = byId.get(edge.targetNodeId)
  if (!source || !target) throw new Error(`projection edge ${edge.edgeId} references a missing node`)
  const inference = edge.origin === "review_inference" ? " [inference]" : ""
  return `${compactNode(source)} -[${edge.relation}]-> ${compactNode(target)}${inference}`
}

function structuredWindow(
  projection: RepositoryContextProjection,
  returnedNodes: string[],
  returnedEdges: string[],
): { nodes: any[]; edges: any[] } {
  const nodesByCompact = new Map<string, ContextNode>()
  for (const node of projection.nodes) {
    const key = compactNode(node)
    if (nodesByCompact.has(key)) throw new Error(`ambiguous compact node representation: ${key}`)
    nodesByCompact.set(key, node)
  }

  const edgesByCompact = new Map<string, ContextEdge>()
  for (const edge of projection.edges) {
    const key = compactEdge(projection, edge)
    if (edgesByCompact.has(key)) throw new Error(`ambiguous compact edge representation: ${key}`)
    edgesByCompact.set(key, edge)
  }

  const nodes = returnedNodes.map((key) => {
    const node = nodesByCompact.get(key)
    if (!node) throw new Error(`canonical query returned an unknown node: ${key}`)
    return {
      nodeId: node.nodeId,
      kind: node.kind,
      key: node.key,
      origin: node.origin,
      ...(node.label ? { label: node.label } : {}),
      ...(node.sourceRef ? { sourceRef: node.sourceRef } : {}),
      ...(node.note ? { note: node.note } : {}),
    }
  })

  const byId = new Map(projection.nodes.map((node) => [node.nodeId, node]))
  const edges = returnedEdges.map((key) => {
    const edge = edgesByCompact.get(key)
    if (!edge) throw new Error(`canonical query returned an unknown edge: ${key}`)
    const source = byId.get(edge.sourceNodeId)
    const target = byId.get(edge.targetNodeId)
    if (!source || !target) throw new Error(`projection edge ${edge.edgeId} references a missing node`)
    return {
      edgeId: edge.edgeId,
      relation: edge.relation,
      origin: edge.origin,
      source: { nodeId: source.nodeId, kind: source.kind, key: source.key },
      target: { nodeId: target.nodeId, kind: target.kind, key: target.key },
      ...(edge.sourceRef ? { sourceRef: edge.sourceRef } : {}),
      ...(edge.note ? { note: edge.note } : {}),
    }
  })

  return { nodes, edges }
}

const rootInputShape = {
  kind: tool.schema.enum(NODE_KINDS),
  key: tool.schema.string().min(1).max(300),
}

export const get = tool({
  description:
    "Return a strict exact-head context capsule for selected coding/review agents. The capsule reuses repo_context_graph_load for integrity/freshness and repo_context_graph_query for the canonical bounded neighborhood selection, then exposes structured SourceRefs for the returned window. Mermaid is optional secondary presentation only.",
  args: {
    expectedHeadSha: tool.schema
      .string()
      .optional()
      .describe("Optional exact current Git SHA expected by the caller; mismatches fail closed"),
    projectionId: tool.schema.string().optional(),
    reviewId: tool.schema.string().optional(),
    roots: tool.schema.array(tool.schema.object(rootInputShape)).max(20).optional(),
    hops: tool.schema.number().int().min(0).max(MAX_HOPS).optional(),
    relation: tool.schema.enum(EDGE_RELATIONS).optional(),
    origin: tool.schema.enum(ELEMENT_ORIGINS).optional(),
    nodeLimit: tool.schema.number().int().min(1).max(MAX_VIEW_NODES).optional(),
    edgeLimit: tool.schema.number().int().min(1).max(MAX_VIEW_EDGES).optional(),
    cursor: tool.schema.string().max(200).optional(),
    includeMermaid: tool.schema
      .boolean()
      .optional()
      .describe("Attach bounded Mermaid source for the same selection. Forbidden together with a continuation cursor."),
    direction: tool.schema.enum(["LR", "TD"]).optional(),
  },
  async execute(args, context: ToolContext) {
    if (args.expectedHeadSha && !EXACT_GIT_SHA_RE.test(args.expectedHeadSha)) {
      throw new Error("expectedHeadSha must be one exact lowercase 40- or 64-hex Git object id")
    }
    if (args.includeMermaid && args.cursor) {
      throw new Error("includeMermaid cannot be combined with a continuation cursor; Mermaid has no cursor window contract")
    }

    const selector = {
      ...(args.projectionId ? { projectionId: args.projectionId } : {}),
      ...(args.reviewId ? { reviewId: args.reviewId } : {}),
    }
    const loaded = parseToolJson(await contextGraphLoad.execute(selector, context), "repo_context_graph_load")
    const currentHeadSha = loaded?.freshness?.currentHeadSha
    if (typeof currentHeadSha !== "string" || !EXACT_GIT_SHA_RE.test(currentHeadSha)) {
      throw new Error("context graph load did not return an exact current Git head")
    }
    if (args.expectedHeadSha && args.expectedHeadSha !== currentHeadSha) {
      throw new Error(`context capsule target drift: expected ${args.expectedHeadSha}, current HEAD is ${currentHeadSha}`)
    }
    if (loaded.headSha !== currentHeadSha || loaded?.freshness?.headChanged === true) {
      throw new Error(`context projection head ${loaded.headSha} does not match current HEAD ${currentHeadSha}`)
    }
    if (loaded?.freshness?.staleLinkageCount !== 0) {
      throw new Error(`context projection has ${loaded?.freshness?.staleLinkageCount ?? "unknown"} stale SourceRef link(s)`)
    }

    const queryArgs = {
      ...selector,
      ...(args.roots ? { roots: args.roots } : {}),
      ...(args.hops !== undefined ? { hops: args.hops } : {}),
      ...(args.relation ? { relation: args.relation } : {}),
      ...(args.origin ? { origin: args.origin } : {}),
      ...(args.nodeLimit !== undefined ? { nodeLimit: args.nodeLimit } : {}),
      ...(args.edgeLimit !== undefined ? { edgeLimit: args.edgeLimit } : {}),
      ...(args.cursor ? { cursor: args.cursor } : {}),
    }
    const queried = parseToolJson(await contextGraphQuery.execute(queryArgs, context), "repo_context_graph_query")
    if (queried.projectionId !== loaded.projectionId || queried.headSha !== currentHeadSha) {
      throw new Error("context graph changed between freshness validation and bounded query")
    }

    const raw = await readFile(projectionPath(context.worktree, loaded.projectionId), "utf8")
    const projection = JSON.parse(raw) as RepositoryContextProjection
    if (projection.projectionId !== loaded.projectionId || projection.headSha !== currentHeadSha) {
      throw new Error("persisted projection identity changed during context-capsule construction")
    }
    const adjacency = structuredWindow(
      projection,
      Array.isArray(queried.returnedNodes) ? queried.returnedNodes : [],
      Array.isArray(queried.returnedEdges) ? queried.returnedEdges : [],
    )

    let mermaid: any = undefined
    if (args.includeMermaid) {
      const mermaidArgs = {
        ...selector,
        ...(args.roots ? { roots: args.roots } : {}),
        ...(args.hops !== undefined ? { hops: args.hops } : {}),
        ...(args.relation ? { relation: args.relation } : {}),
        ...(args.origin ? { origin: args.origin } : {}),
        ...(args.nodeLimit !== undefined ? { nodeLimit: args.nodeLimit } : {}),
        ...(args.edgeLimit !== undefined ? { edgeLimit: args.edgeLimit } : {}),
        ...(args.direction ? { direction: args.direction } : {}),
      }
      const rendered = parseToolJson(
        await contextGraphMermaid.execute(mermaidArgs, context),
        "repo_context_graph_mermaid",
      )
      if (rendered?.derivedFrom?.projectionId !== loaded.projectionId || rendered?.derivedFrom?.headSha !== currentHeadSha) {
        throw new Error("Mermaid projection identity does not match the exact-head context capsule")
      }
      mermaid = {
        role: "secondary-derived-presentation",
        selection: rendered.selection,
        truncated: rendered.truncated,
        mermaidSource: rendered.mermaidSource,
      }
    }

    return JSON.stringify(
      {
        capsuleVersion: CAPSULE_VERSION,
        kind: "codesleuth-context-capsule",
        target: {
          currentHeadSha,
          projectionHeadSha: projection.headSha,
          projectionId: projection.projectionId,
          exactHeadMatch: true,
        },
        reviewId: loaded.reviewId,
        scope: {
          projection: loaded.scope,
          ...(args.roots ? { roots: args.roots } : {}),
          hops: args.hops ?? 1,
          ...(args.relation ? { relation: args.relation } : {}),
          ...(args.origin ? { origin: args.origin } : {}),
        },
        freshness: {
          strict: true,
          staleLinkageCount: 0,
        },
        adjacency: {
          nodes: adjacency.nodes,
          edges: adjacency.edges,
          totalsForSelection: queried.totalsForSelection,
          limits: queried.limits,
        },
        coverage: {
          savedMapTruncatedByAuthor: queried.savedMapTruncatedByAuthor,
          truncated: queried.truncated,
          fullyComplete: queried.fullyComplete,
          nextCursor: queried.nextCursor,
        },
        ...(mermaid ? { mermaid } : {}),
        policy: {
          sourceAuthority: "tracked Git source + blob identity",
          reviewAuthority: "review_state",
          projectionRole: "derived navigation/context",
          mermaidRole: "secondary derived presentation",
          reopenSourceBeforeEditOrFinding: true,
        },
      },
      null,
      2,
    )
  },
})
