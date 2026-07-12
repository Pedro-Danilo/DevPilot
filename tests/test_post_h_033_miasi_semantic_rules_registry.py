from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.miasi.declarative_semantic_rules import DEFAULT_MIASI_SEMANTIC_RULES_PATH, load_miasi_semantic_rules
from devpilot_core.miasi.semantic import MiasiSemanticValidator
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "miasi"


def _read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


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


def test_post_h_033_d_miasi_semantic_rules_schema_validates() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="MiasiSemanticRules",
        instance=".devpilot/miasi/semantic_rules.json",
    )
    registry = _read_json(".devpilot/miasi/semantic_rules.json")

    assert result.ok is True
    assert registry["created_by"] == "POST-H-033-D"
    assert registry["rule_source"] == ".devpilot/miasi/semantic_rules.json"
    assert registry["compatibility"]["no_go_gates_preserved"] is True
    assert registry["compatibility"]["tokens_versioned"] is True
    assert registry["compatibility"]["guard_mappings_versioned"] is True
    assert registry["safety"]["critical_rules_disable_allowed"] is False
    assert registry["safety"]["dynamic_executable_rules_allowed"] is False
    assert "connector" in registry["no_go_action_markers"]


def test_post_h_033_d_loader_uses_registry_as_primary_source() -> None:
    catalog = load_miasi_semantic_rules(ROOT)

    assert catalog.registry_valid is True
    assert catalog.fallback_active is False
    assert catalog.rule_source == DEFAULT_MIASI_SEMANTIC_RULES_PATH.as_posix()
    assert catalog.catalog_version == "1.0.0"
    assert "controlled_write" in catalog.sensitive_side_effects
    assert "secretguard" in catalog.secret_guard_tokens
    assert "connector_write" in catalog.no_go_action_markers["connector"]
    assert len(catalog.required_eval_fixtures) >= 5


def test_post_h_033_d_semantic_report_exposes_rule_source_and_catalog_version() -> None:
    result = MiasiSemanticValidator(ROOT).validate()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["semantic_rules_registry"]["rule_source"] == ".devpilot/miasi/semantic_rules.json"
    assert result.data["semantic_rules_registry"]["catalog_version"] == "1.0.0"
    assert result.data["report"]["source_paths"]["semantic_rules"] == ".devpilot/miasi/semantic_rules.json"
    assert all(
        rule["summary"].get("rule_source") == ".devpilot/miasi/semantic_rules.json"
        for rule in result.data["report"]["rule_results"]
    )
    assert all(
        rule["summary"].get("catalog_version") == "1.0.0"
        for rule in result.data["report"]["rule_results"]
    )


def test_post_h_033_d_missing_registry_uses_explicit_fallback_without_silent_success(tmp_path: Path) -> None:
    root = _workspace_from_fixture(tmp_path, "valid_semantic_bundle.json")

    catalog = load_miasi_semantic_rules(root, emit_fallback_finding=True)
    result = MiasiSemanticValidator(root).validate()

    assert catalog.fallback_active is True
    assert catalog.findings
    assert result.ok is True
    assert result.data["summary"]["warning_findings_total"] >= 1
    assert any(f.id == "MIASI_SEMANTIC_RULES_REGISTRY_MISSING_FALLBACK_ACTIVE" for f in result.findings)
    assert result.data["semantic_rules_registry"]["fallback_active"] is True


def test_post_h_033_d_invalid_registry_blocks_with_explicit_fallback(tmp_path: Path) -> None:
    root = _workspace_from_fixture(tmp_path, "valid_semantic_bundle.json")
    registry_path = root / DEFAULT_MIASI_SEMANTIC_RULES_PATH
    registry_path.write_text("{invalid-json", encoding="utf-8")

    result = MiasiSemanticValidator(root).validate()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(f.id == "MIASI_SEMANTIC_RULES_REGISTRY_INVALID_JSON_BLOCKED" for f in result.findings)
    assert result.data["semantic_rules_registry"]["fallback_active"] is True


