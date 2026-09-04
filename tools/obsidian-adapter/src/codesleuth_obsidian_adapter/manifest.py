from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

RENDERER_ID = "obsidian-vault"
RENDERER_VERSION = "0.1.0"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def build_manifest(profile, objects: Iterable, output_root: Path, generated_paths: Iterable[Path]) -> dict:
    outputs = []
    for path in sorted(set(generated_paths), key=lambda p: p.as_posix()):
        rel = path.relative_to(output_root).as_posix()
        outputs.append({"path": rel, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    sources = [
        {"objectId": obj.object_id, "schemaId": obj.schema_id, "sourceDigest": obj.source_digest}
        for obj in sorted(objects, key=lambda x: x.object_id)
    ]
    return {
        "rendererId": RENDERER_ID,
        "rendererVersion": RENDERER_VERSION,
        "acceptedSchemaIds": sorted({obj.schema_id for obj in objects}),
        "roundTripCapability": "RENDER_ONLY",
        "projectionAuthority": "none",
        "profile": {"id": profile.profile_id, "version": profile.profile_version},
        "sources": sources,
        "outputs": outputs,
    }


def write_manifest(manifest: dict, path: Path) -> None:
    path.write_text(json.dumps(manifest, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
