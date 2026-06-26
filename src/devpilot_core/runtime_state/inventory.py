from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.runtime_state.models import (
    POST_H_008_B_CREATED_BY,
    RUNTIME_STATE_INVENTORY_ID,
    RUNTIME_STATE_INVENTORY_SCHEMA_ID,
    RuntimeArtifact,
    RuntimeArtifactClass,
    RuntimeClassSummary,
    RuntimeStatePolicy,
    RuntimeViolation,
    RuntimeViolationSeverity,
    utc_now_iso,
)
from devpilot_core.runtime_state.policy import RuntimeStatePolicyLoader


@dataclass(frozen=True)
class RuntimeStateInventoryOptions:
    policy_path: str | Path = ".devpilot/runtime_state_policy.json"
    write_report: bool = False
    output_json: str | Path = "outputs/reports/runtime_state_inventory.json"
    output_markdown: str | Path = "outputs/reports/runtime_state_lifecycle_report.md"
    include_source_of_truth_artifacts: bool = True


class RuntimeStateInventoryBuilder:
    """Build a read-only inventory of DevPilot runtime-state artifacts.

    POST-H-008-B deliberately does not delete, redact, export or mutate source
    files. The only optional write is report materialization under outputs/ when
    `write_report=True`; inventory scanning itself only uses filesystem metadata
    and, when available, `git ls-files` to identify versioned runtime artifacts.
    """

    def __init__(self, root: Path, options: RuntimeStateInventoryOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or RuntimeStateInventoryOptions()

    def run(self) -> CommandResult:
        try:
            policy = RuntimeStatePolicyLoader(self.root, self.options.policy_path).load()
            payload = self.build_inventory(policy)
        except Exception as exc:
            finding = Finding(
                id="RUNTIME_STATE_INVENTORY_ERROR",
                message=f"Runtime-state inventory could not be built: {exc}",
                severity=Severity.ERROR,
            )
            return CommandResult(
                command="runtime-state inventory",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Runtime-state inventory failed.",
                data={"summary": {"policy_loaded": False, "read_only": True, "preliminary": True}},
                findings=[finding],
            )

        reports: dict[str, str] = {}
        if self.options.write_report:
            reports = self._planned_report_paths()
            payload["summary"]["reports_written"] = True
            payload["summary"]["output_json"] = reports["json"]
            payload["summary"]["output_markdown"] = reports["markdown"]
            self._write_reports(payload)
        else:
            payload["summary"]["reports_written"] = False
            payload["summary"]["output_json"] = None
            payload["summary"]["output_markdown"] = None

        findings = _findings_from_inventory(payload)
        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        return CommandResult(
            command="runtime-state inventory",
            ok=not blocking,
            exit_code=ExitCode.PASS if not blocking else ExitCode.BLOCK,
            message="Runtime-state inventory passed." if not blocking else "Runtime-state inventory found blocking violations.",
            data={"summary": payload["summary"], "inventory": payload, "reports": reports},
            findings=findings,
        )

    def build_inventory(self, policy: RuntimeStatePolicy) -> dict[str, Any]:
        git_tracked = _git_tracked_paths(self.root)
        git_available = git_tracked is not None
        git_tracked_set = git_tracked or set()
        artifacts = self._scan_artifacts(policy, git_tracked_set)
        violations = self._detect_violations(policy, artifacts, git_available)
        by_class = self._summarize_by_class(policy, artifacts)
        blocking_total = sum(1 for item in violations if _violation_severity(item) == "block")
        warnings_total = sum(1 for item in violations if _violation_severity(item) == "warn")
        runtime_artifacts_total = sum(1 for item in artifacts if not item.source_of_truth)
        source_of_truth_artifacts_total = sum(1 for item in artifacts if item.source_of_truth)
        versioned_runtime_artifacts_total = sum(1 for item in artifacts if item.git_tracked and not item.versionable)
        sensitive_runtime_artifacts_total = sum(1 for item in artifacts if item.sensitive)

        summary = {
            "policy_loaded": True,
            "read_only": True,
            "blocking_violations_total": blocking_total,
            "warnings_total": warnings_total,
            "preliminary": True,
            "created_by": POST_H_008_B_CREATED_BY,
            "status": "implemented-initial",
            "artifacts_total": len(artifacts),
            "runtime_artifacts_total": runtime_artifacts_total,
            "source_of_truth_artifacts_total": source_of_truth_artifacts_total,
            "versioned_runtime_artifacts_total": versioned_runtime_artifacts_total,
            "sensitive_runtime_artifacts_total": sensitive_runtime_artifacts_total,
            "classes_total": len(policy.artifact_classes),
            "classes_with_artifacts_total": sum(1 for item in by_class.values() if item["artifacts_total"] > 0),
            "git_metadata_available": git_available,
            "git_tracked_paths_total": len(git_tracked_set),
            "clean_zip_must_exclude_total": len(policy.zip_hygiene.get("must_exclude", [])),
            "cleanup_execution_enabled": False,
            "export_execution_enabled": False,
            "redaction_execution_enabled": False,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "destructive_cleanup_performed": False,
            "source_mutations_performed": False,
        }

        return {
            "schema_version": "1.0",
            "schema_id": RUNTIME_STATE_INVENTORY_SCHEMA_ID,
            "inventory_id": RUNTIME_STATE_INVENTORY_ID,
            "created_by": POST_H_008_B_CREATED_BY,
            "status": "implemented-initial",
            "generated_at_utc": utc_now_iso(),
            "policy_id": policy.policy_id,
            "policy_path": _rel(self.root, self.root / self.options.policy_path),
            "artifacts_total": len(artifacts),
            "by_class": by_class,
            "artifacts": [item.to_dict() for item in sorted(artifacts, key=lambda item: (item.class_id, item.path))],
            "violations": [item.to_dict() for item in sorted(violations, key=lambda item: (item.path, item.violation_id))],
            "summary": summary,
            "safety": {
                "mutations_performed": False,
                "network_used": False,
                "external_api_used": False,
                "destructive_cleanup_performed": False,
                "source_mutations_performed": False,
                "cleanup_execution_enabled": False,
                "export_execution_enabled": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
            },
            "notes": [
                "POST-H-008-B inventory is read-only: it scans metadata and does not clean, export, redact or persist runtime state.",
                "When .git metadata is available, non-versionable artifacts tracked by Git are blocking findings.",
                "When .git metadata is unavailable, source-archive detection is advisory and clean ZIP enforcement remains owned by POST-H-008-E.",
            ],
        }

    def _scan_artifacts(self, policy: RuntimeStatePolicy, git_tracked: set[str]) -> list[RuntimeArtifact]:
        artifacts_by_path_class: dict[tuple[str, str], RuntimeArtifact] = {}
        for artifact_class in policy.artifact_classes:
            if artifact_class.source_of_truth and not self.options.include_source_of_truth_artifacts:
                continue
            for pattern in artifact_class.paths:
                for candidate in _glob_files(self.root, pattern):
                    rel_path = _rel(self.root, candidate)
                    key = (rel_path, artifact_class.class_id)
                    previous = artifacts_by_path_class.get(key)
                    matched = tuple(sorted({*(previous.matched_patterns if previous else ()), pattern}))
                    artifacts_by_path_class[key] = _artifact_from_path(candidate, rel_path, artifact_class, git_tracked, matched)
        return list(artifacts_by_path_class.values())

    def _detect_violations(
        self,
        policy: RuntimeStatePolicy,
        artifacts: list[RuntimeArtifact],
        git_available: bool,
    ) -> list[RuntimeViolation]:
        violations: list[RuntimeViolation] = []
        must_exclude = tuple(str(item) for item in policy.zip_hygiene.get("must_exclude", []))
        for artifact in artifacts:
            if artifact.git_tracked and not artifact.versionable:
                violations.append(
                    RuntimeViolation(
                        violation_id="RUNTIME_STATE_VERSIONED",
                        path=artifact.path,
                        severity=RuntimeViolationSeverity.BLOCK,
                        class_id=artifact.class_id,
                        recommended_action="Remove the runtime artifact from Git tracking or regenerate it outside the source archive.",
                    )
                )
            if artifact.source_of_truth and artifact.cleanup_allowed:
                violations.append(
                    RuntimeViolation(
                        violation_id="SOURCE_OF_TRUTH_CLEANUP_ALLOWED",
                        path=artifact.path,
                        severity=RuntimeViolationSeverity.BLOCK,
                        class_id=artifact.class_id,
                        recommended_action="Set cleanup_allowed=false for source-of-truth classes before enabling cleanup planning.",
                    )
                )
            if _matches_must_exclude(artifact.path, must_exclude) and artifact.git_tracked:
                violations.append(
                    RuntimeViolation(
                        violation_id="CLEAN_ZIP_EXCLUDED_PATH_VERSIONED",
                        path=artifact.path,
                        severity=RuntimeViolationSeverity.BLOCK,
                        class_id=artifact.class_id,
                        recommended_action="Ensure clean ZIP generation excludes this runtime path using git archive or equivalent release packaging.",
                    )
                )
        if not git_available:
            violations.append(
                RuntimeViolation(
                    violation_id="GIT_METADATA_UNAVAILABLE",
                    path=".",
                    severity=RuntimeViolationSeverity.WARN,
                    recommended_action="Run inside a Git working tree to detect versioned runtime artifacts precisely; git archive ZIPs remain clean-source snapshots.",
                )
            )
        return violations

    def _summarize_by_class(self, policy: RuntimeStatePolicy, artifacts: list[RuntimeArtifact]) -> dict[str, dict[str, Any]]:
        grouped: dict[str, list[RuntimeArtifact]] = defaultdict(list)
        for artifact in artifacts:
            grouped[artifact.class_id].append(artifact)
        summaries: dict[str, dict[str, Any]] = {}
        for artifact_class in policy.artifact_classes:
            items = grouped.get(artifact_class.class_id, [])
            summaries[artifact_class.class_id] = RuntimeClassSummary(
                class_id=artifact_class.class_id,
                artifacts_total=len(items),
                bytes_total=sum(item.size_bytes for item in items),
                versionable=artifact_class.versionable,
                cleanup_allowed=artifact_class.cleanup_allowed,
                redaction_required=artifact_class.redaction_required,
            ).to_dict()
        return summaries

    def _planned_report_paths(self) -> dict[str, str]:
        return {
            "json": _rel(self.root, self.root / self.options.output_json),
            "markdown": _rel(self.root, self.root / self.options.output_markdown),
        }

    def _write_reports(self, payload: dict[str, Any]) -> dict[str, str]:
        json_path = self.root / self.options.output_json
        md_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        md_path.write_text(render_runtime_state_inventory_markdown(payload), encoding="utf-8")
        return self._planned_report_paths()


def render_runtime_state_inventory_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    by_class = payload.get("by_class", {})
    violations = payload.get("violations", [])
    lines = [
        "# Runtime state lifecycle report",
        "",
        f"Inventory ID: `{payload.get('inventory_id', '')}`",
        f"Generated at UTC: `{payload.get('generated_at_utc', '')}`",
        f"Created by: `{payload.get('created_by', '')}`",
        f"Status: `{payload.get('status', '')}`",
        "",
        "## Summary",
        "",
        f"- Artifacts total: `{summary.get('artifacts_total', payload.get('artifacts_total', 0))}`",
        f"- Runtime artifacts total: `{summary.get('runtime_artifacts_total', 0)}`",
        f"- Source-of-truth artifacts total: `{summary.get('source_of_truth_artifacts_total', 0)}`",
        f"- Versioned runtime artifacts total: `{summary.get('versioned_runtime_artifacts_total', 0)}`",
        f"- Blocking violations total: `{summary.get('blocking_violations_total', 0)}`",
        f"- Warnings total: `{summary.get('warnings_total', 0)}`",
        f"- Git metadata available: `{summary.get('git_metadata_available', False)}`",
        f"- Read-only: `{summary.get('read_only', True)}`",
        "",
        "## By class",
        "",
        "| Class | Artifacts | Bytes | Versionable | Cleanup allowed | Redaction required |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for class_id in sorted(by_class):
        item = by_class[class_id]
        lines.append(
            f"| `{class_id}` | {item.get('artifacts_total', 0)} | {item.get('bytes_total', 0)} | "
            f"{item.get('versionable', False)} | {item.get('cleanup_allowed', False)} | {item.get('redaction_required', False)} |"
        )
    lines.extend(["", "## Violations", ""])
    if not violations:
        lines.append("No runtime-state violations detected.")
    else:
        lines.extend(["| Severity | ID | Path | Recommended action |", "|---|---|---|---|"])
        for violation in violations:
            lines.append(
                f"| `{violation.get('severity', '')}` | `{violation.get('violation_id', '')}` | "
                f"`{violation.get('path', '')}` | {violation.get('recommended_action', '')} |"
            )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "This report is produced by a read-only inventory. It does not delete files, redact payloads, export runtime evidence, call network services or enable remote execution.",
            "Cleanup planning starts in POST-H-008-C; export/redaction starts in POST-H-008-D; release/quality-gate blocking starts in POST-H-008-E.",
            "",
        ]
    )
    return "\n".join(lines)


