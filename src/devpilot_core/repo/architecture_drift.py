from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PathGuard, PolicyEffect
from devpilot_core.repo.analyzer import RepoAnalyzer
from devpilot_core.repo.dependency_graph import DependencyGraphBuilder
from devpilot_core.repo.models import ArchitectureComponentRecord, ArchitectureDriftMatrixRow

DEFAULT_ARCHITECTURE_DOCS = (
    "docs/02_architecture/architecture_document.md",
    "docs/02_architecture/c4_container.md",
    "docs/02_architecture/c4_component.md",
)

IMPLEMENTED_STATES = {"implemented", "implemented-initial", "partial"}
ASPIRATIONAL_STATES = {"planned", "future", "disabled"}
KNOWN_COMPONENT_ALIASES: dict[str, tuple[str, ...]] = {
    "cli": ("cli", "devpilot cli", "command line", "interfaz cli"),
    "application": ("application", "applicationservice", "application service", "appsvc"),
    "validators": ("validators", "validation", "frontmatter", "artifact validator", "checklist", "readiness"),
    "standards": ("standards", "standards registry", "mipsoftware", "miasi standards"),
    "reports": ("reports", "report engine", "evidence report"),
    "observability": ("observability", "eventlogger", "jsonl", "traces", "obs"),
    "workspace": ("workspace", "workspace manager", "workspace detector"),
    "policy": ("policy", "policy engine", "guards", "pathguard", "secretguard", "costguard"),
    "store": ("store", "localstore", "sqlite", "persistence"),
    "miasi": ("miasi", "agent registry", "tool registry", "policy matrix"),
    "agents": ("agents", "agentruntime", "agent runtime", "documental agent"),
    "evals": ("evals", "eval harness", "evaluation"),
    "repo": ("repo", "gitadapter", "git adapter", "repo inventory", "repo analyzer", "dependencygraph"),
    "review": ("review", "patch review", "code review"),
    "refactor": ("refactor", "safe refactor", "refactor planner"),
    "modeling": ("modeling", "modeladapter", "model adapter", "mockmodeladapter"),
    "approval": ("approval", "approval workflow", "human approval", "approval queue"),
    "execution": ("execution", "safesubprocess", "safe subprocess", "tests.run"),
    "security": ("security", "security readiness", "policy simulation"),
    "testing": ("testing", "tests.run", "controlled tests"),
    "schemas": ("schemas", "schema registry", "schema validator"),
    "traceability": ("traceability", "traceability engine", "architecture drift"),
    "validation": ("validation gateway", "validation"),
    "errors": ("errors", "devpiloterror"),
    "cli_models": ("cli_models", "commandresult", "finding", "exitcode"),
}

_STOP_WORDS = {
    "devpilot", "core", "engine", "manager", "validator", "registry", "adapter", "service",
    "layer", "container", "component", "queue", "workflow", "local", "initial", "basic",
    "future", "planned", "implemented", "partial", "ui", "api", "guard", "guards",
}
_STATE_PATTERN = re.compile(r"\b(implemented-initial|implemented|partial|planned|future|disabled)\b", re.IGNORECASE)
_BACKTICK_PATH_PATTERN = re.compile(r"`([^`]*(?:src/devpilot_core|devpilot_core)[^`]*)`")
_MERMAID_NODE_PATTERN = re.compile(r"\b[A-Za-z][A-Za-z0-9_]*\s*\[([^\]]+)\]")


@dataclass(frozen=True)
class ArchitectureDriftConfig:
    """Configuration for the FUNC-SPRINT-38 architecture/code drift detector."""

    architecture_docs: tuple[str, ...] = DEFAULT_ARCHITECTURE_DOCS
    source_root: str = "src/devpilot_core"
    max_components: int = 250
    max_rows: int = 500


