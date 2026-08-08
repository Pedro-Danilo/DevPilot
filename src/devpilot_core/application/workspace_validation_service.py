from __future__ import annotations

import hashlib
import json
import os
import posixpath
import re
import time
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.miasi import MiasiRegistryValidator
from devpilot_core.observability.events import EventLogger
from devpilot_core.reports import ReportEngine
from devpilot_core.traceability.workspace_matrix import WorkspaceTraceabilityMatrixBuilder
from devpilot_core.validators.artifact import validate_artifact_file
from devpilot_core.validators.frontmatter import parse_frontmatter_file, validate_frontmatter_file
from devpilot_core.validators.readiness import build_strict_readiness_result

from .ui_workspace_context import UiWorkspaceContext, UiWorkspaceContextResolver
from .workspace_documents_service import WorkspaceDocumentNode, WorkspaceDocumentsApplicationService, sha_bytes

VALIDATION_SCOPES = (
    "frontmatter",
    "artifact_profile",
    "links",
    "miasi",
    "readiness_strict",
    "checklist_pre_code",
    "traceability",
)
MAX_PLAN_DOCUMENTS = 16
MAX_PLAN_SCOPES = len(VALIDATION_SCOPES)
MAX_TIMEOUT_SECONDS = 120
MAX_JOB_FILES = 100
JOB_ID_PATTERN = re.compile(r"^vjob_[0-9a-f]{32}$")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

DEFAULT_PRECODE_ARTIFACTS: tuple[dict[str, Any], ...] = (
    {"role": "project_config", "relative_path": ".devpilot/project.yaml", "required": True},
    {"role": "product_vision", "relative_path": "docs/00_product/product_vision.md", "required": True},
    {"role": "mvp_scope", "relative_path": "docs/00_product/mvp_scope.md", "required": True},
    {"role": "requirements", "relative_path": "docs/01_requirements/requirements_specification.md", "required": True},
    {"role": "architecture", "relative_path": "docs/02_architecture/architecture_document.md", "required": True},
    {"role": "security", "relative_path": "docs/03_security/security_threat_model.md", "required": True},
    {"role": "test_strategy", "relative_path": "docs/04_quality/test_strategy.md", "required": True},
    {"role": "onboarding_baseline", "relative_path": "docs/onboarding/workspace_onboarding_baseline.md", "required": True},
)
MIASI_PATHS = (
    ".devpilot/miasi/agent_registry.json",
    ".devpilot/miasi/tool_registry.json",
    ".devpilot/miasi/policy_matrix.json",
)


@dataclass(frozen=True)
class PlannedArtifact:
    role: str
    relative_path: str
    document_id: str
    sha256: str
    size_bytes: int
    required: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "relative_path": self.relative_path,
            "document_id": self.document_id,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "required": self.required,
        }


