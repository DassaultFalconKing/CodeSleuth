from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path

import pytest

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BIN))

import extension_catalog as catalog  # noqa: E402
from extension_catalog import (  # noqa: E402
    ExtensionCatalogError,
    discover_extensions,
    inspect_extension_source,
    install_extension,
    playbook_adapter,
    skill_adapter,
)


def _write_skill(root: Path, skill_id: str, *, description: str = "fixture skill", slash: bool = True) -> Path:
    skill_dir = root / skill_id
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        f"name: {skill_id}\n"
        f"description: {description}\n"
        f"slash: {'true' if slash else 'false'}\n"
        "---\n\n"
        f"# {skill_id}\n\n"
        "## Atomic contract\n\n"
        "Input: bounded fixture.\n\n"
        "Output: bounded fixture result.\n",
        encoding="utf-8",
    )
    return skill_dir


def test_skill_catalog_overlay_wins_and_origin_is_path_truth(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    overlay = repo / ".opencode" / "skills" / "repository-deep-review"
    overlay.parent.mkdir(parents=True)
    shutil.copytree(ROOT / "pack" / ".opencode" / "skills" / "repository-deep-review", overlay)

    records = {item.id: item for item in discover_extensions(repo, skill_adapter(), ROOT)}

    assert records["repository-deep-review"].origin == "overlay"
    assert records["repository-deep-review"].path == overlay
    assert records["repository-deep-review"].kind_id == "skill"


def test_skill_source_requires_frontmatter_name_and_description(tmp_path: Path) -> None:
    source = _write_skill(tmp_path, "sample-skill")
    record = inspect_extension_source(source, skill_adapter())
    assert record.id == "sample-skill"
    assert record.summary == "fixture skill"
    assert record.details["slash"] is True

    broken = tmp_path / "broken-skill"
    broken.mkdir()
    (broken / "SKILL.md").write_text("# no frontmatter\n", encoding="utf-8")
    with pytest.raises(ExtensionCatalogError, match="frontmatter"):
        inspect_extension_source(broken, skill_adapter())

    mismatched = _write_skill(tmp_path / "mismatch", "actual-name")
    target = mismatched.parent / "folder-name"
    mismatched.rename(target)
    with pytest.raises(ExtensionCatalogError, match="folder"):
        inspect_extension_source(target, skill_adapter())


def test_pack_shadow_requires_explicit_confirmation(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    source = _write_skill(tmp_path / "packages", "repository-deep-review", description="overlay candidate")

    with pytest.raises(ExtensionCatalogError, match="pack already provides"):
        install_extension(source, repo, skill_adapter(), distribution_root=ROOT)

    dest = install_extension(
        source,
        repo,
        skill_adapter(),
        distribution_root=ROOT,
        allow_pack_shadow=True,
    )
    assert dest == repo / ".opencode" / "skills" / "repository-deep-review"
    records = {item.id: item for item in discover_extensions(repo, skill_adapter(), ROOT)}
    assert records["repository-deep-review"].origin == "overlay"
    assert records["repository-deep-review"].summary == "overlay candidate"


def test_zip_input_is_bounded_and_requires_one_top_level_package(tmp_path: Path) -> None:
    adapter = skill_adapter()
    unpack = tmp_path / "unpack"
    unpack.mkdir()

    traversal = tmp_path / "traversal.zip"
    with zipfile.ZipFile(traversal, "w") as zf:
        zf.writestr("../escape/SKILL.md", "bad")
    with pytest.raises(ExtensionCatalogError, match="unsafe zip entry"):
        inspect_extension_source(traversal, adapter, unpack_dir=unpack)

    root_manifest = tmp_path / "root.zip"
    with zipfile.ZipFile(root_manifest, "w") as zf:
        zf.writestr("SKILL.md", "---\nname: root\ndescription: root\n---\n")
    with pytest.raises(ExtensionCatalogError, match="top-level"):
        inspect_extension_source(root_manifest, adapter, unpack_dir=unpack)

    source = _write_skill(tmp_path / "packages", "zip-skill")
    nested = tmp_path / "nested.zip"
    with zipfile.ZipFile(nested, "w") as zf:
        for path in source.rglob("*"):
            if path.is_file():
                zf.write(path, Path(source.name) / path.relative_to(source))
    record = inspect_extension_source(nested, adapter, unpack_dir=unpack)
    assert record.id == "zip-skill"


def test_failed_overlay_replacement_preserves_previous_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "target"
    old = _write_skill(tmp_path / "old", "sample-skill", description="old copy")
    new = _write_skill(tmp_path / "new", "sample-skill", description="new copy")
    dest = install_extension(old, repo, skill_adapter())
    before = (dest / "SKILL.md").read_bytes()
    real_copytree = shutil.copytree

    def fail_stage_copy(src: Path, dst: Path, *args, **kwargs):
        if ".codesleuth-stage-" in str(dst):
            raise OSError("synthetic copy failure")
        return real_copytree(src, dst, *args, **kwargs)

    monkeypatch.setattr(catalog.shutil, "copytree", fail_stage_copy)
    with pytest.raises(ExtensionCatalogError, match="could not stage"):
        install_extension(new, repo, skill_adapter(), replace_overlay=True)

    assert (dest / "SKILL.md").read_bytes() == before
    assert not list(dest.parent.glob(".sample-skill.codesleuth-*"))


def test_loading_skill_copies_content_without_executing_payload(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    source = _write_skill(tmp_path / "packages", "passive-skill")
    sentinel = tmp_path / "should-not-exist"
    (source / "payload.sh").write_text(f"touch {sentinel}\n", encoding="utf-8")

    dest = install_extension(source, repo, skill_adapter())

    assert (dest / "payload.sh").is_file()
    assert not sentinel.exists()


def test_generic_playbook_adapter_reuses_existing_playbook_contract(tmp_path: Path) -> None:
    records = {item.id: item for item in discover_extensions(tmp_path / "target", playbook_adapter(), ROOT)}

    assert records["eha-sib-acceptance"].kind_id == "playbook"
    assert records["eha-sib-acceptance"].origin == "pack"
    assert records["repository-development-continuation"].details["step_count"] > 0
