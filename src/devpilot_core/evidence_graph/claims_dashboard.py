from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.evidence_graph.builder import EvidenceGraphBuilder, EvidenceGraphOptions
from devpilot_core.industrial.production_ready import ProductionReadyClaimsValidator, ProductionReadyClaimsValidatorOptions

POST_H_031_D_CREATED_BY = "POST-H-031-D"
CLAIMS_NO_GO_DASHBOARD_SCHEMA_ID = "SCHEMA-DEVPL-CLAIMS-NO-GO-DASHBOARD-V1"
CLAIMS_NO_GO_DASHBOARD_CONTRACT = "ClaimsNoGoDashboard"
CLAIMS_NO_GO_DASHBOARD_ID = "devpilot-claims-no-go-dashboard"
DEFAULT_CLAIMS_DASHBOARD_CONFIG = Path(".devpilot/operator/claims_no_go_dashboard_config.json")
DEFAULT_CLAIMS_DASHBOARD_OUTPUT_JSON = Path("outputs/reports/claims_no_go_dashboard.json")
DEFAULT_CLAIMS_DASHBOARD_OUTPUT_MARKDOWN = Path("outputs/reports/claims_no_go_dashboard.md")

PROHIBITED_CLAIM_IDS = {"enterprise-ready", "remote-ready", "compliance-certified", "saas-ready"}
NO_GO_FIELD_TO_CLAIMS = {
    "remote_execution_enabled": ["remote-ready"],
    "connector_write_enabled": ["production-ready-local"],
    "plugin_execution_enabled": ["production-ready-local"],
    "external_apis_required": ["saas-ready", "remote-ready"],
    "compliance_certification_claim": ["compliance-certified"],
    "enterprise_ready_claim": ["enterprise-ready"],
    "remote_ready_claim": ["remote-ready"],
    "saas_ready_claim": ["saas-ready"],
}


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


def _source_ref(path: str | Path, *, kind: str = "json", required: bool = False, available: bool | None = None, description: str = "") -> dict[str, Any]:
    display = _display_path(path)
    return {
        "path": display,
        "kind": kind,
        "required": bool(required),
        "available": bool(Path(path).exists()) if available is None and not Path(path).is_absolute() else bool(available),
        "description": description or display,
    }


@dataclass(frozen=True)
class ClaimsDashboardOptions:
    config_path: Path = DEFAULT_CLAIMS_DASHBOARD_CONFIG
    write_report: bool = False
    output_json: Path = DEFAULT_CLAIMS_DASHBOARD_OUTPUT_JSON
    output_markdown: Path = DEFAULT_CLAIMS_DASHBOARD_OUTPUT_MARKDOWN