def _glob_files(root: Path, pattern: str) -> list[Path]:
    normalized = pattern.replace("\\", "/")
    matches: list[Path] = []
    for candidate in root.glob(normalized):
        if candidate.is_file():
            matches.append(candidate.resolve())
    return sorted(set(matches))


def _artifact_from_path(
    path: Path,
    rel_path: str,
    artifact_class: RuntimeArtifactClass,
    git_tracked: set[str],
    matched_patterns: tuple[str, ...],
) -> RuntimeArtifact:
    try:
        size = path.stat().st_size
    except OSError:
        size = 0
    return RuntimeArtifact(
        path=rel_path,
        class_id=artifact_class.class_id,
        classification=artifact_class.classification,
        size_bytes=int(size),
        source_of_truth=artifact_class.source_of_truth,
        versionable=artifact_class.versionable,
        sensitive=artifact_class.sensitive,
        cleanup_allowed=artifact_class.cleanup_allowed,
        export_allowed=artifact_class.export_allowed,
        redaction_required=artifact_class.redaction_required,
        never_delete=artifact_class.never_delete,
        git_tracked=rel_path in git_tracked,
        matched_patterns=matched_patterns,
    )


def _git_tracked_paths(root: Path) -> set[str] | None:
    if not (root / ".git").exists():
        return None
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "ls-files"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return None
    return {line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()}


