from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate_portable_distribution.py"
MANIFEST = ROOT / "portable" / "distribution" / "manifest.json"
GENERATED = ROOT / "portable" / "distribution" / "generated"
NAMING = ROOT / "pack" / ".opencode" / "codesleuth-naming.json"

AGENT_SKILL_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
FULL_PROJECT_CLAIMS = {
    "managed-agents-discovery",
    "reports-convention",
    "durable-review-stores",
    "local-evidence-persistence",
    "context-graph-runtime",
    "playbooks",
    "tools",
    "tui",
    "project-lifecycle",
    "full-host-integration",
    "full-codesleuth-project-runtime",
}


def _skill_text(name: str, *, malformed: bool = False) -> str:
    if malformed:
        return f"---\nname: {name}\ndescription: malformed\n# missing frontmatter terminator\n"
    return (
        "---\n"
        f"name: {name}\n"
        f"description: Portable {name} workflow.\n"
        "slash: true\n"
        "---\n\n"
        f"# {name}\n\n"
        "## Atomic contract\n\n"
        "**Input:** bounded input.\n\n"
        "**Objective:** do one thing.\n\n"
        "**Output:** bounded output.\n\n"
        "**Stop:** objective complete.\n\n"
        "**Must not:** claim full CodeSleuth installation.\n"
    )


