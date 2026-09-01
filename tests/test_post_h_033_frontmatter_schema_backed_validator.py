from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli import main
from devpilot_core.cli_models import ExitCode
from devpilot_core.schemas import SchemaValidator
from devpilot_core.validators.frontmatter import parse_frontmatter_text, validate_frontmatter_document, validate_frontmatter_file
from devpilot_core.validators.frontmatter_catalog import load_frontmatter_catalog

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "docs"
CURRENT_CATALOG = ROOT / ".devpilot" / "validation" / "frontmatter_catalog.json"
AT_CLOSE_CATALOG = ROOT / ".devpilot" / "validation" / "frontmatter_catalog_post_h_033_b_at_close.json"


def _current_catalog_version() -> str:
    return str(json.loads(CURRENT_CATALOG.read_text(encoding="utf-8"))["catalog_version"])


def _document(frontmatter: str) -> object:
    text = f"---\n{frontmatter}---\n\n# Test\n"
    return parse_frontmatter_text(text, path=ROOT / "tests" / "fixtures" / "docs" / "synthetic_frontmatter.md")


def test_post_h_033_b_frontmatter_catalog_schema_validates() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="FrontmatterMetadata",
        instance=".devpilot/validation/frontmatter_catalog.json",
    )
    catalog = json.loads((ROOT / ".devpilot/validation/frontmatter_catalog.json").read_text(encoding="utf-8"))

    assert result.ok is True
    assert catalog["created_by"] == "POST-H-033-B"
    assert catalog["parser_dependency_free"] is True
    assert catalog["fallback_required"] is True
    assert catalog["compatibility"]["runtime_behavior_changed"] is False
    assert catalog["compatibility"]["finding_ids_preserved"] is True
    assert catalog["safety"]["llm_judge_used"] is False
    assert catalog["safety"]["critical_rules_disable_allowed"] is False



def test_post_h_033_b_historical_catalog_snapshot_remains_frozen() -> None:
    historical = json.loads(AT_CLOSE_CATALOG.read_text(encoding="utf-8"))
    current = json.loads(CURRENT_CATALOG.read_text(encoding="utf-8"))

    assert historical["created_by"] == "POST-H-033-B"
    assert historical["catalog_version"] == "1.0.0"
    assert "closed" not in historical["rules"]["allowed_statuses"]
    assert current["catalog_version"] == "1.1.0"
    assert "closed" in current["rules"]["allowed_statuses"]

def test_post_h_033_b_valid_frontmatter_uses_catalog_source() -> None:
    result = validate_frontmatter_file(FIXTURES / "valid_frontmatter.md", root=FIXTURES)

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["rule_source"] == ".devpilot/validation/frontmatter_catalog.json"
    assert result.data["catalog_version"] == _current_catalog_version()
    assert result.data["catalog_valid"] is True
    assert result.data["fallback_active"] is False


def test_post_h_033_b_negative_status_semver_date_and_doc_id_are_catalog_backed() -> None:
    document = _document(
        "title: Synthetic\n"
        "doc_id: invalid doc id\n"
        "status: unknown\n"
        "version: 1\n"
        "owner: Ordóñez\n"
        "updated: 20260711\n"
        "approval: approved\n"
    )

    result = validate_frontmatter_document(document, root=ROOT)
    finding_ids = {finding.id for finding in result.findings}

    assert result.ok is False
    assert result.exit_code == ExitCode.FAIL
    assert "FRONTMATTER_INVALID_STATUS" in finding_ids
    assert "FRONTMATTER_INVALID_VERSION" in finding_ids
    assert "FRONTMATTER_INVALID_UPDATED_DATE" in finding_ids
    assert "FRONTMATTER_INVALID_DOC_ID" in finding_ids
    assert all(finding.metadata.get("rule_source") == ".devpilot/validation/frontmatter_catalog.json" for finding in result.findings)
    assert all(finding.metadata.get("catalog_version") == _current_catalog_version() for finding in result.findings)


def test_post_h_033_b_strict_and_non_strict_approval_behavior_is_preserved() -> None:
    path = FIXTURES / "approved_without_approval.md"

    non_strict = validate_frontmatter_file(path, root=FIXTURES)
    strict = validate_frontmatter_file(path, root=FIXTURES, strict=True)

    assert non_strict.ok is True
    assert non_strict.exit_code == ExitCode.PASS
    assert any(f.id == "FRONTMATTER_APPROVED_WITHOUT_APPROVAL" and f.severity.value == "warning" for f in non_strict.findings)
    assert strict.ok is False
    assert strict.exit_code == ExitCode.FAIL
    assert any(f.id == "FRONTMATTER_APPROVED_WITHOUT_APPROVAL" and f.severity.value == "fail" for f in strict.findings)


