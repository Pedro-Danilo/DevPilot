from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core.docs_governance import DocumentationGovernanceValidator
from devpilot_core.docs_governance.rule_registry import DEFAULT_DOCS_GOVERNANCE_RULE_REGISTRY, load_docs_governance_rule_registry
from devpilot_core.schemas.validator import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / ".devpilot" / "docs_governance" / "rule_registry.json"
MANIFEST = ROOT / "docs" / "post_h_033_f_manifest.json"
SCHEMA = ROOT / "docs" / "schemas" / "docs_governance_rule_registry.schema.json"


def _write_minimal_source_registry(root: Path, *, required_tests: list[str] | None = None, classification: str = "source-of-truth", lifecycle: str = "active") -> None:
    (root / ".devpilot/docs_governance").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "docs/source.md").write_text(
        "---\n"
        "doc_id: \"DOC-001\"\n"
        "title: \"Source\"\n"
        "status: \"approved\"\n"
        "version: \"1.0.0\"\n"
        "owner: \"Ordóñez\"\n"
        "updated: \"2026-07-11\"\n"
        "approval: \"approved_by_owner\"\n"
        "---\n"
        "# Source\n",
        encoding="utf-8",
    )
    if required_tests:
        for test_path in required_tests:
            path = root / test_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("def test_placeholder():\n    assert True\n", encoding="utf-8")
    registry = {
        "schema_version": "1.0",
        "schema_id": "SCHEMA-DEVPL-DOCUMENTATION-SOURCE-REGISTRY-V1",
        "registry_id": "tmp-docs-registry",
        "created_by": "TEST",
        "status": "implemented-initial",
        "phase": "POST-FASE-H",
        "owner": "Ordóñez",
        "updated": "2026-07-11",
        "documents": [
            {
                "doc_id": "DOC-001",
                "path": "docs/source.md",
                "classification": classification,
                "domain": "test",
                "owner": "Ordóñez",
                "status_required": "approved",
                "criticality": "P0",
                "required_tests": required_tests or [],
                "sync_rules": [],
                "lifecycle": lifecycle,
            }
        ],
        "summary": {},
        "rules": {},
        "safety": {},
        "notes": [],
    }
    (root / ".devpilot/docs_governance/source_registry.json").write_text(json.dumps(registry), encoding="utf-8")


def _copy_rule_registry_support(root: Path) -> None:
    shutil.copytree(ROOT / "docs" / "schemas", root / "docs" / "schemas", dirs_exist_ok=True)
    target = root / DEFAULT_DOCS_GOVERNANCE_RULE_REGISTRY
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REGISTRY, target)


def test_post_h_033_f_rule_registry_schema_and_manifest_validate() -> None:
    assert REGISTRY.exists()
    assert SCHEMA.exists()
    assert MANIFEST.exists()

    registry_result = SchemaValidator(ROOT).validate(schema="DocsGovernanceRuleRegistry", instance=REGISTRY.relative_to(ROOT))
    manifest_result = SchemaValidator(ROOT).validate(schema="DocsGovernanceRuleRegistry", instance=MANIFEST.relative_to(ROOT))

    assert registry_result.ok is True, registry_result.to_dict()
    assert manifest_result.ok is True, manifest_result.to_dict()


def test_post_h_033_f_docs_governance_report_exposes_rule_source_and_version() -> None:
    result = DocumentationGovernanceValidator(ROOT).run()

    assert result.ok is True, result.to_dict()
    summary = result.data["summary"]
    governance = result.data["governance"]
    assert summary["rule_source"] == ".devpilot/docs_governance/rule_registry.json"
    assert summary["catalog_version"] == "1.0.0"
    assert summary["rule_registry_valid"] is True
    assert summary["rule_registry_fallback_active"] is False
    assert summary["source_registry_and_rule_registry_validated_together"] is True
    assert governance["rule_registry"]["rule_source"] == ".devpilot/docs_governance/rule_registry.json"


