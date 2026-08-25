#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RENAMES = {
    "pack/.opencode/bin/review-pack-update": "pack/.opencode/bin/codesleuth-update",
    "pack/.opencode/bin/review-pack-update.ps1": "pack/.opencode/bin/codesleuth-update.ps1",
    "pack/.opencode/bin/review-pack-update.py": "pack/.opencode/bin/codesleuth_update.py",
    "pack/.opencode/bin/review-pack-smoke.py": "pack/.opencode/bin/codesleuth-verify.py",
    "pack/.opencode/bin/review_pack_tui.py": "pack/.opencode/bin/codesleuth_tui_base.py",
    "pack/.opencode/bin/review_pack_tui_core.py": "pack/.opencode/bin/codesleuth_tui_core.py",
    "pack/.opencode/bin/review_pack_tui_bootstrap.py": "pack/.opencode/bin/codesleuth_tui_bootstrap.py",
}
DELETE = [
    "review-pack",
    "review-pack.ps1",
    "pack/.opencode/bin/review-pack",
    "pack/.opencode/bin/review-pack.ps1",
]
SKIP_EXACT = {
    "pack/.opencode/codesleuth-naming.json",
    "docs/CODESLEUTH-NAMING-CUTOVER.md",
    ".github/naming_cutover_apply.py",
    ".github/workflows/naming-cutover-worker.yml",
}

REPLACEMENTS = [
    ("review-pack-smoke.py", "codesleuth-verify.py"),
    ("review-pack-update.ps1", "codesleuth-update.ps1"),
    ("review-pack-update.py", "codesleuth_update.py"),
    ("review-pack-update", "codesleuth-update"),
    ("review_pack_tui_bootstrap.py", "codesleuth_tui_bootstrap.py"),
    ("review_pack_tui_bootstrap", "codesleuth_tui_bootstrap"),
    ("review_pack_tui_core.py", "codesleuth_tui_core.py"),
    ("review_pack_tui_core", "codesleuth_tui_core"),
    ("review_pack_tui.py", "codesleuth_tui_base.py"),
    ("review_pack_tui", "codesleuth_tui_base"),
    ("review-pack-user.json", "codesleuth-user.json"),
    ("review-pack.json", "codesleuth.json"),
    ("REVIEW_PACK_DISTRIBUTION_ROOT", "CODESLEUTH_DISTRIBUTION_ROOT"),
    ("REVIEW_PACK_TARGET_ROOT", "CODESLEUTH_TARGET_ROOT"),
    ("--adopt-existing-pack", "--adopt-existing-codesleuth"),
    ("--force-pack-files", "--force-codesleuth-files"),
    ("opencode-review-pack-update-", "codesleuth-update-"),
    ("REVIEW PACK UPDATE APPLIED", "CODESLEUTH UPDATE APPLIED"),
    ("REVIEW PACK UPDATE AVAILABLE", "CODESLEUTH UPDATE AVAILABLE"),
    ("REVIEW PACK CURRENT", "CODESLEUTH CURRENT"),
    ("PACK SMOKE PASS", "CODESLEUTH VERIFY PASS"),
    ("ReviewPackApp", "CodeSleuthBaseApp"),
    ("review-pack updater requires Python 3", "CodeSleuth updater requires Python 3"),
]


def text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in SKIP_EXACT or rel.startswith("docs/archive/"):
            continue
        try:
            path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        yield path


def replace_text() -> None:
    for path in text_files():
        text = path.read_text(encoding="utf-8")
        original = text
        for old, new in REPLACEMENTS:
            text = text.replace(old, new)
        # These exact product spellings are retired outside explicit migration evidence.
        text = text.replace("review-pack", "codesleuth")
        text = text.replace("review_pack", "codesleuth")
        text = text.replace("REVIEW_PACK", "CODESLEUTH")
        if text != original:
            path.write_text(text, encoding="utf-8")


