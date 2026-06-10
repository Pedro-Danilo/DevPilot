from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from devpilot_core.cli_models import Finding, Severity
from devpilot_core.traceability.models import TraceLink

REQUIREMENT_PREFIXES = ("FR", "REQ")
STRICT_TRACE_ID_PATTERN = re.compile(r"(?<![A-Z0-9])(?P<id>(?P<prefix>FR|REQ|US|AC|TEST|ADR)-[A-Z0-9]+(?:-[A-Z0-9]+)*)(?![A-Z0-9-])")
TEST_NAME_PATTERN = re.compile(r"`(?P<name>test_[A-Za-z0-9_]+)`")
PYTEST_PATTERN = re.compile(r"`?(pytest\s+-q)`?", re.IGNORECASE)


@dataclass(frozen=True)
class RequirementTraceRecord:
    """Coverage state for one requirement-like entity.

    Sprint 26 keeps this record intentionally explicit: it stores only links and
    evidence found in controlled SDLC documents. It does not infer semantic
    relations from prose beyond table rows that contain traceability IDs.
    """

    requirement_id: str
    level: str = "unknown"
    source_documents: tuple[str, ...] = field(default_factory=tuple)
    acceptance_criteria: tuple[str, ...] = field(default_factory=tuple)
    test_evidence: tuple[str, ...] = field(default_factory=tuple)
    story_ids: tuple[str, ...] = field(default_factory=tuple)
    use_case_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "level": self.level,
            "source_documents": list(self.source_documents),
            "acceptance_criteria": list(self.acceptance_criteria),
            "test_evidence": list(self.test_evidence),
            "story_ids": list(self.story_ids),
            "use_case_ids": list(self.use_case_ids),
            "covered_by_acceptance": bool(self.acceptance_criteria),
            "covered_by_test_or_eval": bool(self.test_evidence),
            "covered_by_source_document": bool(self.source_documents),
        }


@dataclass(frozen=True)
class TraceabilityCoverage:
    """Deterministic coverage report for explicit traceability evidence."""

    requirement_records: tuple[RequirementTraceRecord, ...]
    acceptance_criteria_total: int
    acceptance_criteria_with_requirement: int
    links: tuple[TraceLink, ...]
    gaps: tuple[Finding, ...]
    preliminary: bool = True

    def summary(self) -> dict[str, Any]:
        requirements_total = len(self.requirement_records)
        req_with_ac = sum(1 for record in self.requirement_records if record.acceptance_criteria)
        req_with_test = sum(1 for record in self.requirement_records if record.test_evidence)
        req_with_doc = sum(1 for record in self.requirement_records if record.source_documents)
        return {
            "requirements_total": requirements_total,
            "requirements_with_acceptance_criteria": req_with_ac,
            "requirements_without_acceptance_criteria": requirements_total - req_with_ac,
            "requirements_with_test_or_eval_evidence": req_with_test,
            "requirements_without_test_or_eval_evidence": requirements_total - req_with_test,
            "requirements_with_source_document": req_with_doc,
            "requirements_without_source_document": requirements_total - req_with_doc,
            "acceptance_criteria_total": self.acceptance_criteria_total,
            "acceptance_criteria_with_requirement": self.acceptance_criteria_with_requirement,
            "acceptance_criteria_without_requirement": self.acceptance_criteria_total - self.acceptance_criteria_with_requirement,
            "links_total": len(self.links),
            "gaps_total": len(self.gaps),
            "warnings_total": sum(1 for gap in self.gaps if gap.severity == Severity.WARNING),
            "blocking_findings_total": sum(1 for gap in self.gaps if gap.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}),
            "coverage_percentages": {
                "requirements_acceptance_criteria": _percent(req_with_ac, requirements_total),
                "requirements_test_or_eval": _percent(req_with_test, requirements_total),
                "requirements_source_document": _percent(req_with_doc, requirements_total),
                "acceptance_criteria_requirement": _percent(self.acceptance_criteria_with_requirement, self.acceptance_criteria_total),
            },
            "preliminary": self.preliminary,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary(),
            "requirements": [record.to_dict() for record in self.requirement_records],
            "links": [link.to_dict() for link in self.links],
            "gaps": [gap.to_dict() for gap in self.gaps],
            "notes": [
                "FUNC-SPRINT-26 computes explicit coverage from controlled SDLC documents.",
                "Gaps are warnings in this first engine version; future sprints may make severity configurable.",
            ],
        }