class WorkspaceValidationApplicationService:
    """UOC-003 deterministic workspace validation and traceability facade.

    The facade reuses existing validators and adds only bounded orchestration,
    immutable plans, source-read-only job evidence, finding navigation and an
    explicit-only traceability matrix. Jobs execute synchronously in this first
    version; async execution, heartbeat and cancellation remain assigned to
    UOC-007/UOC-008.
    """

    def __init__(
        self,
        platform_root: Path,
        *,
        context_resolver: UiWorkspaceContextResolver | None = None,
        documents: WorkspaceDocumentsApplicationService | None = None,
    ) -> None:
        self.platform_root = Path(platform_root).resolve()
        self.context_resolver = context_resolver or UiWorkspaceContextResolver(self.platform_root)
        self.documents = documents or WorkspaceDocumentsApplicationService(self.platform_root, context_resolver=self.context_resolver)
        self._plans: dict[str, dict[str, Any]] = {}

    def plan(
        self,
        *,
        scopes: Iterable[str] | None = None,
        document_ids: Iterable[str] | None = None,
        strict: bool = True,
        timeout_seconds: int = 45,
    ) -> CommandResult:
        context, failure = self._require_context("workspace validations plan")
        if failure is not None:
            return failure
        assert context is not None and context.active_workspace_root is not None
        normalized_scopes, scope_findings = _normalize_scopes(scopes)
        if scope_findings:
            return _result("workspace validations plan", scope_findings, data={"allowed_scopes": list(VALIDATION_SCOPES)})
        safe_timeout = max(5, min(int(timeout_seconds), MAX_TIMEOUT_SECONDS))
        artifacts, artifact_findings, document_map = self._plan_artifacts(context, document_ids=document_ids)
        findings = list(context.findings) + artifact_findings
        if any(item.severity in {Severity.BLOCK, Severity.ERROR} for item in findings):
            return _result("workspace validations plan", findings, data={"artifacts": [item.to_dict() for item in artifacts]})

        plan_content = {
            "schema_id": "devpilot.post_h_eval_002.uoc_003.validation_plan.v1",
            "workspace_id": context.active_workspace_id,
            "workspace_root_fingerprint": _path_fingerprint(context.active_workspace_root),
            "strict": bool(strict),
            "scopes": normalized_scopes,
            "artifacts": [item.to_dict() for item in artifacts],
            "budgets": {
                "timeout_seconds": safe_timeout,
                "documents_max": MAX_PLAN_DOCUMENTS,
                "scopes_max": MAX_PLAN_SCOPES,
                "diff_or_content_bytes_persisted": 0,
            },
            "safety": _safety(runtime_evidence_written=False),
            "preliminary": True,
        }
        plan_hash = _canonical_hash(plan_content)
        plan = {
            **plan_content,
            "plan_id": f"vplan_{plan_hash[:32]}",
            "plan_hash": plan_hash,
            "created_at": _now(),
            "expires_after_seconds": 1800,
        }
        self._plans[plan["plan_id"]] = plan
        while len(self._plans) > 64:
            self._plans.pop(next(iter(self._plans)))
        findings.append(Finding(
            "UOC003_VALIDATION_PLAN_PASS",
            "Immutable read-only validation plan was created for the active workspace.",
            Severity.INFO,
            metadata={"plan_id": plan["plan_id"], "artifacts_total": len(artifacts), "scopes_total": len(normalized_scopes)},
        ))
        return CommandResult(
            "workspace validations plan",
            True,
            ExitCode.PASS,
            "Workspace validation plan is ready for governed execution.",
            data={
                "summary": {
                    "workspace_id": context.active_workspace_id,
                    "artifacts_total": len(artifacts),
                    "required_artifacts_total": sum(1 for item in artifacts if item.required),
                    "scopes_total": len(normalized_scopes),
                    "strict": bool(strict),
                    "read_only": True,
                    "runtime_evidence_written": False,
                    "preliminary": True,
                },
                "plan": plan,
                "document_map": document_map,
                "ui_workspace_context": context.summary(),
                "safety": _safety(runtime_evidence_written=False),
            },
            findings=findings,
        )

    def execute(self, *, plan_id: str, plan_hash: str, plan: dict[str, Any] | None = None) -> CommandResult:
        context, failure = self._require_context("workspace validations execute")
        if failure is not None:
            return failure
        assert context is not None and context.active_workspace_root is not None
        resolved_plan, findings = self._resolve_plan(plan_id=plan_id, plan_hash=plan_hash, supplied_plan=plan)
        if resolved_plan is None:
            return _result("workspace validations execute", findings)
        if resolved_plan.get("workspace_root_fingerprint") != _path_fingerprint(context.active_workspace_root):
            findings.append(Finding("UOC003_VALIDATION_PLAN_WORKSPACE_MISMATCH_BLOCK", "Validation plan belongs to a different workspace.", Severity.BLOCK))
            return _result("workspace validations execute", findings)
        stale = self._stale_artifacts(context.active_workspace_root, resolved_plan.get("artifacts", []))
        if stale:
            findings.append(Finding(
                "UOC003_VALIDATION_PLAN_STALE_BLOCK",
                "One or more planned artifacts changed after the immutable plan was created.",
                Severity.BLOCK,
                metadata={"stale_artifacts": stale},
            ))
            return _result("workspace validations execute", findings)

        job_id = f"vjob_{uuid.uuid4().hex}"
        started = time.perf_counter()
        started_at = _now()
        step_results: list[dict[str, Any]] = []
        all_findings: list[Finding] = list(context.findings)
        document_ids = {str(item["relative_path"]): str(item["document_id"]) for item in resolved_plan.get("artifacts", [])}
        source_paths = [str(item["relative_path"]) for item in resolved_plan.get("artifacts", [])]
        deadline = started + int(resolved_plan.get("budgets", {}).get("timeout_seconds", 45))
        trace_path = self._job_path(context, job_id, create=True)
        initial_job = {
            "schema_id": "devpilot.post_h_eval_002.uoc_003.validation_job.v1",
            "job_id": job_id,
            "plan_id": plan_id,
            "plan_hash": plan_hash,
            "workspace_id": context.active_workspace_id,
            "status": "running",
            "started_at": started_at,
            "steps": [],
            "safety": _safety(runtime_evidence_written=True),
        }
        _atomic_json(trace_path, initial_job)

        try:
            for scope in resolved_plan.get("scopes", []):
                if time.perf_counter() > deadline:
                    all_findings.append(Finding("UOC003_VALIDATION_TIMEOUT_BLOCK", "Validation job exceeded its bounded timeout budget.", Severity.BLOCK, metadata={"scope": scope}))
                    break
                scope_started = time.perf_counter()
                result = self._run_scope(
                    scope,
                    context=context,
                    artifacts=resolved_plan.get("artifacts", []),
                    document_ids=document_ids,
                    source_paths=source_paths,
                    strict=bool(resolved_plan.get("strict", True)),
                )
                navigable = self._navigable_findings(result.findings, context=context, document_ids=document_ids)
                all_findings.extend(navigable)
                step_results.append({
                    "scope": scope,
                    "status": _status_for_result(result),
                    "ok": result.ok,
                    "exit_code": int(result.exit_code),
                    "message": result.message,
                    "duration_ms": round((time.perf_counter() - scope_started) * 1000, 2),
                    "data": result.data,
                    "findings": [item.to_dict() for item in navigable],
                })
        except Exception as exc:
            all_findings.append(Finding(
                "UOC003_VALIDATION_JOB_ERROR",
                "Validation job failed at the application-service boundary.",
                Severity.ERROR,
                metadata={"exception_type": exc.__class__.__name__},
            ))

        exit_code = exit_code_for_findings(all_findings)
        ok = exit_code == ExitCode.PASS
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        counts = Counter(item.severity.value for item in all_findings)
        job_status = "pass" if ok else ("error" if exit_code == ExitCode.ERROR else "block")
        result = CommandResult(
            "workspace validations execute",
            ok,
            exit_code,
            "Workspace validation job completed." if ok else "Workspace validation job completed with blocking findings.",
            data={
                "summary": {
                    "job_id": job_id,
                    "plan_id": plan_id,
                    "workspace_id": context.active_workspace_id,
                    "status": job_status,
                    "steps_total": len(step_results),
                    "steps_passed": sum(1 for item in step_results if item["status"] == "PASS"),
                    "findings_total": len(all_findings),
                    "findings_by_severity": dict(sorted(counts.items())),
                    "duration_ms": duration_ms,
                    "strict_readiness_visible": "readiness_strict" in resolved_plan.get("scopes", []),
                    "precode_artifacts_total": len(resolved_plan.get("artifacts", [])),
                    "read_only_source": True,
                    "runtime_evidence_written": True,
                    "preliminary": True,
                },
                "job": {"job_id": job_id, "status": job_status, "started_at": started_at, "ended_at": _now()},
                "steps": step_results,
                "safety": _safety(runtime_evidence_written=True),
            },
            findings=all_findings,
        )
        report_engine = ReportEngine(context.active_workspace_root, reports_dir=context.reports_root or (context.active_workspace_root / "outputs/reports"))
        report_paths = report_engine.write_command_report(
            result,
            report_id=f"uoc-003-validation-{job_id}",
            metadata={"sprint": "UOC-003", "plan_id": plan_id, "job_id": job_id, "read_only_source": True},
        ).to_dict()
        event_path = EventLogger(
            context.active_workspace_root,
            events_path=(context.traces_root or context.active_workspace_root / "outputs/traces") / "uoc_003_validation_events.jsonl",
        ).emit_result(result, event_type="uoc003.validation.completed", subject=context.active_workspace_root).to_dict()
        job_payload = {
            **initial_job,
            "status": job_status,
            "ended_at": _now(),
            "duration_ms": duration_ms,
            "summary": result.data["summary"],
            "steps": step_results,
            "findings": [item.to_dict() for item in all_findings],
            "report_paths": report_paths,
            "event_ref": event_path,
        }
        _atomic_json(trace_path, job_payload)
        result.data["job"].update({"trace_path": _relative(trace_path, context.active_workspace_root), "report_paths": report_paths, "event_ref": event_path})
        return result

    def get_job(self, *, job_id: str) -> CommandResult:
        context, failure = self._require_context("workspace validations status")
        if failure is not None:
            return failure
        assert context is not None and context.active_workspace_root is not None
        if not JOB_ID_PATTERN.fullmatch(str(job_id or "")):
            return _result("workspace validations status", [Finding("UOC003_VALIDATION_JOB_ID_BLOCK", "Validation job id is invalid.", Severity.BLOCK)])
        path = self._job_path(context, job_id, create=False)
        if not path.is_file():
            return _result("workspace validations status", [Finding("UOC003_VALIDATION_JOB_NOT_FOUND", "Validation job evidence was not found.", Severity.BLOCK)])
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return _result("workspace validations status", [Finding("UOC003_VALIDATION_JOB_READ_ERROR", "Validation job evidence could not be read.", Severity.ERROR, metadata={"exception_type": exc.__class__.__name__})])
        return CommandResult(
            "workspace validations status",
            payload.get("status") == "pass",
            ExitCode.PASS if payload.get("status") == "pass" else ExitCode.BLOCK,
            "Validation job evidence is available.",
            data={"job": payload, "safety": _safety(runtime_evidence_written=True)},
            findings=[Finding("UOC003_VALIDATION_JOB_STATUS_PASS", "Validation job status was read from bounded local evidence.", Severity.INFO, metadata={"job_id": job_id})],
        )

    def traceability(self) -> CommandResult:
        context, failure = self._require_context("workspace traceability")
        if failure is not None:
            return failure
        assert context is not None and context.active_workspace_root is not None
        artifacts, artifact_findings, document_map = self._plan_artifacts(context, document_ids=None)
        source_paths = [item.relative_path for item in artifacts if item.relative_path.endswith((".md", ".txt"))]
        payload, findings = WorkspaceTraceabilityMatrixBuilder(
            context.active_workspace_root,
            document_ids=document_map,
        ).build(source_paths)
        findings = list(context.findings) + artifact_findings + self._navigable_findings(findings, context=context, document_ids=document_map)
        exit_code = exit_code_for_findings(findings)
        return CommandResult(
            "workspace traceability",
            exit_code == ExitCode.PASS,
            exit_code,
            "Workspace traceability matrix is available.",
            data={"traceability": payload, "ui_workspace_context": context.summary(), "safety": _safety(runtime_evidence_written=False)},
            findings=findings,
        )

    def _run_scope(
        self,
        scope: str,
        *,
        context: UiWorkspaceContext,
        artifacts: list[dict[str, Any]],
        document_ids: dict[str, str],
        source_paths: list[str],
        strict: bool,
    ) -> CommandResult:
        assert context.active_workspace_root is not None
        root = context.active_workspace_root
        if scope == "frontmatter":
            return self._validate_documents("frontmatter", root, artifacts, strict=strict)
        if scope == "artifact_profile":
            return self._validate_documents("artifact_profile", root, artifacts, strict=strict)
        if scope == "links":
            return self._validate_links(root, artifacts, document_ids=document_ids)
        if scope == "miasi":
            return MiasiRegistryValidator(root).validate_all()
        if scope == "readiness_strict":
            return build_strict_readiness_result(root)
        if scope == "checklist_pre_code":
            return self._validate_profile_checklist(root, artifacts)
        if scope == "traceability":
            payload, findings = WorkspaceTraceabilityMatrixBuilder(root, document_ids=document_ids).build(source_paths)
            return _result("workspace traceability", findings, data={"traceability": payload})
        return _result("workspace validations execute", [Finding("UOC003_VALIDATION_SCOPE_BLOCK", "Unsupported validation scope.", Severity.BLOCK, metadata={"scope": scope})])

    def _validate_documents(self, mode: str, root: Path, artifacts: list[dict[str, Any]], *, strict: bool) -> CommandResult:
        findings: list[Finding] = []
        rows: list[dict[str, Any]] = []
        for artifact in artifacts:
            relative = str(artifact["relative_path"])
            path = root / PurePosixPath(relative)
            if path.suffix.lower() != ".md":
                continue
            result = validate_frontmatter_file(path, root=root, strict=strict) if mode == "frontmatter" else validate_artifact_file(path, root=root, strict=strict)
            findings.extend(result.findings)
            rows.append({"relative_path": relative, "ok": result.ok, "exit_code": int(result.exit_code), "message": result.message})
        if not rows:
            findings.append(Finding("UOC003_VALIDATION_NO_MARKDOWN_BLOCK", "No Markdown pre-code artifacts were available for validation.", Severity.BLOCK))
        return _result(f"workspace validations {mode}", findings, data={"documents": rows, "summary": {"documents_total": len(rows)}})

    def _validate_profile_checklist(self, root: Path, artifacts: list[dict[str, Any]]) -> CommandResult:
        findings: list[Finding] = []
        checks: list[dict[str, Any]] = []
        for artifact in artifacts:
            relative = str(artifact["relative_path"])
            path = root / PurePosixPath(relative)
            exists = path.is_file()
            approved: bool | None = None
            if exists and path.suffix.lower() == ".md":
                try:
                    approved = str(parse_frontmatter_file(path).frontmatter.get("status", "")).strip().lower() == "approved"
                except (OSError, UnicodeDecodeError):
                    approved = False
            passed = exists and (approved is not False)
            checks.append({"role": artifact.get("role"), "relative_path": relative, "exists": exists, "approved": approved, "status": "PASS" if passed else "BLOCK"})
            if not exists:
                findings.append(Finding("UOC003_PRECODE_ARTIFACT_MISSING_BLOCK", "Required pre-code artifact is missing.", Severity.BLOCK, path=relative, metadata={"role": artifact.get("role")}))
            elif approved is False:
                findings.append(Finding("UOC003_PRECODE_ARTIFACT_NOT_APPROVED_BLOCK", "Required pre-code Markdown artifact is not approved in frontmatter.", Severity.BLOCK, path=relative, metadata={"role": artifact.get("role")}))
        for relative in MIASI_PATHS:
            exists = (root / PurePosixPath(relative)).is_file()
            checks.append({"role": "miasi_registry", "relative_path": relative, "exists": exists, "approved": None, "status": "PASS" if exists else "BLOCK"})
            if not exists:
                findings.append(Finding("UOC003_PRECODE_MIASI_REGISTRY_MISSING_BLOCK", "Required MIASI registry is missing.", Severity.BLOCK, path=relative))
        if not findings:
            findings.append(Finding("UOC003_PRECODE_CHECKLIST_PASS", "Profile-backed pre-code checklist passed for eight artifacts and MIASI registries.", Severity.INFO, metadata={"artifacts_total": len(artifacts), "miasi_registries_total": len(MIASI_PATHS)}))
        return _result("workspace validations checklist pre-code", findings, data={"checks": checks, "summary": {"checks_total": len(checks), "profile_backed": True, "cli_bridge_residual": "checklist-pre-code file-based command remains registered"}})

    def _validate_links(self, root: Path, artifacts: list[dict[str, Any]], *, document_ids: dict[str, str]) -> CommandResult:
        findings: list[Finding] = []
        links: list[dict[str, Any]] = []
        heading_cache: dict[str, set[str]] = {}
        artifact_paths = {str(item["relative_path"]) for item in artifacts}
        for artifact in artifacts:
            relative = str(artifact["relative_path"])
            path = root / PurePosixPath(relative)
            if path.suffix.lower() != ".md" or not path.is_file():
                continue
            try:
                lines = path.read_text(encoding="utf-8-sig").splitlines()
            except (OSError, UnicodeDecodeError) as exc:
                findings.append(Finding("UOC003_LINK_SOURCE_READ_BLOCK", "Markdown source could not be read for link validation.", Severity.BLOCK, path=relative, metadata={"exception_type": exc.__class__.__name__}))
                continue
            section: str | None = None
            for line_number, line in enumerate(lines, start=1):
                heading = _HEADING_RE.match(line)
                if heading:
                    section = heading.group(2).strip()
                for label, raw_target in _LINK_RE.findall(line):
                    target = raw_target.strip().strip("<>")
                    split = urlsplit(target)
                    row = {"source_relative_path": relative, "source_document_id": document_ids.get(relative), "line": line_number, "section": section, "label": label, "target": target}
                    if split.scheme or split.netloc:
                        row.update({"kind": "external", "status": "INFO"})
                        links.append(row)
                        continue
                    decoded = unquote(split.path).replace("\\", "/")
                    if not decoded and split.fragment:
                        normalized = relative
                    else:
                        normalized = posixpath.normpath(str(PurePosixPath(relative).parent / decoded))
                    if decoded.startswith("/") or re.match(r"^[A-Za-z]:", decoded) or ":" in PurePosixPath(decoded).name or normalized.startswith("../") or normalized == "..":
                        row.update({"kind": "blocked", "status": "BLOCK", "resolved_relative_path": normalized})
                        links.append(row)
                        findings.append(Finding("UOC003_LINK_PATH_BLOCK", "Document link is absolute, ADS-like or escapes the workspace.", Severity.BLOCK, path=relative, metadata={"line": line_number, "section": section, "document_id": document_ids.get(relative), "target": target}))
                        continue
                    target_path = root / PurePosixPath(normalized)
                    if not target_path.is_file():
                        row.update({"kind": "missing", "status": "BLOCK", "resolved_relative_path": normalized})
                        links.append(row)
                        findings.append(Finding("UOC003_LINK_TARGET_MISSING_BLOCK", "Local document link target does not exist.", Severity.BLOCK, path=relative, metadata={"line": line_number, "section": section, "document_id": document_ids.get(relative), "target": target, "resolved_relative_path": normalized}))
                        continue
                    if split.fragment:
                        anchors = heading_cache.setdefault(normalized, _heading_anchors(target_path))
                        if _slug(split.fragment) not in anchors:
                            row.update({"kind": "missing-anchor", "status": "BLOCK", "resolved_relative_path": normalized})
                            links.append(row)
                            findings.append(Finding("UOC003_LINK_ANCHOR_MISSING_BLOCK", "Local document link anchor does not exist.", Severity.BLOCK, path=relative, metadata={"line": line_number, "section": section, "document_id": document_ids.get(relative), "target": target, "resolved_relative_path": normalized}))
                            continue
                    row.update({"kind": "document", "status": "PASS", "resolved_relative_path": normalized, "target_document_id": document_ids.get(normalized), "target_in_precode_profile": normalized in artifact_paths})
                    links.append(row)
        if not any(item.severity in {Severity.BLOCK, Severity.ERROR} for item in findings):
            findings.append(Finding("UOC003_LINK_VALIDATION_PASS", "Workspace document links passed deterministic local validation.", Severity.INFO, metadata={"links_total": len(links)}))
        return _result("workspace validations links", findings, data={"links": links, "summary": {"links_total": len(links), "local_links_total": sum(1 for item in links if item.get("kind") != "external")}})

    def _plan_artifacts(self, context: UiWorkspaceContext, *, document_ids: Iterable[str] | None) -> tuple[list[PlannedArtifact], list[Finding], dict[str, str]]:
        assert context.active_workspace_root is not None
        nodes, discovery_findings, _ = self.documents._discover(context)
        by_path = {node.relative_path: node for node in nodes if node.kind == "document"}
        by_id = {node.node_id: node for node in nodes if node.kind == "document"}
        requested = list(document_ids or [])
        definitions: list[dict[str, Any]]
        findings: list[Finding] = list(discovery_findings)
        if requested:
            if len(requested) > MAX_PLAN_DOCUMENTS:
                findings.append(Finding("UOC003_VALIDATION_DOCUMENT_BUDGET_BLOCK", "Too many documents were requested for one validation plan.", Severity.BLOCK, metadata={"maximum": MAX_PLAN_DOCUMENTS}))
                return [], findings, {}
            definitions = []
            for document_id in requested:
                node = by_id.get(str(document_id))
                if node is None:
                    findings.append(Finding("UOC003_VALIDATION_DOCUMENT_ID_BLOCK", "Validation plan contains an unknown opaque document id.", Severity.BLOCK, metadata={"document_id": str(document_id)}))
                    continue
                definitions.append({"role": "operator_selected", "relative_path": node.relative_path, "required": True})
        else:
            definitions = [dict(item) for item in DEFAULT_PRECODE_ARTIFACTS]

        artifacts: list[PlannedArtifact] = []
        document_map: dict[str, str] = {}
        for definition in definitions:
            relative = str(definition["relative_path"]).replace("\\", "/")
            node = by_path.get(relative)
            if node is None:
                findings.append(Finding("UOC003_PRECODE_ARTIFACT_NOT_CONSULTABLE_BLOCK", "Required pre-code artifact is not consultable through the UOC document boundary.", Severity.BLOCK, path=relative, metadata={"role": definition.get("role")}))
                continue
            path = context.active_workspace_root / PurePosixPath(relative)
            try:
                raw = path.read_bytes()
            except OSError as exc:
                findings.append(Finding("UOC003_PRECODE_ARTIFACT_READ_BLOCK", "Required pre-code artifact could not be read.", Severity.BLOCK, path=relative, metadata={"exception_type": exc.__class__.__name__}))
                continue
            artifact = PlannedArtifact(str(definition.get("role") or "artifact"), relative, node.node_id, sha_bytes(raw), len(raw), bool(definition.get("required", True)))
            artifacts.append(artifact)
            document_map[relative] = node.node_id
        return artifacts, findings, document_map

    def _resolve_plan(self, *, plan_id: str, plan_hash: str, supplied_plan: dict[str, Any] | None) -> tuple[dict[str, Any] | None, list[Finding]]:
        findings: list[Finding] = []
        candidate = supplied_plan or self._plans.get(str(plan_id))
        if not isinstance(candidate, dict):
            findings.append(Finding("UOC003_VALIDATION_PLAN_NOT_FOUND_BLOCK", "Validation plan is not available; create a new plan or submit the immutable plan payload.", Severity.BLOCK))
            return None, findings
        if str(candidate.get("plan_id")) != str(plan_id) or str(candidate.get("plan_hash")) != str(plan_hash):
            findings.append(Finding("UOC003_VALIDATION_PLAN_ID_HASH_BLOCK", "Validation plan id/hash binding is invalid.", Severity.BLOCK))
            return None, findings
        content = {key: value for key, value in candidate.items() if key not in {"plan_id", "plan_hash", "created_at", "expires_after_seconds"}}
        actual = _canonical_hash(content)
        if actual != str(plan_hash):
            findings.append(Finding("UOC003_VALIDATION_PLAN_TAMPER_BLOCK", "Validation plan content does not match its immutable hash.", Severity.BLOCK))
            return None, findings
        return candidate, findings

    def _stale_artifacts(self, root: Path, artifacts: list[dict[str, Any]]) -> list[dict[str, str]]:
        stale: list[dict[str, str]] = []
        for item in artifacts:
            relative = str(item.get("relative_path") or "")
            path = root / PurePosixPath(relative)
            actual = sha_bytes(path.read_bytes()) if path.is_file() else "<missing>"
            expected = str(item.get("sha256") or "")
            if actual != expected:
                stale.append({"relative_path": relative, "expected_sha256": expected, "actual_sha256": actual})
        return stale

    def _navigable_findings(self, findings: Iterable[Finding], *, context: UiWorkspaceContext, document_ids: dict[str, str]) -> list[Finding]:
        assert context.active_workspace_root is not None
        normalized: list[Finding] = []
        for finding in findings:
            path = str(finding.path).replace("\\", "/") if finding.path else None
            if path and Path(path).is_absolute():
                try:
                    path = str(Path(path).resolve().relative_to(context.active_workspace_root)).replace("\\", "/")
                except ValueError:
                    path = None
            metadata = dict(finding.metadata or {})
            if path:
                metadata.setdefault("navigation", {
                    "relative_path": path,
                    "document_id": document_ids.get(path),
                    "line": metadata.get("line") or metadata.get("line_number"),
                    "section": metadata.get("section"),
                })
            normalized.append(Finding(finding.id, finding.message, finding.severity, path=path, metadata=metadata))
        return normalized

    def _job_path(self, context: UiWorkspaceContext, job_id: str, *, create: bool) -> Path:
        assert context.active_workspace_root is not None
        traces_root = (context.traces_root or (context.active_workspace_root / "outputs/traces")).resolve()
        root = (traces_root / "uoc_003_validation_jobs").resolve()
        if create:
            root.mkdir(parents=True, exist_ok=True)
            _prune_job_files(root)
        path = (root / f"{job_id}.json").resolve()
        path.relative_to(context.active_workspace_root)
        return path

    def _require_context(self, command: str) -> tuple[UiWorkspaceContext | None, CommandResult | None]:
        context = self.context_resolver.resolve()
        if not context.configured or not context.valid or context.active_workspace_root is None:
            findings = list(context.findings)
            findings.append(Finding("UOC003_ACTIVE_WORKSPACE_REQUIRED_BLOCK", "UOC-003 requires an explicit PathGuard-approved active workspace.", Severity.BLOCK))
            return None, _result(command, findings, data={"ui_workspace_context": context.summary()})
        return context, None


