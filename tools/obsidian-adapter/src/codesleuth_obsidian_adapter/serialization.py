from __future__ import annotations

import json
from typing import Any


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def yaml_property_lines(key: str, value: Any) -> list[str]:
    if isinstance(value, list) and all(isinstance(x, (str, int, float, bool)) or x is None for x in value):
        lines = [f"{key}:"]
        lines.extend(f"  - {yaml_scalar(item)}" for item in value)
        return lines
    return [f"{key}: {yaml_scalar(value)}"]


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
