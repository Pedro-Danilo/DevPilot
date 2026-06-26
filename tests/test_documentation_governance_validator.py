from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.docs_governance import DocumentationGovernanceValidationOptions, DocumentationGovernanceValidator
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def test_documentation_governance_validator_passes_baseline() -> None:
    result = DocumentationGovernanceValidator(ROOT).run()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-009-E"
    assert summary["documents_checked_total"] == summary["documents_total"] == 37
    assert summary["frontmatter_checked_total"] >= 7
    assert summary["blocking_findings_total"] == 0
    assert summary["warnings_total"] == 0
    assert summary["docs_governance_passed"] is True
    assert summary["markdown_json_sync_passed"] is True
    assert summary["backlog_governance_passed"] is True
    assert summary["backlogs_expected_total"] == 24
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["llm_judge_used"] is False


def test_documentation_governance_write_report_validates_against_schema() -> None:
    result = DocumentationGovernanceValidator(ROOT, DocumentationGovernanceValidationOptions(write_report=True)).run()

    assert result.ok, result.to_dict()
    reports = result.data["reports"]
    assert reports["json"] == "outputs/reports/documentation_governance_report.json"
    assert reports["markdown"] == "outputs/reports/documentation_governance_report.md"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()

    schema_result = SchemaValidator(ROOT).validate(
        schema="DocumentationGovernanceReport",
        instance=reports["json"],
    )
    assert schema_result.ok, schema_result.to_dict()
    assert schema_result.data["summary"]["valid"] is True


def test_docs_governance_cli_validate_json_is_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["docs-governance", "validate", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "docs-governance validate"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["frontmatter_status_ownership_passed"] is True
    assert payload["data"]["summary"]["blocking_findings_total"] == 0


def test_documentation_governance_validator_blocks_missing_required_test(tmp_path: Path) -> None:
    root = tmp_path
    (root / ".devpilot/docs_governance").mkdir(parents=True)
    (root / "docs").mkdir()
    source = root / "docs/source.md"
    source.write_text(
        "---\n"
        "doc_id: \"DOC-001\"\n"
        "title: \"Source\"\n"
        "status: \"approved\"\n"
        "version: \"1.0.0\"\n"
        "owner: \"Ordóñez\"\n"
        "updated: \"2026-06-26\"\n"
        "approval: \"approved_by_owner\"\n"
        "---\n"
        "# Source\n",
        encoding="utf-8",
    )
    registry = {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-DOCUMENTATION-SOURCE-REGISTRY-V1",
        "registry_id": "tmp-docs-registry",
        "created_by": "TEST",
        "status": "implemented-initial",
        "documents": [
            {
                "doc_id": "DOC-001",
                "path": "docs/source.md",
                "classification": "source-of-truth",
                "domain": "test",
                "owner": "Ordóñez",
                "status_required": "approved",
                "criticality": "P0",
                "required_tests": ["tests/missing_test.py"],
                "sync_rules": [],
                "lifecycle": "active",
            }
        ],
        "summary": {},
        "rules": {},
        "safety": {},
    }
    (root / ".devpilot/docs_governance/source_registry.json").write_text(json.dumps(registry), encoding="utf-8")

    result = DocumentationGovernanceValidator(root).run()

    assert not result.ok
    assert result.exit_code.value == 2
    assert any(finding.id == "DOCUMENTATION_REQUIRED_TEST_MISSING" for finding in result.findings)
