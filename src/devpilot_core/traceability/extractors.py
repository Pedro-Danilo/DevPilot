from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.traceability.models import (
    PREFIX_TO_ENTITY_TYPE,
    InvalidTraceToken,
    TraceEntity,
    TraceGraph,
)

STRICT_ID_PATTERN = re.compile(r"(?<![A-Z0-9])(?P<id>(?P<prefix>FR|REQ|US|AC|TEST|ADR)-[A-Z0-9]+(?:-[A-Z0-9]+)*)(?![A-Z0-9-])")
LOOSE_ID_PATTERN = re.compile(r"(?<![A-Za-z0-9])(?P<id>(?P<prefix>FR|REQ|US|AC|TEST|ADR)-[A-Za-z0-9_.-]+)")
TRAILING_PUNCTUATION = ".,;:)]}\"'`"
DEFAULT_TEXT_EXTENSIONS = {".md", ".json"}


class MarkdownTraceabilityExtractor:
    """Conservative local extractor for SDLC traceability IDs.

    The extractor reads local Markdown/JSON text only and detects the exact ID
    families declared for FUNC-SPRINT-25. It does not infer links, ownership,
    coverage or semantic relationships.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def scan(self, *, targets: Iterable[str | Path] | None = None) -> CommandResult:
        """Scan configured targets and return a normalized CommandResult."""

        target_paths = self._resolve_targets(targets)
        findings: list[Finding] = []
        if not target_paths:
            return CommandResult(
                command="traceability scan",
                ok=False,
                exit_code=ExitCode.FAIL,
                message="Traceability scan found no readable source files.",
                data={
                    "summary": {
                        "entities_total": 0,
                        "unique_entities_total": 0,
                        "links_total": 0,
                        "invalid_tokens_total": 0,
                        "duplicate_entity_ids_total": 0,
                        "source_paths_total": 0,
                        "preliminary": True,
                        "inferred_links": False,
                    },
                    "source_paths": [],
                    "entities": [],
                    "links": [],
                    "invalid_tokens": [],
                    "duplicate_entity_ids": {},
                },
                findings=[
                    Finding(
                        id="TRACEABILITY_SCAN_NO_SOURCES",
                        message="No traceability source files were found for the requested scan targets.",
                        severity=Severity.FAIL,
                    )
                ],
            )

        entities: list[TraceEntity] = []
        invalid_tokens: list[InvalidTraceToken] = []
        for path in target_paths:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                findings.append(
                    Finding(
                        id="TRACEABILITY_SOURCE_UNREADABLE",
                        message="Source file could not be read as UTF-8 and was skipped.",
                        severity=Severity.WARNING,
                        path=self._display_path(path),
                    )
                )
                continue
            file_entities, file_invalid = self.extract_from_text(text, source_path=self._display_path(path))
            entities.extend(file_entities)
            invalid_tokens.extend(file_invalid)

        duplicate_ids = self._duplicate_entities(entities)
        findings.extend(self._build_findings(entities, invalid_tokens, duplicate_ids))
        graph = TraceGraph(
            entities=entities,
            links=[],
            invalid_tokens=invalid_tokens,
            duplicate_entity_ids=duplicate_ids,
            source_paths=[self._display_path(path) for path in target_paths],
            preliminary=True,
        )
        data = graph.to_dict()
        data["scope"] = "default" if targets is None else "custom"
        data["patterns"] = {
            "strict_id_pattern": STRICT_ID_PATTERN.pattern,
            "loose_id_pattern": LOOSE_ID_PATTERN.pattern,
        }
        data["extractor"] = {
            "name": "MarkdownTraceabilityExtractor",
            "sprint": "FUNC-SPRINT-25",
            "local_only": True,
            "mutations_performed": False,
        }
        return CommandResult(
            command="traceability scan",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Traceability scan completed.",
            data=data,
            findings=findings,
        )

    def extract_from_text(self, text: str, *, source_path: str) -> tuple[list[TraceEntity], list[InvalidTraceToken]]:
        """Extract valid entities and malformed ID-like tokens from text."""

        entities: list[TraceEntity] = []
        invalid_tokens: list[InvalidTraceToken] = []
        seen_valid_spans: set[tuple[int, int]] = set()
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in STRICT_ID_PATTERN.finditer(line):
                entity_id = match.group("id")
                prefix = match.group("prefix")
                entities.append(
                    TraceEntity(
                        entity_id=entity_id,
                        raw_id=match.group("id"),
                        entity_type=PREFIX_TO_ENTITY_TYPE[prefix],
                        source_path=source_path,
                        line=line_number,
                        column=match.start("id") + 1,
                        context=_compact_context(line),
                    )
                )
                seen_valid_spans.add((line_number, match.start("id"), match.end("id")))

            for loose_match in LOOSE_ID_PATTERN.finditer(line):
                loose_start = loose_match.start("id")
                loose_end = loose_match.end("id")
                if any(line_number == span_line and loose_start >= span_start and loose_start < span_end for span_line, span_start, span_end in seen_valid_spans):
                    continue
                raw_id = loose_match.group("id")
                normalized = raw_id.rstrip(TRAILING_PUNCTUATION)
                if STRICT_ID_PATTERN.fullmatch(normalized):
                    continue
                invalid_tokens.append(
                    InvalidTraceToken(
                        raw_id=raw_id,
                        normalized_candidate=normalized,
                        source_path=source_path,
                        line=line_number,
                        column=loose_start + 1,
                        reason="ID-like token does not match the conservative uppercase DevPilot traceability ID pattern.",
                        context=_compact_context(line),
                    )
                )
        return entities, invalid_tokens

    def _resolve_targets(self, targets: Iterable[str | Path] | None) -> list[Path]:
        if targets is not None:
            resolved: list[Path] = []
            for target in targets:
                candidate = self._resolve_inside_root(target)
                resolved.extend(self._expand_target(candidate))
            return sorted(set(resolved), key=lambda path: self._display_path(path))
        return sorted(set(self._default_sources()), key=lambda path: self._display_path(path))

    def _default_sources(self) -> list[Path]:
        sources: list[Path] = []
        explicit_files = [
            "docs/01_requirements/requirements_specification.md",
            "docs/01_requirements/acceptance_criteria.md",
            "docs/01_requirements/use_cases.md",
            "docs/01_requirements/traceability_matrix.md",
            "docs/04_quality/test_strategy.md",
        ]
        for relative in explicit_files:
            path = self.root / relative
            if path.exists() and path.is_file():
                sources.append(path)
        adr_dir = self.root / "docs/02_architecture/adrs"
        if adr_dir.exists():
            sources.extend(sorted(adr_dir.glob("*.md")))
        docs_dir = self.root / "docs"
        sources.extend(sorted(docs_dir.glob("functional_sprint_*_manifest.json")))
        return [path for path in sources if path.is_file() and path.suffix.lower() in DEFAULT_TEXT_EXTENSIONS]

    def _expand_target(self, target: Path) -> list[Path]:
        if target.is_file() and target.suffix.lower() in DEFAULT_TEXT_EXTENSIONS:
            return [target]
        if target.is_dir():
            return [path for path in target.rglob("*") if path.is_file() and path.suffix.lower() in DEFAULT_TEXT_EXTENSIONS]
        return []

    def _resolve_inside_root(self, path: str | Path) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("Traceability scan targets must remain inside the DevPilot project root.") from exc
        return resolved

    def _display_path(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.root)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")

    def _duplicate_entities(self, entities: list[TraceEntity]) -> dict[str, list[dict[str, object]]]:
        occurrences: dict[str, list[TraceEntity]] = defaultdict(list)
        for entity in entities:
            occurrences[entity.entity_id].append(entity)
        duplicates: dict[str, list[dict[str, object]]] = {}
        for entity_id, entity_occurrences in sorted(occurrences.items()):
            if len(entity_occurrences) > 1:
                duplicates[entity_id] = [
                    {
                        "source_path": occurrence.source_path,
                        "line": occurrence.line,
                        "column": occurrence.column,
                        "context": occurrence.context,
                    }
                    for occurrence in entity_occurrences
                ]
        return duplicates

    def _build_findings(
        self,
        entities: list[TraceEntity],
        invalid_tokens: list[InvalidTraceToken],
        duplicate_ids: dict[str, list[dict[str, object]]],
    ) -> list[Finding]:
        findings: list[Finding] = [
            Finding(
                id="TRACEABILITY_SCAN_PASS",
                message="Traceability entity extraction completed without blocking findings.",
                severity=Severity.INFO,
                metadata={
                    "entities_total": len(entities),
                    "unique_entities_total": len({entity.entity_id for entity in entities}),
                    "invalid_tokens_total": len(invalid_tokens),
                    "duplicate_entity_ids_total": len(duplicate_ids),
                    "inferred_links": False,
                },
            )
        ]
        for token in invalid_tokens:
            findings.append(
                Finding(
                    id="TRACEABILITY_ENTITY_ID_INVALID",
                    message="Malformed traceability ID-like token detected.",
                    severity=Severity.WARNING,
                    path=token.source_path,
                    metadata={
                        "raw_id": token.raw_id,
                        "normalized_candidate": token.normalized_candidate,
                        "line": token.line,
                        "column": token.column,
                        "reason": token.reason,
                    },
                )
            )
        for entity_id, occurrences in duplicate_ids.items():
            findings.append(
                Finding(
                    id="TRACEABILITY_ENTITY_DUPLICATE",
                    message=f"Traceability ID appears more than once: {entity_id}.",
                    severity=Severity.WARNING,
                    metadata={"entity_id": entity_id, "occurrences_total": len(occurrences), "occurrences": occurrences},
                )
            )
        return findings


def _compact_context(line: str, *, limit: int = 160) -> str:
    context = " ".join(line.strip().split())
    if len(context) <= limit:
        return context
    return f"{context[: limit - 3]}..."
