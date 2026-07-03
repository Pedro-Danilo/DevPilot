from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.onboarding.templates import TemplateValidationResult, validate_new_project_templates
from devpilot_core.workspace import ProjectBootstrapOptions, ProjectBootstrapPlanner

POST_H_024_E_CREATED_BY = "POST-H-024-E"
ONBOARDING_BOOTSTRAP_READY_SUBGATE = "onboarding-bootstrap-ready"
DEFAULT_ONBOARDING_PILOT_FIXTURE = "tests/fixtures/onboarding/post_h_024_e_pilot_project.json"
_MIN_PLANNED_FILES = 10
_BLOCKING_SEVERITIES = {Severity.FAIL, Severity.BLOCK, Severity.ERROR}


@dataclass(frozen=True)
class OnboardingBootstrapReadyGateOptions:
    """Options for the POST-H-024-E onboarding bootstrap quality subgate.

    The subgate must stay local-first and dry-run. The fixture is a versioned
    pilot-project contract used to prove that the bootstrap workflow can build a
    bounded plan from templates without materializing runtime workspace files.
    """

    fixture_path: str = DEFAULT_ONBOARDING_PILOT_FIXTURE
    min_planned_files: int = _MIN_PLANNED_FILES


class OnboardingBootstrapReadyGate:
    """Validate POST-H-024 onboarding bootstrap readiness as a quality subgate.

    The gate composes POST-H-024-B/C/D primitives instead of duplicating their
    internals: it validates new-project templates, loads the pilot fixture and
    executes ``ProjectBootstrapPlanner`` in dry-run mode. It never writes source
    files, never executes external providers and treats missing templates as a
    blocking condition.
    """

    def __init__(self, root: Path, options: OnboardingBootstrapReadyGateOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or OnboardingBootstrapReadyGateOptions()

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        fixture, fixture_findings = self._load_fixture()
        findings.extend(fixture_findings)

        template_validation = validate_new_project_templates(self.root)
        findings.extend(self._template_findings(template_validation))

        bootstrap_result: CommandResult | None = None
        if fixture and template_validation.ok and not any(item.severity in _BLOCKING_SEVERITIES for item in findings):
            bootstrap_result = ProjectBootstrapPlanner(self.root).run(
                ProjectBootstrapOptions(
                    project_id=str(fixture["project_id"]),
                    project_name=str(fixture["project_name"]),
                    project_type=str(fixture.get("project_type") or "agent-assisted-sdlc"),
                    target_root=str(fixture["target_root"]),
                    execute=False,
                    write_report=False,
                )
            )
            findings.extend(self._bootstrap_findings(bootstrap_result, fixture))

        blocking = [item for item in findings if item.severity in _BLOCKING_SEVERITIES]
        ok = fixture is not None and template_validation.ok and bootstrap_result is not None and bootstrap_result.ok and not blocking
        summary = self._summary(
            fixture=fixture,
            template_validation=template_validation,
            bootstrap_result=bootstrap_result,
            blocking_total=len(blocking),
        )
        return CommandResult(
            command=f"quality {ONBOARDING_BOOTSTRAP_READY_SUBGATE}",
            ok=ok,
            exit_code=ExitCode.PASS if ok else exit_code_for_findings(blocking, default_ok=False),
            message="Onboarding bootstrap quality subgate passed." if ok else "Onboarding bootstrap quality subgate blocked.",
            data={"summary": summary, "fixture": fixture or {}},
            findings=findings
            or [
                Finding(
                    "ONBOARDING_BOOTSTRAP_READY_PASS",
                    "Pilot fixture, templates and bootstrap dry-run plan are ready for onboarding quality gate use.",
                    Severity.INFO,
                    metadata=summary,
                )
            ],
        )

    def _load_fixture(self) -> tuple[dict[str, Any] | None, list[Finding]]:
        fixture_path = self.root / self.options.fixture_path
        if not fixture_path.is_file():
            return None, [
                Finding(
                    "ONBOARDING_BOOTSTRAP_READY_FIXTURE_MISSING",
                    "POST-H-024-E pilot project fixture is missing.",
                    Severity.BLOCK,
                    path=self.options.fixture_path,
                    metadata={"created_by": POST_H_024_E_CREATED_BY},
                )
            ]
        try:
            payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return None, [
                Finding(
                    "ONBOARDING_BOOTSTRAP_READY_FIXTURE_JSON_INVALID",
                    "POST-H-024-E pilot project fixture is not valid JSON.",
                    Severity.ERROR,
                    path=self.options.fixture_path,
                    metadata={"error": str(exc), "created_by": POST_H_024_E_CREATED_BY},
                )
            ]
        findings: list[Finding] = []
        required = ("fixture_id", "project_id", "project_name", "project_type", "target_root")
        for key in required:
            if not str(payload.get(key) or "").strip():
                findings.append(
                    Finding(
                        "ONBOARDING_BOOTSTRAP_READY_FIXTURE_FIELD_MISSING",
                        "POST-H-024-E pilot project fixture is missing a required field.",
                        Severity.BLOCK,
                        path=self.options.fixture_path,
                        metadata={"field": key, "created_by": POST_H_024_E_CREATED_BY},
                    )
                )
        expected_mode = payload.get("expected_mode")
        if expected_mode != "dry-run":
            findings.append(
                Finding(
                    "ONBOARDING_BOOTSTRAP_READY_FIXTURE_MODE_INVALID",
                    "Pilot fixture must require dry-run mode only.",
                    Severity.BLOCK,
                    path=self.options.fixture_path,
                    metadata={"expected_mode": expected_mode, "created_by": POST_H_024_E_CREATED_BY},
                )
            )
        target_root = str(payload.get("target_root") or "")
        if not target_root.replace("\\", "/").startswith("outputs/"):
            findings.append(
                Finding(
                    "ONBOARDING_BOOTSTRAP_READY_FIXTURE_TARGET_NOT_RUNTIME",
                    "Pilot fixture target_root must stay under outputs/ so no runtime artifacts become versionable.",
                    Severity.BLOCK,
                    path=self.options.fixture_path,
                    metadata={"target_root": target_root, "created_by": POST_H_024_E_CREATED_BY},
                )
            )
        no_go = payload.get("no_go") if isinstance(payload.get("no_go"), dict) else {}
        for flag in ("network_used", "external_api_used", "remote_execution_used", "connector_write_used", "plugin_execution_used"):
            if no_go.get(flag) is not False:
                findings.append(
                    Finding(
                        "ONBOARDING_BOOTSTRAP_READY_FIXTURE_NO_GO_INVALID",
                        "Pilot fixture must pin all no-go capability flags to false.",
                        Severity.BLOCK,
                        path=self.options.fixture_path,
                        metadata={"flag": flag, "actual": no_go.get(flag), "created_by": POST_H_024_E_CREATED_BY},
                    )
                )
        if findings:
            return payload, findings
        return payload, []

    def _template_findings(self, validation: TemplateValidationResult) -> list[Finding]:
        if validation.ok:
            return []
        return [
            Finding(
                "ONBOARDING_BOOTSTRAP_READY_TEMPLATES_INVALID",
                "New-project templates are missing or invalid; onboarding bootstrap quality gate cannot pass.",
                Severity.BLOCK,
                path="docs/templates/new_project",
                metadata={"errors": list(validation.errors), "checked_paths": list(validation.checked_paths), "created_by": POST_H_024_E_CREATED_BY},
            )
        ]

    def _bootstrap_findings(self, bootstrap_result: CommandResult, fixture: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        findings.extend(
            Finding(
                f"ONBOARDING_BOOTSTRAP_READY_BOOTSTRAP_{finding.id}",
                finding.message,
                finding.severity,
                path=finding.path,
                metadata={"source_command": bootstrap_result.command, **(finding.metadata or {})},
            )
            for finding in bootstrap_result.findings
            if finding.severity in _BLOCKING_SEVERITIES
        )
        summary = dict((bootstrap_result.data or {}).get("summary") or {})
        report = dict((bootstrap_result.data or {}).get("report") or {})
        safety = dict(report.get("safety") or {})
        planned_files = list(report.get("planned_files") or [])
        expected_min = int(fixture.get("expected_planned_files_min") or self.options.min_planned_files)
        if not bootstrap_result.ok:
            findings.append(
                Finding(
                    "ONBOARDING_BOOTSTRAP_READY_DRY_RUN_BLOCKED",
                    "Bootstrap dry-run did not complete successfully for the pilot fixture.",
                    Severity.BLOCK,
                    path=str(fixture.get("target_root") or ""),
                    metadata={"exit_code": int(bootstrap_result.exit_code), "message": bootstrap_result.message},
                )
            )
        if summary.get("mode") != "dry-run":
            findings.append(Finding("ONBOARDING_BOOTSTRAP_READY_NOT_DRY_RUN", "Pilot bootstrap must run in dry-run mode.", Severity.BLOCK, metadata={"mode": summary.get("mode")}))
        if summary.get("mutations_performed") is not False or safety.get("mutations_performed") is not False:
            findings.append(Finding("ONBOARDING_BOOTSTRAP_READY_MUTATION_BLOCK", "Pilot bootstrap dry-run must not perform mutations.", Severity.BLOCK, metadata={"summary": summary, "safety": safety}))
        if summary.get("source_mutations_performed") is not False or safety.get("source_mutations_performed") is not False:
            findings.append(Finding("ONBOARDING_BOOTSTRAP_READY_SOURCE_MUTATION_BLOCK", "Pilot bootstrap must not mutate source files.", Severity.BLOCK, metadata={"summary": summary, "safety": safety}))
        if summary.get("network_used") is not False or summary.get("external_api_used") is not False:
            findings.append(Finding("ONBOARDING_BOOTSTRAP_READY_REMOTE_DEPENDENCY_BLOCK", "Pilot bootstrap must not use network or external APIs.", Severity.BLOCK, metadata={"summary": summary}))
        if safety.get("remote_execution_used") is not False or safety.get("connector_write_used") is not False or safety.get("plugin_execution_used") is not False:
            findings.append(Finding("ONBOARDING_BOOTSTRAP_READY_FORBIDDEN_CAPABILITY_BLOCK", "Pilot bootstrap must not enable remote execution, connector write or plugin execution.", Severity.BLOCK, metadata={"safety": safety}))
        if int(summary.get("files_total") or 0) < expected_min or len(planned_files) < expected_min:
            findings.append(
                Finding(
                    "ONBOARDING_BOOTSTRAP_READY_PLAN_TOO_SMALL",
                    "Bootstrap dry-run plan does not include the minimum expected starter artifacts.",
                    Severity.BLOCK,
                    metadata={"files_total": summary.get("files_total"), "planned_files_total": len(planned_files), "expected_min": expected_min},
                )
            )
        target_root = str(fixture.get("target_root") or "").replace("\\", "/")
        for planned in planned_files:
            path = str(planned.get("path") or "").replace("\\", "/")
            if target_root and not path.startswith(target_root.rstrip("/") + "/"):
                findings.append(
                    Finding(
                        "ONBOARDING_BOOTSTRAP_READY_PLAN_ESCAPE",
                        "Bootstrap dry-run planned a file outside the fixture target_root.",
                        Severity.BLOCK,
                        path=path,
                        metadata={"target_root": target_root},
                    )
                )
        return findings

    def _summary(
        self,
        *,
        fixture: dict[str, Any] | None,
        template_validation: TemplateValidationResult,
        bootstrap_result: CommandResult | None,
        blocking_total: int,
    ) -> dict[str, Any]:
        bootstrap_summary = dict((bootstrap_result.data or {}).get("summary") or {}) if bootstrap_result else {}
        return {
            "created_by": POST_H_024_E_CREATED_BY,
            "status": "implemented-initial",
            "quality_gate_subgate": ONBOARDING_BOOTSTRAP_READY_SUBGATE,
            "onboarding_bootstrap_ready": bool(fixture and template_validation.ok and bootstrap_result and bootstrap_result.ok and blocking_total == 0),
            "fixture_path": self.options.fixture_path,
            "fixture_loaded": fixture is not None,
            "fixture_id": fixture.get("fixture_id") if fixture else None,
            "project_id": fixture.get("project_id") if fixture else None,
            "target_root": fixture.get("target_root") if fixture else None,
            "templates_ok": template_validation.ok,
            "templates_checked_total": len(template_validation.checked_paths),
            "template_errors_total": len(template_validation.errors),
            "bootstrap_dry_run_ok": bool(bootstrap_result and bootstrap_result.ok),
            "bootstrap_mode": bootstrap_summary.get("mode"),
            "planned_files_total": int(bootstrap_summary.get("files_total") or 0),
            "files_would_write_total": int(bootstrap_summary.get("files_would_write_total") or 0),
            "blocking_findings_total": blocking_total,
            "local_first": True,
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "remote_execution_used": False,
            "connector_write_used": False,
            "plugin_execution_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "runtime_artifacts_versionable": False,
            "reports_written": False,
            "preliminary": True,
        }
