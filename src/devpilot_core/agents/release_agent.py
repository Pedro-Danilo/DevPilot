from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.agents.base import ModelAwareAgent
from devpilot_core.agents.models import AgentMessage, AgentRunResult, AgentSuggestion, AgentToolCall
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest


@dataclass(frozen=True)
class ReleaseEvidence:
    """One auditable ReleaseAgent evidence item."""

    tool_id: str
    command: str
    ok: bool
    exit_code: int
    summary: dict[str, Any]
    findings_total: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "command": self.command,
            "ok": self.ok,
            "exit_code": self.exit_code,
            "summary": self.summary,
            "findings_total": self.findings_total,
        }


class ReleaseAgent(ModelAwareAgent):
    """Dry-run release assistant for Fase G closure.

    FUNC-SPRINT-84 introduces a governed ReleaseAgent MVP. The agent only
    reads local evidence and invokes deterministic in-process release builders
    in dry-run mode. It does not publish, deploy, sign, tag Git, create remote
    releases, mutate source files or require model/API access.
    """

    agent_id = "release.assistant"

    def __init__(self, root: Path, policy: PolicyEngine) -> None:
        super().__init__(root)
        self.root = Path(root).resolve()
        self.policy = policy

    def run(self, message: AgentMessage) -> AgentRunResult:
        tool_calls: list[AgentToolCall] = []
        findings: list[Finding] = []
        suggestions: list[AgentSuggestion] = []
        evidence: list[ReleaseEvidence] = []

        if not message.dry_run:
            findings.append(
                Finding(
                    "RELEASE_AGENT_EXECUTE_BLOCKED",
                    "ReleaseAgent MVP only supports dry-run execution; publication, deployment, signing and Git tagging remain out of scope.",
                    Severity.BLOCK,
                    metadata={"requested_dry_run": message.dry_run},
                )
            )
            return AgentRunResult(
                self.agent_id,
                "ReleaseAgent",
                False,
                "ReleaseAgent blocked because execute mode is not allowed.",
                message.dry_run,
                tool_calls=tool_calls,
                findings=findings,
                suggestions=suggestions,
                artifacts={"release_agent_mvp": True},
                metadata=_security_metadata(),
            )

        checks = [
            ("release.quality_gate", "quality_gate_release", lambda: _run_quality_gate_release(self.root)),
            ("release.manifest", "release_manifest", lambda: _run_release_manifest(self.root)),
            ("release.changelog", "release_changelog", lambda: _run_release_changelog(self.root)),
            ("release.package", "package_build_dry_run", lambda: _run_package_dry_run(self.root)),
            ("release.sbom", "release_sbom", lambda: _run_release_sbom(self.root)),
            ("release.install_plan", "install_plan", lambda: _run_install_plan(self.root)),
            ("release.upgrade_check", "upgrade_check", lambda: _run_upgrade_check(self.root)),
        ]

        for tool_id, action, runner in checks:
            policy_call = self._policy_tool_call(tool_id, action, subject="release-evidence", dry_run=True)
            tool_calls.append(policy_call)
            if not policy_call.allowed:
                findings.extend(policy_call.findings)
                continue
            result = runner()
            evidence.append(_evidence_from_result(tool_id, result))
            findings.extend(_agent_findings(tool_id, result))

        checklist = _release_checklist(evidence=evidence)
        release_ready = all(item["status"] == "PASS" for item in checklist)
        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        ok = release_ready and not blocking

        suggestions.extend(_suggestions(checklist=checklist, evidence=evidence, release_ready=ok))
        artifacts = {
            "release_assistant_report": {
                "schema_version": "1.0.0",
                "agent_id": self.agent_id,
                "release_version": _project_version(self.root),
                "dry_run": True,
                "release_ready": ok,
                "phase_g_closure_candidate": ok,
                "checklist": checklist,
                "evidence": [item.to_dict() for item in evidence],
                "required_evidence": [
                    "quality-gate release",
                    "release manifest",
                    "release changelog",
                    "package build dry-run",
                    "SBOM baseline",
                    "install plan",
                    "upgrade check",
                ],
                "security": _security_metadata(),
                "limitations": [
                    "ReleaseAgent MVP is dry-run only and does not execute publish/deploy/tag/sign operations.",
                    "Recommendations are based on local evidence and deterministic builders; no LLM is required.",
                    "Production release still requires manual operator review and future signing/provenance hardening.",
                ],
            }
        }
        return AgentRunResult(
            self.agent_id,
            "ReleaseAgent",
            ok,
            "ReleaseAgent dry-run completed with release recommendations." if ok else "ReleaseAgent dry-run completed with blocking release findings.",
            True,
            tool_calls=tool_calls,
            findings=findings,
            suggestions=suggestions,
            artifacts=artifacts,
            metadata={
                "mode": "rule-based-release-assistant",
                "phase": "FASE-G-PRODUCTIZACION-RELEASE",
                "sprint": "FUNC-SPRINT-84",
                "tool_calls_auditable": True,
                "policy_engine_used": True,
                "miasi_runtime_required": True,
                **_security_metadata(),
            },
        )

    def _policy_tool_call(self, tool_id: str, action: str, subject: str | Path | None, *, dry_run: bool = True) -> AgentToolCall:
        result = self.policy.evaluate(
            PolicyRequest(
                action="read",
                path=str(subject) if subject is not None else None,
                subject=str(subject) if subject is not None else None,
                tool_id=tool_id,
                dry_run=dry_run,
                metadata={"release_agent_action": action, "sprint": "FUNC-SPRINT-84"},
            )
        )
        return AgentToolCall(
            tool_id=tool_id,
            action=action,
            subject=str(subject) if subject is not None else None,
            allowed=result.ok,
            dry_run=dry_run,
            policy_exit_code=int(result.exit_code),
            findings=result.findings,
            metadata={"policy_summary": result.data.get("summary", {}), "policy_engine_used": True},
        )



