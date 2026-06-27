from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

from devpilot_core import cli
from devpilot_core.auditpack import AuditPackV2BuildOptions, AuditPackV2Builder, AuditPackV2VerifyOptions, AuditPackV2Verifier
from devpilot_core.cli_models import ExitCode
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
TEST_OUTPUT_DIR = "outputs/auditpacks/post_h_013_b_tests"


def _cleanup_test_output() -> None:
    shutil.rmtree(ROOT / TEST_OUTPUT_DIR, ignore_errors=True)


def _build_test_pack() -> Path:
    result = AuditPackV2Builder(ROOT).build(
        AuditPackV2BuildOptions(output_dir=TEST_OUTPUT_DIR, dry_run=False, execute=True)
    )
    assert result.ok is True, result.to_dict()
    return ROOT / result.data["summary"]["pack_path"]


def _rewrite_zip(source: Path, target: Path, replace: dict[str, bytes] | None = None, drop: set[str] | None = None, extra: dict[str, bytes] | None = None) -> None:
    replace = replace or {}
    drop = drop or set()
    extra = extra or {}
    with zipfile.ZipFile(source, "r") as src, zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as dst:
        for name in src.namelist():
            if name in drop:
                continue
            dst.writestr(name, replace.get(name, src.read(name)))
        for name, content in extra.items():
            dst.writestr(name, content)


def _first_payload_member(pack: Path) -> str:
    with zipfile.ZipFile(pack, "r") as archive:
        for name in archive.namelist():
            if name not in {"audit-pack-manifest-v2.json", "redaction_report.json"}:
                return name
    raise AssertionError("No payload member found in audit pack")


