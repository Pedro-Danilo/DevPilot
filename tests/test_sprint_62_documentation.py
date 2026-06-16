from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str):
    return json.loads(_read(path))


def test_sprint_62_artifacts_exist_and_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_E_agentops_observabilidad.md")
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    manifest = _json("docs/functional_sprint_62_manifest.json")

    expected_paths = [
        "src/devpilot_core/observability/exporters/__init__.py",
        "src/devpilot_core/observability/exporters/otel_exporter.py",
        "tests/test_otel_exporter.py",
        "docs/audits/func_sprint_62_otel_exporter_audit.md",
        "docs/functional_sprint_62_manifest.json",
    ]
    for path in expected_paths:
        assert (ROOT / path).exists(), path

    assert "Último hito: `FUNC-SPRINT-69" in readme
    assert "Siguiente hito: `FUNC-SPRINT-70" in readme
    assert "## FUNC-SPRINT-62 — Exporter OpenTelemetry opcional y dry-run" in readme
    assert "## FUNC-SPRINT-62 — Operación de exporter OpenTelemetry dry-run" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-64"' in backlog
    assert 'last_completed_sprint: "FUNC-SPRINT-63"' in backlog
    assert 'next_sprint: "FUNC-SPRINT-64"' in backlog
    assert "## Estado de implementación Sprint 63" in backlog
    assert 'next_sprint: "FUNC-SPRINT-70"' in functional_backlog
    assert "## Transición posterior a FUNC-SPRINT-63" in functional_backlog
    assert manifest["sprint"] == "FUNC-SPRINT-62"
    assert manifest["status"] == "implemented"
    assert manifest["architectural_decision"]["required"] is False
    assert manifest["next_sprint"].startswith("FUNC-SPRINT-63")


def test_sprint_62_otel_exporter_contracts_are_explicit() -> None:
    exporter = _read("src/devpilot_core/observability/exporters/otel_exporter.py")
    cli = _read("src/devpilot_core/cli.py")
    audit = _read("docs/audits/func_sprint_62_otel_exporter_audit.md")
    tool_registry = _read(".devpilot/miasi/tool_registry.json")
    policy_matrix = _read(".devpilot/miasi/policy_matrix.json")

    for term in ["OTelDryRunExporter", "OTelExportOptions", "build_otel_like_payload", "resourceSpans", "resourceMetrics"]:
        assert term in exporter
    for term in ["telemetry_export_command", "telemetry", "export", "telemetry_export_otel_dry_run"]:
        assert term in cli
    assert "telemetry.export" in tool_registry
    assert "OTEL_EXPORT_DRY_RUN_ALLOW" in policy_matrix
    assert "OTEL_REMOTE_EXPORT_BLOCK" in policy_matrix
    assert "Veredicto: `PASS`" in audit
    assert "implemented-initial" in audit


def test_sprint_62_security_and_scope_boundaries_remain_closed() -> None:
    combined = "\n".join(
        _read(path)
        for path in [
            "README.md",
            "docs/05_operations/runbook.md",
            "docs/05_operations/observability_plan.md",
            "docs/06_miasi/observability_card.md",
            "docs/06_miasi/tool_card.md",
            "docs/devpilot_backlog_fase_E_agentops_observabilidad.md",
            "docs/functional_sprint_62_manifest.json",
            "src/devpilot_core/observability/exporters/otel_exporter.py",
        ]
    ).lower()

    assert "commandresult" in combined
    assert "outputs/reports" in combined
    assert "dry-run" in combined
    assert "opentelemetry" in combined
    assert "network_used" in combined
    assert "external_api_used" in combined
    assert "remote_telemetry_enabled" in combined
    assert "collector_required" in combined
    assert "telemetry.export" in combined
    assert "otel_remote_export_block" in combined
    for term in ["prompt", "completion", "stdout", "stderr", "secret"]:
        assert term in combined
    exporter_source = _read("src/devpilot_core/observability/exporters/otel_exporter.py").lower()
    for forbidden in ["requests", "urllib.request", "http.client", "socket", "opentelemetry.sdk"]:
        assert forbidden not in exporter_source
