from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from devpilot_core.docs_governance.models import DocumentationSourceRegistry
from devpilot_core.validators.frontmatter import parse_frontmatter_file

POST_H_MILESTONE_RE = re.compile(r"\bPOST-H-\d{3}\b")
POST_H_DECISION_RE = re.compile(r"\bDEC-POSTH-\d{3}\b")
CRITICAL_ROADMAP_MILESTONES = ("POST-H-024", "POST-H-025")
CRITICAL_ROADMAP_DECISIONS = ("DEC-POSTH-008", "DEC-POSTH-009")


class DocumentationSyncValidator:
    """Deterministic Markdown ↔ JSON sync checks for POST-H-009-C.

    The validator is intentionally local-first and read-only. It compares a
    minimal set of canonical pairs declared by DocumentationSourceRegistry and
    emits structured findings/checks without modifying source documents.
    """

    def __init__(self, root: Path, registry: DocumentationSourceRegistry) -> None:
        self.root = Path(root).resolve()
        self.registry = registry

    def run(self) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        findings: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()

        for source in self.registry.documents:
            counterparts = list(source.machine_readable_counterparts) + list(source.human_readable_counterparts)
            for counterpart in counterparts:
                source_path = source.path
                counterpart_path = counterpart
                rules = tuple(source.sync_rules)
                if not rules:
                    continue
                for rule in rules:
                    key = _pair_key(source_path, counterpart_path, rule)
                    if key in seen:
                        continue
                    seen.add(key)
                    rule_result = self._evaluate_rule(rule, source_path, counterpart_path)
                    if rule_result is None:
                        continue
                    checks.append(rule_result["check"])
                    findings.extend(rule_result["findings"])

        blocking_total = sum(1 for item in findings if item.get("severity") in {"fail", "block", "error"})
        warnings_total = sum(1 for item in findings if item.get("severity") == "warning")
        return {
            "sync_checks": checks,
            "findings": findings,
            "summary": {
                "sync_checks_total": len(checks),
                "version_match_checked_total": sum(1 for item in checks if item.get("rule") == "version_match"),
                "milestones_match_checked_total": sum(1 for item in checks if item.get("rule") == "milestones_match"),
                "decisions_match_checked_total": sum(1 for item in checks if item.get("rule") == "decisions_match"),
                "closure_status_match_checked_total": sum(1 for item in checks if item.get("rule") == "closure_status_match"),
                "next_hito_match_checked_total": sum(1 for item in checks if item.get("rule") == "next_hito_match"),
                "sync_findings_total": len(findings),
                "sync_warnings_total": warnings_total,
                "sync_blocking_findings_total": blocking_total,
                "sync_passed": blocking_total == 0,
                "roadmap_markdown_json_sync_passed": _roadmap_sync_passed(checks),
            },
        }

    def _evaluate_rule(self, rule: str, source_path: str, counterpart_path: str) -> dict[str, Any] | None:
        if rule == "version_match":
            return self._check_version_match(source_path, counterpart_path)
        if rule == "milestones_match":
            return self._check_roadmap_set_match(rule, source_path, counterpart_path, kind="milestones")
        if rule == "decisions_match":
            return self._check_roadmap_set_match(rule, source_path, counterpart_path, kind="decisions")
        if rule == "closure_status_match":
            return self._check_closure_status_match(source_path, counterpart_path)
        if rule == "next_hito_match":
            return self._check_next_hito_match(source_path, counterpart_path)
        return None

    def _check_version_match(self, source_path: str, counterpart_path: str) -> dict[str, Any]:
        source_version = _extract_version(self.root / source_path)
        counterpart_version = _extract_version(self.root / counterpart_path)
        ok = bool(source_version and counterpart_version and source_version == counterpart_version)
        check = _base_check("version_match", source_path, counterpart_path, ok)
        check.update({"source_version": source_version, "counterpart_version": counterpart_version})
        findings: list[dict[str, Any]] = []
        if not ok:
            findings.append(_finding(
                "DOCUMENTATION_SYNC_VERSION_MISMATCH",
                "Markdown and JSON counterpart versions differ or one side does not declare version.",
                "block",
                source_path,
                {
                    "counterpart_path": counterpart_path,
                    "source_version": source_version,
                    "counterpart_version": counterpart_version,
                },
            ))
        return {"check": check, "findings": findings}

    def _check_roadmap_set_match(self, rule: str, source_path: str, counterpart_path: str, *, kind: str) -> dict[str, Any]:
        source_file = self.root / source_path
        counterpart_file = self.root / counterpart_path
        source_values = _extract_roadmap_values(source_file, kind=kind)
        counterpart_values = _extract_roadmap_values(counterpart_file, kind=kind)
        missing_in_counterpart = sorted(source_values - counterpart_values)
        missing_in_source = sorted(counterpart_values - source_values)
        ok = not missing_in_counterpart and not missing_in_source
        check = _base_check(rule, source_path, counterpart_path, ok)
        check.update({
            "source_total": len(source_values),
            "counterpart_total": len(counterpart_values),
            "missing_in_counterpart": missing_in_counterpart,
            "missing_in_source": missing_in_source,
        })
        if kind == "milestones":
            check["critical_milestones_checked"] = list(CRITICAL_ROADMAP_MILESTONES)
            check["critical_milestones_present_in_both"] = all(
                item in source_values and item in counterpart_values for item in CRITICAL_ROADMAP_MILESTONES
            )
        if kind == "decisions":
            check["critical_decisions_checked"] = list(CRITICAL_ROADMAP_DECISIONS)
            check["critical_decisions_present_in_both"] = all(
                item in source_values and item in counterpart_values for item in CRITICAL_ROADMAP_DECISIONS
            )
        findings: list[dict[str, Any]] = []
        if not ok:
            findings.append(_finding(
                f"DOCUMENTATION_SYNC_{kind.upper()}_MISMATCH",
                f"Roadmap Markdown and JSON counterpart differ in {kind}.",
                "block",
                source_path,
                {
                    "counterpart_path": counterpart_path,
                    "missing_in_counterpart": missing_in_counterpart,
                    "missing_in_source": missing_in_source,
                },
            ))
        if kind == "milestones" and not check["critical_milestones_present_in_both"]:
            findings.append(_finding(
                "DOCUMENTATION_SYNC_CRITICAL_MILESTONES_MISSING",
                "POST-H-024 and POST-H-025 must be present in both roadmap Markdown and JSON.",
                "block",
                source_path,
                {"counterpart_path": counterpart_path, "critical_milestones": list(CRITICAL_ROADMAP_MILESTONES)},
            ))
            check["ok"] = False
        if kind == "decisions" and not check["critical_decisions_present_in_both"]:
            findings.append(_finding(
                "DOCUMENTATION_SYNC_CRITICAL_DECISIONS_MISSING",
                "DEC-POSTH-008 and DEC-POSTH-009 must be present in both roadmap Markdown and JSON.",
                "block",
                source_path,
                {"counterpart_path": counterpart_path, "critical_decisions": list(CRITICAL_ROADMAP_DECISIONS)},
            ))
            check["ok"] = False
        return {"check": check, "findings": findings}

    def _check_closure_status_match(self, source_path: str, counterpart_path: str) -> dict[str, Any] | None:
        paths = {source_path, counterpart_path}
        if "docs/post_h_eval_001_manifest.json" not in paths or "docs/audits/post_h_eval_001_closure_report.md" not in paths:
            return None
        manifest = _read_json(self.root / "docs/post_h_eval_001_manifest.json")
        closure_text = _read_text(self.root / "docs/audits/post_h_eval_001_closure_report.md")
        manifest_status = str(manifest.get("status", "")) if isinstance(manifest, dict) else ""
        closure_status = str(manifest.get("closure_status", "")) if isinstance(manifest, dict) else ""
        closure_mentions_hito = "POST-H-EVAL-001" in closure_text
        closure_mentions_closed = any(token in closure_text.lower() for token in ("cierre", "cerrado", "closed"))
        ok = manifest_status.startswith("closed") and closure_status.startswith("closed") and closure_mentions_hito and closure_mentions_closed
        check = _base_check("closure_status_match", source_path, counterpart_path, ok)
        check.update({
            "manifest_status": manifest_status,
            "manifest_closure_status": closure_status,
            "closure_mentions_hito": closure_mentions_hito,
            "closure_mentions_closed": closure_mentions_closed,
        })
        findings: list[dict[str, Any]] = []
        if not ok:
            findings.append(_finding(
                "DOCUMENTATION_SYNC_CLOSURE_STATUS_MISMATCH",
                "POST-H-EVAL-001 manifest and closure report do not agree on closed status.",
                "block",
                "docs/post_h_eval_001_manifest.json",
                {"counterpart_path": "docs/audits/post_h_eval_001_closure_report.md"},
            ))
        return {"check": check, "findings": findings}

    def _check_next_hito_match(self, source_path: str, counterpart_path: str) -> dict[str, Any] | None:
        paths = {source_path, counterpart_path}
        if ".devpilot/project_state.json" not in paths:
            return None
        state = _read_json(self.root / ".devpilot/project_state.json")
        next_hito = str(state.get("next_sprint", "")) if isinstance(state, dict) else ""
        human_path = counterpart_path if source_path == ".devpilot/project_state.json" else source_path
        if not human_path.endswith(('.md', '.txt')):
            return None
        human_text = _read_text(self.root / human_path)
        ok = bool(next_hito and next_hito in human_text)
        check = _base_check("next_hito_match", source_path, counterpart_path, ok)
        check.update({"next_hito": next_hito, "human_path": human_path})
        findings: list[dict[str, Any]] = []
        if not ok:
            findings.append(_finding(
                "DOCUMENTATION_SYNC_NEXT_HITO_MISMATCH",
                "Project state next_sprint is not reflected in the human-readable counterpart.",
                "block",
                human_path,
                {"project_state_path": ".devpilot/project_state.json", "next_hito": next_hito},
            ))
        return {"check": check, "findings": findings}


