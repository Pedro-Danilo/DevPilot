from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.architecture.hotspots import ArchitectureHotspotsBuilder, ArchitectureHotspotsOptions
from devpilot_core.architecture.ownership import DEFAULT_OWNERSHIP_REGISTRY, load_ownership_registry, ownership_entries_from_payload
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import redact_sensitive_data, redact_string
from devpilot_core.schemas import SchemaValidator

DEFAULT_SOURCE_ROOT = Path("src/devpilot_core")
DEFAULT_OUTPUT_JSON = Path("outputs/reports/architecture_map.json")
DEFAULT_OUTPUT_MD = Path("outputs/reports/architecture_map.md")
POST_H_005_E_REPORT_ID = "architecture-map-post-h-005-e"
REQUIRED_CRITICAL_PACKAGES = {
    "devpilot_core.cli",
    "devpilot_core.policy",
    "devpilot_core.schemas",
    "devpilot_core.agents",
    "devpilot_core.testing",
    "devpilot_core.quality",
    "devpilot_core.industrial",
    "devpilot_core.application",
    "devpilot_core.miasi",
}


@dataclass(frozen=True)
class ArchitectureMapReportOptions:
    """Options for POST-H-005-E ownership validation and final report."""

    source_root: Path = DEFAULT_SOURCE_ROOT
    tests_root: Path = Path("tests")
    ownership_registry: Path = DEFAULT_OWNERSHIP_REGISTRY
    top_limit: int = 20
    output_json: Path = DEFAULT_OUTPUT_JSON
    output_markdown: Path = DEFAULT_OUTPUT_MD
    write_report: bool = False


