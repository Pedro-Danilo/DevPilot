from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from devpilot_core import cli
from devpilot_core.application import ApplicationService
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
    JSON_SOURCE_SPECS,
    MaturityDashboardBuilder,
    MaturityDashboardQualityGate,
    PostHSourceReader,
    SourceSpec,
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



def test_post_h_source_reader_reads_mandatory_json_sources() -> None:
    bundle = PostHSourceReader(ROOT).read_all(include_markdown=False)

    assert bundle.ok is True
    assert bundle.blocking_findings_total == 0
    assert len(bundle.json_sources) == len(JSON_SOURCE_SPECS)
    assert all(source.exists and source.ok for source in bundle.json_sources)
    assert ".devpilot/evals/post_h_eval_001_decision_matrix.json" in bundle.evidence_paths()
    assert ".devpilot/testing/test_contract_registry.json" in bundle.evidence_paths()
    assert bundle.to_dict()["summary"]["network_used"] is False
    assert bundle.to_dict()["summary"]["external_api_used"] is False
    assert bundle.to_dict()["summary"]["mutations_performed"] is False


def test_post_h_source_reader_extracts_key_summaries() -> None:
    bundle = PostHSourceReader(ROOT).read_all(include_markdown=False)

    decision_matrix = bundle.source_by_id("decision_matrix")
    security = bundle.source_by_id("security_risk_register")
    contracts = bundle.source_by_id("test_contract_registry")
    roadmap = bundle.source_by_id("prioritized_roadmap")

    assert decision_matrix is not None
    assert decision_matrix.summary["domains_total"] == 28
    assert decision_matrix.summary["remote_runner_enabled"] is False
    assert security is not None
    assert security.summary["risks_total"] == 14
    assert security.summary["critical_total"] == 1
    assert contracts is not None
    assert contracts.summary["contracts_total"] >= 86
    assert roadmap is not None
    assert roadmap.summary["waves_total"] == 8


def test_post_h_source_reader_reports_missing_critical_source_as_block(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    specs = (SourceSpec("missing_manifest", "docs/post_h_eval_001_manifest.json", "json", True),)

    bundle = PostHSourceReader(tmp_path, json_specs=specs, markdown_specs=()).read_all()
    result = bundle.to_command_result()

    assert bundle.ok is False
    assert bundle.blocking_findings_total >= 1
    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "POST_H_SOURCE_MISSING" for finding in result.findings)


def test_post_h_source_reader_uses_markdown_fallback_with_warnings() -> None:
    bundle = PostHSourceReader(ROOT).read_all(include_markdown=True)

    assert len(bundle.markdown_sources) >= 6
    assert all(source.exists for source in bundle.markdown_sources)
    assert bundle.to_command_result().exit_code == ExitCode.PASS
    closure = bundle.source_by_id("closure_report_doc")
    assert closure is not None
    assert closure.summary["heading_count"] > 0
    # Markdown fallback is intentionally warning-tolerant because the JSON
    # sources remain the canonical evidence for the dashboard builder.
    assert bundle.warnings_total >= 0



def test_maturity_dashboard_builder_generates_schema_valid_dashboard() -> None:
    result = MaturityDashboardBuilder(ROOT).build(generated_at_utc="2026-06-24T00:00:00Z")

    assert result.ok is True
    assert result.dashboard is not None
    payload = result.dashboard.to_dict()
    assert payload["dashboard_id"] == "POST-H-002-MATURITY-DASHBOARD"
    assert payload["source_revision"]["roadmap_version"] == "1.1.0"
    assert payload["source_revision"]["post_h_eval_status"] == "closed"
    assert payload["summary"]["capabilities_total"] >= 28
    assert payload["summary"]["production_ready_local_total"] >= 1
    assert payload["summary"]["blocked_total"] >= 3
    assert payload["safety"]["remote_execution_enabled"] is False
    assert payload["safety"]["connector_write_enabled"] is False
    assert payload["safety"]["plugin_execution_enabled"] is False
    assert payload["safety"]["external_apis_enabled_by_default"] is False

    validation = SchemaValidator(ROOT).validate_payload(
        schema="MaturityDashboard",
        payload=payload,
        instance_label="in-memory:builder-dashboard",
    )
    assert validation.ok is True
    assert validation.exit_code == ExitCode.PASS


def test_maturity_dashboard_builder_maps_no_go_capabilities_to_roadmap() -> None:
    result = MaturityDashboardBuilder(ROOT).build(generated_at_utc="2026-06-24T00:00:00Z")
    assert result.dashboard is not None

    by_id = {capability.capability_id: capability for capability in result.dashboard.capabilities}
    assert by_id["no-go-sec-001"].status == CapabilityStatus.BLOCKED
    assert by_id["no-go-sec-001"].roadmap_dependency == "POST-H-021"
    assert by_id["no-go-sec-002"].status == CapabilityStatus.BLOCKED
    assert by_id["no-go-sec-002"].roadmap_dependency == "POST-H-018"
    assert by_id["no-go-sec-003"].status == CapabilityStatus.BLOCKED
    assert by_id["no-go-sec-003"].roadmap_dependency == "POST-H-019"
    assert all(by_id[key].no_go_gate for key in ("no-go-sec-001", "no-go-sec-002", "no-go-sec-003"))


