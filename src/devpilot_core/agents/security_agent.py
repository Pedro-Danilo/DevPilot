from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.agents.base import ModelAwareAgent
from devpilot_core.agents.models import AgentMessage, AgentModelCall, AgentRunResult, AgentSuggestion, AgentToolCall
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest
from devpilot_core.policy.decisions import PolicyEffect
from devpilot_core.policy.secrets import SecretGuard
from devpilot_core.security import PolicySimulationSuite
from devpilot_core.validators.artifact import validate_artifact_file


class SecurityAgent(ModelAwareAgent):
    """Governed mono-agent for security documentation and policy review.

    FUNC-SPRINT-55 creates an initial security reviewer agent. It reads security
    artifacts, scans for obvious secret-like content, runs deterministic policy
    simulation and produces suggestions. It is a reviewer, not an executor: it
    does not mutate policy files, create approvals, run destructive commands or
    call external APIs.
    """

    agent_id = "security.agent"

    def __init__(self, root: Path, policy: PolicyEngine | None = None) -> None:
        super().__init__(root)
        self.policy = policy or PolicyEngine(self.root)

    def run(self, message: AgentMessage) -> AgentRunResult:
        target = message.target or "docs/03_security"
        target_rel = _normalize_subject(target, self.root)
        focus = (message.idea or "Revisar threat model, privacidad, políticas y secretos en modo read-only.").strip()
        tool_calls: list[AgentToolCall] = []
        findings: list[Finding] = []
        suggestions: list[AgentSuggestion] = []
        model_calls: list[AgentModelCall] = []

        if not message.dry_run:
            findings.append(Finding("SECURITY_AGENT_EXECUTION_BLOCKED", "SecurityAgent is read-only in FUNC-SPRINT-55; policy/security mutations require explicit approval workflow.", Severity.BLOCK, path=target_rel, metadata={"mutations_performed": False, "approval_required_for_write": True}))
            return AgentRunResult(self.agent_id, "SecurityAgent", False, "SecurityAgent blocked non-dry-run execution.", message.dry_run, findings=findings, artifacts={"target": target_rel, "read_only": True, "mutations_performed": False}, metadata=_metadata(False, "blocked-non-dry-run"))

        read_call = self._policy_tool_call("artifact.read", "read", target_rel, dry_run=True)
        secret_call = self._policy_tool_call("secret.scan", "read", target_rel, dry_run=True)
        simulation_call = self._policy_tool_call("policy.simulate", "read", "standard", dry_run=True)
        tool_calls.extend([read_call, secret_call, simulation_call])
        if not read_call.allowed or not secret_call.allowed or not simulation_call.allowed:
            findings.extend(read_call.findings)
            findings.extend(secret_call.findings)
            findings.extend(simulation_call.findings)
            return AgentRunResult(self.agent_id, "SecurityAgent", False, "SecurityAgent blocked by policy before security review.", message.dry_run, tool_calls=tool_calls, findings=findings, artifacts={"target": target_rel, "read_only": True, "mutations_performed": False}, metadata=_metadata(False, "blocked-by-policy"))

        doc_result = _review_security_docs(self.root, target_rel)
        simulation = PolicySimulationSuite(self.root).run(matrix="standard")
        findings.extend(doc_result.findings)
        findings.extend(_prefixed_policy_findings(simulation))
        summary = _security_summary(target_rel, doc_result, simulation, focus)
        suggestions.extend(_security_suggestions(summary, target_rel))
        components = [_component_summary("security.docs", doc_result, target_rel), _component_summary("policy.simulate", simulation, "standard")]

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]
        failing = [finding for finding in findings if finding.severity == Severity.FAIL]
        ok = doc_result.ok and simulation.ok and not blocking and not failing

        if ok:
            model_call, model_findings, model_suggestion = self._run_model_generate(
                message,
                default_prompt_id="security.agent",
                default_inputs={
                    "security_goal": focus,
                    "security_signals": _security_signals_for_prompt(summary, findings),
                },
                suggestion_title="Resumen model-aware de revisión de seguridad",
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
            "SecurityAgent",
            ok,
            "SecurityAgent completed governed security review." if ok else "SecurityAgent completed with blocking/failing findings.",
            message.dry_run,
            tool_calls=tool_calls,
            model_calls=model_calls,
            findings=findings,
            suggestions=suggestions,
            artifacts={
                "target": target_rel,
                "summary": summary,
                "components": components,
                "security_docs": doc_result.data,
                "policy_simulation": {"summary": (simulation.data or {}).get("summary", {})},
                "read_only": True,
                "mutations_performed": False,
                "external_api_used": False,
                "raw_prompt_stored": False,
                "raw_output_stored": False,
            },
            metadata={
                **_metadata(bool(model_calls), "security-review"),
                "mode": "security+model-aware" if model_calls else "security",
                "llm_used": any(call.provider != "mock" for call in model_calls),
                "external_api_used": False,
            },
        )

    def _policy_tool_call(self, tool_id: str, action: str, subject: str | Path | None, *, text: str | None = None, dry_run: bool = True) -> AgentToolCall:
        subject_text = _normalize_subject(subject, self.root) if subject and str(subject) != "standard" else (str(subject) if subject else None)
        result = self.policy.evaluate(PolicyRequest(action=action, path=subject_text if subject_text != "standard" else None, text=text, dry_run=dry_run, tool_id=tool_id, subject=subject_text, metadata={"agent_id": self.agent_id, "sprint": "FUNC-SPRINT-55", "read_only": True}))
        return AgentToolCall(tool_id=tool_id, action=action, subject=subject_text, allowed=result.ok, dry_run=dry_run, policy_exit_code=int(result.exit_code), findings=result.findings, metadata={"policy_summary": result.data.get("summary", {})})


