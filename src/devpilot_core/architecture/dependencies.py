from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from devpilot_core.architecture.inventory import ArchitectureInventoryBuilder, ArchitectureInventoryOptions, EXCLUDED_DIR_NAMES
from devpilot_core.architecture.models import DependencyEdge, DependencyKind, DependencyPolicy
from devpilot_core.architecture.ownership import DEFAULT_OWNERSHIP_REGISTRY, load_ownership_registry, ownership_entries_from_payload
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas import SchemaValidator

DEFAULT_SOURCE_ROOT = Path("src/devpilot_core")
POST_H_005_C_REPORT_ID = "architecture-dependencies-post-h-005-c"
SENSITIVE_PACKAGES = {"devpilot_core.remote", "devpilot_core.plugins", "devpilot_core.connectors"}


@dataclass(frozen=True)
class ArchitectureDependenciesOptions:
    """Options for the local read-only POST-H-005-C dependency graph."""

    source_root: Path = DEFAULT_SOURCE_ROOT
    tests_root: Path = Path("tests")
    ownership_registry: Path = DEFAULT_OWNERSHIP_REGISTRY


@dataclass(frozen=True)
class _ImportOccurrence:
    import_name: str
    import_type: str
    lineno: int | None


@dataclass(frozen=True)
class _ResolvedEdge:
    source_module: str
    target_module: str
    source_package: str
    target_package: str
    import_name: str
    import_type: str
    lineno: int | None