def _run_quality_gate_release(root: Path) -> CommandResult:
    from devpilot_core.quality import QualityGate, QualityGateOptions

    return QualityGate(root, options=QualityGateOptions(profile="release")).run()


def _run_release_manifest(root: Path) -> CommandResult:
    from devpilot_core.release import ReleaseManifestBuilder, ReleaseManifestOptions

    return ReleaseManifestBuilder(root, options=ReleaseManifestOptions(version=_project_version(root))).build()


def _run_release_changelog(root: Path) -> CommandResult:
    from devpilot_core.release import ReleaseChangelogBuilder, ReleaseChangelogOptions

    return ReleaseChangelogBuilder(root, options=ReleaseChangelogOptions(version=_project_version(root))).build()


def _run_package_dry_run(root: Path) -> CommandResult:
    from devpilot_core.release import PackageBuildBuilder, PackageBuildOptions

    return PackageBuildBuilder(root, options=PackageBuildOptions(version=_project_version(root), kind="all", execute=False)).build()


def _run_release_sbom(root: Path) -> CommandResult:
    from devpilot_core.release import ReleaseSbomBuilder, ReleaseSbomOptions

    return ReleaseSbomBuilder(root, options=ReleaseSbomOptions(version=_project_version(root))).build()


def _run_install_plan(root: Path) -> CommandResult:
    from devpilot_core.release import InstallPlanBuilder, InstallPlanOptions

    return InstallPlanBuilder(root, options=InstallPlanOptions(mode="all", version=_project_version(root))).build()


def _run_upgrade_check(root: Path) -> CommandResult:
    from devpilot_core.release import UpgradeCheckBuilder, UpgradeCheckOptions

    return UpgradeCheckBuilder(root, options=UpgradeCheckOptions(target_version=_project_version(root))).build()


def _evidence_from_result(tool_id: str, result: CommandResult) -> ReleaseEvidence:
    data = result.data or {}
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    return ReleaseEvidence(
        tool_id=tool_id,
        command=result.command,
        ok=bool(result.ok),
        exit_code=int(result.exit_code),
        summary=dict(summary),
        findings_total=len(result.findings),
    )


