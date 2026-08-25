"""Shared CodeSleuth constants (single authority for TUI/settings literals)."""

from __future__ import annotations

SETTINGS_SCHEMA = 1
TEXTUAL_VERSION = "8.2.8"
PROFILES = ("generic", "rust", "python", "node", "typescript")
PERMISSION_VALUES = ("allow", "ask", "deny")
AGENT_PROFILES = ("native", "open-weight", "codex", "claude")
AGENT_PROFILE_OPTIONS = [
    ("OpenCode native (current model)", "native"),
    ("Open-weight (native kimi.txt when model is Kimi)", "open-weight"),
    ("Codex (native codex.txt)", "codex"),
    ("Claude (native anthropic.txt)", "claude"),
]
