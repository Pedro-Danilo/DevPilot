from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PathGuard, PolicyEffect, SecretGuard
from devpilot_core.repo.dependency_graph import DependencyGraphBuilder
from devpilot_core.repo.git_adapter import GitAdapter
from devpilot_core.repo.inventory import RepoInventory, RepoInventoryItem
from devpilot_core.repo.models import RepoHealthSummary, RepoHotspot, RepoRiskSignal

_DEFAULT_EXCLUDED_DIRS = (".git", ".venv", "__pycache__", ".pytest_cache", "outputs", ".devpilot", "build", "dist", ".mypy_cache", ".ruff_cache")
_TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env", ".example"}
_TODO_PATTERN = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)
_DEFAULT_LARGE_FILE_BYTES = 200_000
_DEFAULT_MAX_FILES = 5000
_DEFAULT_MAX_FINDINGS_PER_KIND = 25


@dataclass(frozen=True)
class RepoAnalyzerConfig:
    """Configuration for the local read-only RepoAnalyzer v2."""

    max_files: int = _DEFAULT_MAX_FILES
    large_file_bytes: int = _DEFAULT_LARGE_FILE_BYTES
    max_text_scan_bytes: int = 65_536
    max_findings_per_kind: int = _DEFAULT_MAX_FINDINGS_PER_KIND
    excluded_dirs: tuple[str, ...] = _DEFAULT_EXCLUDED_DIRS


