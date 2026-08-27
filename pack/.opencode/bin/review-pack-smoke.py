#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
oc = root / ".opencode"
required = [
    "agents/repo-reviewer.md", "agents/repo-scout.md", "agents/repo-documenter.md",
    "agents/repo-profile-architect.md", "agents/repo-prompt-advisor.md",
    "commands/repo-review.md", "commands/repo-docs.md", "commands/repo-review-resume.md",
    "commands/repo-profile.md", "commands/repo-prompts.md", "commands/repo-report.md",
    "commands/repo-map.md", "commands/repo-contracts.md", "commands/eha-test.md", "commands/eha-status.md",
    "commands/eha-repair.md", "commands/playbook.md",
    "skills/repository-deep-review/SKILL.md", "skills/codesleuth-reports/SKILL.md",
    "skills/protected-capability-registry/SKILL.md", "skills/eha-campaign-evidence/SKILL.md",
    "playbooks/repository-map/playbook.json", "playbooks/protected-capability-assessment/playbook.json",
    "playbooks/eha-sib-acceptance/playbook.json",
    "tools/repo_inventory.ts",
    "tools/review_state.ts", "tools/eha_state.ts", "tools/repo_profile.ts", "tools/repo_context_graph.ts",
    "tools/protected_capability_graph.ts", "plugins/review-compaction.ts",
    "profiles/builtin/generic.json", "profiles/builtin/rust.json", "profiles/builtin/python.json",
    "profiles/builtin/node.json", "profiles/builtin/typescript.json",
    "bin/opencode-review", "bin/opencode-review.ps1",
    "bin/review-pack", "bin/review-pack.ps1",
    "bin/review_pack_tui.py", "bin/codesleuth_tui.py", "bin/review_pack_tui_core.py", "bin/review_pack_tui_bootstrap.py",
    "bin/playbook_catalog.py",
    "bin/codesleuth_version.py", "bin/codesleuth_naming.py", "bin/requirements-tui.txt",
    "bin/review-pack-update", "bin/review-pack-update.ps1", "bin/review-pack-update.py",
    "bin/review-pack-smoke.py", "themes/codesleuth.json", "tui.json",
    "opencode.json", "review-pack.json", "review-pack-user.json", "codesleuth-naming.json",
    "CODESLEUTH-REPORTS.md",
    "policy/agents-rules.md",
]
missing = [x for x in required if not (oc / x).is_file()]
if missing:
    raise SystemExit("missing: " + ", ".join(missing))

sys.path.insert(0, str(oc / "bin"))
from codesleuth_version import installed_version  # noqa: E402

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
        raise SystemExit("skill permission denies the CodeSleuth repository review skill")
elif isinstance(skill, dict):
    if skill.get("repository-deep-review") == "deny":
        raise SystemExit("repository-deep-review skill is denied")
    if skill.get("codesleuth-reports") == "deny":
        print("warning: codesleuth-reports skill is denied; analytical reports may not be written")
else:
    raise SystemExit("skill permission is missing or malformed")

bash = permission.get("bash")
if isinstance(bash, dict):
    for destructive in ("git push*", "git reset --hard*", "git clean*"):
        if bash.get(destructive) == "allow":
            print(f"warning: destructive shell rule is explicitly allowed: {destructive}")

meta = json.loads((oc / "review-pack.json").read_text(encoding="utf-8"))
if meta.get("schemaVersion") not in (1, 2):
    raise SystemExit("unsupported or missing CodeSleuth metadata schemaVersion")
version = installed_version(root)
if not isinstance(meta.get("managedFiles"), dict) or not meta["managedFiles"]:
    raise SystemExit("CodeSleuth metadata has no managedFiles hashes")
source = meta.get("source", {})
if source.get("remote") and not source.get("ref"):
    if source.get("commit"):
        print("warning: source is pinned by commit but has no branch/tag ref; floating self-update requires --source-ref or update from the pinned source checkout")
    else:
        raise SystemExit("CodeSleuth source has a remote but neither ref nor commit")

settings = json.loads((oc / "review-pack-user.json").read_text(encoding="utf-8"))
if settings.get("schemaVersion") != 1:
    raise SystemExit("unsupported CodeSleuth project-settings schema")
profiles = settings.get("profiles")
if not isinstance(profiles, list) or "generic" not in profiles:
    raise SystemExit("CodeSleuth project profiles must include generic")

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
for marker in ("CodeSleuth", "DOC_TAGLINE", "Evidence-first repository intelligence", "CODESLEUTH_ART", "activity-panel"):
    if marker not in branding:
        raise SystemExit(f"CodeSleuth TUI identity marker missing: {marker}")
if 'id="brand"' in branding or "right-close" in branding:
    raise SystemExit("CodeSleuth TUI unexpectedly still renders brand chrome or session-close X")
