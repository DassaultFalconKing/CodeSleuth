import type { Plugin } from "@opencode-ai/plugin"
import { readFile } from "node:fs/promises"
import path from "node:path"

async function readOptional(file: string): Promise<string | undefined> {
  try {
    return await readFile(file, "utf8")
  } catch (error: any) {
    if (error?.code === "ENOENT") return undefined
    throw error
  }
}

export const ReviewCompaction: Plugin = async ({ worktree }) => {
  const root = worktree || process.cwd()
  return {
    "experimental.session.compacting": async (input, output) => {
      const base = path.join(root, ".opencode", "state", "reviews")
      const reviewId = (await readOptional(path.join(base, "sessions", `${input.sessionID}.txt`)))?.trim()
      if (!reviewId || !/^[A-Za-z0-9._-]+$/.test(reviewId)) return

      const stateRaw = await readOptional(path.join(base, reviewId, "state.json"))
      if (!stateRaw) return
      const state = JSON.parse(stateRaw)
      const findingRaw = await readOptional(path.join(base, reviewId, "findings.ndjson"))
      const findings = findingRaw
        ? findingRaw
            .trim()
            .split("\n")
            .filter(Boolean)
            .slice(-100)
            .map((line) => JSON.parse(line))
            .map((finding) => ({
              id: finding.id,
              severity: finding.severity,
              title: finding.title,
              path: finding.path,
              startLine: finding.startLine,
              endLine: finding.endLine,
              blobHash: finding.blobHash,
            }))
        : []

      const inventoryPath = path.join(root, ".opencode", "state", "inventory", `${input.sessionID}.json`)
      const hasInventory = Boolean(await readOptional(inventoryPath))

      output.context.push(`
## Durable repository review checkpoint

This is authoritative continuation state written by repository review tools.
Do not restart completed discovery after compaction.

${JSON.stringify(
  {
    reviewId,
    objective: state.objective,
    target: state.target,
    headSha: state.headSha,
    phase: state.phase,
    completed: state.completed,
    reviewedPaths: state.reviewedPaths,
    openQuestions: state.openQuestions,
    next: state.next,
    note: state.note,
    findings,
    inventoryManifest: hasInventory ? `.opencode/state/inventory/${input.sessionID}.json` : null,
  },
  null,
  2,
)}

After compaction, call review_state_load before accepting new findings. Re-open
exact source evidence before relying on a recorded finding if HEAD/worktree has
changed.
`)
    },
  }
}
