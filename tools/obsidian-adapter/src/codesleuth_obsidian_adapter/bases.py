from __future__ import annotations

from pathlib import Path
import re
from .serialization import yaml_scalar


def _file_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-.").lower() + ".base"


def render_bases(base_specs: tuple[dict, ...], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for spec in sorted(base_specs, key=lambda x: str(x.get("name", ""))):
        name = str(spec["name"])
        expr = str(spec.get("filter", "true"))
        text = "\n".join([
            "filters:",
            "  and:",
            '    - \'projectionAuthority == "none"\'',
            "views:",
            "  - type: table",
            f"    name: {yaml_scalar(name)}",
            f"    filters: {yaml_scalar(expr)}",
            "    order:",
            "      - file.name",
            "      - schemaId",
            "      - objectId",
            "",
        ])
        path = output_dir / _file_name(name)
        path.write_text(text, encoding="utf-8", newline="\n")
        paths.append(path)
    return paths
