"""Managed AGENTS.md policy block with exact ownership boundaries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

POLICY_BEGIN = "<!-- CODESLEUTH:AGENTS-RULES:BEGIN -->"
POLICY_END = "<!-- CODESLEUTH:AGENTS-RULES:END -->"
POLICY_STATE_REL = Path(".opencode/state/agents-policy.json")
CANONICAL_REL = Path("policy/agents-rules.md")


def _pack_root() -> Path:
    return Path(__file__).resolve().parents[2]


def canonical_policy_text() -> str:
    """Return canonical policy inner text normalized to LF."""
    cand = _pack_root() / CANONICAL_REL
    if not cand.is_file():
        raise FileNotFoundError(f"canonical policy not found: {cand}")
    raw = cand.read_bytes().decode("utf-8")
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip() + "\n"


def canonical_policy_hash() -> str:
    return hashlib.sha256(canonical_policy_text().encode("utf-8")).hexdigest()


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
    except UnicodeDecodeError as exc:
        raise RuntimeError("AGENTS.md is not valid UTF-8; refusing to modify") from exc
    return data, text


def _write_agents_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def validate_agents_rules(repo: Path) -> None:
    """Allow zero managed blocks or exactly one well-formed block; otherwise fail closed."""
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


def _build_block(canonical_text: str, eol: str) -> str:
    inner = canonical_text.replace("\r\n", "\n").replace("\r", "\n")
    inner = inner.strip("\n") + "\n" if inner.strip() else ""
    return f"{POLICY_BEGIN}{eol}{inner.replace(chr(10), eol)}{POLICY_END}"


def ensure_agents_rules(repo: Path, canonical_text: str | None = None) -> Path:
    """Ensure exactly one current managed block while preserving all user-owned bytes.

    Separators inserted solely to put the block on its own lines are recorded
    with hashes of the adjacent user-owned side. They are removed later only
    while both the exact separator and its original anchor still match.
    """
    if canonical_text is None:
        canonical_text = canonical_policy_text()
    path = repo / "AGENTS.md"
    validate_agents_rules(repo)
    _, text = _read_agents_md(repo)

    if text is None:
        eol = "\n"
        block = _build_block(canonical_text, eol)
        _write_agents_text(path, block + eol)
        _record_state(
            repo,
            created_by_codesleuth=True,
            canonical_text=canonical_text,
            owned_prefix="",
            owned_suffix=eol,
            prefix_anchor="",
            suffix_anchor=_text_hash(""),
        )
        return path

    eol = _detect_line_ending(text)
    block = _build_block(canonical_text, eol)
    begins = text.count(POLICY_BEGIN)

    if begins == 0:
        if text == "":
            owned_prefix = ""
            prefix_anchor = ""
            new_text = block + eol
        elif text.endswith("\n") or text.endswith("\r"):
            owned_prefix = ""
            prefix_anchor = ""
            new_text = text + block + eol
        else:
            owned_prefix = eol
            prefix_anchor = _text_hash(text)
            new_text = text + owned_prefix + block + eol
        _write_agents_text(path, new_text)
        _record_state(
            repo,
            created_by_codesleuth=False,
            canonical_text=canonical_text,
            owned_prefix=owned_prefix,
            owned_suffix=eol,
            prefix_anchor=prefix_anchor,
            suffix_anchor=_text_hash(""),
        )
        return path

    b = text.find(POLICY_BEGIN)
    e = text.find(POLICY_END) + len(POLICY_END)
    current_block = text[b:e]
    if current_block != block:
        _write_agents_text(path, text[:b] + block + text[e:])
    _record_state(
        repo,
        created_by_codesleuth=_state_created_by(repo),
        canonical_text=canonical_text,
    )
    return path


def remove_agents_rules(repo: Path) -> bool:
    """Remove the managed block and only still-provable CodeSleuth separators."""
    _, text = _read_agents_md(repo)
    if text is None:
        return False
    begins = text.count(POLICY_BEGIN)
    ends = text.count(POLICY_END)
    if begins == 0 and ends == 0:
        return False
    validate_agents_rules(repo)

    b = text.find(POLICY_BEGIN)
    e = text.find(POLICY_END) + len(POLICY_END)
    before = text[:b]
    after = text[e:]
    owned_prefix, owned_suffix, prefix_anchor, suffix_anchor = _state_owned_boundaries(repo)

    if owned_prefix and before.endswith(owned_prefix) and prefix_anchor:
        candidate = before[: -len(owned_prefix)]
        if _text_hash(candidate) == prefix_anchor:
            before = candidate
    if owned_suffix and after.startswith(owned_suffix) and suffix_anchor:
        candidate = after[len(owned_suffix) :]
        if _text_hash(candidate) == suffix_anchor:
            after = candidate

    remaining = before + after
    path = repo / "AGENTS.md"
    created = _state_created_by(repo)
    if remaining == "" and created is True:
        path.unlink(missing_ok=True)
    else:
        _write_agents_text(path, remaining)
    _clear_state(repo)
    return True


def apply_agents_md_policy(repo: Path, *, enforce: bool, canonical_text: str | None = None) -> None:
    """Fail-closed apply or remove. Callers should invoke before persisting the setting."""
    validate_agents_rules(repo)
    if enforce:
        ensure_agents_rules(repo, canonical_text)
    else:
        remove_agents_rules(repo)


def _hash_canonical(canonical_text: str) -> str:
    return hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()


def _state_path(repo: Path) -> Path:
    return repo / POLICY_STATE_REL


def _load_state(repo: Path) -> dict:
    path = _state_path(repo)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _record_state(
    repo: Path,
    created_by_codesleuth: bool | None,
    canonical_text: str,
    *,
    owned_prefix: str | None = None,
    owned_suffix: str | None = None,
    prefix_anchor: str | None = None,
    suffix_anchor: str | None = None,
) -> None:
    path = _state_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = _load_state(repo)

    created = created_by_codesleuth
    if created is None:
        prior_created = existing.get("createdByCodesleuth")
        created = prior_created if isinstance(prior_created, bool) else None

    prior_prefix = existing.get("ownedPrefix")
    prior_suffix = existing.get("ownedSuffix")
    prior_prefix_anchor = existing.get("prefixAnchorHash")
    prior_suffix_anchor = existing.get("suffixAnchorHash")
    prefix = owned_prefix if owned_prefix is not None else (prior_prefix if isinstance(prior_prefix, str) else "")
    suffix = owned_suffix if owned_suffix is not None else (prior_suffix if isinstance(prior_suffix, str) else "")
    prefix_hash = (
        prefix_anchor
        if prefix_anchor is not None
        else (prior_prefix_anchor if isinstance(prior_prefix_anchor, str) else "")
    )
    suffix_hash = (
        suffix_anchor
        if suffix_anchor is not None
        else (prior_suffix_anchor if isinstance(prior_suffix_anchor, str) else "")
    )

    payload = {
        "schemaVersion": 3,
        "createdByCodesleuth": created,
        "canonicalHash": _hash_canonical(canonical_text),
        "lastAppliedHash": _hash_canonical(canonical_text),
        "ownedPrefix": prefix,
        "ownedSuffix": suffix,
        "prefixAnchorHash": prefix_hash,
        "suffixAnchorHash": suffix_hash,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _state_created_by(repo: Path) -> bool | None:
    value = _load_state(repo).get("createdByCodesleuth")
    return value if isinstance(value, bool) else None


def _state_owned_boundaries(repo: Path) -> tuple[str, str, str, str]:
    state = _load_state(repo)
    prefix = state.get("ownedPrefix")
    suffix = state.get("ownedSuffix")
    prefix_anchor = state.get("prefixAnchorHash")
    suffix_anchor = state.get("suffixAnchorHash")
    return (
        prefix if isinstance(prefix, str) else "",
        suffix if isinstance(suffix, str) else "",
        prefix_anchor if isinstance(prefix_anchor, str) else "",
        suffix_anchor if isinstance(suffix_anchor, str) else "",
    )


def _clear_state(repo: Path) -> None:
    path = _state_path(repo)
    if path.is_file():
        path.unlink()
