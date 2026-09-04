from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = 1

ROLE_BY_TYPE = {
    "Button": "button",
    "Input": "input",
    "Select": "select",
    "Switch": "switch",
    "Checkbox": "checkbox",
    "RadioButton": "radio",
    "Tab": "tab",
    "Tabs": "tabs",
    "ListItem": "item",
    "OptionList": "list",
    "DataTable": "table",
    "Label": "label",
    "Static": "static",
    "Header": "header",
    "Footer": "footer",
}

USER_REQUIRED_KEYS = {
    "role",
    "goal",
    "notice_first",
    "natural_next_action",
    "must_not_need_to_know",
    "success_visible_as",
    "confusion_if",
    "must_not_imply",
}


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = re.sub(r"\s+", " ", str(value)).strip()
    if text.startswith("<") and text.endswith(">"):
        return ""
    return text[:1000]


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return _normalize_text(value)


def _visible(node: Any) -> bool:
    for attr in ("display", "visible"):
        value = getattr(node, attr, True)
        if value is False:
            return False
    return True


def _node_text(node: Any) -> str:
    for attr in ("label", "text", "placeholder"):
        value = getattr(node, attr, None)
        text = _normalize_text(value)
        if text:
            return text

    if node.__class__.__name__ in {"Static", "Label", "Header", "Footer"}:
        render = getattr(node, "render", None)
        if callable(render):
            try:
                return _normalize_text(render())
            except Exception:
                return ""
    return ""


def _node_state(node: Any) -> dict[str, Any]:
    state: dict[str, Any] = {}
    for attr in ("value", "disabled", "checked", "expanded", "has_focus"):
        if hasattr(node, attr):
            value = _jsonable(getattr(node, attr))
            if value not in (None, ""):
                state[attr] = value
    return state


def _iter_nodes(root: Any) -> Iterable[Any]:
    yield root
    walk_children = getattr(root, "walk_children", None)
    if callable(walk_children):
        yield from walk_children()


def semantic_snapshot(root: Any) -> dict[str, Any]:
    """Return a compact accessibility-like snapshot of user-relevant nodes.

    The raw snapshot keeps machine ids so a later coding pass can map the
    visible surface back to implementation. `render_semantic_text` hides them
    by default for model-as-user use.
    """

    title = _normalize_text(getattr(root, "title", None))
    nodes: list[dict[str, Any]] = []
    for node in _iter_nodes(root):
        if node is root or not _visible(node):
            continue
        type_name = node.__class__.__name__
        role = ROLE_BY_TYPE.get(type_name)
        if role is None:
            continue
        text = _node_text(node)
        state = _node_state(node)
        node_id = getattr(node, "id", None)
        if not text and not state and not node_id:
            continue
        entry: dict[str, Any] = {
            "role": role,
            "type": type_name,
        }
        if text:
            entry["text"] = text
        if node_id:
            entry["id"] = str(node_id)
        if state:
            entry["state"] = state
        nodes.append(entry)

    return {
        "schema_version": SCHEMA_VERSION,
        "screen_title": title,
        "screen_type": root.__class__.__name__,
        "nodes": nodes,
    }


def render_semantic_text(snapshot: dict[str, Any], *, include_machine_ids: bool = False) -> str:
    title = _normalize_text(snapshot.get("screen_title")) or "current screen"
    lines = [f"SCREEN {title}"]
    for node in snapshot.get("nodes", []):
        role = node.get("role", "control")
        text = _normalize_text(node.get("text"))
        state = node.get("state") or {}
        parts = [f"[{role}]", text or "(unlabelled)"]
        if state:
            rendered_state = ", ".join(f"{key}={value!r}" for key, value in sorted(state.items()))
            parts.append(f"({rendered_state})")
        if include_machine_ids:
            if node.get("type"):
                parts.append(f"type={node['type']}")
            if node.get("id"):
                parts.append(f"id=#{node['id']}")
        lines.append(" ".join(parts))
    return "\n".join(lines) + "\n"


def _validate_journey(data: dict[str, Any], *, source: str = "journey") -> dict[str, Any]:
    for key in ("id", "surface", "user", "entry", "trajectory", "affordances"):
        if key not in data:
            raise ValueError(f"{source}: missing top-level key {key!r}")
    if data["surface"] != "tui":
        raise ValueError(f"{source}: expected surface='tui', got {data['surface']!r}")
    user = data["user"]
    if not isinstance(user, dict):
        raise ValueError(f"{source}: user must be an object")
    missing = sorted(USER_REQUIRED_KEYS - set(user))
    if missing:
        raise ValueError(f"{source}: user is missing {', '.join(missing)}")
    if not isinstance(data["trajectory"], list) or not data["trajectory"]:
        raise ValueError(f"{source}: trajectory must contain at least one step")
    return data


