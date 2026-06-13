from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.agents.base import ModelAwareAgent
from devpilot_core.agents.models import AgentMessage, AgentModelCall, AgentRunResult, AgentSuggestion, AgentToolCall
from devpilot_core.cli_models import CommandResult, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest
from devpilot_core.review import CodeReviewEngine


class CodeReviewAgent(ModelAwareAgent):
    """Governed mono-agent for deterministic code review.

    FUNC-SPRINT-53 wraps the existing CodeReviewEngine with AgentRuntime v2,
    MIASI policy checks, structured suggestions and optional model-aware
    explanation. The agent is read-only, dry-run by contract and never modifies
    source files or executes tests.
    """

    agent_id = "code.review"

    def __init__(self, root: Path, policy: PolicyEngine | None = None) -> None:
        super().__init__(root)
        self.policy = policy or PolicyEngine(self.root)

    def run(self, message: AgentMessage) -> AgentRunResult:
        target = message.target or "."
        target_rel = _normalize_subject(target, self.root)
        tool_calls: list[AgentToolCall] = []
        findings: list[Finding] = []
        suggestions: list[AgentSuggestion] = []
        model_calls: list[AgentModelCall] = []

        review_call = self._policy_tool_call("code.review", "read", target_rel, dry_run=message.dry_run)
        tool_calls.append(review_call)
        if not review_call.allowed:
            findings.extend(review_call.findings)
            return AgentRunResult(
                self.agent_id,
                "CodeReviewAgent",
                False,
                "CodeReviewAgent blocked by policy before code review.",
                message.dry_run,
                tool_calls=tool_calls,
                findings=findings,
                artifacts={"target": target_rel, "mutations_performed": False},
                metadata=_metadata(False, "blocked-by-policy"),
            )

        result = CodeReviewEngine(self.root).review(target_rel)
        findings.extend(result.findings)
        summary = dict((result.data or {}).get("summary") or {})
        summary.update(
            {
                "target": target_rel,
                "dry_run": True,
                "mutations_performed": False,
                "files_modified": 0,
                "external_api_used": False,
                "preliminary": True,
            }
        )
        suggestions.extend(_code_review_suggestions(summary, result.findings, target_rel))
        components = [_component_summary("code.review", result, target_rel)]

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]
        failing = [finding for finding in findings if finding.severity == Severity.FAIL]
        ok = not blocking and not failing

        if ok:
            model_call, model_findings, model_suggestion = self._run_model_generate(
                message,
                default_prompt_id="code.review.agent",
                default_inputs={
                    "review_signals": _review_signals_for_prompt(summary, result.findings),
                    "review_focus": "Priorizar riesgos de seguridad, mantenibilidad y pruebas sin modificar archivos.",
                },
                suggestion_title="Resumen model-aware de revisión de código",
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
            "CodeReviewAgent",
            ok,
            "CodeReviewAgent completed in governed read-only mode." if ok else "CodeReviewAgent completed with blocking/failing findings.",
            message.dry_run,
            tool_calls=tool_calls,
            model_calls=model_calls,
            findings=findings,
            suggestions=suggestions,
            artifacts={
                "target": target_rel,
                "summary": summary,
                "components": components,
                "reviewed_files": list((result.data or {}).get("files") or []),
                "mutations_performed": False,
                "files_modified": 0,
                "external_api_used": False,
                "raw_prompt_stored": False,
                "raw_output_stored": False,
            },
            metadata={
                **_metadata(bool(model_calls), "code-review"),
                "mode": "code-review+model-aware" if model_calls else "code-review",
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
                metadata={"agent_id": self.agent_id, "sprint": "FUNC-SPRINT-53"},
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


def _code_review_suggestions(summary: dict[str, Any], findings: list[Finding], target: str) -> list[AgentSuggestion]:
    failing = [finding for finding in findings if finding.severity == Severity.FAIL]
    blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]
    warnings = [finding for finding in findings if finding.severity == Severity.WARNING]
    suggestions: list[AgentSuggestion] = []
    if blocking or failing:
        top = (blocking or failing)[0]
        suggestions.append(
            AgentSuggestion(
                "Prioridad alta: corregir hallazgos bloqueantes/fallidos",
                f"El primer hallazgo prioritario es {top.id}; revisar el archivo y eliminar el patrón antes de avanzar.",
                target=top.path or target,
                severity="fail" if failing else "block",
            )
        )
    elif warnings:
        suggestions.append(
            AgentSuggestion(
                "Prioridad media: revisar advertencias de código",
                "La revisión no bloquea, pero hay advertencias que conviene resolver antes de una revisión humana final.",
                target=target,
                severity="warning",
            )
        )
    else:
        suggestions.append(
            AgentSuggestion(
                "Code review limpio",
                "CodeReviewAgent no detectó hallazgos fail/block en el target analizado.",
                target=target,
                severity="info",
            )
        )
    suggestions.append(
        AgentSuggestion(
            "Mantener revisión como dry-run",
            f"Archivos revisados: {summary.get('files_reviewed', 0)}; archivos modificados: 0.",
            target=target,
            severity="info",
            metadata={"mutations_performed": False, "files_modified": 0},
        )
    )
    return suggestions


def _review_signals_for_prompt(summary: dict[str, Any], findings: list[Finding]) -> str:
    payload = {
        "summary": {k: summary.get(k) for k in sorted(summary) if k not in {"raw", "content"}},
        "finding_ids": [finding.id for finding in findings[:20]],
        "severities": [finding.severity.value for finding in findings[:20]],
        "raw_content_stored": False,
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
        return str(candidate).replace("\\", "/") or "."
    try:
        return candidate.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(candidate).replace("\\", "/")
