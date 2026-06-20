from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.compliance import CompliancePackRegistry
from devpilot_core.enterprise import EnterpriseReportBuilder
from devpilot_core.evals import EvalRunner
from devpilot_core.evals.safety import SAFETY_SUITE_IDS
from devpilot_core.identity import IdentityRegistry
from devpilot_core.miasi import MiasiRegistryValidator
from devpilot_core.policy import PolicyEngine, PolicyRequest
from devpilot_core.portfolio import PortfolioStatusBuilder
from devpilot_core.remote import RemoteRunnerStub
from devpilot_core.schemas import SchemaRegistry


@dataclass(frozen=True)
class IndustrialReadinessOptions:
    """Options for the FUNC-SPRINT-99 industrial readiness gate."""

    minimum_score: float = 80.0
    eval_workdir: str = "outputs/evals/workdir_industrial_readiness"
    include_eval_suites: bool = True


class IndustrialReadinessGate:
    """Aggregate Fase H maturity evidence without overclaiming production readiness.

    The gate is intentionally conservative. It passes when critical governance
    controls are present and safe, but it still classifies capabilities as
    production-ready, implemented, implemented-initial, experimental, planned or
    future. This prevents Fase H closure from pretending that every advanced
    feature is production-grade.
    """

    CAPABILITY_ORDER = [
        "contract",
        "policy",
        "security",
        "evals",
        "observability",
        "release",
        "ui_api",
        "multiagent",
        "rag",
        "connectors",
        "enterprise",
    ]

    def __init__(self, root: Path, *, options: IndustrialReadinessOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or IndustrialReadinessOptions()

    def check(self) -> CommandResult:
        policy = PolicyEngine(self.root).evaluate(
            PolicyRequest(
                action="read",
                path="docs/devpilot_backlog_fase_H_capacidades_avanzadas.md",
                dry_run=True,
                tool_id="industrial.readiness.check",
                subject="phase-h-industrial-readiness",
                actor="local-owner",
                metadata={"component": "IndustrialReadinessGate", "sprint": "FUNC-SPRINT-99", "read_only": True},
            )
        )
        if not policy.ok:
            return CommandResult(
                "industrial-readiness check",
                False,
                policy.exit_code,
                "Industrial readiness gate blocked by PolicyEngine.",
                data={"summary": {"policy_engine_used": True, "preliminary": True}},
                findings=policy.findings,
            )

        schemas = SchemaRegistry(self.root).list()
        miasi = MiasiRegistryValidator(self.root).validate_all()
        identity = IdentityRegistry(self.root).validate()
        portfolio = PortfolioStatusBuilder(self.root).build()
        compliance = CompliancePackRegistry(self.root).list()
        remote = RemoteRunnerStub(self.root).status()
        enterprise = EnterpriseReportBuilder(self.root).build()
        evals = self._run_safety_suites() if self.options.include_eval_suites else self._skipped_evals()

        signals = {
            "schemas": schemas,
            "miasi": miasi,
            "identity": identity,
            "portfolio": portfolio,
            "compliance": compliance,
            "remote": remote,
            "enterprise": enterprise,
        }
        capabilities = self._capabilities(signals=signals, evals=evals)
        status_counts: dict[str, int] = {}
        for item in capabilities:
            status_counts[item["status"]] = status_counts.get(item["status"], 0) + 1

        score = self._score(capabilities)
        gaps = self._gaps(capabilities=capabilities, score=score, remote=remote)
        blocking_findings: list[Finding] = []
        if gaps["blocking"]:
            blocking_findings.append(
                Finding(
                    "INDUSTRIAL_READINESS_BLOCKING_GAPS",
                    "Industrial readiness detected blocking gaps.",
                    Severity.BLOCK,
                    metadata={"gaps": gaps["blocking"]},
                )
            )
        if score < self.options.minimum_score:
            blocking_findings.append(
                Finding(
                    "INDUSTRIAL_READINESS_SCORE_BELOW_THRESHOLD",
                    "Industrial readiness score is below threshold.",
                    Severity.BLOCK,
                    metadata={"score": score, "minimum_score": self.options.minimum_score},
                )
            )
        if status_counts.get("production-ready", 0) == len(capabilities):
            blocking_findings.append(
                Finding(
                    "INDUSTRIAL_READINESS_OVERCLAIM_BLOCKED",
                    "Industrial readiness must not mark every advanced capability as production-ready.",
                    Severity.BLOCK,
                    metadata={"capabilities_total": len(capabilities)},
                )
            )

        ok = not blocking_findings
        summary = {
            "phase": "FASE-H-CAPACIDADES-AVANZADAS",
            "phase_h_closed": ok,
            "industrial_readiness_score": score,
            "minimum_score": self.options.minimum_score,
            "maturity_level": "industrial-baseline-ready" if ok else "not-ready",
            "capabilities_total": len(capabilities),
            "production_ready_total": status_counts.get("production-ready", 0),
            "implemented_total": status_counts.get("implemented", 0),
            "implemented_initial_total": status_counts.get("implemented-initial", 0),
            "experimental_total": status_counts.get("experimental", 0),
            "planned_total": status_counts.get("planned", 0),
            "future_total": status_counts.get("future", 0),
            "status_counts": status_counts,
            "gaps_total": len(gaps["blocking"]) + len(gaps["non_blocking"]),
            "blocking_gaps_total": len(gaps["blocking"]),
            "non_blocking_gaps_total": len(gaps["non_blocking"]),
            "policy_engine_used": True,
            "policy_engine_replaced": False,
            "remote_runner_enabled": _summary(remote).get("remote_runner_enabled", False),
            "remote_execution_used": False,
            "cloud_control_plane_enabled": _summary(remote).get("cloud_control_plane_enabled", False),
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "reports_written": False,
            "preliminary": True,
        }
        findings = list(blocking_findings)
        if ok:
            findings.append(
                Finding(
                    "INDUSTRIAL_READINESS_PASS",
                    "Fase H closes with industrial baseline readiness and explicit maturity classification.",
                    Severity.INFO,
                    metadata={"score": score, "maturity_level": summary["maturity_level"]},
                )
            )
        else:
            findings.append(
                Finding(
                    "INDUSTRIAL_READINESS_BLOCK",
                    "Fase H cannot close until blocking readiness gaps are resolved.",
                    Severity.BLOCK,
                    metadata={"score": score, "blocking_gaps": gaps["blocking"]},
                )
            )
        return CommandResult(
            "industrial-readiness check",
            ok,
            ExitCode.PASS if ok else ExitCode.BLOCK,
            "Industrial readiness gate passed with explicit maturity boundaries." if ok else "Industrial readiness gate blocked.",
            data={
                "summary": summary,
                "capabilities": capabilities,
                "gaps": gaps,
                "signals": {key: _summary(result) for key, result in signals.items()},
                "evals": evals,
                "policy": policy.data,
                "notes": [
                    "FUNC-SPRINT-99 closes Fase H as an industrial baseline, not as a claim that every subsystem is production-grade.",
                    "Capabilities marked implemented-initial or experimental require hardening before production/enterprise deployment.",
                ],
            },
            findings=findings,
        )

    def _run_safety_suites(self) -> dict[str, Any]:
        runner = EvalRunner(self.root, config=None)
        suites = [
            "advanced-agentic",
            "red-team",
            "plugin-ecosystem",
            "multiworkspace-isolation",
            "identity-rbac",
            "audit-pack-integrity",
            "compliance-pack-integrity",
            "remote-enterprise",
        ]
        missing = sorted(set(SAFETY_SUITE_IDS) - set(suites))
        results = [runner.run(suite=suite) for suite in suites]
        scores = {suite: _summary(result).get("safety_score") for suite, result in zip(suites, results)}
        return {
            "suites": suites,
            "missing_registered_suites": missing,
            "suites_total": len(suites),
            "suites_passed": sum(1 for result in results if result.ok),
            "all_passed": all(result.ok for result in results) and not missing,
            "safety_scores": scores,
            "false_negatives_total": sum(int(_summary(result).get("false_negatives") or 0) for result in results),
            "network_used": False,
            "external_api_used": False,
            "llm_judge_used": False,
            "outputs_written": True,
        }

    def _skipped_evals(self) -> dict[str, Any]:
        return {
            "suites": [],
            "suites_total": 0,
            "suites_passed": 0,
            "all_passed": False,
            "safety_scores": {},
            "false_negatives_total": 0,
            "network_used": False,
            "external_api_used": False,
            "llm_judge_used": False,
            "outputs_written": False,
        }

    def _capabilities(self, *, signals: dict[str, CommandResult], evals: dict[str, Any]) -> list[dict[str, Any]]:
        root = self.root
        remote_summary = _summary(signals["remote"])
        enterprise_summary = _summary(signals["enterprise"])
        miasi_summary = _summary(signals["miasi"])
        schema_summary = _summary(signals["schemas"])
        compliance_summary = _summary(signals["compliance"])
        components = [
            self._capability(
                "contract",
                "Contracts, schemas and validation gateway",
                "production-ready" if signals["schemas"].ok and schema_summary.get("schemas_total", 0) >= 23 else "implemented-initial",
                signals["schemas"].ok and schema_summary.get("schemas_existing", 0) >= 23,
                100,
                ["docs/schemas/schema_catalog.json", "docs/schemas/functional_sprint_manifest.schema.json"],
                "Production-ready for local schema catalog integrity; semantic validators keep evolving.",
            ),
            self._capability(
                "policy",
                "PolicyEngine, MIASI and deny-by-default matrix",
                "implemented",
                signals["miasi"].ok and miasi_summary.get("policy_rules_total", 0) >= 90,
                95,
                [".devpilot/miasi/policy_matrix.json", "src/devpilot_core/policy"],
                "Strong local policy baseline; enterprise IAM/policy distribution remains future work.",
            ),
            self._capability(
                "security",
                "Security, RBAC, approvals and secret boundaries",
                "implemented-initial",
                signals["identity"].ok and remote_summary.get("remote_runner_enabled") is False,
                90,
                [".devpilot/identity/identity_registry.json", "docs/03_security/security_threat_model.md"],
                "RBAC and safety controls exist locally; production IAM/session hardening remains pending.",
            ),
            self._capability(
                "evals",
                "Advanced deterministic safety and red-team evals",
                "implemented",
                bool(evals.get("all_passed")) and int(evals.get("false_negatives_total") or 0) == 0,
                95,
                ["evals/fixtures", "src/devpilot_core/evals"],
                "Deterministic local eval harness passes; broader adversarial coverage and real-world datasets remain pending.",
            ),
            self._capability(
                "observability",
                "Reports, traces, AgentOps and operational evidence",
                "implemented-initial",
                (root / "docs/05_operations/observability_plan.md").is_file() and (root / "src/devpilot_core/observability").is_dir(),
                85,
                ["docs/05_operations/observability_plan.md", "src/devpilot_core/observability"],
                "Local observability exists; production telemetry backend and retention model remain future work.",
            ),
            self._capability(
                "release",
                "Productization/release dry-run baseline",
                "implemented-initial",
                (root / "docs/release/CHANGELOG.md").is_file() and (root / "src/devpilot_core/release").is_dir(),
                82,
                ["src/devpilot_core/release", "docs/release/CHANGELOG.md"],
                "Release tooling is local dry-run; publishing/deployment remain denied.",
            ),
            self._capability(
                "ui_api",
                "Local Web UI/API boundary and application facade",
                "implemented-initial",
                (root / "ui/web/package.json").is_file() and (root / "src/devpilot_core/application").is_dir(),
                70,
                ["ui/web", "src/devpilot_core/application"],
                "Web UI is MVP/local smoke-tested; full API/server/desktop productization remains pending.",
            ),
            self._capability(
                "multiagent",
                "MultiAgentCoordinator and governed handoffs",
                "implemented-initial",
                (root / "src/devpilot_core/multiagent").is_dir() and (root / ".devpilot/workflows/sdlc_review.json").is_file(),
                75,
                ["src/devpilot_core/multiagent", ".devpilot/workflows/sdlc_review.json"],
                "Dry-run workflows and handoffs exist; open-ended autonomy remains disabled.",
            ),
            self._capability(
                "rag",
                "Local RAG over documentation with evidence",
                "implemented-initial",
                (root / "src/devpilot_core/rag").is_dir() and (root / ".devpilot/rag/docs_index.json").is_file(),
                78,
                ["src/devpilot_core/rag", ".devpilot/rag/docs_index.json"],
                "Lexical local RAG exists; semantic/vector/quality reranking hardening remains future work.",
            ),
            self._capability(
                "connectors",
                "Connector/MCP MVP and plugin ecosystem",
                "implemented-initial",
                (root / "src/devpilot_core/connectors").is_dir() and (root / ".devpilot/connectors/connector_registry.json").is_file(),
                80,
                ["src/devpilot_core/connectors", ".devpilot/connectors/connector_registry.json"],
                "Read-only connectors and plugin metadata are governed; write connectors remain denied/future.",
            ),
            self._capability(
                "enterprise",
                "Multiworkspace, compliance, audit packs and enterprise report",
                "experimental" if remote_summary.get("experimental") is True else "implemented-initial",
                signals["portfolio"].ok and signals["compliance"].ok and signals["enterprise"].ok and enterprise_summary.get("gaps_total", 1) == 0,
                76,
                ["src/devpilot_core/enterprise", ".devpilot/compliance/packs.json", ".devpilot/remote/runner_registry.json"],
                "Enterprise reporting is local/read-only; remote runner remains experimental and disabled by design.",
            ),
        ]
        return components

    def _capability(self, capability_id: str, title: str, status: str, ok: bool, score: int, evidence: list[str], note: str) -> dict[str, Any]:
        if not ok:
            score = min(score, 40)
        return {
            "id": capability_id,
            "title": title,
            "status": status,
            "ok": ok,
            "score": score,
            "evidence": evidence,
            "note": note,
        }

    def _score(self, capabilities: list[dict[str, Any]]) -> float:
        if not capabilities:
            return 0.0
        return round(sum(float(item.get("score", 0)) for item in capabilities) / len(capabilities), 2)

    def _gaps(self, *, capabilities: list[dict[str, Any]], score: float, remote: CommandResult) -> dict[str, list[dict[str, Any]]]:
        blocking: list[dict[str, Any]] = []
        non_blocking: list[dict[str, Any]] = []
        for item in capabilities:
            if not item["ok"]:
                blocking.append({"capability": item["id"], "reason": "required evidence or gate failed"})
            elif item["status"] in {"implemented-initial", "experimental", "planned", "future"}:
                non_blocking.append({"capability": item["id"], "status": item["status"], "reason": item["note"]})
        remote_summary = _summary(remote)
        if remote_summary.get("remote_runner_enabled") is True or remote_summary.get("execution_allowed") is True:
            blocking.append({"capability": "enterprise", "reason": "remote runner must remain disabled for Fase H closure"})
        if score < self.options.minimum_score:
            blocking.append({"capability": "score", "reason": "industrial readiness score below threshold"})
        return {"blocking": blocking, "non_blocking": non_blocking}


def _summary(result: CommandResult) -> dict[str, Any]:
    data = result.data or {}
    summary = data.get("summary") if isinstance(data, dict) else None
    return summary if isinstance(summary, dict) else {}
