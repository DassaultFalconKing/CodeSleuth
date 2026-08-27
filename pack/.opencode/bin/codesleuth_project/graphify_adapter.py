#!/usr/bin/env python3
"""Fail-closed installed CodeSleuth adapter for Graphify's local structural extractor."""

from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path, PurePosixPath
import socket
import subprocess
import sys
import tempfile
from typing import Any


_MODULE_PATH = Path(__file__).resolve()
ROOT = _MODULE_PATH.parents[4] if _MODULE_PATH.parents[3].name == "pack" else _MODULE_PATH.parents[3]
DEFAULT_RUNTIME = ROOT / ".runtime" / "graphify-provider"
PROVIDER_PACKAGE = "graphifyy"
PROVIDER_VERSION = "0.9.50"
PROVIDER_COMMIT = "43d54acbfa9e731f7a592bb582c1f4b9d48ed73e"
MAX_FILES = 200
MAX_SOURCE_BYTES = 10_000_000
MAX_NODES = 500
MAX_EDGES = 1_000
ALLOWED_RELATIONS = {"imports": "imports", "calls": "calls"}
CONFIDENCES = {"EXTRACTED", "INFERRED", "AMBIGUOUS"}


class AdapterError(RuntimeError):
    pass


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AdapterError(completed.stderr.strip() or f"git {' '.join(args)} failed")
    return completed.stdout.strip()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(131_072), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or any(ord(char) < 32 for char in value):
        raise AdapterError(f"invalid provider input path: {value!r}")
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise AdapterError(f"provider input must be a normalized repository-relative path: {value!r}")
    return candidate.as_posix()


def validate_inputs(root: Path, requested_files: list[str]) -> tuple[list[Path], dict[str, dict[str, Any]]]:
    root = root.resolve()
    top = Path(_git(root, "rev-parse", "--show-toplevel")).resolve()
    if top != root:
        raise AdapterError(f"explicit root must equal Git worktree root: {root} != {top}")
    normalized = sorted({_safe_relative_path(value) for value in requested_files})
    if not normalized:
        raise AdapterError("provider input manifest is empty")
    if len(normalized) > MAX_FILES:
        raise AdapterError(f"provider input exceeds {MAX_FILES} file bound")

    absolute_files: list[Path] = []
    provenance: dict[str, dict[str, Any]] = {}
    total_bytes = 0
    for relative in normalized:
        stage = _git(root, "ls-files", "--stage", "--", relative)
        lines = [line for line in stage.splitlines() if line]
        if len(lines) != 1:
            raise AdapterError(f"provider input is not one tracked stage-0 file: {relative}")
        metadata, tracked_path = lines[0].split("\t", 1)
        mode, index_blob, stage_number = metadata.split()
        if tracked_path.replace("\\", "/") != relative or stage_number != "0":
            raise AdapterError(f"provider input has ambiguous index identity: {relative}")
        if mode not in {"100644", "100755"}:
            raise AdapterError(f"provider input is not a regular tracked file ({mode}): {relative}")
        absolute = (root / Path(*PurePosixPath(relative).parts)).resolve()
        try:
            absolute.relative_to(root)
        except ValueError as error:
            raise AdapterError(f"provider input escapes worktree: {relative}") from error
        if not absolute.is_file() or absolute.is_symlink():
            raise AdapterError(f"provider input is missing, non-regular, or a symlink: {relative}")
        size = absolute.stat().st_size
        total_bytes += size
        if total_bytes > MAX_SOURCE_BYTES:
            raise AdapterError(f"provider inputs exceed {MAX_SOURCE_BYTES} byte bound")
        working_blob = _git(root, "hash-object", "--", relative)
        absolute_files.append(absolute)
        provenance[relative] = {
            "path": relative,
            "mode": mode,
            "indexBlob": index_blob,
            "workingBlob": working_blob,
            "contentSha256": _sha256_file(absolute),
            "bytes": size,
            "exactIndexMatch": working_blob == index_blob,
        }
    return absolute_files, provenance