def add_loader() -> None:
    path = ROOT / "pack/.opencode/bin/codesleuth_naming.py"
    path.write_text(
        '''#!/usr/bin/env python3\nfrom __future__ import annotations\n\nimport json\nfrom pathlib import Path\nfrom typing import Any\n\nMANIFEST_PATH = Path(__file__).resolve().parent.parent / "codesleuth-naming.json"\n\n\ndef load_naming(path: Path | None = None) -> dict[str, Any]:\n    manifest = path or MANIFEST_PATH\n    data = json.loads(manifest.read_text(encoding="utf-8"))\n    if data.get("schemaVersion") != 1:\n        raise RuntimeError("unsupported CodeSleuth naming schema")\n    for section in ("product", "canonical", "legacy", "migration"):\n        if not isinstance(data.get(section), dict):\n            raise RuntimeError(f"missing CodeSleuth naming section: {section}")\n    return data\n''',
        encoding="utf-8",
    )


def patch_installer() -> None:
    path = ROOT / "install.py"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        'META_NAME = "codesleuth.json"\nSETTINGS_NAME = "codesleuth-user.json"\nsys.path.insert(0, str(PACK / "bin"))\nimport codesleuth_project as project_lifecycle  # noqa: E402\nimport codesleuth_tui_core as tui_core  # noqa: E402\n',
        'sys.path.insert(0, str(PACK / "bin"))\nfrom codesleuth_naming import load_naming  # noqa: E402\nimport codesleuth_project as project_lifecycle  # noqa: E402\nimport codesleuth_tui_core as tui_core  # noqa: E402\n\nNAMING = load_naming(PACK / "codesleuth-naming.json")\nCANONICAL = NAMING["canonical"]\nLEGACY = NAMING["legacy"]\nMETA_NAME = CANONICAL["state"]["metadata"]\nSETTINGS_NAME = CANONICAL["state"]["settings"]\nLEGACY_META_NAME = LEGACY["state"]["metadata"]\nLEGACY_SETTINGS_NAME = LEGACY["state"]["settings"]\n',
    )
    helper = r'''

def _atomic_write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def _read_state_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid CodeSleuth persistent state at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"invalid CodeSleuth persistent state at {path}: expected a JSON object")
    return value


def _resolve_named_state(target: Path, canonical_name: str, legacy_name: str) -> tuple[dict | None, bool]:
    canonical = target / canonical_name
    legacy = target / legacy_name
    canonical_exists = canonical.is_file()
    legacy_exists = legacy.is_file()
    if not canonical_exists and not legacy_exists:
        return None, False
    canonical_value = _read_state_json(canonical) if canonical_exists else None
    legacy_value = _read_state_json(legacy) if legacy_exists else None
    if canonical_exists and legacy_exists:
        if canonical_value != legacy_value:
            raise RuntimeError(
                f"conflicting CodeSleuth persistent state: {canonical} and {legacy} differ; refusing to guess authority"
            )
        legacy.unlink()
        return canonical_value, True
    if canonical_exists:
        return canonical_value, False
    assert legacy_value is not None
    _atomic_write_json(canonical, legacy_value)
    legacy.unlink()
    return legacy_value, True


def _materialize_legacy_update_bridges(target: Path) -> None:
    bin_dir = target / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    bridges = set(NAMING["migration"]["bridgeEntrypoints"])
    legacy_env = LEGACY["environment"]
    canonical_env = CANONICAL["environment"]
    legacy_verify = LEGACY["entrypoints"]["verify"]
    legacy_bootstrap = LEGACY["python"]["tuiBootstrap"]
    if legacy_verify in bridges:
        verify = target / legacy_verify
        verify.write_text(
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "from pathlib import Path\n"
            "here = Path(__file__).resolve().parent\n"
            f"os.execv(sys.executable, [sys.executable, str(here / {CANONICAL['entrypoints']['verify'].split('/')[-1]!r}), *sys.argv[1:]])\n",
            encoding="utf-8",
        )
        verify.chmod(0o755)
    if legacy_bootstrap in bridges:
        bootstrap = target / legacy_bootstrap
        bootstrap.write_text(
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "from pathlib import Path\n"
            f"old_target = {legacy_env['targetRoot']!r}\n"
            f"new_target = {canonical_env['targetRoot']!r}\n"
            f"old_distribution = {legacy_env['distributionRoot']!r}\n"
            f"new_distribution = {canonical_env['distributionRoot']!r}\n"
            "if old_target in os.environ and new_target not in os.environ:\n    os.environ[new_target] = os.environ[old_target]\n"
            "if old_distribution in os.environ and new_distribution not in os.environ:\n    os.environ[new_distribution] = os.environ[old_distribution]\n"
            "here = Path(__file__).resolve().parent\n"
            f"os.execv(sys.executable, [sys.executable, str(here / {CANONICAL['python']['tuiBootstrap'].split('/')[-1]!r}), *sys.argv[1:]])\n",
            encoding="utf-8",
        )
        bootstrap.chmod(0o755)
'''
    if "import os\n" not in text:
        text = text.replace("import json\n", "import json\nimport os\n")
    text = text.replace("\ndef parse_args():\n", helper + "\n\ndef parse_args():\n")
    text = text.replace(
        '    parser.add_argument("--force-codesleuth-files", action="store_true", help="overwrite CodeSleuth-owned files, including locally modified ones")\n',
        '    parser.add_argument("--force-codesleuth-files", dest="force_managed_files", action="store_true", help="overwrite CodeSleuth-owned files, including locally modified ones")\n'
        '    parser.add_argument(LEGACY["cliOptions"]["forceManagedFiles"], dest="force_managed_files", action="store_true", help=argparse.SUPPRESS)\n',
    )
    text = text.replace(
        '    parser.add_argument("--adopt-existing-codesleuth", action="store_true", help="adopt an older unversioned installation with backups")\n',
        '    parser.add_argument("--adopt-existing-codesleuth", dest="adopt_existing", action="store_true", help="adopt an older unversioned CodeSleuth installation with backups")\n'
        '    parser.add_argument(LEGACY["cliOptions"]["adoptExisting"], dest="adopt_existing", action="store_true", help=argparse.SUPPRESS)\n',
    )
    text = text.replace("args.adopt_existing_codesleuth", "args.adopt_existing")
    text = text.replace("args.force_codesleuth_files", "args.force_managed_files")
    text = text.replace(
        '    meta_path = target / META_NAME\n    old_meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else None\n',
        '    meta_path = target / META_NAME\n'
        '    legacy_runtime = (target / LEGACY_META_NAME).is_file() or (target / LEGACY_SETTINGS_NAME).is_file()\n'
        '    try:\n'
        '        old_meta, migrated_meta = _resolve_named_state(target, META_NAME, LEGACY_META_NAME)\n'
        '        _, migrated_settings = _resolve_named_state(target, SETTINGS_NAME, LEGACY_SETTINGS_NAME)\n'
        '    except RuntimeError as exc:\n'
        '        raise SystemExit(str(exc)) from exc\n'
        '    legacy_runtime = legacy_runtime or migrated_meta or migrated_settings\n',
    )
    text = text.replace(
        '        raise SystemExit("cannot --update: .opencode/codesleuth.json is missing; use --adopt-existing-codesleuth for an older installation")',
        '        raise SystemExit("cannot --update: .opencode/codesleuth.json is missing; use --adopt-existing-codesleuth for an older unversioned installation")',
    )
    text = text.replace(
        '    managed, conflicts = install_files(target, old_meta, args.update, args.force_managed_files, args.adopt_existing)\n',
        '    managed, conflicts = install_files(target, old_meta, args.update, args.force_managed_files, args.adopt_existing)\n'
        '    if args.update and legacy_runtime:\n'
        '        _materialize_legacy_update_bridges(target)\n',
    )
    text = text.replace(
        '    print("smoke: python3 .opencode/bin/codesleuth-verify.py . (compatibility filename)")',
        '    print("verify: python3 .opencode/bin/codesleuth-verify.py .")',
    )
    path.write_text(text, encoding="utf-8")


