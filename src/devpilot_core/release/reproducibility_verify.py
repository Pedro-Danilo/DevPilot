from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.release.reproducibility_policy import ReleaseReproducibilityPolicyValidator
from devpilot_core.schemas import SchemaValidator

DEFAULT_VERIFICATION_JSON = Path("outputs/release/reproducibility_verification.json")
DEFAULT_VERIFICATION_MARKDOWN = Path("outputs/release/reproducibility_verification.md")

REQUIRED_FALSE_SAFETY_FLAGS = (
    "published",
    "deployed",
    "network_used",
    "external_api_used",
    "remote_execution_used",
    "connector_write_used",
    "plugin_execution_used",
    "mutations_performed",
    "source_mutations_performed",
    "secrets_included",
)

REQUIRED_TRUE_SAFETY_FLAGS = ("local_first", "dry_run")
REQUIRED_VALIDATION_KEYS = (
    "quality_gate_hardening",
    "test_contracts",
    "test_contracts_v2",
    "docs_governance",
    "industrial_readiness",
)


@dataclass(frozen=True)
class ReleaseReproducibilityVerifyOptions:
    """Options for POST-H-017-D local reproducibility verification."""

    pack: Path | str
    write_report: bool = False
    output_json: Path | str = DEFAULT_VERIFICATION_JSON
    output_markdown: Path | str = DEFAULT_VERIFICATION_MARKDOWN


