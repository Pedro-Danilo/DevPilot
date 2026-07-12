from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.sensitive_capabilities import SensitiveCapabilityAdrGate

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_post_h_034_sensitive_capability_decision_gate_covers_all_capabilities() -> None:
    result = SensitiveCapabilityAdrGate(ROOT).run()
    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["subgates_total"] == 5
    assert summary["subgates_passed"] == 5
    assert summary["connector_write_gate_ok"] is True
    assert summary["plugin_execution_gate_ok"] is True
    assert summary["remote_execution_adr3_gate_ok"] is True
    assert summary["multiuser_auth_gate_ok"] is True
    assert summary["enterprise_saas_boundary_gate_ok"] is True

    matrix = _read_json(".devpilot/sensitive_capabilities/capability_decision_matrix.json")
    capabilities = {item["capability_id"]: item for item in matrix["capabilities"]}
    assert set(capabilities) == {
        "connector.write",
        "plugin.execution",
        "remote.execution",
        "multiuser.auth",
        "enterprise.saas",
    }
    assert all(item["decision_state"] == "continue-blocked" for item in capabilities.values())
    assert all(item["runtime_enabled"] is False for item in capabilities.values())
    assert matrix["summary"]["pending_adrs_total"] == 0


def test_post_h_034_sensitive_capability_decision_gate_preserves_global_no_go_gates() -> None:
    matrix = _read_json(".devpilot/sensitive_capabilities/capability_decision_matrix.json")
    no_go = matrix["global_no_go_gates"]
    assert no_go["connector_write_enabled"] is False
    assert no_go["plugin_execution_enabled"] is False
    assert no_go["remote_execution_enabled"] is False
    assert no_go["production_multiuser"] is False
    assert no_go["enterprise_ready"] is False
    assert no_go["saas_ready"] is False
    assert no_go["compliance_certified"] is False
