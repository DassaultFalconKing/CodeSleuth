#!/usr/bin/env python3
"""Discover, validate, and overlay-install stored Playbooks. Does not execute Steps."""

from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

# Inverse of tests/test_playbook_skill_contract.py::test_product_commands_route_broad_work_to_playbooks
COMMAND_ALIASES: dict[str, str] = {
    "repository-deep-review": "/repo-review",
    "protected-capability-assessment": "/repo-contracts",
    "repository-documentation": "/repo-docs",
    "repository-map": "/repo-map",
    "feature-port": "/repo-port",
    "eha-sib-acceptance": "/eha-test",
    "eha-repair": "/eha-repair",
}

_MAX_ZIP_ENTRIES = 200
_MAX_ZIP_UNCOMPRESSED = 8 * 1024 * 1024


class PlaybookCatalogError(ValueError):
    """Invalid Playbook package or install request."""


@dataclass(frozen=True)
class PlaybookStep:
    id: str
    execution: str
    skills: tuple[str, ...]
    tools: tuple[str, ...]
    depends_on: tuple[str, ...]
    output: str
    isolation: str
    prompt: str | None = None
    skill: str | None = None


@dataclass(frozen=True)
class PlaybookRecord:
    id: str
    description: str
    origin: str
    path: Path
    steps: tuple[PlaybookStep, ...]
    summary: str
    command_alias: str | None
    schema_version: int = 1

    @property
    def playbook_command(self) -> str:
        return f"/playbook {self.id}"


@dataclass
class PlaybookValidation:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def overlay_playbooks_root(repo: Path) -> Path:
    return repo / ".opencode" / "playbooks"


def pack_playbook_roots(repo: Path, distribution_root: Path | None = None) -> list[Path]:
    """Return pack catalog directories (not the target overlay)."""

    candidates: list[Path] = []
    if distribution_root is not None:
        candidates.append(distribution_root / "pack" / ".opencode" / "playbooks")
    candidates.append(repo / "pack" / ".opencode" / "playbooks")
    roots: list[Path] = []
    seen: set[Path] = set()
    overlay = overlay_playbooks_root(repo).resolve()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in seen or not resolved.is_dir():
            continue
        if resolved == overlay:
            continue
        seen.add(resolved)
        roots.append(resolved)
    return roots


def skill_roots(repo: Path, distribution_root: Path | None = None) -> list[Path]:
    candidates = [
        repo / ".opencode" / "skills",
        repo / "pack" / ".opencode" / "skills",
    ]
    if distribution_root is not None:
        candidates.append(distribution_root / "pack" / ".opencode" / "skills")
        candidates.append(distribution_root / ".opencode" / "skills")
    roots: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in seen or not resolved.is_dir():
            continue
        seen.add(resolved)
        roots.append(resolved)
    return roots


def known_skill_ids(repo: Path, distribution_root: Path | None = None) -> set[str]:
    ids: set[str] = set()
    for root in skill_roots(repo, distribution_root):
        for path in root.glob("*/SKILL.md"):
            ids.add(path.parent.name)
    return ids


def pack_playbook_ids(repo: Path, distribution_root: Path | None = None) -> set[str]:
    ids: set[str] = set()
    for root in pack_playbook_roots(repo, distribution_root):
        for manifest in root.glob("*/playbook.json"):
            ids.add(manifest.parent.name)
    return ids


def playbook_summary(playbook_dir: Path) -> str:
    path = playbook_dir / "PLAYBOOK.md"
    if not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        return stripped
    return ""


def _as_tuple(value: Any) -> tuple[str, ...]:
    if not value:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(str(item) for item in value if str(item).strip())
    return ()


