from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.evidence_graph.builder import EvidenceGraphBuilder, EvidenceGraphOptions
from devpilot_core.evidence_graph.health import OperatorHealthOptions, OperatorHealthSummaryBuilder

POST_H_031_C_CREATED_BY = "POST-H-031-C"
GAP_ACTION_MAP_SCHEMA_ID = "SCHEMA-DEVPL-GAP-ACTION-MAP-V1"
GAP_ACTION_MAP_CONTRACT = "GapActionMap"
GAP_ACTION_MAP_ID = "devpilot-gap-action-map"
DEFAULT_GAP_ACTION_RULES = Path(".devpilot/evidence/gap_action_rules.json")
DEFAULT_GAP_ACTION_OUTPUT_JSON = Path("outputs/reports/gap_action_map.json")
DEFAULT_GAP_ACTION_OUTPUT_MARKDOWN = Path("outputs/reports/gap_action_map.md")

_FORBIDDEN_COMMAND_FRAGMENTS = (
    "--execute",
    " rm ",
    " del ",
    " rmdir",
    "Remove-Item",
    "pip install",
    "npm install",
    "connector write",
    "plugin execute",
    "remote runner execute",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _display_path(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return str(path).replace("\\", "/")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _source_ref(path: str | None, *, kind: str = "unknown", required: bool = False, available: bool = False, description: str = "") -> dict[str, Any]:
    normalized = _display_path(path or "unknown") or "unknown"
    return {
        "path": normalized,
        "kind": kind,
        "required": bool(required),
        "available": bool(available),
        "description": description or normalized,
    }


def _severity_for_gap(blocking: bool, required: bool) -> str:
    if blocking:
        return "block"
    if required:
        return "fail"
    return "warning"


def _gap_type_for_source(source_id: str, *, required: bool, path: str | None) -> str:
    if required:
        return "missing_required_evidence"
    if source_id == "runtime-operator-dashboard-snapshot":
        return "missing_operator_dashboard_source"
    if source_id == "runtime-observability-redacted-export":
        return "observability_export_not_redacted"
    if source_id == "runtime-state-inventory":
        return "runtime_state_hygiene_failure" if path and "hygiene" in path else "missing_runtime_evidence"
    if source_id.startswith("runtime-"):
        return "missing_runtime_evidence"
    return "unknown_gap"


@dataclass(frozen=True)
class GapActionOptions:
    rules_path: Path = DEFAULT_GAP_ACTION_RULES
    evidence_graph_sources_path: Path = Path(".devpilot/evidence/evidence_graph_sources.json")
    operator_health_config_path: Path = Path(".devpilot/operator/operator_health_config.json")
    write_report: bool = False
    output_json: Path = DEFAULT_GAP_ACTION_OUTPUT_JSON
    output_markdown: Path = DEFAULT_GAP_ACTION_OUTPUT_MARKDOWN


class GapActionMapBuilder:
    """Map local evidence/operator gaps to concrete, verifiable actions.

    POST-H-031-C is intentionally advisory and read-only. It consumes the
    EvidenceGraph and OperatorHealthSummary models, applies declarative rules,
    and emits operator guidance. It never executes the recommended commands.
    """

    def __init__(self, root: Path, options: GapActionOptions | None = None) -> None:
        self.root = Path(root)
        self.options = options or GapActionOptions()

    @property
    def rules_path(self) -> Path:
        return self.root / self.options.rules_path

    def build(self) -> CommandResult:
        findings: list[Finding] = []
        config = _load_json(self.rules_path)
        rules = config.get("rules") if isinstance(config.get("rules"), list) else []
        required_categories = config.get("required_rule_categories") if isinstance(config.get("required_rule_categories"), list) else []
        safety = config.get("safety") if isinstance(config.get("safety"), dict) else {}
        forbidden_fragments = tuple(str(item) for item in safety.get("forbidden_command_fragments", _FORBIDDEN_COMMAND_FRAGMENTS)) or _FORBIDDEN_COMMAND_FRAGMENTS

        rules_by_category = {str(rule.get("gap_type")) for rule in rules if isinstance(rule, dict) and rule.get("gap_type")}
        missing_categories = [category for category in required_categories if str(category) not in rules_by_category]
        if missing_categories:
            findings.append(
                Finding(
                    "GAP_ACTION_REQUIRED_RULE_CATEGORY_MISSING",
                    "Gap action rules are missing required categories.",
                    Severity.BLOCK,
                    path=_display_path(self.options.rules_path),
                    metadata={"missing_categories": missing_categories},
                )
            )

        graph_result = EvidenceGraphBuilder(
            self.root,
            EvidenceGraphOptions(sources_path=self.options.evidence_graph_sources_path),
        ).build()
        graph = ((graph_result.data or {}).get("graph") or {}) if isinstance(graph_result.data, dict) else {}
        nodes = graph.get("nodes") if isinstance(graph.get("nodes"), list) else []
        graph_findings = graph.get("findings") if isinstance(graph.get("findings"), list) else []

        health_result = OperatorHealthSummaryBuilder(
            self.root,
            OperatorHealthOptions(config_path=self.options.operator_health_config_path),
        ).build()
        health = ((health_result.data or {}).get("health") or {}) if isinstance(health_result.data, dict) else {}
        health_overall_status = str(health.get("overall_status") or "unknown")
        health_score = int(health.get("health_score", 0) or 0)

        gaps = self._derive_gaps(nodes, graph_findings, health)
        actions, unmapped_gaps, unsafe_actions = self._map_gaps(gaps, rules, forbidden_fragments)
        blocking_unmapped = [gap for gap in unmapped_gaps if gap.get("blocking")]

        if unsafe_actions:
            findings.append(
                Finding(
                    "GAP_ACTION_UNSAFE_ACTION_BLOCK",
                    "One or more gap actions contain unsafe command guidance.",
                    Severity.BLOCK,
                    metadata={"unsafe_actions_total": len(unsafe_actions)},
                )
            )
        if blocking_unmapped:
            findings.append(
                Finding(
                    "GAP_ACTION_BLOCKING_GAP_UNMAPPED",
                    "One or more blocking gaps have no concrete action mapping.",
                    Severity.BLOCK,
                    metadata={"blocking_unmapped_total": len(blocking_unmapped)},
                )
            )

        blocking_findings = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        decision = "BLOCK" if blocking_findings else "PASS"
        summary = {
            "created_by": POST_H_031_C_CREATED_BY,
            "status": "blocked" if decision == "BLOCK" else "implemented-initial",
            "decision": decision,
            "gaps_total": len(gaps),
            "blocking_gaps_total": sum(1 for gap in gaps if gap.get("blocking")),
            "mapped_gaps_total": sum(1 for gap in gaps if gap.get("mapped")),
            "unmapped_gaps_total": len(unmapped_gaps),
            "actions_total": len(actions),
            "rules_total": len(rules),
            "required_rule_categories_total": len(required_categories),
            "required_rule_categories_present_total": len(required_categories) - len(missing_categories),
            "unsafe_actions_total": len(unsafe_actions),
            "unknown_gaps_total": sum(1 for gap in gaps if gap.get("gap_type") == "unknown_gap"),
            "operator_health_overall_status": health_overall_status,
            "operator_health_score": health_score,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "commands_executed": False,
            "source_mutations_performed": False,
            "reports_written": bool(self.options.write_report),
            "preliminary": True,
        }
        payload = {
            "schema_version": "1.0",
            "schema_id": GAP_ACTION_MAP_SCHEMA_ID,
            "map_id": GAP_ACTION_MAP_ID,
            "created_by": POST_H_031_C_CREATED_BY,
            "status": "blocked" if decision == "BLOCK" else ("warn" if gaps else "pass"),
            "generated_at_utc": _utc_now(),
            "summary": summary,
            "gaps": gaps,
            "actions": actions,
            "unmapped_gaps": unmapped_gaps,
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
                "recommended_commands_executed": False,
                "rules_path": _display_path(self.options.rules_path),
                "evidence_graph_sources_path": _display_path(self.options.evidence_graph_sources_path),
                "operator_health_config_path": _display_path(self.options.operator_health_config_path),
            },
            "limitations": [
                "GapActionMap is advisory operator guidance and does not execute recommended commands.",
                "The map does not relax no-go gates, version outputs runtime or declare readiness.",
                "Unknown gaps are surfaced explicitly instead of being hidden.",
                "Formal PASS/BLOCK decisions remain owned by dedicated validators and quality gates.",
            ],
            "findings": [finding.to_dict() for finding in findings] or [
                Finding(
                    "GAP_ACTION_MAP_READY",
                    "Gap action map was built from local evidence graph and operator health metadata without executing commands.",
                    Severity.INFO,
                    metadata={"gaps_total": len(gaps), "actions_total": len(actions)},
                ).to_dict()
            ],
            "notes": [
                "POST-H-031-C expands the top-actions concept from POST-H-031-B into declarative, testable rules.",
                "Runtime outputs remain regenerable and excluded from clean source ZIPs.",
            ],
        }

        if self.options.write_report:
            self._write_reports(payload)

        result_findings = [
            Finding(
                "GAP_ACTION_MAP_READY" if decision == "PASS" else "GAP_ACTION_MAP_BLOCKED",
                "Gap action map is available." if decision == "PASS" else "Gap action map has blocking rule or mapping issues.",
                Severity.INFO if decision == "PASS" else Severity.BLOCK,
                metadata={"gaps_total": len(gaps), "actions_total": len(actions), "unmapped_gaps_total": len(unmapped_gaps)},
            )
        ]
        if findings:
            result_findings = findings + result_findings
        return CommandResult(
            command="evidence gaps",
            ok=decision == "PASS",
            exit_code=ExitCode.PASS if decision == "PASS" else ExitCode.BLOCK,
            message="Gap action map built." if decision == "PASS" else "Gap action map has blocking issues.",
            data={"summary": summary, "gap_action_map": payload},
            findings=result_findings,
        )

    def _derive_gaps(self, nodes: list[Any], graph_findings: list[Any], health: dict[str, Any]) -> list[dict[str, Any]]:
        gaps: list[dict[str, Any]] = []
        seen: set[str] = set()
        for node in nodes:
            if not isinstance(node, dict) or node.get("node_type") != "gap":
                continue
            metadata = node.get("metadata") if isinstance(node.get("metadata"), dict) else {}
            source_id = str(metadata.get("source_id") or node.get("source_id") or "unknown-source")
            path = _display_path(node.get("path"))
            required = bool(metadata.get("required", False) or node.get("required", False))
            blocking = required or str(node.get("status")) in {"active_blocking", "blocked", "block"}
            gap_type = _gap_type_for_source(source_id, required=required, path=path)
            gap_id = f"gap:{source_id}"
            gap = self._gap(
                gap_id=gap_id,
                gap_type=gap_type,
                title=str(node.get("title") or f"Gap for {source_id}"),
                severity=_severity_for_gap(blocking, required),
                reason=f"EvidenceGraph reports `{source_id}` as {metadata.get('reason', node.get('status', 'missing'))}.",
                source_id=source_id,
                path=path,
                required=required,
                blocking=blocking,
            )
            gaps.append(gap)
            seen.add(gap_id)

        for finding in graph_findings:
            if not isinstance(finding, dict):
                continue
            finding_id = str(finding.get("id") or "UNKNOWN_FINDING")
            metadata = finding.get("metadata") if isinstance(finding.get("metadata"), dict) else {}
            source_id = metadata.get("source_id")
            if source_id and f"gap:{source_id}" in seen:
                continue
            severity = str(finding.get("severity") or "warning")
            blocking = severity in {"block", "error", "fail"}
            gap_id = f"finding:{finding_id}:{source_id or len(gaps)}"
            gaps.append(
                self._gap(
                    gap_id=gap_id,
                    gap_type=self._gap_type_for_finding(finding_id, source_id=source_id, required=bool(metadata.get("required", False))),
                    title=str(finding.get("message") or finding_id),
                    severity=severity if severity in {"info", "warning", "fail", "block", "error"} else "warning",
                    reason=str(finding.get("message") or "Graph finding requires operator review."),
                    source_id=str(source_id) if source_id else None,
                    path=_display_path(finding.get("path")),
                    required=bool(metadata.get("required", False)),
                    blocking=blocking,
                )
            )

        for section in health.get("sections", []) if isinstance(health.get("sections"), list) else []:
            if not isinstance(section, dict) or section.get("status") not in {"red"}:
                continue
            section_id = str(section.get("section_id") or "unknown-section")
            gap_id = f"health-section:{section_id}"
            if gap_id in seen:
                continue
            gaps.append(
                self._gap(
                    gap_id=gap_id,
                    gap_type=self._gap_type_for_health_section(section_id),
                    title=str(section.get("title") or section_id),
                    severity="block",
                    reason=str(section.get("summary") or "Operator health section is red."),
                    source_id=section_id,
                    path=None,
                    required=True,
                    blocking=True,
                )
            )
        return sorted(gaps, key=lambda item: item["gap_id"])

    def _gap(
        self,
        *,
        gap_id: str,
        gap_type: str,
        title: str,
        severity: str,
        reason: str,
        source_id: str | None,
        path: str | None,
        required: bool,
        blocking: bool,
    ) -> dict[str, Any]:
        return {
            "gap_id": gap_id,
            "gap_type": gap_type,
            "title": title,
            "severity": severity,
            "status": "open",
            "reason": reason,
            "source_id": source_id,
            "path": path,
            "required": bool(required),
            "blocking": bool(blocking),
            "mapped": False,
            "source_refs": [_source_ref(path, kind="generated-report" if path and path.startswith("outputs/") else "unknown", required=required, available=False, description=title)] if path else [],
        }

    def _gap_type_for_finding(self, finding_id: str, *, source_id: Any, required: bool) -> str:
        if finding_id == "SCHEMA_VALIDATION_ERROR":
            return "failed_schema_validation"
        if finding_id.startswith("DOCS_GOVERNANCE"):
            return "docs_governance_blocking_finding"
        if finding_id.startswith("TEST_CONTRACT"):
            return "test_contract_registry_invalid"
        if finding_id == "EVIDENCE_STALE":
            return "stale_runtime_evidence"
        if finding_id.startswith("RUNTIME_STATE_HYGIENE"):
            return "runtime_state_hygiene_failure"
        if finding_id.startswith("RELEASE_REPRODUCIBILITY"):
            return "release_reproducibility_missing"
        return _gap_type_for_source(str(source_id or ""), required=required, path=None)

    def _gap_type_for_health_section(self, section_id: str) -> str:
        if section_id == "documentation_governance":
            return "docs_governance_blocking_finding"
        if section_id == "test_contracts":
            return "test_contract_registry_invalid"
        if section_id == "claims_no_go":
            return "no_go_gate_violation"
        if section_id == "runtime_state":
            return "runtime_state_hygiene_failure"
        return "unknown_gap"

    def _map_gaps(
        self,
        gaps: list[dict[str, Any]],
        rules: list[Any],
        forbidden_fragments: tuple[str, ...],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        actions: list[dict[str, Any]] = []
        unmapped: list[dict[str, Any]] = []
        unsafe: list[dict[str, Any]] = []
        for gap in gaps:
            rule = self._find_rule(gap, rules)
            if not rule:
                gap["status"] = "unknown"
                unmapped.append(gap)
                continue
            action = self._action_for_gap(gap, rule)
            if not self._action_is_safe(action, forbidden_fragments):
                unsafe.append(action)
                gap["status"] = "unknown"
                unmapped.append(gap)
                continue
            gap["mapped"] = True
            gap["status"] = "mapped"
            actions.append(action)
        return sorted(actions, key=lambda item: (item["priority"], item["action_id"])), unmapped, unsafe

    def _find_rule(self, gap: dict[str, Any], rules: list[Any]) -> dict[str, Any] | None:
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            match = rule.get("match") if isinstance(rule.get("match"), dict) else {}
            if match.get("source_id") and str(match.get("source_id")) != str(gap.get("source_id")):
                continue
            if match.get("required") is not None and bool(match.get("required")) != bool(gap.get("required")):
                continue
            if match.get("status") and str(match.get("status")) != ("missing" if gap.get("path") else str(gap.get("status"))):
                continue
            if match.get("finding_id") and str(match.get("finding_id")) not in str(gap.get("gap_id")):
                continue
            if match.get("node_type") or match.get("safe") is not None or match.get("forbidden_available") is not None:
                # Current graph has no unsafe no-go/forbidden claim gaps. These rules exist to cover future triggered gaps.
                if str(rule.get("gap_type")) != str(gap.get("gap_type")):
                    continue
            if str(rule.get("gap_type")) == str(gap.get("gap_type")) or match.get("source_id") or match.get("finding_id"):
                return rule
        return None

    def _action_for_gap(self, gap: dict[str, Any], rule: dict[str, Any]) -> dict[str, Any]:
        return {
            "action_id": f"action:{rule.get('rule_id')}:{gap.get('gap_id')}",
            "gap_id": str(gap.get("gap_id")),
            "rule_id": str(rule.get("rule_id") or "unknown-rule"),
            "priority": str(rule.get("priority") or "P2"),
            "category": str(rule.get("category") or gap.get("gap_type") or "evidence"),
            "title": str(rule.get("title") or gap.get("title") or "Revisar gap"),
            "owner": str(rule.get("owner") or "operator.local"),
            "command": str(rule.get("command") or "python -m devpilot_core evidence gaps --json"),
            "verification": str(rule.get("verification") or "python -m devpilot_core evidence gaps --json"),
            "closure_criterion": str(rule.get("closure_criterion") or "El gap queda resuelto o documentado como not_applicable."),
            "risk_if_ignored": str(rule.get("risk_if_ignored") or "El operador pierde trazabilidad accionable sobre el gap."),
            "backlog_ref": str(rule.get("backlog_ref") or "POST-H-031-C"),
            "dry_run": True,
            "requires_approval": bool(rule.get("requires_approval", False)),
            "safe": True,
            "source_refs": gap.get("source_refs") or [_source_ref(gap.get("path"), required=bool(gap.get("required")), description=str(gap.get("title") or "Gap evidence"))],
        }

    def _action_is_safe(self, action: dict[str, Any], forbidden_fragments: tuple[str, ...]) -> bool:
        command = f" {action.get('command', '')} "
        if bool(action.get("dry_run")) is not True or bool(action.get("safe")) is not True:
            return False
        return not any(fragment in command for fragment in forbidden_fragments)

    def _command_summary(self, payload: dict[str, Any]) -> dict[str, Any]:
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        return dict(summary)

    def _write_reports(self, payload: dict[str, Any]) -> None:
        json_path = self.root / self.options.output_json
        markdown_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(render_gap_action_map_markdown(payload), encoding="utf-8")


def render_gap_action_map_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    lines = [
        "# DevPilot Gap Action Map",
        "",
        f"- Map ID: `{payload.get('map_id')}`",
        f"- Created by: `{payload.get('created_by')}`",
        f"- Decision: `{summary.get('decision')}`",
        f"- Gaps total: `{summary.get('gaps_total')}`",
        f"- Actions total: `{summary.get('actions_total')}`",
        f"- Operator health: `{summary.get('operator_health_overall_status')}` / `{summary.get('operator_health_score')}`",
        "",
        "## Actions",
        "",
    ]
    actions = payload.get("actions", []) if isinstance(payload.get("actions"), list) else []
    if not actions:
        lines.append("- No mapped actions were derived.")
    for action in actions:
        lines.append(f"- `{action.get('priority')}` **{action.get('title')}**")
        lines.append(f"  - Gap: `{action.get('gap_id')}`")
        lines.append(f"  - Command: `{action.get('command')}`")
        lines.append(f"  - Verification: `{action.get('verification')}`")
    lines.extend(["", "## Unmapped gaps", ""])
    unmapped = payload.get("unmapped_gaps", []) if isinstance(payload.get("unmapped_gaps"), list) else []
    if not unmapped:
        lines.append("- No unmapped gaps.")
    for gap in unmapped:
        lines.append(f"- `{gap.get('severity')}` `{gap.get('gap_id')}`: {gap.get('reason')}")
    lines.extend(["", "## Safety", ""])
    for key, value in (payload.get("safety") or {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)
