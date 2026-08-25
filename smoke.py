#!/usr/bin/env python3
import json
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
oc = root / ".opencode"
required = [
    "agents/repo-reviewer.md", "agents/repo-scout.md", "agents/repo-documenter.md",
    "agents/repo-profile-architect.md", "agents/repo-prompt-advisor.md",
    "commands/repo-review.md", "commands/repo-docs.md", "commands/repo-review-resume.md",
    "commands/repo-profile.md", "commands/repo-prompts.md",
    "skills/repository-deep-review/SKILL.md", "tools/repo_inventory.ts",
    "tools/review_state.ts", "tools/repo_profile.ts", "plugins/review-compaction.ts",
    "profiles/builtin/generic.json", "profiles/builtin/rust.json", "profiles/builtin/python.json",
    "profiles/builtin/node.json", "profiles/builtin/typescript.json",
    "bin/opencode-review", "bin/opencode-review.ps1",
    "bin/review-pack", "bin/review-pack.ps1",
    "bin/review_pack_tui.py", "bin/codesleuth_tui.py", "bin/review_pack_tui_core.py", "bin/review_pack_tui_bootstrap.py",
    "bin/requirements-tui.txt",
    "bin/review-pack-update", "bin/review-pack-update.ps1", "bin/review-pack-update.py",
    "bin/review-pack-smoke.py", "themes/codesleuth.json", "tui.json",
    "opencode.json", "review-pack.json", "review-pack-user.json"
]
missing = [x for x in required if not (oc / x).is_file()]
if missing:
    raise SystemExit("missing: " + ", ".join(missing))

cfg = json.loads((oc / "opencode.json").read_text(encoding="utf-8"))
permission = cfg.get("permission", {})
if not isinstance(permission, dict):
    raise SystemExit("permission policy must be an object")
for key in ("websearch", "webfetch", "lsp", "question"):
    value = permission.get(key)
    if value not in ("allow", "ask", "deny"):
        raise SystemExit(f"permission {key} has invalid value: {value!r}")
if permission.get("websearch") == "deny" and permission.get("webfetch") == "deny":
    print("warning: both websearch and webfetch are denied by user policy")

skill = permission.get("skill")
if isinstance(skill, str):
    if skill == "deny":
        raise SystemExit("skill permission denies review-pack skill")
elif isinstance(skill, dict):
    if skill.get("repository-deep-review") == "deny":
        raise SystemExit("repository-deep-review skill is denied")
else:
    raise SystemExit("skill permission is missing or malformed")

bash = permission.get("bash")
if isinstance(bash, dict):
    for destructive in ("git push*", "git reset --hard*", "git clean*"):
        if bash.get(destructive) == "allow":
            print(f"warning: destructive shell rule is explicitly allowed: {destructive}")

meta = json.loads((oc / "review-pack.json").read_text(encoding="utf-8"))
if meta.get("schemaVersion") != 1:
    raise SystemExit("unsupported or missing review-pack metadata schemaVersion")
if not meta.get("version"):
    raise SystemExit("review-pack metadata has no version")
if not isinstance(meta.get("managedFiles"), dict) or not meta["managedFiles"]:
    raise SystemExit("review-pack metadata has no managedFiles hashes")
source = meta.get("source", {})
if source.get("remote") and not source.get("ref"):
    if source.get("commit"):
        print("warning: source is pinned by commit but has no branch/tag ref; floating self-update requires --source-ref or update from the pinned source checkout")
    else:
        raise SystemExit("review-pack source has a remote but neither ref nor commit")

settings = json.loads((oc / "review-pack-user.json").read_text(encoding="utf-8"))
if settings.get("schemaVersion") != 1:
    raise SystemExit("unsupported review-pack-user settings schema")
profiles = settings.get("profiles")
if not isinstance(profiles, list) or "generic" not in profiles:
    raise SystemExit("review-pack-user profiles must include generic")

managed_files = meta["managedFiles"]
if "tui.json" in managed_files:
    tui = json.loads((oc / "tui.json").read_text(encoding="utf-8"))
    if tui.get("$schema") != "https://opencode.ai/tui.json":
        raise SystemExit("CodeSleuth tui.json has an unexpected schema")
    if tui.get("theme") != "codesleuth":
        raise SystemExit("pack-managed tui.json must select the codesleuth theme")
else:
    print("warning: preserving user-owned .opencode/tui.json; CodeSleuth theme is not forced")

if "themes/codesleuth.json" in managed_files:
    theme = json.loads((oc / "themes" / "codesleuth.json").read_text(encoding="utf-8"))
    if theme.get("$schema") != "https://opencode.ai/theme.json" or not isinstance(theme.get("theme"), dict):
        raise SystemExit("CodeSleuth theme is missing or malformed")
    for required_color in ("primary", "background", "text", "success", "warning", "error", "diffAdded", "diffRemoved"):
        if required_color not in theme["theme"]:
            raise SystemExit(f"CodeSleuth theme is missing {required_color}")
else:
    print("warning: preserving user-owned codesleuth theme file; pack palette is not forced")

branding = (oc / "bin" / "codesleuth_tui.py").read_text(encoding="utf-8")
for marker in ("CodeSleuth", "Evidence Console", "Evidence-first repository intelligence", "CODESLEUTH_ART"):
    if marker not in branding:
        raise SystemExit(f"CodeSleuth TUI branding marker missing: {marker}")
for launcher_name in ("opencode-review", "opencode-review.ps1"):
    if "OPENCODE_TUI_CONFIG" not in (oc / "bin" / launcher_name).read_text(encoding="utf-8"):
        raise SystemExit(f"{launcher_name} does not activate the project-local CodeSleuth TUI config")

print("PACK SMOKE PASS")
print("product: CodeSleuth")
print("version:", meta["version"])
print("installation complete:", bool(meta.get("complete", False)))
print("profiles:", ", ".join(profiles))
print("theme: codesleuth")
print("Exa runtime:", "enabled" if settings.get("runtime", {}).get("exaEnabled", True) else "disabled")
print("CodeSleuth console: .opencode/bin/review-pack")
print("POSIX launcher: .opencode/bin/opencode-review")
print("PowerShell launcher: .opencode/bin/opencode-review.ps1")
print("update check: .opencode/bin/review-pack-update --check")
