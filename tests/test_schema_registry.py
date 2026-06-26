from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.schemas import SchemaRegistry

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_SCHEMA_IDS = {
    "SCHEMA-DEVPL-COMMAND-RESULT-V1",
    "SCHEMA-DEVPL-FINDING-V1",
    "SCHEMA-DEVPL-EVIDENCE-REPORT-V1",
    "SCHEMA-DEVPL-APPLICATION-REQUEST-V1",
    "SCHEMA-DEVPL-APPLICATION-RESPONSE-V1",
    "SCHEMA-DEVPL-SERVICE-CAPABILITY-V1",
    "SCHEMA-DEVPL-INTERFACE-ROUTE-CONTRACT-V1",
    "SCHEMA-DEVPL-MIASI-AGENT-REGISTRY-V1",
    "SCHEMA-DEVPL-MIASI-TOOL-REGISTRY-V1",
    "SCHEMA-DEVPL-MIASI-POLICY-MATRIX-V1",
    "SCHEMA-DEVPL-WORKSPACE-PROJECT-V1",
    "SCHEMA-DEVPL-PROVIDER-CONFIG-V2",
    "SCHEMA-DEVPL-FUNCTIONAL-SPRINT-MANIFEST-V1",
    "SCHEMA-DEVPL-ARTIFACT-PROFILES-V1",
    "SCHEMA-DEVPL-PROMPT-V1",
    "SCHEMA-DEVPL-CONNECTOR-REGISTRY-V1",
    "SCHEMA-DEVPL-MULTIAGENT-WORKFLOW-V1",
    "SCHEMA-DEVPL-PLUGIN-MANIFEST-V1",
    "SCHEMA-DEVPL-MULTIWORKSPACE-REGISTRY-V1",
    "SCHEMA-DEVPL-IDENTITY-REGISTRY-V1",
    "SCHEMA-DEVPL-AUDIT-PACK-MANIFEST-V1",
    "SCHEMA-DEVPL-COMPLIANCE-PACK-V1",
    "SCHEMA-DEVPL-REMOTE-RUNNER-REGISTRY-V1",
    "SCHEMA-DEVPL-INDUSTRIAL-READINESS-V1",
    "SCHEMA-DEVPL-TEST-CONTRACT-REGISTRY-V1",
    "SCHEMA-DEVPL-TEST-CONTRACT-REGISTRY-V2",
    "SCHEMA-DEVPL-PROJECT-STATE-V1",
    "SCHEMA-DEVPL-POST-H-MANIFEST-V1",
    "SCHEMA-DEVPL-MATURITY-DASHBOARD-V1",
    "SCHEMA-DEVPL-MIASI-SEMANTIC-REPORT-V1",
    "SCHEMA-DEVPL-ARCHITECTURE-MAP-V1",
    "SCHEMA-DEVPL-CLI-COMMAND-REGISTRY-V1",
    "SCHEMA-DEVPL-APPLICATION-SERVICE-BOUNDARY-REPORT-V1",
    "SCHEMA-DEVPL-APPLICATION-OPERATION-CATALOG-V1",
    "SCHEMA-DEVPL-RUNTIME-STATE-POLICY-V1",
    "SCHEMA-DEVPL-RUNTIME-STATE-INVENTORY-V1",
    "SCHEMA-DEVPL-RUNTIME-STATE-CLEANUP-PLAN-V1",
}


def test_schema_registry_lists_registered_schemas() -> None:
    result = SchemaRegistry(ROOT).list()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.command == "schema list"
    assert result.data["summary"]["schemas_total"] == len(EXPECTED_SCHEMA_IDS)
    assert result.data["summary"]["schemas_existing"] == len(EXPECTED_SCHEMA_IDS)
    assert {schema["schema_id"] for schema in result.data["schemas"]} == EXPECTED_SCHEMA_IDS
    assert all(schema["version"] for schema in result.data["schemas"])
    assert all(schema["description"] for schema in result.data["schemas"])


def test_schema_registry_detects_duplicate_ids(tmp_path: Path) -> None:
    catalog_dir = tmp_path / "docs" / "schemas"
    catalog_dir.mkdir(parents=True)
    schema_path = catalog_dir / "command_result.schema.json"
    schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
    duplicate_entry = {
        "schema_id": "SCHEMA-DEVPL-COMMAND-RESULT-V1",
        "title": "CommandResult",
        "version": "1.0.0",
        "path": "docs/schemas/command_result.schema.json",
        "description": "Duplicate synthetic schema entry.",
    }
    (catalog_dir / "schema_catalog.json").write_text(
        json.dumps({"schemas": [duplicate_entry, duplicate_entry]}, indent=2),
        encoding="utf-8",
    )

    result = SchemaRegistry(tmp_path).list()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert "SCHEMA-DEVPL-COMMAND-RESULT-V1" in result.data["summary"]["duplicate_schema_ids"]
    assert any(finding.id == "SCHEMA_REGISTRY_DUPLICATE_ID" for finding in result.findings)


def test_schema_registry_detects_missing_schema_file(tmp_path: Path) -> None:
    catalog_dir = tmp_path / "docs" / "schemas"
    catalog_dir.mkdir(parents=True)
    (catalog_dir / "schema_catalog.json").write_text(
        json.dumps(
            {
                "schemas": [
                    {
                        "schema_id": "SCHEMA-DEVPL-MISSING-V1",
                        "title": "Missing schema",
                        "version": "1.0.0",
                        "path": "docs/schemas/missing.schema.json",
                        "description": "Registered but missing file.",
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    result = SchemaRegistry(tmp_path).list()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["missing_schema_paths"] == ["docs/schemas/missing.schema.json"]
    assert any(finding.id == "SCHEMA_REGISTRY_MISSING_FILE" for finding in result.findings)


def test_schema_registry_catalog_entries_have_existing_files() -> None:
    catalog = json.loads((ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8"))

    schema_ids = [entry["schema_id"] for entry in catalog["schemas"]]
    assert len(schema_ids) == len(set(schema_ids))
    for entry in catalog["schemas"]:
        assert entry["schema_id"].startswith("SCHEMA-DEVPL-")
        assert entry["version"]
        assert entry["description"]
        assert (ROOT / entry["path"]).exists()


def test_schema_list_cli_json_is_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["schema", "list", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "schema list"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["schemas_total"] == len(EXPECTED_SCHEMA_IDS)
    assert payload["data"]["summary"]["schemas_existing"] == len(EXPECTED_SCHEMA_IDS)


def test_schema_list_cli_write_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["schema", "list", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    reports = payload["data"]["reports"]
    assert reports["json"] == "outputs/reports/schema_list.json"
    assert reports["markdown"] == "outputs/reports/schema_list.md"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()
