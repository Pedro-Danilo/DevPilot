from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from devpilot_core.agents.base import ModelAwareAgent
from devpilot_core.agents.models import AgentMessage, AgentModelCall, AgentRunResult, AgentSuggestion, AgentToolCall
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.miasi import AgentSpec, MiasiRegistryValidator
from devpilot_core.policy import PolicyEngine, PolicyRequest
from devpilot_core.validators.artifact import validate_artifact_file
from devpilot_core.validators.checklist import validate_precode_checklist
from devpilot_core.validators.frontmatter import validate_frontmatter_file

AGENT_ALIASES = {
    "documentation-audit": "precode.audit",
    "precode-audit": "precode.audit",
    "precode.audit": "precode.audit",
    "precode-documentation": "precode.documentation",
    "documentation": "precode.documentation",
    "precode.documentation": "precode.documentation",
}


class LocalAgent(Protocol):
    """Minimal protocol implemented by deterministic Sprint 12 agents."""

    agent_id: str

    def run(self, message: AgentMessage) -> AgentRunResult:
        ...


@dataclass(frozen=True)
class AgentRuntimeConfig:
    """Runtime constraints for AgentRuntime.

    FUNC-SPRINT-51 extends the deterministic Sprint 12 runtime with optional
    model-aware execution. Model calls remain opt-in, mono-agent, routed through
    ModelAdapterRouter and governed by PromptRegistry/BudgetLedger.
    """

    allow_execute: bool = False
    require_miasi_validation: bool = True
    model_provider: str | None = None
    model: str | None = None
    prompt_id: str | None = None
    prompt_version: str | None = None
    prompt_inputs: dict[str, str] | None = None
    fallback_to_mock: bool = False
    local_timeout_seconds: float = 3.0


