from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .dtos import ApplicationRequest

POST_H_007_C_CREATED_BY = "POST-H-007-C"
APPLICATION_DTO_NORMALIZATION_REPORT_ID = "devpilot-application-dto-normalization-report"

PRIORITY_OPERATION_IDS: tuple[str, ...] = (
    "workspace.status",
    "validation.docs",
    "validation.contracts",
    "reports.list",
    "reports.read",
    "approvals.list",
    "settings.status",
    "repo.inventory",
    "review.code",
    "refactor.plan",
    "observability.traces",
)


@dataclass(frozen=True)
class PriorityDtoOperation:
    """Descriptor for one POST-H-007-C priority DTO operation.

    The descriptor is intentionally small and local-only. It is not a runtime
    permission system; POST-H-007-D owns per-interface policy enforcement.
    POST-H-007-C only makes the selected operations consistently executable
    through ApplicationRequest and ApplicationResponse while preserving the
    underlying CommandResult produced by existing domain services.
    """

    operation_id: str
    domain: str
    description: str
    default_payload: dict[str, Any] = field(default_factory=dict)
    cli_equivalent: str | None = None
    canonical_result: str = "CommandResult"
    response_contract: str = "ApplicationResponse"
    preserves_findings: bool = True
    preserves_exit_code: bool = True
    preserves_data: bool = True
    dry_run_default: bool = True
    preliminary: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "domain": self.domain,
            "description": self.description,
            "default_payload": dict(self.default_payload),
            "cli_equivalent": self.cli_equivalent,
            "canonical_result": self.canonical_result,
            "response_contract": self.response_contract,
            "preserves_findings": self.preserves_findings,
            "preserves_exit_code": self.preserves_exit_code,
            "preserves_data": self.preserves_data,
            "dry_run_default": self.dry_run_default,
            "preliminary": self.preliminary,
        }


_PRIORITY_DTO_OPERATION_MAP: dict[str, PriorityDtoOperation] = {
    "workspace.status": PriorityDtoOperation(
        operation_id="workspace.status",
        domain="workspace",
        description="Read current workspace status through the ApplicationService DTO boundary.",
        cli_equivalent="python -m devpilot_core workspace status --json",
    ),
    "validation.docs": PriorityDtoOperation(
        operation_id="validation.docs",
        domain="validation",
        description="Run the documentation validation gateway through ApplicationRequest/ApplicationResponse.",
        default_payload={"scope": "docs"},
        cli_equivalent="python -m devpilot_core validate docs --json",
    ),
    "validation.contracts": PriorityDtoOperation(
        operation_id="validation.contracts",
        domain="validation",
        description="Run the structural contract validation gateway through ApplicationRequest/ApplicationResponse.",
        default_payload={"scope": "contracts"},
        cli_equivalent="python -m devpilot_core validate contracts --json",
    ),
    "reports.list": PriorityDtoOperation(
        operation_id="reports.list",
        domain="reports",
        description="List local report metadata through the DTO boundary.",
        default_payload={"limit": 50},
    ),
    "reports.read": PriorityDtoOperation(
        operation_id="reports.read",
        domain="reports",
        description="Read one local report through the DTO boundary using a report_id payload.",
        default_payload={"format": "json", "max_chars": 20000},
    ),
    "approvals.list": PriorityDtoOperation(
        operation_id="approvals.list",
        domain="approvals",
        description="List local approval requests through the DTO boundary.",
        default_payload={"limit": 100},
    ),
    "settings.status": PriorityDtoOperation(
        operation_id="settings.status",
        domain="settings",
        description="Return a read-only aggregate of workspace/provider/policy settings status.",
    ),
    "repo.inventory": PriorityDtoOperation(
        operation_id="repo.inventory",
        domain="repo",
        description="Run repository inventory through the DTO boundary.",
    ),
    "review.code": PriorityDtoOperation(
        operation_id="review.code",
        domain="review",
        description="Run deterministic local code review through the DTO boundary.",
        default_payload={"target": "."},
    ),
    "refactor.plan": PriorityDtoOperation(
        operation_id="refactor.plan",
        domain="refactor",
        description="Build a dry-run refactor plan through the DTO boundary.",
        default_payload={"target": ".", "goal": "", "include_code_review": True},
    ),
    "observability.traces": PriorityDtoOperation(
        operation_id="observability.traces",
        domain="observability",
        description="Read the local trace summary through the DTO boundary.",
        default_payload={"limit": 20, "include_events": True, "include_metrics": True},
    ),
}


def priority_dto_operations() -> list[PriorityDtoOperation]:
    """Return POST-H-007-C priority operation descriptors in stable backlog order."""

    return [_PRIORITY_DTO_OPERATION_MAP[operation_id] for operation_id in PRIORITY_OPERATION_IDS]


def priority_dto_operation_ids() -> tuple[str, ...]:
    """Return operation ids covered by POST-H-007-C."""

    return PRIORITY_OPERATION_IDS


def is_priority_dto_operation(operation_id: str) -> bool:
    return operation_id in _PRIORITY_DTO_OPERATION_MAP


def normalize_priority_application_request(request: ApplicationRequest) -> ApplicationRequest:
    """Apply POST-H-007-C default payloads without changing the requested operation.

    The function deliberately preserves `request.operation` so the resulting
    ApplicationResponse keeps the public operation id requested by API/UI/CLI
    adapters. Defaults only fill omitted keys; user payload values win.
    """

    descriptor = _PRIORITY_DTO_OPERATION_MAP.get(request.operation)
    if descriptor is None:
        return request
    payload = dict(descriptor.default_payload)
    payload.update(dict(request.payload or {}))
    return ApplicationRequest(
        operation=request.operation,
        payload=payload,
        client=request.client,
        dry_run=request.dry_run if request.dry_run is not None else descriptor.dry_run_default,
    )


def application_dto_normalization_report() -> dict[str, Any]:
    """Return a machine-readable static report for POST-H-007-C documentation/tests."""

    operations = [operation.to_dict() for operation in priority_dto_operations()]
    return {
        "report_id": APPLICATION_DTO_NORMALIZATION_REPORT_ID,
        "created_by": POST_H_007_C_CREATED_BY,
        "status": "implemented-initial",
        "preliminary": True,
        "operations": operations,
        "summary": {
            "operations_total": len(operations),
            "operations_required_total": len(PRIORITY_OPERATION_IDS),
            "operations_covered_total": len(operations),
            "preserves_findings": all(operation["preserves_findings"] for operation in operations),
            "preserves_exit_code": all(operation["preserves_exit_code"] for operation in operations),
            "preserves_data": all(operation["preserves_data"] for operation in operations),
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "runtime_routes_added": False,
            "public_cli_commands_added": False,
            "preliminary": True,
        },
        "notes": [
            "POST-H-007-C normalizes selected ApplicationRequest/ApplicationResponse paths without replacing CommandResult.",
            "Boundary authorization and per-interface allow/deny decisions remain deferred to POST-H-007-D.",
            "CLI registry integration remains deferred to POST-H-007-E.",
        ],
    }