def _agent_findings(tool_id: str, result: CommandResult) -> list[Finding]:
    if result.ok:
        return [
            Finding(
                id="RELEASE_AGENT_EVIDENCE_PASS",
                message="ReleaseAgent collected a passing local evidence item.",
                severity=Severity.INFO,
                metadata={"tool_id": tool_id, "command": result.command, "exit_code": int(result.exit_code)},
            )
        ]
    return [
        Finding(
            id="RELEASE_AGENT_EVIDENCE_BLOCK",
            message="ReleaseAgent detected failing or blocking release evidence.",
            severity=Severity.BLOCK if result.exit_code == ExitCode.BLOCK else Severity.FAIL,
            metadata={"tool_id": tool_id, "command": result.command, "exit_code": int(result.exit_code)},
        )
    ] + list(result.findings)


def _release_checklist(*, evidence: list[ReleaseEvidence]) -> list[dict[str, Any]]:
    evidence_by_tool = {item.tool_id: item for item in evidence}
    required = [
        ("quality_gate_release", "release.quality_gate", "Quality gate release profile passes."),
        ("release_manifest", "release.manifest", "Release manifest can be generated from local evidence."),
        ("release_changelog", "release.changelog", "Changelog covers the Fase G sprint range."),
        ("package_build", "release.package", "Package build plan is available and dry-run safe."),
        ("sbom", "release.sbom", "SBOM baseline can be regenerated."),
        ("install_plan", "release.install_plan", "Installation strategy is available."),
        ("upgrade_check", "release.upgrade_check", "Backup/upgrade readiness plan is available."),
    ]
    checklist: list[dict[str, Any]] = []
    for check_id, tool_id, description in required:
        item = evidence_by_tool.get(tool_id)
        checklist.append(
            {
                "id": check_id,
                "description": description,
                "status": "PASS" if item and item.ok else "BLOCK",
                "tool_id": tool_id,
                "command": item.command if item else None,
                "exit_code": item.exit_code if item else None,
            }
        )
    for check_id, status, description in [
        ("no_publish", "PASS", "ReleaseAgent does not publish artifacts."),
        ("no_deploy", "PASS", "ReleaseAgent does not deploy artifacts."),
        ("no_git_tag", "PASS", "ReleaseAgent does not create Git tags."),
        ("dry_run_required", "PASS", "ReleaseAgent MVP is dry-run only."),
    ]:
        checklist.append({"id": check_id, "description": description, "status": status, "tool_id": None, "command": None, "exit_code": 0})
    return checklist


def _suggestions(*, checklist: list[dict[str, Any]], evidence: list[ReleaseEvidence], release_ready: bool) -> list[AgentSuggestion]:
    failed = [item for item in checklist if item["status"] != "PASS"]
    if release_ready:
        return [
            AgentSuggestion(
                title="Release local candidato listo para revisión manual",
                body="La evidencia local requerida para Fase G está en PASS. Mantener revisión humana antes de publicar, firmar, etiquetar o desplegar en sprints futuros.",
                target="FASE-G-PRODUCTIZACION-RELEASE",
                severity="info",
                metadata={"evidence_items_total": len(evidence), "phase_g_closure_candidate": True},
            )
        ]
    return [
        AgentSuggestion(
            title="Release local bloqueado hasta corregir evidencia",
            body="Uno o más checks de release no están en PASS. Revisar findings y comandos asociados antes de cerrar Fase G.",
            target="FASE-G-PRODUCTIZACION-RELEASE",
            severity="fail",
            metadata={"failed_checks": [item["id"] for item in failed]},
        )
    ]


def _project_version(root: Path) -> str:
    try:
        import tomllib

        payload = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        project = payload.get("project") if isinstance(payload.get("project"), dict) else {}
        return str(project.get("version") or "0.1.0")
    except Exception:
        return "0.1.0"


def _security_metadata() -> dict[str, Any]:
    return {
        "dry_run_required": True,
        "network_used": False,
        "external_api_used": False,
        "publishes_artifacts": False,
        "deploys_artifacts": False,
        "git_tagging_performed": False,
        "signing_performed": False,
        "source_mutations_performed": False,
        "runtime_state_mutated": False,
    }
