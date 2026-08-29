import { randomUUID } from "node:crypto"
import path from "node:path"

import { tool } from "@opencode-ai/plugin"

import { get as contextGet } from "./codesleuth_context"
import { load as ehaLoad, mermaid as ehaMermaid } from "./eha_state"
import { writeGraphExportBundle, type GraphExportEnvelope, type GraphExportView } from "./export_bundle"
import { mermaid as protectedMermaid, query as protectedQuery } from "./protected_capability_graph"
import { EDGE_RELATIONS, ELEMENT_ORIGINS, NODE_KINDS } from "./repo_context_graph"

type ToolContext = {
  worktree: string
  directory: string
  sessionID: string
  messageID: string
  agent: string
}

const SAFE_NAME_RE = /^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$/
const PYTHON_RUNTIME_ENV = "CODESLEUTH_PYTHON_EXECUTABLE"

function parseToolJson(value: unknown, label: string): any {
  if (typeof value !== "string") throw new Error(`${label} returned a non-text response`)
  try {
    return JSON.parse(value)
  } catch {
    throw new Error(`${label} returned invalid JSON`)
  }
}

function shortIdentity(value: unknown): string {
  const normalized = String(value ?? "export").replace(/^sha256:/, "").replace(/[^A-Za-z0-9]/g, "")
  return (normalized || "export").slice(0, 16)
}

function bundleName(view: GraphExportView, explicit: string | undefined, identity: unknown): string {
  if (explicit !== undefined) {
    if (!SAFE_NAME_RE.test(explicit) || explicit === "." || explicit === "..") {
      throw new Error("bundleName must be 1..120 safe filename characters")
    }
    return explicit
  }
  const stamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)
  return `${view}-${shortIdentity(identity)}-${stamp}-${randomUUID().slice(0, 8)}`
}

function rendererScript(): string {
  return path.resolve(import.meta.dir, "..", "bin", "codesleuth_export.py")
}

function pythonRuntime(): string {
  const configured = process.env[PYTHON_RUNTIME_ENV]?.trim()
  if (!configured) {
    throw new Error(`${PYTHON_RUNTIME_ENV} must name the explicit Python interpreter used for SVG export`)
  }
  if (!path.isAbsolute(configured)) {
    throw new Error(`${PYTHON_RUNTIME_ENV} must be an absolute interpreter path`)
  }
  return configured
}

function assertProtectedSnapshot(machinePayload: any, envelope: any): void {
  const machine = machinePayload?.provenance
  const presentation = envelope?.provenance
  if (
    !machine ||
    !presentation ||
    machine.path !== presentation.path ||
    machine.indexBlob !== presentation.indexBlob ||
    machine.workingBlob !== presentation.workingBlob ||
    machine.contentSha256 !== presentation.contentSha256
  ) {
    throw new Error("protected capability authority changed between machine query and Mermaid render")
  }
}

function assertEhaSnapshot(machinePayload: any, envelope: any): void {
  const provenance = envelope?.provenance
  if (
    !provenance ||
    machinePayload?.reviewId !== provenance.reviewId ||
    machinePayload?.eventCount !== provenance.eventCount
  ) {
    throw new Error("EHA ledger changed between machine load and Mermaid render")
  }
}

async function renderSvg(mermaidSource: string, outputPath: string) {
  const proc = Bun.spawn([pythonRuntime(), rendererScript(), "mermaid-svg", "--output", outputPath], {
    stdin: "pipe",
    stdout: "pipe",
    stderr: "pipe",
  })
  proc.stdin.write(mermaidSource)
  proc.stdin.end()
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  const code = await proc.exited
  let result: any
  try {
    result = JSON.parse(stdout)
  } catch {
    throw new Error(`Mermaid SVG exporter returned invalid JSON: ${stderr || stdout}`)
  }
  if (code !== 0 || result?.status !== "pass" || result?.retained !== true) {
    throw new Error(result?.error || stderr.trim() || "Mermaid SVG export failed")
  }
  return result
}

