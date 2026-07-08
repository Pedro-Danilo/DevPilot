from __future__ import annotations

import fnmatch
import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from devpilot_core.auditpack.redaction import _count_material_secret_redactions
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy.secrets import SecretGuard

DEFAULT_SOURCE_ZIP_POLICY_PATH = ".devpilot/release/source_zip_release_policy.json"
DEFAULT_SOURCE_ZIP_REPORT_JSON_PATH = "outputs/release/source_zip_release_report.json"
DEFAULT_SOURCE_ZIP_REPORT_MARKDOWN_PATH = "outputs/release/source_zip_release_report.md"
POLICY_SCHEMA_ID = "SCHEMA-DEVPL-SOURCE-ZIP-RELEASE-POLICY-V1"
REPORT_SCHEMA_ID = "SCHEMA-DEVPL-SOURCE-ZIP-RELEASE-REPORT-V1"

_TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".csv",
    ".ini",
    ".cfg",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".mjs",
    ".css",
    ".html",
    ".sha256",
    ".example",
}


@dataclass(frozen=True)
class SourceZipPolicyOptions:
    """Options for POST-H-027-A source ZIP release policy validation.

    The validator is local-first and read-only by default. It can inspect the
    source tree and, when ``artifact`` is provided, the entries of a candidate
    ZIP without extracting the archive. Reports are written only with
    ``write_report=True``.
    """

    policy_path: str = DEFAULT_SOURCE_ZIP_POLICY_PATH
    artifact: str | None = None
    output_json: str = DEFAULT_SOURCE_ZIP_REPORT_JSON_PATH
    output_markdown: str = DEFAULT_SOURCE_ZIP_REPORT_MARKDOWN_PATH
    write_report: bool = False


