from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli import main
from devpilot_core.cli_models import CommandResult, ExitCode
from devpilot_core.portfolio import OperatorDashboardReadyGate, OperatorDashboardReadyGateOptions
from devpilot_core.quality import QualityGate, QualityGateOptions
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def test_post_h_015_e_operator_dashboard_ready_gate_passes_and_writes_snapshot_report() -> None:
    result = OperatorDashboardReadyGate(
        ROOT,
        OperatorDashboardReadyGateOptions(generated_at_utc="2026-06-29T00:00:00Z", write_report=True),
    ).run()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-015-E"
    assert summary["quality_gate_subgate"] == "operator-dashboard-ready"
    assert summary["operator_dashboard_ready"] is True
    assert summary["snapshot_schema_ok"] is True
    assert summary["sections_total"] == 10
    assert summary["recommended_next_actions_total"] >= 1
    assert summary["remote_execution_enabled"] is False
    assert summary["connector_write_enabled"] is False
    assert summary["plugin_execution_enabled"] is False
    assert result.data["reports"] == {
        "json": "outputs/reports/operator_dashboard_snapshot.json",
        "markdown": "outputs/reports/operator_dashboard_snapshot.md",
    }

    schema_result = SchemaValidator(ROOT).validate(
        schema="OperatorDashboardSnapshot",
        instance=result.data["reports"]["json"],
    )
    assert schema_result.ok, schema_result.to_dict()


def test_post_h_015_e_quality_gate_hardening_and_industrial_include_operator_dashboard_ready() -> None:
    hardening_gate = QualityGate(ROOT, options=QualityGateOptions(profile="hardening"))
    hardening_subgates = hardening_gate._subgates()
    hardening_ids = [subgate.id for subgate in hardening_subgates]
    assert "operator-dashboard-ready" in hardening_ids

    industrial_gate = QualityGate(ROOT, options=QualityGateOptions(profile="industrial"))
    industrial_ids = [subgate.id for subgate in industrial_gate._subgates()]
    assert "operator-dashboard-ready" in industrial_ids

    subgate = next(item for item in hardening_subgates if item.id == "operator-dashboard-ready")
    assert subgate.critical is True
    result = subgate.runner()
    assert result.ok, result.to_dict()
    assert result.data["summary"]["quality_gate_subgate"] == "operator-dashboard-ready"


def test_post_h_015_e_operator_dashboard_cli_generates_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = main(["operator", "dashboard", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["command"] == "operator dashboard aggregate"
    assert payload["data"]["summary"]["reports_written"] is True
    assert payload["data"]["reports"]["json"] == "outputs/reports/operator_dashboard_snapshot.json"
    assert (ROOT / "outputs/reports/operator_dashboard_snapshot.md").exists()


def test_post_h_015_e_ready_gate_blocks_invalid_snapshot(monkeypatch) -> None:
    from devpilot_core.portfolio import operator_dashboard_gate as gate_module

    def fake_build(self) -> CommandResult:  # noqa: ANN001 - test monkeypatch signature mirrors bound method.
        return CommandResult(
            command="operator dashboard aggregate",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Synthetic invalid snapshot.",
            data={
                "summary": {"required_sources_missing_total": 0},
                "snapshot": {
                    "schema_version": "1.0",
                    "schema_id": "SCHEMA-DEVPL-OPERATOR-DASHBOARD-SNAPSHOT-V1",
                    "snapshot_id": "operator-dashboard-20260629T000000Z",
                    "workspace_id": "devpilot-local",
                    "created_by": "POST-H-015-B",
                    "status": "pass",
                    "generated_at_utc": "2026-06-29T00:00:00Z",
                    "local_first": True,
                    "read_only": True,
                    "dry_run": True,
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "source_mutations_performed": False,
                    "remote_execution_enabled": True,
                    "connector_write_enabled": False,
                    "plugin_execution_enabled": False,
                    "sections": {},
                    "recommended_next_actions": [],
                    "notes": ["invalid synthetic snapshot"],
                },
                "reports": {},
            },
            findings=[],
        )

    monkeypatch.setattr(gate_module.OperatorDashboardAggregator, "build", fake_build)

    result = OperatorDashboardReadyGate(ROOT).run()

    assert result.ok is False
    assert result.exit_code in {ExitCode.BLOCK, ExitCode.ERROR}
    assert result.data["summary"]["operator_dashboard_ready"] is False
    assert any(finding.id == "OPERATOR_DASHBOARD_READY_NO_GO_FLAG_INVALID" for finding in result.findings)


def test_post_h_015_e_docs_manifests_and_contracts_are_synchronized() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    local_runbook = (ROOT / "docs/05_operations/local_operator_dashboard_runbook.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-015_local_operator_dashboard.md").read_text(encoding="utf-8")
    tcr_v1 = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "docs/post_h_015_e_manifest.json").read_text(encoding="utf-8"))

    assert "POST-H-015-E — Quality gate y runbook operacional" in readme
    assert "POST-H-015-E — Quality gate y runbook operacional" in runbook
    assert "operator-dashboard-ready" in local_runbook
    assert 'current_micro_sprint: "POST-H-015-E"' in backlog
    assert 'implementation_status: "closed"' in backlog
    assert "post-h-015-operator-dashboard-ready-gate" in tcr_v1
    assert "post-h-015-operator-dashboard-ready-gate" in tcr_v2
    assert manifest["post_h_id"] == "POST-H-015"
    assert manifest["phase"] == "POST-H-015-E"