class AgentRuntime:
    """Local/mock agent runtime for DevPilot document agents.

    Sprint 12 starts the executable agent layer without leaving the local-first
    safety envelope. The runtime resolves registered agents from the executable
    MIASI Agent Registry, verifies policy before each tool-like operation and
    adapts internal agent results into the common CommandResult contract.
    """

    def __init__(self, root: Path, *, config: AgentRuntimeConfig | None = None) -> None:
        self.root = root.resolve()
        self.config = config or AgentRuntimeConfig()
        self.policy = PolicyEngine(self.root)
        self._agents: dict[str, LocalAgent] = {
            "precode.audit": DocumentationAuditAgent(self.root, self.policy),
            "precode.documentation": PreCodeDocumentationAgent(self.root, self.policy),
        }

    def run(
        self,
        requested_agent: str,
        *,
        target: str | None = None,
        idea: str | None = None,
        dry_run: bool = True,
        provider: str | None = None,
        model: str | None = None,
        prompt_id: str | None = None,
        prompt_version: str | None = None,
        prompt_inputs: dict[str, str] | None = None,
        fallback_to_mock: bool | None = None,
        timeout_seconds: float | None = None,
    ) -> CommandResult:
        """Run one registered mono-agent and return a normalized CommandResult."""

        agent_id = AGENT_ALIASES.get(requested_agent.strip(), requested_agent.strip())
        bundle, load_findings = MiasiRegistryValidator(self.root).load_bundle()
        if load_findings or bundle is None:
            return _agent_command_result(
                AgentRunResult(
                    agent_id=agent_id or "unknown",
                    agent_name="unknown",
                    ok=False,
                    message="Agent runtime blocked because executable MIASI registries could not be loaded.",
                    dry_run=dry_run,
                    findings=load_findings,
                )
            )

        specs = {agent.agent_id: agent for agent in bundle.agents}
        spec = specs.get(agent_id)
        if spec is None:
            finding = Finding(
                id="AGENT_RUNTIME_UNKNOWN_AGENT",
                message="Requested agent is not registered in the executable MIASI Agent Registry.",
                severity=Severity.BLOCK,
                metadata={"requested_agent": requested_agent, "resolved_agent_id": agent_id},
            )
            return _agent_command_result(
                AgentRunResult(agent_id=agent_id or "unknown", agent_name="unknown", ok=False, message="Agent runtime blocked unknown agent.", dry_run=dry_run, findings=[finding])
            )

        if spec.agent_id not in self._agents:
            finding = Finding(
                id="AGENT_RUNTIME_NOT_IMPLEMENTED",
                message="Requested agent is registered but has no local/mock runtime implementation yet.",
                severity=Severity.BLOCK,
                metadata={"agent_id": spec.agent_id, "phase": spec.phase, "status": spec.status},
            )
            return _agent_command_result(
                AgentRunResult(agent_id=spec.agent_id, agent_name=spec.name, ok=False, message="Agent runtime has no implementation for this agent.", dry_run=dry_run, findings=[finding])
            )

        # FUNC-SPRINT-51 keeps execution mono-agent. Only currently implemented
        # MVP agents can run; MVP+ specialized agents remain planned for later
        # sprints and must not be activated through runtime v2 yet.
        if spec.phase != "MVP":
            finding = Finding(
                id="AGENT_RUNTIME_PHASE_BLOCKED",
                message="AgentRuntime v2 only executes implemented mono-agent MVP agents in Sprint 51.",
                severity=Severity.BLOCK,
                metadata={"agent_id": spec.agent_id, "phase": spec.phase, "multiagent_enabled": False},
            )
            return _agent_command_result(
                AgentRunResult(agent_id=spec.agent_id, agent_name=spec.name, ok=False, message="Agent runtime blocked non-MVP agent.", dry_run=dry_run, findings=[finding])
            )

        if self.config.require_miasi_validation:
            registry_result = MiasiRegistryValidator(self.root).validate_agents()
            blocking = [finding for finding in registry_result.findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]
            if blocking:
                return _agent_command_result(
                    AgentRunResult(
                        agent_id=spec.agent_id,
                        agent_name=spec.name,
                        ok=False,
                        message="Agent runtime blocked because Agent Registry validation failed.",
                        dry_run=dry_run,
                        findings=blocking,
                    )
                )

        model_runtime = self._model_runtime_metadata(
            provider=provider,
            model=model,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            prompt_inputs=prompt_inputs,
            fallback_to_mock=fallback_to_mock,
            timeout_seconds=timeout_seconds,
        )
        message = AgentMessage(
            agent_id=spec.agent_id,
            target=target,
            idea=idea,
            dry_run=dry_run,
            metadata={
                "requested_agent": requested_agent,
                "runtime_version": "v2-model-aware",
                "monoagent": True,
                "handoffs_enabled": False,
                "model_runtime": model_runtime,
            },
        )
        result = self._agents[spec.agent_id].run(message)
        result = AgentRunResult(
            agent_id=result.agent_id,
            agent_name=spec.name,
            ok=result.ok,
            message=result.message,
            dry_run=result.dry_run,
            tool_calls=result.tool_calls,
            model_calls=result.model_calls,
            findings=result.findings,
            suggestions=result.suggestions,
            artifacts=result.artifacts,
            metadata={
                "miasi_status": spec.status,
                "max_autonomy": spec.max_autonomy,
                "runtime_version": "v2-model-aware",
                "model_runtime_enabled": bool(model_runtime.get("enabled")),
                "monoagent": True,
                "handoffs_enabled": False,
                **result.metadata,
            },
        )
        return _agent_command_result(result)

    def _model_runtime_metadata(
        self,
        *,
        provider: str | None,
        model: str | None,
        prompt_id: str | None,
        prompt_version: str | None,
        prompt_inputs: dict[str, str] | None,
        fallback_to_mock: bool | None,
        timeout_seconds: float | None,
    ) -> dict[str, Any]:
        selected_provider = provider if provider is not None else self.config.model_provider
        selected_prompt_id = prompt_id if prompt_id is not None else self.config.prompt_id
        enabled = selected_provider is not None or selected_prompt_id is not None
        inputs = dict(self.config.prompt_inputs or {})
        inputs.update(prompt_inputs or {})
        return {
            "enabled": enabled,
            "provider": selected_provider or "mock",
            "model": model if model is not None else self.config.model,
            "prompt_id": selected_prompt_id,
            "prompt_version": prompt_version if prompt_version is not None else self.config.prompt_version,
            "prompt_inputs": inputs,
            "fallback_to_mock": self.config.fallback_to_mock if fallback_to_mock is None else bool(fallback_to_mock),
            "timeout_seconds": timeout_seconds if timeout_seconds is not None else self.config.local_timeout_seconds,
            "payload_redacted": True,
            "external_api_used": False,
        }


