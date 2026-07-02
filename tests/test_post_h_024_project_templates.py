from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from devpilot_core.onboarding.templates import (
    MARKDOWN_TEMPLATE_PATHS,
    MIASI_TEMPLATE_PATHS,
    REQUIRED_TEMPLATE_PATHS,
    validate_new_project_templates,
)
from devpilot_core.validators.frontmatter import parse_frontmatter_file, validate_frontmatter_file

ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read_text(path))


def test_markdown_templates_have_valid_frontmatter_and_required_sections() -> None:
    expected_doc_ids = {
        "docs/templates/new_project/product_vision.template.md": "NEW-PROJECT-PRODUCT-VISION-TEMPLATE",
        "docs/templates/new_project/mvp_scope.template.md": "NEW-PROJECT-MVP-SCOPE-TEMPLATE",
        "docs/templates/new_project/requirements_specification.template.md": "NEW-PROJECT-REQUIREMENTS-SPECIFICATION-TEMPLATE",
        "docs/templates/new_project/architecture_document.template.md": "NEW-PROJECT-ARCHITECTURE-DOCUMENT-TEMPLATE",
        "docs/templates/new_project/security_threat_model.template.md": "NEW-PROJECT-SECURITY-THREAT-MODEL-TEMPLATE",
        "docs/templates/new_project/test_strategy.template.md": "NEW-PROJECT-TEST-STRATEGY-TEMPLATE",
    }
    assert set(MARKDOWN_TEMPLATE_PATHS) == set(expected_doc_ids)

    for rel_path, expected_doc_id in expected_doc_ids.items():
        path = ROOT / rel_path
        assert path.exists(), rel_path
        parsed = parse_frontmatter_file(path)
        assert parsed.has_frontmatter
        assert parsed.frontmatter["doc_id"] == expected_doc_id
        assert parsed.frontmatter["status"] == "approved"
        assert parsed.frontmatter["implementation_status"] == "implemented-initial"
        assert parsed.frontmatter["created_by"] == "POST-H-024-B"
        assert parsed.frontmatter["preliminary"] is True
        assert parsed.frontmatter["local_first"] is True
        assert parsed.frontmatter["dry_run"] is True
        assert parsed.frontmatter["no_external_apis_required"] is True
        assert parsed.frontmatter["no_secrets_allowed"] is True
        result = validate_frontmatter_file(path, root=ROOT, strict=True)
        assert result.ok, result.to_dict()

        text = path.read_text(encoding="utf-8")
        assert "{{project_name}}" in text
        assert "PASS" in text
        assert "BLOCK" in text
        assert "no_secrets" in text or "secretos" in text.lower() or "secrets" in text.lower()


def test_miasi_json_templates_are_schema_valid_and_local_first() -> None:
    schema_map = {
        "MiasiAgentRegistry": "docs/schemas/miasi_agent_registry.schema.json",
        "MiasiToolRegistry": "docs/schemas/miasi_tool_registry.schema.json",
        "MiasiPolicyMatrix": "docs/schemas/miasi_policy_matrix.schema.json",
    }
    assert set(MIASI_TEMPLATE_PATHS) == set(schema_map)

    for schema_id, rel_path in MIASI_TEMPLATE_PATHS.items():
        payload = read_json(rel_path)
        schema = read_json(schema_map[schema_id])
        errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda error: list(error.path))
        assert not errors, [error.message for error in errors]
        assert payload["schema_version"] == "1.0"
        assert payload["source_document"].startswith("docs/06_miasi/")
        assert payload["created_by"] == "FUNC-SPRINT-23"
        assert "POST-H-024-B" in payload["description"] or "template" in payload["description"].lower()

    agent_template = read_json("docs/templates/new_project/miasi_agent_registry.template.json")
    tool_template = read_json("docs/templates/new_project/miasi_tool_registry.template.json")
    policy_template = read_json("docs/templates/new_project/miasi_policy_matrix.template.json")

    assert agent_template["agents"]
    assert all(agent["max_autonomy"] in {"A0", "A1", "A2", "A1/A2"} for agent in agent_template["agents"])
    assert all(agent["status"] == "planned" for agent in agent_template["agents"])
    assert all(tool["side_effect"] in {"none", "read", "report", "simulation"} for tool in tool_template["tools"])
    assert any(rule["default_effect"] == "block" for rule in policy_template["rules"])
    assert any(rule["rule_id"] == "POLICY-NO-SECRETS" for rule in policy_template["rules"])


def test_templates_do_not_contain_secrets_or_vendor_lock_in() -> None:
    forbidden_fragments = [
        "api_key",
        "access_token",
        "private_key",
        "secret_key",
        "BEGIN PRIVATE KEY",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "MISTRAL_API_KEY",
        "ANTHROPIC_API_KEY",
    ]
    vendor_lock_fragments = [
        "requires openai",
        "requires gemini",
        "requires anthropic",
        "requires mistral",
        "only openai",
        "only gemini",
    ]
    for rel_path in REQUIRED_TEMPLATE_PATHS:
        text = read_text(rel_path)
        lowered = text.lower()
        for fragment in forbidden_fragments:
            assert fragment.lower() not in lowered, f"{fragment} found in {rel_path}"
        for fragment in vendor_lock_fragments:
            assert fragment not in lowered, f"Vendor lock-in phrase {fragment!r} found in {rel_path}"

    architecture = read_text("docs/templates/new_project/architecture_document.template.md")
    requirements = read_text("docs/templates/new_project/requirements_specification.template.md")
    assert "ModelAdapter" in architecture
    assert "Ruta sin API" in requirements
    assert "Ruta local" in requirements
    assert "API externa futura" in requirements


