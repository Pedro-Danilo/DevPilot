from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PathGuard, PolicyEffect
from devpilot_core.repo.models import DependencyGraphEdge, DependencyGraphNode, DependencyGraphResult

_DEFAULT_EXCLUDED_DIRS = (".git", ".venv", "__pycache__", ".pytest_cache", "outputs", "build", "dist", ".mypy_cache")
_MAX_FILES_DEFAULT = 5000


@dataclass(frozen=True)
class PythonImportOccurrence:
    import_name: str
    import_type: str
    lineno: int | None = None


class DependencyGraphBuilder:
    """Build a deterministic Python dependency graph without executing code.

    Purpose:
        Provide repository-intelligence input for RepoAnalyzer, architecture
        drift, review gates and future safe refactor planning.

    Functioning:
        Walks Python files under a target directory, parses imports with
        `ast.parse`, maps local modules to repository paths, and creates
        directed internal edges from importing module to imported module.

    Integration:
        Exposed as `python -m devpilot_core repo dependency-graph --target ...`.
        The command returns CommandResult and can write evidence via ReportEngine.

    PASS:
        Read-only traversal, no code execution, JSON-serializable graph,
        fan-in/fan-out metrics and controlled syntax-error findings.

    BLOCK:
        Target outside workspace, symlink traversal outside workspace, or target
        path not found.

    Risks:
        This is a static AST import graph. It does not evaluate dynamic imports,
        runtime plugins, conditional execution, importlib calls or semantic call
        graphs. Findings are engineering signals, not proof of runtime coupling.
    """

    def __init__(self, root: Path, *, excluded_dirs: tuple[str, ...] = _DEFAULT_EXCLUDED_DIRS, max_files: int = _MAX_FILES_DEFAULT) -> None:
        self.root = root.resolve()
        self.excluded_dirs = excluded_dirs
        self.max_files = max_files

    def build(self, *, target: str | Path = "src/devpilot_core") -> CommandResult:
        target_path = self._resolve_target(target)
        rel_target = _display_path(target_path, self.root)
        path_decision = PathGuard(self.root).evaluate(rel_target, action="read")
        if path_decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            return CommandResult(
                command="repo dependency-graph",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Dependency graph blocked by path policy.",
                findings=[Finding(id=path_decision.rule_id, message=path_decision.reason, severity=Severity.BLOCK, path=path_decision.subject)],
            )
        if not target_path.exists():
            return CommandResult(
                command="repo dependency-graph",
                ok=False,
                exit_code=ExitCode.FAIL,
                message="Dependency graph target does not exist.",
                data={"summary": {"target": rel_target, "preliminary": True}},
                findings=[Finding(id="DEPENDENCY_GRAPH_TARGET_NOT_FOUND", message="Target path does not exist.", severity=Severity.FAIL, path=rel_target)],
            )
        try:
            target_path.resolve().relative_to(self.root)
        except ValueError:
            return CommandResult(
                command="repo dependency-graph",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Dependency graph target is outside the workspace root.",
                findings=[Finding(id="DEPENDENCY_GRAPH_TARGET_OUTSIDE_ROOT", message="Target path is outside the workspace root.", severity=Severity.BLOCK, path=str(target_path))],
            )

        python_files, ignored_dirs, truncated = self._collect_python_files(target_path)
        root_package = _infer_root_package(target_path, self.root)
        module_by_path = {path: _module_name_for(path, target_path, root_package) for path in python_files}
        path_by_module = {module: path for path, module in module_by_path.items()}

        dependencies_by_module: dict[str, set[str]] = {module: set() for module in path_by_module}
        dependents_by_module: dict[str, set[str]] = {module: set() for module in path_by_module}
        external_imports_by_module: dict[str, set[str]] = {module: set() for module in path_by_module}
        edges: list[DependencyGraphEdge] = []
        syntax_error_files: list[str] = []
        findings: list[Finding] = []

        for path in python_files:
            source_module = module_by_path[path]
            rel_path = _display_path(path, self.root)
            try:
                occurrences = _parse_imports(path)
            except SyntaxError as exc:
                syntax_error_files.append(rel_path)
                findings.append(
                    Finding(
                        id="DEPENDENCY_GRAPH_SYNTAX_ERROR",
                        message="Python file could not be parsed with AST; file was kept as node without import edges.",
                        severity=Severity.WARNING,
                        path=rel_path,
                        metadata={"lineno": exc.lineno, "offset": exc.offset, "error": str(exc.msg)},
                    )
                )
                continue
            except OSError as exc:
                findings.append(Finding(id="DEPENDENCY_GRAPH_FILE_READ_FAILED", message="Python file could not be read.", severity=Severity.WARNING, path=rel_path, metadata={"error": str(exc)}))
                continue
            for occurrence in occurrences:
                target_module = _resolve_internal_module(occurrence.import_name, source_module, root_package, path_by_module)
                if target_module is None:
                    external_imports_by_module[source_module].add(_top_level_name(occurrence.import_name))
                    continue
                dependencies_by_module[source_module].add(target_module)
                dependents_by_module[target_module].add(source_module)
                edges.append(
                    DependencyGraphEdge(
                        source=source_module,
                        target=target_module,
                        import_name=occurrence.import_name,
                        import_type=occurrence.import_type,
                        lineno=occurrence.lineno,
                    )
                )

        nodes: list[DependencyGraphNode] = []
        for module, path in sorted(path_by_module.items()):
            rel_path = _display_path(path, self.root)
            nodes.append(
                DependencyGraphNode(
                    module=module,
                    path=rel_path,
                    package=root_package,
                    dependencies=sorted(dependencies_by_module[module]),
                    dependents=sorted(dependents_by_module[module]),
                    external_imports=sorted(external_imports_by_module[module]),
                    syntax_error=rel_path in syntax_error_files,
                )
            )
        graph = DependencyGraphResult(
            root_package=root_package,
            target=rel_target,
            nodes=nodes,
            edges=sorted(edges, key=lambda edge: (edge.source, edge.target, edge.import_name, edge.lineno or 0)),
            external_imports=sorted({name for names in external_imports_by_module.values() for name in names}),
            syntax_error_files=syntax_error_files,
            ignored_dirs=ignored_dirs,
            truncated=truncated,
            max_files=self.max_files,
        )
        data = graph.to_dict()
        if truncated:
            findings.append(Finding(id="DEPENDENCY_GRAPH_FILE_LIMIT_REACHED", message="Dependency graph reached max_files and was truncated.", severity=Severity.WARNING, metadata={"max_files": self.max_files}))
        if not findings:
            findings.append(Finding(id="DEPENDENCY_GRAPH_PASS", message="Python dependency graph generated in read-only mode.", severity=Severity.INFO))
        return CommandResult(command="repo dependency-graph", ok=True, exit_code=ExitCode.PASS, message="Python dependency graph generated in read-only mode.", data=data, findings=findings)

    def _resolve_target(self, target: str | Path) -> Path:
        candidate = Path(target)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        return candidate.resolve()

    def _collect_python_files(self, target_path: Path) -> tuple[list[Path], list[str], bool]:
        files: list[Path] = []
        ignored_dirs: set[str] = set()
        candidates: Iterable[Path]
        if target_path.is_file():
            candidates = [target_path]
        else:
            candidates = sorted(target_path.rglob("*.py"))
        truncated = False
        for path in candidates:
            if _is_ignored(path, self.root, self.excluded_dirs):
                ignored_dirs.add(_ignored_parent(path, self.root, self.excluded_dirs))
                continue
            try:
                resolved = path.resolve()
                resolved.relative_to(self.root)
            except ValueError:
                ignored_dirs.add(_display_path(path, self.root))
                continue
            if not path.is_file() or path.suffix != ".py":
                continue
            if len(files) >= self.max_files:
                truncated = True
                break
            files.append(path)
        return files, sorted(ignored_dirs), truncated


