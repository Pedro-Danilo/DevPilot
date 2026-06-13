from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.agents.base import ModelAwareAgent
from devpilot_core.agents.models import AgentMessage, AgentModelCall, AgentRunResult, AgentSuggestion, AgentToolCall
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest
from devpilot_core.repo.analyzer import RepoAnalyzer, RepoAnalyzerConfig
from devpilot_core.repo.dependency_graph import DependencyGraphBuilder
from devpilot_core.repo.git_adapter import GitAdapter


class RepoAnalysisAgent(ModelAwareAgent):
    """Governed mono-agent for repository analysis.

    FUNC-SPRINT-52 implements the first specialized repository agent on top of
    the Phase C read-only engines. The agent does not mutate files, does not run
    Git write commands, does not apply patches, does not require local model
    servers and only performs optional model calls through AgentRuntime v2.
    """

    agent_id = "repo.analysis"

    def __init__(self, root: Path, policy: PolicyEngine | None = None) -> None:
        super().__init__(root)
        self.policy = policy or PolicyEngine(self.root)

    def run(self, message: AgentMessage) -> AgentRunResult:
        target = message.target or "."
        target_path = Path(target)
        if not target_path.is_absolute():
            target_path = self.root / target_path
        target_path = target_path.resolve()
        target_rel = _repo_path(target_path, self.root)

        tool_calls: list[AgentToolCall] = []
        findings: list[Finding] = []
        suggestions: list[AgentSuggestion] = []
        model_calls: list[AgentModelCall] = []
        components: list[dict[str, Any]] = []

        read_call = self._policy_tool_call("repo.analyze", "read", target_rel, dry_run=message.dry_run)
        tool_calls.append(read_call)
        if not read_call.allowed:
            findings.extend(read_call.findings)
            return AgentRunResult(
                self.agent_id,
                "RepoAnalysisAgent",
                False,
                "RepoAnalysisAgent blocked by policy before repository analysis.",
                message.dry_run,
                tool_calls=tool_calls,
                findings=findings,
                artifacts={"target": target_rel, "mutations_performed": False},
                metadata=_metadata(False, "blocked-by-policy"),
            )

        if not target_path.exists():
            findings.append(Finding("REPO_ANALYSIS_AGENT_TARGET_NOT_FOUND", "RepoAnalysisAgent target does not exist.", Severity.FAIL, path=target_rel))
            return AgentRunResult(
                self.agent_id,
                "RepoAnalysisAgent",
                False,
                "RepoAnalysisAgent target does not exist.",
                message.dry_run,
                tool_calls=tool_calls,
                findings=findings,
                artifacts={"target": target_rel, "mutations_performed": False},
                metadata=_metadata(False, "target-missing"),
            )

        repo_result = RepoAnalyzer(self.root, config=RepoAnalyzerConfig(max_files=800)).analyze(target=target_rel)
        components.append(_component_summary("repo.analyze", repo_result, target_rel))
        findings.extend(_prefixed_findings(repo_result, source="repo_analyze"))

        dependency_target = _dependency_target(self.root, target_path)
        dependency_rel = _repo_path(dependency_target, self.root)
        dependency_call = self._policy_tool_call("repo.dependency_graph", "read", dependency_rel, dry_run=message.dry_run)
        tool_calls.append(dependency_call)
        if dependency_call.allowed:
            dependency_result = DependencyGraphBuilder(self.root).build(target=dependency_target)
        else:
            dependency_result = _blocked_component_result("repo dependency-graph", dependency_call.findings)
        components.append(_component_summary("repo.dependency_graph", dependency_result, dependency_rel))
        findings.extend(_prefixed_findings(dependency_result, source="dependency_graph"))

        git_call = self._policy_tool_call("git.status", "read", ".", dry_run=message.dry_run)
        tool_calls.append(git_call)
        if git_call.allowed:
            git_result = GitAdapter(self.root).status()
        else:
            git_result = _blocked_component_result("git status", git_call.findings)
        components.append(_component_summary("git.status", git_result, "."))
        findings.extend(_prefixed_findings(git_result, source="git_status"))

        quality_call = self._policy_tool_call("repo.quality_gate", "read", target_rel, dry_run=message.dry_run)
        tool_calls.append(quality_call)
        if quality_call.allowed:
            quality_result = CommandResult(
                command="repo quality-gate",
                ok=True,
                exit_code=ExitCode.PASS,
                message="Repo quality gate execution deferred by RepoAnalysisAgent initial profile.",
                data={
                    "summary": {
                        "status": "deferred",
                        "target": target_rel,
                        "skipped": True,
                        "reason": "FUNC-SPRINT-52 avoids duplicating full repo quality-gate inside the agent; run repo quality-gate explicitly for closure evidence.",
                        "dry_run": True,
                        "mutations_performed": False,
                        "external_api_used": False,
                        "preliminary": True,
                    }
                },
                findings=[Finding("REPO_ANALYSIS_AGENT_QUALITY_GATE_DEFERRED", "Repo quality gate was not executed inside RepoAnalysisAgent initial profile; run it explicitly when needed.", Severity.INFO, metadata={"target": target_rel, "preliminary": True})],
            )
        else:
            quality_result = _blocked_component_result("repo quality-gate", quality_call.findings)
        components.append(_component_summary("repo.quality_gate", quality_result, target_rel))
        findings.extend(_prefixed_findings(quality_result, source="repo_quality_gate"))

        summary = _build_summary(target_rel, components, repo_result)
        suggestions.extend(_build_suggestions(summary, repo_result, quality_result))

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]
        failing = [finding for finding in findings if finding.severity == Severity.FAIL]
        ok = not blocking and not failing

        if ok:
            model_call, model_findings, model_suggestion = self._run_model_generate(
                message,
                default_prompt_id="repo.analysis.agent",
                default_inputs={
                    "repository_signals": _repository_signals_for_prompt(summary, repo_result),
                    "analysis_goal": "Explicar estado del repositorio, riesgos principales y próximos pasos sin modificar archivos.",
                },
                suggestion_title="Resumen model-aware de análisis de repositorio",
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
            "RepoAnalysisAgent",
            ok,
            "RepoAnalysisAgent completed in governed read-only mode." if ok else "RepoAnalysisAgent completed with blocking/failing findings.",
            message.dry_run,
            tool_calls=tool_calls,
            model_calls=model_calls,
            findings=findings,
            suggestions=suggestions,
            artifacts={
                "target": target_rel,
                "summary": summary,
                "components": components,
                "mutations_performed": False,
                "git_write_used": False,
                "external_api_used": False,
                "raw_prompt_stored": False,
                "raw_output_stored": False,
            },
            metadata={
                **_metadata(bool(model_calls), "read-only-analysis"),
                "mode": "repo-analysis+model-aware" if model_calls else "repo-analysis",
                "llm_used": any(call.provider != "mock" for call in model_calls),
                "external_api_used": False,
            },
        )

    def _policy_tool_call(self, tool_id: str, action: str, subject: str | Path | None, *, text: str | None = None, dry_run: bool = True) -> AgentToolCall:
        subject_text = _repo_path(self.root / subject, self.root) if subject and not Path(subject).is_absolute() else (_repo_path(Path(subject), self.root) if subject else None)
        result = self.policy.evaluate(PolicyRequest(action=action, path=subject_text, text=text, dry_run=dry_run, tool_id=tool_id, subject=subject_text, metadata={"agent_id": self.agent_id, "sprint": "FUNC-SPRINT-52"}))
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


