from __future__ import annotations

import json
import zipfile
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode, Severity
from devpilot_core.compliance import CompliancePackRegistry, CompliancePackRunner, ComplianceRegistryOptions, ComplianceRunOptions
from devpilot_core.evals import EvalRunner

ROOT = Path(__file__).resolve().parents[1]


def test_compliance_registry_validates_baseline_pack() -> None:
    result = CompliancePackRegistry(ROOT).validate()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["packs_total"] == 1
    assert summary["pack_ids"] == ["baseline"]
    assert summary["schema_valid"] is True
    assert summary["policy_engine_required"] is True
    assert summary["declared_checks_only"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False


def test_compliance_list_cli_json_is_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["compliance", "list", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "compliance list"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["packs_total"] == 1
    assert payload["data"]["packs"][0]["pack_id"] == "baseline"


def test_compliance_run_baseline_uses_declared_gates_and_policy_engine() -> None:
    result = CompliancePackRunner(ROOT).run(ComplianceRunOptions(pack="baseline"))

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["pack_id"] == "baseline"
    assert summary["checks_total"] == 5
    assert summary["checks_passed"] == 5
    assert summary["checks_failed"] == 0
    assert summary["gaps_total"] == 0
    assert summary["policy_engine_used"] is True
    assert summary["policy_engine_replaced"] is False
    assert summary["declared_checks_only"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert {check["runner"] for check in result.data["checks"]} == {
        "schema.registry.list",
        "readiness.strict",
        "standards.status",
        "miasi.validate.all",
        "validation.gateway.all",
    }


def test_compliance_run_cli_json_and_report_are_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["compliance", "run", "--pack", "baseline", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "compliance run"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["pack_id"] == "baseline"
    assert payload["data"]["summary"]["gaps_total"] == 0
    reports = payload["data"].get("reports")
    assert reports["json"] == "outputs/reports/compliance_run_baseline.json"
    assert reports["markdown"] == "outputs/reports/compliance_run_baseline.md"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()


def test_compliance_registry_blocks_undeclared_runner(tmp_path: Path) -> None:
    project = tmp_path
    registry_dir = project / ".devpilot" / "compliance"
    registry_dir.mkdir(parents=True)
    schema_dir = project / "docs" / "schemas"
    schema_dir.mkdir(parents=True)
    miasi_dir = project / ".devpilot" / "miasi"
    miasi_dir.mkdir(parents=True)

    (schema_dir / "schema_catalog.json").write_text(json.dumps({"schemas": []}), encoding="utf-8")
    (miasi_dir / "policy_matrix.json").write_text(json.dumps({"rules": []}), encoding="utf-8")
    (schema_dir / "compliance_pack.schema.json").write_text((ROOT / "docs/schemas/compliance_pack.schema.json").read_text(encoding="utf-8"), encoding="utf-8")
    (registry_dir / "packs.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "created_by": "FUNC-SPRINT-97",
                "updated_at": "2026-06-19",
                "title": "Unsafe synthetic registry",
                "status": "implemented-initial",
                "description": "Synthetic invalid registry.",
                "security": {
                    "local_first": True,
                    "policy_engine_required": True,
                    "packs_declarative_only": True,
                    "declared_actions_only": True,
                    "arbitrary_command_execution_allowed": False,
                    "shell_allowed": False,
                    "network_used": False,
                    "external_api_used": False,
                    "cloud_export_used": False,
                    "mutations_performed": False,
                    "source_mutations_performed": False,
                    "secrets_read": False,
                    "raw_secret_output_allowed": False,
                },
                "packs": [
                    {
                        "pack_id": "unsafe",
                        "title": "Unsafe",
                        "version": "1.0.0",
                        "status": "implemented-initial",
                        "profile": "unsafe",
                        "description": "Uses shell.",
                        "execution_allowed": False,
                        "policy_engine_required": True,
                        "report_required": True,
                        "policy_pack_ids": [],
                        "policy_rule_ids": [],
                        "schema_ids": [],
                        "required_reports": [],
                        "checks": [
                            {"check_id": "bad", "runner": "shell", "required": True, "description": "bad"}
                        ],
                        "notes": ["bad"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = CompliancePackRegistry(project, options=ComplianceRegistryOptions()).validate()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "COMPLIANCE_PACK_RUNNER_UNDECLARED_BLOCK" for finding in result.findings)
    assert any(finding.severity == Severity.BLOCK for finding in result.findings)


def test_compliance_pack_integrity_eval_suite_passes() -> None:
    result = EvalRunner(ROOT).run(suite="compliance-pack-integrity")

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["suite_id"] == "compliance-pack-integrity"
    assert result.data["summary"]["cases_total"] == 4
    assert result.data["summary"]["cases_failed"] == 0
    assert result.data["summary"]["safety_score"] >= 90.0
    assert result.data["summary"]["false_negatives"] == 0
    assert result.data["summary"]["network_used"] is False
    assert result.data["summary"]["external_api_used"] is False
