import { tool } from "@opencode-ai/plugin"
import { readFile } from "node:fs/promises"
import path from "node:path"

async function git(root: string, args: string[]): Promise<string> {
  const p = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const out = await new Response(p.stdout).text()
  const err = await new Response(p.stderr).text()
  if ((await p.exited) !== 0) throw new Error(err.trim() || `git ${args.join(" ")} failed`)
  return out
}

async function optionalJson(root: string, file: string): Promise<any | undefined> {
  try { return JSON.parse(await readFile(path.join(root, file), "utf8")) }
  catch (error: any) { if (error?.code === "ENOENT") return undefined; return { _parseError: String(error) } }
}

export default tool({
  description: "Detect repository language/profile families and verification scripts from tracked local evidence.",
  args: {},
  async execute(_args, context) {
    const root = context.worktree
    const tracked = (await git(root, ["ls-files", "-z"])).split("\0").filter(Boolean).map((x) => x.replace(/\\/g, "/"))
    const has = (name: string) => tracked.includes(name)
    const countExt = (ext: string) => tracked.filter((p) => p.toLowerCase().endsWith(ext)).length
    const packageJson = await optionalJson(root, "package.json")
    const pyproject = await optionalJson(root, "pyproject.toml")
    const profiles = ["generic"]
    const evidence: Record<string, string[]> = {}

    if (has("Cargo.toml") || countExt(".rs") > 0) { profiles.push("rust"); evidence.rust = [has("Cargo.toml") ? "Cargo.toml" : "tracked .rs files"] }
    if (has("pyproject.toml") || has("requirements.txt") || countExt(".py") > 0) { profiles.push("python"); evidence.python = [has("pyproject.toml") ? "pyproject.toml" : has("requirements.txt") ? "requirements.txt" : "tracked .py files"] }
    const typescript = tracked.some((p) => /^tsconfig.*\.json$/i.test(path.posix.basename(p))) || countExt(".ts") + countExt(".tsx") > 0
    const node = Boolean(packageJson) || has("package-lock.json") || has("pnpm-lock.yaml") || has("yarn.lock") || has("bun.lock") || has("bun.lockb")
    if (node) { profiles.push("node"); evidence.node = [packageJson ? "package.json" : "Node lockfile"] }
    if (typescript) { profiles.push("typescript"); evidence.typescript = tracked.filter((p) => /^tsconfig.*\.json$/i.test(path.posix.basename(p))).slice(0, 20); if (!evidence.typescript.length) evidence.typescript = ["tracked .ts/.tsx files"] }

    const scripts = packageJson && typeof packageJson === "object" && packageJson.scripts ? packageJson.scripts : {}
    const packageManager = has("pnpm-lock.yaml") ? "pnpm" : has("yarn.lock") ? "yarn" : (has("bun.lock") || has("bun.lockb")) ? "bun" : has("package-lock.json") ? "npm" : undefined

    return JSON.stringify({
      headSha: (await git(root, ["rev-parse", "HEAD"])).trim(),
      profiles: [...new Set(profiles)],
      evidence,
      counts: { rust: countExt(".rs"), python: countExt(".py"), typescript: countExt(".ts") + countExt(".tsx"), javascript: countExt(".js") + countExt(".jsx") + countExt(".mjs") + countExt(".cjs") },
      node: node ? { packageManager, scripts } : undefined,
      python: pyproject ? { pyproject: true } : undefined,
      existingOpenCode: has(".opencode/opencode.json"),
      exaLaunchDefault: "OPENCODE_ENABLE_EXA=1",
    }, null, 2)
  },
})
