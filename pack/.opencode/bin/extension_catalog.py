#!/usr/bin/env python3
"""Bounded extension catalog/install core for host-native CodeSleuth extensions.

This module manages stored extension bytes only. It never executes Skills,
Playbooks, tools, plugins, or host adapters.
"""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import uuid4

import playbook_catalog

_MAX_ZIP_ENTRIES = 200
_MAX_ZIP_UNCOMPRESSED = 8 * 1024 * 1024
_MAX_MANIFEST_BYTES = 512 * 1024
_ID_RE = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$"


class ExtensionCatalogError(ValueError):
    """Invalid extension package or install request."""


@dataclass
class ExtensionValidation:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class ExtensionRecord:
    kind_id: str
    id: str
    description: str
    origin: str
    path: Path
    summary: str
    manifest_name: str
    host_command: str | None
    details: dict[str, Any]


ParseExtension = Callable[[Path, str], ExtensionRecord]
ValidateExtension = Callable[[Path], ExtensionValidation]


@dataclass(frozen=True)
class ExtensionKindAdapter:
    kind_id: str
    overlay_subdir: str
    pack_subdir: str
    manifest_name: str
    parse: ParseExtension
    validate: ValidateExtension


def _valid_id(value: str) -> bool:
    import re

    return bool(re.fullmatch(_ID_RE, value))


def _overlay_root(repo: Path, adapter: ExtensionKindAdapter) -> Path:
    return repo / ".opencode" / adapter.overlay_subdir


def _pack_roots(
    repo: Path,
    adapter: ExtensionKindAdapter,
    distribution_root: Path | None = None,
) -> list[Path]:
    candidates: list[Path] = []
    if distribution_root is not None:
        candidates.append(distribution_root / "pack" / ".opencode" / adapter.pack_subdir)
    candidates.append(repo / "pack" / ".opencode" / adapter.pack_subdir)

    roots: list[Path] = []
    seen: set[Path] = set()
    overlay = _overlay_root(repo, adapter).resolve()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in seen or resolved == overlay or not resolved.is_dir():
            continue
        seen.add(resolved)
        roots.append(resolved)
    return roots


def _scan_root(root: Path, manifest_name: str) -> dict[str, Path]:
    if not root.is_dir():
        return {}
    found: dict[str, Path] = {}
    for manifest in sorted(root.glob(f"*/{manifest_name}")):
        found[manifest.parent.name] = manifest.parent
    return found


def pack_extension_ids(
    repo: Path,
    adapter: ExtensionKindAdapter,
    distribution_root: Path | None = None,
) -> set[str]:
    ids: set[str] = set()
    for root in _pack_roots(repo, adapter, distribution_root):
        ids.update(_scan_root(root, adapter.manifest_name))
    return ids


def discover_extensions(
    repo: Path,
    adapter: ExtensionKindAdapter,
    distribution_root: Path | None = None,
) -> list[ExtensionRecord]:
    """Return overlay-over-pack extension records for one kind.

    Origin follows the selected source path. Equal bytes do not demote an
    overlay item back to pack origin.
    """

    overlay = _scan_root(_overlay_root(repo, adapter), adapter.manifest_name)
    pack: dict[str, Path] = {}
    for root in _pack_roots(repo, adapter, distribution_root):
        for extension_id, source in _scan_root(root, adapter.manifest_name).items():
            pack.setdefault(extension_id, source)

    records: list[ExtensionRecord] = []
    for extension_id in sorted(set(overlay) | set(pack)):
        source = overlay.get(extension_id) or pack[extension_id]
        origin = "overlay" if extension_id in overlay else "pack"
        try:
            validation = adapter.validate(source)
            if not validation.ok:
                continue
            records.append(adapter.parse(source, origin))
        except (ExtensionCatalogError, OSError, UnicodeError):
            continue
    return records


def _safe_extract_zip(archive: Path, dest: Path) -> Path:
    try:
        with zipfile.ZipFile(archive) as zf:
            infos = zf.infolist()
            if len(infos) > _MAX_ZIP_ENTRIES:
                raise ExtensionCatalogError("zip has too many entries")
            uncompressed = 0
            for info in infos:
                normalized = info.filename.replace("\\", "/")
                name = PurePosixPath(normalized)
                if normalized.startswith("/") or ".." in name.parts:
                    raise ExtensionCatalogError(f"unsafe zip entry: {info.filename}")
                if name.parts and name.parts[0].endswith(":"):
                    raise ExtensionCatalogError(f"unsafe zip entry: {info.filename}")
                uncompressed += info.file_size
                if uncompressed > _MAX_ZIP_UNCOMPRESSED:
                    raise ExtensionCatalogError("zip is too large")
            extract_root = Path(tempfile.mkdtemp(prefix="source-", dir=dest))
            zf.extractall(extract_root)
            return extract_root
    except (OSError, zipfile.BadZipFile) as exc:
        raise ExtensionCatalogError(f"invalid zip: {exc}") from exc