class ArchitectureDriftDetector:
    """Compare architecture documentation against the actual Python package map.

    The detector is deliberately conservative and read-only. It extracts
    documented components from architecture Markdown tables and Mermaid nodes,
    extracts actual top-level modules from `DependencyGraph`, then builds a
    traceable matrix with confidence and drift type.

    It does not execute code, does not call LLMs, does not use network and does
    not mutate documentation. It is an `implemented-initial` signal for Fase C,
    not a semantic architecture-certification engine.
    """

    def __init__(self, root: Path, *, config: ArchitectureDriftConfig | None = None) -> None:
        self.root = root.resolve()
        self.config = config or ArchitectureDriftConfig()

    def detect(self) -> CommandResult:
        source_root = (self.root / self.config.source_root).resolve()
        path_decision = PathGuard(self.root).evaluate(self.config.source_root, action="read")
        if path_decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            return CommandResult(
                command="repo architecture-drift",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Architecture drift detection blocked by path policy.",
                findings=[Finding(id=path_decision.rule_id, message=path_decision.reason, severity=Severity.BLOCK, path=path_decision.subject)],
                data={"summary": _empty_summary()},
            )
        if not source_root.exists():
            return CommandResult(
                command="repo architecture-drift",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Architecture drift detection blocked because source root is missing.",
                findings=[Finding(id="ARCH_DRIFT_SOURCE_ROOT_MISSING", message="Configured source root does not exist.", severity=Severity.BLOCK, path=self.config.source_root)],
                data={"summary": _empty_summary()},
            )

        doc_records, doc_text, doc_findings = self._load_architecture_docs()
        documented_components = self._extract_documented_components(doc_records)
        code_modules = self._extract_code_modules(source_root)
        dependency_result = DependencyGraphBuilder(self.root).build(target=source_root)
        repo_result = RepoAnalyzer(self.root).analyze(target=".")

        rows = self._build_matrix(documented_components, code_modules)
        findings = [*doc_findings]
        findings.extend(self._derive_findings(rows))
        if not findings:
            findings.append(Finding(id="ARCH_DRIFT_PASS", message="Architecture/code drift check completed without actionable drift findings.", severity=Severity.INFO))

        summary = _build_summary(rows, doc_records, dependency_result, repo_result)
        data = {
            "summary": summary,
            "architecture_docs": [record.to_dict() for record in doc_records],
            "documented_components": [component.to_dict() for component in documented_components[: self.config.max_components]],
            "code_modules": list(code_modules.values()),
            "matrix": [row.to_dict() for row in rows[: self.config.max_rows]],
            "repo_analyzer_summary": (repo_result.data or {}).get("summary", {}),
            "dependency_summary": (dependency_result.data or {}).get("summary", {}),
            "notes": [
                "FUNC-SPRINT-38 Architecture/code drift is read-only and heuristic.",
                "Documented components are extracted from Markdown tables and Mermaid nodes; matching is confidence-based.",
                "planned/future/disabled components are not blocking when code is absent.",
                "This detector does not infer runtime behavior and does not replace architecture review.",
                "No LLM, network, API, Git write, patch apply or document mutation is performed.",
            ],
        }
        return CommandResult(
            command="repo architecture-drift",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Architecture/code drift analysis completed in read-only mode.",
            data=data,
            findings=findings,
        )

    def _load_architecture_docs(self) -> tuple[list[ArchitectureDocRecord], str, list[Finding]]:
        records: list[ArchitectureDocRecord] = []
        text_parts: list[str] = []
        findings: list[Finding] = []
        for rel_path in self.config.architecture_docs:
            normalized = str(rel_path).replace("\\", "/")
            decision = PathGuard(self.root).evaluate(normalized, action="read")
            if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
                records.append(ArchitectureDocRecord(path=normalized, exists=False, size_bytes=0, components_total=0))
                findings.append(Finding(id=decision.rule_id, message=decision.reason, severity=Severity.BLOCK, path=decision.subject))
                continue
            path = self.root / normalized
            exists = path.exists() and path.is_file()
            raw_text = ""
            if exists:
                try:
                    raw_text = path.read_text(encoding="utf-8")
                    text_parts.append(raw_text)
                except UnicodeDecodeError:
                    findings.append(Finding(id="ARCH_DRIFT_DOC_UNREADABLE", message="Architecture document cannot be decoded as UTF-8.", severity=Severity.WARNING, path=normalized))
            else:
                findings.append(Finding(id="ARCH_DRIFT_ARCHITECTURE_DOC_MISSING", message="Architecture reference document is missing.", severity=Severity.WARNING, path=normalized))
            records.append(ArchitectureDocRecord(path=normalized, exists=exists, size_bytes=path.stat().st_size if exists else 0, text=raw_text))
        return records, "\n".join(text_parts), findings

    def _extract_documented_components(self, doc_records: list[ArchitectureDocRecord]) -> list[ArchitectureComponentRecord]:
        components: list[ArchitectureComponentRecord] = []
        seen: set[tuple[str, str, str]] = set()
        for doc in doc_records:
            if not doc.exists:
                continue
            for component in _extract_table_components(doc.path, doc.text):
                key = (component.normalized_name, component.documented_path or "", doc.path)
                if key not in seen:
                    seen.add(key)
                    components.append(component)
            for component in _extract_mermaid_components(doc.path, doc.text):
                key = (component.normalized_name, component.documented_path or "", doc.path)
                if key not in seen:
                    seen.add(key)
                    components.append(component)
            doc.components_total = sum(1 for component in components if component.source_doc == doc.path)
        return sorted(components, key=lambda item: (item.source_doc, item.name.lower()))

    def _extract_code_modules(self, source_root: Path) -> dict[str, dict[str, Any]]:
        modules: dict[str, dict[str, Any]] = {}
        dependency_result = DependencyGraphBuilder(self.root).build(target=source_root)
        nodes = (dependency_result.data or {}).get("nodes", [])
        for node in nodes:
            module = str(node.get("module", ""))
            path = str(node.get("path", ""))
            if not module.startswith("devpilot_core") or not path:
                continue
            parts = module.split(".")
            if len(parts) == 1:
                top = "devpilot_core"
            else:
                top = parts[1]
            if top in {"__main__"}:
                continue
            entry = modules.setdefault(
                top,
                {
                    "module": top,
                    "path": _module_path_for_top(source_root, top, self.root),
                    "package": "devpilot_core",
                    "nodes_total": 0,
                    "fan_in": 0,
                    "fan_out": 0,
                    "aliases": _module_aliases(top),
                },
            )
            entry["nodes_total"] += 1
            entry["fan_in"] = max(int(entry.get("fan_in", 0)), int(node.get("fan_in", 0) or 0))
            entry["fan_out"] = max(int(entry.get("fan_out", 0)), int(node.get("fan_out", 0) or 0))
        # Fallback when DependencyGraph is unavailable or empty.
        if not modules:
            for path in sorted(source_root.iterdir(), key=lambda item: item.name):
                if path.name in {"__pycache__", "__init__.py", "__main__.py"}:
                    continue
                if path.is_dir():
                    top = path.name
                elif path.is_file() and path.suffix == ".py":
                    top = path.stem
                else:
                    continue
                modules[top] = {"module": top, "path": path.relative_to(self.root).as_posix(), "package": "devpilot_core", "nodes_total": 1, "fan_in": 0, "fan_out": 0, "aliases": _module_aliases(top)}
        return dict(sorted(modules.items()))

    def _build_matrix(self, components: list[ArchitectureComponentRecord], code_modules: dict[str, dict[str, Any]]) -> list[ArchitectureDriftMatrixRow]:
        rows: list[ArchitectureDriftMatrixRow] = []
        matched_modules: set[str] = set()
        for component in components:
            match = _match_component(component, code_modules)
            if match["module"]:
                matched_modules.add(match["module"])
            drift_type = _drift_type_for_documented_component(component, match)
            rows.append(
                ArchitectureDriftMatrixRow(
                    documented_component=component.name,
                    documented_status=component.status,
                    source_doc=component.source_doc,
                    documented_path=component.documented_path,
                    code_module=match["module"],
                    code_path=match["path"],
                    match_type=match["match_type"],
                    confidence=match["confidence"],
                    drift_type=drift_type,
                    severity=_severity_for_row(component.status, drift_type),
                    rationale=match["rationale"],
                )
            )
        documented_index = _normalized_component_index(components)
        for module, info in code_modules.items():
            if module in matched_modules:
                continue
            if _normalize(module) in documented_index:
                continue
            rows.append(
                ArchitectureDriftMatrixRow(
                    documented_component=None,
                    documented_status=None,
                    source_doc=None,
                    documented_path=None,
                    code_module=module,
                    code_path=str(info.get("path")),
                    match_type="none",
                    confidence=0.0,
                    drift_type="doc_missing",
                    severity="warning",
                    rationale="Code module has no evident architecture-documentation match.",
                )
            )
        return sorted(rows, key=lambda row: (row.severity_order(), row.drift_type, row.documented_component or row.code_module or ""))

    def _derive_findings(self, rows: list[ArchitectureDriftMatrixRow]) -> list[Finding]:
        findings: list[Finding] = []
        for row in rows:
            if row.drift_type == "in_sync":
                continue
            finding_id = {
                "doc_missing": "ARCH_DRIFT_DOC_MISSING",
                "code_missing": "ARCH_DRIFT_CODE_MISSING",
                "name_mismatch": "ARCH_DRIFT_NAME_MISMATCH",
            }.get(row.drift_type, "ARCH_DRIFT_REVIEW_REQUIRED")
            severity = _severity_enum(row.severity)
            findings.append(
                Finding(
                    id=finding_id,
                    message=_finding_message(row),
                    severity=severity,
                    path=row.code_path or row.documented_path or row.source_doc,
                    metadata={
                        "documented_component": row.documented_component,
                        "documented_status": row.documented_status,
                        "code_module": row.code_module,
                        "match_type": row.match_type,
                        "confidence": row.confidence,
                        "drift_type": row.drift_type,
                    },
                )
            )
        return findings


