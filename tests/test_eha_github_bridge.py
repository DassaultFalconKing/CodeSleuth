from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

_CASES_PATH = Path(__file__).with_name("eha_github_bridge_cases.py")
_spec = importlib.util.spec_from_file_location("eha_github_bridge_cases", _CASES_PATH)
assert _spec and _spec.loader
_cases = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _cases
_spec.loader.exec_module(_cases)

_EXCLUDED = {"test_workflow_is_a_delegating_owner_gated_self_hosted_bridge"}
for _name, _value in vars(_cases).items():
    if _name.startswith("test_") and callable(_value) and _name not in _EXCLUDED:
        globals()[_name] = _value


def test_workflow_is_a_delegating_owner_gated_self_hosted_bridge(tmp_path, monkeypatch) -> None:
    scripts = str(_cases.ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    controller = importlib.import_module("eha_github_bridge_controller")
    captured: dict[str, object] = {}

    monkeypatch.setattr(controller.shutil, "which", lambda name: "/trusted/opencode" if name == "opencode" else None)
    monkeypatch.setattr(controller.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout="1.18.25\n"))
    monkeypatch.setattr(controller.bridge, "opencode_wrapper_command", lambda root: ["/trusted/opencode"])
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setattr(controller.bridge, "prepare_scratch_dir", lambda root, persist: scratch)
    monkeypatch.setattr(controller.bridge, "opencode_environment", lambda *args, **kwargs: {"BASE": "1"})

    def fake_monitor(command, **kwargs):
        captured["command"] = list(command)
        captured["env"] = dict(kwargs["env"])
        started_at = kwargs["started_at"]
        return 0, None, True, True, False, started_at, None

    monkeypatch.setattr(controller.bridge, "run_monitored_process", fake_monitor)
    started = controller.bridge.datetime.now(controller.bridge.timezone.utc)
    transcript = tmp_path / "private" / "bridge.log"
    transcript.parent.mkdir()
    execution = controller.invoke_opencode_rc6(
        tmp_path,
        "dev/release-0.4.0",
        "a" * 40,
        "RC6 exact-head acceptance",
        "provider/model",
        transcript,
        tmp_path / "state",
        started,
        controller.bridge.WatchdogConfig(),
        review_id="review-prestarted",
        campaign_id="EHA-prestarted",
        provenance_watermark="github-eha-0123456789ab",
    )

    command = captured["command"]
    assert command[:6] == ["/trusted/opencode", "run", "--command", "eha-test", "--format", "json"]
    assert command[6:8] == ["--model", "provider/model"]
    env = captured["env"]
    assert env["CODESLEUTH_EHA_REVIEW_ID"] == "review-prestarted"
    assert env["CODESLEUTH_EHA_CAMPAIGN_ID"] == "EHA-prestarted"
    assert env["CODESLEUTH_EHA_PROVENANCE"] == "github-eha-0123456789ab"
    assert execution.transport_outcome == "PASS"
    assert execution.first_response_observed is True
    assert execution.campaign_observed is True
