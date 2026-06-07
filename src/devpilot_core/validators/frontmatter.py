from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings


REQUIRED_FRONTMATTER_FIELDS = ("title", "doc_id", "status", "version", "owner", "updated")
ALLOWED_STATUSES = ("draft", "reviewed", "approved", "deprecated")
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9_.-]+)?$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DOC_ID_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_.-]*$")


@dataclass(frozen=True)
class FrontmatterDocument:
    """Parsed Markdown document with extracted frontmatter metadata."""

    path: Path
    raw_text: str
    frontmatter: dict[str, Any] = field(default_factory=dict)
    body: str = ""
    has_frontmatter: bool = False


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    return _strip_quotes(value)


def parse_frontmatter_text(text: str, path: Path | None = None) -> FrontmatterDocument:
    """Parse a simple YAML-like frontmatter block from Markdown text.

    DevPilot intentionally keeps this parser dependency-free for FUNC-SPRINT-02.
    It supports the key-value metadata format used by the project's docs. It is
    not intended to be a complete YAML parser.
    """

    doc_path = path or Path("<memory>")
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return FrontmatterDocument(path=doc_path, raw_text=text, has_frontmatter=False, body=text)

    normalized = text.replace("\r\n", "\n")
    lines = normalized.split("\n")
    closing_index: int | None = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break

    if closing_index is None:
        return FrontmatterDocument(path=doc_path, raw_text=text, has_frontmatter=False, body=text)

    metadata: dict[str, Any] = {}
    for line_number, line in enumerate(lines[1:closing_index], start=2):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            metadata[f"__parse_error_line_{line_number}"] = stripped
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        if not key:
            metadata[f"__parse_error_line_{line_number}"] = stripped
            continue
        metadata[key] = _parse_scalar(value)

    body = "\n".join(lines[closing_index + 1 :])
    return FrontmatterDocument(
        path=doc_path,
        raw_text=text,
        frontmatter=metadata,
        body=body,
        has_frontmatter=True,
    )


def parse_frontmatter_file(path: Path) -> FrontmatterDocument:
    """Read and parse a Markdown file."""

    text = path.read_text(encoding="utf-8")
    return parse_frontmatter_text(text, path=path)


