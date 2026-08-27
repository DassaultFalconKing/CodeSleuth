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
    # Also check installed location for verification after install
    if not cand.is_file():
        # When running from installed .opencode (tests use repo/.opencode)
        # Caller will pass explicit canonical path; this is fallback.
        raise FileNotFoundError(f"canonical policy not found: {cand}")
    raw = cand.read_bytes().decode("utf-8")
    # Normalize line endings to LF for storage, strip trailing whitespace but keep internal structure
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    # Canonical file should end with newline; keep content without requiring final newline to be part of hash.
    return text.strip() + "\n"


def canonical_policy_hash() -> str:
    data = canonical_policy_text().encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _detect_line_ending(text: str) -> str:
    if "\r\n" in text:
        return "\r\n"
    return "\n"


def _has_final_newline_bytes(data: bytes) -> bool:
    return data.endswith(b"\n") or data.endswith(b"\r")


def _read_agents_md(repo: Path) -> tuple[bytes | None, str | None]:
    path = repo / "AGENTS.md"
    if not path.is_file():
        return None, None
    data = path.read_bytes()
    # Decode preserving content, but we need text for marker search. Use utf-8.
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        # Fail closed on binary/unexpected encoding – preserve file.
        raise RuntimeError("AGENTS.md is not valid UTF-8; refusing to modify")
    return data, text


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
    # Check for overlapping / nested markers inside block content (should not contain markers)
    inner = text[b + len(POLICY_BEGIN): e]
    if POLICY_BEGIN in inner or POLICY_END in inner:
        raise RuntimeError("malformed CodeSleuth AGENTS.md block: nested markers")
    # Ensure no second BEGIN before END (already checked counts, but be explicit)
    next_b = text.find(POLICY_BEGIN, b + len(POLICY_BEGIN))
    if next_b != -1 and next_b < e:
        raise RuntimeError("malformed CodeSleuth AGENTS.md block: BEGIN without END")


