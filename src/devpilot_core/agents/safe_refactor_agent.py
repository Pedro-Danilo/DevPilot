from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.agents.base import ModelAwareAgent
from devpilot_core.agents.models import AgentMessage, AgentModelCall, AgentRunResult, AgentSuggestion, AgentToolCall
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest
from devpilot_core.refactor import RefactorPlanner


class SafeRefactorAgent(ModelAwareAgent):
    """Governed mono-agent for safe refactor planning.

    FUNC-SPRINT-54 wraps RefactorPlanner with AgentRuntime v2 and MIASI
    controls. The agent is plan-only by contract: it produces refactor
    candidates, verification commands, rollback guidance and suggestions, but
    it never executes RefactorExecutor, applies patches or modifies workspace
    files. Future execution remains approval-gated and sandbox-only.
    """

    agent_id = "safe.refactor"

    def __init__(self, root: Path, policy: PolicyEngine | None = None) -> None:
        super().__init__(root)
        self.policy = policy or PolicyEngine(self.root)

    def run(self, message: AgentMessage) -> AgentRunResult:
        target = message.target or "."
        target_rel = _normalize_subject(target, self.root)
        goal = (message.idea or "General safe refactor planning").strip() or "General safe refactor planning"
        tool_calls: list[AgentToolCall] = []
        findings: list[Finding] = []
        suggestions: list[AgentSuggestion] = []
        model_calls: list[AgentModelCall] = []

        if not message.dry_run:
            findings.append(
                Finding(
                    "SAFE_REFACTOR_EXECUTION_BLOCKED",
                    "SafeRefactorAgent is plan-only in FUNC-SPRINT-54; real refactor execution requires a future approval-gated sandbox flow.",
                    Severity.BLOCK,
                    path=target_rel,
                    metadata={"plan_only": True, "mutations_performed": False, "approval_required_for_execution": True},
                )
            )
            return AgentRunResult(
                self.agent_id,
                "SafeRefactorAgent",
                False,
                "SafeRefactorAgent blocked non-dry-run execution.",
                message.dry_run,
                findings=findings,
                artifacts={"target": target_rel, "plan_only": True, "mutations_performed": False, "files_modified": 0, "patch_generated": False},
                metadata=_metadata(False, "blocked-non-dry-run"),
            )

        plan_call = self._policy_tool_call("refactor.plan", "read", target_rel, text=goal, dry_run=True)
        tool_calls.append(plan_call)
        if not plan_call.allowed:
            findings.extend(plan_call.findings)
            return AgentRunResult(
                self.agent_id,
                "SafeRefactorAgent",
                False,
                "SafeRefactorAgent blocked by policy before planning.",
                message.dry_run,
                tool_calls=tool_calls,
                findings=findings,
                artifacts={"target": target_rel, "plan_only": True, "mutations_performed": False, "files_modified": 0, "patch_generated": False},
                metadata=_metadata(False, "blocked-by-policy"),
            )

        # Explicitly declare execution/sandbox capabilities as deferred. This is
        # not an execution attempt and therefore must not require approval in
        # normal plan-only mode. Actual refactor.sandbox/tests.run execution
        # remains approval-gated in their dedicated commands.
        sandbox_call = _deferred_tool_call("refactor.sandbox", "plan", target_rel)
        tests_call = _deferred_tool_call("tests.run", "plan", "smoke")
        tool_calls.extend([sandbox_call, tests_call])

        result = RefactorPlanner(self.root).plan(target_rel, goal=goal, include_code_review=True)
        findings.extend(result.findings)
        summary = dict((result.data or {}).get("summary") or {})
        summary.update(
            {
                "target": target_rel,
                "goal": goal,
                "dry_run": True,
                "plan_only": True,
                "mutations_performed": False,
                "files_modified": 0,
                "patch_generated": False,
                "refactor_executor_invoked": False,
                "sandbox_execution_deferred": True,
                "tests_run_executed": False,
                "external_api_used": False,
                "preliminary": True,
            }
        )
        suggestions.extend(_safe_refactor_suggestions(summary, result, target_rel))
        components = [_component_summary("refactor.plan", result, target_rel)]

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]
        failing = [finding for finding in findings if finding.severity == Severity.FAIL]
        ok = result.ok and not blocking and not failing

        if ok:
            model_call, model_findings, model_suggestion = self._run_model_generate(
                message,
                default_prompt_id="safe.refactor.agent",
                default_inputs={
                    "refactor_goal": goal,
                    "refactor_signals": _refactor_signals_for_prompt(summary, result),
                },
                suggestion_title="Resumen model-aware de planificación de refactor seguro",
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
            "SafeRefactorAgent",
            ok,
            "SafeRefactorAgent generated a governed plan-only refactor plan." if ok else "SafeRefactorAgent generated a plan with blocking/failing findings.",
            message.dry_run,
            tool_calls=tool_calls,
            model_calls=model_calls,
            findings=findings,
            suggestions=suggestions,
            artifacts={
                "target": target_rel,
                "summary": summary,
                "components": components,
                "candidates": list((result.data or {}).get("candidates") or []),
                "plan": list((result.data or {}).get("plan") or []),
                "verification": list((result.data or {}).get("verification") or []),
                "rollback": list((result.data or {}).get("rollback") or []),
                "preconditions": dict((result.data or {}).get("preconditions") or {}),
                "plan_only": True,
                "refactor_executor_invoked": False,
                "patch_generated": False,
                "files_modified": 0,
                "mutations_performed": False,
                "tests_run_executed": False,
                "external_api_used": False,
                "raw_prompt_stored": False,
                "raw_output_stored": False,
            },
            metadata={
                **_metadata(bool(model_calls), "safe-refactor"),
                "mode": "safe-refactor+model-aware" if model_calls else "safe-refactor",
                "llm_used": any(call.provider != "mock" for call in model_calls),
                "plan_only": True,
                "refactor_executor_invoked": False,
                "tests_run_executed": False,
                "external_api_used": False,
            },
        )

    def _policy_tool_call(self, tool_id: str, action: str, subject: str | Path | None, *, text: str | None = None, dry_run: bool = True) -> AgentToolCall:
        subject_text = _normalize_subject(subject, self.root) if subject else None
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
                "Tool capability was declared for planning only; no execution was performed by the agent.",
                Severity.INFO,
                path=subject if subject != "smoke" else None,
                metadata={"tool_id": tool_id, "plan_only": True, "executed": False},
            )
        ],
        metadata={"execution_deferred": True, "plan_only": True, "policy_summary": {"allowed": True, "approval_required_for_execution": True}},
    )


