from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.onboarding.templates import MARKDOWN_TEMPLATE_PATHS, MIASI_TEMPLATE_PATHS, validate_new_project_templates
from devpilot_core.policy import PathGuard, PolicyEffect, SecretGuard
from devpilot_core.workspace.manager import DEFAULT_PROJECT_TYPE, render_project_yaml

PROJECT_BOOTSTRAP_REPORT_SCHEMA_ID = "SCHEMA-DEVPL-PROJECT-BOOTSTRAP-REPORT-V1"
PROJECT_BOOTSTRAP_REPORT_SCHEMA_PATH = "docs/schemas/project_bootstrap_report.schema.json"
DEFAULT_BOOTSTRAP_OUTPUT_JSON = "outputs/reports/project_bootstrap_report.json"
DEFAULT_BOOTSTRAP_OUTPUT_MARKDOWN = "outputs/reports/project_bootstrap_report.md"
DEFAULT_BOOTSTRAP_TARGET_BASE = "outputs/bootstrap_workspaces"

_DOC_TEMPLATE_TARGETS: dict[str, str] = {
    "docs/templates/new_project/product_vision.template.md": "docs/00_product/product_vision.md",
    "docs/templates/new_project/mvp_scope.template.md": "docs/00_product/mvp_scope.md",
    "docs/templates/new_project/requirements_specification.template.md": "docs/01_requirements/requirements_specification.md",
    "docs/templates/new_project/architecture_document.template.md": "docs/02_architecture/architecture_document.md",
    "docs/templates/new_project/security_threat_model.template.md": "docs/03_security/security_threat_model.md",
    "docs/templates/new_project/test_strategy.template.md": "docs/04_quality/test_strategy.md",
}

_MIASI_TEMPLATE_TARGETS: dict[str, str] = {
    "MiasiAgentRegistry": ".devpilot/miasi/agent_registry.json",
    "MiasiToolRegistry": ".devpilot/miasi/tool_registry.json",
    "MiasiPolicyMatrix": ".devpilot/miasi/policy_matrix.json",
}

