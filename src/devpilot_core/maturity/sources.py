from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings


@dataclass(frozen=True)
class SourceSpec:
    """Declarative source expected by POST-H-002 maturity readers."""

    source_id: str
    path: str
    source_type: str
    critical: bool = True
    required_sections: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceReadResult:
    """Read outcome for one post-H source artifact.

    The result stores a compact summary and optional parsed payload. The full
    payload is intentionally not emitted by ``to_dict`` by default so future
    dashboard commands can stay concise and avoid duplicating large source JSON.
    Tests and builders may still use ``payload`` in memory.
    """

    source_id: str
    path: str
    source_type: str
    critical: bool
    exists: bool
    ok: bool
    summary: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] | list[Any] | str | None = None
    sections_found: list[str] = field(default_factory=list)
    missing_sections: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self, *, include_payload: bool = False) -> dict[str, Any]:
        data: dict[str, Any] = {
            "source_id": self.source_id,
            "path": self.path,
            "source_type": self.source_type,
            "critical": self.critical,
            "exists": self.exists,
            "ok": self.ok,
            "summary": dict(self.summary),
        }
        if self.sections_found:
            data["sections_found"] = list(self.sections_found)
        if self.missing_sections:
            data["missing_sections"] = list(self.missing_sections)
        if self.error:
            data["error"] = self.error
        if include_payload:
            data["payload"] = self.payload
        return data


@dataclass(frozen=True)
class PostHSourceBundle:
    """Aggregated POST-H evidence sources for the maturity dashboard."""

    json_sources: list[SourceReadResult]
    markdown_sources: list[SourceReadResult]
    findings: list[Finding]

    @property
    def ok(self) -> bool:
        return not any(finding.severity in {Severity.BLOCK, Severity.ERROR} for finding in self.findings)

    @property
    def blocking_findings_total(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == Severity.BLOCK)

    @property
    def warnings_total(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == Severity.WARNING)

    def evidence_paths(self) -> list[str]:
        paths = [source.path for source in self.json_sources + self.markdown_sources if source.exists]
        return sorted(dict.fromkeys(paths))

    def source_by_id(self, source_id: str) -> SourceReadResult | None:
        for source in self.json_sources + self.markdown_sources:
            if source.source_id == source_id:
                return source
        return None

    def to_dict(self, *, include_payload: bool = False) -> dict[str, Any]:
        return {
            "summary": {
                "json_sources_total": len(self.json_sources),
                "markdown_sources_total": len(self.markdown_sources),
                "sources_total": len(self.json_sources) + len(self.markdown_sources),
                "sources_ok": sum(1 for source in self.json_sources + self.markdown_sources if source.ok),
                "sources_missing": sum(1 for source in self.json_sources + self.markdown_sources if not source.exists),
                "blocking_findings_total": self.blocking_findings_total,
                "warnings_total": self.warnings_total,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "preliminary": True,
            },
            "json_sources": [source.to_dict(include_payload=include_payload) for source in self.json_sources],
            "markdown_sources": [source.to_dict(include_payload=include_payload) for source in self.markdown_sources],
            "evidence_paths": self.evidence_paths(),
        }

    def to_command_result(self) -> CommandResult:
        exit_code = exit_code_for_findings(self.findings)
        return CommandResult(
            command="maturity source-read",
            ok=self.ok,
            exit_code=exit_code,
            message="POST-H maturity sources read successfully." if self.ok else "POST-H maturity sources have blocking findings.",
            data=self.to_dict(),
            findings=self.findings,
        )


JSON_SOURCE_SPECS: tuple[SourceSpec, ...] = (
    SourceSpec("post_h_eval_manifest", "docs/post_h_eval_001_manifest.json", "json", True),
    SourceSpec("decision_matrix", ".devpilot/evals/post_h_eval_001_decision_matrix.json", "json", True),
    SourceSpec("security_risk_register", ".devpilot/evals/post_h_eval_001_security_risk_register.json", "json", True),
    SourceSpec("test_cost_assessment", ".devpilot/evals/post_h_eval_001_test_cost_assessment.json", "json", True),
    SourceSpec("prioritized_roadmap", ".devpilot/evals/post_h_eval_001_prioritized_roadmap.json", "json", True),
    SourceSpec("test_contract_registry", ".devpilot/testing/test_contract_registry.json", "json", True),
)

MARKDOWN_SOURCE_SPECS: tuple[SourceSpec, ...] = (
    SourceSpec("baseline_assessment_doc", "docs/audits/post_h_eval_001_baseline_assessment.md", "markdown", False, ("propósito", "estado")),
    SourceSpec("architecture_map_doc", "docs/02_architecture/post_h_current_architecture_map.md", "markdown", False, ("propósito", "estado")),
    SourceSpec("security_risk_register_doc", "docs/03_security/post_h_security_risk_register.md", "markdown", False, ("propósito", "estado")),
    SourceSpec("test_cost_assessment_doc", "docs/04_quality/post_h_test_cost_assessment.md", "markdown", False, ("propósito", "estado")),
    SourceSpec("prioritized_roadmap_doc", "docs/backlogs/post_h_prioritized_roadmap.md", "markdown", False, ("propósito", "estado")),
    SourceSpec("closure_report_doc", "docs/audits/post_h_eval_001_closure_report.md", "markdown", False, ("propósito", "estado")),
)


