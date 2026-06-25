from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.architecture.dependencies import ArchitectureDependenciesBuilder, ArchitectureDependenciesOptions
from devpilot_core.architecture.models import Hotspot
from devpilot_core.architecture.ownership import DEFAULT_OWNERSHIP_REGISTRY
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas import SchemaValidator

DEFAULT_SOURCE_ROOT = Path("src/devpilot_core")
POST_H_005_D_REPORT_ID = "architecture-hotspots-post-h-005-d"
DEFAULT_TOP_LIMIT = 20
CRITICALITY_WEIGHTS = {"P0": 10.0, "P1": 6.0, "P2": 3.0, "P3": 1.0}
CORE_DOMAIN_PREFIXES = ("governance", "application", "agent", "quality", "testing")


@dataclass(frozen=True)
class ArchitectureHotspotsOptions:
    """Options for the local read-only POST-H-005-D hotspot analyzer."""

    source_root: Path = DEFAULT_SOURCE_ROOT
    tests_root: Path = Path("tests")
    ownership_registry: Path = DEFAULT_OWNERSHIP_REGISTRY
    top_limit: int = DEFAULT_TOP_LIMIT


@dataclass(frozen=True)
class _HotspotCandidate:
    subject_id: str
    subject_type: str
    score: float
    criticality: str
    reasons: tuple[str, ...]
    recommendations: tuple[str, ...]
    metadata: dict[str, Any]

    def to_hotspot(self) -> Hotspot:
        return Hotspot(
            subject_id=self.subject_id,
            subject_type=self.subject_type,
            score=round(self.score, 2),
            criticality=self.criticality,
            reasons=self.reasons,
            recommendations=self.recommendations,
            metadata=self.metadata,
        )


