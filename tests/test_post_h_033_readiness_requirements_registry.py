from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli import main
from devpilot_core.cli_models import ExitCode
from devpilot_core.schemas import SchemaValidator
from devpilot_core.validators.readiness import build_readiness_result, build_strict_readiness_result, check_required_artifacts
from devpilot_core.validators.readiness_requirements import load_readiness_requirements

ROOT = Path(__file__).resolve().parents[1]


def test_post_h_033_c_readiness_requirements_schema_validates() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="ReadinessRequirements",
        instance=".devpilot/readiness/readiness_requirements.json",
    )
    registry = json.loads((ROOT / ".devpilot/readiness/readiness_requirements.json").read_text(encoding="utf-8"))

    assert result.ok is True
    assert registry["created_by"] == "POST-H-033-C"
    assert registry["compatibility"]["runtime_behavior_changed"] is False
    assert registry["compatibility"]["python_fallback_preserved"] is True
    assert registry["compatibility"]["invalid_registry_blocks_success"] is True
    assert registry["safety"]["llm_judge_used"] is False
    assert registry["safety"]["critical_rules_disable_allowed"] is False
    assert "docs/06_miasi/agent_card.md" in registry["required_miasi_artifacts"]


def test_post_h_033_c_readiness_uses_registry_as_primary_source() -> None:
    registry = load_readiness_requirements(ROOT)
    result = build_strict_readiness_result(ROOT)

    assert registry.registry_valid is True
    assert registry.fallback_active is False
    assert registry.rule_source == ".devpilot/readiness/readiness_requirements.json"
    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["registry"]["rule_source"] == ".devpilot/readiness/readiness_requirements.json"
    assert result.data["registry"]["catalog_version"] == "1.0.0"
    assert result.data["summary"]["required_artifacts_total"] == len(registry.strict_required_artifacts)


def test_post_h_033_c_compatibility_readiness_preserves_required_artifacts() -> None:
    legacy = check_required_artifacts(ROOT)
    result = build_readiness_result(ROOT)

    assert legacy["ok"] is True
    assert result.ok is True
    registry = load_readiness_requirements(ROOT)
    assert result.data["registry"]["rule_source"] == ".devpilot/readiness/readiness_requirements.json"
    assert result.data["registry"]["required_pre_code_artifacts_total"] == len(registry.required_pre_code_artifacts)
    assert {item["artifact"] for item in legacy["checks"]} == set(registry.required_pre_code_artifacts)


def test_post_h_033_c_missing_registry_falls_back_without_false_missing_pass(tmp_path: Path) -> None:
    registry = load_readiness_requirements(tmp_path, emit_fallback_finding=True)
    result = build_strict_readiness_result(tmp_path)

    assert registry.fallback_active is True
    assert registry.findings
    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["registry"]["fallback_active"] is True
    assert any(f.id == "READINESS_REQUIREMENTS_REGISTRY_MISSING_FALLBACK_ACTIVE" for f in result.findings)
    assert any(f.id == "READINESS_STRICT_REQUIRED_ARTIFACT_MISSING" for f in result.findings)


def test_post_h_033_c_invalid_registry_blocks_success_even_with_fallback(tmp_path: Path) -> None:
    registry_path = tmp_path / ".devpilot" / "readiness" / "readiness_requirements.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text("{invalid-json", encoding="utf-8")

    registry = load_readiness_requirements(tmp_path, emit_fallback_finding=True)
    result = build_readiness_result(tmp_path)

    assert registry.fallback_active is True
    assert registry.findings[0].severity.value == "block"
    assert result.ok is False
    assert result.exit_code == ExitCode.FAIL
    assert any(f.id == "READINESS_REQUIREMENTS_REGISTRY_INVALID_JSON_BLOCKED" for f in result.findings)


def test_post_h_033_c_miasi_artifacts_remain_required_for_strict_readiness(tmp_path: Path) -> None:
    registry = load_readiness_requirements(ROOT)
    for rel in registry.strict_required_artifacts:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "---\n"
            "title: Synthetic\n"
            "doc_id: SYNTHETIC\n"
            "status: approved\n"
            "version: 1.0.0\n"
            "owner: Ordóñez\n"
            "updated: 2026-07-11\n"
            "approval: approved\n"
            "---\n# Synthetic\n",
            encoding="utf-8",
        )
    (tmp_path / "docs/06_miasi/agent_card.md").unlink()

    result = build_strict_readiness_result(tmp_path)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(f.id == "READINESS_STRICT_REQUIRED_ARTIFACT_MISSING" and f.path == "docs/06_miasi/agent_card.md" for f in result.findings)
    assert any(f.id == "READINESS_STRICT_MIASI_ARTIFACT_MISSING" and f.path == "docs/06_miasi/agent_card.md" for f in result.findings)


