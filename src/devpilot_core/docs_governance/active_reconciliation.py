"""Focused, read-only governance consistency audit for MP132 R03-01.

This auditor deliberately separates current-active invariants from immutable
historical documents. It neither edits the project nor infers semantic approval.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any


PROGRAM = "docs/programs/DEVPL_MP_SUCCESSOR_132/v1_1_0_owner_approved_133"
CURRENT = "MP132-R03-04/TECH-DECISION-ADR"
PHASE = "DEVPL-MP-SUCCESSOR-132/R03-ARCHITECTURE-RISK-SCAFFOLD"
NEXT = "R03_05_NOT_AUTHORIZED"
REQUIRED_PROGRAM = {
    "0_program/12_ENMIENDA_188_APROBADA.md": "OWNER_APPROVED_PROGRAM_AMENDMENT",
    "0_program/13_DECISION_OWNER_188.md": "OWNER_APPROVED_PROGRAM_ONLY",
    "0_program/14_DECISION_OWNER_A190.md": "OWNER_APPROVED_PROGRAM_AMENDMENT",
    "1_arquitectura/ADR_MP132_016_CALIDAD_ARTEFACTOS_188.md": "OWNER_APPROVED_PROGRAM_ADR",
    "2_contratos/ARTIFACT_AUTHORING_QUALITY_CONTRACT_188.md": "OWNER_APPROVED_PROGRAM_CONTRACT",
    "7_ Execution_packages-sprints_prompts/BACKLOG_R03/02_sprints/R03_01_DOC_RECONCILIATION_SPRINT.md": "SPRINT_EXECUTION_APPROVED",
    "7_ Execution_packages-sprints_prompts/BACKLOG_R03/03_prompts/R03_01_DOC_RECONCILIATION_PROMPT.md": "OWNER_APPROVED",
    "7_ Execution_packages-sprints_prompts/BACKLOG_R03/02_sprints/R03_02_TECH_CONTEXT_PROFILE_SPRINT.md": "SPRINT_EXECUTION_APPROVED",
    "7_ Execution_packages-sprints_prompts/BACKLOG_R03/03_prompts/R03_02_TECH_CONTEXT_PROFILE_PROMPT.md": "OWNER_APPROVED",
    "7_ Execution_packages-sprints_prompts/BACKLOG_R03/02_sprints/R03_03_ARCHITECTURE_AUTHORING_SPRINT.md": "SPRINT_EXECUTION_APPROVED",
    "7_ Execution_packages-sprints_prompts/BACKLOG_R03/03_prompts/R03_03_ARCHITECTURE_AUTHORING_PROMPT.md": "OWNER_APPROVED",
    "7_ Execution_packages-sprints_prompts/BACKLOG_R03/02_sprints/R03_04_TECH_DECISION_ADR_SPRINT.md": "SPRINT_EXECUTION_APPROVED",
    "7_ Execution_packages-sprints_prompts/BACKLOG_R03/03_prompts/R03_04_TECH_DECISION_ADR_PROMPT.md": "OWNER_APPROVED",
    "6_trazabilidad/17_R03_01_CLOSURE_R03_02_AUTHORITY.md": "OWNER_APPROVED_INCREMENT_R03_02_WINDOWS_PENDING",
    "7_ Execution_packages-sprints_prompts/BACKLOG_R03/CHECKPOINT_R03_189.md": "R03_03_CLOSED_R03_04_OWNER_APPROVED_WINDOWS_PENDING",
    "6_trazabilidad/16_R03_01_APPROVAL_BINDING.md": "OWNER_APPROVED_SPRINT_ONLY_WINDOWS_PENDING",
}


def _safe_path(root: Path, value: str) -> bool:
    path = PurePosixPath(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts and (root / value).is_file()


def _frontmatter_status(path: Path) -> str | None:
    content = path.read_text(encoding="utf-8-sig", errors="replace")
    if not content.startswith("---\n"):
        return None
    end = content.find("\n---", 4)
    if end < 0:
        return None
    for line in content[4:end].splitlines():
        if line.startswith("status:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return None


def audit_repo(root: Path) -> dict[str, Any]:
    """Return evidence, never perform mutation; do not judge semantic quality."""
    root = Path(root).resolve()
    state = json.loads((root / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    registry = json.loads((root / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8"))
    documents = registry["documents"]
    findings: list[dict[str, Any]] = []

    def block(code: str, detail: str) -> None:
        findings.append({"severity": "BLOCK", "code": code, "detail": detail})

    for key, expected in (("current_micro_sprint", CURRENT), ("current_phase", PHASE), ("next_micro_sprint", NEXT)):
        if state.get(key) != registry.get(key) or state.get(key) != expected:
            block("POINTER_DRIFT", f"{key}: state={state.get(key)!r}; registry={registry.get(key)!r}; expected={expected!r}")

    paths = set()
    active_ids: dict[str, list[str]] = defaultdict(list)
    missing: list[str] = []
    for document in documents:
        path = document["path"]
        key = (document["doc_id"], path)
        if key in paths:
            block("DUPLICATE_REGISTRY_ROW", f"{key!r}")
        paths.add(key)
        if document.get("lifecycle") == "active":
            active_ids[document["doc_id"]].append(path)
        for linked in [path, *(value for field in ("required_tests", "related_adrs", "machine_readable_counterparts", "human_readable_counterparts", "derived_documents") for value in document.get(field, []))]:
            if linked.startswith("outputs/"):
                continue  # reproducible runtime evidence, excluded from Git archives
            if not _safe_path(root, linked):
                missing.append(linked)
    if missing:
        block("BROKEN_DOCUMENT_PATHS", f"{len(missing)} missing/unsafe references, examples: {sorted(set(missing))[:8]}")
    for doc_id, items in sorted(active_ids.items()):
        if len(items) > 1:
            block("MULTIPLE_ACTIVE_AUTHORITIES", f"{doc_id}: {items}")

    for key, expected in {
        "documents_total": len(documents),
        "documents_with_required_tests_total": sum(bool(x.get("required_tests")) for x in documents),
        "source_of_truth_total": sum(x["classification"] == "source-of-truth" for x in documents),
        "machine_readable_source_total": sum(x["classification"] == "machine-readable-source" for x in documents),
        "derived_total": sum(x["classification"] == "derived" for x in documents),
        "historical_total": sum(x["classification"] == "historical" for x in documents),
        "deprecated_total": sum(x["classification"] == "deprecated" for x in documents),
        "generated_runtime_total": sum(x["classification"] == "generated-runtime" for x in documents),
        "critical_sources_total": sum(x.get("criticality") in {"P0", "P1"} for x in documents),
    }.items():
        if registry["summary"].get(key) != expected:
            block("DERIVED_COUNT_DRIFT", f"{key}: reported={registry['summary'].get(key)}; actual={expected}")

    registered = {x["path"] for x in documents if x.get("lifecycle") == "active"}
    for rel, expected_status in REQUIRED_PROGRAM.items():
        full = f"{PROGRAM}/{rel}"
        path = root / full
        if not path.is_file() or full not in registered:
            block("UNREGISTERED_ACTIVE_PROGRAM", full)
        elif expected_status is not None and _frontmatter_status(path) != expected_status:
            block("APPROVAL_STATUS_DRIFT", f"{full}: {_frontmatter_status(path)} != {expected_status}")

    return {
        "audit_id": "MP132-R03-01-ACTIVE-DOCS",
        "read_only": True,
        "documents_checked": len(documents),
        "registered_paths_checked": len(paths),
        "active_duplicate_doc_ids": sum(len(items) > 1 for items in active_ids.values()),
        "classification_counts": dict(Counter(x["classification"] for x in documents)),
        "findings": findings,
        "disposition": "PASS" if not findings else "BLOCK",
        "limitations": [
            "No semantic equivalence judgment of Vision/Scope/Requirements.",
            "No examination of unregistered historic documents or Windows runtime databases.",
            "Actual Windows branch/HEAD and local state must be verified independently.",
        ],
    }
