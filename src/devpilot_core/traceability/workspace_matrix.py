from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from devpilot_core.cli_models import Finding, Severity

REQUIREMENT_PATTERN = re.compile(r"(?<![A-Z0-9-])((?:FR|REQ)-[A-Z0-9]+(?:-[A-Z0-9]+)*)(?![A-Z0-9-])")
STORY_PATTERN = re.compile(r"(?<![A-Z0-9-])((?:US|STORY)-[A-Z0-9]+(?:-[A-Z0-9]+)*)(?![A-Z0-9-])")
RISK_PATTERN = re.compile(r"(?<![A-Z0-9-])((?:RISK|THREAT|TH)-[A-Z0-9]+(?:-[A-Z0-9]+)*)(?![A-Z0-9-])")
CONTROL_PATTERN = re.compile(r"(?<![A-Z0-9-])((?:CTRL|CONTROL|CTL)-[A-Z0-9]+(?:-[A-Z0-9]+)*)(?![A-Z0-9-])")
TEST_PATTERN = re.compile(r"(?<![A-Z0-9-])((?:TEST|TC)-[A-Z0-9]+(?:-[A-Z0-9]+)*)(?![A-Z0-9-])")
PYTEST_PATTERN = re.compile(r"\btest_[A-Za-z0-9_]+\b")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class MatrixSource:
    relative_path: str
    document_id: str | None
    line: int
    section: str | None
    excerpt: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "document_id": self.document_id,
            "line": self.line,
            "section": self.section,
            "excerpt": self.excerpt,
        }


@dataclass
class MatrixRecord:
    requirement_id: str
    stories: set[str]
    risks: set[str]
    controls: set[str]
    tests: set[str]
    sources: list[MatrixSource]

    def to_dict(self) -> dict[str, Any]:
        primary = self.sources[0].to_dict() if self.sources else None
        return {
            "requirement_id": self.requirement_id,
            "story_ids": sorted(self.stories),
            "risk_ids": sorted(self.risks),
            "control_ids": sorted(self.controls),
            "test_ids": sorted(self.tests),
            "sources": [item.to_dict() for item in self.sources],
            "navigation": primary,
            "coverage": {
                "story": bool(self.stories),
                "risk": bool(self.risks),
                "control": bool(self.controls),
                "test": bool(self.tests),
                "complete": bool(self.stories and self.risks and self.controls and self.tests),
            },
        }


class WorkspaceTraceabilityMatrixBuilder:
    """Build an explicit-only pre-code traceability matrix for UOC-003.

    Relationships are created only when identifiers coexist on the same source
    line/table row. The builder never uses semantic inference, network calls or
    LLMs, and never mutates workspace source files.
    """

    def __init__(self, workspace_root: Path, *, document_ids: dict[str, str] | None = None) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.document_ids = {str(k).replace("\\", "/"): v for k, v in (document_ids or {}).items()}

    def build(self, source_paths: Iterable[str]) -> tuple[dict[str, Any], list[Finding]]:
        records: dict[str, MatrixRecord] = {}
        source_files: list[str] = []
        findings: list[Finding] = []

        for relative in dict.fromkeys(str(item).replace("\\", "/") for item in source_paths):
            candidate = (self.workspace_root / PurePosixPath(relative)).resolve()
            try:
                candidate.relative_to(self.workspace_root)
            except ValueError:
                findings.append(Finding(
                    "UOC003_TRACEABILITY_PATH_ESCAPE_BLOCK",
                    "Traceability source escaped the active workspace root.",
                    Severity.BLOCK,
                    path=relative,
                ))
                continue
            if not candidate.is_file() or candidate.suffix.lower() not in {".md", ".txt"}:
                continue
            try:
                lines = candidate.read_text(encoding="utf-8-sig").splitlines()
            except (OSError, UnicodeDecodeError) as exc:
                findings.append(Finding(
                    "UOC003_TRACEABILITY_SOURCE_READ_BLOCK",
                    "Traceability source could not be read as UTF-8 text.",
                    Severity.BLOCK,
                    path=relative,
                    metadata={"exception_type": exc.__class__.__name__},
                ))
                continue
            source_files.append(relative)
            section: str | None = None
            for line_number, line in enumerate(lines, start=1):
                heading = HEADING_PATTERN.match(line)
                if heading:
                    section = heading.group(2).strip()
                requirements = set(REQUIREMENT_PATTERN.findall(line))
                if not requirements:
                    continue
                stories = set(STORY_PATTERN.findall(line))
                risks = set(RISK_PATTERN.findall(line))
                controls = set(CONTROL_PATTERN.findall(line))
                tests = set(TEST_PATTERN.findall(line)) | set(PYTEST_PATTERN.findall(line))
                excerpt = _compact(line)
                for requirement_id in sorted(requirements):
                    record = records.setdefault(
                        requirement_id,
                        MatrixRecord(requirement_id, set(), set(), set(), set(), []),
                    )
                    record.stories.update(stories)
                    record.risks.update(risks)
                    record.controls.update(controls)
                    record.tests.update(tests)
                    source = MatrixSource(
                        relative_path=relative,
                        document_id=self.document_ids.get(relative),
                        line=line_number,
                        section=section,
                        excerpt=excerpt,
                    )
                    if source not in record.sources:
                        record.sources.append(source)

        matrix = [records[key].to_dict() for key in sorted(records)]
        for item in matrix:
            missing = [key for key in ("story", "risk", "control", "test") if not item["coverage"][key]]
            if missing:
                navigation = item.get("navigation") or {}
                findings.append(Finding(
                    "UOC003_TRACEABILITY_REQUIREMENT_GAP",
                    f"Requirement {item['requirement_id']} lacks explicit links: {', '.join(missing)}.",
                    Severity.WARNING,
                    path=navigation.get("relative_path"),
                    metadata={
                        "requirement_id": item["requirement_id"],
                        "missing_link_types": missing,
                        "line": navigation.get("line"),
                        "section": navigation.get("section"),
                        "document_id": navigation.get("document_id"),
                    },
                ))

        complete_total = sum(1 for item in matrix if item["coverage"]["complete"])
        requirements_total = len(matrix)
        summary = {
            "requirements_total": requirements_total,
            "complete_requirements_total": complete_total,
            "coverage_percent": round((complete_total / requirements_total) * 100, 2) if requirements_total else 0.0,
            "source_paths_total": len(source_files),
            "findings_total": len(findings),
            "explicit_links_only": True,
            "semantic_inference_used": False,
            "preliminary": True,
            "read_only": True,
            "source_mutations_performed": False,
            "network_used": False,
            "external_api_used": False,
        }
        payload = {
            "schema_id": "devpilot.post_h_eval_002.uoc_003.workspace_traceability.v1",
            "summary": summary,
            "matrix": matrix,
            "source_paths": source_files,
            "notes": [
                "UOC-003 v1 links requirement, story, risk/control and test identifiers only when explicit local evidence coexists on a source line.",
                "Semantic inference and LLM-based matching are intentionally out of scope for this preliminary deterministic version.",
            ],
        }
        return payload, findings


def _compact(value: str, *, limit: int = 220) -> str:
    compact = " ".join(value.strip().split())
    return compact if len(compact) <= limit else f"{compact[: limit - 3]}..."