class ArchitectureHotspotsBuilder:
    """Rank executable architecture hotspots from inventory and dependency metrics.

    POST-H-005-D is observational only. It reuses the POST-H-005-C dependency
    graph, derives scores from existing local AST/import evidence and returns an
    ArchitectureMap payload enriched with the top hotspots. It never imports
    analyzed project modules dynamically, never executes tests and never mutates
    source files.
    """

    def __init__(self, root: Path, options: ArchitectureHotspotsOptions | None = None) -> None:
        self.root = Path(root)
        self.options = options or ArchitectureHotspotsOptions()

    def build(self) -> CommandResult:
        top_limit = max(1, int(self.options.top_limit or DEFAULT_TOP_LIMIT))
        dependencies_result = ArchitectureDependenciesBuilder(
            self.root,
            ArchitectureDependenciesOptions(
                source_root=self.options.source_root,
                tests_root=self.options.tests_root,
                ownership_registry=self.options.ownership_registry,
            ),
        ).build()
        if not dependencies_result.ok:
            return CommandResult(
                command="architecture hotspots",
                ok=False,
                exit_code=dependencies_result.exit_code,
                message="Architecture hotspots blocked because dependency graph failed.",
                data=dependencies_result.data,
                findings=dependencies_result.findings,
            )

        architecture_map = dict((dependencies_result.data or {}).get("architecture_map", {}))
        packages = [dict(item) for item in architecture_map.get("packages", []) if isinstance(item, dict)]
        modules = [dict(item) for item in architecture_map.get("modules", []) if isinstance(item, dict)]
        dependencies = [dict(item) for item in architecture_map.get("dependencies", []) if isinstance(item, dict)]

        module_fan_in, module_fan_out = self._module_fan_metrics(dependencies)
        package_policy_counts = self._package_policy_counts(dependencies)
        candidates = self._build_candidates(
            packages=packages,
            modules=modules,
            module_fan_in=module_fan_in,
            module_fan_out=module_fan_out,
            package_policy_counts=package_policy_counts,
        )
        candidates = sorted(candidates, key=lambda item: (-item.score, item.subject_type, item.subject_id))[:top_limit]
        hotspots = [candidate.to_hotspot().to_dict() for candidate in candidates]
        hotspots_by_package = self._hotspots_by_package(hotspots)
        packages = self._updated_packages(packages, hotspots_by_package)
        payload = self._architecture_payload(
            architecture_map=architecture_map,
            packages=packages,
            hotspots=hotspots,
            top_limit=top_limit,
        )

        schema_validation = SchemaValidator(self.root).validate_payload(
            schema="ArchitectureMap",
            payload=payload,
            instance_label="in-memory:architecture-map-hotspots",
        )
        findings = list(dependencies_result.findings)
        if not schema_validation.ok:
            findings.extend(schema_validation.findings)

        hotspot_findings = self._hotspot_findings(hotspots)
        findings.extend(hotspot_findings)
        warnings_total = sum(1 for finding in findings if finding.severity == Severity.WARNING)
        blocking_findings_total = sum(1 for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL})
        technical_hotspots_total = sum(1 for hotspot in hotspots if hotspot.get("metadata", {}).get("technical_hotspot") is True)
        core_domain_hotspots_total = sum(1 for hotspot in hotspots if hotspot.get("metadata", {}).get("core_domain_hotspot") is True)
        module_hotspots_total = sum(1 for hotspot in hotspots if hotspot.get("subject_type") == "module")
        package_hotspots_total = sum(1 for hotspot in hotspots if hotspot.get("subject_type") == "package")

        summary = {
            **payload["summary"],
            "top_hotspots_limit": top_limit,
            "technical_hotspots_total": technical_hotspots_total,
            "core_domain_hotspots_total": core_domain_hotspots_total,
            "module_hotspots_total": module_hotspots_total,
            "package_hotspots_total": package_hotspots_total,
            "score_formula": "LOC + fan-in + fan-out + functions + CLI commands + criticality, normalized per subject type with advisory policy metadata.",
            "warnings_total": warnings_total,
            "blocking_findings_total": blocking_findings_total,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
        data = {
            "summary": summary,
            "architecture_map": payload,
            "hotspots": hotspots,
            "schema_validation": (schema_validation.data or {}).get("summary", {}),
            "score_formula": {
                "loc_weight": 35,
                "fan_in_weight": 15,
                "fan_out_weight": 15,
                "functions_weight": 15,
                "cli_commands_weight": 10,
                "criticality_weight": 10,
                "normalization": "Per subject type, each raw metric is divided by the observed max for that metric.",
            },
            "notes": [
                "POST-H-005-D ranks hotspots using AST inventory and package dependency graph evidence only.",
                "Hotspots are advisory prioritization signals; refactoring and quality-gate enforcement are deferred to POST-H-006/007 and POST-H-005-E.",
                "Technical hotspots and core-domain hotspots are separated in metadata so platform debt is not confused with strategic domain criticality.",
            ],
            "tests_executed": False,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
        ok = blocking_findings_total == 0 and schema_validation.ok and bool(hotspots)
        if ok:
            findings.append(
                Finding(
                    id="ARCHITECTURE_HOTSPOTS_PASS",
                    message="Architecture hotspot analyzer completed without blocking findings.",
                    severity=Severity.INFO,
                    metadata={
                        "hotspots_total": len(hotspots),
                        "top_hotspots_limit": top_limit,
                        "technical_hotspots_total": technical_hotspots_total,
                        "core_domain_hotspots_total": core_domain_hotspots_total,
                    },
                )
            )
        return CommandResult(
            command="architecture hotspots",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Architecture hotspot analyzer passed." if ok else "Architecture hotspot analyzer failed with blocking findings.",
            data=data,
            findings=findings,
        )

    def _build_candidates(
        self,
        *,
        packages: list[dict[str, Any]],
        modules: list[dict[str, Any]],
        module_fan_in: Counter[str],
        module_fan_out: Counter[str],
        package_policy_counts: dict[str, Counter[str]],
    ) -> list[_HotspotCandidate]:
        package_by_id = {str(package.get("package")): package for package in packages}
        package_module_sums = self._package_module_sums(modules)
        package_metrics = [
            self._package_metrics(
                package,
                package_policy_counts.get(str(package.get("package") or ""), Counter()),
                package_module_sums.get(str(package.get("package") or ""), {}),
            )
            for package in packages
        ]
        module_metrics = [self._module_metrics(module, package_by_id, module_fan_in, module_fan_out) for module in modules]
        scored_packages = self._score_metrics(package_metrics, subject_type="package")
        scored_modules = self._score_metrics(module_metrics, subject_type="module")
        return [*scored_packages, *scored_modules]

    def _package_metrics(self, package: dict[str, Any], policy_counts: Counter[str], module_sums: dict[str, int]) -> dict[str, Any]:
        metadata = dict(package.get("metadata") or {})
        return {
            "subject_id": str(package.get("package")),
            "subject_type": "package",
            "package": str(package.get("package")),
            "path": None,
            "domain": str(package.get("domain") or "architecture.unknown"),
            "owner": package.get("owner"),
            "criticality": str(package.get("criticality") or "P3"),
            "risk_level": str(package.get("risk_level") or "low"),
            "loc": int(package.get("loc") or 0),
            "functions": int(module_sums.get("functions_total", 0)),
            "classes": int(module_sums.get("classes_total", 0)),
            "imports": int(module_sums.get("imports_total", 0)),
            "fan_in": int(package.get("fan_in") or 0),
            "fan_out": int(package.get("fan_out") or 0),
            "cli_commands": int(metadata.get("cli_commands_total") or 0),
            "cli_handlers": int(metadata.get("cli_handlers_total") or 0),
            "modules_total": int(metadata.get("modules_total") or len(package.get("modules") or [])),
            "forbidden_edges": int(policy_counts.get("forbidden", 0)),
            "restricted_edges": int(policy_counts.get("restricted", 0)),
            "sensitive_edges": int(policy_counts.get("sensitive", 0)),
            "declared_owner": bool(package.get("owner")),
            "related_tests_total": int(metadata.get("related_tests_total") or 0),
        }

    def _module_metrics(
        self,
        module: dict[str, Any],
        package_by_id: dict[str, dict[str, Any]],
        module_fan_in: Counter[str],
        module_fan_out: Counter[str],
    ) -> dict[str, Any]:
        metadata = dict(module.get("metadata") or {})
        package_id = str(module.get("package"))
        package = package_by_id.get(package_id, {})
        return {
            "subject_id": str(module.get("module_id")),
            "subject_type": "module",
            "package": package_id,
            "path": str(module.get("path") or ""),
            "domain": str(package.get("domain") or "architecture.unknown"),
            "owner": package.get("owner"),
            "criticality": str(package.get("criticality") or "P3"),
            "risk_level": str(package.get("risk_level") or "low"),
            "loc": int(module.get("loc") or 0),
            "functions": int(module.get("functions_total") or 0),
            "classes": int(module.get("classes_total") or 0),
            "imports": int(module.get("imports_total") or 0),
            "fan_in": int(module_fan_in.get(str(module.get("module_id")), 0)),
            "fan_out": int(module_fan_out.get(str(module.get("module_id")), 0)),
            "cli_commands": int(metadata.get("cli_commands_total") or len(metadata.get("cli_commands") or [])),
            "cli_handlers": int(metadata.get("cli_handlers_total") or len(metadata.get("cli_handlers") or [])),
            "modules_total": 1,
            "forbidden_edges": 0,
            "restricted_edges": 0,
            "sensitive_edges": 0,
            "declared_owner": bool(package.get("owner")),
            "related_tests_total": int(metadata.get("related_tests_total") or len(metadata.get("related_tests") or [])),
        }

    def _score_metrics(self, metrics: list[dict[str, Any]], *, subject_type: str) -> list[_HotspotCandidate]:
        if not metrics:
            return []
        max_loc = max(max(item["loc"] for item in metrics), 1)
        max_fan_in = max(max(item["fan_in"] for item in metrics), 1)
        max_fan_out = max(max(item["fan_out"] for item in metrics), 1)
        max_functions = max(max(item["functions"] for item in metrics), 1)
        max_commands = max(max(item["cli_commands"] for item in metrics), 1)
        scored: list[_HotspotCandidate] = []
        for item in metrics:
            score_parts = {
                "loc": self._ratio(item["loc"], max_loc) * 35.0,
                "fan_in": self._ratio(item["fan_in"], max_fan_in) * 15.0,
                "fan_out": self._ratio(item["fan_out"], max_fan_out) * 15.0,
                "functions": self._ratio(item["functions"], max_functions) * 15.0,
                "cli_commands": self._ratio(item["cli_commands"], max_commands) * 10.0,
                "criticality": CRITICALITY_WEIGHTS.get(item["criticality"], 1.0),
            }
            policy_signal = min((item["forbidden_edges"] * 3.0) + (item["restricted_edges"] * 1.0) + (item["sensitive_edges"] * 1.0), 8.0)
            score = sum(score_parts.values()) + policy_signal
            technical = self._is_technical_hotspot(item, score_parts)
            core_domain = self._is_core_domain_hotspot(item)
            if not technical and not core_domain and score < 8.0:
                continue
            reasons = self._reasons(item, score_parts, technical, core_domain)
            recommendations = self._recommendations(item, technical, core_domain)
            metadata = {
                "package": item["package"],
                "path": item["path"],
                "domain": item["domain"],
                "owner": item["owner"],
                "risk_level": item["risk_level"],
                "technical_hotspot": technical,
                "core_domain_hotspot": core_domain,
                "hotspot_kind": self._hotspot_kind(technical, core_domain),
                "score_parts": {key: round(value, 2) for key, value in score_parts.items()},
                "policy_signal": round(policy_signal, 2),
                "raw_metrics": {
                    "loc": item["loc"],
                    "fan_in": item["fan_in"],
                    "fan_out": item["fan_out"],
                    "functions": item["functions"],
                    "classes": item["classes"],
                    "imports": item["imports"],
                    "cli_commands": item["cli_commands"],
                    "cli_handlers": item["cli_handlers"],
                    "modules_total": item["modules_total"],
                    "related_tests_total": item["related_tests_total"],
                    "forbidden_edges": item["forbidden_edges"],
                    "restricted_edges": item["restricted_edges"],
                    "sensitive_edges": item["sensitive_edges"],
                },
                "formula_version": "POST-H-005-D-v1",
                "advisory": True,
            }
            scored.append(
                _HotspotCandidate(
                    subject_id=item["subject_id"],
                    subject_type=subject_type,
                    score=score,
                    criticality=item["criticality"],
                    reasons=tuple(reasons),
                    recommendations=tuple(recommendations),
                    metadata=metadata,
                )
            )
        return scored


    def _package_module_sums(self, modules: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
        sums: dict[str, dict[str, int]] = defaultdict(lambda: {"functions_total": 0, "classes_total": 0, "imports_total": 0})
        for module in modules:
            package = str(module.get("package") or "")
            if not package:
                continue
            sums[package]["functions_total"] += int(module.get("functions_total") or 0)
            sums[package]["classes_total"] += int(module.get("classes_total") or 0)
            sums[package]["imports_total"] += int(module.get("imports_total") or 0)
        return dict(sums)

    def _module_fan_metrics(self, dependencies: list[dict[str, Any]]) -> tuple[Counter[str], Counter[str]]:
        fan_in: Counter[str] = Counter()
        fan_out: Counter[str] = Counter()
        for edge in dependencies:
            metadata = dict(edge.get("metadata") or {})
            source_modules = [str(item) for item in metadata.get("source_modules", []) if item]
            target_modules = [str(item) for item in metadata.get("target_modules", []) if item]
            for source_module in source_modules:
                fan_out[source_module] += len(set(target_modules)) or 1
            for target_module in target_modules:
                fan_in[target_module] += len(set(source_modules)) or 1
        return fan_in, fan_out

    def _package_policy_counts(self, dependencies: list[dict[str, Any]]) -> dict[str, Counter[str]]:
        counts: dict[str, Counter[str]] = defaultdict(Counter)
        for edge in dependencies:
            source = str(edge.get("source"))
            target = str(edge.get("target"))
            policy = str(edge.get("policy") or "unknown")
            if policy in {"forbidden", "restricted"}:
                counts[source][policy] += 1
            if edge.get("sensitive") is True:
                counts[source]["sensitive"] += 1
                counts[target]["sensitive"] += 1
        return counts

    def _updated_packages(self, packages: list[dict[str, Any]], hotspots_by_package: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        updated: list[dict[str, Any]] = []
        for package in packages:
            item = dict(package)
            package_id = str(item.get("package"))
            package_hotspots = hotspots_by_package.get(package_id, [])
            metadata = dict(item.get("metadata") or {})
            metadata.update(
                {
                    "hotspot_score_materialized": True,
                    "hotspots_total": len(package_hotspots),
                    "top_hotspot_score": round(max((float(hotspot.get("score", 0.0)) for hotspot in package_hotspots), default=0.0), 2),
                    "top_hotspots": [
                        {
                            "subject_id": hotspot.get("subject_id"),
                            "subject_type": hotspot.get("subject_type"),
                            "score": hotspot.get("score"),
                            "hotspot_kind": hotspot.get("metadata", {}).get("hotspot_kind"),
                        }
                        for hotspot in package_hotspots[:5]
                    ],
                }
            )
            item["metadata"] = metadata
            updated.append(item)
        return sorted(updated, key=lambda item: str(item.get("package")))

    def _architecture_payload(
        self,
        *,
        architecture_map: dict[str, Any],
        packages: list[dict[str, Any]],
        hotspots: list[dict[str, Any]],
        top_limit: int,
    ) -> dict[str, Any]:
        payload = dict(architecture_map)
        summary = dict(payload.get("summary") or {})
        summary.update(
            {
                "packages_total": len(packages),
                "modules_total": len(payload.get("modules", [])),
                "dependencies_total": len(payload.get("dependencies", [])),
                "hotspots_total": len(hotspots),
                "top_hotspots_limit": top_limit,
            }
        )
        source_paths = dict(payload.get("source_paths") or {})
        source_paths.update(
            {
                "hotspot_analyzer": "in-memory:architecture-hotspots",
                "hotspot_source": "POST-H-005-C dependency graph + POST-H-005-B AST inventory",
            }
        )
        payload.update(
            {
                "map_id": POST_H_005_D_REPORT_ID,
                "created_by": "POST-H-005-D",
                "status": "implemented-initial",
                "source_paths": source_paths,
                "summary": summary,
                "packages": packages,
                "hotspots": hotspots,
                "recommendations": [
                    "Use the top CLI/module hotspots as direct input for POST-H-006 CLI command registry and handler extraction planning.",
                    "Treat P0/P1 core-domain hotspots as protected domains: add/confirm test contracts before any refactor.",
                    "Keep hotspot scores advisory until POST-H-005-E defines ownership validation and report-level governance.",
                ],
            }
        )
        return payload

    def _hotspots_by_package(self, hotspots: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for hotspot in hotspots:
            package = str(hotspot.get("metadata", {}).get("package") or "")
            if package:
                grouped[package].append(hotspot)
        for package in grouped:
            grouped[package].sort(key=lambda item: -float(item.get("score", 0.0)))
        return grouped

    def _hotspot_findings(self, hotspots: list[dict[str, Any]]) -> list[Finding]:
        findings: list[Finding] = []
        for rank, hotspot in enumerate(hotspots, start=1):
            metadata = dict(hotspot.get("metadata") or {})
            if rank <= 5:
                severity = Severity.WARNING
                finding_id = "ARCHITECTURE_HOTSPOT_TOP5"
            else:
                severity = Severity.INFO
                finding_id = "ARCHITECTURE_HOTSPOT_DETECTED"
            findings.append(
                Finding(
                    id=finding_id,
                    message="Architecture hotspot detected for prioritization; advisory only.",
                    severity=severity,
                    path=str(hotspot.get("metadata", {}).get("path") or hotspot.get("subject_id")),
                    metadata={
                        "rank": rank,
                        "subject_id": hotspot.get("subject_id"),
                        "subject_type": hotspot.get("subject_type"),
                        "score": hotspot.get("score"),
                        "hotspot_kind": metadata.get("hotspot_kind"),
                        "sprint": "POST-H-005-D",
                        "enforcement": "advisory",
                    },
                )
            )
        return findings

    def _is_technical_hotspot(self, item: dict[str, Any], score_parts: dict[str, float]) -> bool:
        return (
            item["subject_id"] == "devpilot_core.cli"
            or item["path"] == "src/devpilot_core/cli.py"
            or item["cli_commands"] > 0
            or score_parts["loc"] >= 20.0
            or score_parts["functions"] >= 8.0
            or score_parts["fan_out"] >= 8.0
            or item["forbidden_edges"] > 0
            or item["restricted_edges"] > 0
        )

    def _is_core_domain_hotspot(self, item: dict[str, Any]) -> bool:
        domain = str(item.get("domain") or "")
        return item.get("criticality") in {"P0", "P1"} and any(domain.startswith(prefix) for prefix in CORE_DOMAIN_PREFIXES)

    def _hotspot_kind(self, technical: bool, core_domain: bool) -> str:
        if technical and core_domain:
            return "technical-and-core-domain"
        if core_domain:
            return "core-domain"
        return "technical"

    def _reasons(self, item: dict[str, Any], score_parts: dict[str, float], technical: bool, core_domain: bool) -> list[str]:
        reasons: list[str] = []
        if item["subject_id"] == "devpilot_core.cli" or item["path"] == "src/devpilot_core/cli.py":
            reasons.append("Known monolithic CLI hotspot; command registry extraction is planned in POST-H-006.")
        if item["loc"] > 0:
            reasons.append(f"LOC={item['loc']} contributes to maintenance and review surface.")
        if item["functions"] > 0:
            reasons.append(f"functions_total={item['functions']} contributes to behavioral density.")
        if item["fan_in"] > 0 or item["fan_out"] > 0:
            reasons.append(f"fan_in={item['fan_in']} and fan_out={item['fan_out']} indicate coupling pressure.")
        if item["cli_commands"] > 0:
            reasons.append(f"cli_commands_total={item['cli_commands']} adds command ownership pressure.")
        if item["forbidden_edges"] or item["restricted_edges"] or item["sensitive_edges"]:
            reasons.append(
                f"boundary_signals forbidden={item['forbidden_edges']}, restricted={item['restricted_edges']}, sensitive={item['sensitive_edges']} require review."
            )
        if core_domain:
            reasons.append(f"criticality={item['criticality']} and domain={item['domain']} mark this as a core-domain hotspot.")
        if technical and not core_domain:
            reasons.append("Classified as technical hotspot rather than strategic domain hotspot.")
        return reasons[:8]

    def _recommendations(self, item: dict[str, Any], technical: bool, core_domain: bool) -> list[str]:
        recommendations: list[str] = []
        if item["subject_id"] == "devpilot_core.cli" or item["path"] == "src/devpilot_core/cli.py":
            recommendations.append("Use POST-H-006 to extract a CLI command registry and move handlers behind stable command descriptors.")
        if item["fan_out"] >= 5:
            recommendations.append("Review fan-out before adding new dependencies; prefer ApplicationService or explicit boundary adapters.")
        if item["fan_in"] >= 5:
            recommendations.append("Protect inbound contract with focused tests before refactor; downstream packages depend on this subject.")
        if item["functions"] >= 20:
            recommendations.append("Split cohesive responsibilities only after tests identify stable behavior seams.")
        if item["forbidden_edges"] or item["restricted_edges"] or item["sensitive_edges"]:
            recommendations.append("Document boundary exception or plan dependency inversion before promoting findings to blockers.")
        if core_domain:
            recommendations.append("Treat as core-domain: require owner confirmation and test-contract coverage before structural change.")
        if technical and not recommendations:
            recommendations.append("Track as technical-debt candidate and revisit during modularization planning.")
        return recommendations[:6]

    def _ratio(self, value: int | float, maximum: int | float) -> float:
        return float(value) / float(maximum or 1)