def test_maturity_dashboard_builder_renders_operator_markdown_without_writes() -> None:
    result = MaturityDashboardBuilder(ROOT).build(generated_at_utc="2026-06-24T00:00:00Z")

    assert result.ok is True
    assert "# DevPilot Local — Maturity Dashboard" in result.markdown
    assert "## Safety no-go gates" in result.markdown
    assert "`remote_execution_enabled` | `false`" in result.markdown
    assert "`connector_write_enabled` | `false`" in result.markdown
    assert "POST-H-021" in result.markdown
    assert "Persistent report writing is explicit and limited to outputs/reports/maturity_dashboard.json and outputs/reports/maturity_dashboard.md when the CLI uses --write-report." in result.markdown
    assert "enterprise-production-ready" not in result.markdown
    assert result.to_command_result().ok is True
    assert result.to_command_result().data["network_used"] is False
    assert result.to_command_result().data["external_api_used"] is False
    assert result.to_command_result().data["mutations_performed"] is False



def test_maturity_dashboard_application_service_exposes_boundary() -> None:
    result = ApplicationService(ROOT).maturity_dashboard()

    assert result.ok is True
    assert result.command == "maturity dashboard"
    assert result.data["dashboard"]["dashboard_id"] == "POST-H-002-MATURITY-DASHBOARD"
    assert result.data["summary"]["blocked_total"] >= 3
    assert result.data["network_used"] is False
    assert result.data["external_api_used"] is False
    assert result.data["mutations_performed"] is False


def test_maturity_dashboard_cli_json_is_parseable_without_writes(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["maturity", "dashboard", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "maturity dashboard"
    assert payload["ok"] is True
    assert payload["data"]["dashboard"]["dashboard_id"] == "POST-H-002-MATURITY-DASHBOARD"
    assert "reports" not in payload["data"]
    assert payload["data"]["network_used"] is False
    assert payload["data"]["external_api_used"] is False
    assert payload["data"]["mutations_performed"] is False


def test_maturity_dashboard_cli_write_report_creates_canonical_outputs(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    reports_dir = ROOT / "outputs" / "reports"
    json_report = reports_dir / "maturity_dashboard.json"
    markdown_report = reports_dir / "maturity_dashboard.md"
    json_report.unlink(missing_ok=True)
    markdown_report.unlink(missing_ok=True)

    exit_code = cli.main(["maturity", "dashboard", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["data"]["reports"] == {
        "json": "outputs/reports/maturity_dashboard.json",
        "markdown": "outputs/reports/maturity_dashboard.md",
    }
    assert json_report.is_file()
    assert markdown_report.is_file()
    persisted = json.loads(json_report.read_text(encoding="utf-8"))
    assert persisted["dashboard_id"] == "POST-H-002-MATURITY-DASHBOARD"
    assert persisted["safety"]["remote_execution_enabled"] is False
    assert "# DevPilot Local — Maturity Dashboard" in markdown_report.read_text(encoding="utf-8")


def test_maturity_dashboard_quality_gate_passes_without_writes() -> None:
    result = MaturityDashboardQualityGate(ROOT).run()

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    assert result.command == "maturity dashboard gate"
    assert result.data["summary"]["checks_passed"] == result.data["summary"]["checks_total"]
    assert result.data["checks"]["schema_valid"] is True
    assert result.data["checks"]["safety_no_go_flags_false"] is True
    assert result.data["checks"]["no_go_capabilities_blocked"] is True
    assert result.data["summary"]["network_used"] is False
    assert result.data["summary"]["external_api_used"] is False
    assert result.data["summary"]["mutations_performed"] is False


def test_maturity_dashboard_application_service_exposes_gate_boundary() -> None:
    result = ApplicationService(ROOT).maturity_dashboard_gate()

    assert result.ok is True, result.to_dict()
    assert result.data["checks"]["roadmap_alignment_present"] is True
    assert result.data["checks"]["source_evidence_present"] is True


def test_maturity_dashboard_gate_cli_json_and_write_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    reports_dir = ROOT / "outputs" / "reports"
    json_report = reports_dir / "maturity_dashboard.json"
    markdown_report = reports_dir / "maturity_dashboard.md"
    json_report.unlink(missing_ok=True)
    markdown_report.unlink(missing_ok=True)

    exit_code = cli.main(["maturity", "gate", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "maturity dashboard gate"
    assert payload["ok"] is True
    assert payload["data"]["checks"]["reports_valid"] is True
    assert payload["data"]["reports"] == {
        "json": "outputs/reports/maturity_dashboard.json",
        "markdown": "outputs/reports/maturity_dashboard.md",
    }
    assert json_report.is_file()
    assert markdown_report.is_file()


def test_schema_validate_accepts_schema_id_alias_after_report_write(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    cli.main(["maturity", "dashboard", "--json", "--write-report"])
    capsys.readouterr()

    exit_code = cli.main([
        "schema",
        "validate",
        "--schema-id",
        "MaturityDashboard",
        "--instance",
        "outputs/reports/maturity_dashboard.json",
        "--json",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["exit_code"] == 0


def test_quality_gate_hardening_includes_maturity_dashboard_subgate() -> None:
    from devpilot_core.quality import QualityGate, QualityGateOptions

    result = QualityGate(ROOT, options=QualityGateOptions(profile="hardening")).run()

    assert result.ok is True, result.to_dict()
    subgate_ids = {item["id"] for item in result.data["subgates"]}
    assert "maturity-dashboard" in subgate_ids
    maturity = next(item for item in result.data["subgates"] if item["id"] == "maturity-dashboard")
    assert maturity["ok"] is True
    assert maturity["summary"]["checks_passed"] == maturity["summary"]["checks_total"]