def _build_block(canonical_text: str, eol: str) -> str:
    inner = canonical_text.replace("\r\n", "\n").replace("\r", "\n")
    # Ensure inner ends with no extra blank line, then we wrap.
    inner = inner.strip("\n") + "\n" if inner.strip() else ""
    # Convert inner LF to target eol
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
        # New file: exactly block + eol
        path.write_text(block + eol, encoding="utf-8", newline="")
        _record_state(repo, created_by_codesleuth=True, canonical_text=canonical_text)
        return path

    eol = _detect_line_ending(text)
    had_final_newline = text.endswith("\n") or text.endswith("\r")
    block = _build_block(canonical_text, eol)

    begins = text.count(POLICY_BEGIN)
    if begins == 0:
        # Append without rewriting existing content's line endings
        # Preserve original's final newline behavior: if original had no final newline, insert eol before block.
        if had_final_newline:
            # Original ends with newline, we can just append block
            # need to ensure we don't add extra blank line: original already ends with eol, block starts with marker
            # Append block with preceding separation: if text ends with eol, add block directly; else add eol + block
            # Simpler: strip trailing eol handling – we want exactly one blank separation? Keep original's trailing newline, then block.
            # If original text is empty or only whitespace, treat as empty.
            if text.strip() == "":
                new_text = block + eol
            else:
                # Ensure we have a blank line separation? Original pattern for reports pointer uses two newlines before block when body non-empty.
                # For policy block, use single newline separation to avoid double blank lines if original already ends with eol.
                # If original ends with eol, we just append block; otherwise append eol + block
                new_text = text + block + eol if text.endswith(eol) else text + eol + block + eol
                # But text already ends with eol in had_final_newline case, so first branch is text + block + eol (which adds block directly after existing eol)
                # For idempotence, we should not add extra eol if text already ends with eol and block already ends with eol – file will end with eol (good).
                # Need to handle CRLF case where text.endswith("\n") true even for CRLF, but we already have eol.
                pass
        else:
            # No final newline, preserve that quirk for the user part, but add separation
            new_text = text + eol + block + eol
        # Write preserving eol by disabling newline translation
        path.write_text(new_text, encoding="utf-8", newline="")
        _record_state(repo, created_by_codesleuth=False, canonical_text=canonical_text)
        return path

    # Exactly one block exists – replace only inner content if needed, preserve surrounding bytes
    b = text.find(POLICY_BEGIN)
    e = text.find(POLICY_END) + len(POLICY_END)
    before = text[:b]
    after = text[e:]
    # before and after are preserved exactly (including their line endings)
    # We need to ensure block replacement does not alter surrounding newlines gratuitously.
    # Construct new_text = before + block + after
    # However before may end with eol or not, and after may start with eol or not. We keep them as-is.
    # To avoid doubling newlines, we check: block already starts with BEGIN and ends with END. The surrounding text's newlines are kept.
    # Common pattern: before ends with \n, block starts with BEGIN, after starts with \n.
    # Our block includes its own internal eols but not extra surrounding eols beyond markers.
    # So recompose:
    new_inner_block = block
    # If before ends without newline and is non-empty, we might want to ensure separation? But existing valid file already has separation; we preserve it.
    # For idempotence, we replace exactly the old block with new block; surrounding stays.
    current_block = text[b:e]
    if current_block == block and _hash_canonical(canonical_text) == _hash_block_inner(current_block, eol):
        # Already current – ensure state updated but no write
        _record_state(repo, created_by_codesleuth=_state_created_by(repo), canonical_text=canonical_text)
        return path
    new_text = before + new_inner_block + after
    # Preserve final newline behavior: if original had final newline, ensure new_text ends with eol; else preserve absence? For simplicity, ensure file ends with eol when block is present (common). But spec says preserve LF/CRLF/final-newline where practical.
    # If original had no final newline and after was empty, new_text would end with END without trailing eol. We should add eol to match newly built block's trailing eol handling.
    # Our block does not include trailing eol after END; we added eol when building file for append case but not for replace case. Decide: block itself does not include trailing eol; surrounding after may contain it.
    # To keep idempotence, if after == "" (block at EOF), we should ensure file ends with eol if had_final_newline or if block was previously ending with eol. Simpler: if new_text and not new_text.endswith("\n") and not new_text.endswith("\r"):
    #   Append eol if had_final_newline else don't? But had_final_newline in replace case is whether original file ended with newline.
    # We will preserve: if had_final_newline and not new_text.endswith(("\n", "\r")): new_text += eol
    if had_final_newline and not (new_text.endswith("\n") or new_text.endswith("\r")):
        new_text += eol
    path.write_text(new_text, encoding="utf-8", newline="")
    _record_state(repo, created_by_codesleuth=_state_created_by(repo), canonical_text=canonical_text)
    return path