async function persist(
  context: ToolContext,
  input: {
    view: GraphExportView
    bundleName?: string
    identity: unknown
    machinePayload: unknown
    machinePayloadRole: string
    envelope: GraphExportEnvelope
    includeSvg?: boolean
  },
) {
  return writeGraphExportBundle({
    root: context.worktree,
    bundleName: bundleName(input.view, input.bundleName, input.identity),
    view: input.view,
    machinePayload: input.machinePayload,
    machinePayloadRole: input.machinePayloadRole,
    mermaidEnvelope: input.envelope,
    ...(input.includeSvg ? { renderSvg } : {}),
  })
}

const rootInputShape = {
  kind: tool.schema.enum(NODE_KINDS),
  key: tool.schema.string().min(1).max(300),
}

export const repository_graph = tool({
  description:
    "Explicitly retain a repository-context export bundle under ignored .codesleuth/exports/graphs. Uses codesleuth_context_get as the exact-head machine source and writes graph.json + graph.mmd, with optional pinned Mermaid SVG rendering. Export copies are presentation/navigation artifacts and never evidence authority.",
  args: {
    expectedHeadSha: tool.schema.string().optional(),
    projectionId: tool.schema.string().optional(),
    reviewId: tool.schema.string().optional(),
    roots: tool.schema.array(tool.schema.object(rootInputShape)).max(20).optional(),
    hops: tool.schema.number().int().min(0).max(3).optional(),
    relation: tool.schema.enum(EDGE_RELATIONS).optional(),
    origin: tool.schema.enum(ELEMENT_ORIGINS).optional(),
    nodeLimit: tool.schema.number().int().min(1).max(200).optional(),
    edgeLimit: tool.schema.number().int().min(1).max(300).optional(),
    direction: tool.schema.enum(["LR", "TD"]).optional(),
    bundleName: tool.schema.string().max(120).optional(),
    includeSvg: tool.schema.boolean().optional().describe("Render retained graph.svg with the exact-pinned optional Mermaid runtime"),
  },
  async execute(args, context: ToolContext) {
    const capsule = parseToolJson(
      await contextGet.execute(
        {
          ...(args.expectedHeadSha ? { expectedHeadSha: args.expectedHeadSha } : {}),
          ...(args.projectionId ? { projectionId: args.projectionId } : {}),
          ...(args.reviewId ? { reviewId: args.reviewId } : {}),
          ...(args.roots ? { roots: args.roots } : {}),
          ...(args.hops !== undefined ? { hops: args.hops } : {}),
          ...(args.relation ? { relation: args.relation } : {}),
          ...(args.origin ? { origin: args.origin } : {}),
          ...(args.nodeLimit !== undefined ? { nodeLimit: args.nodeLimit } : {}),
          ...(args.edgeLimit !== undefined ? { edgeLimit: args.edgeLimit } : {}),
          ...(args.direction ? { direction: args.direction } : {}),
          includeMermaid: true,
        },
        context,
      ),
      "codesleuth_context_get",
    )
    if (capsule?.target?.exactHeadMatch !== true || capsule?.freshness?.staleLinkageCount !== 0) {
      throw new Error("repository export requires a fresh exact-head context capsule")
    }
    if (capsule?.mermaid?.role !== "secondary-derived-presentation" || typeof capsule?.mermaid?.mermaidSource !== "string") {
      throw new Error("exact-head context capsule did not return the required secondary Mermaid presentation")
    }
    const envelope: GraphExportEnvelope = {
      schemaVersion: 1,
      view: "repository_context",
      authority: {
        kind: "exact_head_context_capsule",
        statement: "tracked Git source + blob identity remain source authority; export is retained derived presentation only",
      },
      provenance: {
        projectionId: capsule.target.projectionId,
        headSha: capsule.target.currentHeadSha,
        reviewId: capsule.reviewId ?? null,
      },
      selection: {
        scope: capsule.scope,
        totalsForSelection: capsule.adjacency?.totalsForSelection ?? null,
        limits: capsule.adjacency?.limits ?? null,
      },
      truncated: capsule.coverage?.truncated === true,
      derivedPresentationOnly: true,
      mermaidSource: capsule.mermaid.mermaidSource,
    }
    return JSON.stringify(
      await persist(context, {
        view: "repository_context",
        bundleName: args.bundleName,
        identity: capsule.target.projectionId,
        machinePayload: capsule,
        machinePayloadRole: "bounded_exact_head_context_capsule",
        envelope,
        includeSvg: args.includeSvg,
      }),
      null,
      2,
    )
  },
})

