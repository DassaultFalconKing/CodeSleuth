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
from uuid import uuid4

# Inverse of tests/test_playbook_skill_contract.py::test_product_commands_route_broad_work_to_playbooks
COMMAND_ALIASES: dict[str, str] = {
    "repository-deep-review": "/repo-review",
    "repository-contract-bootstrap": "/repo-contract-bootstrap",
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
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise PlaybookCatalogError(f"cannot read PLAYBOOK.md: {exc}") from exc
    for line in lines:
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


def _read_manifest(playbook_dir: Path) -> dict[str, Any]:
    manifest_path = playbook_dir / "playbook.json"
    if not manifest_path.is_file():
        raise PlaybookCatalogError(f"missing playbook.json in {playbook_dir}")
    try:
        text = manifest_path.read_text(encoding="utf-8")
        manifest = json.loads(text)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PlaybookCatalogError(f"invalid playbook.json: {exc}") from exc
    if not isinstance(manifest, dict):
        raise PlaybookCatalogError("playbook.json must be an object")
    return manifest


def parse_playbook_dir(playbook_dir: Path, *, origin: str) -> PlaybookRecord:
    manifest = _read_manifest(playbook_dir)
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
    raw_schema = manifest.get("schema_version", 1)
    schema_version = raw_schema if isinstance(raw_schema, int) and not isinstance(raw_schema, bool) else -1
    return PlaybookRecord(
        id=playbook_id,
        description=str(manifest.get("description") or ""),
        origin=origin,
        path=playbook_dir,
        steps=tuple(steps),
        summary=playbook_summary(playbook_dir),
        command_alias=COMMAND_ALIASES.get(playbook_id),
        schema_version=schema_version,
    )


def validate_playbook(
    record: PlaybookRecord,
    *,
    known_skills: set[str],
    source_root: Path | None = None,
) -> PlaybookValidation:
    result = PlaybookValidation()
    if record.schema_version != 1:
        result.errors.append(f"unsupported schema_version {record.schema_version!r}; expected 1")
    if not record.id or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for char in record.id):
        result.errors.append("id must use lowercase alphanumerics, '-' or '_'")
    if not record.description.strip():
        result.errors.append("description is required")
    if not record.steps:
        result.errors.append("steps must not be empty")

    step_ids: set[str] = set()
    for index, step in enumerate(record.steps):
        prefix = f"steps[{index}]"
        if not step.id:
            result.errors.append(f"{prefix}.id is required")
        elif step.id in step_ids:
            result.errors.append(f"duplicate step id {step.id!r}")
        step_ids.add(step.id)
        if step.execution not in {"step", "skill"}:
            result.errors.append(f"{prefix}.execution must be 'step' or 'skill'")
        if not step.output:
            result.errors.append(f"{prefix}.output is required")
        if step.isolation not in {"fresh_subagent", "controller"}:
            result.errors.append(f"{prefix}.isolation must be fresh_subagent or controller")
        if step.execution == "step" and not step.prompt:
            result.errors.append(f"{prefix}.prompt is required for execution=step")
        if step.execution == "skill" and not step.skill:
            result.errors.append(f"{prefix}.skill is required for execution=skill")
        for skill in step.skills:
            if skill not in known_skills:
                result.errors.append(f"{prefix}.skills references unknown Skill {skill!r}")
        for dependency in step.depends_on:
            if dependency not in step_ids:
                result.errors.append(f"{prefix}.depends_on references future/unknown step {dependency!r}")
        if source_root is not None and step.prompt:
            prompt = source_root / step.prompt
            if not prompt.is_file():
                result.errors.append(f"{prefix}.prompt is missing: {step.prompt}")
    return result


def _copy_tree_transactional(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = target.parent / f".{target.name}.stage-{uuid4().hex}"
    backup = target.parent / f".{target.name}.backup-{uuid4().hex}"
    try:
        shutil.copytree(source, stage)
        if target.exists():
            target.rename(backup)
        stage.rename(target)
        if backup.exists():
            shutil.rmtree(backup)
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        if backup.exists() and not target.exists():
            backup.rename(target)
        raise


def _safe_zip_entries(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    infos = archive.infolist()
    if len(infos) > _MAX_ZIP_ENTRIES:
        raise PlaybookCatalogError(f"ZIP has too many entries ({len(infos)} > {_MAX_ZIP_ENTRIES})")
    total = sum(info.file_size for info in infos)
    if total > _MAX_ZIP_UNCOMPRESSED:
        raise PlaybookCatalogError(f"ZIP is too large after extraction ({total} > {_MAX_ZIP_UNCOMPRESSED} bytes)")
    for info in infos:
        pure = Path(info.filename)
        if pure.is_absolute() or ".." in pure.parts:
            raise PlaybookCatalogError(f"unsafe ZIP path: {info.filename}")
    return infos


def _find_playbook_root(root: Path) -> Path:
    candidates = [path.parent for path in root.rglob("playbook.json")]
    if len(candidates) != 1:
        raise PlaybookCatalogError("Playbook package must contain exactly one playbook.json")
    return candidates[0]


def inspect_playbook_source(source: Path) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    resolved = source.expanduser().resolve()
    if resolved.is_dir():
        return resolved, None
    if resolved.is_file() and resolved.suffix.lower() == ".zip":
        temp = tempfile.TemporaryDirectory(prefix="codesleuth-playbook-")
        temp_root = Path(temp.name)
        with zipfile.ZipFile(resolved) as archive:
            infos = _safe_zip_entries(archive)
            archive.extractall(temp_root, members=infos)
        return _find_playbook_root(temp_root), temp
    raise PlaybookCatalogError("Playbook source must be a local directory or ZIP archive")


def load_playbook_catalog(repo: Path, distribution_root: Path | None = None) -> list[PlaybookRecord]:
    records: dict[str, PlaybookRecord] = {}
    for root in pack_playbook_roots(repo, distribution_root):
        for manifest in sorted(root.glob("*/playbook.json")):
            record = parse_playbook_dir(manifest.parent, origin="pack")
            records.setdefault(record.id, record)
    overlay = overlay_playbooks_root(repo)
    if overlay.is_dir():
        for manifest in sorted(overlay.glob("*/playbook.json")):
            record = parse_playbook_dir(manifest.parent, origin="overlay")
            records[record.id] = record
    return sorted(records.values(), key=lambda item: item.id)


def inspect_playbook(repo: Path, source: Path, distribution_root: Path | None = None) -> tuple[PlaybookRecord, PlaybookValidation]:
    playbook_dir, temp = inspect_playbook_source(source)
    try:
        record = parse_playbook_dir(playbook_dir, origin="candidate")
        validation = validate_playbook(record, known_skills=known_skill_ids(repo, distribution_root), source_root=playbook_dir)
        return record, validation
    finally:
        if temp is not None:
            temp.cleanup()


def install_playbook(repo: Path, source: Path, distribution_root: Path | None = None) -> PlaybookRecord:
    playbook_dir, temp = inspect_playbook_source(source)
    try:
        record = parse_playbook_dir(playbook_dir, origin="candidate")
        validation = validate_playbook(record, known_skills=known_skill_ids(repo, distribution_root), source_root=playbook_dir)
        if not validation.ok:
            raise PlaybookCatalogError("; ".join(validation.errors))
        target = overlay_playbooks_root(repo) / record.id
        _copy_tree_transactional(playbook_dir, target)
        return parse_playbook_dir(target, origin="overlay")
    finally:
        if temp is not None:
            temp.cleanup()
