from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from devpilot_core.agents.base import ModelAwareAgent
from devpilot_core.agents.models import AgentMessage, AgentModelCall, AgentRunResult, AgentSuggestion, AgentToolCall
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest
from devpilot_core.repo.architecture_drift import ArchitectureDriftDetector
from devpilot_core.validators.artifact import validate_artifact_file


class ArchitectureAgent(ModelAwareAgent):
    """Governed mono-agent for architecture review.

    FUNC-SPRINT-55 wraps the existing architecture/code drift signal with a
    higher-level SDLC agent. It reads C4/architecture/ADR artifacts, runs drift
    detection where applicable, emits suggestions and can produce a redacted
    model-aware summary through AgentRuntime v2. It does not rewrite diagrams,
    generate code or infer architecture outside local evidence.
    """

    agent_id = "architecture.agent"

    def __init__(self, root: Path, policy: PolicyEngine | None = None) -> None:
        super().__init__(root)
        self.policy = policy or PolicyEngine(self.root)

    def run(self, message: AgentMessage) -> AgentRunResult:
        target = message.target or "docs/02_architecture"
        target_rel = _normalize_subject(target, self.root)
        focus = (message.idea or "Revisar C4, ADRs y drift arquitectura/código.").strip()
        tool_calls: list[AgentToolCall] = []
        findings: list[Finding] = []
        suggestions: list[AgentSuggestion] = []
        model_calls: list[AgentModelCall] = []

        if not message.dry_run:
            findings.append(
                Finding(
                    "ARCHITECTURE_AGENT_EXECUTION_BLOCKED",
                    "ArchitectureAgent is read-only in FUNC-SPRINT-55; architecture edits require a future draft/write workflow and approval.",
                    Severity.BLOCK,
                    path=target_rel,
                    metadata={"mutations_performed": False, "approval_required_for_write": True},
                )
            )
            return AgentRunResult(self.agent_id, "ArchitectureAgent", False, "ArchitectureAgent blocked non-dry-run execution.", message.dry_run, findings=findings, artifacts={"target": target_rel, "read_only": True, "mutations_performed": False}, metadata=_metadata(False, "blocked-non-dry-run"))

        read_call = self._policy_tool_call("artifact.read", "read", target_rel, dry_run=True)
        drift_call = self._policy_tool_call("architecture.drift", "read", target_rel, dry_run=True)
        tool_calls.extend([read_call, drift_call])
        if not read_call.allowed or not drift_call.allowed:
            findings.extend(read_call.findings)
            findings.extend(drift_call.findings)
            return AgentRunResult(self.agent_id, "ArchitectureAgent", False, "ArchitectureAgent blocked by policy before architecture review.", message.dry_run, tool_calls=tool_calls, findings=findings, artifacts={"target": target_rel, "read_only": True, "mutations_performed": False}, metadata=_metadata(False, "blocked-by-policy"))

        if target_rel in {"docs/02_architecture", "."}:
            drift_result = ArchitectureDriftDetector(self.root).detect()
        else:
            drift_result = _deferred_drift_result(target_rel)
        custom_result = _review_target_architecture_docs(self.root, target_rel)
        findings.extend(_downgrade_drift_findings(drift_result))
        findings.extend(custom_result.findings)
        summary = _architecture_summary(target_rel, drift_result, custom_result, focus)
        suggestions.extend(_architecture_suggestions(summary, target_rel))
        components = [_component_summary("architecture.drift", drift_result, target_rel), _component_summary("architecture.target_review", custom_result, target_rel)]

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]
        failing = [finding for finding in findings if finding.severity == Severity.FAIL]
        ok = drift_result.ok and custom_result.ok and not blocking and not failing

        if ok:
            model_call, model_findings, model_suggestion = self._run_model_generate(
                message,
                default_prompt_id="architecture.agent",
                default_inputs={
                    "architecture_goal": focus,
                    "architecture_signals": _architecture_signals_for_prompt(summary, findings),
                },
                suggestion_title="Resumen model-aware de revisión arquitectónica",
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
            "ArchitectureAgent",
            ok,
            "ArchitectureAgent completed governed architecture review." if ok else "ArchitectureAgent completed with blocking/failing findings.",
            message.dry_run,
            tool_calls=tool_calls,
            model_calls=model_calls,
            findings=findings,
            suggestions=suggestions,
            artifacts={
                "target": target_rel,
                "summary": summary,
                "components": components,
                "drift": {"summary": (drift_result.data or {}).get("summary", {}), "matrix_sample": list((drift_result.data or {}).get("matrix", [])[:20])},
                "target_review": custom_result.data,
                "read_only": True,
                "mutations_performed": False,
                "external_api_used": False,
                "raw_prompt_stored": False,
                "raw_output_stored": False,
            },
            metadata={
                **_metadata(bool(model_calls), "architecture-review"),
                "mode": "architecture+model-aware" if model_calls else "architecture",
                "llm_used": any(call.provider != "mock" for call in model_calls),
                "external_api_used": False,
            },
        )

    def _policy_tool_call(self, tool_id: str, action: str, subject: str | Path | None, *, text: str | None = None, dry_run: bool = True) -> AgentToolCall:
        subject_text = _normalize_subject(subject, self.root) if subject else None
        result = self.policy.evaluate(
            PolicyRequest(action=action, path=subject_text, text=text, dry_run=dry_run, tool_id=tool_id, subject=subject_text, metadata={"agent_id": self.agent_id, "sprint": "FUNC-SPRINT-55", "read_only": True})
        )
        return AgentToolCall(tool_id=tool_id, action=action, subject=subject_text, allowed=result.ok, dry_run=dry_run, policy_exit_code=int(result.exit_code), findings=result.findings, metadata={"policy_summary": result.data.get("summary", {})})


