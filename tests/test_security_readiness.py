from __future__ import annotations

from pathlib import Path

from devpilot_core import cli
from devpilot_core.security import PolicySimulationSuite, SecurityReadiness


def test_policy_simulation_standard_matrix_passes() -> None:
    root = Path(__file__).resolve().parents[1]

    result = PolicySimulationSuite(root).run(matrix="standard")

    assert result.ok is True
    assert result.exit_code == 0
    assert result.data["summary"]["cases_total"] >= 7
    assert result.data["summary"]["cases_failed"] == 0
    case_ids = {case["case_id"] for case in result.data["cases"]}
    assert {"missing-approval", "valid-approval", "wrong-scope", "expired-approval"}.issubset(case_ids)


def test_security_readiness_passes_against_repo() -> None:
    root = Path(__file__).resolve().parents[1]

    result = SecurityReadiness(root).run()

    assert result.ok is True
    assert result.exit_code == 0
    assert result.data["summary"]["phase_b_closed"] is True
    gate_ids = {gate["gate_id"] for gate in result.data["gates"]}
    assert {
        "phase_b_exit_artifacts",
        "miasi_registry",
        "approval_workflow",
        "policy_approval_binding",
        "approval_required_negative_case",
        "tests_run_controlled",
        "security_guards",
        "policy_simulation_matrix",
        "no_destructive_capabilities",
    }.issubset(gate_ids)


def test_policy_simulate_matrix_cli_writes_report(capsys) -> None:
    exit_code = cli.main(["policy", "simulate", "--matrix", "standard", "--json", "--write-report"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"command": "policy simulate"' in output
    assert '"matrix": "standard"' in output
    assert Path("outputs/reports/policy_simulate_standard.json").is_file()


def test_security_readiness_cli_writes_report(capsys) -> None:
    exit_code = cli.main(["security", "readiness", "--json", "--write-report"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"command": "security readiness"' in output
    assert '"phase_b_closed": true' in output
    assert Path("outputs/reports/security_readiness.json").is_file()
