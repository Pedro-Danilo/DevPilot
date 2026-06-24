from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.maturity.models import (
    CapabilityStatus,
    MaturityCapability,
    MaturityDashboard,
    MaturityLevel,
    RiskLevel,
    RoadmapDependency,
    SafetySignal,
    TestCoverageLevel,
)
from devpilot_core.maturity.sources import PostHSourceBundle, PostHSourceReader, SourceReadResult
from devpilot_core.schemas import SchemaValidator


@dataclass(frozen=True)
class DashboardBuildResult:
    """In-memory build result for POST-H-002-C.

    The builder remains read-only: it builds JSON/Markdown payloads in memory,
    validates the JSON against ``MaturityDashboard`` and does not write reports.
    Report persistence and CLI exposure are intentionally deferred to
    POST-H-002-D.
    """

    dashboard: MaturityDashboard | None
    markdown: str
    findings: list[Finding]
    source_bundle: PostHSourceBundle

    @property
    def ok(self) -> bool:
        return self.dashboard is not None and not any(
            finding.severity in {Severity.BLOCK, Severity.ERROR} for finding in self.findings
        )

    @property
    def exit_code(self) -> ExitCode:
        return ExitCode.PASS if self.ok else ExitCode.BLOCK

    def to_command_result(self) -> CommandResult:
        return CommandResult(
            command="maturity dashboard build",
            ok=self.ok,
            exit_code=self.exit_code,
            message="Maturity dashboard built in memory." if self.ok else "Maturity dashboard build has blocking findings.",
            data={
                "dashboard": self.dashboard.to_dict() if self.dashboard else None,
                "markdown": self.markdown,
                "summary": self.dashboard.summary() if self.dashboard else {},
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "preliminary": True,
            },
            findings=self.findings,
        )


