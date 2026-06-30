from __future__ import annotations

import copy
import json
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.release import ReleaseReproducibilityPolicyValidator
from devpilot_core.schemas import SchemaRegistry, SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def test_post_h_017_a_release_reproducibility_schemas_are_registered() -> None:
    result = SchemaRegistry(ROOT).list()

    assert result.ok, result.to_dict()
    schema_ids = {schema["schema_id"] for schema in result.data["schemas"]}
    assert "SCHEMA-DEVPL-RELEASE-REPRODUCIBILITY-PACK-V1" in schema_ids
    assert "SCHEMA-DEVPL-RELEASE-ENVIRONMENT-SNAPSHOT-V1" in schema_ids
    assert "SCHEMA-DEVPL-RELEASE-SOURCE-ARCHIVE-MANIFEST-V1" in schema_ids
    assert "SCHEMA-DEVPL-RELEASE-REPRODUCIBILITY-VERIFICATION-V1" in schema_ids
    assert result.data["summary"]["schemas_total"] == len(schema_ids)


def test_post_h_017_a_release_pack_fixture_validates_against_schema() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="ReleaseReproducibilityPack",
        instance="tests/fixtures/release_reproducibility_pack.valid.json",
    )

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["valid"] is True


def test_post_h_017_a_environment_snapshot_fixture_is_redacted_and_valid() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="ReleaseEnvironmentSnapshot",
        instance="tests/fixtures/release_environment_snapshot.valid.json",
    )

    assert result.ok, result.to_dict()
    assert result.data["summary"]["valid"] is True

    fixture = json.loads((ROOT / "tests/fixtures/release_environment_snapshot.valid.json").read_text(encoding="utf-8"))
    assert fixture["redaction"]["env_files_read"] is False
    assert fixture["redaction"]["secret_values_read"] is False
    assert fixture["redaction"]["secret_values_included"] is False
    assert fixture["safety"]["secrets_included"] is False


def test_post_h_017_c_source_archive_manifest_fixture_is_valid_and_clean() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="ReleaseSourceArchiveManifest",
        instance="tests/fixtures/release_source_archive_manifest.valid.json",
    )

    assert result.ok, result.to_dict()
    assert result.data["summary"]["valid"] is True

    fixture = json.loads((ROOT / "tests/fixtures/release_source_archive_manifest.valid.json").read_text(encoding="utf-8"))
    assert fixture["created_by"] == "POST-H-017-C"
    assert fixture["exclusions"]["forbidden_entries_total"] == 0
    assert fixture["safety"]["secrets_included"] is False


def test_post_h_017_d_reproducibility_verification_fixture_is_valid() -> None:
    result = SchemaValidator(ROOT).validate(
        schema="ReleaseReproducibilityVerification",
        instance="tests/fixtures/release_reproducibility_verification.valid.json",
    )

    assert result.ok, result.to_dict()
    assert result.data["summary"]["valid"] is True

    fixture = json.loads((ROOT / "tests/fixtures/release_reproducibility_verification.valid.json").read_text(encoding="utf-8"))
    assert fixture["created_by"] == "POST-H-017-D"
    assert fixture["summary"]["release_reproducibility_verified"] is True
    assert fixture["safety"]["network_used"] is False


def test_post_h_017_a_reproducibility_policy_declares_blocking_exclusions() -> None:
    result = ReleaseReproducibilityPolicyValidator(ROOT).run()

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["policy_exists"] is True
    assert summary["dirty_repo_blocks_reproducible_release"] is True
    assert summary["secret_free_required"] is True
    assert summary["dry_run_only"] is True
    assert summary["runtime_artifacts_forbidden"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["secrets_read"] is False
    exclusions = set(result.data["policy"]["critical_exclusions"])
    assert {"outputs/", ".devpilot/devpilot.db", ".venv/", "node_modules/"}.issubset(exclusions)


def test_post_h_017_a_reproducibility_policy_blocks_missing_runtime_exclusions() -> None:
    validator = ReleaseReproducibilityPolicyValidator(ROOT)
    payload = copy.deepcopy(validator.load().payload)
    payload["critical_exclusions"] = ["outputs/"]

    findings = validator.validate_payload(payload)

    assert any(finding.id == "RELEASE_REPRODUCIBILITY_POLICY_EXCLUSIONS_MISSING" for finding in findings)
    assert any(finding.severity.value == "block" for finding in findings)


def test_post_h_017_a_docs_state_and_contracts_are_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-017_release_reproducibility_pack.md").read_text(encoding="utf-8")
    post_doc = (ROOT / "docs/POST-H-017_release_reproducibility_pack.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    tcr_v1 = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")
    source_registry = (ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8")

    assert 'status: "approved"' in backlog
    assert 'current_micro_sprint: "POST-H-017-D"' in backlog
    assert 'next_micro_sprint: "POST-H-017-E"' in backlog
    assert 'status: "approved"' in post_doc
    assert "POST-H-017-A — Release reproducibility schema y policy" in backlog
    assert "POST-H-017-A — Release reproducibility schema y policy" in post_doc
    assert "POST-H-017-C — Source archive manifest y checksums" in backlog
    assert "POST-H-017-C — Source archive manifest y checksums" in post_doc
    assert "POST-H-017-D — Verifier local de reproducibilidad" in backlog
    assert "POST-H-017-D — Verifier local de reproducibilidad" in post_doc
    assert "ReleaseReproducibilityPack" in readme
    assert "release_reproducibility_pack.schema.json" in runbook
    assert state["last_completed_sprint"] == "POST-H-016"
    assert state["next_sprint"] == "POST-H-017"
    assert state["current_micro_sprint"] == "POST-H-017-D"
    assert state["next_micro_sprint"] == "POST-H-017-E"
    assert "post-h-017-release-reproducibility-schema-policy" in tcr_v1
    assert "post-h-017-release-reproducibility-schema-policy" in tcr_v2
    assert "POST-H-017-IMPLEMENTATION" in source_registry
    assert "POST-H-017-REPRODUCIBILITY-POLICY" in source_registry
    assert "release_reproducibility_verifier_enabled" in source_registry