class ReleaseReproducibilityVerifier:
    """Verify a local ReleaseReproducibilityPack without publishing or deploying."""

    def __init__(self, root: Path, *, options: ReleaseReproducibilityVerifyOptions) -> None:
        self.root = Path(root).resolve()
        self.options = options

    def verify(self) -> CommandResult:
        findings: list[Finding] = []
        pack_path = _resolve_path(self.root, self.options.pack)
        pack_display = _display_path(self.root, pack_path)
        pack_payload = self._load_pack(pack_path, findings)
        if pack_payload is None:
            return self._result(
                ok=False,
                findings=findings,
                pack_path=pack_display,
                verification=None,
                reports={},
            )

        schema_result = SchemaValidator(self.root).validate(schema="ReleaseReproducibilityPack", instance=pack_path)
        findings.extend(_prefixed_findings(schema_result.findings, prefix="PACK_SCHEMA"))

        policy_result = ReleaseReproducibilityPolicyValidator(self.root).run()
        findings.extend(_prefixed_findings(policy_result.findings, prefix="POLICY"))

        findings.extend(self._verify_git_section(pack_payload))
        findings.extend(self._verify_safety(pack_payload))
        findings.extend(self._verify_validation_declarations(pack_payload))
        artifact_checks = self._verify_artifacts(pack_payload, findings)

        blocking_findings = _blocking_findings(findings)
        verification = self._verification_payload(
            pack_path=pack_display,
            pack=pack_payload,
            artifact_checks=artifact_checks,
            findings_total=len(findings),
            blocking_findings_total=len(blocking_findings),
            pack_schema_valid=not any(
                finding.id.startswith("PACK_SCHEMA_") and finding in blocking_findings
                for finding in findings
            ),
        )
        reports: dict[str, str] = {}
        if self.options.write_report:
            reports = {
                "json": _display_path(self.root, _resolve_path(self.root, self.options.output_json)),
                "markdown": _display_path(self.root, _resolve_path(self.root, self.options.output_markdown)),
            }
            verification["summary"]["reports_written"] = True
            verification["summary"]["output_json"] = reports["json"]
            verification["summary"]["output_markdown"] = reports["markdown"]
            self._write_reports(verification)

        return self._result(
            ok=not blocking_findings,
            findings=findings,
            pack_path=pack_display,
            verification=verification,
            reports=reports,
        )

    def _load_pack(self, path: Path, findings: list[Finding]) -> dict[str, Any] | None:
        if not path.exists():
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_PACK_MISSING",
                    "Release reproducibility pack file is missing.",
                    Severity.BLOCK,
                    path=_display_path(self.root, path),
                )
            )
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_PACK_INVALID_JSON",
                    f"Release reproducibility pack is not valid JSON: {exc.msg}",
                    Severity.ERROR,
                    path=_display_path(self.root, path),
                    metadata={"line": exc.lineno, "column": exc.colno},
                )
            )
            return None
        if not isinstance(payload, dict):
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_PACK_ROOT_INVALID",
                    "Release reproducibility pack root must be a JSON object.",
                    Severity.ERROR,
                    path=_display_path(self.root, path),
                )
            )
            return None
        return payload

    def _verify_git_section(self, pack: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        git = pack.get("git") if isinstance(pack.get("git"), dict) else {}
        commit = str(git.get("commit") or "").strip()
        dirty = git.get("dirty")
        status = pack.get("status")

        if not commit:
            findings.append(Finding("RELEASE_REPRODUCIBILITY_COMMIT_MISSING", "Pack git.commit is missing.", Severity.BLOCK))
        if dirty is True:
            findings.append(Finding("RELEASE_REPRODUCIBILITY_DIRTY_TRUE", "Pack declares git.dirty=true.", Severity.BLOCK))
        if git.get("source_archive_required") is not True or git.get("git_metadata_required") is not True:
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_GIT_REQUIREMENTS_INVALID",
                    "Pack must require source archive and Git metadata.",
                    Severity.BLOCK,
                )
            )

        git_state = _current_git_state(self.root)
        if status == "verified-local" and git_state.get("git_metadata_available") and git_state.get("dirty") is True:
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_CURRENT_REPO_DIRTY",
                    "Current checkout is dirty and cannot support a verified-local reproducibility declaration.",
                    Severity.BLOCK,
                    metadata=git_state,
                )
            )
        else:
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_GIT_STATE_DECLARED",
                    "Pack git commit and dirty-state declaration were evaluated.",
                    Severity.INFO,
                    metadata={"pack_commit": commit, "pack_dirty": dirty, **git_state},
                )
            )
        return findings

    def _verify_safety(self, pack: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        safety = pack.get("safety") if isinstance(pack.get("safety"), dict) else {}
        invalid_true = [name for name in REQUIRED_TRUE_SAFETY_FLAGS if safety.get(name) is not True]
        invalid_false = [name for name in REQUIRED_FALSE_SAFETY_FLAGS if safety.get(name) is not False]
        if invalid_true or invalid_false:
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_SAFETY_FLAGS_INVALID",
                    "Pack safety flags violate local-first, dry-run or secret-free requirements.",
                    Severity.BLOCK,
                    metadata={"required_true_invalid": invalid_true, "required_false_invalid": invalid_false},
                )
            )
        else:
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_SAFETY_FLAGS_PASS",
                    "Pack safety flags are local-first, dry-run and secret-free.",
                    Severity.INFO,
                )
            )
        return findings

    def _verify_validation_declarations(self, pack: dict[str, Any]) -> list[Finding]:
        validation = pack.get("validation") if isinstance(pack.get("validation"), dict) else {}
        status = pack.get("status")
        findings: list[Finding] = []
        missing = [key for key in REQUIRED_VALIDATION_KEYS if key not in validation]
        if missing:
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_VALIDATION_DECLARATIONS_MISSING",
                    "Pack is missing required validation declarations.",
                    Severity.BLOCK,
                    metadata={"missing": missing},
                )
            )
        if status == "verified-local":
            not_pass = [key for key in REQUIRED_VALIDATION_KEYS if validation.get(key) != "pass"]
            if not_pass:
                findings.append(
                    Finding(
                        "RELEASE_REPRODUCIBILITY_VERIFIED_LOCAL_GATES_NOT_PASS",
                        "verified-local packs require all required gates to be declared as pass.",
                        Severity.BLOCK,
                        metadata={"not_pass": not_pass},
                    )
                )
        findings.append(
            Finding(
                "RELEASE_REPRODUCIBILITY_VALIDATION_DECLARATIONS_CHECKED",
                "Required gate declarations were checked without executing gates.",
                Severity.INFO,
                metadata={key: validation.get(key) for key in REQUIRED_VALIDATION_KEYS},
            )
        )
        return findings

    def _verify_artifacts(self, pack: dict[str, Any], findings: list[Finding]) -> dict[str, Any]:
        artifacts = pack.get("artifacts") if isinstance(pack.get("artifacts"), dict) else {}
        checks = {
            "environment_snapshot": self._verify_environment_snapshot(artifacts.get("environment_snapshot"), findings),
            "source_archive_manifest": self._verify_source_archive_manifest(artifacts.get("source_archive_manifest"), findings),
            "optional_artifacts": self._inspect_optional_artifacts(artifacts, findings),
        }
        return checks

    def _verify_environment_snapshot(self, raw_path: Any, findings: list[Finding]) -> dict[str, Any]:
        path = _resolve_path(self.root, str(raw_path or ""))
        display = _display_path(self.root, path)
        if not raw_path or not path.exists():
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_ENVIRONMENT_SNAPSHOT_MISSING",
                    "Pack environment_snapshot artifact is missing.",
                    Severity.BLOCK,
                    path=display,
                )
            )
            return {"path": display, "exists": False, "schema_valid": False, "secrets_included": None}
        schema_result = SchemaValidator(self.root).validate(schema="ReleaseEnvironmentSnapshot", instance=path)
        findings.extend(_prefixed_findings(schema_result.findings, prefix="ENVIRONMENT_SNAPSHOT_SCHEMA"))
        snapshot = _read_json_object(path)
        safety = snapshot.get("safety") if isinstance(snapshot.get("safety"), dict) else {}
        secrets = safety.get("secrets_included")
        if secrets is not False:
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_ENVIRONMENT_SECRETS_INCLUDED",
                    "Environment snapshot must declare secrets_included=false.",
                    Severity.BLOCK,
                    path=display,
                )
            )
        return {"path": display, "exists": True, "schema_valid": schema_result.ok, "secrets_included": secrets}

    def _verify_source_archive_manifest(self, raw_path: Any, findings: list[Finding]) -> dict[str, Any]:
        path = _resolve_path(self.root, str(raw_path or ""))
        display = _display_path(self.root, path)
        result = {
            "path": display,
            "exists": path.exists(),
            "schema_valid": False,
            "forbidden_entries_total": None,
            "checksum_records_total": 0,
            "checksum_mismatches_total": 0,
            "checksum_missing_files_total": 0,
        }
        if not raw_path or not path.exists():
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_SOURCE_ARCHIVE_MANIFEST_MISSING",
                    "Pack source_archive_manifest artifact is missing.",
                    Severity.BLOCK,
                    path=display,
                )
            )
            return result

        schema_result = SchemaValidator(self.root).validate(schema="ReleaseSourceArchiveManifest", instance=path)
        result["schema_valid"] = schema_result.ok
        findings.extend(_prefixed_findings(schema_result.findings, prefix="SOURCE_ARCHIVE_SCHEMA"))
        manifest = _read_json_object(path)
        exclusions = manifest.get("exclusions") if isinstance(manifest.get("exclusions"), dict) else {}
        forbidden_total = int(exclusions.get("forbidden_entries_total") or 0)
        result["forbidden_entries_total"] = forbidden_total
        if forbidden_total:
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_FORBIDDEN_ARCHIVE_ENTRIES",
                    "Source archive manifest contains forbidden entries.",
                    Severity.BLOCK,
                    path=display,
                    metadata={"forbidden_entries_total": forbidden_total},
                )
            )

        critical = manifest.get("critical_artifacts") if isinstance(manifest.get("critical_artifacts"), dict) else {}
        checksum_records = critical.get("sha256") if isinstance(critical.get("sha256"), list) else []
        result["checksum_records_total"] = len(checksum_records)
        mismatches = 0
        missing_files = 0
        for record in checksum_records:
            if not isinstance(record, dict) or not record.get("exists"):
                continue
            relative = str(record.get("path") or "")
            expected = str(record.get("sha256") or "")
            artifact_path = _resolve_path(self.root, relative)
            if not artifact_path.exists():
                missing_files += 1
                findings.append(
                    Finding(
                        "RELEASE_REPRODUCIBILITY_CHECKSUM_FILE_MISSING",
                        "A critical artifact declared as present is missing locally.",
                        Severity.BLOCK,
                        path=relative,
                    )
                )
                continue
            actual = _sha256_file(artifact_path)
            if expected and actual != expected:
                mismatches += 1
                findings.append(
                    Finding(
                        "RELEASE_REPRODUCIBILITY_CHECKSUM_MISMATCH",
                        "A critical artifact checksum does not match the local file.",
                        Severity.BLOCK,
                        path=relative,
                        metadata={"expected": expected, "actual": actual},
                    )
                )
        result["checksum_mismatches_total"] = mismatches
        result["checksum_missing_files_total"] = missing_files
        if not mismatches and not missing_files:
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_CHECKSUMS_PASS",
                    "Source archive critical artifact checksums match local files.",
                    Severity.INFO,
                    metadata={"checksum_records_total": len(checksum_records)},
                )
            )
        return result

    def _inspect_optional_artifacts(self, artifacts: dict[str, Any], findings: list[Finding]) -> list[dict[str, Any]]:
        optional = []
        for key in ("changelog", "manifest", "sbom", "checksums"):
            raw = artifacts.get(key)
            path = _resolve_path(self.root, str(raw or ""))
            exists = bool(raw) and path.exists()
            optional.append({"artifact": key, "path": _display_path(self.root, path), "exists": exists})
            if not exists:
                findings.append(
                    Finding(
                        "RELEASE_REPRODUCIBILITY_OPTIONAL_ARTIFACT_MISSING",
                        "Optional release artifact is not present yet; POST-H-017-D keeps this advisory until pack generation/gate integration.",
                        Severity.WARNING,
                        path=str(raw or key),
                        metadata={"artifact": key},
                    )
                )
        return optional

    def _verification_payload(
        self,
        *,
        pack_path: str,
        pack: dict[str, Any],
        artifact_checks: dict[str, Any],
        findings_total: int,
        blocking_findings_total: int,
        pack_schema_valid: bool,
    ) -> dict[str, Any]:
        summary = {
            "created_by": "POST-H-017-D",
            "status": "implemented-initial",
            "preliminary": True,
            "pack_path": pack_path,
            "pack_id": pack.get("pack_id"),
            "pack_status": pack.get("status"),
            "schema_id": "SCHEMA-DEVPL-RELEASE-REPRODUCIBILITY-VERIFICATION-V1",
            "release_reproducibility_verified": blocking_findings_total == 0,
            "schema_valid": pack_schema_valid,
            "dirty_declared": (pack.get("git") or {}).get("dirty") if isinstance(pack.get("git"), dict) else None,
            "secrets_included": (pack.get("safety") or {}).get("secrets_included") if isinstance(pack.get("safety"), dict) else None,
            "checksum_mismatches_total": artifact_checks["source_archive_manifest"]["checksum_mismatches_total"],
            "checksum_missing_files_total": artifact_checks["source_archive_manifest"]["checksum_missing_files_total"],
            "forbidden_entries_total": artifact_checks["source_archive_manifest"]["forbidden_entries_total"],
            "findings_total": findings_total,
            "blocking_findings_total": blocking_findings_total,
            "local_first": True,
            "dry_run": True,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "remote_execution_used": False,
            "connector_write_used": False,
            "plugin_execution_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "reports_written": False,
            "output_json": None,
            "output_markdown": None,
        }
        return {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-RELEASE-REPRODUCIBILITY-VERIFICATION-V1",
            "verification_id": "devpilot-release-reproducibility-verification",
            "created_by": "POST-H-017-D",
            "status": "implemented-initial",
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "summary": summary,
            "pack": {
                "path": pack_path,
                "pack_id": pack.get("pack_id"),
                "status": pack.get("status"),
                "git": pack.get("git"),
                "validation": pack.get("validation"),
                "safety": pack.get("safety"),
            },
            "artifact_checks": artifact_checks,
            "safety": {
                "local_first": True,
                "dry_run": True,
                "read_only": True,
                "network_used": False,
                "external_api_used": False,
                "remote_execution_used": False,
                "connector_write_used": False,
                "plugin_execution_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "secrets_included": False,
            },
            "preliminary": True,
        }

    def _write_reports(self, payload: dict[str, Any]) -> None:
        json_path = _resolve_path(self.root, self.options.output_json)
        markdown_path = _resolve_path(self.root, self.options.output_markdown)
        _ensure_inside_root(self.root, json_path)
        _ensure_inside_root(self.root, markdown_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(_render_markdown(payload), encoding="utf-8")

    def _result(
        self,
        *,
        ok: bool,
        findings: list[Finding],
        pack_path: str,
        verification: dict[str, Any] | None,
        reports: dict[str, str],
    ) -> CommandResult:
        if verification is None:
            summary = {
                "created_by": "POST-H-017-D",
                "status": "implemented-initial",
                "preliminary": True,
                "pack_path": pack_path,
                "release_reproducibility_verified": False,
                "findings_total": len(findings),
                "blocking_findings_total": len(_blocking_findings(findings)),
                "network_used": False,
                "external_api_used": False,
                "reports_written": False,
            }
        else:
            summary = verification["summary"]
        data: dict[str, Any] = {
            "summary": summary,
            "verification": verification,
            "notes": [
                "POST-H-017-D verifies a local reproducibility pack; it does not generate the final pack.",
                "Quality-gate release-reproducibility integration remains POST-H-017-E scope.",
            ],
        }
        if reports:
            data["reports"] = reports
        return CommandResult(
            command="release reproducibility-verify",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Release reproducibility verification passed." if ok else "Release reproducibility verification blocked.",
            data=data,
            findings=findings,
        )


def _prefixed_findings(findings: list[Finding], *, prefix: str) -> list[Finding]:
    return [
        Finding(
            id=f"{prefix}_{finding.id}",
            message=finding.message,
            severity=finding.severity,
            path=finding.path,
            metadata=finding.metadata,
        )
        for finding in findings
    ]


def _blocking_findings(findings: list[Finding]) -> list[Finding]:
    return [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]


def _resolve_path(root: Path, value: Path | str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _display_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _ensure_inside_root(root: Path, path: Path) -> None:
    path.resolve().relative_to(root.resolve())


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _current_git_state(root: Path) -> dict[str, Any]:
    if not (root / ".git").exists():
        return {"git_metadata_available": False, "commit": None, "dirty": None}
    commit_result = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=root, capture_output=True, text=True, check=False)
    status_result = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=False)
    return {
        "git_metadata_available": commit_result.returncode == 0,
        "commit": commit_result.stdout.strip() if commit_result.returncode == 0 else None,
        "dirty": bool(status_result.stdout.strip()) if status_result.returncode == 0 else None,
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Release reproducibility verification",
        "",
        "Estado: `implemented-initial`.",
        "",
        "## Resumen",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Alcance",
            "",
            "- Verifica schema del pack, policy local, dirty state declarado, safety flags, snapshot redactado y checksums críticos del source archive manifest.",
            "- No genera el pack final ni integra el quality gate; eso queda para POST-H-017-E.",
            "",
        ]
    )
    return "\n".join(lines)