class MaturityDashboardBuilder:
    """Build a local evidence-backed maturity dashboard from POST-H sources.

    POST-H-002-C consumes the source bundle from POST-H-002-B and maps the
    machine-readable assessment into a schema-backed ``MaturityDashboard``.
    It intentionally does not add CLI handlers and does not write
    ``outputs/reports``; those behaviors are scheduled for POST-H-002-D.
    """

    dashboard_id = "POST-H-002-MATURITY-DASHBOARD"

    def __init__(self, root: str | Path, *, source_reader: PostHSourceReader | None = None) -> None:
        self.root = Path(root).resolve()
        self.source_reader = source_reader or PostHSourceReader(self.root)

    def build(
        self,
        *,
        source_bundle: PostHSourceBundle | None = None,
        generated_at_utc: str | None = None,
    ) -> DashboardBuildResult:
        bundle = source_bundle or self.source_reader.read_all(include_markdown=True)
        findings = list(bundle.findings)
        if not bundle.ok:
            findings.append(
                Finding(
                    id="MATURITY_DASHBOARD_BUILD_BLOCKED_BY_SOURCES",
                    message="Maturity dashboard cannot be built because source bundle has blocking findings.",
                    severity=Severity.BLOCK,
                )
            )
            return DashboardBuildResult(dashboard=None, markdown="", findings=findings, source_bundle=bundle)

        generated_at = generated_at_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        manifest = _payload_dict(bundle.source_by_id("post_h_eval_manifest"))
        roadmap = _payload_dict(bundle.source_by_id("prioritized_roadmap"))
        decision_matrix = _payload_dict(bundle.source_by_id("decision_matrix"))
        security = _payload_dict(bundle.source_by_id("security_risk_register"))
        test_cost = _payload_dict(bundle.source_by_id("test_cost_assessment"))
        contracts = _payload_dict(bundle.source_by_id("test_contract_registry"))

        capabilities = self._build_capabilities(decision_matrix, security, contracts)
        roadmap_alignment = self._build_roadmap_alignment(roadmap, security)
        dashboard = MaturityDashboard(
            dashboard_id=self.dashboard_id,
            generated_at_utc=generated_at,
            roadmap_version=str(roadmap.get("version") or "unknown"),
            post_h_eval_status=str(manifest.get("status") or "unknown"),
            capabilities=capabilities,
            roadmap_alignment=roadmap_alignment,
            safety=self._build_safety_signal(manifest, decision_matrix, security, roadmap, test_cost),
            preliminary=True,
        )

        validation = SchemaValidator(self.root).validate_payload(
            schema="MaturityDashboard",
            payload=dashboard.to_dict(),
            instance_label="in-memory:maturity-dashboard",
        )
        findings.extend(validation.findings)
        if validation.ok:
            findings.append(
                Finding(
                    id="MATURITY_DASHBOARD_SCHEMA_PASS",
                    message="Maturity dashboard payload conforms to schema.",
                    severity=Severity.INFO,
                    metadata=dashboard.summary(),
                )
            )
        else:
            findings.append(
                Finding(
                    id="MATURITY_DASHBOARD_SCHEMA_BLOCK",
                    message="Maturity dashboard payload does not conform to schema.",
                    severity=Severity.BLOCK,
                )
            )

        markdown = render_maturity_dashboard_markdown(dashboard, source_paths=bundle.evidence_paths())
        findings.append(
            Finding(
                id="MATURITY_DASHBOARD_BUILT_READ_ONLY",
                message="Maturity dashboard built without network, external APIs or mutations.",
                severity=Severity.INFO,
                metadata={
                    "capabilities_total": len(capabilities),
                    "roadmap_alignment_total": len(roadmap_alignment),
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "preliminary": True,
                },
            )
        )
        return DashboardBuildResult(dashboard=dashboard, markdown=markdown, findings=findings, source_bundle=bundle)

    def _build_capabilities(
        self,
        decision_matrix: Mapping[str, Any],
        security: Mapping[str, Any],
        contracts: Mapping[str, Any],
    ) -> list[MaturityCapability]:
        domains = decision_matrix.get("domains")
        capabilities: list[MaturityCapability] = []
        if isinstance(domains, list):
            for domain in domains:
                if not isinstance(domain, Mapping):
                    continue
                evidence = _extract_evidence_paths(domain.get("evidence"))
                matching_contracts = _matching_contract_ids(evidence, contracts)
                status = _map_status(domain.get("maturity"))
                risk = _map_risk(domain.get("risk_level"))
                roadmap_dependency = _domain_roadmap_dependency(str(domain.get("domain_id") or ""))
                capabilities.append(
                    MaturityCapability(
                        capability_id=str(domain.get("domain_id") or "unknown-domain"),
                        name=str(domain.get("domain") or domain.get("domain_id") or "Unknown domain"),
                        domain=str(domain.get("category") or "unknown"),
                        status=status,
                        maturity=_derive_maturity(status, risk),
                        test_coverage=_derive_test_coverage(status, matching_contracts, str(domain.get("domain_id") or "")),
                        risk=risk,
                        source_evidence=evidence or [".devpilot/evals/post_h_eval_001_decision_matrix.json"],
                        roadmap_dependency=roadmap_dependency,
                        no_go_gate=_is_domain_no_go(str(domain.get("domain_id") or ""), status, risk),
                        notes=[str(domain.get("rationale"))] if domain.get("rationale") else [],
                        metadata={
                            "priority": domain.get("priority"),
                            "recommended_action": domain.get("recommended_action"),
                            "matching_contracts": matching_contracts,
                            "blocking_conditions": domain.get("blocking_conditions") or [],
                        },
                    )
                )

        capabilities.extend(_blocked_capabilities_from_security(security))
        return sorted(capabilities, key=lambda item: (item.domain, item.capability_id))

    def _build_roadmap_alignment(self, roadmap: Mapping[str, Any], security: Mapping[str, Any]) -> list[RoadmapDependency]:
        dependencies: dict[str, RoadmapDependency] = {}
        for item in roadmap.get("executable_backlogs_to_create", []) if isinstance(roadmap.get("executable_backlogs_to_create"), list) else []:
            if not isinstance(item, Mapping):
                continue
            milestone = str(item.get("milestone") or "").strip()
            if not milestone:
                continue
            unblocks = [_unblock_from_path(str(item.get("path") or milestone))]
            dependencies[milestone] = RoadmapDependency(
                milestone=milestone,
                unblocks=unblocks,
                priority=str(item.get("priority") or _priority_from_milestone(milestone)),
            )
        for risk in security.get("risks", []) if isinstance(security.get("risks"), list) else []:
            if not isinstance(risk, Mapping):
                continue
            milestone = _milestone_from_recommended_sprint(str(risk.get("recommended_sprint") or ""))
            if not milestone:
                continue
            current = dependencies.get(milestone)
            unblock = str(risk.get("id") or risk.get("title") or milestone)
            if current:
                merged = sorted(dict.fromkeys([*current.unblocks, unblock]))
                dependencies[milestone] = RoadmapDependency(milestone=milestone, unblocks=merged, priority=current.priority)
            else:
                dependencies[milestone] = RoadmapDependency(milestone=milestone, unblocks=[unblock], priority=str(risk.get("priority") or _priority_from_milestone(milestone)))
        return [dependencies[key] for key in sorted(dependencies)]

    def _build_safety_signal(self, *payloads: Mapping[str, Any]) -> SafetySignal:
        # Safety remains deny-by-default regardless of source wording. If a
        # source ever reports enablement, schema validation would still block the
        # dashboard because SafetySignal is fixed to false values here.
        return SafetySignal(
            remote_execution_enabled=False,
            connector_write_enabled=False,
            plugin_execution_enabled=False,
            external_apis_enabled_by_default=False,
            network_used=False,
            mutations_performed=False,
            preliminary=True,
        )


