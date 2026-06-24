from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.miasi import MiasiSemanticValidator
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def test_miasi_semantic_validator_current_bundle_passes_with_read_only_report() -> None:
    result = MiasiSemanticValidator(ROOT).validate()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.command == "miasi semantic-validate"
    assert result.data["summary"]["rules_total"] >= 10
    assert result.data["summary"]["blocking_findings_total"] == 0
    assert result.data["dry_run"] is True
    assert result.data["network_used"] is False
    assert result.data["external_api_used"] is False
    assert result.data["mutations_performed"] is False
    assert result.data["report"]["created_by"] == "POST-H-004-C"
    assert result.data["report"]["status"] in {"pass", "warning"}

    schema_result = SchemaValidator(ROOT).validate_payload(
        schema="MiasiSemanticReport",
        payload=result.data["report"],
        instance_label="in-memory:miasi-semantic-validator-current-bundle",
    )
    assert schema_result.ok, schema_result.to_dict()


def test_miasi_semantic_validate_cli_json_is_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["miasi", "semantic-validate", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "miasi semantic-validate"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["blocking_findings_total"] == 0
    assert payload["data"]["report"]["schema_id"] == "SCHEMA-DEVPL-MIASI-SEMANTIC-REPORT-V1"
    assert payload["data"]["tests_executed"] is False


def test_miasi_semantic_validate_cli_can_write_evidence_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["miasi", "semantic-validate", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["data"]["reports"]["json"] == "outputs/reports/miasi_semantic_validate.json"
    assert payload["data"]["reports"]["markdown"] == "outputs/reports/miasi_semantic_validate.md"
    assert (ROOT / payload["data"]["reports"]["json"]).is_file()
    assert (ROOT / payload["data"]["reports"]["markdown"]).is_file()


def test_post_h_004_c_documentation_markers_are_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-004_policy_miasi_semantic_validator.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    security_doc = (ROOT / "docs/03_security/policy_miasi_semantic_validation.md").read_text(encoding="utf-8")

    assert 'version: "0.4.0"' in backlog
    assert "POST-H-004-B" in backlog
    assert "miasi semantic-validate" in backlog
    assert "POST-H-004-C" in readme
    assert "POST-H-004-D" in readme
    assert "POST-H-004-C" in runbook
    assert "approval/RBAC/security guards" in security_doc
