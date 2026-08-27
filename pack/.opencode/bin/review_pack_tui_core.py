#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path
from typing import Any

from constants import (
    AGENT_PROFILE_OPTIONS as AGENT_PROFILE_OPTIONS
)
from constants import (
    AGENT_PROFILES,
    PERMISSION_VALUES,
    PROFILES,
    SETTINGS_SCHEMA,
)

SAFE_GIT_RULES = {
    "*": "ask",
    "git status*": "allow",
    "git diff*": "allow",
    "git log*": "allow",
    "git show*": "allow",
    "git rev-parse*": "allow",
    "git ls-files*": "allow",
    "git branch --show-current*": "allow",
    "git merge-base*": "allow",
    "git cat-file*": "allow",
    "git blame*": "allow",
    "git grep*": "allow",
    "git push*": "deny",
    "git reset --hard*": "deny",
    "git clean*": "deny",
}

BALANCED_GIT_RULES = {
    **SAFE_GIT_RULES,
    "cargo test*": "allow",
    "cargo check*": "allow",
    "cargo clippy*": "allow",
    "cargo fmt --check*": "allow",
    "pytest*": "allow",
    "python -m pytest*": "allow",
    "npm test*": "allow",
    "npm run test*": "allow",
    "npm run lint*": "allow",
    "npm run typecheck*": "allow",
    "pnpm test*": "allow",
    "pnpm lint*": "allow",
    "pnpm typecheck*": "allow",
    "yarn test*": "allow",
}

AUTONOMOUS_GIT_RULES = {
    "*": "allow",
    "git push*": "ask",
    "git reset --hard*": "ask",
    "git clean*": "ask",
}


def default_settings(profiles: list[str] | None = None) -> dict[str, Any]:
    """Return default CodeSleuth/OpenCode user settings."""
    return {
        "schemaVersion": SETTINGS_SCHEMA,
        "profiles": profiles or ["generic"],
        "profilesMode": "auto",
        "permissions": {
            "preset": "review-safe",
            "websearch": "ask",
            "webfetch": "ask",
            "externalDirectory": "ask",
            "edit": "ask",
            "question": "allow",
            "doomLoop": "ask",
            "managePolicy": True,
        },
        "runtime": {
            "exaEnabled": True,
            "watchdogEnabled": True,
            "stallSeconds": 480,
            "maxStallRecoveries": 2,
            "webStallSeconds": 180,
            "compactionReserved": 20000,
            "checkUpdatesOnStart": True,
        },
        "agent": {
            "profile": "native",
            "model": "",
        },
        "policy": {
            "enforceAgentsMdRules": False,
        },
    }


def _deep_merge(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def detect_profiles(repo: Path) -> list[str]:
    """Detect language profiles from tracked files in *repo*."""
    proc = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "-z"],
        capture_output=True,
        check=True,
    )
    files = [x for x in proc.stdout.decode("utf-8", "surrogateescape").split("\0") if x]
    names = set(files)
    profiles = ["generic"]
    if "Cargo.toml" in names or any(x.endswith(".rs") for x in files):
        profiles.append("rust")
    if any(x in names for x in ("pyproject.toml", "requirements.txt", "setup.py")) or any(x.endswith(".py") for x in files):
        profiles.append("python")
    if "package.json" in names:
        profiles.append("node")
    if any(Path(x).name.startswith("tsconfig") and x.endswith(".json") for x in files) or any(x.endswith((".ts", ".tsx")) for x in files):
        profiles.append("typescript")
    return profiles


def installation_state(repo: Path) -> str:
    """Describe whether CodeSleuth is installed in *target*."""
    oc = repo / ".opencode"
    if (oc / "review-pack.json").is_file():
        return "versioned"
    legacy_markers = (
        oc / "agents" / "repo-reviewer.md",
        oc / "commands" / "repo-review.md",
        oc / "skills" / "repository-deep-review" / "SKILL.md",
    )
    if sum(p.is_file() for p in legacy_markers) >= 2:
        return "legacy-pack"
    if oc.exists():
        return "existing-opencode"
    return "fresh"


def recommended_operation(repo: Path, distribution_available: bool) -> str:
    """Recommend install vs update from *state*."""
    state = installation_state(repo)
    if not distribution_available:
        return "configure" if state == "versioned" else "unavailable"
    if state == "versioned":
        return "update"
    if state == "legacy-pack":
        return "adopt"
    return "install"