def _source_ref(node: dict[str, Any], provenance: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    raw = node.get("source_file")
    if not isinstance(raw, str) or not raw:
        return None
    try:
        relative = _safe_relative_path(raw.replace("\\", "/"))
    except AdapterError:
        return None
    return provenance.get(relative)


def normalize_extraction(
    extraction: dict[str, Any],
    provenance: dict[str, dict[str, Any]],
    *,
    node_limit: int = MAX_NODES,
    edge_limit: int = MAX_EDGES,
) -> dict[str, Any]:
    raw_nodes = extraction.get("nodes")
    raw_edges = extraction.get("edges")
    if not isinstance(raw_nodes, list) or not isinstance(raw_edges, list):
        raise AdapterError("Graphify extraction must contain node and edge arrays")

    node_limit = min(max(1, node_limit), MAX_NODES)
    edge_limit = min(max(1, edge_limit), MAX_EDGES)
    nodes_by_provider_id: dict[str, dict[str, Any]] = {}
    diagnostics = {
        "invalidNodes": 0,
        "invalidEdges": 0,
        "unmappedRelations": {},
        "confidenceCounts": {confidence: 0 for confidence in sorted(CONFIDENCES)},
        "droppedEdges": 0,
    }
    candidates: list[dict[str, Any]] = []
    for raw_node in raw_nodes:
        if not isinstance(raw_node, dict) or not isinstance(raw_node.get("id"), str):
            diagnostics["invalidNodes"] += 1
            continue
        provider_id = raw_node["id"]
        if provider_id in nodes_by_provider_id:
            diagnostics["invalidNodes"] += 1
            continue
        ref = _source_ref(raw_node, provenance)
        label = raw_node.get("label") if isinstance(raw_node.get("label"), str) else provider_id
        if ref:
            basename = PurePosixPath(ref["path"]).name
            kind = "file" if label == basename and not raw_node.get("_callable") else "symbol"
            key = ref["path"] if kind == "file" else f"{label}@{ref['path']}"
        else:
            kind = "external"
            key = label
        candidate = {
            "providerId": provider_id,
            "kind": kind,
            "key": key,
            "label": label,
            "sourceLocation": raw_node.get("source_location") or None,
            "sourceRef": ref,
            "origin": "verified_source" if ref and ref["exactIndexMatch"] else "review_inference",
            "providerMetadata": {"fileType": raw_node.get("file_type"), "origin": raw_node.get("_origin")},
        }
        if candidate["origin"] == "verified_source":
            source_ref: dict[str, Any] = {"path": ref["path"], "blobHash": ref["indexBlob"]}
            location = raw_node.get("source_location")
            if isinstance(location, str) and location.startswith("L") and location[1:].isdigit():
                source_ref["startLine"] = int(location[1:])
            candidate["projectionInput"] = {
                "kind": kind,
                "key": key,
                "label": label,
                "origin": "verified_source",
                "path": source_ref["path"],
                **({"startLine": source_ref["startLine"]} if "startLine" in source_ref else {}),
            }
        else:
            candidate["projectionInput"] = {
                "kind": kind,
                "key": key,
                "label": label,
                "origin": "review_inference",
                "note": "Graphify candidate lacks exact tracked source identity",
            }
        nodes_by_provider_id[provider_id] = candidate
        candidates.append(candidate)

    normalized_edges: list[dict[str, Any]] = []
    for raw_edge in raw_edges:
        if not isinstance(raw_edge, dict):
            diagnostics["invalidEdges"] += 1
            continue
        source = nodes_by_provider_id.get(raw_edge.get("source"))
        target = nodes_by_provider_id.get(raw_edge.get("target"))
        relation = raw_edge.get("relation")
        confidence = raw_edge.get("confidence")
        if not source or not target or confidence not in CONFIDENCES or not isinstance(relation, str):
            diagnostics["invalidEdges"] += 1
            diagnostics["droppedEdges"] += 1
            continue
        diagnostics["confidenceCounts"][confidence] += 1
        mapped_relation = ALLOWED_RELATIONS.get(relation)
        if not mapped_relation:
            unmapped = diagnostics["unmappedRelations"]
            unmapped[relation] = unmapped.get(relation, 0) + 1
            diagnostics["droppedEdges"] += 1
            continue
        exact = (
            confidence == "EXTRACTED"
            and source["sourceRef"] is not None
            and target["sourceRef"] is not None
            and source["sourceRef"]["exactIndexMatch"]
            and target["sourceRef"]["exactIndexMatch"]
        )
        projection_edge: dict[str, Any] = {
            "sourceKind": source["kind"],
            "sourceKey": source["key"],
            "targetKind": target["kind"],
            "targetKey": target["key"],
            "relation": mapped_relation if exact else "review_inference",
            "origin": "verified_source" if exact else "review_inference",
        }
        if exact:
            edge_source_file = raw_edge.get("source_file")
            edge_ref = provenance.get(str(edge_source_file).replace("\\", "/"))
            if edge_ref and edge_ref["exactIndexMatch"]:
                projection_edge["path"] = edge_ref["path"]
                edge_location = raw_edge.get("source_location")
                if isinstance(edge_location, str) and edge_location.startswith("L") and edge_location[1:].isdigit():
                    projection_edge["startLine"] = int(edge_location[1:])
            else:
                exact = False
                projection_edge = {
                    "sourceKind": projection_edge["sourceKind"],
                    "sourceKey": projection_edge["sourceKey"],
                    "targetKind": projection_edge["targetKind"],
                    "targetKey": projection_edge["targetKey"],
                    "relation": "review_inference",
                    "origin": "review_inference",
                }
        if not exact:
            projection_edge["note"] = f"Graphify {confidence} candidate relation {mapped_relation}; not exact verified linkage"
        normalized_edges.append(
            {
                "sourceProviderId": source["providerId"],
                "targetProviderId": target["providerId"],
                "relation": mapped_relation,
                "origin": "verified_source" if exact else "review_inference",
                "confidence": confidence,
                "note": None if exact else f"Graphify {confidence}; not promoted as exact verified linkage",
                "sourceLocation": raw_edge.get("source_location") or None,
                "projectionInput": projection_edge,
            }
        )

    candidates.sort(key=lambda node: (node["kind"], node["key"], node["providerId"]))
    normalized_edges.sort(
        key=lambda edge: (edge["sourceProviderId"], edge["relation"], edge["targetProviderId"])
    )
    shown_nodes = candidates[:node_limit]
    shown_ids = {node["providerId"] for node in shown_nodes}
    eligible_edges = [
        edge
        for edge in normalized_edges
        if edge["sourceProviderId"] in shown_ids and edge["targetProviderId"] in shown_ids
    ]
    shown_edges = eligible_edges[:edge_limit]
    return {
        "nodes": shown_nodes,
        "edges": shown_edges,
        "selection": {
            "limits": {"nodes": node_limit, "edges": edge_limit},
            "totals": {"nodes": len(candidates), "edges": len(normalized_edges)},
            "returned": {"nodes": len(shown_nodes), "edges": len(shown_edges)},
            "truncated": len(shown_nodes) < len(candidates) or len(shown_edges) < len(eligible_edges),
        },
        "diagnostics": diagnostics,
    }


def _disable_network() -> tuple[Any, Any]:
    original_connect = socket.socket.connect
    original_create_connection = socket.create_connection

    def denied(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("network disabled by CodeSleuth Graphify adapter")

    socket.socket.connect = denied  # type: ignore[method-assign]
    socket.create_connection = denied  # type: ignore[assignment]
    return original_connect, original_create_connection


def provider_status(runtime: Path = DEFAULT_RUNTIME) -> dict[str, Any]:
    runtime = runtime.resolve()
    resolved_version: str | None = None
    if runtime.is_dir():
        for distribution in importlib.metadata.distributions(path=[str(runtime)]):
            if distribution.metadata.get("Name", "").lower() == PROVIDER_PACKAGE:
                resolved_version = distribution.version
                break
    available = resolved_version == PROVIDER_VERSION
    return {
        "schemaVersion": 1,
        "provider": "graphify",
        "status": "available" if available else "unavailable",
        "installed": resolved_version is not None,
        "compatible": available,
        "expected": {"package": PROVIDER_PACKAGE, "version": PROVIDER_VERSION, "upstreamCommit": PROVIDER_COMMIT},
        "resolved": {"version": resolved_version, "runtime": str(runtime)},
        "capabilities": ["local_structural_extract", "bounded_candidate_projection"],
        "permissions": {
            "trackedFilesRead": True,
            "ignoredLocalCacheWrite": "temporary only",
            "network": False,
            "semanticLlm": False,
            "gitMutation": False,
            "trackedWrite": False,
        },
        "defaultProvider": False,
        "removal": ".opencode/bin/codesleuth-project --remove-graphify-runtime .",
    }


def run_provider(
    root: Path,
    files: list[str],
    *,
    runtime: Path = DEFAULT_RUNTIME,
    node_limit: int = MAX_NODES,
    edge_limit: int = MAX_EDGES,
) -> dict[str, Any]:
    absolute_files, provenance = validate_inputs(root, files)
    runtime = runtime.resolve()
    if not runtime.is_dir():
        raise AdapterError(
            "optional Graphify runtime unavailable; explicitly install graphifyy==0.9.50 "
            "under .runtime/graphify-provider"
        )
    sys.path.insert(0, str(runtime))
    try:
        version = importlib.metadata.version(PROVIDER_PACKAGE)
        if version != PROVIDER_VERSION:
            raise AdapterError(f"expected exact {PROVIDER_PACKAGE} {PROVIDER_VERSION}, found {version}")
        from graphify.extract import extract  # type: ignore[import-not-found]
        from graphify.build import build  # type: ignore[import-not-found]
        from graphify.cluster import cluster  # type: ignore[import-not-found]
    except (ImportError, importlib.metadata.PackageNotFoundError) as error:
        raise AdapterError(f"optional Graphify runtime unavailable: {error}") from error

    original_connect, original_create_connection = _disable_network()
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    try:
        with tempfile.TemporaryDirectory(prefix="codesleuth-graphify-cache-") as cache_dir:
            with redirect_stdout(captured_stdout), redirect_stderr(captured_stderr):
                extraction = extract(
                    absolute_files,
                    root=root.resolve(),
                    cache_root=Path(cache_dir),
                    parallel=False,
                )
                graph = build([extraction])
                communities = cluster(graph)
    finally:
        socket.socket.connect = original_connect  # type: ignore[method-assign]
        socket.create_connection = original_create_connection  # type: ignore[assignment]

    normalized = normalize_extraction(
        extraction,
        provenance,
        node_limit=node_limit,
        edge_limit=edge_limit,
    )
    community_by_id = {
        str(node_id): str(community_id)
        for community_id, node_ids in communities.items()
        for node_id in node_ids
    }
    denominator = max(1, graph.number_of_nodes() - 1)
    centrality = {str(node_id): round(graph.degree(node_id) / denominator, 8) for node_id in graph.nodes}
    for node in normalized["nodes"]:
        provider_id = node["providerId"]
        node["topologyHint"] = {
            "community": community_by_id.get(provider_id),
            "centrality": centrality.get(provider_id, 0.0),
        }
    return {
        "schemaVersion": 1,
        "provider": {
            "id": "graphify",
            "package": PROVIDER_PACKAGE,
            "version": version,
            "upstreamCommit": PROVIDER_COMMIT,
            "mode": "local_structural_library_only",
            "network": False,
            "semanticLlm": False,
        },
        "authority": {
            "kind": "candidate_structural_provider",
            "statement": "tracked Git/blob validation remains CodeSleuth authority",
        },
        "input": {
            "root": str(root.resolve()),
            "files": [provenance[key] for key in sorted(provenance)],
            "fileCount": len(provenance),
            "totalBytes": sum(item["bytes"] for item in provenance.values()),
        },
        "providerDiagnostics": {
            "stdout": captured_stdout.getvalue()[:4_000],
            "stderr": captured_stderr.getvalue()[:4_000],
            "failedSources": extraction.get("failed_sources", []),
        },
        "topology": {
            "derivedSelectionHintsOnly": True,
            "algorithm": "graphify.cluster+undirected_degree_centrality",
            "algorithmVersion": 1,
            "graphNodes": graph.number_of_nodes(),
            "graphEdges": graph.number_of_edges(),
            "communities": len(communities),
            "hintedReturnedNodes": sum(node["topologyHint"]["community"] is not None for node in normalized["nodes"]),
        },
        **normalized,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    if args.status:
        print(json.dumps(provider_status(args.runtime), indent=2, sort_keys=True))
        return 0
    try:
        request = json.load(sys.stdin)
        if not isinstance(request, dict):
            raise AdapterError("request must be a JSON object")
        result = run_provider(
            Path(request.get("root", "")),
            request.get("files", []),
            runtime=args.runtime,
            node_limit=request.get("nodeLimit", MAX_NODES),
            edge_limit=request.get("edgeLimit", MAX_EDGES),
        )
    except (AdapterError, OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        print(json.dumps({"schemaVersion": 1, "status": "error", "error": str(error)}, indent=2))
        return 2
    print(json.dumps({"status": "ok", **result}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
