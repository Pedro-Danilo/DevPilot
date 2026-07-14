from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.testing.project_state_progress import post_h_progress_rank as _post_h_number

from devpilot_core import cli
from devpilot_core.cli_commands import (
    handle_portfolio_hardening_gate,
    handle_portfolio_status,
    handle_workspace_bootstrap,
    handle_workspace_isolation_check,
    handle_workspace_list,
    handle_workspace_readiness_preview,
    handle_workspace_registry_validate,
)
from devpilot_core.cli_registry.registry import DeclarativeCliRegistryBuilder

ROOT = Path(__file__).resolve().parents[1]



POST_H_030_D_COMMANDS = {
    "workspace.isolation-check",
    "workspace.list",
    "workspace.register",
    "workspace.registry-validate",
    "workspace.select",
    "portfolio.hardening-gate",
    "portfolio.status",
}

WORKSPACE_ONBOARDING_BOUNDARY_COMMANDS = POST_H_030_D_COMMANDS | {
    "workspace.bootstrap",
    "workspace.init",
    "workspace.readiness-preview",
    "workspace.status",
}


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _commands_by_id() -> dict[str, dict]:
    registry = DeclarativeCliRegistryBuilder(ROOT).build_registry().to_dict()
    return {command["command_id"]: command for group in registry["groups"] for command in group["commands"]}


def test_post_h_030_d_workspace_and_portfolio_handlers_are_extracted_without_runtime_router() -> None:
    commands = _commands_by_id()

    missing = sorted(POST_H_030_D_COMMANDS - set(commands))
    assert missing == []
    for command_id in sorted(POST_H_030_D_COMMANDS):
        command = commands[command_id]
        metadata = command["metadata"]
        assert command["handler"].startswith("handle_")
        assert command["legacy_cli_owned"] is False
        assert metadata["registry_phase"] == "handler-migrated-incremental"
        assert metadata["registration_status"] == "handler-migrated"
        assert metadata["handler_migration_performed"] is True
        assert metadata["migrated_by"] == "POST-H-030-D"
        assert metadata["runtime_router_enabled"] is False
        assert command["remote_execution_enabled"] is False
        assert command["connector_write_enabled"] is False
        assert command["plugin_execution_enabled"] is False

    assert commands["workspace.register"]["owner_module"] == "src/devpilot_core/cli_commands/workspace.py"
    assert commands["workspace.list"]["owner_module"] == "src/devpilot_core/cli_commands/workspace.py"
    assert commands["portfolio.status"]["owner_module"] == "src/devpilot_core/cli_commands/workspace_onboarding.py"
    assert commands["portfolio.hardening-gate"]["owner_module"] == "src/devpilot_core/cli_commands/workspace_onboarding.py"


def test_post_h_030_d_cli_py_preserves_wrappers_but_delegates_workspace_result_building() -> None:
    source = (ROOT / "src/devpilot_core/cli.py").read_text(encoding="utf-8")
    workspace_module = (ROOT / "src/devpilot_core/cli_commands/workspace.py").read_text(encoding="utf-8")
    onboarding_module = (ROOT / "src/devpilot_core/cli_commands/workspace_onboarding.py").read_text(encoding="utf-8")

    for handler in [
        "handle_workspace_register",
        "handle_workspace_list",
        "handle_workspace_select",
        "handle_workspace_registry_validate",
        "handle_workspace_isolation_check",
    ]:
        assert handler in source
        assert f"def {handler}" in workspace_module
    for handler in ["handle_portfolio_status", "handle_portfolio_hardening_gate"]:
        assert handler in source
        assert f"def {handler}" in onboarding_module

    assert "runtime_router_enabled = True" not in source
    assert "importlib" not in workspace_module
    assert "importlib" not in onboarding_module
    assert "subprocess.run" not in workspace_module
    assert "subprocess.run" not in onboarding_module


