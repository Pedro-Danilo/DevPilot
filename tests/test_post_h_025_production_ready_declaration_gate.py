from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.application import ApplicationService
from devpilot_core.cli_models import ExitCode
from devpilot_core.industrial import ProductionReadyDeclarationGate, ProductionReadyDeclarationGateOptions
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def test_production_ready_declaration_gate_passes_current_repo_without_source_mutation() -> None:
    before = _tracked_snapshot(ROOT)

    result = ProductionReadyDeclarationGate(ROOT).check()

    after = _tracked_snapshot(ROOT)
    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    assert before == after
    summary = result.data["summary"]
    report = result.data["report"]
    assert summary["decision"] == "PASS"
    assert summary["blocking_gaps_total"] == 0
    assert summary["production_ready_local_declared"] is True
    assert summary["formal_audit_declaration_pending"] is True
    assert summary["reports_written"] is False
    assert report["claims"] == {
        "production_ready_local": True,
        "enterprise_ready": False,
        "remote_ready": False,
        "compliance_certified": False,
        "saas_ready": False,
    }
    assert report["decision"] == "PASS"
    assert report["blocking_gaps_total"] == 0
    assert report["no_go_gates_passed"] is True
    validation = SchemaValidator(ROOT).validate_payload(
        schema="ProductionReadyLocalReport",
        payload=report,
        instance_label="in-memory:post-h-025-c-report",
    )
    assert validation.ok, validation.to_dict()


def test_production_ready_declaration_gate_blocks_missing_required_evidence(tmp_path: Path) -> None:
    criteria_path = tmp_path / ".devpilot/production/production_ready_local_criteria.json"
    criteria_path.parent.mkdir(parents=True)
    criteria_path.write_text(json.dumps(_minimal_criteria(), indent=2), encoding="utf-8")

    result = ProductionReadyDeclarationGate(
        tmp_path,
        options=ProductionReadyDeclarationGateOptions(
            criteria_path=".devpilot/production/production_ready_local_criteria.json"
        ),
    ).check()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    report = result.data["report"]
    assert report["decision"] == "BLOCK"
    assert report["claims"]["production_ready_local"] is False
    assert report["blocking_gaps_total"] == 1
    assert report["gaps"][0]["severity"] == "block"
    assert report["gaps"][0]["action"] == "Generate or restore the mapped local evidence artifact before final declaration."
    validation = SchemaValidator(ROOT).validate_payload(
        schema="ProductionReadyLocalReport",
        payload=report,
        instance_label="in-memory:post-h-025-c-block-report",
    )
    assert validation.ok, validation.to_dict()


def test_production_ready_declaration_gate_writes_schema_valid_reports_when_requested() -> None:
    output_json = "outputs/test_post_h_025_c/production_ready_local_report.json"
    output_markdown = "outputs/test_post_h_025_c/production_ready_local_report.md"

    result = ProductionReadyDeclarationGate(
        ROOT,
        options=ProductionReadyDeclarationGateOptions(
            write_report=True,
            output_json=output_json,
            output_markdown=output_markdown,
        ),
    ).check()

    assert result.ok is True, result.to_dict()
    assert result.data["summary"]["reports_written"] is True
    assert result.data["reports"] == {"json": output_json, "markdown": output_markdown}
    assert (ROOT / output_json).exists()
    assert (ROOT / output_markdown).exists()
    validation = SchemaValidator(ROOT).validate(
        schema="ProductionReadyLocalReport",
        instance=output_json,
    )
    assert validation.ok, validation.to_dict()
    markdown = (ROOT / output_markdown).read_text(encoding="utf-8")
    assert "Production-ready-local gate report" in markdown
    assert "Formal audit declaration pending" in markdown


def test_production_ready_declaration_gate_cli_and_application_service_are_synchronized(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    api_result = ApplicationService(ROOT).production_ready_local_gate()
    exit_code = cli.main(["industrial-readiness", "production-ready-local", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert api_result.ok is True
    assert exit_code == 0
    assert payload["command"] == "industrial-readiness production-ready-local"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["decision"] == api_result.data["summary"]["decision"]
    assert payload["data"]["summary"]["reports_written"] is False
    assert payload["data"]["report"]["claims"]["enterprise_ready"] is False


def test_production_ready_declaration_gate_artifacts_are_synchronized() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-025_production_ready_declaration_gate.md").read_text(encoding="utf-8")
    tcr = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")

    assert "POST-H-025-C — Declaration gate CLI/API" in readme
    assert "POST-H-025-C — Declaration gate CLI/API" in runbook
    assert 'current_micro_sprint: "POST-H-025-D"' in backlog
    assert 'next_micro_sprint: "POST-H-025-E"' in backlog
    assert "post-h-025-production-ready-declaration-gate" in tcr
    assert "post-h-025-production-ready-declaration-gate" in tcr_v2
    assert (ROOT / "docs/audits/post_h_025_c_declaration_gate_report.md").exists()
    assert (ROOT / "docs/post_h_025_c_manifest.json").exists()


def _minimal_criteria() -> dict:
    return {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-PRODUCTION-READY-LOCAL-CRITERIA-V1",
        "criteria_id": "test-criteria",
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
                        "validation_command": "not executed by POST-H-025-C",
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