class BaseDocumentAgent(ModelAwareAgent):
    """Shared helpers for deterministic document agents."""

    agent_id: str

    def __init__(self, root: Path, policy: PolicyEngine) -> None:
        super().__init__(root)
        self.policy = policy

    def _policy_tool_call(self, tool_id: str, action: str, subject: str | Path | None, *, text: str | None = None, dry_run: bool = True) -> AgentToolCall:
        subject_text = _repo_path(self.root / subject, self.root) if subject and not Path(subject).is_absolute() else (_repo_path(Path(subject), self.root) if subject else None)
        result = self.policy.evaluate(PolicyRequest(action=action, path=subject_text, text=text, dry_run=dry_run))
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


class DocumentationAuditAgent(BaseDocumentAgent):
    """Rule-based agent that audits Markdown documentation artifacts.

    It reuses existing frontmatter/artifact validators and never edits files.
    The agent is suitable for MVP because it only reads permitted paths and
    produces findings/suggestions as evidence.
    """

    agent_id = "precode.audit"

    def run(self, message: AgentMessage) -> AgentRunResult:
        target = message.target or "docs"
        tool_calls: list[AgentToolCall] = []
        findings: list[Finding] = []
        suggestions: list[AgentSuggestion] = []

        target_path = Path(target)
        if not target_path.is_absolute():
            target_path = self.root / target_path
        target_rel = _repo_path(target_path, self.root)

        read_call = self._policy_tool_call("artifact.read", "read", target_rel, dry_run=message.dry_run)
        tool_calls.append(read_call)
        if not read_call.allowed:
            findings.extend(read_call.findings)
            return AgentRunResult(self.agent_id, "DocumentationAuditAgent", False, "Documentation audit blocked by policy.", message.dry_run, tool_calls=tool_calls, findings=findings)

        if not target_path.exists():
            findings.append(Finding("AGENT_TARGET_MISSING", "Documentation audit target does not exist.", Severity.BLOCK, path=target_rel))
            return AgentRunResult(self.agent_id, "DocumentationAuditAgent", False, "Documentation audit target is missing.", message.dry_run, tool_calls=tool_calls, findings=findings)

        markdown_files = _markdown_targets(target_path)
        if not markdown_files:
            findings.append(Finding("AGENT_TARGET_EMPTY", "Documentation audit target has no Markdown files.", Severity.FAIL, path=target_rel))
            return AgentRunResult(self.agent_id, "DocumentationAuditAgent", False, "Documentation audit found no Markdown files.", message.dry_run, tool_calls=tool_calls, findings=findings)

        validated = 0
        for file_path in markdown_files:
            rel = _repo_path(file_path, self.root)
            file_read = self._policy_tool_call("artifact.read", "read", rel, dry_run=message.dry_run)
            tool_calls.append(file_read)
            if not file_read.allowed:
                findings.extend(file_read.findings)
                continue
            frontmatter_result = validate_frontmatter_file(file_path, root=self.root, strict=True)
            artifact_result = validate_artifact_file(file_path, root=self.root, strict=True)
            validated += 1
            findings.extend(frontmatter_result.findings)
            findings.extend(artifact_result.findings)
            if not frontmatter_result.ok:
                suggestions.append(AgentSuggestion("Revisar frontmatter", "El documento tiene metadatos faltantes o no aprobados.", target=rel, severity="fail"))
            if not artifact_result.ok:
                suggestions.append(AgentSuggestion("Revisar estructura del artefacto", "El documento no cumple completamente su perfil MIPSoftware/MIASI.", target=rel, severity="fail"))

        checklist_call = self._policy_tool_call("checklist.precode.run", "read", "docs/checklists/checklist_pre_code.md", dry_run=message.dry_run)
        tool_calls.append(checklist_call)
        if checklist_call.allowed:
            checklist = validate_precode_checklist(self.root, strict=True)
            findings.extend(checklist.findings)
            if not checklist.ok:
                suggestions.append(AgentSuggestion("Revisar checklist pre-code", "El checklist ejecutable tiene filas obligatorias no aprobadas.", target="docs/checklists/checklist_pre_code.md", severity="fail"))
        else:
            findings.extend(checklist_call.findings)

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        warnings = [finding for finding in findings if finding.severity == Severity.WARNING]
        if not blocking and not warnings:
            suggestions.append(AgentSuggestion("Auditoría documental sin bloqueos", "No se detectaron fallos ni bloqueos en los documentos auditados.", target=target_rel))
        elif warnings and not blocking:
            suggestions.append(AgentSuggestion("Auditoría documental con advertencias", "Hay secciones recomendadas o señales no bloqueantes para revisar.", target=target_rel, severity="warning"))

        ok = not blocking
        model_calls: list[AgentModelCall] = []
        if ok:
            model_call, model_findings, model_suggestion = self._run_model_generate(
                message,
                default_prompt_id="model.generate.default",
                default_inputs={
                    "user_request": f"Resume de forma segura la auditoría documental ejecutada sobre {target_rel}.",
                    "project_context": f"Archivos markdown evaluados: {len(markdown_files)}; archivos validados: {validated}; findings: {len(findings)}.",
                },
                suggestion_title="Resumen model-aware de auditoría documental",
                suggestion_target=target_rel,
            )
            if model_call is not None:
                model_calls.append(model_call)
            if model_findings:
                findings.extend(model_findings)
                blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
                ok = not blocking
            if model_suggestion is not None:
                suggestions.append(model_suggestion)
        return AgentRunResult(
            self.agent_id,
            "DocumentationAuditAgent",
            ok,
            "Documentation audit completed." if ok else "Documentation audit completed with blocking/failing findings.",
            message.dry_run,
            tool_calls,
            model_calls,
            findings,
            suggestions,
            artifacts={"target": target_rel, "markdown_files": [_repo_path(path, self.root) for path in markdown_files], "validated_files": validated},
            metadata={"mode": "rule-based+model-aware" if model_calls else "rule-based", "llm_used": any(call.provider != "mock" for call in model_calls), "external_api_used": False},
        )


