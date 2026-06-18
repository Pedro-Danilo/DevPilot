from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_35_manifest_and_audit_exist() -> None:
    manifest = json.loads(_read("docs/functional_sprint_35_manifest.json"))
    audit = _read("docs/audits/func_sprint_35_git_adapter_v2_audit.md")

    assert manifest["sprint"] == "FUNC-SPRINT-35"
    assert manifest["status"] == "implemented"
    assert "src/devpilot_core/repo/diff_report.py" in manifest["created_files"]
    assert "src/devpilot_core/repo/git_adapter.py" in manifest["modified_files"]
    assert "tests/test_git_adapter_v2.py" in manifest["tests"]
    assert manifest["architectural_decision"]["required"] is False
    assert "GitAdapter v2 read-only" in audit
    assert "shell=False" in audit


def test_sprint_35_readme_runbook_and_phase_c_backlog_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    backlog = _read("docs/devpilot_backlog_fase_C_ingenieria_repositorio.md")

    assert "Último hito: `FUNC-SPRINT-85" in readme
    assert "Siguiente hito: `FUNC-SPRINT-86" in readme
    assert "## FUNC-SPRINT-35 — GitAdapter v2 read-only" in runbook
    assert "python -m devpilot_core git diff-report --json --write-report" in runbook
    assert 'phase_c_status: "completed"' in backlog
    assert 'first_open_sprint: "FUNC-SPRINT-45"' in backlog
    assert "Estado de implementación Sprint 35" in backlog


def test_sprint_35_miasi_git_tools_declared() -> None:
    registry = json.loads(_read(".devpilot/miasi/tool_registry.json"))
    tool_ids = {tool["tool_id"] for tool in registry["tools"]}
    tool_card = _read("docs/06_miasi/tool_card.md")
    tool_registry_doc = _read("docs/06_miasi/tool_registry.md")

    assert {"git.branches", "git.tags", "git.log", "git.diff_report"}.issubset(tool_ids)
    assert "Tool Card — GitAdapter v2 read-only" in tool_card
    assert "Estado operacional GitAdapter v2" in tool_registry_doc


def test_sprint_35_functional_backlog_points_to_sprint_36_without_overclaiming() -> None:
    functional_backlog = _read("docs/functional_backlog_after_precode.md")
    assert 'next_sprint: "FUNC-SPRINT-86"' in functional_backlog
    assert "Transición posterior a FUNC-SPRINT-35" in functional_backlog
    assert "No habilita patch apply" in functional_backlog
