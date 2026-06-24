from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from devpilot_core.testing import TestContractRegistryV2ValidationOptions, TestContractRegistryV2Validator

ROOT = Path(__file__).resolve().parents[1]


def load_registry() -> dict:
    return json.loads((ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8"))


def write_registry(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "test_contract_registry_v2.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def test_test_contract_registry_v2_validator_passes_migrated_registry_without_execution() -> None:
    result = TestContractRegistryV2Validator(ROOT).validate()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["contracts_total"] == 87
    assert summary["profiles_total"] == 5
    assert summary["p0_contracts_total"] >= 5
    assert summary["needs_review_total"] == 2
    assert summary["network_allowed_total"] == 0
    assert summary["external_api_allowed_total"] == 0
    assert summary["mutations_allowed_total"] == 0
    assert summary["source_mutations_allowed_total"] == 1
    assert summary["tests_executed"] is False
    assert summary["mutations_performed"] is False
    assert any(finding.id == "TEST_CONTRACT_REGISTRY_V2_VALIDATION_PASS" for finding in result.findings)


def test_test_contract_registry_v2_profiles_select_contracts_without_execution() -> None:
    validator = TestContractRegistryV2Validator(ROOT)

    p0 = validator.profile("p0-critical")
    security = validator.profile("security")
    release = validator.profile("release")
    impact = validator.profile("impact")
    docs = validator.profile("docs-historical")

    assert p0.ok, p0.to_dict()
    assert security.ok, security.to_dict()
    assert release.ok, release.to_dict()
    assert impact.ok, impact.to_dict()
    assert docs.ok, docs.to_dict()

    assert p0.data["summary"]["contracts_selected"] >= 5
    assert security.data["summary"]["contracts_selected"] >= 5
    assert release.data["summary"]["contracts_selected"] >= 5
    assert impact.data["summary"]["contracts_selected"] >= 80
    assert docs.data["summary"]["contracts_selected"] >= 78
    assert p0.data["summary"]["tests_executed"] is False
    assert all("pytest" in cmd or cmd.startswith("python -m devpilot_core") or cmd == "npm --prefix ui/web test" for cmd in p0.data["recommended_commands"])

    selected_ids = {contract["contract_id"] for contract in p0.data["contracts"]}
    assert "project-global-state" in selected_ids
    assert "schema-registry" in selected_ids
    assert "test-contract-registry" in selected_ids


def test_test_contract_registry_v2_unknown_profile_blocks() -> None:
    result = TestContractRegistryV2Validator(ROOT).profile("unknown")

    assert not result.ok
    assert result.exit_code.value == 2
    assert any(finding.id == "TEST_CONTRACT_REGISTRY_V2_UNKNOWN_PROFILE" for finding in result.findings)


def test_test_contract_registry_v2_validator_blocks_missing_test_file(tmp_path: Path) -> None:
    payload = load_registry()
    payload["contracts"][0]["test_files"] = ["tests/does_not_exist_post_h_003_c.py"]
    path = write_registry(tmp_path, payload)

    result = TestContractRegistryV2Validator(
        ROOT,
        TestContractRegistryV2ValidationOptions(registry_path=path),
    ).validate()

    assert not result.ok
    assert any(finding.id == "TEST_CONTRACT_REGISTRY_V2_PATH_MISSING" and finding.severity.value == "block" for finding in result.findings)


def test_test_contract_registry_v2_validator_blocks_unsafe_recommended_command(tmp_path: Path) -> None:
    payload = load_registry()
    payload["contracts"][0]["recommended_commands"] = ["python -m pytest tests/test_project_global_state.py -q && curl https://example.invalid"]
    path = write_registry(tmp_path, payload)

    result = TestContractRegistryV2Validator(
        ROOT,
        TestContractRegistryV2ValidationOptions(registry_path=path),
    ).validate()

    assert not result.ok
    assert any(finding.id == "TEST_CONTRACT_REGISTRY_V2_UNSAFE_RECOMMENDED_COMMAND" for finding in result.findings)


def test_test_contract_registry_v2_cli_validate_and_profile_are_available() -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"

    validate_proc = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "test-contracts", "validate-v2", "--json"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert validate_proc.returncode == 0, validate_proc.stderr + validate_proc.stdout
    validate_payload = json.loads(validate_proc.stdout)
    assert validate_payload["ok"] is True
    assert validate_payload["data"]["summary"]["contracts_total"] == 87

    profile_proc = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "test-contracts", "profile", "--profile", "p0-critical", "--json"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert profile_proc.returncode == 0, profile_proc.stderr + profile_proc.stdout
    profile_payload = json.loads(profile_proc.stdout)
    assert profile_payload["ok"] is True
    assert profile_payload["data"]["summary"]["contracts_selected"] >= 5
    assert profile_payload["data"]["summary"]["tests_executed"] is False


def test_post_h_003_c_documentation_is_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-003_test_contract_registry_2.md").read_text(encoding="utf-8")
    design = (ROOT / "docs/04_quality/test_contract_registry_2_design.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")

    assert "POST-H-003-C" in backlog
    assert "Validator v2 y perfiles de ejecución" in backlog
    assert 'version: "0.5.0"' in backlog
    assert "test-contracts validate-v2" in design
    assert "test-contracts profile --profile p0-critical" in runbook
    assert "POST-H-003-C" in readme
    assert "post-h-003-c" in changelog
