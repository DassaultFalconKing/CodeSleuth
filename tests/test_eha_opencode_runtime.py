from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts" / "eha_opencode_runtime.py"
WORKFLOW = ROOT / ".github" / "workflows" / "eha.yml"
POSIX_WRAPPER = ROOT / "pack" / ".opencode" / "bin" / "opencode-review"
WINDOWS_WRAPPER = ROOT / "pack" / ".opencode" / "bin" / "opencode-review.ps1"


def load_helper():
    spec = importlib.util.spec_from_file_location("eha_opencode_runtime", HELPER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runtime_config_is_exact_mirror_outside_candidate_and_bootstrap_stays_external(
    tmp_path: Path,
) -> None:
    helper = load_helper()
    repo = tmp_path / "repo"
    source = repo / "pack" / ".opencode"
    (source / "commands").mkdir(parents=True)
    (source / "tools").mkdir()
    (source / "opencode.json").write_text('{"permission": {}}\n', encoding="utf-8")
    (source / "commands" / "eha-test.md").write_text("run EHA\n", encoding="utf-8")
    (source / "tools" / "eha_state.ts").write_text("export {}\n", encoding="utf-8")

    target = tmp_path / "persist" / "bridge-runtime" / "run-1" / "opencode-config"
    prepared = helper.prepare_runtime_config(source, target)

    assert prepared == target.resolve()
    assert (prepared / "opencode.json").read_bytes() == (source / "opencode.json").read_bytes()
    assert (prepared / "commands" / "eha-test.md").read_bytes() == (
        source / "commands" / "eha-test.md"
    ).read_bytes()
    assert (prepared / "tools" / "eha_state.ts").read_bytes() == (
        source / "tools" / "eha_state.ts"
    ).read_bytes()

    # Reproduce the class of OpenCode bootstrap residue seen on the Rc4 EHA host.
    (prepared / "package.json").write_text("{}\n", encoding="utf-8")
    (prepared / "package-lock.json").write_text("{}\n", encoding="utf-8")
    assert not (source / "package.json").exists()
    assert not (source / "package-lock.json").exists()

    # A run identity is single-use. Reusing a prior runtime mirror could mix
    # bootstrap state from different executions, so fail closed instead.
    with pytest.raises(helper.RuntimeConfigError):
        helper.prepare_runtime_config(source, target)


def test_runtime_config_refuses_target_inside_candidate(tmp_path: Path) -> None:
    helper = load_helper()
    repo = tmp_path / "repo"
    source = repo / "pack" / ".opencode"
    source.mkdir(parents=True)
    (source / "opencode.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(helper.RuntimeConfigError):
        helper.prepare_runtime_config(source, repo / ".eha-runtime" / "opencode-config")


def test_eha_workflow_and_both_wrappers_route_only_custom_dir_to_external_runtime() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    posix = POSIX_WRAPPER.read_text(encoding="utf-8")
    windows = WINDOWS_WRAPPER.read_text(encoding="utf-8")

    expected = (
        'export CODESLEUTH_EHA_RUNTIME_CONFIG="${persist_root}/bridge-runtime/'
        '${GITHUB_RUN_ID}-attempt-${GITHUB_RUN_ATTEMPT}/opencode-config"'
    )
    assert workflow.count(expected) == 2

    for wrapper in (posix, windows):
        assert "CODESLEUTH_EHA_RUNTIME_CONFIG" in wrapper
        assert "eha_opencode_runtime.py" in wrapper
        assert "OPENCODE_CONFIG_DIR" in wrapper
        assert "package metadata" in wrapper

    # The bridge remains responsible for binding OPENCODE_CONFIG to the exact
    # tracked target config. The wrappers redirect only the writable custom dir.
    assert 'export OPENCODE_CONFIG="$CODESLEUTH_EHA_RUNTIME_CONFIG' not in posix
    assert "$env:OPENCODE_CONFIG = $RuntimeConfig" not in windows