class RepoAnalyzer:
    """Consolidate repository structure, Git state, dependencies and risks.

    Purpose:
        Provide the first repository-health summary for Fase C by combining
        existing read-only engines: RepoInventory, DependencyGraph and GitAdapter.

    Functioning:
        Walks a target inside the workspace, excludes runtime/cache folders,
        inspects metadata and bounded text windows, aggregates documentation,
        source and test sections, and derives heuristic risk signals.

    Integration:
        Exposed through `python -m devpilot_core repo analyze --json` and used
        as future input for architecture drift and repo quality gates.

    PASS:
        Read-only analysis, JSON/Markdown report support, no raw secret values,
        partial operation when Git is unavailable and explicit preliminary notes.

    BLOCK:
        Target outside workspace, path policy violation, raw secret leakage or
        traversal outside the project root.

    Risks:
        This analyzer is heuristic. It is not a SAST/SCA scanner, not a runtime
        profiler, not a license scanner and not a production readiness
        certification.
    """

    def __init__(self, root: Path, *, config: RepoAnalyzerConfig | None = None) -> None:
        self.root = root.resolve()
        self.config = config or RepoAnalyzerConfig()
        self.secret_guard = SecretGuard()

    def analyze(self, *, target: str | Path = ".") -> CommandResult:
        target_path = self._resolve_target(target)
        rel_target = _display_path(target_path, self.root)
        decision = PathGuard(self.root).evaluate(rel_target, action="read")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            return CommandResult(
                command="repo analyze",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="RepoAnalyzer blocked by path policy.",
                findings=[Finding(id=decision.rule_id, message=decision.reason, severity=Severity.BLOCK, path=decision.subject)],
            )
        if not target_path.exists():
            return CommandResult(
                command="repo analyze",
                ok=False,
                exit_code=ExitCode.FAIL,
                message="RepoAnalyzer target does not exist.",
                data={"summary": {"target": rel_target, "preliminary": True}},
                findings=[Finding(id="REPO_ANALYZER_TARGET_NOT_FOUND", message="Target path does not exist.", severity=Severity.FAIL, path=rel_target)],
            )
        try:
            target_path.resolve().relative_to(self.root)
        except ValueError:
            return CommandResult(
                command="repo analyze",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="RepoAnalyzer target is outside the workspace root.",
                findings=[Finding(id="REPO_ANALYZER_TARGET_OUTSIDE_ROOT", message="Target path is outside the workspace root.", severity=Severity.BLOCK, path=str(target_path))],
            )

        inventory_result = RepoInventory(self.root).build()
        inventory_items = [item for item in _inventory_items(inventory_result) if not _is_runtime_artifact_item(item)]
        sections = self._section_summary(inventory_items)

        dependency_target = self._default_dependency_target(target_path)
        dependency_result = DependencyGraphBuilder(self.root, excluded_dirs=self.config.excluded_dirs, max_files=self.config.max_files).build(target=dependency_target)
        dependency_summary = _safe_summary(dependency_result)
        dependency_metrics = _safe_metrics(dependency_result)

        git_result = GitAdapter(self.root).status()
        git_summary = _safe_summary(git_result)

        risk_signals, findings = self._derive_risks(
            inventory_items=inventory_items,
            dependency_result=dependency_result,
            git_result=git_result,
            target_path=target_path,
        )
        hotspots = _derive_hotspots(dependency_metrics)
        health = RepoHealthSummary.from_inputs(
            target=rel_target,
            sections=sections,
            risk_signals=risk_signals,
            dependency_summary=dependency_summary,
            git_summary=git_summary,
            hotspots=hotspots,
        )

        findings.extend(_copy_relevant_findings(inventory_result, prefix="inventory"))
        findings.extend(_copy_relevant_findings(dependency_result, prefix="dependency_graph"))
        findings.extend(_copy_relevant_findings(git_result, prefix="git"))
        if not findings:
            findings.append(Finding(id="REPO_ANALYZER_PASS", message="Repository analysis completed without blocking findings.", severity=Severity.INFO))

        data = {
            "summary": health.to_dict(),
            "sections": sections,
            "inventory_summary": _safe_summary(inventory_result),
            "dependency_summary": dependency_summary,
            "dependency_metrics": dependency_metrics,
            "git_summary": git_summary,
            "hotspots": [hotspot.to_dict() for hotspot in hotspots],
            "risk_signals": [signal.to_dict() for signal in risk_signals],
            "notes": [
                "FUNC-SPRINT-37 RepoAnalyzer v2 is read-only and heuristic.",
                "Runtime folders such as outputs, caches, virtualenvs, build and dist are excluded from the analysis.",
                "Secret-like content is reported only as redacted metadata; raw values are never emitted.",
                "The health score is an engineering signal, not a production certification.",
                "Dependency metrics come from static AST imports and do not prove runtime call relationships.",
            ],
        }
        return CommandResult(
            command="repo analyze",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Repository analysis completed in read-only mode.",
            data=data,
            findings=findings,
        )

    def _resolve_target(self, target: str | Path) -> Path:
        candidate = Path(target)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        return candidate.resolve()

    def _default_dependency_target(self, target_path: Path) -> Path:
        if (self.root / "src" / "devpilot_core").exists():
            return self.root / "src" / "devpilot_core"
        if (target_path / "src").exists():
            return target_path / "src"
        if (self.root / "src").exists():
            return self.root / "src"
        return target_path

    def _section_summary(self, items: list[RepoInventoryItem]) -> dict[str, Any]:
        sections: dict[str, dict[str, Any]] = {
            "source": {"files": 0, "python_files": 0, "size_bytes": 0},
            "tests": {"files": 0, "python_files": 0, "size_bytes": 0},
            "docs": {"files": 0, "markdown_files": 0, "size_bytes": 0},
            "config": {"files": 0, "size_bytes": 0},
            "other": {"files": 0, "size_bytes": 0},
        }
        for item in items:
            bucket = _section_for(item.path, item.category)
            sections[bucket]["files"] += 1
            sections[bucket]["size_bytes"] += item.size_bytes
            if item.suffix == ".py":
                sections[bucket]["python_files"] = sections[bucket].get("python_files", 0) + 1
            if item.suffix == ".md":
                sections[bucket]["markdown_files"] = sections[bucket].get("markdown_files", 0) + 1
        sections["summary"] = {
            "files_total": len(items),
            "src_tests_ratio": _safe_ratio(sections["source"].get("python_files", 0), sections["tests"].get("python_files", 0)),
            "docs_to_source_ratio": _safe_ratio(sections["docs"].get("markdown_files", 0), sections["source"].get("python_files", 0)),
        }
        return sections

    def _derive_risks(
        self,
        *,
        inventory_items: list[RepoInventoryItem],
        dependency_result: CommandResult,
        git_result: CommandResult,
        target_path: Path,
    ) -> tuple[list[RepoRiskSignal], list[Finding]]:
        signals: list[RepoRiskSignal] = []
        findings: list[Finding] = []
        large_files = [item for item in inventory_items if item.size_bytes > self.config.large_file_bytes]
        for item in large_files[: self.config.max_findings_per_kind]:
            signals.append(RepoRiskSignal("large_file", item.path, "warning", "File exceeds configured large_file_bytes threshold.", {"size_bytes": item.size_bytes, "threshold": self.config.large_file_bytes}))
        if large_files:
            findings.append(Finding(id="REPO_ANALYZER_LARGE_FILES", message="Large files were detected; review maintainability and report size impact.", severity=Severity.WARNING, metadata={"count": len(large_files), "threshold": self.config.large_file_bytes}))

        secret_like = [item for item in inventory_items if item.secret_like and _is_actionable_secret_item(item)]
        for item in secret_like[: self.config.max_findings_per_kind]:
            signals.append(RepoRiskSignal("secret_like_file", item.path, "block", "Secret-like content was detected and redacted; raw values are not emitted.", {"redacted": True, "reasons": item.reasons}))
        if secret_like:
            findings.append(Finding(id="REPO_ANALYZER_SECRET_LIKE_CONTENT", message="Secret-like content detected. Raw secret values were not emitted.", severity=Severity.BLOCK, metadata={"count": len(secret_like), "redacted": True}))

        todo_files = self._scan_todo_files(target_path)
        for path, count in todo_files[: self.config.max_findings_per_kind]:
            signals.append(RepoRiskSignal("todo_marker", path, "warning", "TODO/FIXME/HACK markers detected without emitting source text.", {"markers": count}))
        if todo_files:
            findings.append(Finding(id="REPO_ANALYZER_TODO_MARKERS", message="TODO/FIXME/HACK markers were detected in bounded text scan.", severity=Severity.WARNING, metadata={"files": len(todo_files), "markers_total": sum(count for _, count in todo_files)}))

        untested_modules = _modules_without_near_tests(dependency_result.data or {}, self.root)
        for item in untested_modules[: self.config.max_findings_per_kind]:
            signals.append(RepoRiskSignal("module_without_near_test", item["path"], "warning", "Python module has no obvious nearby/direct test by naming heuristic.", {"module": item["module"]}))
        if untested_modules:
            findings.append(Finding(id="REPO_ANALYZER_MODULES_WITHOUT_NEAR_TESTS", message="Some modules do not have obvious nearby/direct tests by heuristic.", severity=Severity.WARNING, metadata={"count": len(untested_modules), "sample": untested_modules[:10]}))

        syntax_errors = (dependency_result.data or {}).get("summary", {}).get("syntax_error_files_total", 0)
        if isinstance(syntax_errors, int) and syntax_errors > 0:
            findings.append(Finding(id="REPO_ANALYZER_DEPENDENCY_SYNTAX_ERRORS", message="DependencyGraph reported Python syntax errors.", severity=Severity.WARNING, metadata={"count": syntax_errors}))

        git_is_repo = (git_result.data or {}).get("summary", {}).get("is_git_repo")
        if git_is_repo is False:
            findings.append(Finding(id="REPO_ANALYZER_GIT_UNAVAILABLE", message="Git metadata is unavailable or workspace is not a Git repository; analysis continues partially.", severity=Severity.WARNING))
        else:
            counts = (git_result.data or {}).get("summary", {}).get("counts", {})
            if isinstance(counts, dict) and counts.get("entries_total", 0):
                signals.append(RepoRiskSignal("git_worktree_changes", ".", "warning", "Working tree contains changes; repository health is based on current uncommitted state.", {"counts": counts}))
                findings.append(Finding(id="REPO_ANALYZER_GIT_WORKTREE_CHANGES", message="Working tree changes are present during analysis.", severity=Severity.WARNING, metadata=counts))
        return signals, findings

    def _scan_todo_files(self, target_path: Path) -> list[tuple[str, int]]:
        files: list[Path]
        if target_path.is_file():
            files = [target_path]
        else:
            files = sorted(path for path in target_path.rglob("*") if path.is_file())
        matches: list[tuple[str, int]] = []
        for path in files[: self.config.max_files]:
            if _is_excluded(path, self.root, self.config.excluded_dirs):
                continue
            if path.suffix.lower() not in _TEXT_SUFFIXES and not path.name.lower().startswith(".env"):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")[: self.config.max_text_scan_bytes]
            except OSError:
                continue
            count = len(_TODO_PATTERN.findall(text))
            if count:
                matches.append((_display_path(path, self.root), count))
        return matches


