from __future__ import annotations

import json
import shutil
import sys
import zipfile
from pathlib import Path

import pytest

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BIN))
import playbook_catalog as catalog  # noqa: E402
from playbook_catalog import (  # noqa: E402
    PlaybookCatalogError,
    discover_playbooks,
    install_playbook,
    pack_playbook_ids,
    parse_playbook_dir,
    resolve_playbook_source,
    validate_playbook_dir,
)


def _write_playbook(root: Path, playbook_id: str, *, cyclic: bool = False, description: str = "fixture") -> Path:
    playbook_dir = root / playbook_id
    steps_dir = playbook_dir / "steps"
    steps_dir.mkdir(parents=True)
    (playbook_dir / "PLAYBOOK.md").write_text(f"# {playbook_id}\n\n{description}\n", encoding="utf-8")
    if cyclic:
        steps = [
            {
                "id": "a",
                "execution": "step",
                "prompt": "steps/a.md",
                "skills": [],
                "depends_on": ["b"],
                "output": "out_a",
                "isolation": "fresh_subagent",
            },
            {
                "id": "b",
                "execution": "step",
                "prompt": "steps/b.md",
                "skills": [],
                "depends_on": ["a"],
                "output": "out_b",
                "isolation": "fresh_subagent",
            },
        ]
        (steps_dir / "a.md").write_text("# a\n", encoding="utf-8")
        (steps_dir / "b.md").write_text("# b\n", encoding="utf-8")
    else:
        steps = [
            {
                "id": "capture",
                "execution": "skill",
                "skill": "exact-target-identity",
                "depends_on": [],
                "output": "target_identity",
                "isolation": "fresh_subagent",
            }
        ]
    (playbook_dir / "playbook.json").write_text(
        json.dumps({"schema_version": 1, "id": playbook_id, "description": description, "steps": steps}) + "\n",
        encoding="utf-8",
    )
    return playbook_dir


def test_discover_overlay_wins_over_pack(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    overlay = repo / ".opencode" / "playbooks" / "repository-map"
    overlay.mkdir(parents=True)
    shutil.copytree(ROOT / "pack" / ".opencode" / "playbooks" / "repository-map", overlay, dirs_exist_ok=True)
    manifest = json.loads((overlay / "playbook.json").read_text(encoding="utf-8"))
    manifest["description"] = "overlay description wins"
    (overlay / "playbook.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")

    records = {item.id: item for item in discover_playbooks(repo, ROOT)}
    assert records["repository-map"].origin == "overlay"
    assert records["repository-map"].description == "overlay description wins"
    assert records["eha-sib-acceptance"].origin == "pack"
    assert len(records["eha-sib-acceptance"].steps) == 6


def test_discover_marks_overlay_origin_when_only_step_content_differs(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    overlay = repo / ".opencode" / "playbooks" / "repository-map"
    overlay.mkdir(parents=True)
    shutil.copytree(ROOT / "pack" / ".opencode" / "playbooks" / "repository-map", overlay, dirs_exist_ok=True)
    (overlay / "PLAYBOOK.md").write_text("# repository-map\n\noverlay-only body\n", encoding="utf-8")

    record = {item.id: item for item in discover_playbooks(repo, ROOT)}["repository-map"]
    assert record.origin == "overlay"
    assert record.path == overlay
    assert record.summary == "overlay-only body"


def test_validate_rejects_cyclic_and_broken_packages(tmp_path: Path) -> None:
    cyclic = _write_playbook(tmp_path, "cyclic", cyclic=True)
    report = validate_playbook_dir(cyclic)
    assert not report.ok
    assert any("cycle" in error for error in report.errors)

    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / "playbook.json").write_text('{"schema_version": 1, "id": "nope", "steps": []}\n', encoding="utf-8")
    broken_report = validate_playbook_dir(broken)
    assert not broken_report.ok
    assert any("PLAYBOOK.md" in error or "id" in error or "steps" in error for error in broken_report.errors)


def test_malformed_schema_is_a_validation_error_not_raw_parser_failure(tmp_path: Path) -> None:
    package = _write_playbook(tmp_path, "bad-schema")
    manifest = json.loads((package / "playbook.json").read_text(encoding="utf-8"))
    manifest["schema_version"] = "garbage"
    (package / "playbook.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")

    record = parse_playbook_dir(package, origin="overlay")
    assert record.schema_version == -1
    report = validate_playbook_dir(package)
    assert not report.ok
    assert "schema_version must be 1" in report.errors


def test_root_level_zip_is_rejected_with_clear_layout_contract(tmp_path: Path) -> None:
    package = _write_playbook(tmp_path / "packages", "zip-root")
    archive = tmp_path / "root.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        for path in package.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(package))
    unpack = tmp_path / "unpack"
    unpack.mkdir()

    with pytest.raises(PlaybookCatalogError, match="top-level Playbook folder"):
        resolve_playbook_source(archive, unpack)

    nested_archive = tmp_path / "nested.zip"
    with zipfile.ZipFile(nested_archive, "w") as zf:
        for path in package.rglob("*"):
            if path.is_file():
                zf.write(path, Path(package.name) / path.relative_to(package))
    resolved = resolve_playbook_source(nested_archive, unpack)
    assert resolved.name == "zip-root"


def test_install_writes_overlay_and_does_not_execute(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    repo.mkdir()
    source = _write_playbook(tmp_path / "packages", "sample-load")
    dest = install_playbook(source, repo)
    assert dest == repo / ".opencode" / "playbooks" / "sample-load"
    assert (dest / "playbook.json").is_file()
    record = parse_playbook_dir(dest, origin="overlay")
    assert record.id == "sample-load"
    assert record.playbook_command == "/playbook sample-load"


def test_install_requires_overwrite_for_existing_overlay(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    source = _write_playbook(tmp_path / "packages", "sample-load")
    install_playbook(source, repo)
    with pytest.raises(PlaybookCatalogError, match="overlay already has"):
        install_playbook(source, repo)
    dest = install_playbook(source, repo, overwrite=True)
    assert dest.is_dir()


def test_overwrite_copy_failure_preserves_existing_overlay(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "target"
    old = _write_playbook(tmp_path / "old", "sample-load", description="old copy")
    new = _write_playbook(tmp_path / "new", "sample-load", description="new copy")
    dest = install_playbook(old, repo)
    before = (dest / "PLAYBOOK.md").read_bytes()
    real_copytree = shutil.copytree

    def fail_stage_copy(src: Path, dst: Path, *args, **kwargs):
        if ".codesleuth-stage-" in str(dst):
            raise OSError("synthetic copy failure")
        return real_copytree(src, dst, *args, **kwargs)

    monkeypatch.setattr(catalog.shutil, "copytree", fail_stage_copy)
    with pytest.raises(PlaybookCatalogError, match="could not stage"):
        install_playbook(new, repo, overwrite=True)

    assert (dest / "PLAYBOOK.md").read_bytes() == before
    assert not list(dest.parent.glob(".sample-load.codesleuth-*"))


def test_pack_ids_include_builtins() -> None:
    ids = pack_playbook_ids(ROOT, ROOT)
    assert "eha-sib-acceptance" in ids
    assert "eha-repair" in ids
