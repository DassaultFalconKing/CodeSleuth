import { createHash, randomUUID } from "node:crypto"
import { lstat, mkdir, readFile, realpath, rename, rm, writeFile } from "node:fs/promises"
import path from "node:path"

export const GRAPH_EXPORT_SCHEMA_VERSION = 1
export const GRAPH_EXPORT_VIEWS = ["repository_context", "protected_capability_impact", "eha_state"] as const
export type GraphExportView = (typeof GRAPH_EXPORT_VIEWS)[number]

export type SvgRenderMetadata = {
  renderer: Record<string, unknown>
  [key: string]: unknown
}

export type GraphExportEnvelope = {
  schemaVersion: number
  view: GraphExportView
  authority: unknown
  provenance?: unknown
  selection?: unknown
  truncated?: boolean
  derivedPresentationOnly: true
  mermaidSource: string
}

type WriteGraphExportBundleInput = {
  root: string
  bundleName: string
  view: GraphExportView
  machinePayload: unknown
  machinePayloadRole: string
  mermaidEnvelope: GraphExportEnvelope
  exportedAt?: string
  renderSvg?: (mermaidSource: string, outputPath: string) => Promise<SvgRenderMetadata>
}

const NAME_RE = /^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$/

function sha256(data: string | Uint8Array): string {
  return createHash("sha256").update(data).digest("hex")
}

function byteLength(data: string | Uint8Array): number {
  return typeof data === "string" ? Buffer.byteLength(data, "utf8") : data.byteLength
}

function assertSafeName(value: string): void {
  if (!NAME_RE.test(value) || value === "." || value === "..") {
    throw new Error("export bundle name must be 1..120 safe filename characters")
  }
}

function assertEnvelope(input: WriteGraphExportBundleInput): void {
  const envelope = input.mermaidEnvelope
  if (envelope.schemaVersion !== 1) throw new Error("unsupported Mermaid export envelope schema")
  if (envelope.view !== input.view) throw new Error(`export view mismatch: ${envelope.view} != ${input.view}`)
  if (envelope.derivedPresentationOnly !== true) {
    throw new Error("refusing to export Mermaid without derivedPresentationOnly=true")
  }
  if (typeof envelope.mermaidSource !== "string" || !envelope.mermaidSource.trim()) {
    throw new Error("Mermaid export source must be non-empty text")
  }
}

export function graphExportRoot(root: string): string {
  return path.resolve(root, ".codesleuth", "exports", "graphs")
}

export function graphExportDirectory(root: string, bundleName: string): string {
  assertSafeName(bundleName)
  const base = graphExportRoot(root)
  const target = path.resolve(base, bundleName)
  if (!target.startsWith(`${base}${path.sep}`)) throw new Error("graph export path escapes .codesleuth/exports/graphs")
  return target
}

async function ensurePhysicalGraphExportRoot(root: string): Promise<{ physicalRoot: string; base: string }> {
  const physicalRoot = await realpath(root)
  let current = physicalRoot
  for (const segment of [".codesleuth", "exports", "graphs"]) {
    const next = path.join(current, segment)
    try {
      const info = await lstat(next)
      if (info.isSymbolicLink() || !info.isDirectory()) {
        throw new Error(`export path component must be a real directory, not a link or file: ${next}`)
      }
    } catch (error: any) {
      if (error?.code !== "ENOENT") throw error
      await mkdir(next)
      const info = await lstat(next)
      if (info.isSymbolicLink() || !info.isDirectory()) {
        throw new Error(`export path component changed during creation: ${next}`)
      }
    }
    const physical = await realpath(next)
    if (path.normalize(physical) !== path.normalize(next)) {
      throw new Error(`export path component resolves through a link: ${next} -> ${physical}`)
    }
    current = next
  }
  return { physicalRoot, base: current }
}

async function writeUtf8(file: string, content: string): Promise<void> {
  await writeFile(file, content, { encoding: "utf8", flag: "wx" })
}

export async function writeGraphExportBundle(input: WriteGraphExportBundleInput) {
  assertSafeName(input.bundleName)
  assertEnvelope(input)

  const { physicalRoot, base } = await ensurePhysicalGraphExportRoot(input.root)
  const finalDir = path.join(base, input.bundleName)
  try {
    await lstat(finalDir)
    throw new Error(`export bundle already exists: ${finalDir}`)
  } catch (error: any) {
    if (error?.code !== "ENOENT") throw error
  }
  const staging = path.join(base, `.${input.bundleName}.${process.pid}.${randomUUID()}.tmp`)
  await mkdir(staging, { recursive: false })

  try {
    const machineJson = `${JSON.stringify(input.machinePayload, null, 2)}\n`
    const mermaidSource = input.mermaidEnvelope.mermaidSource.endsWith("\n")
      ? input.mermaidEnvelope.mermaidSource
      : `${input.mermaidEnvelope.mermaidSource}\n`

    const graphJsonPath = path.join(staging, "graph.json")
    const mermaidPath = path.join(staging, "graph.mmd")
    await writeUtf8(graphJsonPath, machineJson)
    await writeUtf8(mermaidPath, mermaidSource)

    const artifacts: Record<string, unknown> = {
      graphJson: {
        path: "graph.json",
        format: "json",
        bytes: byteLength(machineJson),
        sha256: sha256(machineJson),
      },
      mermaid: {
        path: "graph.mmd",
        format: "mermaid",
        bytes: byteLength(mermaidSource),
        sha256: sha256(mermaidSource),
      },
    }

    let svgRenderer: Record<string, unknown> | undefined
    if (input.renderSvg) {
      const svgPath = path.join(staging, "graph.svg")
      const renderMetadata = await input.renderSvg(mermaidSource, svgPath)
      const svg = await readFile(svgPath)
      const probe = svg.subarray(0, Math.min(svg.length, 2_000)).toString("utf8").toLowerCase()
      if (!probe.includes("<svg")) throw new Error("retained renderer output is not recognizable SVG")
      artifacts.svg = {
        path: "graph.svg",
        format: "svg",
        bytes: svg.byteLength,
        sha256: sha256(svg),
      }
      svgRenderer = renderMetadata.renderer
    }

    const manifest = {
      schemaVersion: GRAPH_EXPORT_SCHEMA_VERSION,
      kind: "codesleuth-graph-export",
      view: input.view,
      exportedAt: input.exportedAt ?? new Date().toISOString(),
      exportAuthority: "none",
      retainedArtifactOnly: true,
      derivedPresentationOnly: true,
      sourceAuthority: input.mermaidEnvelope.authority,
      provenance: input.mermaidEnvelope.provenance ?? null,
      selection: input.mermaidEnvelope.selection ?? null,
      truncated: input.mermaidEnvelope.truncated ?? false,
      machinePayloadRole: input.machinePayloadRole,
      ...(svgRenderer ? { renderer: svgRenderer } : {}),
      artifacts,
      reminder: "export copies are not repository truth, review evidence, or acceptance evidence",
    }
    await writeUtf8(path.join(staging, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`)

    await rename(staging, finalDir)
    return {
      ...manifest,
      outputDirectory: path.relative(physicalRoot, finalDir).replace(/\\/g, "/"),
    }
  } catch (error) {
    await rm(staging, { recursive: true, force: true }).catch(() => undefined)
    throw error
  }
}
