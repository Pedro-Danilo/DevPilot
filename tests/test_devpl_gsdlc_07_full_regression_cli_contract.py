from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli import build_parser
from devpilot_core.cli_registry.growth_gate import CliNoGrowthGate
from devpilot_core.cli_registry.registry import DeclarativeCliRegistryBuilder


def test_full_session_cli_surface_is_registered() -> None:
    parser = build_parser()
    args = parser.parse_args(["tests", "full-session", "collect", "--session-id", "demo", "--target", "tests/test_api_contract.py", "--json"])
    assert args.command == "tests"
    assert args.tests_command == "full-session"
    assert args.full_session_command == "collect"
    registry = DeclarativeCliRegistryBuilder(Path.cwd()).build_registry().to_dict()
    command_ids = {command["command_id"] for group in registry["groups"] for command in group["commands"]}
    for action in ("collect", "plan", "run", "resume", "status", "adjudicate"):
        assert f"tests.full-session.{action}" in command_ids


def test_cli_no_growth_gate_accepts_full_session_commands() -> None:
    result = CliNoGrowthGate(Path.cwd()).run()
    assert result.ok, result.to_dict()