def test_audit_pack_build_v2_dry_run_does_not_write_pack_artifacts() -> None:
    _cleanup_test_output()

    result = AuditPackV2Builder(ROOT).build(
        AuditPackV2BuildOptions(output_dir=TEST_OUTPUT_DIR, dry_run=True, execute=False)
    )

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["dry_run"] is True
    assert summary["execute"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False
    assert summary["pack_path"] is None
    assert summary["manifest_path"] is None
    assert summary["redaction_report_path"] is None
    assert summary["files_included"] > 0
    assert summary["files_with_sha256"] == summary["files_included"]
    assert summary["redaction_report_present"] is True
    assert summary["secrets_detected"] == 0
    assert not (ROOT / TEST_OUTPUT_DIR).exists()


def test_audit_pack_build_v2_execute_writes_zip_manifest_and_redaction_report() -> None:
    _cleanup_test_output()
    try:
        result = AuditPackV2Builder(ROOT).build(
            AuditPackV2BuildOptions(output_dir=TEST_OUTPUT_DIR, dry_run=False, execute=True)
        )

        assert result.ok is True, result.to_dict()
        assert result.exit_code == ExitCode.PASS
        summary = result.data["summary"]
        assert summary["mode"] == "execute"
        assert summary["mutations_performed"] is True
        assert summary["source_mutations_performed"] is False
        assert summary["redaction_report_written"] is True
        assert summary["redaction_report_embedded"] is True
        assert summary["manifest_embedded"] is True
        assert summary["files_with_sha256"] == summary["files_included"]
        assert summary["runtime_db_exported"] is False
        assert summary["agent_sessions_exported"] is False
        assert summary["env_files_exported"] is False
        assert summary["remote_export_used"] is False
        assert summary["network_used"] is False
        assert summary["external_api_used"] is False
        assert summary["compliance_certification_claimed"] is False

        pack_path = ROOT / summary["pack_path"]
        manifest_path = ROOT / summary["manifest_path"]
        redaction_report_path = ROOT / summary["redaction_report_path"]
        assert pack_path.exists()
        assert manifest_path.exists()
        assert redaction_report_path.exists()

        manifest_validation = SchemaValidator(ROOT).validate(
            schema="AuditPackManifestV2",
            instance=summary["manifest_path"],
        )
        assert manifest_validation.ok is True, manifest_validation.to_dict()

        with zipfile.ZipFile(pack_path) as archive:
            names = set(archive.namelist())
            assert "audit-pack-manifest-v2.json" in names
            assert "redaction_report.json" in names
            assert ".devpilot/devpilot.db" not in names
            assert ".env" not in names
            assert not any(name.startswith(".devpilot/agent_sessions/") for name in names)
            manifest = json.loads(archive.read("audit-pack-manifest-v2.json").decode("utf-8"))
            redaction_report = json.loads(archive.read("redaction_report.json").decode("utf-8"))
        assert manifest["schema_id"] == "SCHEMA-DEVPL-AUDIT-PACK-MANIFEST-V2"
        assert manifest["integrity"]["manifest_hash"]
        assert manifest["redaction"]["redaction_report_present"] is True
        assert manifest["redaction"]["redaction_passed"] is True
        assert redaction_report["redaction_passed"] is True
        assert redaction_report["secrets_detected"] == 0
        assert "redaction_report.json" in {item["path"] for item in manifest["files"]}
        assert all(item["sha256"] and len(item["sha256"]) == 64 for item in manifest["files"])
    finally:
        _cleanup_test_output()


def test_audit_pack_build_v2_blocks_material_secret_like_content(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / ".devpilot/auditpack").mkdir(parents=True)
    (tmp_path / ".devpilot/identity").mkdir(parents=True)
    shutil.copyfile(ROOT / ".devpilot/identity/identity_registry.json", tmp_path / ".devpilot/identity/identity_registry.json")
    policy = {
        "schema_version": "1.0",
        "policy_id": "test-audit-pack-policy-v2",
        "local_first": True,
        "compliance_certification_claimed": False,
        "remote_export_allowed": False,
        "network_required": False,
        "external_api_required": False,
        "include_patterns": ["docs/**"],
        "exclude_patterns": ["outputs/**", ".env", ".env.*", ".devpilot/devpilot.db", ".devpilot/agent_sessions/**"],
        "forbidden_exact_paths": [".devpilot/devpilot.db", ".env"],
        "forbidden_prefixes": ["outputs/", ".devpilot/agent_sessions/"],
        "redaction": {"redaction_report_required": True, "raw_secret_export_policy": "block"},
    }
    (tmp_path / ".devpilot/auditpack/audit_pack_policy.json").write_text(json.dumps(policy), encoding="utf-8")
    (tmp_path / "docs/secret.md").write_text("sk-proj-abcdefghijklmnopqrstuvwxyz123456", encoding="utf-8")

    result = AuditPackV2Builder(tmp_path).build(AuditPackV2BuildOptions(dry_run=True, execute=False))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["secrets_detected"] > 0
    assert result.data["summary"]["pack_path"] is None
    assert any(finding.id == "AUDIT_PACK_V2_SECRET_DETECTED_BLOCKED" for finding in result.findings)


def test_audit_pack_build_v2_cli_json_is_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["audit-pack", "build-v2", "--dry-run", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "audit-pack build-v2"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["dry_run"] is True
    assert payload["data"]["summary"]["pack_path"] is None


def test_post_h_013_b_docs_and_contracts_are_synchronized() -> None:
    backlog = (ROOT / "docs/backlogs/POST-H-013_audit_pack_integrity.md").read_text(encoding="utf-8")
    mirror = (ROOT / "docs/POST-H-013_audit_pack_integrity.md").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "docs/post_h_013_b_manifest.json").read_text(encoding="utf-8"))
    tcr = json.loads((ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8"))
    tcr_v2 = json.loads((ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8"))

    assert backlog == mirror
    assert 'current_micro_sprint: "POST-H-013-C"' in backlog
    assert 'next_micro_sprint: "POST-H-013-D"' in backlog
    assert "## 15. Avance de implementación — POST-H-013-B" in backlog
    assert "## 16. Avance de implementación — POST-H-013-C" in backlog
    manifest = json.loads((ROOT / "docs/post_h_013_c_manifest.json").read_text(encoding="utf-8"))
    assert manifest["micro_sprint"] == "POST-H-013-C"
    assert manifest["current_repo"] == "repo_DevPilot_Local_198_POST_H_013_C.zip"

    contract = next(item for item in tcr["contracts"] if item["contract_id"] == "post-h-013-audit-pack-builder-v2")
    assert contract["owner"] == "POST-H-013-B"
    assert "tests/test_post_h_013_audit_pack_integrity.py" in contract["test_files"]
    assert "src/devpilot_core/auditpack/manifest_v2.py" in contract["validates"]

    contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-013-audit-pack-builder-v2")
    assert contract_v2["capability"] == "AuditPackV2Builder"
    assert contract_v2["network_allowed"] is False
    assert contract_v2["external_api_allowed"] is False
    assert contract_v2["source_mutations_allowed"] is False

    verifier_contract = next(item for item in tcr["contracts"] if item["contract_id"] == "post-h-013-audit-pack-verifier-v2")
    assert verifier_contract["owner"] == "POST-H-013-C"
    assert "src/devpilot_core/auditpack/verify_v2.py" in verifier_contract["validates"]

    verifier_contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-013-audit-pack-verifier-v2")
    assert verifier_contract_v2["capability"] == "AuditPackV2Verifier"
    assert verifier_contract_v2["network_allowed"] is False
    assert verifier_contract_v2["external_api_allowed"] is False
    assert verifier_contract_v2["source_mutations_allowed"] is False


def test_audit_pack_verify_v2_passes_clean_pack_and_writes_integrity_report() -> None:
    _cleanup_test_output()
    try:
        pack_path = _build_test_pack()

        result = AuditPackV2Verifier(ROOT).verify(AuditPackV2VerifyOptions(pack=str(pack_path.relative_to(ROOT)), output_dir=TEST_OUTPUT_DIR))

        assert result.ok is True, result.to_dict()
        assert result.exit_code == ExitCode.PASS
        summary = result.data["summary"]
        report = result.data["integrity_report"]
        assert summary["manifest_schema_valid"] is True
        assert summary["manifest_hash_valid"] is True
        assert summary["files_total"] == summary["files_verified"]
        assert summary["hash_mismatches_total"] == 0
        assert summary["missing_files_total"] == 0
        assert summary["extra_files_total"] == 0
        assert summary["network_used"] is False
        assert summary["external_api_used"] is False
        assert summary["source_mutations_performed"] is False
        assert report["schema_id"] == "SCHEMA-DEVPL-AUDIT-PACK-INTEGRITY-REPORT-V1"
        assert report["status"] == "passed"
        assert report["compliance_certification_claimed"] is False
        assert (ROOT / summary["integrity_report_path"]).exists()
        schema_result = SchemaValidator(ROOT).validate(
            schema="AuditPackIntegrityReport",
            instance=summary["integrity_report_path"],
        )
        assert schema_result.ok is True, schema_result.to_dict()
    finally:
        _cleanup_test_output()


def test_audit_pack_verify_v2_blocks_hash_mismatch() -> None:
    _cleanup_test_output()
    try:
        pack_path = _build_test_pack()
        member = _first_payload_member(pack_path)
        tampered = ROOT / TEST_OUTPUT_DIR / "tampered_hash.zip"
        _rewrite_zip(pack_path, tampered, replace={member: b"tampered-content"})

        result = AuditPackV2Verifier(ROOT).verify(AuditPackV2VerifyOptions(pack=str(tampered.relative_to(ROOT)), output_dir=TEST_OUTPUT_DIR))

        assert result.ok is False
        assert result.exit_code == ExitCode.BLOCK
        assert result.data["summary"]["hash_mismatches_total"] == 1
        assert any(finding.id == "AUDIT_PACK_V2_HASH_MISMATCH" for finding in result.findings)
    finally:
        _cleanup_test_output()


def test_audit_pack_verify_v2_blocks_missing_declared_file() -> None:
    _cleanup_test_output()
    try:
        pack_path = _build_test_pack()
        member = _first_payload_member(pack_path)
        tampered = ROOT / TEST_OUTPUT_DIR / "tampered_missing.zip"
        _rewrite_zip(pack_path, tampered, drop={member})

        result = AuditPackV2Verifier(ROOT).verify(AuditPackV2VerifyOptions(pack=str(tampered.relative_to(ROOT)), output_dir=TEST_OUTPUT_DIR))

        assert result.ok is False
        assert result.exit_code == ExitCode.BLOCK
        assert result.data["summary"]["missing_files_total"] == 1
        assert any(finding.id == "AUDIT_PACK_V2_ENTRY_MISSING" for finding in result.findings)
    finally:
        _cleanup_test_output()


def test_audit_pack_verify_v2_blocks_extra_undeclared_file() -> None:
    _cleanup_test_output()
    try:
        pack_path = _build_test_pack()
        tampered = ROOT / TEST_OUTPUT_DIR / "tampered_extra.zip"
        _rewrite_zip(pack_path, tampered, extra={"undeclared-extra.txt": b"extra"})

        result = AuditPackV2Verifier(ROOT).verify(AuditPackV2VerifyOptions(pack=str(tampered.relative_to(ROOT)), output_dir=TEST_OUTPUT_DIR))

        assert result.ok is False
        assert result.exit_code == ExitCode.BLOCK
        assert result.data["summary"]["extra_files_total"] == 1
        assert any(finding.id == "AUDIT_PACK_V2_EXTRA_MEMBER_BLOCKED" for finding in result.findings)
    finally:
        _cleanup_test_output()


def test_audit_pack_verify_v2_blocks_compliance_claim_drift() -> None:
    _cleanup_test_output()
    try:
        pack_path = _build_test_pack()
        with zipfile.ZipFile(pack_path, "r") as archive:
            manifest = json.loads(archive.read("audit-pack-manifest-v2.json").decode("utf-8"))
        manifest["compliance_certification_claimed"] = True
        tampered = ROOT / TEST_OUTPUT_DIR / "tampered_compliance.zip"
        _rewrite_zip(
            pack_path,
            tampered,
            replace={"audit-pack-manifest-v2.json": json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")},
        )

        result = AuditPackV2Verifier(ROOT).verify(AuditPackV2VerifyOptions(pack=str(tampered.relative_to(ROOT)), output_dir=TEST_OUTPUT_DIR))

        assert result.ok is False
        assert result.exit_code == ExitCode.BLOCK
        assert any(finding.id == "AUDIT_PACK_V2_MANIFEST_SCHEMA_INVALID" for finding in result.findings)
        assert any(finding.id == "AUDIT_PACK_V2_SAFETY_FLAG_INVALID" for finding in result.findings)
    finally:
        _cleanup_test_output()


def test_audit_pack_verify_v2_cli_json_is_parseable(monkeypatch, capsys) -> None:
    _cleanup_test_output()
    try:
        pack_path = _build_test_pack()
        monkeypatch.chdir(ROOT)

        exit_code = cli.main(["audit-pack", "verify-v2", "--pack", str(pack_path.relative_to(ROOT)), "--output-dir", TEST_OUTPUT_DIR, "--json"])
        payload = json.loads(capsys.readouterr().out)

        assert exit_code == 0
        assert payload["command"] == "audit-pack verify-v2"
        assert payload["ok"] is True
        assert payload["data"]["summary"]["manifest_schema_valid"] is True
        assert payload["data"]["summary"]["files_total"] == payload["data"]["summary"]["files_verified"]
    finally:
        _cleanup_test_output()