def patch_lifecycle() -> None:
    path = ROOT / "pack/.opencode/bin/codesleuth_project.py"
    text = path.read_text(encoding="utf-8")
    marker = "from typing import Any\n"
    insert = '''from typing import Any\n\nfrom codesleuth_naming import load_naming\n\nNAMING = load_naming()\nMETA_NAME = NAMING["canonical"]["state"]["metadata"]\nSETTINGS_NAME = NAMING["canonical"]["state"]["settings"]\nLEGACY_META_NAME = NAMING["legacy"]["state"]["metadata"]\nLEGACY_SETTINGS_NAME = NAMING["legacy"]["state"]["settings"]\n'''
    text = text.replace(marker, insert)
    text = text.replace('(repo / ".opencode" / "codesleuth.json").is_file()', '((repo / ".opencode" / META_NAME).is_file() or (repo / ".opencode" / LEGACY_META_NAME).is_file())')
    text = text.replace('runtime = (repo / ".opencode" / "codesleuth.json").is_file()', 'runtime = (repo / ".opencode" / META_NAME).is_file() or (repo / ".opencode" / LEGACY_META_NAME).is_file()')
    text = text.replace('repo / ".opencode" / "codesleuth.json",\n        repo / ".opencode" / "codesleuth-user.json",', 'repo / ".opencode" / META_NAME,\n        repo / ".opencode" / SETTINGS_NAME,\n        repo / ".opencode" / LEGACY_META_NAME,\n        repo / ".opencode" / LEGACY_SETTINGS_NAME,')
    text = text.replace('remove_rel.update({"codesleuth.json", "codesleuth-user.json", "profiles/detected.json"})', 'remove_rel.update({META_NAME, SETTINGS_NAME, LEGACY_META_NAME, LEGACY_SETTINGS_NAME, "profiles/detected.json"})')
    text = text.replace('meta_path = repo / ".opencode" / "codesleuth.json"\n    metadata = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else None', 'meta_path = repo / ".opencode" / META_NAME\n    legacy_meta_path = repo / ".opencode" / LEGACY_META_NAME\n    active_meta_path = meta_path if meta_path.is_file() else legacy_meta_path\n    metadata = json.loads(active_meta_path.read_text(encoding="utf-8")) if active_meta_path.is_file() else None')
    text = text.replace('meta = repo / ".opencode" / "codesleuth.json"\n    if not meta.is_file():\n        return None', 'meta = repo / ".opencode" / META_NAME\n    if not meta.is_file():\n        meta = repo / ".opencode" / LEGACY_META_NAME\n    if not meta.is_file():\n        return None')
    path.write_text(text, encoding="utf-8")


