from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.quality import QualityGate, QualityGateOptions
from devpilot_core.remote import RemoteReadinessQualityGate, RemoteReadinessQualityGateOptions

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def test_post_h_021_d_remote_readiness_quality_gate_passes_design_only() -> None:
    result = RemoteReadinessQualityGate(ROOT).run()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-021-D"
    assert summary["quality_gate_subgate"] == "remote-readiness-design-only"
    assert summary["readiness_report_ok"] is True
    assert summary["readiness_level"] == "remote-design-only"
    assert summary["decision_status"] == "design-only"
    assert summary["schema_valid"] is True
    assert summary["runner_registry_valid"] is True
    assert summary["requires_future_adr"] is True
    assert summary["future_adr_required"] is True
    assert summary["remote_enterprise_eval_signal_present"] is True
    assert summary["remote_enterprise_suite_id"] == "remote-enterprise"
    assert summary["remote_enterprise_cases_total"] >= 4
    assert summary["remote_execution_allowed"] is False
    assert summary["remote_runner_enabled"] is False
    assert summary["execution_allowed"] is False
    assert summary["remote_execution_used"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["credentials_required"] is False
    assert summary["secrets_read"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False
    assert summary["connector_write_enabled"] is False
    assert summary["plugin_execution_enabled"] is False
    assert summary["reports_written"] is False
    assert summary["blocking_findings_total"] == 0


def test_post_h_021_d_quality_gate_hardening_profile_includes_remote_subgate() -> None:
    gate = QualityGate(ROOT, options=QualityGateOptions(profile="hardening"))
    subgate_ids = [subgate.id for subgate in gate._subgates()]

    assert "remote-readiness-design-only" in subgate_ids
    assert subgate_ids.index("compliance-mapping-pack") < subgate_ids.index("remote-readiness-design-only")
    subgate = next(item for item in gate._subgates() if item.id == "remote-readiness-design-only")
    assert subgate.critical is True


def test_post_h_021_d_remote_quality_gate_blocks_enabled_criteria(tmp_path: Path) -> None:
    criteria = copy.deepcopy(_read_json(".devpilot/remote/remote_readiness_criteria.json"))
    criteria["remote_execution_allowed"] = True
    criteria["no_go_gates"]["remote_runner_enabled"] = True
    criteria_path = tmp_path / "remote_readiness_criteria.json"
    _write_json(criteria_path, criteria)

    result = RemoteReadinessQualityGate(
        ROOT,
        options=RemoteReadinessQualityGateOptions(criteria_path=str(criteria_path)),
    ).run()

    assert result.ok is False
    assert result.exit_code in {ExitCode.BLOCK, ExitCode.FAIL, ExitCode.ERROR}
    assert result.data["summary"]["remote_execution_allowed"] is True
    assert result.data["summary"]["blocking_findings_total"] > 0
    assert any(
        finding.id in {"REMOTE_READINESS_UNSAFE_FLAG_BLOCKED", "REMOTE_READINESS_SCHEMA_OR_REGISTRY_BLOCKED"}
        or "REMOTE_READINESS" in finding.id
        for finding in result.findings
    )


def test_post_h_021_d_remote_quality_gate_blocks_unsafe_eval_signal(tmp_path: Path) -> None:
    fixture = copy.deepcopy(_read_json("evals/fixtures/remote_enterprise_eval_cases.json"))
    fixture["network_used"] = True
    fixture_path = tmp_path / "remote_enterprise_eval_cases.json"
    _write_json(fixture_path, fixture)

    result = RemoteReadinessQualityGate(
        ROOT,
        options=RemoteReadinessQualityGateOptions(remote_enterprise_fixture_path=str(fixture_path)),
    ).run()

    assert result.ok is False
    assert result.data["summary"]["network_used"] is True
    assert any(finding.id == "REMOTE_ENTERPRISE_EVAL_UNSAFE_FLAG" for finding in result.findings)


def test_post_h_021_d_remote_quality_gate_source_has_no_transport_or_execution_primitives() -> None:
    source = (ROOT / "src/devpilot_core/remote/quality_gate.py").read_text(encoding="utf-8")
    forbidden_tokens = [
        "subprocess",
        "socket",
        "paramiko",
        "requests",
        "httpx",
        "urllib.request",
        "importlib",
        "os.system",
    ]
    for token in forbidden_tokens:
        assert token not in source
