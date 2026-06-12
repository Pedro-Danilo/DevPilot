from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.repo.analyzer import RepoAnalyzer
from devpilot_core.repo.architecture_drift import ArchitectureDriftDetector
from devpilot_core.repo.dependency_graph import DependencyGraphBuilder
from devpilot_core.repo.git_adapter import GitAdapter
from devpilot_core.repo.quality_gate import RepoQualityGate, RepoQualityGateConfig


_PHASE_C_REQUIRED_TOOLS = {
    "git.status",
    "git.diff",
    "git.branches",
    "git.tags",
    "git.log",
    "git.diff_report",
    "repo.inventory",
    "repo.dependency_graph",
    "repo.analyze",
    "repo.architecture_drift",
    "repo.quality_gate",
    "repo.engineering_gate",
    "patch.check",
    "patch.sandbox",
    "rollback.plan",
    "rollback.list",
    "rollback.show",
    "rollback.execute",
    "refactor.plan",
    "refactor.sandbox",
    "tests.run",
}

_PHASE_C_REQUIRED_RULES = {
    "GIT_READ_ALLOW",
    "REPO_QUALITY_GATE_DRY_RUN_ALLOW",
    "ENGINEERING_GATE_READ_ONLY_ALLOW",
    "PATCH_CHECK_DRY_RUN_ALLOW",
    "PATCH_SANDBOX_RUNTIME_ALLOW",
    "ROLLBACK_PLAN_RUNTIME_ALLOW",
    "ROLLBACK_READ_ALLOW",
    "ROLLBACK_EXECUTE_GATED_BLOCKED",
    "REFACTOR_SANDBOX_EXECUTE_GATED",
    "AGENT_CRITICAL_TOOL_DENY",
    "SECRETS_RAW_DENY",
}

_APPROVAL_GATED_TOOLS = {
    "tests.run",
    "rollback.execute",
    "refactor.sandbox",
    "model.call.external",
}

_PHASE_C_MANIFESTS = tuple(f"docs/functional_sprint_{index}_manifest.json" for index in range(35, 45))
_PHASE_C_AUDITS = (
    "docs/audits/func_sprint_35_git_adapter_v2_audit.md",
    "docs/audits/func_sprint_36_dependency_graph_audit.md",
    "docs/audits/func_sprint_37_repo_analyzer_v2_audit.md",
    "docs/audits/func_sprint_38_architecture_drift_audit.md",
    "docs/audits/func_sprint_39_repo_quality_gate_audit.md",
    "docs/audits/func_sprint_40_patch_preflight_audit.md",
    "docs/audits/func_sprint_41_patch_sandbox_changeset_audit.md",
    "docs/audits/func_sprint_42_rollback_manager_audit.md",
    "docs/audits/func_sprint_43_refactor_executor_sandbox_audit.md",
    "docs/audits/phase_c_repository_engineering_closure_report.md",
)


@dataclass(frozen=True)
class RepoEngineeringGateConfig:
    """Configuration for FUNC-SPRINT-44 repository engineering gate."""

    profile: str = "quick"
    target: str = "."
    code_target: str | None = None
    patch_file: str | None = None
    include_architecture_drift: bool = True


