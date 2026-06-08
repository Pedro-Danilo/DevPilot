from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.validators.artifact_profiles import ArtifactProfile, select_artifact_profile
from devpilot_core.validators.frontmatter import parse_frontmatter_file, validate_frontmatter_document


HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class MarkdownHeading:
    """One Markdown heading extracted from an engineering artifact."""

    level: int
    title: str
    normalized: str
    line_number: int


def normalize_heading(value: str) -> str:
    """Normalize a Markdown heading for profile matching.

    The normalizer intentionally ignores numbering and punctuation so headings
    like `## 1. Propósito` and `## Propósito` match the same rule.
    """

    value = value.strip().lower()
    value = re.sub(r"^\d+(?:\.\d+)*\s*[\.\-)]?\s*", "", value)
    value = re.sub(r"`", "", value)
    value = re.sub(r"[^\wáéíóúüñ+\-/ ]+", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def extract_headings(markdown_text: str) -> list[MarkdownHeading]:
    """Extract Markdown ATX headings from a document body.

    Fenced code blocks are ignored so operational examples such as PowerShell
    comments beginning with `#` are not misclassified as document headings.
    """

    headings: list[MarkdownHeading] = []
    inside_fenced_code = False
    for line_number, line in enumerate(markdown_text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            inside_fenced_code = not inside_fenced_code
            continue
        if inside_fenced_code:
            continue

        match = HEADING_PATTERN.match(line)
        if not match:
            continue
        marker, title = match.groups()
        headings.append(
            MarkdownHeading(
                level=len(marker),
                title=title.strip(),
                normalized=normalize_heading(title),
                line_number=line_number,
            )
        )
    return headings


def _display_path(path: Path, root: Path | None = None) -> str:
    """Return deterministic repository-style paths for evidence contracts."""

    if root is None:
        return str(path).replace("\\", "/")
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _contains_heading(headings: Iterable[MarkdownHeading], expected_fragment: str) -> bool:
    expected = normalize_heading(expected_fragment)
    return any(expected in heading.normalized for heading in headings)


def _status_from_metadata(metadata: dict[str, object]) -> str:
    return str(metadata.get("status", "")).strip().lower()


def _missing_severity(status: str) -> Severity:
    # Backlog rule: approved artifacts with missing minimum structure must be
    # reported as BLOCK rather than a simple FAIL.
    return Severity.BLOCK if status == "approved" else Severity.FAIL


def validate_artifact_file(
    path: Path,
    *,
    root: Path | None = None,
    strict: bool = False,
) -> CommandResult:
    """Validate one Markdown engineering artifact against its profile.

    The validator composes FUNC-SPRINT-02 frontmatter validation with
    FUNC-SPRINT-03 structural checks. It does not modify files.
    """

    path_str = _display_path(path, root)

    if not path.exists():
        finding = Finding(
            id="ARTIFACT_FILE_NOT_FOUND",
            message=f"File does not exist: {path}",
            severity=Severity.ERROR,
            path=path_str,
        )
        return CommandResult(
            command="validate-artifact",
            ok=False,
            exit_code=ExitCode.ERROR,
            message="Artifact validation could not run because file was not found.",
            data={"path": path_str, "strict": strict},
            findings=[finding],
        )

    if not path.is_file():
        finding = Finding(
            id="ARTIFACT_PATH_NOT_FILE",
            message=f"Path is not a file: {path}",
            severity=Severity.ERROR,
            path=path_str,
        )
        return CommandResult(
            command="validate-artifact",
            ok=False,
            exit_code=ExitCode.ERROR,
            message="Artifact validation could not run because path is not a file.",
            data={"path": path_str, "strict": strict},
            findings=[finding],
        )

    if path.suffix.lower() != ".md":
        finding = Finding(
            id="ARTIFACT_NOT_MARKDOWN",
            message="Artifact validator currently supports Markdown files only.",
            severity=Severity.ERROR,
            path=path_str,
            metadata={"suffix": path.suffix},
        )
        return CommandResult(
            command="validate-artifact",
            ok=False,
            exit_code=ExitCode.ERROR,
            message="Artifact validation could not run because file is not Markdown.",
            data={"path": path_str, "strict": strict},
            findings=[finding],
        )

    document = parse_frontmatter_file(path)
    profile = select_artifact_profile(path, root=root)
    frontmatter_result = validate_frontmatter_document(document, root=root, strict=strict)
    findings: list[Finding] = list(frontmatter_result.findings)

    status = _status_from_metadata(document.frontmatter)
    headings = extract_headings(document.body)
    h1_count = sum(1 for heading in headings if heading.level == 1)
    normalized_headings = [heading.normalized for heading in headings]

    if h1_count == 0:
        findings.append(
            Finding(
                id="ARTIFACT_H1_MISSING",
                message="Markdown artifact should include exactly one H1 title heading.",
                severity=_missing_severity(status),
                path=path_str,
            )
        )
    elif h1_count > 1:
        findings.append(
            Finding(
                id="ARTIFACT_MULTIPLE_H1",
                message="Markdown artifact should not include multiple H1 title headings.",
                severity=Severity.FAIL,
                path=path_str,
                metadata={"h1_count": h1_count},
            )
        )

    missing_required: list[str] = []
    for expected in profile.required_headings:
        if not _contains_heading(headings, expected):
            missing_required.append(expected)
            findings.append(
                Finding(
                    id="ARTIFACT_REQUIRED_SECTION_MISSING",
                    message=f"Required section is missing for profile '{profile.id}': {expected}",
                    severity=_missing_severity(status),
                    path=path_str,
                    metadata={"profile": profile.id, "section": expected},
                )
            )

    missing_recommended: list[str] = []
    for expected in profile.recommended_headings:
        if not _contains_heading(headings, expected):
            missing_recommended.append(expected)
            findings.append(
                Finding(
                    id="ARTIFACT_RECOMMENDED_SECTION_MISSING",
                    message=f"Recommended section is missing for profile '{profile.id}': {expected}",
                    severity=Severity.WARNING,
                    path=path_str,
                    metadata={"profile": profile.id, "section": expected},
                )
            )

    body_text = document.body.strip()
    if len(body_text) < 80:
        findings.append(
            Finding(
                id="ARTIFACT_BODY_TOO_SHORT",
                message="Artifact body is too short to be considered an engineering artifact.",
                severity=_missing_severity(status),
                path=path_str,
                metadata={"body_length": len(body_text)},
            )
        )

    exit_code = exit_code_for_findings(findings)
    ok = not any(finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} for finding in findings)

    return CommandResult(
        command="validate-artifact",
        ok=ok,
        exit_code=ExitCode.PASS if ok else exit_code,
        message="Artifact validation passed." if ok else "Artifact validation failed.",
        data={
            "path": path_str,
            "profile": {
                "id": profile.id,
                "description": profile.description,
            },
            "strict": strict,
            "status": status or None,
            "heading_count": len(headings),
            "h1_count": h1_count,
            "headings": [heading.title for heading in headings],
            "missing_required_sections": missing_required,
            "missing_recommended_sections": missing_recommended,
            "frontmatter_ok": frontmatter_result.ok,
        },
        findings=findings,
    )
