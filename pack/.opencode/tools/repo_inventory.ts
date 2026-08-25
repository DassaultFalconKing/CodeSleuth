import { tool } from "@opencode-ai/plugin"
import { mkdir, writeFile } from "node:fs/promises"
import path from "node:path"

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

function normalizePrefix(input?: string): string {
  if (!input) return ""
  return input.replace(/\\/g, "/").replace(/^\.\//, "").replace(/\/+$/, "")
}

export default tool({
  description:
    "Build a deterministic inventory of tracked Git files/blobs and return a bounded repository or path-prefix summary. The full manifest is stored under .opencode/state.",
  args: {
    prefix: tool.schema.string().optional().describe("Optional tracked path prefix to summarize"),
    maxPaths: tool.schema.number().int().min(1).max(1000).optional().describe("Maximum paths returned in the model-visible preview (default 200)"),
  },
  async execute(args, context) {
    const root = context.worktree
    const raw = await git(root, ["ls-files", "-s", "-z"])
    const headSha = (await git(root, ["rev-parse", "HEAD"])).trim()
    const status = await git(root, ["status", "--porcelain=v1"])

    const files = raw
      .split("\0")
      .filter(Boolean)
      .map((record) => {
        const tab = record.indexOf("\t")
        if (tab < 0) throw new Error(`unexpected git ls-files record: ${record}`)
        const meta = record.slice(0, tab).trim().split(/\s+/)
        return {
          mode: meta[0] ?? "",
          blob: meta[1] ?? "",
          stage: meta[2] ?? "",
          path: record.slice(tab + 1).replace(/\\/g, "/"),
        }
      })

    const stateDir = path.join(root, ".opencode", "state", "inventory")
    await mkdir(stateDir, { recursive: true })
    const manifestPath = path.join(stateDir, `${context.sessionID}.json`)
    await writeFile(
      manifestPath,
      JSON.stringify(
        {
          schemaVersion: 1,
          generatedAt: new Date().toISOString(),
          headSha,
          dirty: status.trim().length > 0,
          status: status.trim().split("\n").filter(Boolean),
          files,
        },
        null,
        2,
      ),
      "utf8",
    )

    const prefix = normalizePrefix(args.prefix)
    const scoped = prefix
      ? files.filter((file) => file.path === prefix || file.path.startsWith(`${prefix}/`))
      : files

    const topDirectories: Record<string, number> = {}
    const extensions: Record<string, number> = {}
    const rootFiles: string[] = []
    for (const file of scoped) {
      const slash = file.path.indexOf("/")
      if (slash < 0) rootFiles.push(file.path)
      else {
        const dir = file.path.slice(0, slash)
        topDirectories[dir] = (topDirectories[dir] ?? 0) + 1
      }
      const base = path.posix.basename(file.path)
      const dot = base.lastIndexOf(".")
      const ext = dot > 0 ? base.slice(dot).toLowerCase() : "<none>"
      extensions[ext] = (extensions[ext] ?? 0) + 1
    }

    const sortCounts = (value: Record<string, number>) =>
      Object.entries(value)
        .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
        .slice(0, 40)
        .map(([name, count]) => ({ name, count }))

    const maxPaths = args.maxPaths ?? 200
    const preview = scoped.slice(0, maxPaths).map((file) => file.path)
    return JSON.stringify(
      {
        headSha,
        dirty: status.trim().length > 0,
        trackedFiles: files.length,
        scope: prefix || ".",
        scopeFiles: scoped.length,
        manifestPath: path.relative(root, manifestPath).replace(/\\/g, "/"),
        rootFiles: rootFiles.slice(0, 80),
        topDirectories: sortCounts(topDirectories),
        extensions: sortCounts(extensions),
        paths: preview,
        pathsTruncated: scoped.length > preview.length,
      },
      null,
      2,
    )
  },
})
