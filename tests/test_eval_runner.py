from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.evals import EvalRunner


def _copy_eval_workspace(target: Path) -> None:
    source_root = Path.cwd()
    (target / ".devpilot").mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_root / ".devpilot" / "miasi", target / ".devpilot" / "miasi")
    shutil.copytree(source_root / "docs", target / "docs", dirs_exist_ok=True)
    shutil.copytree(source_root / "evals", target / "evals", dirs_exist_ok=True)
    (target / "pyproject.toml").write_text("[project]\nname='tmp-devpilot'\n", encoding="utf-8")


def test_eval_runner_documentation_suite_passes(tmp_path: Path) -> None:
    _copy_eval_workspace(tmp_path)

    result = EvalRunner(tmp_path).run(suite="documentation")

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["cases_total"] == 8
    assert result.data["summary"]["pass_rate"] == 1.0
    assert result.data["summary"]["false_positives"] == 0
    assert result.data["summary"]["false_negatives"] == 0
    assert result.data["metadata"]["llm_required"] is False


def test_eval_runner_single_case_filter(tmp_path: Path) -> None:
    _copy_eval_workspace(tmp_path)

    result = EvalRunner(tmp_path).run(suite="documentation", case_id="frontmatter-missing-doc-id")

    assert result.ok is True
    assert result.data["summary"]["cases_total"] == 1
    case = result.data["cases"][0]
    assert case["case_id"] == "frontmatter-missing-doc-id"
    assert "FRONTMATTER_REQUIRED_FIELD_MISSING" in case["actual_finding_ids"]


def test_eval_runner_missing_case_blocks(tmp_path: Path) -> None:
    _copy_eval_workspace(tmp_path)

    result = EvalRunner(tmp_path).run(suite="documentation", case_id="missing-case")

    assert result.ok is False
    assert result.exit_code == ExitCode.ERROR
    assert "EVAL_CASE_NOT_FOUND" in {finding.id for finding in result.findings}


def test_eval_cli_run_json_and_report(tmp_path: Path, monkeypatch, capsys) -> None:
    _copy_eval_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["eval", "run", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "eval run"
    assert payload["data"]["summary"]["cases_total"] == 8
    assert payload["data"]["summary"]["false_negatives"] == 0
    assert payload["data"]["reports"]["json"] == "outputs/reports/eval_run_documentation.json"
    assert (tmp_path / "outputs" / "reports" / "eval_run_documentation.json").is_file()


def test_eval_cli_case_filter_json_is_parseable(tmp_path: Path, monkeypatch, capsys) -> None:
    _copy_eval_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["eval", "run", "--case-id", "agent-precode-documentation-secret-block", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["data"]["summary"]["cases_total"] == 1
    case = payload["data"]["cases"][0]
    assert case["actual_ok"] is False
    assert "SECRETGUARD_SECRET_DETECTED" in case["actual_finding_ids"]
