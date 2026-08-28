from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BIN))
from playbook_catalog import (  # noqa: E402
    PlaybookCatalogError,
    discover_playbooks,
    install_playbook,
    pack_playbook_ids,
    parse_playbook_dir,
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


def test_pack_ids_include_builtins() -> None:
    ids = pack_playbook_ids(ROOT, ROOT)
    assert "eha-sib-acceptance" in ids
    assert "eha-repair" in ids