def _safe_refactor_suggestions(summary: dict[str, Any], result: CommandResult, target: str) -> list[AgentSuggestion]:
    candidates_total = int(summary.get("candidates_total") or 0)
    steps_total = int(summary.get("steps_total") or 0)
    suggestions = [
        AgentSuggestion(
            "Plan de refactor seguro generado",
            f"Se generó un plan plan-only con {steps_total} pasos y {candidates_total} candidatos; no se modificaron archivos.",
            target=target,
            severity="info" if result.ok else "warning",
            metadata={"plan_only": True, "files_modified": 0, "patch_generated": False},
        ),
        AgentSuggestion(
            "Validar antes de ejecutar en el futuro",
            "Antes de cualquier ejecución real se requiere revisión humana, sandbox, rollback plan y pruebas controladas.",
            target=target,
            severity="info",
            metadata={"approval_required_for_execution": True, "tests_required": True},
        ),
    ]
    if candidates_total:
        suggestions.append(
            AgentSuggestion(
                "Priorizar candidatos de mayor score",
                "Atender primero los candidatos con mayor score y mantener cambios pequeños, reversibles y cubiertos por pruebas.",
                target=target,
                severity="warning",
            )
        )
    else:
        suggestions.append(
            AgentSuggestion(
                "Refactor conservador",
                "No se detectaron candidatos estructurales fuertes; mantener el plan como checklist de verificación y baseline.",
                target=target,
                severity="info",
            )
        )
    return suggestions


def _refactor_signals_for_prompt(summary: dict[str, Any], result: CommandResult) -> str:
    payload = {
        "summary": {k: summary.get(k) for k in sorted(summary)},
        "finding_ids": [finding.id for finding in result.findings[:20]],
        "severities": [finding.severity.value for finding in result.findings[:20]],
        "plan_preview": list((result.data or {}).get("plan") or [])[:5],
        "raw_source_stored": False,
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
        "plan_only": bool(summary.get("plan_only", True)),
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