def _deferred_drift_result(target: str) -> CommandResult:
    return CommandResult(
        command="repo architecture-drift",
        ok=True,
        exit_code=ExitCode.PASS,
        message="Architecture/code drift full-repo analysis deferred for scoped synthetic target.",
        data={"summary": {"target": target, "status": "deferred", "dry_run": True, "mutations_performed": False, "external_api_used": False, "preliminary": True}},
        findings=[Finding("ARCHITECTURE_AGENT_DRIFT_DEFERRED", "Full architecture drift was deferred for scoped target; target document review still executed.", Severity.INFO, path=target)],
    )


def _review_target_architecture_docs(root: Path, target: str) -> CommandResult:
    target_path = (root / target).resolve()
    findings: list[Finding] = []
    docs = [target_path] if target_path.is_file() else sorted(target_path.rglob("*.md")) if target_path.exists() else []
    validated = 0
    unbacked = 0
    for path in docs[:50]:
        rel = _normalize_subject(path, root)
        validation = validate_artifact_file(path, root=root, strict=False)
        validated += 1
        for finding in validation.findings:
            if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}:
                findings.append(Finding(f"ARCHITECTURE_AGENT_ARTIFACT_{finding.id}", finding.message, Severity.WARNING, path=finding.path, metadata={"source_finding_id": finding.id}))
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(Finding("ARCHITECTURE_AGENT_DOC_UNREADABLE", "Architecture document could not be read as UTF-8.", Severity.WARNING, path=rel))
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            # Synthetic and real-doc friendly heuristic: implemented components
            # should cite code/module evidence, unless explicitly marked future/planned.
            if "component" in lowered and "implemented" in lowered and "src/" not in lowered and "devpilot_core" not in lowered and "planned" not in lowered and "future" not in lowered:
                unbacked += 1
                findings.append(
                    Finding(
                        "ARCHITECTURE_AGENT_UNBACKED_COMPONENT",
                        "ArchitectureAgent detected an implemented component statement without code/module evidence on the same line.",
                        Severity.WARNING,
                        path=f"{rel}:{line_number}",
                        metadata={"line_preview": line[:180], "source": "target_architecture_review"},
                    )
                )
    if not findings:
        findings.append(Finding("ARCHITECTURE_AGENT_TARGET_REVIEW_PASS", "Architecture target review completed without derived target findings.", Severity.INFO, path=target))
    return CommandResult(
        command="architecture target-review",
        ok=True,
        exit_code=ExitCode.PASS,
        message="Architecture target review completed.",
        data={"summary": {"target": target, "documents_reviewed": validated, "unbacked_components": unbacked, "dry_run": True, "mutations_performed": False, "external_api_used": False, "preliminary": True}},
        findings=findings,
    )


