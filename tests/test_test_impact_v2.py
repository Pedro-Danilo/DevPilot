from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from devpilot_core.testing import TestImpactAnalyzerV2, TestImpactV2Options

ROOT = Path(__file__).resolve().parents[1]


def test_test_impact_v2_policy_change_recommends_policy_security_plan() -> None:
    result = TestImpactAnalyzerV2(ROOT, TestImpactV2Options(changed_paths=("src/devpilot_core/policy",))).analyze()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["matched_contracts_total"] >= 3
    assert summary["p0_selected_total"] >= 3
    assert "p0-critical" in summary["recommended_profiles"]
    assert "security" in summary["recommended_profiles"]
    assert "tests/test_policy_engine.py" in result.data["recommended_tests"]
    assert "tests/test_security_readiness.py" in result.data["recommended_tests"]
    assert any("quality-gate run --profile hardening" in command for command in result.data["recommended_commands"])
    assert summary["tests_executed"] is False
    assert summary["network_used"] is False
    assert any(finding.id == "TEST_IMPACT_V2_HEURISTIC_APPLIED" for finding in result.findings)


def test_test_impact_v2_docs_change_selects_relevant_historical_contract_only() -> None:
    result = TestImpactAnalyzerV2(ROOT, TestImpactV2Options(changed_paths=("docs/audits/func_sprint_24/report.md",))).analyze()

    assert result.ok, result.to_dict()
    selected_ids = {item["contract_id"] for item in result.data["matched_contracts"]}
    assert "sprint-24-documentation" in selected_ids
    assert "sprint-23-documentation" not in selected_ids
    assert "sprint-25-documentation" not in selected_ids
    assert "tests/test_sprint_24_documentation.py" in result.data["recommended_tests"]
    assert result.data["summary"]["p0_selected_total"] == 0
    assert result.data["summary"]["tests_executed"] is False


def test_test_impact_v2_cli_change_recommends_cli_and_impact_tests() -> None:
    result = TestImpactAnalyzerV2(ROOT, TestImpactV2Options(changed_paths=("src/devpilot_core/cli.py",))).analyze()

    assert result.ok, result.to_dict()
    assert "tests/test_cli_core.py" in result.data["recommended_tests"]
    assert "tests/test_test_impact.py" in result.data["recommended_tests"]
    assert any(item["contract_id"] == "test-impact-analyzer" for item in result.data["matched_contracts"])
    assert "impact" in result.data["summary"]["recommended_profiles"]
    assert result.data["summary"]["tests_executed"] is False


def test_test_impact_v2_schema_change_selects_schema_registry() -> None:
    result = TestImpactAnalyzerV2(ROOT, TestImpactV2Options(changed_paths=("docs/schemas/test_contract_registry_v2.schema.json",))).analyze()

    assert result.ok, result.to_dict()
    selected_ids = {item["contract_id"] for item in result.data["matched_contracts"]}
    assert "schema-registry" in selected_ids
    assert "tests/test_schema_registry.py" in result.data["recommended_tests"]
    assert "tests/test_schema_validator.py" in result.data["recommended_tests"]
    assert "p0-critical" in result.data["summary"]["recommended_profiles"]


def test_test_impact_v2_unknown_path_warns_and_stays_local() -> None:
    result = TestImpactAnalyzerV2(ROOT, TestImpactV2Options(changed_paths=("sandbox/unknown/new_file.txt",))).analyze()

    assert result.ok, result.to_dict()
    assert result.data["summary"]["matched_contracts_total"] == 0
    assert result.data["summary"]["unmatched_paths_total"] == 1
    assert "p0-critical" in result.data["summary"]["recommended_profiles"]
    assert any(finding.id == "TEST_IMPACT_V2_UNMATCHED_PATHS_REVIEW_REQUIRED" for finding in result.findings)
    assert result.data["summary"]["tests_executed"] is False
    assert result.data["summary"]["external_api_used"] is False


def test_test_impact_v2_changed_paths_file_is_supported(tmp_path: Path) -> None:
    changed = tmp_path / "changed_paths.txt"
    changed.write_text("docs/audits/func_sprint_24/report.md\n", encoding="utf-8")

    result = TestImpactAnalyzerV2(ROOT, TestImpactV2Options(changed_paths_file=changed)).analyze()

    assert result.ok, result.to_dict()
    assert "tests/test_sprint_24_documentation.py" in result.data["recommended_tests"]


def test_test_impact_v2_cli_command_is_available() -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"

    proc = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "test-impact", "analyze-v2", "--changed-paths", "src/devpilot_core/policy", "--json"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["data"]["summary"]["tests_executed"] is False
    assert "tests/test_policy_engine.py" in payload["data"]["recommended_tests"]


def test_post_h_003_d_documentation_is_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-003_test_contract_registry_2.md").read_text(encoding="utf-8")
    design = (ROOT / "docs/04_quality/test_contract_registry_2_design.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "docs/post_h_003_d_manifest.json").read_text(encoding="utf-8"))

    assert "POST-H-003-D" in backlog
    assert "Integración con Test Impact Analyzer" in backlog
    assert 'version: "0.5.0"' in backlog
    assert "test-impact analyze-v2" in design
    assert "test-impact analyze-v2" in runbook
    assert "POST-H-003-D" in readme
    assert "post-h-003-d" in changelog
    assert manifest["micro_sprint"] == "POST-H-003-D"
    assert manifest["tests_execute_from_json"] is False