def test_post_h_030_d_cli_json_contract_matches_selected_extracted_handlers(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    direct_list = handle_workspace_list(ROOT).to_dict()
    exit_code = cli.main(["workspace", "list", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == direct_list["exit_code"] == 0
    assert payload["command"] == direct_list["command"] == "workspace list"
    assert payload["data"]["summary"]["workspaces_total"] == direct_list["data"]["summary"]["workspaces_total"]
    assert payload["data"]["summary"]["network_used"] is False

    direct_registry = handle_workspace_registry_validate(ROOT, registry_version="v2").to_dict()
    exit_code = cli.main(["workspace", "registry-validate", "--registry-version", "v2", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == direct_registry["exit_code"] == 0
    assert payload["command"] == direct_registry["command"] == "workspace registry validate v2"
    assert payload["data"]["summary"]["v2_schema_valid"] is True
    assert payload["data"]["summary"]["mutations_performed"] is False

    direct_portfolio = handle_portfolio_status(ROOT).to_dict()
    exit_code = cli.main(["portfolio", "status", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == direct_portfolio["exit_code"] == 0
    assert payload["command"] == direct_portfolio["command"] == "portfolio status"
    assert payload["data"]["summary"]["portfolio_status_read_only"] is True


def test_post_h_030_d_onboarding_dry_run_and_readiness_safety_are_preserved(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    direct_bootstrap = handle_workspace_bootstrap(
        ROOT,
        project_id="post-h-030-d-demo",
        project_name="POST-H-030-D Demo",
        target_root="outputs/test_post_h_030_d/demo-project",
        execute=False,
        write_report=False,
    ).to_dict()
    assert direct_bootstrap["exit_code"] == 0
    assert direct_bootstrap["data"]["summary"]["mode"] == "dry-run"
    assert direct_bootstrap["data"]["summary"]["mutations_performed"] is False
    assert not (ROOT / "outputs/test_post_h_030_d/demo-project").exists()

    exit_code = cli.main([
        "workspace",
        "bootstrap",
        "--project-id",
        "post-h-030-d-demo",
        "--project-name",
        "POST-H-030-D Demo",
        "--target-root",
        "outputs/test_post_h_030_d/cli-demo-project",
        "--dry-run",
        "--json",
    ])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "workspace bootstrap"
    assert payload["data"]["summary"]["mode"] == "dry-run"
    assert payload["data"]["summary"]["mutations_performed"] is False
    assert not (ROOT / "outputs/test_post_h_030_d/cli-demo-project").exists()

    direct_preview = handle_workspace_readiness_preview(
        ROOT,
        target_root="outputs/bootstrap_workspaces/ventas-micro-local",
        write_report=False,
    ).to_dict()
    assert direct_preview["data"]["summary"]["network_used"] is False
    assert direct_preview["data"]["summary"]["external_api_used"] is False
    assert direct_preview["data"]["summary"].get("source_mutations_performed", False) is False


def test_post_h_030_d_workspace_isolation_and_portfolio_gate_remain_local_first(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    direct_isolation = handle_workspace_isolation_check(ROOT).to_dict()
    assert direct_isolation["exit_code"] == 0
    assert direct_isolation["data"]["summary"]["network_used"] is False
    assert direct_isolation["data"]["summary"]["external_api_used"] is False
    assert direct_isolation["data"]["summary"].get("source_mutations_performed", False) is False

    exit_code = cli.main(["workspace", "isolation-check", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == direct_isolation["command"] == "workspace isolation-check"
    assert payload["data"]["summary"]["path_guard_aligned"] is True

    direct_gate = handle_portfolio_hardening_gate(ROOT).to_dict()
    exit_code = cli.main(["portfolio", "hardening-gate", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == direct_gate["exit_code"] == 0
    assert payload["command"] == direct_gate["command"] == "quality workspace-portfolio-hardening"
    assert payload["data"]["summary"]["network_used"] is False
    assert payload["data"]["summary"]["external_api_used"] is False


def test_post_h_030_d_ownership_matrix_and_extraction_plan_mark_workspace_family_migrated() -> None:
    matrix = _load(".devpilot/cli_registry/command_ownership_matrix.json")
    plan = _load(".devpilot/cli_registry/cli_extraction_plan.json")
    commands = {item["command_id"]: item for item in matrix["commands"]}

    assert matrix["summary"]["migration_state_counts"]["already-migrated"] >= 41
    for command_id in POST_H_030_D_COMMANDS:
        item = commands[command_id]
        assert item["migration_state"] == "already-migrated"
        assert item["registry_phase"] == "handler-migrated-incremental"
        assert item["planned_micro_sprint"] == "POST-H-030-D"
        assert item["current_module"] == item["target_module"]

    for command_id in WORKSPACE_ONBOARDING_BOUNDARY_COMMANDS:
        assert commands[command_id]["migration_state"] == "already-migrated"

    plan_items = {item["plan_id"]: item for item in plan["plan_items"]}
    workspace_plan = plan_items["post-h-030-d:src/devpilot_core/cli_commands/workspace.py"]
    portfolio_plan = plan_items["post-h-030-d:src/devpilot_core/cli_commands/workspace_onboarding.py"]
    assert workspace_plan["status"] == "already-started"
    assert portfolio_plan["status"] == "already-started"
    assert set(workspace_plan["command_ids"]) == {
        "workspace.isolation-check",
        "workspace.list",
        "workspace.register",
        "workspace.registry-validate",
        "workspace.select",
    }
    assert set(portfolio_plan["command_ids"]) == {"portfolio.hardening-gate", "portfolio.status"}


def test_post_h_030_d_governance_artifacts_are_synchronized() -> None:
    state = _load(".devpilot/project_state.json")
    source_registry = _load(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = _load(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = _load(".devpilot/testing/test_contract_registry_v2.json")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-030_cli_hotspot_reduction_application_boundaries.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")

    assert state.get("post_h_030_current_micro_sprint") in {"POST-H-030-D", "POST-H-030-E"}
    assert state.get("post_h_030_next_micro_sprint") in {"POST-H-030-E", "POST-H-031-A"}
    assert _post_h_number(state["last_completed_sprint"]) >= 30
    assert state["post_h_030_status"] in {"active/implemented-initial-post-h-030-d", "closed/cli-boundary-hotspot-reduction"}
    assert state["post_h_030_workspace_cli_module"] == "src/devpilot_core/cli_commands/workspace.py"
    assert state["post_h_030_workspace_onboarding_cli_module"] == "src/devpilot_core/cli_commands/workspace_onboarding.py"
    assert state["post_h_030_workspace_onboarding_commands_migrated_total"] == len(POST_H_030_D_COMMANDS)
    assert state["post_h_030_workspace_onboarding_public_behavior_changed"] is False

    assert any(marker in backlog for marker in ['current_micro_sprint: "POST-H-030-D"', 'current_micro_sprint: "POST-H-030-E"'])
    assert any(marker in backlog for marker in ['next_micro_sprint: "POST-H-030-E"', 'next_micro_sprint: "POST-H-031-A"'])
    assert "POST-H-030-D — Workspace/onboarding command extraction" in readme
    assert "POST-H-030-D — Workspace/onboarding command extraction" in runbook
    assert "post-h-030-d" in changelog.lower()

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert "POST-H-030-D-WORKSPACE-CLI-MODULE" in doc_ids
    assert "POST-H-030-D-WORKSPACE-ONBOARDING-CLI-MODULE" in doc_ids
    assert "POST-H-030-D-WORKSPACE-ONBOARDING-REPORT" in doc_ids
    assert "POST-H-030-D-WORKSPACE-ONBOARDING-TEST" in doc_ids

    assert any(c["contract_id"] == "post-h-030-workspace-onboarding-command-extraction" for c in tcr_v1["contracts"])
    assert any(c["contract_id"] == "post-h-030-workspace-onboarding-command-extraction" for c in tcr_v2["contracts"])


def test_post_h_030_d_cli_registry_guard_still_passes() -> None:
    exit_code = cli.main(["cli-registry", "guard", "--json"])

    assert exit_code == 0