class ClaimsNoGoDashboardBuilder:
    """Build a local read-only dashboard for claims and no-go gates.

    POST-H-031-D does not create or mutate claims. It renders the bounded claim
    baseline from config, production-ready-local criteria, project-state flags,
    EvidenceGraph no-go nodes and ProductionReadyClaimsValidator output into one
    operator view.
    """

    def __init__(self, root: Path, options: ClaimsDashboardOptions | None = None) -> None:
        self.root = Path(root)
        self.options = options or ClaimsDashboardOptions()

    @property
    def config_path(self) -> Path:
        return self.root / self.options.config_path

    def build(self) -> CommandResult:
        config = self._load_config()
        criteria_path = Path(config.get("production_ready_criteria_path") or ".devpilot/production/production_ready_local_criteria.json")
        state_path = Path(config.get("project_state_path") or ".devpilot/project_state.json")
        sources_path = Path(config.get("evidence_graph_sources_path") or ".devpilot/evidence/evidence_graph_sources.json")
        document_paths = [str(item) for item in config.get("overclaim_documents", []) if item]

        criteria = _load_json(self.root / criteria_path)
        state = _load_json(self.root / state_path)

        graph_result = EvidenceGraphBuilder(self.root, EvidenceGraphOptions(sources_path=sources_path)).build()
        graph = ((graph_result.data or {}).get("graph") or {}) if isinstance(graph_result.data, dict) else {}
        graph_nodes = graph.get("nodes") if isinstance(graph.get("nodes"), list) else []

        validator_result = ProductionReadyClaimsValidator(
            self.root,
            options=ProductionReadyClaimsValidatorOptions(document_paths=tuple(document_paths)),
        ).validate()
        validator_data = validator_result.data if isinstance(validator_result.data, dict) else {}

        no_go_gates = self._no_go_gates(criteria, state, graph_nodes, criteria_path)
        claims = self._claims(config, criteria, state, validator_result, validator_data, no_go_gates)
        overclaim_scan = self._overclaim_scan(validator_result, validator_data, document_paths)
        relation = self._production_ready_relation(validator_result, validator_data, criteria_path)

        no_go_violations = sum(1 for gate in no_go_gates if not gate.get("safe"))
        overclaim_violations = int(overclaim_scan.get("violations_total", 0))
        prohibited_available = sum(1 for claim in claims if claim["claim_id"] in PROHIBITED_CLAIM_IDS and claim["allowed"])
        allowed_claims = sum(1 for claim in claims if claim["status"] == "allowed")
        conditioned_claims = sum(1 for claim in claims if claim["status"] == "conditioned")
        prohibited_claims = sum(1 for claim in claims if claim["status"] in {"prohibited", "blocked"})
        decision = "BLOCK" if no_go_violations or overclaim_violations or prohibited_available or not validator_result.ok else "PASS"
        status = "blocked" if decision == "BLOCK" else ("warn" if conditioned_claims else "pass")

        warnings = self._warnings(claims, no_go_gates, overclaim_scan, relation)
        findings = list(graph_result.findings or []) + list(validator_result.findings or [])
        if not findings:
            findings = [Finding("CLAIMS_NO_GO_DASHBOARD_READY", "Claims/no-go dashboard was built from local evidence without mutating claims or gates.", Severity.INFO)]

        dashboard = {
            "schema_version": "1.0",
            "schema_id": CLAIMS_NO_GO_DASHBOARD_SCHEMA_ID,
            "dashboard_id": CLAIMS_NO_GO_DASHBOARD_ID,
            "created_by": POST_H_031_D_CREATED_BY,
            "status": status,
            "generated_at_utc": _utc_now(),
            "summary": {
                "created_by": POST_H_031_D_CREATED_BY,
                "status": "implemented-initial",
                "decision": decision,
                "claims_total": len(claims),
                "allowed_claims_total": allowed_claims,
                "conditioned_claims_total": conditioned_claims,
                "prohibited_claims_total": prohibited_claims,
                "no_go_gates_total": len(no_go_gates),
                "no_go_violations_total": no_go_violations,
                "overclaim_violations_total": overclaim_violations,
                "prohibited_claims_available_total": prohibited_available,
                "claims_validator_ok": bool(validator_result.ok),
                "documents_scanned_total": int(overclaim_scan.get("documents_scanned_total", 0)),
                "read_only": True,
                "network_used": False,
                "external_api_used": False,
                "source_mutations_performed": False,
                "reports_written": bool(self.options.write_report),
                "preliminary": True,
            },
            "claims": claims,
            "no_go_gates": no_go_gates,
            "overclaim_scan": overclaim_scan,
            "production_ready_relation": relation,
            "warnings": warnings,
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
                "claims_mutated": False,
                "no_go_gates_mutated": False,
                "overclaim_scan_llm_used": False,
            },
            "limitations": [
                "ClaimsNoGoDashboard is an operator view, not a new readiness declaration.",
                "It does not mutate claims, no-go gates, project state or production-ready criteria.",
                "It reuses deterministic ProductionReadyClaimsValidator scanning; no LLM judge or network is used.",
                "Enterprise-ready, remote-ready, compliance-certified and SaaS-ready remain prohibited unless a future approved backlog/ADR changes the scope.",
            ],
            "findings": [finding.to_dict() for finding in findings],
            "notes": [
                "POST-H-031-D makes existing POST-H-025 claims/no-go evidence consumable by operator, CLI and local API.",
                "The audit-friendly claim is conditioned to internal evidence/audit usability and does not imply compliance certification.",
            ],
        }

        if self.options.write_report:
            self._write_reports(dashboard)

        result_findings = [
            Finding(
                "CLAIMS_NO_GO_DASHBOARD_READY" if decision == "PASS" else "CLAIMS_NO_GO_DASHBOARD_BLOCK",
                "Claims/no-go dashboard is available." if decision == "PASS" else "Claims/no-go dashboard has blocking overclaim/no-go findings.",
                Severity.INFO if decision == "PASS" else Severity.BLOCK,
                metadata={"claims_total": len(claims), "no_go_violations_total": no_go_violations, "overclaim_violations_total": overclaim_violations},
            )
        ]
        return CommandResult(
            command="evidence claims-dashboard",
            ok=decision == "PASS",
            exit_code=ExitCode.PASS if decision == "PASS" else ExitCode.BLOCK,
            message="Claims/no-go dashboard built." if decision == "PASS" else "Claims/no-go dashboard has blocking findings.",
            data={"summary": self._command_summary(dashboard), "claims_no_go_dashboard": dashboard},
            findings=result_findings,
        )

    def _load_config(self) -> dict[str, Any]:
        payload = _load_json(self.config_path)
        if payload:
            return payload
        return {
            "production_ready_criteria_path": ".devpilot/production/production_ready_local_criteria.json",
            "project_state_path": ".devpilot/project_state.json",
            "evidence_graph_sources_path": ".devpilot/evidence/evidence_graph_sources.json",
            "overclaim_documents": ["README.md", "docs/05_operations/runbook.md", "docs/release/CHANGELOG.md"],
            "claims_baseline": [],
        }

    def _no_go_gates(self, criteria: dict[str, Any], state: dict[str, Any], graph_nodes: list[Any], criteria_path: Path) -> list[dict[str, Any]]:
        no_go = criteria.get("no_go_gates") if isinstance(criteria.get("no_go_gates"), dict) else {}
        graph_by_gate = {
            str(node.get("title") or ""): node
            for node in graph_nodes
            if isinstance(node, dict) and node.get("node_type") == "gate" and "no-go-gate" in (node.get("tags") or [])
        }
        gates: list[dict[str, Any]] = []
        for gate_id in sorted(NO_GO_FIELD_TO_CLAIMS):
            expected = no_go.get(gate_id, False)
            actual = state.get(gate_id, state.get(f"post_h_025_{gate_id}", expected))
            graph_node = graph_by_gate.get(gate_id, {})
            metadata = graph_node.get("metadata") if isinstance(graph_node.get("metadata"), dict) else {}
            safe = bool(metadata.get("safe", actual is False and expected is False))
            gates.append(
                {
                    "gate_id": gate_id,
                    "status": "active_blocking" if safe else "violated",
                    "safe": safe,
                    "expected": expected,
                    "actual": actual,
                    "blocks_claims": NO_GO_FIELD_TO_CLAIMS.get(gate_id, []),
                    "reason": "Gate is safe because the forbidden capability/claim remains disabled." if safe else "Gate is violated because a forbidden capability/claim appears enabled.",
                    "source_refs": [
                        self._source_ref(criteria_path, required=True, description="Production-ready-local no-go criteria"),
                        self._source_ref(".devpilot/project_state.json", required=True, description="Project state no-go flag source"),
                    ],
                }
            )
        return gates

    def _claims(
        self,
        config: dict[str, Any],
        criteria: dict[str, Any],
        state: dict[str, Any],
        validator_result: CommandResult,
        validator_data: dict[str, Any],
        no_go_gates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        claim_config = config.get("claims_baseline") if isinstance(config.get("claims_baseline"), list) else []
        claims_allowed = criteria.get("claims_allowed") if isinstance(criteria.get("claims_allowed"), dict) else {}
        unsafe_by_claim: dict[str, list[str]] = {}
        for gate in no_go_gates:
            if gate.get("safe"):
                continue
            for claim_id in gate.get("blocks_claims", []):
                unsafe_by_claim.setdefault(str(claim_id), []).append(str(gate.get("gate_id")))
        claims: list[dict[str, Any]] = []
        seen: set[str] = set()
        for raw in claim_config:
            if not isinstance(raw, dict):
                continue
            claim_id = str(raw.get("claim_id") or "").strip()
            if not claim_id:
                continue
            seen.add(claim_id)
            configured_status = str(raw.get("status") or "prohibited")
            no_go_refs = list(raw.get("blocked_by") or []) + unsafe_by_claim.get(claim_id, [])
            blocking_reasons: list[str] = []
            if claim_id in PROHIBITED_CLAIM_IDS:
                blocking_reasons.append(str(raw.get("reason") or f"{claim_id} is outside current local-first scope."))
            if no_go_refs and claim_id != "production-ready-local":
                blocking_reasons.append(f"Blocked by no-go gates: {', '.join(sorted(set(no_go_refs)))}.")

            if claim_id == "production-ready-local":
                allowed = bool(claims_allowed.get("production_ready_local", state.get("post_h_025_production_ready_local_declared", False))) and validator_result.ok and not unsafe_by_claim.get(claim_id)
                status = "allowed" if allowed else "blocked"
                if not allowed:
                    blocking_reasons.append("production-ready-local requires POST-H-025 evidence, claims validator PASS and safe no-go gates.")
            elif configured_status == "conditioned":
                allowed = False
                status = "conditioned"
            elif configured_status == "allowed":
                allowed = True
                status = "allowed"
            else:
                allowed = False
                status = "prohibited"

            claims.append(
                {
                    "claim_id": claim_id,
                    "title": str(raw.get("title") or claim_id),
                    "status": status,
                    "allowed": bool(allowed),
                    "conditioned": status == "conditioned",
                    "prohibited": status in {"prohibited", "blocked"},
                    "scope": str(raw.get("scope") or "local-first"),
                    "evidence_refs": [self._source_ref(path, required=(claim_id == "production-ready-local"), description=f"Evidence for claim {claim_id}") for path in raw.get("evidence_refs", [])],
                    "blocking_reasons": blocking_reasons,
                    "no_go_gate_refs": sorted(set(no_go_refs)),
                    "notes": [str(item) for item in raw.get("notes", [])],
                }
            )
        for required_claim in ["production-ready-local", "enterprise-ready", "remote-ready", "compliance-certified", "saas-ready"]:
            if required_claim not in seen:
                claims.append(
                    {
                        "claim_id": required_claim,
                        "title": required_claim,
                        "status": "prohibited" if required_claim != "production-ready-local" else "blocked",
                        "allowed": False,
                        "conditioned": False,
                        "prohibited": True,
                        "scope": "fallback-baseline",
                        "evidence_refs": [self._source_ref(".devpilot/operator/claims_no_go_dashboard_config.json", required=True, description="Fallback dashboard claim baseline")],
                        "blocking_reasons": ["Missing explicit dashboard claim baseline entry."],
                        "no_go_gate_refs": [],
                        "notes": ["Fallback entry created to avoid hiding a baseline claim."],
                    }
                )
        return sorted(claims, key=lambda item: item["claim_id"])

    def _overclaim_scan(self, validator_result: CommandResult, validator_data: dict[str, Any], document_paths: list[str]) -> dict[str, Any]:
        summary = validator_data.get("summary") if isinstance(validator_data.get("summary"), dict) else {}
        documents = validator_data.get("documents") if isinstance(validator_data.get("documents"), list) else []
        report = validator_data.get("report") if isinstance(validator_data.get("report"), dict) else {}
        project_state = validator_data.get("project_state") if isinstance(validator_data.get("project_state"), dict) else {}
        document_violations_total = int(summary.get("forbidden_document_claims_total") or 0)
        report_claim_violations_total = int(summary.get("report_claim_violations_total") or 0)
        report_no_go_violations_total = int(summary.get("report_no_go_violations_total") or 0)
        project_state_no_go_violations_total = int(summary.get("project_state_no_go_violations_total") or 0)
        return {
            "status": "pass" if validator_result.ok else "blocked",
            "validator_command": validator_result.command,
            "validator_exit_code": int(validator_result.exit_code),
            "documents_scanned_total": int(summary.get("documents_scanned_total") or len(document_paths)),
            "documents_missing_total": int(summary.get("documents_missing_total") or 0),
            "forbidden_document_claims_total": document_violations_total,
            "report_validated": bool(summary.get("report_validated", False)),
            "report_source": summary.get("report_source"),
            "report_claim_violations_total": report_claim_violations_total,
            "report_no_go_violations_total": report_no_go_violations_total,
            "project_state_validated": bool(summary.get("project_state_validated", False)),
            "project_state_no_go_violations_total": project_state_no_go_violations_total,
            "violations_total": document_violations_total + report_claim_violations_total + report_no_go_violations_total + project_state_no_go_violations_total,
            "documents": documents,
            "report_status": report.get("status"),
            "project_state_status": project_state.get("status"),
            "llm_judge_used": False,
            "network_used": False,
            "external_api_used": False,
        }

    def _production_ready_relation(self, validator_result: CommandResult, validator_data: dict[str, Any], criteria_path: Path) -> dict[str, Any]:
        report_info = validator_data.get("report") if isinstance(validator_data.get("report"), dict) else {}
        report = report_info.get("report") if isinstance(report_info.get("report"), dict) else {}
        claims = report.get("claims") if isinstance(report.get("claims"), dict) else {}
        summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
        return {
            "criteria_path": _display_path(criteria_path),
            "claims_validator_ok": bool(validator_result.ok),
            "claims_validator_command": validator_result.command,
            "report_source": report_info.get("source"),
            "report_available": report_info.get("status") == "pass",
            "production_ready_local_declared": bool(claims.get("production_ready_local", False)),
            "decision": report.get("decision"),
            "score": report.get("score"),
            "blocking_gaps_total": report.get("blocking_gaps_total"),
            "no_go_gates_passed": report.get("no_go_gates_passed"),
            "production_ready_local_report_path": "outputs/reports/production_ready_local_report.json",
            "final_declaration_audit_path": "docs/audits/devpilot_local_production_ready_declaration.md",
            "reports_written_by_dashboard": bool(self.options.write_report),
            "source_refs": [
                self._source_ref(criteria_path, required=True, description="Production-ready-local criteria source"),
                self._source_ref("docs/audits/devpilot_local_production_ready_declaration.md", required=True, description="Bounded local production-ready declaration artifact"),
                self._source_ref("outputs/reports/production_ready_local_report.json", kind="generated-report", required=False, available=(self.root / "outputs/reports/production_ready_local_report.json").exists(), description="Regenerable production-ready-local runtime report"),
            ],
            "summary": summary,
        }

    def _warnings(self, claims: list[dict[str, Any]], no_go_gates: list[dict[str, Any]], overclaim_scan: dict[str, Any], relation: dict[str, Any]) -> list[str]:
        warnings: list[str] = []
        if any(claim.get("conditioned") for claim in claims):
            warnings.append("Some claims are conditioned and must be presented with their explicit scope.")
        if any(not gate.get("safe") for gate in no_go_gates):
            warnings.append("At least one no-go gate is violated; operator must treat readiness/claim views as blocked.")
        if int(overclaim_scan.get("violations_total", 0)) > 0:
            warnings.append("Overclaim scan detected forbidden claims or no-go violations.")
        if not relation.get("report_available"):
            warnings.append("ProductionReadyLocalReport was built in-memory or is unavailable as a runtime file; regenerate outputs if operator audit evidence is needed.")
        return warnings

    def _source_ref(self, relative_path: str | Path, *, kind: str = "json", required: bool = False, available: bool | None = None, description: str = "") -> dict[str, Any]:
        display = _display_path(relative_path)
        path = Path(relative_path)
        exists = (self.root / path).exists() if not path.is_absolute() else path.exists()
        return {"path": display, "kind": kind, "required": bool(required), "available": bool(exists if available is None else available), "description": description or display}

    def _command_summary(self, dashboard: dict[str, Any]) -> dict[str, Any]:
        summary = dict(dashboard.get("summary") or {})
        summary.update(
            {
                "created_by": POST_H_031_D_CREATED_BY,
                "status": "implemented-initial",
                "read_only": True,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "commands_executed": False,
                "claims_mutated": False,
                "no_go_gates_mutated": False,
                "reports_written": bool(self.options.write_report),
                "preliminary": True,
            }
        )
        return summary

    def _write_reports(self, dashboard: dict[str, Any]) -> None:
        json_path = self.root / self.options.output_json
        markdown_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(dashboard, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(render_claims_no_go_dashboard_markdown(dashboard), encoding="utf-8")


def render_claims_no_go_dashboard_markdown(dashboard: dict[str, Any]) -> str:
    summary = dashboard.get("summary") if isinstance(dashboard.get("summary"), dict) else {}
    lines = [
        "# DevPilot Claims and No-Go Dashboard",
        "",
        f"- Dashboard ID: `{dashboard.get('dashboard_id')}`",
        f"- Created by: `{dashboard.get('created_by')}`",
        f"- Decision: `{summary.get('decision')}`",
        f"- Claims: `{summary.get('claims_total')}`",
        f"- No-go violations: `{summary.get('no_go_violations_total')}`",
        f"- Overclaim violations: `{summary.get('overclaim_violations_total')}`",
        "",
        "## Claims",
        "",
    ]
    for claim in dashboard.get("claims", []):
        reasons = "; ".join(claim.get("blocking_reasons") or []) or "sin bloqueos adicionales"
        lines.append(f"- `{claim.get('status')}` **{claim.get('claim_id')}** — {claim.get('scope')}. {reasons}")
    lines.extend(["", "## No-go gates", ""])
    for gate in dashboard.get("no_go_gates", []):
        lines.append(f"- `{gate.get('status')}` **{gate.get('gate_id')}** — safe=`{gate.get('safe')}`, actual=`{gate.get('actual')}`")
    lines.extend(["", "## Overclaim scan", ""])
    scan = dashboard.get("overclaim_scan") if isinstance(dashboard.get("overclaim_scan"), dict) else {}
    lines.append(f"- Status: `{scan.get('status')}`")
    lines.append(f"- Documents scanned: `{scan.get('documents_scanned_total')}`")
    lines.append(f"- Violations: `{scan.get('violations_total')}`")
    lines.extend(["", "## Safety", ""])
    for key, value in (dashboard.get("safety") or {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)