def test_post_h_033_f_registry_complements_source_registry_without_replacing_it() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    source_registry = json.loads((ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8"))

    assert payload["source_registry_path"] == ".devpilot/docs_governance/source_registry.json"
    assert payload["integrates_with_source_registry"] is True
    assert payload["compatibility"]["source_registry_preserved"] is True
    assert payload["critical_rules_disable_allowed"] is False
    assert source_registry["documents"]


def test_post_h_033_f_invalid_rule_registry_fails_closed(tmp_path: Path) -> None:
    _write_minimal_source_registry(tmp_path, required_tests=["tests/test_source.py"])
    _copy_rule_registry_support(tmp_path)
    target = tmp_path / DEFAULT_DOCS_GOVERNANCE_RULE_REGISTRY
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["critical_rules_disable_allowed"] = True
    target.write_text(json.dumps(payload), encoding="utf-8")

    catalog = load_docs_governance_rule_registry(tmp_path)
    result = DocumentationGovernanceValidator(tmp_path).run()

    assert catalog.registry_valid is False
    assert catalog.fallback_active is True
    assert catalog.has_blocking_registry_findings is True
    assert result.ok is False
    assert any(finding.id == "DOCS_GOVERNANCE_RULE_REGISTRY_SCHEMA_INVALID_BLOCKED" for finding in result.findings)


def test_post_h_033_f_missing_rule_registry_uses_explicit_fallback(tmp_path: Path) -> None:
    _write_minimal_source_registry(tmp_path, required_tests=["tests/test_source.py"])

    catalog = load_docs_governance_rule_registry(tmp_path)
    result = DocumentationGovernanceValidator(tmp_path).run()

    assert catalog.registry_valid is False
    assert catalog.fallback_active is True
    assert catalog.has_blocking_registry_findings is False
    assert result.ok is True, result.to_dict()
    assert result.data["summary"]["rule_registry_fallback_active"] is True
    assert any(finding.id == "DOCS_GOVERNANCE_RULE_REGISTRY_MISSING_FALLBACK_ACTIVE" for finding in result.findings)


def test_post_h_033_f_source_of_truth_without_required_tests_still_blocks(tmp_path: Path) -> None:
    _write_minimal_source_registry(tmp_path, required_tests=[])
    _copy_rule_registry_support(tmp_path)

    result = DocumentationGovernanceValidator(tmp_path).run()

    assert result.ok is False
    assert any(finding.id == "DOCUMENTATION_REQUIRED_TESTS_MISSING" for finding in result.findings)


def test_post_h_033_f_historical_active_authority_still_warns(tmp_path: Path) -> None:
    _write_minimal_source_registry(tmp_path, required_tests=["tests/test_source.py"], classification="historical", lifecycle="active")
    _copy_rule_registry_support(tmp_path)

    result = DocumentationGovernanceValidator(tmp_path).run()

    assert result.ok is True, result.to_dict()
    assert result.data["summary"]["historical_current_authority_total"] == 1
    assert any(finding.id == "DOCUMENTATION_HISTORICAL_ACTIVE_REVIEW" and finding.severity.value == "warning" for finding in result.findings)


def test_post_h_033_f_governance_artifacts_registered_and_docs_synced() -> None:
    state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8"))
    source_registry = json.loads((ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8"))
    tcr_v1 = json.loads((ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8"))
    tcr_v2 = json.loads((ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/release/CHANGELOG.md").read_text(encoding="utf-8")

    assert state["post_h_033_e_closed"] is True
    assert state["post_h_033_current_micro_sprint"] == "POST-H-033-F"
    assert state["post_h_033_next_micro_sprint"] == "POST-H-033-CLOSURE"
    assert state["post_h_033_f_docs_governance_rule_registry_available"] is True
    assert state["post_h_033_f_docs_governance_rule_registry_schema_registered"] is True
    assert state["post_h_033_f_docs_governance_validator_integrated"] is True
    assert state["post_h_033_f_source_of_truth_drift_blocks"] is True
    assert state["post_h_033_f_required_tests_blocks"] is True
    assert state["post_h_033_f_frontmatter_required_preserved"] is True
    assert state["post_h_033_f_invalid_registry_blocks_success"] is True
    assert state["post_h_033_f_rule_source_reported"] is True
    assert state["post_h_033_f_catalog_version_reported"] is True
    assert state["post_h_033_f_network_used"] is False
    assert state["post_h_033_f_external_api_used"] is False
    assert state["post_h_033_f_remote_execution_enabled"] is False
    assert state["post_h_033_f_connector_write_enabled"] is False
    assert state["post_h_033_f_plugin_execution_enabled"] is False
    assert state["post_h_033_f_source_mutations"] is False
    assert state["post_h_033_f_critical_rules_disable_allowed"] is False

    assert "SCHEMA-DEVPL-DOCS-GOVERNANCE-RULE-REGISTRY-V1" in {item["schema_id"] for item in catalog["schemas"]}
    assert "POST-H-033-F-DOCS-GOVERNANCE-RULE-REGISTRY" in {item["doc_id"] for item in source_registry["documents"]}
    assert "post-h-033-docs-governance-rule-registry" in {item["contract_id"] for item in tcr_v1["contracts"]}
    assert "post-h-033-docs-governance-rule-registry" in {item["contract_id"] for item in tcr_v2["contracts"]}
    assert "POST-H-033-F — Docs governance rule registry" in readme
    assert "POST-H-033-F — Docs governance rule registry" in runbook
    assert "post-h-033-f" in changelog.lower()
