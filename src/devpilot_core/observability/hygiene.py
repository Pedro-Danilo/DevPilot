from __future__ import annotations

import fnmatch
import hashlib
import io
import json
import subprocess
import tarfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.observability.inventory import ObservabilityInventoryBuilder, ObservabilityInventoryOptions
from devpilot_core.observability.retention import (
    CLEAN_ZIP_REQUIRED_PREFIXES,
    DEFAULT_OBSERVABILITY_RETENTION_POLICY,
    ObservabilityRetentionPolicy,
    ObservabilityRetentionPolicyValidator,
    load_observability_retention_policy,
)

POST_H_010_E_CREATED_BY = "POST-H-010-E"
OBSERVABILITY_RETENTION_HYGIENE_SCHEMA_ID = "SCHEMA-DEVPL-OBSERVABILITY-RETENTION-HYGIENE-V1"
OBSERVABILITY_RETENTION_HYGIENE_CONTRACT = "ObservabilityRetentionHygiene"
OBSERVABILITY_RETENTION_HYGIENE_REPORT_ID = "devpilot-observability-retention-hygiene"

DEFAULT_OBSERVABILITY_HYGIENE_JSON = Path("outputs/reports/observability_retention_hygiene.json")
DEFAULT_OBSERVABILITY_HYGIENE_MARKDOWN = Path("outputs/reports/observability_retention_hygiene.md")

# This list is intentionally aligned with clean source ZIP rules and the
# POST-H-010 retention policy. It is repeated here so observability hygiene can
# fail closed even if a future runtime-state policy becomes stale.
BASE_FORBIDDEN_ARCHIVE_PATTERNS: tuple[str, ...] = (
    "outputs/",
    ".devpilot/devpilot.db",
    ".devpilot/*.db",
    ".devpilot/*.db-*",
    ".devpilot/agent_sessions/",
    ".git/",
    ".venv/",
    "venv/",
    "node_modules/",
    "ui/web/node_modules/",
    "dist/",
    "build/",
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".tox/",
    ".nox/",
    ".cache/",
    "*.pyc",
    "*.pyo",
    ".env",
    ".env.*",
)

SOURCE_ARCHIVE_ROOTS: tuple[str, ...] = (
    ".devpilot/",
    ".github/",
    "docs/",
    "evals/",
    "patches/",
    "scripts/",
    "src/",
    "tests/",
    "ui/",
)

SOURCE_ARCHIVE_ROOT_FILES: tuple[str, ...] = (
    ".env.example",
    ".gitignore",
    "README.md",
    "devpilot_bootstrap_manifest.json",
    "pyproject.toml",
    "safe.patch",
)


@dataclass(frozen=True)
class ObservabilityRetentionHygieneOptions:
    policy_path: str | Path = DEFAULT_OBSERVABILITY_RETENTION_POLICY
    write_report: bool = False
    output_json: str | Path = DEFAULT_OBSERVABILITY_HYGIENE_JSON
    output_markdown: str | Path = DEFAULT_OBSERVABILITY_HYGIENE_MARKDOWN
    include_git_archive_check: bool = True