class PostHSourceReader:
    """Read-only source reader for POST-H-002 maturity dashboard inputs.

    POST-H-002-B deliberately reads existing evidence only. It does not write
    reports, does not mutate manifests, does not call the network and does not
    infer maturity values without a concrete source artifact.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        json_specs: Sequence[SourceSpec] = JSON_SOURCE_SPECS,
        markdown_specs: Sequence[SourceSpec] = MARKDOWN_SOURCE_SPECS,
    ) -> None:
        self.root = Path(root).resolve()
        self.json_specs = tuple(json_specs)
        self.markdown_specs = tuple(markdown_specs)

    def read_all(self, *, include_markdown: bool = True) -> PostHSourceBundle:
        findings: list[Finding] = []
        json_sources = [self.read_json_source(spec, findings) for spec in self.json_specs]
        markdown_sources = [self.read_markdown_source(spec, findings) for spec in self.markdown_specs] if include_markdown else []
        findings.append(
            Finding(
                id="POST_H_SOURCE_READER_PASS" if not any(f.severity in {Severity.BLOCK, Severity.ERROR} for f in findings) else "POST_H_SOURCE_READER_BLOCK",
                message="POST-H source reader completed without blocking findings." if not any(f.severity in {Severity.BLOCK, Severity.ERROR} for f in findings) else "POST-H source reader completed with blocking findings.",
                severity=Severity.INFO if not any(f.severity in {Severity.BLOCK, Severity.ERROR} for f in findings) else Severity.BLOCK,
                metadata={
                    "json_sources_total": len(json_sources),
                    "markdown_sources_total": len(markdown_sources),
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "preliminary": True,
                },
            )
        )
        return PostHSourceBundle(json_sources=json_sources, markdown_sources=markdown_sources, findings=findings)

    def read_json_source(self, spec: SourceSpec, findings: list[Finding] | None = None) -> SourceReadResult:
        findings = findings if findings is not None else []
        path = self._resolve_workspace_path(spec.path)
        display_path = self._display_path(path)
        if not path.exists():
            severity = Severity.BLOCK if spec.critical else Severity.WARNING
            findings.append(
                Finding(
                    id="POST_H_SOURCE_MISSING",
                    message=f"POST-H source is missing: {spec.path}",
                    severity=severity,
                    path=spec.path,
                    metadata={"source_id": spec.source_id, "critical": spec.critical},
                )
            )
            return SourceReadResult(spec.source_id, spec.path, spec.source_type, spec.critical, False, False, error="missing")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            severity = Severity.BLOCK if spec.critical else Severity.WARNING
            findings.append(
                Finding(
                    id="POST_H_SOURCE_INVALID_JSON",
                    message=f"POST-H JSON source is invalid: {exc}",
                    severity=severity,
                    path=display_path,
                    metadata={"source_id": spec.source_id, "critical": spec.critical},
                )
            )
            return SourceReadResult(spec.source_id, spec.path, spec.source_type, spec.critical, True, False, error=str(exc))
        except OSError as exc:
            severity = Severity.BLOCK if spec.critical else Severity.WARNING
            findings.append(
                Finding(
                    id="POST_H_SOURCE_READ_ERROR",
                    message=f"POST-H source could not be read: {exc}",
                    severity=severity,
                    path=display_path,
                    metadata={"source_id": spec.source_id, "critical": spec.critical},
                )
            )
            return SourceReadResult(spec.source_id, spec.path, spec.source_type, spec.critical, True, False, error=str(exc))
        summary = summarize_json_payload(payload)
        findings.append(
            Finding(
                id="POST_H_SOURCE_READ",
                message=f"POST-H JSON source read: {spec.path}",
                severity=Severity.INFO,
                path=display_path,
                metadata={"source_id": spec.source_id, **summary},
            )
        )
        return SourceReadResult(spec.source_id, spec.path, spec.source_type, spec.critical, True, True, summary=summary, payload=payload)

    def read_markdown_source(self, spec: SourceSpec, findings: list[Finding] | None = None) -> SourceReadResult:
        findings = findings if findings is not None else []
        path = self._resolve_workspace_path(spec.path)
        display_path = self._display_path(path)
        if not path.exists():
            severity = Severity.BLOCK if spec.critical else Severity.WARNING
            findings.append(
                Finding(
                    id="POST_H_MARKDOWN_SOURCE_MISSING",
                    message=f"POST-H Markdown source is missing: {spec.path}",
                    severity=severity,
                    path=spec.path,
                    metadata={"source_id": spec.source_id, "critical": spec.critical},
                )
            )
            return SourceReadResult(spec.source_id, spec.path, spec.source_type, spec.critical, False, not spec.critical, error="missing")
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            severity = Severity.BLOCK if spec.critical else Severity.WARNING
            findings.append(
                Finding(
                    id="POST_H_MARKDOWN_SOURCE_READ_ERROR",
                    message=f"POST-H Markdown source could not be read: {exc}",
                    severity=severity,
                    path=display_path,
                    metadata={"source_id": spec.source_id, "critical": spec.critical},
                )
            )
            return SourceReadResult(spec.source_id, spec.path, spec.source_type, spec.critical, True, not spec.critical, error=str(exc))
        sections = extract_markdown_headings(text)
        normalized_sections = {_normalize_heading(section) for section in sections}
        missing_sections = [section for section in spec.required_sections if _normalize_heading(section) not in normalized_sections]
        for section in missing_sections:
            severity = Severity.BLOCK if spec.critical else Severity.WARNING
            findings.append(
                Finding(
                    id="POST_H_MARKDOWN_SECTION_MISSING",
                    message=f"Expected section is missing in POST-H Markdown source: {section}",
                    severity=severity,
                    path=display_path,
                    metadata={"source_id": spec.source_id, "section": section, "critical": spec.critical},
                )
            )
        ok = not any(missing_sections) or not spec.critical
        summary = {
            "bytes": len(text.encode("utf-8")),
            "heading_count": len(sections),
            "required_sections_total": len(spec.required_sections),
            "missing_sections_total": len(missing_sections),
        }
        findings.append(
            Finding(
                id="POST_H_MARKDOWN_SOURCE_READ",
                message=f"POST-H Markdown source read: {spec.path}",
                severity=Severity.INFO,
                path=display_path,
                metadata={"source_id": spec.source_id, **summary},
            )
        )
        return SourceReadResult(
            spec.source_id,
            spec.path,
            spec.source_type,
            spec.critical,
            True,
            ok,
            summary=summary,
            payload=text,
            sections_found=sections,
            missing_sections=missing_sections,
        )

    def _resolve_workspace_path(self, relative_path: str | Path) -> Path:
        candidate = (self.root / relative_path).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError(f"Path escapes workspace root: {relative_path}")
        return candidate

    def _display_path(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()


def summarize_json_payload(payload: Any) -> dict[str, Any]:
    """Return compact deterministic metadata for a JSON source payload."""

    if isinstance(payload, Mapping):
        summary: dict[str, Any] = {
            "top_level_type": "object",
            "top_level_keys": sorted(str(key) for key in payload.keys())[:20],
        }
        for key in ("id", "title", "status", "generated_at_utc", "current_micro_sprint", "micro_sprint_status"):
            if key in payload:
                summary[key] = payload[key]
        if isinstance(payload.get("summary"), Mapping):
            source_summary = payload["summary"]
            for key in (
                "domains_total",
                "risks_total",
                "critical_total",
                "high_total",
                "contracts_total",
                "blocking_findings_total",
                "production_ready_local_total",
                "implemented_total",
                "implemented_initial_total",
                "experimental_total",
                "p0_total",
                "p1_total",
                "p2_total",
                "p3_total",
            ):
                if key in source_summary:
                    summary[key] = source_summary[key]
        for list_key in ("domains", "risks", "waves", "contracts", "capabilities"):
            value = payload.get(list_key)
            if isinstance(value, list):
                summary[f"{list_key}_total"] = len(value)
        policy = payload.get("policy") if isinstance(payload.get("policy"), Mapping) else payload.get("execution_policy")
        if isinstance(policy, Mapping):
            for key in (
                "local_first",
                "dry_run",
                "no_runtime_features_added",
                "no_remote_execution_enabled",
                "no_write_connectors_enabled",
                "no_connector_write_enabled",
                "no_plugin_execution_enabled",
                "no_external_apis_used",
                "documentation_and_metadata_only",
            ):
                if key in policy:
                    summary[key] = policy[key]
        if isinstance(payload.get("quality_signals"), Mapping):
            quality = payload["quality_signals"]
            for key in ("project_state_ok", "test_contracts_ok", "hardening_quality_gate_ok", "industrial_readiness_ok", "remote_runner_enabled", "remote_execution_used", "network_used", "external_api_used"):
                if key in quality:
                    summary[key] = quality[key]
        return summary
    if isinstance(payload, list):
        return {"top_level_type": "array", "items_total": len(payload)}
    return {"top_level_type": type(payload).__name__}


def extract_markdown_headings(text: str) -> list[str]:
    headings: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            headings.append(match.group(2).strip())
    return headings


def _normalize_heading(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", value)
    value = value.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    return value