def _pair_key(source_path: str, counterpart_path: str, rule: str) -> tuple[str, str, str]:
    ordered = tuple(sorted((source_path, counterpart_path)))
    return ordered[0], ordered[1], rule


def _base_check(rule: str, source_path: str, counterpart_path: str, ok: bool) -> dict[str, Any]:
    return {
        "rule": rule,
        "source_path": source_path,
        "counterpart_path": counterpart_path,
        "ok": ok,
        "read_only": True,
        "network_used": False,
        "external_api_used": False,
    }


def _extract_version(path: Path) -> str | None:
    if not path.exists():
        return None
    if path.suffix.lower() == ".md":
        parsed = parse_frontmatter_file(path)
        if parsed.has_frontmatter:
            value = parsed.frontmatter.get("version")
            return str(value).strip() if value is not None else None
        return None
    if path.suffix.lower() == ".json":
        payload = _read_json(path)
        if isinstance(payload, dict):
            value = payload.get("version")
            return str(value).strip() if value is not None else None
    return None


def _extract_roadmap_values(path: Path, *, kind: str) -> set[str]:
    if not path.exists():
        return set()
    if path.suffix.lower() == ".md":
        text = _read_text(path)
        if kind == "milestones":
            return _normalize_post_h_milestones(set(POST_H_MILESTONE_RE.findall(text)))
        if kind == "decisions":
            return set(POST_H_DECISION_RE.findall(text))
    if path.suffix.lower() == ".json":
        payload = _read_json(path)
        if not isinstance(payload, dict):
            return set()
        if kind == "milestones":
            values: set[str] = set()
            for wave in payload.get("waves", []):
                if isinstance(wave, dict):
                    values.update(str(item) for item in wave.get("milestones", []) if isinstance(item, str))
            for backlog in payload.get("executable_backlogs_to_create", []):
                if isinstance(backlog, dict) and isinstance(backlog.get("milestone"), str):
                    values.add(str(backlog["milestone"]))
            return _normalize_post_h_milestones(values)
        if kind == "decisions":
            return {
                str(decision.get("id"))
                for decision in payload.get("decisions", [])
                if isinstance(decision, dict) and isinstance(decision.get("id"), str)
            }
    return set()


def _normalize_post_h_milestones(values: set[str]) -> set[str]:
    normalized: set[str] = set()
    for value in values:
        match = re.fullmatch(r"POST-H-(\d{3})", value)
        if not match:
            continue
        # POST-H-001 belongs to the earlier hardening hito, not the prioritized roadmap POST-H-002..025 sync set.
        if int(match.group(1)) >= 2:
            normalized.add(value)
    return normalized


def _roadmap_sync_passed(checks: list[dict[str, Any]]) -> bool:
    roadmap_checks = [
        item for item in checks
        if item.get("rule") in {"version_match", "milestones_match", "decisions_match"}
        and "post_h_eval_001_prioritized_roadmap" in str(item.get("counterpart_path", ""))
    ]
    return bool(roadmap_checks) and all(item.get("ok") is True for item in roadmap_checks)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _read_json(path: Path) -> Any:
    try:
        return json.loads(_read_text(path))
    except Exception:
        return {}


def _finding(id: str, message: str, severity: str, path: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    data: dict[str, Any] = {"id": id, "message": message, "severity": severity}
    if path:
        data["path"] = path
    if metadata:
        data["metadata"] = metadata
    return data
