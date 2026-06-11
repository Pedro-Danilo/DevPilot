from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint_31_readme_runbook_and_phase_b_backlog_are_synchronized() -> None:
    readme = _read("README.md")
    runbook = _read("docs/05_operations/runbook.md")
    phase_b = _read("docs/devpilot_backlog_fase_B_seguridad_operacional.md")

    assert "FUNC-SPRINT-31 — SafeSubprocessRunner" in readme
    assert "FUNC-SPRINT-31 — SafeSubprocessRunner" in runbook
    assert "Estado de implementación Sprint 31" in phase_b
    assert 'source_repo: "repo_DevPilot_Local_39.zip"' in phase_b
    assert 'first_open_sprint: "FUNC-SPRINT-35"' in phase_b
    assert "FUNC-SPRINT-32 — tests.run" in readme
    assert "FUNC-SPRINT-32 — tests.run" in runbook
    assert "No expone todavía un CLI público" in readme or "No hay CLI pública" in runbook


def test_sprint_31_manifest_declares_execution_boundary_and_no_adr_needed() -> None:
    payload = json.loads((ROOT / "docs/functional_sprint_31_manifest.json").read_text(encoding="utf-8"))

    assert payload["sprint"] == "FUNC-SPRINT-31"
    assert payload["status"] == "implemented"
    assert payload["architectural_decision"]["required"] is False
    assert "src/devpilot_core/execution/safe_subprocess.py" in payload["created_files"]
    assert ".devpilot/execution/command_allowlist.json" in payload["created_files"]
    assert payload["next_sprint"].startswith("FUNC-SPRINT-32")


def test_sprint_31_audit_documents_limits_and_runner_controls() -> None:
    audit = _read("docs/audits/func_sprint_31_safe_subprocess_runner_audit.md")

    for required in ["Propósito", "Funcionamiento técnico", "Criterios PASS", "Criterios BLOCK", "Riesgos", "Veredicto"]:
        assert required in audit
    assert "implemented-initial" in audit
    assert "shell=False" in audit
    assert "No hay CLI pública" in audit
    assert "tests.run" in audit


def test_sprint_31_allowlist_is_narrow_and_controlled() -> None:
    payload = json.loads((ROOT / ".devpilot/execution/command_allowlist.json").read_text(encoding="utf-8"))
    commands = payload["commands"]
    command_ids = {command["command_id"] for command in commands}

    assert command_ids == {"python.pytest", "git.apply.check"}
    pytest_command = next(command for command in commands if command["command_id"] == "python.pytest")
    git_check_command = next(command for command in commands if command["command_id"] == "git.apply.check")
    assert pytest_command["args_prefix"] == ["-m", "pytest"]
    assert git_check_command["args_prefix"] == ["apply", "--check"]
    assert commands[0]["max_timeout_seconds"] <= 120
