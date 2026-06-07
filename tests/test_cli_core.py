from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli import build_miasi_required_result, build_readiness_result, main
from devpilot_core.cli_models import ExitCode


def test_readiness_result_uses_common_contract():
    root = Path(__file__).resolve().parents[1]
    result = build_readiness_result(root)

    assert result.command == "readiness-check"
    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["ok"] is True


def test_miasi_required_result_uses_common_contract():
    result = build_miasi_required_result()

    assert result.command == "miasi-required"
    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["miasi_required"] is True
    assert "docs/06_miasi/agent_card.md" in result.data["required_artifacts"]


def test_readiness_check_json_output_is_parseable(capsys):
    exit_code = main(["readiness-check", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["command"] == "readiness-check"
    assert payload["ok"] is True
    assert payload["exit_code"] == 0


def test_miasi_required_json_output_is_parseable(capsys):
    exit_code = main(["miasi-required", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["command"] == "miasi-required"
    assert payload["ok"] is True
    assert payload["data"]["miasi_required"] is True


def test_version_command_remains_compatible(capsys):
    exit_code = main(["--version"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "devpilot-local" in captured.out
