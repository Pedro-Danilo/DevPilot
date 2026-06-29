from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.runtime_state.models import utc_now_iso

POST_H_015_B_CREATED_BY = "POST-H-015-B"
OPERATOR_DASHBOARD_SCHEMA_ID = "SCHEMA-DEVPL-OPERATOR-DASHBOARD-SNAPSHOT-V1"
DEFAULT_OPERATOR_DASHBOARD_CONFIG = Path(".devpilot/operator/dashboard_config.json")


@dataclass(frozen=True)
class OperatorDashboardAggregatorOptions:
    """Options for the local read-only operator dashboard aggregator."""

    config_path: str | Path = DEFAULT_OPERATOR_DASHBOARD_CONFIG
    generated_at_utc: str | None = None
    write_report: bool = False


class OperatorDashboardAggregator:
    """Build the POST-H-015-B local operator dashboard snapshot.

    The aggregator reads source-controlled metadata and optional runtime
    evidence. It never calls network services, never executes shell commands and
    writes only `outputs/reports` when `write_report=True`.
    """

    def __init__(self, root: Path, options: OperatorDashboardAggregatorOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or OperatorDashboardAggregatorOptions()
        self.config_path = Path(self.options.config_path)

    def build(self) -> CommandResult:
        findings: list[Finding] = []
        config = self._load_config(findings)
        generated_at = self.options.generated_at_utc or utc_now_iso()
        snapshot = self._build_snapshot(config, generated_at=generated_at, findings=findings)
        reports: dict[str, str] = {}

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        ok = not blocking
        if self.options.write_report and ok:
            reports = self._write_reports(snapshot, config)
        elif self.options.write_report and not ok:
            findings.append(
                Finding(
                    "OPERATOR_DASHBOARD_REPORT_WRITE_BLOCKED",
                    "Operator dashboard reports were not written because required sources are missing.",
                    Severity.BLOCK,
                    metadata={"created_by": POST_H_015_B_CREATED_BY},
                )
            )
            ok = False

        summary = {
            "created_by": POST_H_015_B_CREATED_BY,
            "status": snapshot["status"],
            "sections_total": len(snapshot["sections"]),
            "required_sources_missing_total": _count_missing_required_sources(snapshot),
            "optional_sources_missing_total": _count_missing_optional_sources(snapshot),
            "recommended_next_actions_total": len(snapshot["recommended_next_actions"]),
            "reports_written": bool(reports),
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "preliminary": True,
        }
        return CommandResult(
            command="operator dashboard aggregate",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Operator dashboard snapshot built in read-only mode." if ok else "Operator dashboard snapshot has missing required sources.",
            data={"summary": summary, "snapshot": snapshot, "reports": reports},
            findings=findings or [
                Finding(
                    "OPERATOR_DASHBOARD_AGGREGATE_PASS",
                    "Operator dashboard snapshot consolidated local operational signals without mutations.",
                    Severity.INFO,
                    metadata=summary,
                )
            ],
        )

    def _load_config(self, findings: list[Finding]) -> dict[str, Any]:
        path = self.root / self.config_path
        if not path.exists():
            findings.append(Finding("OPERATOR_DASHBOARD_CONFIG_MISSING", "Operator dashboard config is missing.", Severity.BLOCK, path=_posix(self.config_path)))
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(
                Finding(
                    "OPERATOR_DASHBOARD_CONFIG_INVALID_JSON",
                    f"Operator dashboard config is invalid JSON: {exc.msg}",
                    Severity.ERROR,
                    path=_posix(self.config_path),
                )
            )
            return {}
        if not isinstance(payload, dict):
            findings.append(Finding("OPERATOR_DASHBOARD_CONFIG_INVALID", "Operator dashboard config root must be an object.", Severity.BLOCK, path=_posix(self.config_path)))
            return {}
        return payload

    def _build_snapshot(self, config: dict[str, Any], *, generated_at: str, findings: list[Finding]) -> dict[str, Any]:
        section_sources = self._section_source_refs(config)
        sections = {
            "maturity": self._maturity_section(section_sources),
            "quality_gates": self._quality_gates_section(section_sources),
            "test_contracts": self._test_contracts_section(section_sources),
            "roadmap": self._roadmap_section(section_sources),
            "security": self._security_section(section_sources),
            "observability": self._observability_section(section_sources),
            "agents": self._agents_section(section_sources),
            "approvals": self._approvals_section(section_sources),
            "release": self._release_section(section_sources),
            "workspace": self._workspace_section(section_sources),
        }
        self._record_missing_required_sources(sections, findings)
        status = _overall_status(sections)
        workspace_id = str(config.get("workspace_id") or "devpilot-local")
        return {
            "schema_version": "1.0",
            "schema_id": OPERATOR_DASHBOARD_SCHEMA_ID,
            "snapshot_id": _snapshot_id(generated_at),
            "workspace_id": workspace_id,
            "created_by": POST_H_015_B_CREATED_BY,
            "status": status,
            "generated_at_utc": generated_at,
            "local_first": True,
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "sections": sections,
            "recommended_next_actions": self._recommended_next_actions(config),
            "notes": [
                "POST-H-015-B aggregates local operational signals only; API and UI exposure remain future POST-H-015-C/D scope.",
                "Missing optional runtime outputs are represented as unknown rather than errors.",
            ],
        }

    def _section_source_refs(self, config: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        refs: dict[str, list[dict[str, Any]]] = {section: [] for section in config.get("required_sections", [])}
        for item in config.get("required_source_refs", []):
            if not isinstance(item, dict):
                continue
            section = str(item.get("section") or "")
            ref = self._source_ref(
                path=str(item.get("path") or ""),
                kind=str(item.get("kind") or "json"),
                required=bool(item.get("required", False)),
                description=str(item.get("description") or ""),
            )
            refs.setdefault(section, []).append(ref)
        return refs

    def _maturity_section(self, section_sources: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        refs = list(section_sources.get("maturity") or [])
        refs.append(self._source_ref("outputs/reports/maturity_dashboard.json", "generated-report", required=False))
        payload = _read_json_if_exists(self.root / "outputs/reports/maturity_dashboard.json")
        score = None
        if isinstance(payload, dict):
            summary = payload.get("summary")
            if isinstance(summary, dict) and isinstance(summary.get("score"), (int, float)):
                score = summary["score"]
        return _section(
            "Maturity",
            refs,
            summary="Maturity dashboard output is available." if payload else "Maturity dashboard output not generated yet.",
            score=score,
            metrics={"maturity_dashboard_present": payload is not None},
        )

    def _quality_gates_section(self, section_sources: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        refs = list(section_sources.get("quality_gates") or [])
        refs.append(self._source_ref("outputs/reports/ui_api_shell_report.json", "generated-report", required=False))
        shell_report = _read_json_if_exists(self.root / "outputs/reports/ui_api_shell_report.json")
        blocking = None
        warnings = None
        if isinstance(shell_report, dict):
            summary = shell_report.get("summary")
            if isinstance(summary, dict):
                blocking = _int_or_none(summary.get("blocking_findings_total"))
                warnings = _int_or_none(summary.get("warnings_total"))
        return _section(
            "Quality gates",
            refs,
            summary="Quality gate module present; runtime gate reports are optional evidence.",
            blocking_findings_total=blocking,
            warnings_total=warnings,
            metrics={"ui_api_shell_report_present": shell_report is not None},
        )

    def _test_contracts_section(self, section_sources: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        refs = list(section_sources.get("test_contracts") or [])
        refs.append(self._source_ref(".devpilot/testing/test_contract_registry_v2.json", "json", required=True))
        v1 = _read_json_if_exists(self.root / ".devpilot/testing/test_contract_registry.json")
        v2 = _read_json_if_exists(self.root / ".devpilot/testing/test_contract_registry_v2.json")
        return _section(
            "Test contracts",
            refs,
            summary="Test contract registries are readable." if v1 and v2 else "One or more test contract registries are missing.",
            metrics={
                "contracts_total_v1": _contracts_total(v1),
                "contracts_total_v2": _contracts_total(v2),
            },
        )

    def _roadmap_section(self, section_sources: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        refs = list(section_sources.get("roadmap") or [])
        refs.append(self._source_ref("docs/backlogs/POST-H-015_local_operator_dashboard.md", "markdown", required=True))
        state = _read_json_if_exists(self.root / ".devpilot/project_state.json")
        roadmap = _read_json_if_exists(self.root / ".devpilot/evals/post_h_eval_001_prioritized_roadmap.json")
        metrics = {}
        if isinstance(state, dict):
            metrics.update(
                {
                    "last_completed_sprint": state.get("last_completed_sprint"),
                    "next_sprint": state.get("next_sprint"),
                    "current_micro_sprint": state.get("current_micro_sprint"),
                    "next_micro_sprint": state.get("next_micro_sprint"),
                }
            )
        return _section(
            "Roadmap",
            refs,
            summary="Project state and prioritized roadmap are readable." if state and roadmap else "Roadmap metadata is incomplete.",
            metrics=metrics,
        )

    def _security_section(self, section_sources: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        refs = list(section_sources.get("security") or [])
        no_go_active = False
        return _section(
            "Security",
            refs,
            summary="Security risk register is available and no-go flags remain disabled.",
            metrics={"no_go_active": no_go_active},
        )

    def _observability_section(self, section_sources: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        refs = list(section_sources.get("observability") or [])
        refs.append(self._source_ref(".devpilot/observability/retention_policy.json", "json", required=True))
        refs.append(self._source_ref("outputs/reports/observability_inventory.json", "generated-report", required=False))
        reports_dir = self.root / "outputs/reports"
        return _section(
            "Observability",
            refs,
            summary="Observability policy is available; runtime reports may be absent in clean repos.",
            metrics={
                "retention_policy_present": (self.root / ".devpilot/observability/retention_policy.json").exists(),
                "reports_dir_present": reports_dir.exists(),
                "reports_total": len(list(reports_dir.glob("*"))) if reports_dir.exists() else 0,
            },
        )

    def _agents_section(self, section_sources: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        refs = list(section_sources.get("agents") or [])
        refs.extend(
            [
                self._source_ref("src/devpilot_core/agents", "directory", required=True),
                self._source_ref(".devpilot/miasi/agent_registry.json", "json", required=True),
                self._source_ref(".devpilot/miasi/tool_registry.json", "json", required=True),
            ]
        )
        return _section(
            "Agents",
            refs,
            summary="Agent runtime and MIASI registries are available.",
            metrics={
                "agent_runtime_present": (self.root / "src/devpilot_core/agents").exists(),
                "miasi_agent_registry_present": (self.root / ".devpilot/miasi/agent_registry.json").exists(),
                "miasi_tool_registry_present": (self.root / ".devpilot/miasi/tool_registry.json").exists(),
            },
        )

    def _approvals_section(self, section_sources: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        refs = list(section_sources.get("approvals") or [])
        refs.extend(
            [
                self._source_ref("src/devpilot_core/approval", "directory", required=True),
                self._source_ref(".devpilot/approval/sensitive_action_catalog.json", "json", required=True),
            ]
        )
        return _section(
            "Approvals",
            refs,
            summary="Approval/RBAC sources are available.",
            metrics={
                "approval_module_present": (self.root / "src/devpilot_core/approval").exists(),
                "sensitive_action_catalog_present": (self.root / ".devpilot/approval/sensitive_action_catalog.json").exists(),
            },
        )

    def _release_section(self, section_sources: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        refs = list(section_sources.get("release") or [])
        refs.append(self._source_ref("src/devpilot_core/release", "directory", required=True))
        refs.append(self._source_ref("outputs/reports/release_verification.json", "generated-report", required=False))
        release_report = _read_json_if_exists(self.root / "outputs/reports/release_verification.json")
        return _section(
            "Release",
            refs,
            summary="Release module is available; release verification evidence may be absent in clean repos.",
            metrics={
                "release_module_present": (self.root / "src/devpilot_core/release").exists(),
                "release_verification_present": release_report is not None,
                "release_ready": bool(release_report and release_report.get("ok") is True),
            },
        )

    def _workspace_section(self, section_sources: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        refs = list(section_sources.get("workspace") or [])
        refs.append(self._source_ref(".devpilot/workspaces/workspace_registry.json", "json", required=False))
        registry = _read_json_if_exists(self.root / ".devpilot/workspaces/workspace_registry.json")
        workspaces = registry.get("workspaces") if isinstance(registry, dict) else []
        return _section(
            "Workspace",
            refs,
            summary="Workspace registry is available." if registry else "Workspace registry is not available.",
            metrics={
                "workspace_registry_present": registry is not None,
                "workspaces_total": len(workspaces) if isinstance(workspaces, list) else 0,
            },
        )

    def _recommended_next_actions(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        for item in config.get("recommended_next_actions", []):
            if not isinstance(item, dict):
                continue
            action_id = str(item.get("action_id") or "operator-action")
            command = str(item.get("command") or "")
            source_path = "src/devpilot_core/quality/gate.py" if "quality-gate" in command else ".devpilot/testing/test_contract_registry.json"
            actions.append(
                {
                    "action_id": action_id,
                    "command": command,
                    "reason": str(item.get("reason") or "Operator follow-up action."),
                    "priority": str(item.get("priority") or "P1"),
                    "dry_run": True,
                    "source_refs": [self._source_ref(source_path, "python" if source_path.endswith(".py") else "json", required=True)],
                }
            )
        if not actions:
            actions.append(
                {
                    "action_id": "validate-operator-dashboard-schema",
                    "command": "python -m devpilot_core schema validate --schema-id OperatorDashboardSnapshot --instance outputs/reports/operator_dashboard_snapshot.json --json",
                    "reason": "Validate the generated operator dashboard snapshot.",
                    "priority": "P1",
                    "dry_run": True,
                    "source_refs": [self._source_ref("docs/schemas/operator_dashboard_snapshot.schema.json", "json", required=True)],
                }
            )
        return actions

    def _source_ref(self, path: str, kind: str, *, required: bool, description: str = "") -> dict[str, Any]:
        ref = {"path": path, "kind": kind, "required": required, "available": (self.root / path).exists()}
        if description:
            ref["description"] = description
        return ref

    def _record_missing_required_sources(self, sections: dict[str, dict[str, Any]], findings: list[Finding]) -> None:
        for section_id, section in sections.items():
            for ref in section.get("source_refs", []):
                if ref.get("required") is True and ref.get("available") is not True:
                    findings.append(
                        Finding(
                            "OPERATOR_DASHBOARD_REQUIRED_SOURCE_MISSING",
                            "Required operator dashboard source is missing.",
                            Severity.BLOCK,
                            path=str(ref.get("path")),
                            metadata={"section": section_id, "created_by": POST_H_015_B_CREATED_BY},
                        )
                    )

    def _write_reports(self, snapshot: dict[str, Any], config: dict[str, Any]) -> dict[str, str]:
        json_path = self.root / str(config.get("snapshot_output_path") or "outputs/reports/operator_dashboard_snapshot.json")
        markdown_path = self.root / str(config.get("markdown_output_path") or "outputs/reports/operator_dashboard_snapshot.md")
        _assert_inside_root(self.root, json_path)
        _assert_inside_root(self.root, markdown_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(_snapshot_markdown(snapshot), encoding="utf-8")
        return {"json": _rel(json_path, self.root), "markdown": _rel(markdown_path, self.root)}


def _section(
    title: str,
    refs: list[dict[str, Any]],
    *,
    summary: str,
    score: int | float | None = None,
    blocking_findings_total: int | None = None,
    warnings_total: int | None = None,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    missing_required = any(ref.get("required") is True and ref.get("available") is not True for ref in refs)
    missing_optional = any(ref.get("required") is False and ref.get("available") is not True for ref in refs)
    status = "block" if missing_required else "unknown" if missing_optional else "pass"
    payload: dict[str, Any] = {"status": status, "title": title, "summary": summary, "source_refs": refs}
    if score is not None:
        payload["score"] = score
    if blocking_findings_total is not None:
        payload["blocking_findings_total"] = blocking_findings_total
    if warnings_total is not None:
        payload["warnings_total"] = warnings_total
    if metrics:
        payload["metrics"] = metrics
    return payload


def _overall_status(sections: dict[str, dict[str, Any]]) -> str:
    statuses = {str(section.get("status")) for section in sections.values()}
    if "block" in statuses:
        return "block"
    if "error" in statuses:
        return "error"
    if "unknown" in statuses or "warn" in statuses:
        return "warn"
    return "pass"


def _snapshot_id(generated_at: str) -> str:
    return "operator-dashboard-" + generated_at.replace("-", "").replace(":", "")


def _read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _contracts_total(payload: dict[str, Any] | None) -> int:
    if not isinstance(payload, dict):
        return 0
    contracts = payload.get("contracts")
    return len(contracts) if isinstance(contracts, list) else 0


def _int_or_none(value: Any) -> int | None:
    return value if isinstance(value, int) else None


def _count_missing_required_sources(snapshot: dict[str, Any]) -> int:
    return sum(1 for section in snapshot.get("sections", {}).values() for ref in section.get("source_refs", []) if ref.get("required") is True and ref.get("available") is not True)


def _count_missing_optional_sources(snapshot: dict[str, Any]) -> int:
    return sum(1 for section in snapshot.get("sections", {}).values() for ref in section.get("source_refs", []) if ref.get("required") is False and ref.get("available") is not True)


def _snapshot_markdown(snapshot: dict[str, Any]) -> str:
    lines = [
        "# Operator Dashboard Snapshot",
        "",
        f"- Snapshot: `{snapshot.get('snapshot_id')}`",
        f"- Status: `{snapshot.get('status')}`",
        f"- Generated at UTC: `{snapshot.get('generated_at_utc')}`",
        "",
        "## Sections",
        "",
    ]
    for section_id, section in snapshot.get("sections", {}).items():
        lines.append(f"- `{section_id}`: `{section.get('status')}` - {section.get('summary', '')}")
    lines.extend(["", "## Recommended Next Actions", ""])
    for action in snapshot.get("recommended_next_actions", []):
        lines.append(f"- `{action.get('action_id')}`: `{action.get('command')}`")
    return "\n".join(lines) + "\n"


def _assert_inside_root(root: Path, path: Path) -> None:
    path.resolve().relative_to(root.resolve())


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _posix(path: str | Path) -> str:
    return str(path).replace("\\", "/")