def test_post_h_033_c_cli_and_manifest_contracts_are_synced(capsys) -> None:
    exit_code = main(["schema", "validate", "--schema-id", "ReadinessRequirements", "--instance", ".devpilot/readiness/readiness_requirements.json", "--json"])
    payload = json.loads(capsys.readouterr().out)
    manifest_result = SchemaValidator(ROOT).validate(schema="ReadinessRequirements", instance="docs/post_h_033_c_manifest.json")

    assert exit_code == 0
    assert payload["ok"] is True
    assert manifest_result.ok is True


def test_post_h_033_c_governance_artifacts_registered_and_docs_synced() -> None:
    source_registry = json.loads((ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8"))
    schema_catalog = json.loads((ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8"))
    tcr_v1 = json.loads((ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8"))
    tcr_v2 = json.loads((ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8"))
    state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-033_schema_backed_validators_declarative_semantics.md").read_text(encoding="utf-8")

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert "POST-H-033-C-READINESS-REQUIREMENTS" in doc_ids
    assert "SCHEMA-DEVPL-READINESS-REQUIREMENTS-V1" in doc_ids
    assert "POST-H-033-C-READINESS-REQUIREMENTS-MODULE" in doc_ids
    assert "POST-H-033-C-READINESS-REQUIREMENTS-TEST" in doc_ids

    schema_ids = {item["schema_id"] for item in schema_catalog["schemas"]}
    assert "SCHEMA-DEVPL-READINESS-REQUIREMENTS-V1" in schema_ids
    assert any(contract["contract_id"] == "post-h-033-readiness-requirements-registry" for contract in tcr_v1["contracts"])
    contract_v2 = next(contract for contract in tcr_v2["contracts"] if contract["contract_id"] == "post-h-033-readiness-requirements-registry")
    assert contract_v2["subgate_id"] == "schema-backed-validator-governance"
    assert contract_v2["network_allowed"] is False
    assert contract_v2["external_api_allowed"] is False
    assert contract_v2["source_mutations_allowed"] is False

    assert state["current_micro_sprint"] in {"POST-H-033-C", "POST-H-033-D", "POST-H-033-E", "POST-H-033-F"}
    assert state["next_micro_sprint"] in {"POST-H-033-D", "POST-H-033-E", "POST-H-033-F", "POST-H-033-CLOSURE"}
    assert state["post_h_033_b_closed"] is True
    assert state["post_h_033_c_readiness_requirements_available"] is True
    assert state["post_h_033_c_registry_source_primary"] is True
    assert state["post_h_033_c_python_fallback_required"] is True
    assert state["post_h_033_c_invalid_registry_blocks_success"] is True
    assert state["post_h_033_c_miasi_strict_required_preserved"] is True
    assert "POST-H-033-C — Readiness requirements registry" in readme
    assert "POST-H-033-C — Readiness requirements registry" in runbook
    assert any(marker in backlog for marker in ['implementation_status: "active/post-h-033-c-implemented-initial"', 'implementation_status: "active/post-h-033-d-implemented-initial"', 'implementation_status: "active/post-h-033-e-implemented-initial"', 'implementation_status: "active/post-h-033-f-implemented-initial"'])
