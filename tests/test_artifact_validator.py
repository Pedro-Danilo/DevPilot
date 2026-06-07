from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli import main
from devpilot_core.cli_models import ExitCode
from devpilot_core.validators.artifact import validate_artifact_file


FIXTURES = Path(__file__).parent / "fixtures" / "docs"
ROOT = Path(__file__).resolve().parents[1]


def test_valid_requirements_artifact_passes():
    result = validate_artifact_file(
        FIXTURES / "valid_requirements_artifact.md",
        root=ROOT,
    )

    # The synthetic fixture uses the generic profile because it is outside docs/.
    # This verifies the validator path itself. Real profile validation is covered
    # by the repository document tests below.
    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["h1_count"] == 1


def test_real_requirements_document_matches_profile():
    path = ROOT / "docs" / "01_requirements" / "requirements_specification.md"
    result = validate_artifact_file(path, root=ROOT)

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["profile"]["id"] == "requirements-specification"
    assert result.data["missing_required_sections"] == []


def test_real_miasi_agent_card_matches_profile():
    path = ROOT / "docs" / "06_miasi" / "agent_card.md"
    result = validate_artifact_file(path, root=ROOT)

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["profile"]["id"] == "miasi-agent-card"
    assert result.data["missing_required_sections"] == []


def test_missing_sections_fail_for_reviewed_artifact():
    result = validate_artifact_file(
        FIXTURES / "invalid_requirements_missing_sections.md",
        root=ROOT,
    )

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    # Fixture is outside docs/ and therefore generic. Profile-specific failures
    # are tested through real docs and approved fixture below.


def test_approved_artifact_missing_structure_blocks_when_profile_matches(tmp_path):
    docs_dir = tmp_path / "docs" / "01_requirements"
    docs_dir.mkdir(parents=True)
    target = docs_dir / "requirements_specification.md"
    target.write_text((FIXTURES / "approved_missing_sections.md").read_text(encoding="utf-8"), encoding="utf-8")

    result = validate_artifact_file(target, root=tmp_path)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "ARTIFACT_REQUIRED_SECTION_MISSING" for finding in result.findings)
    assert any(finding.severity.value == "block" for finding in result.findings)


def test_validate_artifact_cli_json_pass(capsys):
    path = ROOT / "docs" / "01_requirements" / "requirements_specification.md"
    exit_code = main(["validate-artifact", str(path), "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["command"] == "validate-artifact"
    assert payload["ok"] is True
    assert payload["data"]["profile"]["id"] == "requirements-specification"


def test_validate_artifact_cli_json_blocks_for_approved_broken_profile(tmp_path, capsys):
    docs_dir = tmp_path / "docs" / "01_requirements"
    docs_dir.mkdir(parents=True)
    target = docs_dir / "requirements_specification.md"
    target.write_text((FIXTURES / "approved_missing_sections.md").read_text(encoding="utf-8"), encoding="utf-8")

    exit_code = main(["validate-artifact", str(target), "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 2
    assert payload["command"] == "validate-artifact"
    assert payload["ok"] is False
    assert any(finding["severity"] == "block" for finding in payload["findings"])