@dataclass
class ArchitectureDocRecord:
    path: str
    exists: bool
    size_bytes: int
    components_total: int = 0
    text: str = field(default="", repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "exists": self.exists, "size_bytes": self.size_bytes, "components_total": self.components_total}


def _extract_table_components(source_doc: str, text: str) -> list[ArchitectureComponentRecord]:
    components: list[ArchitectureComponentRecord] = []
    lines = text.splitlines()
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        headerish = _normalize(" ".join(cells[:3]))
        if any(token in headerish for token in ["componente ruta estado", "component route status", "contenedor etapa", "nombre estado"]):
            continue
        first = _clean_markdown(cells[0])
        if not first or len(first) > 80:
            continue
        if _looks_like_non_component_row(first):
            continue
        joined = " | ".join(cells)
        status = _extract_status(joined)
        path = _extract_path(joined)
        if _normalize(first) in {_normalize(state) for state in IMPLEMENTED_STATES | ASPIRATIONAL_STATES | {"unknown"}}:
            continue
        if not status and not path and not _known_component_name(first):
            continue
        component = ArchitectureComponentRecord(
            name=first,
            normalized_name=_normalize_component_name(first),
            status=status or "unknown",
            source_doc=source_doc,
            source_type="table",
            documented_path=path,
            aliases=list(_component_aliases(first)),
        )
        components.append(component)
    return components


