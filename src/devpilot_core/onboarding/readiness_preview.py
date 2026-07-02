from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.miasi import MiasiRegistryValidator
from devpilot_core.policy import PathGuard, PolicyEffect
from devpilot_core.schemas import SchemaValidator
from devpilot_core.standards.registry import build_standards_status_result
from devpilot_core.validators.artifact import validate_artifact_file
from devpilot_core.validators.checklist import validate_precode_checklist
from devpilot_core.validators.frontmatter import validate_frontmatter_file
from devpilot_core.validators.readiness import build_strict_readiness_result

ONBOARDING_READINESS_PREVIEW_SCHEMA_ID = "SCHEMA-DEVPL-ONBOARDING-READINESS-PREVIEW-REPORT-V1"
ONBOARDING_READINESS_PREVIEW_SCHEMA_PATH = "docs/schemas/onboarding_readiness_preview_report.schema.json"
DEFAULT_ONBOARDING_READINESS_PREVIEW_JSON = "outputs/reports/onboarding_readiness_preview_report.json"
DEFAULT_ONBOARDING_READINESS_PREVIEW_MARKDOWN = "outputs/reports/onboarding_readiness_preview_report.md"
DEFAULT_PREVIEW_TARGET_ROOT = "outputs/bootstrap_workspaces/ventas-micro-local"

_PROJECT_YAML = ".devpilot/project.yaml"

DOC_ARTIFACTS: tuple[tuple[str, str, str], ...] = (
    ("product", "docs/00_product/product_vision.md", "Product vision starter artifact"),
    ("product", "docs/00_product/mvp_scope.md", "MVP scope starter artifact"),
    ("requirements", "docs/01_requirements/requirements_specification.md", "Requirements starter artifact"),
    ("architecture", "docs/02_architecture/architecture_document.md", "Architecture starter artifact"),
    ("security", "docs/03_security/security_threat_model.md", "Security threat model starter artifact"),
    ("quality", "docs/04_quality/test_strategy.md", "Test strategy starter artifact"),
)

MIASI_ARTIFACTS: tuple[tuple[str, str, str], ...] = (
    ("MiasiAgentRegistry", ".devpilot/miasi/agent_registry.json", "Agent Registry starter contract"),
    ("MiasiToolRegistry", ".devpilot/miasi/tool_registry.json", "Tool Registry starter contract"),
    ("MiasiPolicyMatrix", ".devpilot/miasi/policy_matrix.json", "Policy Matrix starter contract"),
)

CHECKLIST_PATH = "docs/checklists/checklist_pre_code.md"
_SAFE_PREVIEW_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{2,63}$")
_BLOCKING_SEVERITIES = {Severity.BLOCK, Severity.ERROR, Severity.FAIL}


@dataclass(frozen=True)
class OnboardingReadinessPreviewOptions:
    """Options for POST-H-024-D onboarding readiness preview."""

    target_root: str = DEFAULT_PREVIEW_TARGET_ROOT
    project_id: str | None = None
    project_name: str | None = None
    write_report: bool = False
    output_json: str = DEFAULT_ONBOARDING_READINESS_PREVIEW_JSON
    output_markdown: str = DEFAULT_ONBOARDING_READINESS_PREVIEW_MARKDOWN


