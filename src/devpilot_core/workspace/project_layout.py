"""R01-14: read-only logical layout projection, never a second bootstrap executor.

Source of execution authority remains the approved GSDLC-03 BootstrapPlan and
its existing Owner-approved executor. This class performs no filesystem writes.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.workspace.project_entry_contracts import (
    PROJECT_INTAKE_GSDLC13_SCHEMA_ID,
    ProjectEntryContractService,
    ProjectIntake,
    stable_sha256,
)

LAYOUT_SCHEMA = "MP132.R01.14.logical-layout.v1"


class ProjectLayoutPlanner:
    """Project-agnostic logical zones, bounded by existing intake/plan authority."""

    def __init__(self, platform_root: Path, *, allowed_roots: Iterable[Path] | None = None) -> None:
        self.root = Path(platform_root).resolve()
        self.intake_service = ProjectEntryContractService(self.root, allowed_roots=allowed_roots)

    @staticmethod
    def _block(code: str, message: str) -> CommandResult:
        return CommandResult("project layout preview", False, ExitCode.BLOCK, message,
                             {"planning_only": True, "writes_performed": False},
                             [Finding(code, message, Severity.BLOCK)])

    def preview(self, *, intake: Mapping[str, Any], bootstrap_plan: Mapping[str, Any]) -> CommandResult:
        """Describe approved neutral-shell paths; never materialize docs or scaffold."""
        try:
            check = self.intake_service.validate_intake(intake)
            if not check.ok:
                return self._block("LAYOUT_INTAKE_NOT_AUTHORIZED", "Project intake is invalid under the existing boundary.")
            normalized = ProjectIntake.from_mapping(intake)
            if normalized.schema_id != PROJECT_INTAKE_GSDLC13_SCHEMA_ID or normalized.entry_mode.value != "CREATE_NEW":
                return self._block("LAYOUT_CREATE_ONLY", "Neutral layout applies only to greenfield CREATE_NEW v2.")
            if (normalized.frontend, normalized.backend, normalized.database) != ("undecided",) * 3:
                return self._block("LAYOUT_TECHNOLOGY_PREMATURE", "Technology remains undecided until Architecture.")
            if not isinstance(bootstrap_plan, Mapping) or not bootstrap_plan.get("planning_only") or bootstrap_plan.get("execution_enabled") is not False:
                return self._block("LAYOUT_APPROVED_PLAN_REQUIRED", "A planning-only BootstrapPlan is required.")
            plan_hash = str(bootstrap_plan.get("plan_hash") or "")
            if len(plan_hash) != 64 or stable_sha256({k:v for k,v in bootstrap_plan.items() if k != "plan_hash"}) != plan_hash:
                return self._block("LAYOUT_PLAN_HASH_DRIFT", "BootstrapPlan hash is inconsistent.")
            if (bootstrap_plan.get("source_intake_hash") != stable_sha256(normalized.to_mapping())
                or bootstrap_plan.get("entry_mode") != "CREATE_NEW"
                or bootstrap_plan.get("project_id") != normalized.project_id
                or Path(str(bootstrap_plan.get("target_root") or "")).resolve() != Path(normalized.target_root).resolve()):
                return self._block("LAYOUT_PLAN_INTAKE_DRIFT", "BootstrapPlan does not correspond to the selected project.")
            if bootstrap_plan.get("network", {}).get("required_by_plan") or bootstrap_plan.get("dependency_jobs") or bootstrap_plan.get("venv", {}).get("required"):
                return self._block("LAYOUT_PREMATURE_EXECUTION", "Neutral shell cannot require network, dependencies or a venv.")
            root = Path(normalized.target_root).resolve()
            rows: list[dict[str, str]] = []
            seen: set[str] = set()
            for key, kind in (("directories", "directory"), ("files", "file")):
                items = bootstrap_plan.get(key)
                if not isinstance(items, list):
                    return self._block("LAYOUT_ROWS_INVALID", "Bootstrap path entries are malformed.")
                for item in items:
                    if not isinstance(item, Mapping):
                        return self._block("LAYOUT_ROWS_INVALID", "Bootstrap path entry is malformed.")
                    rel = item.get("relative_path")
                    if not isinstance(rel, str) or not rel or "\\" in rel or ":" in rel or any(part in ("", ".", "..") for part in rel.split("/")):
                        return self._block("LAYOUT_UNSAFE_PATH", "Unsafe relative project path.")
                    candidate = root.joinpath(*rel.split("/"))
                    if candidate.resolve(strict=False) != Path(str(item.get("absolute_path") or "")).resolve(strict=False):
                        return self._block("LAYOUT_PATH_MISMATCH", "Bootstrap relative and absolute paths disagree.")
                    if not candidate.is_relative_to(root) or any(p.is_symlink() for p in (candidate, *candidate.parents) if p != root):
                        return self._block("LAYOUT_UNSAFE_PATH", "A path escapes the approved project boundary.")
                    if rel in seen or rel.startswith(("frontend/", "backend/")) or rel.endswith(("package.json", "requirements.txt", "pyproject.toml")):
                        return self._block("LAYOUT_PREMATURE_TECH_ARTIFACT", "Duplicate or technology-specific shell path.")
                    seen.add(rel)
                    rows.append({"path": rel, "kind": kind})
            rows.sort(key=lambda r: (r["path"], r["kind"]))
            if not any(r["path"] == "docs/02_architecture" for r in rows):
                return self._block("LAYOUT_ARCHITECTURE_MISSING", "Architecture zone required before technology decision.")
            layout = {
                "schema": LAYOUT_SCHEMA, "project_id": normalized.project_id,
                "target_root": str(root), "source_bootstrap_plan_hash": plan_hash,
                "planning_only": True, "writes_performed": False, "network_used": False,
                "technology_profile": {"status": "PENDING_ARCHITECTURE", "profile_id": None,
                                       "frontend": None, "backend": None, "database": None},
                "logical_paths": rows,
                "documents": {"content_creation": "LAZY_GOVERNED", "standard_reference_seed": True,
                              "generic_templates_autofilled": False},
                "scaffold": {"status": "NOT_AUTHORIZED", "execution_enabled": False,
                             "approval_required_for_future_execution": True},
                "bootstrap_authority": "GSDLC-03 existing approved executor only",
            }
            layout["layout_hash"] = stable_sha256(layout)
            return CommandResult("project layout preview", True, ExitCode.PASS,
                                 "Neutral logical layout projected without workspace mutation.",
                                 {"layout": layout, "writes_performed": False, "network_used": False})
        except (ValueError, TypeError, OSError, KeyError) as exc:
            return self._block("LAYOUT_INPUT_INVALID", type(exc).__name__ + ": " + str(exc)[:120])