def _review_security_docs(root: Path, target: str) -> CommandResult:
    target_path = (root / target).resolve()
    docs = [target_path] if target_path.is_file() else sorted(target_path.rglob("*.md")) if target_path.exists() else []
    findings: list[Finding] = []
    docs_reviewed = 0
    secret_hits = 0
    artifact_warnings = 0
    guard = SecretGuard()
    for path in docs[:80]:
        rel = _normalize_subject(path, root)
        docs_reviewed += 1
        validation = validate_artifact_file(path, root=root, strict=False)
        for finding in validation.findings:
            if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}:
                artifact_warnings += 1
                findings.append(Finding(f"SECURITY_AGENT_ARTIFACT_{finding.id}", finding.message, Severity.WARNING, path=finding.path, metadata={"source_finding_id": finding.id}))
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(Finding("SECURITY_AGENT_DOC_UNREADABLE", "Security document could not be read as UTF-8.", Severity.WARNING, path=rel))
            continue
        decision = guard.scan_text(_security_scan_payload(text), subject=rel)
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            secret_hits += int(decision.metadata.get("redactions", 1) or 1)
            findings.append(Finding("SECURITY_AGENT_SECRET_DETECTED", "SecurityAgent detected secret-like content in a security artifact; raw value is not exposed.", Severity.BLOCK, path=rel, metadata={"payload_redacted": True, "redactions": decision.metadata.get("redactions", 1), "source_rule_id": decision.rule_id}))
    if not docs:
        findings.append(Finding("SECURITY_AGENT_NO_SECURITY_DOCS", "SecurityAgent found no Markdown security artifacts in the requested target.", Severity.WARNING, path=target))
    if not findings:
        findings.append(Finding("SECURITY_AGENT_DOC_REVIEW_PASS", "Security document review completed without derived security findings.", Severity.INFO, path=target))
    ok = not any(f.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for f in findings)
    return CommandResult("security docs-review", ok, ExitCode.PASS if ok else ExitCode.BLOCK, "Security docs review completed." if ok else "Security docs review detected blocking/failing findings.", data={"summary": {"target": target, "documents_reviewed": docs_reviewed, "secret_hits": secret_hits, "artifact_warnings": artifact_warnings, "dry_run": True, "mutations_performed": False, "external_api_used": False, "preliminary": True}}, findings=findings)


def _security_scan_payload(text: str) -> str:
    # Security docs may intentionally include redacted examples such as
    # OPENAI_API_KEY=sk-...REDACTED. Do not treat already-redacted examples as
    # live secrets, while still blocking concrete token-like payloads in fixtures
    # and user-authored artifacts.
    safe_lines = []
    for line in text.splitlines():
        upper = line.upper()
        if "REDACTED" in upper or "<REDACTED" in upper or "..." in line:
            continue
        safe_lines.append(line)
    return "\n".join(safe_lines)


def _prefixed_policy_findings(result: CommandResult) -> list[Finding]:
    findings: list[Finding] = []
    for finding in result.findings:
        severity = Severity.WARNING if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} else finding.severity
        findings.append(Finding(f"SECURITY_AGENT_POLICY_{finding.id}", finding.message, severity, path=finding.path, metadata={"source_finding_id": finding.id, **finding.metadata}))
    return findings


def _security_summary(target: str, doc_result: CommandResult, simulation: CommandResult, focus: str) -> dict[str, Any]:
    doc_summary = dict((doc_result.data or {}).get("summary") or {})
    sim_summary = dict((simulation.data or {}).get("summary") or {})
    return {"target": target, "focus": focus, "documents_reviewed": doc_summary.get("documents_reviewed", 0), "secret_hits": doc_summary.get("secret_hits", 0), "policy_simulation_ok": simulation.ok, "policy_simulation_summary": sim_summary, "read_only": True, "dry_run": True, "mutations_performed": False, "external_api_used": False, "preliminary": True}


def _security_suggestions(summary: dict[str, Any], target: str) -> list[AgentSuggestion]:
    suggestions = [AgentSuggestion("Revisión de seguridad gobernada", f"Documentos revisados: {summary.get('documents_reviewed', 0)}; secretos detectados: {summary.get('secret_hits', 0)}.", target=target, severity="block" if summary.get("secret_hits") else "info")]
    if int(summary.get("secret_hits") or 0):
        suggestions.append(AgentSuggestion("Rotar y remover secretos", "Eliminar el valor crudo del repositorio, rotar la credencial y reemplazarla por referencia segura/env example.", target=target, severity="block", metadata={"raw_secret_exposed": False}))
    suggestions.append(AgentSuggestion("Mantener simulación de políticas", "PolicySimulationSuite debe permanecer PASS antes de habilitar acciones críticas de agentes.", target="policy.simulate", severity="info"))
    suggestions.append(AgentSuggestion("No habilitar ejecución autónoma", "Los agentes de seguridad deben seguir read-only hasta que existan approval, rollback y auditoría operacional suficientes.", target=target, severity="info"))
    return suggestions


def _security_signals_for_prompt(summary: dict[str, Any], findings: list[Finding]) -> str:
    payload = {"summary": summary, "finding_ids": [finding.id for finding in findings[:25]], "raw_content_stored": False, "raw_secret_exposed": False, "mutations_performed": False}
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