class OnboardingReadinessPreviewer:
    """Build a read-only readiness preview for a newly bootstrapped project.

    POST-H-024-D intentionally previews readiness rather than declaring a new
    project ready. Missing MIASI, checklist, standards or approved artifacts are
    reported as pending/blocking work items. The preview calls no network, no
    LLMs, no external APIs and never mutates source or workspace files unless
    the caller explicitly asks to persist the preview report under outputs/.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.path_guard = PathGuard(self.root)
        self.schema_validator = SchemaValidator(self.root)

    def run(self, options: OnboardingReadinessPreviewOptions) -> CommandResult:
        target_root = self._resolve_repo_path(options.target_root)
        path_decision = self.path_guard.evaluate(target_root, action="read")
        if path_decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            finding = Finding(
                "ONBOARDING_READINESS_TARGET_PATH_BLOCKED",
                f"Target workspace path is not allowed: {path_decision.reason}",
                Severity.BLOCK,
                path=path_decision.subject,
                metadata=path_decision.metadata,
            )
            report = self._build_report(options, target_root, [], [], [finding], report_written=False)
            return CommandResult(
                command="workspace readiness-preview",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Onboarding readiness preview blocked before validation.",
                data={"summary": report["summary"], "report": report},
                findings=[finding],
            )

        phases: list[dict[str, Any]] = []
        validations: list[dict[str, Any]] = []
        findings: list[Finding] = []

        phases.append(self._workspace_phase(target_root, options))
        phases.extend(self._documentation_phases(target_root, validations, findings))
        phases.append(self._checklist_phase(target_root, validations, findings))
        phases.append(self._standards_phase(target_root, validations, findings))
        phases.append(self._miasi_phase(target_root, validations, findings))
        phases.append(self._strict_readiness_phase(target_root, validations, findings))

        report = self._build_report(options, target_root, phases, validations, findings, report_written=False)
        report_schema = self.schema_validator.validate_payload(
            schema="OnboardingReadinessPreviewReport",
            payload=report,
            instance_label="onboarding_readiness_preview_report",
        )
        if not report_schema.ok:
            findings.extend(report_schema.findings)
            report = self._build_report(options, target_root, phases, validations, findings, report_written=False)

        report_written = False
        report_paths: dict[str, str] = {}
        if options.write_report:
            report_paths = self.write_report(report, output_json=options.output_json, output_markdown=options.output_markdown)
            report_written = True
            report = {
                **report,
                "reports": report_paths,
                "summary": {**report["summary"], "report_written": True, "reports": report_paths},
            }

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]
        ok = not blocking
        status = report["summary"]["status"]
        if ok:
            result_finding = Finding(
                "ONBOARDING_READINESS_PREVIEW_PASS" if status == "pass" else "ONBOARDING_READINESS_PREVIEW_PENDING",
                "Onboarding readiness preview completed; pending items are reported without overclaiming readiness.",
                Severity.INFO if status == "pass" else Severity.WARNING,
                path=_relative(target_root, self.root),
                metadata={"pending_total": report["summary"]["pending_total"], "report_written": report_written},
            )
            findings = [*findings, result_finding]
            report = self._build_report(options, target_root, phases, validations, findings, report_written=report_written)
            if report_written:
                report = {**report, "reports": report_paths, "summary": {**report["summary"], "report_written": True, "reports": report_paths}}

        return CommandResult(
            command="workspace readiness-preview",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message=(
                "Onboarding readiness preview completed with pending items."
                if ok and status != "pass"
                else "Onboarding readiness preview passed."
                if ok
                else "Onboarding readiness preview found blocking findings."
            ),
            data={"summary": report["summary"], "report": report},
            findings=findings,
        )

    def write_report(self, report: dict[str, Any], *, output_json: str, output_markdown: str) -> dict[str, str]:
        json_path = self._resolve_repo_path(output_json)
        markdown_path = self._resolve_repo_path(output_markdown)
        for path in (json_path, markdown_path):
            decision = self.path_guard.evaluate(path, action="write")
            if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
                raise ValueError(f"Report path blocked by PathGuard: {decision.reason}")
        paths = {"json": _relative(json_path, self.root), "markdown": _relative(markdown_path, self.root)}
        report_to_write = {**report, "reports": paths, "summary": {**report.get("summary", {}), "report_written": True, "reports": paths}}
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report_to_write, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(_render_markdown_report(report_to_write), encoding="utf-8")
        return paths

    def _workspace_phase(self, target_root: Path, options: OnboardingReadinessPreviewOptions) -> dict[str, Any]:
        project_yaml = target_root / _PROJECT_YAML
        checks: list[dict[str, Any]] = []
        if target_root.exists() and target_root.is_dir():
            checks.append(_check("workspace-root", _relative(target_root, self.root), "pass", "path-guard", "Target workspace root exists."))
        else:
            checks.append(
                _check(
                    "workspace-root",
                    _relative(target_root, self.root),
                    "pending",
                    "path-guard",
                    "Target workspace root does not exist yet. Run workspace bootstrap --execute in a controlled target when ready.",
                )
            )
        if project_yaml.is_file():
            checks.append(_check("workspace-project-yaml", _PROJECT_YAML, "pass", "workspace-project", ".devpilot/project.yaml exists."))
        else:
            checks.append(_check("workspace-project-yaml", _PROJECT_YAML, "pending", "workspace-project", ".devpilot/project.yaml is pending."))
        return _phase("workspace", "Workspace baseline", checks)

    def _documentation_phases(self, target_root: Path, validations: list[dict[str, Any]], findings: list[Finding]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = {key: [] for key, _, _ in DOC_ARTIFACTS}
        for phase_id, rel_path, description in DOC_ARTIFACTS:
            path = target_root / rel_path
            if not path.is_file():
                grouped[phase_id].append(_check(f"artifact-present:{rel_path}", rel_path, "pending", "artifact-inventory", f"{description} is pending."))
                continue
            grouped[phase_id].append(_check(f"artifact-present:{rel_path}", rel_path, "pass", "artifact-inventory", f"{description} exists."))
            frontmatter = validate_frontmatter_file(path, root=target_root, strict=False)
            artifact = validate_artifact_file(path, root=target_root, strict=False)
            validations.append(_validation("frontmatter", frontmatter, path=rel_path))
            validations.append(_validation("artifact", artifact, path=rel_path))
            grouped[phase_id].append(
                _check(
                    f"frontmatter:{rel_path}",
                    rel_path,
                    "pass" if frontmatter.ok else "pending",
                    "validate-frontmatter",
                    "Frontmatter validates." if frontmatter.ok else "Frontmatter requires correction before readiness.",
                    metadata={"findings_total": len(frontmatter.findings)},
                )
            )
            grouped[phase_id].append(
                _check(
                    f"artifact:{rel_path}",
                    rel_path,
                    "pass" if artifact.ok else "pending",
                    "validate-artifact",
                    "Artifact structure validates." if artifact.ok else "Artifact structure requires completion before readiness.",
                    metadata={"findings_total": len(artifact.findings), "missing_required_sections": artifact.data.get("missing_required_sections", [])},
                )
            )
            status = str(artifact.data.get("status") or "").strip().lower()
            if status == "approved":
                grouped[phase_id].append(_check(f"approval:{rel_path}", rel_path, "pass", "readiness-policy", "Artifact is approved."))
            else:
                grouped[phase_id].append(
                    _check(
                        f"approval:{rel_path}",
                        rel_path,
                        "pending",
                        "readiness-policy",
                        "Artifact exists but is not approved yet; readiness must not be overclaimed.",
                        metadata={"status": status or None},
                    )
                )
        titles = {
            "product": "Product artifacts",
            "requirements": "Requirements artifacts",
            "architecture": "Architecture artifacts",
            "security": "Security artifacts",
            "quality": "Quality artifacts",
        }
        return [_phase(phase_id, titles[phase_id], checks) for phase_id, checks in grouped.items()]

    def _checklist_phase(self, target_root: Path, validations: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        checklist_path = target_root / CHECKLIST_PATH
        if not checklist_path.is_file():
            checks = [_check("precode-checklist", CHECKLIST_PATH, "pending", "checklist-pre-code", "Pre-code checklist is pending for the new project.")]
            validations.append({"validator": "checklist-pre-code", "status": "pending", "ok": False, "path": CHECKLIST_PATH, "findings_total": 1, "summary": {"missing": True}})
            return _phase("checklist", "Pre-code checklist", checks)
        result = validate_precode_checklist(target_root, strict=False)
        validations.append(_validation("checklist-pre-code", result, path=CHECKLIST_PATH))
        checks = [
            _check(
                "precode-checklist",
                CHECKLIST_PATH,
                "pass" if result.ok else "pending",
                "checklist-pre-code",
                "Pre-code checklist validates." if result.ok else "Pre-code checklist has pending rows before readiness.",
                metadata=result.data.get("summary", {}),
            )
        ]
        return _phase("checklist", "Pre-code checklist", checks)

    def _standards_phase(self, target_root: Path, validations: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        result = build_standards_status_result(target_root)
        validations.append(_validation("standards-status", result, path="docs/standards"))
        checks = [
            _check(
                "standards-registry",
                "docs/standards",
                "pass" if result.ok else "pending",
                "standards-status",
                "StandardsRegistry validates required standards." if result.ok else "StandardsRegistry requirements are pending for this new project.",
                metadata=result.data.get("summary", {}),
            )
        ]
        return _phase("standards", "StandardsRegistry", checks)

    def _miasi_phase(self, target_root: Path, validations: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        missing = False
        for schema_id, rel_path, description in MIASI_ARTIFACTS:
            path = target_root / rel_path
            if not path.is_file():
                missing = True
                checks.append(_check(f"miasi-present:{rel_path}", rel_path, "pending", "miasi-inventory", f"{description} is pending."))
                continue
            checks.append(_check(f"miasi-present:{rel_path}", rel_path, "pass", "miasi-inventory", f"{description} exists."))
            schema_result = self.schema_validator.validate(schema=schema_id, instance=path)
            validations.append(_validation(f"schema:{schema_id}", schema_result, path=rel_path))
            checks.append(
                _check(
                    f"miasi-schema:{rel_path}",
                    rel_path,
                    "pass" if schema_result.ok else "pending",
                    f"schema:{schema_id}",
                    "MIASI starter JSON is structurally valid." if schema_result.ok else "MIASI starter JSON requires schema correction.",
                    metadata={"findings_total": len(schema_result.findings)},
                )
            )
        if missing:
            validations.append({"validator": "miasi-validate", "status": "pending", "ok": False, "path": ".devpilot/miasi", "findings_total": 1, "summary": {"miasi_missing": True}})
        else:
            miasi_result = MiasiRegistryValidator(target_root).validate_all()
            validations.append(_validation("miasi-validate", miasi_result, path=".devpilot/miasi"))
            checks.append(
                _check(
                    "miasi-semantic-readiness",
                    ".devpilot/miasi",
                    "pass" if miasi_result.ok else "pending",
                    "miasi-validate",
                    "MIASI semantic validation passed." if miasi_result.ok else "MIASI semantic/readiness requirements are pending; this is not reported as success.",
                    metadata={"findings_total": len(miasi_result.findings), "summary": miasi_result.data.get("summary", {})},
                )
            )
        return _phase("miasi", "MIASI readiness", checks)

    def _strict_readiness_phase(self, target_root: Path, validations: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        result = build_strict_readiness_result(target_root)
        validations.append(_validation("readiness-check --strict", result, path=_relative(target_root, self.root)))
        checks = [
            _check(
                "strict-readiness",
                _relative(target_root, self.root),
                "pass" if result.ok else "pending",
                "readiness-check --strict",
                "Strict readiness passed." if result.ok else "Strict readiness still has pending or blocking prerequisites; preview reports them without overclaiming readiness.",
                metadata=result.data.get("summary", {}),
            )
        ]
        return _phase("readiness", "Strict readiness preview", checks)

    def _build_report(
        self,
        options: OnboardingReadinessPreviewOptions,
        target_root: Path,
        phases: list[dict[str, Any]],
        validations: list[dict[str, Any]],
        findings: list[Finding],
        *,
        report_written: bool,
    ) -> dict[str, Any]:
        pending_items = _pending_items(phases)
        block_total = sum(phase["block_total"] for phase in phases)
        pending_total = sum(phase["pending_total"] for phase in phases)
        checks_total = sum(phase["checks_total"] for phase in phases)
        passed_total = sum(phase["passed_total"] for phase in phases)
        status = "block" if block_total else "warning" if pending_total else "pass"
        project = self._project_info(target_root, options)
        miasi_missing_reported_as_pending = any(
            item["phase_id"] == "miasi" and item["status"] == "pending" for item in pending_items
        )
        report = {
            "schema_version": "1.0",
            "schema_id": ONBOARDING_READINESS_PREVIEW_SCHEMA_ID,
            "preview_id": f"onboarding-readiness-preview-{_preview_id(project['project_id'])}",
            "created_by": "POST-H-024-D",
            "created_at": _now(),
            "target_root": _relative(target_root, self.root),
            "status": status,
            "project": project,
            "phases": phases,
            "pending_items": pending_items,
            "validations": validations,
            "safety": _safety(),
            "summary": {
                "status": status,
                "target_root": _relative(target_root, self.root),
                "target_exists": target_root.exists() and target_root.is_dir(),
                "phases_total": len(phases),
                "checks_total": checks_total,
                "passed_total": passed_total,
                "pending_total": pending_total,
                "block_total": block_total,
                "miasi_required": True,
                "miasi_missing_reported_as_pending": bool(miasi_missing_reported_as_pending or any(item["phase_id"] == "miasi" for item in pending_items)),
                "readiness_success_overclaimed": False,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "report_written": report_written,
            },
            "findings": [finding.to_dict() for finding in findings],
            "limitations": [
                "POST-H-024-D is a readiness preview, not a production-ready declaration.",
                "POST-H-024-D does not create the pilot fixture or quality gate; POST-H-024-E owns those capabilities.",
                "The preview reports pending MIASI/checklist/standards/readiness items instead of treating their absence as success.",
            ],
            "next_commands": _next_commands(_relative(target_root, self.root)),
        }
        return report

    def _project_info(self, target_root: Path, options: OnboardingReadinessPreviewOptions) -> dict[str, Any]:
        project_yaml = target_root / _PROJECT_YAML
        project_id = options.project_id or _slug(target_root.name or "project")
        project_name = options.project_name or project_id
        project_type = "agent-assisted-sdlc"
        if project_yaml.is_file():
            parsed = _parse_project_yaml(project_yaml)
            project = parsed.get("project", {}) if isinstance(parsed, dict) else {}
            project_id = str(project.get("id") or project.get("project_id") or project_id)
            project_name = str(project.get("name") or project.get("project_name") or project_name)
            project_type = str(project.get("type") or project.get("project_type") or project_type)
        return {
            "project_id": project_id,
            "project_name": project_name,
            "project_type": project_type,
            "project_yaml_exists": project_yaml.is_file(),
        }

    def _resolve_repo_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        return candidate.resolve()


def _check(check_id: str, path: str | None, status: str, source_validator: str, message: str, *, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "path": path,
        "status": status,
        "source_validator": source_validator,
        "message": message,
        "metadata": metadata or {},
    }


def _phase(phase_id: str, title: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
    block_total = sum(1 for check in checks if check["status"] == "block")
    pending_total = sum(1 for check in checks if check["status"] == "pending")
    passed_total = sum(1 for check in checks if check["status"] == "pass")
    status = "block" if block_total else "pending" if pending_total else "pass"
    return {
        "phase_id": phase_id,
        "title": title,
        "status": status,
        "checks_total": len(checks),
        "passed_total": passed_total,
        "pending_total": pending_total,
        "block_total": block_total,
        "checks": checks,
    }


def _validation(validator: str, result: CommandResult, *, path: str | None) -> dict[str, Any]:
    has_blocking = any(finding.severity in _BLOCKING_SEVERITIES for finding in result.findings)
    return {
        "validator": validator,
        "status": "pass" if result.ok else "pending" if has_blocking else "pending",
        "ok": bool(result.ok),
        "path": path,
        "findings_total": len(result.findings),
        "summary": result.data.get("summary", {}) if isinstance(result.data, dict) else {},
    }


def _pending_items(phases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for phase in phases:
        for check in phase["checks"]:
            if check["status"] in {"pending", "block"}:
                items.append(
                    {
                        "id": check["check_id"],
                        "phase_id": phase["phase_id"],
                        "path": check.get("path"),
                        "status": check["status"],
                        "source_validator": check["source_validator"],
                        "message": check["message"],
                        "metadata": check.get("metadata", {}),
                    }
                )
    return items


def _safety() -> dict[str, bool]:
    return {
        "local_first": True,
        "read_only": True,
        "dry_run": True,
        "network_used": False,
        "external_api_used": False,
        "remote_execution_used": False,
        "connector_write_used": False,
        "plugin_execution_used": False,
        "secrets_included": False,
        "mutations_performed": False,
        "source_mutations_performed": False,
    }


def _next_commands(target_root: str) -> list[str]:
    return [
        f"python -m devpilot_core workspace readiness-preview --target-root {target_root} --json --write-report",
        "python -m devpilot_core validate-frontmatter <artifact.md> --strict --json",
        "python -m devpilot_core validate-artifact <artifact.md> --strict --json",
        f"python -m devpilot_core workspace bootstrap --project-id ventas-micro-local --project-name \"Sistema agent-assisted de ventas e inventario para microemprendimientos locales\" --target-root {target_root} --dry-run --json --write-report",
        "python -m devpilot_core miasi validate --json",
    ]


def _render_markdown_report(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "---",
        'doc_id: "POST-H-024-D-ONBOARDING-READINESS-PREVIEW-RUNTIME-REPORT"',
        'title: "POST-H-024-D — Onboarding readiness preview runtime report"',
        'status: "generated"',
        'version: "1.0.0"',
        'owner: "Ordóñez"',
        f'updated: "{_today()}"',
        'created_by: "POST-H-024-D"',
        "preliminary: true",
        "local_first: true",
        "dry_run: true",
        "---",
        "",
        "# POST-H-024-D — Onboarding readiness preview runtime report",
        "",
        "## Summary",
        "",
        f"- Status: `{summary.get('status')}`",
        f"- Target root: `{summary.get('target_root')}`",
        f"- Pending items: `{summary.get('pending_total')}`",
        f"- Block items: `{summary.get('block_total')}`",
        f"- Network used: `{summary.get('network_used')}`",
        f"- External API used: `{summary.get('external_api_used')}`",
        f"- Mutations performed: `{summary.get('mutations_performed')}`",
        "",
        "## Pending items",
        "",
    ]
    pending = report.get("pending_items", [])
    if not pending:
        lines.append("No pending items reported by preview.")
    for item in pending:
        path = f" `{item.get('path')}`" if item.get("path") else ""
        lines.append(f"- `{item.get('phase_id')}` / `{item.get('id')}`{path}: {item.get('message')}")
    lines.extend(["", "## Limitations", ""])
    for limitation in report.get("limitations", []):
        lines.append(f"- {limitation}")
    return "\n".join(lines) + "\n"


def _parse_project_yaml(path: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    section: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        stripped = raw_line.strip()
        if not raw_line.startswith(" ") and stripped.endswith(":"):
            section = stripped[:-1]
            payload.setdefault(section, {})
            continue
        if section and raw_line.startswith("  ") and ":" in stripped:
            key, value = stripped.split(":", 1)
            payload.setdefault(section, {})[key.strip()] = value.strip().strip('"')
    return payload


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9_-]+", "-", value.lower()).strip("-")
    if _SAFE_PREVIEW_ID.match(slug):
        return slug
    return "project-preview"


def _preview_id(value: str) -> str:
    return _slug(value or "project-preview")


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _today() -> str:
    return datetime.now(UTC).date().isoformat()
