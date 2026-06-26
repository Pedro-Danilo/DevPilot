from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.observability import ObservabilityInventoryBuilder, ObservabilityInventoryOptions
from devpilot_core.schemas import SchemaRegistry, SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_observability_inventory_schema_is_registered() -> None:
    catalog = read_json("docs/schemas/schema_catalog.json")
    entries = {item["schema_id"]: item for item in catalog["schemas"]}

    assert "SCHEMA-DEVPL-OBSERVABILITY-INVENTORY-V1" in entries
    entry = entries["SCHEMA-DEVPL-OBSERVABILITY-INVENTORY-V1"]
    assert entry["path"] == "docs/schemas/observability_inventory.schema.json"
    assert entry["contract"] == "ObservabilityInventory"
    assert entry["sprint"] == "POST-H-010-B"
    assert (ROOT / entry["path"]).exists()

    registry_result = SchemaRegistry(ROOT).list()
    assert registry_result.ok, registry_result.to_dict()
    assert "SCHEMA-DEVPL-OBSERVABILITY-INVENTORY-V1" in {item["schema_id"] for item in registry_result.data["schemas"]}


def test_observability_inventory_is_read_only_and_reports_targets() -> None:
    result = ObservabilityInventoryBuilder(ROOT).run()
    summary = result.data["summary"]
    inventory = result.data["inventory"]

    assert result.ok, result.to_dict()
    assert result.command == "observability inventory"
    assert summary["created_by"] == "POST-H-010-B"
    assert summary["policy_loaded"] is True
    assert summary["read_only"] is True
    assert summary["raw_payloads_read"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False
    assert summary["targets_total"] >= 6
    assert summary["clean_zip_excluded_total"] == summary["targets_total"]
    assert summary["blocking_findings_total"] == 0
    assert {item["target_id"] for item in inventory["target_checks"]} >= {
        "events-jsonl",
        "trace-files",
        "devpilot-db",
        "agent-sessions",
        "generated-reports",
        "metrics-local-store",
    }
    for item in inventory["target_checks"]:
        assert "records_estimated" in item
        assert item["inside_workspace"] is True
        assert item["source_of_truth"] is False
        assert item["versionable"] is False
        assert item["raw_payload_storage_allowed"] is False


def test_observability_inventory_write_report_validates_against_schema() -> None:
    result = ObservabilityInventoryBuilder(ROOT, ObservabilityInventoryOptions(write_report=True)).run()
    reports = result.data["reports"]

    assert result.ok, result.to_dict()
    assert reports["json"] == "outputs/reports/observability_inventory.json"
    assert reports["markdown"] == "outputs/reports/observability_inventory.md"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()

    validation = SchemaValidator(ROOT).validate(
        schema="ObservabilityInventory",
        instance=reports["json"],
    )
    assert validation.ok, validation.to_dict()


def test_observability_inventory_cli_json_and_write_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["observability", "inventory", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "observability inventory"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["created_by"] == "POST-H-010-B"
    assert payload["data"]["summary"]["read_only"] is True
    assert payload["data"]["summary"]["raw_payloads_read"] is False
    assert payload["data"]["reports"]["json"] == "outputs/reports/observability_inventory.json"
