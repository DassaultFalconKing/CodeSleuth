import { tool } from "@opencode-ai/plugin"
import { access } from "node:fs/promises"
import path from "node:path"

const MAX_FILES = 200
const MAX_NODES = 500
const MAX_EDGES = 1000

async function exists(file: string): Promise<boolean> {
  try {
    await access(file)
    return true
  } catch {
    return false
  }
}

async function helperPath(root: string): Promise<string> {
  const installed = path.join(root, ".opencode", "bin", "codesleuth_project", "graphify_adapter.py")
  if (await exists(installed)) return installed
  const source = path.join(root, "pack", ".opencode", "bin", "codesleuth_project", "graphify_adapter.py")
  if (await exists(source)) return source
  throw new Error("CodeSleuth Graphify adapter helper is not installed")
}

async function runGraphify(root: string, request?: unknown): Promise<string> {
  const helper = await helperPath(root)
  const runtime = path.join(root, ".runtime", "graphify-provider")
  const args = ["python", helper, "--runtime", runtime, ...(request === undefined ? ["--status"] : [])]
  const proc = Bun.spawn(args, {
    cwd: root,
    stdin: request === undefined ? undefined : "pipe",
    stdout: "pipe",
    stderr: "pipe",
  })
  if (request !== undefined) {
    proc.stdin.write(JSON.stringify(request))
    proc.stdin.end()
  }
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  const code = await proc.exited
  if (code !== 0) throw new Error(stderr.trim() || stdout.trim() || "Graphify adapter failed")
  return stdout.trim()
}

export const status = tool({
  description:
    "Report repository-context provider availability, exact version/origin, capabilities and permission boundary. builtin is always the safe default; graphify is isolated and explicitly enabled.",
  args: {
    provider: tool.schema.enum(["builtin", "graphify"]).optional(),
  },
  async execute(args, context) {
    if ((args.provider ?? "builtin") === "builtin") {
      return JSON.stringify(
        {
          schemaVersion: 1,
          provider: "builtin",
          status: "available",
          installed: true,
          compatible: true,
          defaultProvider: true,
          capabilities: ["agent_verified_bounded_projection"],
          permissions: { hostControlled: true, networkAdded: false, trackedWriteAdded: false },
        },
        null,
        2,
      )
    }
    return runGraphify(context.worktree)
  },
})

export const extract = tool({
  description:
    "Explicitly run one repository-context provider. builtin returns the existing agent-mapping route; graphify calls only the isolated local structural adapter over the caller-supplied tracked file manifest and returns bounded candidates for repo_context_graph_save validation.",
  args: {
    provider: tool.schema.enum(["builtin", "graphify"]),
    files: tool.schema.array(tool.schema.string().min(1)).max(MAX_FILES).optional(),
    nodeLimit: tool.schema.number().int().min(1).max(MAX_NODES).optional(),
    edgeLimit: tool.schema.number().int().min(1).max(MAX_EDGES).optional(),
  },
  async execute(args, context) {
    if (args.provider === "builtin") {
      return JSON.stringify(
        {
          schemaVersion: 1,
          provider: "builtin",
          status: "delegate_to_existing_repository_map",
          candidates: null,
          instruction: "Use repo_inventory and exact-source review, then validate/persist with repo_context_graph_save.",
        },
        null,
        2,
      )
    }
    if (!args.files || args.files.length === 0) throw new Error("graphify provider requires an explicit tracked file manifest")
    return runGraphify(context.worktree, {
      root: context.worktree,
      files: args.files,
      nodeLimit: args.nodeLimit,
      edgeLimit: args.edgeLimit,
    })
  },
})
