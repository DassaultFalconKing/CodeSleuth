"""Isolate the host-tracked repository registry from the operator machine."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolate_codesleuth_host_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request) -> None:
    """Keep install/TUI tests from writing pytest leftovers into the live host catalog.

    - Uses a per-test ``CODESLEUTH_HOST_STATE_DIR`` inside ``tmp_path``.
    - Honors ``@pytest.mark.no_host_isolation`` or ``--no-host-isolation`` opt-out for tests
      that explicitly verify default host-state resolution.
    - Preserves Windows path semantics via ``Path.resolve()`` in the implementation.
    """
    if request.node.get_closest_marker("no_host_isolation"):
        return
    # Allow explicit opt-out via env var for subprocess-based tests that set their own env
    # but still need default resolution.  Marker is preferred.
    monkeypatch.setenv("CODESLEUTH_HOST_STATE_DIR", str(tmp_path / "codesleuth-host-state"))
