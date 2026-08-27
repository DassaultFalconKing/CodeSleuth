import { tool } from "@opencode-ai/plugin"
import { createHash } from "node:crypto"
import { readFile } from "node:fs/promises"
import path from "node:path"

const REGISTRY_PATH = "docs/protected-capabilities.json"
const DEFAULT_CONTRACT_LIMIT = 30
const MAX_CONTRACT_LIMIT = 50

type ForbiddenRegression = { id: string; sib_origin: "SIB0" | "SIB1" | "SIB2"; must_not: string }
export type ProtectedContract = {
  id: string
  capability_class: string
  capability_class_id: string
  status: string
  depends_on: string[]
  forbidden_regressions: ForbiddenRegression[]
}
export type ProtectedRegistry = {
  schema_version: number
  registry: string
  authority: string
  contracts: ProtectedContract[]
}

type ImpactOptions = {
  contractIds?: string[]
  includeDependencies?: boolean
  includeConsumers?: boolean
  contractLimit?: number
}

export type ImpactSelection = {
  roots: string[]
  selected: ProtectedContract[]
  edges: Array<{ dependency: string; consumer: string }>
  totals: { contracts: number; edges: number }
  returned: { contracts: number; edges: number }
  truncated: boolean
}

async function git(root: string, args: string[]): Promise<string> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  if ((await proc.exited) !== 0) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`)
  return stdout.trim()
}

function validateRegistry(value: unknown): ProtectedRegistry {
  if (!value || typeof value !== "object") throw new Error("protected capability registry must be an object")
  const registry = value as ProtectedRegistry
  if (registry.schema_version !== 1 || registry.registry !== "codesleuth-protected-capabilities") {
    throw new Error("unsupported protected capability registry identity or schema")
  }
  if (!Array.isArray(registry.contracts) || registry.contracts.length === 0) {
    throw new Error("protected capability registry has no contracts")
  }
  const ids = new Set<string>()
  for (const [index, contract] of registry.contracts.entries()) {
    if (!contract || typeof contract.id !== "string" || !contract.id) throw new Error(`contracts[${index}] has no id`)
    if (ids.has(contract.id)) throw new Error(`duplicate protected contract id: ${contract.id}`)
    ids.add(contract.id)
    if (!Array.isArray(contract.depends_on)) throw new Error(`${contract.id} depends_on must be an array`)
    if (!Array.isArray(contract.forbidden_regressions) || contract.forbidden_regressions.length === 0) {
      throw new Error(`${contract.id} has no forbidden regressions`)
    }
  }
  for (const contract of registry.contracts) {
    for (const dependency of contract.depends_on) {
      if (!ids.has(dependency)) throw new Error(`${contract.id} depends on unknown contract ${dependency}`)
    }
  }
  return registry
}

export function selectProtectedImpact(registry: ProtectedRegistry, options: ImpactOptions = {}): ImpactSelection {
  const byId = new Map(registry.contracts.map((contract) => [contract.id, contract]))
  const roots = [...new Set(options.contractIds ?? [])].sort()
  for (const id of roots) if (!byId.has(id)) throw new Error(`protected contract not found: ${id}`)
  const includeDependencies = options.includeDependencies ?? false
  const includeConsumers = options.includeConsumers ?? true
  const selectedIds = new Set(roots.length > 0 ? roots : byId.keys())
  const consumers = new Map<string, string[]>()
  for (const contract of registry.contracts) {
    for (const dependency of contract.depends_on) {
      const values = consumers.get(dependency) ?? []
      values.push(contract.id)
      consumers.set(dependency, values)
    }
  }
  const queue = [...selectedIds].sort()
  while (queue.length > 0) {
    const current = queue.shift()!
    const neighbors = [
      ...(includeDependencies ? byId.get(current)!.depends_on : []),
      ...(includeConsumers ? consumers.get(current) ?? [] : []),
    ].sort()
    for (const neighbor of neighbors) {
      if (selectedIds.has(neighbor)) continue
      selectedIds.add(neighbor)
      queue.push(neighbor)
    }
  }

  const allSelected = [...selectedIds].map((id) => byId.get(id)!).sort((a, b) => a.id.localeCompare(b.id))
  const allEdges = registry.contracts
    .flatMap((consumer) => consumer.depends_on.map((dependency) => ({ dependency, consumer: consumer.id })))
    .filter((edge) => selectedIds.has(edge.dependency) && selectedIds.has(edge.consumer))
    .sort((a, b) => a.dependency.localeCompare(b.dependency) || a.consumer.localeCompare(b.consumer))
  const limit = Math.min(Math.max(1, options.contractLimit ?? DEFAULT_CONTRACT_LIMIT), MAX_CONTRACT_LIMIT)
  const selected = allSelected.slice(0, limit)
  const returnedIds = new Set(selected.map((contract) => contract.id))
  const edges = allEdges.filter((edge) => returnedIds.has(edge.dependency) && returnedIds.has(edge.consumer))
  return {
    roots,
    selected,
    edges,
    totals: { contracts: allSelected.length, edges: allEdges.length },
    returned: { contracts: selected.length, edges: edges.length },
    truncated: selected.length < allSelected.length || edges.length < allEdges.length,
  }
}

function escapeLabel(value: string): string {
  return value
    .replace(/[\u0000-\u001f\u007f\u2028\u2029]+/g, " ")
    .replace(/&/g, "#amp;")
    .replace(/"/g, "#quot;")
    .replace(/</g, "#lt;")
    .replace(/>/g, "#gt;")
    .replace(/`/g, "")
    .replace(/[{}[\]]/g, "()")
    .slice(0, 180)
}

