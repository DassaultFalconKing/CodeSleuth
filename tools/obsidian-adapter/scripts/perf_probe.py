from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from codesleuth_obsidian_adapter.profile import ProjectionProfile
from codesleuth_obsidian_adapter.render import render_projection


def synthetic_records(count: int) -> list[dict]:
    records = []
    for i in range(count):
        object_id = f"SYN-{i:06d}"
        records.append({
            "schemaId": "SyntheticObject",
            "id": object_id,
            "status": "open" if i % 7 else "closed",
            "result": "FAIL" if i % 13 == 0 else "PASS",
            "subjectSha": f"{i:040x}"[-40:],
            "stale": i % 17 == 0,
        })
    return records


def run(count: int, output: Path | None = None) -> dict:
    profile = ProjectionProfile.load(ROOT / "profiles" / "generic.json")
    own_tmp = output is None
    holder = tempfile.TemporaryDirectory(prefix="obsidian-adapter-") if own_tmp else None
    root = Path(holder.name) if holder else output
    start = time.perf_counter()
    manifest = render_projection(synthetic_records(count), profile, root)
    elapsed = time.perf_counter() - start
    total_bytes = sum(item["bytes"] for item in manifest["outputs"])
    result = {"objects": count, "seconds": round(elapsed, 3), "bytes": total_bytes, "objectsPerSecond": round(count / elapsed, 1)}
    if holder:
        holder.cleanup()
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("count", type=int, choices=[1000, 10000, 100000])
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    print(run(args.count, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