def _downgrade_drift_findings(result: CommandResult) -> list[Finding]:
    findings: list[Finding] = []
    for finding in result.findings:
        severity = Severity.WARNING if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} else finding.severity
        findings.append(Finding(f"ARCHITECTURE_AGENT_DRIFT_{finding.id}", finding.message, severity, path=finding.path, metadata={"source_finding_id": finding.id, **finding.metadata}))
    return findings


def _architecture_summary(target: str, drift: CommandResult, target_review: CommandResult, focus: str) -> dict[str, Any]:
    drift_summary = dict((drift.data or {}).get("summary") or {})
    target_summary = dict((target_review.data or {}).get("summary") or {})
    return {
        "target": target,
        "focus": focus,
        "drift_ok": drift.ok,
        "drift_findings_total": len(drift.findings),
        "drift_summary": drift_summary,
        "target_review_summary": target_summary,
        "documents_reviewed": target_summary.get("documents_reviewed", 0),
        "unbacked_components": target_summary.get("unbacked_components", 0),
        "read_only": True,
        "dry_run": True,
        "mutations_performed": False,
        "external_api_used": False,
        "preliminary": True,
    }


def _architecture_suggestions(summary: dict[str, Any], target: str) -> list[AgentSuggestion]:
    suggestions = [AgentSuggestion("Revisión arquitectónica gobernada", f"Documentos revisados: {summary.get('documents_reviewed', 0)}; componentes sin evidencia directa: {summary.get('unbacked_components', 0)}.", target=target, severity="warning" if summary.get("unbacked_components") else "info")]
    if int(summary.get("unbacked_components") or 0):
        suggestions.append(AgentSuggestion("Vincular componentes a código", "Para cada componente implementado, documentar módulo, paquete o ruta `src/devpilot_core/...` asociada.", target=target, severity="warning"))
    suggestions.append(AgentSuggestion("Separar planned/future de implemented", "Mantener explícito el estado de componentes aspiracionales para evitar falsos drift positivos.", target=target, severity="info"))
    return suggestions


def _architecture_signals_for_prompt(summary: dict[str, Any], findings: list[Finding]) -> str:
    payload = {"summary": summary, "finding_ids": [finding.id for finding in findings[:25]], "raw_content_stored": False, "mutations_performed": False}
    return str(payload)[:12000]


def _component_summary(source: str, result: CommandResult, subject: str) -> dict[str, Any]:
    summary = dict((result.data or {}).get("summary") or {})
    return {"source": source, "command": result.command, "subject": subject, "ok": result.ok, "exit_code": int(result.exit_code), "findings_total": len(result.findings), "blocking_findings": sum(1 for f in result.findings if f.severity == Severity.BLOCK), "failing_findings": sum(1 for f in result.findings if f.severity in {Severity.FAIL, Severity.ERROR}), "warnings_total": sum(1 for f in result.findings if f.severity == Severity.WARNING), "dry_run": bool(summary.get("dry_run", True)), "mutations_performed": False}


def _metadata(model_runtime_enabled: bool, mode: str) -> dict[str, Any]:
    return {"miasi_status": "implemented-initial", "max_autonomy": "A3", "runtime_version": "v2-model-aware", "model_runtime_enabled": model_runtime_enabled, "monoagent": True, "handoffs_enabled": False, "mutations_performed": False, "network_used": False, "external_api_used": False, "preliminary": True, "mode": mode}


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
