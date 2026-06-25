from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

POST_H_007_A_CREATED_BY = "POST-H-007-A"
APPLICATION_SERVICE_BOUNDARY_REPORT_ID = "devpilot-application-service-boundary-report"
APPLICATION_SERVICE_BOUNDARY_REPORT_SCHEMA_ID = "SCHEMA-DEVPL-APPLICATION-SERVICE-BOUNDARY-REPORT-V1"


@dataclass(frozen=True)
class ApplicationBoundaryOperation:
    """Static inventory row for one operation visible at the ApplicationService boundary.

    POST-H-007-A keeps this descriptor intentionally read-only and evidence-only.
    It does not execute operations, does not register runtime routes and does not
    alter CLI/API/UI behaviour. Later POST-H-007 micro-sprints can promote these
    rows into stricter operation catalog descriptors.
    """

    operation_id: str
    domain: str
    service: str
    method: str
    request_contract: str = "ApplicationRequest"
    response_contract: str = "ApplicationResponse"
    cli_commands: list[str] = field(default_factory=list)
    api_routes: list[str] = field(default_factory=list)
    ui_surfaces: list[str] = field(default_factory=list)
    policy_required: bool = False
    dry_run_default: bool = True
    writes_files: bool = False
    risk_level: str = "medium"
    direct_core_bypass: bool = False
    source: str = "static-analysis"

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "domain": self.domain,
            "service": self.service,
            "method": self.method,
            "request_contract": self.request_contract,
            "response_contract": self.response_contract,
            "cli_commands": list(self.cli_commands),
            "api_routes": list(self.api_routes),
            "ui_surfaces": list(self.ui_surfaces),
            "policy_required": self.policy_required,
            "dry_run_default": self.dry_run_default,
            "writes_files": self.writes_files,
            "risk_level": self.risk_level,
            "direct_core_bypass": self.direct_core_bypass,
            "source": self.source,
        }


@dataclass(frozen=True)
class ApplicationBoundaryBypass:
    """Static finding for one interface path that does not yet pass through ApplicationService."""

    interface: str
    identifier: str
    domain: str
    owner_module: str
    risk_level: str
    side_effects: list[str] = field(default_factory=list)
    writes_files: bool = False
    policy_required: bool = False
    reason: str = "No explicit ApplicationService boundary was detected by POST-H-007-A static analysis."
    recommendation: str = "Add an ApplicationService operation descriptor before changing runtime behaviour."

    def to_dict(self) -> dict[str, Any]:
        return {
            "interface": self.interface,
            "identifier": self.identifier,
            "domain": self.domain,
            "owner_module": self.owner_module,
            "risk_level": self.risk_level,
            "side_effects": list(self.side_effects),
            "writes_files": self.writes_files,
            "policy_required": self.policy_required,
            "reason": self.reason,
            "recommendation": self.recommendation,
        }