def render_maturity_dashboard_markdown(dashboard: MaturityDashboard, *, source_paths: Sequence[str] = ()) -> str:
    """Render a human-readable local maturity dashboard report."""

    payload = dashboard.to_dict()
    summary = payload["summary"]
    safety = payload["safety"]
    lines = [
        "# DevPilot Local — Maturity Dashboard",
        "",
        f"Dashboard ID: `{dashboard.dashboard_id}`  ",
        f"Generated at UTC: `{dashboard.generated_at_utc}`  ",
        f"Roadmap version: `{dashboard.roadmap_version}`  ",
        f"POST-H-EVAL status: `{dashboard.post_h_eval_status}`  ",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for key in (
        "capabilities_total",
        "production_ready_local_total",
        "implemented_total",
        "implemented_initial_total",
        "experimental_total",
        "planned_total",
        "stub_total",
        "blocked_total",
        "critical_risks_total",
        "blocking_gaps_total",
    ):
        lines.append(f"| `{key}` | {summary[key]} |")
    lines.extend(
        [
            "",
            "## Safety no-go gates",
            "",
            "| Gate | Value |",
            "|---|---:|",
        ]
    )
    for key in (
        "remote_execution_enabled",
        "connector_write_enabled",
        "plugin_execution_enabled",
        "external_apis_enabled_by_default",
        "network_used",
        "mutations_performed",
    ):
        lines.append(f"| `{key}` | `{str(safety[key]).lower()}` |")
    lines.extend(
        [
            "",
            "## Capabilities",
            "",
            "| Capability | Domain | Status | Maturity | Tests | Risk | Roadmap | No-go |",
            "|---|---|---|---|---|---|---|---:|",
        ]
    )
    for capability in dashboard.capabilities:
        lines.append(
            "| "
            f"{_md_escape(capability.name)} | "
            f"`{_md_escape(capability.domain)}` | "
            f"`{capability.status.value}` | "
            f"`{capability.maturity.value}` | "
            f"`{capability.test_coverage.value}` | "
            f"`{capability.risk.value}` | "
            f"`{capability.roadmap_dependency or 'n/a'}` | "
            f"`{str(capability.no_go_gate).lower()}` |"
        )
    lines.extend(
        [
            "",
            "## Roadmap alignment",
            "",
            "| Milestone | Priority | Unblocks |",
            "|---|---|---|",
        ]
    )
    for dependency in dashboard.roadmap_alignment:
        lines.append(f"| `{dependency.milestone}` | `{dependency.priority}` | {_md_escape(', '.join(dependency.unblocks))} |")
    lines.extend(
        [
            "",
            "## Evidence sources",
            "",
        ]
    )
    for path in source_paths:
        lines.append(f"- `{path}`")
    lines.extend(
        [
            "",
            "## Explicit limitations",
            "",
            "This report is generated in memory by POST-H-002-C. It is an implemented-initial builder/rendering capability, not the final CLI workflow.",
            "It does not enable remote execution, connector write, plugin execution, external APIs or source mutations.",
            "Persistent report writing under outputs/reports and CLI exposure are deferred to POST-H-002-D.",
            "It does not declare enterprise readiness, remote readiness, compliance certification or generic production readiness.",
        ]
    )
    return "\n".join(lines) + "\n"


def _payload_dict(source: SourceReadResult | None) -> Mapping[str, Any]:
    if source and isinstance(source.payload, Mapping):
        return source.payload
    return {}


def _extract_evidence_paths(value: Any) -> list[str]:
    paths: list[str] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, Mapping):
                path = item.get("path")
                if path and item.get("exists", True):
                    paths.append(str(path))
            elif isinstance(item, str):
                paths.append(item)
    return sorted(dict.fromkeys(paths))


