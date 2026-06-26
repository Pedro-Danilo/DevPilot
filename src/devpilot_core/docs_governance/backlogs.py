from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.validators.frontmatter import parse_frontmatter_file

ROADMAP_JSON = Path(".devpilot/evals/post_h_eval_001_prioritized_roadmap.json")
BACKLOG_PATH_RE = re.compile(r"^docs/backlogs/POST-H-(\d{3})_[a-z0-9_]+\.md$")
POST_H_ID_RE = re.compile(r"^POST-H-\d{3}$")
MINIMUM_BACKLOG_FRONTMATTER = (
    "doc_id",
    "id",
    "title",
    "status",
    "version",
    "owner",
    "updated",
    "priority",
    "roadmap_source",
)
BLOCKING_SEVERITIES = {"fail", "block", "error"}


@dataclass(frozen=True)
class ExpectedBacklog:
    milestone: str
    path: str
    priority: str


class DocumentationBacklogGovernanceValidator:
    """Validate executable backlog documents derived from the post-H roadmap.

    POST-H-009-D is deterministic, read-only and local-first. It validates that
    every roadmap executable backlog entry is governed by the source registry,
    follows the expected naming convention and exposes minimum frontmatter.
    Missing future backlogs are reported as planned findings, not as blocking
    errors, so the registry can govern planned documents before they exist.
    """

    def __init__(self, root: Path, registry: Any) -> None:
        self.root = Path(root).resolve()
        self.registry = registry

    def run(self) -> dict[str, Any]:
        expected = self._load_expected_backlogs()
        documents_by_path = {document.path: document for document in self.registry.documents}
        findings: list[dict[str, Any]] = []
        checks: list[dict[str, Any]] = []

        for item in expected:
            document = documents_by_path.get(item.path)
            path = self.root / item.path
            exists = path.exists()
            check: dict[str, Any] = {
                "milestone": item.milestone,
                "path": item.path,
                "expected_priority": item.priority,
                "registered": document is not None,
                "exists": exists,
                "classification": getattr(document, "classification", None) if document else None,
                "lifecycle": getattr(document, "lifecycle", None) if document else "planned",
                "status_required": getattr(document, "status_required", None) if document else "planned",
                "naming_checked": True,
                "naming_ok": bool(BACKLOG_PATH_RE.fullmatch(item.path)),
                "frontmatter_checked": False,
                "frontmatter_ok": None,
                "milestone_match_checked": False,
                "milestone_match_ok": None,
                "planned_missing": not exists,
                "ok": True,
            }

            if document is None:
                findings.append(_finding(
                    "DOCUMENTATION_BACKLOG_REGISTRY_MISSING",
                    "Roadmap executable backlog is not registered in the documentation source registry.",
                    "block",
                    item.path,
                    {"milestone": item.milestone},
                ))
                check["ok"] = False

            if not check["naming_ok"]:
                findings.append(_finding(
                    "DOCUMENTATION_BACKLOG_NAMING_MISMATCH",
                    "Backlog path does not follow docs/backlogs/POST-H-###_<slug>.md naming convention.",
                    "block",
                    item.path,
                    {"milestone": item.milestone},
                ))
                check["ok"] = False

            if not exists:
                findings.append(_finding(
                    "DOCUMENTATION_BACKLOG_PLANNED_MISSING",
                    "Roadmap backlog is planned but the Markdown file does not exist yet; this is informational in POST-H-009-D.",
                    "info",
                    item.path,
                    {"milestone": item.milestone, "expected_priority": item.priority},
                ))
                checks.append(check)
                continue

            frontmatter_result = self._validate_frontmatter(path, item, document)
            check.update(frontmatter_result["check"])
            findings.extend(frontmatter_result["findings"])
            if not frontmatter_result["ok"]:
                check["ok"] = False

            checks.append(check)

        blocking = sum(1 for finding in findings if finding["severity"] in BLOCKING_SEVERITIES)
        summary = {
            "backlogs_expected_total": len(expected),
            "backlogs_checked_total": len(checks),
            "backlogs_registered_total": sum(1 for check in checks if check.get("registered")),
            "backlogs_existing_total": sum(1 for check in checks if check.get("exists")),
            "backlogs_planned_missing_total": sum(1 for check in checks if check.get("planned_missing")),
            "backlog_naming_checked_total": sum(1 for check in checks if check.get("naming_checked")),
            "backlog_frontmatter_checked_total": sum(1 for check in checks if check.get("frontmatter_checked")),
            "backlog_milestone_match_checked_total": sum(1 for check in checks if check.get("milestone_match_checked")),
            "backlog_governance_findings_total": len(findings),
            "backlog_governance_blocking_findings_total": blocking,
            "backlog_governance_passed": blocking == 0,
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "llm_judge_used": False,
        }
        return {"summary": summary, "backlog_checks": checks, "findings": findings}

    def _load_expected_backlogs(self) -> list[ExpectedBacklog]:
        path = self.root / ROADMAP_JSON
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw_items = payload.get("executable_backlogs_to_create", []) if isinstance(payload, dict) else []
        expected: list[ExpectedBacklog] = []
        for raw in raw_items:
            if not isinstance(raw, dict):
                continue
            milestone = str(raw.get("milestone", "")).strip()
            item_path = str(raw.get("path", "")).strip()
            priority = str(raw.get("priority", "")).strip()
            if POST_H_ID_RE.fullmatch(milestone) and item_path:
                expected.append(ExpectedBacklog(milestone=milestone, path=item_path, priority=priority or "P3"))
        return expected

    def _validate_frontmatter(self, path: Path, item: ExpectedBacklog, document: Any | None) -> dict[str, Any]:
        path_str = _rel(self.root, path)
        parsed = parse_frontmatter_file(path)
        findings: list[dict[str, Any]] = []
        check: dict[str, Any] = {
            "frontmatter_checked": True,
            "frontmatter_ok": False,
            "milestone_match_checked": True,
            "milestone_match_ok": False,
            "frontmatter_doc_id": None,
            "frontmatter_id": None,
            "frontmatter_title": None,
            "frontmatter_status": None,
            "frontmatter_priority": None,
            "frontmatter_roadmap_source": None,
        }

        if not parsed.has_frontmatter:
            findings.append(_finding(
                "DOCUMENTATION_BACKLOG_FRONTMATTER_MISSING",
                "Executable backlog Markdown requires frontmatter.",
                "block",
                path_str,
                {"milestone": item.milestone},
            ))
            return {"ok": False, "check": check, "findings": findings}

        frontmatter = parsed.frontmatter
        check.update({
            "frontmatter_doc_id": frontmatter.get("doc_id"),
            "frontmatter_id": frontmatter.get("id"),
            "frontmatter_title": frontmatter.get("title"),
            "frontmatter_status": frontmatter.get("status"),
            "frontmatter_priority": frontmatter.get("priority"),
            "frontmatter_roadmap_source": frontmatter.get("roadmap_source"),
        })

        missing = [key for key in MINIMUM_BACKLOG_FRONTMATTER if not str(frontmatter.get(key, "")).strip()]
        if missing:
            findings.append(_finding(
                "DOCUMENTATION_BACKLOG_FRONTMATTER_INCOMPLETE",
                "Executable backlog frontmatter is missing required fields.",
                "block",
                path_str,
                {"milestone": item.milestone, "missing": missing},
            ))

        expected_doc_id = f"{item.milestone}-BACKLOG"
        if str(frontmatter.get("doc_id", "")).strip() != expected_doc_id:
            findings.append(_finding(
                "DOCUMENTATION_BACKLOG_DOC_ID_MISMATCH",
                "Backlog doc_id does not match POST-H-###-BACKLOG convention.",
                "block",
                path_str,
                {"expected_doc_id": expected_doc_id, "actual_doc_id": frontmatter.get("doc_id")},
            ))

        if str(frontmatter.get("id", "")).strip() != item.milestone:
            findings.append(_finding(
                "DOCUMENTATION_BACKLOG_ID_MISMATCH",
                "Backlog id does not match roadmap milestone.",
                "block",
                path_str,
                {"expected_id": item.milestone, "actual_id": frontmatter.get("id")},
            ))
        else:
            check["milestone_match_ok"] = True

        if str(frontmatter.get("priority", "")).strip() != item.priority:
            findings.append(_finding(
                "DOCUMENTATION_BACKLOG_PRIORITY_MISMATCH",
                "Backlog priority does not match roadmap machine-readable source.",
                "block",
                path_str,
                {"expected_priority": item.priority, "actual_priority": frontmatter.get("priority")},
            ))

        if str(frontmatter.get("roadmap_source", "")).strip() != "docs/backlogs/post_h_prioritized_roadmap.md":
            findings.append(_finding(
                "DOCUMENTATION_BACKLOG_ROADMAP_SOURCE_MISMATCH",
                "Backlog roadmap_source must point to the post-H prioritized roadmap.",
                "block",
                path_str,
                {"expected_roadmap_source": "docs/backlogs/post_h_prioritized_roadmap.md", "actual_roadmap_source": frontmatter.get("roadmap_source")},
            ))

        if document is not None and str(getattr(document, "doc_id", "")).strip() != expected_doc_id:
            findings.append(_finding(
                "DOCUMENTATION_BACKLOG_REGISTRY_DOC_ID_MISMATCH",
                "Registry doc_id for backlog does not match POST-H-###-BACKLOG convention.",
                "block",
                path_str,
                {"expected_doc_id": expected_doc_id, "registry_doc_id": getattr(document, "doc_id", None)},
            ))

        check["frontmatter_ok"] = not any(finding["severity"] in BLOCKING_SEVERITIES for finding in findings)
        return {"ok": check["frontmatter_ok"], "check": check, "findings": findings}


def _finding(id: str, message: str, severity: str, path: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    data: dict[str, Any] = {"id": id, "message": message, "severity": severity}
    if path:
        data["path"] = path
    if metadata:
        data["metadata"] = metadata
    return data


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
