from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.remote import RemoteReadinessReportOptions, RemoteReadinessReporter

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_remote_readiness_report_schema_is_registered_and_blocks_enablement_flags() -> None:
    catalog = _read_json("docs/schemas/schema_catalog.json")
    schema = _read_json("docs/schemas/remote_readiness_report.schema.json")

    assert any(entry["schema_id"] == "SCHEMA-DEVPL-REMOTE-READINESS-REPORT-V1" for entry in catalog["schemas"])
    assert schema["properties"]["remote_runner_enabled"]["const"] is False
    assert schema["properties"]["remote_execution_used"]["const"] is False
    assert schema["properties"]["network_used"]["const"] is False
    assert schema["properties"]["external_api_used"]["const"] is False
    assert schema["properties"]["credentials_required"]["const"] is False
    assert schema["properties"]["secrets_read"]["const"] is False
    assert schema["properties"]["future_adr_required"]["const"] is True
    assert schema["properties"]["readiness_level"]["const"] == "remote-design-only"


def test_remote_readiness_report_builds_read_only_design_evidence() -> None:
    result = RemoteReadinessReporter(ROOT).build(write_report=False)

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-021-C"
    assert summary["readiness_level"] == "remote-design-only"
    assert summary["decision_status"] == "design-only"
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
    assert summary["requires_future_adr"] is True
    assert summary["reports_written"] is False
    assert summary["blocking_findings_total"] == 0

    report = result.data["report"]
    assert report["schema_id"] == "SCHEMA-DEVPL-REMOTE-READINESS-REPORT-V1"
    assert report["future_adr_required"] is True
    assert report["readiness_level"] == "remote-design-only"
    assert "secure_transport_design" in report["required_before_enablement"]
    assert "approval_rbac_hardening" in report["required_before_enablement"]
    assert "remote_execution_quality_gate" in report["required_before_enablement"]
    assert report["safety"]["read_only"] is True
    assert report["safety"]["remote_execution_enabled"] is False
    assert result.data["reports"] == {}


def test_remote_readiness_cli_json_and_write_report(monkeypatch, capsys, tmp_path: Path) -> None:
    monkeypatch.chdir(ROOT)
    output_json = tmp_path / "remote_readiness_report.json"
    output_markdown = tmp_path / "remote_readiness_report.md"

    exit_code = cli.main(
        [
            "remote",
            "runner",
            "readiness",
            "--json",
            "--write-report",
            "--output-json",
            str(output_json),
            "--output-markdown",
            str(output_markdown),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "remote runner readiness"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["remote_runner_enabled"] is False
    assert payload["data"]["summary"]["remote_execution_used"] is False
    assert payload["data"]["summary"]["network_used"] is False
    assert payload["data"]["summary"]["external_api_used"] is False
    assert payload["data"]["reports"]["json"] == str(output_json)
    assert payload["data"]["reports"]["markdown"] == str(output_markdown)
    assert output_json.exists()
    assert output_markdown.exists()


def test_remote_readiness_reporter_rejects_directory_output(tmp_path: Path) -> None:
    result = RemoteReadinessReporter(
        ROOT,
        options=RemoteReadinessReportOptions(output_json=str(tmp_path), output_markdown=str(tmp_path / "report.md")),
    ).build(write_report=True)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "REMOTE_READINESS_REPORT_OUTPUT_BLOCKED" for finding in result.findings)


def test_remote_readiness_runtime_does_not_import_execution_primitives() -> None:
    readiness_source = (ROOT / "src/devpilot_core/remote/readiness.py").read_text(encoding="utf-8")
    reports_source = (ROOT / "src/devpilot_core/remote/reports.py").read_text(encoding="utf-8")
    combined = readiness_source + reports_source

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
        assert token not in combined
