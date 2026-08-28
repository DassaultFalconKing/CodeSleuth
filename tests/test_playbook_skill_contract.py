import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "pack" / ".opencode" / "skills"
PLAYBOOKS = ROOT / "pack" / ".opencode" / "playbooks"
COMMANDS = ROOT / "pack" / ".opencode" / "commands"
CONTRACT = ROOT / "docs" / "PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md"


def _skill_ids() -> set[str]:
    return {path.parent.name for path in SKILLS.glob("*/SKILL.md")}


def _manifest_paths() -> list[Path]:
    return sorted(PLAYBOOKS.glob("*/playbook.json"))


def _assert_acyclic(steps: list[dict]) -> None:
    graph = {step["id"]: list(step.get("depends_on", [])) for step in steps}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visited:
            return
        assert node not in visiting, f"playbook dependency cycle at {node}"
        visiting.add(node)
        for dependency in graph[node]:
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)


def test_normative_playbook_skill_contract_exists_and_defines_layers() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    for expected in (
        "Skill    = atomic reusable reasoning procedure loaded on demand",
        "Step     = one independently executable Playbook unit",
        "Playbook = ordered/DAG orchestration of Steps",
        "Command  = user-facing prompt entry point",
        "Tool     = bounded execution primitive",
        "STEP_ISOLATION_UNPROVEN",
        "pack/.opencode/playbooks/<playbook-id>/",
    ):
        assert expected in text


def test_every_codesleuth_skill_is_atomic_and_slash_exposed() -> None:
    skills = sorted(SKILLS.glob("*/SKILL.md"))
    assert skills
    for path in skills:
        text = path.read_text(encoding="utf-8")
        assert "## Atomic contract" in text, path
        for field in ("**Input:**", "**Objective:**", "**Output:**", "**Stop:**", "**Must not:**"):
            assert field in text, f"{path}: missing {field}"
        assert "slash: true" in text.split("---", 2)[1], f"{path}: must remain directly slash-callable"


def test_playbook_manifests_reference_real_atomic_skills_and_steps() -> None:
    skill_ids = _skill_ids()
    manifests = _manifest_paths()
    assert manifests

    for manifest_path in manifests:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        playbook_dir = manifest_path.parent
        assert manifest["schema_version"] == 1
        assert manifest["id"] == playbook_dir.name
        assert (playbook_dir / "PLAYBOOK.md").is_file()
        steps = manifest["steps"]
        assert steps
        ids = [step["id"] for step in steps]
        assert len(ids) == len(set(ids)), f"duplicate step id in {manifest_path}"
        id_set = set(ids)

        for step in steps:
            assert step["execution"] in {"skill", "step"}
            assert step.get("output"), f"{manifest_path}: {step['id']} missing output contract"
            assert step.get("isolation") == "fresh_subagent", f"{manifest_path}: {step['id']} must request fresh step context"
            for dependency in step.get("depends_on", []):
                assert dependency in id_set, f"{manifest_path}: unknown dependency {dependency}"

            if step["execution"] == "skill":
                skill = step.get("skill")
                assert skill in skill_ids, f"{manifest_path}: unknown skill {skill}"
                assert not step.get("prompt"), f"{manifest_path}: Skill Step must not duplicate a Step prompt"
            else:
                prompt = step.get("prompt")
                assert prompt, f"{manifest_path}: composite Step missing prompt"
                prompt_path = playbook_dir / prompt
                assert prompt_path.is_file(), f"{manifest_path}: missing {prompt}"
                for skill in step.get("skills", []):
                    assert skill in skill_ids, f"{manifest_path}: unknown skill {skill}"
            if "tools" in step:
                assert isinstance(step["tools"], list), f"{manifest_path}: {step['id']} tools must be an array"
                for tool in step["tools"]:
                    assert isinstance(tool, str) and tool.strip(), f"{manifest_path}: blank tool name"

        _assert_acyclic(steps)


def test_step_payloads_are_bounded_for_on_demand_materialization() -> None:
    for playbook_dir in sorted(path for path in PLAYBOOKS.iterdir() if path.is_dir()):
        description = playbook_dir / "PLAYBOOK.md"
        assert len(description.read_text(encoding="utf-8").splitlines()) <= 120, description
        for step in sorted((playbook_dir / "steps").glob("*.md")) if (playbook_dir / "steps").is_dir() else []:
            assert len(step.read_text(encoding="utf-8").splitlines()) <= 120, step


def test_playbook_command_requires_one_step_at_a_time_and_host_native_isolation() -> None:
    text = (COMMANDS / "playbook.md").read_text(encoding="utf-8")
    assert "PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md" in text
    assert "playbook.json" in text
    assert ".opencode/playbooks/$1/playbook.json" in text
    assert "pack/.opencode/playbooks/$1/playbook.json" in text
    assert "exactly one Step" in text
    assert "fresh host-native subagent" in text
    assert "STEP_ISOLATION_UNPROVEN" in text


def test_product_commands_route_broad_work_to_playbooks() -> None:
    expected = {
        "repo-review.md": "repository-deep-review",
        "repo-contracts.md": "protected-capability-assessment",
        "repo-docs.md": "repository-documentation",
        "repo-map.md": "repository-map",
        "repo-port.md": "feature-port",
        "eha-test.md": "eha-sib-acceptance",
        "eha-repair.md": "eha-repair",
    }
    for command, playbook_id in expected.items():
        path = COMMANDS / command
        assert path.is_file(), path
        assert playbook_id in path.read_text(encoding="utf-8"), path


def test_discovery_docs_point_to_playbook_skill_contract() -> None:
    assert "docs/PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md" in (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md" in (ROOT / "docs" / "README.md").read_text(encoding="utf-8")


def test_opencode_explicitly_allows_every_bundled_atomic_skill() -> None:
    config = json.loads((ROOT / "pack" / ".opencode" / "opencode.json").read_text(encoding="utf-8"))
    permissions = config["permission"]["skill"]
    assert permissions["*"] == "ask"
    for skill in _skill_ids():
        assert permissions.get(skill) == "allow", f"missing explicit bundled Skill permission: {skill}"
