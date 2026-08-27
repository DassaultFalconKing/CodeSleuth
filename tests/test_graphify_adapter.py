from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "graphify_adapter.py"
SPEC = importlib.util.spec_from_file_location("codesleuth_graphify_adapter", SCRIPT)
assert SPEC and SPEC.loader
ADAPTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTER)


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def repository(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "CodeSleuth Test")
    (tmp_path / "app.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    (tmp_path / "other.py").write_text("from app import run\n", encoding="utf-8")
    git(tmp_path, "add", "app.py", "other.py")
    git(tmp_path, "commit", "-qm", "fixture")
    return tmp_path


def test_input_manifest_is_tracked_bounded_and_exact(tmp_path: Path) -> None:
    root = repository(tmp_path)
    files, provenance = ADAPTER.validate_inputs(root, ["other.py", "app.py", "app.py"])
    assert [path.name for path in files] == ["app.py", "other.py"]
    assert all(item["exactIndexMatch"] for item in provenance.values())
    (root / "untracked.py").write_text("secret = True\n", encoding="utf-8")
    with pytest.raises(ADAPTER.AdapterError, match="not one tracked"):
        ADAPTER.validate_inputs(root, ["untracked.py"])
    with pytest.raises(ADAPTER.AdapterError, match="normalized"):
        ADAPTER.validate_inputs(root, ["../outside.py"])


def test_dirty_input_cannot_promote_extracted_edge(tmp_path: Path) -> None:
    root = repository(tmp_path)
    (root / "other.py").write_text("from app import run\n# dirty\n", encoding="utf-8")
    _, provenance = ADAPTER.validate_inputs(root, ["app.py", "other.py"])
    extraction = {
        "nodes": [
            {"id": "a", "label": "run()", "file_type": "code", "source_file": "app.py"},
            {"id": "b", "label": "other.py", "file_type": "code", "source_file": "other.py"},
        ],
        "edges": [
            {"source": "b", "target": "a", "relation": "calls", "confidence": "EXTRACTED"}
        ],
    }
    result = ADAPTER.normalize_extraction(extraction, provenance)
    assert result["edges"][0]["origin"] == "review_inference"
    assert provenance["other.py"]["exactIndexMatch"] is False


def test_unknown_and_ambiguous_semantics_fail_closed(tmp_path: Path) -> None:
    root = repository(tmp_path)
    _, provenance = ADAPTER.validate_inputs(root, ["app.py", "other.py"])
    extraction = {
        "nodes": [
            {"id": "a", "label": "run()", "file_type": "code", "source_file": "app.py"},
            {"id": "b", "label": "other.py", "file_type": "code", "source_file": "other.py"},
        ],
        "edges": [
            {"source": "b", "target": "a", "relation": "inherits", "confidence": "EXTRACTED"},
            {"source": "b", "target": "a", "relation": "calls", "confidence": "AMBIGUOUS"},
        ],
    }
    result = ADAPTER.normalize_extraction(extraction, provenance)
    assert result["diagnostics"]["unmappedRelations"] == {"inherits": 1}
    assert len(result["edges"]) == 1
    assert result["edges"][0]["origin"] == "review_inference"
    assert "AMBIGUOUS" in result["edges"][0]["note"]


def test_exact_runtime_executes_local_structural_api(tmp_path: Path) -> None:
    runtime = ROOT / ".runtime" / "graphify-provider"
    if not runtime.is_dir():
        pytest.skip("optional exact Graphify runtime not installed")
    root = repository(tmp_path)
    result = ADAPTER.run_provider(root, ["app.py", "other.py"], runtime=runtime)
    assert result["provider"]["version"] == "0.9.50"
    assert result["provider"]["upstreamCommit"] == ADAPTER.PROVIDER_COMMIT
    assert result["provider"]["network"] is False
    assert result["provider"]["semanticLlm"] is False
    assert result["input"]["fileCount"] == 2
    assert result["selection"]["returned"]["nodes"] > 0
    assert json.dumps(result).find("graphify-out") == -1


def test_provider_pin_and_verified_profile_lock_are_visible() -> None:
    top_level = (ROOT / "tools" / "graphify-provider" / "requirements.txt").read_text(
        encoding="utf-8"
    )
    lock = (ROOT / "tools" / "graphify-provider" / "requirements-lock.txt").read_text(
        encoding="utf-8"
    )
    docs = (ROOT / "docs" / "GRAPHIFY-PROVIDER.md").read_text(encoding="utf-8")
    assert "graphifyy==0.9.50" in top_level and "graphifyy==0.9.50" in lock
    assert ADAPTER.PROVIDER_COMMIT in top_level and ADAPTER.PROVIDER_COMMIT in docs
    assert "builtin repository mapping remains default" in docs
    assert ".runtime/graphify-provider" in docs