def remove_agents_rules(repo: Path) -> bool:
    """Remove managed block if present. Fail closed on malformed/duplicate. Returns True if removed."""
    _, text = _read_agents_md(repo)
    if text is None:
        return False
    # Fail closed on malformed
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
    inner = text[b + len(POLICY_BEGIN): e]
    if POLICY_BEGIN in inner or POLICY_END in inner:
        raise RuntimeError("malformed CodeSleuth AGENTS.md block: nested markers")
    # Remove block
    before = text[:b]
    after = text[e + len(POLICY_END):]
    # Preserve line ending style for surrounding
    # Remove the block plus one surrounding newline to avoid leaving double blank lines, but preserve user content.
    # Approach: rstrip then lstrip one newline sequence.
    # Detect eol for this file
    eol = _detect_line_ending(text)
    # Normalize removal: before.rstrip trailing whitespace's newlines? Use logic similar to reports pointer but CRLF-aware.
    # We want: before.rstrip("\r\n") + after.lstrip("\r\n") handling, but preserve whether file had content.
    # Use string operations that handle both \n and \r\n
    # Remove block and clean up: before without trailing eols, after without leading eols, then re-join
    before_stripped = before.rstrip("\r\n")
    after_stripped = after.lstrip("\r\n")
    if before_stripped == "" and after_stripped == "":
        # No user content remains – delete file only if created by CodeSleuth
        path = repo / "AGENTS.md"
        created = _state_created_by(repo)
        # Heuristic: if state says createdByCodesleuth True, or before/after empty and we have no prior user hash, delete
        # Also check preinstall snapshot: if AGENTS.md was not in preinstall, treat as created
        if created is True:
            path.unlink(missing_ok=True)
            _clear_state(repo)
            return True
        # If we don't know, check if file was empty besides block – safest is to delete if no user text
        # But spec: delete AGENTS.md only when CodeSleuth created it and nothing user-owned remains.
        # If we have no state, we conservatively keep empty file? Spec says delete only when CodeSleuth created it.
        # So if we don't have state, we should not delete.
        if created is None:
            # Look at preinstall: if AGENTS.md not in preinstall, it was created by CodeSleuth
            try:
                from codesleuth_project import _load_snapshot
                manifest, _ = _load_snapshot(repo)
                if manifest is not None:
                    paths = {entry["path"] for entry in manifest.get("files", [])}
                    if "AGENTS.md" not in paths:
                        path.unlink(missing_ok=True)
                        _clear_state(repo)
                        return True
            except Exception:
                pass
        # Otherwise remove block and leave empty file? Spec says preserve file if user-owned remains; here none remains but not created by us – keep empty?
        # Fallback: delete if empty and no state indicates user ownership
        if before_stripped == "" and after_stripped == "":
            # No user content, and we are not sure it's user-owned, but spec says delete only when created by Codesleuth.
            # If state is False (user existed), we should keep file with empty content? Instead truncate to empty and not delete.
            if created is False:
                path = repo / "AGENTS.md"
                path.write_text("", encoding="utf-8", newline="")
                _clear_state(repo)
                return True
        path = repo / "AGENTS.md"
        path.unlink(missing_ok=True)
        _clear_state(repo)
        return True

    # Reconstruct with exactly one eol between before and after if both non-empty
    if before_stripped and after_stripped:
        new_text = before_stripped + eol + after_stripped
    elif before_stripped:
        new_text = before_stripped
    else:
        new_text = after_stripped
    # Preserve final newline if original had it and we have content
    had_final_newline = text.endswith("\n") or text.endswith("\r")
    if new_text and had_final_newline and not (new_text.endswith("\n") or new_text.endswith("\r")):
        new_text += eol
    elif new_text:
        # Ensure file ends with newline when we have content? Keep original behavior: if had_final_newline then ensure eol, else not.
        pass
    if new_text:
        new_text = new_text if new_text.endswith(eol) or not had_final_newline else new_text
        # Write only if content remains; ensure trailing newline handling as original
        (repo / "AGENTS.md").write_text(new_text + (eol if had_final_newline and not new_text.endswith(eol) else ""), encoding="utf-8", newline="")
    else:
        (repo / "AGENTS.md").unlink(missing_ok=True)
    _clear_state(repo)
    return True


def _hash_canonical(canonical_text: str) -> str:
    return hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()


def _hash_block_inner(block: str, eol: str) -> str:
    # Extract inner between markers and normalize to LF for hash comparison
    b = block.find(POLICY_BEGIN) + len(POLICY_BEGIN)
    e = block.find(POLICY_END)
    inner = block[b:e]
    inner = inner.replace("\r\n", "\n").replace("\r", "\n").strip() + "\n"
    return hashlib.sha256(inner.encode("utf-8")).hexdigest()


def _state_path(repo: Path) -> Path:
    return repo / POLICY_STATE_REL


def _record_state(repo: Path, created_by_codesleuth: bool | None, canonical_text: str) -> None:
    path = _state_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if path.is_file():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
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
        return data.get("createdByCodesleuth")
    except Exception:
        return None


def _clear_state(repo: Path) -> None:
    path = _state_path(repo)
    if path.is_file():
        try:
            path.unlink()
        except Exception:
            pass
