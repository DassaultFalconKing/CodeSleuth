from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable


def _token(prefix: str, value: str) -> str:
    return f"{prefix}-{hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]}"


def render_canvas(name: str, objects: Iterable, allowed_schemas: set[str], output: Path) -> Path:
    selected = sorted((obj for obj in objects if obj.schema_id in allowed_schemas), key=lambda x: x.object_id)
    selected_ids = {obj.object_id for obj in selected}
    nodes = []
    for index, obj in enumerate(selected):
        nodes.append({
            "id": _token("node", obj.object_id),
            "type": "file",
            "file": obj.note_path,
            "x": (index % 4) * 340,
            "y": (index // 4) * 220,
            "width": 300,
            "height": 160,
        })
    node_map = {obj.object_id: _token("node", obj.object_id) for obj in selected}
    edges = []
    for obj in selected:
        for relation, target in obj.relations:
            if target not in selected_ids:
                continue
            edge_key = f"{obj.object_id}|{relation}|{target}"
            edges.append({
                "id": _token("edge", edge_key),
                "fromNode": node_map[obj.object_id],
                "toNode": node_map[target],
                "label": relation,
            })
    doc = {"nodes": nodes, "edges": sorted(edges, key=lambda x: x["id"])}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(doc, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return output


def render_standard_canvases(objects: Iterable, output_dir: Path) -> list[Path]:
    objects = list(objects)
    return [
        render_canvas(
            "repair-lineage",
            objects,
            {"EHACampaign", "RepairCaseV1", "RepairPacketV1", "RegressionWitness", "RepairLearningRecordV1"},
            output_dir / "repair-lineage.canvas",
        ),
        render_canvas(
            "contract-traceability",
            objects,
            {"Contract", "Finding", "RepairCaseV1", "RepairPacketV1", "RepairLearningRecordV1"},
            output_dir / "contract-traceability.canvas",
        ),
    ]
