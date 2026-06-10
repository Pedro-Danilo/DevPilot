from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings


DEFAULT_ARCHITECTURE_DOCS = (
    "docs/02_architecture/architecture_document.md",
    "docs/02_architecture/c4_container.md",
    "docs/02_architecture/c4_component.md",
)

IGNORED_TOP_LEVEL_FILES = {"__init__.py", "__main__.py"}
IGNORED_TOP_LEVEL_DIRS = {"__pycache__"}

MODULE_ALIASES: dict[str, tuple[str, ...]] = {
    "agents": ("agents", "agentruntime", "agent runtime", "documentationauditagent", "precode documentation agent"),
    "application": ("applicationservice", "application service", "applicationrequest", "applicationresponse", "internal_application_contract"),
    "cli": ("devpilot cli", " cli ", "cli.py"),
    "cli_models": ("cli_models", "commandresult", "finding", "exitcode"),
    "errors": ("devpiloterror", "errors.py", "error accionable"),
    "evals": ("eval harness", "evaluation harness", "evals"),
    "miasi": ("miasi", "agent registry", "tool registry", "policy matrix"),
    "modeling": ("modeladapter", "model adapter", "mockmodeladapter", "local llm", "external llm"),
    "observability": ("observability", "eventlogger", "jsonl", "traces"),
    "policy": ("policy engine", "pathguard", "secretguard", "costguard", "policy"),
    "refactor": ("refactor", "safe refactor planner", "safe refactor", "refactor plan"),
    "repo": ("repo", "gitadapter", "git adapter", "repoinventory", "repo inventory"),
    "reports": ("report engine", "reports", "evidence report", "json/markdown"),
    "review": ("review", "patch review", "code review", "patchengine", "patch review engine"),
    "schemas": ("schema validator", "schema registry", "schemas", "schema engine"),
    "standards": ("standards registry", "standards", "mipsoftware"),
    "store": ("localstore", "store", "sqlite", "persistence layer"),
    "traceability": ("traceability", "traceability engine", "traceability validator", "architecture drift"),
    "validation": ("validationgateway", "validation gateway", "validation engine"),
    "validators": ("validators", "frontmatter validator", "artifact validator", "checklist", "readiness"),
    "workspace": ("workspace manager", "workspace detector", "workspace"),
}


@dataclass(frozen=True)
class ArchitectureModuleRecord:
    """Documentation coverage record for one executable top-level module."""

    module_name: str
    path: str
    kind: str
    documented: bool
    matched_aliases: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_name": self.module_name,
            "path": self.path,
            "kind": self.kind,
            "documented": self.documented,
            "matched_aliases": list(self.matched_aliases),
        }


