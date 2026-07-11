from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from devpilot_core.application import ApplicationRequest, ApplicationResponse, ApplicationService
from devpilot_core.cli_models import ExitCode
from devpilot_core.evidence_graph import OperatorEvidenceExportBuilder, OperatorEvidenceExportOptions
from devpilot_core.interfaces.api import ApiRouteContractRegistryValidator, create_app
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "test-token-operator-evidence-export"

FORBIDDEN_LITERAL_VALUES = [
    ".devpilot/devpilot.db",
    "\\\\.devpilot\\\\devpilot.db",
    ".env",
]


def _export_from_result(result):
    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    export = result.data["export"]
    assert export["schema_id"] == "SCHEMA-DEVPL-OPERATOR-EVIDENCE-EXPORT-V1"
    return export


def _assert_redacted_payload(export: dict) -> None:
    serialized = json.dumps(export, ensure_ascii=False, sort_keys=True)
    for literal in FORBIDDEN_LITERAL_VALUES:
        assert literal not in serialized
    assert export["redacted"] is True
    assert export["redaction_manifest"]["redaction_required"] is True
    assert export["redaction_manifest"]["redaction_applied"] is True
    assert export["redaction_manifest"]["raw_prompts_exported"] is False
    assert export["redaction_manifest"]["raw_outputs_exported"] is False
    assert export["redaction_manifest"]["raw_payloads_exported"] is False
    assert export["redaction_manifest"]["env_files_exported"] is False
    assert export["redaction_manifest"]["devpilot_db_exported"] is False
    assert export["redaction_manifest"]["sqlite_raw_exported"] is False
    assert export["safety"]["network_used"] is False
    assert export["safety"]["external_api_used"] is False
    assert export["safety"]["commands_executed"] is False
    assert export["safety"]["source_mutations_performed"] is False


def test_operator_evidence_export_requires_redacted_flag() -> None:
    result = OperatorEvidenceExportBuilder(ROOT, OperatorEvidenceExportOptions(redacted=False)).build()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["decision"] == "BLOCK"
    assert any(finding.id == "OPERATOR_EVIDENCE_EXPORT_REDACTION_REQUIRED" for finding in result.findings)


def test_operator_evidence_export_dry_run_is_schema_valid_and_writes_nothing() -> None:
    package_dir = Path("outputs/audit_exports/operator_evidence_export/test_dry_run_package")
    report_json = Path("outputs/reports/test_post_h_031_e_dry_run_report.json")
    report_md = Path("outputs/reports/test_post_h_031_e_dry_run_report.md")
    shutil.rmtree(ROOT / package_dir.parent, ignore_errors=True)

    result = OperatorEvidenceExportBuilder(
        ROOT,
        OperatorEvidenceExportOptions(
            redacted=True,
            dry_run=True,
            write_report=False,
            package_dir=package_dir,
            output_json=report_json,
            output_markdown=report_md,
        ),
    ).build()
    export = _export_from_result(result)

    validation = SchemaValidator(ROOT).validate_payload(
        schema="OperatorEvidenceExport",
        payload=export,
        instance_label="in-memory-operator-evidence-export",
    )

    assert validation.ok is True, validation.to_dict()
    assert export["created_by"] == "POST-H-031-E"
    assert export["summary"]["decision"] == "PASS"
    assert export["summary"]["dry_run"] is True
    assert export["summary"]["reports_written"] is False
    assert export["summary"]["files_written_total"] == 0
    assert export["summary"]["sections_total"] >= 7
    assert set(export["sections"]) >= {
        "evidence_graph",
        "operator_health",
        "gap_action_map",
        "claims_no_go_dashboard",
        "observability_redacted_export",
        "runtime_state_inventory",
        "production_ready_final_declaration",
    }
    assert not (ROOT / package_dir).exists()
    assert not (ROOT / report_json).exists()
    assert not (ROOT / report_md).exists()
    _assert_redacted_payload(export)


def test_operator_evidence_export_write_report_creates_curated_package_and_checksums() -> None:
    base = Path("outputs/audit_exports/operator_evidence_export/test_write_report")
    package_dir = base
    report_json = Path("outputs/reports/test_post_h_031_e_write_operator_evidence_export.json")
    report_md = Path("outputs/reports/test_post_h_031_e_write_operator_evidence_export.md")
    shutil.rmtree(ROOT / base, ignore_errors=True)
    report_json.unlink(missing_ok=True)
    report_md.unlink(missing_ok=True)

    result = OperatorEvidenceExportBuilder(
        ROOT,
        OperatorEvidenceExportOptions(
            redacted=True,
            dry_run=False,
            write_report=True,
            package_dir=package_dir,
            output_json=report_json,
            output_markdown=report_md,
        ),
    ).build()
    export = _export_from_result(result)

    assert export["summary"]["dry_run"] is False
    assert export["summary"]["reports_written"] is True
    assert export["summary"]["files_written_total"] == len(export["exported_files"])
    assert (ROOT / report_json).exists()
    assert (ROOT / report_md).exists()
    assert (ROOT / package_dir / "operator_evidence_export.json").exists()
    assert (ROOT / package_dir / "operator_evidence_export_manifest.json").exists()
    assert (ROOT / package_dir / "operator_evidence_export_README.md").exists()
    assert (ROOT / package_dir / "checksums.sha256").exists()
    assert (ROOT / package_dir / "sections" / "evidence_graph_summary.json").exists()
    assert all(item["path"].startswith("outputs/") for item in export["exported_files"])
    assert export["checksums"]
    assert "operator_evidence_export.json" in export["checksums"]
    assert "not an external certification" in (ROOT / package_dir / "operator_evidence_export_README.md").read_text(encoding="utf-8")
    _assert_redacted_payload(json.loads((ROOT / report_json).read_text(encoding="utf-8")))