def _extract_mermaid_components(source_doc: str, text: str) -> list[ArchitectureComponentRecord]:
    components: list[ArchitectureComponentRecord] = []
    in_mermaid = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```mermaid"):
            in_mermaid = True
            continue
        if in_mermaid and stripped.startswith("```"):
            in_mermaid = False
            continue
        if not in_mermaid:
            continue
        for raw_label in _MERMAID_NODE_PATTERN.findall(line):
            label = _clean_mermaid_label(raw_label)
            if not label or label.startswith("(") or _looks_like_non_component_row(label):
                continue
            status = _extract_status(raw_label) or "unknown"
            name = _strip_status(label)
            if not name or len(name) > 80:
                continue
            if status == "unknown" and not _known_component_name(name):
                continue
            components.append(
                ArchitectureComponentRecord(
                    name=name,
                    normalized_name=_normalize_component_name(name),
                    status=status,
                    source_doc=source_doc,
                    source_type="mermaid",
                    documented_path=None,
                    aliases=list(_component_aliases(name)),
                )
            )
    return components


def _match_component(component: ArchitectureComponentRecord, code_modules: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if component.documented_path:
        normalized_path = component.documented_path.strip("./").replace("\\", "/")
        for module, info in code_modules.items():
            module_path = str(info.get("path", "")).strip("./")
            if normalized_path == module_path or normalized_path.startswith(module_path + "/") or module_path.startswith(normalized_path + "/"):
                return {"module": module, "path": info.get("path"), "match_type": "path", "confidence": 1.0, "rationale": "Documented path matches source module path."}
    normalized = component.normalized_name
    for module, info in code_modules.items():
        if normalized == _normalize_component_name(module):
            return {"module": module, "path": info.get("path"), "match_type": "exact", "confidence": 1.0, "rationale": "Component name exactly matches top-level module."}
    component_tokens = _tokens(normalized)
    best: dict[str, Any] = {"module": None, "path": None, "match_type": "none", "confidence": 0.0, "rationale": "No supported match found."}
    for module, info in code_modules.items():
        aliases = set(info.get("aliases", [])) | set(_module_aliases(module))
        comp_aliases = set(component.aliases) | set(_component_aliases(component.name))
        alias_hit = bool({_normalize(a) for a in aliases} & {_normalize(a) for a in comp_aliases})
        if alias_hit:
            score = 0.9
            match_type = "alias"
        else:
            module_tokens = _tokens(" ".join([module, *aliases]))
            score = _jaccard(component_tokens, module_tokens)
            match_type = "fuzzy"
        if score > best["confidence"]:
            best = {"module": module, "path": info.get("path"), "match_type": match_type, "confidence": round(score, 3), "rationale": f"Best {match_type} match between component and code module."}
    if best["confidence"] < 0.45:
        return {"module": None, "path": None, "match_type": "none", "confidence": 0.0, "rationale": "No match reached minimum confidence threshold."}
    return best


def _drift_type_for_documented_component(component: ArchitectureComponentRecord, match: dict[str, Any]) -> str:
    if not match["module"]:
        return "code_missing"
    if match["match_type"] in {"fuzzy"} or match["confidence"] < 0.75:
        return "name_mismatch"
    return "in_sync"


def _severity_for_row(status: str | None, drift_type: str) -> str:
    normalized_status = (status or "unknown").lower()
    if drift_type == "in_sync":
        return "info"
    if drift_type == "code_missing" and normalized_status in ASPIRATIONAL_STATES:
        return "info"
    return "warning"


def _severity_enum(value: str) -> Severity:
    return {"info": Severity.INFO, "warning": Severity.WARNING, "fail": Severity.FAIL, "block": Severity.BLOCK}.get(value, Severity.WARNING)


def _build_summary(rows: list[ArchitectureDriftMatrixRow], docs: list[ArchitectureDocRecord], dependency_result: CommandResult, repo_result: CommandResult) -> dict[str, Any]:
    drift_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}
    for row in rows:
        drift_counts[row.drift_type] = drift_counts.get(row.drift_type, 0) + 1
        severity_counts[row.severity] = severity_counts.get(row.severity, 0) + 1
    return {
        "components_documented_total": sum(1 for row in rows if row.documented_component),
        "code_modules_total": sum(1 for row in rows if row.code_module),
        "matrix_rows_total": len(rows),
        "drift_counts": drift_counts,
        "severity_counts": severity_counts,
        "architecture_docs_total": len(docs),
        "architecture_docs_existing": sum(1 for doc in docs if doc.exists),
        "dependency_nodes_total": (dependency_result.data or {}).get("summary", {}).get("nodes_total", 0),
        "repo_health_score": (repo_result.data or {}).get("summary", {}).get("health_score"),
        "drift_detected": any(row.drift_type != "in_sync" and row.severity != "info" for row in rows),
        "network_used": False,
        "external_api_used": False,
        "mutations_performed": False,
        "preliminary": True,
    }