def _fixture_repo(
    tmp_path: Path,
    *,
    skills: tuple[str, ...] = ("alpha",),
    legacy_aliases: dict[str, str] | None = None,
    malformed_skill: str | None = None,
    adapter_outputs: dict[str, str] | None = None,
    extra_manifest: dict | None = None,
) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    source = repo / "pack" / ".opencode" / "skills"
    source.mkdir(parents=True)
    for skill in skills:
        skill_dir = source / skill
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            _skill_text(skill, malformed=skill == malformed_skill), encoding="utf-8", newline="\n"
        )

    naming = repo / "pack" / ".opencode" / "codesleuth-naming.json"
    naming.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "product": {"displayName": "CodeSleuth", "slug": "codesleuth"},
                "canonical": {"portableSkills": {"namespacePrefix": "codesleuth-"}},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    outputs = adapter_outputs or {
        "agent-skills": "agent-skills",
        "agent-plugins": "agent-plugins/codesleuth",
    }
    manifest_data = {
        "schemaVersion": 1,
        "sourceRoot": "pack/.opencode/skills",
        "namingAuthority": "pack/.opencode/codesleuth-naming.json",
        "legacyAliases": legacy_aliases or {},
        "adapters": {name: {"output": output} for name, output in outputs.items()},
        "capabilityLevels": {
            "skills-only": {
                "claims": ["portable-workflow-discipline", "portable-agent-skills"],
                "notInstalled": sorted(FULL_PROJECT_CLAIMS),
            },
            "plugin": {
                "claims": ["portable-workflow-discipline", "portable-agent-skills", "agent-plugin-adapter"],
                "notInstalled": sorted(FULL_PROJECT_CLAIMS),
            },
            "full-project": {"claims": sorted(FULL_PROJECT_CLAIMS)},
        },
    }
    if extra_manifest:
        manifest_data.update(extra_manifest)
    manifest = repo / "portable" / "distribution" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps(manifest_data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return repo, manifest, tmp_path / "out"


def _run(repo: Path, manifest: Path, output: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    assert GENERATOR.is_file(), f"missing portable generator: {GENERATOR.relative_to(ROOT)}"
    return subprocess.run(
        [
            sys.executable,
            str(GENERATOR),
            "--repo-root",
            str(repo),
            "--manifest",
            str(manifest),
            "--output-root",
            str(output),
            *extra,
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for name, payload in _tree_bytes(root).items():
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
    return digest.hexdigest()


def _frontmatter_keys(text: str) -> set[str]:
    assert text.startswith("---\n")
    frontmatter = text.split("---\n", 2)[1]
    keys = set()
    for line in frontmatter.splitlines():
        if not line or line[:1].isspace():
            continue
        keys.add(line.split(":", 1)[0])
    return keys


def test_canonical_ids_have_codesleuth_namespace(tmp_path: Path) -> None:
    repo, manifest, output = _fixture_repo(tmp_path, skills=("alpha", "codesleuth-reports"))
    result = _run(repo, manifest, output)
    assert result.returncode == 0, result.stderr
    discovery = _json(output / "agent-skills" / "codesleuth-discovery.json")
    ids = [item["id"] for item in discovery["skills"]]
    assert ids == ["codesleuth-alpha", "codesleuth-reports"]
    assert all(re.fullmatch(r"codesleuth-[a-z0-9]+(?:-[a-z0-9]+)*", item) for item in ids)


def test_duplicate_canonical_id_is_rejected(tmp_path: Path) -> None:
    repo, manifest, output = _fixture_repo(tmp_path, skills=("alpha", "codesleuth-alpha"))
    result = _run(repo, manifest, output)
    assert result.returncode != 0
    assert "duplicate canonical skill id" in result.stderr.lower()


def test_legacy_alias_collision_is_rejected(tmp_path: Path) -> None:
    repo, manifest, output = _fixture_repo(
        tmp_path,
        skills=("alpha", "beta"),
        legacy_aliases={"codesleuth-beta": "alpha"},
    )
    result = _run(repo, manifest, output)
    assert result.returncode != 0
    assert "alias collision" in result.stderr.lower()


def test_canonical_discovery_does_not_advertise_legacy_ids(tmp_path: Path) -> None:
    repo, manifest, output = _fixture_repo(tmp_path, skills=("alpha",), legacy_aliases={"old-alpha": "alpha"})
    result = _run(repo, manifest, output)
    assert result.returncode == 0, result.stderr
    raw = (output / "agent-skills" / "codesleuth-discovery.json").read_text(encoding="utf-8")
    assert "codesleuth-alpha" in raw
    assert '"alpha"' not in raw
    assert "old-alpha" not in raw


def test_generation_is_deterministic_with_stable_ordering(tmp_path: Path) -> None:
    repo, manifest, output = _fixture_repo(tmp_path, skills=("zeta", "alpha", "middle"))
    first = tmp_path / "first"
    second = tmp_path / "second"
    assert _run(repo, manifest, first).returncode == 0
    assert _run(repo, manifest, second).returncode == 0
    assert _tree_digest(first) == _tree_digest(second)
    assert _tree_bytes(first) == _tree_bytes(second)


def test_second_generation_is_byte_identical(tmp_path: Path) -> None:
    repo, manifest, output = _fixture_repo(tmp_path, skills=("alpha", "beta"))
    assert _run(repo, manifest, output).returncode == 0
    first = _tree_bytes(output)
    assert _run(repo, manifest, output).returncode == 0
    assert _tree_bytes(output) == first


def test_check_detects_drift_without_mutation(tmp_path: Path) -> None:
    repo, manifest, output = _fixture_repo(tmp_path)
    assert _run(repo, manifest, output).returncode == 0
    generated = output / "agent-skills" / "skills" / "codesleuth-alpha" / "SKILL.md"
    generated.write_text(generated.read_text(encoding="utf-8") + "\nDRIFT\n", encoding="utf-8", newline="\n")
    drifted = generated.read_bytes()
    result = _run(repo, manifest, output, "--check")
    assert result.returncode != 0
    assert "drift" in result.stderr.lower()
    assert generated.read_bytes() == drifted


def test_agent_skills_representation_matches_verified_upstream_contract(tmp_path: Path) -> None:
    repo, manifest, output = _fixture_repo(tmp_path)
    result = _run(repo, manifest, output, "--adapter", "agent-skills")
    assert result.returncode == 0, result.stderr
    skill = output / "agent-skills" / "skills" / "codesleuth-alpha" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    keys = _frontmatter_keys(text)
    assert keys <= AGENT_SKILL_FIELDS
    assert "slash" not in keys
    assert "name: codesleuth-alpha\n" in text
    assert skill.parent.name == "codesleuth-alpha"
    assert "description:" in text


def test_agent_plugins_representation_matches_verified_upstream_contract(tmp_path: Path) -> None:
    repo, manifest, output = _fixture_repo(tmp_path)
    result = _run(repo, manifest, output, "--adapter", "agent-plugins")
    assert result.returncode == 0, result.stderr
    plugin_root = output / "agent-plugins" / "codesleuth"
    plugin = _json(plugin_root / "plugin.json")
    assert plugin == {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": "codesleuth-portable",
    }
    skill = plugin_root / "skills" / "codesleuth-alpha" / "SKILL.md"
    assert skill.is_file()
    assert skill.parent.parent == plugin_root / "skills"
    assert not (plugin_root / "mcp.json").exists()


def test_skills_only_capabilities_exclude_full_project_claims(tmp_path: Path) -> None:
    repo, manifest, output = _fixture_repo(tmp_path)
    assert _run(repo, manifest, output, "--adapter", "agent-skills").returncode == 0
    capabilities = _json(output / "agent-skills" / "codesleuth-capabilities.json")
    assert capabilities["installationLevel"] == "skills-only"
    assert FULL_PROJECT_CLAIMS.isdisjoint(capabilities["claims"])
    assert FULL_PROJECT_CLAIMS <= set(capabilities["notInstalled"])


def test_plugin_capabilities_do_not_claim_full_project_installation(tmp_path: Path) -> None:
    repo, manifest, output = _fixture_repo(tmp_path)
    assert _run(repo, manifest, output, "--adapter", "agent-plugins").returncode == 0
    capabilities = _json(output / "agent-plugins" / "codesleuth" / "codesleuth-capabilities.json")
    assert capabilities["installationLevel"] == "plugin"
    assert FULL_PROJECT_CLAIMS.isdisjoint(capabilities["claims"])
    assert FULL_PROJECT_CLAIMS <= set(capabilities["notInstalled"])


def test_generated_adapters_are_not_input_semantic_authority(tmp_path: Path) -> None:
    repo, manifest, output = _fixture_repo(tmp_path)
    source = repo / "pack" / ".opencode" / "skills" / "alpha" / "SKILL.md"
    source_before = source.read_bytes()
    assert _run(repo, manifest, output).returncode == 0
    generated = output / "agent-skills" / "skills" / "codesleuth-alpha" / "SKILL.md"
    expected = generated.read_bytes()
    generated.write_text("invented second authority\n", encoding="utf-8", newline="\n")
    assert _run(repo, manifest, output).returncode == 0
    assert generated.read_bytes() == expected
    assert source.read_bytes() == source_before


def test_malformed_source_fails_closed(tmp_path: Path) -> None:
    repo, manifest, output = _fixture_repo(tmp_path, malformed_skill="alpha")
    result = _run(repo, manifest, output)
    assert result.returncode != 0
    assert "malformed" in result.stderr.lower() or "frontmatter" in result.stderr.lower()
    assert not output.exists()


def test_unknown_adapter_fails_closed(tmp_path: Path) -> None:
    repo, manifest, output = _fixture_repo(tmp_path)
    result = _run(repo, manifest, output, "--adapter", "future-host")
    assert result.returncode != 0
    assert "unknown adapter" in result.stderr.lower()
    assert not output.exists()


def test_output_path_traversal_is_rejected(tmp_path: Path) -> None:
    repo, manifest, output = _fixture_repo(
        tmp_path,
        adapter_outputs={"agent-skills": "../escape", "agent-plugins": "agent-plugins/codesleuth"},
    )
    escaped = output.parent / "escape"
    result = _run(repo, manifest, output)
    assert result.returncode != 0
    assert "output" in result.stderr.lower() and ("traversal" in result.stderr.lower() or "root" in result.stderr.lower())
    assert not escaped.exists()


def test_unknown_manifest_field_fails_closed(tmp_path: Path) -> None:
    repo, manifest, output = _fixture_repo(tmp_path, extra_manifest={"futureGuess": True})
    result = _run(repo, manifest, output)
    assert result.returncode != 0
    assert "unknown" in result.stderr.lower()


def test_committed_generated_representations_match_canonical_source() -> None:
    assert GENERATOR.is_file(), f"missing portable generator: {GENERATOR.relative_to(ROOT)}"
    assert MANIFEST.is_file(), f"missing portable distribution manifest: {MANIFEST.relative_to(ROOT)}"
    assert NAMING.is_file()
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert GENERATED.is_dir()