class RepoEngineeringGate:
    """Aggregate repository engineering signals for Phase C closure.

    The gate is read-only and evidence-oriented. It consolidates the Phase C
    stack without enabling productive patch/refactor execution: GitAdapter,
    DependencyGraph, RepoAnalyzer, ArchitectureDrift, RepoQualityGate and MIASI
    declaration checks. Optional reports are written by the CLI report layer,
    not by this class.
    """

    def __init__(self, root: Path, *, config: RepoEngineeringGateConfig | None = None) -> None:
        self.root = root.resolve()
        self.config = config or RepoEngineeringGateConfig()

    def run(self) -> CommandResult:
        profile = _normalize_profile(self.config.profile)
        findings: list[Finding] = []
        components: list[dict[str, Any]] = []

        git_result = GitAdapter(self.root).status()
        components.append(_component_summary("git_status", git_result, "."))
        findings.extend(_prefixed_findings(git_result, source="git_status"))

        dependency_result = DependencyGraphBuilder(self.root).build(target=self._dependency_target())
        components.append(_component_summary("dependency_graph", dependency_result, "src/devpilot_core"))
        findings.extend(_prefixed_findings(dependency_result, source="dependency_graph"))

        repo_result = RepoAnalyzer(self.root).analyze(target=self.config.target)
        components.append(_component_summary("repo_analyzer", repo_result, self.config.target))
        findings.extend(_prefixed_findings(repo_result, source="repo_analyzer"))

        if self.config.include_architecture_drift and profile == "full":
            drift_result = ArchitectureDriftDetector(self.root).detect()
            components.append(_component_summary("architecture_drift", drift_result, "docs+src/devpilot_core"))
            findings.extend(_prefixed_findings(drift_result, source="architecture_drift"))
        else:
            drift_result = _skipped_result(
                command="repo architecture-drift",
                reason="Architecture drift skipped by configuration.",
                source="architecture_drift",
            )
            components.append(_component_summary("architecture_drift", drift_result, "skipped"))
            findings.extend(_prefixed_findings(drift_result, source="architecture_drift"))

        quality_result = RepoQualityGate(
            self.root,
            config=RepoQualityGateConfig(
                target=self.config.target,
                code_target=self.config.code_target,
                patch_file=self.config.patch_file,
            ),
        ).run()
        components.append(_component_summary("repo_quality_gate", quality_result, self.config.target))
        findings.extend(_prefixed_findings(quality_result, source="repo_quality_gate"))

        miasi_result = self._validate_miasi_contracts()
        components.append(_component_summary("miasi_phase_c", miasi_result, ".devpilot/miasi"))
        findings.extend(_prefixed_findings(miasi_result, source="miasi_phase_c"))

        docs_result = self._validate_phase_c_documents(include_sprint_44=profile == "full")
        components.append(_component_summary("phase_c_documents", docs_result, "docs"))
        findings.extend(_prefixed_findings(docs_result, source="phase_c_documents"))

        if profile == "full":
            invariants_result = self._validate_runtime_invariants()
            components.append(_component_summary("runtime_invariants", invariants_result, ".gitignore+runtime"))
            findings.extend(_prefixed_findings(invariants_result, source="runtime_invariants"))

        exit_code = _derive_exit_code(findings)
        status = _status(exit_code)
        capability_map = self._phase_c_capability_map()
        blocking = sum(1 for finding in findings if finding.severity == Severity.BLOCK)
        failing = sum(1 for finding in findings if finding.severity in {Severity.FAIL, Severity.ERROR})
        warnings = sum(1 for finding in findings if finding.severity == Severity.WARNING)
        components_passed = sum(1 for component in components if component["ok"])
        summary = {
            "status": status,
            "profile": profile,
            "target": self.config.target,
            "components_total": len(components),
            "components_passed": components_passed,
            "components_failed": len(components) - components_passed,
            "findings_total": len(findings),
            "blocking_findings": blocking,
            "failing_findings": failing,
            "warnings_total": warnings,
            "phase_c_status": "closed" if exit_code == ExitCode.PASS else "blocked",
            "ready_for_phase_d_initial": exit_code == ExitCode.PASS,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "git_write_used": False,
            "patch_applied_to_productive_workspace": False,
            "refactor_applied_to_productive_workspace": False,
            "preliminary": True,
        }
        data = {
            "summary": summary,
            "components": components,
            "phase_c_capabilities": capability_map,
            "closure": {
                "phase": "FASE-C-INGENIERIA-DE-REPOSITORIO",
                "sprints": [f"FUNC-SPRINT-{index}" for index in range(35, 45)],
                "closed_by": "FUNC-SPRINT-44",
                "next_phase": "Fase D — IA local gobernada",
                "status": summary["phase_c_status"],
                "preliminary": True,
            },
            "notes": [
                "FUNC-SPRINT-44 consolidates repository engineering signals but remains read-only.",
                "This gate does not apply patches, does not execute productive refactors, does not perform Git write and does not deploy.",
                "Warnings are preserved as engineering signals; FAIL/BLOCK/ERROR findings block Phase C closure.",
                "Phase D should introduce governed local AI/model execution only after this gate remains reproducible.",
            ],
        }
        ok = exit_code == ExitCode.PASS
        message = "Repository engineering gate passed." if ok else f"Repository engineering gate completed with status {status}."
        return CommandResult(
            command="repo engineering-gate",
            ok=ok,
            exit_code=exit_code,
            message=message,
            data=data,
            findings=findings,
        )

    def _dependency_target(self) -> Path:
        candidate = self.root / "src" / "devpilot_core"
        if candidate.exists():
            return candidate
        return self.root / "src" if (self.root / "src").exists() else self.root

    def _validate_miasi_contracts(self) -> CommandResult:
        findings: list[Finding] = []
        tool_registry = _read_json(self.root / ".devpilot" / "miasi" / "tool_registry.json")
        policy_matrix = _read_json(self.root / ".devpilot" / "miasi" / "policy_matrix.json")
        agent_registry = _read_json(self.root / ".devpilot" / "miasi" / "agent_registry.json")

        tool_ids = {str(tool.get("tool_id")) for tool in tool_registry.get("tools", []) if isinstance(tool, dict)}
        rule_ids = {str(rule.get("rule_id")) for rule in policy_matrix.get("rules", []) if isinstance(rule, dict)}
        agent_ids = {str(agent.get("agent_id")) for agent in agent_registry.get("agents", []) if isinstance(agent, dict)}

        missing_tools = sorted(_PHASE_C_REQUIRED_TOOLS - tool_ids)
        missing_rules = sorted(_PHASE_C_REQUIRED_RULES - rule_ids)
        if missing_tools:
            findings.append(Finding("ENGINEERING_GATE_MIASI_TOOLS_MISSING", "Phase C MIASI tools are missing.", Severity.BLOCK, path=".devpilot/miasi/tool_registry.json", metadata={"missing_tools": missing_tools}))
        if missing_rules:
            findings.append(Finding("ENGINEERING_GATE_MIASI_RULES_MISSING", "Phase C MIASI policy rules are missing.", Severity.BLOCK, path=".devpilot/miasi/policy_matrix.json", metadata={"missing_rules": missing_rules}))

        tools_by_id = {str(tool.get("tool_id")): tool for tool in tool_registry.get("tools", []) if isinstance(tool, dict)}
        approval_mismatches = [tool_id for tool_id in sorted(_APPROVAL_GATED_TOOLS & tool_ids) if not bool(tools_by_id.get(tool_id, {}).get("requires_approval"))]
        if approval_mismatches:
            findings.append(Finding("ENGINEERING_GATE_APPROVAL_GATES_MISSING", "Approval-gated high-risk tools are not declared with requires_approval=true.", Severity.BLOCK, path=".devpilot/miasi/tool_registry.json", metadata={"tools": approval_mismatches}))

        if not {"repo.analysis", "patch.review", "safe.refactor"}.issubset(agent_ids):
            findings.append(Finding("ENGINEERING_GATE_PHASE_C_AGENTS_MISSING", "Expected Phase C repository/refactor agents are missing from Agent Registry.", Severity.BLOCK, path=".devpilot/miasi/agent_registry.json"))

        if not findings:
            findings.append(Finding("ENGINEERING_GATE_MIASI_PASS", "Phase C MIASI tools, policies and approval gates are declared.", Severity.INFO))
        return CommandResult(
            command="repo engineering-gate miasi-phase-c",
            ok=_ok(findings),
            exit_code=_derive_exit_code(findings),
            message="Phase C MIASI declarations validated.",
            data={
                "summary": {
                    "tools_total": len(tool_ids),
                    "policy_rules_total": len(rule_ids),
                    "agents_total": len(agent_ids),
                    "required_tools_total": len(_PHASE_C_REQUIRED_TOOLS),
                    "required_rules_total": len(_PHASE_C_REQUIRED_RULES),
                    "approval_gated_tools_checked": sorted(_APPROVAL_GATED_TOOLS & tool_ids),
                    "missing_tools": missing_tools,
                    "missing_rules": missing_rules,
                    "preliminary": True,
                }
            },
            findings=findings,
        )

    def _validate_phase_c_documents(self, *, include_sprint_44: bool) -> CommandResult:
        findings: list[Finding] = []
        manifests = list(_PHASE_C_MANIFESTS)
        audits = list(_PHASE_C_AUDITS)
        if not include_sprint_44:
            manifests = manifests[:-1]
            audits = audits[:-1]
        required = [
            "README.md",
            "docs/05_operations/runbook.md",
            "docs/04_quality/test_strategy.md",
            "docs/06_miasi/tool_card.md",
            "docs/06_miasi/tool_registry.md",
            "docs/devpilot_backlog_fase_C_ingenieria_repositorio.md",
            "docs/functional_backlog_after_precode.md",
            *manifests,
            *audits,
        ]
        missing = [path for path in required if not (self.root / path).exists()]
        if missing:
            findings.append(Finding("ENGINEERING_GATE_PHASE_C_DOCS_MISSING", "Required Phase C engineering documents are missing.", Severity.BLOCK, path="docs", metadata={"missing": missing}))
        backlog = _safe_read(self.root / "docs" / "devpilot_backlog_fase_C_ingenieria_repositorio.md")
        if include_sprint_44 and 'phase_c_status: "completed"' not in backlog:
            findings.append(Finding("ENGINEERING_GATE_PHASE_C_STATUS_NOT_COMPLETED", "Phase C backlog is not marked completed after Sprint 44.", Severity.BLOCK, path="docs/devpilot_backlog_fase_C_ingenieria_repositorio.md"))
        if include_sprint_44 and 'last_completed_sprint: "FUNC-SPRINT-44"' not in backlog:
            findings.append(Finding("ENGINEERING_GATE_LAST_COMPLETED_NOT_44", "Backlog does not point to FUNC-SPRINT-44 as last completed sprint.", Severity.BLOCK, path="docs/devpilot_backlog_fase_C_ingenieria_repositorio.md"))
        if not findings:
            findings.append(Finding("ENGINEERING_GATE_PHASE_C_DOCS_PASS", "Phase C engineering documents and manifests are present.", Severity.INFO))
        return CommandResult(
            command="repo engineering-gate phase-c-docs",
            ok=_ok(findings),
            exit_code=_derive_exit_code(findings),
            message="Phase C documentation closure checks completed.",
            data={"summary": {"required_documents_total": len(required), "missing_documents_total": len(missing), "include_sprint_44": include_sprint_44, "preliminary": True}},
            findings=findings,
        )

    def _validate_runtime_invariants(self) -> CommandResult:
        findings: list[Finding] = []
        gitignore = _safe_read(self.root / ".gitignore")
        for required in ("outputs/", ".devpilot/rollback/"):
            if required not in gitignore:
                findings.append(Finding("ENGINEERING_GATE_GITIGNORE_RUNTIME_MISSING", "Runtime path is not excluded in .gitignore.", Severity.BLOCK, path=".gitignore", metadata={"required": required}))
        if not (self.root / "src" / "devpilot_core" / "sandbox" / "patch_sandbox.py").exists():
            findings.append(Finding("ENGINEERING_GATE_PATCH_SANDBOX_MISSING", "PatchSandbox implementation is missing.", Severity.BLOCK, path="src/devpilot_core/sandbox/patch_sandbox.py"))
        if not (self.root / "src" / "devpilot_core" / "changes" / "rollback.py").exists():
            findings.append(Finding("ENGINEERING_GATE_ROLLBACK_MANAGER_MISSING", "RollbackManager implementation is missing.", Severity.BLOCK, path="src/devpilot_core/changes/rollback.py"))
        if not (self.root / "src" / "devpilot_core" / "refactor" / "executor.py").exists():
            findings.append(Finding("ENGINEERING_GATE_REFACTOR_EXECUTOR_MISSING", "RefactorExecutor implementation is missing.", Severity.BLOCK, path="src/devpilot_core/refactor/executor.py"))
        if not findings:
            findings.append(Finding("ENGINEERING_GATE_RUNTIME_INVARIANTS_PASS", "Runtime artifact exclusions and sandbox modules are present.", Severity.INFO))
        return CommandResult(
            command="repo engineering-gate runtime-invariants",
            ok=_ok(findings),
            exit_code=_derive_exit_code(findings),
            message="Runtime invariant checks completed.",
            data={"summary": {"checks_total": 5, "preliminary": True}},
            findings=findings,
        )

    def _phase_c_capability_map(self) -> list[dict[str, Any]]:
        return [
            {"sprint": "FUNC-SPRINT-35", "capability": "GitAdapter v2 read-only", "status": "implemented", "productive_write": False},
            {"sprint": "FUNC-SPRINT-36", "capability": "DependencyGraph/import graph Python", "status": "implemented-initial", "productive_write": False},
            {"sprint": "FUNC-SPRINT-37", "capability": "RepoAnalyzer v2", "status": "implemented-initial", "productive_write": False},
            {"sprint": "FUNC-SPRINT-38", "capability": "Architecture/code drift", "status": "implemented-initial", "productive_write": False},
            {"sprint": "FUNC-SPRINT-39", "capability": "Repo quality gate dry-run", "status": "implemented-initial", "productive_write": False},
            {"sprint": "FUNC-SPRINT-40", "capability": "Patch preflight", "status": "implemented-initial", "productive_write": False},
            {"sprint": "FUNC-SPRINT-41", "capability": "PatchSandbox + ChangeSet", "status": "implemented-initial", "productive_write": False},
            {"sprint": "FUNC-SPRINT-42", "capability": "RollbackManager local backup", "status": "implemented-initial", "productive_write": False},
            {"sprint": "FUNC-SPRINT-43", "capability": "RefactorExecutor sandbox", "status": "implemented-initial", "productive_write": False},
            {"sprint": "FUNC-SPRINT-44", "capability": "Repository engineering gate closure", "status": "implemented-initial", "productive_write": False},
        ]


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
        "mutations_performed": bool((result.data or {}).get("summary", {}).get("mutations_performed", False)),
    }


