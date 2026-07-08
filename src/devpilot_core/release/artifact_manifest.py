from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

DEFAULT_LOCAL_ARTIFACT_MANIFEST_POLICY_PATH = Path(".devpilot/release/local_artifact_manifest_policy.json")
DEFAULT_RELEASE_ARTIFACT_MANIFEST_JSON = Path("outputs/release/release_artifact_manifest.json")
DEFAULT_RELEASE_ARTIFACT_MANIFEST_MARKDOWN = Path("outputs/release/release_artifact_manifest.md")
DEFAULT_RELEASE_ARTIFACT_CHECKSUMS = Path("outputs/release/checksums.sha256")
_SCHEMA_ID = "SCHEMA-DEVPL-RELEASE-ARTIFACT-MANIFEST-V1"
_SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")


@dataclass(frozen=True)
class ReleaseArtifactManifestOptions:
    """Options for POST-H-027-C local artifact manifest/checksum evidence.

    The builder is local-first and computes SHA-256 over already-created local
    artifacts. It does not build, publish, deploy, sign, download or mutate
    source files. Runtime evidence is written only when ``write_report`` is
    explicit.
    """

    version: str = "0.1.0"
    policy_path: str = str(DEFAULT_LOCAL_ARTIFACT_MANIFEST_POLICY_PATH)
    output_json: str = str(DEFAULT_RELEASE_ARTIFACT_MANIFEST_JSON)
    output_markdown: str = str(DEFAULT_RELEASE_ARTIFACT_MANIFEST_MARKDOWN)
    output_checksums: str = str(DEFAULT_RELEASE_ARTIFACT_CHECKSUMS)
    verify_checksums: bool = False
    write_report: bool = False


