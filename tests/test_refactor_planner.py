from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.refactor import RefactorPlanner


def _minimal_workspace(root: Path) -> None:
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text("[project]\nname='tmp-devpilot'\n", encoding="utf-8")


def _long_function_source() -> str:
    body = ["def long_function(a, b, c, d, e, f):"]
    body.extend(f"    value_{idx} = {idx}" for idx in range(70))
    body.append("    return value_69")
    return "\n".join(body) + "\n"


def test_refactor_planner_generates_plan_without_modifying_files(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    source = tmp_path / "src" / "service.py"
    source.write_text(_long_function_source(), encoding="utf-8")
    before = source.read_text(encoding="utf-8")

    result = RefactorPlanner(tmp_path).plan("src", goal="Extract focused helpers")

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["dry_run"] is True
    assert result.data["summary"]["files_modified"] == 0
    assert result.data["summary"]["patch_generated"] is False
    assert result.data["summary"]["candidates_total"] >= 1
    assert result.data["plan"]
    assert source.read_text(encoding="utf-8") == before


def test_refactor_planner_blocks_secret_like_goal_without_emitting_secret(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    (tmp_path / "src" / "service.py").write_text("def ok():\n    return 1\n", encoding="utf-8")

    result = RefactorPlanner(tmp_path).plan("src", goal="api_key=sk-1234567890abcdef")
    payload = json.dumps(result.to_dict(), ensure_ascii=False)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "SECRETGUARD_SECRET_DETECTED" for finding in result.findings)
    assert "sk-1234567890abcdef" not in payload


def test_refactor_planner_blocks_target_outside_workspace(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    outside = tmp_path.parent / "outside.py"
    outside.write_text("def x():\n    return 1\n", encoding="utf-8")

    result = RefactorPlanner(tmp_path).plan(outside)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "PATHGUARD_OUTSIDE_ROOT" for finding in result.findings)


def test_refactor_planner_conservative_plan_for_clean_small_file(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    (tmp_path / "src" / "small.py").write_text("def ok():\n    return 1\n", encoding="utf-8")

    result = RefactorPlanner(tmp_path).plan("src/small.py")

    assert result.ok is True
    assert result.data["summary"]["candidates_total"] == 0
    assert any(finding.id == "REFACTOR_PLAN_CONSERVATIVE" for finding in result.findings)
    assert result.data["summary"]["tests_required"] is True


def test_refactor_plan_cli_json_and_report_are_parseable(tmp_path: Path, monkeypatch, capsys) -> None:
    _minimal_workspace(tmp_path)
    (tmp_path / "src" / "service.py").write_text(_long_function_source(), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["refactor-plan", "--target", "src", "--goal", "Extract helpers", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "refactor-plan"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["plan_only"] is True
    assert payload["data"]["reports"]["json"] == "outputs/reports/refactor_plan.json"
    assert (tmp_path / "outputs" / "reports" / "refactor_plan.json").is_file()


def test_refactor_planner_reports_python_syntax_error(tmp_path: Path) -> None:
    _minimal_workspace(tmp_path)
    (tmp_path / "src" / "broken.py").write_text("def broken(:\n    pass\n", encoding="utf-8")

    result = RefactorPlanner(tmp_path).plan("src")

    assert result.ok is False
    assert result.exit_code == ExitCode.FAIL
    assert any(finding.id == "REFACTOR_PYTHON_SYNTAX_ERROR" for finding in result.findings)