def _parse_imports(path: Path) -> list[PythonImportOccurrence]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[PythonImportOccurrence] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(PythonImportOccurrence(import_name=alias.name, import_type="import", lineno=node.lineno))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level > 0:
                base_name = "." * node.level + module
            else:
                base_name = module
            if not base_name:
                continue
            for alias in node.names:
                if alias.name == "*":
                    import_name = base_name
                else:
                    import_name = f"{base_name}.{alias.name}" if module or not base_name.endswith(".") else f"{base_name}{alias.name}"
                imports.append(PythonImportOccurrence(import_name=import_name, import_type="from", lineno=node.lineno))
    return imports


def _infer_root_package(target_path: Path, root: Path) -> str | None:
    if target_path.is_file():
        package_root = target_path.parent
    else:
        package_root = target_path
    if (package_root / "__init__.py").exists():
        return package_root.name
    try:
        parts = package_root.resolve().relative_to(root.resolve()).parts
    except ValueError:
        return None
    if len(parts) >= 2 and parts[0] == "src":
        return parts[-1]
    return parts[-1] if parts else None


def _module_name_for(path: Path, target_path: Path, root_package: str | None) -> str:
    base = target_path if target_path.is_dir() else target_path.parent
    rel = path.resolve().relative_to(base.resolve())
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    if root_package:
        parts = [root_package, *parts]
    return ".".join(parts) if parts else (root_package or path.stem)


def _resolve_internal_module(import_name: str, source_module: str, root_package: str | None, path_by_module: dict[str, Path]) -> str | None:
    if import_name.startswith("."):
        resolved = _resolve_relative_import(import_name, source_module)
        return _match_module(resolved, path_by_module)
    if root_package and import_name == root_package:
        return _match_module(import_name, path_by_module)
    if root_package and import_name.startswith(root_package + "."):
        return _match_module(import_name, path_by_module)
    return None


def _resolve_relative_import(import_name: str, source_module: str) -> str:
    level = len(import_name) - len(import_name.lstrip("."))
    remainder = import_name[level:]
    source_parts = source_module.split(".")
    # One dot imports from the current package; two dots go one level up.
    keep = max(1, len(source_parts) - level)
    base = source_parts[:keep]
    if remainder:
        base.extend(part for part in remainder.split(".") if part)
    return ".".join(base)


def _match_module(import_name: str, path_by_module: dict[str, Path]) -> str | None:
    if import_name in path_by_module:
        return import_name
    pieces = import_name.split(".")
    while len(pieces) > 1:
        pieces.pop()
        candidate = ".".join(pieces)
        if candidate in path_by_module:
            return candidate
    return None


def _top_level_name(import_name: str) -> str:
    stripped = import_name.lstrip(".")
    return stripped.split(".", 1)[0] if stripped else import_name


def _is_ignored(path: Path, root: Path, excluded_dirs: tuple[str, ...]) -> bool:
    try:
        parts = path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        return True
    return any(part in excluded_dirs for part in parts[:-1] if part)


def _ignored_parent(path: Path, root: Path, excluded_dirs: tuple[str, ...]) -> str:
    try:
        parts = path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        return _display_path(path, root)
    current = Path()
    for part in parts:
        current = current / part
        if part in excluded_dirs:
            return str(current).replace("\\", "/")
    return _display_path(path.parent, root)


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/") or "."
    except ValueError:
        return str(path).replace("\\", "/")