def resolve_extension_source(
    source: Path,
    adapter: ExtensionKindAdapter,
    unpack_dir: Path | None = None,
) -> Path:
    source = source.expanduser()
    if not source.exists():
        raise ExtensionCatalogError(f"source does not exist: {source}")
    if source.is_dir():
        if not (source / adapter.manifest_name).is_file():
            raise ExtensionCatalogError(
                f"directory has no {adapter.manifest_name} for {adapter.kind_id}"
            )
        return source
    if source.is_file() and source.suffix.lower() == ".zip":
        if unpack_dir is None:
            raise ExtensionCatalogError("zip install requires an unpack directory")
        extract_root = _safe_extract_zip(source, unpack_dir)
        if (extract_root / adapter.manifest_name).is_file():
            raise ExtensionCatalogError(
                f"zip must contain one top-level {adapter.kind_id} folder, "
                f"not root-level {adapter.manifest_name}"
            )
        matches = [path.parent for path in extract_root.glob(f"*/{adapter.manifest_name}")]
        if len(matches) != 1:
            raise ExtensionCatalogError(
                f"zip must contain exactly one top-level {adapter.kind_id} folder"
            )
        return matches[0]
    raise ExtensionCatalogError(
        f"source must be a {adapter.kind_id} directory or .zip"
    )


def inspect_extension_source(
    source: Path,
    adapter: ExtensionKindAdapter,
    unpack_dir: Path | None = None,
) -> ExtensionRecord:
    package = resolve_extension_source(source, adapter, unpack_dir)
    validation = adapter.validate(package)
    if not validation.ok:
        raise ExtensionCatalogError(
            f"invalid {adapter.kind_id} package: " + "; ".join(validation.errors)
        )
    return adapter.parse(package, "overlay")


def install_extension(
    source: Path,
    repo: Path,
    adapter: ExtensionKindAdapter,
    *,
    distribution_root: Path | None = None,
    replace_overlay: bool = False,
    allow_pack_shadow: bool = False,
    unpack_dir: Path | None = None,
) -> Path:
    """Validate and transactionally publish one package into its overlay root."""

    temporary_unpack: tempfile.TemporaryDirectory[str] | None = None
    try:
        if source.is_file() and source.suffix.lower() == ".zip" and unpack_dir is None:
            temporary_unpack = tempfile.TemporaryDirectory(prefix="codesleuth-extension-")
            unpack_dir = Path(temporary_unpack.name)
        package = resolve_extension_source(source, adapter, unpack_dir)
        validation = adapter.validate(package)
        if not validation.ok:
            raise ExtensionCatalogError(
                f"invalid {adapter.kind_id} package: " + "; ".join(validation.errors)
            )
        record = adapter.parse(package, "overlay")

        if record.id in pack_extension_ids(repo, adapter, distribution_root) and not allow_pack_shadow:
            raise ExtensionCatalogError(
                f"pack already provides {record.id}; explicit allow_pack_shadow is required"
            )

        dest = _overlay_root(repo, adapter) / record.id
        if dest.exists() and not replace_overlay:
            raise ExtensionCatalogError(
                f"overlay already has {record.id}; explicit replace_overlay is required"
            )
        dest.parent.mkdir(parents=True, exist_ok=True)

        stage_root = Path(
            tempfile.mkdtemp(
                prefix=f".{record.id}.codesleuth-stage-",
                dir=dest.parent,
            )
        )
        staged = stage_root / record.id
        backup: Path | None = None
        try:
            try:
                shutil.copytree(package, staged)
            except (OSError, shutil.Error) as exc:
                raise ExtensionCatalogError(
                    f"could not stage {adapter.kind_id} install: {exc}"
                ) from exc

            staged_validation = adapter.validate(staged)
            if not staged_validation.ok:
                raise ExtensionCatalogError(
                    f"staged {adapter.kind_id} failed validation: "
                    + "; ".join(staged_validation.errors)
                )

            if dest.exists():
                backup = dest.parent / f".{record.id}.codesleuth-backup-{uuid4().hex}"
                try:
                    dest.rename(backup)
                    staged.rename(dest)
                except OSError as exc:
                    if backup.exists() and not dest.exists():
                        try:
                            backup.rename(dest)
                        except OSError as rollback_exc:
                            raise ExtensionCatalogError(
                                "overlay swap failed and rollback failed; "
                                f"previous copy remains at {backup}: {rollback_exc}"
                            ) from exc
                    raise ExtensionCatalogError(
                        f"overlay swap failed; previous copy restored: {exc}"
                    ) from exc
                shutil.rmtree(backup, ignore_errors=True)
                backup = None
            else:
                try:
                    staged.rename(dest)
                except OSError as exc:
                    raise ExtensionCatalogError(
                        f"could not publish staged {adapter.kind_id}: {exc}"
                    ) from exc
            return dest
        finally:
            shutil.rmtree(stage_root, ignore_errors=True)
            if backup is not None and backup.exists() and dest.exists():
                shutil.rmtree(backup, ignore_errors=True)
    finally:
        if temporary_unpack is not None:
            temporary_unpack.cleanup()


