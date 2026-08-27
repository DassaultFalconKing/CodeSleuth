"""Managed AGENTS.md policy block: exactly one fenced CodeSleuth block, user-owned surrounding text preserved."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

POLICY_BEGIN = "<!-- CODESLEUTH:AGENTS-RULES:BEGIN -->"
POLICY_END = "<!-- CODESLEUTH:AGENTS-RULES:END -->"
POLICY_STATE_REL = Path(".opencode/state/agents-policy.json")
CANONICAL_REL = Path("policy/agents-rules.md")


def _pack_root() -> Path:
    # This module lives under pack/.opencode/bin/codesleuth_project
    return Path(__file__).resolve().parents[2]


def canonical_policy_text() -> str:
    """Return canonical policy inner text as stored in the pack (LF normalized, no surrounding markers)."""
    cand = _pack_root() / CANONICAL_REL
    if not cand.is_file():
        raise FileNotFoundError(f"canonical policy not found: {cand}")
    raw = cand.read_bytes().decode("utf-8")
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip() + "\n"


def canonical_policy_hash() -> str:
    data = canonical_policy_text().encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _detect_line_ending(text: str) -> str:
    if "\r\n" in text:
        return "\r\n"
    return "\n"


def _read_agents_md(repo: Path) -> tuple[bytes | None, str | None]:
    path = repo / "AGENTS.md"
    if not path.is_file():
        return None, None
    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise RuntimeError("AGENTS.md is not valid UTF-8; refusing to modify")
    return data, text


def _write_agents_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def _strip_one_leading_eol(text: str, eol: str) -> str:
    """Remove at most one CodeSleuth-owned marker-line terminator after END."""
    if eol and text.startswith(eol):
        return text[len(eol) :]
    if text.startswith("\r\n"):
        return text[2:]
    if text.startswith("\n") or text.startswith("\r"):
        return text[1:]
    return text


def validate_agents_rules(repo: Path) -> None:
    """Fail closed if AGENTS.md contains malformed or duplicate managed block.

    Allows: 0 blocks, or exactly 1 well-formed block where BEGIN precedes END and no overlap.
    Raises RuntimeError otherwise and must not be used to guess deletion.
    """
    _, text = _read_agents_md(repo)
    if text is None:
        return
    begins = text.count(POLICY_BEGIN)
    ends = text.count(POLICY_END)
    if begins == 0 and ends == 0:
        return
    if begins != 1 or ends != 1:
        raise RuntimeError("malformed CodeSleuth AGENTS.md block: duplicate or missing marker")
    b = text.find(POLICY_BEGIN)
    e = text.find(POLICY_END)
    if b < 0 or e < 0 or e < b:
        raise RuntimeError("malformed CodeSleuth AGENTS.md block: BEGIN without END")
    inner = text[b + len(POLICY_BEGIN) : e]
    if POLICY_BEGIN in inner or POLICY_END in inner:
        raise RuntimeError("malformed CodeSleuth AGENTS.md block: nested markers")
    next_b = text.find(POLICY_BEGIN, b + len(POLICY_BEGIN))
    if next_b != -1 and next_b < e:
        raise RuntimeError("malformed CodeSleuth AGENTS.md block: BEGIN without END")


def _build_block(canonical_text: str, eol: str) -> str:
    inner = canonical_text.replace("\r\n", "\n").replace("\r", "\n")
    inner = inner.strip("\n") + "\n" if inner.strip() else ""
    inner_eol = inner.replace("\n", eol)
    return f"{POLICY_BEGIN}{eol}{inner_eol}{POLICY_END}"


def ensure_agents_rules(repo: Path, canonical_text: str | None = None) -> Path:
    """Ensure AGENTS.md contains exactly one managed block with canonical_text.

    Preserves all text outside the block, preserves dominant line ending, and is idempotent.
    Fail closed on malformed/duplicate markers.
    """
    if canonical_text is None:
        canonical_text = canonical_policy_text()
    path = repo / "AGENTS.md"
    validate_agents_rules(repo)
    data, text = _read_agents_md(repo)
    if text is None:
        eol = "\n"
        block = _build_block(canonical_text, eol)
        _write_agents_text(path, block + eol)
        _record_state(repo, created_by_codesleuth=True, canonical_text=canonical_text)
        return path

    eol = _detect_line_ending(text)
    had_final_newline = text.endswith("\n") or text.endswith("\r")
    block = _build_block(canonical_text, eol)

    begins = text.count(POLICY_BEGIN)
    if begins == 0:
        if text.strip() == "":
            new_text = block + eol
        elif had_final_newline:
            new_text = text + block + eol
        else:
            new_text = text + eol + block + eol
        _write_agents_text(path, new_text)
        _record_state(repo, created_by_codesleuth=False, canonical_text=canonical_text)
        return path

    b = text.find(POLICY_BEGIN)
    e = text.find(POLICY_END) + len(POLICY_END)
    before = text[:b]
    after = text[e:]
    current_block = text[b:e]
    if current_block == block:
        _record_state(repo, created_by_codesleuth=_state_created_by(repo), canonical_text=canonical_text)
        return path
    new_text = before + block + after
    if had_final_newline and not (new_text.endswith("\n") or new_text.endswith("\r")):
        new_text += eol
    _write_agents_text(path, new_text)
    _record_state(repo, created_by_codesleuth=_state_created_by(repo), canonical_text=canonical_text)
    return path


def _remaining_after_block_removal(text: str) -> str:
    """Return exact user-owned bytes with the managed block removed.

    Strips at most one CodeSleuth-owned line terminator immediately after END so
    an append-at-EOF round-trip restores the original user file. All other
    surrounding bytes, including extra blank lines, are preserved.
    """
    b = text.find(POLICY_BEGIN)
    e = text.find(POLICY_END)
    before = text[:b]
    after = text[e + len(POLICY_END) :]
    eol = _detect_line_ending(text)
    after = _strip_one_leading_eol(after, eol)
    return before + after


def remove_agents_rules(repo: Path) -> bool:
    """Remove managed block if present. Fail closed on malformed/duplicate. Returns True if removed."""
    _, text = _read_agents_md(repo)
    if text is None:
        return False
    begins = text.count(POLICY_BEGIN)
    ends = text.count(POLICY_END)
    if begins == 0 and ends == 0:
        return False
    if begins != 1 or ends != 1:
        raise RuntimeError("malformed CodeSleuth AGENTS.md block: duplicate or missing marker; refusing to delete")
    b = text.find(POLICY_BEGIN)
    e = text.find(POLICY_END)
    if e < b:
        raise RuntimeError("malformed CodeSleuth AGENTS.md block: BEGIN without END")
    inner = text[b + len(POLICY_BEGIN) : e]
    if POLICY_BEGIN in inner or POLICY_END in inner:
        raise RuntimeError("malformed CodeSleuth AGENTS.md block: nested markers")

    remaining = _remaining_after_block_removal(text)
    path = repo / "AGENTS.md"
    created = _state_created_by(repo)
    if remaining.strip() == "" and created is True:
        path.unlink(missing_ok=True)
        _clear_state(repo)
        return True
    _write_agents_text(path, remaining)
    _clear_state(repo)
    return True


def apply_agents_md_policy(repo: Path, *, enforce: bool, canonical_text: str | None = None) -> None:
    """Fail-closed apply or remove. Callers must preflight via this function before persisting settings."""
    validate_agents_rules(repo)
    if enforce:
        ensure_agents_rules(repo, canonical_text)
    else:
        remove_agents_rules(repo)


def _hash_canonical(canonical_text: str) -> str:
    return hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()


def _state_path(repo: Path) -> Path:
    return repo / POLICY_STATE_REL


def _record_state(repo: Path, created_by_codesleuth: bool | None, canonical_text: str) -> None:
    path = _state_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    if path.is_file():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    existing.update({
        "schemaVersion": 1,
        "createdByCodesleuth": created_by_codesleuth if created_by_codesleuth is not None else existing.get("createdByCodesleuth"),
        "canonicalHash": _hash_canonical(canonical_text),
        "lastAppliedHash": _hash_canonical(canonical_text),
    })
    path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")


def _state_created_by(repo: Path) -> bool | None:
    path = _state_path(repo)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    value = data.get("createdByCodesleuth")
    if value is True:
        return True
    if value is False:
        return False
    return None


def _clear_state(repo: Path) -> None:
    path = _state_path(repo)
    if path.is_file():
        path.unlink()