def build_coverage(root: Path, source_paths: Iterable[str]) -> TraceabilityCoverage:
    """Build explicit Req→AC, Req→Test/Eval and Req→Doc coverage.

    The function intentionally accepts root-relative source paths from the
    extractor. It parses only local Markdown/JSON text and never mutates files.
    """

    source_paths = tuple(dict.fromkeys(str(path).replace("\\", "/") for path in source_paths))
    requirement_ids: set[str] = set()
    acceptance_ids: set[str] = set()
    ac_to_req: dict[str, set[str]] = {}
    req_to_ac: dict[str, set[str]] = {}
    req_to_test: dict[str, set[str]] = {}
    req_to_doc: dict[str, set[str]] = {}
    req_to_story: dict[str, set[str]] = {}
    req_to_uc: dict[str, set[str]] = {}
    req_level: dict[str, str] = {}
    links: list[TraceLink] = []

    for relative in source_paths:
        path = root / relative
        if not path.exists() or not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            ids = _ids_by_prefix(line)
            reqs = sorted(ids.get("FR", set()) | ids.get("REQ", set()))
            acs = sorted(ids.get("AC", set()))
            stories = sorted(ids.get("US", set()))
            tests = sorted(ids.get("TEST", set()))
            evidence = _test_evidence_from_line(line, tests=tests)
            if not reqs and not acs:
                continue

            cells = _split_markdown_row(line)
            level = _row_level(cells)
            if acs:
                acceptance_ids.update(acs)
            if reqs:
                requirement_ids.update(reqs)
                for req in reqs:
                    req_to_doc.setdefault(req, set()).add(relative)
                    if level != "unknown":
                        req_level.setdefault(req, level)
                    if stories:
                        req_to_story.setdefault(req, set()).update(stories)
                    for uc_id in _extract_uc_ids(line):
                        req_to_uc.setdefault(req, set()).add(uc_id)

            for req in reqs:
                for ac in acs:
                    req_to_ac.setdefault(req, set()).add(ac)
                    ac_to_req.setdefault(ac, set()).add(req)
                    links.append(
                        TraceLink(
                            source_entity_id=req,
                            target_entity_id=ac,
                            link_type="requirement_to_acceptance_criterion",
                            source_path=relative,
                            evidence=_compact(line),
                            explicit=True,
                        )
                    )
                for item in evidence:
                    req_to_test.setdefault(req, set()).add(item)
                    links.append(
                        TraceLink(
                            source_entity_id=req,
                            target_entity_id=item,
                            link_type="requirement_to_test_or_eval_evidence",
                            source_path=relative,
                            evidence=_compact(line),
                            explicit=True,
                        )
                    )

    requirement_records: list[RequirementTraceRecord] = []
    for req in sorted(_valid_requirement_ids(requirement_ids)):
        requirement_records.append(
            RequirementTraceRecord(
                requirement_id=req,
                level=req_level.get(req, _infer_level(req)),
                source_documents=tuple(sorted(req_to_doc.get(req, set()))),
                acceptance_criteria=tuple(sorted(req_to_ac.get(req, set()))),
                test_evidence=tuple(sorted(req_to_test.get(req, set()))),
                story_ids=tuple(sorted(req_to_story.get(req, set()))),
                use_case_ids=tuple(sorted(req_to_uc.get(req, set()))),
            )
        )

    gaps: list[Finding] = []
    for record in requirement_records:
        if not record.acceptance_criteria:
            gaps.append(
                Finding(
                    id="TRACEABILITY_REQUIREMENT_WITHOUT_ACCEPTANCE_CRITERIA",
                    message=f"Requirement has no explicit acceptance criterion: {record.requirement_id}.",
                    severity=Severity.WARNING,
                    metadata={"requirement_id": record.requirement_id, "level": record.level},
                )
            )
        if _test_expected_for_level(record.level) and not record.test_evidence:
            gaps.append(
                Finding(
                    id="TRACEABILITY_REQUIREMENT_WITHOUT_TEST_EVIDENCE",
                    message=f"Requirement has no explicit test/eval evidence: {record.requirement_id}.",
                    severity=Severity.WARNING,
                    metadata={"requirement_id": record.requirement_id, "level": record.level},
                )
            )
        if not record.source_documents:
            gaps.append(
                Finding(
                    id="TRACEABILITY_REQUIREMENT_WITHOUT_SOURCE_DOCUMENT",
                    message=f"Requirement has no source document evidence: {record.requirement_id}.",
                    severity=Severity.WARNING,
                    metadata={"requirement_id": record.requirement_id, "level": record.level},
                )
            )

    for ac in sorted(acceptance_ids):
        if not ac_to_req.get(ac):
            gaps.append(
                Finding(
                    id="TRACEABILITY_ACCEPTANCE_CRITERION_WITHOUT_REQUIREMENT",
                    message=f"Acceptance criterion has no explicit requirement: {ac}.",
                    severity=Severity.WARNING,
                    metadata={"acceptance_criterion_id": ac},
                )
            )

    return TraceabilityCoverage(
        requirement_records=tuple(requirement_records),
        acceptance_criteria_total=len(acceptance_ids),
        acceptance_criteria_with_requirement=sum(1 for ac in acceptance_ids if ac_to_req.get(ac)),
        links=tuple(links),
        gaps=tuple(gaps),
        preliminary=True,
    )


