from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import tomllib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

RELEASE_METADATA_ROLES = {"owner", "release-manager"}
RUNTIME_DIR = Path("outputs/runtime/gsdlc11d_release_metadata")
RELEASE_DIR = Path("outputs/release/gsdlc11d")
RELEASE_NOTES_PATH = RELEASE_DIR / "release_notes.md"
VERSION_DECISION_PATH = RELEASE_DIR / "version_decision.json"
TAG_PLAN_PATH = RELEASE_DIR / "tag_plan.json"
APPROVAL_PATH = RELEASE_DIR / "release_approval.json"
TAG_VERIFICATION_PATH = RELEASE_DIR / "tag_verification.json"
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?$")
REF_RE = re.compile(r"\b(?:US|STORY|REQ|RF|RNF|ADR|GSDLC)-[A-Za-z0-9_.-]+\b", re.IGNORECASE)


@dataclass(frozen=True)
class GitAuthority:
    commit: str
    tree: str
    branch: str
    dirty_tracked: bool

    def to_dict(self) -> dict[str, Any]:
        return {"commit": self.commit, "tree": self.tree, "branch": self.branch, "dirty_tracked": self.dirty_tracked}


class ReleaseMetadataApplicationService:
    """GSDLC-11-D governed release metadata, approval and local annotated tag workflow.

    The service is deliberately local-first. It derives release notes only from local
    repository evidence, separates proposal from approval authority, creates an exact
    commit-bound TagPlan, and permits one annotated *local* tag only after a fresh
    server-side owner/release-manager approval bound to the exact plan hash.

    It never pushes, publishes, deploys, calls an external model/API, or grants an
    agent/model approval authority.
    """

    def __init__(self, platform_root: Path, *, context_resolver) -> None:
        self.root = Path(platform_root).resolve()
        self.context_resolver = context_resolver
        self.runtime_dir = self.root / RUNTIME_DIR
        self.release_dir = self.root / RELEASE_DIR

    def status(self, *, actor: str, actor_roles: Iterable[str], workspace_scopes: Iterable[str]) -> CommandResult:
        command = "release metadata status"
        checked = self._authorize(command, actor_roles, workspace_scopes, require_release_role=False)
        if checked is not None:
            return checked
        data = {
            "state": self._state(),
            "version_decision": self._read_json(self.root / VERSION_DECISION_PATH),
            "tag_plan": self._read_json(self.root / TAG_PLAN_PATH),
            "release_approval": self._read_json(self.root / APPROVAL_PATH),
            "tag_verification": self._read_json(self.root / TAG_VERIFICATION_PATH),
            "release_notes_path": RELEASE_NOTES_PATH.as_posix() if (self.root / RELEASE_NOTES_PATH).is_file() else None,
            "authority": {
                "approval_roles": sorted(RELEASE_METADATA_ROLES),
                "model_or_agent_can_approve": False,
                "model_or_agent_can_tag": False,
                "push_or_publish_enabled": False,
            },
            "safety": self._safety(git_tag_mutated=False),
        }
        return CommandResult(command, True, ExitCode.PASS, "Release metadata status collected.", data=data, findings=[])

    def prepare(
        self,
        *,
        actor: str,
        actor_roles: Iterable[str],
        workspace_scopes: Iterable[str],
        mode: str,
        version: str,
        manual_notes: str = "",
        agent_proposal: str = "",
    ) -> CommandResult:
        command = "release metadata prepare"
        checked = self._authorize(command, actor_roles, workspace_scopes, require_release_role=True)
        if checked is not None:
            return checked
        precondition = self._precondition(command)
        if precondition is not None:
            return precondition
        authority = self._git_authority()
        if authority is None or authority.dirty_tracked:
            return self._block(command, "GSDLC11D_GIT_AUTHORITY_BLOCK", "Release metadata preparation requires a clean tracked Git authority.")

        normalized_mode = str(mode or "MANUAL").strip().upper()
        if normalized_mode not in {"MANUAL", "AGENT_ASSISTED"}:
            return self._block(command, "GSDLC11D_NOTES_MODE_BLOCK", "Release notes mode must be MANUAL or AGENT_ASSISTED.")
        version = str(version or "").strip()
        if not SEMVER_RE.fullmatch(version):
            return self._block(command, "GSDLC11D_VERSION_POLICY_BLOCK", "Release version must be valid Semantic Versioning (MAJOR.MINOR.PATCH with optional prerelease/build metadata).", {"version": version})
        project_version = self._project_version()
        package_version = self._package_version_from_local_evidence() or project_version
        if version != project_version or version != package_version:
            return self._block(
                command,
                "GSDLC11D_VERSION_DRIFT_BLOCK",
                "VersionDecision requires exact alignment between requested version, pyproject package version and current release package evidence.",
                {"requested_version": version, "pyproject_version": project_version, "package_version": package_version},
            )

        tag_name = f"v{version}"
        existing = self._tag_target(tag_name)
        if existing is not None:
            return self._block(command, "GSDLC11D_EXISTING_TAG_CONFLICT_BLOCK", "The release tag already exists. GSDLC-11-D fails closed and will not overwrite or move an existing tag.", {"tag_name": tag_name, "existing_target": existing})

        commits = self._recent_commits(limit=24)
        evidence_refs = self._evidence_refs()
        traced_refs = sorted({match.group(0) for item in commits for match in REF_RE.finditer(item.get("subject", ""))})
        proposal = str(agent_proposal or "").strip()
        manual = str(manual_notes or "").strip()
        supplied_text = proposal if normalized_mode == "AGENT_ASSISTED" else manual
        provenance = {
            "mode": normalized_mode,
            "proposal_has_authority": False,
            "approval_separate": True,
            "source_commit": authority.commit,
            "source_tree": authority.tree,
            "source_commits": commits,
            "trace_refs": traced_refs,
            "evidence_refs": evidence_refs,
            "supplied_text_sha256": _sha256_text(supplied_text) if supplied_text else None,
            "network_used": False,
            "external_api_used": False,
        }
        notes = self._render_notes(version=version, authority=authority, commits=commits, evidence_refs=evidence_refs, supplied_text=supplied_text, mode=normalized_mode)
        decision_core = {
            "schema_version": "1.0.0",
            "status": "PASS",
            "decision": "KEEP_CURRENT_PACKAGE_VERSION",
            "version": version,
            "tag_name": tag_name,
            "pyproject_version": project_version,
            "package_version": package_version,
            "source_authority": authority.to_dict(),
            "policy": {"semver_valid": True, "version_alignment": True, "existing_tag_conflict": False},
            "provenance": provenance,
            "safety": self._safety(git_tag_mutated=False),
        }
        decision_hash = _canonical_hash(decision_core)
        version_decision = {**decision_core, "decision_hash": decision_hash, "generated_at_utc": _now()}

        notes_path = self.root / RELEASE_NOTES_PATH
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_text(notes_path, notes)
        self._write_json(self.root / VERSION_DECISION_PATH, version_decision)
        # Any prior plan/approval/verification becomes stale when notes are prepared again.
        for stale in [self.root / TAG_PLAN_PATH, self.root / APPROVAL_PATH, self.root / TAG_VERIFICATION_PATH, self.runtime_dir / "approval.json", self.runtime_dir / "tag_receipt.json"]:
            if stale.exists():
                stale.unlink()
        return CommandResult(
            command,
            True,
            ExitCode.PASS,
            "Release notes and VersionDecision prepared from local traceable evidence.",
            data={"version_decision": version_decision, "release_notes_path": RELEASE_NOTES_PATH.as_posix(), "release_notes_sha256": _sha256_file(notes_path), "provenance": provenance, "safety": self._safety(git_tag_mutated=False)},
            findings=[Finding("GSDLC11D_METADATA_PREPARE_PASS", "VersionDecision and release notes are evidence-derived; proposal authority remains false.", Severity.INFO)],
        )

    def tag_plan(self, *, actor: str, actor_roles: Iterable[str], workspace_scopes: Iterable[str]) -> CommandResult:
        command = "release metadata tag plan"
        checked = self._authorize(command, actor_roles, workspace_scopes, require_release_role=True)
        if checked is not None:
            return checked
        precondition = self._precondition(command)
        if precondition is not None:
            return precondition
        decision = self._read_json(self.root / VERSION_DECISION_PATH)
        notes_path = self.root / RELEASE_NOTES_PATH
        if not decision or decision.get("status") != "PASS" or not notes_path.is_file():
            return self._block(command, "GSDLC11D_METADATA_REQUIRED_BLOCK", "Prepare a PASS VersionDecision and release notes before creating TagPlan.")
        authority = self._git_authority()
        if authority is None or authority.dirty_tracked:
            return self._block(command, "GSDLC11D_GIT_AUTHORITY_BLOCK", "TagPlan requires a clean tracked Git authority.")
        planned_authority = decision.get("source_authority") or {}
        if authority.to_dict() != planned_authority:
            return self._block(command, "GSDLC11D_VERSION_DECISION_STALE_BLOCK", "Git authority changed after VersionDecision; prepare metadata again.")
        tag_name = str(decision.get("tag_name") or "")
        if self._tag_target(tag_name) is not None:
            return self._block(command, "GSDLC11D_EXISTING_TAG_CONFLICT_BLOCK", "TagPlan refuses an already-existing tag.", {"tag_name": tag_name})
        core = {
            "schema_version": "1.0.0",
            "operation": "release.metadata.tag.execute",
            "version": str(decision.get("version")),
            "tag_name": tag_name,
            "message": f"DevPilot Local {decision.get('version')} - GSDLC-11-D governed local release",
            "source_authority": authority.to_dict(),
            "release_notes_path": RELEASE_NOTES_PATH.as_posix(),
            "release_notes_sha256": _sha256_file(notes_path),
            "version_decision_hash": str(decision.get("decision_hash") or ""),
            "approval_required": True,
            "approval_roles": sorted(RELEASE_METADATA_ROLES),
            "annotated": True,
            "push_performed": False,
            "publish_performed": False,
            "dry_run": True,
        }
        plan_hash = _canonical_hash(core)
        plan_id = f"GSDLC11D-TAG-{authority.commit[:12]}-{plan_hash[:12]}"
        plan = {**core, "plan_id": plan_id, "plan_hash": plan_hash, "created_at_utc": _now()}
        self._write_json(self.root / TAG_PLAN_PATH, plan)
        return CommandResult(command, True, ExitCode.PASS, "Exact commit-bound annotated TagPlan created in dry-run mode.", data={"tag_plan": plan, "safety": self._safety(git_tag_mutated=False)}, findings=[Finding("GSDLC11D_TAG_PLAN_PASS", "TagPlan is exact-commit and release-notes hash bound.", Severity.INFO)])

    def approve(
        self,
        *,
        actor: str,
        actor_roles: Iterable[str],
        workspace_scopes: Iterable[str],
        plan_id: str,
        plan_hash: str,
        reason: str,
        ttl_minutes: int = 30,
    ) -> CommandResult:
        command = "release metadata approve"
        checked = self._authorize(command, actor_roles, workspace_scopes, require_release_role=True)
        if checked is not None:
            return checked
        plan = self._bound_tag_plan(command, plan_id=plan_id, plan_hash=plan_hash)
        if isinstance(plan, CommandResult):
            return plan
        ttl = max(5, min(int(ttl_minutes), 120))
        now = datetime.now(timezone.utc)
        approval_core = {
            "schema_version": "1.0.0",
            "status": "APPROVED",
            "approval_id": f"GSDLC11D-APPROVAL-{plan_hash[:16]}",
            "plan_id": plan_id,
            "plan_hash": plan_hash,
            "tag_name": plan["tag_name"],
            "target_commit": plan["source_authority"]["commit"],
            "actor": actor,
            "actor_roles": sorted({str(role) for role in actor_roles}),
            "authority_source": "server-authenticated-human-session",
            "reason": str(reason or "Release approval after reviewed TagPlan.").strip(),
            "issued_at_utc": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
            "expires_at_utc": (now + timedelta(minutes=ttl)).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "model_or_agent_authority": False,
            "push_or_publish_authorized": False,
        }
        approval_hash = _canonical_hash(approval_core)
        approval = {**approval_core, "approval_hash": approval_hash}
        self._write_json(self.root / APPROVAL_PATH, approval)
        self._write_json(self.runtime_dir / "approval.json", approval)
        return CommandResult(command, True, ExitCode.PASS, "Release approval recorded server-side and bound to exact TagPlan hash.", data={"release_approval": approval, "safety": self._safety(git_tag_mutated=False)}, findings=[Finding("GSDLC11D_RELEASE_APPROVAL_PASS", "Human release authority is bound to the exact TagPlan/hash.", Severity.INFO)])

    def tag_execute(
        self,
        *,
        actor: str,
        actor_roles: Iterable[str],
        workspace_scopes: Iterable[str],
        plan_id: str,
        plan_hash: str,
        approval_id: str,
    ) -> CommandResult:
        command = "release metadata tag execute"
        checked = self._authorize(command, actor_roles, workspace_scopes, require_release_role=True)
        if checked is not None:
            return checked
        plan = self._bound_tag_plan(command, plan_id=plan_id, plan_hash=plan_hash)
        if isinstance(plan, CommandResult):
            return plan
        approval = self._read_json(self.root / APPROVAL_PATH)
        approval_failure = self._validate_approval(approval, plan=plan, approval_id=approval_id)
        if approval_failure is not None:
            return approval_failure

        prior = self._read_json(self.runtime_dir / "tag_receipt.json")
        if prior and prior.get("status") == "PASS" and prior.get("plan_hash") == plan_hash and prior.get("approval_id") == approval_id:
            if self._tag_target(str(plan["tag_name"])) == str(plan["source_authority"]["commit"]):
                return CommandResult(command, True, ExitCode.PASS, "Prior exact tag receipt remains valid; tag execution reused without mutation.", data={"tag_verification": prior, "reused": True, "safety": self._safety(git_tag_mutated=False)}, findings=[Finding("GSDLC11D_TAG_EXECUTE_REUSED_PASS", "Existing receipt proves the exact governed tag mutation was already completed.", Severity.INFO)])

        tag_name = str(plan["tag_name"])
        if self._tag_target(tag_name) is not None:
            return self._block(command, "GSDLC11D_EXISTING_TAG_CONFLICT_BLOCK", "Tag execution refuses to overwrite or move any pre-existing tag.", {"tag_name": tag_name})
        authority = self._git_authority()
        if authority is None or authority.dirty_tracked or authority.to_dict() != plan["source_authority"]:
            return self._block(command, "GSDLC11D_TAG_AUTHORITY_STALE_BLOCK", "Git authority changed after approval; tag execution is stale.")

        remotes_before = self._git_output("remote", "-v") or ""
        create = subprocess.run(
            ["git", "-C", str(self.root), "tag", "-a", tag_name, authority.commit, "-m", str(plan["message"])],
            capture_output=True,
            text=True,
            check=False,
        )
        if create.returncode != 0:
            return self._block(command, "GSDLC11D_TAG_CREATE_BLOCK", "Annotated local tag creation failed.", {"stderr": (create.stderr or "")[-1200:]})
        target = self._tag_target(tag_name)
        tag_type = self._git_output("cat-file", "-t", f"refs/tags/{tag_name}") or ""
        remotes_after = self._git_output("remote", "-v") or ""
        if target != authority.commit or tag_type.strip() != "tag" or remotes_before != remotes_after:
            return self._block(command, "GSDLC11D_TAG_VERIFY_BLOCK", "Post-tag verification failed exact commit, annotated-object or remote-configuration invariants.", {"target": target, "expected": authority.commit, "tag_type": tag_type})

        verification = {
            "schema_version": "1.0.0",
            "status": "PASS",
            "plan_id": plan_id,
            "plan_hash": plan_hash,
            "approval_id": approval_id,
            "tag_name": tag_name,
            "annotated": True,
            "tag_object_type": tag_type.strip(),
            "tag_target_commit": target,
            "expected_commit": authority.commit,
            "exact_commit_match": target == authority.commit,
            "remote_configuration_unchanged": remotes_before == remotes_after,
            "push_performed": False,
            "publish_performed": False,
            "deploy_performed": False,
            "network_used": False,
            "external_api_used": False,
            "secrets_exposed": False,
            "verified_at_utc": _now(),
        }
        self._write_json(self.root / TAG_VERIFICATION_PATH, verification)
        self._write_json(self.runtime_dir / "tag_receipt.json", verification)
        return CommandResult(command, True, ExitCode.PASS, "Annotated local tag created and verified on the exact approved commit.", data={"tag_verification": verification, "reused": False, "safety": self._safety(git_tag_mutated=True)}, findings=[Finding("GSDLC11D_TAG_EXECUTE_PASS", "Annotated local tag is exact-commit, approval-bound and not pushed/published.", Severity.INFO)])

    # ------------------------------------------------------------------ helpers
    def _precondition(self, command: str) -> CommandResult | None:
        state = self._read_json(self.root / ".devpilot/project_state.json") or {}
        if state.get("gsdlc_11_c_status") != "CLOSED/PASS/WINDOWS-VALIDATED" or state.get("gsdlc_11_d_authorized") is not True:
            return self._block(command, "GSDLC11D_PREDECESSOR_BLOCK", "GSDLC-11-D requires GSDLC-11-C CLOSED/PASS/WINDOWS-VALIDATED and explicit authorization.")
        if int(state.get("gsdlc_11_full_regression_budget_consumed") or 0) != 0:
            return self._block(command, "GSDLC11D_FULL_BUDGET_BLOCK", "GSDLC-11-D must preserve the GSDLC-11 Full Regression budget for 11-E.")
        return None

    def _authorize(self, command: str, actor_roles: Iterable[str], workspace_scopes: Iterable[str], *, require_release_role: bool) -> CommandResult | None:
        context = self.context_resolver.resolve()
        if not context.configured or not context.valid or context.active_workspace_root is None or not context.active_workspace_id:
            return self._block(command, "GSDLC11D_PROJECT_CONTEXT_BLOCK", "Release metadata workbench requires a server-validated active project workspace.")
        scopes = {str(item) for item in workspace_scopes if str(item).strip()}
        workspace_id = str(context.active_workspace_id)
        if scopes and workspace_id not in scopes and "*" not in scopes:
            return self._block(command, "GSDLC11D_WORKSPACE_SCOPE_BLOCK", "Authenticated session is not scoped to the active workspace.")
        roles = {str(item).strip() for item in actor_roles if str(item).strip()}
        if require_release_role and not roles.intersection(RELEASE_METADATA_ROLES):
            return self._block(command, "GSDLC11D_RELEASE_ROLE_BLOCK", "Release metadata/tag operations require owner or release-manager server-side role.")
        return None

    def _bound_tag_plan(self, command: str, *, plan_id: str, plan_hash: str) -> dict[str, Any] | CommandResult:
        plan = self._read_json(self.root / TAG_PLAN_PATH)
        if not plan or plan.get("plan_id") != plan_id or plan.get("plan_hash") != plan_hash:
            return self._block(command, "GSDLC11D_TAG_PLAN_BINDING_BLOCK", "Operation requires the exact current TagPlan id/hash.")
        core = {k: v for k, v in plan.items() if k not in {"plan_id", "plan_hash", "created_at_utc"}}
        if _canonical_hash(core) != plan_hash:
            return self._block(command, "GSDLC11D_TAG_PLAN_HASH_BLOCK", "Stored TagPlan no longer matches its immutable hash.")
        authority = self._git_authority()
        notes_path = self.root / RELEASE_NOTES_PATH
        decision = self._read_json(self.root / VERSION_DECISION_PATH)
        if authority is None or authority.dirty_tracked or authority.to_dict() != plan.get("source_authority"):
            return self._block(command, "GSDLC11D_TAG_PLAN_STALE_BLOCK", "Git authority changed after TagPlan creation.")
        if not notes_path.is_file() or _sha256_file(notes_path) != plan.get("release_notes_sha256"):
            return self._block(command, "GSDLC11D_NOTES_STALE_BLOCK", "Release notes changed after TagPlan creation.")
        if not decision or decision.get("decision_hash") != plan.get("version_decision_hash"):
            return self._block(command, "GSDLC11D_VERSION_DECISION_STALE_BLOCK", "VersionDecision changed after TagPlan creation.")
        return plan

    def _validate_approval(self, approval: dict[str, Any] | None, *, plan: dict[str, Any], approval_id: str) -> CommandResult | None:
        command = "release metadata tag execute"
        if not approval or approval.get("status") != "APPROVED" or approval.get("approval_id") != approval_id:
            return self._block(command, "GSDLC11D_APPROVAL_REQUIRED_BLOCK", "Tag execution requires a valid server-side release approval.")
        if approval.get("plan_id") != plan.get("plan_id") or approval.get("plan_hash") != plan.get("plan_hash") or approval.get("target_commit") != plan.get("source_authority", {}).get("commit"):
            return self._block(command, "GSDLC11D_APPROVAL_HASH_MISMATCH_BLOCK", "Release approval is not bound to the exact current TagPlan/hash/commit.")
        roles = set(approval.get("actor_roles") or [])
        if not roles.intersection(RELEASE_METADATA_ROLES) or approval.get("model_or_agent_authority") is not False:
            return self._block(command, "GSDLC11D_APPROVAL_AUTHORITY_BLOCK", "Only an authorized human owner/release-manager approval can authorize local tagging.")
        try:
            expires = datetime.fromisoformat(str(approval.get("expires_at_utc") or "").replace("Z", "+00:00"))
        except ValueError:
            return self._block(command, "GSDLC11D_APPROVAL_EXPIRY_BLOCK", "Release approval expiry is invalid.")
        if expires <= datetime.now(timezone.utc):
            return self._block(command, "GSDLC11D_APPROVAL_EXPIRED_BLOCK", "Release approval expired before tag execution.")
        return None

    def _state(self) -> str:
        verification = self._read_json(self.root / TAG_VERIFICATION_PATH)
        if verification and verification.get("status") == "PASS":
            return "TAG_VERIFIED"
        approval = self._read_json(self.root / APPROVAL_PATH)
        if approval and approval.get("status") == "APPROVED":
            return "APPROVED"
        plan = self._read_json(self.root / TAG_PLAN_PATH)
        if plan:
            return "TAG_PLAN_READY"
        decision = self._read_json(self.root / VERSION_DECISION_PATH)
        if decision:
            return "METADATA_READY"
        return "NOT_STARTED"

    def _render_notes(self, *, version: str, authority: GitAuthority, commits: list[dict[str, str]], evidence_refs: list[str], supplied_text: str, mode: str) -> str:
        lines = [
            f"# DevPilot Local {version} - release notes",
            "",
            "> Local release candidate. No public publish/deploy is implied by these notes.",
            "",
            "## Provenance",
            "",
            f"- Mode: `{mode}` (proposal only; no approval authority).",
            f"- Exact source commit: `{authority.commit}`.",
            f"- Exact source tree: `{authority.tree}`.",
            "- Derived only from local Git/evidence plus explicitly supplied human/agent proposal text.",
            "- Network/API use: none.",
            "",
            "## Traceable changes from recent commits",
            "",
        ]
        if commits:
            lines.extend([f"- `{item['commit'][:12]}` {item['subject']}" for item in commits])
        else:
            lines.append("- No bounded Git commit subjects were available.")
        lines.extend(["", "## Release evidence references", ""])
        lines.extend([f"- `{item}`" for item in evidence_refs] or ["- No additional bounded release evidence refs were discovered."])
        if supplied_text:
            lines.extend(["", "## Proposed editorial notes", "", supplied_text, ""])
        lines.extend([
            "## Authority and limitations",
            "",
            "- Release approval is separate and must be performed server-side by `owner` or `release-manager`.",
            "- Models/agents may propose wording only and cannot approve, tag, push, publish, deploy, or widen waivers.",
            "- GSDLC-11-D creates at most a local annotated tag after exact-plan approval; remote push/publication remains disabled.",
            "",
        ])
        return "\n".join(lines)

    def _evidence_refs(self) -> list[str]:
        refs: list[str] = []
        preferred = [
            "docs/audits/DEVPL_GSDLC_11_A_IMPLEMENTATION_REPORT.md",
            "docs/audits/DEVPL_GSDLC_11_B_IMPLEMENTATION_REPORT.md",
            "docs/audits/DEVPL_GSDLC_11_C_IMPLEMENTATION_REPORT.md",
            "docs/audits/DEVPL_GSDLC_11_C_SOURCE_DELTA_MANIFEST.json",
            ".devpilot/project_state.json",
        ]
        for rel in preferred:
            if (self.root / rel).is_file():
                refs.append(rel)
        return refs

    def _recent_commits(self, *, limit: int) -> list[dict[str, str]]:
        completed = subprocess.run(
            ["git", "-C", str(self.root), "log", f"-{max(1, min(limit, 50))}", "--pretty=format:%H%x09%s"],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            return []
        items: list[dict[str, str]] = []
        for line in completed.stdout.splitlines():
            commit, sep, subject = line.partition("\t")
            if sep and re.fullmatch(r"[0-9a-fA-F]{40,64}", commit):
                items.append({"commit": commit.lower(), "subject": subject.strip()[:300]})
        return items

    def _project_version(self) -> str:
        data = tomllib.loads((self.root / "pyproject.toml").read_text(encoding="utf-8"))
        return str((data.get("project") or {}).get("version") or "")

    def _package_version_from_local_evidence(self) -> str | None:
        # GSDLC-11-B runtime evidence is preferred when present. Clean source ZIPs
        # intentionally exclude outputs/, so absence is not drift and pyproject is
        # the current source-of-truth fallback.
        candidates = [
            self.root / "outputs/runtime/gsdlc11b_release_package/job_result.json",
            self.root / "outputs/release/gsdlc11b/release_artifact_manifest.json",
        ]
        for path in candidates:
            data = self._read_json(path)
            if not data:
                continue
            for key in ("release_version", "version"):
                value = data.get(key)
                if isinstance(value, str) and value:
                    return value
        return None

    def _git_authority(self) -> GitAuthority | None:
        commit = self._git_output("rev-parse", "HEAD")
        tree = self._git_output("rev-parse", "HEAD^{tree}")
        branch = self._git_output("branch", "--show-current") or "DETACHED"
        status = self._git_output("status", "--porcelain", "--untracked-files=no")
        if not commit or not tree or status is None:
            return None
        return GitAuthority(commit=commit.strip(), tree=tree.strip(), branch=branch.strip() or "DETACHED", dirty_tracked=bool(status.strip()))

    def _tag_target(self, tag_name: str) -> str | None:
        if not tag_name:
            return None
        exists = subprocess.run(["git", "-C", str(self.root), "show-ref", "--verify", "--quiet", f"refs/tags/{tag_name}"], capture_output=True, check=False)
        if exists.returncode != 0:
            return None
        target = self._git_output("rev-list", "-n", "1", tag_name)
        return target.strip() if target else None

    def _git_output(self, *args: str) -> str | None:
        completed = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True, check=False)
        return completed.stdout if completed.returncode == 0 else None

    def _safety(self, *, git_tag_mutated: bool) -> dict[str, Any]:
        return {
            "local_first": True,
            "network_used": False,
            "external_api_used": False,
            "publish_performed": False,
            "deploy_performed": False,
            "push_performed": False,
            "git_tag_mutation_performed": git_tag_mutated,
            "arbitrary_shell_used": False,
            "secrets_exposed": False,
            "model_or_agent_approval_authority": False,
        }

    def _block(self, command: str, finding_id: str, message: str, metadata: dict[str, Any] | None = None) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, message, data={"safety": self._safety(git_tag_mutated=False)}, findings=[Finding(finding_id, message, Severity.BLOCK, metadata=metadata or {})])

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
                handle.flush()
                os.fsync(handle.fileno())
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


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            if not text.endswith("\n"):
                handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
