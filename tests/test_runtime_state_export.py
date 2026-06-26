from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core import cli
from devpilot_core.runtime_state import RuntimeStateExportOptions, RuntimeStateExporter
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _make_runtime_export_root(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='devpilot-test'\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / ".devpilot" / "agent_sessions").mkdir(parents=True)
    (root / "outputs" / "traces").mkdir(parents=True)
    (root / "outputs" / "reports").mkdir(parents=True)
    (root / "outputs" / "evals").mkdir(parents=True)
    shutil.copy(ROOT / ".devpilot" / "runtime_state_policy.json", root / ".devpilot" / "runtime_state_policy.json")

    (root / "outputs" / "traces" / "events.jsonl").write_text(
        json.dumps(
            {
                "event": "model_call",
                "prompt_id": "safe.prompt.ref",
                "raw_prompt": "secret prompt sk-proj-1234567890ABCDEFG",
                "raw_output": "model output should not be exported",
                "metadata": {"api_key": "sk-proj-1234567890ABCDEFG"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (root / ".devpilot" / "agent_sessions" / "session.json").write_text(
        json.dumps(
            {
                "session_id": "s1",
                "prompt": "do not export this raw prompt",
                "raw_outputs": ["do not export"],
                "safe_metadata": {"prompt_id": "requirements.agent", "token": "sk-proj-ABCDEFG1234567890"},
            }
        ),
        encoding="utf-8",
    )
    (root / "outputs" / "reports" / "summary.md").write_text(
        "# Report\nraw_prompt: never export\nAPI_KEY=sk-proj-ABCDEFG1234567890\n",
        encoding="utf-8",
    )
    (root / ".devpilot" / "devpilot.db").write_bytes(b"SQLite format 3\x00secret raw db bytes")
    return root


def test_runtime_state_export_dry_run_plans_without_writing(tmp_path: Path) -> None:
    root = _make_runtime_export_root(tmp_path)

    result = RuntimeStateExporter(root).run()

    assert result.ok is True, result.to_dict()
    summary = result.data["summary"]
    manifest = result.data["manifest"]
    assert result.command == "runtime-state export"
    assert summary["created_by"] == "POST-H-008-D"
    assert summary["dry_run"] is True
    assert summary["execute_requested"] is False
    assert summary["planned_entries_total"] >= 4
    assert summary["files_exported_total"] == 0
    assert summary["raw_prompts_exported"] is False
    assert summary["raw_outputs_exported"] is False
    assert summary["secrets_exported"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert manifest["safety"]["no_raw_prompts"] is True
    assert not (root / "outputs" / "runtime_exports").exists()


def test_runtime_state_export_execute_writes_redacted_manifest_and_checksums(tmp_path: Path) -> None:
    root = _make_runtime_export_root(tmp_path)
    output = "outputs/runtime_exports/test-export"

    result = RuntimeStateExporter(root, RuntimeStateExportOptions(execute=True, dry_run=False, output=output)).run()

    assert result.ok is True, result.to_dict()
    summary = result.data["summary"]
    manifest = result.data["manifest"]
    output_path = root / output
    manifest_path = output_path / "runtime_state_export_manifest.json"
    checksums_path = output_path / "checksums.sha256"

    assert summary["dry_run"] is False
    assert summary["execute_requested"] is True
    assert summary["export_execution_enabled"] is True
    assert summary["manifest_written"] is True
    assert summary["checksums_written"] is True
    assert summary["files_exported_total"] >= 3
    assert summary["raw_payload_fields_removed_total"] >= 2
    assert summary["redactions_total"] >= 1
    assert summary["raw_prompts_exported"] is False
    assert summary["raw_outputs_exported"] is False
    assert summary["secrets_exported"] is False
    assert summary["local_db_raw_exported"] is False
    assert manifest_path.exists()
    assert checksums_path.exists()

    exported_text = "\n".join(path.read_text(encoding="utf-8") for path in output_path.rglob("*") if path.is_file())
    assert "sk-proj-ABCDEFG1234567890" not in exported_text
    assert "sk-proj-1234567890ABCDEFG" not in exported_text
    assert "secret prompt" not in exported_text
    assert "model output should not be exported" not in exported_text
    assert "SQLite format" not in exported_text
    assert "[REDACTED]" in exported_text or "REDACTED_RAW_PAYLOAD_LINE" in exported_text

    schema_result = SchemaValidator(ROOT).validate_payload(
        schema="RuntimeStateExportManifest",
        payload=json.loads(manifest_path.read_text(encoding="utf-8")),
        instance_label="runtime_state_export_manifest.synthetic.json",
    )
    assert schema_result.ok is True, schema_result.to_dict()


def test_runtime_state_export_execute_requires_output_under_runtime_exports(tmp_path: Path) -> None:
    root = _make_runtime_export_root(tmp_path)

    missing_output = RuntimeStateExporter(root, RuntimeStateExportOptions(execute=True, dry_run=False)).run()
    assert missing_output.ok is False
    assert missing_output.exit_code == 2
    assert any(finding.id == "RUNTIME_STATE_EXPORT_OUTPUT_REQUIRED" for finding in missing_output.findings)

    forbidden_output = RuntimeStateExporter(root, RuntimeStateExportOptions(execute=True, dry_run=False, output="docs/leak")).run()
    assert forbidden_output.ok is False
    assert forbidden_output.exit_code == 2
    assert any(finding.id == "RUNTIME_STATE_EXPORT_OUTPUT_OUTSIDE_RUNTIME_EXPORTS" for finding in forbidden_output.findings)


def test_runtime_state_export_cli_dry_run_is_parseable_and_side_effect_free(tmp_path: Path, monkeypatch, capsys) -> None:
    root = _make_runtime_export_root(tmp_path)
    monkeypatch.chdir(root)

    exit_code = cli.main(["runtime-state", "export", "--dry-run", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "runtime-state export"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["dry_run"] is True
    assert payload["data"]["summary"]["execute_requested"] is False
    assert payload["data"]["summary"]["mutations_performed"] is False
    assert not (root / "outputs" / "runtime_exports").exists()
