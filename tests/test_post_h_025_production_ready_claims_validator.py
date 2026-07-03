from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.industrial import ProductionReadyClaimsValidator, ProductionReadyClaimsValidatorOptions
from devpilot_core.quality import QualityGate, QualityGateOptions

ROOT = Path(__file__).resolve().parents[1]


def test_production_ready_claims_validator_passes_current_repo() -> None:
    result = ProductionReadyClaimsValidator(ROOT).validate()

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["quality_gate_subgate"] == "production-ready-claims-validator"
    assert summary["documents_scanned_total"] == 3
    assert summary["forbidden_document_claims_total"] == 0
    assert summary["report_validated"] is True
    assert summary["report_claim_violations_total"] == 0
    assert summary["report_no_go_violations_total"] == 0
    assert summary["project_state_no_go_violations_total"] == 0
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["source_mutations_performed"] is False


def test_production_ready_claims_validator_blocks_affirmative_document_overclaims(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "DevPilot is enterprise-ready and compliance-certified. remote_execution_enabled=true.\n",
        encoding="utf-8",
    )

    result = ProductionReadyClaimsValidator(
        tmp_path,
        options=ProductionReadyClaimsValidatorOptions(
            document_paths=("README.md",),
            include_gate_report=False,
            project_state_path=None,
        ),
    ).validate()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    summary = result.data["summary"]
    assert summary["forbidden_document_claims_total"] >= 3
    finding_ids = {finding.id for finding in result.findings}
    assert "PRODUCTION_READY_FORBIDDEN_DOCUMENT_CLAIM" in finding_ids


def test_production_ready_claims_validator_blocks_report_and_project_state_no_go_flags(tmp_path: Path) -> None:
    report = _valid_report()
    report["claims"]["enterprise_ready"] = True
    report["no_go_gates"]["remote_execution_enabled"] = True
    report_path = tmp_path / "production_ready_local_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    project_state = {
        "remote_execution_enabled": True,
        "connector_write_enabled": False,
        "plugin_execution_enabled": False,
        "post_h_025_remote_execution_enabled": False,
        "post_h_025_connector_write_enabled": False,
        "post_h_025_plugin_execution_enabled": False,
        "post_h_025_external_apis_required": False,
        "post_h_025_enterprise_ready_claimed": False,
        "post_h_025_compliance_certified_claimed": False,
        "post_h_025_remote_ready_claimed": False,
        "post_h_025_saas_ready_claimed": False,
    }
    state_path = tmp_path / "project_state.json"
    state_path.write_text(json.dumps(project_state, indent=2), encoding="utf-8")

    result = ProductionReadyClaimsValidator(
        tmp_path,
        options=ProductionReadyClaimsValidatorOptions(
            document_paths=(),
            report_path="production_ready_local_report.json",
            project_state_path="project_state.json",
        ),
    ).validate()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    finding_ids = {finding.id for finding in result.findings}
    assert "PRODUCTION_READY_REPORT_FORBIDDEN_CLAIM" in finding_ids
    assert "PRODUCTION_READY_REPORT_NO_GO_ENABLED" in finding_ids
    assert "PRODUCTION_READY_PROJECT_STATE_NO_GO_ENABLED" in finding_ids
    assert result.data["summary"]["report_claim_violations_total"] == 1
    assert result.data["summary"]["report_no_go_violations_total"] == 1
    assert result.data["summary"]["project_state_no_go_violations_total"] == 1


def test_production_ready_claims_validator_is_registered_in_quality_gate() -> None:
    gate = QualityGate(ROOT, options=QualityGateOptions(profile="hardening"))
    subgates = {subgate.id: subgate for subgate in gate._subgates()}

    assert "production-ready-claims-validator" in subgates
    assert subgates["production-ready-claims-validator"].critical is True
    result = subgates["production-ready-claims-validator"].runner()
    assert result.ok is True, result.to_dict()
    assert result.data["summary"]["quality_gate_subgate"] == "production-ready-claims-validator"


def test_production_ready_claims_validator_artifacts_are_synchronized() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-025_production_ready_declaration_gate.md").read_text(encoding="utf-8")
    tcr = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")

    assert "POST-H-025-D — No-go gates y claims validator" in readme
    assert "POST-H-025-D — No-go gates y claims validator" in runbook
    assert 'current_micro_sprint: "POST-H-025-D"' in backlog
    assert 'next_micro_sprint: "POST-H-025-E"' in backlog
    assert "post-h-025-production-ready-claims-validator" in tcr
    assert "post-h-025-production-ready-claims-validator" in tcr_v2
    assert (ROOT / "docs/audits/post_h_025_d_claims_validator_report.md").exists()
    assert (ROOT / "docs/post_h_025_d_manifest.json").exists()


def _valid_report() -> dict:
    return {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-PRODUCTION-READY-LOCAL-REPORT-V1",
        "report_id": "production-ready-local-report-test",
        "created_by": "POST-H-025-D",
        "created_at": "2026-07-03T00:00:00Z",
        "scope": "production-ready-local",
        "decision": "PASS",
        "score": 100,
        "minimum_score": 90,
        "blocking_gaps_total": 0,
        "passed_hitos_total": 17,
        "required_hitos_total": 17,
        "no_go_gates_passed": True,
        "claims": {
            "production_ready_local": True,
            "enterprise_ready": False,
            "remote_ready": False,
            "compliance_certified": False,
            "saas_ready": False,
        },
        "no_go_gates": {
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "external_apis_required": False,
            "compliance_certification_claim": False,
            "enterprise_ready_claim": False,
            "remote_ready_claim": False,
            "saas_ready_claim": False,
        },
        "evidence_results": [
            {"hito_id": "POST-H-024", "status": "pass", "required_for_pass": True, "findings_total": 0}
        ],
        "gaps": [],
        "safety": {
            "local_first": True,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
        },
        "summary": {"preliminary": True},
        "limitations": ["Synthetic PASS payload for claims validator tests."],
    }
