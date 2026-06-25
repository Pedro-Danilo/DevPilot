from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from devpilot_core.architecture.models import (
    ArchitectureMap,
    ArchitectureMapSafety,
    ArchitectureModule,
    ArchitecturePackage,
    OwnershipEntry,
)
from devpilot_core.architecture.ownership import DEFAULT_OWNERSHIP_REGISTRY, load_ownership_registry, ownership_entries_from_payload
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas import SchemaValidator

DEFAULT_SOURCE_ROOT = Path("src/devpilot_core")
DEFAULT_TESTS_ROOT = Path("tests")
POST_H_005_B_REPORT_ID = "architecture-inventory-post-h-005-b"

EXCLUDED_DIR_NAMES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "node_modules",
    "outputs",
    "dist",
    "build",
}


@dataclass(frozen=True)
class ArchitectureInventoryOptions:
    """Options for the local read-only POST-H-005-B inventory builder."""

    source_root: Path = DEFAULT_SOURCE_ROOT
    tests_root: Path = DEFAULT_TESTS_ROOT
    ownership_registry: Path = DEFAULT_OWNERSHIP_REGISTRY
    max_related_tests_per_module: int = 12


@dataclass(frozen=True)
class _ModuleAnalysis:
    module: ArchitectureModule
    internal_imports: tuple[str, ...]
    external_imports: tuple[str, ...]
    cli_commands: tuple[str, ...]
    cli_handlers: tuple[str, ...]
    related_tests: tuple[str, ...]


