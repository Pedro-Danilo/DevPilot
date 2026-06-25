from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _registry_result():
    from devpilot_core.cli_registry.report import CliCommandRegistryReportBuilder

    return CliCommandRegistryReportBuilder(ROOT).build()


def test_cli_command_registry_static_builder_detects_public_cli_surface() -> None:
    result = _registry_result()

    assert result.ok is True, result.to_dict()
    summary = result.data["summary"]
    registry = result.data["registry"]
    groups = {group["group_id"]: group for group in registry["groups"]}

    assert summary["commands_total"] >= 100
    assert summary["groups_total"] >= 40
    assert summary["schema_validation_ok"] is True
    assert summary["blocking_findings_total"] == 0
    assert summary["dynamic_handler_loading_enabled"] is False
    assert summary["remote_execution_enabled"] is False
    assert summary["connector_write_enabled"] is False
    assert summary["plugin_execution_enabled"] is False
    for expected in ["workspace", "schema", "validate", "quality-gate", "test-contracts", "architecture", "cli-registry"]:
        assert expected in groups


def test_cli_command_registry_descriptors_are_actionable_and_safe() -> None:
    registry = _registry_result().data["registry"]
    commands = {command["command_id"]: command for group in registry["groups"] for command in group["commands"]}

    assert "architecture.map" in commands
    assert "cli-registry.report" in commands
    assert commands["cli-registry.report"]["public_invocation"] == "python -m devpilot_core cli-registry report"
    assert commands["cli-registry.report"]["returns"] == "CommandResult"
    assert commands["cli-registry.report"]["remote_execution_enabled"] is False
    assert commands["cli-registry.report"]["connector_write_enabled"] is False
    assert commands["cli-registry.report"]["plugin_execution_enabled"] is False
    assert commands["cli-registry.report"]["recommended_tests"]
    assert any(option["name"] == "json" for option in commands["cli-registry.report"]["options"])
    assert any(option["name"] == "write_report" for option in commands["cli-registry.report"]["options"])


def test_cli_command_registry_writes_schema_valid_reports() -> None:
    from devpilot_core.cli_registry.report import CliCommandRegistryReportBuilder, CliCommandRegistryReportOptions

    outputs = ROOT / "outputs" / "reports"
    for name in ["cli_command_registry.json", "cli_command_registry.md"]:
        path = outputs / name
        if path.exists():
            path.unlink()

    result = CliCommandRegistryReportBuilder(ROOT, CliCommandRegistryReportOptions(write_report=True)).build()

    assert result.ok is True, result.to_dict()
    assert result.data["summary"]["reports_written"] is True
    assert result.data["summary"]["output_json"] == "outputs/reports/cli_command_registry.json"
    assert result.data["summary"]["output_markdown"] == "outputs/reports/cli_command_registry.md"
    raw_json = ROOT / "outputs/reports/cli_command_registry.json"
    raw_md = ROOT / "outputs/reports/cli_command_registry.md"
    assert raw_json.exists()
    assert raw_md.exists()
    raw_payload = json.loads(raw_json.read_text(encoding="utf-8"))
    assert raw_payload["schema_id"] == "SCHEMA-DEVPL-CLI-COMMAND-REGISTRY-V1"
    assert raw_payload["created_by"] == "POST-H-006-C"
    assert "CLI command registry incremental handler migration" in raw_md.read_text(encoding="utf-8")


def test_cli_registry_cli_contract_is_registered_with_incremental_handler_migration() -> None:
    cli = _read("src/devpilot_core/cli.py")

    assert 'sub.add_parser("cli-registry"' in cli
    assert 'cli_registry_sub.add_parser("report"' in cli
    assert "CliCommandRegistryReportBuilder" in cli
    assert "cli_registry_report_command" in cli
    assert "src/devpilot_core/cli_commands/" not in "\n".join(_read("docs/post_h_006_a_manifest.json").splitlines())
    assert "src/devpilot_core/cli_commands/" not in "\n".join(_read("docs/post_h_006_b_manifest.json").splitlines())


def test_post_h_006_a_docs_manifest_and_contracts_are_synchronized() -> None:
    backlog = _read("docs/backlogs/POST-H-006_cli_command_registry.md")
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    changelog = _read("docs/release/CHANGELOG.md")
    architecture_doc = _read("docs/02_architecture/cli_command_registry_map.md")
    audit = _read("docs/audits/post_h_006_a_cli_command_registry_report.md")
    manifest = _read_json("docs/post_h_006_a_manifest.json")
    v1 = _read_json(".devpilot/testing/test_contract_registry.json")
    v2 = _read_json(".devpilot/testing/test_contract_registry_v2.json")
    v1_contracts = {item["contract_id"]: item for item in v1["contracts"]}
    v2_contracts = {item["contract_id"]: item for item in v2["contracts"]}

    assert 'status: "approved"' in backlog
    assert 'implementation_status: "in-progress"' in backlog
    assert "POST-H-006-A — Inventario estático del CLI" in backlog
    assert "Último micro-sprint implementado: `POST-H-006-C" in readme
    assert "Siguiente micro-sprint: `POST-H-006-D" in readme
    assert "POST-H-006-A — Operación del CLI command registry estático" in runbook
    assert "POST-H-006-B — Operación del registry declarativo inicial" in runbook
    assert "POST-H-006-C — Operación de handlers migrados de workspace/validación" in runbook
    assert "post-h-006-a" in changelog
    assert "post-h-006-b" in changelog
    assert "post-h-006-c" in changelog
    assert "StaticCliInventoryExtractor" in architecture_doc
    assert "DeclarativeCliRegistryBuilder" in architecture_doc
    assert "cli_commands/workspace.py" in architecture_doc
    assert "cli-registry report --write-report --json" in audit
    assert manifest["id"] == "POST-H-006-A"
    manifest_b = _read_json("docs/post_h_006_b_manifest.json")
    assert manifest_b["id"] == "POST-H-006-B"
    assert manifest["parent_hito"] == "POST-H-006"
    assert manifest["handler_migration_performed"] is False
    manifest_c = _read_json("docs/post_h_006_c_manifest.json")
    assert manifest_c["id"] == "POST-H-006-C"
    assert manifest_c["handler_migration_performed"] is True
    assert manifest_c["runtime_router_enabled"] is False
    assert manifest["dynamic_handler_loading_enabled"] is False
    assert manifest["remote_execution_enabled"] is False
    assert "post-h-006-cli-command-registry" in v1_contracts
    assert "post-h-006-cli-command-registry" in v2_contracts
    assert v1_contracts["post-h-006-cli-command-registry"]["owner"] == "POST-H-006-A"
    assert v2_contracts["post-h-006-cli-command-registry"]["domain"] == "interface.cli"
    assert v2_contracts["post-h-006-cli-command-registry"]["criticality"] == "P1"
