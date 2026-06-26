from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core import cli
from devpilot_core.observability import ObservabilityRedactedExporter, ObservabilityRedactedExportOptions
from devpilot_core.schemas import SchemaRegistry, SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _make_export_workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    (root / ".devpilot" / "observability").mkdir(parents=True)
    (root / ".devpilot" / "agent_sessions").mkdir(parents=True)
    (root / "outputs" / "traces").mkdir(parents=True)
    (root / "outputs" / "reports").mkdir(parents=True)
    shutil.copy(ROOT / ".devpilot" / "observability" / "retention_policy.json", root / ".devpilot" / "observability" / "retention_policy.json")
    (root / "outputs" / "traces" / "events.jsonl").write_text(
        json.dumps(
            {
                "event_type": "model.call",
                "command": "model generate",
                "status": "ok",
                "ok": True,
                "exit_code": 0,
                "level": "info",
                "raw_prompt": "secret prompt sk-proj-1234567890ABCDEFG",
                "raw_output": "model output should never be exported",
                "metadata": {"api_key": "sk-proj-ABCDEFG1234567890"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (root / ".devpilot" / "agent_sessions" / "session.json").write_text(
        json.dumps(
            {
                "session_id": "s1",
                "prompt": "raw session prompt",
                "raw_outputs": ["raw session output"],
                "token": "sk-proj-ABCDEFG1234567890",
            }
        ),
        encoding="utf-8",
    )
    (root / "outputs" / "reports" / "report.md").write_text("# Report\npassword=sk-proj-ABCDEFG1234567890\n", encoding="utf-8")
    return root


def test_observability_redacted_export_schema_is_registered() -> None:
    catalog = read_json("docs/schemas/schema_catalog.json")
    entries = {item["schema_id"]: item for item in catalog["schemas"]}

    assert "SCHEMA-DEVPL-OBSERVABILITY-REDACTED-EXPORT-V1" in entries
    entry = entries["SCHEMA-DEVPL-OBSERVABILITY-REDACTED-EXPORT-V1"]
    assert entry["path"] == "docs/schemas/observability_redacted_export.schema.json"
    assert entry["contract"] == "ObservabilityRedactedExport"
    assert entry["sprint"] == "POST-H-010-D"
    assert entry["no_remote_execution_enabled"] is True
    assert (ROOT / entry["path"]).exists()

    registry_result = SchemaRegistry(ROOT).list()
    assert registry_result.ok, registry_result.to_dict()
    assert "SCHEMA-DEVPL-OBSERVABILITY-REDACTED-EXPORT-V1" in {item["schema_id"] for item in registry_result.data["schemas"]}


def test_observability_redacted_export_builds_without_raw_payloads(tmp_path: Path) -> None:
    root = _make_export_workspace(tmp_path)

    result = ObservabilityRedactedExporter(root).run()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    export = result.data["export"]
    rendered = json.dumps(export, ensure_ascii=False, sort_keys=True)

    assert result.command == "observability export"
    assert summary["created_by"] == "POST-H-010-D"
    assert summary["redacted"] is True
    assert summary["redaction_applied"] is True
    assert summary["events_exported_total"] == 1
    assert summary["raw_payload_fields_removed_total"] >= 2
    assert summary["raw_prompts_exported"] is False
    assert summary["raw_outputs_exported"] is False
    assert summary["secrets_exported"] is False
    assert summary["sqlite_raw_exported"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert export["safety"]["metadata_only_for_sqlite"] is True
    assert export["safety"]["metadata_only_for_agent_sessions"] is True
    assert "sk-proj-1234567890ABCDEFG" not in rendered
    assert "sk-proj-ABCDEFG1234567890" not in rendered
    assert "secret prompt" not in rendered
    assert "model output should never be exported" not in rendered


def test_observability_redacted_export_write_report_validates_schema(tmp_path: Path) -> None:
    root = _make_export_workspace(tmp_path)
    result = ObservabilityRedactedExporter(root, ObservabilityRedactedExportOptions(write_report=True)).run()

    assert result.ok, result.to_dict()
    reports = result.data["reports"]
    assert reports["json"] == "outputs/reports/observability_redacted_export.json"
    assert reports["markdown"] == "outputs/reports/observability_redacted_export.md"
    assert reports["audit_export_dir"] == "outputs/audit_exports/observability_redacted_export"
    assert (root / reports["json"]).exists()
    assert (root / reports["markdown"]).exists()
    assert (root / reports["audit_export_dir"] / "observability_redacted_summary.json").exists()
    assert (root / reports["audit_export_dir"] / "checksums.sha256").exists()

    validation = SchemaValidator(ROOT).validate_payload(
        schema="ObservabilityRedactedExport",
        payload=json.loads((root / reports["json"]).read_text(encoding="utf-8")),
        instance_label="observability_redacted_export.synthetic.json",
    )
    assert validation.ok, validation.to_dict()

    exported_text = "\n".join(path.read_text(encoding="utf-8") for path in (root / reports["audit_export_dir"]).rglob("*") if path.is_file())
    assert "sk-proj-1234567890ABCDEFG" not in exported_text
    assert "sk-proj-ABCDEFG1234567890" not in exported_text
    assert "raw session prompt" not in exported_text
    assert "raw session output" not in exported_text


def test_observability_export_cli_requires_redacted(monkeypatch, tmp_path: Path, capsys) -> None:
    root = _make_export_workspace(tmp_path)
    monkeypatch.chdir(root)

    exit_code = cli.main(["observability", "export", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert payload["ok"] is False
    assert payload["data"]["summary"]["redaction_applied"] is False
    assert any(item["id"] == "OBSERVABILITY_EXPORT_REDACTION_REQUIRED" for item in payload["findings"])


def test_observability_export_cli_json_and_write_report(monkeypatch, tmp_path: Path, capsys) -> None:
    root = _make_export_workspace(tmp_path)
    monkeypatch.chdir(root)

    exit_code = cli.main(["observability", "export", "--redacted", "--json", "--write-report", "--limit", "10"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "observability export"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["created_by"] == "POST-H-010-D"
    assert payload["data"]["summary"]["redaction_applied"] is True
    assert payload["data"]["summary"]["raw_prompts_exported"] is False
    assert payload["data"]["summary"]["network_used"] is False
    assert payload["data"]["reports"]["json"] == "outputs/reports/observability_redacted_export.json"