class ObservabilityRetentionHygieneGate:
    """POST-H-010-E quality gate for observability retention hygiene.

    The gate is read-only and deterministic. It composes the POST-H-010 policy
    validator, the metadata-only inventory and a source ZIP hygiene simulation.
    It never requires runtime outputs to exist and never reads raw prompts,
    outputs, secrets or SQLite bytes.
    """

    def __init__(self, root: Path, options: ObservabilityRetentionHygieneOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ObservabilityRetentionHygieneOptions()

    def run(self) -> CommandResult:
        try:
            policy_validation = ObservabilityRetentionPolicyValidator(self.root, policy_path=self.options.policy_path).validate()
            policy = load_observability_retention_policy(self.root, self.options.policy_path)
            inventory_result = ObservabilityInventoryBuilder(
                self.root,
                ObservabilityInventoryOptions(policy_path=self.options.policy_path, write_report=False),
            ).run()
            inventory = (inventory_result.data or {}).get("inventory") or {}
            report = self.build_report(policy=policy, policy_validation=policy_validation, inventory=inventory)
        except Exception as exc:  # pragma: no cover - defensive quality-gate boundary
            finding = Finding(
                "OBSERVABILITY_RETENTION_HYGIENE_ERROR",
                f"Observability retention hygiene gate could not be evaluated: {exc}",
                Severity.ERROR,
            )
            return CommandResult(
                "observability retention-hygiene",
                False,
                ExitCode.ERROR,
                "Observability retention hygiene gate failed with an unexpected error.",
                data={"summary": {"created_by": POST_H_010_E_CREATED_BY, "preliminary": True}},
                findings=[finding],
            )

        reports: dict[str, str] = {}
        if self.options.write_report:
            report["summary"]["reports_written"] = True
            report["summary"]["output_json"] = _rel(self.root, self.root / self.options.output_json)
            report["summary"]["output_markdown"] = _rel(self.root, self.root / self.options.output_markdown)
            reports = self._write_reports(report)
        else:
            report["summary"]["reports_written"] = False
            report["summary"]["output_json"] = None
            report["summary"]["output_markdown"] = None

        findings = _findings_from_report(report)
        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        ok = not blocking
        return CommandResult(
            "observability retention-hygiene",
            ok,
            ExitCode.PASS if ok else _exit_code_from_findings(blocking),
            "Observability retention hygiene gate passed." if ok else "Observability retention hygiene gate found blocking findings.",
            data={"summary": report["summary"], "hygiene": report, "reports": reports},
            findings=findings,
        )

    def build_report(
        self,
        *,
        policy: ObservabilityRetentionPolicy,
        policy_validation: CommandResult,
        inventory: dict[str, Any],
    ) -> dict[str, Any]:
        policy_checks = self._policy_checks(policy, policy_validation)
        inventory_checks = self._inventory_checks(inventory)
        clean_zip_patterns = _clean_zip_patterns(policy)
        source_archive_plan = self._source_archive_plan(inventory=inventory, clean_zip_patterns=clean_zip_patterns)
        git_archive_check = self._git_archive_check(inventory=inventory, clean_zip_patterns=clean_zip_patterns)

        blocking_reasons: list[str] = []
        for check in policy_checks:
            if not check["ok"] and check["severity"] in {"fail", "block", "error"}:
                blocking_reasons.append(check["id"])
        for check in inventory_checks["target_checks"]:
            if not check["ok"] and check["severity"] in {"fail", "block", "error"}:
                blocking_reasons.append(check["id"])
        if source_archive_plan["forbidden_entries_total"] > 0:
            blocking_reasons.append("OBSERVABILITY_SOURCE_ARCHIVE_FORBIDDEN_ENTRIES")
        if source_archive_plan["runtime_entries_total"] > 0:
            blocking_reasons.append("OBSERVABILITY_SOURCE_ARCHIVE_RUNTIME_ENTRIES")
        if git_archive_check["checked"]:
            if git_archive_check["forbidden_entries_total"] > 0:
                blocking_reasons.append("OBSERVABILITY_GIT_ARCHIVE_FORBIDDEN_ENTRIES")
            if git_archive_check["runtime_entries_total"] > 0:
                blocking_reasons.append("OBSERVABILITY_GIT_ARCHIVE_RUNTIME_ENTRIES")
            if not git_archive_check["ok"]:
                blocking_reasons.append("OBSERVABILITY_GIT_ARCHIVE_CHECK_FAILED")

        clean_zip_hygiene_passed = source_archive_plan["clean"] and (not git_archive_check["checked"] or git_archive_check["clean"])
        policy_passed = all(check["ok"] for check in policy_checks)
        inventory_passed = inventory_checks["blocking_findings_total"] == 0
        gate_passed = not blocking_reasons
        summary = {
            "created_by": POST_H_010_E_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "policy_id": policy.policy_id,
            "policy_path": _rel(self.root, self.root / self.options.policy_path),
            "inventory_id": inventory.get("inventory_id", "devpilot-local-observability-inventory"),
            "dry_run": True,
            "read_only": True,
            "quality_gate_ready": gate_passed,
            "observability_retention_hygiene_passed": gate_passed,
            "policy_validation_passed": policy_passed,
            "inventory_validation_passed": inventory_passed,
            "clean_zip_hygiene_passed": clean_zip_hygiene_passed,
            "source_archive_plan_checked": source_archive_plan["checked"],
            "source_archive_plan_clean": source_archive_plan["clean"],
            "git_archive_available": git_archive_check["available"],
            "git_archive_checked": git_archive_check["checked"],
            "git_archive_clean": git_archive_check["clean"],
            "targets_total": len(policy.targets),
            "inventory_targets_total": inventory_checks["targets_total"],
            "inventory_missing_required_total": inventory_checks["required_targets_missing_total"],
            "inventory_clean_zip_risks_total": inventory_checks["clean_zip_risks_total"],
            "rotation_recommended_total": inventory_checks["rotation_recommended_total"],
            "redaction_required_total": inventory_checks["redaction_required_total"],
            "forbidden_archive_entries_total": source_archive_plan["forbidden_entries_total"] + (git_archive_check["forbidden_entries_total"] if git_archive_check["checked"] else 0),
            "runtime_archive_entries_total": source_archive_plan["runtime_entries_total"] + (git_archive_check["runtime_entries_total"] if git_archive_check["checked"] else 0),
            "clean_zip_patterns_total": len(clean_zip_patterns),
            "blocking_reasons_total": len(set(blocking_reasons)),
            "warnings_total": inventory_checks["warnings_total"] + (0 if git_archive_check["checked"] else 1),
            "blocking_findings_total": len(set(blocking_reasons)),
            "reports_written": False,
            "output_json": None,
            "output_markdown": None,
            "raw_payloads_read": False,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "destructive_cleanup_performed": False,
            "source_mutations_performed": False,
            "cleanup_execution_enabled": False,
            "export_execution_enabled": False,
            "redaction_execution_enabled": False,
            "remote_export_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
        }
        return {
            "schema_version": "1.0",
            "schema_id": OBSERVABILITY_RETENTION_HYGIENE_SCHEMA_ID,
            "report_id": OBSERVABILITY_RETENTION_HYGIENE_REPORT_ID,
            "created_by": POST_H_010_E_CREATED_BY,
            "status": "implemented-initial",
            "generated_at_utc": _utc_now_iso(),
            "policy_id": policy.policy_id,
            "policy_path": summary["policy_path"],
            "inventory_id": summary["inventory_id"],
            "policy_checks": policy_checks,
            "inventory_checks": inventory_checks,
            "source_archive_plan": source_archive_plan,
            "git_archive_check": git_archive_check,
            "summary": summary,
            "safety": {
                "local_first": True,
                "read_only": True,
                "dry_run_default": True,
                "raw_payloads_read": False,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "destructive_cleanup_performed": False,
                "source_mutations_performed": False,
                "cleanup_execution_enabled": False,
                "export_execution_enabled": False,
                "redaction_execution_enabled": False,
                "remote_export_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "zip_hygiene_enforced": True,
            },
            "notes": [
                "POST-H-010-E integrates observability retention hygiene into quality-gate hardening/industrial as a deterministic read-only subgate.",
                "Runtime outputs are not required for this gate to pass; missing observability runtime artifacts are warnings so clean source ZIPs remain verifiable.",
                "The gate validates policy defaults, inventory metadata, redaction/clean ZIP flags and deterministic source archive hygiene without reading raw payloads.",
                "Actual cleanup execution, remote export, signing/encryption and production DLP remain out of scope for this implemented-initial version.",
            ],
        }

    def _policy_checks(self, policy: ObservabilityRetentionPolicy, policy_validation: CommandResult) -> list[dict[str, Any]]:
        checks: list[dict[str, Any]] = [
            _check_dict(
                "POLICY_VALIDATION_PASS",
                bool(policy_validation.ok),
                "info" if policy_validation.ok else "block",
                "Observability retention policy semantic validation passed." if policy_validation.ok else "Observability retention policy semantic validation failed.",
                path=str(self.options.policy_path).replace("\\", "/"),
            ),
            _check_dict(
                "POLICY_LOCAL_FIRST",
                policy.local_first,
                "info" if policy.local_first else "block",
                "Policy is local-first." if policy.local_first else "Policy must be local-first.",
                path=str(self.options.policy_path).replace("\\", "/"),
            ),
            _check_dict(
                "POLICY_REMOTE_EXPORT_DISABLED",
                not policy.remote_export_enabled,
                "info" if not policy.remote_export_enabled else "block",
                "Remote export is disabled." if not policy.remote_export_enabled else "Remote export must remain disabled.",
                path=str(self.options.policy_path).replace("\\", "/"),
            ),
            _check_dict(
                "POLICY_DEFAULT_DRY_RUN",
                policy.default_mode == "dry-run",
                "info" if policy.default_mode == "dry-run" else "block",
                "Policy defaults to dry-run." if policy.default_mode == "dry-run" else "Policy must default to dry-run.",
                path=str(self.options.policy_path).replace("\\", "/"),
                metadata={"default_mode": policy.default_mode},
            ),
        ]
        required_prefixes = list(CLEAN_ZIP_REQUIRED_PREFIXES)
        for prefix in required_prefixes:
            ok = any(target.path == prefix.rstrip("/") or target.path.startswith(prefix) or target.path == prefix for target in policy.targets)
            checks.append(_check_dict(
                f"POLICY_DECLARES_TARGET_{_slug(prefix)}",
                ok,
                "info" if ok else "block",
                f"Policy declares a governed observability target for {prefix}." if ok else f"Policy must declare a governed target for {prefix}.",
                path=str(self.options.policy_path).replace("\\", "/"),
            ))
        for target in policy.targets:
            ok = target.clean_zip_excluded and not target.versionable and not target.source_of_truth and not target.raw_payload_storage_allowed
            severity = "info" if ok else "block"
            checks.append(_check_dict(
                f"TARGET_POLICY_SAFE_{_slug(target.target_id)}",
                ok,
                severity,
                "Observability target has safe retention/archive defaults." if ok else "Observability target must be clean_zip_excluded, non-versionable and disallow raw payload storage.",
                path=target.path,
                metadata={"target_id": target.target_id},
            ))
            if target.contains_sensitive_payloads:
                checks.append(_check_dict(
                    f"TARGET_REDACTION_REQUIRED_{_slug(target.target_id)}",
                    target.redaction_required,
                    "info" if target.redaction_required else "block",
                    "Sensitive observability target requires redaction." if target.redaction_required else "Sensitive observability target must require redaction.",
                    path=target.path,
                    metadata={"target_id": target.target_id},
                ))
        return checks

    def _inventory_checks(self, inventory: dict[str, Any]) -> dict[str, Any]:
        summary = inventory.get("summary") or {}
        target_checks = inventory.get("target_checks") if isinstance(inventory.get("target_checks"), list) else []
        checks: list[dict[str, Any]] = []
        for item in target_checks:
            target_id = str(item.get("target_id", "unknown"))
            path = str(item.get("path", ""))
            clean_ok = bool(item.get("clean_zip_excluded", False)) and not bool(item.get("clean_zip_risk", False))
            checks.append(_check_dict(
                f"INVENTORY_CLEAN_ZIP_{_slug(target_id)}",
                clean_ok,
                "info" if clean_ok else "block",
                "Inventory target is clean ZIP excluded." if clean_ok else "Inventory target has clean ZIP risk.",
                path=path,
                metadata={"target_id": target_id},
            ))
            workspace_ok = bool(item.get("inside_workspace", False))
            checks.append(_check_dict(
                f"INVENTORY_WORKSPACE_BOUNDARY_{_slug(target_id)}",
                workspace_ok,
                "info" if workspace_ok else "block",
                "Inventory target is inside workspace." if workspace_ok else "Inventory target resolves outside workspace.",
                path=path,
                metadata={"target_id": target_id},
            ))
            runtime_ok = not bool(item.get("versionable", False)) and not bool(item.get("source_of_truth", False))
            checks.append(_check_dict(
                f"INVENTORY_RUNTIME_NONVERSIONABLE_{_slug(target_id)}",
                runtime_ok,
                "info" if runtime_ok else "block",
                "Inventory target is non-versionable runtime evidence." if runtime_ok else "Inventory target must not be source-of-truth or versionable.",
                path=path,
                metadata={"target_id": target_id},
            ))
        return {
            "inventory_available": bool(inventory),
            "targets_total": int(summary.get("targets_total", len(target_checks)) or 0),
            "targets_existing_total": int(summary.get("targets_existing_total", 0) or 0),
            "required_targets_missing_total": int(summary.get("required_targets_missing_total", 0) or 0),
            "clean_zip_risks_total": int(summary.get("clean_zip_risks_total", 0) or 0),
            "rotation_recommended_total": int(summary.get("rotation_recommended_total", 0) or 0),
            "redaction_required_total": int(summary.get("redaction_required_total", 0) or 0),
            "warnings_total": int(summary.get("warnings_total", 0) or 0),
            "blocking_findings_total": int(summary.get("blocking_findings_total", 0) or 0),
            "target_checks": checks,
        }

    def _source_archive_plan(self, *, inventory: dict[str, Any], clean_zip_patterns: list[str]) -> dict[str, Any]:
        candidates = sorted(_iter_source_archive_candidates(self.root))
        included: list[str] = []
        excluded: list[dict[str, Any]] = []
        forbidden_included: list[dict[str, Any]] = []
        runtime_included: list[dict[str, Any]] = []
        target_map = _target_map(inventory)
        for rel in candidates:
            matches = _matching_patterns(rel, clean_zip_patterns)
            if matches:
                excluded.append({"path": rel, "reason": "clean-zip-excluded", "patterns": matches})
                continue
            included.append(rel)
            forbidden = _matching_patterns(rel, clean_zip_patterns)
            if forbidden:
                forbidden_included.append({"path": rel, "patterns": forbidden})
            target = target_map.get(rel)
            if target and _is_nonversionable_observability_target(target):
                runtime_included.append({"path": rel, "target_id": target.get("target_id"), "classification": target.get("classification")})
        digest = hashlib.sha256("\n".join(included).encode("utf-8")).hexdigest()
        return {
            "checked": True,
            "strategy": "deterministic-source-archive-plan",
            "clean": not forbidden_included and not runtime_included,
            "included_files_total": len(included),
            "excluded_files_total": len(excluded),
            "forbidden_entries_total": len(forbidden_included),
            "runtime_entries_total": len(runtime_included),
            "included_files_sha256": digest,
            "forbidden_entries": forbidden_included[:100],
            "runtime_entries": runtime_included[:100],
            "excluded_samples": excluded[:100],
        }

    def _git_archive_check(self, *, inventory: dict[str, Any], clean_zip_patterns: list[str]) -> dict[str, Any]:
        git_dir = self.root / ".git"
        if not self.options.include_git_archive_check:
            return _git_archive_skipped(available=git_dir.exists(), reason="disabled-by-options")
        if not git_dir.exists():
            return _git_archive_skipped(available=False, reason="git-metadata-unavailable")
        completed = subprocess.run(
            ["git", "archive", "--format=tar", "HEAD"],
            cwd=self.root,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            return {
                **_git_archive_skipped(available=True, reason="git-archive-command-failed"),
                "ok": False,
                "stderr_tail": completed.stderr.decode("utf-8", errors="replace")[-500:],
            }
        try:
            with tarfile.open(fileobj=io.BytesIO(completed.stdout), mode="r:") as archive:
                names = sorted(name for name in archive.getnames() if name and not name.endswith("/"))
        except tarfile.TarError as exc:
            return {
                **_git_archive_skipped(available=True, reason="git-archive-tar-parse-failed"),
                "ok": False,
                "stderr_tail": str(exc),
            }
        target_map = _target_map(inventory)
        forbidden: list[dict[str, Any]] = []
        runtime: list[dict[str, Any]] = []
        normalized = [_normalize_rel(name) for name in names]
        for rel in normalized:
            matches = _matching_patterns(rel, clean_zip_patterns)
            if matches:
                forbidden.append({"path": rel, "patterns": matches})
            target = target_map.get(rel)
            if target and _is_nonversionable_observability_target(target):
                runtime.append({"path": rel, "target_id": target.get("target_id"), "classification": target.get("classification")})
        digest = hashlib.sha256("\n".join(normalized).encode("utf-8")).hexdigest()
        return {
            "available": True,
            "checked": True,
            "ok": True,
            "clean": not forbidden and not runtime,
            "strategy": "git-archive-head-in-memory",
            "entries_total": len(normalized),
            "entries_sha256": digest,
            "forbidden_entries_total": len(forbidden),
            "runtime_entries_total": len(runtime),
            "forbidden_entries": forbidden[:100],
            "runtime_entries": runtime[:100],
            "reason": None,
        }

    def _write_reports(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = self.root / self.options.output_json
        markdown_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        markdown_path.write_text(render_observability_retention_hygiene_markdown(report), encoding="utf-8")
        return {"json": _rel(self.root, json_path), "markdown": _rel(self.root, markdown_path)}


def render_observability_retention_hygiene_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    source = report.get("source_archive_plan", {})
    git = report.get("git_archive_check", {})
    lines = [
        "# Observability retention hygiene report",
        "",
        f"- Created by: `{report.get('created_by')}`",
        f"- Status: `{report.get('status')}`",
        f"- Generated at UTC: `{report.get('generated_at_utc')}`",
        f"- Quality-gate ready: `{summary.get('quality_gate_ready')}`",
        f"- Policy validation passed: `{summary.get('policy_validation_passed')}`",
        f"- Inventory validation passed: `{summary.get('inventory_validation_passed')}`",
        f"- Clean ZIP hygiene passed: `{summary.get('clean_zip_hygiene_passed')}`",
        f"- Blocking findings: `{summary.get('blocking_findings_total')}`",
        f"- Warnings: `{summary.get('warnings_total')}`",
        "",
        "## Source archive plan",
        "",
        f"- Strategy: `{source.get('strategy')}`",
        f"- Clean: `{source.get('clean')}`",
        f"- Included files: `{source.get('included_files_total')}`",
        f"- Excluded files: `{source.get('excluded_files_total')}`",
        f"- Forbidden entries: `{source.get('forbidden_entries_total')}`",
        f"- Runtime entries: `{source.get('runtime_entries_total')}`",
        "",
        "## Git archive HEAD",
        "",
        f"- Available: `{git.get('available')}`",
        f"- Checked: `{git.get('checked')}`",
        f"- Clean: `{git.get('clean')}`",
        f"- Reason: `{git.get('reason')}`",
        "",
        "## Safety",
        "",
        "```json",
        json.dumps(report.get("safety", {}), indent=2, ensure_ascii=False, sort_keys=True),
        "```",
        "",
        "## Notes",
        "",
    ]
    for note in report.get("notes", []):
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def _findings_from_report(report: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for check in report.get("policy_checks", []):
        findings.append(_finding_from_check(check, default_id="OBSERVABILITY_POLICY_CHECK"))
    for check in report.get("inventory_checks", {}).get("target_checks", []):
        findings.append(_finding_from_check(check, default_id="OBSERVABILITY_INVENTORY_CHECK"))
    source = report.get("source_archive_plan", {})
    if source.get("forbidden_entries_total", 0) > 0:
        findings.append(Finding(
            "OBSERVABILITY_SOURCE_ARCHIVE_FORBIDDEN_ENTRIES_BLOCK",
            "Deterministic source archive plan includes forbidden observability/runtime/build/cache entries.",
            Severity.BLOCK,
            metadata={"entries": source.get("forbidden_entries", [])[:25]},
        ))
    if source.get("runtime_entries_total", 0) > 0:
        findings.append(Finding(
            "OBSERVABILITY_SOURCE_ARCHIVE_RUNTIME_ENTRIES_BLOCK",
            "Deterministic source archive plan includes non-versionable observability runtime artifacts.",
            Severity.BLOCK,
            metadata={"entries": source.get("runtime_entries", [])[:25]},
        ))
    git = report.get("git_archive_check", {})
    if git.get("checked"):
        if git.get("forbidden_entries_total", 0) > 0:
            findings.append(Finding(
                "OBSERVABILITY_GIT_ARCHIVE_FORBIDDEN_ENTRIES_BLOCK",
                "git archive HEAD includes forbidden observability/runtime/build/cache entries.",
                Severity.BLOCK,
                metadata={"entries": git.get("forbidden_entries", [])[:25]},
            ))
        if git.get("runtime_entries_total", 0) > 0:
            findings.append(Finding(
                "OBSERVABILITY_GIT_ARCHIVE_RUNTIME_ENTRIES_BLOCK",
                "git archive HEAD includes non-versionable observability runtime artifacts.",
                Severity.BLOCK,
                metadata={"entries": git.get("runtime_entries", [])[:25]},
            ))
        if not git.get("ok", True):
            findings.append(Finding(
                "OBSERVABILITY_GIT_ARCHIVE_CHECK_ERROR",
                "git archive HEAD check failed.",
                Severity.ERROR,
                metadata={"reason": git.get("reason"), "stderr_tail": git.get("stderr_tail")},
            ))
    else:
        findings.append(Finding(
            "OBSERVABILITY_GIT_ARCHIVE_CHECK_SKIPPED",
            "git archive HEAD was not inspected because Git metadata is unavailable or disabled; deterministic source archive plan was checked instead.",
            Severity.WARNING,
            metadata={"reason": git.get("reason")},
        ))
    if not any(finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for finding in findings):
        findings.append(Finding(
            "OBSERVABILITY_RETENTION_HYGIENE_PASS",
            "Observability retention hygiene checks passed.",
            Severity.INFO,
            metadata={"quality_gate_ready": report.get("summary", {}).get("quality_gate_ready")},
        ))
    return findings


def _finding_from_check(check: dict[str, Any], *, default_id: str) -> Finding:
    severity = _severity_from_string(str(check.get("severity", "info")))
    return Finding(
        id=str(check.get("id") or default_id),
        message=str(check.get("message") or "Observability retention hygiene check."),
        severity=severity,
        path=str(check["path"]) if check.get("path") else None,
        metadata=dict(check.get("metadata", {})),
    )


def _check_dict(
    id_: str,
    ok: bool,
    severity: str,
    message: str,
    *,
    path: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"id": id_, "ok": bool(ok), "severity": severity, "message": message}
    if path:
        payload["path"] = path
    if metadata:
        payload["metadata"] = metadata
    return payload


def _clean_zip_patterns(policy: ObservabilityRetentionPolicy) -> list[str]:
    target_patterns = []
    for target in policy.targets:
        if target.clean_zip_excluded:
            path = _normalize_rel(target.path)
            if target.kind in {"directory", "directory-glob"} and not path.endswith("/"):
                path = path + "/"
            target_patterns.append(path)
    result: list[str] = []
    for item in [*CLEAN_ZIP_REQUIRED_PREFIXES, *target_patterns, *BASE_FORBIDDEN_ARCHIVE_PATTERNS]:
        value = str(item).replace("\\", "/")
        if value and value not in result:
            result.append(value)
    return result


def _target_map(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    target_checks = inventory.get("target_checks") if isinstance(inventory.get("target_checks"), list) else []
    return {_normalize_rel(str(item.get("path"))): item for item in target_checks if isinstance(item, dict) and item.get("path")}


def _is_nonversionable_observability_target(target: dict[str, Any]) -> bool:
    return not bool(target.get("source_of_truth")) and not bool(target.get("versionable"))


def _iter_source_archive_candidates(root: Path) -> list[str]:
    candidates: list[str] = []
    for file_name in SOURCE_ARCHIVE_ROOT_FILES:
        path = root / file_name
        if path.exists() and path.is_file():
            candidates.append(file_name)
    for prefix in SOURCE_ARCHIVE_ROOTS:
        base = root / prefix
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file():
                candidates.append(_rel(root, path))
    return sorted(set(candidates))


def _git_archive_skipped(*, available: bool, reason: str) -> dict[str, Any]:
    return {
        "available": available,
        "checked": False,
        "ok": True,
        "clean": True,
        "strategy": "git-archive-head-in-memory",
        "entries_total": 0,
        "entries_sha256": None,
        "forbidden_entries_total": 0,
        "runtime_entries_total": 0,
        "forbidden_entries": [],
        "runtime_entries": [],
        "reason": reason,
    }


def _matching_patterns(path: str, patterns: list[str]) -> list[str]:
    rel = _normalize_rel(path)
    return [pattern for pattern in patterns if _matches_pattern(rel, pattern)]


def _matches_pattern(path: str, pattern: str) -> bool:
    rel = _normalize_rel(path)
    pat = pattern.replace("\\", "/").strip()
    if not pat:
        return False
    if pat.endswith("/"):
        prefix = pat.rstrip("/") + "/"
        return rel.startswith(prefix) or f"/{prefix}" in f"/{rel}"
    if "*" in pat or "?" in pat or "[" in pat:
        return fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(PurePosixPath(rel).name, pat)
    return rel == pat or rel.startswith(pat.rstrip("/") + "/")


def _normalize_rel(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _severity_from_string(value: str) -> Severity:
    return {
        "info": Severity.INFO,
        "warning": Severity.WARNING,
        "warn": Severity.WARNING,
        "block": Severity.BLOCK,
        "fail": Severity.FAIL,
        "error": Severity.ERROR,
    }.get(value, Severity.INFO)


def _exit_code_from_findings(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _slug(value: str) -> str:
    result = value.upper().replace(".", "_").replace("/", "_").replace("-", "_").replace("*", "STAR")
    return "_".join(part for part in result.split("_") if part)


__all__ = [
    "DEFAULT_OBSERVABILITY_HYGIENE_JSON",
    "DEFAULT_OBSERVABILITY_HYGIENE_MARKDOWN",
    "OBSERVABILITY_RETENTION_HYGIENE_CONTRACT",
    "OBSERVABILITY_RETENTION_HYGIENE_REPORT_ID",
    "OBSERVABILITY_RETENTION_HYGIENE_SCHEMA_ID",
    "POST_H_010_E_CREATED_BY",
    "ObservabilityRetentionHygieneGate",
    "ObservabilityRetentionHygieneOptions",
    "render_observability_retention_hygiene_markdown",
]
