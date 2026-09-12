from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

RELEASE_LIFECYCLE_ROLES = {"owner", "release-manager"}
RUNTIME_DIR = Path("outputs/runtime/gsdlc11c_release_lifecycle")
RELEASE_DIR = Path("outputs/release/gsdlc11c")
TARGET_DIR = RELEASE_DIR / "controlled-install-target"
BACKUP_ZIP = RELEASE_DIR / "backup-before-upgrade.zip"
BACKUP_MANIFEST = RELEASE_DIR / "backup_manifest.json"
INSTALL_REPORT = RELEASE_DIR / "install_smoke_report.json"
UPGRADE_ROLLBACK_REPORT = RELEASE_DIR / "upgrade_rollback_report.json"
FAULT_MARKER = Path("outputs/runtime/gsdlc11c/controlled_upgrade_fault.json")


@dataclass(frozen=True)
class GitAuthority:
    commit: str
    tree: str
    branch: str
    dirty_tracked: bool

    def to_dict(self) -> dict[str, Any]:
        return {"commit": self.commit, "tree": self.tree, "branch": self.branch, "dirty_tracked": self.dirty_tracked}


class ReleaseLifecycleApplicationService:
    """GSDLC-11-C governed local install / upgrade / rollback workflow.

    Mutations are restricted to a deterministic sandbox under outputs/release/gsdlc11c.
    Source/Git are never changed. No network/package-manager/public release action is used.
    """

    def __init__(self, platform_root: Path, *, context_resolver) -> None:
        self.root = Path(platform_root).resolve()
        self.context_resolver = context_resolver
        self.runtime_dir = self.root / RUNTIME_DIR
        self.release_dir = self.root / RELEASE_DIR
        self.target_dir = self.root / TARGET_DIR
        self.backup_zip = self.root / BACKUP_ZIP
        self.backup_manifest = self.root / BACKUP_MANIFEST

    def status(self, *, actor: str, actor_roles: Iterable[str], workspace_scopes: Iterable[str]) -> CommandResult:
        checked = self._authorize("release lifecycle status", actor_roles, workspace_scopes, require_release_role=False)
        if checked is not None:
            return checked
        payload = {
            "install_plan": self._read_json(self.runtime_dir / "install_plan.json"),
            "install_result": self._read_json(self.runtime_dir / "install_result.json"),
            "upgrade_plan": self._read_json(self.runtime_dir / "upgrade_plan.json"),
            "upgrade_result": self._read_json(self.runtime_dir / "upgrade_result.json"),
            "rollback_plan": self._read_json(self.runtime_dir / "rollback_plan.json"),
            "rollback_result": self._read_json(self.runtime_dir / "rollback_result.json"),
        }
        state = "ROLLBACK_VERIFIED" if (payload["rollback_result"] or {}).get("status") == "PASS" else "ROLLBACK_REQUIRED" if (payload["upgrade_result"] or {}).get("status") == "ROLLBACK_REQUIRED" else "INSTALLED" if (payload["install_result"] or {}).get("status") == "PASS" else "NOT_STARTED"
        return CommandResult(
            command="release lifecycle status",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Release lifecycle status projected.",
            data={"state": state, "lifecycle": payload, "safety": self._safety(mutated=False)},
            findings=[Finding("GSDLC11C_LIFECYCLE_STATUS_PASS", "Install/upgrade/rollback status is available from governed local evidence.", Severity.INFO)],
        )

    def install_plan(self, *, actor: str, actor_roles: Iterable[str], workspace_scopes: Iterable[str]) -> CommandResult:
        command = "release lifecycle install plan"
        checked = self._authorize(command, actor_roles, workspace_scopes, require_release_role=True)
        if checked is not None:
            return checked
        pre = self._precondition()
        if pre is not None:
            return pre
        package = self._package_receipt()
        if isinstance(package, CommandResult):
            return package
        authority = self._git_authority()
        if authority is None or authority.dirty_tracked:
            return self._block(command, "GSDLC11C_GIT_AUTHORITY_BLOCK", "Install planning requires a clean tracked Git authority.")
        if package["source_authority"]["commit"] != authority.commit or package["source_authority"]["tree"] != authority.tree:
            return self._block(command, "GSDLC11C_PACKAGE_AUTHORITY_STALE_BLOCK", "Release package commit/tree does not match the active Git authority.")
        plan_core = {
            "schema_version": "1.0.0",
            "operation": "release.lifecycle.install.execute",
            "source_authority": authority.to_dict(),
            "package": {"path": package["artifact"]["path"], "sha256": package["artifact"]["sha256"], "file_count": package["artifact"].get("file_count")},
            "target": TARGET_DIR.as_posix(),
            "release_version": self._project_version(),
            "dry_run": True,
            "clean_target_required": True,
            "network_used": False,
            "external_api_used": False,
            "production_data_allowed": False,
            "arbitrary_shell_used": False,
        }
        plan_hash = _canonical_hash(plan_core)
        plan = {**plan_core, "plan_id": f"GSDLC11C-INSTALL-{authority.commit[:12]}-{plan_hash[:12]}", "plan_hash": plan_hash, "created_at_utc": _now()}
        self._write_json(self.runtime_dir / "install_plan.json", plan)
        return CommandResult(command=command, ok=True, exit_code=ExitCode.PASS, message="Clean-install dry-run plan created.", data={"plan": plan, "safety": self._safety(mutated=False)}, findings=[Finding("GSDLC11C_INSTALL_PLAN_PASS", "InstallPlan is package/commit-bound and targets only the controlled local sandbox.", Severity.INFO)])

    def install_execute(self, *, actor: str, actor_roles: Iterable[str], workspace_scopes: Iterable[str], plan_id: str, plan_hash: str) -> CommandResult:
        command = "release lifecycle install execute"
        checked = self._authorize(command, actor_roles, workspace_scopes, require_release_role=True)
        if checked is not None:
            return checked
        plan = self._bound_plan("install_plan.json", plan_id, plan_hash)
        if isinstance(plan, CommandResult):
            return plan
        package = self.root / str(plan["package"]["path"])
        if not package.is_file() or _sha256_file(package) != plan["package"]["sha256"]:
            return self._block(command, "GSDLC11C_INSTALL_PACKAGE_HASH_BLOCK", "Install package is missing or no longer matches the planned SHA-256.")
        prior = self._read_json(self.runtime_dir / "install_result.json")
        if prior and prior.get("status") == "PASS" and prior.get("plan_hash") == plan_hash and self.target_dir.is_dir() and _tree_hash(self.target_dir) == prior.get("installed_tree_sha256"):
            return CommandResult(command=command, ok=True, exit_code=ExitCode.PASS, message="Clean-install PASS evidence reused.", data={"install": prior, "reused": True, "safety": self._safety(mutated=False)}, findings=[Finding("GSDLC11C_INSTALL_REUSED_PASS", "Hash-bound install evidence remains valid; install was not repeated.", Severity.INFO)])
        self._assert_controlled_target(self.target_dir)
        staging = self.release_dir / ".install-staging"
        self._safe_remove(staging)
        self._safe_remove(self.target_dir)
        staging.mkdir(parents=True, exist_ok=True)
        try:
            _safe_extract(package, staging)
            expected_version = str(plan["release_version"])
            actual_version = _pyproject_version(staging)
            if actual_version != expected_version:
                return self._block(command, "GSDLC11C_INSTALL_VERSION_BLOCK", "Extracted package version does not match the planned release version.", {"expected": expected_version, "actual": actual_version})
            capability = _capability_probe(staging)
            if not capability["ok"]:
                return self._block(command, "GSDLC11C_INSTALL_CAPABILITY_BLOCK", "Installed sandbox failed the minimal import/capability probe.", capability)
            staging.replace(self.target_dir)
        finally:
            if staging.exists():
                self._safe_remove(staging)
        installed_hash = _tree_hash(self.target_dir)
        report = {
            "schema_version": "1.0.0", "status": "PASS", "generated_at_utc": _now(),
            "source_authority": plan["source_authority"], "plan_id": plan_id, "plan_hash": plan_hash,
            "package": {**plan["package"], "verified": True}, "release_version": plan["release_version"],
            "target": TARGET_DIR.as_posix(), "installed_tree_sha256": installed_hash,
            "checks": {"safe_extract": True, "version_match": True, "package_sha256_match": True, "minimal_capability": capability},
            "safety": self._safety(mutated=True),
            "limitations": ["GSDLC-11-C clean install is a controlled local source-package sandbox smoke, not a system-wide installer.", "No pip/npm/network/service installation is performed."],
        }
        self._write_json(self.root / INSTALL_REPORT, report)
        receipt = {**report, "report": INSTALL_REPORT.as_posix()}
        self._write_json(self.runtime_dir / "install_result.json", receipt)
        return CommandResult(command=command, ok=True, exit_code=ExitCode.PASS, message="Controlled clean-install smoke passed.", data={"install": receipt, "reused": False, "safety": self._safety(mutated=True)}, findings=[Finding("GSDLC11C_INSTALL_EXECUTE_PASS", "Controlled install target was extracted and capability-verified without production data or network.", Severity.INFO)])

    def upgrade_plan(self, *, actor: str, actor_roles: Iterable[str], workspace_scopes: Iterable[str]) -> CommandResult:
        command = "release lifecycle upgrade plan"
        checked = self._authorize(command, actor_roles, workspace_scopes, require_release_role=True)
        if checked is not None:
            return checked
        install = self._read_json(self.runtime_dir / "install_result.json")
        if not install or install.get("status") != "PASS" or not self.target_dir.is_dir() or _tree_hash(self.target_dir) != install.get("installed_tree_sha256"):
            return self._block(command, "GSDLC11C_INSTALL_EVIDENCE_BLOCK", "Upgrade planning requires intact clean-install PASS evidence.")
        authority = self._git_authority()
        if authority is None or authority.dirty_tracked or authority.to_dict() != install.get("source_authority"):
            return self._block(command, "GSDLC11C_UPGRADE_AUTHORITY_BLOCK", "Upgrade planning requires the same clean Git authority used by the install.")
        plan_core = {
            "schema_version": "1.0.0", "operation": "release.lifecycle.upgrade.execute",
            "source_authority": authority.to_dict(), "install_tree_sha256": install["installed_tree_sha256"],
            "target": TARGET_DIR.as_posix(), "backup_required_before_mutation": True,
            "backup_zip": BACKUP_ZIP.as_posix(), "backup_manifest": BACKUP_MANIFEST.as_posix(),
            "fault_injection": {"enabled": True, "scope": "controlled-sandbox-only", "marker": FAULT_MARKER.as_posix()},
            "version_policy": {"release_version": install["release_version"], "version_mutation_performed": False, "reason": "GSDLC-11-D owns release version/tag decisions."},
            "approval_policy": {"required": False, "reason": "Mutation is restricted to an isolated disposable sandbox; owner/release-manager RBAC plus exact-plan binding is the applicable authority for 11-C."},
            "dry_run": True, "network_used": False, "external_api_used": False, "production_data_allowed": False,
        }
        plan_hash = _canonical_hash(plan_core)
        plan = {**plan_core, "plan_id": f"GSDLC11C-UPGRADE-{authority.commit[:12]}-{plan_hash[:12]}", "plan_hash": plan_hash, "created_at_utc": _now()}
        self._write_json(self.runtime_dir / "upgrade_plan.json", plan)
        return CommandResult(command=command, ok=True, exit_code=ExitCode.PASS, message="Upgrade dry-run plan created with mandatory pre-mutation backup.", data={"plan": plan, "safety": self._safety(mutated=False)}, findings=[Finding("GSDLC11C_UPGRADE_PLAN_PASS", "Upgrade plan is exact-target/hash-bound and requires backup before controlled mutation.", Severity.INFO)])

    def upgrade_execute(self, *, actor: str, actor_roles: Iterable[str], workspace_scopes: Iterable[str], plan_id: str, plan_hash: str) -> CommandResult:
        command = "release lifecycle upgrade execute"
        checked = self._authorize(command, actor_roles, workspace_scopes, require_release_role=True)
        if checked is not None:
            return checked
        plan = self._bound_plan("upgrade_plan.json", plan_id, plan_hash)
        if isinstance(plan, CommandResult):
            return plan
        prior = self._read_json(self.runtime_dir / "upgrade_result.json")
        if (
            prior
            and prior.get("status") == "ROLLBACK_REQUIRED"
            and prior.get("plan_hash") == plan_hash
            and self._backup_valid(prior.get("backup") or {})
            and self.target_dir.is_dir()
            and _tree_hash(self.target_dir) == prior.get("faulted_tree_sha256")
            and (self.target_dir / FAULT_MARKER).is_file()
        ):
            return CommandResult(command=command, ok=True, exit_code=ExitCode.PASS, message="Controlled upgrade/fault evidence reused; rollback remains required.", data={"upgrade": prior, "reused": True, "safety": self._safety(mutated=False)}, findings=[Finding("GSDLC11C_UPGRADE_REUSED_PASS", "Hash-bound fault-injection evidence remains valid; mutation was not repeated.", Severity.INFO)])
        if not self.target_dir.is_dir() or _tree_hash(self.target_dir) != plan["install_tree_sha256"]:
            return self._block(command, "GSDLC11C_UPGRADE_PREIMAGE_BLOCK", "Controlled install target changed after upgrade planning and no intact prior upgrade receipt can be reused.")
        self.release_dir.mkdir(parents=True, exist_ok=True)
        backup = _deterministic_backup(self.target_dir, self.backup_zip)
        manifest = {"schema_version": "1.0.0", "created_at_utc": _now(), "target": TARGET_DIR.as_posix(), "pre_upgrade_tree_sha256": plan["install_tree_sha256"], **backup}
        self._write_json(self.backup_manifest, manifest)
        if not self._backup_valid({"zip": BACKUP_ZIP.as_posix(), "manifest": BACKUP_MANIFEST.as_posix(), "zip_sha256": backup["zip_sha256"], "pre_upgrade_tree_sha256": plan["install_tree_sha256"]}):
            return self._block(command, "GSDLC11C_BACKUP_VERIFY_BLOCK", "Backup was not verifiable before the controlled upgrade mutation.")
        marker = self.target_dir / FAULT_MARKER
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps({"fault": "GSDLC-11-C-CONTROLLED", "injected_at_utc": _now(), "production_data": False}, indent=2) + "\n", encoding="utf-8")
        after_hash = _tree_hash(self.target_dir)
        if after_hash == plan["install_tree_sha256"]:
            return self._block(command, "GSDLC11C_FAULT_INJECTION_BLOCK", "Controlled fault injection did not alter the sandbox target as expected.")
        receipt = {
            "schema_version": "1.0.0", "status": "ROLLBACK_REQUIRED", "generated_at_utc": _now(), "plan_id": plan_id, "plan_hash": plan_hash,
            "source_authority": plan["source_authority"], "target": TARGET_DIR.as_posix(),
            "pre_upgrade_tree_sha256": plan["install_tree_sha256"], "faulted_tree_sha256": after_hash,
            "backup": {"zip": BACKUP_ZIP.as_posix(), "manifest": BACKUP_MANIFEST.as_posix(), "zip_sha256": backup["zip_sha256"], "pre_upgrade_tree_sha256": plan["install_tree_sha256"], "verified_before_mutation": True},
            "fault_injection": {"performed": True, "marker": FAULT_MARKER.as_posix(), "production_data": False},
            "approval_policy": plan["approval_policy"], "safety": self._safety(mutated=True),
        }
        self._write_json(self.runtime_dir / "upgrade_result.json", receipt)
        self._write_upgrade_rollback_report(upgrade=receipt, rollback=None)
        return CommandResult(command=command, ok=True, exit_code=ExitCode.PASS, message="Controlled upgrade fault injected after verified backup; rollback is required.", data={"upgrade": receipt, "reused": False, "safety": self._safety(mutated=True)}, findings=[Finding("GSDLC11C_UPGRADE_FAULT_INJECTED_PASS", "Backup was verified before sandbox-only mutation; rollback workflow is now required.", Severity.INFO)])

    def rollback_plan(self, *, actor: str, actor_roles: Iterable[str], workspace_scopes: Iterable[str]) -> CommandResult:
        command = "release lifecycle rollback plan"
        checked = self._authorize(command, actor_roles, workspace_scopes, require_release_role=True)
        if checked is not None:
            return checked
        upgrade = self._read_json(self.runtime_dir / "upgrade_result.json")
        if not upgrade or upgrade.get("status") != "ROLLBACK_REQUIRED" or not self._backup_valid(upgrade.get("backup") or {}):
            return self._block(command, "GSDLC11C_ROLLBACK_PRECONDITION_BLOCK", "Rollback plan requires verified backup plus controlled upgrade-fault evidence.")
        if not (self.target_dir / FAULT_MARKER).is_file():
            return self._block(command, "GSDLC11C_ROLLBACK_FAULT_MARKER_BLOCK", "Rollback plan requires the expected controlled fault marker.")
        core = {
            "schema_version": "1.0.0", "operation": "release.lifecycle.rollback.execute",
            "source_authority": upgrade["source_authority"], "target": TARGET_DIR.as_posix(),
            "backup": upgrade["backup"], "expected_restored_tree_sha256": upgrade["pre_upgrade_tree_sha256"],
            "approval_policy": {"required": False, "reason": "Rollback is restricted to the same disposable controlled sandbox; owner/release-manager RBAC plus exact-plan binding is the applicable authority."},
            "dry_run": True, "network_used": False, "external_api_used": False, "production_data_allowed": False,
        }
        plan_hash = _canonical_hash(core)
        plan = {**core, "plan_id": f"GSDLC11C-ROLLBACK-{plan_hash[:16]}", "plan_hash": plan_hash, "created_at_utc": _now()}
        self._write_json(self.runtime_dir / "rollback_plan.json", plan)
        return CommandResult(command=command, ok=True, exit_code=ExitCode.PASS, message="Rollback dry-run plan created from verified backup evidence.", data={"plan": plan, "safety": self._safety(mutated=False)}, findings=[Finding("GSDLC11C_ROLLBACK_PLAN_PASS", "Rollback plan is bound to backup hash and expected restored tree hash.", Severity.INFO)])

    def rollback_execute(self, *, actor: str, actor_roles: Iterable[str], workspace_scopes: Iterable[str], plan_id: str, plan_hash: str) -> CommandResult:
        command = "release lifecycle rollback execute"
        checked = self._authorize(command, actor_roles, workspace_scopes, require_release_role=True)
        if checked is not None:
            return checked
        plan = self._bound_plan("rollback_plan.json", plan_id, plan_hash)
        if isinstance(plan, CommandResult):
            return plan
        prior = self._read_json(self.runtime_dir / "rollback_result.json")
        expected = str(plan["expected_restored_tree_sha256"])
        if prior and prior.get("status") == "PASS" and prior.get("plan_hash") == plan_hash and self.target_dir.is_dir() and _tree_hash(self.target_dir) == expected:
            return CommandResult(command=command, ok=True, exit_code=ExitCode.PASS, message="Verified rollback PASS evidence reused.", data={"rollback": prior, "reused": True, "safety": self._safety(mutated=False)}, findings=[Finding("GSDLC11C_ROLLBACK_REUSED_PASS", "Restored hash remains valid; rollback was not repeated.", Severity.INFO)])
        if not self._backup_valid(plan.get("backup") or {}):
            return self._block(command, "GSDLC11C_ROLLBACK_BACKUP_BLOCK", "Rollback backup or manifest hash is no longer valid.")
        staging = self.release_dir / ".rollback-staging"
        self._safe_remove(staging)
        staging.mkdir(parents=True, exist_ok=True)
        try:
            _safe_extract(self.backup_zip, staging)
            staging_hash = _tree_hash(staging)
            if staging_hash != expected:
                return self._block(command, "GSDLC11C_ROLLBACK_BACKUP_TREE_BLOCK", "Backup content does not reconstruct the expected pre-upgrade tree hash.", {"expected": expected, "actual": staging_hash})
            capability = _capability_probe(staging)
            if not capability["ok"]:
                return self._block(command, "GSDLC11C_ROLLBACK_CAPABILITY_BLOCK", "Restored staging target failed the minimal capability probe.", capability)
            self._safe_remove(self.target_dir)
            staging.replace(self.target_dir)
        finally:
            if staging.exists():
                self._safe_remove(staging)
        restored = _tree_hash(self.target_dir)
        receipt = {
            "schema_version": "1.0.0", "status": "PASS", "generated_at_utc": _now(), "plan_id": plan_id, "plan_hash": plan_hash,
            "source_authority": plan["source_authority"], "target": TARGET_DIR.as_posix(), "restored_tree_sha256": restored,
            "expected_restored_tree_sha256": expected, "hash_parity": restored == expected,
            "fault_marker_absent": not (self.target_dir / FAULT_MARKER).exists(), "capability": capability,
            "backup": plan["backup"], "safety": self._safety(mutated=True),
        }
        if not receipt["hash_parity"] or not receipt["fault_marker_absent"]:
            return self._block(command, "GSDLC11C_ROLLBACK_VERIFY_BLOCK", "Rollback completed but restore proof did not match the pre-upgrade state.", receipt)
        self._write_json(self.runtime_dir / "rollback_result.json", receipt)
        self._write_upgrade_rollback_report(upgrade=self._read_json(self.runtime_dir / "upgrade_result.json"), rollback=receipt)
        return CommandResult(command=command, ok=True, exit_code=ExitCode.PASS, message="Rollback restored and verified the controlled install target.", data={"rollback": receipt, "reused": False, "safety": self._safety(mutated=True)}, findings=[Finding("GSDLC11C_ROLLBACK_EXECUTE_PASS", "Rollback restore verified by exact tree hash and capability probe.", Severity.INFO)])

    def _package_receipt(self) -> dict[str, Any] | CommandResult:
        receipt = self._read_json(self.root / "outputs/runtime/gsdlc11b_release_package/job_result.json")
        if not receipt or receipt.get("status") != "PASS" or not (receipt.get("reproducibility") or {}).get("package_byte_reproducible"):
            return self._block("release lifecycle install plan", "GSDLC11C_PACKAGE_PRECONDITION_BLOCK", "11-C requires a PASS commit-bound reproducible package produced by the GSDLC-11-B workbench in the active project.")
        artifact = self.root / str((receipt.get("artifact") or {}).get("path") or "")
        if not artifact.is_file() or _sha256_file(artifact) != str((receipt.get("artifact") or {}).get("sha256") or ""):
            return self._block("release lifecycle install plan", "GSDLC11C_PACKAGE_ARTIFACT_BLOCK", "11-B package artifact is missing or checksum-invalid.")
        return receipt

    def _precondition(self) -> CommandResult | None:
        state = self._read_json(self.root / ".devpilot/project_state.json") or {}
        if state.get("gsdlc_11_b_status") != "CLOSED/PASS/WINDOWS-VALIDATED" or state.get("gsdlc_11_c_authorized") is not True:
            return self._block("release lifecycle install plan", "GSDLC11C_PREDECESSOR_BLOCK", "GSDLC-11-C requires GSDLC-11-B CLOSED/PASS/WINDOWS-VALIDATED and explicit authorization.")
        if int(state.get("gsdlc_11_full_regression_budget_consumed") or 0) != 0:
            return self._block("release lifecycle install plan", "GSDLC11C_FULL_BUDGET_BLOCK", "GSDLC-11-C must not consume the GSDLC-11 Full Regression budget.")
        return None

    def _authorize(self, command: str, actor_roles: Iterable[str], workspace_scopes: Iterable[str], *, require_release_role: bool) -> CommandResult | None:
        context = self.context_resolver.resolve()
        if not context.configured or not context.valid or context.active_workspace_root is None or not context.active_workspace_id:
            return self._block(command, "GSDLC11C_PROJECT_CONTEXT_BLOCK", "Release lifecycle workbench requires a server-validated active project workspace.")
        scopes = {str(item) for item in workspace_scopes if str(item).strip()}
        workspace_id = str(context.active_workspace_id)
        if scopes and workspace_id not in scopes and "*" not in scopes:
            return self._block(command, "GSDLC11C_WORKSPACE_SCOPE_BLOCK", "Authenticated session is not scoped to the active workspace.")
        roles = {str(item).strip() for item in actor_roles if str(item).strip()}
        if require_release_role and not roles.intersection(RELEASE_LIFECYCLE_ROLES):
            return self._block(command, "GSDLC11C_RELEASE_ROLE_BLOCK", "Install/upgrade/rollback plan/execute requires owner or release-manager server-side role.")
        return None

    def _bound_plan(self, filename: str, plan_id: str, plan_hash: str) -> dict[str, Any] | CommandResult:
        plan = self._read_json(self.runtime_dir / filename)
        if not plan or plan.get("plan_id") != plan_id or plan.get("plan_hash") != plan_hash:
            return self._block("release lifecycle execute", "GSDLC11C_PLAN_BINDING_BLOCK", "Execute requires the exact current typed plan id/hash.")
        core = {k: v for k, v in plan.items() if k not in {"plan_id", "plan_hash", "created_at_utc"}}
        if _canonical_hash(core) != plan_hash:
            return self._block("release lifecycle execute", "GSDLC11C_PLAN_HASH_BLOCK", "Stored lifecycle plan no longer matches its immutable hash.")
        authority = self._git_authority()
        if authority is None or authority.dirty_tracked or authority.to_dict() != plan.get("source_authority"):
            return self._block("release lifecycle execute", "GSDLC11C_PLAN_AUTHORITY_STALE_BLOCK", "Git authority changed after planning.")
        return plan

    def _git_authority(self) -> GitAuthority | None:
        def run(*args: str) -> str | None:
            completed = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True, check=False)
            return completed.stdout.strip() if completed.returncode == 0 else None
        commit = run("rev-parse", "HEAD"); tree = run("rev-parse", "HEAD^{tree}"); branch = run("branch", "--show-current") or "DETACHED"; status = run("status", "--porcelain", "--untracked-files=no")
        if not commit or not tree or status is None:
            return None
        return GitAuthority(commit=commit, tree=tree, branch=branch, dirty_tracked=bool(status.strip()))

    def _project_version(self) -> str:
        data = tomllib.loads((self.root / "pyproject.toml").read_text(encoding="utf-8"))
        return str((data.get("project") or {}).get("version") or "0.1.0")

    def _backup_valid(self, backup: dict[str, Any]) -> bool:
        zip_rel = str(backup.get("zip") or ""); manifest_rel = str(backup.get("manifest") or "")
        if zip_rel != BACKUP_ZIP.as_posix() or manifest_rel != BACKUP_MANIFEST.as_posix() or not self.backup_zip.is_file() or not self.backup_manifest.is_file():
            return False
        manifest = self._read_json(self.backup_manifest) or {}
        return _sha256_file(self.backup_zip) == str(backup.get("zip_sha256") or "") == str(manifest.get("zip_sha256") or "") and str(manifest.get("pre_upgrade_tree_sha256") or "") == str(backup.get("pre_upgrade_tree_sha256") or "")

    def _assert_controlled_target(self, path: Path) -> None:
        expected = self.target_dir.resolve(strict=False)
        if path.resolve(strict=False) != expected:
            raise RuntimeError("GSDLC11C controlled target mismatch")

    def _safe_remove(self, path: Path) -> None:
        allowed = self.release_dir.resolve(strict=False)
        resolved = path.resolve(strict=False)
        try:
            resolved.relative_to(allowed)
        except ValueError as exc:
            raise RuntimeError("GSDLC11C refuses to remove paths outside its controlled release sandbox") from exc
        if path.is_symlink():
            path.unlink()
        elif path.exists():
            shutil.rmtree(path)

    def _write_upgrade_rollback_report(self, *, upgrade: dict[str, Any] | None, rollback: dict[str, Any] | None) -> None:
        status = "PASS" if rollback and rollback.get("status") == "PASS" else "ROLLBACK_REQUIRED"
        report = {
            "schema_version": "1.0.0", "status": status, "generated_at_utc": _now(),
            "upgrade": upgrade, "rollback": rollback,
            "restore_verified": bool(rollback and rollback.get("hash_parity") and rollback.get("fault_marker_absent")),
            "backup_required_before_mutation": True,
            "production_data_touched": False,
            "safety": self._safety(mutated=True),
            "limitations": ["GSDLC-11-C validates install/upgrade/rollback only against a disposable local sandbox.", "System-wide installers, production data migration, service installation and remote deployment remain out of scope."],
        }
        self._write_json(self.root / UPGRADE_ROLLBACK_REPORT, report)

    def _safety(self, *, mutated: bool) -> dict[str, Any]:
        return {"local_first": True, "network_used": False, "external_api_used": False, "publish_performed": False, "deploy_performed": False, "source_mutations_performed": False, "git_mutations_performed": False, "sandbox_mutations_performed": mutated, "production_data_touched": False, "arbitrary_shell_used": False, "secrets_exposed": False}

    def _block(self, command: str, finding_id: str, message: str, metadata: dict[str, Any] | None = None) -> CommandResult:
        return CommandResult(command=command, ok=False, exit_code=ExitCode.BLOCK, message=message, data={"safety": self._safety(mutated=False)}, findings=[Finding(finding_id, message, Severity.BLOCK, metadata=metadata or {})])

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any] | None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
                handle.flush(); os.fsync(handle.fileno())
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _canonical_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _pyproject_version(root: Path) -> str:
    path = root / "pyproject.toml"
    if not path.is_file():
        return ""
    return str((tomllib.loads(path.read_text(encoding="utf-8")).get("project") or {}).get("version") or "")


