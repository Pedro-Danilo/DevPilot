from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.agents.base import ModelAwareAgent
from devpilot_core.agents.models import AgentMessage, AgentModelCall, AgentRunResult, AgentSuggestion, AgentToolCall
from devpilot_core.cli_models import Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest
from devpilot_core.traceability import TraceabilityEngine


class RequirementsAgent(ModelAwareAgent):
    """Governed mono-agent for requirements review.

    FUNC-SPRINT-55 introduces the first high-level SDLC agents. This agent is
    read-only and evidence-driven: it uses TraceabilityEngine coverage over
    requirements artifacts, converts explicit gaps into actionable findings and
    optionally asks a local/mock model for a redacted summary through
    AgentRuntime v2. It never edits requirements, approves gates or infers hidden
    product semantics.
    """

    agent_id = "requirements.agent"

    def __init__(self, root: Path, policy: PolicyEngine | None = None) -> None:
        super().__init__(root)
        self.policy = policy or PolicyEngine(self.root)

    def run(self, message: AgentMessage) -> AgentRunResult:
        target = message.target or "docs/01_requirements"
        target_rel = _normalize_subject(target, self.root)
        focus = (message.idea or "Revisar cobertura, criterios y evidencia de requisitos.").strip()
        tool_calls: list[AgentToolCall] = []
        findings: list[Finding] = []
        suggestions: list[AgentSuggestion] = []
        model_calls: list[AgentModelCall] = []

        if not message.dry_run:
            findings.append(
                Finding(
                    "REQUIREMENTS_AGENT_EXECUTION_BLOCKED",
                    "RequirementsAgent is read-only in FUNC-SPRINT-55; document edits require a future draft/write workflow and approval.",
                    Severity.BLOCK,
                    path=target_rel,
                    metadata={"mutations_performed": False, "approval_required_for_write": True},
                )
            )
            return AgentRunResult(
                self.agent_id,
                "RequirementsAgent",
                False,
                "RequirementsAgent blocked non-dry-run execution.",
                message.dry_run,
                findings=findings,
                artifacts={"target": target_rel, "read_only": True, "mutations_performed": False},
                metadata=_metadata(False, "blocked-non-dry-run"),
            )

        read_call = self._policy_tool_call("artifact.read", "read", target_rel, dry_run=True)
        coverage_call = self._policy_tool_call("traceability.coverage", "read", target_rel, dry_run=True)
        tool_calls.extend([read_call, coverage_call])
        if not read_call.allowed or not coverage_call.allowed:
            findings.extend(read_call.findings)
            findings.extend(coverage_call.findings)
            return AgentRunResult(
                self.agent_id,
                "RequirementsAgent",
                False,
                "RequirementsAgent blocked by policy before requirements review.",
                message.dry_run,
                tool_calls=tool_calls,
                findings=findings,
                artifacts={"target": target_rel, "read_only": True, "mutations_performed": False},
                metadata=_metadata(False, "blocked-by-policy"),
            )

        coverage = TraceabilityEngine(self.root).coverage(targets=[target_rel])
        findings.extend(coverage.findings)
        summary = dict((coverage.data or {}).get("summary") or {})
        derived = _requirements_findings(summary, target_rel)
        findings.extend(derived)
        suggestions.extend(_requirements_suggestions(summary, target_rel, focus))
        components = [_component_summary("traceability.coverage", coverage, target_rel)]
        summary.update(
            {
                "target": target_rel,
                "focus": focus,
                "derived_findings_total": len(derived),
                "read_only": True,
                "dry_run": True,
                "mutations_performed": False,
                "external_api_used": False,
                "preliminary": True,
            }
        )

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]
        failing = [finding for finding in findings if finding.severity == Severity.FAIL]
        ok = coverage.ok and not blocking and not failing

        if ok:
            model_call, model_findings, model_suggestion = self._run_model_generate(
                message,
                default_prompt_id="requirements.agent",
                default_inputs={
                    "requirements_goal": focus,
                    "requirements_signals": _requirements_signals_for_prompt(summary, derived),
                },
                suggestion_title="Resumen model-aware de revisión de requisitos",
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
            "RequirementsAgent",
            ok,
            "RequirementsAgent completed governed requirements review." if ok else "RequirementsAgent completed with blocking/failing findings.",
            message.dry_run,
            tool_calls=tool_calls,
            model_calls=model_calls,
            findings=findings,
            suggestions=suggestions,
            artifacts={
                "target": target_rel,
                "summary": summary,
                "components": components,
                "coverage": dict((coverage.data or {}).get("coverage") or {}),
                "derived_findings": [finding.to_dict() for finding in derived],
                "read_only": True,
                "mutations_performed": False,
                "external_api_used": False,
                "raw_prompt_stored": False,
                "raw_output_stored": False,
            },
            metadata={
                **_metadata(bool(model_calls), "requirements-review"),
                "mode": "requirements+model-aware" if model_calls else "requirements",
                "llm_used": any(call.provider != "mock" for call in model_calls),
                "external_api_used": False,
            },
        )

    def _policy_tool_call(self, tool_id: str, action: str, subject: str | Path | None, *, text: str | None = None, dry_run: bool = True) -> AgentToolCall:
        subject_text = _normalize_subject(subject, self.root) if subject else None
        result = self.policy.evaluate(
            PolicyRequest(
                action=action,
                path=subject_text,
                text=text,
                dry_run=dry_run,
                tool_id=tool_id,
                subject=subject_text,
                metadata={"agent_id": self.agent_id, "sprint": "FUNC-SPRINT-55", "read_only": True},
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


def _requirements_findings(summary: dict[str, Any], target: str) -> list[Finding]:
    findings: list[Finding] = []
    missing_ac = int(summary.get("requirements_without_acceptance_criteria") or 0)
    missing_tests = int(summary.get("requirements_without_test_or_eval_evidence") or 0)
    gaps_total = int(summary.get("gaps_total") or 0)
    if missing_ac:
        findings.append(
            Finding(
                "REQUIREMENTS_AGENT_REQUIREMENTS_WITHOUT_ACCEPTANCE_CRITERIA",
                f"RequirementsAgent detected {missing_ac} requirement(s) without explicit acceptance criteria.",
                Severity.WARNING,
                path=target,
                metadata={"requirements_without_acceptance_criteria": missing_ac, "source": "TraceabilityEngine"},
            )
        )
    if missing_tests:
        findings.append(
            Finding(
                "REQUIREMENTS_AGENT_REQUIREMENTS_WITHOUT_TEST_EVIDENCE",
                f"RequirementsAgent detected {missing_tests} requirement(s) without explicit test/eval evidence.",
                Severity.WARNING,
                path=target,
                metadata={"requirements_without_test_or_eval_evidence": missing_tests, "source": "TraceabilityEngine"},
            )
        )
    if gaps_total and not (missing_ac or missing_tests):
        findings.append(
            Finding(
                "REQUIREMENTS_AGENT_TRACEABILITY_GAPS_PRESENT",
                f"RequirementsAgent detected {gaps_total} non-blocking traceability gap(s).",
                Severity.WARNING,
                path=target,
                metadata={"gaps_total": gaps_total, "source": "TraceabilityEngine"},
            )
        )
    if not findings:
        findings.append(
            Finding(
                "REQUIREMENTS_AGENT_PASS",
                "RequirementsAgent review completed without derived requirements coverage findings.",
                Severity.INFO,
                path=target,
            )
        )
    return findings


def _requirements_suggestions(summary: dict[str, Any], target: str, focus: str) -> list[AgentSuggestion]:
    missing_ac = int(summary.get("requirements_without_acceptance_criteria") or 0)
    missing_tests = int(summary.get("requirements_without_test_or_eval_evidence") or 0)
    suggestions = [
        AgentSuggestion(
            "Revisión de requisitos gobernada",
            f"Objetivo: {focus}. Requisitos detectados: {summary.get('requirements_total', 0)}; gaps: {summary.get('gaps_total', 0)}.",
            target=target,
            severity="info" if not (missing_ac or missing_tests) else "warning",
        )
    ]
    if missing_ac:
        suggestions.append(AgentSuggestion("Cerrar criterios de aceptación", "Agregar o vincular AC-* explícitos para cada requisito sin criterio.", target=target, severity="warning"))
    if missing_tests:
        suggestions.append(AgentSuggestion("Cerrar evidencia de pruebas", "Agregar TEST-* o casos eval que cubran los requisitos sin evidencia.", target=target, severity="warning"))
    suggestions.append(AgentSuggestion("Mantener modo read-only", "El agente no edita documentos; las correcciones deben entrar por draft/PR/patch revisado.", target=target, severity="info", metadata={"mutations_performed": False}))
    return suggestions


def _requirements_signals_for_prompt(summary: dict[str, Any], findings: list[Finding]) -> str:
    payload = {
        "summary": {k: summary.get(k) for k in sorted(summary) if k not in {"raw", "content"}},
        "derived_finding_ids": [finding.id for finding in findings[:20]],
        "raw_content_stored": False,
        "mutations_performed": False,
    }
    return str(payload)[:12000]


def _component_summary(source: str, result: Any, subject: str) -> dict[str, Any]:
    summary = dict((getattr(result, "data", {}) or {}).get("summary") or {})
    result_findings = list(getattr(result, "findings", []) or [])
    return {
        "source": source,
        "command": getattr(result, "command", source),
        "subject": subject,
        "ok": bool(getattr(result, "ok", False)),
        "exit_code": int(getattr(result, "exit_code", 3)),
        "findings_total": len(result_findings),
        "blocking_findings": sum(1 for finding in result_findings if finding.severity == Severity.BLOCK),
        "failing_findings": sum(1 for finding in result_findings if finding.severity in {Severity.FAIL, Severity.ERROR}),
        "warnings_total": sum(1 for finding in result_findings if finding.severity == Severity.WARNING),
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
    resolved = candidate.resolve()
    try:
        return str(resolved.relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(subject).replace("\\", "/")
