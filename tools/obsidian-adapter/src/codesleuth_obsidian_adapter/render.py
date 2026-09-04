from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from .bases import render_bases
from .canvas import render_standard_canvases
from .manifest import RENDERER_ID, RENDERER_VERSION, build_manifest, write_manifest
from .profile import ProjectionProfile
from .serialization import canonical_json, yaml_property_lines, yaml_scalar


@dataclass(frozen=True)
class NormalizedObject:
    schema_id: str
    object_id: str
    folder: str
    source_digest: str
    record: dict[str, Any]
    relations: tuple[tuple[str, str], ...]
    note_path: str


def _source_digest(record: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(record).encode("utf-8")).hexdigest()


def normalize_records(records: Iterable[dict[str, Any]], profile: ProjectionProfile) -> list[NormalizedObject]:
    result: list[NormalizedObject] = []
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("every input record must be a JSON object")
        schema_id = profile.classify(record)
        object_id = profile.object_id(schema_id, record)
        if object_id in seen:
            raise ValueError(f"duplicate object id: {object_id}")
        seen.add(object_id)
        folder = profile.folder(schema_id)
        note_path = f"objects/{folder}/{object_id}.md"
        result.append(NormalizedObject(
            schema_id=schema_id,
            object_id=object_id,
            folder=folder,
            source_digest=_source_digest(record),
            record=dict(record),
            relations=tuple(profile.relations(schema_id, record)),
            note_path=note_path,
        ))
    return sorted(result, key=lambda x: x.object_id)


def render_note(obj: NormalizedObject) -> str:
    lines = [
        "---",
        "projectionAuthority: none",
        f"rendererId: {yaml_scalar(RENDERER_ID)}",
        f"rendererVersion: {yaml_scalar(RENDERER_VERSION)}",
        f"schemaId: {yaml_scalar(obj.schema_id)}",
        f"objectId: {yaml_scalar(obj.object_id)}",
        f"sourceDigest: {yaml_scalar(obj.source_digest)}",
    ]
    skip = {"schemaId", "schema", "codesleuth_schema", "type", "id", "objectId"}
    for key in sorted(obj.record):
        if key in skip or key.startswith("_"):
            continue
        value = obj.record[key]
        if isinstance(value, (str, int, float, bool)) or value is None or (
            isinstance(value, list) and all(isinstance(x, (str, int, float, bool)) or x is None for x in value)
        ):
            lines.extend(yaml_property_lines(key, value))
    lines.extend(["---", "", f"# {obj.object_id}", "", "> Derived projection. This note has no evidence authority.", ""])
    if obj.relations:
        lines.extend(["## Relations", ""])
        for relation, target in obj.relations:
            lines.append(f"- **{relation}** -> [[{target}]]")
        lines.append("")
    lines.extend(["## Structured source", "", "```json", json.dumps(obj.record, sort_keys=True, ensure_ascii=False, indent=2), "```", ""])
    return "\n".join(lines)


def _projection_readme(profile: ProjectionProfile, object_count: int) -> str:
    return (
        "# Derived Obsidian Projection\n\n"
        "`projectionAuthority: none`\n\n"
        "This vault is generated from structured source objects. Edits here do not change canonical evidence.\n\n"
        f"Profile: `{profile.profile_id}` v{profile.profile_version}; objects: {object_count}.\n"
    )


def _remove_previous_generated_outputs(root: Path) -> None:
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        return
    try:
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    if previous.get("projectionAuthority") != "none" or previous.get("roundTripCapability") != "RENDER_ONLY":
        return
    for item in previous.get("outputs", []):
        rel = item.get("path") if isinstance(item, dict) else None
        if not isinstance(rel, str):
            continue
        rel_path = Path(rel)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            continue
        candidate = root / rel_path
        if candidate.is_file():
            candidate.unlink()


def render_projection(records: Iterable[dict[str, Any]], profile: ProjectionProfile, output_dir: str | Path) -> dict:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    _remove_previous_generated_outputs(root)
    objects = normalize_records(records, profile)
    generated: list[Path] = []
    for obj in objects:
        path = root / obj.note_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_note(obj), encoding="utf-8", newline="\n")
        generated.append(path)
    generated.extend(render_bases(profile.bases, root / "views"))
    generated.extend(render_standard_canvases(objects, root / "graphs"))
    readme = root / "README.md"
    readme.write_text(_projection_readme(profile, len(objects)), encoding="utf-8", newline="\n")
    generated.append(readme)
    manifest = build_manifest(profile, objects, root, generated)
    write_manifest(manifest, root / "manifest.json")
    return manifest
