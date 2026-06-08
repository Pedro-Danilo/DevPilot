from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.miasi import MiasiRegistryValidator


def _copy_miasi_contract(target: Path) -> None:
    """Copy the repo's executable MIASI contract into a temporary workspace."""

    source_root = Path.cwd()
    (target / ".devpilot").mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_root / ".devpilot" / "miasi", target / ".devpilot" / "miasi")
    shutil.copytree(source_root / "docs" / "06_miasi", target / "docs" / "06_miasi", dirs_exist_ok=True)
    (target / "pyproject.toml").write_text("[project]\nname='tmp-devpilot'\n", encoding="utf-8")


def test_miasi_validate_all_passes_on_repo_contract() -> None:
    result = MiasiRegistryValidator(Path.cwd()).validate_all()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["agents_total"] >= 2
    assert result.data["summary"]["tools_total"] >= 10
    assert result.data["summary"]["policy_rules_total"] >= 8


def test_miasi_validate_agents_tools_and_policy_matrix_pass_individually() -> None:
    validator = MiasiRegistryValidator(Path.cwd())

    assert validator.validate_agents().ok is True
    assert validator.validate_tools().ok is True
    assert validator.validate_policy_matrix().ok is True


def test_miasi_cli_validate_json_and_write_report(tmp_path: Path, monkeypatch, capsys) -> None:
    _copy_miasi_contract(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["miasi", "validate", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "miasi validate"
    assert payload["data"]["summary"]["mvp_agents"] == 2
    assert payload["data"]["reports"]["json"] == "outputs/reports/miasi_validate.json"
    assert (tmp_path / "outputs" / "reports" / "miasi_validate.json").is_file()


def test_miasi_cli_validate_registry_and_tools_are_parseable(tmp_path: Path, monkeypatch, capsys) -> None:
    _copy_miasi_contract(tmp_path)
    monkeypatch.chdir(tmp_path)

    registry_exit = cli.main(["miasi", "validate-registry", "--json"])
    registry_payload = json.loads(capsys.readouterr().out)
    tools_exit = cli.main(["miasi", "validate-tools", "--json"])
    tools_payload = json.loads(capsys.readouterr().out)

    assert registry_exit == 0
    assert registry_payload["command"] == "miasi validate-registry"
    assert tools_exit == 0
    assert tools_payload["command"] == "miasi validate-tools"


def test_miasi_validator_blocks_missing_executable_configs(tmp_path: Path) -> None:
    (tmp_path / "docs" / "06_miasi").mkdir(parents=True)

    result = MiasiRegistryValidator(tmp_path).validate_all()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert {finding.id for finding in result.findings} == {"MIASI_CONFIG_MISSING"}


def test_miasi_validator_blocks_agent_with_unknown_tool(tmp_path: Path) -> None:
    _copy_miasi_contract(tmp_path)
    config_path = tmp_path / ".devpilot" / "miasi" / "agent_registry.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload["agents"][0]["allowed_tools"].append("missing.tool")
    config_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    result = MiasiRegistryValidator(tmp_path).validate_agents()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert "MIASI_AGENT_TOOL_UNKNOWN" in {finding.id for finding in result.findings}


def test_miasi_validator_blocks_high_autonomy_agent_without_approval(tmp_path: Path) -> None:
    _copy_miasi_contract(tmp_path)
    config_path = tmp_path / ".devpilot" / "miasi" / "agent_registry.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload["agents"][2]["max_autonomy"] = "A4"
    payload["agents"][2]["approval_required"] = False
    config_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    result = MiasiRegistryValidator(tmp_path).validate_agents()

    assert result.ok is False
    assert "MIASI_AGENT_APPROVAL_REQUIRED" in {finding.id for finding in result.findings}


def test_miasi_validator_blocks_tool_without_policy_coverage(tmp_path: Path) -> None:
    _copy_miasi_contract(tmp_path)
    config_path = tmp_path / ".devpilot" / "miasi" / "tool_registry.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload["tools"][0]["policy_rule_ids"] = []
    config_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    result = MiasiRegistryValidator(tmp_path).validate_tools()

    assert result.ok is False
    assert "MIASI_TOOL_POLICY_MISSING" in {finding.id for finding in result.findings}
