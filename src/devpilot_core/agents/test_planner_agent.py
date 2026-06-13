from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.agents.base import ModelAwareAgent
from devpilot_core.agents.models import AgentMessage, AgentModelCall, AgentRunResult, AgentSuggestion, AgentToolCall
from devpilot_core.cli_models import CommandResult, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest
from devpilot_core.testing import TestsRunTool
from devpilot_core.traceability import TraceabilityEngine


class TestPlannerAgent(ModelAwareAgent):
    """Governed mono-agent for traceability-aware test planning.

    FUNC-SPRINT-54 creates a plan-only test planning agent. It can inspect
    traceability coverage, list fixed tests.run profiles and recommend
    verification commands, but it does not execute pytest or arbitrary commands
    unless a future approval-gated flow explicitly does so.
    """

    agent_id = "testplanner.agent"

    def __init__(self, root: Path, policy: PolicyEngine | None = None) -> None:
        super().__init__(root)
        self.policy = policy or PolicyEngine(self.root)

    def run(self, message: AgentMessage) -> AgentRunResult:
        target = message.target or "docs/01_requirements"
        target_rel = _normalize_subject(target, self.root)
        focus = (message.idea or "Planificar pruebas mínimas y trazables para el target indicado.").strip()
        tool_calls: list[AgentToolCall] = []
        findings: list[Finding] = []
        suggestions: list[AgentSuggestion] = []
        model_calls: list[AgentModelCall] = []

        if not message.dry_run:
            execution_call = self._policy_tool_call("tests.run", "execute", "smoke", dry_run=False)
            tool_calls.append(execution_call)
            findings.extend(execution_call.findings)
            findings.append(
                Finding(
                    "TEST_PLANNER_EXECUTION_BLOCKED",
                    "TestPlannerAgent is plan-only in FUNC-SPRINT-54; tests.run execution requires explicit scoped approval in a future workflow.",
                    Severity.BLOCK,
                    metadata={"tests_run_executed": False, "arbitrary_commands_allowed": False},
                )
            )
            return AgentRunResult(
                self.agent_id,
                "TestPlannerAgent",
                False,
                "TestPlannerAgent blocked non-dry-run test execution.",
                message.dry_run,
                tool_calls=tool_calls,
                findings=findings,
                artifacts={"target": target_rel, "plan_only": True, "tests_run_executed": False, "mutations_performed": False},
                metadata=_metadata(False, "blocked-non-dry-run"),
            )

        read_call = self._policy_tool_call("artifact.read", "read", target_rel, dry_run=True)
        trace_call = self._policy_tool_call("traceability.coverage", "read", target_rel, dry_run=True)
        tests_profile_call = _deferred_tool_call("tests.run", "plan", "smoke")
        tool_calls.extend([read_call, trace_call, tests_profile_call])
        for call in tool_calls:
            if not call.allowed:
                findings.extend(call.findings)
        if not read_call.allowed or not trace_call.allowed:
            return AgentRunResult(
                self.agent_id,
                "TestPlannerAgent",
                False,
                "TestPlannerAgent blocked by policy before test planning.",
                message.dry_run,
                tool_calls=tool_calls,
                findings=findings,
                artifacts={"target": target_rel, "plan_only": True, "tests_run_executed": False, "mutations_performed": False},
                metadata=_metadata(False, "blocked-by-policy"),
            )

        coverage = TraceabilityEngine(self.root).coverage(targets=[target_rel])
        profiles = TestsRunTool(self.root).list_profiles()
        findings.extend(coverage.findings)
        summary = dict((coverage.data or {}).get("summary") or {})
        profile_summary = dict((profiles.data or {}).get("summary") or {})
        plan = _build_test_plan(target_rel, summary, profiles.data or {})
        summary.update(
            {
                "target": target_rel,
                "focus": focus,
                "plan_items_total": len(plan),
                "dry_run": True,
                "plan_only": True,
                "tests_run_profiles_total": profile_summary.get("profiles_total", 0),
                "tests_run_executed": False,
                "arbitrary_commands_allowed": False,
                "mutations_performed": False,
                "external_api_used": False,
                "preliminary": True,
            }
        )
        suggestions.extend(_test_planner_suggestions(summary, plan, target_rel))
        components = [_component_summary("traceability.coverage", coverage, target_rel), _component_summary("tests.profiles", profiles, "tests.run")]

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]
        failing = [finding for finding in findings if finding.severity == Severity.FAIL]
        ok = coverage.ok and profiles.ok and not blocking and not failing

        if ok:
            model_call, model_findings, model_suggestion = self._run_model_generate(
                message,
                default_prompt_id="test.planner.agent",
                default_inputs={
                    "test_goal": focus,
                    "traceability_signals": _test_planner_signals_for_prompt(summary, plan, coverage),
                },
                suggestion_title="Resumen model-aware de plan de pruebas",
                suggestion_target=target_rel,
            )
            if model_call is not None:
                model_calls.append(model_call)
            if model_findings:
                findings.extend(model_findings)
                blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]
                failing = [finding for finding in findings if finding.severity == Severity.FAIL]
                ok = not blocking and not failing
            if model_suggestion is not None:
                suggestions.append(model_suggestion)

        return AgentRunResult(
            self.agent_id,
            "TestPlannerAgent",
            ok,
            "TestPlannerAgent generated a governed traceability-aware test plan." if ok else "TestPlannerAgent generated a plan with blocking/failing findings.",
            message.dry_run,
            tool_calls=tool_calls,
            model_calls=model_calls,
            findings=findings,
            suggestions=suggestions,
            artifacts={
                "target": target_rel,
                "summary": summary,
                "components": components,
                "test_plan": plan,
                "coverage": dict((coverage.data or {}).get("coverage") or {}),
                "test_profiles": (profiles.data or {}).get("profile_registry") or (profiles.data or {}).get("profiles") or {},
                "plan_only": True,
                "tests_run_executed": False,
                "arbitrary_commands_allowed": False,
                "mutations_performed": False,
                "external_api_used": False,
                "raw_prompt_stored": False,
                "raw_output_stored": False,
            },
            metadata={
                **_metadata(bool(model_calls), "test-planner"),
                "mode": "test-planner+model-aware" if model_calls else "test-planner",
                "llm_used": any(call.provider != "mock" for call in model_calls),
                "plan_only": True,
                "tests_run_executed": False,
                "external_api_used": False,
            },
        )

    def _policy_tool_call(self, tool_id: str, action: str, subject: str | Path | None, *, text: str | None = None, dry_run: bool = True) -> AgentToolCall:
        subject_text = _normalize_subject(subject, self.root) if subject and str(subject) != "smoke" else (str(subject) if subject else None)
        result = self.policy.evaluate(
            PolicyRequest(
                action=action,
                path=subject_text if subject_text and subject_text != "smoke" else None,
                text=text,
                dry_run=dry_run,
                tool_id=tool_id,
                subject=subject_text,
                metadata={"agent_id": self.agent_id, "sprint": "FUNC-SPRINT-54", "plan_only": True},
            )
        )
        return AgentToolCall(
            tool_id=tool_id,
            action=action,
            subject=subject_text,
            allowed=result.ok,
            dry_run=dry_run,
            policy_exit_code=int(result.exit_code),
            findings=result.findings,
            metadata={"policy_summary": result.data.get("summary", {})},
        )


