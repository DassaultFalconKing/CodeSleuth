import { tool } from "@opencode-ai/plugin"
import { randomUUID } from "node:crypto"
import { mkdir, readFile, rename, rm, stat, writeFile } from "node:fs/promises"
import path from "node:path"

const SHA_RE = /^[0-9a-f]{40}$/
const SAFE_ID_RE = /^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$/
const MAX_TRACKED_FILES = 5000
const MAX_READ_BYTES = 512 * 1024
const MAX_ENTRIES = 200
const MANIFESTS = new Set(["Cargo.toml", "package.json", "pyproject.toml", "go.mod", "pom.xml", "build.gradle", "build.gradle.kts", "Makefile"])

type SurfaceKind =
  | "SEED"
  | "WORKSPACE_MANIFEST"
  | "IMPORT_REFERENCE"
  | "TEST_REFERENCE"
  | "SCHEMA_MIGRATION"
  | "API_DEFINITION"
  | "CI_VERIFY"
  | "OWNERSHIP_DOC"
  | "REVERSE_DEPENDENCY"
  | "INCLUDE_REFERENCE"
  | "AUTHORITY_SURFACE"
type SurfaceEntry = { path: string; blobHash: string; kinds: SurfaceKind[]; reasons: string[] }
type Projection = {
  schemaVersion: 1
  surfaceMapId: string
  targetSha: string
  authority: "DERIVED_NON_AUTHORITATIVE"
  seedPaths: string[]
  entries: SurfaceEntry[]
  truncated: boolean
  recordedAt: string
}
type CargoPackage = {
  name: string
  root: string
  manifest: string
  dependencyNames: Set<string>
  dependencyRoots: Set<string>
}