class SourceZipReleasePolicyValidator:
    """Validate the governed clean source ZIP policy and optional ZIP artifact.

    POST-H-027-A elevates the package-builder exclusion rules into a versioned
    policy so source ZIP release handoffs are auditable instead of relying on
    informal ignore conventions. The validator never builds, publishes or
    extracts artifacts; it only reads source metadata and optional ZIP member
    names/content for policy checks.
    """

    def __init__(self, root: Path, options: SourceZipPolicyOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or SourceZipPolicyOptions()
        self.policy_path = self._resolve(self.options.policy_path)
        self.secret_guard = SecretGuard()

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        policy = self._load_policy(findings)
        checks: list[dict[str, Any]] = []
        included: list[str] = []
        excluded: list[str] = []
        forbidden_present: list[dict[str, Any]] = []
        required_missing: list[str] = []
        secret_findings: list[dict[str, Any]] = []
        text_files_scanned_total = 0

        if policy is None:
            report = self._build_report(
                decision="BLOCK",
                policy={},
                checks=[self._check("policy-load", "policy", "block", "Policy file is missing or invalid.")],
                included=included,
                excluded=excluded,
                required_missing=[],
                forbidden_present=[],
                secret_findings=[],
                text_files_scanned_total=0,
                artifact_result=None,
                reports_written=False,
            )
            return CommandResult(
                command="package source-zip-policy",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Source ZIP release policy blocked.",
                data={"summary": report["summary"], "report": report, "reports": {}},
                findings=findings,
            )

        policy_check_status = "pass" if _policy_semantics_valid(policy) else "block"
        checks.append(
            self._check(
                "policy-schema-backed-versioned",
                "policy",
                policy_check_status,
                "Source ZIP policy declares schema id, local release scope, dry-run default and no publish/deploy flags.",
                {"policy_id": policy.get("policy_id"), "status": policy.get("status")},
            )
        )
        if policy_check_status == "block":
            findings.append(Finding("SOURCE_ZIP_POLICY_SEMANTICS_BLOCK", "Source ZIP release policy lacks required semantic safety flags.", Severity.BLOCK, path=_rel(self.root, self.policy_path)))

        required_includes = list(policy.get("required_includes") or [])
        for rel in required_includes:
            if not (self.root / rel).exists():
                required_missing.append(rel)
        checks.append(
            self._check(
                "required-source-includes-present",
                "source-tree",
                "pass" if not required_missing else "block",
                "Required source files/directories are present before packaging.",
                {"required_total": len(required_includes), "missing": required_missing},
            )
        )
        if required_missing:
            findings.append(Finding("SOURCE_ZIP_REQUIRED_INCLUDES_MISSING", "Source ZIP policy required includes are missing from the source tree.", Severity.BLOCK, metadata={"missing": required_missing}))

        for path in sorted(self.root.rglob("*")):
            if not path.is_file():
                continue
            rel = _to_posix(path.relative_to(self.root))
            reason = policy_forbidden_reason(rel, policy)
            if reason:
                excluded.append(rel)
            else:
                included.append(rel)
                path_secret_reason = _secret_path_reason(rel, policy)
                if path_secret_reason:
                    forbidden_present.append({"path": rel, "reason": path_secret_reason})
                if _should_secret_scan(rel, path, policy):
                    text_files_scanned_total += 1
                    redactions = _scan_secret_text(path, rel, self.secret_guard)
                    if redactions > 0:
                        secret_findings.append({"path": rel, "redactions": redactions})

        source_forbidden_count = len(forbidden_present) + len(secret_findings)
        checks.append(
            self._check(
                "source-tree-forbidden-paths-excluded",
                "source-tree",
                "pass" if not forbidden_present else "block",
                "Forbidden runtime/build/secret paths are excluded from the source package candidate set.",
                {"forbidden_present_total": len(forbidden_present), "sample": forbidden_present[:10]},
            )
        )
        checks.append(
            self._check(
                "secretguard-source-content-pass",
                "security",
                "pass" if not secret_findings else "block",
                "SecretGuard-compatible textual scan found no material secrets in included text files.",
                {"text_files_scanned_total": text_files_scanned_total, "secret_findings_total": len(secret_findings), "sample": secret_findings[:10]},
            )
        )
        if forbidden_present:
            findings.append(Finding("SOURCE_ZIP_FORBIDDEN_SOURCE_PATHS_BLOCK", "Forbidden source paths would be included by policy.", Severity.BLOCK, metadata={"paths": forbidden_present[:25], "total": len(forbidden_present)}))
        if secret_findings:
            findings.append(Finding("SOURCE_ZIP_SECRET_CONTENT_BLOCK", "Secret-like content was detected in included text files.", Severity.BLOCK, metadata={"paths": secret_findings[:25], "total": len(secret_findings)}))

        artifact_result = self._inspect_artifact(policy, findings)
        if artifact_result is not None:
            checks.append(
                self._check(
                    "candidate-zip-artifact-hygiene",
                    "artifact",
                    "pass" if artifact_result["forbidden_present_total"] == 0 and artifact_result["required_missing_total"] == 0 and artifact_result["secret_findings_total"] == 0 else "block",
                    "Candidate source ZIP entries comply with forbidden, required and secret-scan policy.",
                    {
                        "artifact": artifact_result["artifact"],
                        "entries_total": artifact_result["entries_total"],
                        "forbidden_present_total": artifact_result["forbidden_present_total"],
                        "required_missing_total": artifact_result["required_missing_total"],
                        "secret_findings_total": artifact_result["secret_findings_total"],
                    },
                )
            )

        critical_failed = sum(1 for item in checks if item["critical"] and item["status"] != "pass")
        decision = "PASS" if critical_failed == 0 and source_forbidden_count == 0 else "BLOCK"
        reports_written = False
        report = self._build_report(
            decision=decision,
            policy=policy,
            checks=checks,
            included=included,
            excluded=excluded,
            required_missing=required_missing,
            forbidden_present=forbidden_present,
            secret_findings=secret_findings,
            text_files_scanned_total=text_files_scanned_total,
            artifact_result=artifact_result,
            reports_written=False,
        )
        if self.options.write_report:
            reports_written = True
            report["safety"]["reports_written"] = True
            report["safety"]["mutations_performed"] = True
            report["safety"]["read_only"] = False
            report["summary"]["reports_written"] = True
            report["summary"]["mutations_performed"] = True
            self._write_reports(report)

        if decision == "PASS":
            findings.append(Finding("SOURCE_ZIP_RELEASE_POLICY_PASS", "Source ZIP release policy passed for source tree and optional artifact without network or source mutations.", Severity.INFO, metadata={"checks_total": len(checks), "artifact_checked": artifact_result is not None}))
        else:
            findings.append(Finding("SOURCE_ZIP_RELEASE_POLICY_BLOCK", "Source ZIP release policy blocked due to missing required files, forbidden entries or secret findings.", Severity.BLOCK, metadata={"checks_total": len(checks), "critical_failed_total": critical_failed}))

        return CommandResult(
            command="package source-zip-policy",
            ok=decision == "PASS",
            exit_code=ExitCode.PASS if decision == "PASS" else ExitCode.BLOCK,
            message="Source ZIP release policy passed." if decision == "PASS" else "Source ZIP release policy blocked.",
            data={
                "summary": report["summary"],
                "report": report,
                "policy": policy,
                "reports": {"json": self.options.output_json, "markdown": self.options.output_markdown} if reports_written else {},
            },
            findings=findings,
        )

    def _load_policy(self, findings: list[Finding]) -> dict[str, Any] | None:
        if not self.policy_path.is_file():
            findings.append(Finding("SOURCE_ZIP_POLICY_MISSING", "Source ZIP release policy file is missing.", Severity.BLOCK, path=_rel(self.root, self.policy_path)))
            return None
        try:
            payload = json.loads(self.policy_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding("SOURCE_ZIP_POLICY_JSON_INVALID", "Source ZIP release policy JSON is invalid.", Severity.BLOCK, path=_rel(self.root, self.policy_path), metadata={"error": str(exc)}))
            return None
        return payload

    def _inspect_artifact(self, policy: dict[str, Any], findings: list[Finding]) -> dict[str, Any] | None:
        if not self.options.artifact:
            return None
        artifact = self._resolve(self.options.artifact)
        if not artifact.is_file():
            findings.append(Finding("SOURCE_ZIP_ARTIFACT_MISSING", "Candidate source ZIP artifact could not be found.", Severity.BLOCK, path=str(self.options.artifact)))
            return {
                "artifact": str(self.options.artifact),
                "artifact_checked": True,
                "entries_total": 0,
                "required_missing_total": len(policy.get("required_includes") or []),
                "required_missing": list(policy.get("required_includes") or []),
                "forbidden_present_total": 0,
                "forbidden_present": [],
                "secret_findings_total": 0,
                "secret_findings": [],
                "text_files_scanned_total": 0,
                "load_error": "artifact-missing",
            }
        required = set(policy.get("required_includes") or [])
        forbidden: list[dict[str, Any]] = []
        secret_findings: list[dict[str, Any]] = []
        text_scanned = 0
        try:
            with zipfile.ZipFile(artifact) as archive:
                names = [name for name in archive.namelist() if not name.endswith("/")]
                name_set = set(names)
                for name in names:
                    normalized = _normalize_zip_name(name)
                    reason = policy_forbidden_reason(normalized, policy) or _secret_path_reason(normalized, policy)
                    if reason:
                        forbidden.append({"path": name, "reason": reason})
                        continue
                    if _should_scan_zip_entry(normalized, policy):
                        info = archive.getinfo(name)
                        max_bytes = int((policy.get("secret_scan") or {}).get("max_file_size_bytes", 262144))
                        if info.file_size <= max_bytes:
                            data = archive.read(name)
                            if b"\x00" not in data[:1024]:
                                text_scanned += 1
                                redactions = _count_material_secret_redactions(data.decode("utf-8", errors="replace"), secret_guard=self.secret_guard)
                                if redactions > 0:
                                    secret_findings.append({"path": name, "redactions": redactions})
                required_missing = sorted(item for item in required if item not in name_set)
        except (zipfile.BadZipFile, OSError) as exc:
            findings.append(Finding("SOURCE_ZIP_ARTIFACT_LOAD_BLOCK", "Candidate source ZIP artifact could not be inspected.", Severity.BLOCK, path=str(self.options.artifact), metadata={"error": str(exc)}))
            return {
                "artifact": str(self.options.artifact),
                "artifact_checked": True,
                "entries_total": 0,
                "required_missing_total": len(required),
                "required_missing": sorted(required),
                "forbidden_present_total": 0,
                "forbidden_present": [],
                "secret_findings_total": 0,
                "secret_findings": [],
                "text_files_scanned_total": 0,
                "load_error": str(exc),
            }
        if forbidden:
            findings.append(Finding("SOURCE_ZIP_ARTIFACT_FORBIDDEN_ENTRIES_BLOCK", "Candidate source ZIP contains forbidden runtime/build/secret entries.", Severity.BLOCK, path=_rel(self.root, artifact), metadata={"entries": forbidden[:25], "total": len(forbidden)}))
        if required_missing:
            findings.append(Finding("SOURCE_ZIP_ARTIFACT_REQUIRED_ENTRIES_MISSING", "Candidate source ZIP misses required entries.", Severity.BLOCK, path=_rel(self.root, artifact), metadata={"missing": required_missing}))
        if secret_findings:
            findings.append(Finding("SOURCE_ZIP_ARTIFACT_SECRET_CONTENT_BLOCK", "Candidate source ZIP contains secret-like content in allowed text entries.", Severity.BLOCK, path=_rel(self.root, artifact), metadata={"entries": secret_findings[:25], "total": len(secret_findings)}))
        return {
            "artifact": _rel(self.root, artifact),
            "artifact_checked": True,
            "entries_total": len(names),
            "required_missing_total": len(required_missing),
            "required_missing": required_missing,
            "forbidden_present_total": len(forbidden),
            "forbidden_present": forbidden,
            "secret_findings_total": len(secret_findings),
            "secret_findings": secret_findings,
            "text_files_scanned_total": text_scanned,
            "load_error": None,
        }

    def _build_report(
        self,
        *,
        decision: str,
        policy: dict[str, Any],
        checks: list[dict[str, Any]],
        included: list[str],
        excluded: list[str],
        required_missing: list[str],
        forbidden_present: list[dict[str, Any]],
        secret_findings: list[dict[str, Any]],
        text_files_scanned_total: int,
        artifact_result: dict[str, Any] | None,
        reports_written: bool,
    ) -> dict[str, Any]:
        checks_total = len(checks)
        checks_passed = sum(1 for item in checks if item["status"] == "pass")
        checks_failed = checks_total - checks_passed
        critical_total = sum(1 for item in checks if item["critical"])
        critical_failed = sum(1 for item in checks if item["critical"] and item["status"] != "pass")
        artifact_checked = artifact_result is not None
        artifact_summary = artifact_result or {
            "artifact": None,
            "artifact_checked": False,
            "entries_total": 0,
            "required_missing_total": 0,
            "required_missing": [],
            "forbidden_present_total": 0,
            "forbidden_present": [],
            "secret_findings_total": 0,
            "secret_findings": [],
            "text_files_scanned_total": 0,
            "load_error": None,
        }
        summary = {
            "decision": decision,
            "created_by": "POST-H-027-A",
            "preliminary": True,
            "policy_valid": _policy_semantics_valid(policy),
            "artifact_checked": artifact_checked,
            "required_missing_total": len(required_missing) + int(artifact_summary.get("required_missing_total") or 0),
            "forbidden_present_total": len(forbidden_present) + int(artifact_summary.get("forbidden_present_total") or 0),
            "secret_findings_total": len(secret_findings) + int(artifact_summary.get("secret_findings_total") or 0),
            "clean_source_zip_policy_passed": decision == "PASS",
            "no_runtime_artifacts_in_packages": decision == "PASS",
            "no_secrets_in_packages": decision == "PASS",
            "package_build_dry_run_default": bool((policy.get("package_build_requirements") or {}).get("dry_run_default") is True),
            "execute_required_to_write": bool((policy.get("package_build_requirements") or {}).get("execute_required_to_write") is True),
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": reports_written,
            "source_mutations": False,
            "reports_written": reports_written,
        }
        return {
            "schema_version": "1.0",
            "schema_id": REPORT_SCHEMA_ID,
            "report_id": "source-zip-release-policy-post_h_027_a",
            "created_by": "POST-H-027-A",
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "scope": "local-source-zip-release",
            "decision": decision,
            "implemented_status": "implemented-initial",
            "execution_mode": "source-tree-and-optional-artifact-policy-validation",
            "policy_path": _rel(self.root, self.policy_path),
            "policy_id": policy.get("policy_id"),
            "artifact": artifact_summary.get("artifact"),
            "artifact_checked": artifact_checked,
            "checks_total": checks_total,
            "checks_passed_total": checks_passed,
            "checks_failed_total": checks_failed,
            "critical_checks_total": critical_total,
            "critical_checks_failed_total": critical_failed,
            "included_files_total": len(included),
            "excluded_files_total": len(excluded),
            "required_includes_total": len(policy.get("required_includes") or []),
            "required_missing_total": len(required_missing),
            "required_missing": required_missing,
            "forbidden_present_total": len(forbidden_present),
            "forbidden_present": forbidden_present,
            "secret_findings_total": len(secret_findings),
            "secret_findings": secret_findings,
            "text_files_scanned_total": text_files_scanned_total,
            "artifact_result": artifact_summary,
            "checks": checks,
            "sample_included_files": included[:50],
            "sample_excluded_files": excluded[:50],
            "summary": summary,
            "safety": {
                "local_first": True,
                "read_only": not reports_written,
                "dry_run": True,
                "artifact_extracted": False,
                "subprocess_executed": False,
                "pip_executed": False,
                "npm_executed": False,
                "socket_opened": False,
                "network_used": False,
                "external_api_used": False,
                "publish_performed": False,
                "deploy_performed": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "mutations_performed": reports_written,
                "source_mutations": False,
                "reports_written": reports_written,
                "raw_secrets_exported": False,
            },
            "limitations": [
                "POST-H-027-A validates clean source ZIP policy and optional ZIP artifacts; it does not publish, sign, install wheel/sdist or create desktop installers.",
                "Wheel/sdist installation, artifact manifest/checksums, Windows smoke and upgrade/rollback remain later POST-H-027 micro-sprints.",
                "Secret scanning is deterministic and local; it is not a replacement for a dedicated industrial secret-scanning service.",
            ],
        }

    def _check(self, check_id: str, category: str, status: str, reason: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        return {"check_id": check_id, "category": category, "status": status, "critical": True, "reason": reason, "metadata": metadata or {}}

    def _write_reports(self, report: dict[str, Any]) -> None:
        json_path = self._resolve(self.options.output_json)
        md_path = self._resolve(self.options.output_markdown)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        md_path.write_text(_markdown_report(report), encoding="utf-8")

    def _resolve(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.root / path


def load_source_zip_release_policy(root: Path, policy_path: str = DEFAULT_SOURCE_ZIP_POLICY_PATH) -> dict[str, Any] | None:
    path = Path(policy_path)
    if not path.is_absolute():
        path = Path(root) / path
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def policy_forbidden_reason(rel: str, policy: dict[str, Any] | None) -> str | None:
    normalized = rel.replace("\\", "/").lstrip("/")
    if policy is None:
        return _fallback_forbidden_reason(normalized)
    forbidden = policy.get("forbidden_entries") or {}
    for exact in forbidden.get("exact") or []:
        if normalized == exact:
            return f"exact:{exact}"
    for prefix in forbidden.get("prefixes") or []:
        prefix = str(prefix).rstrip("/") + "/"
        if normalized.startswith(prefix) or f"/{prefix}" in normalized:
            return f"prefix:{prefix}"
    for marker in forbidden.get("path_markers") or []:
        marker = str(marker).strip("/")
        if marker and marker in PurePosixPath(normalized).parts:
            return f"path-marker:{marker}"
    for suffix in forbidden.get("suffixes") or []:
        if normalized.endswith(str(suffix)):
            return f"suffix:{suffix}"
    for pattern in forbidden.get("glob_patterns") or []:
        if fnmatch.fnmatch(normalized, str(pattern)):
            return f"glob:{pattern}"
    return None


def _fallback_forbidden_reason(rel: str) -> str | None:
    if rel in {".devpilot/devpilot.db", ".devpilot/providers.yaml"}:
        return f"exact:{rel}"
    if rel.startswith((".devpilot/backups/", ".devpilot/agent_sessions/", ".devpilot/rag/")):
        return "runtime-state"
    if rel.endswith((".pyc", ".pyo")):
        return "python-bytecode"
    parts = PurePosixPath(rel).parts
    for marker in (".git", ".venv", "node_modules", "outputs", "dist", "__pycache__", ".pytest_cache"):
        if marker in parts:
            return f"path-marker:{marker}"
    return _secret_path_reason(rel, None)


def _secret_path_reason(rel: str, policy: dict[str, Any] | None) -> str | None:
    normalized = rel.lower()
    filename = PurePosixPath(rel).name.lower()
    parts = {part.lower() for part in PurePosixPath(rel).parts}
    secret_paths = [str(item).lower() for item in ((policy or {}).get("secret_path_markers") or ["secrets", ".secrets", "private_key", "id_rsa"])]
    if filename == ".env" or (filename.startswith(".env.") and not filename.endswith(".example")):
        return "env-secret"
    if filename.endswith((".pem", ".key", ".p12", ".pfx")):
        return "secret-key-file"
    for marker in secret_paths:
        if marker in {"secrets", ".secrets", "credentials"}:
            if marker in parts:
                return "secret-path-marker"
        elif marker and marker in normalized:
            return "secret-path-marker"
    return None


def _should_secret_scan(rel: str, path: Path, policy: dict[str, Any]) -> bool:
    scan = policy.get("secret_scan") or {}
    if scan.get("enabled") is False:
        return False
    if rel in set(scan.get("excluded_paths") or []):
        return False
    if any(rel.startswith(str(prefix)) for prefix in (scan.get("excluded_prefixes") or [])):
        return False
    max_bytes = int(scan.get("max_file_size_bytes", 262144))
    try:
        if path.stat().st_size > max_bytes:
            return False
    except OSError:
        return False
    return _text_like(rel, path.read_bytes()[:1024])


def _should_scan_zip_entry(rel: str, policy: dict[str, Any]) -> bool:
    scan = policy.get("secret_scan") or {}
    if scan.get("enabled") is False:
        return False
    if rel in set(scan.get("excluded_paths") or []):
        return False
    if any(rel.startswith(str(prefix)) for prefix in (scan.get("excluded_prefixes") or [])):
        return False
    suffix = PurePosixPath(rel).suffix.lower()
    name = PurePosixPath(rel).name.lower()
    suffixes = set(scan.get("text_suffixes") or sorted(_TEXT_SUFFIXES))
    return suffix in suffixes or name.endswith((".yaml.example", ".yml.example", ".env.example"))


def _scan_secret_text(path: Path, rel: str, secret_guard: SecretGuard) -> int:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    return _count_material_secret_redactions(text, secret_guard=secret_guard)


def _text_like(rel: str, sample: bytes) -> bool:
    suffix = PurePosixPath(rel).suffix.lower()
    name = PurePosixPath(rel).name.lower()
    return suffix in _TEXT_SUFFIXES or name.endswith((".yaml.example", ".yml.example", ".env.example")) or b"\x00" not in sample


def _policy_semantics_valid(policy: dict[str, Any]) -> bool:
    return (
        policy.get("schema_id") == POLICY_SCHEMA_ID
        and policy.get("created_by") == "POST-H-027-A"
        and policy.get("scope") == "local-source-zip-release"
        and isinstance(policy.get("required_includes"), list)
        and isinstance((policy.get("forbidden_entries") or {}).get("prefixes"), list)
        and (policy.get("package_build_requirements") or {}).get("dry_run_default") is True
        and (policy.get("package_build_requirements") or {}).get("execute_required_to_write") is True
        and (policy.get("safety") or {}).get("network_allowed") is False
        and (policy.get("safety") or {}).get("external_api_allowed") is False
        and (policy.get("safety") or {}).get("publish_allowed") is False
        and (policy.get("safety") or {}).get("deploy_allowed") is False
    )


def _normalize_zip_name(name: str) -> str:
    normalized = name.replace("\\", "/").lstrip("/")
    parts = normalized.split("/")
    # Source archives created by tar-like tools may include a top-level folder;
    # DevPilot source ZIPs do not, but this keeps validation operator-friendly.
    if parts and parts[0].startswith("devpilot-local-") and len(parts) > 1:
        return "/".join(parts[1:])
    return normalized


def _markdown_report(report: dict[str, Any]) -> str:
    summary = report.get("summary") or {}
    lines = [
        "# POST-H-027-A — Source ZIP release policy report",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Policy: `{report.get('policy_path')}`",
        f"- Artifact checked: `{report.get('artifact_checked')}`",
        f"- Required missing: `{summary.get('required_missing_total')}`",
        f"- Forbidden present: `{summary.get('forbidden_present_total')}`",
        f"- Secret findings: `{summary.get('secret_findings_total')}`",
        "",
        "## Checks",
        "",
    ]
    for check in report.get("checks") or []:
        lines.append(f"- `{check['status']}` — `{check['check_id']}`: {check['reason']}")
    lines.extend(
        [
            "",
            "## Limitaciones",
            "",
        ]
    )
    for item in report.get("limitations") or []:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _to_posix(path: Path) -> str:
    return path.as_posix()


def _rel(root: Path, path: Path) -> str:
    try:
        return _to_posix(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)