class ArchitectureInventoryBuilder:
    """Build a deterministic AST inventory for ``src/devpilot_core``.

    POST-H-005-B is intentionally local-first and read-only. It parses Python
    sources with the standard-library ``ast`` module, never imports project
    modules dynamically, never executes tests, and does not mutate source files.
    """

    def __init__(self, root: Path, options: ArchitectureInventoryOptions | None = None) -> None:
        self.root = Path(root)
        self.options = options or ArchitectureInventoryOptions()

    def build(self) -> CommandResult:
        source_root = self._resolve_inside_root(self.options.source_root)
        tests_root = self._resolve_inside_root(self.options.tests_root)
        findings: list[Finding] = []

        if not source_root.exists() or not source_root.is_dir():
            return CommandResult(
                command="architecture inventory",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Architecture inventory source root is missing.",
                data={"summary": self._empty_summary(source_root, tests_root)},
                findings=[
                    Finding(
                        id="ARCHITECTURE_INVENTORY_SOURCE_ROOT_MISSING",
                        message="Source root for architecture inventory does not exist.",
                        severity=Severity.BLOCK,
                        path=str(self.options.source_root).replace("\\", "/"),
                    )
                ],
            )

        test_paths = self._discover_test_paths(tests_root)
        ownership_payload = load_ownership_registry(self.root, self.options.ownership_registry)
        ownership_entries = ownership_entries_from_payload(ownership_payload)
        ownership_by_package = {entry.package: entry for entry in ownership_entries}

        analyses: list[_ModuleAnalysis] = []
        parse_errors = 0
        for path in self._iter_python_files(source_root):
            try:
                analyses.append(self._analyze_module(path, source_root=source_root, test_paths=test_paths))
            except SyntaxError as exc:
                parse_errors += 1
                findings.append(
                    Finding(
                        id="ARCHITECTURE_INVENTORY_AST_PARSE_ERROR",
                        message="Python source file could not be parsed by ast.",
                        severity=Severity.WARNING,
                        path=self._rel(path),
                        metadata={"lineno": exc.lineno, "offset": exc.offset, "message": exc.msg},
                    )
                )

        modules = tuple(analysis.module for analysis in analyses)
        packages = tuple(self._build_packages(analyses, ownership_by_package))
        architecture_map = ArchitectureMap(
            map_id=POST_H_005_B_REPORT_ID,
            created_by="POST-H-005-B",
            status="implemented-initial",
            packages=packages,
            modules=modules,
            ownership_registry=tuple(ownership_entries),
            ownership_gaps=tuple(self._ownership_gaps(packages)),
            recommendations=(
                "Use POST-H-005-C to convert internal import metadata into a governed dependency graph.",
                "Use POST-H-005-D to score hotspots from LOC, imports, command handlers and test coverage.",
                "Keep architecture inventory read-only; do not import or execute discovered modules.",
            ),
            source_paths={
                "source_root": self._rel(source_root),
                "tests_root": self._rel(tests_root),
                "ownership_registry": str(self.options.ownership_registry).replace("\\", "/"),
                "schema": "docs/schemas/architecture_map.schema.json",
            },
            safety=ArchitectureMapSafety(),
            preliminary=True,
        )
        payload = architecture_map.to_dict()
        schema_validation = SchemaValidator(self.root).validate_payload(schema="ArchitectureMap", payload=payload, instance_label="in-memory:architecture-map-inventory")

        if not schema_validation.ok:
            findings.extend(schema_validation.findings)

        warnings_total = sum(1 for finding in findings if finding.severity == Severity.WARNING)
        blocking_findings_total = sum(1 for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL})
        internal_imports_total = sum(len(analysis.internal_imports) for analysis in analyses)
        external_imports_total = sum(len(analysis.external_imports) for analysis in analyses)
        cli_commands_total = sum(len(analysis.cli_commands) for analysis in analyses)
        cli_handlers_total = sum(len(analysis.cli_handlers) for analysis in analyses)
        related_tests_total = len({test for analysis in analyses for test in analysis.related_tests})
        unowned_packages_total = sum(1 for package in packages if package.ownership_status == "missing")

        summary = {
            **payload["summary"],
            "source_root": self._rel(source_root),
            "tests_root": self._rel(tests_root),
            "python_files_total": len(modules),
            "parse_errors_total": parse_errors,
            "internal_imports_total": internal_imports_total,
            "external_imports_total": external_imports_total,
            "cli_commands_total": cli_commands_total,
            "cli_handlers_total": cli_handlers_total,
            "related_tests_total": related_tests_total,
            "unowned_packages_total": unowned_packages_total,
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
            "schema_validation": (schema_validation.data or {}).get("summary", {}),
            "notes": [
                "POST-H-005-B parses Python source with ast only; it does not import project modules or execute tests.",
                "Dependency edges and hotspot scores remain future POST-H-005-C/D work; this sprint stores import evidence as module/package metadata.",
                "The inventory is local-first, read-only and non-mutating by default.",
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
                    id="ARCHITECTURE_INVENTORY_PASS",
                    message="Architecture AST inventory completed without blocking findings.",
                    severity=Severity.INFO,
                    metadata={
                        "modules_total": len(modules),
                        "packages_total": len(packages),
                        "cli_commands_total": cli_commands_total,
                        "cli_handlers_total": cli_handlers_total,
                    },
                )
            )
        return CommandResult(
            command="architecture inventory",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Architecture AST inventory passed." if ok else "Architecture AST inventory failed with blocking findings.",
            data=data,
            findings=findings,
        )

    def _resolve_inside_root(self, path: Path) -> Path:
        candidate = (self.root / path).resolve()
        root_resolved = self.root.resolve()
        try:
            candidate.relative_to(root_resolved)
        except ValueError as exc:
            raise ValueError(f"architecture inventory path escapes project root: {path}") from exc
        return candidate

    def _iter_python_files(self, source_root: Path) -> Iterable[Path]:
        for path in sorted(source_root.rglob("*.py")):
            if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
                continue
            yield path

    def _discover_test_paths(self, tests_root: Path) -> tuple[Path, ...]:
        if not tests_root.exists() or not tests_root.is_dir():
            return ()
        return tuple(
            path
            for path in sorted(tests_root.rglob("test_*.py"))
            if not any(part in EXCLUDED_DIR_NAMES for part in path.parts)
        )

    def _analyze_module(self, path: Path, *, source_root: Path, test_paths: tuple[Path, ...]) -> _ModuleAnalysis:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=self._rel(path))
        module_id = self._module_id(path, source_root)
        package = self._package_id(module_id)
        imports = self._imports(tree)
        internal_imports = tuple(sorted({item for item in imports if item.startswith("devpilot_core")}))
        external_imports = tuple(sorted({item for item in imports if item and not item.startswith("devpilot_core")}))
        cli_commands = self._cli_commands(tree) if module_id == "devpilot_core.cli" else ()
        cli_handlers = self._cli_handlers(tree) if module_id == "devpilot_core.cli" else ()
        exports = self._exports(tree)
        related_tests = self._related_tests(module_id=module_id, package=package, test_paths=test_paths)
        metadata = {
            "internal_imports": list(internal_imports),
            "external_imports": list(external_imports),
            "related_tests": list(related_tests),
            "cli_commands": list(cli_commands),
            "cli_handlers": list(cli_handlers),
            "ast_inventory": True,
            "tests_executed": False,
        }
        module = ArchitectureModule(
            module_id=module_id,
            package=package,
            path=self._rel(path),
            loc=self._loc(text),
            classes_total=sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef)),
            functions_total=sum(1 for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))),
            imports_total=sum(1 for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))),
            exports_total=len(exports),
            is_cli_entrypoint=module_id == "devpilot_core.cli",
            is_test_module=False,
            metadata=metadata,
        )
        return _ModuleAnalysis(module, internal_imports, external_imports, cli_commands, cli_handlers, related_tests)

    def _build_packages(
        self,
        analyses: list[_ModuleAnalysis],
        ownership_by_package: dict[str, OwnershipEntry],
    ) -> list[ArchitecturePackage]:
        modules_by_package: dict[str, list[_ModuleAnalysis]] = defaultdict(list)
        for analysis in analyses:
            modules_by_package[analysis.module.package].append(analysis)
        packages: list[ArchitecturePackage] = []
        for package in sorted(modules_by_package):
            package_modules = sorted(modules_by_package[package], key=lambda item: item.module.module_id)
            owner = self._resolve_owner(package, ownership_by_package)
            internal_import_packages = sorted(
                {
                    self._package_id(import_id)
                    for analysis in package_modules
                    for import_id in analysis.internal_imports
                    if self._package_id(import_id) != package
                }
            )
            external_import_roots = sorted(
                {
                    import_id.split(".", maxsplit=1)[0]
                    for analysis in package_modules
                    for import_id in analysis.external_imports
                    if import_id
                }
            )
            related_tests = sorted({test for analysis in package_modules for test in analysis.related_tests})
            cli_commands = sorted({command for analysis in package_modules for command in analysis.cli_commands})
            cli_handlers = sorted({handler for analysis in package_modules for handler in analysis.cli_handlers})
            packages.append(
                ArchitecturePackage(
                    package=package,
                    domain=owner.domain if owner else "architecture.unknown",
                    owner=owner.owner if owner else None,
                    criticality=owner.criticality if owner else "P3",
                    risk_level=owner.risk_level if owner else "low",
                    modules=tuple(analysis.module.module_id for analysis in package_modules),
                    direct_dependencies=(),
                    fan_in=0,
                    fan_out=0,
                    loc=sum(analysis.module.loc for analysis in package_modules),
                    test_contracts=owner.test_contracts if owner else (),
                    ownership_status="declared" if owner else "missing",
                    metadata={
                        "modules_total": len(package_modules),
                        "internal_import_packages": internal_import_packages,
                        "external_import_roots": external_import_roots,
                        "related_tests": related_tests[:50],
                        "related_tests_total": len(related_tests),
                        "cli_commands": cli_commands,
                        "cli_handlers": cli_handlers,
                        "cli_commands_total": len(cli_commands),
                        "cli_handlers_total": len(cli_handlers),
                        "dependency_edges_materialized": False,
                        "hotspot_score_materialized": False,
                    },
                )
            )
        return packages

    def _ownership_gaps(self, packages: tuple[ArchitecturePackage, ...]) -> list[dict[str, Any]]:
        return [
            {
                "package": package.package,
                "severity": "warning",
                "message": "Discovered package has no explicit ownership entry yet.",
                "recommended_action": "Classify package ownership in POST-H-005-E or keep as inferred if non-critical.",
            }
            for package in packages
            if package.ownership_status == "missing"
        ]

    def _resolve_owner(self, package: str, ownership_by_package: dict[str, OwnershipEntry]) -> OwnershipEntry | None:
        if package in ownership_by_package:
            return ownership_by_package[package]
        # Ownership registry may declare a package family. Use the longest prefix.
        matches = [entry for prefix, entry in ownership_by_package.items() if package.startswith(prefix + ".")]
        if not matches:
            return None
        return sorted(matches, key=lambda entry: len(entry.package), reverse=True)[0]

    def _imports(self, tree: ast.AST) -> list[str]:
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module
                    if node.level and module and not module.startswith("devpilot_core"):
                        # Relative import inside devpilot_core; materialize as internal root evidence.
                        module = f"devpilot_core.{module}"
                    imports.append(module)
                elif node.level:
                    imports.append("devpilot_core")
        return imports

    def _cli_commands(self, tree: ast.AST) -> tuple[str, ...]:
        commands: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute) or node.func.attr != "add_parser":
                continue
            if not node.args:
                continue
            value = self._string_literal(node.args[0])
            if value:
                commands.append(value)
        return tuple(sorted(dict.fromkeys(commands)))

    def _cli_handlers(self, tree: ast.AST) -> tuple[str, ...]:
        handlers: list[str] = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef) and (node.name.endswith("_command") or node.name in {"readiness_check", "miasi_required"}):
                handlers.append(node.name)
        return tuple(sorted(dict.fromkeys(handlers)))

    def _exports(self, tree: ast.AST) -> tuple[str, ...]:
        exports: set[str] = set()
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
                exports.add(node.name)
            if isinstance(node, ast.Assign):
                if any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
                    exports.update(self._string_sequence(node.value))
        return tuple(sorted(exports))

    def _related_tests(self, *, module_id: str, package: str, test_paths: tuple[Path, ...]) -> tuple[str, ...]:
        if not test_paths:
            return ()
        leaf = module_id.rsplit(".", maxsplit=1)[-1].replace("_", "-")
        package_leaf = package.rsplit(".", maxsplit=1)[-1].replace("_", "-")
        tokens = {leaf, package_leaf, leaf.replace("-", "_"), package_leaf.replace("-", "_")}
        if module_id == "devpilot_core.cli":
            tokens.update({"cli", "command"})
        matched: list[str] = []
        for path in test_paths:
            rel = self._rel(path)
            normalized = rel.lower().replace("_", "-")
            if any(token and token.lower() in normalized for token in tokens):
                matched.append(rel)
        return tuple(matched[: self.options.max_related_tests_per_module])

    def _module_id(self, path: Path, source_root: Path) -> str:
        relative = path.relative_to(source_root)
        parts = list(relative.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(["devpilot_core", *parts]) if parts else "devpilot_core"

    def _package_id(self, module_id: str) -> str:
        parts = module_id.split(".")
        if len(parts) <= 2:
            return module_id
        return ".".join(parts[:2])

    def _loc(self, text: str) -> int:
        return sum(1 for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#"))

    def _string_literal(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def _string_sequence(self, node: ast.AST) -> tuple[str, ...]:
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            values = [self._string_literal(item) for item in node.elts]
            return tuple(value for value in values if value)
        return ()

    def _rel(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()

    def _empty_summary(self, source_root: Path, tests_root: Path) -> dict[str, Any]:
        return {
            "source_root": self._rel(source_root),
            "tests_root": self._rel(tests_root),
            "packages_total": 0,
            "modules_total": 0,
            "dependencies_total": 0,
            "hotspots_total": 0,
            "ownership_entries_total": 0,
            "forbidden_dependency_findings_total": 0,
            "unowned_packages_total": 0,
            "python_files_total": 0,
            "parse_errors_total": 0,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