def _tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        h.update(rel.encode("utf-8")); h.update(b"\0"); h.update(_sha256_file(path).encode("ascii")); h.update(b"\n")
    return h.hexdigest()


def _safe_extract(zip_path: Path, destination: Path) -> None:
    dest = destination.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            name = info.filename.replace("\\", "/")
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts or not pure.parts:
                raise ValueError(f"unsafe ZIP entry: {name}")
            # Symlink bit in Unix external attrs.
            mode = (info.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                raise ValueError(f"symlink ZIP entry blocked: {name}")
            target = (dest / Path(*pure.parts)).resolve(strict=False)
            try:
                target.relative_to(dest)
            except ValueError as exc:
                raise ValueError(f"ZIP path escape: {name}") from exc
        archive.extractall(dest)


def _capability_probe(target: Path) -> dict[str, Any]:
    code = "import json,pathlib,devpilot_core; from devpilot_core import cli; p=pathlib.Path(devpilot_core.__file__).resolve(); print(json.dumps({'module_path':str(p),'cli_main_callable':callable(cli.main)}))"
    env = os.environ.copy(); env["PYTHONPATH"] = str((target / "src").resolve()); env["PIP_NO_INDEX"] = "1"; env["PYTHONDONTWRITEBYTECODE"] = "1"; env.pop("PYTHONHOME", None)
    run = subprocess.run([sys.executable, "-B", "-c", code], cwd=str(target), env=env, capture_output=True, text=True, timeout=30, check=False)
    payload: dict[str, Any] = {}
    try:
        payload = json.loads((run.stdout or "{}").strip().splitlines()[-1])
    except Exception:
        payload = {}
    module_path = str(payload.get("module_path") or "")
    inside = False
    try:
        Path(module_path).resolve().relative_to((target / "src").resolve()); inside = True
    except Exception:
        inside = False
    return {"ok": run.returncode == 0 and inside and payload.get("cli_main_callable") is True, "returncode": run.returncode, "module_from_target": inside, "cli_main_callable": payload.get("cli_main_callable") is True, "stderr_tail": (run.stderr or "")[-1000:], "network_used": False}


def _deterministic_backup(source: Path, zip_path: Path) -> dict[str, Any]:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    temp = zip_path.with_suffix(zip_path.suffix + ".tmp")
    if temp.exists(): temp.unlink()
    files = sorted((p for p in source.rglob("*") if p.is_file()), key=lambda p: p.relative_to(source).as_posix())
    with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            rel = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(1980,1,1,0,0,0)); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes())
    os.replace(temp, zip_path)
    return {"zip": BACKUP_ZIP.as_posix(), "zip_sha256": _sha256_file(zip_path), "files_total": len(files), "source_tree_sha256": _tree_hash(source)}