function escapeComment(value: string): string {
  return escapeLabel(value).replace(/%/g, "").replace(/"/g, "'").slice(0, 200)
}

export function renderProtectedImpactMermaid(
  registry: ProtectedRegistry,
  selection: ImpactSelection,
  direction: "LR" | "TD" = "LR",
): string {
  const aliases = new Map(selection.selected.map((contract, index) => [contract.id, `c${index}`]))
  const lines = [
    "%% CodeSleuth protected-capability impact (derived, bounded presentation; not registry or acceptance evidence)",
    `%% registry: ${escapeComment(registry.registry)} schema ${registry.schema_version}`,
    `%% authority: ${escapeComment(registry.authority)}`,
    `%% selectionRoots: ${selection.roots.length > 0 ? escapeComment(selection.roots.join(", ")) : "all contracts"}`,
    `%% selectionTotals: ${selection.totals.contracts} contract(s), ${selection.totals.edges} dependency edge(s) before limits`,
    `flowchart ${direction}`,
    "  classDef csProtected stroke-width: 3px",
    "  classDef csRoot stroke:#f0c36a,stroke-width:3px",
  ]
  for (const contract of selection.selected) {
    const alias = aliases.get(contract.id)!
    const label = escapeLabel(
      `${contract.capability_class_id} | ${contract.id} | ${contract.status} | ${contract.forbidden_regressions.length} FR`,
    )
    lines.push(`  ${alias}["${label}"]`)
    if (contract.status === "protected") lines.push(`  class ${alias} csProtected`)
    if (selection.roots.includes(contract.id)) lines.push(`  class ${alias} csRoot`)
  }
  for (const edge of selection.edges) {
    lines.push(`  ${aliases.get(edge.dependency)} -->|"consumer impact"| ${aliases.get(edge.consumer)}`)
  }
  if (selection.truncated) {
    lines.push(
      `  truncated["bounded subset: showing ${selection.returned.contracts} of ${selection.totals.contracts} contracts and ${selection.returned.edges} of ${selection.totals.edges} dependency edges"]`,
    )
  }
  lines.push("  %% Forbidden-regression text remains contract-owned in docs/protected-capabilities.json; this diagram only visualizes relationships.")
  return `${lines.join("\n")}\n`
}

async function loadCurrentRegistry(root: string) {
  const tracked = await git(root, ["ls-files", "--stage", "--", REGISTRY_PATH])
  if (!tracked) throw new Error(`${REGISTRY_PATH} is not a tracked registry file`)
  const indexBlob = tracked.split(/\s+/)[1]
  const absolute = path.join(root, ...REGISTRY_PATH.split("/"))
  const raw = await readFile(absolute, "utf8")
  const registry = validateRegistry(JSON.parse(raw))
  return {
    registry,
    provenance: {
      path: REGISTRY_PATH,
      indexBlob,
      workingBlob: await git(root, ["hash-object", "--", REGISTRY_PATH]),
      contentSha256: createHash("sha256").update(raw).digest("hex"),
    },
  }
}

const selectionArgs = {
  contractIds: tool.schema.array(tool.schema.string()).max(20).optional(),
  includeDependencies: tool.schema.boolean().optional().describe("Include transitive dependencies of the roots (default false)"),
  includeConsumers: tool.schema.boolean().optional().describe("Include transitive reverse-dependency consumers (default true)"),
  contractLimit: tool.schema.number().int().min(1).max(MAX_CONTRACT_LIMIT).optional(),
}

export const query = tool({
  description:
    "Query a bounded protected-capability dependency/impact closure directly from the tracked docs/protected-capabilities.json registry. Returns derived navigation with exact registry provenance; never changes registry or acceptance state.",
  args: selectionArgs,
  async execute(args, context) {
    const loaded = await loadCurrentRegistry(context.worktree)
    const selection = selectProtectedImpact(loaded.registry, args)
    return JSON.stringify({ provenance: loaded.provenance, ...selection }, null, 2)
  },
})

export const mermaid = tool({
  description:
    "Render a deterministic bounded Mermaid impact view derived directly from the tracked Protected Capability Registry. Presentation/navigation only; forbidden-regression text and acceptance authority stay in the registry and exact evidence.",
  args: { ...selectionArgs, direction: tool.schema.enum(["LR", "TD"]).optional() },
  async execute(args, context) {
    const loaded = await loadCurrentRegistry(context.worktree)
    const selection = selectProtectedImpact(loaded.registry, args)
    return JSON.stringify(
      {
        provenance: loaded.provenance,
        selection,
        derivedPresentationOnly: true,
        mermaidSource: renderProtectedImpactMermaid(loaded.registry, selection, args.direction ?? "LR"),
      },
      null,
      2,
    )
  },
})
