from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

ARCHITECTURE_MAP_SCHEMA_ID = "SCHEMA-DEVPL-ARCHITECTURE-MAP-V1"
ARCHITECTURE_MAP_CONTRACT = "ArchitectureMap"
ARCHITECTURE_MAP_VERSION = "1.0"


def _now_utc_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class ArchitectureCriticality(str, Enum):
    """Criticality vocabulary used by the executable architecture map."""

    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class ArchitectureRiskLevel(str, Enum):
    """Risk level vocabulary aligned with post-H hardening reports."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DependencyKind(str, Enum):
    """Dependency edge categories expected from future AST/import analysis."""

    INTERNAL_IMPORT = "internal-import"
    EXTERNAL_IMPORT = "external-import"
    TEST_REFERENCE = "test-reference"
    CLI_REFERENCE = "cli-reference"
    SCHEMA_REFERENCE = "schema-reference"
    DOCUMENTATION_REFERENCE = "documentation-reference"


class DependencyPolicy(str, Enum):
    """Boundary policy decision for one dependency edge."""

    ALLOW = "allow"
    RESTRICTED = "restricted"
    FORBIDDEN = "forbidden"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ArchitectureModule:
    """One Python module discovered by the future POST-H-005-B AST inventory.

    POST-H-005-A defines only the stable payload. Later micro-sprints will
    populate these fields from the repository without introducing external
    tooling or source mutations.
    """

    module_id: str
    package: str
    path: str
    loc: int = 0
    classes_total: int = 0
    functions_total: int = 0
    imports_total: int = 0
    exports_total: int = 0
    is_cli_entrypoint: bool = False
    is_test_module: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_id": self.module_id,
            "package": self.package,
            "path": self.path,
            "loc": self.loc,
            "classes_total": self.classes_total,
            "functions_total": self.functions_total,
            "imports_total": self.imports_total,
            "exports_total": self.exports_total,
            "is_cli_entrypoint": self.is_cli_entrypoint,
            "is_test_module": self.is_test_module,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class OwnershipEntry:
    """Declarative owner/boundary contract for one package or package family."""

    package: str
    domain: str
    owner: str
    criticality: ArchitectureCriticality | str
    risk_level: ArchitectureRiskLevel | str
    allowed_dependencies: tuple[str, ...] = ()
    restricted_dependencies: tuple[str, ...] = ()
    forbidden_dependencies: tuple[str, ...] = ()
    test_contracts: tuple[str, ...] = ()
    notes: str = ""
    preliminary: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "package": self.package,
            "domain": self.domain,
            "owner": self.owner,
            "criticality": _enum_value(self.criticality),
            "risk_level": _enum_value(self.risk_level),
            "allowed_dependencies": list(self.allowed_dependencies),
            "restricted_dependencies": list(self.restricted_dependencies),
            "forbidden_dependencies": list(self.forbidden_dependencies),
            "test_contracts": list(self.test_contracts),
            "notes": self.notes,
            "preliminary": self.preliminary,
        }


@dataclass(frozen=True)
class ArchitecturePackage:
    """Package-level summary for ownership, dependency and hotspot reporting."""

    package: str
    domain: str
    owner: str | None
    criticality: ArchitectureCriticality | str
    risk_level: ArchitectureRiskLevel | str
    modules: tuple[str, ...] = ()
    direct_dependencies: tuple[str, ...] = ()
    fan_in: int = 0
    fan_out: int = 0
    loc: int = 0
    test_contracts: tuple[str, ...] = ()
    ownership_status: str = "declared"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "package": self.package,
            "domain": self.domain,
            "owner": self.owner,
            "criticality": _enum_value(self.criticality),
            "risk_level": _enum_value(self.risk_level),
            "modules": list(self.modules),
            "direct_dependencies": list(self.direct_dependencies),
            "fan_in": self.fan_in,
            "fan_out": self.fan_out,
            "loc": self.loc,
            "test_contracts": list(self.test_contracts),
            "ownership_status": self.ownership_status,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class DependencyEdge:
    """Directed architecture dependency edge."""

    source: str
    target: str
    kind: DependencyKind | str
    policy: DependencyPolicy | str = DependencyPolicy.UNKNOWN
    sensitive: bool = False
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "kind": _enum_value(self.kind),
            "policy": _enum_value(self.policy),
            "sensitive": self.sensitive,
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class Hotspot:
    """Architecture hotspot candidate calculated by future POST-H-005-D."""

    subject_id: str
    subject_type: str
    score: float
    criticality: ArchitectureCriticality | str
    reasons: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "subject_type": self.subject_type,
            "score": self.score,
            "criticality": _enum_value(self.criticality),
            "reasons": list(self.reasons),
            "recommendations": list(self.recommendations),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ArchitectureMapSafety:
    """Safety invariants for architecture map generation."""

    dry_run: bool = True
    network_used: bool = False
    external_api_used: bool = False
    mutations_performed: bool = False
    source_mutations_performed: bool = False
    remote_execution_enabled: bool = False
    connector_write_enabled: bool = False
    plugin_execution_enabled: bool = False
    preliminary: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "dry_run": self.dry_run,
            "network_used": self.network_used,
            "external_api_used": self.external_api_used,
            "mutations_performed": self.mutations_performed,
            "source_mutations_performed": self.source_mutations_performed,
            "remote_execution_enabled": self.remote_execution_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "plugin_execution_enabled": self.plugin_execution_enabled,
            "preliminary": self.preliminary,
        }


@dataclass(frozen=True)
class ArchitectureMap:
    """Top-level schema-backed architecture map contract.

    POST-H-005-A is deliberately schema/model/ownership only. Inventory,
    dependency graph, hotspot scoring and final report generation are introduced
    by POST-H-005-B/C/D/E.
    """

    map_id: str
    created_by: str
    packages: tuple[ArchitecturePackage, ...]
    modules: tuple[ArchitectureModule, ...] = ()
    dependencies: tuple[DependencyEdge, ...] = ()
    hotspots: tuple[Hotspot, ...] = ()
    ownership_registry: tuple[OwnershipEntry, ...] = ()
    ownership_gaps: tuple[dict[str, Any], ...] = ()
    recommendations: tuple[str, ...] = ()
    source_paths: dict[str, str] = field(default_factory=dict)
    generated_at_utc: str = field(default_factory=_now_utc_iso)
    status: str = "implemented-initial"
    schema_version: str = ARCHITECTURE_MAP_VERSION
    schema_id: str = ARCHITECTURE_MAP_SCHEMA_ID
    safety: ArchitectureMapSafety = field(default_factory=ArchitectureMapSafety)
    preliminary: bool = True

    def summary(self) -> dict[str, int]:
        forbidden_dependency_findings_total = sum(1 for edge in self.dependencies if _enum_value(edge.policy) == DependencyPolicy.FORBIDDEN.value)
        unowned_packages_total = sum(1 for package in self.packages if not package.owner or package.ownership_status == "missing")
        return {
            "packages_total": len(self.packages),
            "modules_total": len(self.modules),
            "dependencies_total": len(self.dependencies),
            "hotspots_total": len(self.hotspots),
            "ownership_entries_total": len(self.ownership_registry),
            "forbidden_dependency_findings_total": forbidden_dependency_findings_total,
            "unowned_packages_total": unowned_packages_total,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "schema_id": self.schema_id,
            "map_id": self.map_id,
            "created_by": self.created_by,
            "status": self.status,
            "generated_at_utc": self.generated_at_utc,
            "preliminary": self.preliminary,
            "source_paths": dict(self.source_paths),
            "summary": self.summary(),
            "packages": [package.to_dict() for package in self.packages],
            "modules": [module.to_dict() for module in self.modules],
            "dependencies": [edge.to_dict() for edge in self.dependencies],
            "hotspots": [hotspot.to_dict() for hotspot in self.hotspots],
            "ownership_registry": [entry.to_dict() for entry in self.ownership_registry],
            "ownership_gaps": list(self.ownership_gaps),
            "recommendations": list(self.recommendations),
            "safety": self.safety.to_dict(),
        }


def _enum_value(value: Enum | str) -> str:
    return value.value if isinstance(value, Enum) else str(value)