def parse_playbook_dir(playbook_dir: Path, *, origin: str) -> PlaybookRecord:
    manifest_path = playbook_dir / "playbook.json"
    if not manifest_path.is_file():
        raise PlaybookCatalogError(f"missing playbook.json in {playbook_dir}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PlaybookCatalogError(f"invalid playbook.json: {exc}") from exc
    if not isinstance(manifest, dict):
        raise PlaybookCatalogError("playbook.json must be an object")
    playbook_id = str(manifest.get("id") or playbook_dir.name)
    steps: list[PlaybookStep] = []
    raw_steps = manifest.get("steps") or []
    if not isinstance(raw_steps, list):
        raise PlaybookCatalogError("steps must be an array")
    for raw in raw_steps:
        if not isinstance(raw, dict):
            raise PlaybookCatalogError("each step must be an object")
        skill = raw.get("skill")
        skills = _as_tuple(raw.get("skills"))
        if skill and skill not in skills:
            skills = (str(skill),) + skills
        tools = _as_tuple(raw.get("tools"))
        steps.append(
            PlaybookStep(
                id=str(raw.get("id") or ""),
                execution=str(raw.get("execution") or ""),
                skills=skills,
                tools=tools,
                depends_on=_as_tuple(raw.get("depends_on")),
                output=str(raw.get("output") or ""),
                isolation=str(raw.get("isolation") or ""),
                prompt=str(raw["prompt"]) if raw.get("prompt") else None,
                skill=str(skill) if skill else None,
            )
        )
    return PlaybookRecord(
        id=playbook_id,
        description=str(manifest.get("description") or ""),
        origin=origin,
        path=playbook_dir,
        steps=tuple(steps),
        summary=playbook_summary(playbook_dir),
        command_alias=COMMAND_ALIASES.get(playbook_id),
        schema_version=int(manifest["schema_version"]) if "schema_version" in manifest else 1,
    )


def _manifest_bytes(playbook_dir: Path) -> bytes | None:
    path = playbook_dir / "playbook.json"
    if not path.is_file():
        return None
    try:
        return path.read_bytes()
    except OSError:
        return None


def _scan_root(root: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    if not root.is_dir():
        return found
    for manifest in sorted(root.glob("*/playbook.json")):
        found[manifest.parent.name] = manifest.parent
    return found


def discover_playbooks(repo: Path, distribution_root: Path | None = None) -> list[PlaybookRecord]:
    """Return overlay-over-pack Playbooks. Overlay content wins; origin is pack vs overlay."""

    overlay = _scan_root(overlay_playbooks_root(repo))
    pack: dict[str, Path] = {}
    for root in pack_playbook_roots(repo, distribution_root):
        for playbook_id, path in _scan_root(root).items():
            pack.setdefault(playbook_id, path)

    records: list[PlaybookRecord] = []
    for playbook_id in sorted(set(overlay) | set(pack)):
        overlay_dir = overlay.get(playbook_id)
        pack_dir = pack.get(playbook_id)
        if overlay_dir is not None and pack_dir is not None:
            overlay_bytes = _manifest_bytes(overlay_dir)
            pack_bytes = _manifest_bytes(pack_dir)
            origin = "pack" if overlay_bytes == pack_bytes else "overlay"
            source = overlay_dir
        elif overlay_dir is not None:
            origin = "overlay"
            source = overlay_dir
        else:
            origin = "pack"
            source = pack_dir
        try:
            records.append(parse_playbook_dir(source, origin=origin))
        except PlaybookCatalogError:
            continue
    return records


def _assert_acyclic(steps: Iterable[PlaybookStep]) -> str | None:
    graph = {step.id: list(step.depends_on) for step in steps}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> str | None:
        if node in visited:
            return None
        if node in visiting:
            return f"playbook dependency cycle at {node}"
        visiting.add(node)
        for dependency in graph.get(node, []):
            if dependency not in graph:
                continue
            cycle = visit(dependency)
            if cycle:
                return cycle
        visiting.remove(node)
        visited.add(node)
        return None

    for node in graph:
        cycle = visit(node)
        if cycle:
            return cycle
    return None


def validate_playbook_dir(
    playbook_dir: Path,
    *,
    skill_ids: set[str] | None = None,
) -> PlaybookValidation:
    """Same hard invariants as test_playbook_manifests_reference_real_atomic_skills_and_steps.

    Missing Skills and empty tools[] are warnings. Tool names are never invented from markdown.
    """

    result = PlaybookValidation()
    manifest_path = playbook_dir / "playbook.json"
    if not manifest_path.is_file():
        result.errors.append("missing playbook.json")
        return result
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.errors.append(f"invalid playbook.json: {exc}")
        return result
    if not isinstance(manifest, dict):
        result.errors.append("playbook.json must be an object")
        return result
    if manifest.get("schema_version") != 1:
        result.errors.append("schema_version must be 1")
    playbook_id = manifest.get("id")
    if playbook_id != playbook_dir.name:
        result.errors.append(f"id {playbook_id!r} does not match folder name {playbook_dir.name!r}")
    if not (playbook_dir / "PLAYBOOK.md").is_file():
        result.errors.append("missing PLAYBOOK.md")
    steps = manifest.get("steps")
    if not isinstance(steps, list) or not steps:
        result.errors.append("steps must be a non-empty array")
        return result
    ids = [step.get("id") for step in steps if isinstance(step, dict)]
    if len(ids) != len(set(ids)):
        result.errors.append("duplicate step id")
    id_set = {str(item) for item in ids if item}
    known = skill_ids if skill_ids is not None else set()
    parsed_steps: list[PlaybookStep] = []
    for step in steps:
        if not isinstance(step, dict):
            result.errors.append("each step must be an object")
            continue
        step_id = str(step.get("id") or "")
        execution = step.get("execution")
        if execution not in {"skill", "step"}:
            result.errors.append(f"{step_id or '?'}: execution must be skill or step")
        if not step.get("output"):
            result.errors.append(f"{step_id or '?'}: missing output contract")
        if step.get("isolation") != "fresh_subagent":
            result.errors.append(f"{step_id or '?'}: isolation must be fresh_subagent")
        for dependency in step.get("depends_on") or []:
            if dependency not in id_set:
                result.errors.append(f"{step_id or '?'}: unknown dependency {dependency}")
        tools_declared = "tools" in step
        tools = step.get("tools", [])
        if tools is None:
            tools = []
        if tools_declared and not isinstance(tools, list):
            result.errors.append(f"{step_id or '?'}: tools must be an array when present")
            tools = []
        elif tools_declared and not tools:
            result.warnings.append(f"{step_id or '?'}: empty tools[]")
        skills: list[str] = []
        if execution == "skill":
            skill = step.get("skill")
            if not skill:
                result.errors.append(f"{step_id or '?'}: Skill Step missing skill")
            else:
                skills.append(str(skill))
                if known and skill not in known:
                    result.warnings.append(f"{step_id or '?'}: unknown skill {skill}")
            if step.get("prompt"):
                result.errors.append(f"{step_id or '?'}: Skill Step must not duplicate a Step prompt")
        elif execution == "step":
            prompt = step.get("prompt")
            if not prompt:
                result.errors.append(f"{step_id or '?'}: composite Step missing prompt")
            else:
                prompt_path = playbook_dir / prompt
                if not prompt_path.is_file():
                    result.errors.append(f"{step_id or '?'}: missing {prompt}")
            for skill in step.get("skills") or []:
                skills.append(str(skill))
                if known and skill not in known:
                    result.warnings.append(f"{step_id or '?'}: unknown skill {skill}")
        parsed_steps.append(
            PlaybookStep(
                id=step_id,
                execution=str(execution or ""),
                skills=tuple(skills),
                tools=tuple(str(item) for item in tools if str(item).strip()),
                depends_on=_as_tuple(step.get("depends_on")),
                output=str(step.get("output") or ""),
                isolation=str(step.get("isolation") or ""),
            )
        )
    cycle = _assert_acyclic(parsed_steps)
    if cycle:
        result.errors.append(cycle)
    return result


def _safe_extract_zip(archive: Path, dest: Path) -> None:
    with zipfile.ZipFile(archive) as zf:
        infos = zf.infolist()
        if len(infos) > _MAX_ZIP_ENTRIES:
            raise PlaybookCatalogError("zip has too many entries")
        uncompressed = 0
        for info in infos:
            name = Path(info.filename)
            if name.is_absolute() or ".." in name.parts:
                raise PlaybookCatalogError(f"unsafe zip entry: {info.filename}")
            uncompressed += info.file_size
            if uncompressed > _MAX_ZIP_UNCOMPRESSED:
                raise PlaybookCatalogError("zip is too large")
        zf.extractall(dest)


def resolve_playbook_source(source: Path, unpack_dir: Path | None = None) -> Path:
    """Return a directory containing playbook.json from a folder or zip."""

    source = source.expanduser()
    if not source.exists():
        raise PlaybookCatalogError(f"source does not exist: {source}")
    if source.is_dir():
        if not (source / "playbook.json").is_file():
            raise PlaybookCatalogError("directory has no playbook.json")
        return source
    if source.is_file() and source.suffix.lower() == ".zip":
        if unpack_dir is None:
            raise PlaybookCatalogError("zip install requires an unpack directory")
        _safe_extract_zip(source, unpack_dir)
        direct = unpack_dir / "playbook.json"
        if direct.is_file():
            return unpack_dir
        matches = [path.parent for path in unpack_dir.glob("*/playbook.json")]
        if len(matches) == 1:
            return matches[0]
        raise PlaybookCatalogError("zip must contain exactly one playbook.json at the root or one folder down")
    raise PlaybookCatalogError("source must be a Playbook directory or .zip")


def inspect_playbook_source(source: Path, unpack_dir: Path | None = None) -> PlaybookRecord:
    return parse_playbook_dir(resolve_playbook_source(source, unpack_dir), origin="overlay")


def install_playbook(
    source: Path,
    repo: Path,
    *,
    overwrite: bool = False,
    unpack_dir: Path | None = None,
) -> Path:
    """Copy a validated-or-caller-confirmed package into repo/.opencode/playbooks/<id>/.

    Does not start /playbook or materialize Steps.
    """

    package = resolve_playbook_source(source, unpack_dir)
    record = parse_playbook_dir(package, origin="overlay")
    dest = overlay_playbooks_root(repo) / record.id
    if dest.exists() and not overwrite:
        raise PlaybookCatalogError(f"overlay already has {record.id}; confirm to replace")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(package, dest)
    return dest


def skill_contract_excerpt(skill_id: str, repo: Path, distribution_root: Path | None = None) -> str:
    for root in skill_roots(repo, distribution_root):
        path = root / skill_id / "SKILL.md"
        if not path.is_file():
            continue
        lines: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("## Atomic contract"):
                lines = [stripped]
                continue
            if lines:
                if stripped.startswith("## ") and not stripped.startswith("## Atomic"):
                    break
                lines.append(line.rstrip())
                if len(lines) >= 12:
                    break
        text = "\n".join(lines).strip()
        if text:
            return text
        preview = path.read_text(encoding="utf-8").strip().splitlines()[:8]
        return "\n".join(preview)
    return f"Skill {skill_id}: contract file not found. Catalog chips do not load Skills."


def tool_purpose(tool_name: str) -> str:
    return (
        f"OpenCode tool `{tool_name}`. Catalog chips show declared metadata only "
        "and do not invoke tools."
    )


def unpack_workspace() -> tempfile.TemporaryDirectory[str]:
    return tempfile.TemporaryDirectory(prefix="codesleuth-playbook-")