def _deferred_tool_call(tool_id: str, action: str, subject: str) -> AgentToolCall:
    return AgentToolCall(
        tool_id=tool_id,
        action=action,
        subject=subject,
        allowed=True,
        dry_run=True,
        policy_exit_code=0,
        findings=[
            Finding(
                "AGENT_TOOL_EXECUTION_DEFERRED",
                "Tool capability was declared for planning only; no subprocess execution was performed by the agent.",
                Severity.INFO,
                metadata={"tool_id": tool_id, "plan_only": True, "executed": False},
            )
        ],
        metadata={"execution_deferred": True, "plan_only": True, "policy_summary": {"allowed": True, "approval_required_for_execution": True}},
    )


def _build_test_plan(target: str, summary: dict[str, Any], profiles_data: dict[str, Any]) -> list[dict[str, Any]]:
    gaps_total = int(summary.get("gaps_total") or 0)
    requirements_total = int(summary.get("requirements_total") or 0)
    profiles = []
    registry = profiles_data.get("profile_registry") if isinstance(profiles_data, dict) else None
    if isinstance(registry, dict):
        profiles = [item.get("profile_id") for item in registry.get("profiles", []) if isinstance(item, dict)]
    if not profiles and isinstance(profiles_data, dict):
        profiles = [item.get("profile_id") for item in profiles_data.get("profiles", []) if isinstance(item, dict)]
    profiles = [str(item) for item in profiles if item]
    return [
        {
            "step_id": "TP-001",
            "title": "Mapear requisitos y criterios de aceptación explícitos",
            "target": target,
            "rationale": f"Requisitos detectados: {requirements_total}; gaps: {gaps_total}.",
            "recommended_profile": "smoke" if "smoke" in profiles else (profiles[0] if profiles else "manual"),
            "execute_now": False,
        },
        {
            "step_id": "TP-002",
            "title": "Cubrir gaps de trazabilidad con pruebas o evals",
            "target": target,
            "rationale": "Priorizar requisitos sin evidencia test/eval y documentar IDs TEST-* o casos eval asociados.",
            "recommended_profile": "unit" if "unit" in profiles else "manual",
            "execute_now": False,
        },
        {
            "step_id": "TP-003",
            "title": "Ejecutar tests.run solo con aprobación futura",
            "target": "tests.run",
            "rationale": "tests.run es una capacidad controlada; el agente solo propone perfiles, no ejecuta comandos arbitrarios.",
            "recommended_profile": "all" if "all" in profiles else (profiles[-1] if profiles else "manual"),
            "execute_now": False,
        },
    ]