def _matching_contract_ids(evidence_paths: Sequence[str], contracts_payload: Mapping[str, Any]) -> list[str]:
    contracts = contracts_payload.get("contracts")
    if not isinstance(contracts, list):
        return []
    normalized_evidence = [_normalize_path(path) for path in evidence_paths]
    matches: list[str] = []
    for contract in contracts:
        if not isinstance(contract, Mapping):
            continue
        candidates: list[str] = []
        for key in ("watched_paths", "validates", "test_files"):
            value = contract.get(key)
            if isinstance(value, list):
                candidates.extend(str(item) for item in value)
        normalized_candidates = [_normalize_path(path) for path in candidates]
        if any(_paths_overlap(evidence, candidate) for evidence in normalized_evidence for candidate in normalized_candidates):
            contract_id = str(contract.get("contract_id") or "")
            if contract_id:
                matches.append(contract_id)
    return sorted(dict.fromkeys(matches))[:10]


def _paths_overlap(left: str, right: str) -> bool:
    return bool(left and right and (left.startswith(right.rstrip("/") + "/") or right.startswith(left.rstrip("/") + "/") or left == right))


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip().lstrip("./")


def _map_status(value: Any) -> CapabilityStatus:
    text = str(value or "implemented-initial").strip().lower()
    aliases = {
        "production-ready-local": CapabilityStatus.PRODUCTION_READY_LOCAL,
        "implemented": CapabilityStatus.IMPLEMENTED,
        "implemented-initial": CapabilityStatus.IMPLEMENTED_INITIAL,
        "experimental": CapabilityStatus.EXPERIMENTAL,
        "planned": CapabilityStatus.PLANNED,
        "stub": CapabilityStatus.STUB,
        "blocked": CapabilityStatus.BLOCKED,
    }
    return aliases.get(text, CapabilityStatus.IMPLEMENTED_INITIAL)


def _map_risk(value: Any) -> RiskLevel:
    text = str(value or "medium").strip().lower().replace("_", "-")
    aliases = {
        "crítica": RiskLevel.CRITICO,
        "critica": RiskLevel.CRITICO,
        "critical": RiskLevel.CRITICO,
        "alta": RiskLevel.ALTO,
        "alto": RiskLevel.ALTO,
        "high": RiskLevel.ALTO,
        "medium-high": RiskLevel.MEDIO_ALTO,
        "medio-alto": RiskLevel.MEDIO_ALTO,
        "media-alta": RiskLevel.MEDIO_ALTO,
        "medium": RiskLevel.MEDIO,
        "medio": RiskLevel.MEDIO,
        "media": RiskLevel.MEDIO,
        "low": RiskLevel.BAJO,
        "bajo": RiskLevel.BAJO,
        "baja": RiskLevel.BAJO,
    }
    return aliases.get(text, RiskLevel.MEDIO)


def _derive_maturity(status: CapabilityStatus, risk: RiskLevel) -> MaturityLevel:
    if status == CapabilityStatus.PRODUCTION_READY_LOCAL:
        return MaturityLevel.ALTA_LOCAL
    if status == CapabilityStatus.IMPLEMENTED:
        return MaturityLevel.MEDIA if risk in {RiskLevel.ALTO, RiskLevel.CRITICO} else MaturityLevel.MEDIA_ALTA
    if status == CapabilityStatus.IMPLEMENTED_INITIAL:
        return MaturityLevel.BAJA if risk == RiskLevel.ALTO else MaturityLevel.MEDIA
    if status in {CapabilityStatus.EXPERIMENTAL, CapabilityStatus.STUB}:
        return MaturityLevel.BAJA
    return MaturityLevel.NO_HABILITADA


def _derive_test_coverage(status: CapabilityStatus, matching_contracts: Sequence[str], domain_id: str) -> TestCoverageLevel:
    if domain_id in {"schemas_contracts", "project_state", "quality_gates"}:
        return TestCoverageLevel.ALTA
    if matching_contracts:
        return TestCoverageLevel.MEDIA_ALTA if status in {CapabilityStatus.PRODUCTION_READY_LOCAL, CapabilityStatus.IMPLEMENTED} else TestCoverageLevel.MEDIA
    if status == CapabilityStatus.PRODUCTION_READY_LOCAL:
        return TestCoverageLevel.MEDIA_ALTA
    if status == CapabilityStatus.IMPLEMENTED:
        return TestCoverageLevel.MEDIA
    if status == CapabilityStatus.IMPLEMENTED_INITIAL:
        return TestCoverageLevel.BAJA
    return TestCoverageLevel.NA if status in {CapabilityStatus.PLANNED, CapabilityStatus.BLOCKED} else TestCoverageLevel.BAJA