def _normalize_scopes(scopes: Iterable[str] | None) -> tuple[list[str], list[Finding]]:
    requested = [str(item).strip().lower() for item in (scopes or VALIDATION_SCOPES) if str(item).strip()]
    requested = list(dict.fromkeys(requested))
    findings: list[Finding] = []
    if not requested:
        findings.append(Finding("UOC003_VALIDATION_SCOPE_EMPTY_BLOCK", "At least one validation scope is required.", Severity.BLOCK))
    unknown = [item for item in requested if item not in VALIDATION_SCOPES]
    if unknown:
        findings.append(Finding("UOC003_VALIDATION_SCOPE_UNKNOWN_BLOCK", "Validation plan contains unsupported scopes.", Severity.BLOCK, metadata={"unknown_scopes": unknown}))
    if len(requested) > MAX_PLAN_SCOPES:
        findings.append(Finding("UOC003_VALIDATION_SCOPE_BUDGET_BLOCK", "Validation scope budget was exceeded.", Severity.BLOCK))
    return requested, findings


def _result(command: str, findings: list[Finding], *, data: dict[str, Any] | None = None) -> CommandResult:
    exit_code = exit_code_for_findings(findings)
    ok = exit_code == ExitCode.PASS
    return CommandResult(command, ok, exit_code, f"{command} {'passed' if ok else 'reported findings'}.", data=data or {}, findings=findings)


