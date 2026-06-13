from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core import cli
from devpilot_core.agents import AgentRuntime
from devpilot_core.cli_models import ExitCode
from devpilot_core.evals import EvalRunner

ROOT = Path(__file__).resolve().parents[1]


def _copy_agent_workspace(target: Path) -> None:
    (target / ".devpilot").mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / ".devpilot" / "miasi", target / ".devpilot" / "miasi")
    shutil.copytree(ROOT / ".devpilot" / "testing", target / ".devpilot" / "testing", dirs_exist_ok=True)
    shutil.copytree(ROOT / "docs", target / "docs", dirs_exist_ok=True)
    shutil.copytree(ROOT / "evals", target / "evals", dirs_exist_ok=True)
    (target / ".devpilot" / "providers.yaml.example").write_text((ROOT / ".devpilot" / "providers.yaml.example").read_text(encoding="utf-8"), encoding="utf-8")
    (target / "pyproject.toml").write_text("[project]\nname='tmp-devpilot-refactor-testplanner-agents'\n", encoding="utf-8")


def _long_function() -> str:
    body = "def complex_value(items):\n    total = 0\n"
    for index in range(15):
        body += f"    if len(items) > {index}:\n        total += {index}\n"
    body += "    return total\n"
    return body


def test_safe_refactor_agent_plan_only_uses_mock_model(tmp_path: Path) -> None:
    _copy_agent_workspace(tmp_path)
    source = tmp_path / "src" / "refactor_target.py"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(_long_function(), encoding="utf-8")

    result = AgentRuntime(tmp_path).run("safe-refactor", target="src", idea="Extract focused helpers", provider="mock", dry_run=True)

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["agent"]["agent_id"] == "safe.refactor"
    assert result.data["metadata"]["monoagent"] is True
    assert result.data["metadata"]["handoffs_enabled"] is False
    assert result.data["summary"]["model_calls_total"] == 1
    assert result.data["artifacts"]["plan_only"] is True
    assert result.data["artifacts"]["refactor_executor_invoked"] is False
    assert result.data["artifacts"]["mutations_performed"] is False
    assert result.data["artifacts"]["files_modified"] == 0
    assert result.data["model_calls"][0]["prompt_id"] == "safe.refactor.agent"
    assert any(finding.id == "MODEL_ADAPTER_PASS" for finding in result.findings)


def test_safe_refactor_agent_blocks_non_dry_run_execution(tmp_path: Path) -> None:
    _copy_agent_workspace(tmp_path)
    source = tmp_path / "src" / "target.py"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("def ok() -> str:\n    return 'ok'\n", encoding="utf-8")

    result = AgentRuntime(tmp_path).run("safe-refactor", target="src", dry_run=False)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    ids = {finding.id for finding in result.findings}
    assert "SAFE_REFACTOR_EXECUTION_BLOCKED" in ids
    assert result.data["artifacts"]["mutations_performed"] is False


def test_test_planner_agent_traceability_plan_uses_mock_model(tmp_path: Path) -> None:
    _copy_agent_workspace(tmp_path)
    doc = tmp_path / "docs" / "requirements.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("# Requirements\n\nREQ-001 is covered by AC-001 and TEST-001.\n\nUS-001 links to AC-001.\n", encoding="utf-8")

    result = AgentRuntime(tmp_path).run("test-planner", target="docs/requirements.md", idea="Plan tests", provider="mock", dry_run=True)

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["agent"]["agent_id"] == "testplanner.agent"
    assert result.data["summary"]["model_calls_total"] == 1
    assert result.data["artifacts"]["plan_only"] is True
    assert result.data["artifacts"]["tests_run_executed"] is False
    assert result.data["artifacts"]["arbitrary_commands_allowed"] is False
    assert result.data["artifacts"]["summary"]["plan_items_total"] >= 3
    assert result.data["model_calls"][0]["prompt_id"] == "test.planner.agent"
    assert any(finding.id == "MODEL_ADAPTER_PASS" for finding in result.findings)


def test_test_planner_agent_blocks_non_dry_run_test_execution(tmp_path: Path) -> None:
    _copy_agent_workspace(tmp_path)

    result = AgentRuntime(tmp_path).run("test-planner", target="docs/01_requirements", dry_run=False)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    ids = {finding.id for finding in result.findings}
    assert "TEST_PLANNER_EXECUTION_BLOCKED" in ids
    assert "APPROVAL_REQUIRED_MISSING" in ids
    assert result.data["artifacts"]["tests_run_executed"] is False


def test_refactor_testplanner_agents_cli_and_eval_cases_are_parseable(tmp_path: Path, monkeypatch, capsys) -> None:
    _copy_agent_workspace(tmp_path)
    source = tmp_path / "src" / "refactor_target.py"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(_long_function(), encoding="utf-8")
    doc = tmp_path / "docs" / "requirements.md"
    doc.write_text("# Requirements\n\nREQ-002 is covered by AC-002 and TEST-002.\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["agent", "run", "safe-refactor", "--target", "src", "--provider", "mock", "--json"])
    refactor_payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert refactor_payload["data"]["agent"]["agent_id"] == "safe.refactor"
    assert refactor_payload["data"]["artifacts"]["plan_only"] is True

    exit_code = cli.main(["agent", "run", "test-planner", "--target", "docs/requirements.md", "--provider", "mock", "--json"])
    test_payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert test_payload["data"]["agent"]["agent_id"] == "testplanner.agent"
    assert test_payload["data"]["artifacts"]["tests_run_executed"] is False

    eval_refactor = EvalRunner(tmp_path).run(case_id="agent-safe-refactor-plan-model-aware-mock")
    eval_tests = EvalRunner(tmp_path).run(case_id="agent-test-planner-traceability-model-aware-mock")

    assert eval_refactor.ok is True
    assert eval_tests.ok is True