def load_journey(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: journey must be a JSON object")
    return _validate_journey(data, source=str(path))


def render_user_probe(journey: dict[str, Any], semantic_text: str = "") -> str:
    """Render the default model-as-user input without implementation mapping."""

    user = journey["user"]
    lines = [
        "You are the operator, not the developer.",
        "Use only the user goal and visible/semantic UI evidence.",
        "Do not reason about classes, selectors, handlers or tests.",
        "",
        "USER ROLE:",
        str(user["role"]),
        "",
        "USER GOAL:",
        str(user["goal"]),
        "",
        "NOTICE FIRST:",
    ]
    lines.extend(f"- {item}" for item in user["notice_first"])
    lines.extend(["", "NATURAL NEXT ACTION:"])
    lines.extend(f"- {item}" for item in user["natural_next_action"])
    lines.extend(["", "SUCCESS LOOKS LIKE:"])
    lines.extend(f"- {item}" for item in user["success_visible_as"])
    lines.extend(["", "CONFUSION SIGNALS:"])
    lines.extend(f"- {item}" for item in user["confusion_if"])
    lines.extend(["", "MUST NOT IMPLY:"])
    lines.extend(f"- {item}" for item in user["must_not_imply"])

    lines.extend(["", "EXPECTED USER JOURNEY:"])
    for step in journey["trajectory"]:
        action = step.get("action") or {}
        label = action.get("label") or action.get("kind") or "inspect"
        expectation = step.get("user_expects", "")
        lines.append(f"- {step.get('state', 'state')}: {expectation} Action: {label}.")

    if semantic_text.strip():
        lines.extend(["", "VISIBLE / SEMANTIC UI:", semantic_text.strip()])

    lines.extend(
        [
            "",
            "ANSWER AS THE OPERATOR:",
            "1. What are you trying to accomplish?",
            "2. What would you do next?",
            "3. What do you believe the relevant visible controls do?",
            "4. What is confusing or misleading?",
            "5. Can you complete the stated goal from this interface?",
        ]
    )
    return "\n".join(lines) + "\n"


def _semantic_occurrences(snapshot: dict[str, Any]) -> dict[tuple[str, str, int], dict[str, Any]]:
    counts: dict[tuple[str, str], int] = {}
    result: dict[tuple[str, str, int], dict[str, Any]] = {}
    for node in snapshot.get("nodes", []):
        role = str(node.get("role") or "control")
        text = _normalize_text(node.get("text")) or "(unlabelled)"
        base = (role, text)
        counts[base] = counts.get(base, 0) + 1
        result[(role, text, counts[base])] = node
    return result


def _describe_key(key: tuple[str, str, int]) -> str:
    role, text, occurrence = key
    suffix = f" [{occurrence}]" if occurrence > 1 else ""
    return f"[{role}] {text}{suffix}"


def render_ux_diff(before: dict[str, Any], after: dict[str, Any]) -> str:
    """Render a user-facing semantic UI diff without implementation identifiers."""

    before_nodes = _semantic_occurrences(before)
    after_nodes = _semantic_occurrences(after)
    lines = ["USER EXPERIENCE DIFF"]

    before_title = _normalize_text(before.get("screen_title"))
    after_title = _normalize_text(after.get("screen_title"))
    if before_title != after_title:
        lines.append(f"SCREEN: {before_title or '(untitled)'} -> {after_title or '(untitled)'}")

    removed = sorted(set(before_nodes) - set(after_nodes))
    added = sorted(set(after_nodes) - set(before_nodes))
    changed: list[tuple[tuple[str, str, int], dict[str, Any], dict[str, Any]]] = []
    for key in sorted(set(before_nodes) & set(after_nodes)):
        before_state = before_nodes[key].get("state") or {}
        after_state = after_nodes[key].get("state") or {}
        if before_state != after_state:
            changed.append((key, before_state, after_state))

    lines.append("REMOVED:")
    lines.extend(f"- {_describe_key(key)}" for key in removed)
    if not removed:
        lines.append("- none")

    lines.append("ADDED:")
    lines.extend(f"- {_describe_key(key)}" for key in added)
    if not added:
        lines.append("- none")

    lines.append("STATE CHANGES:")
    for key, before_state, after_state in changed:
        lines.append(f"- {_describe_key(key)}: {before_state!r} -> {after_state!r}")
    if not changed:
        lines.append("- none")

    return "\n".join(lines) + "\n"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
    return slug or "state"


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


class WitnessRecorder:
    """Record a deterministic multi-state User Witness bundle.

    The recorder stores both a user-safe semantic representation and a
    developer mapping. Only the user-safe representation belongs in a
    model-as-user prompt.
    """

    def __init__(self, journey: dict[str, Any], output_dir: Path) -> None:
        self.journey = _validate_journey(dict(journey), source="journey")
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.states: list[dict[str, Any]] = []
        self._snapshots: list[dict[str, Any]] = []
        _write_json(self.output_dir / "journey.json", self.journey)

    def checkpoint(
        self,
        name: str,
        root: Any,
        *,
        screenshot_svg: str | None = None,
        action: dict[str, Any] | None = None,
        user_expects: str = "",
    ) -> dict[str, Any]:
        index = len(self.states)
        state_dir = self.output_dir / f"{index:02d}-{_slug(name)}"
        state_dir.mkdir(parents=True, exist_ok=True)

        snapshot = semantic_snapshot(root)
        _write_json(state_dir / "semantic.json", snapshot)
        (state_dir / "user-view.txt").write_text(render_semantic_text(snapshot), encoding="utf-8")
        (state_dir / "developer-view.txt").write_text(
            render_semantic_text(snapshot, include_machine_ids=True),
            encoding="utf-8",
        )
        (state_dir / "user-probe.txt").write_text(
            render_user_probe(self.journey, render_semantic_text(snapshot)),
            encoding="utf-8",
        )

        screenshot_name: str | None = None
        if screenshot_svg is not None:
            screenshot_name = "screen.svg"
            (state_dir / screenshot_name).write_text(screenshot_svg, encoding="utf-8")

        if self._snapshots:
            diff = render_ux_diff(self._snapshots[-1], snapshot)
        else:
            diff = "USER EXPERIENCE DIFF\nINITIAL STATE\n"
        (state_dir / "ux-diff.txt").write_text(diff, encoding="utf-8")

        state = {
            "index": index,
            "name": name,
            "action": action or {},
            "user_expects": user_expects,
            "screen_title": snapshot.get("screen_title", ""),
            "files": {
                "semantic": f"{state_dir.name}/semantic.json",
                "user_view": f"{state_dir.name}/user-view.txt",
                "developer_view": f"{state_dir.name}/developer-view.txt",
                "user_probe": f"{state_dir.name}/user-probe.txt",
                "ux_diff": f"{state_dir.name}/ux-diff.txt",
                "screenshot": f"{state_dir.name}/{screenshot_name}" if screenshot_name else None,
            },
        }
        self.states.append(state)
        self._snapshots.append(snapshot)
        return state

    def finalize(self) -> dict[str, Any]:
        trajectory = {
            "schema_version": SCHEMA_VERSION,
            "journey_id": self.journey["id"],
            "surface": self.journey["surface"],
            "states": self.states,
        }
        _write_json(self.output_dir / "trajectory.json", trajectory)

        combined_diff = []
        for state in self.states:
            diff_path = self.output_dir / state["files"]["ux_diff"]
            combined_diff.append(f"## {state['index']:02d} {state['name']}\n{diff_path.read_text(encoding='utf-8').strip()}")
        (self.output_dir / "ux-diff.txt").write_text("\n\n".join(combined_diff) + "\n", encoding="utf-8")

        manifest = {
            "schema_version": SCHEMA_VERSION,
            "kind": "codesleuth-user-witness",
            "journey_id": self.journey["id"],
            "surface": self.journey["surface"],
            "diagnostic_only": True,
            "acceptance_authority": False,
            "state_count": len(self.states),
            "files": {
                "journey": "journey.json",
                "trajectory": "trajectory.json",
                "ux_diff": "ux-diff.txt",
            },
            "states": self.states,
        }
        _write_json(self.output_dir / "manifest.json", manifest)
        return manifest


def capture_textual_checkpoint(
    app: Any,
    recorder: WitnessRecorder,
    name: str,
    *,
    action: dict[str, Any] | None = None,
    user_expects: str = "",
    include_screenshot: bool = True,
) -> dict[str, Any]:
    """Capture the current Textual screen without making Textual a hard import."""

    screenshot = None
    if include_screenshot:
        screenshot = app.export_screenshot(
            title=f"CodeSleuth User Witness: {recorder.journey['id']} / {name}",
            simplify=True,
        )
    return recorder.checkpoint(
        name,
        app.screen,
        screenshot_svg=screenshot,
        action=action,
        user_expects=user_expects,
    )


def _cmd_validate(paths: list[str]) -> int:
    for raw in paths:
        path = Path(raw)
        journey = load_journey(path)
        print(f"PASS {path}: {journey['id']}")
    return 0


def _cmd_render(path: str, semantic_path: str | None, machine_ids: bool) -> int:
    journey = load_journey(Path(path))
    semantic_text = ""
    if semantic_path:
        snapshot = json.loads(Path(semantic_path).read_text(encoding="utf-8"))
        semantic_text = render_semantic_text(snapshot, include_machine_ids=machine_ids)
    print(render_user_probe(journey, semantic_text), end="")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Experimental CodeSleuth TUI User Witness helpers")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate one or more TUI user-journey JSON files")
    validate.add_argument("paths", nargs="+")

    render = sub.add_parser("render", help="render a model-as-user prompt from a journey")
    render.add_argument("journey")
    render.add_argument("--semantic", help="optional semantic snapshot JSON")
    render.add_argument("--machine-ids", action="store_true", help="include implementation ids in semantic text")

    args = parser.parse_args()
    if args.command == "validate":
        return _cmd_validate(args.paths)
    return _cmd_render(args.journey, args.semantic, args.machine_ids)


if __name__ == "__main__":
    raise SystemExit(main())