def _inventory_items(result: CommandResult) -> list[RepoInventoryItem]:
    items: list[RepoInventoryItem] = []
    for raw in (result.data or {}).get("items", []):
        if not isinstance(raw, dict):
            continue
        items.append(
            RepoInventoryItem(
                path=str(raw.get("path", "")),
                size_bytes=int(raw.get("size_bytes", 0)),
                suffix=str(raw.get("suffix", "")),
                category=str(raw.get("category", "other")),
                risk=str(raw.get("risk", "low")),
                secret_like=bool(raw.get("secret_like", False)),
                reasons=list(raw.get("reasons", [])),
            )
        )
    return items


def _is_runtime_artifact_item(item: RepoInventoryItem) -> bool:
    path = item.path.replace("\\", "/")
    if path.startswith("outputs/"):
        return True
    if path in {".devpilot/devpilot.db"} or (path.startswith(".devpilot/") and path.endswith((".db", ".sqlite", ".sqlite3"))):
        return True
    if "/__pycache__/" in path or path.endswith("/__pycache__"):
        return True
    return False


def _is_actionable_secret_item(item: RepoInventoryItem) -> bool:
    path = item.path.lower()
    name = Path(path).name
    if name in {".env", ".env.local", ".env.dev", "id_rsa", "id_ed25519"}:
        return True
    if path.endswith((".pem", ".key", ".p12", ".pfx")):
        return True
    if "/.env" in path or path.startswith(".env"):
        return not path.endswith(".example")
    return False