const protectedSelectionArgs = {
  contractIds: tool.schema.array(tool.schema.string()).max(20).optional(),
  includeDependencies: tool.schema.boolean().optional(),
  includeConsumers: tool.schema.boolean().optional(),
  contractLimit: tool.schema.number().int().min(1).max(50).optional(),
}

export const protected_graph = tool({
  description:
    "Explicitly retain a protected-capability graph export under ignored .codesleuth/exports/graphs. The tracked protected-capability registry remains authority; the export bundle is a bounded retained copy only.",
  args: {
    ...protectedSelectionArgs,
    direction: tool.schema.enum(["LR", "TD"]).optional(),
    bundleName: tool.schema.string().max(120).optional(),
    includeSvg: tool.schema.boolean().optional(),
  },
  async execute(args, context: ToolContext) {
    const selectionArgs = {
      ...(args.contractIds ? { contractIds: args.contractIds } : {}),
      ...(args.includeDependencies !== undefined ? { includeDependencies: args.includeDependencies } : {}),
      ...(args.includeConsumers !== undefined ? { includeConsumers: args.includeConsumers } : {}),
      ...(args.contractLimit !== undefined ? { contractLimit: args.contractLimit } : {}),
    }
    const machinePayload = parseToolJson(
      await protectedQuery.execute(selectionArgs, context),
      "protected_capability_graph_query",
    )
    const envelope = parseToolJson(
      await protectedMermaid.execute(
        { ...selectionArgs, ...(args.direction ? { direction: args.direction } : {}) },
        context,
      ),
      "protected_capability_graph_mermaid",
    ) as GraphExportEnvelope
    if (envelope.view !== "protected_capability_impact" || envelope.derivedPresentationOnly !== true) {
      throw new Error("protected-capability Mermaid envelope lost derived-presentation authority metadata")
    }
    assertProtectedSnapshot(machinePayload, envelope)
    return JSON.stringify(
      await persist(context, {
        view: "protected_capability_impact",
        bundleName: args.bundleName,
        identity: (envelope as any)?.provenance?.contentSha256,
        machinePayload: machinePayload,
        machinePayloadRole: "bounded_tracked_registry_selection",
        envelope,
        includeSvg: args.includeSvg,
      }),
      null,
      2,
    )
  },
})

export const eha_graph = tool({
  description:
    "Explicitly retain an EHA lineage graph export under ignored .codesleuth/exports/graphs. eha.ndjson remains append-only acceptance authority; the retained graph and SVG are derived presentation only.",
  args: {
    reviewId: tool.schema.string().optional(),
    campaignLimit: tool.schema.number().int().min(1).max(50).optional(),
    repairLimit: tool.schema.number().int().min(1).max(50).optional(),
    direction: tool.schema.enum(["LR", "TD"]).optional(),
    bundleName: tool.schema.string().max(120).optional(),
    includeSvg: tool.schema.boolean().optional(),
  },
  async execute(args, context: ToolContext) {
    const selector = { ...(args.reviewId ? { reviewId: args.reviewId } : {}) }
    const machinePayload = parseToolJson(await ehaLoad.execute(selector, context), "eha_state_load")
    const envelope = parseToolJson(
      await ehaMermaid.execute(
        {
          ...selector,
          ...(args.campaignLimit !== undefined ? { campaignLimit: args.campaignLimit } : {}),
          ...(args.repairLimit !== undefined ? { repairLimit: args.repairLimit } : {}),
          ...(args.direction ? { direction: args.direction } : {}),
          responseFormat: "json",
        },
        context,
      ),
      "eha_state_mermaid",
    ) as GraphExportEnvelope
    if (envelope.view !== "eha_state" || envelope.derivedPresentationOnly !== true) {
      throw new Error("EHA Mermaid envelope lost derived-presentation authority metadata")
    }
    assertEhaSnapshot(machinePayload, envelope)
    return JSON.stringify(
      await persist(context, {
        view: "eha_state",
        bundleName: args.bundleName,
        identity: (envelope as any)?.provenance?.contentSha256,
        machinePayload: machinePayload,
        machinePayloadRole: "durable_eha_ledger_summary",
        envelope,
        includeSvg: args.includeSvg,
      }),
      null,
      2,
    )
  },
})
