from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .manifest import sha256_file
from .profile import ProjectionProfile
from .render import render_projection


def load_records(path: str | Path) -> list[dict[str, Any]]:
    text = Path(path).read_text(encoding="utf-8")
    try:
        value = json.loads(text)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            return [value]
    except json.JSONDecodeError:
        pass
    records = []
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid NDJSON at line {line_no}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"NDJSON line {line_no} is not an object")
        records.append(value)
    return records


def validate_vault(root: str | Path) -> None:
    root = Path(root)
    manifest_path = root / "manifest.json"
    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    if doc.get("projectionAuthority") != "none" or doc.get("roundTripCapability") != "RENDER_ONLY":
        raise ValueError("manifest violates read-only projection authority contract")
    for item in doc.get("outputs", []):
        path = root / item["path"]
        if not path.is_file() or sha256_file(path) != item["sha256"]:
            raise ValueError(f"projection output digest mismatch: {item['path']}")
    for note in (root / "objects").rglob("*.md") if (root / "objects").exists() else []:
        if "projectionAuthority: none" not in note.read_text(encoding="utf-8"):
            raise ValueError(f"missing non-authority marker: {note.relative_to(root)}")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="codesleuth-obsidian")
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("render")
    r.add_argument("--input", required=True)
    r.add_argument("--profile", required=True)
    r.add_argument("--output", required=True)
    v = sub.add_parser("validate")
    v.add_argument("--vault", required=True)
    m = sub.add_parser("manifest")
    m.add_argument("--vault", required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "render":
        profile = ProjectionProfile.load(args.profile)
        manifest = render_projection(load_records(args.input), profile, args.output)
        print(json.dumps({"objects": len(manifest["sources"]), "output": str(args.output)}, sort_keys=True))
        return 0
    if args.command == "validate":
        validate_vault(args.vault)
        print("VALID")
        return 0
    if args.command == "manifest":
        print((Path(args.vault) / "manifest.json").read_text(encoding="utf-8"), end="")
        return 0
    return 2