def _display_path(path: Path, root: Path | None = None) -> str:
    if root is None:
        return str(path)
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def validate_frontmatter_document(
    document: FrontmatterDocument,
    *,
    root: Path | None = None,
    strict: bool = False,
) -> CommandResult:
    """Validate frontmatter according to DevPilot's FUNC-SPRINT-02 rules."""

    path_str = _display_path(document.path, root)
    findings: list[Finding] = []

    if not document.has_frontmatter:
        findings.append(
            Finding(
                id="FRONTMATTER_MISSING",
                message="Markdown document does not start with a valid frontmatter block.",
                severity=Severity.FAIL,
                path=path_str,
            )
        )
        return CommandResult(
            command="validate-frontmatter",
            ok=False,
            exit_code=exit_code_for_findings(findings),
            message="Frontmatter validation failed.",
            data={
                "path": path_str,
                "has_frontmatter": False,
                "fields": {},
                "strict": strict,
            },
            findings=findings,
        )

    metadata = document.frontmatter

    for key in sorted(k for k in metadata if k.startswith("__parse_error_line_")):
        findings.append(
            Finding(
                id="FRONTMATTER_PARSE_WARNING",
                message=f"Unparsed frontmatter line: {metadata[key]}",
                severity=Severity.WARNING,
                path=path_str,
                metadata={"line_key": key},
            )
        )

    for field_name in REQUIRED_FRONTMATTER_FIELDS:
        value = metadata.get(field_name)
        if value is None or str(value).strip() == "":
            findings.append(
                Finding(
                    id="FRONTMATTER_REQUIRED_FIELD_MISSING",
                    message=f"Required frontmatter field is missing or empty: {field_name}",
                    severity=Severity.FAIL,
                    path=path_str,
                    metadata={"field": field_name},
                )
            )

    status = str(metadata.get("status", "")).strip().lower()
    if status and status not in ALLOWED_STATUSES:
        findings.append(
            Finding(
                id="FRONTMATTER_INVALID_STATUS",
                message=f"Invalid status '{status}'. Allowed values: {', '.join(ALLOWED_STATUSES)}.",
                severity=Severity.FAIL,
                path=path_str,
                metadata={"field": "status", "value": status},
            )
        )

    version = str(metadata.get("version", "")).strip()
    if version and not SEMVER_PATTERN.match(version):
        findings.append(
            Finding(
                id="FRONTMATTER_INVALID_VERSION",
                message="Version must follow SemVer-like format, for example 1.0.0.",
                severity=Severity.FAIL,
                path=path_str,
                metadata={"field": "version", "value": version},
            )
        )

    updated = str(metadata.get("updated", "")).strip()
    if updated and not DATE_PATTERN.match(updated):
        findings.append(
            Finding(
                id="FRONTMATTER_INVALID_UPDATED_DATE",
                message="Updated date must use YYYY-MM-DD format.",
                severity=Severity.FAIL,
                path=path_str,
                metadata={"field": "updated", "value": updated},
            )
        )

    doc_id = str(metadata.get("doc_id", "")).strip()
    if doc_id and not DOC_ID_PATTERN.match(doc_id):
        findings.append(
            Finding(
                id="FRONTMATTER_INVALID_DOC_ID",
                message="doc_id should use uppercase letters, digits, dots, hyphens or underscores.",
                severity=Severity.WARNING,
                path=path_str,
                metadata={"field": "doc_id", "value": doc_id},
            )
        )

    if status == "approved":
        approval = str(metadata.get("approval", "")).strip()
        if not approval:
            findings.append(
                Finding(
                    id="FRONTMATTER_APPROVED_WITHOUT_APPROVAL",
                    message="Approved documents should include an approval field.",
                    severity=Severity.FAIL if strict else Severity.WARNING,
                    path=path_str,
                    metadata={"field": "approval", "strict": strict},
                )
            )

    exit_code = exit_code_for_findings(findings)
    ok = exit_code == ExitCode.PASS or (
        exit_code == ExitCode.PASS and not findings
    )
    # Warnings do not fail the command.
    ok = not any(f.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} for f in findings)

    return CommandResult(
        command="validate-frontmatter",
        ok=ok,
        exit_code=ExitCode.PASS if ok else exit_code_for_findings(findings),
        message="Frontmatter validation passed." if ok else "Frontmatter validation failed.",
        data={
            "path": path_str,
            "has_frontmatter": document.has_frontmatter,
            "fields": {
                key: metadata.get(key)
                for key in REQUIRED_FRONTMATTER_FIELDS
                if key in metadata
            },
            "status": metadata.get("status"),
            "strict": strict,
        },
        findings=findings,
    )


def validate_frontmatter_file(path: Path, *, root: Path | None = None, strict: bool = False) -> CommandResult:
    """Validate a Markdown file frontmatter and return a CommandResult."""

    if not path.exists():
        finding = Finding(
            id="FRONTMATTER_FILE_NOT_FOUND",
            message=f"File does not exist: {path}",
            severity=Severity.ERROR,
            path=_display_path(path, root),
        )
        return CommandResult(
            command="validate-frontmatter",
            ok=False,
            exit_code=ExitCode.ERROR,
            message="Frontmatter validation could not run because file was not found.",
            data={"path": _display_path(path, root), "strict": strict},
            findings=[finding],
        )

    if not path.is_file():
        finding = Finding(
            id="FRONTMATTER_PATH_NOT_FILE",
            message=f"Path is not a file: {path}",
            severity=Severity.ERROR,
            path=_display_path(path, root),
        )
        return CommandResult(
            command="validate-frontmatter",
            ok=False,
            exit_code=ExitCode.ERROR,
            message="Frontmatter validation could not run because path is not a file.",
            data={"path": _display_path(path, root), "strict": strict},
            findings=[finding],
        )

    document = parse_frontmatter_file(path)
    return validate_frontmatter_document(document, root=root, strict=strict)
