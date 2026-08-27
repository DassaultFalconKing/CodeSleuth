import { mkdtemp, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"
import { resolveBuiltinProfile, resolveBuiltinProfiles } from "../pack/.opencode/tools/repo_profile"

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message)
}

async function expectFailure(operation: () => Promise<unknown>, contains: string) {
  try {
    await operation()
  } catch (error) {
    assert(String(error).includes(contains), `expected failure containing ${contains}, got ${String(error)}`)
    return
  }
  throw new Error(`expected failure containing ${contains}`)
}

async function main() {
  const builtinRoot = path.join(import.meta.dir, "..", "pack", ".opencode", "profiles", "builtin")
  const typescript = await resolveBuiltinProfile(builtinRoot, "typescript")
  assert(typescript.lineage.join(" -> ") === "node -> typescript", "typescript must resolve its declared node parent")
  const verification = typescript.profile.recommendedVerification as string[]
  const focus = typescript.profile.reviewFocus as string[]
  assert(verification.some((item) => item.includes("package manager")), "parent verification guidance must survive inheritance")
  assert(verification.some((item) => item.includes("typecheck")), "child verification guidance must be added")
  assert(focus.some((item) => item.includes("runtime/module-system")), "parent review focus must survive inheritance")
  assert(focus.some((item) => item.includes("unsound casts")), "child review focus must be added")
  assert(typescript.profile.extends === undefined, "resolved profiles must not leave an unresolved extends marker")

  const effective = await resolveBuiltinProfiles(builtinRoot, ["generic", "node", "typescript"])
  assert(effective.effectiveOrder.join(",") === "generic,node,typescript", "effective inheritance order must be deterministic and deduplicated")
  const effectiveFocus = effective.effective.reviewFocus as string[]
  assert(effectiveFocus.length === new Set(effectiveFocus).size, "inherited arrays must deduplicate deterministically")

  const invalidRoot = await mkdtemp(path.join(tmpdir(), "profile-smoke-"))
  await writeFile(path.join(invalidRoot, "missing.json"), JSON.stringify({ profile: "missing", extends: "ghost" }), "utf8")
  await expectFailure(() => resolveBuiltinProfile(invalidRoot, "missing"), "builtin profile not found: ghost")
  await writeFile(path.join(invalidRoot, "a.json"), JSON.stringify({ profile: "a", extends: "b" }), "utf8")
  await writeFile(path.join(invalidRoot, "b.json"), JSON.stringify({ profile: "b", extends: "a" }), "utf8")
  await expectFailure(() => resolveBuiltinProfile(invalidRoot, "a"), "inheritance cycle: a -> b -> a")

  console.log("PROFILE SMOKE PASS")
}

await main()
