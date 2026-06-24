from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.maturity import (
    CapabilityStatus,
    MaturityCapability,
    MaturityDashboard,
    MaturityLevel,
    RiskLevel,
    RoadmapDependency,
    SafetySignal,
    TestCoverageLevel,
)
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _sample_dashboard_payload() -> dict[str, object]:
    dashboard = MaturityDashboard(
        dashboard_id="POST-H-002-MATURITY-DASHBOARD",
        generated_at_utc="2026-06-23T00:00:00Z",
        roadmap_version="1.1.0",
        post_h_eval_status="closed",
        capabilities=[
            MaturityCapability(
                capability_id="schemas-contracts",
                name="Schemas y contratos",
                domain="contracts",
                status=CapabilityStatus.PRODUCTION_READY_LOCAL,
                maturity=MaturityLevel.ALTA_LOCAL,
                test_coverage=TestCoverageLevel.ALTA,
                risk=RiskLevel.BAJO,
                source_evidence=["docs/schemas/schema_catalog.json", "tests/test_schema_registry.py"],
            ),
            MaturityCapability(
                capability_id="remote-runner",
                name="Remote Runner",
                domain="remote",
                status=CapabilityStatus.BLOCKED,
                maturity=MaturityLevel.NO_HABILITADA,
                test_coverage=TestCoverageLevel.NA,
                risk=RiskLevel.CRITICO,
                source_evidence=["docs/backlogs/post_h_prioritized_roadmap.md"],
                roadmap_dependency="POST-H-021",
                no_go_gate=True,
            ),
            MaturityCapability(
                capability_id="plugin-execution",
                name="Plugin execution",
                domain="plugins",
                status=CapabilityStatus.STUB,
                maturity=MaturityLevel.BAJA,
                test_coverage=TestCoverageLevel.BAJA,
                risk=RiskLevel.ALTO,
                source_evidence=[".devpilot/plugins/plugin_registry.json"],
                roadmap_dependency="POST-H-019",
                no_go_gate=True,
            ),
        ],
        roadmap_alignment=[
            RoadmapDependency(milestone="POST-H-003", unblocks=["test-contract-registry-2"], priority="P0"),
            RoadmapDependency(milestone="POST-H-021", unblocks=["remote-readiness-design"], priority="P3"),
        ],
        safety=SafetySignal(),
    )
    return dashboard.to_dict()


def test_maturity_status_vocabulary_is_local_and_complete() -> None:
    values = {item.value for item in CapabilityStatus}

    assert "production-ready-local" in values
    assert "production-ready" not in values
    assert {"implemented", "implemented-initial", "experimental", "planned", "stub", "blocked"}.issubset(values)


def test_maturity_dashboard_model_computes_summary_and_safety_defaults() -> None:
    payload = _sample_dashboard_payload()

    assert payload["summary"]["capabilities_total"] == 3
    assert payload["summary"]["production_ready_local_total"] == 1
    assert payload["summary"]["stub_total"] == 1
    assert payload["summary"]["blocked_total"] == 1
    assert payload["summary"]["critical_risks_total"] == 1
    assert payload["summary"]["blocking_gaps_total"] == 2
    assert payload["safety"]["remote_execution_enabled"] is False
    assert payload["safety"]["connector_write_enabled"] is False
    assert payload["safety"]["plugin_execution_enabled"] is False
    assert payload["safety"]["external_apis_enabled_by_default"] is False


def test_maturity_dashboard_schema_validates_sample_payload() -> None:
    result = SchemaValidator(ROOT).validate_payload(
        schema="MaturityDashboard",
        payload=_sample_dashboard_payload(),
        instance_label="in-memory:maturity-dashboard-sample",
    )

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS


def test_maturity_dashboard_schema_blocks_generic_production_ready_claim() -> None:
    payload = deepcopy(_sample_dashboard_payload())
    payload["capabilities"][0]["status"] = "production-ready"
    result = SchemaValidator(ROOT).validate_payload(
        schema="MaturityDashboard",
        payload=payload,
        instance_label="in-memory:maturity-dashboard-overclaim",
    )

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "SCHEMA_VALIDATION_ERROR" for finding in result.findings)


def test_maturity_dashboard_schema_blocks_sensitive_capability_enablement() -> None:
    payload = deepcopy(_sample_dashboard_payload())
    payload["safety"]["remote_execution_enabled"] = True
    result = SchemaValidator(ROOT).validate_payload(
        schema="MaturityDashboard",
        payload=payload,
        instance_label="in-memory:maturity-dashboard-unsafe-safety",
    )

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "SCHEMA_VALIDATION_ERROR" for finding in result.findings)


def test_post_h_002_backlog_is_approved_for_execution() -> None:
    backlog = ROOT / "docs" / "backlogs" / "POST-H-002_maturity_dashboard_local.md"
    text = backlog.read_text(encoding="utf-8")

    assert 'status: "approved"' in text
    assert "POST-H-002-A — Modelo de madurez y schema" in text
    assert "POST-H-002-A" in text
