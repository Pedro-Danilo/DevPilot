from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli import main
from devpilot_core.cli_models import ExitCode
from devpilot_core.validators.checklist import parse_checklist_markdown, validate_precode_checklist
from devpilot_core.validators.readiness import build_strict_readiness_result


ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "docs" / "checklists" / "checklist_pre_code.md"


def test_precode_checklist_parser_extracts_mandatory_artifact_rows():
    document = parse_checklist_markdown(CHECKLIST)
    mandatory_artifacts = [row for row in document.rows if row.mandatory and row.artifact_path]

    assert len(document.rows) >= 20
    assert any(row.artifact_path == "docs/00_product/product_vision.md" for row in mandatory_artifacts)
    assert any(row.artifact_path == "docs/06_miasi/agent_card.md" for row in mandatory_artifacts)


def test_precode_checklist_gate_passes_on_repository_baseline():
    result = validate_precode_checklist(ROOT)

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["mandatory_artifacts_present"] == result.data["summary"]["mandatory_artifacts_total"]


def test_precode_checklist_cli_json_is_parseable(capsys):
    exit_code = main(["checklist-pre-code", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["command"] == "checklist-pre-code"
    assert payload["ok"] is True


def test_precode_checklist_blocks_when_mandatory_artifacts_are_missing(tmp_path):
    checklist_dir = tmp_path / "docs" / "checklists"
    checklist_dir.mkdir(parents=True)
    (checklist_dir / "checklist_pre_code.md").write_text(CHECKLIST.read_text(encoding="utf-8"), encoding="utf-8")

    result = validate_precode_checklist(tmp_path)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "CHECKLIST_REQUIRED_ARTIFACT_MISSING" for finding in result.findings)


def test_strict_readiness_passes_and_generates_report_paths(capsys):
    exit_code = main(["readiness-check", "--strict", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["command"] == "readiness-check"
    assert payload["ok"] is True
    assert payload["data"]["strict"] is True
    assert payload["data"]["reports"]["json"] == "outputs/reports/readiness_check.json"
    assert payload["data"]["reports"]["markdown"] == "outputs/reports/readiness_check.md"


def test_strict_readiness_blocks_when_required_artifact_is_missing(tmp_path):
    result = build_strict_readiness_result(tmp_path)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "READINESS_STRICT_REQUIRED_ARTIFACT_MISSING" for finding in result.findings)