def _matches_must_exclude(path: str, patterns: tuple[str, ...]) -> bool:
    normalized = path.replace("\\", "/")
    for pattern in patterns:
        clean = pattern.replace("\\", "/")
        if clean.endswith("/") and normalized.startswith(clean):
            return True
        if clean.startswith("*.") and normalized.endswith(clean[1:]):
            return True
        if normalized == clean:
            return True
    return False


def _findings_from_inventory(payload: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for violation in payload.get("violations", []) or []:
        severity = _finding_severity(str(violation.get("severity", "info")))
        findings.append(
            Finding(
                id=str(violation.get("violation_id", "RUNTIME_STATE_VIOLATION")),
                message=str(violation.get("recommended_action", "Runtime-state inventory finding.")),
                severity=severity,
                path=str(violation.get("path", "")) or None,
                metadata={"class_id": violation.get("class_id")},
            )
        )
    summary = payload.get("summary", {})
    if not any(finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for finding in findings):
        findings.append(
            Finding(
                id="RUNTIME_STATE_INVENTORY_PASS",
                message="Runtime-state inventory completed without blocking violations.",
                severity=Severity.INFO,
                metadata={
                    "artifacts_total": summary.get("artifacts_total", payload.get("artifacts_total", 0)),
                    "runtime_artifacts_total": summary.get("runtime_artifacts_total", 0),
                    "warnings_total": summary.get("warnings_total", 0),
                },
            )
        )
    return findings


def _finding_severity(severity: str) -> Severity:
    if severity == "block":
        return Severity.BLOCK
    if severity == "warn":
        return Severity.WARNING
    return Severity.INFO


def _violation_severity(violation: RuntimeViolation) -> str:
    severity = violation.severity
    return severity.value if isinstance(severity, RuntimeViolationSeverity) else str(severity)


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