def patch_tui_core() -> None:
    path = ROOT / "pack/.opencode/bin/codesleuth_tui_core.py"
    text = path.read_text(encoding="utf-8")
    anchor = "from constants import (\n    AGENT_PROFILES,\n    PERMISSION_VALUES,\n    PROFILES,\n    SETTINGS_SCHEMA,\n)\n"
    addition = anchor + '\nfrom codesleuth_naming import load_naming\n\nNAMING = load_naming()\nMETA_NAME = NAMING["canonical"]["state"]["metadata"]\nSETTINGS_NAME = NAMING["canonical"]["state"]["settings"]\nLEGACY_META_NAME = NAMING["legacy"]["state"]["metadata"]\n'
    text = text.replace(anchor, addition)
    text = text.replace('    if (oc / "codesleuth.json").is_file():\n        return "versioned"\n', '    if (oc / META_NAME).is_file():\n        return "versioned"\n    if (oc / LEGACY_META_NAME).is_file():\n        return "legacy-pack"\n')
    text = text.replace('repo / ".opencode" / "codesleuth-user.json"', 'repo / ".opencode" / SETTINGS_NAME')
    text = text.replace('disabled by codesleuth-user.json', 'disabled by canonical CodeSleuth settings')
    path.write_text(text, encoding="utf-8")


