from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

_INVALID_ID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def unsafe_id(value: Any) -> str:
    text = str(value).strip()
    if not text or text in {".", ".."} or _INVALID_ID.search(text) or ".." in text:
        raise ValueError(f"unsafe object id: {value!r}")
    return text


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.").lower()
    if not text:
        raise ValueError(f"unsafe schema/folder name: {value!r}")
    return text


def _values(record: dict[str, Any], fields: list[str]) -> list[str]:
    out: list[str] = []
    for field in fields:
        if field not in record or record[field] is None:
            continue
        value = record[field]
        items = value if isinstance(value, list) else [value]
        for item in items:
            if isinstance(item, (str, int)):
                out.append(unsafe_id(item))
    return out


@dataclass(frozen=True)
class ProjectionProfile:
    profile_id: str
    profile_version: int
    schema_fields: tuple[str, ...]
    default_id_fields: tuple[str, ...]
    kinds: dict[str, dict[str, Any]]
    bases: tuple[dict[str, Any], ...]

    @classmethod
    def load(cls, path: str | Path) -> "ProjectionProfile":
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            profile_id=str(doc["profileId"]),
            profile_version=int(doc.get("profileVersion", 1)),
            schema_fields=tuple(doc.get("schemaFieldCandidates", ["schemaId", "schema", "type"])),
            default_id_fields=tuple(doc.get("defaultIdFields", ["id", "objectId"])),
            kinds=dict(doc.get("kinds", {})),
            bases=tuple(doc.get("bases", [])),
        )

    def classify(self, record: dict[str, Any]) -> str:
        for field in self.schema_fields:
            value = record.get(field)
            if value:
                return str(value)
        raise ValueError("record has no schema identifier")

    def object_id(self, schema_id: str, record: dict[str, Any]) -> str:
        spec = self.kinds.get(schema_id, {})
        fields = list(spec.get("idFields", [])) + [f for f in self.default_id_fields if f not in spec.get("idFields", [])]
        for field in fields:
            value = record.get(field)
            if value is not None and str(value).strip():
                return unsafe_id(value)
        raise ValueError(f"record {schema_id!r} has no stable object id")

    def folder(self, schema_id: str) -> str:
        return _slug(str(self.kinds.get(schema_id, {}).get("folder", schema_id)))

    def relations(self, schema_id: str, record: dict[str, Any]) -> list[tuple[str, str]]:
        relation_spec = self.kinds.get(schema_id, {}).get("relations", {})
        out: set[tuple[str, str]] = set()
        for relation, fields in relation_spec.items():
            for target in _values(record, list(fields)):
                out.add((str(relation), target))
        return sorted(out)
