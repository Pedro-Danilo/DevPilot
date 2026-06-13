from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.agents.base import ModelAwareAgent
from devpilot_core.agents.models import AgentMessage, AgentModelCall, AgentRunResult, AgentSuggestion, AgentToolCall
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest
from devpilot_core.review import PatchPreflightEngine, PatchReviewEngine


class PatchReviewAgent(ModelAwareAgent):
    """Governed mono-agent for patch review and preflight.

    FUNC-SPRINT-53 wraps PatchReviewEngine and PatchPreflightEngine without ever
    applying a patch. It is a dry-run explanatory agent: it reads one patch file,
    evaluates deterministic risks, optionally checks applicability with
    git apply --check through SafeSubprocessRunner, and emits redacted evidence.
    """

    agent_id = "patch.review"

    def __init__(self, root: Path, policy: PolicyEngine | None = None) -> None:
        super().__init__(root)
        self.policy = policy or PolicyEngine(self.root)

    def run(self, message: AgentMessage) -> AgentRunResult:
        patch_file = _patch_file_from_message(message)
        tool_calls: list[AgentToolCall] = []
        findings: list[Finding] = []
        suggestions: list[AgentSuggestion] = []
        model_calls: list[AgentModelCall] = []

        if not patch_file:
            findings.append(Finding("PATCH_REVIEW_AGENT_PATCH_FILE_REQUIRED", "PatchReviewAgent requires --patch-file or --target pointing to a patch file.", Severity.BLOCK))
            return AgentRunResult(
                self.agent_id,
                "PatchReviewAgent",
                False,
                "PatchReviewAgent blocked: patch file is required.",
                message.dry_run,
                findings=findings,
                artifacts={"patch_file": None, "patch_applied": False, "mutations_performed": False},
                metadata=_metadata(False, "missing-patch-file"),
            )

        patch_rel = _normalize_subject(patch_file, self.root)
        parse_call = self._policy_tool_call("patch.parse", "read", patch_rel, dry_run=message.dry_run)
        tool_calls.append(parse_call)
        if not parse_call.allowed:
            findings.extend(parse_call.findings)
            return AgentRunResult(
                self.agent_id,
                "PatchReviewAgent",
                False,
                "PatchReviewAgent blocked by policy before patch review.",
                message.dry_run,
                tool_calls=tool_calls,
                findings=findings,
                artifacts={"patch_file": patch_rel, "patch_applied": False, "mutations_performed": False},
                metadata=_metadata(False, "blocked-by-policy"),
            )

        patch_result = PatchReviewEngine(self.root).review(patch_file=patch_rel)
        findings.extend(patch_result.findings)
        components = [_component_summary("patch.parse", patch_result, patch_rel)]

        preflight_result: CommandResult | None = None
        preflight_call = self._policy_tool_call("patch.check", "read", patch_rel, dry_run=message.dry_run)
        tool_calls.append(preflight_call)
        if not preflight_call.allowed:
            findings.extend(preflight_call.findings)
            preflight_result = _blocked_component_result("patch check", preflight_call.findings)
        else:
            preflight_result = PatchPreflightEngine(self.root).check(patch_file=patch_rel)
            findings.extend(preflight_result.findings)
        components.append(_component_summary("patch.check", preflight_result, patch_rel))

        summary = _build_summary(patch_rel, patch_result, preflight_result)
        suggestions.extend(_patch_review_suggestions(summary, findings, patch_rel))

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]
        failing = [finding for finding in findings if finding.severity == Severity.FAIL]
        ok = not blocking and not failing

        if ok:
            model_call, model_findings, model_suggestion = self._run_model_generate(
                message,
                default_prompt_id="patch.review.agent",
                default_inputs={
                    "patch_signals": _patch_signals_for_prompt(summary, patch_result, preflight_result),
                    "review_focus": "Explicar riesgos del patch y próximos pasos seguros sin aplicar cambios.",
                },
                suggestion_title="Resumen model-aware de revisión de patch",
                suggestion_target=patch_rel,
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
            "PatchReviewAgent",
            ok,
            "PatchReviewAgent completed in governed dry-run mode." if ok else "PatchReviewAgent completed with blocking/failing findings.",
            message.dry_run,
            tool_calls=tool_calls,
            model_calls=model_calls,
            findings=findings,
            suggestions=suggestions,
            artifacts={
                "patch_file": patch_rel,
                "summary": summary,
                "components": components,
                "patch_review": _safe_result_summary(patch_result),
                "preflight": _safe_result_summary(preflight_result),
                "patch_applied": False,
                "mutations_performed": False,
                "external_api_used": False,
                "raw_prompt_stored": False,
                "raw_output_stored": False,
            },
            metadata={
                **_metadata(bool(model_calls), "patch-review"),
                "mode": "patch-review+model-aware" if model_calls else "patch-review",
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


def _patch_file_from_message(message: AgentMessage) -> str | None:
    metadata = dict(message.metadata or {})
    value = metadata.get("patch_file") or message.target
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _build_summary(patch_rel: str, patch_result: CommandResult, preflight_result: CommandResult) -> dict[str, Any]:
    patch_summary = dict((patch_result.data or {}).get("summary") or {})
    preflight_summary = dict((preflight_result.data or {}).get("summary") or {})
    return {
        "patch_file": patch_rel,
        "patch_review_ok": patch_result.ok,
        "preflight_ok": preflight_result.ok,
        "files_changed": patch_summary.get("files_changed", 0),
        "added_lines": patch_summary.get("added_lines", 0),
        "deleted_lines": patch_summary.get("deleted_lines", 0),
        "patch_review_findings": len(patch_result.findings),
        "preflight_findings": len(preflight_result.findings),
        "apply_check_executed": bool(preflight_summary.get("apply_check_executed", False)),
        "applies": bool(preflight_summary.get("applies", False)),
        "security_block": bool(preflight_summary.get("security_block", False)),
        "working_tree_unchanged": bool(preflight_summary.get("working_tree_unchanged", True)),
        "patch_applied": False,
        "mutations_performed": False,
        "external_api_used": False,
        "dry_run": True,
        "preliminary": True,
    }


def _patch_review_suggestions(summary: dict[str, Any], findings: list[Finding], patch_rel: str) -> list[AgentSuggestion]:
    blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]
    failing = [finding for finding in findings if finding.severity == Severity.FAIL]
    warnings = [finding for finding in findings if finding.severity == Severity.WARNING]
    suggestions: list[AgentSuggestion] = []
    if blocking:
        suggestions.append(AgentSuggestion("Patch bloqueado", f"El patch contiene un bloqueo de seguridad o política: {blocking[0].id}.", target=patch_rel, severity="block"))
    elif failing:
        suggestions.append(AgentSuggestion("Patch requiere corrección", f"El patch no debe avanzar hasta corregir el hallazgo: {failing[0].id}.", target=patch_rel, severity="fail"))
    elif warnings:
        suggestions.append(AgentSuggestion("Patch con advertencias", "El patch no bloquea, pero requiere revisión humana por advertencias detectadas.", target=patch_rel, severity="warning"))
    else:
        suggestions.append(AgentSuggestion("Patch review limpio", "PatchReviewAgent no detectó hallazgos fail/block y no aplicó cambios.", target=patch_rel, severity="info"))
    suggestions.append(
        AgentSuggestion(
            "Confirmar dry-run",
            "El agente solo ejecutó revisión/preflight; patch_applied=false y mutations_performed=false.",
            target=patch_rel,
            severity="info",
            metadata={"patch_applied": False, "mutations_performed": False},
        )
    )
    return suggestions


def _patch_signals_for_prompt(summary: dict[str, Any], patch_result: CommandResult, preflight_result: CommandResult) -> str:
    payload = {
        "summary": summary,
        "finding_ids": [finding.id for finding in [*patch_result.findings, *preflight_result.findings][:20]],
        "severities": [finding.severity.value for finding in [*patch_result.findings, *preflight_result.findings][:20]],
        "raw_patch_stored": False,
        "patch_applied": False,
    }
    return str(payload)[:12000]


def _safe_result_summary(result: CommandResult | None) -> dict[str, Any]:
    if result is None:
        return {"available": False, "payload_redacted": True}
    return {
        "command": result.command,
        "ok": result.ok,
        "exit_code": int(result.exit_code),
        "message": result.message,
        "summary": dict((result.data or {}).get("summary") or {}),
        "findings_total": len(result.findings),
        "payload_redacted": True,
    }


def _blocked_component_result(command: str, findings: list[Finding]) -> CommandResult:
    return CommandResult(
        command=command,
        ok=False,
        exit_code=ExitCode.BLOCK,
        message=f"{command} blocked by policy.",
        data={"summary": {"dry_run": True, "mutations_performed": False, "external_api_used": False, "preliminary": True}},
        findings=findings,
    )


def _component_summary(source: str, result: CommandResult, subject: str) -> dict[str, Any]:
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
        "dry_run": True,
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
        "patch_applied": False,
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