def _read_bounded_text(path: Path) -> str:
    try:
        if path.stat().st_size > _MAX_MANIFEST_BYTES:
            raise ExtensionCatalogError(
                f"{path.name} exceeds {_MAX_MANIFEST_BYTES} bytes"
            )
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ExtensionCatalogError(f"cannot read {path.name}: {exc}") from exc


def _strip_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _skill_frontmatter(skill_dir: Path) -> tuple[dict[str, str], str]:
    path = skill_dir / "SKILL.md"
    if not path.is_file():
        raise ExtensionCatalogError(f"missing SKILL.md in {skill_dir}")
    text = _read_bounded_text(path)
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ExtensionCatalogError("SKILL.md frontmatter must start with ---")
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as exc:
        raise ExtensionCatalogError("SKILL.md frontmatter is not terminated") from exc

    values: dict[str, str] = {}
    for line in lines[1:end]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, raw = stripped.split(":", 1)
        values[key.strip()] = _strip_scalar(raw)
    return values, text


def _atomic_contract_excerpt(text: str, limit: int = 18) -> str:
    lines = text.splitlines()
    start: int | None = None
    selected: list[str] = []
    for index, line in enumerate(lines):
        if line.strip().lower() == "## atomic contract":
            start = index
            break
    if start is None:
        return ""
    for line in lines[start : start + limit]:
        if selected and line.startswith("## ") and line.strip().lower() != "## atomic contract":
            break
        selected.append(line.rstrip())
    return "\n".join(selected).strip()


def _parse_skill(skill_dir: Path, origin: str) -> ExtensionRecord:
    frontmatter, text = _skill_frontmatter(skill_dir)
    name = frontmatter.get("name", "").strip()
    description = frontmatter.get("description", "").strip()
    if not name:
        raise ExtensionCatalogError("SKILL.md frontmatter requires name")
    if not _valid_id(name):
        raise ExtensionCatalogError("Skill name must use safe [A-Za-z0-9._-] identity characters")
    if name != skill_dir.name:
        raise ExtensionCatalogError(
            f"Skill name {name} does not match folder {skill_dir.name}"
        )
    if not description:
        raise ExtensionCatalogError("SKILL.md frontmatter requires description")

    raw_slash = frontmatter.get("slash", "false").strip().lower()
    if raw_slash not in {"true", "false"}:
        raise ExtensionCatalogError("Skill slash frontmatter must be true or false")
    slash = raw_slash == "true"
    return ExtensionRecord(
        kind_id="skill",
        id=name,
        description=description,
        origin=origin,
        path=skill_dir,
        summary=description,
        manifest_name="SKILL.md",
        host_command=None,
        details={
            "slash": slash,
            "atomic_contract": _atomic_contract_excerpt(text),
            "execution_authority": "host",
        },
    )


def _validate_skill(skill_dir: Path) -> ExtensionValidation:
    result = ExtensionValidation()
    try:
        record = _parse_skill(skill_dir, "overlay")
    except ExtensionCatalogError as exc:
        result.errors.append(str(exc))
        return result
    if not record.details.get("atomic_contract"):
        result.warnings.append("Skill has no bounded ## Atomic contract section")
    return result


def skill_adapter() -> ExtensionKindAdapter:
    return ExtensionKindAdapter(
        kind_id="skill",
        overlay_subdir="skills",
        pack_subdir="skills",
        manifest_name="SKILL.md",
        parse=_parse_skill,
        validate=_validate_skill,
    )


def _parse_playbook(playbook_dir: Path, origin: str) -> ExtensionRecord:
    record = playbook_catalog.parse_playbook_dir(playbook_dir, origin=origin)
    skills = sorted({skill for step in record.steps for skill in step.skills})
    tools = sorted({tool for step in record.steps for tool in step.tools})
    host_command = record.canonical_command or record.command_alias or record.playbook_command
    return ExtensionRecord(
        kind_id="playbook",
        id=record.id,
        description=record.description,
        origin=record.origin,
        path=record.path,
        summary=record.summary or record.description,
        manifest_name="playbook.json",
        host_command=host_command,
        details={
            "step_count": len(record.steps),
            "skills": skills,
            "tools": tools,
            "canonical_command": record.canonical_command,
            "command_alias": record.command_alias,
            "execution_authority": "host",
        },
    )


def _validate_playbook(playbook_dir: Path) -> ExtensionValidation:
    existing = playbook_catalog.validate_playbook_dir(playbook_dir)
    return ExtensionValidation(
        errors=list(existing.errors),
        warnings=list(existing.warnings),
    )


def playbook_adapter() -> ExtensionKindAdapter:
    return ExtensionKindAdapter(
        kind_id="playbook",
        overlay_subdir="playbooks",
        pack_subdir="playbooks",
        manifest_name="playbook.json",
        parse=_parse_playbook,
        validate=_validate_playbook,
    )