def _metadata(model_runtime_enabled: bool, mode: str) -> dict[str, Any]:
    return {
        "miasi_status": "implemented-initial",
        "max_autonomy": "A3",
        "runtime_version": "v2-model-aware",
        "model_runtime_enabled": model_runtime_enabled,
        "monoagent": True,
        "handoffs_enabled": False,
        "mode": mode,
        "mutations_performed": False,
        "network_used": False,
        "external_api_used": False,
        "preliminary": True,
    }


def _dependency_target(root: Path, target_path: Path) -> Path:
    if target_path.resolve() != root.resolve():
        candidate = target_path / "src"
        if candidate.exists():
            return candidate
        return target_path
    candidate = root / "src" / "devpilot_core"
    if candidate.exists():
        return candidate
    candidate = root / "src"
    if candidate.exists():
        return candidate
    return target_path


def _component_summary(source: str, result: CommandResult, subject: str | None) -> dict[str, Any]:
    severities = [finding.severity for finding in result.findings]
    return {
        "source": source,
        "command": result.command,
        "subject": subject,
        "ok": result.ok,
        "exit_code": int(result.exit_code),
        "findings_total": len(result.findings),
        "blocking_findings": sum(1 for severity in severities if severity == Severity.BLOCK),
        "failing_findings": sum(1 for severity in severities if severity in {Severity.FAIL, Severity.ERROR}),
        "warnings_total": sum(1 for severity in severities if severity == Severity.WARNING),
        "dry_run": True,
        "mutations_performed": False,
    }


