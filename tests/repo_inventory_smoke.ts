import { mkdtemp, readFile, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"
import inventory from "../pack/.opencode/tools/repo_inventory"

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message)
}

async function git(root: string, args: string[]): Promise<string> {
  const proc = Bun.spawn(["git", "-C", root, ...args], { stdout: "pipe", stderr: "pipe" })
  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  if ((await proc.exited) !== 0) throw new Error(stderr.trim() || `git ${args.join(" ")} failed`)
  return stdout.trim()
}

async function main() {
  const root = await mkdtemp(path.join(tmpdir(), "repo-inventory-smoke-"))
  await git(root, ["init", "-b", "main"])
  await writeFile(path.join(root, "tracked.txt"), "unborn\n", "utf8")
  await git(root, ["add", "tracked.txt"])

  const context = {
    worktree: root,
    directory: root,
    sessionID: "unborn-inventory-session",
    messageID: "message-1",
    agent: "build",
  } as any

  const unborn = JSON.parse(await inventory.execute({}, context))
  assert(unborn.headSha === null, "an unborn repository must not invent a HEAD SHA")
  assert(unborn.headState === "unborn", "an unborn repository must disclose its HEAD state")
  assert(unborn.trackedFiles === 1 && unborn.paths[0] === "tracked.txt", "staged files remain inventory evidence before the first commit")
  assert(unborn.dirty === true, "the staged unborn repository is dirty")
  const manifest = JSON.parse(await readFile(path.join(root, unborn.manifestPath), "utf8"))
  assert(manifest.headSha === null && manifest.headState === "unborn", "durable inventory records the same truthful unborn identity")

  await git(root, ["config", "user.email", "codesleuth-ci@example.invalid"])
  await git(root, ["config", "user.name", "CodeSleuth CI"])
  await git(root, ["commit", "-m", "first commit"])
  const committed = JSON.parse(await inventory.execute({}, { ...context, sessionID: "committed-inventory-session" }))
  assert(committed.headState === "committed", "committed repositories disclose committed HEAD state")
  assert(typeof committed.headSha === "string" && committed.headSha.length === 40, "committed repositories retain exact HEAD identity")

  console.log("REPO INVENTORY SMOKE PASS")
}

await main()
