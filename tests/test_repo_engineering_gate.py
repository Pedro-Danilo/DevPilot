from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.repo import RepoEngineeringGate, RepoEngineeringGateConfig

ROOT = Path(__file__).resolve().parents[1]


def test_repo_engineering_gate_quick_passes_without_mutations() -> None:
    result = RepoEngineeringGate(ROOT, config=RepoEngineeringGateConfig(profile="quick")).run()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["status"] == "PASS"
    assert summary["profile"] == "quick"
    assert summary["mutations_performed"] is False
    assert summary["git_write_used"] is False
    assert summary["external_api_used"] is False
    assert summary["ready_for_phase_d_initial"] is True
    assert {component["source"] for component in result.data["components"]} >= {
        "git_status",
        "dependency_graph",
        "repo_analyzer",
        "architecture_drift",
        "repo_quality_gate",
        "miasi_phase_c",
        "phase_c_documents",
    }


def test_repo_engineering_gate_full_closure_checks_are_available() -> None:
    gate = RepoEngineeringGate(ROOT, config=RepoEngineeringGateConfig(profile="full", include_architecture_drift=False))

    docs_result = gate._validate_phase_c_documents(include_sprint_44=True)
    runtime_result = gate._validate_runtime_invariants()

    assert docs_result.ok is True
    assert runtime_result.ok is True
    assert docs_result.exit_code == ExitCode.PASS
    assert runtime_result.exit_code == ExitCode.PASS


def test_repo_engineering_gate_detects_missing_miasi_policy(tmp_path: Path) -> None:
    root = tmp_path
    (root / ".devpilot/miasi").mkdir(parents=True)
    (root / "docs/audits").mkdir(parents=True)
    (root / "src/devpilot_core/repo").mkdir(parents=True)
    (root / ".gitignore").write_text("outputs/\n.devpilot/rollback/\n", encoding="utf-8")
    (root / ".devpilot/miasi/tool_registry.json").write_text(json.dumps({"tools": []}), encoding="utf-8")
    (root / ".devpilot/miasi/policy_matrix.json").write_text(json.dumps({"rules": []}), encoding="utf-8")
    (root / ".devpilot/miasi/agent_registry.json").write_text(json.dumps({"agents": []}), encoding="utf-8")

    result = RepoEngineeringGate(root, config=RepoEngineeringGateConfig(profile="quick", include_architecture_drift=False))._validate_miasi_contracts()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "ENGINEERING_GATE_MIASI_TOOLS_MISSING" for finding in result.findings)
    assert any(finding.id == "ENGINEERING_GATE_MIASI_RULES_MISSING" for finding in result.findings)


def test_repo_engineering_gate_cli_contract_is_registered() -> None:
    cli_source = (ROOT / "src/devpilot_core/cli.py").read_text(encoding="utf-8")

    assert "repo_engineering_gate_command" in cli_source
    assert "repo_engineering_gate" in cli_source
    assert "engineering-gate" in cli_source
    assert "RepoEngineeringGateConfig" in cli_source
