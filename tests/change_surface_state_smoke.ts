import { mkdtemp, mkdir, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"
import { derive, load } from "../pack/.opencode/tools/change_surface_state"

function assert(condition: unknown, message: string): asserts condition { if (!condition) throw new Error(message) }
async function git(root: string, args: string[]): Promise<string> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text(); const stderr = await new Response(proc.stderr).text(); const code = await proc.exited
  if (code !== 0) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`); return stdout.trim()
}

async function main() {
  const root = await mkdtemp(path.join(tmpdir(), "change-surface-"))
  await git(root, ["init", "-b", "main"]); await git(root, ["config", "user.email", "ci@example.invalid"]); await git(root, ["config", "user.name", "CI"]); await git(root, ["config", "core.quotepath", "true"])
  await mkdir(path.join(root, "src", "pkg"), { recursive: true }); await mkdir(path.join(root, "tests"), { recursive: true }); await mkdir(path.join(root, "tests", "набор аудита"), { recursive: true }); await mkdir(path.join(root, "docs"), { recursive: true }); await mkdir(path.join(root, ".github", "workflows"), { recursive: true }); await mkdir(path.join(root, "migrations"), { recursive: true })
  await writeFile(path.join(root, "pyproject.toml"), "[project]\nname='fixture'\nversion='0.0.0'\n", "utf8")
  await writeFile(path.join(root, "src", "pkg", "service.py"), "def run():\n    return 1\n", "utf8")
  await writeFile(path.join(root, "src", "pkg", "api.py"), "from .service import run\n\ndef handler():\n    return run()\n", "utf8")
  await writeFile(path.join(root, "tests", "test_service.py"), "from pkg.service import run\n\ndef test_run():\n    assert run() == 1\n", "utf8")
  await writeFile(path.join(root, "tests", "набор аудита", "test_service_unicode.py"), "from pkg.service import run\n\ndef test_unicode_path():\n    assert run() == 1\n", "utf8")
  await writeFile(path.join(root, "migrations", "001_service.sql"), "-- migration for service\nselect 1;\n", "utf8")
  await writeFile(path.join(root, "docs", "SESSION.md"), "# Session\nAllowed path: src/pkg/service.py\n", "utf8")
  await writeFile(path.join(root, "verify.sh"), "#!/bin/sh\npython -m pytest tests/test_service.py\n", "utf8")
  await writeFile(path.join(root, ".github", "workflows", "ci.yml"), "name: ci\non: [push]\njobs: {}\n", "utf8")
  await git(root, ["add", "."]); await git(root, ["commit", "-m", "fixture"])
  const sha = await git(root, ["rev-parse", "HEAD"])
  const context = { worktree: root, directory: root, sessionID: "rc6-change-surface", messageID: "m1", agent: "build" } as any

  const projection = JSON.parse(await derive.execute({ targetSha: sha, seedPaths: ["src/pkg/service.py"] }, context))
  assert(projection.targetSha === sha, "projection must bind exact target")
  assert(projection.authority === "DERIVED_NON_AUTHORITATIVE", "pre-registry change surface must never become authority")
  const byPath = new Map(projection.entries.map((entry: any) => [entry.path, entry]))
  for (const required of ["src/pkg/service.py", "src/pkg/api.py", "tests/test_service.py", "tests/набор аудита/test_service_unicode.py", "pyproject.toml", "docs/SESSION.md", "verify.sh"]) {
    assert(byPath.has(required), `expected derived surface entry for ${required}`)
    assert(/^[0-9a-f]{40}$/.test(byPath.get(required).blobHash), `${required} must carry exact blob hash`)
    assert(byPath.get(required).reasons.length > 0, `${required} must explain derivation`)
  }
  assert(!byPath.has(".github/workflows/ci.yml"), "unrelated CI files must not be pulled into change surface without evidence")

  const loaded = JSON.parse(await load.execute({ surfaceMapId: projection.surfaceMapId }, context))
  assert(loaded.evidenceIntegrity === "PASS", "loaded surface must revalidate exact blobs")

  await writeFile(path.join(root, "src", "pkg", "service.py"), "def run():\n    return 2\n", "utf8")
  let dirtyRejected = false
  try { await load.execute({ surfaceMapId: projection.surfaceMapId }, context) } catch (error) { dirtyRejected = String(error).includes("TRACKED WORKTREE DIRTY") }
  assert(dirtyRejected, "change surface must fail closed on tracked dirtiness")

  console.log("CHANGE SURFACE STATE SMOKE PASS")
}

await main()
