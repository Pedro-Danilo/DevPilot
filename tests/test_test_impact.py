from __future__ import annotations

from pathlib import Path

from devpilot_core.testing import TestImpactAnalyzer, TestImpactOptions

ROOT = Path(__file__).resolve().parents[1]


def test_test_impact_recommends_global_state_for_readme_change() -> None:
    result = TestImpactAnalyzer(ROOT).analyze(TestImpactOptions(changed_files=("README.md",)))

    assert result.ok, result.to_dict()
    assert "tests/test_project_global_state.py" in result.data["recommended_tests"]
    assert result.data["summary"]["full_pytest_required"] is False


def test_test_impact_recommends_schema_and_full_pytest_for_unknown_or_core_change() -> None:
    result = TestImpactAnalyzer(ROOT).analyze(
        TestImpactOptions(changed_files=("docs/schemas/schema_catalog.json", "src/devpilot_core/cli.py"))
    )

    assert result.ok, result.to_dict()
    assert "tests/test_schema_registry.py" in result.data["recommended_tests"]
    assert result.data["summary"]["full_pytest_required"] is True
    assert "pytest -q" in result.data["recommended_commands"]


def test_test_impact_changed_files_file_is_supported(tmp_path: Path) -> None:
    changed = tmp_path / "changed_files.txt"
    changed.write_text("docs/POST-H-001_industrial_hardening_tests_contracts.md\n", encoding="utf-8")

    result = TestImpactAnalyzer(ROOT).analyze(TestImpactOptions(changed_files_path=str(changed)))

    assert result.ok, result.to_dict()
    assert "tests/test_project_global_state.py" in result.data["recommended_tests"]
