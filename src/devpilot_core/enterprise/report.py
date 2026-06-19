from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.compliance import CompliancePackRegistry
from devpilot_core.identity import IdentityRegistry
from devpilot_core.miasi import MiasiRegistryValidator
from devpilot_core.policy import PolicyEngine, PolicyRequest
from devpilot_core.portfolio import PortfolioStatusBuilder
from devpilot_core.remote import RemoteRunnerStatusOptions, RemoteRunnerStub
from devpilot_core.schemas import SchemaRegistry


@dataclass(frozen=True)
class EnterpriseReportOptions:
    """Options for the local enterprise aggregate report."""

    remote_registry_path: str = ".devpilot/remote/runner_registry.json"
    remote_schema_path: str = "docs/schemas/remote_runner.schema.json"
    compliance_registry_path: str = ".devpilot/compliance/packs.json"
    workspace_registry_path: str = ".devpilot/workspaces/workspace_registry.json"


class EnterpriseReportBuilder:
    """Build a local read-only enterprise governance report.

    The Sprint 98 report aggregates already-governed local evidence: schemas,
    MIASI, identity/RBAC, portfolio, compliance packs and remote-runner status.
    It intentionally does not run remote jobs, does not call cloud services, does
    not read secrets and does not replace lower-level gates. It is a reporting
    overlay for enterprise reviewers, not a control plane.
    """

    def __init__(self, root: Path, *, options: EnterpriseReportOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or EnterpriseReportOptions()

    def build(self) -> CommandResult:
        policy = PolicyEngine(self.root).evaluate(
            PolicyRequest(
                action="read",
                path="docs/devpilot_backlog_fase_H_capacidades_avanzadas.md",
                dry_run=True,
                tool_id="enterprise.report",
                subject="local-enterprise-governance-report",
                actor="local-owner",
                metadata={"component": "EnterpriseReportBuilder", "sprint": "FUNC-SPRINT-98", "read_only": True},
            )
        )
        if not policy.ok:
            return CommandResult("enterprise report", False, policy.exit_code, "Enterprise report blocked by PolicyEngine.", data={"summary": {"policy_engine_used": True, "preliminary": True}}, findings=policy.findings)

        remote = RemoteRunnerStub(
            self.root,
            options=RemoteRunnerStatusOptions(registry_path=self.options.remote_registry_path, schema_path=self.options.remote_schema_path),
        ).status()
        portfolio = PortfolioStatusBuilder(self.root, registry_path=self.options.workspace_registry_path).build()
        compliance = CompliancePackRegistry(self.root).list()
        schemas = SchemaRegistry(self.root).list()
        miasi = MiasiRegistryValidator(self.root).validate_all()
        identity = IdentityRegistry(self.root).validate()

        artifacts = self._artifact_inventory()
        sprints = self._sprint_inventory()
        controls = {
            "policy_engine_used": True,
            "policy_engine_replaced": False,
            "remote_runner_disabled": _summary(remote).get("remote_runner_enabled") is False and _summary(remote).get("execution_allowed") is False,
            "cloud_control_plane_enabled": _summary(remote).get("cloud_control_plane_enabled") is True,
            "enterprise_report_read_only": True,
            "portfolio_available": portfolio.ok,
            "identity_rbac_available": identity.ok,
            "compliance_packs_available": compliance.ok,
            "miasi_available": miasi.ok,
            "schema_registry_available": schemas.ok,
            "audit_pack_available": (self.root / "docs/functional_sprint_96_manifest.json").is_file(),
            "compliance_manifest_available": (self.root / "docs/functional_sprint_97_manifest.json").is_file(),
        }
        positive_controls = {key: value for key, value in controls.items() if key not in {"policy_engine_replaced", "cloud_control_plane_enabled"}}
        gaps = [key for key, passed in positive_controls.items() if not passed]
        if controls["policy_engine_replaced"]:
            gaps.append("policy_engine_must_not_be_replaced")
        if controls["cloud_control_plane_enabled"]:
            gaps.append("cloud_control_plane_must_remain_disabled")
        findings: list[Finding] = []
        if gaps:
            findings.append(Finding("ENTERPRISE_REPORT_GAPS_DETECTED", "Enterprise report detected governance gaps.", Severity.BLOCK, metadata={"gaps": gaps}))
        else:
            findings.append(Finding("ENTERPRISE_REPORT_PASS", "Enterprise report aggregated local governance evidence without remote execution.", Severity.INFO, metadata={"sprints_total": sprints["manifests_total"]}))
        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        summary = {
            "local_first": True,
            "enterprise_report_read_only": True,
            "policy_engine_used": True,
            "policy_engine_replaced": False,
            "remote_runner_enabled": _summary(remote).get("remote_runner_enabled", False),
            "remote_execution_used": False,
            "cloud_control_plane_enabled": _summary(remote).get("cloud_control_plane_enabled", False),
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "gaps_total": len(gaps),
            "schemas_total": _summary(schemas).get("schemas_total", 0),
            "miasi_tools_total": _summary(miasi).get("tools_total", 0),
            "miasi_policy_rules_total": _summary(miasi).get("policy_rules_total", 0),
            "compliance_packs_total": _summary(compliance).get("packs_total", 0),
            "workspaces_total": _summary(portfolio).get("workspaces_total", 0),
            "sprint_manifests_total": sprints["manifests_total"],
            "latest_sprint_manifest": sprints["latest_manifest"],
            "preliminary": True,
        }
        return CommandResult(
            "enterprise report",
            not blocking,
            ExitCode.PASS if not blocking else ExitCode.BLOCK,
            "Enterprise report built locally in read-only mode." if not blocking else "Enterprise report detected governance gaps.",
            data={
                "summary": summary,
                "controls": controls,
                "gaps": gaps,
                "remote_runner": remote.data.get("summary", {}),
                "portfolio": portfolio.data.get("summary", {}),
                "identity": identity.data.get("summary", {}),
                "compliance": compliance.data.get("summary", {}),
                "schemas": schemas.data.get("summary", {}),
                "miasi": miasi.data.get("summary", {}),
                "artifacts": artifacts,
                "sprints": sprints,
                "policy": policy.data,
            },
            findings=findings,
        )

    def _artifact_inventory(self) -> dict[str, Any]:
        docs = self.root / "docs"
        audits = docs / "audits"
        schemas = docs / "schemas"
        reports = self.root / "outputs" / "reports"
        return {
            "docs_present": docs.is_dir(),
            "audits_total": len(list(audits.glob("*.md"))) if audits.is_dir() else 0,
            "schemas_total": len(list(schemas.glob("*.json"))) if schemas.is_dir() else 0,
            "runtime_reports_present": reports.is_dir(),
            "runtime_reports_read": False,
            "secrets_read": False,
            "state_db_read": False,
        }

    def _sprint_inventory(self) -> dict[str, Any]:
        manifests = sorted(self.root.glob("docs/functional_sprint_*_manifest.json"))
        ids: list[str] = []
        for path in manifests:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            sprint_id = payload.get("sprint_id")
            if isinstance(sprint_id, str):
                ids.append(sprint_id)
        return {
            "manifests_total": len(manifests),
            "sprint_ids_total": len(ids),
            "latest_manifest": manifests[-1].name if manifests else None,
            "latest_sprint_id": ids[-1] if ids else None,
        }


def _summary(result: CommandResult) -> dict[str, Any]:
    data = result.data or {}
    summary = data.get("summary") if isinstance(data, dict) else None
    return summary if isinstance(summary, dict) else {}
