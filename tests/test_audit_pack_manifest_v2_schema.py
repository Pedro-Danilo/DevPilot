from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.schemas import SchemaRegistry, SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_audit_pack_manifest_v2_schema_validates_sample_fixture() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="AuditPackManifestV2",
        instance="tests/fixtures/audit_pack_manifest_v2_sample.json",
    )

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS


def test_audit_pack_manifest_v2_blocks_compliance_claim_and_remote_export(tmp_path: Path) -> None:
    payload = read_json("tests/fixtures/audit_pack_manifest_v2_sample.json")
    payload["compliance_certification_claimed"] = True
    payload["remote_export_used"] = True
    instance = tmp_path / "bad_manifest.json"
    instance.write_text(json.dumps(payload), encoding="utf-8")

    result = SchemaValidator(ROOT).validate(schema="AuditPackManifestV2", instance=instance)

    assert result.ok is False
    assert result.exit_code != ExitCode.PASS
    assert any(finding.id == "SCHEMA_VALIDATION_ERROR" for finding in result.findings)


def test_audit_pack_integrity_report_schema_validates_sample_fixture() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="AuditPackIntegrityReport",
        instance="tests/fixtures/audit_pack_integrity_report_sample.json",
    )

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS


def test_audit_pack_policy_excludes_runtime_outputs_and_secrets() -> None:
    policy = read_json(".devpilot/auditpack/audit_pack_policy.json")
    excluded = set(policy["exclude_patterns"])
    forbidden_exact = set(policy["forbidden_exact_paths"])
    forbidden_prefixes = set(policy["forbidden_prefixes"])

    assert policy["created_by"] == "POST-H-013-A"
    assert policy["local_first"] is True
    assert policy["compliance_certification_claimed"] is False
    assert policy["remote_export_allowed"] is False
    assert policy["network_required"] is False
    assert policy["external_api_required"] is False
    assert "outputs/**" in excluded
    assert ".devpilot/devpilot.db" in excluded
    assert ".devpilot/agent_sessions/**" in excluded
    assert ".env" in excluded
    assert "**/*.pem" in excluded
    assert "**/*.key" in excluded
    assert ".devpilot/devpilot.db" in forbidden_exact
    assert "outputs/" in forbidden_prefixes
    assert ".devpilot/agent_sessions/" in forbidden_prefixes
    assert policy["redaction"]["redaction_report_required"] is True
    assert policy["redaction"]["raw_secret_export_policy"] == "block"
    assert policy["crypto"]["remote_kms_allowed"] is False
    assert policy["crypto"]["keys_in_repo_allowed"] is False


def test_schema_catalog_registers_audit_pack_v2_contracts() -> None:
    result = SchemaRegistry(ROOT).list()
    assert result.ok is True, result.to_dict()
    schemas = {item["contract"]: item for item in result.data["schemas"]}

    assert "AuditPackManifestV2" in schemas
    assert "AuditPackIntegrityReport" in schemas
    assert schemas["AuditPackManifestV2"]["schema_id"] == "SCHEMA-DEVPL-AUDIT-PACK-MANIFEST-V2"
    assert schemas["AuditPackIntegrityReport"]["schema_id"] == "SCHEMA-DEVPL-AUDIT-PACK-INTEGRITY-REPORT-V1"


def test_post_h_013_a_docs_and_contracts_are_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-013_audit_pack_integrity.md").read_text(encoding="utf-8")
    mirror = (ROOT / "docs/POST-H-013_audit_pack_integrity.md").read_text(encoding="utf-8")
    manifest = read_json("docs/post_h_013_a_manifest.json")
    tcr = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")

    assert backlog == mirror
    assert 'status: "approved"' in backlog
    assert 'implementation_status: "closed"' in backlog
    assert 'current_micro_sprint: "POST-H-013-E"' in backlog
    assert 'next_micro_sprint: "POST-H-014"' in backlog
    assert "## 14. Avance de implementación — POST-H-013-A" in backlog
    assert "## 17. Avance de implementación — POST-H-013-D" in backlog
    assert "## 18. Avance de implementación — POST-H-013-E" in backlog
    assert manifest["micro_sprint"] == "POST-H-013-A"
    assert manifest["current_repo"] == "repo_DevPilot_Local_196_POST_H_013_A.zip"

    contract = next(item for item in tcr["contracts"] if item["contract_id"] == "post-h-013-audit-pack-manifest-v2-policy")
    assert contract["owner"] == "POST-H-013-A"
    assert "tests/test_audit_pack_manifest_v2_schema.py" in contract["test_files"]
    assert "docs/schemas/audit_pack_manifest_v2.schema.json" in contract["validates"]

    contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-013-audit-pack-manifest-v2-policy")
    assert contract_v2["domain"] == "operations.audit"
    assert contract_v2["capability"] == "AuditPackManifestV2Policy"
    assert contract_v2["network_allowed"] is False
    assert contract_v2["external_api_allowed"] is False
    assert contract_v2["source_mutations_allowed"] is False