_PLACEHOLDER_DEFAULTS: dict[str, str] = {
    "project_idea": "TODO: describir idea inicial validada por el owner",
    "target_user": "TODO: identificar usuario objetivo principal",
    "business_problem": "TODO: describir problema observable y evidencia",
    "expected_outcome": "TODO: definir resultado medible del MVP",
    "vision_statement": "TODO: redactar visión de producto en una frase operacional",
    "primary_value": "TODO: valor principal para el usuario objetivo",
    "differentiator": "local-first, dry-run y evidencia verificable",
    "metric_1": "TODO: métrica de adopción",
    "metric_2": "TODO: métrica de calidad",
    "baseline_1": "TODO: línea base inicial",
    "baseline_2": "TODO: línea base de operación",
    "measurement_1": "TODO: método de medición 1",
    "measurement_2": "TODO: método de medición 2",
    "target_1": "TODO: meta MVP 1",
    "target_2": "TODO: meta MVP 2",
    "early_adopters": "TODO: usuarios piloto",
    "mvp_objective": "TODO: objetivo del MVP verificable",
    "primary_user": "TODO: usuario principal",
    "primary_scenario": "TODO: escenario principal",
    "capability_1": "Captura y consulta local de información mínima",
    "capability_2": "Validación de calidad y trazabilidad básica",
    "user_1": "Operador local",
    "user_2": "Owner del proyecto",
    "deliverable_1": "Documento o flujo local verificable",
    "deliverable_2": "Reporte o checklist local",
    "evidence_1": "Prueba o comando reproducible",
    "evidence_2": "Reporte JSON/Markdown",
    "feature_description": "TODO: describir feature candidata",
    "quality_description": "TODO: definir criterio de calidad mínimo",
    "actor": "Operador local",
    "action": "ejecutar flujo controlado",
    "benefit": "obtener evidencia local reproducible",
    "pass_criterion": "PASS si existe evidencia local verificable",
    "risk": "TODO: riesgo pendiente de análisis",
    "actor_1": "Operador local",
    "actor_2": "Owner del proyecto",
    "need_1": "iniciar proyecto con trazabilidad",
    "need_2": "aprobar avance sin depender de memoria conversacional",
    "permissions_1": "read/write bounded sobre workspace local",
    "permissions_2": "aprobación humana de cambios críticos",
    "risk_1": "sobrescritura accidental",
    "risk_2": "falsa readiness",
    "functional_requirement": "TODO: requisito funcional verificable",
    "acceptance_criterion": "TODO: criterio de aceptación observable",
    "evidence": "TODO: evidencia requerida",
    "data_item": "TODO: dato local protegido",
    "sensitivity": "TODO: sensibilidad del dato",
    "retention": "TODO: política de retención local",
    "redaction": "TODO: regla de redacción",
    "mock_or_rule_based_path": "mock agents / reglas determinísticas",
    "local_model_path": "Ollama o LM Studio mediante ModelAdapter",
    "external_api_path_requiring_approval": "API externa futura con aprobación y budget guard",
    "owner": "Ordóñez",
    "architecture_style": "modular local-first con CLI como entrada inicial",
    "persistence_choice": "archivos locales y SQLite solo cuando aplique",
    "interface_choice": "CLI local primero; API/UI local futuras según backlog",
    "system_name": "Sistema local agent-assisted",
    "users": "Operador local, owner y usuarios piloto",
    "component_1": "Core de dominio",
    "component_2": "Capa de validación y reportes",
    "responsibility_1": "procesar reglas de negocio locales",
    "responsibility_2": "emitir evidencia y gates",
    "input_1": "documentos pre-code",
    "input_2": "fixtures locales",
    "output_1": "CommandResult JSON",
    "output_2": "reporte verificable",
    "config_paths": ".devpilot/, docs/, outputs/",
    "adr_id": "ADR-0001",
    "decision_reason": "mantener local-first, dry-run y bajo costo inicial",
    "asset_1": "documentación de proyecto",
    "asset_2": "estado local y outputs",
    "sensitivity_1": "media",
    "sensitivity_2": "media-alta",
    "threat_1": "drift documental",
    "threat_2": "fuga de secretos por logs o fixtures",
    "control_1": "docs-governance y tests focales",
    "control_2": "SecretGuard y no-secrets policy",
}

_SAFE_PROJECT_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{2,63}$")
_PLACEHOLDER = re.compile(r"{{\s*([A-Za-z0-9_]+)\s*}}")


@dataclass(frozen=True)
class ProjectBootstrapOptions:
    """Options for POST-H-024-C project bootstrap planning/materialization."""

    project_id: str
    project_name: str
    project_type: str = DEFAULT_PROJECT_TYPE
    target_root: str | None = None
    execute: bool = False
    write_report: bool = False
    output_json: str = DEFAULT_BOOTSTRAP_OUTPUT_JSON
    output_markdown: str = DEFAULT_BOOTSTRAP_OUTPUT_MARKDOWN


@dataclass(frozen=True)
class PlannedFile:
    """One bounded file that the bootstrap workflow would create."""

    path: str
    kind: str
    source_template: str | None
    exists: bool
    action: str
    would_write: bool
    content: str

    def to_report_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "kind": self.kind,
            "source_template": self.source_template,
            "exists": self.exists,
            "action": self.action,
            "would_write": self.would_write,
            "content_included": False,
        }


