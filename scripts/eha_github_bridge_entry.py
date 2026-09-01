#!/usr/bin/env python3
"""Canonical CodeSleuth GitHub EHA bridge entry point.

The stable bridge primitives live in eha_github_bridge_core; RC6 trusted
campaign/provenance bootstrap lives in eha_github_bridge_controller. This module
re-exports the stable primitives for tests/operators while owning the only
production CLI entry point.
"""

from eha_github_bridge_core import *  # noqa: F403
from eha_github_bridge_controller import bootstrap_then_invoke, invoke_opencode_rc6, main

__all__ = ["bootstrap_then_invoke", "invoke_opencode_rc6", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