def _section_for(path: str, category: str) -> str:
    if path.startswith("src/"):
        return "source"
    if path.startswith("tests/") or "/tests/" in path:
        return "tests"
    if path.startswith("docs/") or category == "documentation":
        return "docs"
    if category == "configuration" or path.startswith(".devpilot/") or path in {"pyproject.toml", ".gitignore", ".env.example"}:
        return "config"
    return "other"


def _safe_summary(result: CommandResult) -> dict[str, Any]:
    summary = (result.data or {}).get("summary", {})
    return summary if isinstance(summary, dict) else {}


def _safe_metrics(result: CommandResult) -> dict[str, Any]:
    metrics = (result.data or {}).get("metrics", {})
    return metrics if isinstance(metrics, dict) else {}


def _derive_hotspots(metrics: dict[str, Any]) -> list[RepoHotspot]:
    hotspots: list[RepoHotspot] = []
    for key, metric_name in (("top_fan_in", "fan_in"), ("top_fan_out", "fan_out")):
        values = metrics.get(key, [])
        if not isinstance(values, list):
            continue
        for item in values[:10]:
            if not isinstance(item, dict):
                continue
            score = int(item.get(metric_name, 0) or 0)
            if score <= 0:
                continue
            hotspots.append(RepoHotspot(module=str(item.get("module", "")), path=str(item.get("path", "")), metric=metric_name, score=score))
    return hotspots


def _modules_without_near_tests(data: dict[str, Any], root: Path) -> list[dict[str, str]]:
    nodes = data.get("nodes", [])
    if not isinstance(nodes, list):
        return []
    test_paths = {str(path).replace("\\", "/") for path in _iter_files(root / "tests", suffix=".py")}
    result: list[dict[str, str]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        path = str(node.get("path", ""))
        module = str(node.get("module", ""))
        if not path.startswith("src/") or path.endswith("/__init__.py"):
            continue
        stem = Path(path).stem
        module_leaf = module.rsplit(".", 1)[-1]
        candidates = {f"tests/test_{stem}.py", f"tests/test_{module_leaf}.py"}
        has_test = any(candidate in test_paths for candidate in candidates)
        if not has_test:
            # Broader filename heuristic without reading test contents.
            has_test = any((stem in Path(test_path).stem or module_leaf in Path(test_path).stem) for test_path in test_paths)
        if not has_test:
            result.append({"module": module, "path": path})
    return result


def _iter_files(root: Path, *, suffix: str) -> Iterable[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob(f"*{suffix}") if path.is_file())


def _copy_relevant_findings(result: CommandResult, *, prefix: str) -> list[Finding]:
    copied: list[Finding] = []
    for finding in result.findings:
        if finding.severity == Severity.INFO:
            continue
        if prefix == "inventory" and finding.id in {"REPO_INVENTORY_SECRET_LIKE_CONTENT", "REPO_INVENTORY_HIGH_RISK_FILE"}:
            continue
        copied.append(
            Finding(
                id=f"REPO_ANALYZER_UPSTREAM_{finding.id}",
                message=f"Upstream {prefix} finding: {finding.message}",
                severity=finding.severity,
                path=finding.path,
                metadata={"source": prefix, **finding.metadata},
            )
        )
    return copied


def _safe_ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 3)


def _is_excluded(path: Path, root: Path, excluded_dirs: tuple[str, ...]) -> bool:
    try:
        parts = path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        return True
    return any(part in excluded_dirs for part in parts[:-1] if part)


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/") or "."
    except ValueError:
        return str(path).replace("\\", "/")
