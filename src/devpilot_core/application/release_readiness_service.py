from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.story_execution import StoryExecutionStore

RELEASE_AUTHORITY_ROLES = {"owner", "release-manager"}
NO_GO_KEYS = (
    "enterprise_ready_claim",
    "remote_ready_claim",
    "saas_ready_claim",
    "compliance_certification_claim",
    "remote_execution_enabled",
    "connector_write_enabled",
    "plugin_execution_enabled",
    "external_apis_required",
)


@dataclass(frozen=True)
class ReleaseReadinessBlocker:
    blocker_id: str
    severity: str
    title: str
    owner: str
    evidence_ref: str
    policy_source: str
    next_action: str
    pending_approval: bool = False
    state: str = "BLOCKED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "blocker_id": self.blocker_id,
            "severity": self.severity,
            "title": self.title,
            "owner": self.owner,
            "evidence_ref": self.evidence_ref,
            "policy_source": self.policy_source,
            "next_action": self.next_action,
            "pending_approval": self.pending_approval,
            "state": self.state,
        }


class ReleaseReadinessApplicationService:
    """GSDLC-11-A deterministic, read-only release readiness projection.

    The projection composes the current Story/Quality/Git/Approval contracts. It
    intentionally does not introduce a second test runner, packaging engine or
    release approval path. Missing or stale evidence fails closed. A READY
    projection is *not* a release approval and grants no mutation authority.
    """

    def __init__(
        self,
        platform_root: Path,
        *,
        context_resolver,
        quality_reports_lister: Callable[[], list[dict[str, Any]]],
        quality_report_loader: Callable[..., CommandResult],
        approvals_lister: Callable[..., CommandResult],
        git_status_loader: Callable[[], CommandResult],
        commit_records_loader: Callable[[str], list[dict[str, Any]]] | None = None,
        story_projection_loader: Callable[[Path, str], dict[str, Any] | None] | None = None,
    ) -> None:
        self.platform_root = Path(platform_root).resolve()
        self.context_resolver = context_resolver
        self.quality_reports_lister = quality_reports_lister
        self.quality_report_loader = quality_report_loader
        self.approvals_lister = approvals_lister
        self.git_status_loader = git_status_loader
        self.commit_records_loader = commit_records_loader or self._commit_records
        self.story_projection_loader = story_projection_loader or self._story_projection

    def evaluate(self, *, actor: str, actor_roles: Iterable[str], workspace_scopes: Iterable[str]) -> CommandResult:
        command = "release readiness evaluate"
        context = self.context_resolver.resolve()
        if not context.configured or not context.valid or context.active_workspace_root is None or not context.active_workspace_id:
            return self._block(command, "GSDLC11A_PROJECT_CONTEXT_BLOCK", "Release readiness requires a server-validated active project workspace.")
        workspace_id = str(context.active_workspace_id)
        scopes = {str(item) for item in workspace_scopes if str(item).strip()}
        if scopes and workspace_id not in scopes and "*" not in scopes:
            return self._block(command, "GSDLC11A_WORKSPACE_SCOPE_BLOCK", "Authenticated session is not scoped to the active workspace.", {"workspace_id": workspace_id})

        roles = sorted({str(role).strip() for role in actor_roles if str(role).strip()})
        release_roles = sorted(RELEASE_AUTHORITY_ROLES.intersection(roles))
        blockers: list[ReleaseReadinessBlocker] = []
        unknown = False

        story = self.story_projection_loader(context.active_workspace_root, workspace_id)
        story_execution_id = str((story or {}).get("execution_id") or "")
        if not story:
            unknown = True
            blockers.append(self._missing("story-evidence-missing", "Current story lifecycle evidence is missing.", "developer", "outputs/story_execution/gsdlc_09_a", "GSDLC-09/GSDLC-10", "Complete the governed story cycle before release readiness."))
        elif str(story.get("status")) != "DONE":
            blockers.append(self._known("story-not-done", f"Current story is {story.get('status')}, not DONE.", "developer", "outputs/story_execution/gsdlc_09_a", "GSDLC-10-E", "Complete the story through governed commit before release readiness."))

        quality = self._quality(story_execution_id)
        if quality is None:
            unknown = True
            blockers.append(self._missing("quality-evidence-missing", "Current StoryQualityReport is missing.", "qa-reviewer", "outputs/runtime/gsdlc10c_story_quality", "GSDLC-10-C", "Evaluate Story Quality and preserve the current report."))
        else:
            if bool(quality.get("stale")):
                blockers.append(self._known("quality-stale", "StoryQualityReport is stale.", "qa-reviewer", str(quality.get("report_id") or "StoryQualityReport"), "GSDLC-10-C", "Re-evaluate Story Quality against current inputs."))
            if quality.get("decision") != "PASS" or quality.get("commit_ready") is not True:
                blockers.append(self._known("quality-not-pass", "Story Quality is not PASS/COMMIT_READY.", "qa-reviewer", str(quality.get("report_id") or "StoryQualityReport"), "GSDLC-10-C", "Resolve Quality blockers before release readiness."))
            required_jobs = [row for row in quality.get("required_job_results", []) if isinstance(row, dict)]
            non_pass = [row for row in required_jobs if str(row.get("story_validation_status") or row.get("status") or "").upper() != "PASS"]
            if not required_jobs:
                unknown = True
                blockers.append(self._missing("validation-evidence-missing", "Required validation results are missing from StoryQualityReport.", "qa-reviewer", str(quality.get("report_id") or "StoryQualityReport"), "GSDLC-10-B/C", "Run the required typed validation jobs."))
            elif non_pass:
                blockers.append(self._known("validation-not-pass", "One or more required validation jobs are not PASS.", "qa-reviewer", str(quality.get("report_id") or "StoryQualityReport"), "GSDLC-10-B/C", "Resolve failed/pending validation jobs."))
            security_blockers = [row for row in quality.get("findings", []) if isinstance(row, dict) and row.get("blocking") and (str(row.get("origin")) == "security" or str(row.get("severity")) in {"S0", "S1"})]
            if security_blockers:
                blockers.append(self._known("security-findings-open", "Blocking security/S0/S1 findings remain open.", "security-reviewer", str(quality.get("report_id") or "StoryQualityReport"), "GSDLC-10-C", "Resolve blocking security findings; S0/S1 cannot be waived."))

        git_result = self.git_status_loader()
        head = None
        if not git_result.ok:
            unknown = True
            blockers.append(self._missing("git-status-unavailable", "Git status could not be resolved through the governed read adapter.", "developer", "workspace.git.status", "UOC-006/GSDLC-10-D", "Restore a valid local Git workspace and retry readiness."))
        else:
            summary = dict((git_result.data or {}).get("summary") or {})
            head = str(summary.get("head") or "") or None
            status = dict((git_result.data or {}).get("status") or {})
            dirty = list(status.get("short_status") or [])
            if dirty:
                blockers.append(self._known("git-worktree-dirty", "Release candidate workspace has uncommitted Git changes.", "developer", "workspace.git.status", "UOC-006/GSDLC-10-D", "Resolve unexpected dirty paths before packaging."))

        records = self.commit_records_loader(workspace_id)
        commit_record = self._matching_commit_record(records, story_execution_id, head)
        if commit_record is None:
            unknown = True
            blockers.append(self._missing("traceability-commit-missing", "Governed GitCommitRecord bound to the current story/HEAD is missing.", "release-manager", "outputs/uoc006_control/gsdlc10d_story_git/evidence", "GSDLC-10-D", "Complete or recover the governed commit and trace graph."))
        elif not bool(commit_record.get("traceability_complete")):
            blockers.append(self._known("traceability-incomplete", "GitCommitRecord traceability is incomplete.", "release-manager", str(commit_record.get("commit_record_id") or "GitCommitRecord"), "GSDLC-10-D", "Repair requirement→story→files→tests→quality→commit traceability."))

        pending = self._pending_approvals(workspace_id)
        if pending is None:
            unknown = True
            blockers.append(self._missing("approval-inventory-unavailable", "Pending approval inventory could not be read.", "owner", "approval-store", "GSDLC-02-D", "Restore the approval store and re-evaluate readiness."))
        elif pending:
            blockers.append(ReleaseReadinessBlocker(
                blocker_id="pending-approvals",
                severity="S1",
                title=f"{len(pending)} pending approval(s) remain for the active workspace.",
                owner="owner",
                evidence_ref="approval-store",
                policy_source="GSDLC-02-D",
                next_action="Resolve pending governed approvals before release packaging.",
                pending_approval=True,
            ))

        machinery = self._release_machinery()
        if machinery["unknown"]:
            unknown = True
            blockers.append(self._missing(
                "release-machinery-unavailable",
                "Inherited POST-H-017/026/027 release machinery is incomplete or cannot be verified.",
                "release-manager",
                "POST-H-017/026/027 source contracts",
                "POST-H-017/026/027 + GSDLC-11",
                "Restore the source-controlled release machinery before declaring readiness.",
            ))

        claims = self._claim_policy()
        if claims["unknown"]:
            unknown = True
            blockers.append(self._missing("release-claim-policy-unavailable", "Local release claim/no-go policy is missing or invalid.", "release-manager", ".devpilot/release/local_release_candidate_criteria.json", "POST-H-026/GSDLC-11", "Restore the current local-release criteria before readiness."))
        elif claims["enabled"]:
            blockers.append(self._known("unsupported-release-claim", "One or more forbidden enterprise/remote/SaaS/compliance release claims are enabled.", "owner", ".devpilot/release/local_release_candidate_criteria.json", "POST-H-026/GSDLC-11", "Disable unsupported claims; GSDLC-11 remains local-only."))

        state = "UNKNOWN" if unknown else ("BLOCKED" if blockers else "RELEASE_READY")
        next_action = self._next_action(blockers, state)
        projection = {
            "schema_id": "DEVPL-GSDLC-11-A-RELEASE-READINESS-PROJECTION-V1",
            "schema_version": "1.0.0",
            "workspace_id": workspace_id,
            "state": state,
            "release_ready": state == "RELEASE_READY",
            "blockers": [item.to_dict() for item in blockers],
            "blockers_total": len(blockers),
            "missing_or_unknown_evidence": unknown,
            "next_action": next_action,
            "evidence": {
                "release_machinery": machinery,
                "story": story,
                "quality_report_id": None if quality is None else quality.get("report_id"),
                "quality_report_hash": None if quality is None else quality.get("report_hash"),
                "git_head": head,
                "commit_record_id": None if commit_record is None else commit_record.get("commit_record_id"),
                "pending_approval_ids": [] if not pending else [row.get("approval_id") for row in pending],
            },
            "release_authority": {
                "allowed": bool(release_roles),
                "effective_roles": roles,
                "release_roles": release_roles,
                "approval_required_later": True,
                "readiness_is_release_approval": False,
                "model_or_agent_can_approve": False,
            },
            "claims": {
                "scope": "local-release-only",
                "enterprise_ready_claim": False,
                "compliance_certification_claim": False,
                "public_release_claim": False,
                "forbidden_claims_enabled": claims["enabled"],
            },
            "safety": {
                "read_only": True,
                "mutations_performed": False,
                "network_used": False,
                "external_api_used": False,
                "arbitrary_shell_used": False,
                "full_regression_started": False,
            },
        }
        finding = Finding(
            "GSDLC11A_RELEASE_READINESS_READY" if state == "RELEASE_READY" else "GSDLC11A_RELEASE_READINESS_FAIL_CLOSED",
            "Release readiness projection is complete." if state == "RELEASE_READY" else "Release readiness remains fail-closed until all blockers/unknown evidence are resolved.",
            Severity.INFO if state == "RELEASE_READY" else Severity.WARNING,
            metadata={"state": state, "blockers_total": len(blockers)},
        )
        return CommandResult(command, True, ExitCode.PASS, f"Release readiness projected as {state}.", data={"release_readiness": projection, "summary": {"state": state, "release_ready": state == "RELEASE_READY", "blockers_total": len(blockers)}}, findings=[finding])

    def _quality(self, story_execution_id: str) -> dict[str, Any] | None:
        if not story_execution_id:
            return None
        rows = [row for row in self.quality_reports_lister() if str(row.get("story_execution_id") or "") == story_execution_id]
        rows.sort(key=lambda row: (str(row.get("created_at_utc") or ""), str(row.get("report_id") or "")), reverse=True)
        for row in rows:
            report_id = str(row.get("report_id") or "")
            if not report_id:
                continue
            result = self.quality_report_loader(report_id=report_id)
            if result.ok:
                return dict((result.data or {}).get("story_quality_report") or {})
        return None

    def _pending_approvals(self, workspace_id: str) -> list[dict[str, Any]] | None:
        result = self.approvals_lister(status="requested", limit=200)
        if not result.ok:
            return None
        rows = list((result.data or {}).get("approvals") or [])
        pending: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            scope = dict(row.get("scope") or {})
            metadata = dict(row.get("metadata") or {})
            scoped = str(scope.get("workspace_id") or metadata.get("workspace_id") or "")
            if scoped == workspace_id:
                pending.append(row)
        return pending

    def _release_machinery(self) -> dict[str, Any]:
        required = {
            "POST-H-017": [
                "docs/backlogs/POST-H-017_release_reproducibility_pack.md",
                ".devpilot/release/reproducibility_policy.json",
                "src/devpilot_core/release/reproducibility_pack.py",
            ],
            "POST-H-026": [
                "docs/backlogs/POST-H-026_local_release_candidate_operator_verification.md",
                ".devpilot/release/local_release_candidate_criteria.json",
                "src/devpilot_core/release_candidate/report.py",
            ],
            "POST-H-027": [
                "docs/backlogs/POST-H-027_packaging_reproducible_local_installation.md",
                ".devpilot/release/source_zip_release_policy.json",
                "src/devpilot_core/release/artifact_manifest.py",
            ],
        }
        missing = [rel for rows in required.values() for rel in rows if not (self.platform_root / rel).is_file()]
        project_state_path = self.platform_root / ".devpilot" / "project_state.json"
        statuses: dict[str, Any] = {}
        try:
            state = json.loads(project_state_path.read_text(encoding="utf-8"))
            statuses = {
                "post_h_026_status": state.get("post_h_026_status"),
                "post_h_027_status": state.get("post_h_027_status"),
            }
        except (OSError, json.JSONDecodeError):
            missing.append(".devpilot/project_state.json")
        if statuses and statuses.get("post_h_026_status") != "closed/local-release-candidate-pass":
            missing.append("project_state:post_h_026_status")
        if statuses and statuses.get("post_h_027_status") != "closed/packaging-local-ready":
            missing.append("project_state:post_h_027_status")
        return {
            "unknown": bool(missing),
            "missing": sorted(set(missing)),
            "contracts": required,
            "project_state_statuses": statuses,
            "reuse_mode": "compose-existing-read-only-contracts/no-second-release-stack",
        }

    def _claim_policy(self) -> dict[str, Any]:
        path = self.platform_root / ".devpilot" / "release" / "local_release_candidate_criteria.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            gates = dict(payload.get("no_go_gates") or {})
        except (OSError, json.JSONDecodeError):
            return {"unknown": True, "enabled": []}
        enabled = sorted(key for key in NO_GO_KEYS if bool(gates.get(key)))
        return {"unknown": False, "enabled": enabled}

    def _commit_records(self, workspace_id: str) -> list[dict[str, Any]]:
        root = self.platform_root / "outputs" / "uoc006_control" / "gsdlc10d_story_git" / "evidence"
        rows: list[dict[str, Any]] = []
        if not root.exists():
            return rows
        for path in sorted(root.glob("*_commit_record.json")):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(row, dict) and str(row.get("workspace_id") or "") == workspace_id:
                rows.append(row)
        return rows

    @staticmethod
    def _story_projection(root: Path, workspace_id: str) -> dict[str, Any] | None:
        try:
            return StoryExecutionStore(root, workspace_id=workspace_id).current_story_projection()
        except (OSError, ValueError, json.JSONDecodeError):
            return None

    @staticmethod
    def _matching_commit_record(rows: list[dict[str, Any]], story_execution_id: str, head: str | None) -> dict[str, Any] | None:
        candidates = [row for row in rows if str(row.get("story_execution_id") or "") == story_execution_id]
        if head:
            exact = [row for row in candidates if str(row.get("commit_hash") or "") == head]
            if exact:
                candidates = exact
        candidates.sort(key=lambda row: (str(row.get("created_at_utc") or ""), str(row.get("commit_record_id") or "")), reverse=True)
        return candidates[0] if candidates else None

    @staticmethod
    def _known(blocker_id: str, title: str, owner: str, evidence_ref: str, policy_source: str, next_action: str) -> ReleaseReadinessBlocker:
        return ReleaseReadinessBlocker(blocker_id, "S1", title, owner, evidence_ref, policy_source, next_action)

    @staticmethod
    def _missing(blocker_id: str, title: str, owner: str, evidence_ref: str, policy_source: str, next_action: str) -> ReleaseReadinessBlocker:
        return ReleaseReadinessBlocker(blocker_id, "S1", title, owner, evidence_ref, policy_source, next_action, state="UNKNOWN")

    @staticmethod
    def _next_action(blockers: list[ReleaseReadinessBlocker], state: str) -> dict[str, Any]:
        if blockers:
            first = blockers[0]
            return {"action_id": first.blocker_id, "title": first.next_action, "owner": first.owner, "evidence_ref": first.evidence_ref, "mutating": False}
        return {"action_id": "proceed-gsdlc-11-b", "title": "Proceed to reproducible package/checksum/SBOM workbench; release approval remains a later separate decision.", "owner": "release-manager", "evidence_ref": "DEVPL-GSDLC-11-B", "mutating": False}

    @staticmethod
    def _block(command: str, finding_id: str, message: str, metadata: dict[str, Any] | None = None) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, message, data={"release_readiness": None, "safety": {"mutations_performed": False, "network_used": False, "external_api_used": False}}, findings=[Finding(finding_id, message, Severity.BLOCK, metadata=metadata or {})])