class ReleaseArtifactManifestBuilder:
    """Build and verify POST-H-027-C release artifact manifest evidence."""

    def __init__(self, root: Path, *, options: ReleaseArtifactManifestOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ReleaseArtifactManifestOptions()

    def build(self) -> CommandResult:
        findings: list[Finding] = []
        if not _SEMVER_RE.match(self.options.version):
            findings.append(Finding("RELEASE_ARTIFACT_MANIFEST_VERSION_INVALID", "Release version must be SemVer.", Severity.ERROR, metadata={"version": self.options.version}))
            return self._result({}, findings)

        policy, policy_error = self._load_policy()
        if policy_error is not None:
            findings.append(policy_error)
            return self._result(self._empty_manifest(policy={}), findings)

        manifest = self._build_manifest(policy)
        checksum_findings = self._verify_manifest_checksums(manifest) if self.options.verify_checksums else []
        findings.extend(checksum_findings)
        required_missing = [item for item in manifest["artifacts"] if item["required"] and not item["exists"]]
        checksum_mismatches = manifest["checksums"].get("mismatches", [])

        if required_missing:
            findings.append(
                Finding(
                    "RELEASE_ARTIFACT_MANIFEST_REQUIRED_MISSING",
                    "Required local release artifacts are missing from the manifest.",
                    Severity.BLOCK,
                    metadata={"missing": [item["path"] for item in required_missing]},
                )
            )
        if checksum_mismatches:
            findings.append(
                Finding(
                    "RELEASE_ARTIFACT_MANIFEST_CHECKSUM_MISMATCH",
                    "One or more artifact checksums do not match the current local files.",
                    Severity.BLOCK,
                    metadata={"mismatches_total": len(checksum_mismatches), "sample": checksum_mismatches[:10]},
                )
            )

        blocking = [item for item in findings if item.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        manifest["summary"].update(
            {
                "decision": "PASS" if not blocking else "BLOCK",
                "required_missing_total": len(required_missing),
                "checksum_mismatch_total": len(checksum_mismatches),
                "checksums_verified": bool(self.options.verify_checksums and not checksum_mismatches and not required_missing),
                "reports_written": self.options.write_report,
            }
        )
        manifest["checksums"]["verified"] = bool(self.options.verify_checksums and not checksum_mismatches and not required_missing)
        manifest["safety"]["reports_written"] = self.options.write_report

        if not blocking:
            findings.append(
                Finding(
                    "RELEASE_ARTIFACT_MANIFEST_PASS",
                    "Release artifact manifest and SHA-256 checksum evidence passed.",
                    Severity.INFO,
                    metadata={"artifacts_total": manifest["summary"]["artifacts_total"], "checksums_verified": manifest["checksums"]["verified"]},
                )
            )

        reports: dict[str, str] = {}
        if self.options.write_report:
            reports = self._write_outputs(manifest)

        return CommandResult(
            command="release artifact-manifest",
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK,
            message="Release artifact manifest passed." if not blocking else "Release artifact manifest blocked.",
            data={
                "summary": manifest["summary"],
                "manifest": manifest,
                "reports": reports,
                "notes": [
                    "POST-H-027-C consolidates local distributable artifact checksums and manifest metadata.",
                    "The command does not build artifacts, publish, deploy, sign, call network or mutate source files.",
                    "Windows install smoke and upgrade/rollback dry-run remain POST-H-027-D/E scope.",
                ],
            },
            findings=findings,
        )

    def _empty_manifest(self, *, policy: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "schema_id": _SCHEMA_ID,
            "manifest_id": f"DEVPL-LOCAL-ARTIFACT-MANIFEST-{_safe_version(self.options.version)}",
            "created_by": "POST-H-027-C",
            "status": "implemented-initial",
            "generated_at_utc": _now(),
            "release_version": self.options.version,
            "scope": "local-package",
            "policy": {
                "policy_id": policy.get("policy_id"),
                "policy_path": _normalize_report_path(self.options.policy_path),
                "status": policy.get("status"),
                "required_artifacts_total": 0,
                "optional_artifacts_total": 0,
            },
            "artifacts": [],
            "checksums_file": _normalize_report_path(self.options.output_checksums),
            "checksums": {"algorithm": "sha256", "generated": False, "verified": False, "entries_total": 0, "entries_sha256": _sha256_text(""), "mismatches": []},
            "summary": self._summary_template(decision="BLOCK"),
            "safety": _safety_flags(reports_written=self.options.write_report),
            "limitations": _limitations(),
            "preliminary": True,
        }

    def _build_manifest(self, policy: dict[str, Any]) -> dict[str, Any]:
        artifacts: list[dict[str, Any]] = []
        for item in policy.get("required_artifacts", []):
            artifacts.append(self._artifact_record(item, required=True))
        for item in policy.get("optional_artifacts", []):
            artifacts.append(self._artifact_record(item, required=False))

        checksum_lines = [_checksum_line(item) for item in artifacts if item["exists"] and item["sha256"]]
        checksums_text = "".join(checksum_lines)
        required = [item for item in artifacts if item["required"]]
        required_present = [item for item in required if item["exists"]]
        optional_missing = [item for item in artifacts if not item["required"] and not item["exists"]]
        distributable = [item for item in artifacts if item.get("classification") == "distributable"]
        return {
            "schema_version": "1.0",
            "schema_id": _SCHEMA_ID,
            "manifest_id": f"DEVPL-LOCAL-ARTIFACT-MANIFEST-{_safe_version(self.options.version)}",
            "created_by": "POST-H-027-C",
            "status": "implemented-initial",
            "generated_at_utc": _now(),
            "release_version": self.options.version,
            "scope": "local-package",
            "policy": {
                "policy_id": policy.get("policy_id"),
                "policy_path": _normalize_report_path(self.options.policy_path),
                "status": policy.get("status"),
                "required_artifacts_total": len(policy.get("required_artifacts", [])),
                "optional_artifacts_total": len(policy.get("optional_artifacts", [])),
            },
            "artifacts": artifacts,
            "checksums_file": _normalize_report_path(self.options.output_checksums),
            "checksums": {
                "algorithm": "sha256",
                "generated": bool(checksum_lines),
                "verified": False,
                "entries_total": len(checksum_lines),
                "entries_sha256": _sha256_text(checksums_text),
                "mismatches": [],
            },
            "summary": {
                **self._summary_template(decision="PASS"),
                "artifacts_total": len(artifacts),
                "distributable_artifacts_total": len(distributable),
                "required_total": len(required),
                "required_present_total": len(required_present),
                "required_missing_total": len(required) - len(required_present),
                "optional_missing_total": len(optional_missing),
                "checksums_entries_total": len(checksum_lines),
                "checksums_file_written": self.options.write_report,
                "checksum_mismatch_total": 0,
                "checksums_verified": False,
            },
            "safety": _safety_flags(reports_written=self.options.write_report),
            "limitations": _limitations(),
            "preliminary": True,
        }

    def _summary_template(self, *, decision: str) -> dict[str, Any]:
        return {
            "decision": decision,
            "created_by": "POST-H-027-C",
            "preliminary": True,
            "release_version": self.options.version,
            "scope": "local-package",
            "network_used": False,
            "external_api_used": False,
            "publish_performed": False,
            "deploy_performed": False,
            "signing_performed": False,
            "source_mutations": False,
            "reports_written": self.options.write_report,
        }

    def _artifact_record(self, policy_item: dict[str, Any], *, required: bool) -> dict[str, Any]:
        relative = _render_template(str(policy_item["path"]), self.options.version)
        path = _workspace_path(self.root, relative)
        exists = False
        sha256: str | None = None
        size_bytes: int | None = None
        try:
            path.relative_to(self.root)
            exists = path.is_file()
        except ValueError:
            exists = False
        if exists:
            payload = path.read_bytes()
            sha256 = hashlib.sha256(payload).hexdigest()
            size_bytes = len(payload)
        return {
            "artifact_id": str(policy_item["artifact_id"]),
            "artifact_type": str(policy_item["artifact_type"]),
            "path": relative.replace("\\", "/"),
            "required": required,
            "classification": str(policy_item.get("classification", "distributable")),
            "exists": exists,
            "sha256": sha256,
            "size_bytes": size_bytes,
            "verification_status": "pass" if exists else "missing",
            "source": str(policy_item.get("source", "local-artifact")),
            "notes": list(policy_item.get("notes", [])),
        }

    def _verify_manifest_checksums(self, manifest: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        mismatches: list[dict[str, Any]] = []
        for item in manifest.get("artifacts", []):
            if not item.get("exists"):
                continue
            path = self.root / item["path"]
            current = hashlib.sha256(path.read_bytes()).hexdigest()
            if current != item.get("sha256"):
                item["verification_status"] = "checksum-mismatch"
                mismatches.append({"path": item["path"], "expected_sha256": item.get("sha256"), "actual_sha256": current})
            else:
                item["verification_status"] = "pass"
        manifest["checksums"]["mismatches"] = mismatches
        if not mismatches:
            findings.append(Finding("RELEASE_ARTIFACT_CHECKSUMS_VERIFIED", "All existing artifact checksums match current local files.", Severity.INFO, metadata={"artifacts_checked_total": sum(1 for item in manifest.get("artifacts", []) if item.get("exists"))}))
        return findings

    def _load_policy(self) -> tuple[dict[str, Any], Finding | None]:
        path = _workspace_path(self.root, self.options.policy_path)
        try:
            path.relative_to(self.root)
        except ValueError:
            return {}, Finding("RELEASE_ARTIFACT_MANIFEST_POLICY_OUTSIDE_WORKSPACE", "Artifact manifest policy path must stay inside workspace.", Severity.BLOCK, metadata={"policy_path": self.options.policy_path})
        if not path.is_file():
            return {}, Finding("RELEASE_ARTIFACT_MANIFEST_POLICY_MISSING", "Artifact manifest policy is missing.", Severity.BLOCK, metadata={"policy_path": self.options.policy_path})
        try:
            policy = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return {}, Finding("RELEASE_ARTIFACT_MANIFEST_POLICY_INVALID_JSON", "Artifact manifest policy is not valid JSON.", Severity.BLOCK, metadata={"error": str(exc)})
        required = policy.get("required_artifacts") or []
        if not required:
            return policy, Finding("RELEASE_ARTIFACT_MANIFEST_POLICY_EMPTY", "Artifact manifest policy must declare required artifacts.", Severity.BLOCK)
        return policy, None

    def _write_outputs(self, manifest: dict[str, Any]) -> dict[str, str]:
        json_path = _workspace_path(self.root, self.options.output_json)
        md_path = _workspace_path(self.root, self.options.output_markdown)
        checksums_path = _workspace_path(self.root, self.options.output_checksums)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        checksums_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        md_path.write_text(self.render_markdown(manifest), encoding="utf-8")
        checksums_path.write_text("".join(_checksum_line(item) for item in manifest["artifacts"] if item["exists"] and item["sha256"]), encoding="utf-8")
        return {
            "json": _normalize_report_path(self.options.output_json),
            "markdown": _normalize_report_path(self.options.output_markdown),
            "checksums": _normalize_report_path(self.options.output_checksums),
        }

    @staticmethod
    def render_markdown(manifest: dict[str, Any]) -> str:
        summary = manifest.get("summary", {})
        lines = [
            "# POST-H-027-C — Artifact manifest and checksums",
            "",
            f"Decision: **{summary.get('decision')}**",
            f"Release version: `{manifest.get('release_version')}`",
            f"Artifacts: `{summary.get('artifacts_total')}`",
            f"Required missing: `{summary.get('required_missing_total')}`",
            f"Checksum mismatches: `{summary.get('checksum_mismatch_total')}`",
            "",
            "## Artifacts",
            "",
        ]
        for item in manifest.get("artifacts", []):
            lines.append(f"- `{item.get('verification_status')}` — `{item.get('artifact_id')}`: `{item.get('path')}` sha256=`{item.get('sha256')}` required=`{item.get('required')}`")
        lines.extend(["", "## Safety", ""])
        for key, value in manifest.get("safety", {}).items():
            lines.append(f"- `{key}`: `{value}`")
        lines.extend(["", "## Limitations", ""])
        for item in manifest.get("limitations", []):
            lines.append(f"- {item}")
        return "\n".join(lines) + "\n"

    def _result(self, manifest: dict[str, Any], findings: list[Finding]) -> CommandResult:
        blocking = [item for item in findings if item.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        summary = (manifest or {}).get("summary") or self._summary_template(decision="BLOCK")
        return CommandResult(
            command="release artifact-manifest",
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK,
            message="Release artifact manifest passed." if not blocking else "Release artifact manifest blocked.",
            data={"summary": summary, "manifest": manifest, "reports": {}},
            findings=findings,
        )


def _normalize_report_path(value: str | Path) -> str:
    """Return repo-relative report paths with POSIX separators for JSON contracts.

    Windows argparse/default Path values may carry backslashes. DevPilot report
    contracts use stable slash-separated paths so logs are deterministic across
    Windows/Linux/macOS and can be asserted by tests and downstream validators.
    """

    return str(value).replace("\\", "/")


def _workspace_path(root: Path, value: str | Path) -> Path:
    """Resolve a repo-relative path accepting either Windows or POSIX separators."""

    return (root / _normalize_report_path(value)).resolve()


def _render_template(value: str, version: str) -> str:
    return value.replace("{version}", version).replace("<version>", version).replace("\\", "/")


def _checksum_line(item: dict[str, Any]) -> str:
    return f"{item['sha256']}  {item['path']}\n"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _safe_version(version: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]+", "-", version)


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safety_flags(*, reports_written: bool) -> dict[str, bool]:
    return {
        "local_first": True,
        "network_used": False,
        "external_api_used": False,
        "publish_performed": False,
        "deploy_performed": False,
        "git_tagging_performed": False,
        "signing_performed": False,
        "remote_execution_enabled": False,
        "connector_write_enabled": False,
        "plugin_execution_enabled": False,
        "source_mutations": False,
        "reports_written": reports_written,
    }


def _limitations() -> list[str]:
    return [
        "POST-H-027-C creates local manifest/checksum evidence only; it does not sign artifacts or provide SLSA attestation.",
        "Artifacts must already exist locally; building source ZIP, wheel and sdist remains an explicit package build step.",
        "Windows install smoke and upgrade/rollback dry-run remain POST-H-027-D/E scope.",
    ]