for launcher_name in ("opencode-review", "opencode-review.ps1"):
    if "OPENCODE_TUI_CONFIG" not in (oc / "bin" / launcher_name).read_text(encoding="utf-8"):
        raise SystemExit(f"{launcher_name} does not activate the project-local CodeSleuth TUI config")


def _frontmatter_field(path: Path, key: str) -> str | None:
    text = path.read_text(encoding="utf-8")
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")
    if not text.lstrip().startswith("---"):
        return None
    match = re.search(r"^[ \t]*---[ \t]*\r?\n(.*?)\r?\n[ \t]*---[ \t]*\r?\n", text, re.S | re.M)
    if match:
        inner = match.group(1)
    else:
        parts = text.split("---", 2)
        if len(parts) < 3:
            return None
        inner = parts[1]
    pat = re.compile(rf"^\s*{re.escape(key)}\s*:\s*(.*?)\s*$")
    for line in inner.splitlines():
        m = pat.match(line)
        if m:
            return m.group(1).strip()
    return None


for name in ("repo-review.md", "repo-docs.md", "repo-review-resume.md", "repo-profile.md", "repo-prompts.md", "repo-report.md"):
    agent = _frontmatter_field(oc / "commands" / name, "agent")
    if agent != "build":
        raise SystemExit(f"command {name} must run on OpenCode primary agent build, not {agent!r}")
for name in ("repo-reviewer.md", "repo-documenter.md", "repo-profile-architect.md", "repo-prompt-advisor.md", "repo-scout.md"):
    mode = _frontmatter_field(oc / "agents" / name, "mode")
    if mode != "subagent":
        raise SystemExit(f"agent {name} must be a Task subagent, not {mode!r}")
agent_cfg = cfg.get("agent")
if isinstance(agent_cfg, dict):
    build = agent_cfg.get("build")
    if isinstance(build, dict) and str(build.get("prompt") or "").strip():
        print("warning: agent.build.prompt is set; this replaces OpenCode's native provider controller")
if not (root / ".codesleuth" / "reports" / "README.md").is_file():
    raise SystemExit("missing .codesleuth/reports/README.md; report workspace was not seeded")
if "CodeSleuth reports" not in (root / "AGENTS.md").read_text(encoding="utf-8"):
    raise SystemExit("AGENTS.md is missing the CodeSleuth reports discovery pointer")

# Agents policy block Verify – only when enforcement is enabled on a non-self install
enforce = bool(settings.get("policy", {}).get("enforceAgentsMdRules", False))
if bool(meta.get("selfInstall")):
    if enforce:
        print(
            "warning: policy.enforceAgentsMdRules is ignored for CodeSleuth self-install",
            file=sys.stderr,
        )
    enforce = False
agents_path = root / "AGENTS.md"
BEGIN = "<!-- CODESLEUTH:AGENTS-RULES:BEGIN -->"
END = "<!-- CODESLEUTH:AGENTS-RULES:END -->"
if enforce:
    canonical = oc / "policy" / "agents-rules.md"
    if not canonical.is_file():
        raise SystemExit("enforced AGENTS.md policy: missing canonical policy asset .opencode/policy/agents-rules.md")
    canon_text = canonical.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").strip() + "\n"
    if not agents_path.is_file():
        raise SystemExit("enforced AGENTS.md policy: AGENTS.md missing managed block")
    text = agents_path.read_text(encoding="utf-8")
    begins = text.count(BEGIN)
    ends = text.count(END)
    if begins != 1 or ends != 1:
        raise SystemExit(f"enforced AGENTS.md policy: expected exactly one managed block, found BEGIN={begins} END={ends}")
    b = text.find(BEGIN)
    e = text.find(END)
    if e < b:
        raise SystemExit("enforced AGENTS.md policy: malformed block BEGIN without END")
    inner = text[b + len(BEGIN): e].replace("\r\n", "\n").replace("\r", "\n").strip() + "\n"
    if inner != canon_text:
        raise SystemExit("enforced AGENTS.md policy: managed block does not match canonical .opencode/policy/agents-rules.md")
else:
    # When not enforced, do not require the block, but fail closed if malformed duplicate would be destructive
    if agents_path.is_file():
        _t = agents_path.read_text(encoding="utf-8")
        if _t.count(BEGIN) > 1 or _t.count(END) > 1:
            print("warning: AGENTS.md contains duplicate CodeSleuth policy markers while enforcement is off", file=sys.stderr)

print("PACK SMOKE PASS")
print("product: CodeSleuth")
print("version:", version)
print("installation complete:", bool(meta.get("complete", False)))
print("profiles:", ", ".join(profiles))
print("theme: codesleuth")
print("Exa runtime:", "enabled" if settings.get("runtime", {}).get("exaEnabled", True) else "disabled")
print("CodeSleuth console: .opencode/bin/codesleuth")
print("POSIX launcher: .opencode/bin/opencode-review")
print("PowerShell launcher: .opencode/bin/opencode-review.ps1")
print("floating update check (compatibility command): .opencode/bin/review-pack-update --check")
