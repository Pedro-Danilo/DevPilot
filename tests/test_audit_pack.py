from __future__ import annotations

import json
import zipfile
from pathlib import Path

from devpilot_core import cli
from devpilot_core.auditpack import AuditPackBuildOptions, AuditPackBuilder, AuditPackVerifyOptions
from devpilot_core.cli_models import ExitCode

ROOT = Path(__file__).resolve().parents[1]


def test_audit_pack_build_creates_clean_zip_with_manifest() -> None:
    result = AuditPackBuilder(ROOT).build(AuditPackBuildOptions(actor="local-owner"))

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["secrets_exported"] is False
    assert summary["runtime_db_exported"] is False
    assert summary["providers_local_exported"] is False
    assert summary["manifest_embedded"] is True
    pack_path = ROOT / summary["pack_path"]
    assert pack_path.exists()

    with zipfile.ZipFile(pack_path) as archive:
        names = set(archive.namelist())
        assert "audit-pack-manifest.json" in names
        assert ".devpilot/devpilot.db" not in names
        assert ".devpilot/providers.yaml" not in names
        assert ".env" not in names
        manifest = json.loads(archive.read("audit-pack-manifest.json").decode("utf-8"))
    assert manifest["schema_id"] == "SCHEMA-DEVPL-AUDIT-PACK-MANIFEST-V1"
    assert manifest["secrets_exported"] is False
    assert manifest["runtime_db_exported"] is False
    assert manifest["entries_total"] == len(manifest["entries"])
    assert "docs/release/CHANGELOG.md" in manifest["checksums"]


def test_audit_pack_verify_passes_for_generated_pack() -> None:
    built = AuditPackBuilder(ROOT).build(AuditPackBuildOptions(actor="local-owner"))
    pack_path = built.data["summary"]["pack_path"]

    result = AuditPackBuilder(ROOT).verify(AuditPackVerifyOptions(path=pack_path))

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["manifest_present"] is True
    assert summary["checksum_mismatches"] == 0
    assert summary["forbidden_paths_total"] == 0
    assert summary["secret_findings_total"] == 0


def test_audit_pack_build_blocks_runtime_db_export_request() -> None:
    result = AuditPackBuilder(ROOT).build(AuditPackBuildOptions(actor="local-owner", include_runtime_db=True, confirm_include_runtime_db=True))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "AUDIT_PACK_RUNTIME_DB_EXPORT_BLOCKED" for finding in result.findings)


def test_audit_pack_cli_build_and_verify_json_are_parseable(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["audit-pack", "build", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "audit-pack build"
    assert payload["ok"] is True
    pack_path = payload["data"]["summary"]["pack_path"]

    exit_code = cli.main(["audit-pack", "verify", "--path", pack_path, "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "audit-pack verify"
    assert payload["ok"] is True


def test_audit_pack_verify_blocks_tampered_checksum(tmp_path: Path) -> None:
    built = AuditPackBuilder(ROOT).build(AuditPackBuildOptions(actor="local-owner"))
    source = ROOT / built.data["summary"]["pack_path"]
    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(tampered, "w", compression=zipfile.ZIP_DEFLATED) as dst:
        for name in src.namelist():
            data = src.read(name)
            if name == "README.md":
                data += b"\nTAMPERED\n"
            dst.writestr(name, data)

    # Verification is intentionally limited to governed workspace paths.
    relative = Path("outputs/auditpacks/tampered.zip")
    target = ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(tampered.read_bytes())
    result = AuditPackBuilder(ROOT).verify(AuditPackVerifyOptions(path=relative.as_posix()))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "AUDIT_PACK_CHECKSUM_MISMATCH" for finding in result.findings)


def test_audit_pack_eval_suite_passes(capsys) -> None:
    exit_code = cli.main(["eval", "run", "--suite", "audit-pack-integrity", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["data"]["summary"]["suite_id"] == "audit-pack-integrity"
    assert payload["data"]["summary"]["safety_score"] >= 90
