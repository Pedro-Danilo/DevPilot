from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_commands import (
    handle_industrial_readiness_check,
    handle_industrial_readiness_production_ready_local,
    handle_industrial_readiness_production_ready_local_final,
)
from devpilot_core.cli_registry.registry import DeclarativeCliRegistryBuilder

ROOT = Path(__file__).resolve().parents[1]


def _post_h_number(value: str) -> int:
    return int(str(value).split("POST-H-")[-1].split("-")[0])
INDUSTRIAL_COMMANDS = {
    "industrial-readiness.check",
    "industrial-readiness.production-ready-local",
    "industrial-readiness.production-ready-local-final",
}


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _commands_by_id() -> dict[str, dict]:
    registry = DeclarativeCliRegistryBuilder(ROOT).build_registry().to_dict()
    return {command["command_id"]: command for group in registry["groups"] for command in group["commands"]}


def test_post_h_030_b_handlers_are_extracted_without_cli_runtime_router() -> None:
    commands = _commands_by_id()

    expected_handlers = {
        "industrial-readiness.check": "handle_industrial_readiness_check",
        "industrial-readiness.production-ready-local": "handle_industrial_readiness_production_ready_local",
        "industrial-readiness.production-ready-local-final": "handle_industrial_readiness_production_ready_local_final",
    }
    for command_id, handler in expected_handlers.items():
        command = commands[command_id]
        metadata = command["metadata"]
        assert command["owner_module"] == "src/devpilot_core/cli_commands/industrial_readiness.py"
        assert command["handler"] == handler
        assert command["legacy_cli_owned"] is False
        assert metadata["registry_phase"] == "handler-migrated-incremental"
        assert metadata["registration_status"] == "handler-migrated"
        assert metadata["handler_migration_performed"] is True
        assert metadata["migrated_by"] == "POST-H-030-B"
        assert metadata["runtime_router_enabled"] is False
        assert command["remote_execution_enabled"] is False
        assert command["connector_write_enabled"] is False
        assert command["plugin_execution_enabled"] is False


def test_post_h_030_b_cli_py_preserves_wrappers_but_delegates_result_building() -> None:
    source = (ROOT / "src/devpilot_core/cli.py").read_text(encoding="utf-8")
    module = (ROOT / "src/devpilot_core/cli_commands/industrial_readiness.py").read_text(encoding="utf-8")

    assert "handle_industrial_readiness_check" in source
    assert "handle_industrial_readiness_production_ready_local" in source
    assert "handle_industrial_readiness_production_ready_local_final" in source
    assert "IndustrialReadinessGate(root" not in source
    assert "ApplicationService(root).production_ready_local_gate" not in source
    assert "ApplicationService(root).production_ready_local_final_declaration" not in source
    assert "IndustrialReadinessGate" in module
    assert "ApplicationService(root).production_ready_local_gate" in module
    assert "ApplicationService(root).production_ready_local_final_declaration" in module


