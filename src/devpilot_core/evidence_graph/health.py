from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.evidence_graph.builder import EvidenceGraphBuilder, EvidenceGraphOptions

POST_H_031_B_CREATED_BY = "POST-H-031-B"
OPERATOR_HEALTH_SCHEMA_ID = "SCHEMA-DEVPL-OPERATOR-HEALTH-SUMMARY-V1"
OPERATOR_HEALTH_CONTRACT = "OperatorHealthSummary"
OPERATOR_HEALTH_SUMMARY_ID = "devpilot-operator-health-summary"
DEFAULT_OPERATOR_HEALTH_CONFIG = Path(".devpilot/operator/operator_health_config.json")
DEFAULT_OPERATOR_HEALTH_OUTPUT_JSON = Path("outputs/reports/operator_health_summary.json")
DEFAULT_OPERATOR_HEALTH_OUTPUT_MARKDOWN = Path("outputs/reports/operator_health_summary.md")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _display_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _source_ref(path: str, *, kind: str = "json", required: bool = False, available: bool = False, description: str = "") -> dict[str, Any]:
    return {
        "path": _display_path(path),
        "kind": kind,
        "required": bool(required),
        "available": bool(available),
        "description": description or _display_path(path),
    }


@dataclass(frozen=True)
class OperatorHealthOptions:
    config_path: Path = DEFAULT_OPERATOR_HEALTH_CONFIG
    write_report: bool = False
    output_json: Path = DEFAULT_OPERATOR_HEALTH_OUTPUT_JSON
    output_markdown: Path = DEFAULT_OPERATOR_HEALTH_OUTPUT_MARKDOWN


