from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_commands.validation import handle_validate_scope
from devpilot_core.cli_commands.workspace import handle_workspace_init, handle_workspace_status

ROOT = Path(__file__).resolve().parents[1]


def _create_minimal_docs(root: Path) -> None:
    (root / "docs" / "standards").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "checklists").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "checklists" / "checklist_pre_code.md").write_text("# Checklist\n", encoding="utf-8")


@lru_cache(maxsize=1)
def _registry_payload() -> dict:
    from devpilot_core.cli_registry.report import CliCommandRegistryReportBuilder

    return CliCommandRegistryReportBuilder(ROOT).build().data["registry"]


def _commands_by_id() -> dict[str, dict]:
    registry = _registry_payload()
    return {command["command_id"]: command for group in registry["groups"] for command in group["commands"]}


def test_post_h_006_c_workspace_init_handler_matches_cli_dry_run(tmp_path, monkeypatch, capsys) -> None:
    _create_minimal_docs(tmp_path)
    direct = handle_workspace_init(tmp_path, execute=False, project_id=None, project_name=None, project_type=None).to_dict()

    monkeypatch.chdir(tmp_path)
    exit_code = cli.main(["workspace", "init", "--dry-run", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == direct["exit_code"] == 0
    assert payload["command"] == direct["command"] == "workspace init"
    assert payload["ok"] == direct["ok"] is True
    assert payload["data"]["dry_run"] == direct["data"]["dry_run"] is True
    assert payload["data"]["plan"] == direct["data"]["plan"]
    assert not (tmp_path / ".devpilot" / "project.yaml").exists()


def test_post_h_006_c_workspace_status_handler_matches_cli_json(tmp_path, monkeypatch, capsys) -> None:
    _create_minimal_docs(tmp_path)
    handle_workspace_init(tmp_path, execute=True, project_id="demo", project_name="Demo", project_type="agent-assisted-sdlc")
    direct = handle_workspace_status(tmp_path).to_dict()

    monkeypatch.chdir(tmp_path)
    exit_code = cli.main(["workspace", "status", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == direct["exit_code"] == 0
    assert payload["command"] == direct["command"] == "workspace status"
    assert payload["ok"] == direct["ok"] is True
    for key in ["initialized", "ready", "docs_present", "standards_present", "precode_checklist_present"]:
        assert payload["data"]["summary"][key] == direct["data"]["summary"][key]


def test_post_h_006_c_validate_scope_handler_matches_cli_docs_contracts_all(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    for scope in ["docs", "contracts", "all"]:
        direct = handle_validate_scope(ROOT, scope).to_dict()
        exit_code = cli.main(["validate", scope, "--json"])
        payload = json.loads(capsys.readouterr().out)

        assert exit_code == direct["exit_code"]
        assert payload["command"] == direct["command"] == f"validate {scope}"
        assert payload["ok"] == direct["ok"]
        assert payload["data"]["summary"]["scope"] == direct["data"]["summary"]["scope"]
        assert payload["data"]["summary"]["validations_failed"] == direct["data"]["summary"]["validations_failed"]


def test_post_h_006_c_registry_marks_migrated_handlers_without_runtime_router() -> None:
    registry = _registry_payload()
    commands = _commands_by_id()
    summary = registry["summary"]

    assert registry["created_by"] == "POST-H-006-D"
    assert registry["generated_from"] == "static-cli-parser-ast-plus-declarative-descriptors-plus-migrated-handlers-plus-hotspot-ownership-report"
    assert registry["metadata"]["handler_migration_performed"] is True
    assert registry["metadata"]["runtime_router_enabled"] is False
    assert summary["migrated_handlers_total"] == 3
    assert set(summary["migrated_command_ids"]) == {"workspace.init", "workspace.status", "validate"}

    assert commands["workspace.init"]["owner_module"] == "src/devpilot_core/cli_commands/workspace.py"
    assert commands["workspace.init"]["handler"] == "handle_workspace_init"
    assert commands["workspace.status"]["handler"] == "handle_workspace_status"
    assert commands["validate"]["owner_module"] == "src/devpilot_core/cli_commands/validation.py"
    assert commands["validate"]["handler"] == "handle_validate_scope"

    for command_id in ["workspace.init", "workspace.status", "validate"]:
        metadata = commands[command_id]["metadata"]
        assert metadata["registry_phase"] == "handler-migrated-incremental"
        assert metadata["registration_status"] == "handler-migrated"
        assert metadata["handler_migration_performed"] is True
        assert metadata["runtime_router_enabled"] is False
        assert commands[command_id]["legacy_cli_owned"] is False


def test_post_h_006_c_cli_py_keeps_public_wrappers_but_delegates_logic() -> None:
    source = (ROOT / "src/devpilot_core/cli.py").read_text(encoding="utf-8")

    assert "from .cli_commands import handle_validate_scope, handle_workspace_init, handle_workspace_status" in source
    assert "return workspace_init_command(" in source
    assert "return workspace_status_command(" in source
    assert "return validate_gateway_command(" in source
    assert "result = handle_workspace_init(" in source
    assert "result = handle_workspace_status(root)" in source
    assert "result = handle_validate_scope(root, scope)" in source
    assert "ValidationGateway(root).validate_scope(scope)" not in source