def patch_updater() -> None:
    path = ROOT / "pack/.opencode/bin/codesleuth_update.py"
    text = path.read_text(encoding="utf-8")
    insert = '''from codesleuth_naming import load_naming\n\nNAMING = load_naming()\nCANONICAL = NAMING["canonical"]\nMETA_NAME = CANONICAL["state"]["metadata"]\nENV_TARGET_ROOT = CANONICAL["environment"]["targetRoot"]\nSTATUS = CANONICAL["statusMessages"]\nRESTART_MARKER = Path(".opencode") / "state" / "tui-restart-request.json"\nAPPLIED_MESSAGE = STATUS["updateApplied"]\n'''
    text = re.sub(r'META_NAME = "codesleuth\.json"\nRESTART_MARKER = Path\("\.opencode"\) / "state" / "tui-restart-request\.json"\nAPPLIED_MESSAGE = "CODESLEUTH UPDATE APPLIED"\n', insert, text, count=1)
    text = text.replace('os.environ["CODESLEUTH_TARGET_ROOT"] = str(repo)', 'os.environ[ENV_TARGET_ROOT] = str(repo)')
    text = text.replace('print("CODESLEUTH CURRENT")', 'print(STATUS["current"])')
    text = text.replace('print("CODESLEUTH UPDATE AVAILABLE")', 'print(STATUS["updateAvailable"])')
    text = text.replace('prefix="codesleuth-update-"', 'prefix=CANONICAL["temporaryPrefix"]')
    path.write_text(text, encoding="utf-8")


def patch_bootstrap() -> None:
    path = ROOT / "pack/.opencode/bin/codesleuth_tui_bootstrap.py"
    text = path.read_text(encoding="utf-8")
    anchor = 'from pathlib import Path\n\nTEXTUAL_VERSION = "8.2.8"\n'
    replacement = 'from pathlib import Path\n\nfrom codesleuth_naming import load_naming\n\nNAMING = load_naming()\nENV_DISTRIBUTION_ROOT = NAMING["canonical"]["environment"]["distributionRoot"]\nENV_TARGET_ROOT = NAMING["canonical"]["environment"]["targetRoot"]\n\nTEXTUAL_VERSION = "8.2.8"\n'
    text = text.replace(anchor, replacement)
    text = text.replace('os.environ.get("CODESLEUTH_DISTRIBUTION_ROOT")', 'os.environ.get(ENV_DISTRIBUTION_ROOT)')
    text = text.replace('os.environ.get("CODESLEUTH_TARGET_ROOT", HERE.parents[2])', 'os.environ.get(ENV_TARGET_ROOT, HERE.parents[2])')
    text = text.replace('os.environ.get("CODESLEUTH_TARGET_ROOT")', 'os.environ.get(ENV_TARGET_ROOT)')
    cleanup = '''\n\ndef cleanup_transition_bridges(target: Path) -> None:\n    if not NAMING["migration"].get("removeBridgeAfterCanonicalBootstrap", False):\n        return\n    opencode = target.resolve() / ".opencode"\n    for rel in NAMING["migration"].get("bridgeEntrypoints", []):\n        candidate = opencode / rel\n        try:\n            if candidate.is_file():\n                candidate.unlink()\n        except OSError:\n            pass\n'''
    text = text.replace('\ndef main() -> int:\n', cleanup + '\n\ndef main() -> int:\n')
    text = text.replace('    target, distribution_root = parse_app_args(argv)\n    return supervise_app(target, distribution_root, argv)', '    target, distribution_root = parse_app_args(argv)\n    cleanup_transition_bridges(target)\n    return supervise_app(target, distribution_root, argv)')
    path.write_text(text, encoding="utf-8")