class ArchitectureDriftDetector:
    """Heuristic architecture/code drift detector for FUNC-SPRINT-27.

    This detector is intentionally conservative: it checks whether top-level
    DevPilot Core modules are mentioned in controlled architecture documents.
    It emits non-destructive findings and never mutates source or docs.
    """

    def __init__(self, root: Path, architecture_docs: Iterable[str | Path] | None = None) -> None:
        self.root = root.resolve()
        self.architecture_docs = tuple(str(path).replace("\\", "/") for path in (architecture_docs or DEFAULT_ARCHITECTURE_DOCS))

    def detect(self) -> CommandResult:
        src_root = self.root / "src" / "devpilot_core"
        if not src_root.exists():
            finding = Finding(
                id="ARCHITECTURE_DRIFT_SRC_ROOT_MISSING",
                message="DevPilot source root is missing; architecture/code drift cannot be evaluated.",
                severity=Severity.BLOCK,
                path="src/devpilot_core",
            )
            return CommandResult(
                command="traceability architecture-drift",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Architecture/code drift check blocked because source root is missing.",
                findings=[finding],
                data={"summary": _empty_summary()},
            )

        doc_text, doc_records, doc_findings = self._load_architecture_docs()
        module_records = self._module_records(src_root, doc_text)
        findings = [*doc_findings]
        for record in module_records:
            if not record.documented:
                findings.append(
                    Finding(
                        id="ARCHITECTURE_DRIFT_CODE_MODULE_UNDOCUMENTED",
                        message=f"Top-level DevPilot module is not explicitly represented in architecture docs: {record.module_name}.",
                        severity=Severity.WARNING,
                        path=record.path,
                        metadata={
                            "module_name": record.module_name,
                            "kind": record.kind,
                            "architecture_docs": self.architecture_docs,
                        },
                    )
                )

        undocumented = [record for record in module_records if not record.documented]
        summary = {
            "modules_total": len(module_records),
            "modules_documented": len(module_records) - len(undocumented),
            "modules_undocumented": len(undocumented),
            "architecture_docs_total": len(doc_records),
            "architecture_docs_existing": sum(1 for item in doc_records if item["exists"]),
            "findings_total": len(findings) + 1,
            "warnings_total": sum(1 for finding in findings if finding.severity == Severity.WARNING),
            "blocking_findings_total": sum(1 for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}),
            "drift_detected": bool(undocumented),
            "preliminary": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
        }
        findings.insert(
            0,
            Finding(
                id="ARCHITECTURE_DRIFT_CHECK_COMPLETED",
                message="Architecture/code drift check completed with non-destructive findings.",
                severity=Severity.INFO,
                metadata=summary,
            ),
        )
        exit_code = exit_code_for_findings(findings)
        return CommandResult(
            command="traceability architecture-drift",
            ok=exit_code == ExitCode.PASS,
            exit_code=exit_code,
            message="Architecture/code drift check completed.",
            data={
                "summary": summary,
                "modules": [record.to_dict() for record in module_records],
                "architecture_docs": doc_records,
                "notes": [
                    "FUNC-SPRINT-27 uses a heuristic module-vs-architecture-doc coverage check.",
                    "Findings are non-destructive and do not replace manual architecture review.",
                    "Minor naming differences may require future alias configuration.",
                ],
            },
            findings=findings,
        )

    def _load_architecture_docs(self) -> tuple[str, list[dict[str, Any]], list[Finding]]:
        texts: list[str] = []
        records: list[dict[str, Any]] = []
        findings: list[Finding] = []
        for relative in self.architecture_docs:
            path = self.root / relative
            exists = path.exists() and path.is_file()
            records.append({"path": relative, "exists": exists, "size_bytes": path.stat().st_size if exists else 0})
            if not exists:
                findings.append(
                    Finding(
                        id="ARCHITECTURE_DRIFT_ARCH_DOC_MISSING",
                        message=f"Architecture reference document is missing: {relative}.",
                        severity=Severity.WARNING,
                        path=relative,
                    )
                )
                continue
            try:
                texts.append(path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                findings.append(
                    Finding(
                        id="ARCHITECTURE_DRIFT_ARCH_DOC_UNREADABLE",
                        message=f"Architecture reference document cannot be decoded as UTF-8: {relative}.",
                        severity=Severity.WARNING,
                        path=relative,
                    )
                )
        return _normalize_text("\n".join(texts)), records, findings

    def _module_records(self, src_root: Path, doc_text: str) -> list[ArchitectureModuleRecord]:
        records: list[ArchitectureModuleRecord] = []
        for path in sorted(src_root.iterdir(), key=lambda item: item.name):
            if path.name in IGNORED_TOP_LEVEL_DIRS or path.name in IGNORED_TOP_LEVEL_FILES:
                continue
            if path.is_dir():
                module_name = path.name
                kind = "package"
            elif path.is_file() and path.suffix == ".py":
                module_name = path.stem
                kind = "module"
            else:
                continue
            relative = path.relative_to(self.root).as_posix()
            aliases = MODULE_ALIASES.get(module_name, (module_name.replace("_", " "), module_name))
            matched = tuple(alias for alias in aliases if _normalize_text(alias) in doc_text)
            records.append(
                ArchitectureModuleRecord(
                    module_name=module_name,
                    path=relative,
                    kind=kind,
                    documented=bool(matched),
                    matched_aliases=matched,
                )
            )
        return records


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().replace("`", " ").replace("_", " ").split())


def _empty_summary() -> dict[str, Any]:
    return {
        "modules_total": 0,
        "modules_documented": 0,
        "modules_undocumented": 0,
        "architecture_docs_total": 0,
        "architecture_docs_existing": 0,
        "findings_total": 0,
        "warnings_total": 0,
        "blocking_findings_total": 1,
        "drift_detected": False,
        "preliminary": True,
        "network_used": False,
        "external_api_used": False,
        "mutations_performed": False,
    }