def _test_planner_suggestions(summary: dict[str, Any], plan: list[dict[str, Any]], target: str) -> list[AgentSuggestion]:
    gaps_total = int(summary.get("gaps_total") or 0)
    suggestions = [
        AgentSuggestion(
            "Plan de pruebas trazable generado",
            f"Se generaron {len(plan)} pasos plan-only; tests.run no fue ejecutado.",
            target=target,
            severity="info",
            metadata={"plan_only": True, "tests_run_executed": False},
        )
    ]
    if gaps_total:
        suggestions.append(
            AgentSuggestion(
                "Prioridad alta: cerrar gaps de trazabilidad",
                f"TraceabilityEngine reporta {gaps_total} gaps; asociar pruebas/evals antes de cierre industrial.",
                target=target,
                severity="warning",
            )
        )
    else:
        suggestions.append(
            AgentSuggestion(
                "Cobertura trazable sin gaps detectados",
                "La evidencia explícita no reporta gaps; mantener el plan como checklist de regresión.",
                target=target,
                severity="info",
            )
        )
    suggestions.append(
        AgentSuggestion(
            "No ejecutar pruebas arbitrarias desde el agente",
            "Usar solamente perfiles tests.run declarados y aprobación explícita cuando se habilite ejecución futura.",
            target="tests.run",
            severity="info",
            metadata={"arbitrary_commands_allowed": False},
        )
    )
    return suggestions


def _test_planner_signals_for_prompt(summary: dict[str, Any], plan: list[dict[str, Any]], coverage: CommandResult) -> str:
    payload = {
        "summary": {k: summary.get(k) for k in sorted(summary)},
        "plan": plan,
        "finding_ids": [finding.id for finding in coverage.findings[:20]],
        "raw_documents_stored": False,
        "tests_run_executed": False,
        "mutations_performed": False,
    }
    return str(payload)[:12000]


def _component_summary(source: str, result: CommandResult, subject: str) -> dict[str, Any]:
    summary = dict((result.data or {}).get("summary") or {})
    return {
        "source": source,
        "command": result.command,
        "subject": subject,
        "ok": result.ok,
        "exit_code": int(result.exit_code),
        "findings_total": len(result.findings),
        "blocking_findings": sum(1 for finding in result.findings if finding.severity == Severity.BLOCK),
        "failing_findings": sum(1 for finding in result.findings if finding.severity in {Severity.FAIL, Severity.ERROR}),
        "warnings_total": sum(1 for finding in result.findings if finding.severity == Severity.WARNING),
        "dry_run": bool(summary.get("dry_run", True)),
        "mutations_performed": False,
    }


def _metadata(model_runtime_enabled: bool, mode: str) -> dict[str, Any]:
    return {
        "miasi_status": "implemented-initial",
        "max_autonomy": "A3",
        "runtime_version": "v2-model-aware",
        "model_runtime_enabled": model_runtime_enabled,
        "monoagent": True,
        "handoffs_enabled": False,
        "mutations_performed": False,
        "network_used": False,
        "external_api_used": False,
        "preliminary": True,
        "mode": mode,
    }


def _normalize_subject(subject: str | Path | None, root: Path) -> str:
    if subject is None:
        return "."
    candidate = Path(str(subject))
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        return str(candidate.resolve().relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(candidate).replace("\\", "/")
