from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core import cli
from devpilot_core.agents import AgentRuntime
from devpilot_core.cli_models import ExitCode


def _copy_agent_workspace(target: Path) -> None:
    source_root = Path.cwd()
    (target / ".devpilot").mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_root / ".devpilot" / "miasi", target / ".devpilot" / "miasi")
    shutil.copytree(source_root / "docs", target / "docs", dirs_exist_ok=True)
    (target / "pyproject.toml").write_text("[project]\nname='tmp-devpilot'\n", encoding="utf-8")


def test_agent_runtime_runs_precode_documentation_in_dry_run_without_writing(tmp_path: Path) -> None:
    _copy_agent_workspace(tmp_path)

    result = AgentRuntime(tmp_path).run("precode-documentation", idea="Agregar trazabilidad para agentes documentales", dry_run=True)

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["agent"]["agent_id"] == "precode.documentation"
    assert result.data["artifacts"]["written"] is False
    assert "preview" in result.data["artifacts"]
    assert not (tmp_path / result.data["artifacts"]["draft_path"]).exists()


def test_agent_runtime_blocks_precode_documentation_secret_payload(tmp_path: Path) -> None:
    _copy_agent_workspace(tmp_path)

    result = AgentRuntime(tmp_path).run("precode-documentation", idea="usar api_key=sk-1234567890abcdef", dry_run=True)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert "SECRETGUARD_SECRET_DETECTED" in {finding.id for finding in result.findings}


def test_agent_runtime_runs_documentation_audit_on_target(tmp_path: Path) -> None:
    _copy_agent_workspace(tmp_path)

    result = AgentRuntime(tmp_path).run("documentation-audit", target="docs/01_requirements", dry_run=True)

    assert result.command == "agent run"
    assert result.data["agent"]["agent_id"] == "precode.audit"
    assert result.data["artifacts"]["validated_files"] >= 1
    assert result.data["summary"]["tool_calls_total"] >= 2


def test_agent_runtime_blocks_unknown_agent(tmp_path: Path) -> None:
    _copy_agent_workspace(tmp_path)

    result = AgentRuntime(tmp_path).run("missing-agent", dry_run=True)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert "AGENT_RUNTIME_UNKNOWN_AGENT" in {finding.id for finding in result.findings}


def test_agent_cli_run_precode_documentation_json_and_report(tmp_path: Path, monkeypatch, capsys) -> None:
    _copy_agent_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main([
        "agent",
        "run",
        "precode-documentation",
        "--idea",
        "Crear control de cambios para documentos generados",
        "--dry-run",
        "--json",
        "--write-report",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "agent run"
    assert payload["data"]["agent"]["agent_id"] == "precode.documentation"
    assert payload["data"]["reports"]["json"] == "outputs/reports/agent_run_precode_documentation.json"
    assert (tmp_path / "outputs" / "reports" / "agent_run_precode_documentation.json").is_file()


def test_agent_cli_documentation_audit_json_is_parseable(tmp_path: Path, monkeypatch, capsys) -> None:
    _copy_agent_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["agent", "run", "documentation-audit", "--target", "docs/01_requirements", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["data"]["agent"]["agent_id"] == "precode.audit"
    assert payload["data"]["artifacts"]["target"] == "docs/01_requirements"
