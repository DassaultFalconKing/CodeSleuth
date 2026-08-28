from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "graphify_corpus_compare.py"
FIXTURES = ROOT / "tests" / "fixtures" / "graphify-corpus"
SPEC = importlib.util.spec_from_file_location("codesleuth_graphify_corpus", SCRIPT)
assert SPEC and SPEC.loader
CORPUS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CORPUS)


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=check
    )


def test_representative_corpus_reports_bounded_honest_metrics() -> None:
    if not (ROOT / ".runtime" / "graphify-provider").is_dir():
        pytest.skip("optional exact Graphify runtime not installed")
    report = CORPUS.run(FIXTURES, check=True)
    expected = {"python", "typescript", "rust", "mixed", "large-over-limit", "odd-encoding", "codesleuth-self"}
    assert expected <= set(report["cases"])
    assert report["passed"] is True
    assert report["cases"]["large-over-limit"]["truncated"] is True
    assert "no unsupported token-savings claim" in report["measurementScope"]["tokens"]
    for metrics in report["cases"].values():
        assert metrics["wallMs"] >= 0
        assert metrics["pythonPeakBytes"] > 0
        assert metrics["modelVisibleBytes"] > 0


def test_dirty_rename_delete_and_windows_path_contracts(tmp_path: Path) -> None:
    root = tmp_path
    git(root, "init", "-q")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "CodeSleuth Test")
    (root / "old.py").write_text("def old():\n    pass\n", encoding="utf-8")
    git(root, "add", "old.py")
    git(root, "commit", "-qm", "fixture")
    git(root, "mv", "old.py", "new.py")
    with pytest.raises(CORPUS.ADAPTER.AdapterError, match="not one tracked"):
        CORPUS.ADAPTER.validate_inputs(root, ["old.py"])
    _, provenance = CORPUS.ADAPTER.validate_inputs(root, ["new.py"])
    assert provenance["new.py"]["exactIndexMatch"] is True
    with pytest.raises(CORPUS.ADAPTER.AdapterError, match="invalid provider input path"):
        CORPUS.ADAPTER.validate_inputs(root, ["new\\path.py"])
    (root / "new.py").unlink()
    with pytest.raises(CORPUS.ADAPTER.AdapterError, match="missing"):
        CORPUS.ADAPTER.validate_inputs(root, ["new.py"])


def test_symlink_and_gitlink_modes_fail_closed(tmp_path: Path) -> None:
    root = tmp_path
    git(root, "init", "-q")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "CodeSleuth Test")
    blob = subprocess.run(
        ["git", "-C", str(root), "hash-object", "-w", "--stdin"],
        input="target.py",
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    git(root, "update-index", "--add", "--cacheinfo", f"120000,{blob},link.py")
    commit = git(ROOT, "rev-parse", "HEAD").stdout.strip()
    git(root, "update-index", "--add", "--cacheinfo", f"160000,{commit},vendor")
    with pytest.raises(CORPUS.ADAPTER.AdapterError, match="not a regular tracked file"):
        CORPUS.ADAPTER.validate_inputs(root, ["link.py"])
    with pytest.raises(CORPUS.ADAPTER.AdapterError, match="not a regular tracked file"):
        CORPUS.ADAPTER.validate_inputs(root, ["vendor"])


def test_malicious_provider_labels_remain_candidate_data(tmp_path: Path) -> None:
    root = tmp_path
    git(root, "init", "-q")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "CodeSleuth Test")
    (root / "safe.py").write_text("value = 1\n", encoding="utf-8")
    git(root, "add", "safe.py")
    _, provenance = CORPUS.ADAPTER.validate_inputs(root, ["safe.py"])
    hostile = 'x%%\n"<img>`'
    result = CORPUS.ADAPTER.normalize_extraction(
        {
            "nodes": [
                {"id": "hostile", "label": hostile, "file_type": "code", "source_file": "safe.py"}
            ],
            "edges": [],
        },
        provenance,
    )
    assert result["nodes"][0]["label"] == hostile
    assert result["nodes"][0]["sourceRef"]["exactIndexMatch"] is True
    # Escaping belongs to the existing Mermaid renderer, never to provider identity normalization.
    assert result["edges"] == []


def test_cli_refuses_tracked_or_external_report_output(tmp_path: Path) -> None:
    if not (ROOT / ".runtime" / "graphify-provider").is_dir():
        pytest.skip("optional exact Graphify runtime not installed")
    completed = subprocess.run(
        [
            "python",
            str(SCRIPT),
            "--fixtures",
            str(FIXTURES),
            "--output",
            str(tmp_path / "report.json"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 2
    assert "output must remain under ignored .runtime" in completed.stdout
    assert not (tmp_path / "report.json").exists()