async function git(root: string, args: string[], allowFailure = false): Promise<{ code: number; stdout: string; stderr: string }> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text(); const stderr = await new Response(proc.stderr).text(); const code = await proc.exited
  if (code !== 0 && !allowFailure) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`)
  return { code, stdout: stdout.trim(), stderr: stderr.trim() }
}
async function trackedPaths(root: string): Promise<string[]> {
  const proc = Bun.spawn(["git", "-C", root, "ls-files", "-z"], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text(); const stderr = await new Response(proc.stderr).text(); const code = await proc.exited
  if (code !== 0) throw new Error(stderr.trim() || "git ls-files -z failed")
  return stdout.split("\0").filter(Boolean).map((item) => item.replace(/\\/g, "/")).sort()
}
async function currentHead(root: string) { return (await git(root, ["rev-parse", "HEAD"])).stdout.toLowerCase() }
async function requireExactClean(root: string, sha: string) {
  if (!SHA_RE.test(sha)) throw new Error("target SHA must be a full lowercase Git SHA")
  const head = await currentHead(root); if (head !== sha) throw new Error(`CHANGE SURFACE INVALIDATED — HEAD CHANGED: expected ${sha}, got ${head}`)
  const status = (await git(root, ["status", "--porcelain=v1", "--untracked-files=no"])).stdout
  if (status) throw new Error(`CHANGE SURFACE INVALIDATED — TRACKED WORKTREE DIRTY:\n${status}`)
}
async function readOptional(file: string): Promise<string | undefined> { try { return await readFile(file, "utf8") } catch (error: any) { if (error?.code === "ENOENT") return undefined; throw error } }
async function atomicWrite(file: string, content: string) {
  await mkdir(path.dirname(file), { recursive: true }); const temp = `${file}.${process.pid}.${randomUUID()}.tmp`
  try { await writeFile(temp, content, { encoding: "utf8", flag: "wx" }); await rename(temp, file) } catch (error) { await rm(temp, { force: true }).catch(() => undefined); throw error }
}
function baseDir(root: string) { return path.join(root, ".opencode", "state", "change-surfaces") }
function mapDir(root: string, id: string) { if (!SAFE_ID_RE.test(id)) throw new Error("invalid change surface id"); return path.join(baseDir(root), id) }
function normalizeRepoPath(root: string, input: string) {
  const resolvedRoot = path.resolve(root); const absolute = path.resolve(root, input)
  if (absolute !== resolvedRoot && !absolute.startsWith(resolvedRoot + path.sep)) throw new Error(`path escapes worktree: ${input}`)
  const relative = path.relative(resolvedRoot, absolute).replace(/\\/g, "/")
  if (!relative || relative === ".") throw new Error("change-surface input must name a tracked repository path")
  return relative
}
function unique(values: string[]) { return [...new Set(values)] }
function expandTrackedInputs(root: string, inputs: string[], tracked: string[], label: string): string[] {
  const trackedSet = new Set(tracked)
  const expanded: string[] = []
  for (const input of inputs) {
    const requested = normalizeRepoPath(root, input)
    if (trackedSet.has(requested)) {
      expanded.push(requested)
      continue
    }
    const prefix = `${requested}/`
    const members = tracked.filter((file) => file.startsWith(prefix))
    if (members.length === 0) throw new Error(`${label} is not tracked at exact target: ${requested}`)
    expanded.push(...members)
  }
  return unique(expanded).sort()
}
function stem(file: string) {
  const base = path.posix.basename(file).replace(/\.(test|spec)\.[^.]+$/, "").replace(/^test_/, "")
  return base.replace(/\.[^.]+$/, "").replace(/[^A-Za-z0-9_]+/g, "_").toLowerCase()
}
function tokensFor(seed: string): string[] {
  const values = [stem(seed), path.posix.basename(seed).toLowerCase(), seed.toLowerCase()]
  return unique(values.filter((value) => value.length >= 3))
}
function ancestorDirectories(file: string): string[] {
  const result = [""]; let current = path.posix.dirname(file)
  while (current && current !== ".") { result.push(current); const next = path.posix.dirname(current); if (next === current) break; current = next }
  return unique(result)
}
function isTestPath(file: string) { const lower = file.toLowerCase(); return lower.includes("/tests/") || lower.startsWith("tests/") || /(^|\/)(test_[^/]+|[^/]+\.(test|spec)\.[^/]+)$/.test(lower) }
function isSchemaMigration(file: string) { const lower = file.toLowerCase(); return /(^|\/)(migrations?|schemas?|dto|dtos|proto|openapi)(\/|$)/.test(lower) }
function isApiPath(file: string) { const lower = file.toLowerCase(); return /(^|\/)(api|apis|routes?|endpoints?|controllers?)(\/|\.|$)/.test(lower) || /(^|\/)(api|routes?|endpoints?|controllers?)\.[^/]+$/.test(lower) }
function isVerifyPath(file: string) { const lower = file.toLowerCase(); const base = path.posix.basename(lower); return base === "verify.sh" || base === "makefile" || /(^|\/)scripts\/verify[^/]*$/.test(lower) || /(^|\/)\.github\/workflows\//.test(lower) }
function isOwnershipDoc(file: string) { const lower = file.toLowerCase(); const base = path.posix.basename(lower); return base === "agents.md" || base === "codeowners" || (lower.startsWith("docs/") && /(session|orientation|waypoint|roadmap|plan|scope|ownership|handoff)/.test(lower)) }
function containsAny(text: string, tokens: string[]) { const lower = text.toLowerCase(); return tokens.some((token) => lower.includes(token)) }
function importMentions(text: string, tokens: string[]) {
  return text.split(/\r?\n/).some((line) => /\b(import|from|require|use|include)\b/i.test(line) && containsAny(line, tokens))
}
async function trackedBlob(root: string, file: string) {
  const blob = (await git(root, ["rev-parse", `HEAD:${file}`])).stdout.toLowerCase()
  if (!SHA_RE.test(blob)) throw new Error(`change-surface evidence is not a regular tracked blob: ${file}`)
  return blob
}
async function boundedText(root: string, file: string): Promise<string> {
  const absolute = path.join(root, ...file.split("/"))
  try {
    const info = await stat(absolute)
    if (!info.isFile() || info.size > MAX_READ_BYTES) return ""
    return await readFile(absolute, "utf8")
  } catch { return "" }
}
function addReason(index: Map<string, { kinds: Set<SurfaceKind>; reasons: Set<string> }>, file: string, kind: SurfaceKind, reason: string) {
  const item = index.get(file) ?? { kinds: new Set<SurfaceKind>(), reasons: new Set<string>() }; item.kinds.add(kind); item.reasons.add(reason); index.set(file, item)
}
function cargoSection(line: string): string | null {
  const match = /^\s*\[([^\]]+)\]\s*$/.exec(line)
  return match ? match[1].trim() : null
}
function normalizeDependencyRoot(manifest: string, raw: string): string | null {
  const base = path.posix.dirname(manifest) === "." ? "" : path.posix.dirname(manifest)
  const resolved = path.posix.normalize(path.posix.join(base, raw.replace(/\\/g, "/")))
  if (!resolved || resolved === "." || resolved === ".." || resolved.startsWith("../") || path.posix.isAbsolute(resolved)) return null
  return resolved.replace(/\/$/, "")
}
async function cargoPackages(root: string, tracked: string[]): Promise<CargoPackage[]> {
  const result: CargoPackage[] = []
  for (const manifest of tracked.filter((file) => path.posix.basename(file) === "Cargo.toml")) {
    const text = await boundedText(root, manifest)
    if (!text) continue
    const lines = text.split(/\r?\n/)
    let section = ""
    let packageName: string | null = null
    const dependencyNames = new Set<string>()
    const dependencyRoots = new Set<string>()
    for (const line of lines) {
      const nextSection = cargoSection(line)
      if (nextSection !== null) { section = nextSection; continue }
      if (section === "package" && packageName === null) {
        const name = /^\s*name\s*=\s*["']([^"']+)["']/.exec(line)
        if (name) packageName = name[1]
      }
      if (/^(?:target\.[^.]+\.)?(?:dev-|build-)?dependencies$/.test(section) || section === "dependencies") {
        const dependency = /^\s*([A-Za-z0-9_.-]+)\s*=/.exec(line)
        if (!dependency) continue
        dependencyNames.add(dependency[1])
        const packageAlias = /\bpackage\s*=\s*["']([^"']+)["']/.exec(line)
        if (packageAlias) dependencyNames.add(packageAlias[1])
        const pathRef = /\bpath\s*=\s*["']([^"']+)["']/.exec(line)
        if (pathRef) {
          const resolved = normalizeDependencyRoot(manifest, pathRef[1])
          if (resolved) dependencyRoots.add(resolved)
        }
      }
    }
    if (!packageName) continue
    const pkgRoot = path.posix.dirname(manifest) === "." ? "" : path.posix.dirname(manifest)
    result.push({ name: packageName, root: pkgRoot, manifest, dependencyNames, dependencyRoots })
  }
  return result
}
function ownsPath(pkg: CargoPackage, file: string): boolean {
  if (file === pkg.manifest) return true
  return pkg.root === "" || file.startsWith(`${pkg.root}/`)
}
function owningCargoPackages(packages: CargoPackage[], seeds: string[]): Set<string> {
  const roots = new Set<string>()
  for (const seed of seeds) {
    const owners = packages.filter((pkg) => ownsPath(pkg, seed)).sort((a, b) => b.root.length - a.root.length)
    if (owners[0]) roots.add(owners[0].root)
  }
  return roots
}
function reverseCargoClosure(packages: CargoPackage[], directRoots: Set<string>): Set<string> {
  const affected = new Set(directRoots)
  let changed = true
  while (changed) {
    changed = false
    const affectedPackages = packages.filter((pkg) => affected.has(pkg.root))
    const affectedNames = new Set(affectedPackages.map((pkg) => pkg.name))
    const affectedRoots = new Set(affectedPackages.map((pkg) => pkg.root).filter(Boolean))
    for (const pkg of packages) {
      if (affected.has(pkg.root)) continue
      const namedDependency = [...pkg.dependencyNames].some((name) => affectedNames.has(name))
      const pathDependency = [...pkg.dependencyRoots].some((root) => affectedRoots.has(root))
      if (namedDependency || pathDependency) { affected.add(pkg.root); changed = true }
    }
  }
  return affected
}
function cargoPackageFiles(pkg: CargoPackage, tracked: string[]): string[] {
  const prefixes = pkg.root === "" ? ["src/", "tests/", "benches/", "examples/"] : ["src/", "tests/", "benches/", "examples/"].map((part) => `${pkg.root}/${part}`)
  const build = pkg.root === "" ? "build.rs" : `${pkg.root}/build.rs`
  return tracked.filter((file) => file === pkg.manifest || file === build || prefixes.some((prefix) => file.startsWith(prefix)))
}
function includeTargets(source: string, text: string): string[] {
  const targets: string[] = []
  const regex = /\binclude_(?:str|bytes)!\s*\(\s*["']([^"']+)["']\s*\)/g
  for (const match of text.matchAll(regex)) {
    const base = path.posix.dirname(source) === "." ? "" : path.posix.dirname(source)
    const resolved = path.posix.normalize(path.posix.join(base, match[1].replace(/\\/g, "/")))
    if (resolved && resolved !== "." && resolved !== ".." && !resolved.startsWith("../") && !path.posix.isAbsolute(resolved)) targets.push(resolved)
  }
  return unique(targets)
}
async function resolveId(root: string, explicit?: string) {
  if (explicit) { if (!SAFE_ID_RE.test(explicit)) throw new Error("invalid change surface id"); return explicit }
  const latest = await readOptional(path.join(baseDir(root), "latest.txt")); if (!latest?.trim()) throw new Error("no pre-registry change surface found; derive one first"); return latest.trim()
}
async function verifyProjection(root: string, projection: Projection) {
  await requireExactClean(root, projection.targetSha)
  for (const entry of projection.entries) {
    const current = await trackedBlob(root, entry.path)
    if (current !== entry.blobHash) throw new Error(`change-surface evidence blob changed for ${entry.path}`)
  }
}

export const derive = tool({
  description: "Derive one bounded, non-authoritative pre-registry change surface from exact tracked repository evidence and bounded structural dependency metadata.",
  args: {
    targetSha: tool.schema.string().optional(),
    seedPaths: tool.schema.array(tool.schema.string().min(1)).min(1).max(50),
    authorityPaths: tool.schema.array(tool.schema.string().min(1)).max(100).optional().describe("Exact repository-authority named gate/read-only surface paths; never treated as positive mutation authority"),
  },
  async execute(args, context) {
    const root = context.worktree; const targetSha = (args.targetSha ?? await currentHead(root)).trim().toLowerCase(); await requireExactClean(root, targetSha)
    const tracked = await trackedPaths(root)
    if (tracked.length > MAX_TRACKED_FILES) throw new Error(`pre-registry change-surface inventory exceeds ${MAX_TRACKED_FILES} tracked files; narrow the active scope first`)
    const trackedSet = new Set(tracked)
    const seeds = expandTrackedInputs(root, args.seedPaths, tracked, "change-surface seed")
    if (seeds.length > MAX_ENTRIES) throw new Error(`change-surface seed expansion exceeds ${MAX_ENTRIES} tracked files; narrow the active scope first`)
    const authorityPaths = expandTrackedInputs(root, args.authorityPaths ?? [], tracked, "change-surface authority path")
    if (authorityPaths.length > MAX_ENTRIES) throw new Error(`change-surface authority expansion exceeds ${MAX_ENTRIES} tracked files; narrow the authority surface first`)
    const index = new Map<string, { kinds: Set<SurfaceKind>; reasons: Set<string> }>()

    for (const seed of seeds) addReason(index, seed, "SEED", "declared active-scope seed path or tracked member of a declared seed directory")
    for (const file of authorityPaths) addReason(index, file, "AUTHORITY_SURFACE", "repository authority explicitly names this verification/read-only surface")

    const packages = await cargoPackages(root, tracked)
    const directPackageRoots = owningCargoPackages(packages, seeds)
    const affectedPackageRoots = reverseCargoClosure(packages, directPackageRoots)
    for (const pkg of packages) {
      if (!affectedPackageRoots.has(pkg.root)) continue
      const reverse = !directPackageRoots.has(pkg.root)
      for (const file of cargoPackageFiles(pkg, tracked)) {
        addReason(index, file, reverse ? "REVERSE_DEPENDENCY" : "IMPORT_REFERENCE", reverse ? `Cargo package ${pkg.name} is a reverse consumer of the active package closure` : `Cargo package ${pkg.name} owns or implements the active seed surface`)
      }
      addReason(index, pkg.manifest, reverse ? "REVERSE_DEPENDENCY" : "WORKSPACE_MANIFEST", reverse ? `Cargo manifest declares a reverse dependency on the active package closure` : `Cargo manifest owns an active-scope seed`)
    }

    const ancestorDirs = new Set(seeds.flatMap(ancestorDirectories))
    for (const file of tracked) {
      const base = path.posix.basename(file)
      const directory = path.posix.dirname(file) === "." ? "" : path.posix.dirname(file)
      if (MANIFESTS.has(base) && ancestorDirs.has(directory)) addReason(index, file, "WORKSPACE_MANIFEST", "workspace/build manifest owns an ancestor of an active-scope seed")
    }

    const structuralTokens = unique([
      ...seeds.flatMap(tokensFor),
      ...packages.filter((pkg) => affectedPackageRoots.has(pkg.root)).flatMap((pkg) => [pkg.name.toLowerCase(), pkg.name.replace(/-/g, "_").toLowerCase()]),
    ]).filter((value) => value.length >= 3)
    for (const file of tracked) {
      if (index.has(file) && seeds.includes(file)) continue
      const text = await boundedText(root, file); if (!text || !containsAny(text, structuralTokens)) continue
      if (isTestPath(file)) addReason(index, file, "TEST_REFERENCE", "tracked test references an active-scope seed or affected package")
      if (isSchemaMigration(file)) addReason(index, file, "SCHEMA_MIGRATION", "tracked schema/migration surface references an active-scope seed or affected package")
      if (isApiPath(file)) addReason(index, file, "API_DEFINITION", "tracked API surface references an active-scope seed or affected package")
      if (isVerifyPath(file)) addReason(index, file, "CI_VERIFY", "tracked native verify/CI surface references an active-scope seed or affected package")
      if (isOwnershipDoc(file)) addReason(index, file, "OWNERSHIP_DOC", "tracked planning/ownership document references an active-scope seed or affected package")
      if (!isTestPath(file) && importMentions(text, structuralTokens)) addReason(index, file, "IMPORT_REFERENCE", "tracked import/use statement references an active-scope seed or affected package")
    }

    let includeChanged = true
    while (includeChanged) {
      includeChanged = false
      for (const source of [...index.keys()]) {
        const text = await boundedText(root, source)
        if (!text) continue
        for (const target of includeTargets(source, text)) {
          if (!trackedSet.has(target)) continue
          const wasPresent = index.has(target)
          addReason(index, target, "INCLUDE_REFERENCE", `tracked ${source} embeds this file with include_str!/include_bytes!`)
          if (!wasPresent) includeChanged = true
        }
      }
    }

    const paths = [...index.keys()].sort(); const truncated = paths.length > MAX_ENTRIES; const selected = paths.slice(0, MAX_ENTRIES)
    const entries: SurfaceEntry[] = []
    for (const file of selected) {
      const item = index.get(file)!; entries.push({ path: file, blobHash: await trackedBlob(root, file), kinds: [...item.kinds].sort() as SurfaceKind[], reasons: [...item.reasons].sort() })
    }
    const surfaceMapId = `CSM-${new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)}-${targetSha.slice(0, 12)}-${randomUUID().slice(0, 8)}`
    const projection: Projection = { schemaVersion: 1, surfaceMapId, targetSha, authority: "DERIVED_NON_AUTHORITATIVE", seedPaths: seeds, entries, truncated, recordedAt: new Date().toISOString() }
    await mkdir(baseDir(root), { recursive: true }); await mkdir(mapDir(root, surfaceMapId), { recursive: false }); await atomicWrite(path.join(mapDir(root, surfaceMapId), "projection.json"), `${JSON.stringify(projection, null, 2)}\n`); await atomicWrite(path.join(baseDir(root), "latest.txt"), `${surfaceMapId}\n`)
    return JSON.stringify(projection, null, 2)
  },
})

export const load = tool({
  description: "Load and revalidate a derived pre-registry change surface against exact tracked blobs.",
  args: { surfaceMapId: tool.schema.string().optional() },
  async execute(args, context) {
    const root = context.worktree; const id = await resolveId(root, args.surfaceMapId); const projection = JSON.parse(await readFile(path.join(mapDir(root, id), "projection.json"), "utf8")) as Projection
    await verifyProjection(root, projection)
    return JSON.stringify({ ...projection, evidenceIntegrity: "PASS" }, null, 2)
  },
})