class ProjectBootstrapPlanner:
    """Build and optionally materialize a bounded new-project bootstrap plan.

    POST-H-024-C intentionally implements a dry-run-first bootstrap surface. It
    copies no code, calls no network, does not invoke LLMs and refuses overwrite
    by default. Execute mode is bounded to the configured target workspace and
    is intended for controlled local scaffolding only.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.path_guard = PathGuard(self.root)
        self.secret_guard = SecretGuard()

    def run(self, options: ProjectBootstrapOptions) -> CommandResult:
        findings = self._validate_options(options)
        target_root = self._target_root(options)
        target_rel = _relative(target_root, self.root)
        if not findings:
            findings.extend(self._evaluate_target_root(target_root))
        if findings:
            report = self._build_report(options, target_root, [], findings, mode="execute" if options.execute else "dry-run", report_written=False)
            return CommandResult(
                command="workspace bootstrap",
                ok=False,
                exit_code=exit_code_for_findings(findings, default_ok=False),
                message="Project bootstrap blocked before planning.",
                data={"summary": report["summary"], "report": report},
                findings=findings,
            )

        template_validation = validate_new_project_templates(self.root)
        if not template_validation.ok:
            findings.append(
                Finding(
                    "PROJECT_BOOTSTRAP_TEMPLATES_INVALID",
                    "POST-H-024-B templates must validate before bootstrap can plan a project.",
                    Severity.BLOCK,
                    path="docs/templates/new_project",
                    metadata=template_validation.to_dict(),
                )
            )
            report = self._build_report(options, target_root, [], findings, mode="execute" if options.execute else "dry-run", report_written=False)
            return CommandResult(
                command="workspace bootstrap",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Project bootstrap blocked because templates are invalid.",
                data={"summary": report["summary"], "report": report},
                findings=findings,
            )

        planned_files = self._build_planned_files(options, target_root)
        findings.extend(self._validate_planned_files(planned_files, target_root))

        if options.execute and findings:
            report = self._build_report(options, target_root, planned_files, findings, mode="execute", report_written=False)
            return CommandResult(
                command="workspace bootstrap",
                ok=False,
                exit_code=exit_code_for_findings(findings, default_ok=False),
                message="Project bootstrap execute blocked; no files were written.",
                data={"summary": report["summary"], "report": report},
                findings=findings,
            )

        if options.execute:
            self._materialize(planned_files)
            findings.append(
                Finding(
                    "PROJECT_BOOTSTRAP_EXECUTE_PASS",
                    "Project bootstrap materialized bounded starter files without overwriting existing files.",
                    Severity.INFO,
                    path=target_rel,
                    metadata={"files_written": len(planned_files)},
                )
            )
        else:
            findings.append(
                Finding(
                    "PROJECT_BOOTSTRAP_DRY_RUN_PASS",
                    "Project bootstrap dry-run completed; no workspace files were written.",
                    Severity.INFO,
                    path=target_rel,
                    metadata={"planned_files": len(planned_files)},
                )
            )

        report_written = False
        report = self._build_report(
            options,
            target_root,
            planned_files,
            findings,
            mode="execute" if options.execute else "dry-run",
            report_written=False,
        )
        if options.write_report:
            report_paths = self.write_report(report, output_json=options.output_json, output_markdown=options.output_markdown)
            report_written = True
            report = {**report, "reports": report_paths, "summary": {**report["summary"], "report_written": True, "reports": report_paths}}

        return CommandResult(
            command="workspace bootstrap",
            ok=True,
            exit_code=ExitCode.PASS,
            message=(
                "Project bootstrap execute completed within the target workspace."
                if options.execute
                else "Project bootstrap dry-run completed; no workspace files were written."
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
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        report_paths = {"json": _relative(json_path, self.root), "markdown": _relative(markdown_path, self.root)}
        report_to_write = {
            **report,
            "reports": report_paths,
            "summary": {**report.get("summary", {}), "report_written": True, "reports": report_paths},
        }
        json_path.write_text(json.dumps(report_to_write, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(_render_markdown_report(report_to_write), encoding="utf-8")
        return report_paths

    def _validate_options(self, options: ProjectBootstrapOptions) -> list[Finding]:
        findings: list[Finding] = []
        if not _SAFE_PROJECT_ID.match(options.project_id or ""):
            findings.append(
                Finding(
                    "PROJECT_BOOTSTRAP_PROJECT_ID_INVALID",
                    "project_id must be lowercase and match ^[a-z0-9][a-z0-9_-]{2,63}$.",
                    Severity.BLOCK,
                    metadata={"project_id": options.project_id},
                )
            )
        if not (options.project_name or "").strip():
            findings.append(Finding("PROJECT_BOOTSTRAP_PROJECT_NAME_REQUIRED", "project_name is required.", Severity.BLOCK))
        if (options.project_type or "").strip() != DEFAULT_PROJECT_TYPE:
            findings.append(
                Finding(
                    "PROJECT_BOOTSTRAP_PROJECT_TYPE_UNSUPPORTED",
                    f"POST-H-024-C supports only {DEFAULT_PROJECT_TYPE!r} until template variants are formalized.",
                    Severity.BLOCK,
                    metadata={"project_type": options.project_type},
                )
            )
        for label, flag in (
            ("network_used", False),
            ("external_api_used", False),
            ("remote_execution_used", False),
            ("connector_write_used", False),
            ("plugin_execution_used", False),
        ):
            if flag:
                findings.append(Finding("PROJECT_BOOTSTRAP_NO_GO_FLAG", f"{label} must remain false.", Severity.BLOCK))
        return findings

    def _target_root(self, options: ProjectBootstrapOptions) -> Path:
        raw = options.target_root or f"{DEFAULT_BOOTSTRAP_TARGET_BASE}/{options.project_id}"
        return self._resolve_repo_path(raw)

    def _evaluate_target_root(self, target_root: Path) -> list[Finding]:
        decision = self.path_guard.evaluate(target_root, action="write")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            return [
                Finding(
                    "PROJECT_BOOTSTRAP_TARGET_PATH_BLOCKED",
                    f"Target workspace path is not allowed: {decision.reason}",
                    Severity.BLOCK,
                    path=decision.subject,
                    metadata=decision.metadata,
                )
            ]
        return []

    def _build_planned_files(self, options: ProjectBootstrapOptions, target_root: Path) -> list[PlannedFile]:
        planned: list[PlannedFile] = []
        project_yaml_path = target_root / ".devpilot" / "project.yaml"
        planned.append(
            PlannedFile(
                path=_relative(project_yaml_path, self.root),
                kind="workspace-project-yaml",
                source_template=None,
                exists=project_yaml_path.exists(),
                action="create",
                would_write=not project_yaml_path.exists(),
                content=render_project_yaml(project_id=options.project_id, project_name=options.project_name, project_type=options.project_type),
            )
        )

        context = self._template_context(options)
        for source_template in MARKDOWN_TEMPLATE_PATHS:
            target_rel_inside_project = _DOC_TEMPLATE_TARGETS[source_template]
            target_path = target_root / target_rel_inside_project
            template_text = (self.root / source_template).read_text(encoding="utf-8")
            content = _render_markdown_artifact(template_text, target_rel_inside_project, options, context)
            planned.append(
                PlannedFile(
                    path=_relative(target_path, self.root),
                    kind="markdown-artifact",
                    source_template=source_template,
                    exists=target_path.exists(),
                    action="create",
                    would_write=not target_path.exists(),
                    content=content,
                )
            )

        for schema_id, source_template in MIASI_TEMPLATE_PATHS.items():
            target_rel_inside_project = _MIASI_TEMPLATE_TARGETS[schema_id]
            target_path = target_root / target_rel_inside_project
            payload = json.loads((self.root / source_template).read_text(encoding="utf-8"))
            payload["description"] = f"POST-H-024-C bootstrap starter registry for {options.project_name}. {payload.get('description', '')}".strip()
            content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
            planned.append(
                PlannedFile(
                    path=_relative(target_path, self.root),
                    kind="miasi-json",
                    source_template=source_template,
                    exists=target_path.exists(),
                    action="create",
                    would_write=not target_path.exists(),
                    content=content,
                )
            )
        return planned

    def _template_context(self, options: ProjectBootstrapOptions) -> dict[str, str]:
        return {
            **_PLACEHOLDER_DEFAULTS,
            "project_id": options.project_id,
            "project_name": options.project_name,
            "project_type": options.project_type,
            "updated": _today(),
            "system_name": options.project_name,
            "project_idea": options.project_name,
            "vision_statement": f"{options.project_name} debe validar un MVP local-first con evidencia trazable antes de cualquier integración externa.",
        }

    def _validate_planned_files(self, planned_files: list[PlannedFile], target_root: Path) -> list[Finding]:
        findings: list[Finding] = []
        target_resolved = target_root.resolve()
        seen_paths: set[str] = set()
        for planned in planned_files:
            path = self._resolve_repo_path(planned.path)
            rel = _relative(path, self.root)
            if rel in seen_paths:
                findings.append(Finding("PROJECT_BOOTSTRAP_DUPLICATE_TARGET", "Bootstrap plan contains a duplicate target path.", Severity.BLOCK, path=rel))
            seen_paths.add(rel)
            try:
                path.resolve().relative_to(target_resolved)
            except ValueError:
                findings.append(
                    Finding(
                        "PROJECT_BOOTSTRAP_TARGET_ESCAPE",
                        "Bootstrap planned file escapes the target workspace boundary.",
                        Severity.BLOCK,
                        path=rel,
                        metadata={"target_root": _relative(target_resolved, self.root)},
                    )
                )
            decision = self.path_guard.evaluate(path, action="write")
            if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
                findings.append(
                    Finding(
                        "PROJECT_BOOTSTRAP_FILE_PATH_BLOCKED",
                        f"Planned file path is not writable under current policy: {decision.reason}",
                        Severity.BLOCK,
                        path=rel,
                        metadata=decision.metadata,
                    )
                )
            if planned.exists:
                findings.append(
                    Finding(
                        "PROJECT_BOOTSTRAP_OVERWRITE_BLOCKED",
                        "Bootstrap refuses to overwrite existing files by default.",
                        Severity.BLOCK,
                        path=rel,
                    )
                )
            redaction = self.secret_guard.redact(planned.content)
            if redaction.redactions:
                findings.append(
                    Finding(
                        "PROJECT_BOOTSTRAP_SECRET_RISK_BLOCKED",
                        "SecretGuard detected secret-like content in planned bootstrap output.",
                        Severity.BLOCK,
                        path=rel,
                        metadata={"redactions_total": redaction.redactions},
                    )
                )
        return findings

    def _materialize(self, planned_files: list[PlannedFile]) -> None:
        for planned in planned_files:
            path = self._resolve_repo_path(planned.path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(planned.content, encoding="utf-8")

    def _build_report(
        self,
        options: ProjectBootstrapOptions,
        target_root: Path,
        planned_files: list[PlannedFile],
        findings: list[Finding],
        *,
        mode: str,
        report_written: bool,
    ) -> dict[str, Any]:
        status = "pass" if not any(item.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for item in findings) else "block"
        files_existing_total = sum(1 for item in planned_files if item.exists)
        files_would_write_total = sum(1 for item in planned_files if item.would_write)
        next_commands = [
            "python -m devpilot_core workspace status --json",
            f"python -m devpilot_core workspace bootstrap --project-id {options.project_id} --project-name \"{options.project_name}\" --dry-run --json --write-report",
            "python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --strict --json",
            f"python -m devpilot_core workspace readiness-preview --target-root {_relative(target_root, self.root)} --json --write-report",
            "python -m devpilot_core miasi validate --json",
        ]
        report = {
            "schema_version": "1.0",
            "schema_id": PROJECT_BOOTSTRAP_REPORT_SCHEMA_ID,
            "bootstrap_id": f"project-bootstrap-{options.project_id}",
            "created_by": "POST-H-024-C",
            "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "project": {"project_id": options.project_id, "project_name": options.project_name, "project_type": options.project_type},
            "mode": mode,
            "status": status,
            "target_root": _relative(target_root, self.root),
            "steps": [
                {"step_id": "workspace-plan", "status": "pass" if planned_files else status, "mutations_performed": mode == "execute" and status == "pass"},
                {"step_id": "docs-template-plan", "status": "pass" if planned_files else status, "mutations_performed": mode == "execute" and status == "pass"},
                {"step_id": "miasi-template-plan", "status": "pass" if planned_files else status, "mutations_performed": mode == "execute" and status == "pass"},
                {"step_id": "readiness-preview", "status": "warning", "mutations_performed": False, "message": "Run workspace readiness-preview for POST-H-024-D onboarding validation evidence."},
            ],
            "planned_files": [item.to_report_dict() for item in planned_files],
            "safety": {
                "local_first": True,
                "dry_run_default": True,
                "network_used": False,
                "external_api_used": False,
                "remote_execution_used": False,
                "connector_write_used": False,
                "plugin_execution_used": False,
                "secrets_included": False,
                "source_mutations_performed": False,
                "mutations_performed": mode == "execute" and status == "pass",
                "overwrite_allowed": False,
            },
            "summary": {
                "status": status,
                "mode": mode,
                "target_root": _relative(target_root, self.root),
                "files_total": len(planned_files),
                "files_existing_total": files_existing_total,
                "files_would_write_total": files_would_write_total,
                "mutations_performed": mode == "execute" and status == "pass",
                "source_mutations_performed": False,
                "network_used": False,
                "external_api_used": False,
                "report_written": report_written,
                "next_commands": next_commands,
            },
            "findings": [finding.to_dict() for finding in findings],
            "limitations": [
                "POST-H-024-D provides onboarding readiness preview as a separate read-only command; bootstrap remains plan/materialization only.",
                "POST-H-024-C does not integrate onboarding quality gate; POST-H-024-E owns it.",
                "Bootstrap does not generate production code or call LLM/API providers.",
            ],
        }
        return report

    def _resolve_repo_path(self, value: str | Path) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = self.root / path
        return path.resolve()


def _render_markdown_artifact(template_text: str, target_rel_inside_project: str, options: ProjectBootstrapOptions, context: dict[str, str]) -> str:
    body = _strip_frontmatter(template_text)
    body = _PLACEHOLDER.sub(lambda match: context.get(match.group(1), f"TODO: definir {match.group(1)}"), body)
    doc_id = _doc_id_for_target(options.project_id, target_rel_inside_project)
    title = _title_for_target(options.project_name, target_rel_inside_project)
    frontmatter = f'''---
doc_id: "{doc_id}"
title: "{title}"
status: "draft"
version: "0.1.0"
owner: "Ordóñez"
updated: "{_today()}"
created_by: "POST-H-024-C"
project_id: "{options.project_id}"
project_type: "{options.project_type}"
implementation_status: "bootstrap-draft"
preliminary: true
local_first: true
dry_run: true
no_external_apis_required: true
no_secrets_allowed: true
---
'''
    return frontmatter + "\n" + body.lstrip()


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2]
    return text


def _doc_id_for_target(project_id: str, target_rel_inside_project: str) -> str:
    stem = Path(target_rel_inside_project).stem.replace("_", "-").upper()
    return f"{project_id.upper().replace('-', '_')}-{stem}".replace("_", "-")


def _title_for_target(project_name: str, target_rel_inside_project: str) -> str:
    labels = {
        "docs/00_product/product_vision.md": "Product vision",
        "docs/00_product/mvp_scope.md": "MVP scope",
        "docs/01_requirements/requirements_specification.md": "Requirements specification",
        "docs/02_architecture/architecture_document.md": "Architecture document",
        "docs/03_security/security_threat_model.md": "Security threat model",
        "docs/04_quality/test_strategy.md": "Test strategy",
    }
    return f"{labels.get(target_rel_inside_project, Path(target_rel_inside_project).stem)} — {project_name}"


def _render_markdown_report(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    planned = report.get("planned_files", [])
    lines = [
        "# Project bootstrap report",
        "",
        f"Bootstrap: `{report.get('bootstrap_id')}`",
        f"Status: `{report.get('status')}`",
        f"Mode: `{report.get('mode')}`",
        f"Target root: `{report.get('target_root')}`",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(summary, indent=2, ensure_ascii=False),
        "```",
        "",
        "## Planned files",
        "",
    ]
    for item in planned:
        lines.append(f"- `{item['path']}` — {item['kind']} — exists={item['exists']} — action={item['action']}")
    lines.extend([
        "",
        "## Safety",
        "",
        "```json",
        json.dumps(report.get("safety", {}), indent=2, ensure_ascii=False),
        "```",
        "",
    ])
    return "\n".join(lines)


def _today() -> str:
    return datetime.now(UTC).date().isoformat()


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