def test_onboarding_template_validator_is_read_only_and_passes() -> None:
    result = validate_new_project_templates(ROOT)
    assert result.ok, result.to_dict()
    payload = result.to_dict()
    assert set(payload["checked_paths"]) == set(REQUIRED_TEMPLATE_PATHS)
    assert payload["network_used"] is False
    assert payload["external_api_used"] is False
    assert payload["mutations_performed"] is False
    assert payload["source_mutations_performed"] is False


def test_post_h_024_b_manifest_registry_and_contracts_are_synchronized() -> None:
    manifest = read_json("docs/post_h_024_b_manifest.json")
    source_registry = read_json(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")

    assert manifest["post_h_id"] == "POST-H-024"
    assert manifest["micro_sprint"] == "POST-H-024-B"
    assert manifest["status"] == "implemented-initial"
    assert manifest["next_micro_sprint"] == "POST-H-024-C"
    assert manifest["no_remote_execution_enabled"] is True
    assert manifest["no_external_apis_used"] is True
    assert manifest["no_connector_write_enabled"] is True
    assert manifest["no_plugin_execution_enabled"] is True

    for rel_path in REQUIRED_TEMPLATE_PATHS:
        assert rel_path in manifest["created_files"]

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    expected_doc_ids = {
        "NEW-PROJECT-PRODUCT-VISION-TEMPLATE",
        "NEW-PROJECT-MVP-SCOPE-TEMPLATE",
        "NEW-PROJECT-REQUIREMENTS-SPECIFICATION-TEMPLATE",
        "NEW-PROJECT-ARCHITECTURE-DOCUMENT-TEMPLATE",
        "NEW-PROJECT-SECURITY-THREAT-MODEL-TEMPLATE",
        "NEW-PROJECT-TEST-STRATEGY-TEMPLATE",
        "POST-H-024-B-MIASI-AGENT-TEMPLATE",
        "POST-H-024-B-MIASI-TOOL-TEMPLATE",
        "POST-H-024-B-MIASI-POLICY-TEMPLATE",
        "POST-H-024-B-PROJECT-TEMPLATES-REPORT",
        "POST-H-024-B-MANIFEST",
        "POST-H-024-B-ONBOARDING-TEMPLATES-MODULE",
        "POST-H-024-B-PROJECT-TEMPLATES-TEST",
    }
    assert expected_doc_ids <= doc_ids
    assert source_registry["project_state_snapshot"]["current_micro_sprint"] == "POST-H-024-C"
    assert source_registry["project_state_snapshot"]["next_micro_sprint"] == "POST-H-024-D"
    assert source_registry["project_state_snapshot"]["post_h_024_templates_available"] is True

    contract_ids_v1 = {item["contract_id"] for item in tcr_v1["contracts"]}
    contract_ids_v2 = {item["contract_id"] for item in tcr_v2["contracts"]}
    assert "post-h-024-project-templates" in contract_ids_v1
    assert "post-h-024-project-templates" in contract_ids_v2
    contract = next(item for item in tcr_v1["contracts"] if item["contract_id"] == "post-h-024-project-templates")
    assert contract["critical"] is True
    assert contract["mutable_global_state_allowed"] is False
    assert contract["network_allowed"] is False
    assert contract["external_api_allowed"] is False
    assert contract["mutations_allowed"] is False


def test_post_h_024_documents_and_global_state_advance_to_b_only() -> None:
    state = read_json(".devpilot/project_state.json")
    backlog = read_text("docs/backlogs/POST-H-024_operator_onboarding_bootstrap.md")
    implementation = read_text("docs/POST-H-024_operator_onboarding_bootstrap.md")
    report = read_text("docs/audits/post_h_024_b_project_templates_report.md")
    readme = read_text("README.md")
    runbook = read_text("docs/05_operations/runbook.md")
    changelog = read_text("docs/release/CHANGELOG.md")

    assert state["current_micro_sprint"] == "POST-H-024-C"
    assert state["next_micro_sprint"] == "POST-H-024-D"
    assert state["post_h_024_current_micro_sprint"] == "POST-H-024-C"
    assert state["post_h_024_next_micro_sprint"] == "POST-H-024-D"
    assert state["post_h_024_operator_playbook_available"] is True
    assert state["post_h_024_templates_available"] is True
    assert state["post_h_024_bootstrap_workflow_available"] is True
    assert state["post_h_024_project_bootstrap_report_available"] is True
    assert state["post_h_024_readiness_preview_available"] is False
    assert state["post_h_024_onboarding_quality_gate_available"] is False
    assert state["post_h_024_network_used"] is False
    assert state["post_h_024_external_api_used"] is False
    assert state["post_h_024_remote_execution_enabled"] is False
    assert state["post_h_024_connector_write_enabled"] is False
    assert state["post_h_024_plugin_execution_enabled"] is False
    assert state["post_h_024_secrets_included"] is False

    for text in (backlog, implementation):
        assert 'current_micro_sprint: "POST-H-024-C"' in text
        assert 'next_micro_sprint: "POST-H-024-D"' in text
        assert "POST-H-024-B" in text
        assert "implemented-initial" in text
        assert "templates-only" in text

    assert "POST-H-024-B — Templates de proyecto nuevo" in readme
    assert "POST-H-024-B — Templates de proyecto nuevo" in runbook
    assert "Siguiente micro-sprint: `POST-H-024-D — Onboarding validation y readiness preview`" in readme
    assert "workspace bootstrap" in report
    assert "post-h-024-b" in changelog
