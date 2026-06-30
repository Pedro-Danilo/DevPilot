from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.connectors import ConnectorSandboxQualityGate
from devpilot_core.quality import QualityGate, QualityGateOptions
from devpilot_core.quality.gate import QualitySubgate

ROOT = Path(__file__).resolve().parents[1]


def test_post_h_018_e_connector_sandbox_quality_gate_passes_without_network_or_write() -> None:
    result = ConnectorSandboxQualityGate(ROOT).run()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    assert result.command == "quality connector-sandbox"
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-018-E"
    assert summary["quality_gate_subgate"] == "connector-sandbox"
    assert summary["exposure_ok"] is True
    assert summary["sandbox_replay_ok"] is True
    assert summary["connectors_total"] == 4
    assert summary["write_future_blocked_total"] == summary["connectors_total"]
    assert summary["policy_coverage_complete"] is True
    assert summary["all_high_risk_rbac_evaluated"] is True
    assert summary["all_side_effecting_future_write_blocked"] is True
    assert summary["policy_engine_invoked"] is True
    assert summary["connector_binding_checked"] is True
    assert summary["connector_binding_passed"] is True
    assert summary["fixtures_total"] == 1
    assert summary["fixtures_passed"] == 1
    assert summary["redaction_passed"] is True
    assert summary["deterministic_replay"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["connector_write_used"] is False
    assert summary["remote_execution_used"] is False
    assert summary["plugin_execution_used"] is False
    assert summary["secrets_included"] is False
    assert any(finding.id == "CONNECTOR_SANDBOX_GATE_PASS" for finding in result.findings)


def test_post_h_018_e_hardening_profile_registers_connector_sandbox_subgate() -> None:
    gate = QualityGate(ROOT, options=QualityGateOptions(profile="hardening"))
    subgates = {subgate.id: subgate for subgate in gate._subgates()}

    assert "connector-sandbox" in subgates
    assert subgates["connector-sandbox"].critical is True
    result = subgates["connector-sandbox"].runner()
    assert result.ok, result.to_dict()
    assert result.data["summary"]["quality_gate_subgate"] == "connector-sandbox"


def test_post_h_018_e_quality_gate_cli_json_can_report_connector_sandbox_subgate(monkeypatch, capsys) -> None:
    # Keep the unit contract focal: the full hardening profile is validated as a
    # command in release evidence, while this CLI test executes only the new
    # POST-H-018-E subgate through the same JSON output path.
    def only_connector_sandbox(self: QualityGate) -> list[QualitySubgate]:
        return [
            QualitySubgate(
                "connector-sandbox",
                "POST-H-018 connector sandbox deny-write, replay, redaction and Policy/Approval/RBAC gate.",
                self._connector_sandbox,
            )
        ]

    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(QualityGate, "_subgates", only_connector_sandbox)
    exit_code = cli.main(["quality-gate", "run", "--profile", "hardening", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0, payload
    assert payload["command"] == "quality-gate run"
    assert payload["ok"] is True
    subgates = {item["id"]: item for item in payload["data"]["subgates"]}
    assert "connector-sandbox" in subgates
    assert subgates["connector-sandbox"]["ok"] is True
    assert subgates["connector-sandbox"]["summary"]["network_used"] is False
    assert subgates["connector-sandbox"]["summary"]["external_api_used"] is False
    assert subgates["connector-sandbox"]["summary"]["connector_write_used"] is False
    assert subgates["connector-sandbox"]["summary"]["write_future_blocked_total"] == 4