def _empty_summary() -> dict[str, Any]:
    return {
        "components_documented_total": 0,
        "code_modules_total": 0,
        "matrix_rows_total": 0,
        "drift_counts": {},
        "severity_counts": {},
        "architecture_docs_total": 0,
        "architecture_docs_existing": 0,
        "drift_detected": False,
        "network_used": False,
        "external_api_used": False,
        "mutations_performed": False,
        "preliminary": True,
    }


def _finding_message(row: ArchitectureDriftMatrixRow) -> str:
    if row.drift_type == "doc_missing":
        return f"Code module has no evident architectural reference: {row.code_module}."
    if row.drift_type == "code_missing":
        return f"Documented component has no evident source module: {row.documented_component}."
    if row.drift_type == "name_mismatch":
        return f"Documented component and code module only match heuristically: {row.documented_component} -> {row.code_module}."
    return "Architecture/code drift row requires review."


def _normalized_component_index(components: list[ArchitectureComponentRecord]) -> set[str]:
    values: set[str] = set()
    for component in components:
        values.add(component.normalized_name)
        for alias in component.aliases:
            values.add(_normalize_component_name(alias))
    return values


def _extract_status(value: str) -> str | None:
    match = _STATE_PATTERN.search(value)
    return match.group(1).lower() if match else None