def _is_domain_no_go(domain_id: str, status: CapabilityStatus, risk: RiskLevel) -> bool:
    return domain_id in {"remote_runner_stub", "connectors_mcp", "plugin_registry", "enterprise_reports"} or status == CapabilityStatus.BLOCKED or risk == RiskLevel.CRITICO


DOMAIN_ROADMAP_DEPENDENCIES: dict[str, str] = {
    "core_cli": "POST-H-006",
    "application_services": "POST-H-007",
    "schemas_contracts": "POST-H-003",
    "project_state": "POST-H-008",
    "quality_gates": "POST-H-002",
    "testing_contracts": "POST-H-003",
    "policy_engine": "POST-H-004",
    "miasi": "POST-H-004",
    "approval": "POST-H-012",
    "rbac_identity": "POST-H-012",
    "security_guards": "POST-H-012",
    "agent_runtime": "POST-H-004",
    "sdlc_agents": "POST-H-004",
    "multiagent_coordinator": "POST-H-004",
    "multiagent_workflows": "POST-H-004",
    "rag_local": "POST-H-011",
    "connectors_mcp": "POST-H-018",
    "plugin_registry": "POST-H-019",
    "multiworkspace": "POST-H-016",
    "observability_agentops": "POST-H-010",
    "audit_packs": "POST-H-013",
    "compliance_packs": "POST-H-020",
    "release_dry_run": "POST-H-017",
    "remote_runner_stub": "POST-H-021",
    "enterprise_reports": "POST-H-022",
    "web_ui": "POST-H-014",
    "api_local": "POST-H-014",
    "documentation_governance": "POST-H-009",
}


def _domain_roadmap_dependency(domain_id: str) -> str | None:
    return DOMAIN_ROADMAP_DEPENDENCIES.get(domain_id)


def _blocked_capabilities_from_security(security: Mapping[str, Any]) -> list[MaturityCapability]:
    capabilities: list[MaturityCapability] = []
    for risk in security.get("risks", []) if isinstance(security.get("risks"), list) else []:
        if not isinstance(risk, Mapping):
            continue
        risk_id = str(risk.get("id") or "")
        if risk_id not in {"SEC-001", "SEC-002", "SEC-003"}:
            continue
        title = str(risk.get("title") or risk_id)
        evidence = [str(item) for item in risk.get("evidence", [])] if isinstance(risk.get("evidence"), list) else [".devpilot/evals/post_h_eval_001_security_risk_register.json"]
        milestone = _milestone_from_recommended_sprint(str(risk.get("recommended_sprint") or ""))
        capabilities.append(
            MaturityCapability(
                capability_id=f"no-go-{risk_id.lower()}",
                name=f"No-go: {title}",
                domain="safety",
                status=CapabilityStatus.BLOCKED,
                maturity=MaturityLevel.NO_HABILITADA,
                test_coverage=TestCoverageLevel.NA,
                risk=_map_risk(risk.get("severity")),
                source_evidence=evidence,
                roadmap_dependency=milestone,
                no_go_gate=True,
                notes=[str(risk.get("mitigation"))] if risk.get("mitigation") else [],
                metadata={
                    "security_risk_id": risk_id,
                    "priority": risk.get("priority"),
                    "status": risk.get("status"),
                    "closure_criteria": risk.get("closure_criteria"),
                },
            )
        )
    return capabilities


def _milestone_from_recommended_sprint(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    return value.split("—", 1)[0].strip()


def _unblock_from_path(value: str) -> str:
    name = Path(value).stem
    for prefix in ("POST-H-", "post_h_", "POST_H_"):
        name = name.replace(prefix, "")
    return name.strip("_") or value


def _priority_from_milestone(milestone: str) -> str:
    p0 = {"POST-H-002", "POST-H-003", "POST-H-004", "POST-H-005"}
    p1 = {"POST-H-006", "POST-H-007", "POST-H-008", "POST-H-009", "POST-H-010", "POST-H-011", "POST-H-012", "POST-H-013", "POST-H-014", "POST-H-015", "POST-H-016", "POST-H-017", "POST-H-024"}
    p2 = {"POST-H-018", "POST-H-019", "POST-H-020"}
    if milestone in p0:
        return "P0"
    if milestone in p1:
        return "P1"
    if milestone in p2:
        return "P2"
    return "P3"


def _md_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
