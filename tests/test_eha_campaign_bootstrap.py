from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys

_CASES_PATH = Path(__file__).with_name("eha_campaign_bootstrap_cases.py")
_spec = importlib.util.spec_from_file_location("eha_campaign_bootstrap_cases", _CASES_PATH)
assert _spec and _spec.loader
_cases = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _cases
_spec.loader.exec_module(_cases)

_EXCLUDED = {"test_workflow_uses_one_canonical_bridge_entrypoint"}
for _name, _value in vars(_cases).items():
    if _name.startswith("test_") and callable(_value) and _name not in _EXCLUDED:
        globals()[_name] = _value


def test_workflow_uses_one_canonical_bridge_entrypoint() -> None:
    bridge = _cases.load_module("eha_github_bridge_behavior", _cases.BRIDGE_SCRIPT)
    assert callable(bridge.main)
    assert callable(bridge.bootstrap_then_invoke)
    completed = subprocess.run(
        [sys.executable, str(_cases.BRIDGE_SCRIPT), "--help"],
        cwd=_cases.ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert completed.returncode == 0
    assert "--persist-root" in completed.stdout
    assert "--model" in completed.stdout