def _ids_by_prefix(line: str) -> dict[str, set[str]]:
    ids: dict[str, set[str]] = {}
    for match in STRICT_TRACE_ID_PATTERN.finditer(line):
        ids.setdefault(match.group("prefix"), set()).add(match.group("id"))
    return ids


def _extract_uc_ids(line: str) -> set[str]:
    return set(re.findall(r"(?<![A-Z0-9])(UC-[A-Z0-9]+(?:-[A-Z0-9]+)*)(?![A-Z0-9-])", line))


def _test_evidence_from_line(line: str, *, tests: list[str]) -> set[str]:
    evidence = set(tests)
    evidence.update(match.group("name") for match in TEST_NAME_PATTERN.finditer(line))
    evidence.update(match.group(1) for match in PYTEST_PATTERN.finditer(line))
    cells = _split_markdown_row(line)
    if cells:
        for cell in cells:
            normalized = cell.strip().strip("`")
            if not normalized or normalized.lower().startswith("n/a"):
                continue
            lower = normalized.lower()
            if "test" in lower or "pytest" in lower or "eval" in lower or "report" in lower or "schema" in lower or "checklist" in lower or "evidence" in lower or "evidencia" in lower:
                evidence.add(normalized)
    return {_compact(item, limit=120) for item in evidence if item.strip()}


def _split_markdown_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    if cells and all(set(cell) <= {"-", ":", " "} for cell in cells):
        return []
    return cells


def _row_level(cells: list[str]) -> str:
    if not cells:
        return "unknown"
    for cell in reversed(cells):
        normalized = cell.strip()
        if normalized in {"MVP", "MVP+", "Post-MVP"}:
            return normalized
    return "unknown"


def _valid_requirement_ids(ids: set[str]) -> set[str]:
    # Filter frontmatter/doc-id fragments such as REQ-004. Functional
    # requirements are the primary Sprint 26 coverage target in DevPilot docs.
    return {item for item in ids if item.startswith("FR-") or re.match(r"REQ-[A-Z]+-", item)}


def _infer_level(requirement_id: str) -> str:
    if "-MVP-" in requirement_id:
        return "MVP"
    if "-PLUS-" in requirement_id:
        return "MVP+"
    if "-POST-" in requirement_id:
        return "Post-MVP"
    return "unknown"


def _test_expected_for_level(level: str) -> bool:
    return level in {"MVP", "MVP+", "unknown"}


def _percent(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def _compact(text: str, *, limit: int = 180) -> str:
    compact = " ".join(str(text).strip().split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."