class ArchitectureDependenciesBuilder:
    """Materialize governed package dependency edges from Python AST imports.

    POST-H-005-C deliberately remains observational. It parses sources with the
    standard-library ``ast`` module, creates package-level ``DependencyEdge``
    records, calculates fan-in/fan-out, and classifies boundary policy signals.
    It never imports project modules dynamically, never executes tests and never
    mutates source files.
    """

    def __init__(self, root: Path, options: ArchitectureDependenciesOptions | None = None) -> None:
        self.root = Path(root)
        self.options = options or ArchitectureDependenciesOptions()

    def build(self) -> CommandResult:
        source_root = self._resolve_inside_root(self.options.source_root)
        findings: list[Finding] = []
        if not source_root.exists() or not source_root.is_dir():
            return CommandResult(
                command="architecture dependencies",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Architecture dependencies source root is missing.",
                data={"summary": self._empty_summary(source_root)},
                findings=[
                    Finding(
                        id="ARCHITECTURE_DEPENDENCIES_SOURCE_ROOT_MISSING",
                        message="Source root for architecture dependencies does not exist.",
                        severity=Severity.BLOCK,
                        path=str(self.options.source_root).replace("\\", "/"),
                    )
                ],
            )

        inventory_result = ArchitectureInventoryBuilder(
            self.root,
            ArchitectureInventoryOptions(
                source_root=self.options.source_root,
                tests_root=self.options.tests_root,
                ownership_registry=self.options.ownership_registry,
            ),
        ).build()
        if not inventory_result.ok:
            return CommandResult(
                command="architecture dependencies",
                ok=False,
                exit_code=inventory_result.exit_code,
                message="Architecture dependencies blocked because AST inventory failed.",
                data=inventory_result.data,
                findings=inventory_result.findings,
            )

        inventory_map = dict((inventory_result.data or {}).get("architecture_map", {}))
        module_path_by_id = self._module_path_by_id(inventory_map)
        module_ids = set(module_path_by_id)
        package_by_module = {module_id: self._package_id(module_id) for module_id in module_ids}
        ownership_payload = load_ownership_registry(self.root, self.options.ownership_registry)
        ownership_by_package = {entry.package: entry for entry in ownership_entries_from_payload(ownership_payload)}

        resolved_edges: list[_ResolvedEdge] = []
        parse_errors = 0
        for module_id, rel_path in sorted(module_path_by_id.items()):
            path = self.root / rel_path
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel_path)
            except SyntaxError as exc:
                parse_errors += 1
                findings.append(
                    Finding(
                        id="ARCHITECTURE_DEPENDENCIES_AST_PARSE_ERROR",
                        message="Python source file could not be parsed by ast for dependency graph.",
                        severity=Severity.WARNING,
                        path=rel_path,
                        metadata={"lineno": exc.lineno, "offset": exc.offset, "message": exc.msg},
                    )
                )
                continue
            for occurrence in self._imports(tree):
                target_module = self._resolve_import_target(occurrence.import_name, module_id, module_ids, path.name == "__init__.py")
                if target_module is None or target_module == module_id:
                    continue
                source_package = package_by_module[module_id]
                target_package = package_by_module.get(target_module, self._package_id(target_module))
                if source_package == target_package:
                    continue
                resolved_edges.append(
                    _ResolvedEdge(
                        source_module=module_id,
                        target_module=target_module,
                        source_package=source_package,
                        target_package=target_package,
                        import_name=occurrence.import_name,
                        import_type=occurrence.import_type,
                        lineno=occurrence.lineno,
                    )
                )

        package_edges = self._package_edges(resolved_edges, ownership_by_package)
        package_edges_dict = [edge.to_dict() for edge in package_edges]
        packages = self._updated_packages(inventory_map.get("packages", []), package_edges_dict)
        payload = self._architecture_payload(
            inventory_map=inventory_map,
            packages=packages,
            dependencies=package_edges_dict,
            parse_errors=parse_errors,
        )
        schema_validation = SchemaValidator(self.root).validate_payload(
            schema="ArchitectureMap",
            payload=payload,
            instance_label="in-memory:architecture-map-dependencies",
        )
        if not schema_validation.ok:
            findings.extend(schema_validation.findings)

        boundary_findings = self._boundary_findings(package_edges_dict)
        findings.extend(boundary_findings)
        warnings_total = sum(1 for finding in findings if finding.severity == Severity.WARNING)
        blocking_findings_total = sum(1 for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL})
        forbidden_dependency_findings_total = sum(1 for edge in package_edges_dict if edge.get("policy") == DependencyPolicy.FORBIDDEN.value)
        restricted_dependency_findings_total = sum(1 for edge in package_edges_dict if edge.get("policy") == DependencyPolicy.RESTRICTED.value)
        sensitive_dependencies_total = sum(1 for edge in package_edges_dict if edge.get("sensitive") is True)
        fan_in_total = sum(int(package.get("fan_in", 0)) for package in packages)
        fan_out_total = sum(int(package.get("fan_out", 0)) for package in packages)

        summary = {
            **payload["summary"],
            "source_root": self._rel(source_root),
            "python_files_total": len(module_ids),
            "module_edges_total": len(resolved_edges),
            "package_edges_total": len(package_edges_dict),
            "parse_errors_total": parse_errors,
            "forbidden_dependency_findings_total": forbidden_dependency_findings_total,
            "restricted_dependency_findings_total": restricted_dependency_findings_total,
            "sensitive_dependencies_total": sensitive_dependencies_total,
            "fan_in_total": fan_in_total,
            "fan_out_total": fan_out_total,
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
            "dependencies": package_edges_dict,
            "boundary_findings": [finding.to_dict() for finding in boundary_findings],
            "schema_validation": (schema_validation.data or {}).get("summary", {}),
            "notes": [
                "POST-H-005-C materializes package-level dependency edges from Python AST imports only.",
                "Boundary findings are advisory warnings in this sprint; aggressive blocking/enforcement is deferred to POST-H-005-E or later gates.",
                "The graph is local-first, read-only and non-mutating by default.",
            ],
            "tests_executed": False,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
        ok = blocking_findings_total == 0 and schema_validation.ok
        if ok:
            findings.append(
                Finding(
                    id="ARCHITECTURE_DEPENDENCIES_PASS",
                    message="Architecture dependency graph completed without blocking findings.",
                    severity=Severity.INFO,
                    metadata={
                        "package_edges_total": len(package_edges_dict),
                        "forbidden_dependency_findings_total": forbidden_dependency_findings_total,
                        "restricted_dependency_findings_total": restricted_dependency_findings_total,
                        "sensitive_dependencies_total": sensitive_dependencies_total,
                    },
                )
            )
        return CommandResult(
            command="architecture dependencies",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Architecture dependency graph passed." if ok else "Architecture dependency graph failed with blocking findings.",
            data=data,
            findings=findings,
        )

    def _resolve_inside_root(self, path: Path) -> Path:
        candidate = (self.root / path).resolve()
        root_resolved = self.root.resolve()
        try:
            candidate.relative_to(root_resolved)
        except ValueError as exc:
            raise ValueError(f"architecture dependencies path escapes project root: {path}") from exc
        return candidate

    def _module_path_by_id(self, inventory_map: dict[str, Any]) -> dict[str, str]:
        return {
            str(module["module_id"]): str(module["path"])
            for module in inventory_map.get("modules", [])
            if isinstance(module, dict) and module.get("module_id") and module.get("path")
        }

    def _imports(self, tree: ast.AST) -> tuple[_ImportOccurrence, ...]:
        occurrences: list[_ImportOccurrence] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    occurrences.append(_ImportOccurrence(alias.name, "import", node.lineno))
            elif isinstance(node, ast.ImportFrom):
                module = "." * int(node.level or 0) + (node.module or "")
                for alias in node.names:
                    if alias.name == "*":
                        occurrences.append(_ImportOccurrence(module, "from", node.lineno))
                    else:
                        occurrences.append(_ImportOccurrence(f"{module}:{alias.name}", "from", node.lineno))
        return tuple(occurrences)

    def _resolve_import_target(self, import_name: str, source_module: str, module_ids: set[str], source_is_package: bool) -> str | None:
        module_part, _, imported_name = import_name.partition(":")
        candidates: list[str] = []
        if module_part.startswith("."):
            base_module = self._resolve_relative_module(module_part, source_module, source_is_package)
            if base_module is None:
                return None
            if imported_name:
                candidates.append(f"{base_module}.{imported_name}")
            candidates.append(base_module)
        else:
            if imported_name:
                candidates.append(f"{module_part}.{imported_name}")
            candidates.append(module_part)
        return self._best_existing_module(candidates, module_ids)

    def _resolve_relative_module(self, module_part: str, source_module: str, source_is_package: bool) -> str | None:
        level = len(module_part) - len(module_part.lstrip("."))
        suffix = module_part[level:].strip(".")
        base_parts = source_module.split(".") if source_is_package else source_module.split(".")[:-1]
        if level > 1:
            remove = level - 1
            if remove >= len(base_parts):
                return None
            base_parts = base_parts[:-remove]
        if suffix:
            base_parts = [*base_parts, *suffix.split(".")]
        return ".".join(part for part in base_parts if part)

    def _best_existing_module(self, candidates: Iterable[str], module_ids: set[str]) -> str | None:
        expanded: list[str] = []
        for candidate in candidates:
            if not candidate or not candidate.startswith("devpilot_core"):
                continue
            expanded.append(candidate)
            parts = candidate.split(".")
            for index in range(len(parts) - 1, 1, -1):
                expanded.append(".".join(parts[:index]))
        for candidate in expanded:
            if candidate in module_ids:
                return candidate
        return None

    def _package_edges(
        self,
        resolved_edges: list[_ResolvedEdge],
        ownership_by_package: dict[str, Any],
    ) -> list[DependencyEdge]:
        grouped: dict[tuple[str, str], list[_ResolvedEdge]] = defaultdict(list)
        for edge in resolved_edges:
            grouped[(edge.source_package, edge.target_package)].append(edge)
        dependency_edges: list[DependencyEdge] = []
        for (source_package, target_package), edges in sorted(grouped.items()):
            policy, reason = self._classify_policy(source_package, target_package, ownership_by_package)
            sensitive = self._is_sensitive_dependency(source_package, target_package)
            if sensitive and policy == DependencyPolicy.UNKNOWN:
                policy = DependencyPolicy.RESTRICTED
                reason = "Dependency touches remote/plugins/connectors and is sensitive until explicitly justified."
            dependency_edges.append(
                DependencyEdge(
                    source=source_package,
                    target=target_package,
                    kind=DependencyKind.INTERNAL_IMPORT,
                    policy=policy,
                    sensitive=sensitive,
                    reason=reason,
                    metadata={
                        "imports_total": len(edges),
                        "source_modules": sorted({edge.source_module for edge in edges})[:50],
                        "target_modules": sorted({edge.target_module for edge in edges})[:50],
                        "sample_imports": [
                            {
                                "source_module": edge.source_module,
                                "target_module": edge.target_module,
                                "import_name": edge.import_name,
                                "import_type": edge.import_type,
                                "lineno": edge.lineno,
                            }
                            for edge in sorted(edges, key=lambda item: (item.source_module, item.target_module, item.import_name, item.lineno or 0))[:10]
                        ],
                        "boundary_checked": True,
                    },
                )
            )
        return dependency_edges

    def _classify_policy(self, source_package: str, target_package: str, ownership_by_package: dict[str, Any]) -> tuple[DependencyPolicy, str | None]:
        owner = self._resolve_owner(source_package, ownership_by_package)
        if owner:
            if self._matches_any(target_package, owner.forbidden_dependencies):
                return DependencyPolicy.FORBIDDEN, "Target matches source ownership forbidden_dependencies."
            if self._matches_any(target_package, owner.restricted_dependencies):
                return DependencyPolicy.RESTRICTED, "Target matches source ownership restricted_dependencies."
            if self._matches_any(target_package, owner.allowed_dependencies):
                return DependencyPolicy.ALLOW, "Target matches source ownership allowed_dependencies."
        if source_package == "devpilot_core.interfaces":
            if target_package in {"devpilot_core.application", "devpilot_core.cli_models", "devpilot_core.interfaces"}:
                return DependencyPolicy.ALLOW, "API/interface layer depends on allowed application/interface contracts."
            return DependencyPolicy.RESTRICTED, "API/interface layer should prefer ApplicationService over deep core modules."
        if target_package == "devpilot_core.interfaces" and source_package not in {"devpilot_core.interfaces"}:
            return DependencyPolicy.FORBIDDEN, "Core/local packages should not depend on interface/API modules."
        if source_package == "devpilot_core.policy" and target_package in {"devpilot_core.remote", "devpilot_core.interfaces"}:
            return DependencyPolicy.FORBIDDEN, "Policy layer must not depend on remote or interface layers."
        return DependencyPolicy.UNKNOWN, "No explicit ownership/boundary rule matched yet."

    def _boundary_findings(self, edges: list[dict[str, Any]]) -> list[Finding]:
        findings: list[Finding] = []
        for edge in edges:
            policy = edge.get("policy")
            if policy not in {DependencyPolicy.FORBIDDEN.value, DependencyPolicy.RESTRICTED.value} and not edge.get("sensitive"):
                continue
            severity = Severity.WARNING
            finding_id = "ARCHITECTURE_DEPENDENCY_FORBIDDEN" if policy == DependencyPolicy.FORBIDDEN.value else "ARCHITECTURE_DEPENDENCY_RESTRICTED"
            if edge.get("sensitive") and policy != DependencyPolicy.FORBIDDEN.value:
                finding_id = "ARCHITECTURE_DEPENDENCY_SENSITIVE"
            findings.append(
                Finding(
                    id=finding_id,
                    message="Architecture dependency requires review before future enforcement.",
                    severity=severity,
                    path=f"{edge.get('source')} -> {edge.get('target')}",
                    metadata={
                        "source": edge.get("source"),
                        "target": edge.get("target"),
                        "policy": policy,
                        "sensitive": edge.get("sensitive"),
                        "reason": edge.get("reason"),
                        "sprint": "POST-H-005-C",
                        "enforcement": "advisory",
                    },
                )
            )
        return findings

    def _updated_packages(self, packages: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
        direct_out: dict[str, set[str]] = defaultdict(set)
        direct_in: dict[str, set[str]] = defaultdict(set)
        for edge in edges:
            source = str(edge.get("source"))
            target = str(edge.get("target"))
            direct_out[source].add(target)
            direct_in[target].add(source)
        updated: list[dict[str, Any]] = []
        for package in packages:
            item = dict(package)
            package_id = str(item.get("package"))
            metadata = dict(item.get("metadata") or {})
            metadata.update(
                {
                    "dependency_edges_materialized": True,
                    "hotspot_score_materialized": False,
                    "fan_in_sources": sorted(direct_in.get(package_id, set())),
                    "fan_out_targets": sorted(direct_out.get(package_id, set())),
                }
            )
            item["direct_dependencies"] = sorted(direct_out.get(package_id, set()))
            item["fan_in"] = len(direct_in.get(package_id, set()))
            item["fan_out"] = len(direct_out.get(package_id, set()))
            item["metadata"] = metadata
            updated.append(item)
        return sorted(updated, key=lambda item: str(item.get("package")))

    def _architecture_payload(
        self,
        *,
        inventory_map: dict[str, Any],
        packages: list[dict[str, Any]],
        dependencies: list[dict[str, Any]],
        parse_errors: int,
    ) -> dict[str, Any]:
        payload = dict(inventory_map)
        summary = dict(payload.get("summary") or {})
        forbidden_total = sum(1 for edge in dependencies if edge.get("policy") == DependencyPolicy.FORBIDDEN.value)
        unowned_total = sum(1 for package in packages if not package.get("owner") or package.get("ownership_status") == "missing")
        summary.update(
            {
                "packages_total": len(packages),
                "modules_total": len(payload.get("modules", [])),
                "dependencies_total": len(dependencies),
                "hotspots_total": len(payload.get("hotspots", [])),
                "forbidden_dependency_findings_total": forbidden_total,
                "unowned_packages_total": unowned_total,
                "parse_errors_total": parse_errors,
            }
        )
        source_paths = dict(payload.get("source_paths") or {})
        source_paths.update(
            {
                "dependency_graph": "in-memory:architecture-dependencies",
                "dependency_source": "Python AST import graph",
            }
        )
        payload.update(
            {
                "map_id": POST_H_005_C_REPORT_ID,
                "created_by": "POST-H-005-C",
                "status": "implemented-initial",
                "source_paths": source_paths,
                "summary": summary,
                "packages": packages,
                "dependencies": dependencies,
                "recommendations": [
                    "Use POST-H-005-D to rank hotspots using LOC, fan-in/fan-out, functions, CLI handlers and criticality.",
                    "Use POST-H-005-E to decide which advisory boundary findings become quality-gate blockers.",
                    "Keep dependency graph generation read-only; do not import or execute discovered modules.",
                ],
            }
        )
        return payload

    def _resolve_owner(self, package: str, ownership_by_package: dict[str, Any]) -> Any | None:
        if package in ownership_by_package:
            return ownership_by_package[package]
        matches = [entry for prefix, entry in ownership_by_package.items() if package.startswith(prefix + ".")]
        if not matches:
            return None
        return sorted(matches, key=lambda entry: len(entry.package), reverse=True)[0]

    def _matches_any(self, package: str, candidates: Iterable[str]) -> bool:
        return any(package == candidate or package.startswith(candidate + ".") for candidate in candidates)

    def _is_sensitive_dependency(self, source_package: str, target_package: str) -> bool:
        return self._matches_any(source_package, SENSITIVE_PACKAGES) or self._matches_any(target_package, SENSITIVE_PACKAGES)

    def _package_id(self, module_id: str) -> str:
        parts = module_id.split(".")
        if len(parts) <= 2:
            return module_id
        return ".".join(parts[:2])

    def _rel(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()

    def _empty_summary(self, source_root: Path) -> dict[str, Any]:
        return {
            "source_root": self._rel(source_root),
            "packages_total": 0,
            "modules_total": 0,
            "dependencies_total": 0,
            "hotspots_total": 0,
            "module_edges_total": 0,
            "package_edges_total": 0,
            "parse_errors_total": 0,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
