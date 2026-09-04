from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys

_CASES_PATH = Path(__file__).with_name("eha_github_bridge_workflow_hardening_cases.py")
_spec = importlib.util.spec_from_file_location("eha_github_bridge_workflow_hardening_cases", _CASES_PATH)
assert _spec and _spec.loader
_cases = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _cases
_spec.loader.exec_module(_cases)

_EXCLUDED = {"test_remote_eha_does_not_stream_opencode_transcript_to_public_actions_log"}
for _name, _value in vars(_cases).items():
    if _name.startswith("test_") and callable(_value) and _name not in _EXCLUDED:
        globals()[_name] = _value


def _load_bridge():
    scripts = str(_cases.ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location("eha_github_bridge_privacy_behavior", _cases.SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_remote_eha_does_not_stream_opencode_transcript_to_public_actions_log(tmp_path, capsys) -> None:
    bridge = _load_bridge()
    transcript = tmp_path / "private-transcript.log"
    state = tmp_path / "state"
    state.mkdir()
    marker = "PRIVATE_PROVIDER_TRANSCRIPT_SENTINEL"
    started = bridge.datetime.now(bridge.timezone.utc)

    result = bridge.run_monitored_process(
        [sys.executable, "-c", f"print({marker!r}, flush=True)"],
        cwd=tmp_path,
        env=os.environ.copy(),
        transcript_path=transcript,
        state_dir=state,
        expected_sha="b" * 40,
        started_at=started,
        watchdog=bridge.WatchdogConfig(
            first_response_seconds=1,
            campaign_start_seconds=1,
            idle_seconds=1,
            poll_seconds=0.02,
        ),
    )

    captured = capsys.readouterr()
    assert result[0] == 0
    assert marker in transcript.read_text(encoding="utf-8")
    assert marker not in captured.out
    assert marker not in captured.err
