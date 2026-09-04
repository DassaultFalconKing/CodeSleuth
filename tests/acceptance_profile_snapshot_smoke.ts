import { compileAcceptanceProfileSnapshotV1 } from "../pack/.opencode/tools/acceptance_profile_snapshot"

if (typeof compileAcceptanceProfileSnapshotV1 !== "function") {
  throw new Error("W7 compiler boundary is missing")
}

console.log("acceptance profile snapshot smoke: module present")