def validate_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize a settings dict."""
    merged = _deep_merge(default_settings(settings.get("profiles") or ["generic"]), settings)
    profiles = list(dict.fromkeys(merged.get("profiles") or ["generic"]))
    if "generic" not in profiles:
        profiles.insert(0, "generic")
    unknown = [p for p in profiles if p not in PROFILES]
    if unknown:
        raise ValueError(f"unknown profiles: {', '.join(unknown)}")
    merged["profiles"] = profiles
    perms = merged["permissions"]
    if perms.get("preset") not in ("review-safe", "balanced", "autonomous"):
        raise ValueError("permission preset must be review-safe, balanced, or autonomous")
    for key in ("websearch", "webfetch", "externalDirectory", "edit", "question", "doomLoop"):
        if perms.get(key) not in PERMISSION_VALUES:
            raise ValueError(f"invalid permission value for {key}")
    runtime = merged["runtime"]
    for key, lo, hi in (
        ("stallSeconds", 60, 3600),
        ("webStallSeconds", 60, 1800),
        ("maxStallRecoveries", 0, 20),
        ("compactionReserved", 1000, 500000),
    ):
        try:
            value = int(runtime[key])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{key} must be an integer") from exc
        if not lo <= value <= hi:
            raise ValueError(f"{key} must be between {lo} and {hi}")
        runtime[key] = value
    agent = merged.get("agent")
    if not isinstance(agent, dict):
        agent = {}
        merged["agent"] = agent
    profile = agent.get("profile") or "native"
    if profile not in AGENT_PROFILES:
        raise ValueError("agent profile must be native, open-weight, codex, or claude")
    agent["profile"] = profile
    model = agent.get("model") or ""
    if not isinstance(model, str):
        raise ValueError("agent.model must be a string")
    agent["model"] = model.strip()
    policy = merged.get("policy")
    if not isinstance(policy, dict):
        policy = {}
        merged["policy"] = policy
    val = policy.get("enforceAgentsMdRules", False)
    if not isinstance(val, bool):
        raise ValueError("policy.enforceAgentsMdRules must be a boolean")
    policy["enforceAgentsMdRules"] = bool(val)
    return merged


def build_permission_policy(settings: dict[str, Any]) -> dict[str, Any]:
    """Build an OpenCode permission policy from settings."""
    settings = validate_settings(settings)
    perms = settings["permissions"]
    preset = perms["preset"]
    if preset == "review-safe":
        bash = copy.deepcopy(SAFE_GIT_RULES)
    elif preset == "balanced":
        bash = copy.deepcopy(BALANCED_GIT_RULES)
    else:
        bash = copy.deepcopy(AUTONOMOUS_GIT_RULES)

    read_policy = {
        "*": "allow",
        "*.env": "deny",
        "*.env.*": "deny",
        "*.env.example": "allow",
    }
    perm_edit = perms["edit"]
    if perm_edit == "deny":
        edit_policy: str | dict[str, str] = "deny"
    elif perm_edit == "allow":
        edit_policy = "allow"
    else:
        edit_policy = {"*": perm_edit, ".codesleuth/reports/**": "allow"}
    return {
        "read": read_policy,
        "edit": edit_policy,
        "bash": bash,
        "external_directory": perms["externalDirectory"],
        "websearch": perms["websearch"],
        "webfetch": perms["webfetch"],
        "lsp": "allow",
        "skill": {
            "*": "ask",
            "repository-deep-review": "allow",
            "codesleuth-reports": "allow",
        },
        "question": perms["question"],
        "doom_loop": perms["doomLoop"],
    }


def _set_keepalive(cfg: dict[str, Any], settings: dict[str, Any]) -> None:
    runtime = settings["runtime"]
    plugins = list(cfg.get("plugin") or [])
    kept = []
    found = False
    for entry in plugins:
        package = entry[0] if isinstance(entry, list) and entry else entry if isinstance(entry, str) else None
        if isinstance(package, str) and package.startswith("opencode-keepalive"):
            found = True
            if runtime["watchdogEnabled"]:
                options = entry[1] if isinstance(entry, list) and len(entry) > 1 and isinstance(entry[1], dict) else {}
                options = dict(options)
                options.update({
                    "stallMs": runtime["stallSeconds"] * 1000,
                    "maxStallRecoveries": runtime["maxStallRecoveries"],
                    "toolStallMsByTool": {
                        **dict(options.get("toolStallMsByTool") or {}),
                        "webfetch": runtime["webStallSeconds"] * 1000,
                        "websearch": runtime["webStallSeconds"] * 1000,
                    },
                })
                kept.append([package, options])
        else:
            kept.append(entry)
    if runtime["watchdogEnabled"] and not found:
        kept.append([
            "opencode-keepalive@0.1.0",
            {
                "intervalMs": 10000,
                "stallMs": runtime["stallSeconds"] * 1000,
                "childStallAction": "abort-resume-parent",
                "maxStallRecoveries": runtime["maxStallRecoveries"],
                "abortWaitMs": 30000,
                "toolStallMsByTool": {
                    "glob": 90000,
                    "grep": 90000,
                    "read": 120000,
                    "webfetch": runtime["webStallSeconds"] * 1000,
                    "websearch": runtime["webStallSeconds"] * 1000,
                },
                "bashQuickStallMs": 90000,
                "output": "file",
            },
        ])
    cfg["plugin"] = kept


def apply_agent_profile_to_config(cfg: dict[str, Any], settings: dict[str, Any]) -> None:
    """Bind an optional OpenCode model, or clear it when empty. Never write agent.prompt.

    OpenCode's primary `build` agent has no own prompt; the controller text is
    chosen by model via SystemPrompt.provider(). A custom `prompt` on `build`
    replaces that native controller entirely rather than appending to it.
    An empty settings model removes a previously set top-level ``model``.
    """
    agent = settings.get("agent") or {}
    model = str(agent.get("model") or "").strip()
    if model:
        cfg["model"] = model
    else:
        cfg.pop("model", None)


def apply_settings_to_config_dict(cfg: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    settings = validate_settings(settings)
    out = copy.deepcopy(cfg)
    if settings["permissions"].get("managePolicy", True):
        existing = out.get("permission")
        if not isinstance(existing, dict):
            existing = {}
        existing.update(build_permission_policy(settings))
        out["permission"] = existing
    out.setdefault("compaction", {})["reserved"] = settings["runtime"]["compactionReserved"]
    _set_keepalive(out, settings)
    apply_agent_profile_to_config(out, settings)
    return out


def settings_from_config(cfg: dict[str, Any], profiles: list[str]) -> dict[str, Any]:
    """Derive settings fields from an existing OpenCode config."""
    settings = default_settings(profiles)
    permission = cfg.get("permission")
    if isinstance(permission, dict):
        mapping = {
            "websearch": "websearch",
            "webfetch": "webfetch",
            "external_directory": "externalDirectory",
            "edit": "edit",
            "question": "question",
            "doom_loop": "doomLoop",
        }
        for source, target in mapping.items():
            value = permission.get(source)
            if source == "edit" and isinstance(value, dict):
                nested = value.get("*")
                if isinstance(nested, str) and nested in PERMISSION_VALUES:
                    settings["permissions"][target] = nested
                continue
            if isinstance(value, str) and value in PERMISSION_VALUES:
                settings["permissions"][target] = value
        settings["permissions"]["managePolicy"] = False
    compaction = cfg.get("compaction")
    if isinstance(compaction, dict) and isinstance(compaction.get("reserved"), int):
        settings["runtime"]["compactionReserved"] = compaction["reserved"]
    for entry in cfg.get("plugin") or []:
        if isinstance(entry, list) and entry and isinstance(entry[0], str) and entry[0].startswith("opencode-keepalive"):
            options = entry[1] if len(entry) > 1 and isinstance(entry[1], dict) else {}
            if isinstance(options.get("stallMs"), int):
                settings["runtime"]["stallSeconds"] = options["stallMs"] // 1000
            if isinstance(options.get("maxStallRecoveries"), int):
                settings["runtime"]["maxStallRecoveries"] = options["maxStallRecoveries"]
            break
    model = cfg.get("model")
    if isinstance(model, str) and model.strip():
        settings["agent"]["model"] = model.strip()
    return settings


def load_settings(repo: Path, profiles: list[str] | None = None) -> dict[str, Any]:
    """Load persisted review-pack user settings for *repo*."""
    path = repo / ".opencode" / "review-pack-user.json"
    if path.is_file():
        return validate_settings(json.loads(path.read_text(encoding="utf-8")))
    cfg_path = repo / ".opencode" / "opencode.json"
    if cfg_path.is_file():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            return validate_settings(settings_from_config(cfg, profiles or detect_profiles(repo)))
        except Exception:
            pass
    return validate_settings(default_settings(profiles or detect_profiles(repo)))


def save_settings(repo: Path, settings: dict[str, Any]) -> Path:
    """Persist validated settings beside the OpenCode install."""
    settings = validate_settings(settings)
    path = repo / ".opencode" / "review-pack-user.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    return path


def coerce_self_install_agents_policy(settings: dict[str, Any], *, is_self: bool) -> dict[str, Any]:
    """Self-install must not persist enforce=true; maintainer AGENTS.md is not a target policy file."""
    settings = validate_settings(settings)
    if is_self:
        settings.setdefault("policy", {})["enforceAgentsMdRules"] = False
    return validate_settings(settings)


def apply_settings_to_target(
    repo: Path,
    settings: dict[str, Any],
    *,
    source_root: Path | None = None,
) -> Path:
    """Apply settings onto the target OpenCode config on disk.

    The managed AGENTS.md policy mutation is preflighted and applied before
    persisting policy/config. On later failure, AGENTS.md and config are restored.
    """
    import codesleuth_project as project_lifecycle
    from codesleuth_project.agents_policy import apply_agents_md_policy

    is_self = project_lifecycle.is_self_target(repo, source_root=source_root)
    meta_path = repo / ".opencode" / "review-pack.json"
    if not is_self and meta_path.is_file():
        try:
            is_self = bool(json.loads(meta_path.read_text(encoding="utf-8")).get("selfInstall"))
        except json.JSONDecodeError:
            is_self = False
    settings = coerce_self_install_agents_policy(settings, is_self=is_self)
    oc = repo / ".opencode"
    cfg_path = oc / "opencode.json"
    if not cfg_path.is_file():
        raise FileNotFoundError(f"{cfg_path} does not exist")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    settings_path = oc / "review-pack-user.json"
    settings_backup = settings_path.read_bytes() if settings_path.is_file() else None
    agents_path = repo / "AGENTS.md"
    agents_backup = agents_path.read_bytes() if agents_path.is_file() else None
    backup_dir = oc / "state" / "tui-backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    (backup_dir / "opencode.json.before-tui").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    updated = apply_settings_to_config_dict(cfg, settings)

    def _restore() -> None:
        cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        if settings_backup is None:
            settings_path.unlink(missing_ok=True)
        else:
            settings_path.write_bytes(settings_backup)
        if agents_backup is None:
            agents_path.unlink(missing_ok=True)
        else:
            agents_path.write_bytes(agents_backup)

    try:
        if not is_self:
            apply_agents_md_policy(repo, enforce=bool(settings["policy"]["enforceAgentsMdRules"]))
        cfg_path.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
        save_settings(repo, settings)
        detected = oc / "profiles" / "detected.json"
        detected.parent.mkdir(parents=True, exist_ok=True)
        detected.write_text(json.dumps({
            "profiles": settings["profiles"],
            "detectedFromTrackedFiles": settings.get("profilesMode") == "auto",
            "exaLaunchDefault": "OPENCODE_ENABLE_EXA=1" if settings["runtime"]["exaEnabled"] else "disabled by review-pack-user.json",
        }, indent=2) + "\n", encoding="utf-8")
        project_lifecycle.ensure_reports_workspace(repo)
        project_lifecycle.ensure_agents_reports_pointer(repo)
    except Exception:
        _restore()
        raise
    return cfg_path


def settings_summary(settings: dict[str, Any]) -> str:
    """Return a short human-readable settings summary."""
    settings = validate_settings(settings)
    p = settings["permissions"]
    r = settings["runtime"]
    agent = settings["agent"]
    policy = settings.get("policy", {})
    model = agent["model"] or "OpenCode current model"
    return "\n".join([
        f"Profiles: {', '.join(settings['profiles'])} ({settings['profilesMode']})",
        f"Agent profile: {agent['profile']} ({model}); controller: OpenCode native build prompt",
        "Reports: .codesleuth/reports/ (OpenCode build writes; other assistants read INDEX.md)",
        f"Permission preset: {p['preset']}",
        f"Web: search={p['websearch']}, fetch={p['webfetch']}; external dirs={p['externalDirectory']}; edit={p['edit']}",
        f"Exa: {'enabled' if r['exaEnabled'] else 'disabled'}; watchdog: {'enabled' if r['watchdogEnabled'] else 'disabled'}",
        f"Watchdog: stall={r['stallSeconds']}s, web={r['webStallSeconds']}s, recoveries={r['maxStallRecoveries']}",
        f"Compaction reserved tokens: {r['compactionReserved']}",
        f"Check updates when TUI opens: {'yes' if r['checkUpdatesOnStart'] else 'no'}",
        f"Agents policy: {'enforced' if policy.get('enforceAgentsMdRules') else 'off'} — Maintain CodeSleuth workflow rules in root AGENTS.md",
    ])


def config_preview(settings: dict[str, Any]) -> str:
    """Return a JSON preview of settings applied to *cfg*."""
    settings = validate_settings(settings)
    preview = {
        "permission": build_permission_policy(settings),
        "compaction": {"reserved": settings["runtime"]["compactionReserved"]},
        "exa": {"OPENCODE_ENABLE_EXA": "1" if settings["runtime"]["exaEnabled"] else "unset"},
        "watchdogEnabled": settings["runtime"]["watchdogEnabled"],
        "agent": {
            "profile": settings["agent"]["profile"],
            "model": settings["agent"]["model"] or None,
            "controller": "OpenCode primary build; prompt left unset",
        },
        "policy": {
            "enforceAgentsMdRules": bool(settings.get("policy", {}).get("enforceAgentsMdRules", False)),
        },
    }
    return json.dumps(preview, indent=2)


def generate_prompts(repo: Path, profiles: list[str]) -> list[tuple[str, str]]:
    """Generate profile prompt texts for the selected profiles."""
    prompts: list[tuple[str, str]] = [
        (
            "Repository architecture + correctness",
            "/repo-review map the repository architecture, identify authority boundaries and invariants, then perform an in-depth correctness review. Inspect callers, callees, tests, CI, migrations and documentation, not only obvious entrypoints. Record exact evidence for every material finding.",
        ),
        (
            "Current branch acceptance",
            "/repo-review compare current HEAD and worktree against the repository's canonical base branch. Review changed code and unchanged consumers/contracts/tests/CI. Distinguish blockers from improvements and state all unreviewed areas.",
        ),
        (
            "Documentation truth pass",
            "/repo-docs build an evidence-first repository guide from current source, manifests, CI and tests. Separate documented guarantees from behavior inferred from code and call out stale or contradictory documentation.",
        ),
        (
            "Persist an assistant-readable report",
            "/repo-report write a CodeSleuth analytical report for the current HEAD and active review into .codesleuth/reports/, update INDEX.md, and keep application source unchanged.",
        ),
        (
            "External assumptions verification",
            "/repo-review identify version-sensitive external API, framework and tooling assumptions in this repository. Use websearch only for discovery and webfetch primary official sources for verification. Do not claim web verification without successful tool calls.",
        ),
    ]
    if "rust" in profiles:
        prompts.append((
            "Rust safety + concurrency",
            "/repo-review focus on Rust ownership boundaries, error propagation, async cancellation, Send/Sync assumptions, lock ordering, blocking work in async contexts, idempotency and persistence correctness. Run only repository-authorized checks and report exactly which checks executed.",
        ))
    if "typescript" in profiles:
        prompts.append((
            "TypeScript contract review",
            "/repo-review focus on TypeScript static-vs-runtime validation, unsafe casts/any, discriminated-union exhaustiveness, ESM/CJS and moduleResolution, generated schema/type drift, async cleanup and frontend/backend contract compatibility.",
        ))
    if "python" in profiles:
        prompts.append((
            "Python runtime review",
            "/repo-review focus on Python runtime validation, typing/runtime mismatches, exception boundaries, resource cleanup, subprocess/network timeouts, async cancellation, packaging metadata and test isolation.",
        ))
    if "node" in profiles:
        prompts.append((
            "Node dependency + lifecycle review",
            "/repo-review inspect Node package scripts, lockfile/runtime assumptions, lifecycle hooks, async resource cleanup, dependency boundaries, build/test parity and server/client contract drift.",
        ))
    return prompts[:8]


def write_prompts(repo: Path, prompts: list[tuple[str, str]]) -> Path:
    """Write generated profile prompts into *target*."""
    out = repo / ".opencode" / "state" / "tui" / "suggested-prompts.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    body = ["# Suggested CodeSleuth prompts", ""]
    for i, (title, prompt) in enumerate(prompts, 1):
        body.extend([f"## {i}. {title}", "", prompt, ""])
    out.write_text("\n".join(body), encoding="utf-8")
    return out
