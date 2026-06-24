from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CapabilityStatus(str, Enum):
    """Controlled maturity status vocabulary for POST-H-002 dashboards.

    The vocabulary intentionally uses ``production-ready-local`` and does not
    expose a generic ``production-ready`` value. DevPilot can only claim local
    production readiness after the final declaration gate; enterprise, remote
    and compliance claims remain outside this model.
    """

    PRODUCTION_READY_LOCAL = "production-ready-local"
    IMPLEMENTED = "implemented"
    IMPLEMENTED_INITIAL = "implemented-initial"
    EXPERIMENTAL = "experimental"
    PLANNED = "planned"
    STUB = "stub"
    BLOCKED = "blocked"


class MaturityLevel(str, Enum):
    """Human-facing maturity level used by the local dashboard."""

    ALTA_LOCAL = "alta-local"
    MEDIA_ALTA = "media-alta"
    MEDIA = "media"
    BAJA = "baja"
    NO_HABILITADA = "no-habilitada"


class TestCoverageLevel(str, Enum):
    """Coarse-grained test coverage levels for capability summaries."""

    ALTA = "alta"
    MEDIA_ALTA = "media-alta"
    MEDIA = "media"
    BAJA = "baja"
    NA = "n/a"


TestCoverageLevel.__test__ = False


class RiskLevel(str, Enum):
    """Risk vocabulary aligned with post-H assessment and roadmap language."""

    CRITICO = "critico"
    ALTO = "alto"
    MEDIO_ALTO = "medio-alto"
    MEDIO = "medio"
    BAJO = "bajo"


@dataclass(frozen=True)
class SafetySignal:
    """Safety invariants surfaced by the maturity dashboard.

    POST-H-002-A is model/schema only: these fields are consumed by later
    builders and gates to prove that the dashboard does not enable remote
    execution, connector writes, plugin execution or external APIs by default.
    """

    remote_execution_enabled: bool = False
    connector_write_enabled: bool = False
    plugin_execution_enabled: bool = False
    external_apis_enabled_by_default: bool = False
    network_used: bool = False
    mutations_performed: bool = False
    preliminary: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "remote_execution_enabled": self.remote_execution_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "plugin_execution_enabled": self.plugin_execution_enabled,
            "external_apis_enabled_by_default": self.external_apis_enabled_by_default,
            "network_used": self.network_used,
            "mutations_performed": self.mutations_performed,
            "preliminary": self.preliminary,
        }


@dataclass(frozen=True)
class RoadmapDependency:
    """Relationship between a roadmap milestone and capabilities it unblocks."""

    milestone: str
    unblocks: list[str]
    priority: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "milestone": self.milestone,
            "unblocks": list(self.unblocks),
            "priority": self.priority,
        }


@dataclass(frozen=True)
class MaturityCapability:
    """One capability row in the local maturity dashboard."""

    capability_id: str
    name: str
    domain: str
    status: CapabilityStatus
    maturity: MaturityLevel
    test_coverage: TestCoverageLevel
    risk: RiskLevel
    source_evidence: list[str]
    roadmap_dependency: str | None = None
    no_go_gate: bool = False
    notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "capability_id": self.capability_id,
            "name": self.name,
            "domain": self.domain,
            "status": self.status.value,
            "maturity": self.maturity.value,
            "test_coverage": self.test_coverage.value,
            "risk": self.risk.value,
            "source_evidence": list(self.source_evidence),
            "roadmap_dependency": self.roadmap_dependency,
            "no_go_gate": self.no_go_gate,
            "notes": list(self.notes),
            "metadata": dict(self.metadata),
        }
        return payload


@dataclass(frozen=True)
class MaturityDashboard:
    """Schema-backed model for POST-H-002 local maturity dashboards."""

    dashboard_id: str
    generated_at_utc: str
    roadmap_version: str
    post_h_eval_status: str
    capabilities: list[MaturityCapability]
    roadmap_alignment: list[RoadmapDependency]
    safety: SafetySignal = field(default_factory=SafetySignal)
    schema_version: str = "1.0"
    preliminary: bool = True

    def summary(self) -> dict[str, int]:
        counts = {status.value: 0 for status in CapabilityStatus}
        for capability in self.capabilities:
            counts[capability.status.value] += 1
        critical_risks_total = sum(1 for item in self.capabilities if item.risk == RiskLevel.CRITICO)
        blocking_gaps_total = sum(1 for item in self.capabilities if item.no_go_gate or item.status == CapabilityStatus.BLOCKED)
        return {
            "capabilities_total": len(self.capabilities),
            "production_ready_local_total": counts[CapabilityStatus.PRODUCTION_READY_LOCAL.value],
            "implemented_total": counts[CapabilityStatus.IMPLEMENTED.value],
            "implemented_initial_total": counts[CapabilityStatus.IMPLEMENTED_INITIAL.value],
            "experimental_total": counts[CapabilityStatus.EXPERIMENTAL.value],
            "planned_total": counts[CapabilityStatus.PLANNED.value],
            "stub_total": counts[CapabilityStatus.STUB.value],
            "blocked_total": counts[CapabilityStatus.BLOCKED.value],
            "critical_risks_total": critical_risks_total,
            "blocking_gaps_total": blocking_gaps_total,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "dashboard_id": self.dashboard_id,
            "generated_at_utc": self.generated_at_utc,
            "source_revision": {
                "roadmap_version": self.roadmap_version,
                "post_h_eval_status": self.post_h_eval_status,
            },
            "summary": self.summary(),
            "capabilities": [capability.to_dict() for capability in self.capabilities],
            "roadmap_alignment": [dependency.to_dict() for dependency in self.roadmap_alignment],
            "safety": self.safety.to_dict(),
            "preliminary": self.preliminary,
        }
