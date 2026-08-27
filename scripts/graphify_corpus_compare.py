#!/usr/bin/env python3
"""Run deterministic Graphify structural comparisons over bounded fixture repositories."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import tracemalloc
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "scripts" / "graphify_adapter.py"
SPEC = importlib.util.spec_from_file_location("codesleuth_graphify_adapter", ADAPTER_PATH)
assert SPEC and SPEC.loader
ADAPTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTER)


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return completed.stdout.strip()


def _init_repo(root: Path) -> list[str]:
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "corpus@example.invalid")
    _git(root, "config", "user.name", "CodeSleuth Corpus")
    files = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.parts
    )
    _git(root, "add", "--", *files)
    _git(root, "commit", "-qm", "corpus fixture")
    return files


def _measure(root: Path, files: list[str], node_limit: int = 200) -> tuple[dict[str, Any], dict[str, Any]]:
    tracemalloc.start()
    started = time.perf_counter()
    result = ADAPTER.run_provider(root, files, node_limit=node_limit, edge_limit=500)
    wall_ms = round((time.perf_counter() - started) * 1_000, 3)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    exact_nodes = sum(node["origin"] == "verified_source" for node in result["nodes"])
    exact_edges = sum(edge["origin"] == "verified_source" for edge in result["edges"])
    return result, {
        "wallMs": wall_ms,
        "pythonPeakBytes": peak,
        "modelVisibleBytes": len(encoded),
        "returnedNodes": result["selection"]["returned"]["nodes"],
        "returnedEdges": result["selection"]["returned"]["edges"],
        "exactNodeRatio": round(exact_nodes / max(1, len(result["nodes"])), 4),
        "exactEdgeRatio": round(exact_edges / max(1, len(result["edges"])), 4),
        "truncated": result["selection"]["truncated"],
        "unmappedRelations": result["diagnostics"]["unmappedRelations"],
    }


def _fixture_cases(fixtures: Path, temporary: Path) -> list[tuple[str, Path, list[str]]]:
    cases: list[tuple[str, Path, list[str]]] = []
    for source in sorted(path for path in fixtures.iterdir() if path.is_dir()):
        target = temporary / source.name
        shutil.copytree(source, target)
        cases.append((source.name, target, _init_repo(target)))

    large = temporary / "large-over-limit"
    large.mkdir()
    (large / "large.py").write_text(
        "\n\n".join(f"def function_{index}():\n    return {index}" for index in range(260)) + "\n",
        encoding="utf-8",
    )
    cases.append(("large-over-limit", large, _init_repo(large)))

    odd = temporary / "odd-encoding"
    odd.mkdir()
    (odd / "legacy.py").write_bytes(b"# coding: latin-1\nvalue = '\xff'\n")
    cases.append(("odd-encoding", odd, _init_repo(odd)))
    return cases


def run(fixtures: Path, *, check: bool) -> dict[str, Any]:
    expectations = json.loads((fixtures / "expectations.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    results: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="codesleuth-graphify-corpus-") as directory:
        temporary = Path(directory)
        for name, root, files in _fixture_cases(fixtures, temporary):
            limit = 25 if name == "large-over-limit" else 200
            result, metrics = _measure(root, files, node_limit=limit)
            expected = expectations.get(name, {})
            if metrics["returnedNodes"] < expected.get("minNodes", 1):
                failures.append(f"{name}: returned too few useful nodes")
            if metrics["returnedEdges"] < expected.get("minMappedEdges", 0):
                failures.append(f"{name}: returned too few mapped edges")
            if name == "large-over-limit" and not metrics["truncated"]:
                failures.append("large-over-limit: expected explicit truncation")
            if any(edge["relation"] not in {"imports", "calls"} for edge in result["edges"]):
                failures.append(f"{name}: provider ontology escaped the closed mapping")
            results[name] = metrics

    # Directly exercise repository-specific extraction without copying or mutating it.
    self_files = ["scripts/graphify_adapter.py", "scripts/mermaid_qa.py"]
    _, self_metrics = _measure(ROOT, self_files, node_limit=200)
    results["codesleuth-self"] = self_metrics

    report = {
        "schemaVersion": 1,
        "provider": {
            "package": ADAPTER.PROVIDER_PACKAGE,
            "version": ADAPTER.PROVIDER_VERSION,
            "upstreamCommit": ADAPTER.PROVIDER_COMMIT,
        },
        "measurementScope": {
            "precisionProxy": "ratio of returned candidates retaining exact Git/blob promotion",
            "recallProxy": "fixture minimum useful structural nodes/edges; not semantic recall",
            "memory": "Python tracemalloc peak; native parser allocations may be excluded",
            "tokens": "modelVisibleBytes reported; no unsupported token-savings claim",
        },
        "cases": results,
        "failures": failures,
        "passed": not failures,
    }
    if check and failures:
        raise RuntimeError("; ".join(failures))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output: Path | None = None
    if args.output:
        output = args.output.resolve()
        runtime_root = (ROOT / ".runtime").resolve()
        try:
            output.relative_to(runtime_root)
        except ValueError:
            print(
                json.dumps(
                    {"schemaVersion": 1, "passed": False, "error": "output must remain under ignored .runtime/"},
                    indent=2,
                )
            )
            return 2
    try:
        report = run(args.fixtures.resolve(), check=args.check)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(json.dumps({"schemaVersion": 1, "passed": False, "error": str(error)}, indent=2))
        return 2
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(f"{rendered}\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
