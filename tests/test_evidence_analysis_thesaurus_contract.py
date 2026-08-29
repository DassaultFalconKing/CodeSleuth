from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THESAURUS = ROOT / "docs" / "EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md"
DOCS_INDEX = ROOT / "docs" / "README.md"
STABLE_BASELINE = ROOT / "docs" / "STABLE-INTEGRATION-BASELINE.md"


def test_thesaurus_is_indexed_and_keeps_core_identity_authority_rules() -> None:
    text = THESAURUS.read_text(encoding="utf-8")
    index = DOCS_INDEX.read_text(encoding="utf-8")

    assert "EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md" in index
    assert "Identity before claim" in text
    assert "Authority precedes representation" in text
    assert "Ancestry transfers context, not acceptance" in text
    assert "tree-equivalent != acceptance-equivalent" in text
    assert "mergeable=true` is **not** acceptance evidence" in text
    assert "Publication increases reach, not authority" in text


def test_thesaurus_binds_acceptance_to_profile_identity_as_well_as_subject() -> None:
    text = THESAURUS.read_text(encoding="utf-8")

    assert "exact subject SHA" in text
    assert "+ profile identity" in text
    assert "+ gates/environments" in text
    assert "+ run/result identity" in text


def test_thesaurus_does_not_upgrade_test_acceptance_to_formal_proof() -> None:
    text = THESAURUS.read_text(encoding="utf-8")

    assert "Ordinary unit/integration/acceptance testing is **not formal proof of program correctness**" in text
    assert "evidence-backed verification or acceptance within a declared profile" in text
    assert "unless a formal method is explicitly named" in text
    assert "verification obligation" in text
    assert "acceptance obligation" in text


def test_thesaurus_preserves_fail_closed_uncertainty_vocabulary() -> None:
    text = THESAURUS.read_text(encoding="utf-8")

    for result in ("`PASS`", "`FAIL`", "`INCONCLUSIVE`", "`UNAVAILABLE`", "`NOT_APPLICABLE`"):
        assert result in text
    assert "Do not collapse `INCONCLUSIVE` or `UNAVAILABLE` into PASS" in text
    assert "Unknown remains unknown" in text


def test_external_crosswalk_is_explicitly_non_certifying() -> None:
    text = THESAURUS.read_text(encoding="utf-8")

    assert "not a compliance certification" in text
    assert "SWEBOK" in text
    assert "NASA Software Engineering / Software Assurance Handbook" in text
    assert "NIST Secure Software Development Framework" in text
    assert "SLSA v1.2" in text
    assert "in-toto" in text
    assert "Reproducible Builds" in text
    assert "Structured Assurance Case Metamodel" in text


def test_anti_shortcuts_keep_branch_ci_and_reports_non_authoritative() -> None:
    text = THESAURUS.read_text(encoding="utf-8")

    for shortcut in (
        "CI is green",
        "This PR passed",
        "The parent passed, so this is safe",
        "GitHub says mergeable",
        "The report says PASS",
        "The graph says X depends on Y",
        "No issues found",
        "Same code, new SHA",
    ):
        assert shortcut in text


def test_stable_baseline_never_hard_codes_the_live_sib_ref_target() -> None:
    text = STABLE_BASELINE.read_text(encoding="utf-8")

    assert "Its current target must be resolved from Git when needed" in text
    assert "must not be hard-coded into this normative definition" in text
    assert "moving the `SIB` ref does not create, transfer, or strengthen acceptance" in text
    assert "At the time this model was introduced it points to:" not in text
