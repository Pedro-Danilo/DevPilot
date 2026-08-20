from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import SecretGuard
from devpilot_core.schemas import SchemaValidator
from devpilot_core.validation.artifact_profile_registry import ArtifactProfileRegistry

DEFAULT_ARTIFACT_LIFECYCLE_POLICY = Path(".devpilot/artifacts/artifact_lifecycle_policy.json")
_ZERO_SHA = "0" * 64
_DRIVE_PATTERN = re.compile(r"^[A-Za-z]:")


class ArtifactState(str, Enum):
    MISSING = "MISSING"
    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    FINDINGS = "FINDINGS"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVED = "APPROVED"
    FROZEN = "FROZEN"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"


class ArtifactSourceType(str, Enum):
    MANUAL = "MANUAL"
    PASTE = "PASTE"
    UPLOAD = "UPLOAD"
    IMPORT = "IMPORT"
    AGENT_ASSISTED = "AGENT_ASSISTED"
    EXTERNAL_EDITOR = "EXTERNAL_EDITOR"


class ArtifactLifecycleService:
    """GSDLC-04-A server-authoritative artifact lifecycle/provenance boundary.

    The service is deliberately metadata-only in this micro-sprint. It does not
    persist drafts, mutate workspace documents, expose API/UI routes, execute
    uploads, or replace UOC-004/UOC-005 planning/apply. It validates deterministic
    state transitions and provenance so later GSDLC-04 micro-sprints can compose
    the existing governed write pipeline without introducing a second write engine.
    """

    def __init__(
        self,
        root: Path,
        *,
        policy_path: str | Path = DEFAULT_ARTIFACT_LIFECYCLE_POLICY,
        profile_registry: ArtifactProfileRegistry | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.policy_path = Path(policy_path)
        self.profile_registry = profile_registry or ArtifactProfileRegistry(self.root)
        self.secret_guard = SecretGuard(self.root)
        self.schemas = SchemaValidator(self.root)

    @property
    def resolved_policy_path(self) -> Path:
        return self.root / self.policy_path

    def policy(self) -> dict[str, Any]:
        payload = json.loads(self.resolved_policy_path.read_text(encoding="utf-8"))
        result = self.schemas.validate_payload(
            schema="ArtifactLifecyclePolicy",
            payload=payload,
            instance_label=str(self.policy_path).replace("\\", "/"),
        )
        if not result.ok:
            raise ValueError("Artifact lifecycle policy failed schema validation.")
        return payload

    def create_draft(
        self,
        *,
        artifact_id: str,
        relative_path: str,
        content: str,
        source_type: str | ArtifactSourceType,
        base_commit: str,
        actor: str,
        actor_role: str,
        session_principal: str,
        reviewer: str,
        reviewer_role: str,
        source_label: str | None = None,
        source_reference: str | None = None,
        now: str | None = None,
    ) -> CommandResult:
        command = "artifact lifecycle create draft"
        findings: list[Finding] = []
        policy = self.policy()

        normalized_source = self._source_type(source_type, findings)
        path = self._safe_relative_path(relative_path, findings, policy)
        self._validate_identity(actor, actor_role, session_principal, reviewer, reviewer_role, findings, policy)
        self._validate_base_commit(base_commit, findings)
        self._validate_content(content, path, findings, policy)

        if findings:
            return self._blocked(command, findings)

        assert normalized_source is not None
        profile_id = self._profile_id(path)
        profile = self._profile_policy(profile_id, policy, findings)
        if profile is None:
            return self._blocked(command, findings)

        if normalized_source.value not in profile["allowed_source_types"]:
            findings.append(
                Finding(
                    "GSDLC04A_SOURCE_PROFILE_DENY",
                    f"Source type {normalized_source.value} is not allowed for artifact profile {profile_id}.",
                    Severity.BLOCK,
                    path=path,
                    metadata={"profile_id": profile_id, "source_type": normalized_source.value},
                )
            )
            return self._blocked(command, findings)

        transition = self._transition_rule(ArtifactState.MISSING, ArtifactState.DRAFT, policy)
        if actor_role not in transition["allowed_roles"]:
            findings.append(
                Finding(
                    "GSDLC04A_TRANSITION_ROLE_BLOCK",
                    "Actor role is not allowed to create a governed draft.",
                    Severity.BLOCK,
                    path=path,
                    metadata={"role": actor_role, "from": "MISSING", "to": "DRAFT"},
                )
            )
            return self._blocked(command, findings)

        raw_sha = self.hash_source(content)
        normalized_sha = self.hash_normalized(content)
        timestamp = now or _now()
        provenance = {
            "schema_id": "devpilot.gsdlc04.artifact_provenance.v1",
            "source_type": normalized_source.value,
            "source_sha256": raw_sha,
            "normalized_sha256": normalized_sha,
            "artifact_version": 1,
            "base_commit": base_commit,
            "author_actor": actor.strip(),
            "author_role": actor_role,
            "session_principal": session_principal.strip(),
            "reviewer": reviewer.strip(),
            "reviewer_role": reviewer_role,
            "created_at": timestamp,
            "updated_at": timestamp,
            "source_label": _optional_text(source_label),
            "source_reference": _optional_text(source_reference),
            "lineage": [
                {
                    "event": "MISSING_TO_DRAFT",
                    "at": timestamp,
                    "actor": actor.strip(),
                    "actor_role": actor_role,
                    "state": ArtifactState.DRAFT.value,
                    "source_type": normalized_source.value,
                    "normalized_sha256": normalized_sha,
                }
            ],
        }
        record = {
            "schema_id": "devpilot.gsdlc04.artifact_lifecycle_record.v1",
            "artifact_id": artifact_id.strip(),
            "relative_path": path,
            "profile_id": profile_id,
            "state": ArtifactState.DRAFT.value,
            "content_hash": normalized_sha,
            "provenance": provenance,
            "validators": list(profile["validators"]),
            "approval_required": bool(profile["approval_required"]),
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        schema_findings = self._schema_findings(record)
        if schema_findings:
            return self._blocked(command, schema_findings)

        return CommandResult(
            command,
            True,
            ExitCode.PASS,
            "Governed artifact draft lifecycle/provenance record created in memory; no source write performed.",
            data={
                "artifact": record,
                "summary": {
                    "state": ArtifactState.DRAFT.value,
                    "profile_id": profile_id,
                    "source_type": normalized_source.value,
                    "source_mutations_performed": False,
                    "network_used": False,
                    "external_api_used": False,
                    "server_authoritative": True,
                },
            },
            findings=[
                Finding(
                    "GSDLC04A_DRAFT_CREATED_PASS",
                    "Artifact draft state and provenance passed deterministic validation.",
                    Severity.INFO,
                    path=path,
                )
            ],
        )

    def transition(
        self,
        record: dict[str, Any],
        *,
        target_state: str | ArtifactState,
        actor: str,
        actor_role: str,
        findings_present: bool | None = None,
        now: str | None = None,
    ) -> CommandResult:
        command = "artifact lifecycle transition"
        validation = self.validate_record(record)
        if not validation.ok:
            return CommandResult(command, False, validation.exit_code, "Artifact record is invalid; transition blocked.", data=validation.data, findings=validation.findings)

        policy = self.policy()
        current = ArtifactState(str(record["state"]))
        try:
            target = target_state if isinstance(target_state, ArtifactState) else ArtifactState(str(target_state))
        except ValueError:
            return self._blocked(command, [Finding("GSDLC04A_UNKNOWN_STATE_BLOCK", "Unknown target artifact state.", Severity.BLOCK, metadata={"target_state": str(target_state)})])

        rule = self._transition_rule(current, target, policy, allow_missing=True)
        if rule is None or rule["mode"] != "actor":
            return self._blocked(
                command,
                [Finding("GSDLC04A_ILLEGAL_TRANSITION_BLOCK", f"Transition {current.value} -> {target.value} is not an actor-driven legal transition.", Severity.BLOCK, path=record["relative_path"])],
            )
        if actor_role not in rule["allowed_roles"]:
            return self._blocked(
                command,
                [Finding("GSDLC04A_TRANSITION_ROLE_BLOCK", "Actor role is not authorized for this lifecycle transition.", Severity.BLOCK, path=record["relative_path"], metadata={"role": actor_role, "from": current.value, "to": target.value})],
            )
        if not str(actor or "").strip():
            return self._blocked(command, [Finding("GSDLC04A_ACTOR_REQUIRED_BLOCK", "Transition actor is required.", Severity.BLOCK, path=record["relative_path"])])
        if rule["requires_reviewer"] and not str(record["provenance"].get("reviewer") or "").strip():
            return self._blocked(command, [Finding("GSDLC04A_REVIEWER_REQUIRED_BLOCK", "Reviewer assignment is required for this transition.", Severity.BLOCK, path=record["relative_path"])])

        if current is ArtifactState.VALIDATING and target is ArtifactState.FINDINGS and findings_present is not True:
            return self._blocked(command, [Finding("GSDLC04A_FINDINGS_EVIDENCE_REQUIRED_BLOCK", "VALIDATING -> FINDINGS requires findings_present=true.", Severity.BLOCK, path=record["relative_path"])])
        if current is ArtifactState.VALIDATING and target is ArtifactState.READY_FOR_REVIEW and findings_present is not False:
            return self._blocked(command, [Finding("GSDLC04A_VALIDATION_CLEAR_REQUIRED_BLOCK", "VALIDATING -> READY_FOR_REVIEW requires findings_present=false.", Severity.BLOCK, path=record["relative_path"])])

        provenance = record["provenance"]
        if target in {ArtifactState.APPROVED, ArtifactState.FROZEN}:
            if actor.strip() != str(provenance["reviewer"]).strip() or actor_role != provenance["reviewer_role"]:
                return self._blocked(
                    command,
                    [Finding("GSDLC04A_REVIEWER_BINDING_BLOCK", "APPROVED/FROZEN transition must be performed by the assigned reviewer identity and role.", Severity.BLOCK, path=record["relative_path"])],
                )

        updated = deepcopy(record)
        timestamp = now or _now()
        updated["state"] = target.value
        updated["updated_at"] = timestamp
        updated["provenance"]["updated_at"] = timestamp
        updated["provenance"]["lineage"].append(
            {
                "event": f"{current.value}_TO_{target.value}",
                "at": timestamp,
                "actor": actor.strip(),
                "actor_role": actor_role,
                "state": target.value,
                "normalized_sha256": updated["content_hash"],
            }
        )

        schema_findings = self._schema_findings(updated)
        if schema_findings:
            return self._blocked(command, schema_findings)
        return CommandResult(
            command,
            True,
            ExitCode.PASS,
            f"Artifact lifecycle transition {current.value} -> {target.value} passed.",
            data={"artifact": updated, "summary": {"from": current.value, "to": target.value, "source_mutations_performed": False}},
            findings=[Finding("GSDLC04A_TRANSITION_PASS", "Legal server-authoritative lifecycle transition completed in memory.", Severity.INFO, path=record["relative_path"])],
        )

    def reconcile_external_content(
        self,
        record: dict[str, Any],
        *,
        current_content: str,
        actor: str,
        actor_role: str,
        session_principal: str,
        now: str | None = None,
    ) -> CommandResult:
        command = "artifact lifecycle reconcile external content"
        validation = self.validate_record(record)
        if not validation.ok:
            return CommandResult(command, False, validation.exit_code, "Artifact record is invalid; reconciliation blocked.", data=validation.data, findings=validation.findings)

        current_state = ArtifactState(str(record["state"]))
        if current_state not in {ArtifactState.APPROVED, ArtifactState.FROZEN}:
            return self._blocked(
                command,
                [Finding("GSDLC04A_DRIFT_STATE_BLOCK", "External hash reconciliation is only authoritative from APPROVED or FROZEN.", Severity.BLOCK, path=record["relative_path"], metadata={"state": current_state.value})],
            )
        policy = self.policy()
        self._validate_identity(
            actor,
            actor_role,
            session_principal,
            str(record["provenance"]["reviewer"]),
            str(record["provenance"]["reviewer_role"]),
            findings := [],
            policy,
        )
        path = self._safe_relative_path(str(record["relative_path"]), findings, policy)
        self._validate_content(current_content, path, findings, policy)
        if findings:
            return self._blocked(command, findings)

        raw_sha = self.hash_source(current_content)
        normalized_sha = self.hash_normalized(current_content)
        if normalized_sha == record["content_hash"]:
            return CommandResult(
                command,
                True,
                ExitCode.PASS,
                "Artifact hash is unchanged; approval/freeze remains valid.",
                data={"artifact": deepcopy(record), "summary": {"drift_detected": False, "state": current_state.value, "source_mutations_performed": False}},
                findings=[Finding("GSDLC04A_NO_DRIFT_PASS", "External content normalization hash matches the governed record.", Severity.INFO, path=path)],
            )

        rule = self._transition_rule(current_state, ArtifactState.REVALIDATION_REQUIRED, policy)
        if rule["mode"] != "hash-drift-only":
            return self._blocked(command, [Finding("GSDLC04A_DRIFT_POLICY_BLOCK", "Hash-drift transition policy is invalid.", Severity.BLOCK, path=path)])

        updated = deepcopy(record)
        timestamp = now or _now()
        updated["state"] = ArtifactState.REVALIDATION_REQUIRED.value
        updated["content_hash"] = normalized_sha
        updated["updated_at"] = timestamp
        provenance = updated["provenance"]
        provenance["source_type"] = ArtifactSourceType.EXTERNAL_EDITOR.value
        provenance["source_sha256"] = raw_sha
        provenance["normalized_sha256"] = normalized_sha
        provenance["artifact_version"] = int(provenance["artifact_version"]) + 1
        provenance["updated_at"] = timestamp
        provenance["session_principal"] = session_principal.strip()
        provenance["lineage"].append(
            {
                "event": f"{current_state.value}_HASH_DRIFT_TO_REVALIDATION_REQUIRED",
                "at": timestamp,
                "actor": actor.strip(),
                "actor_role": actor_role,
                "state": ArtifactState.REVALIDATION_REQUIRED.value,
                "source_type": ArtifactSourceType.EXTERNAL_EDITOR.value,
                "previous_normalized_sha256": record["content_hash"],
                "normalized_sha256": normalized_sha,
            }
        )
        schema_findings = self._schema_findings(updated)
        if schema_findings:
            return self._blocked(command, schema_findings)
        return CommandResult(
            command,
            True,
            ExitCode.PASS,
            "External content hash drift invalidated the approved/frozen state and requires revalidation.",
            data={"artifact": updated, "summary": {"drift_detected": True, "state": ArtifactState.REVALIDATION_REQUIRED.value, "artifact_version": provenance["artifact_version"], "source_mutations_performed": False}},
            findings=[Finding("GSDLC04A_EXTERNAL_DRIFT_REVALIDATION_PASS", "Hash drift moved the artifact to REVALIDATION_REQUIRED without auto-reverting external content.", Severity.INFO, path=path)],
        )

    def validate_record(self, record: dict[str, Any]) -> CommandResult:
        command = "artifact lifecycle validate record"
        findings = self._schema_findings(record)
        if findings:
            return self._blocked(command, findings)

        policy = self.policy()
        relative_path = str(record["relative_path"])
        safe_path = self._safe_relative_path(relative_path, findings, policy)
        profile = self._profile_policy(str(record["profile_id"]), policy, findings)
        if record["content_hash"] != record["provenance"]["normalized_sha256"]:
            findings.append(Finding("GSDLC04A_RECORD_HASH_MISMATCH_BLOCK", "Record content_hash must equal provenance normalized_sha256.", Severity.BLOCK, path=relative_path))
        if profile is not None:
            if sorted(record["validators"]) != sorted(profile["validators"]):
                findings.append(Finding("GSDLC04A_VALIDATOR_BINDING_BLOCK", "Artifact validators do not match lifecycle policy for the selected profile.", Severity.BLOCK, path=relative_path))
            if bool(record["approval_required"]) != bool(profile["approval_required"]):
                findings.append(Finding("GSDLC04A_APPROVAL_PROFILE_BINDING_BLOCK", "Artifact approval_required does not match lifecycle profile policy.", Severity.BLOCK, path=relative_path))
        if str(record["provenance"]["source_type"]) not in policy["source_types"]:
            findings.append(Finding("GSDLC04A_UNKNOWN_SOURCE_BLOCK", "Artifact provenance contains an unknown source type.", Severity.BLOCK, path=relative_path))

        if findings:
            return self._blocked(command, findings)
        return CommandResult(
            command,
            True,
            ExitCode.PASS,
            "Artifact lifecycle record passed structural and semantic validation.",
            data={"artifact": deepcopy(record), "summary": {"state": record["state"], "profile_id": record["profile_id"], "source_mutations_performed": False}},
            findings=[Finding("GSDLC04A_RECORD_VALID_PASS", "Lifecycle/provenance record is valid.", Severity.INFO, path=safe_path)],
        )

    @staticmethod
    def normalize_content(content: str) -> str:
        if content.startswith("\ufeff"):
            content = content[1:]
        return content.replace("\r\n", "\n").replace("\r", "\n")

    @classmethod
    def hash_source(cls, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @classmethod
    def hash_normalized(cls, content: str) -> str:
        return hashlib.sha256(cls.normalize_content(content).encode("utf-8")).hexdigest()

    def _schema_findings(self, record: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        checks = [
            ("ArtifactState", {"state": record.get("state")}, "artifact.state"),
            ("ArtifactProvenance", record.get("provenance") if isinstance(record.get("provenance"), dict) else {}, "artifact.provenance"),
            ("ArtifactLifecycleRecord", record, "artifact.record"),
        ]
        for schema, payload, label in checks:
            result = self.schemas.validate_payload(schema=schema, payload=payload, instance_label=label)
            if not result.ok:
                findings.extend(
                    Finding(
                        id="GSDLC04A_SCHEMA_BLOCK",
                        message=f"{schema} validation failed: {finding.message}",
                        severity=Severity.BLOCK if finding.severity is not Severity.ERROR else Severity.ERROR,
                        path=finding.path,
                        metadata={"schema": schema, **finding.metadata},
                    )
                    for finding in result.findings
                    if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}
                )
        return findings

    def _source_type(self, source_type: str | ArtifactSourceType, findings: list[Finding]) -> ArtifactSourceType | None:
        try:
            return source_type if isinstance(source_type, ArtifactSourceType) else ArtifactSourceType(str(source_type))
        except ValueError:
            findings.append(Finding("GSDLC04A_UNKNOWN_SOURCE_BLOCK", "Unknown artifact source type; fail-closed.", Severity.BLOCK, metadata={"source_type": str(source_type)}))
            return None

    def _safe_relative_path(self, value: str, findings: list[Finding], policy: dict[str, Any]) -> str:
        raw = str(value or "").strip().replace("\\", "/")
        if not raw or raw.startswith("/") or _DRIVE_PATTERN.match(raw):
            findings.append(Finding("GSDLC04A_PATH_ABSOLUTE_BLOCK", "Artifact path must be a repository-relative path.", Severity.BLOCK, path=raw or None))
            return raw
        pure = PurePosixPath(raw)
        if any(part in {"", ".", ".."} for part in pure.parts) or ".." in pure.parts:
            findings.append(Finding("GSDLC04A_PATH_TRAVERSAL_BLOCK", "Artifact path traversal/ambiguous segments are not allowed.", Severity.BLOCK, path=raw))
            return raw
        suffix = Path(pure.name).suffix.lower()
        if suffix not in policy["path_policy"]["allowed_extensions"]:
            findings.append(Finding("GSDLC04A_PATH_TYPE_BLOCK", "Artifact extension is not allowlisted for GSDLC-04 authoring.", Severity.BLOCK, path=raw, metadata={"extension": suffix}))
        if not re.fullmatch(policy["path_policy"]["filename_pattern"], pure.name):
            findings.append(Finding("GSDLC04A_FILENAME_BLOCK", "Artifact filename failed sanitization policy.", Severity.BLOCK, path=raw))
        resolved = (self.root / Path(*pure.parts)).resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError:
            findings.append(Finding("GSDLC04A_PATH_ESCAPE_BLOCK", "Artifact path resolves outside repository root.", Severity.BLOCK, path=raw))
        if resolved.exists() and resolved.is_symlink():
            findings.append(Finding("GSDLC04A_SYMLINK_BLOCK", "Symlink artifact targets are denied by lifecycle path policy.", Severity.BLOCK, path=raw))
        return pure.as_posix()

    def _validate_content(self, content: str, path: str, findings: list[Finding], policy: dict[str, Any]) -> None:
        if not isinstance(content, str):
            findings.append(Finding("GSDLC04A_CONTENT_TYPE_BLOCK", "Artifact source content must be UTF-8 text.", Severity.BLOCK, path=path))
            return
        size = len(content.encode("utf-8"))
        maximum = int(policy["path_policy"]["max_source_bytes"])
        if size > maximum:
            findings.append(Finding("GSDLC04A_SOURCE_SIZE_BLOCK", "Artifact source exceeds lifecycle size bound.", Severity.BLOCK, path=path, metadata={"bytes": size, "max_bytes": maximum}))
        secret = self.secret_guard.scan_text(content, subject=path)
        if secret.effect.value == "block":
            findings.append(Finding("GSDLC04A_SECRET_AUTO_VERSION_BLOCK", "Secret-like content cannot be automatically versioned into artifact provenance.", Severity.BLOCK, path=path, metadata={"policy_rule": secret.rule_id}))

    @staticmethod
    def _validate_base_commit(base_commit: str, findings: list[Finding]) -> None:
        if not re.fullmatch(r"[0-9a-f]{40}", str(base_commit or "")):
            findings.append(Finding("GSDLC04A_BASE_COMMIT_BLOCK", "Artifact provenance requires an exact 40-character Git base commit.", Severity.BLOCK))

    @staticmethod
    def _validate_identity(actor: str, actor_role: str, session_principal: str, reviewer: str, reviewer_role: str, findings: list[Finding], policy: dict[str, Any]) -> None:
        if not str(actor or "").strip():
            findings.append(Finding("GSDLC04A_ACTOR_REQUIRED_BLOCK", "Artifact provenance requires authenticated author actor.", Severity.BLOCK))
        if actor_role not in policy["roles"]:
            findings.append(Finding("GSDLC04A_ACTOR_ROLE_BLOCK", "Artifact provenance author role is not a canonical RBAC role.", Severity.BLOCK, metadata={"role": actor_role}))
        if not str(session_principal or "").strip():
            findings.append(Finding("GSDLC04A_SESSION_PRINCIPAL_REQUIRED_BLOCK", "Artifact provenance requires authenticated session principal.", Severity.BLOCK))
        if not str(reviewer or "").strip():
            findings.append(Finding("GSDLC04A_REVIEWER_REQUIRED_BLOCK", "Artifact provenance requires explicit reviewer assignment.", Severity.BLOCK))
        if reviewer_role not in policy["roles"]:
            findings.append(Finding("GSDLC04A_REVIEWER_ROLE_BLOCK", "Artifact provenance reviewer role is not a canonical RBAC role.", Severity.BLOCK, metadata={"role": reviewer_role}))

    def _profile_id(self, relative_path: str) -> str:
        if Path(relative_path).suffix.lower() == ".json":
            return "structured-json"
        return self.profile_registry.select(Path(relative_path)).id

    @staticmethod
    def _profile_policy(profile_id: str, policy: dict[str, Any], findings: list[Finding]) -> dict[str, Any] | None:
        profile = policy["profile_permissions"].get(profile_id)
        if not isinstance(profile, dict):
            findings.append(Finding("GSDLC04A_PROFILE_POLICY_BLOCK", "Artifact profile has no lifecycle authoring/import policy.", Severity.BLOCK, metadata={"profile_id": profile_id}))
            return None
        return profile

    @staticmethod
    def _transition_rule(current: ArtifactState, target: ArtifactState, policy: dict[str, Any], *, allow_missing: bool = False) -> dict[str, Any] | None:
        for row in policy["transitions"]:
            if row["from"] == current.value and row["to"] == target.value:
                return row
        if allow_missing:
            return None
        raise ValueError(f"Lifecycle policy does not define transition {current.value}->{target.value}")

    @staticmethod
    def _blocked(command: str, findings: list[Finding]) -> CommandResult:
        exit_code = ExitCode.ERROR if any(f.severity is Severity.ERROR for f in findings) else ExitCode.BLOCK
        return CommandResult(command, False, exit_code, "Artifact lifecycle operation blocked.", data={"summary": {"source_mutations_performed": False, "network_used": False, "external_api_used": False}}, findings=findings)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _optional_text(value: str | None) -> str | None:
    text = str(value or "").strip()
    return text or None