def patch_verify() -> None:
    path = ROOT / "pack/.opencode/bin/codesleuth-verify.py"
    text = path.read_text(encoding="utf-8")
    text = text.replace('    "bin/codesleuth", "bin/codesleuth.ps1",\n    "bin/codesleuth_tui_base.py", "bin/codesleuth_tui.py", "bin/codesleuth_tui_core.py", "bin/codesleuth_tui_bootstrap.py",', '    "bin/codesleuth", "bin/codesleuth.ps1",\n    "bin/codesleuth_tui_base.py", "bin/codesleuth_tui.py", "bin/codesleuth_tui_core.py", "bin/codesleuth_tui_bootstrap.py",\n    "bin/codesleuth_naming.py",')
    text = text.replace('    "opencode.json", "codesleuth.json", "codesleuth-user.json", "CODESLEUTH-REPORTS.md"', '    "opencode.json", "codesleuth.json", "codesleuth-user.json", "codesleuth-naming.json", "CODESLEUTH-REPORTS.md"')
    text = text.replace('print("floating update check (compatibility command): .opencode/bin/codesleuth-update --check")', 'print("floating update check: .opencode/bin/codesleuth-update --check")')
    path.write_text(text, encoding="utf-8")


def patch_docs() -> None:
    files = [ROOT / "README.md", ROOT / "README.ru.md", ROOT / "README.uk.md"]
    for path in files:
        lines = path.read_text(encoding="utf-8").splitlines()
        cleaned = []
        for line in lines:
            low = line.lower()
            if "compatibility alias" in low and "codesleuth" in low:
                continue
            cleaned.append(line)
        text = "\n".join(cleaned) + "\n"
        text = text.replace("Direct smoke/integrity check:", "Direct integrity check:")
        text = text.replace("The TUI **Verify** button invokes this installed smoke gate.", "The TUI **Verify** button invokes this installed integrity gate.")
        text = text.replace("Прямая smoke/integrity-проверка:", "Прямая integrity-проверка:")
        text = text.replace("Кнопка TUI **Verify** вызывает этот установленный smoke gate.", "Кнопка TUI **Verify** вызывает этот установленный integrity gate.")
        text = text.replace("Пряма smoke/integrity-перевірка:", "Пряма integrity-перевірка:")
        text = text.replace("Кнопка TUI **Verify** викликає цей встановлений smoke gate.", "Кнопка TUI **Verify** викликає цей встановлений integrity gate.")
        path.write_text(text, encoding="utf-8")

    english = (ROOT / "README.md").read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(english)).encode() + b"\0" + english).hexdigest()
    for name in ("README.ru.md", "README.uk.md"):
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        text = re.sub(r'<!-- README-SOURCE-BLOB: [0-9a-f]{40} -->', f'<!-- README-SOURCE-BLOB: {blob} -->', text, count=1)
        path.write_text(text, encoding="utf-8")


