from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core import cli
from devpilot_core.agents import AgentRuntime
from devpilot_core.evals import EvalRunner
from devpilot_core.cli_models import ExitCode

ROOT = Path(__file__).resolve().parents[1]


def _copy_repo_agent_workspace(target: Path) -> None:
    (target / ".devpilot").mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / ".devpilot" / "miasi", target / ".devpilot" / "miasi")
    shutil.copytree(ROOT / "docs", target / "docs", dirs_exist_ok=True)
    shutil.copytree(ROOT / "evals", target / "evals", dirs_exist_ok=True)
    (target / ".devpilot" / "providers.yaml.example").write_text((ROOT / ".devpilot" / "providers.yaml.example").read_text(encoding="utf-8"), encoding="utf-8")
    (target / "pyproject.toml").write_text("[project]\nname='tmp-devpilot-repo-agent'\n", encoding="utf-8")


def test_repo_analysis_agent_runs_read_only_without_model(tmp_path: Path) -> None:
    _copy_repo_agent_workspace(tmp_path)

    result = AgentRuntime(tmp_path).run("repo-analysis", target=".", dry_run=True)

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["agent"]["agent_id"] == "repo.analysis"
    assert result.data["metadata"]["monoagent"] is True
    assert result.data["metadata"]["handoffs_enabled"] is False
    assert result.data["summary"]["model_calls_total"] == 0
    assert result.data["artifacts"]["mutations_performed"] is False
    assert {call["tool_id"] for call in result.data["tool_calls"]} >= {"repo.analyze", "repo.dependency_graph", "git.status", "repo.quality_gate"}


def test_repo_analysis_agent_uses_mock_model_aware_path(tmp_path: Path) -> None:
    _copy_repo_agent_workspace(tmp_path)

    result = AgentRuntime(tmp_path).run("repo-analysis", target=".", provider="mock", dry_run=True)

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["model_calls_total"] == 1
    call = result.data["model_calls"][0]
    assert call["provider"] == "mock"
    assert call["prompt_id"] == "repo.analysis.agent"
    assert call["prompt_payload_redacted"] is True
    assert call["raw_prompt_stored"] is False
    assert call["raw_output_stored"] is False
    assert call["external_api_used"] is False
    assert any(finding.id == "MODEL_ADAPTER_PASS" for finding in result.findings)


def test_repo_analysis_agent_blocks_target_outside_workspace(tmp_path: Path) -> None:
    _copy_repo_agent_workspace(tmp_path)
    outside = tmp_path.parent / "outside-repo-agent-target"
    outside.mkdir(exist_ok=True)

    result = AgentRuntime(tmp_path).run("repo-analysis", target=str(outside), dry_run=True)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.severity.value == "block" for finding in result.findings)
    assert result.data["artifacts"]["mutations_performed"] is False


def test_repo_analysis_agent_cli_and_eval_case_are_parseable(tmp_path: Path, monkeypatch, capsys) -> None:
    _copy_repo_agent_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["agent", "run", "repo-analysis", "--target", ".", "--provider", "mock", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["data"]["agent"]["agent_id"] == "repo.analysis"
    assert payload["data"]["summary"]["model_calls_total"] == 1
    assert payload["data"]["metadata"]["handoffs_enabled"] is False

    eval_result = EvalRunner(tmp_path).run(case_id="agent-repo-analysis-model-aware-mock")

    assert eval_result.ok is True
    assert any(case["component"] == "agent.repo_analysis_model_aware" for case in eval_result.data["cases"])