def _prefixed_findings(result: CommandResult, *, source: str) -> list[Finding]:
    prefixed: list[Finding] = []
    for finding in result.findings[:30]:
        original_severity = finding.severity
        # RepoAnalysisAgent is an explanatory read-only agent. Underlying engines
        # may report BLOCK/FAIL as risk signals for the repository, but the agent
        # itself should not fail unless policy/target validation blocks before
        # analysis. Preserve the original severity in metadata for auditability.
        severity = Severity.WARNING if original_severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} else original_severity
        metadata = {
            "source": source,
            "source_command": result.command,
            "source_finding_id": finding.id,
            "source_severity": original_severity.value,
            **finding.metadata,
        }
        prefixed.append(Finding(id=f"REPO_AGENT_{source.upper()}_{finding.id}", message=finding.message, severity=severity, path=finding.path, metadata=metadata))
    return prefixed


def _blocked_component_result(command: str, findings: list[Finding]) -> CommandResult:
    return CommandResult(command=command, ok=False, exit_code=ExitCode.BLOCK, message=f"{command} blocked by policy.", data={"summary": {"blocked": True, "preliminary": True}}, findings=findings)


def _build_summary(target: str, components: list[dict[str, Any]], repo_result: CommandResult) -> dict[str, Any]:
    repo_summary = dict((repo_result.data or {}).get("summary") or {})
    risk_signals = list((repo_result.data or {}).get("risk_signals") or [])
    hotspots = list((repo_result.data or {}).get("hotspots") or [])
    warnings_total = sum(int(component.get("warnings_total", 0)) for component in components)
    blocking_total = sum(int(component.get("blocking_findings", 0)) for component in components)
    failing_total = sum(int(component.get("failing_findings", 0)) for component in components)
    return {
        "target": target,
        "health_score": repo_summary.get("health_score"),
        "status": repo_summary.get("status") or ("blocked" if blocking_total else "needs-review" if warnings_total else "pass"),
        "components_total": len(components),
        "components_passed": sum(1 for component in components if component.get("ok") is True),
        "warnings_total": warnings_total,
        "blocking_findings": blocking_total,
        "failing_findings": failing_total,
        "risk_signals_total": len(risk_signals),
        "hotspots_total": len(hotspots),
        "top_risks": risk_signals[:5],
        "top_hotspots": hotspots[:5],
        "dry_run": True,
        "mutations_performed": False,
        "external_api_used": False,
        "preliminary": True,
    }


def _build_suggestions(summary: dict[str, Any], repo_result: CommandResult, quality_result: CommandResult) -> list[AgentSuggestion]:
    suggestions: list[AgentSuggestion] = []
    target = str(summary.get("target") or ".")
    if summary.get("blocking_findings") or summary.get("failing_findings"):
        suggestions.append(AgentSuggestion("Prioridad alta: resolver bloqueos del análisis de repositorio", "El agente detectó hallazgos BLOCK/FAIL en uno o más motores; revisar findings por componente antes de continuar.", target=target, severity="fail"))
    elif summary.get("warnings_total"):
        suggestions.append(AgentSuggestion("Prioridad media: reducir advertencias del repositorio", "El repositorio no está bloqueado, pero hay advertencias acumuladas que deben priorizarse por impacto y recurrencia.", target=target, severity="warning"))
    else:
        suggestions.append(AgentSuggestion("Repositorio sin bloqueos críticos", "El análisis gobernado no detectó bloqueos ni fallos. Mantener la suite de regresión y quality gates antes de cambios funcionales.", target=target, severity="info"))

    top_risks = summary.get("top_risks") or []
    if top_risks:
        first = top_risks[0]
        suggestions.append(AgentSuggestion("Revisar señal de riesgo prioritaria", f"Riesgo principal: {first.get('kind', 'risk')} en {first.get('path', target)}.", target=str(first.get("path") or target), severity=str(first.get("severity") or "warning")))

    q_summary = dict((quality_result.data or {}).get("summary") or {})
    if q_summary:
        suggestions.append(AgentSuggestion("Usar repo quality-gate como criterio de salida", f"Estado quality-gate: {q_summary.get('status', 'unknown')}; findings: {q_summary.get('findings_total', 0)}.", target=target, severity="info"))
    return suggestions


def _repository_signals_for_prompt(summary: dict[str, Any], repo_result: CommandResult) -> str:
    payload = {
        "summary": {key: value for key, value in summary.items() if key not in {"top_risks", "top_hotspots"}},
        "top_risks": summary.get("top_risks", [])[:3],
        "repo_message": repo_result.message,
    }
    return str(payload)[:12000]


def _repo_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
