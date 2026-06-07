from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli import main
from devpilot_core.cli_models import ExitCode
from devpilot_core.standards.registry import StandardsRegistry, build_standards_status_result


ROOT = Path(__file__).resolve().parents[1]


def test_standards_registry_detects_mipsoftware_and_miasi():
    registry = StandardsRegistry(ROOT)
    standards = registry.discover_standards()

    ids = {standard.id for standard in standards}
    assert {"mipsoftware", "miasi"} <= ids
    assert all(standard.ok for standard in standards)


def test_standards_status_result_uses_common_contract():
    result = build_standards_status_result(ROOT)

    assert result.command == "standards status"
    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["standards_ok"] == 2
    assert result.data["summary"]["validation_profiles_total"] > 0
    assert any(item["id"] == "agent_card" for item in result.data["required_project_artifacts"])


def test_standards_status_cli_json_is_parseable(capsys):
    exit_code = main(["standards", "status", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["command"] == "standards status"
    assert payload["ok"] is True
    assert payload["data"]["standards_root"] == "docs/standards"


def test_standards_registry_blocks_when_standard_directory_missing(tmp_path):
    (tmp_path / "docs" / "standards" / "mipsoftware").mkdir(parents=True)
    (tmp_path / "docs" / "standards" / "mipsoftware" / "README.md").write_text(
        """---
title: "MIPSoftware"
doc_id: "TMP-MIPS"
status: "approved"
version: "1.0.0"
owner: "Test"
updated: "2026-06-07"
approval: "test"
---
# MIPSoftware
""",
        encoding="utf-8",
    )

    result = build_standards_status_result(tmp_path)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "STANDARD_DIRECTORY_MISSING" for finding in result.findings)