class PreCodeDocumentationAgent(BaseDocumentAgent):
    """Rule-based agent that drafts pre-code documentation suggestions.

    The first version does not use an LLM. It turns a user idea into a small,
    reviewable Markdown draft and refuses to overwrite approved project docs.
    """

    agent_id = "precode.documentation"

    def run(self, message: AgentMessage) -> AgentRunResult:
        idea = (message.idea or "").strip()
        findings: list[Finding] = []
        tool_calls: list[AgentToolCall] = []
        suggestions: list[AgentSuggestion] = []

        if not idea:
            findings.append(Finding("AGENT_IDEA_REQUIRED", "PreCodeDocumentationAgent requires --idea text.", Severity.BLOCK))
            return AgentRunResult(self.agent_id, "PreCodeDocumentationAgent", False, "Pre-code documentation draft blocked: idea is required.", message.dry_run, findings=findings)

        draft_name = f"precode_documentation_{_slugify(idea)[:48] or 'draft'}.md"
        draft_rel = f"outputs/drafts/{draft_name}"
        policy_call = self._policy_tool_call("document.draft.generate", "create", draft_rel, text=idea, dry_run=message.dry_run)
        tool_calls.append(policy_call)
        if not policy_call.allowed:
            findings.extend(policy_call.findings)
            return AgentRunResult(self.agent_id, "PreCodeDocumentationAgent", False, "Pre-code documentation draft blocked by policy.", message.dry_run, tool_calls=tool_calls, findings=findings)

        draft = _render_precode_draft(idea)
        if message.dry_run:
            suggestions.append(
                AgentSuggestion(
                    "Borrador pre-code propuesto",
                    "DevPilot generó un borrador en memoria. Usa --execute para escribirlo bajo outputs/drafts sin modificar documentos aprobados.",
                    target=draft_rel,
                )
            )
            artifacts = {"draft_path": draft_rel, "written": False, "preview": draft}
        else:
            draft_path = self.root / draft_rel
            draft_path.parent.mkdir(parents=True, exist_ok=True)
            if draft_path.exists():
                findings.append(Finding("AGENT_DRAFT_EXISTS", "Draft output already exists; refusing to overwrite.", Severity.BLOCK, path=draft_rel))
                return AgentRunResult(self.agent_id, "PreCodeDocumentationAgent", False, "Draft already exists; no overwrite performed.", message.dry_run, tool_calls=tool_calls, findings=findings)
            draft_path.write_text(draft, encoding="utf-8")
            suggestions.append(AgentSuggestion("Borrador pre-code escrito", "Se escribió un borrador revisable bajo outputs/drafts.", target=draft_rel))
            artifacts = {"draft_path": draft_rel, "written": True}

        model_calls: list[AgentModelCall] = []
        model_call, model_findings, model_suggestion = self._run_model_generate(
            message,
            default_prompt_id="model.generate.default",
            default_inputs={
                "user_request": "Propón mejoras seguras para el borrador pre-code generado en dry-run.",
                "project_context": f"Draft path: {draft_rel}. Idea provided: yes. Raw idea is not persisted in model call metadata.",
            },
            suggestion_title="Sugerencia model-aware para borrador pre-code",
            suggestion_target=draft_rel,
        )
        if model_call is not None:
            model_calls.append(model_call)
        if model_findings:
            findings.extend(model_findings)
            blocking_model_findings = [finding for finding in model_findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
            if blocking_model_findings:
                return AgentRunResult(
                    self.agent_id,
                    "PreCodeDocumentationAgent",
                    False,
                    "Pre-code documentation draft generated but model-aware guidance was blocked.",
                    message.dry_run,
                    tool_calls,
                    model_calls,
                    findings,
                    suggestions,
                    artifacts=artifacts,
                    metadata={"mode": "rule-based+model-aware", "llm_used": False, "external_api_used": False},
                )
        if model_suggestion is not None:
            suggestions.append(model_suggestion)

        return AgentRunResult(
            self.agent_id,
            "PreCodeDocumentationAgent",
            True,
            "Pre-code documentation draft generated in dry-run." if message.dry_run else "Pre-code documentation draft written under outputs/drafts.",
            message.dry_run,
            tool_calls,
            model_calls,
            findings,
            suggestions,
            artifacts=artifacts,
            metadata={"mode": "rule-based+model-aware" if model_calls else "rule-based", "llm_used": any(call.provider != "mock" for call in model_calls), "external_api_used": False},
        )


def _agent_command_result(result: AgentRunResult) -> CommandResult:
    blocking = [finding for finding in result.findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]
    failing = [finding for finding in result.findings if finding.severity == Severity.FAIL]
    ok = result.ok and not blocking and not failing
    exit_code = ExitCode.BLOCK if blocking else (ExitCode.FAIL if failing else ExitCode.PASS)
    data = {
        "agent": {
            "agent_id": result.agent_id,
            "agent_name": result.agent_name,
            "dry_run": result.dry_run,
            "preliminary": True,
            "llm_required": any(call.provider != "mock" for call in result.model_calls),
            "model_aware": bool(result.model_calls),
        },
        "summary": {
            "tool_calls_total": len(result.tool_calls),
            "model_calls_total": len(result.model_calls),
            "suggestions_total": len(result.suggestions),
            "findings_total": len(result.findings),
            "blocking_findings": len(blocking),
            "failing_findings": len(failing),
        },
        "tool_calls": [call.to_dict() for call in result.tool_calls],
        "model_calls": [call.to_dict() for call in result.model_calls],
        "suggestions": [suggestion.to_dict() for suggestion in result.suggestions],
        "artifacts": result.artifacts,
        "metadata": result.metadata,
    }
    return CommandResult(
        command="agent run",
        ok=ok,
        exit_code=exit_code,
        message=result.message if ok else f"{result.message} See findings.",
        data=data,
        findings=result.findings,
    )


def _markdown_targets(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() == ".md" else []
    return sorted(item for item in path.rglob("*.md") if item.is_file())


def _repo_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def _render_precode_draft(idea: str) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        "---\n"
        "title: \"Pre-code draft generated by DevPilot Local\"\n"
        "status: draft\n"
        "generated_by: FUNC-SPRINT-12\n"
        f"generated_at: \"{generated_at}\"\n"
        "---\n\n"
        "# Pre-code draft generated by DevPilot Local\n\n"
        "## 1. Idea de entrada\n\n"
        f"{idea}\n\n"
        "## 2. Clasificación inicial\n\n"
        "- Tipo: propuesta documental preliminar.\n"
        "- Modo: mock/local rule-based.\n"
        "- LLM externo: no utilizado.\n"
        "- Acción sobre documentos aprobados: ninguna.\n\n"
        "## 3. Sugerencias de ingeniería\n\n"
        "1. Vincular la idea con un requerimiento funcional o no funcional.\n"
        "2. Identificar artefactos MIPSoftware/MIASI afectados.\n"
        "3. Definir criterios PASS/BLOCK antes de implementar código.\n"
        "4. Registrar riesgos de seguridad, costos, persistencia y trazabilidad.\n\n"
        "## 4. Próxima acción segura\n\n"
        "Revisar manualmente este borrador y decidir si debe convertirse en un ajuste controlado de documentación.\n"
    )
