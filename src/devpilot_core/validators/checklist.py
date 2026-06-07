from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.validators.frontmatter import parse_frontmatter_file, validate_frontmatter_file


TABLE_SEPARATOR_PATTERN = re.compile(r"^\s*\|\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
BACKTICK_PATH_PATTERN = re.compile(r"`([^`]+)`")


@dataclass(frozen=True)
class ChecklistRow:
    """One normalized row extracted from a Markdown checklist table."""

    section: str
    values: dict[str, str]
    line_number: int

    @property
    def name(self) -> str:
        return self.values.get("bloque") or self.values.get("criterio") or self.values.get("id") or "checklist-row"

    @property
    def mandatory(self) -> bool:
        value = self.values.get("obligatorio", "").strip().lower()
        return value in {"sí", "si", "yes", "true", "1"}

    @property
    def status(self) -> str:
        return (self.values.get("estado") or self.values.get("resultado") or self.values.get("estado actual") or "").strip()

    @property
    def normalized_status(self) -> str:
        return self.status.strip().lower()

    @property
    def artifact_cell(self) -> str:
        return self.values.get("artefacto principal", "").strip()

    @property
    def artifact_path(self) -> str | None:
        match = BACKTICK_PATH_PATTERN.search(self.artifact_cell)
        if not match:
            return None
        return match.group(1).strip()

    def to_dict(self) -> dict[str, Any]:
        return {
            "section": self.section,
            "line_number": self.line_number,
            "name": self.name,
            "mandatory": self.mandatory,
            "status": self.status,
            "artifact_path": self.artifact_path,
            "values": self.values,
        }


@dataclass(frozen=True)
class ChecklistDocument:
    """Parsed pre-code checklist document."""

    path: Path
    rows: tuple[ChecklistRow, ...]


def _normalize_header(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"`", "", value)
    value = re.sub(r"\s+", " ", value)
    return value


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def parse_checklist_markdown(path: Path) -> ChecklistDocument:
    """Parse mandatory rows from the DevPilot pre-code checklist.

    The parser is intentionally dependency-free and focused on the Markdown
    tables used by `docs/checklists/checklist_pre_code.md`. It is not a full
    Markdown parser; it extracts table rows with headers and keeps the section
    heading active at the moment each row appears.
    """

    text = path.read_text(encoding="utf-8")
    rows: list[ChecklistRow] = []
    active_section = ""
    active_headers: list[str] | None = None
    waiting_separator = False

    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("## "):
            active_section = stripped.lstrip("#").strip()
            active_headers = None
            waiting_separator = False
            continue

        if not stripped.startswith("|"):
            active_headers = None
            waiting_separator = False
            continue

        if TABLE_SEPARATOR_PATTERN.match(stripped):
            if waiting_separator:
                waiting_separator = False
            continue

        cells = _split_table_row(stripped)
        normalized_cells = [_normalize_header(cell) for cell in cells]

        if active_headers is None:
            active_headers = normalized_cells
            waiting_separator = True
            continue

        if waiting_separator:
            # A malformed table without separator is treated leniently by
            # resetting headers. The validator will fail if no rows are found.
            waiting_separator = False

        if len(cells) != len(active_headers):
            continue

        values = {header: cell for header, cell in zip(active_headers, cells)}
        rows.append(ChecklistRow(section=active_section, values=values, line_number=line_number))

    return ChecklistDocument(path=path, rows=tuple(rows))


def _display_path(path: Path, root: Path | None = None) -> str:
    if root is None:
        return str(path)
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _path_status(root: Path, artifact_path: str) -> dict[str, Any]:
    normalized = artifact_path.replace("\\", "/")
    candidate = root / normalized
    if normalized.endswith("/"):
        exists = candidate.exists() and candidate.is_dir()
        size_bytes = 0
        markdown_files = len(list(candidate.glob("*.md"))) if exists else 0
        return {
            "path": normalized,
            "exists": exists,
            "kind": "directory",
            "size_bytes": size_bytes,
            "markdown_files": markdown_files,
        }

    exists = candidate.exists() and candidate.is_file()
    return {
        "path": normalized,
        "exists": exists,
        "kind": "file",
        "size_bytes": candidate.stat().st_size if exists else 0,
        "markdown_files": None,
    }


def validate_precode_checklist(
    root: Path,
    *,
    checklist_path: str = "docs/checklists/checklist_pre_code.md",
    strict: bool = True,
) -> CommandResult:
    """Evaluate the pre-code checklist as an executable local gate."""

    path = root / checklist_path
    findings: list[Finding] = []

    if not path.exists():
        finding = Finding(
            id="CHECKLIST_FILE_MISSING",
            message=f"Pre-code checklist file is missing: {checklist_path}",
            severity=Severity.BLOCK,
            path=checklist_path,
        )
        return CommandResult(
            command="checklist-pre-code",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message="Pre-code checklist gate blocked.",
            data={"checklist_path": checklist_path, "checks": [], "summary": {"total": 0, "mandatory": 0}},
            findings=[finding],
        )

    checklist_frontmatter = validate_frontmatter_file(path, root=root, strict=strict)
    findings.extend(checklist_frontmatter.findings)

    document = parse_checklist_markdown(path)
    checks: list[dict[str, Any]] = []

    if not document.rows:
        findings.append(
            Finding(
                id="CHECKLIST_NO_ROWS_FOUND",
                message="No checklist table rows were found.",
                severity=Severity.BLOCK,
                path=checklist_path,
            )
        )

    mandatory_rows = [row for row in document.rows if row.mandatory]
    if not mandatory_rows:
        findings.append(
            Finding(
                id="CHECKLIST_NO_MANDATORY_ROWS",
                message="No mandatory checklist rows were found.",
                severity=Severity.BLOCK,
                path=checklist_path,
            )
        )

    for row in document.rows:
        artifact_state: dict[str, Any] | None = None
        artifact_frontmatter_status: str | None = None

        if row.mandatory and row.normalized_status != "pass":
            findings.append(
                Finding(
                    id="CHECKLIST_MANDATORY_ROW_NOT_PASS",
                    message=f"Mandatory checklist row is not PASS: {row.name}",
                    severity=Severity.BLOCK,
                    path=checklist_path,
                    metadata={"line_number": row.line_number, "status": row.status, "section": row.section},
                )
            )

        artifact_path = row.artifact_path
        if artifact_path:
            artifact_state = _path_status(root, artifact_path)
            if row.mandatory and not artifact_state["exists"]:
                findings.append(
                    Finding(
                        id="CHECKLIST_REQUIRED_ARTIFACT_MISSING",
                        message=f"Mandatory checklist artifact is missing: {artifact_path}",
                        severity=Severity.BLOCK,
                        path=artifact_path,
                        metadata={"line_number": row.line_number, "section": row.section},
                    )
                )
            elif row.mandatory and artifact_state["kind"] == "directory" and artifact_state["markdown_files"] == 0:
                findings.append(
                    Finding(
                        id="CHECKLIST_REQUIRED_DIRECTORY_EMPTY",
                        message=f"Mandatory checklist directory has no Markdown evidence: {artifact_path}",
                        severity=Severity.BLOCK,
                        path=artifact_path,
                        metadata={"line_number": row.line_number, "section": row.section},
                    )
                )
            elif row.mandatory and artifact_state["kind"] == "file":
                candidate = root / artifact_path
                if candidate.suffix.lower() == ".md" and candidate.exists():
                    try:
                        parsed = parse_frontmatter_file(candidate)
                        artifact_frontmatter_status = str(parsed.frontmatter.get("status", "") or "")
                        if artifact_frontmatter_status.strip().lower() != "approved":
                            findings.append(
                                Finding(
                                    id="CHECKLIST_REQUIRED_ARTIFACT_NOT_APPROVED",
                                    message=f"Mandatory artifact is not approved: {artifact_path}",
                                    severity=Severity.BLOCK,
                                    path=artifact_path,
                                    metadata={"status": artifact_frontmatter_status, "line_number": row.line_number},
                                )
                            )
                    except Exception as exc:
                        findings.append(
                            Finding(
                                id="CHECKLIST_ARTIFACT_FRONTMATTER_READ_ERROR",
                                message=f"Could not read artifact frontmatter: {artifact_path}",
                                severity=Severity.ERROR,
                                path=artifact_path,
                                metadata={"error": str(exc)},
                            )
                        )

        checks.append(
            {
                **row.to_dict(),
                "artifact_state": artifact_state,
                "artifact_frontmatter_status": artifact_frontmatter_status,
            }
        )

    exit_code = exit_code_for_findings(findings)
    ok = not any(finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} for finding in findings)

    mandatory_artifact_checks = [check for check in checks if check["mandatory"] and check["artifact_path"]]
    present_mandatory_artifacts = [
        check
        for check in mandatory_artifact_checks
        if check.get("artifact_state") and check["artifact_state"].get("exists")
    ]

    return CommandResult(
        command="checklist-pre-code",
        ok=ok,
        exit_code=ExitCode.PASS if ok else exit_code,
        message="Pre-code checklist gate passed." if ok else "Pre-code checklist gate blocked.",
        data={
            "checklist_path": checklist_path,
            "strict": strict,
            "frontmatter_ok": checklist_frontmatter.ok,
            "checks": checks,
            "summary": {
                "total_rows": len(checks),
                "mandatory_rows": len(mandatory_rows),
                "mandatory_artifacts_total": len(mandatory_artifact_checks),
                "mandatory_artifacts_present": len(present_mandatory_artifacts),
                "pass_rows": sum(1 for check in checks if str(check["status"]).strip().lower() == "pass"),
            },
        },
        findings=findings,
    )
