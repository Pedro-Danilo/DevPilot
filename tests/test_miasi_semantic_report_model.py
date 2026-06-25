from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.miasi import (
    MiasiSemanticReport,
    MiasiSemanticReportBuilder,
    SemanticFinding,
    SemanticRuleResult,
    SemanticRuleStatus,
    SemanticSeverity,
)
from devpilot_core.miasi.semantic_rules import (
    highest_semantic_severity,
    is_blocking_severity,
    normalize_semantic_severity,
    severity_to_rule_status,
)
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "miasi_semantic_report"


def _read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_miasi_semantic_report_schema_is_registered() -> None:
    catalog = _read_json("docs/schemas/schema_catalog.json")
    entries = {item["schema_id"]: item for item in catalog["schemas"]}

    assert "SCHEMA-DEVPL-MIASI-SEMANTIC-REPORT-V1" in entries
    entry = entries["SCHEMA-DEVPL-MIASI-SEMANTIC-REPORT-V1"]
    assert entry["path"] == "docs/schemas/miasi_semantic_report.schema.json"
    assert entry["contract"] == "MiasiSemanticReport"
    assert entry["validation_enabled_sprint"] == "POST-H-004-A"
    assert (ROOT / entry["path"]).is_file()


def test_empty_report_builder_generates_schema_valid_payload() -> None:
    payload = MiasiSemanticReportBuilder(ROOT).build_empty_payload()

    result = SchemaValidator(ROOT).validate_payload(
        schema="MiasiSemanticReport",
        payload=payload,
        instance_label="in-memory:miasi-semantic-empty-report",
    )

    assert result.ok, result.to_dict()
    assert payload["schema_id"] == "SCHEMA-DEVPL-MIASI-SEMANTIC-REPORT-V1"
    assert payload["created_by"] == "POST-H-004-A"
    assert payload["summary"]["blocking_findings_total"] == 0
    assert payload["dry_run"] is True
    assert payload["network_used"] is False
    assert payload["external_api_used"] is False
    assert payload["mutations_performed"] is False


def test_report_fixture_validates_against_schema() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="MiasiSemanticReport",
        instance=FIXTURES / "valid_schema_only_report.json",
    )

    assert result.ok, result.to_dict()


def test_schema_rejects_mutating_or_network_like_report() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="MiasiSemanticReport",
        instance=FIXTURES / "invalid_mutating_report.json",
    )

    assert not result.ok
    assert any(finding.id == "SCHEMA_VALIDATION_ERROR" for finding in result.findings)
    assert any("True was expected" in finding.message or "const" in finding.message or "true" in finding.message.lower() for finding in result.findings)


def test_semantic_rule_result_keeps_block_findings_machine_readable() -> None:
    finding = SemanticFinding(
        finding_id="MIASI_SEMANTIC_REMOTE_EXECUTE_BLOCK",
        rule_id="SEM-REMOTE-001",
        severity=SemanticSeverity.BLOCK,
        message="remote.execute must remain blocked.",
        category="no-go",
        subject_type="tool",
        subject_id="remote.execute",
        path=".devpilot/miasi/tool_registry.json",
        metadata={"no_go_gate": True},
    )
    rule = SemanticRuleResult.from_findings(
        rule_id="SEM-REMOTE-001",
        title="Remote execution must remain blocked",
        findings=[finding],
        subjects_evaluated=1,
    )
    report = MiasiSemanticReport(
        report_id="blocked-synthetic-report",
        created_by="POST-H-004-A",
        status="blocked",
        rule_results=(rule,),
        source_paths={"tool_registry": ".devpilot/miasi/tool_registry.json"},
    )
    payload = report.to_dict()

    assert payload["summary"]["block_findings_total"] == 1
    assert payload["summary"]["blocking_findings_total"] == 1
    assert payload["rule_results"][0]["status"] == SemanticRuleStatus.BLOCK.value
    assert payload["findings"][0]["severity"] == "block"

    result = SchemaValidator(ROOT).validate_payload(
        schema="MiasiSemanticReport",
        payload=payload,
        instance_label="in-memory:miasi-semantic-block-report",
    )
    assert result.ok, result.to_dict()


def test_semantic_severity_mapping_is_stable() -> None:
    assert normalize_semantic_severity("fail") == SemanticSeverity.ERROR
    assert severity_to_rule_status("block") == SemanticRuleStatus.BLOCK
    assert is_blocking_severity("error") is True
    assert is_blocking_severity("warning") is False
    assert highest_semantic_severity(["info", "warning", "block"]) == SemanticSeverity.BLOCK


def test_post_h_004_backlog_is_approved_and_documents_a() -> None:
    text = (ROOT / "docs" / "backlogs" / "POST-H-004_policy_miasi_semantic_validator.md").read_text(encoding="utf-8")

    assert 'status: "approved"' in text
    assert 'version: "1.0.0"' in text
    assert "POST-H-004-A" in text
    assert "SCHEMA-DEVPL-MIASI-SEMANTIC-REPORT-V1" in text
    assert "implemented-initial" in text
    assert "POST-H-004-B" in text
    assert "POST-H-004-E" in text