def add_tests() -> None:
    path = ROOT / "tests/test_naming_cutover.py"
    path.write_text(
        r'''from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "pack/.opencode/codesleuth-naming.json"


def test_naming_manifest_is_authoritative_and_complete():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["schemaVersion"] == 1
    assert data["product"] == {"displayName": "CodeSleuth", "slug": "codesleuth"}
    assert data["canonical"]["state"] == {"metadata": "codesleuth.json", "settings": "codesleuth-user.json"}
    assert data["canonical"]["entrypoints"]["verify"] == "bin/codesleuth-verify.py"
    assert data["canonical"]["python"]["tuiBootstrap"] == "bin/codesleuth_tui_bootstrap.py"
    assert data["migration"]["freshInstallMaterializesLegacy"] is False
    assert data["migration"]["bridgeManaged"] is False


def test_static_legacy_entrypoints_are_absent():
    for rel in (
        "review-pack",
        "review-pack.ps1",
        "pack/.opencode/bin/review-pack",
        "pack/.opencode/bin/review-pack.ps1",
        "pack/.opencode/bin/review-pack-update",
        "pack/.opencode/bin/review-pack-update.ps1",
        "pack/.opencode/bin/review-pack-update.py",
        "pack/.opencode/bin/review-pack-smoke.py",
        "pack/.opencode/bin/review_pack_tui.py",
        "pack/.opencode/bin/review_pack_tui_core.py",
        "pack/.opencode/bin/review_pack_tui_bootstrap.py",
    ):
        assert not (ROOT / rel).exists(), rel


def test_canonical_entrypoints_are_present():
    for rel in (
        "codesleuth",
        "codesleuth.ps1",
        "pack/.opencode/bin/codesleuth",
        "pack/.opencode/bin/codesleuth.ps1",
        "pack/.opencode/bin/codesleuth-update",
        "pack/.opencode/bin/codesleuth-update.ps1",
        "pack/.opencode/bin/codesleuth_update.py",
        "pack/.opencode/bin/codesleuth-verify.py",
        "pack/.opencode/bin/codesleuth_tui_base.py",
        "pack/.opencode/bin/codesleuth_tui_core.py",
        "pack/.opencode/bin/codesleuth_tui_bootstrap.py",
    ):
        assert (ROOT / rel).is_file(), rel


def test_legacy_product_literals_are_bounded():
    needles = ("review-pack", "review_pack", "REVIEW_PACK")
    allowed = {
        "pack/.opencode/codesleuth-naming.json",
        "docs/CODESLEUTH-NAMING-CUTOVER.md",
        "tests/test_naming_cutover.py",
    }
    offenders = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in allowed or rel.startswith("docs/archive/"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(needle in text for needle in needles):
            offenders.append(rel)
    assert offenders == []


def test_installer_conflicting_persistent_state_fails_closed(tmp_path):
    spec = importlib.util.spec_from_file_location("codesleuth_installer", ROOT / "install.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    target = tmp_path / ".opencode"
    target.mkdir()
    (target / module.META_NAME).write_text('{"schemaVersion": 2, "version": "new"}\n', encoding="utf-8")
    (target / module.LEGACY_META_NAME).write_text('{"schemaVersion": 2, "version": "old"}\n', encoding="utf-8")
    try:
        module._resolve_named_state(target, module.META_NAME, module.LEGACY_META_NAME)
    except RuntimeError as exc:
        assert "conflicting CodeSleuth persistent state" in str(exc)
    else:
        raise AssertionError("conflicting persistent state must fail closed")


def test_installer_migrates_identical_or_legacy_only_state(tmp_path):
    spec = importlib.util.spec_from_file_location("codesleuth_installer_migrate", ROOT / "install.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    target = tmp_path / ".opencode"
    target.mkdir()
    legacy = target / module.LEGACY_META_NAME
    legacy.write_text('{"schemaVersion": 2, "version": "dev"}\n', encoding="utf-8")
    value, migrated = module._resolve_named_state(target, module.META_NAME, module.LEGACY_META_NAME)
    assert migrated is True
    assert value["version"] == "dev"
    assert (target / module.META_NAME).is_file()
    assert not legacy.exists()
''',
        encoding="utf-8",
    )


def cleanup_worker() -> None:
    (ROOT / ".github/naming_cutover_apply.py").unlink(missing_ok=True)
    (ROOT / ".github/workflows/naming-cutover-worker.yml").unlink(missing_ok=True)
    workflows = ROOT / ".github/workflows"
    if workflows.exists() and not any(workflows.iterdir()):
        workflows.rmdir()
    github = ROOT / ".github"
    if github.exists() and not any(github.iterdir()):
        github.rmdir()


def main() -> None:
    for src, dst in RENAMES.items():
        source = ROOT / src
        target = ROOT / dst
        if source.exists():
            if target.exists():
                raise RuntimeError(f"rename target already exists: {dst}")
            target.parent.mkdir(parents=True, exist_ok=True)
            source.rename(target)
    for rel in DELETE:
        (ROOT / rel).unlink(missing_ok=True)
    replace_text()
    add_loader()
    patch_installer()
    patch_lifecycle()
    patch_tui_core()
    patch_updater()
    patch_bootstrap()
    patch_verify()
    patch_docs()
    add_tests()
    cleanup_worker()


if __name__ == "__main__":
    main()