class ArchitectureMapReportBuilder:
    """Build the final executable ArchitectureMap report for POST-H-005.

    The builder is intentionally local-first and read-only with respect to the
    source tree. It consumes the POST-H-005-D hotspot payload, validates the
    ownership registry, emits ownership gaps and recommendations, and optionally
    writes the canonical raw ArchitectureMap files expected by the backlog:
    ``outputs/reports/architecture_map.json`` and ``outputs/reports/architecture_map.md``.
    """

    def __init__(self, root: Path, options: ArchitectureMapReportOptions | None = None) -> None:
        self.root = Path(root)
        self.options = options or ArchitectureMapReportOptions()

    def build(self) -> CommandResult:
        hotspots_result = ArchitectureHotspotsBuilder(
            self.root,
            ArchitectureHotspotsOptions(
                source_root=self.options.source_root,
                tests_root=self.options.tests_root,
                ownership_registry=self.options.ownership_registry,
                top_limit=self.options.top_limit,
            ),
        ).build()
        if not hotspots_result.ok:
            return CommandResult(
                command="architecture map",
                ok=False,
                exit_code=hotspots_result.exit_code,
                message="Architecture map blocked because hotspot analysis failed.",
                data=hotspots_result.data,
                findings=hotspots_result.findings,
            )

        architecture_map = dict((hotspots_result.data or {}).get("architecture_map", {}))
        findings: list[Finding] = list(hotspots_result.findings)
        ownership_payload, ownership_findings = self._load_and_validate_ownership_registry()
        findings.extend(ownership_findings)

        ownership_entries = ownership_entries_from_payload(ownership_payload) if ownership_payload else []
        ownership_by_package = {entry.package: entry for entry in ownership_entries}
        packages = [dict(item) for item in architecture_map.get("packages", []) if isinstance(item, dict)]
        dependencies = [dict(item) for item in architecture_map.get("dependencies", []) if isinstance(item, dict)]
        hotspots = [dict(item) for item in architecture_map.get("hotspots", []) if isinstance(item, dict)]

        ownership_gaps = self._ownership_gaps(packages, ownership_by_package)
        findings.extend(self._ownership_gap_findings(ownership_gaps))
        critical_contract_findings = self._critical_contract_findings(packages, ownership_by_package)
        findings.extend(critical_contract_findings)
        findings.extend(self._required_package_findings(packages, ownership_by_package))

        recommendations = self._recommendations(packages=packages, dependencies=dependencies, hotspots=hotspots, ownership_gaps=ownership_gaps)
        architecture_map["created_by"] = "POST-H-005-E"
        architecture_map["map_id"] = "devpilot-post-h-005-executable-architecture-map"
        architecture_map["status"] = "implemented-initial"
        architecture_map["ownership_registry"] = [entry.to_dict() for entry in ownership_entries]
        architecture_map["ownership_gaps"] = ownership_gaps
        architecture_map["recommendations"] = recommendations
        architecture_map["source_paths"] = {
            **dict(architecture_map.get("source_paths", {})),
            "source_root": str(self.options.source_root).replace("\\", "/"),
            "tests_root": str(self.options.tests_root).replace("\\", "/"),
            "ownership_registry": str(self.options.ownership_registry).replace("\\", "/"),
            "schema": "docs/schemas/architecture_map.schema.json",
            "output_json": str(self.options.output_json).replace("\\", "/"),
            "output_markdown": str(self.options.output_markdown).replace("\\", "/"),
        }
        architecture_map["summary"] = {
            **dict(architecture_map.get("summary", {})),
            "ownership_entries_total": len(ownership_entries),
            "ownership_gaps_total": len(ownership_gaps),
            "unowned_packages_total": sum(1 for gap in ownership_gaps if gap.get("gap_type") == "missing-owner"),
            "critical_packages_missing_test_contracts_total": sum(
                1 for gap in ownership_gaps if gap.get("gap_type") == "critical-missing-test-contracts"
            ),
            "forbidden_dependency_findings_total": sum(1 for edge in dependencies if edge.get("policy") == "forbidden"),
            "restricted_dependency_findings_total": sum(1 for edge in dependencies if edge.get("policy") == "restricted"),
            "sensitive_dependencies_total": sum(1 for edge in dependencies if edge.get("sensitive") is True),
        }

        schema_validation = SchemaValidator(self.root).validate_payload(
            schema="ArchitectureMap",
            payload=architecture_map,
            instance_label="in-memory:architecture-map-final",
        )
        if not schema_validation.ok:
            findings.extend(schema_validation.findings)

        output_paths: dict[str, str] = {}
        if self.options.write_report and schema_validation.ok:
            output_paths = self._write_raw_reports(architecture_map, findings=findings)

        blocking_findings_total = sum(1 for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL})
        warnings_total = sum(1 for finding in findings if finding.severity == Severity.WARNING)
        summary = {
            **architecture_map["summary"],
            "top_hotspots_limit": self.options.top_limit,
            "schema_validation_ok": schema_validation.ok,
            "reports_written": bool(output_paths),
            "output_json": output_paths.get("json"),
            "output_markdown": output_paths.get("markdown"),
            "warnings_total": warnings_total,
            "blocking_findings_total": blocking_findings_total,
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
        data = {
            "summary": summary,
            "architecture_map": architecture_map,
            "ownership_validation": {
                "registry_path": str(self.options.ownership_registry).replace("\\", "/"),
                "entries_total": len(ownership_entries),
                "gaps_total": len(ownership_gaps),
                "critical_packages_required": sorted(REQUIRED_CRITICAL_PACKAGES),
                "critical_packages_missing_test_contracts_total": summary["critical_packages_missing_test_contracts_total"],
            },
            "schema_validation": (schema_validation.data or {}).get("summary", {}),
            "output_paths": output_paths,
            "notes": [
                "POST-H-005-E materializes the final ArchitectureMap report as raw schema-valid JSON plus a human Markdown summary.",
                "Ownership gaps and dependency policy findings remain advisory warnings in this hito; no runtime enforcement, refactor or boundary mutation is performed.",
                "The report is intended as objective input for POST-H-006 CLI command registry and POST-H-007 ApplicationService boundary hardening.",
            ],
            "tests_executed": False,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
        ok = schema_validation.ok and blocking_findings_total == 0
        if ok:
            findings.append(
                Finding(
                    id="ARCHITECTURE_MAP_PASS",
                    message="Executable architecture map report completed without blocking findings.",
                    severity=Severity.INFO,
                    metadata={
                        "packages_total": summary["packages_total"],
                        "modules_total": summary["modules_total"],
                        "dependencies_total": summary["dependencies_total"],
                        "hotspots_total": summary["hotspots_total"],
                        "ownership_gaps_total": summary["ownership_gaps_total"],
                        "reports_written": bool(output_paths),
                    },
                )
            )
        return CommandResult(
            command="architecture map",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Executable architecture map passed." if ok else "Executable architecture map failed with blocking findings.",
            data=data,
            findings=findings,
        )

    def _load_and_validate_ownership_registry(self) -> tuple[dict[str, Any], list[Finding]]:
        findings: list[Finding] = []
        try:
            payload = load_ownership_registry(self.root, self.options.ownership_registry)
        except FileNotFoundError:
            return {}, [
                Finding(
                    id="ARCHITECTURE_OWNERSHIP_REGISTRY_MISSING",
                    message="Architecture ownership registry is missing.",
                    severity=Severity.BLOCK,
                    path=str(self.options.ownership_registry).replace("\\", "/"),
                )
            ]
        except json.JSONDecodeError as exc:
            return {}, [
                Finding(
                    id="ARCHITECTURE_OWNERSHIP_REGISTRY_JSON_INVALID",
                    message="Architecture ownership registry is not valid JSON.",
                    severity=Severity.ERROR,
                    path=str(self.options.ownership_registry).replace("\\", "/"),
                    metadata={"error": str(exc)},
                )
            ]

        packages = payload.get("packages")
        if not isinstance(packages, list):
            findings.append(
                Finding(
                    id="ARCHITECTURE_OWNERSHIP_REGISTRY_PACKAGES_INVALID",
                    message="Architecture ownership registry must contain a packages array.",
                    severity=Severity.BLOCK,
                    path=str(self.options.ownership_registry).replace("\\", "/"),
                )
            )
            return payload, findings

        seen: set[str] = set()
        required_fields = {"package", "domain", "owner", "criticality", "risk_level", "test_contracts"}
        for index, item in enumerate(packages):
            if not isinstance(item, dict):
                findings.append(
                    Finding(
                        id="ARCHITECTURE_OWNERSHIP_REGISTRY_ENTRY_INVALID",
                        message="Ownership registry package entry is not an object.",
                        severity=Severity.BLOCK,
                        path=f"{self.options.ownership_registry}#/packages/{index}",
                    )
                )
                continue
            package = str(item.get("package", ""))
            missing = sorted(field for field in required_fields if field not in item)
            if missing:
                findings.append(
                    Finding(
                        id="ARCHITECTURE_OWNERSHIP_REGISTRY_ENTRY_FIELD_MISSING",
                        message="Ownership registry entry is missing required fields.",
                        severity=Severity.BLOCK,
                        path=f"{self.options.ownership_registry}#/packages/{index}",
                        metadata={"package": package, "missing_fields": missing},
                    )
                )
            if package in seen:
                findings.append(
                    Finding(
                        id="ARCHITECTURE_OWNERSHIP_REGISTRY_DUPLICATE_PACKAGE",
                        message="Ownership registry has duplicate package ownership entries.",
                        severity=Severity.BLOCK,
                        path=f"{self.options.ownership_registry}#/packages/{index}",
                        metadata={"package": package},
                    )
                )
            seen.add(package)
            if not package.startswith("devpilot_core"):
                findings.append(
                    Finding(
                        id="ARCHITECTURE_OWNERSHIP_REGISTRY_PACKAGE_OUT_OF_SCOPE",
                        message="Ownership registry entry is outside devpilot_core package scope.",
                        severity=Severity.WARNING,
                        path=f"{self.options.ownership_registry}#/packages/{index}",
                        metadata={"package": package},
                    )
                )
        return payload, findings

    def _ownership_gaps(self, packages: list[dict[str, Any]], ownership_by_package: dict[str, Any]) -> list[dict[str, Any]]:
        gaps: list[dict[str, Any]] = []
        for package in sorted(packages, key=lambda item: str(item.get("package", ""))):
            package_id = str(package.get("package", ""))
            criticality = str(package.get("criticality", "P3"))
            modules_total = len(package.get("modules", []) or [])
            owner = package.get("owner")
            if package_id not in ownership_by_package or not owner or package.get("ownership_status") == "missing":
                gaps.append(
                    {
                        "package": package_id,
                        "gap_type": "missing-owner",
                        "severity": "warning",
                        "criticality": criticality,
                        "modules_total": modules_total,
                        "loc": int(package.get("loc", 0)),
                        "recommendation": "Declare owner/domain/criticality/test_contracts before using this package as a protected architecture boundary.",
                    }
                )
            entry = ownership_by_package.get(package_id)
            test_contracts = list(getattr(entry, "test_contracts", ()) if entry is not None else package.get("test_contracts", []) or [])
            if criticality in {"P0", "P1"} and not test_contracts:
                gaps.append(
                    {
                        "package": package_id,
                        "gap_type": "critical-missing-test-contracts",
                        "severity": "warning",
                        "criticality": criticality,
                        "modules_total": modules_total,
                        "loc": int(package.get("loc", 0)),
                        "recommendation": "Attach at least one Test Contract Registry contract before promoting this package boundary to production-local enforcement.",
                    }
                )
        return gaps

    def _ownership_gap_findings(self, ownership_gaps: list[dict[str, Any]]) -> list[Finding]:
        findings: list[Finding] = []
        for gap in ownership_gaps:
            gap_type = str(gap.get("gap_type", "ownership-gap"))
            finding_id = "ARCHITECTURE_OWNERSHIP_GAP" if gap_type == "missing-owner" else "ARCHITECTURE_CRITICAL_PACKAGE_TEST_CONTRACT_GAP"
            findings.append(
                Finding(
                    id=finding_id,
                    message="Architecture ownership validation found an advisory gap.",
                    severity=Severity.WARNING,
                    path=str(gap.get("package")),
                    metadata={k: v for k, v in gap.items() if k != "package"},
                )
            )
        return findings

    def _critical_contract_findings(self, packages: list[dict[str, Any]], ownership_by_package: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        for package_id in sorted(REQUIRED_CRITICAL_PACKAGES):
            entry = ownership_by_package.get(package_id)
            if entry is None:
                continue
            if not tuple(getattr(entry, "test_contracts", ())):
                findings.append(
                    Finding(
                        id="ARCHITECTURE_REQUIRED_CRITICAL_PACKAGE_CONTRACT_MISSING",
                        message="Required critical package has no test contract in the ownership registry.",
                        severity=Severity.WARNING,
                        path=package_id,
                        metadata={"required_package": True},
                    )
                )
        return findings

    def _required_package_findings(self, packages: list[dict[str, Any]], ownership_by_package: dict[str, Any]) -> list[Finding]:
        package_ids = {str(package.get("package")) for package in packages}
        findings: list[Finding] = []
        for package_id in sorted(REQUIRED_CRITICAL_PACKAGES):
            if package_id not in package_ids:
                findings.append(
                    Finding(
                        id="ARCHITECTURE_REQUIRED_PACKAGE_NOT_DISCOVERED",
                        message="Required critical package was not discovered in the architecture inventory.",
                        severity=Severity.BLOCK,
                        path=package_id,
                    )
                )
            if package_id not in ownership_by_package:
                findings.append(
                    Finding(
                        id="ARCHITECTURE_REQUIRED_PACKAGE_OWNER_MISSING",
                        message="Required critical package is missing from ownership registry.",
                        severity=Severity.BLOCK,
                        path=package_id,
                    )
                )
        return findings

    def _recommendations(
        self,
        *,
        packages: list[dict[str, Any]],
        dependencies: list[dict[str, Any]],
        hotspots: list[dict[str, Any]],
        ownership_gaps: list[dict[str, Any]],
    ) -> list[str]:
        top_hotspot = hotspots[0]["subject_id"] if hotspots else "N/A"
        forbidden = [edge for edge in dependencies if edge.get("policy") == "forbidden"]
        restricted = [edge for edge in dependencies if edge.get("policy") == "restricted"]
        unowned = [gap for gap in ownership_gaps if gap.get("gap_type") == "missing-owner"]
        return [
            f"Use {top_hotspot} as first input for POST-H-006 CLI command registry modularization.",
            "Convert forbidden/restricted dependency findings into reviewed ADR exceptions or refactor candidates before enabling blocking enforcement.",
            "Expand .devpilot/architecture/ownership_registry.json for discovered packages that remain unowned before declaring architecture boundaries production-local.",
            "Use POST-H-007 to harden ApplicationService/API/UI boundaries surfaced by the dependency graph.",
            f"Current advisory baseline: {len(forbidden)} forbidden, {len(restricted)} restricted and {len(unowned)} unowned package signals.",
        ]

    def _write_raw_reports(self, architecture_map: dict[str, Any], *, findings: list[Finding]) -> dict[str, str]:
        json_path = self._resolve_output_path(self.options.output_json)
        markdown_path = self._resolve_output_path(self.options.output_markdown)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        payload = redact_sensitive_data(architecture_map)
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        markdown_path.write_text(redact_string(self._render_markdown(payload, findings=findings)), encoding="utf-8")
        return {"json": self._rel(json_path), "markdown": self._rel(markdown_path)}

    def _resolve_output_path(self, path: Path) -> Path:
        candidate = path if path.is_absolute() else self.root / path
        candidate = candidate.resolve()
        root_resolved = self.root.resolve()
        try:
            candidate.relative_to(root_resolved)
        except ValueError as exc:
            raise ValueError(f"architecture map output path escapes project root: {path}") from exc
        return candidate

    def _render_markdown(self, architecture_map: dict[str, Any], *, findings: list[Finding]) -> str:
        summary = dict(architecture_map.get("summary", {}))
        hotspots = [dict(item) for item in architecture_map.get("hotspots", [])[:20]]
        gaps = [dict(item) for item in architecture_map.get("ownership_gaps", [])]
        dependencies = [dict(item) for item in architecture_map.get("dependencies", [])]
        forbidden = [edge for edge in dependencies if edge.get("policy") == "forbidden"]
        restricted = [edge for edge in dependencies if edge.get("policy") == "restricted"]
        lines = [
            "---",
            'doc_id: "POST-H-005-ARCHITECTURE-MAP-REPORT"',
            'title: "POST-H-005 — Executable architecture map report"',
            'status: "implemented-initial"',
            'version: "1.0.0"',
            'owner: "Ordóñez"',
            'updated: "2026-06-25"',
            'approval: "internal"',
            "---",
            "",
            "# POST-H-005 — Executable architecture map report",
            "",
            "## Propósito",
            "",
            "Reporte final local-first de `POST-H-005 — Architecture map executable / dependency ownership`. Materializa inventario AST, grafo de dependencias, ownership, hotspots y recomendaciones sin mutar código fuente.",
            "",
            "## Estado",
            "",
            "Estado: `implemented-initial`. El reporte es advisory y no habilita enforcement blocking, remote execution, connector write ni plugin execution.",
            "",
            "## Resumen",
            "",
            "| Métrica | Valor |",
            "|---|---:|",
        ]
        for key in [
            "packages_total",
            "modules_total",
            "dependencies_total",
            "hotspots_total",
            "ownership_entries_total",
            "ownership_gaps_total",
            "unowned_packages_total",
            "critical_packages_missing_test_contracts_total",
            "forbidden_dependency_findings_total",
            "restricted_dependency_findings_total",
            "sensitive_dependencies_total",
        ]:
            lines.append(f"| `{key}` | {summary.get(key, 0)} |")
        lines.extend(["", "## Top hotspots", "", "| Rank | Subject | Type | Score | Criticality | Kind |", "|---:|---|---|---:|---|---|"])
        for index, hotspot in enumerate(hotspots, start=1):
            metadata = hotspot.get("metadata", {}) if isinstance(hotspot.get("metadata"), dict) else {}
            lines.append(
                f"| {index} | `{hotspot.get('subject_id')}` | {hotspot.get('subject_type')} | {hotspot.get('score')} | {hotspot.get('criticality')} | {metadata.get('hotspot_kind', 'unknown')} |"
            )
        lines.extend(["", "## Ownership gaps", ""])
        if gaps:
            lines.extend(["| Package | Gap | Criticality | Recommendation |", "|---|---|---|---|"])
            for gap in gaps[:50]:
                recommendation = str(gap.get("recommendation", "")).replace("|", "\\|")
                lines.append(f"| `{gap.get('package')}` | {gap.get('gap_type')} | {gap.get('criticality')} | {recommendation} |")
        else:
            lines.append("No ownership gaps detected.")
        lines.extend(["", "## Dependency policy signals", "", f"Forbidden dependencies: `{len(forbidden)}`.", "", f"Restricted dependencies: `{len(restricted)}`.", ""])
        lines.extend(["## Recomendaciones", ""])
        for recommendation in architecture_map.get("recommendations", []):
            lines.append(f"- {recommendation}")
        lines.extend(["", "## Criterios PASS", "", "```text", "PASS si architecture_map.json valida contra ArchitectureMap.", "PASS si top 20 hotspots existe y cli.py/devpilot_core.cli no se omite.", "PASS si ownership gaps y dependencias prohibidas/restringidas quedan explícitos.", "PASS si no hay red, APIs externas, mutaciones, remote execution, connector write ni plugin execution.", "```", "", "## Criterios BLOCK", "", "```text", "BLOCK si el schema falla.", "BLOCK si faltan paquetes críticos requeridos o ownership de paquetes críticos iniciales.", "BLOCK si el reporte muta fuentes o habilita enforcement/runtime sensible.", "```", "", "## Riesgos", "", "- El reporte es baseline `implemented-initial`; las decisiones de refactor requieren revisión humana y ADR/patch posterior.", "- Los ownership gaps son warnings explícitos para endurecimiento posterior; no son enforcement automático.", "- El score de hotspots es heurístico y debe complementarse con complejidad/cobertura en sprints futuros.", ""])
        return "\n".join(lines)

    def _rel(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return str(path).replace("\\", "/")