def _extract_path(value: str) -> str | None:
    match = _BACKTICK_PATH_PATTERN.search(value)
    if not match:
        return None
    raw = match.group(1).replace("\\", "/").strip()
    if "src/devpilot_core" not in raw:
        return None
    if raw.endswith("/*"):
        raw = raw[:-2]
    return raw.rstrip("/")


def _clean_markdown(value: str) -> str:
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"[`*_]", "", value)
    value = re.sub(r"\[[^\]]+\]\([^)]+\)", lambda m: m.group(0).split("]", 1)[0].lstrip("["), value)
    return " ".join(value.split()).strip()


def _clean_mermaid_label(value: str) -> str:
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", " ", value)
    return _clean_markdown(value)


def _strip_status(value: str) -> str:
    return _STATE_PATTERN.sub("", value).replace("  ", " ").strip(" -")


def _looks_like_non_component_row(value: str) -> bool:
    normalized = _normalize(value)
    return normalized in {
        "implemented initial", "implemented", "partial", "planned", "future", "disabled",
        "componente", "ruta principal", "estado", "responsabilidad", "limite explicito",
        "campo", "valor", "vista c4", "baseline representada", "cambios de implementacion",
        "tipo de vista", "estado uso en esta vista", "elemento valor esperado", "accion comando actual o futuro",
    } or normalized.startswith("no ")


def _known_component_name(value: str) -> bool:
    normalized = _normalize_component_name(value)
    return normalized in {_normalize_component_name(k) for k in KNOWN_COMPONENT_ALIASES} or normalized in {"frontmatter", "artifact", "checklist", "readiness", "pathguard", "secretguard", "costguard"}


def _component_aliases(name: str) -> tuple[str, ...]:
    normalized = _normalize_component_name(name)
    aliases = [normalized, normalized.replace(" ", ""), normalized.replace(" ", "_")]
    for module, module_aliases in KNOWN_COMPONENT_ALIASES.items():
        alias_norms = {_normalize_component_name(alias) for alias in module_aliases} | {_normalize_component_name(module)}
        if normalized in alias_norms:
            aliases.extend(module_aliases)
            aliases.append(module)
    return tuple(dict.fromkeys(alias for alias in aliases if alias))


def _module_aliases(module: str) -> tuple[str, ...]:
    aliases = list(KNOWN_COMPONENT_ALIASES.get(module, ()))
    aliases.extend([module, module.replace("_", " "), module.replace("_", "")])
    return tuple(dict.fromkeys(aliases))


def _normalize_component_name(value: str) -> str:
    return _normalize(_strip_status(_clean_markdown(value)))


def _normalize(value: str) -> str:
    value = value.lower().replace("_", " ").replace("/", " ").replace("-", " ")
    value = re.sub(r"[^a-z0-9áéíóúñü ]+", " ", value)
    return " ".join(value.split())


def _tokens(value: str) -> set[str]:
    return {token for token in _normalize(value).split() if token and token not in _STOP_WORDS}


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _module_path_for_top(source_root: Path, top: str, root: Path) -> str:
    directory = source_root / top
    if directory.exists():
        return directory.relative_to(root).as_posix()
    module_file = source_root / f"{top}.py"
    if module_file.exists():
        return module_file.relative_to(root).as_posix()
    return (source_root / top).relative_to(root).as_posix()
