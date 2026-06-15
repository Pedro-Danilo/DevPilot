from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from devpilot_core.cli_models import CommandResult


@dataclass(frozen=True)
class ApplicationRequest:
    """Serializable request envelope for future API local/Web UI clients.

    FUNC-SPRINT-18 introduces this DTO and FUNC-SPRINT-65 reuses it
    to keep interface clients from calling domain/core modules directly. It is intentionally small, local-first and JSON-safe.
    It does not carry secrets, credentials or transport-specific state.
    """

    operation: str
    payload: dict[str, Any] = field(default_factory=dict)
    client: str = "cli"
    dry_run: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "payload": self.payload,
            "client": self.client,
            "dry_run": self.dry_run,
        }


@dataclass(frozen=True)
class ApplicationResponse:
    """Serializable response envelope shared by CLI, API local and Web UI shells.

    It wraps the existing CommandResult contract without replacing it. This
    provides a stable UI-facing shape while preserving the current CLI JSON
    output and exit-code semantics.
    """

    operation: str
    ok: bool
    exit_code: int
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    findings: list[dict[str, Any]] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"))
    contract: str = "DevPilotApplicationResponse"
    schema_version: str = "1.0"

    @classmethod
    def from_command_result(cls, result: CommandResult, *, operation: str | None = None) -> "ApplicationResponse":
        return cls(
            operation=operation or result.command,
            ok=result.ok,
            exit_code=int(result.exit_code),
            message=result.message,
            data=result.data,
            findings=[finding.to_dict() for finding in result.findings],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "schema_version": self.schema_version,
            "operation": self.operation,
            "ok": self.ok,
            "exit_code": self.exit_code,
            "message": self.message,
            "data": self.data,
            "findings": self.findings,
            "generated_at": self.generated_at,
        }


@dataclass(frozen=True)
class ServiceCapability:
    """UI/API-facing description of one callable ApplicationService v2 operation."""

    operation: str
    description: str
    side_effect: str
    dry_run_default: bool
    command_equivalent: str
    output_contract: str = "CommandResult + ApplicationResponse"

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "description": self.description,
            "side_effect": self.side_effect,
            "dry_run_default": self.dry_run_default,
            "command_equivalent": self.command_equivalent,
            "output_contract": self.output_contract,
        }


@dataclass(frozen=True)
class InterfaceRouteContract:
    """Logical route contract for future API local/Web UI integration.

    These are not active HTTP routes and do not implement UI. They document
    stable service boundaries that the future FastAPI API and Web UI can
    map to ApplicationService v2 without duplicating DevPilot Core logic. Desktop remains deferred outside Fase F.
    """

    route_id: str
    method: str
    path: str
    operation: str
    status: str = "contract-only"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "method": self.method,
            "path": self.path,
            "operation": self.operation,
            "status": self.status,
            "notes": self.notes,
        }
