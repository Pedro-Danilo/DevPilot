from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.modeling import ModelEvalRunner, ModelEvalRunnerConfig

ROOT = Path(__file__).resolve().parents[1]


def test_model_eval_runner_mock_suite_passes_with_prompt_metrics() -> None:
    result = ModelEvalRunner(ROOT, config=ModelEvalRunnerConfig(timeout_seconds=0.1)).run(provider="mock")

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["provider"] == "mock"
    assert summary["cases_total"] >= 3
    assert summary["passed_total"] == summary["cases_total"]
    assert summary["failed_total"] == 0
    assert summary["external_api_used"] is False
    assert summary["raw_prompts_stored"] is False
    assert summary["raw_outputs_stored"] is False
    first = result.data["matrix"][0]
    assert first["prompt_id"] == "model.generate.default"
    assert first["prompt_payload_redacted"] is True
    assert first["quality"]["quality_pass"] is True
    assert "result_digest" in first


def test_model_eval_runner_skips_disabled_local_provider_without_failing_suite() -> None:
    result = ModelEvalRunner(ROOT, config=ModelEvalRunnerConfig(timeout_seconds=0.1)).run(provider="lmstudio")

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["skipped_total"] == result.data["summary"]["cases_total"]
    assert result.data["summary"]["failed_total"] == 0
    assert result.data["provider_readiness"]["reason"] in {"local_provider_disabled", "local_provider_health"}
    assert any(finding.id == "MODEL_EVAL_PROVIDER_SKIPPED" for finding in result.findings)


def test_model_eval_cli_run_json_and_write_report_are_redacted() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "model", "eval", "run", "--provider", "mock", "--json", "--write-report"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["data"]["summary"]["provider"] == "mock"
    assert payload["data"]["summary"]["external_api_used"] is False
    assert payload["data"]["summary"]["raw_prompts_stored"] is False
    reports = payload["data"].get("reports") or {}
    assert reports.get("matrix_json") == "outputs/evals/model_eval_matrix.json"
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    assert "api_key=" not in serialized
    assert "sk-" not in serialized
    assert "resume el propósito de devpilot" not in serialized


def test_model_eval_budget_events_are_recorded_without_raw_prompt() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "model", "eval", "run", "--provider", "mock", "--json"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout

    budget = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "model", "budget", "status", "--limit", "10", "--json"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert budget.returncode == 0, budget.stderr + budget.stdout
    payload = json.loads(budget.stdout)
    assert payload["ok"] is True
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    assert "model-eval-runner" in serialized
    assert "prompt_id" in serialized
    assert "resume el propósito de devpilot" not in serialized
    assert "sk-" not in serialized
