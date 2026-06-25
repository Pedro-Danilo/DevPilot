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


def test_post_h_006_e_no_growth_gate_passes_with_explicit_legacy_allowlist() -> None:
    from devpilot_core.cli_registry.growth_gate import CliNoGrowthGate

    result = CliNoGrowthGate(ROOT).run()

    assert result.ok is True, result.to_dict()
    summary = result.data["summary"]
    gate = result.data["gate"]
    allowlist = result.data["allowlist"]

    assert summary["created_by"] == "POST-H-006-E"
    assert summary["registry_created_by"] == "POST-H-006-E"
    assert summary["commands_total"] >= 130
    assert summary["legacy_commands_total"] == summary["allowed_legacy_commands_total"]
    assert summary["unexpected_legacy_commands_total"] == 0
    assert summary["blocking_findings_total"] == 0
    assert gate["policy"]["new_public_cli_commands_must_be_registered"] is True
    assert gate["policy"]["temporary_legacy_allowlist_required"] is True
    assert gate["safety"]["read_only"] is True
    assert gate["safety"]["dynamic_handler_loading_enabled"] is False
    assert allowlist["created_by"] == "POST-H-006-E"
    assert allowlist["policy"]["new_legacy_commands_blocked"] is True


def test_post_h_006_e_new_unregistered_command_is_blocked_by_focal_gate(tmp_path: Path) -> None:
    from devpilot_core.cli_registry.growth_gate import CliNoGrowthGate, CliNoGrowthGateOptions

    allowlist = _read_json(".devpilot/cli_registry/legacy_command_allowlist.json")
    removed = "agent.run"
    assert removed in allowlist["allowed_legacy_command_ids"]
    allowlist["allowed_legacy_command_ids"] = [
        command_id for command_id in allowlist["allowed_legacy_command_ids"] if command_id != removed
    ]
    temporary_allowlist = tmp_path / "legacy_command_allowlist.json"
    temporary_allowlist.write_text(json.dumps(allowlist, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    result = CliNoGrowthGate(
        ROOT,
        CliNoGrowthGateOptions(allowlist_path=temporary_allowlist),
    ).run()

    assert result.ok is False
    assert int(result.exit_code) == 2
    summary = result.data["summary"]
    assert summary["unexpected_legacy_commands_total"] == 1
    assert result.data["gate"]["commands"]["unexpected_legacy_command_ids"] == [removed]
    assert any(finding.id == "CLI_NO_GROWTH_UNEXPECTED_LEGACY_COMMANDS" for finding in result.findings)


def test_post_h_006_e_cli_registry_guard_is_registered_and_safe() -> None:
    registry = _registry_result().data["registry"]
    commands = {command["command_id"]: command for group in registry["groups"] for command in group["commands"]}

    assert registry["created_by"] == "POST-H-006-E"
    assert registry["metadata"]["no_growth_gate_enabled"] is True
    assert registry["metadata"]["no_growth_gate_id"] == "devpilot-cli-no-growth-gate"
    assert registry["metadata"]["legacy_allowlist_path"] == ".devpilot/cli_registry/legacy_command_allowlist.json"
    assert "cli-registry.guard" in commands
    assert commands["cli-registry.guard"]["metadata"]["registry_phase"] == "declarative-initial"
    assert commands["cli-registry.guard"]["metadata"]["registration_status"] == "registered-declarative"
    assert commands["cli-registry.guard"]["risk_level"] == "high"
    assert commands["cli-registry.guard"]["remote_execution_enabled"] is False
    assert commands["cli-registry.guard"]["connector_write_enabled"] is False
    assert commands["cli-registry.guard"]["plugin_execution_enabled"] is False
    assert any(option["name"] == "allowlist" for option in commands["cli-registry.guard"]["options"])


def test_post_h_006_e_no_growth_gate_writes_reports() -> None:
    from devpilot_core.cli_registry.growth_gate import CliNoGrowthGate, CliNoGrowthGateOptions

    outputs = ROOT / "outputs" / "reports"
    for name in ["cli_command_registry_no_growth_gate.json", "cli_command_registry_no_growth_gate.md"]:
        path = outputs / name
        if path.exists():
            path.unlink()

    result = CliNoGrowthGate(ROOT, CliNoGrowthGateOptions(write_report=True)).run()

    assert result.ok is True, result.to_dict()
    summary = result.data["summary"]
    assert summary["reports_written"] is True
    assert summary["output_json"] == "outputs/reports/cli_command_registry_no_growth_gate.json"
    assert summary["output_markdown"] == "outputs/reports/cli_command_registry_no_growth_gate.md"
    json_payload = _read_json("outputs/reports/cli_command_registry_no_growth_gate.json")
    markdown = _read("outputs/reports/cli_command_registry_no_growth_gate.md")
    assert json_payload["created_by"] == "POST-H-006-E"
    assert json_payload["summary"]["unexpected_legacy_commands_total"] == 0
    assert "CLI no-growth gate" in markdown


def test_post_h_006_e_docs_manifest_allowlist_and_contracts_are_synchronized() -> None:
    backlog = _read("docs/backlogs/POST-H-006_cli_command_registry.md")
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    architecture_doc = _read("docs/02_architecture/cli_command_registry_map.md")
    audit = _read("docs/audits/post_h_006_e_no_growth_gate_report.md")
    manifest = _read_json("docs/post_h_006_e_manifest.json")
    allowlist = _read_json(".devpilot/cli_registry/legacy_command_allowlist.json")
    changelog = _read("docs/release/CHANGELOG.md")
    v1 = _read_json(".devpilot/testing/test_contract_registry.json")
    v2 = _read_json(".devpilot/testing/test_contract_registry_v2.json")
    v1_contracts = {item["contract_id"]: item for item in v1["contracts"]}
    v2_contracts = {item["contract_id"]: item for item in v2["contracts"]}

    assert "POST-H-006-E — Gate de no crecimiento monolítico" in backlog
    assert "Estado: `implemented-initial`" in backlog
    assert "POST-H-006-E" in readme
    assert "POST-H-007" in readme
    assert "POST-H-006-E — Operación del gate de no crecimiento monolítico" in runbook
    assert "CliNoGrowthGate" in architecture_doc
    assert "legacy_command_allowlist.json" in audit
    assert "post-h-006-e" in changelog
    assert manifest["id"] == "POST-H-006-E"
    assert manifest["no_growth_gate_enabled"] is True
    assert manifest["runtime_router_enabled"] is False
    assert manifest["dynamic_handler_loading_enabled"] is False
    assert allowlist["id"] == "DEVPL-CLI-LEGACY-COMMAND-ALLOWLIST"
    assert allowlist["created_by"] == "POST-H-006-E"
    assert allowlist["allowed_legacy_command_ids"]
    assert "post-h-006-cli-no-growth-gate" in v1_contracts
    assert "post-h-006-cli-no-growth-gate" in v2_contracts
    assert v1_contracts["post-h-006-cli-no-growth-gate"]["owner"] == "POST-H-006-E"
    assert v2_contracts["post-h-006-cli-no-growth-gate"]["domain"] == "interface.cli"
    assert v2_contracts["post-h-006-cli-no-growth-gate"]["owner"] == "POST-H-006-E"
