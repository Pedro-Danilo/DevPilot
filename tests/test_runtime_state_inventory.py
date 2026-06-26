from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.runtime_state import RuntimeStateInventoryBuilder, RuntimeStateInventoryOptions
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_runtime_state_inventory_scans_policy_classes_without_mutating_outputs(monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    trace_path = ROOT / "outputs" / "traces" / "events.jsonl"
    before_exists = trace_path.exists()
    before_size = trace_path.stat().st_size if before_exists else 0

    result = RuntimeStateInventoryBuilder(ROOT).run()

    assert result.ok is True, result.to_dict()
    summary = result.data["summary"]
    inventory = result.data["inventory"]
    assert result.command == "runtime-state inventory"
    assert summary["created_by"] == "POST-H-008-B"
    assert summary["read_only"] is True
    assert summary["cleanup_execution_enabled"] is False
    assert summary["export_execution_enabled"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["destructive_cleanup_performed"] is False
    assert summary["source_mutations_performed"] is False
    assert summary["classes_total"] >= 13
    assert inventory["by_class"]["source-code"]["artifacts_total"] > 0
    assert inventory["by_class"]["engineering-docs"]["artifacts_total"] > 0
    assert inventory["by_class"]["runtime-policy"]["artifacts_total"] > 0
    assert inventory["by_class"]["generated-reports"]["versionable"] is False
    assert inventory["by_class"]["trace-events"]["redaction_required"] is True
    assert inventory["by_class"]["local-db"]["cleanup_allowed"] is False
    assert inventory["safety"]["remote_execution_enabled"] is False
    assert any(item["path"] == ".devpilot/runtime_state_policy.json" for item in inventory["artifacts"])

    after_exists = trace_path.exists()
    after_size = trace_path.stat().st_size if after_exists else 0
    assert (after_exists, after_size) == (before_exists, before_size)


def test_runtime_state_inventory_write_report_outputs_schema_valid_payload(monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    result = RuntimeStateInventoryBuilder(ROOT, RuntimeStateInventoryOptions(write_report=True)).run()

    assert result.ok is True, result.to_dict()
    reports = result.data["reports"]
    assert reports["json"] == "outputs/reports/runtime_state_inventory.json"
    assert reports["markdown"] == "outputs/reports/runtime_state_lifecycle_report.md"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()

    payload = _read_json(reports["json"])
    assert payload["created_by"] == "POST-H-008-B"
    assert payload["summary"]["reports_written"] is True
    assert "Runtime state lifecycle report" in (ROOT / reports["markdown"]).read_text(encoding="utf-8")

    schema_result = SchemaValidator(ROOT).validate(schema="RuntimeStateInventory", instance=reports["json"])
    assert schema_result.ok is True, schema_result.to_dict()
    assert schema_result.data["summary"]["valid"] is True


def test_runtime_state_inventory_cli_json_is_read_only_and_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)
    trace_path = ROOT / "outputs" / "traces" / "events.jsonl"
    before_exists = trace_path.exists()
    before_size = trace_path.stat().st_size if before_exists else 0

    exit_code = cli.main(["runtime-state", "inventory", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "runtime-state inventory"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["read_only"] is True
    assert payload["data"]["summary"]["reports_written"] is False
    assert payload["data"]["summary"]["destructive_cleanup_performed"] is False
    after_exists = trace_path.exists()
    after_size = trace_path.stat().st_size if after_exists else 0
    assert (after_exists, after_size) == (before_exists, before_size)


def test_runtime_state_inventory_detects_versioned_runtime_artifacts(tmp_path: Path) -> None:
    root = tmp_path
    (root / ".devpilot").mkdir(parents=True)
    (root / "outputs" / "reports").mkdir(parents=True)
    (root / "docs" / "schemas").mkdir(parents=True)
    policy = _read_json(".devpilot/runtime_state_policy.json")
    (root / ".devpilot" / "runtime_state_policy.json").write_text(json.dumps(policy), encoding="utf-8")
    (root / "outputs" / "reports" / "leaked.json").write_text("{}\n", encoding="utf-8")
    (root / ".git").mkdir()

    import subprocess

    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", ".devpilot/runtime_state_policy.json", "outputs/reports/leaked.json"], cwd=root, check=True, capture_output=True, text=True)

    result = RuntimeStateInventoryBuilder(root).run()

    assert result.ok is False
    assert int(result.exit_code) == 2
    assert result.data["summary"]["versioned_runtime_artifacts_total"] == 1
    violations = result.data["inventory"]["violations"]
    assert any(item["violation_id"] == "RUNTIME_STATE_VERSIONED" for item in violations)
    assert any(item["path"] == "outputs/reports/leaked.json" for item in violations)
