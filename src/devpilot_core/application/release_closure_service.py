from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.guided_sdlc.models import EngineeringLifecycleStatus, MIPSoftwarePhase, RevalidationStatus, WorkspaceEngineeringState
from devpilot_core.guided_sdlc.repository import WorkspaceEngineeringStateRepository

RELEASE_CLOSURE_ROLES = {"owner", "release-manager"}
FINAL_DIR = Path("outputs/release/gsdlc11e")
FINAL_GRAPH = FINAL_DIR / "local_release_graph.json"
FINAL_STATUS = FINAL_DIR / "final_release_status.json"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class ReleaseClosureApplicationService:
    """GSDLC-11-E final local release closure.

    The service does not recreate packaging/install/metadata machinery. It
    aggregates the current-A-D evidence on the exact current Git authority and
    permits one final local lifecycle mutation only after every prerequisite is
    proven.  No network, push, publish or deploy capability is introduced.
    """

    def __init__(self, platform_root: Path, *, context_resolver) -> None:
        self.root = Path(platform_root).resolve()
        self.context_resolver = context_resolver

    def status(self, *, actor: str, actor_roles: Iterable[str], workspace_scopes: Iterable[str]) -> CommandResult:
        command = "release closure status"
        checked = self._authorize(command, actor_roles, workspace_scopes, require_release_role=False)
        if checked is not None:
            return checked
        graph = self._build_graph()
        final = self._read_json(self.root / FINAL_STATUS)
        return CommandResult(
            command=command,
            ok=True,
            exit_code=ExitCode.PASS,
            message="Final local release graph projected.",
            data={"release_closure": graph, "final_release_status": final, "safety": self._safety(mutated=False)},
            findings=[Finding("GSDLC11E_RELEASE_GRAPH_PROJECTED", "Final release graph is available and explainable.", Severity.INFO)],
        )

    def finalize(self, *, actor: str, actor_roles: Iterable[str], workspace_scopes: Iterable[str], graph_hash: str) -> CommandResult:
        command = "release closure finalize"
        checked = self._authorize(command, actor_roles, workspace_scopes, require_release_role=True)
        if checked is not None:
            return checked
        graph = self._build_graph()
        if graph.get("graph_hash") != graph_hash:
            return self._block(command, "GSDLC11E_GRAPH_HASH_MISMATCH_BLOCK", "Finalization requires the exact current release graph hash.")
        if graph.get("state") != "READY_TO_FINALIZE" or not graph.get("ready_to_finalize"):
            return self._block(command, "GSDLC11E_RELEASE_NOT_READY_BLOCK", "Final local release is blocked until every current release node is PASS.", {"blockers": graph.get("blockers", [])})
        prior = self._read_json(self.root / FINAL_STATUS)
        if prior and prior.get("status") == "RELEASED" and prior.get("graph_hash") == graph_hash:
            return CommandResult(command, True, ExitCode.PASS, "Prior exact final release receipt remains valid; finalization was not repeated.", data={"final_release_status": prior, "reused": True, "safety": self._safety(mutated=False)}, findings=[Finding("GSDLC11E_FINALIZE_REUSED_PASS", "Exact graph-bound release finalization evidence was reused.", Severity.INFO)])

        context = self.context_resolver.resolve()
        workspace_id = str(context.active_workspace_id)
        repository = WorkspaceEngineeringStateRepository(self.root)
        binding = repository.binding(workspace_id)
        observed = _now()
        state_path = repository.state_path(workspace_id)
        adoption_mode = "EVIDENCE_BACKED_REGISTERED_WORKSPACE_ADOPTION"
        if state_path.is_file():
            current = repository.load(workspace_id)
            successor = replace(
                current,
                lifecycle_status=EngineeringLifecycleStatus.RELEASED,
                phase=MIPSoftwarePhase.RELEASE,
                current_step="local-release-closed",
                sequence=current.sequence + 1,
                updated_at_utc=observed,
                git={"head": graph["source_authority"]["commit"], "tree": graph["source_authority"]["tree"], "dirty": False, "fingerprint": graph_hash},
                quality=tuple(list(current.quality) + [{"id": "gsdlc-11-release-closure", "status": "PASS", "graph_hash": graph_hash}]),
                gates=tuple(list(current.gates) + [{"id": "gsdlc-11-release-closure", "status": "PASS", "evidence_ref": str(FINAL_GRAPH).replace("\\", "/")}]),
                blockers=(),
                revalidation={"status": RevalidationStatus.NOT_REQUIRED.value, "reason_codes": []},
                source_fingerprints=tuple(list(current.source_fingerprints) + [{"kind": "local-release-graph", "sha256": graph_hash}]),
                next_action_ref=None,
            )
            repository.save(successor, expected_sequence=current.sequence)
            adoption_mode = "SUCCESSOR_STATE_UPDATE"
            persisted = successor
        else:
            persisted = WorkspaceEngineeringState(
                workspace_id=workspace_id,
                project_id=binding.project_id,
                workspace_root_fingerprint=binding.root_fingerprint,
                lifecycle_status=EngineeringLifecycleStatus.RELEASED,
                phase=MIPSoftwarePhase.RELEASE,
                current_step="local-release-closed",
                sequence=0,
                created_at_utc=observed,
                updated_at_utc=observed,
                git={"head": graph["source_authority"]["commit"], "tree": graph["source_authority"]["tree"], "dirty": False, "fingerprint": graph_hash},
                artifacts=({"id": "local-release", "status": "PASS", "evidence_ref": str(FINAL_GRAPH).replace("\\", "/")},),
                quality=({"id": "gsdlc-11-release-closure", "status": "PASS", "graph_hash": graph_hash},),
                gates=({"id": "gsdlc-11-release-closure", "status": "PASS", "evidence_ref": str(FINAL_GRAPH).replace("\\", "/")},),
                blockers=(),
                revalidation={"status": RevalidationStatus.NOT_REQUIRED.value, "reason_codes": []},
                source_fingerprints=({"kind": "local-release-graph", "sha256": graph_hash},),
                next_action_ref=None,
            )
            repository.save(persisted)

        final = {
            "schema_version": "1.0.0",
            "status": "RELEASED",
            "release_scope": "LOCAL_ONLY",
            "graph_hash": graph_hash,
            "workspace_id": workspace_id,
            "project_id": binding.project_id,
            "source_commit": graph["source_authority"]["commit"],
            "source_tree": graph["source_authority"]["tree"],
            "tag_name": graph["metadata"]["tag_name"],
            "tag_target_commit": graph["metadata"]["tag_target_commit"],
            "engineering_state_fingerprint": persisted.fingerprint(),
            "engineering_state_sequence": persisted.sequence,
            "engineering_state_mode": adoption_mode,
            "normal_user_external_script": 0,
            "push_performed": False,
            "publish_performed": False,
            "deploy_performed": False,
            "network_used": False,
            "external_api_used": False,
            "secrets_exposed": False,
            "mutations_performed": ["platform runtime release evidence", "platform WorkspaceEngineeringState only"],
            "released_at_utc": observed,
        }
        self._write_json(self.root / FINAL_GRAPH, graph)
        self._write_json(self.root / FINAL_STATUS, final)
        return CommandResult(command, True, ExitCode.PASS, "Local release finalized and Project Status advanced to RELEASED.", data={"release_closure": graph, "final_release_status": final, "reused": False, "safety": self._safety(mutated=True)}, findings=[Finding("GSDLC11E_FINAL_RELEASE_PASS", "Guided local release is graph-bound, local-only and Project Status is RELEASED.", Severity.INFO)])

    def _build_graph(self) -> dict[str, Any]:
        authority = self._git_authority()
        blockers: list[dict[str, str]] = []
        if authority is None or authority["dirty_tracked"]:
            blockers.append({"id": "git-authority", "message": "Tracked Git source must be clean."})
        state = self._read_json(self.root / ".devpilot/project_state.json") or {}
        predecessor_pass = all(state.get(f"gsdlc_11_{x}_status") == "CLOSED/PASS/WINDOWS-VALIDATED" for x in ("a", "b", "c", "d")) and state.get("gsdlc_11_e_authorized") is True
        if not predecessor_pass:
            blockers.append({"id": "predecessor", "message": "GSDLC-11 A-D must be CLOSED/PASS/WINDOWS-VALIDATED and 11-E authorized."})

        package = self._read_json(self.root / "outputs/runtime/gsdlc11b_release_package/job_result.json")
        package_ok = self._package_ok(package, authority)
        if not package_ok:
            blockers.append({"id": "package", "message": "Generate the reproducible package/checksum/SBOM on the current commit."})

        install = self._read_json(self.root / "outputs/release/gsdlc11c/install_smoke_report.json")
        rollback = self._read_json(self.root / "outputs/release/gsdlc11c/upgrade_rollback_report.json")
        lifecycle_ok = bool(install and install.get("status") == "PASS" and rollback and rollback.get("status") == "PASS" and rollback.get("restore_verified") is True and rollback.get("backup_required_before_mutation") is True and rollback.get("production_data_touched") is False)
        if not lifecycle_ok:
            blockers.append({"id": "install-rollback", "message": "Run clean install plus backup/rollback verification on the current package."})

        decision = self._read_json(self.root / "outputs/release/gsdlc11d/version_decision.json")
        approval = self._read_json(self.root / "outputs/release/gsdlc11d/release_approval.json")
        tag_verification = self._read_json(self.root / "outputs/release/gsdlc11d/tag_verification.json")
        metadata_ok = self._metadata_ok(decision, approval, tag_verification, authority)
        if not metadata_ok:
            blockers.append({"id": "metadata-tag", "message": "Prepare version/release notes, approve and create the annotated local tag on the current commit."})

        nodes = {
            "predecessors": {"status": "PASS" if predecessor_pass else "BLOCK"},
            "package": {"status": "PASS" if package_ok else "BLOCK", "artifact_sha256": ((package or {}).get("artifact") or {}).get("sha256"), "checksums": ((package or {}).get("checksums") or {}).get("path"), "sbom": ((package or {}).get("sbom") or {}).get("path")},
            "install_rollback": {"status": "PASS" if lifecycle_ok else "BLOCK", "install": (install or {}).get("status"), "rollback": (rollback or {}).get("status"), "restore_verified": (rollback or {}).get("restore_verified")},
            "metadata": {"status": "PASS" if metadata_ok else "BLOCK", "version": (decision or {}).get("version"), "tag_name": (tag_verification or {}).get("tag_name"), "tag_target_commit": (tag_verification or {}).get("tag_target_commit"), "approval": (approval or {}).get("status")},
        }
        graph_core = {
            "schema_version": "1.0.0",
            "release_scope": "LOCAL_ONLY",
            "source_authority": authority,
            "nodes": nodes,
            "blockers": blockers,
            "ready_to_finalize": not blockers,
            "normal_user_external_script": 0,
            "push_performed": False,
            "publish_performed": False,
            "deploy_performed": False,
            "network_used": False,
            "external_api_used": False,
            "secrets_exposed": False,
        }
        graph_hash = _canonical_hash(graph_core)
        metadata_summary = nodes["metadata"]
        return {**graph_core, "state": "READY_TO_FINALIZE" if not blockers else "BLOCKED", "next_action": "Finalize local release" if not blockers else blockers[0]["message"], "metadata": metadata_summary, "graph_hash": graph_hash, "generated_at_utc": _now()}

    def _package_ok(self, package: dict[str, Any] | None, authority: dict[str, Any] | None) -> bool:
        if not package or package.get("status") != "PASS" or not authority:
            return False
        src = package.get("source_authority") or {}
        if src.get("commit") != authority.get("commit") or src.get("tree") != authority.get("tree"):
            return False
        artifact = package.get("artifact") or {}
        path = self.root / str(artifact.get("path") or "")
        if not path.is_file() or _sha256_file(path) != artifact.get("sha256"):
            return False
        return bool((package.get("reproducibility") or {}).get("package_byte_reproducible") and (package.get("sbom") or {}).get("schema_validation") == "PASS")

    def _metadata_ok(self, decision: dict[str, Any] | None, approval: dict[str, Any] | None, verification: dict[str, Any] | None, authority: dict[str, Any] | None) -> bool:
        if not decision or not approval or not verification or not authority:
            return False
        if decision.get("status") != "PASS" or (decision.get("source_authority") or {}).get("commit") != authority.get("commit"):
            return False
        if approval.get("status") != "APPROVED" or approval.get("target_commit") != authority.get("commit") or approval.get("model_or_agent_authority") is not False:
            return False
        if verification.get("status") != "PASS" or verification.get("tag_target_commit") != authority.get("commit") or verification.get("exact_commit_match") is not True or verification.get("annotated") is not True:
            return False
        if any(verification.get(k) is not False for k in ("push_performed", "publish_performed", "deploy_performed")):
            return False
        return self._tag_target(str(verification.get("tag_name") or "")) == authority.get("commit")

    def _authorize(self, command: str, actor_roles: Iterable[str], workspace_scopes: Iterable[str], *, require_release_role: bool) -> CommandResult | None:
        context = self.context_resolver.resolve()
        if not context.configured or not context.valid or context.active_workspace_root is None or not context.active_workspace_id:
            return self._block(command, "GSDLC11E_PROJECT_CONTEXT_BLOCK", "Release closure requires a server-validated active project workspace.")
        scopes = {str(item) for item in workspace_scopes if str(item).strip()}
        if scopes and str(context.active_workspace_id) not in scopes and "*" not in scopes:
            return self._block(command, "GSDLC11E_WORKSPACE_SCOPE_BLOCK", "Authenticated session is not scoped to the active workspace.")
        roles = {str(item).strip() for item in actor_roles if str(item).strip()}
        if require_release_role and not roles.intersection(RELEASE_CLOSURE_ROLES):
            return self._block(command, "GSDLC11E_RELEASE_ROLE_BLOCK", "Final local release requires owner or release-manager server-side role.")
        return None

    def _git_authority(self) -> dict[str, Any] | None:
        try:
            commit = self._git("rev-parse", "HEAD")
            tree = self._git("rev-parse", "HEAD^{tree}")
            branch = self._git("branch", "--show-current") or "DETACHED"
            dirty = bool(self._git("status", "--porcelain", "--untracked-files=no"))
            return {"commit": commit, "tree": tree, "branch": branch, "dirty_tracked": dirty}
        except Exception:
            return None

    def _tag_target(self, tag_name: str) -> str | None:
        if not tag_name:
            return None
        proc = subprocess.run(["git", "-C", str(self.root), "rev-list", "-n", "1", tag_name], capture_output=True, text=True, check=False)
        return proc.stdout.strip() if proc.returncode == 0 and proc.stdout.strip() else None

    def _git(self, *args: str) -> str:
        return subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True, check=True).stdout.strip()

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any] | None:
        try:
            value = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    def _safety(self, *, mutated: bool) -> dict[str, Any]:
        return {"local_first": True, "network_used": False, "external_api_used": False, "push_performed": False, "publish_performed": False, "deploy_performed": False, "source_mutations_performed": False, "platform_state_mutations_performed": mutated, "arbitrary_shell_used": False, "secrets_exposed": False}

    def _block(self, command: str, finding_id: str, message: str, metadata: dict[str, Any] | None = None) -> CommandResult:
        return CommandResult(command=command, ok=False, exit_code=ExitCode.BLOCK, message=message, data={"safety": self._safety(mutated=False)}, findings=[Finding(finding_id, message, Severity.BLOCK, metadata=metadata or {})])