def _prefixed_findings(result: CommandResult, *, source: str) -> list[Finding]:
    prefixed: list[Finding] = []
    for finding in result.findings:
        metadata = {"source": source, "source_command": result.command, "source_finding_id": finding.id, **finding.metadata}
        prefixed.append(Finding(id=f"ENGINEERING_GATE_{source.upper()}_{finding.id}", message=finding.message, severity=finding.severity, path=finding.path, metadata=metadata))
    return prefixed


def _derive_exit_code(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS


def _status(exit_code: ExitCode) -> str:
    return "PASS" if exit_code == ExitCode.PASS else "BLOCK" if exit_code == ExitCode.BLOCK else "FAIL" if exit_code == ExitCode.FAIL else "ERROR"


def _ok(findings: list[Finding]) -> bool:
    return _derive_exit_code(findings) == ExitCode.PASS


def _normalize_profile(value: str) -> str:
    normalized = (value or "quick").strip().lower()
    return normalized if normalized in {"quick", "full"} else "quick"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _skipped_result(*, command: str, reason: str, source: str) -> CommandResult:
    return CommandResult(
        command=command,
        ok=True,
        exit_code=ExitCode.PASS,
        message=reason,
        data={"summary": {"skipped": True, "preliminary": True}},
        findings=[Finding(f"{source.upper()}_SKIPPED", reason, Severity.INFO)],
    )
