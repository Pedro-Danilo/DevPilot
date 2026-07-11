from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.agents import AgentCapabilityInventoryBuilder, AgentCapabilityInventoryOptions
from devpilot_core.application import ApplicationService
from devpilot_core.cli_models import ExitCode
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _inventory_from_result(result):
    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    inventory = result.data["inventory"]
    assert inventory["schema_id"] == "SCHEMA-DEVPL-AGENT-CAPABILITY-INVENTORY-V1"
    return inventory


def test_agent_capability_inventory_covers_miasi_agents_and_blocks_unsafe_defaults() -> None:
    result = AgentCapabilityInventoryBuilder(ROOT).build()
    inventory = _inventory_from_result(result)
    summary = inventory["summary"]
    registry = _load(".devpilot/miasi/agent_registry.json")
    tool_registry = _load(".devpilot/miasi/tool_registry.json")
    registered_agent_ids = {agent["agent_id"] for agent in registry["agents"]}
    inventory_agent_ids = {agent["agent_id"] for agent in inventory["agents"]}
    registered_tool_ids = {tool["tool_id"] for tool in tool_registry["tools"]}

    assert inventory_agent_ids == registered_agent_ids
    assert summary["agents_total"] == len(registered_agent_ids)
    assert summary["implemented_agents_total"] >= 13
    assert summary["blocking_findings_total"] == 0
    assert summary["implemented_without_module_total"] == 0
    assert summary["implemented_without_tests_total"] == 0
    assert summary["agents_with_tools_without_allowlist_total"] == 0
    assert summary["external_api_allowed_total"] == 0
    assert summary["memory_enabled_total"] == 0
    assert summary["rag_enabled_total"] == 0
    assert summary["remote_execution_enabled_total"] == 0
    assert summary["connector_write_enabled_total"] == 0
    assert summary["plugin_execution_enabled_total"] == 0
    assert summary["source_mutation_allowed_total"] == 0
    assert inventory["safety"]["agents_executed"] is False
    assert inventory["safety"]["tools_executed"] is False
    assert inventory["safety"]["models_called"] is False
    assert inventory["safety"]["network_used"] is False
    assert inventory["safety"]["external_api_used"] is False

    for agent in inventory["agents"]:
        assert set(agent["allowed_tools"]).issubset(registered_tool_ids)
        if agent["implemented_agent"]:
            assert agent["implementation_module_exists"] is True
            assert agent["eval_coverage_existing"]
        assert agent["external_api_allowed"] is False
        assert agent["memory_enabled"] is False
        assert agent["source_mutation_allowed"] is False
        assert agent["tool_calling_dry_run_first"] is True


def test_agent_promotion_criteria_schema_and_no_go_gates_are_valid() -> None:
    criteria = _load(".devpilot/agents/agent_promotion_criteria.json")
    result = SchemaValidator(ROOT).validate(
        schema="AgentPromotionCriteria",
        instance=".devpilot/agents/agent_promotion_criteria.json",
    )

    assert result.ok is True, result.to_dict()
    assert criteria["schema_id"] == "SCHEMA-DEVPL-AGENT-PROMOTION-CRITERIA-V1"
    gate_ids = {gate["gate_id"] for gate in criteria["global_no_go_gates"]}
    assert {
        "external-api-disabled-by-default",
        "memory-disabled-by-default",
        "no-source-mutation-without-approval",
        "no-remote-connector-plugin-execution",
        "deterministic-gates-not-replaced-by-llm",
    }.issubset(gate_ids)
    assert criteria["safety"]["external_api_default_enabled"] is False
    assert criteria["safety"]["memory_default_enabled"] is False
    assert criteria["safety"]["remote_execution_enabled"] is False
    assert criteria["safety"]["connector_write_enabled"] is False
    assert criteria["safety"]["plugin_execution_enabled"] is False


def test_agent_capability_inventory_source_artifact_validates_against_schema() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="AgentCapabilityInventory",
        instance=".devpilot/agents/agent_capability_inventory.json",
    )

    assert result.ok is True, result.to_dict()


def test_agent_capability_inventory_cli_and_application_service_are_synchronized(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["agent", "capability-inventory", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["data"]["summary"]["decision"] == "PASS"
    assert payload["data"]["summary"]["external_api_allowed_total"] == 0

    app_result = ApplicationService(ROOT).agent_capability_inventory()
    assert app_result.ok is True, app_result.to_dict()
    assert app_result.data["summary"]["agents_total"] == payload["data"]["summary"]["agents_total"]


def test_agent_capability_inventory_write_report_is_outputs_only(tmp_path: Path) -> None:
    output_json = Path("outputs/reports/test_post_h_032_a_agent_capability_inventory.json")
    output_md = Path("outputs/reports/test_post_h_032_a_agent_capability_inventory.md")
    for path in (ROOT / output_json, ROOT / output_md):
        if path.exists():
            path.unlink()

    result = AgentCapabilityInventoryBuilder(
        ROOT,
        AgentCapabilityInventoryOptions(write_report=True, output_json=output_json, output_markdown=output_md),
    ).build()

    inventory = _inventory_from_result(result)
    assert inventory["summary"]["reports_written"] is True
    assert result.data["reports"] == {"json": output_json.as_posix(), "markdown": output_md.as_posix()}
    assert (ROOT / output_json).exists()
    assert (ROOT / output_md).exists()


def test_post_h_032_a_governance_artifacts_are_synchronized() -> None:
    state = _load(".devpilot/project_state.json")
    catalog = _load("docs/schemas/schema_catalog.json")
    tcr = _load(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = _load(".devpilot/testing/test_contract_registry_v2.json")
    source_registry = _load(".devpilot/docs_governance/source_registry.json")

    schema_ids = {schema["schema_id"] for schema in catalog["schemas"]}
    contract_ids = {contract["contract_id"] for contract in tcr["contracts"]}
    contract_ids_v2 = {contract["contract_id"] for contract in tcr_v2["contracts"]}
    document_paths = {document["path"] for document in source_registry["documents"]}

    assert state["post_h_032_backlog_approved"] is True
    assert state["post_h_032_current_micro_sprint"] in {"POST-H-032-A", "POST-H-032-B", "POST-H-032-C", "POST-H-032-D", "POST-H-032-E", "POST-H-032-F", "POST-H-032-G", "POST-H-032-H"}
    assert state["post_h_032_next_micro_sprint"] in {"POST-H-032-B", "POST-H-032-C", "POST-H-032-D", "POST-H-032-E", "POST-H-032-F", "POST-H-032-G", "POST-H-032-H"}
    assert state["post_h_032_agent_capability_inventory_available"] is True
    assert state["post_h_032_external_api_allowed_total"] == 0
    assert state["post_h_032_memory_enabled_total"] == 0
    assert "SCHEMA-DEVPL-AGENT-CAPABILITY-INVENTORY-V1" in schema_ids
    assert "SCHEMA-DEVPL-AGENT-PROMOTION-CRITERIA-V1" in schema_ids
    assert "post-h-032-agent-capability-inventory" in contract_ids
    assert "post-h-032-agent-promotion-criteria" in contract_ids
    assert "post-h-032-agent-capability-inventory" in contract_ids_v2
    assert "post-h-032-agent-promotion-criteria" in contract_ids_v2
    assert "docs/backlogs/POST-H-032_advanced_ai_agents_llm_rag_memory_tools.md" in document_paths
    assert ".devpilot/agents/agent_capability_inventory.json" in document_paths
    assert ".devpilot/agents/agent_promotion_criteria.json" in document_paths