def _status_for_result(result: CommandResult) -> str:
    return {ExitCode.PASS: "PASS", ExitCode.FAIL: "FAIL", ExitCode.BLOCK: "BLOCK", ExitCode.ERROR: "ERROR"}[result.exit_code]


def _safety(*, runtime_evidence_written: bool) -> dict[str, Any]:
    return {
        "local_first": True,
        "read_only_source": True,
        "runtime_evidence_written": runtime_evidence_written,
        "source_mutations_performed": False,
        "arbitrary_shell_allowed": False,
        "free_form_validator_command_allowed": False,
        "network_used": False,
        "external_api_used": False,
        "remote_execution_enabled": False,
        "connector_write_enabled": False,
        "plugin_execution_enabled": False,
        "jobs_synchronous_preliminary": True,
        "cancel_supported": False,
    }


def _canonical_hash(payload: dict[str, Any]) -> str:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(rendered).hexdigest()


def _path_fingerprint(path: Path) -> str:
    return hashlib.sha256(os.path.normcase(str(path.resolve())).encode("utf-8")).hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(temp, path)


def _prune_job_files(root: Path) -> None:
    files = sorted((item for item in root.glob("vjob_*.json") if item.is_file()), key=lambda item: item.stat().st_mtime, reverse=True)
    for stale in files[MAX_JOB_FILES:]:
        try:
            stale.unlink()
        except OSError:
            pass


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _heading_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeDecodeError):
        return anchors
    for line in lines:
        match = _HEADING_RE.match(line)
        if match:
            anchors.add(_slug(match.group(2)))
    return anchors


def _slug(value: str) -> str:
    value = unquote(str(value)).strip().lower()
    value = re.sub(r"[^a-z0-9\s_-]", "", value)
    value = re.sub(r"[\s_]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-")