def test_post_h_033_d_no_go_plugin_and_connector_rules_still_block(tmp_path: Path) -> None:
    plugin_result = MiasiSemanticValidator(_workspace_from_fixture(tmp_path, "plugin_execution_without_sandbox.json")).validate()
    connector_result = MiasiSemanticValidator(_workspace_from_fixture(tmp_path, "connector_write_without_adr.json")).validate()

    assert plugin_result.ok is False
    assert connector_result.ok is False
    assert "MIASI_SEMANTIC_NO_GO_RULE_ALLOWED" in {finding.id for finding in plugin_result.findings}
    assert "MIASI_SEMANTIC_CONNECTOR_WRITE_WITHOUT_FUTURE_GUARDS" in {finding.id for finding in connector_result.findings}


def test_post_h_033_d_manifest_contract_and_governance_are_synced() -> None:
    manifest_result = SchemaValidator(ROOT).validate(schema="MiasiSemanticRules", instance="docs/post_h_033_d_manifest.json")
    source_registry = _read_json(".devpilot/docs_governance/source_registry.json")
    schema_catalog = _read_json("docs/schemas/schema_catalog.json")
    tcr_v1 = _read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = _read_json(".devpilot/testing/test_contract_registry_v2.json")
    state = _read_json(".devpilot/project_state.json")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-033_schema_backed_validators_declarative_semantics.md").read_text(encoding="utf-8")

    assert manifest_result.ok is True
    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert "POST-H-033-D-MIASI-SEMANTIC-RULES" in doc_ids
    assert "SCHEMA-DEVPL-MIASI-SEMANTIC-RULES-V1" in doc_ids
    assert "POST-H-033-D-MIASI-SEMANTIC-RULES-MODULE" in doc_ids
    assert "POST-H-033-D-MIASI-SEMANTIC-VALIDATOR-MODULE" in doc_ids
    assert "POST-H-033-D-MIASI-SEMANTIC-RULES-REGISTRY-TEST" in doc_ids

    schema_ids = {item["schema_id"] for item in schema_catalog["schemas"]}
    assert "SCHEMA-DEVPL-MIASI-SEMANTIC-RULES-V1" in schema_ids
    assert any(contract["contract_id"] == "post-h-033-miasi-semantic-rules-registry" for contract in tcr_v1["contracts"])
    contract_v2 = next(contract for contract in tcr_v2["contracts"] if contract["contract_id"] == "post-h-033-miasi-semantic-rules-registry")
    assert contract_v2["subgate_id"] == "miasi-semantic-no-go-governance"
    assert contract_v2["required_for_security_gate"] is True
    assert contract_v2["network_allowed"] is False
    assert contract_v2["external_api_allowed"] is False
    assert contract_v2["source_mutations_allowed"] is False

    assert state["current_micro_sprint"] in {"POST-H-033-D", "POST-H-033-E", "POST-H-033-F", "POST-H-034-A"}
    assert state["next_micro_sprint"] in {"POST-H-033-E", "POST-H-033-F", "POST-H-033-CLOSURE", "POST-H-034-B"}
    assert state["post_h_033_c_closed"] is True
    assert state["post_h_033_d_miasi_semantic_rules_available"] is True
    assert state["post_h_033_d_registry_source_primary"] is True
    assert state["post_h_033_d_no_go_gates_preserved"] is True
    assert state["post_h_033_d_rule_source_reported"] is True
    assert state["post_h_033_d_catalog_version_reported"] is True
    assert state["post_h_033_d_critical_rules_disable_allowed"] is False
    assert "POST-H-033-D — MIASI semantic rules registry" in readme
    assert "POST-H-033-D — MIASI semantic rules registry" in runbook
    assert any(marker in backlog for marker in ['implementation_status: "active/post-h-033-d-implemented-initial"', 'implementation_status: "active/post-h-033-e-implemented-initial"', 'implementation_status: "active/post-h-033-f-implemented-initial"', 'implementation_status: "closed/schema-backed-validators-declarative-semantics"'])