def test_operator_evidence_export_cli_json_dry_run_and_write_report() -> None:
    base = Path("outputs/audit_exports/operator_evidence_export/test_cli")
    package_dir = base / "package"
    report_json = Path("outputs/reports/test_post_h_031_e_cli_operator_evidence_export.json")
    report_md = Path("outputs/reports/test_post_h_031_e_cli_operator_evidence_export.md")
    shutil.rmtree(ROOT / base, ignore_errors=True)
    report_json.unlink(missing_ok=True)
    report_md.unlink(missing_ok=True)

    dry_run = subprocess.run(
        [
            sys.executable,
            "-m",
            "devpilot_core",
            "operator",
            "evidence-export",
            "--redacted",
            "--dry-run",
            "--json",
            "--package-dir",
            str(package_dir),
            "--output-json",
            str(report_json),
            "--output-markdown",
            str(report_md),
        ],
        cwd=ROOT,
        env={"PYTHONPATH": "src"},
        text=True,
        capture_output=True,
        check=False,
    )
    assert dry_run.returncode == 0, dry_run.stderr + dry_run.stdout
    dry_payload = json.loads(dry_run.stdout)
    assert dry_payload["command"] == "operator evidence-export"
    assert dry_payload["data"]["summary"]["dry_run"] is True
    assert dry_payload["data"]["summary"]["reports_written"] is False
    assert not (ROOT / package_dir).exists()

    write = subprocess.run(
        [
            sys.executable,
            "-m",
            "devpilot_core",
            "operator",
            "evidence-export",
            "--redacted",
            "--write-report",
            "--json",
            "--package-dir",
            str(package_dir),
            "--output-json",
            str(report_json),
            "--output-markdown",
            str(report_md),
        ],
        cwd=ROOT,
        env={"PYTHONPATH": "src"},
        text=True,
        capture_output=True,
        check=False,
    )
    assert write.returncode == 0, write.stderr + write.stdout
    write_payload = json.loads(write.stdout)
    assert write_payload["data"]["summary"]["reports_written"] is True
    assert (ROOT / package_dir / "checksums.sha256").exists()


def test_operator_evidence_export_application_service_and_api_route() -> None:
    service = ApplicationService(ROOT)
    direct = service.operator_evidence_export(redacted=True, dry_run=True, write_report=False)
    export = _export_from_result(direct)

    response = service.handle(
        ApplicationRequest(
            operation="operator.evidence_export",
            payload={"redacted": True, "dry_run": True, "write_report": False},
            client="api-local",
            dry_run=True,
        )
    )

    assert isinstance(response, ApplicationResponse)
    assert response.operation == "operator.evidence_export"
    assert response.ok is True, response.to_dict()
    assert response.exit_code == int(ExitCode.PASS)
    assert response.data["export"]["schema_id"] == export["schema_id"]
    assert response.data["summary"]["raw_payloads_exported"] is False

    client = TestClient(create_app(ROOT, api_token=TOKEN))
    missing_token = client.get("/api/v1/operator/evidence-export", headers={"Origin": "http://127.0.0.1:5173"})
    assert missing_token.status_code == 401
    api_response = client.get(
        "/api/v1/operator/evidence-export?redacted=true&dry_run=true&write_report=false",
        headers={"X-DevPilot-Token": TOKEN, "Origin": "http://127.0.0.1:5173"},
    )
    assert api_response.status_code == 200, api_response.text
    assert api_response.headers.get("X-DevPilot-Policy") == "allowed"
    payload = api_response.json()
    assert payload["contract"] == "DevPilotApplicationResponse"
    assert payload["operation"] == "operator.evidence_export"
    assert payload["ok"] is True
    assert payload["data"]["export"]["schema_id"] == "SCHEMA-DEVPL-OPERATOR-EVIDENCE-EXPORT-V1"
    assert payload["data"]["summary"]["dry_run"] is True


def test_operator_evidence_export_contracts_and_route_registry_are_synchronized() -> None:
    route_result = ApiRouteContractRegistryValidator(ROOT).validate()
    assert route_result.ok, route_result.to_dict()
    route_summary = route_result.data["summary"]
    assert route_summary["routes_total"] == 39
    assert route_summary["fastapi_route_keys_total"] == 39
    assert route_summary["canonical_router_route_keys_total"] == 39
    assert route_summary["application_service_routes_total"] == 35

    route_registry = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    routes = {route["route_id"]: route for route in route_registry["routes"]}
    assert routes["api.operator.evidence_export"]["operation"] == "operator.evidence_export"
    assert routes["api.operator.evidence_export"]["application_service_required"] is True
    assert routes["api.operator.evidence_export"]["policy_check_required"] is True
    assert routes["api.operator.evidence_export"]["auth_required"] is True
    assert routes["api.operator.evidence_export"]["mutations_allowed"] is False
    assert routes["api.operator.evidence_export"]["external_api_allowed"] is False

    schema_catalog = json.loads((ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8"))
    assert any(schema["schema_id"] == "SCHEMA-DEVPL-OPERATOR-EVIDENCE-EXPORT-V1" for schema in schema_catalog["schemas"])

    tcr_v2 = json.loads((ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8"))
    contracts = {contract["contract_id"]: contract for contract in tcr_v2["contracts"]}
    assert contracts["post-h-031-redacted-evidence-export-ux"]["domain"] == "operations.observability"
    assert contracts["post-h-031-redacted-evidence-export-application-api"]["domain"] == "application.service"
