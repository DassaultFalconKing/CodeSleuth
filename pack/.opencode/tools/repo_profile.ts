import { tool } from "@opencode-ai/plugin"
import { readFile } from "node:fs/promises"
import path from "node:path"

type JsonObject = Record<string, unknown>
type ProfileFragment = JsonObject & { profile: string; extends?: string }

function isObject(value: unknown): value is JsonObject {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function mergeProfileValues(parent: unknown, child: unknown): unknown {
  if (Array.isArray(parent) && Array.isArray(child)) {
    const merged: unknown[] = []
    for (const item of [...parent, ...child]) {
      if (!merged.some((candidate) => JSON.stringify(candidate) === JSON.stringify(item))) merged.push(item)
    }
    return merged
  }
  if (isObject(parent) && isObject(child)) {
    const merged: JsonObject = { ...parent }
    for (const [key, value] of Object.entries(child)) {
      if (key === "extends") continue
      merged[key] = key in merged ? mergeProfileValues(merged[key], value) : value
    }
    return merged
  }
  return child
}

async function readProfile(profileRoot: string, name: string): Promise<ProfileFragment> {
  if (!/^[a-z0-9][a-z0-9_-]*$/.test(name)) throw new Error(`invalid builtin profile name: ${name}`)
  const file = path.join(profileRoot, `${name}.json`)
  let parsed: unknown
  try {
    parsed = JSON.parse(await readFile(file, "utf8"))
  } catch (error: any) {
    if (error?.code === "ENOENT") throw new Error(`builtin profile not found: ${name}`)
    throw new Error(`builtin profile ${name} is not valid JSON: ${String(error)}`)
  }
  if (!isObject(parsed) || parsed.profile !== name) {
    throw new Error(`builtin profile ${name} must declare profile=${name}`)
  }
  if (parsed.extends !== undefined && typeof parsed.extends !== "string") {
    throw new Error(`builtin profile ${name} extends must be a profile name`)
  }
  return parsed as ProfileFragment
}

export async function resolveBuiltinProfile(
  profileRoot: string,
  name: string,
  stack: string[] = [],
): Promise<{ profile: ProfileFragment; lineage: string[] }> {
  if (stack.includes(name)) throw new Error(`builtin profile inheritance cycle: ${[...stack, name].join(" -> ")}`)
  const fragment = await readProfile(profileRoot, name)
  if (!fragment.extends) return { profile: { ...fragment }, lineage: [name] }
  const parent = await resolveBuiltinProfile(profileRoot, fragment.extends, [...stack, name])
  const merged = mergeProfileValues(parent.profile, fragment) as ProfileFragment
  merged.profile = name
  delete merged.extends
  return { profile: merged, lineage: [...parent.lineage, name] }
}

export async function resolveBuiltinProfiles(profileRoot: string, names: string[]) {
  const selected = [...new Set(names)]
  const definitions = []
  const effectiveOrder: string[] = []
  const resolvedByName = new Map<string, ProfileFragment>()
  for (const name of selected) {
    const resolved = await resolveBuiltinProfile(profileRoot, name)
    definitions.push({ name, lineage: resolved.lineage, value: resolved.profile })
    for (const inherited of resolved.lineage) {
      if (!effectiveOrder.includes(inherited)) effectiveOrder.push(inherited)
    }
  }
  for (const name of effectiveOrder) {
    resolvedByName.set(name, (await resolveBuiltinProfile(profileRoot, name)).profile)
  }
  let effective: JsonObject = {}
  for (const name of effectiveOrder) effective = mergeProfileValues(effective, resolvedByName.get(name)) as JsonObject
  effective.profile = selected.join("+")
  return { definitions, effective, effectiveOrder }
}

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
    const resolvedProfiles = await resolveBuiltinProfiles(path.join(root, ".opencode", "profiles", "builtin"), profiles)

    return JSON.stringify({
      headSha: (await git(root, ["rev-parse", "HEAD"])).trim(),
      profiles: [...new Set(profiles)],
      profileDefinitions: resolvedProfiles.definitions,
      effectiveProfile: resolvedProfiles.effective,
      effectiveProfileOrder: resolvedProfiles.effectiveOrder,
      evidence,
      counts: { rust: countExt(".rs"), python: countExt(".py"), typescript: countExt(".ts") + countExt(".tsx"), javascript: countExt(".js") + countExt(".jsx") + countExt(".mjs") + countExt(".cjs") },
      node: node ? { packageManager, scripts } : undefined,
      python: pyproject ? { pyproject: true } : undefined,
      existingOpenCode: has(".opencode/opencode.json"),
      exaLaunchDefault: "OPENCODE_ENABLE_EXA=1",
    }, null, 2)
  },
})
