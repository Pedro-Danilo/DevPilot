from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.miasi import MiasiSemanticValidator
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "miasi"


def _workspace_from_fixture(tmp_path: Path, fixture_name: str) -> Path:
    payload = json.loads((FIXTURE_DIR / fixture_name).read_text(encoding="utf-8"))
    root = tmp_path / fixture_name.removesuffix(".json")
    miasi_dir = root / ".devpilot" / "miasi"
    schema_dir = root / "docs" / "schemas"
    miasi_dir.mkdir(parents=True)
    schema_dir.mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname='devpilot-semantic-fixture'\n", encoding="utf-8")
    (miasi_dir / "agent_registry.json").write_text(json.dumps(payload["agent_registry"], indent=2), encoding="utf-8")
    (miasi_dir / "tool_registry.json").write_text(json.dumps(payload["tool_registry"], indent=2), encoding="utf-8")
    (miasi_dir / "policy_matrix.json").write_text(json.dumps(payload["policy_matrix"], indent=2), encoding="utf-8")
    identity_dir = root / ".devpilot" / "identity"
    identity_dir.mkdir(parents=True)
    if "identity_registry" in payload:
        (identity_dir / "identity_registry.json").write_text(json.dumps(payload["identity_registry"], indent=2), encoding="utf-8")
    else:
        shutil.copy2(ROOT / ".devpilot" / "identity" / "identity_registry.json", identity_dir / "identity_registry.json")
    shutil.copy2(ROOT / "docs" / "schemas" / "miasi_semantic_report.schema.json", schema_dir / "miasi_semantic_report.schema.json")
    shutil.copy2(ROOT / "docs" / "schemas" / "schema_catalog.json", schema_dir / "schema_catalog.json")
    return root


def _validate_fixture(tmp_path: Path, fixture_name: str):
    root = _workspace_from_fixture(tmp_path, fixture_name)
    result = MiasiSemanticValidator(root).validate()
    schema_result = SchemaValidator(root).validate_payload(
        schema="MiasiSemanticReport",
        payload=result.data["report"],
        instance_label=f"in-memory:{fixture_name}",
    )
    assert schema_result.ok, schema_result.to_dict()
    return result


def test_valid_semantic_bundle_fixture_passes(tmp_path: Path) -> None:
    result = _validate_fixture(tmp_path, "valid_semantic_bundle.json")

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["blocking_findings_total"] == 0


def test_missing_approval_for_high_risk_tool_fixture_blocks(tmp_path: Path) -> None:
    result = _validate_fixture(tmp_path, "missing_approval_for_high_risk_tool.json")

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert "MIASI_SEMANTIC_SENSITIVE_TOOL_APPROVAL_MISSING" in {finding.id for finding in result.findings}


def test_unknown_agent_tool_reference_fixture_blocks(tmp_path: Path) -> None:
    result = _validate_fixture(tmp_path, "unknown_agent_tool_reference.json")

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert "MIASI_SEMANTIC_AGENT_TOOL_UNKNOWN" in {finding.id for finding in result.findings}


def test_contradictory_policy_rules_fixture_blocks(tmp_path: Path) -> None:
    result = _validate_fixture(tmp_path, "contradictory_policy_rules.json")

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert "MIASI_SEMANTIC_POLICY_CONTRADICTION" in {finding.id for finding in result.findings}


def test_plugin_execution_without_sandbox_fixture_blocks(tmp_path: Path) -> None:
    result = _validate_fixture(tmp_path, "plugin_execution_without_sandbox.json")

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert "MIASI_SEMANTIC_NO_GO_RULE_ALLOWED" in {finding.id for finding in result.findings}


def test_missing_rbac_registry_fixture_blocks(tmp_path: Path) -> None:
    root = _workspace_from_fixture(tmp_path, "valid_semantic_bundle.json")
    (root / ".devpilot" / "identity" / "identity_registry.json").unlink()

    result = MiasiSemanticValidator(root).validate()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert "MIASI_SEMANTIC_IDENTITY_REGISTRY_MISSING" in {finding.id for finding in result.findings}


def test_generic_approval_for_sensitive_tool_fixture_blocks(tmp_path: Path) -> None:
    result = _validate_fixture(tmp_path, "generic_approval_for_sensitive_tool.json")

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    ids = {finding.id for finding in result.findings}
    assert "MIASI_SEMANTIC_APPROVAL_SCOPE_GENERIC" in ids


def test_network_cost_without_cost_guard_fixture_blocks(tmp_path: Path) -> None:
    result = _validate_fixture(tmp_path, "network_cost_without_costguard.json")

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert "MIASI_SEMANTIC_NETWORK_COST_GUARD_MISSING" in {finding.id for finding in result.findings}


def test_connector_write_without_adr_fixture_blocks(tmp_path: Path) -> None:
    result = _validate_fixture(tmp_path, "connector_write_without_adr.json")

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert "MIASI_SEMANTIC_CONNECTOR_WRITE_WITHOUT_FUTURE_GUARDS" in {finding.id for finding in result.findings}