def test_post_h_033_b_invalid_catalog_falls_back_without_bypass(tmp_path: Path) -> None:
    catalog_path = tmp_path / ".devpilot" / "validation" / "frontmatter_catalog.json"
    catalog_path.parent.mkdir(parents=True)
    catalog_path.write_text("{invalid-json", encoding="utf-8")
    doc_path = tmp_path / "invalid.md"
    doc_path.write_text(
        "---\n"
        "title: Invalid\n"
        "status: approved\n"
        "version: 1.0.0\n"
        "owner: Ordóñez\n"
        "updated: 2026-07-11\n"
        "---\n# Invalid\n",
        encoding="utf-8",
    )

    catalog = load_frontmatter_catalog(tmp_path, emit_fallback_finding=True)
    result = validate_frontmatter_file(doc_path, root=tmp_path)

    assert catalog.fallback_active is True
    assert catalog.findings
    assert result.ok is False
    assert result.exit_code == ExitCode.FAIL
    assert result.data["fallback_active"] is True
    assert any(f.id == "FRONTMATTER_REQUIRED_FIELD_MISSING" and f.metadata["field"] == "doc_id" for f in result.findings)


def test_post_h_033_b_cli_and_manifest_contracts_are_synced(capsys) -> None:
    exit_code = main(["schema", "validate", "--schema-id", "FrontmatterMetadata", "--instance", ".devpilot/validation/frontmatter_catalog.json", "--json"])
    payload = json.loads(capsys.readouterr().out)
    manifest_result = SchemaValidator(ROOT).validate(schema="FrontmatterMetadata", instance="docs/post_h_033_b_manifest.json")

    assert exit_code == 0
    assert payload["ok"] is True
    assert manifest_result.ok is True


def test_post_h_033_b_governance_artifacts_registered_and_docs_synced() -> None:
    source_registry = json.loads((ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8"))
    schema_catalog = json.loads((ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8"))
    tcr_v1 = json.loads((ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8"))
    tcr_v2 = json.loads((ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8"))
    state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-033_schema_backed_validators_declarative_semantics.md").read_text(encoding="utf-8")

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert "POST-H-033-B-FRONTMATTER-CATALOG" in doc_ids
    assert "SCHEMA-DEVPL-FRONTMATTER-METADATA-V1" in doc_ids
    assert "POST-H-033-B-FRONTMATTER-CATALOG-MODULE" in doc_ids
    assert "POST-H-033-B-FRONTMATTER-SCHEMA-BACKED-TEST" in doc_ids

    schema_ids = {item["schema_id"] for item in schema_catalog["schemas"]}
    assert "SCHEMA-DEVPL-FRONTMATTER-METADATA-V1" in schema_ids
    assert any(contract["contract_id"] == "post-h-033-frontmatter-schema-backed-validator" for contract in tcr_v1["contracts"])
    contract_v2 = next(contract for contract in tcr_v2["contracts"] if contract["contract_id"] == "post-h-033-frontmatter-schema-backed-validator")
    assert contract_v2["subgate_id"] == "schema-backed-validator-governance"
    assert contract_v2["network_allowed"] is False
    assert contract_v2["external_api_allowed"] is False
    assert contract_v2["source_mutations_allowed"] is False

    assert state["post_h_033_status"] == "closed/schema-backed-validators-declarative-semantics"
    assert state["post_h_033_a_closed"] is True
    assert state["post_h_033_b_frontmatter_catalog_available"] is True
    assert state["post_h_033_b_catalog_source_primary"] is True
    assert state["post_h_033_b_runtime_behavior_changed"] is False
    assert state["post_h_033_b_no_yaml_dependency_added"] is True
    assert state["post_h_033_b_critical_rules_disable_allowed"] is False
    assert "POST-H-033-B — Frontmatter schema-backed validator" in readme
    assert "POST-H-033-B — Frontmatter schema-backed validator" in runbook
    assert any(marker in backlog for marker in ['implementation_status: "active/post-h-033-c-implemented-initial"', 'implementation_status: "active/post-h-033-d-implemented-initial"', 'implementation_status: "active/post-h-033-e-implemented-initial"', 'implementation_status: "active/post-h-033-f-implemented-initial"'])
