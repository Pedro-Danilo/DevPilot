from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_32_manifest_and_audit_exist_and_are_synchronized() -> None:
    manifest = json.loads(_read("docs/functional_sprint_32_manifest.json"))
    audit = _read("docs/audits/func_sprint_32_tests_run_tool_audit.md")

    assert manifest["sprint"] == "FUNC-SPRINT-32"
    assert manifest["status"] == "implemented"
    assert "src/devpilot_core/testing/tests_run.py" in manifest["created_files"]
    assert "tests/test_tests_run_tool.py" in manifest["tests"]
    assert "FUNC-SPRINT-32" in audit
    assert "tests.run" in audit
    assert "implemented-initial" in audit


def test_sprint_32_readme_runbook_and_backlog_point_to_sprint_33() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_B_seguridad_operacional.md")

    assert "Último hito: `FUNC-SPRINT-92" in readme
    assert "Siguiente hito: `FUNC-SPRINT-93" in readme
    assert "FUNC-SPRINT-32" in runbook
    assert "tests run --profile smoke" in runbook
    assert 'first_open_sprint: "FUNC-SPRINT-35"' in backlog
    assert "`FUNC-SPRINT-32` queda implementado" in backlog


def test_sprint_32_miasi_tool_registry_is_implemented_initial() -> None:
    registry = json.loads(_read(".devpilot/miasi/tool_registry.json"))
    tools = {tool["tool_id"]: tool for tool in registry["tools"]}

    assert tools["tests.run"]["status"] == "implemented-initial"
    assert tools["tests.run"]["requires_approval"] is True
    assert tools["tests.run"]["side_effect"] == "controlled_execution"

    tool_registry_doc = _read("docs/06_miasi/tool_registry.md")
    tool_card = _read("docs/06_miasi/tool_card.md")
    assert "tests.run" in tool_registry_doc
    assert "implemented-initial" in tool_registry_doc
    assert "SafeSubprocessRunner" in tool_card


def test_sprint_32_profiles_config_exists() -> None:
    profiles = json.loads(_read(".devpilot/testing/test_profiles.json"))
    ids = {profile["profile_id"] for profile in profiles["profiles"]}

    assert {"smoke", "unit", "all"}.issubset(ids)
    assert profiles["created_by"] == "FUNC-SPRINT-32"
