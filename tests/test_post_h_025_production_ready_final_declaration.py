from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.application import ApplicationService
from devpilot_core.cli_models import ExitCode
from devpilot_core.industrial import ProductionReadyFinalDeclaration, ProductionReadyFinalDeclarationOptions
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def test_production_ready_final_declaration_passes_current_repo_without_source_mutation() -> None:
    before = _tracked_snapshot(ROOT)

    result = ProductionReadyFinalDeclaration(ROOT).finalize()

    after = _tracked_snapshot(ROOT)
    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    assert before == after
    summary = result.data["summary"]
    report = result.data["report"]
    assert summary["decision"] == "PASS"
    assert summary["production_ready_local_declared"] is True
    assert summary["final_declaration_artifact_available"] is True
    assert summary["formal_audit_declaration_pending"] is False
    assert summary["claims_valid"] is True
    assert summary["reports_written"] is False
    assert summary["audit_markdown_written"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["source_mutations_performed"] is False
    assert report["created_by"] == "POST-H-025-E"
    assert report["claims"] == {
        "production_ready_local": True,
        "enterprise_ready": False,
        "remote_ready": False,
        "compliance_certified": False,
        "saas_ready": False,
    }
    validation = SchemaValidator(ROOT).validate_payload(
        schema="ProductionReadyLocalReport",
        payload=report,
        instance_label="in-memory:post-h-025-e-final-report",
    )
    assert validation.ok, validation.to_dict()


def test_production_ready_final_declaration_writes_reports_and_audit_when_requested() -> None:
    output_json = "outputs/test_post_h_025_e/production_ready_local_report.json"
    output_markdown = "outputs/test_post_h_025_e/production_ready_local_report.md"
    audit_markdown = "outputs/test_post_h_025_e/devpilot_local_production_ready_declaration.md"

    result = ProductionReadyFinalDeclaration(
        ROOT,
        options=ProductionReadyFinalDeclarationOptions(
            write_report=True,
            write_audit_markdown=True,
            output_json=output_json,
            output_markdown=output_markdown,
            audit_markdown=audit_markdown,
        ),
    ).finalize()

    assert result.ok is True, result.to_dict()
    assert result.data["summary"]["reports_written"] is True
    assert result.data["summary"]["audit_markdown_written"] is True
    assert result.data["reports"] == {"json": output_json, "markdown": output_markdown}
    assert result.data["audit"] == {"written": True, "path": audit_markdown}
    assert (ROOT / output_json).exists()
    assert (ROOT / output_markdown).exists()
    assert (ROOT / audit_markdown).exists()
    payload = json.loads((ROOT / output_json).read_text(encoding="utf-8"))
    assert payload["decision"] == "PASS"
    assert payload["summary"]["reports_written"] is True
    assert payload["summary"]["audit_markdown_written"] is True
    audit_text = (ROOT / audit_markdown).read_text(encoding="utf-8")
    assert "DevPilot Local production-ready-local declaration" in audit_text
    assert "This declaration is limited to `production-ready-local`." in audit_text


def test_production_ready_final_declaration_blocks_missing_required_evidence(tmp_path: Path) -> None:
    criteria_path = tmp_path / ".devpilot/production/production_ready_local_criteria.json"
    criteria_path.parent.mkdir(parents=True)
    criteria_path.write_text(json.dumps(_minimal_criteria(), indent=2), encoding="utf-8")

    result = ProductionReadyFinalDeclaration(
        tmp_path,
        options=ProductionReadyFinalDeclarationOptions(
            criteria_path=".devpilot/production/production_ready_local_criteria.json",
        ),
    ).finalize()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    report = result.data["report"]
    assert report["decision"] == "BLOCK"
    assert report["claims"]["production_ready_local"] is False
    assert report["blocking_gaps_total"] >= 1
    assert result.data["summary"]["production_ready_local_declared"] is False


def test_production_ready_final_declaration_cli_and_application_service_are_synchronized(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    api_result = ApplicationService(ROOT).production_ready_local_final_declaration()
    exit_code = cli.main(["industrial-readiness", "production-ready-local-final", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert api_result.ok is True
    assert exit_code == 0
    assert payload["command"] == "industrial-readiness production-ready-local-final"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["decision"] == api_result.data["summary"]["decision"]
    assert payload["data"]["summary"]["claims_valid"] is True
    assert payload["data"]["summary"]["reports_written"] is False
    assert payload["data"]["report"]["created_by"] == "POST-H-025-E"


def test_production_ready_final_declaration_artifacts_are_synchronized() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-025_production_ready_declaration_gate.md").read_text(encoding="utf-8")
    tcr = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")

    assert "POST-H-025-E — Declaración final o BLOCK report" in readme
    assert "POST-H-025-E — Declaración final o BLOCK report" in runbook
    assert 'current_micro_sprint: "POST-H-025-E"' in backlog
    assert 'next_micro_sprint: "POST-H-026"' in backlog
    assert "post-h-025-production-ready-final-declaration" in tcr
    assert "post-h-025-production-ready-final-declaration" in tcr_v2
    assert (ROOT / "docs/audits/devpilot_local_production_ready_declaration.md").exists()
    assert (ROOT / "docs/audits/post_h_025_e_final_declaration_report.md").exists()
    assert (ROOT / "docs/post_h_025_e_manifest.json").exists()


def _minimal_criteria() -> dict:
    return {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-PRODUCTION-READY-LOCAL-CRITERIA-V1",
        "criteria_id": "test-final-criteria",
        "status": "implemented-initial",
        "scope": "production-ready-local",
        "minimum_score": 90,
        "blocking_gaps_allowed": 0,
        "required_hitos": ["POST-H-999"],
        "optional_design_hitos": [],
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
        "evidence_map": [
            {
                "hito_id": "POST-H-999",
                "classification": "required",
                "required_for_pass": True,
                "weight": 100,
                "evidence": [
                    {
                        "evidence_id": "required-evidence",
                        "title": "Required evidence",
                        "path": "missing_required.json",
                        "category": "manifest",
                        "requirement_level": "blocker",
                        "blocker_on_missing": True,
                        "expected_status": "present",
                        "expected_schema_id": None,
                        "producer_sprint": "POST-H-999",
                        "validation_command": "not executed by POST-H-025-E",
                        "notes": [],
                    }
                ],
            }
        ],
    }


def _tracked_snapshot(root: Path) -> set[str]:
    ignored_parts = {".git", ".pytest_cache", "__pycache__", "outputs"}
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and not ignored_parts.intersection(path.relative_to(root).parts)
    }
