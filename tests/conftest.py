"""Isolate the host-tracked repository registry from the operator machine."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolate_codesleuth_host_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep install/TUI tests from writing pytest leftovers into the live host catalog."""
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "codesleuth-host-state"))