class OperatorHealthSummaryBuilder:
    """Build a local operator health summary from evidence graph signals.

    The summary is a read-only operator view. It does not execute recommended
    commands, does not regenerate runtime evidence and does not replace formal
    quality gates or production-ready-local declarations.
    """

    def __init__(self, root: Path, options: OperatorHealthOptions | None = None) -> None:
        self.root = Path(root)
        self.options = options or OperatorHealthOptions()

    @property
    def config_path(self) -> Path:
        return self.root / self.options.config_path

    def build(self) -> CommandResult:
        config = self._load_config()
        graph_result = EvidenceGraphBuilder(
            self.root,
            EvidenceGraphOptions(sources_path=Path(config.get("evidence_graph_sources_path") or ".devpilot/evidence/evidence_graph_sources.json")),
        ).build()
        graph = ((graph_result.data or {}).get("graph") or {}) if isinstance(graph_result.data, dict) else {}
        graph_summary = graph.get("summary") if isinstance(graph.get("summary"), dict) else {}
        nodes = graph.get("nodes") if isinstance(graph.get("nodes"), list) else []

        findings: list[Finding] = []
        findings.extend(graph_result.findings or [])

        claim_summary = self._claim_summary(nodes)
        no_go_summary = self._no_go_summary(nodes)
        evidence_quality = self._evidence_quality(graph_summary, nodes)
        sections = self._sections(config, graph, evidence_quality, claim_summary, no_go_summary)
        top_actions = self._top_actions(config, nodes)

        blocking_findings_total = int(evidence_quality.get("blocking_findings_total", 0))
        blocking_gaps_total = int(evidence_quality.get("blocking_gaps_total", 0))
        no_go_violations = int(no_go_summary.get("violations_total", 0))
        forbidden_available = int(claim_summary.get("forbidden_available_total", 0))
        missing_expected = int(evidence_quality.get("missing_expected_total", 0))

        overall_status = self._overall_status(
            blocking_findings_total=blocking_findings_total,
            blocking_gaps_total=blocking_gaps_total,
            no_go_violations=no_go_violations,
            forbidden_available=forbidden_available,
            missing_expected=missing_expected,
            graph_ok=bool(graph_result.ok),
        )
        health_score = self._health_score(
            overall_status=overall_status,
            missing_expected=missing_expected,
            warnings_total=sum(int(section.get("warnings_total", 0)) for section in sections),
            blocking_findings_total=blocking_findings_total,
            blocking_gaps_total=blocking_gaps_total,
            no_go_violations=no_go_violations,
            forbidden_available=forbidden_available,
        )
        decision = "BLOCK" if overall_status == "red" else "PASS"

        summary = {
            "schema_version": "1.0",
            "schema_id": OPERATOR_HEALTH_SCHEMA_ID,
            "summary_id": OPERATOR_HEALTH_SUMMARY_ID,
            "created_by": POST_H_031_B_CREATED_BY,
            "status": "blocked" if decision == "BLOCK" else ("warn" if overall_status == "yellow" else "pass"),
            "generated_at_utc": _utc_now(),
            "overall_status": overall_status,
            "decision": decision,
            "health_score": health_score,
            "sections": sections,
            "evidence_quality": evidence_quality,
            "claims": claim_summary,
            "no_go_gates": no_go_summary,
            "top_actions": top_actions,
            "safety": {
                "local_first": True,
                "read_only": True,
                "dry_run": True,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "commands_executed": False,
                "secrets_read": False,
                "raw_payloads_exported": False,
                "devpilot_db_read": False,
                "reports_written": bool(self.options.write_report),
            },
            "limitations": [
                "OperatorHealthSummary is an operator summary, not a formal readiness declaration.",
                "It does not execute recommended commands; top_actions are operator instructions only.",
                "Formal PASS/BLOCK remains owned by quality gates, production-ready-local and future POST-H-031 dashboards.",
                "Runtime evidence under outputs/ is treated as regenerable and not versioned source of truth.",
            ],
            "findings": [finding.to_dict() for finding in findings] or [
                Finding("OPERATOR_HEALTH_SUMMARY_READY", "Operator health summary built from local evidence graph metadata.", Severity.INFO).to_dict()
            ],
            "notes": [
                "POST-H-031-B synthesizes evidence graph, project state, claims, no-go gates, TCR/docs governance source presence and runtime evidence availability.",
                "POST-H-031-C will expand full gap-to-action rules beyond the top-actions list included here.",
            ],
        }

        if self.options.write_report:
            self._write_reports(summary)

        result_findings = [Finding("OPERATOR_HEALTH_SUMMARY_READY", "Operator health summary is available.", Severity.INFO, metadata={"overall_status": overall_status, "health_score": health_score})]
        return CommandResult(
            command="evidence health",
            ok=decision == "PASS",
            exit_code=ExitCode.PASS if decision == "PASS" else ExitCode.BLOCK,
            message="Operator health summary built." if decision == "PASS" else "Operator health summary has blocking issues.",
            data={"summary": self._command_summary(summary), "health": summary},
            findings=result_findings,
        )

    def _load_config(self) -> dict[str, Any]:
        payload = _load_json(self.config_path)
        return payload if payload else {"evidence_graph_sources_path": ".devpilot/evidence/evidence_graph_sources.json", "recommended_runtime_actions": {}}

    def _claim_summary(self, nodes: list[Any]) -> dict[str, Any]:
        allowed: list[str] = []
        prohibited: list[str] = []
        forbidden_available = 0
        for node in nodes:
            if not isinstance(node, dict) or node.get("node_type") != "claim":
                continue
            title = str(node.get("title") or node.get("node_id") or "")
            status = str(node.get("status") or "unknown")
            if status == "allowed":
                allowed.append(title)
            elif status == "prohibited":
                prohibited.append(title)
            else:
                if title != "production-ready-local":
                    forbidden_available += 1
        return {
            "allowed": sorted(allowed),
            "prohibited": sorted(prohibited),
            "forbidden_available_total": forbidden_available,
        }

    def _no_go_summary(self, nodes: list[Any]) -> dict[str, Any]:
        gates: list[dict[str, Any]] = []
        violations = 0
        for node in nodes:
            if not isinstance(node, dict) or node.get("node_type") != "gate":
                continue
            if "no-go-gate" not in (node.get("tags") or []):
                continue
            metadata = node.get("metadata") if isinstance(node.get("metadata"), dict) else {}
            safe = bool(metadata.get("safe", False))
            if not safe:
                violations += 1
            gates.append(
                {
                    "gate_id": str(node.get("title") or node.get("node_id") or ""),
                    "status": str(node.get("status") or "unknown"),
                    "safe": safe,
                    "expected": metadata.get("expected"),
                    "actual": metadata.get("actual"),
                }
            )
        return {
            "active_total": len(gates),
            "violations_total": violations,
            "gates": sorted(gates, key=lambda item: item["gate_id"]),
        }

    def _evidence_quality(self, graph_summary: dict[str, Any], nodes: list[Any]) -> dict[str, Any]:
        versioned_available = 0
        runtime_available = 0
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if node.get("evidence_class") == "versioned_source" and node.get("status") == "available":
                versioned_available += 1
            if node.get("evidence_class") == "runtime_generated" and node.get("status") == "available":
                runtime_available += 1
        return {
            "graph_nodes_total": int(graph_summary.get("nodes_total", 0) or 0),
            "graph_edges_total": int(graph_summary.get("edges_total", 0) or 0),
            "versioned_sources_available_total": versioned_available,
            "runtime_generated_available_total": runtime_available,
            "missing_expected_total": int(graph_summary.get("missing_evidence_total", 0) or 0),
            "blocking_gaps_total": int(graph_summary.get("blocking_gaps_total", 0) or 0),
            "blocking_findings_total": int(graph_summary.get("blocking_findings_total", 0) or 0),
            "reports_written": bool(self.options.write_report),
        }

    def _sections(
        self,
        config: dict[str, Any],
        graph: dict[str, Any],
        evidence_quality: dict[str, Any],
        claims: dict[str, Any],
        no_go: dict[str, Any],
    ) -> list[dict[str, Any]]:
        nodes = graph.get("nodes") if isinstance(graph.get("nodes"), list) else []
        sources = {str(node.get("source_id")): node for node in nodes if isinstance(node, dict) and node.get("source_id")}
        state_path = self.root / ".devpilot/project_state.json"
        source_registry_path = self.root / ".devpilot/docs_governance/source_registry.json"
        tcr_v1_path = self.root / ".devpilot/testing/test_contract_registry.json"
        tcr_v2_path = self.root / ".devpilot/testing/test_contract_registry_v2.json"
        criteria_path = self.root / ".devpilot/production/production_ready_local_criteria.json"
        graph_sources_path = self.root / str(config.get("evidence_graph_sources_path") or ".devpilot/evidence/evidence_graph_sources.json")
        operator_config_path = self.config_path

        state = _load_json(state_path)
        source_registry = _load_json(source_registry_path)
        tcr_v1 = _load_json(tcr_v1_path)
        tcr_v2 = _load_json(tcr_v2_path)

        no_go_status = "green" if int(no_go.get("violations_total", 0)) == 0 and int(claims.get("forbidden_available_total", 0)) == 0 else "red"
        evidence_status = "red" if int(evidence_quality.get("blocking_findings_total", 0)) or int(evidence_quality.get("blocking_gaps_total", 0)) else ("yellow" if int(evidence_quality.get("missing_expected_total", 0)) else "green")
        observability_missing = self._source_missing(sources, "runtime-observability-inventory") or self._source_missing(sources, "runtime-observability-redacted-export")
        operator_dashboard_missing = self._source_missing(sources, "runtime-operator-dashboard-snapshot")

        return [
            self._section(
                "global_state",
                "Project global state",
                "green" if state_path.exists() and state.get("current_micro_sprint") else "red",
                f"Current micro-sprint: {state.get('current_micro_sprint', 'unknown')}; next: {state.get('next_micro_sprint', 'unknown')}.",
                {"last_completed_sprint": state.get("last_completed_sprint"), "current_repo": state.get("current_repo")},
                [_source_ref(".devpilot/project_state.json", required=True, available=state_path.exists(), description="Source-controlled project state")],
            ),
            self._section(
                "evidence_graph",
                "Evidence graph",
                evidence_status,
                f"Evidence graph has {evidence_quality.get('graph_nodes_total')} nodes, {evidence_quality.get('missing_expected_total')} missing expected runtime evidence items and {evidence_quality.get('blocking_gaps_total')} blocking gaps.",
                evidence_quality,
                [_source_ref(str(config.get("evidence_graph_sources_path") or ".devpilot/evidence/evidence_graph_sources.json"), required=True, available=graph_sources_path.exists(), description="Evidence graph source configuration")],
                warnings_total=int(evidence_quality.get("missing_expected_total", 0)),
                blocking_findings_total=int(evidence_quality.get("blocking_findings_total", 0)) + int(evidence_quality.get("blocking_gaps_total", 0)),
            ),
            self._section(
                "documentation_governance",
                "Documentation governance",
                "green" if source_registry_path.exists() else "red",
                f"Documentation source registry contains {len(source_registry.get('documents', [])) if isinstance(source_registry.get('documents'), list) else 0} registered documents.",
                {"documents_total": len(source_registry.get("documents", [])) if isinstance(source_registry.get("documents"), list) else 0},
                [_source_ref(".devpilot/docs_governance/source_registry.json", required=True, available=source_registry_path.exists(), description="Canonical documentation source registry")],
            ),
            self._section(
                "test_contracts",
                "Test contracts",
                "green" if tcr_v1_path.exists() and tcr_v2_path.exists() else "red",
                f"TCR v1/v2 are present with {len(tcr_v1.get('contracts', [])) if isinstance(tcr_v1.get('contracts'), list) else 0}/{len(tcr_v2.get('contracts', [])) if isinstance(tcr_v2.get('contracts'), list) else 0} contracts.",
                {"tcr_v1_contracts_total": len(tcr_v1.get("contracts", [])) if isinstance(tcr_v1.get("contracts"), list) else 0, "tcr_v2_contracts_total": len(tcr_v2.get("contracts", [])) if isinstance(tcr_v2.get("contracts"), list) else 0},
                [
                    _source_ref(".devpilot/testing/test_contract_registry.json", required=True, available=tcr_v1_path.exists(), description="TCR v1"),
                    _source_ref(".devpilot/testing/test_contract_registry_v2.json", required=True, available=tcr_v2_path.exists(), description="TCR v2"),
                ],
            ),
            self._section(
                "production_ready_local",
                "Production-ready-local declaration",
                "green" if bool(state.get("post_h_025_production_ready_local_declared")) and criteria_path.exists() else "yellow",
                "Production-ready-local remains the bounded allowed claim; enterprise/remote/SaaS/compliance claims remain blocked.",
                {"production_ready_local_declared": bool(state.get("post_h_025_production_ready_local_declared")), "criteria_present": criteria_path.exists()},
                [_source_ref(".devpilot/production/production_ready_local_criteria.json", required=True, available=criteria_path.exists(), description="Production-ready-local criteria and no-go gates")],
            ),
            self._section(
                "claims_no_go",
                "Claims and no-go gates",
                no_go_status,
                f"Allowed claims: {len(claims.get('allowed', []))}; prohibited claims: {len(claims.get('prohibited', []))}; no-go violations: {no_go.get('violations_total')}.",
                {"allowed_claims_total": len(claims.get("allowed", [])), "prohibited_claims_total": len(claims.get("prohibited", [])), "no_go_violations_total": no_go.get("violations_total")},
                [_source_ref(".devpilot/production/production_ready_local_criteria.json", required=True, available=criteria_path.exists(), description="Claims/no-go criteria")],
                blocking_findings_total=int(no_go.get("violations_total", 0)) + int(claims.get("forbidden_available_total", 0)),
            ),
            self._section(
                "runtime_state",
                "Runtime state evidence",
                "green" if not self._source_missing(sources, "runtime-state-inventory") else "yellow",
                "Runtime state evidence is treated as regenerable and excluded from source deliverables.",
                {"runtime_state_inventory_available": not self._source_missing(sources, "runtime-state-inventory")},
                [_source_ref("outputs/reports/runtime_state_inventory.json", kind="generated-report", required=False, available=not self._source_missing(sources, "runtime-state-inventory"), description="Regenerable runtime state inventory")],
                warnings_total=1 if self._source_missing(sources, "runtime-state-inventory") else 0,
            ),
            self._section(
                "observability",
                "Observability evidence",
                "yellow" if observability_missing else "green",
                "Observability inventory/export are optional runtime reports and should be regenerated for operator review when needed.",
                {"observability_inventory_missing": self._source_missing(sources, "runtime-observability-inventory"), "observability_export_missing": self._source_missing(sources, "runtime-observability-redacted-export")},
                [
                    _source_ref("outputs/reports/observability_inventory.json", kind="generated-report", required=False, available=not self._source_missing(sources, "runtime-observability-inventory"), description="Regenerable observability inventory"),
                    _source_ref("outputs/reports/observability_redacted_export.json", kind="generated-report", required=False, available=not self._source_missing(sources, "runtime-observability-redacted-export"), description="Regenerable redacted observability export"),
                ],
                warnings_total=(1 if self._source_missing(sources, "runtime-observability-inventory") else 0) + (1 if self._source_missing(sources, "runtime-observability-redacted-export") else 0),
            ),
            self._section(
                "operator_dashboard",
                "Operator dashboard snapshot",
                "yellow" if operator_dashboard_missing else "green",
                "Operator dashboard snapshot is available when regenerated under outputs/reports.",
                {"operator_dashboard_snapshot_missing": operator_dashboard_missing},
                [_source_ref("outputs/reports/operator_dashboard_snapshot.json", kind="generated-report", required=False, available=not operator_dashboard_missing, description="Regenerable operator dashboard snapshot")],
                warnings_total=1 if operator_dashboard_missing else 0,
            ),
            self._section(
                "application_boundary",
                "CLI/API/ApplicationService boundary",
                "green",
                "POST-H-031-B is exposed through ApplicationService and CLI; local API route is protected by token/policy when used.",
                {"application_service_method": "operator_health_summary", "cli_command": "evidence health", "api_route": "/api/v1/operator/health"},
                [
                    _source_ref("src/devpilot_core/application/services.py", kind="python", required=True, available=True, description="ApplicationService boundary"),
                    _source_ref("src/devpilot_core/interfaces/api/routers/operator.py", kind="python", required=True, available=True, description="Protected operator API router"),
                    _source_ref("src/devpilot_core/cli.py", kind="python", required=True, available=True, description="CLI parser/dispatcher")
                ],
            ),
            self._section(
                "operator_health_config",
                "Operator health configuration",
                "green" if operator_config_path.exists() else "red",
                "Operator health config defines safe top actions and report paths without executing commands.",
                {"config_present": operator_config_path.exists()},
                [_source_ref(str(self.options.config_path), required=True, available=operator_config_path.exists(), description="Operator health summary config")],
            ),
        ]

    def _section(
        self,
        section_id: str,
        title: str,
        status: str,
        summary: str,
        metrics: dict[str, Any],
        source_refs: list[dict[str, Any]],
        *,
        blocking_findings_total: int = 0,
        warnings_total: int = 0,
    ) -> dict[str, Any]:
        return {
            "section_id": section_id,
            "title": title,
            "status": status,
            "summary": summary,
            "metrics": metrics,
            "source_refs": source_refs,
            "blocking_findings_total": int(blocking_findings_total),
            "warnings_total": int(warnings_total),
        }

    def _top_actions(self, config: dict[str, Any], nodes: list[Any]) -> list[dict[str, Any]]:
        action_config = config.get("recommended_runtime_actions") if isinstance(config.get("recommended_runtime_actions"), dict) else {}
        actions: list[dict[str, Any]] = []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if node.get("node_type") != "report" or node.get("status") != "missing":
                continue
            source_id = str(node.get("source_id") or "")
            rule = action_config.get(source_id) if isinstance(action_config.get(source_id), dict) else {}
            if not rule:
                continue
            path = str(node.get("path") or "")
            actions.append(
                {
                    "action_id": f"regenerate:{source_id}",
                    "priority": str(rule.get("priority") or "P2"),
                    "category": str(rule.get("category") or "evidence"),
                    "title": str(rule.get("title") or f"Regenerar {source_id}"),
                    "command": str(rule.get("command") or "python -m devpilot_core evidence health --json"),
                    "reason": f"La evidencia runtime `{source_id}` no existe en `{path}` y puede regenerarse localmente si el operador la necesita.",
                    "dry_run": True,
                    "verification": str(rule.get("verification") or "python -m devpilot_core evidence health --json"),
                    "source_refs": [_source_ref(path, kind="generated-report", required=False, available=False, description=f"Runtime evidence for {source_id}")],
                }
            )
        return sorted(actions, key=lambda item: (item["priority"], item["action_id"]))[:8]

    def _source_missing(self, sources: dict[str, dict[str, Any]], source_id: str) -> bool:
        node = sources.get(source_id)
        return not node or node.get("status") == "missing"

    def _overall_status(
        self,
        *,
        blocking_findings_total: int,
        blocking_gaps_total: int,
        no_go_violations: int,
        forbidden_available: int,
        missing_expected: int,
        graph_ok: bool,
    ) -> str:
        if not graph_ok or blocking_findings_total or blocking_gaps_total or no_go_violations or forbidden_available:
            return "red"
        if missing_expected:
            return "yellow"
        return "green"

    def _health_score(
        self,
        *,
        overall_status: str,
        missing_expected: int,
        warnings_total: int,
        blocking_findings_total: int,
        blocking_gaps_total: int,
        no_go_violations: int,
        forbidden_available: int,
    ) -> int:
        score = 100
        score -= min(40, missing_expected * 4)
        score -= min(25, warnings_total * 2)
        score -= min(70, (blocking_findings_total + blocking_gaps_total + no_go_violations + forbidden_available) * 25)
        if overall_status == "red":
            score = min(score, 59)
        elif overall_status == "yellow":
            score = min(score, 89)
        return max(0, min(100, score))

    def _command_summary(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "created_by": POST_H_031_B_CREATED_BY,
            "status": "implemented-initial",
            "decision": payload.get("decision"),
            "overall_status": payload.get("overall_status"),
            "health_score": payload.get("health_score"),
            "sections_total": len(payload.get("sections", [])) if isinstance(payload.get("sections"), list) else 0,
            "top_actions_total": len(payload.get("top_actions", [])) if isinstance(payload.get("top_actions"), list) else 0,
            "missing_expected_total": (payload.get("evidence_quality") or {}).get("missing_expected_total"),
            "blocking_gaps_total": (payload.get("evidence_quality") or {}).get("blocking_gaps_total"),
            "no_go_violations_total": (payload.get("no_go_gates") or {}).get("violations_total"),
            "forbidden_claims_available_total": (payload.get("claims") or {}).get("forbidden_available_total"),
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "reports_written": bool(self.options.write_report),
            "preliminary": True,
        }

    def _write_reports(self, payload: dict[str, Any]) -> None:
        json_path = self.root / self.options.output_json
        markdown_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(render_operator_health_markdown(payload), encoding="utf-8")


def render_operator_health_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# DevPilot Operator Health Summary",
        "",
        f"- Summary ID: `{payload.get('summary_id')}`",
        f"- Created by: `{payload.get('created_by')}`",
        f"- Overall status: `{payload.get('overall_status')}`",
        f"- Decision: `{payload.get('decision')}`",
        f"- Health score: `{payload.get('health_score')}`",
        "",
        "## Sections",
        "",
    ]
    for section in payload.get("sections", []):
        lines.append(f"- `{section.get('status')}` **{section.get('title')}**: {section.get('summary')}")
    lines.extend(["", "## Top actions", ""])
    actions = payload.get("top_actions", [])
    if not actions:
        lines.append("- No top operator actions were derived.")
    for action in actions:
        lines.append(f"- `{action.get('priority')}` **{action.get('title')}**: `{action.get('command')}`")
    lines.extend(["", "## Safety", ""])
    for key, value in (payload.get("safety") or {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)