def test_post_h_030_b_cli_json_contract_matches_extracted_handlers(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    direct_check = handle_industrial_readiness_check(ROOT).to_dict()
    exit_code = cli.main(["industrial-readiness", "check", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == direct_check["exit_code"] == 0
    assert payload["command"] == direct_check["command"] == "industrial-readiness check"
    assert payload["ok"] == direct_check["ok"]
    assert payload["data"]["summary"]["industrial_readiness_score"] == direct_check["data"]["summary"]["industrial_readiness_score"]
    assert payload["data"]["summary"]["network_used"] is False
    assert payload["data"]["summary"]["external_api_used"] is False

    direct_prl = handle_industrial_readiness_production_ready_local(ROOT).to_dict()
    exit_code = cli.main(["industrial-readiness", "production-ready-local", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == direct_prl["exit_code"] == 0
    assert payload["command"] == direct_prl["command"] == "industrial-readiness production-ready-local"
    assert payload["data"]["summary"]["decision"] == direct_prl["data"]["summary"]["decision"]
    assert payload["data"]["report"]["claims"] == direct_prl["data"]["report"]["claims"]

    direct_final = handle_industrial_readiness_production_ready_local_final(ROOT).to_dict()
    exit_code = cli.main(["industrial-readiness", "production-ready-local-final", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == direct_final["exit_code"] == 0
    assert payload["command"] == direct_final["command"] == "industrial-readiness production-ready-local-final"
    assert payload["data"]["summary"]["decision"] == direct_final["data"]["summary"]["decision"]
    assert payload["data"]["report"]["claims"]["production_ready_local"] is True
    assert payload["data"]["report"]["claims"]["enterprise_ready"] is False


def test_post_h_030_b_ownership_matrix_and_extraction_plan_mark_industrial_family_migrated() -> None:
    matrix = _load(".devpilot/cli_registry/command_ownership_matrix.json")
    plan = _load(".devpilot/cli_registry/cli_extraction_plan.json")
    commands = {item["command_id"]: item for item in matrix["commands"]}

    assert matrix["summary"]["migration_state_counts"]["already-migrated"] >= 8
    for command_id in INDUSTRIAL_COMMANDS:
        item = commands[command_id]
        assert item["current_module"] == "src/devpilot_core/cli_commands/industrial_readiness.py"
        assert item["target_module"] == "src/devpilot_core/cli_commands/industrial_readiness.py"
        assert item["migration_state"] == "already-migrated"
        assert item["registry_phase"] == "handler-migrated-incremental"
        assert item["planned_micro_sprint"] == "POST-H-030-B"

    plan_items = {item["plan_id"]: item for item in plan["plan_items"]}
    industrial_plan = plan_items["post-h-030-b:src/devpilot_core/cli_commands/industrial_readiness.py"]
    assert industrial_plan["status"] == "already-started"
    assert set(industrial_plan["command_ids"]) == INDUSTRIAL_COMMANDS
    target_modules = {item["module_path"]: item for item in plan["target_modules"]}
    target = target_modules["src/devpilot_core/cli_commands/industrial_readiness.py"]
    assert target["exists_now"] is True
    assert target["creation_required"] is False


def test_post_h_030_b_governance_artifacts_are_synchronized() -> None:
    state = _load(".devpilot/project_state.json")
    source_registry = _load(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = _load(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = _load(".devpilot/testing/test_contract_registry_v2.json")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-030_cli_hotspot_reduction_application_boundaries.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")

    assert state.get("post_h_030_current_micro_sprint") in {"POST-H-030-B", "POST-H-030-C", "POST-H-030-D", "POST-H-030-E"}
    assert state.get("post_h_030_next_micro_sprint") in {"POST-H-030-C", "POST-H-030-D", "POST-H-030-E", "POST-H-031-A"}
    assert _post_h_number(state["last_completed_sprint"]) >= 30
    assert state["post_h_030_status"] in {"active/implemented-initial-post-h-030-b", "active/implemented-initial-post-h-030-c", "active/implemented-initial-post-h-030-d", "closed/cli-boundary-hotspot-reduction"}
    assert state["post_h_030_industrial_readiness_cli_module"] == "src/devpilot_core/cli_commands/industrial_readiness.py"
    assert state["post_h_030_industrial_readiness_commands_migrated_total"] == 3
    assert state["post_h_030_cli_public_behavior_changed"] is False

    assert any(marker in backlog for marker in ['current_micro_sprint: "POST-H-030-B"', 'current_micro_sprint: "POST-H-030-C"', 'current_micro_sprint: "POST-H-030-D"', 'current_micro_sprint: "POST-H-030-E"'])
    assert any(marker in backlog for marker in ['next_micro_sprint: "POST-H-030-C"', 'next_micro_sprint: "POST-H-030-D"', 'next_micro_sprint: "POST-H-030-E"', 'next_micro_sprint: "POST-H-031-A"'])
    assert "POST-H-030-B — Industrial readiness command extraction" in readme
    assert "POST-H-030-B — Industrial readiness command extraction" in runbook
    assert "post-h-030-b" in changelog.lower()

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert "POST-H-030-B-INDUSTRIAL-READINESS-CLI-MODULE" in doc_ids
    assert "POST-H-030-B-INDUSTRIAL-READINESS-EXTRACTION-REPORT" in doc_ids
    assert "POST-H-030-B-INDUSTRIAL-READINESS-TEST" in doc_ids

    assert any(c["contract_id"] == "post-h-030-industrial-readiness-command-extraction" for c in tcr_v1["contracts"])
    assert any(c["contract_id"] == "post-h-030-industrial-readiness-command-extraction" for c in tcr_v2["contracts"])


def test_post_h_030_b_cli_registry_guard_still_passes() -> None:
    exit_code = cli.main(["cli-registry", "guard", "--json"])

    assert exit_code == 0
