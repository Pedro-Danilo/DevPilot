from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlsplit

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.policy import PathGuard, PolicyEffect, configured_external_workspace_roots

PROJECT_INTAKE_SCHEMA_ID = "SCHEMA-DEVPL-GSDLC-03-A-PROJECT-INTAKE-V1"
TECHNOLOGY_CATALOG_SCHEMA_ID = "SCHEMA-DEVPL-GSDLC-03-A-TECHNOLOGY-CATALOG-V1"
PROJECT_CREATION_PLAN_SCHEMA_ID = "SCHEMA-DEVPL-GSDLC-03-A-PROJECT-CREATION-PLAN-V1"
DEFAULT_TECHNOLOGY_CATALOG = ".devpilot/workspaces/technology_catalog.json"

_SAFE_PROJECT_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{2,63}$")
_FORBIDDEN_SECRET_KEYS = {
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "credential",
    "credentials",
    "private_key",
    "authorization",
    "cookie",
}
_FORBIDDEN_COMMAND_KEYS = {"command", "command_line", "shell", "shell_text", "script", "argv"}


class ProjectEntryMode(str, Enum):
    CREATE_NEW = "CREATE_NEW"
    OPEN_EXISTING = "OPEN_EXISTING"
    IMPORT_GIT = "IMPORT_GIT"


class GitSourceKind(str, Enum):
    LOCAL_PATH = "local-path"
    REMOTE_URL = "remote-url"


@dataclass(frozen=True)
class ProjectIntake:
    project_id: str
    project_name: str
    target_root: str
    entry_mode: ProjectEntryMode
    frontend: str
    backend: str
    database: str
    project_type: str = "agent-assisted-sdlc"
    standards: tuple[str, ...] = ("MIPSoftware", "MIASI")
    provider_mode: str = "none"
    provider_id: str | None = None
    restrictions: Mapping[str, bool] | None = None
    git_source_kind: GitSourceKind | None = None
    git_source_location: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "ProjectIntake":
        stack = payload.get("stack") if isinstance(payload.get("stack"), Mapping) else {}
        provider = payload.get("provider") if isinstance(payload.get("provider"), Mapping) else {}
        source = payload.get("git_source") if isinstance(payload.get("git_source"), Mapping) else None
        restrictions = payload.get("restrictions") if isinstance(payload.get("restrictions"), Mapping) else {}
        return cls(
            project_id=str(payload.get("project_id") or ""),
            project_name=str(payload.get("project_name") or ""),
            target_root=str(payload.get("target_root") or ""),
            entry_mode=ProjectEntryMode(str(payload.get("entry_mode") or "")),
            frontend=str(stack.get("frontend") or ""),
            backend=str(stack.get("backend") or ""),
            database=str(stack.get("database") or ""),
            project_type=str(payload.get("project_type") or "agent-assisted-sdlc"),
            standards=tuple(str(item) for item in payload.get("standards", ())),
            provider_mode=str(provider.get("mode") or "none"),
            provider_id=str(provider.get("provider_id")) if provider.get("provider_id") is not None else None,
            restrictions={str(k): bool(v) for k, v in restrictions.items()},
            git_source_kind=GitSourceKind(str(source.get("kind"))) if source else None,
            git_source_location=str(source.get("location")) if source else None,
        )

    def to_mapping(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "schema_id": PROJECT_INTAKE_SCHEMA_ID,
            "schema_version": "1.0",
            "project_id": self.project_id,
            "project_name": self.project_name,
            "project_type": self.project_type,
            "entry_mode": self.entry_mode.value,
            "target_root": self.target_root,
            "stack": {
                "frontend": self.frontend,
                "backend": self.backend,
                "database": self.database,
            },
            "standards": list(self.standards),
            "provider": {"mode": self.provider_mode, "provider_id": self.provider_id},
            "restrictions": dict(self.restrictions or {}),
        }
        if self.git_source_kind is not None:
            data["git_source"] = {
                "kind": self.git_source_kind.value,
                "location": self.git_source_location or "",
            }
        return data


class ProjectEntryContractService:
    """Deterministic GSDLC-03-A intake/catalog contract boundary.

    The service only validates and builds immutable planning contracts. It does
    not create workspaces, run Git, install dependencies, invoke shells, use
    network, call models or write outside caller-selected evidence outputs.
    """

    def __init__(
        self,
        platform_root: Path,
        *,
        allowed_roots: Iterable[Path] | None = None,
        catalog_path: str | Path = DEFAULT_TECHNOLOGY_CATALOG,
    ) -> None:
        self.platform_root = Path(platform_root).resolve()
        roots = tuple(Path(item).resolve() for item in (allowed_roots if allowed_roots is not None else configured_external_workspace_roots()))
        self.allowed_roots = roots
        self.path_guard = PathGuard(self.platform_root, allowed_external_roots=roots)
        candidate = Path(catalog_path)
        self.catalog_path = candidate if candidate.is_absolute() else self.platform_root / candidate

    def load_catalog(self) -> dict[str, Any]:
        return json.loads(self.catalog_path.read_text(encoding="utf-8"))

    def validate_intake(self, payload: Mapping[str, Any]) -> CommandResult:
        findings: list[Finding] = []
        if _contains_forbidden_key(payload, _FORBIDDEN_SECRET_KEYS):
            findings.append(Finding("PROJECT_INTAKE_SECRET_FIELD_BLOCKED", "Project intake must not contain credential or secret material fields.", Severity.BLOCK))
        if _contains_forbidden_key(payload, _FORBIDDEN_COMMAND_KEYS):
            findings.append(Finding("PROJECT_INTAKE_FREE_FORM_COMMAND_BLOCKED", "Project intake must not contain shell/command fields; only typed operations are allowed.", Severity.BLOCK))

        try:
            intake = ProjectIntake.from_mapping(payload)
        except (ValueError, TypeError) as exc:
            findings.append(Finding("PROJECT_INTAKE_SHAPE_BLOCKED", f"Project intake could not be normalized: {exc}", Severity.BLOCK))
            return self._result("project intake validate", findings, data={"writes_performed": False})

        findings.extend(self._validate_scalar_contract(intake))
        target: Path | None = None
        if intake.target_root.strip():
            target = Path(intake.target_root).expanduser()
            findings.extend(self._validate_target(intake, target))
        findings.extend(self._validate_git_source(intake, target))

        catalog = self.load_catalog()
        profile = _resolve_profile(catalog, intake.frontend, intake.backend, intake.database)
        if profile is None:
            findings.append(
                Finding(
                    "PROJECT_INTAKE_UNSUPPORTED_OR_AMBIGUOUS_STACK",
                    "Technology stack is unsupported or ambiguous in the active TechnologyCatalog.",
                    Severity.BLOCK,
                    metadata={"frontend": intake.frontend, "backend": intake.backend, "database": intake.database},
                )
            )

        normalized = intake.to_mapping()
        if intake.git_source_kind is GitSourceKind.REMOTE_URL:
            source = normalized.get("git_source")
            if isinstance(source, dict):
                source["location"] = _sanitize_remote_git_location(str(source.get("location") or ""))
        data = {
            "intake": normalized,
            "intake_hash": stable_sha256(normalized),
            "technology_profile_id": profile.get("profile_id") if profile else None,
            "target_root_resolved": str(target.resolve(strict=False)) if target is not None else None,
            "writes_performed": False,
            "network_used": False,
            "external_api_used": False,
            "pilot_workspace_accessed": False,
            "arbitrary_shell_used": False,
        }
        if not findings:
            findings.append(Finding("PROJECT_INTAKE_CONTRACT_PASS", "Project intake is valid for deterministic contract planning.", Severity.INFO))
        return self._result("project intake validate", findings, data=data)

    def build_creation_plan(self, payload: Mapping[str, Any]) -> CommandResult:
        validated = self.validate_intake(payload)
        if not validated.ok:
            return CommandResult(
                command="project creation plan",
                ok=False,
                exit_code=validated.exit_code,
                message="Project creation plan blocked because intake validation failed.",
                data={"validation": validated.to_dict(), "writes_performed": False},
                findings=validated.findings,
            )

        intake = ProjectIntake.from_mapping(payload)
        catalog = self.load_catalog()
        profile = _resolve_profile(catalog, intake.frontend, intake.backend, intake.database)
        assert profile is not None
        target = Path(intake.target_root).expanduser().resolve(strict=False)
        boundary_root = _matching_boundary(target, self.allowed_roots)
        operations = self._operations_for(intake, catalog)
        source_intake_hash = stable_sha256(intake.to_mapping())

        plan_without_hash: dict[str, Any] = {
            "schema_id": PROJECT_CREATION_PLAN_SCHEMA_ID,
            "schema_version": "1.0",
            "plan_version": "1.0.0",
            "planning_only": True,
            "execution_enabled": False,
            "source_intake_hash": source_intake_hash,
            "entry_mode": intake.entry_mode.value,
            "project": {
                "project_id": intake.project_id,
                "project_name": intake.project_name,
                "project_type": intake.project_type,
                "standards": list(intake.standards),
                "provider_mode": intake.provider_mode,
                "provider_id": intake.provider_id,
            },
            "target": {
                "root": str(target),
                "boundary_root": str(boundary_root) if boundary_root else None,
                "platform_overlap": False,
                "collision_state": _collision_state(target),
            },
            "stack": {
                "profile_id": profile["profile_id"],
                "frontend": intake.frontend,
                "backend": intake.backend,
                "database": intake.database,
            },
            "typed_operations": operations,
            "network": {
                "required_by_plan": any(bool(item["network_required"]) for item in operations),
                "runtime_network_used": False,
                "silent_network_allowed": False,
                "remote_git_disabled_by_default": True,
            },
            "cost": {
                "cost_class": "zero-contract-planning",
                "external_cost_estimate": 0.0,
                "currency": "USD",
                "billing_action_performed": False,
            },
            "approval": {
                "approval_required_for_execute": any(bool(item["approval_required"]) for item in operations),
                "approval_requested": False,
                "approval_bound_to_plan_hash": True,
            },
            "rollback": {
                "rollback_required_for_mutating_plan": any(bool(item["writes"]) for item in operations),
                "rollback_executed": False,
                "contract_only": True,
            },
            "safety": {
                "local_first": True,
                "deny_by_default": True,
                "dry_run_default": True,
                "writes_performed": False,
                "network_used": False,
                "external_api_used": False,
                "arbitrary_shell_used": False,
                "pilot_workspace_accessed": False,
                "credentials_included": False,
            },
        }
        plan = {**plan_without_hash, "plan_hash": stable_sha256(plan_without_hash)}
        return CommandResult(
            command="project creation plan",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Deterministic project creation contract plan built; no side effects were executed.",
            data={"plan": plan, "writes_performed": False},
            findings=[Finding("PROJECT_CREATION_PLAN_CONTRACT_PASS", "Project creation plan contract is deterministic and side-effect free.", Severity.INFO)],
        )

    def _validate_scalar_contract(self, intake: ProjectIntake) -> list[Finding]:
        findings: list[Finding] = []
        if not _SAFE_PROJECT_ID.fullmatch(intake.project_id):
            findings.append(Finding("PROJECT_INTAKE_PROJECT_ID_BLOCKED", "project_id must match the bounded lowercase identifier contract.", Severity.BLOCK))
        if not intake.project_name.strip() or len(intake.project_name.strip()) > 120 or any(ch in intake.project_name for ch in "\r\n"):
            findings.append(Finding("PROJECT_INTAKE_PROJECT_NAME_BLOCKED", "project_name must be 1..120 characters and contain no line breaks.", Severity.BLOCK))
        if intake.project_type != "agent-assisted-sdlc":
            findings.append(Finding("PROJECT_INTAKE_PROJECT_TYPE_BLOCKED", "Only agent-assisted-sdlc is supported by GSDLC-03-A.", Severity.BLOCK))
        if set(intake.standards) != {"MIPSoftware", "MIASI"}:
            findings.append(Finding("PROJECT_INTAKE_STANDARDS_BLOCKED", "MIPSoftware and MIASI are both mandatory for the current Guided SDLC project contract.", Severity.BLOCK))
        if intake.provider_mode not in {"none", "mock", "local", "external-api"}:
            findings.append(Finding("PROJECT_INTAKE_PROVIDER_MODE_BLOCKED", "Unsupported provider mode.", Severity.BLOCK))
        restrictions = dict(intake.restrictions or {})
        for key in ("arbitrary_shell_allowed", "silent_network_allowed", "remote_git_execute_allowed"):
            if restrictions.get(key) is not False:
                findings.append(Finding("PROJECT_INTAKE_RESTRICTION_BLOCKED", f"{key} must be explicitly false in GSDLC-03-A.", Severity.BLOCK, metadata={"restriction": key}))
        return findings

    def _validate_target(self, intake: ProjectIntake, target: Path) -> list[Finding]:
        findings: list[Finding] = []
        raw = intake.target_root.replace("\\", "/")
        if ".." in raw.split("/"):
            findings.append(Finding("PROJECT_INTAKE_TRAVERSAL_BLOCKED", "Parent traversal segments are not accepted even when canonicalization would remain inside a root.", Severity.BLOCK, path=raw))
        if not target.is_absolute():
            findings.append(Finding("PROJECT_INTAKE_ABSOLUTE_ROOT_REQUIRED", "target_root must be absolute.", Severity.BLOCK, path=raw))
            return findings

        resolved = target.resolve(strict=False)
        if _paths_overlap(resolved, self.platform_root):
            findings.append(Finding("PROJECT_INTAKE_PLATFORM_OVERLAP_BLOCKED", "Project target must not overlap the DevPilot platform repository.", Severity.BLOCK, path=str(resolved)))
        decision = self.path_guard.evaluate(resolved, action="create")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            findings.append(Finding("PROJECT_INTAKE_ALLOWED_ROOT_BLOCKED", decision.reason, Severity.BLOCK, path=decision.subject, metadata=decision.metadata))
        elif decision.effect is PolicyEffect.WARN:
            findings.append(Finding("PROJECT_INTAKE_PATH_WARNING_BLOCKED", decision.reason, Severity.BLOCK, path=decision.subject, metadata=decision.metadata))
        if _contains_symlink_component(target):
            findings.append(Finding("PROJECT_INTAKE_SYMLINK_BLOCKED", "Symlinked target/ancestor components are rejected at intake contract time.", Severity.BLOCK, path=str(target)))

        if intake.entry_mode in {ProjectEntryMode.CREATE_NEW, ProjectEntryMode.IMPORT_GIT}:
            if target.exists() and (not target.is_dir() or any(target.iterdir())):
                findings.append(Finding("PROJECT_INTAKE_TARGET_COLLISION_BLOCKED", "CREATE_NEW/IMPORT_GIT target must be absent or an empty directory.", Severity.BLOCK, path=str(target)))
        elif intake.entry_mode is ProjectEntryMode.OPEN_EXISTING:
            if not target.is_dir():
                findings.append(Finding("PROJECT_INTAKE_OPEN_TARGET_MISSING", "OPEN_EXISTING requires an existing directory.", Severity.BLOCK, path=str(target)))
        return findings

    def _validate_git_source(self, intake: ProjectIntake, target: Path | None) -> list[Finding]:
        findings: list[Finding] = []
        if intake.entry_mode is ProjectEntryMode.IMPORT_GIT:
            if intake.git_source_kind is None or not (intake.git_source_location or "").strip():
                findings.append(Finding("PROJECT_INTAKE_GIT_SOURCE_REQUIRED", "IMPORT_GIT requires a typed local-path or remote-url source.", Severity.BLOCK))
                return findings
            if intake.git_source_kind is GitSourceKind.LOCAL_PATH:
                raw = (intake.git_source_location or "").replace("\\", "/")
                source = Path(intake.git_source_location or "").expanduser()
                if ".." in raw.split("/"):
                    findings.append(Finding("PROJECT_INTAKE_GIT_LOCAL_TRAVERSAL_BLOCKED", "Local Git source may not contain parent traversal segments.", Severity.BLOCK, path=raw))
                if not source.is_absolute():
                    findings.append(Finding("PROJECT_INTAKE_GIT_LOCAL_ABSOLUTE_PATH_REQUIRED", "Local Git source must be an absolute path.", Severity.BLOCK, path=raw))
                else:
                    resolved = source.resolve(strict=False)
                    if _paths_overlap(resolved, self.platform_root):
                        findings.append(Finding("PROJECT_INTAKE_GIT_LOCAL_PLATFORM_OVERLAP_BLOCKED", "Local Git source must not overlap the DevPilot platform repository.", Severity.BLOCK, path=str(resolved)))
                    decision = self.path_guard.evaluate(resolved, action="read")
                    if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY, PolicyEffect.WARN}:
                        findings.append(Finding("PROJECT_INTAKE_GIT_LOCAL_ALLOWED_ROOT_BLOCKED", decision.reason, Severity.BLOCK, path=decision.subject, metadata=decision.metadata))
                    if _contains_symlink_component(source):
                        findings.append(Finding("PROJECT_INTAKE_GIT_LOCAL_SYMLINK_BLOCKED", "Symlinked local Git source/ancestor components are rejected at intake contract time.", Severity.BLOCK, path=str(source)))
                    if target is not None and resolved == target.resolve(strict=False):
                        findings.append(Finding("PROJECT_INTAKE_GIT_SOURCE_TARGET_COLLISION_BLOCKED", "Local Git source and import target must be different paths.", Severity.BLOCK, path=str(resolved)))
            if intake.git_source_kind is GitSourceKind.REMOTE_URL:
                parsed = urlsplit(intake.git_source_location or "")
                if parsed.username is not None or parsed.password is not None:
                    findings.append(Finding("PROJECT_INTAKE_GIT_CREDENTIAL_MATERIAL_BLOCKED", "Remote Git URL must not embed username/password credentials.", Severity.BLOCK))
                if parsed.scheme not in {"https", "ssh"}:
                    findings.append(Finding("PROJECT_INTAKE_GIT_REMOTE_SCHEME_BLOCKED", "Remote Git URL scheme must be https or ssh for plan-only handling.", Severity.BLOCK))
        elif intake.git_source_kind is not None:
            findings.append(Finding("PROJECT_INTAKE_GIT_SOURCE_MODE_MISMATCH", "git_source is only valid for IMPORT_GIT.", Severity.BLOCK))
        return findings

    def _operations_for(self, intake: ProjectIntake, catalog: Mapping[str, Any]) -> list[dict[str, Any]]:
        allowed = {item["operation_id"]: item for item in catalog.get("typed_operations", []) if isinstance(item, Mapping)}
        by_mode = {
            ProjectEntryMode.CREATE_NEW: [
                "workspace.target.prepare",
                "workspace.structure.materialize",
                "git.init",
                "python.venv.create",
                "dependency.python.install",
                "dependency.node.install",
                "workspace.register",
            ],
            ProjectEntryMode.OPEN_EXISTING: ["workspace.inspect", "workspace.register"],
            ProjectEntryMode.IMPORT_GIT: [
                "git.import.local" if intake.git_source_kind is GitSourceKind.LOCAL_PATH else "git.clone.remote",
                "workspace.register",
            ],
        }
        operations: list[dict[str, Any]] = []
        for operation_id in by_mode[intake.entry_mode]:
            item = allowed.get(operation_id)
            if item is None:
                # Catalog validation tests make this unreachable in valid source.
                continue
            operations.append(
                {
                    "operation_id": operation_id,
                    "category": item["category"],
                    "writes": bool(item["writes"]),
                    "network_required": bool(item["network_required"]),
                    "approval_required": bool(item["approval_required"]),
                    "rollback_required": bool(item["rollback_required"]),
                    "execution_status": "planned-contract-only",
                }
            )
        return operations

    @staticmethod
    def _result(command: str, findings: list[Finding], *, data: dict[str, Any]) -> CommandResult:
        blocking = [item for item in findings if item.severity in {Severity.BLOCK, Severity.FAIL, Severity.ERROR}]
        ok = not blocking
        return CommandResult(
            command=command,
            ok=ok,
            exit_code=ExitCode.PASS if ok else exit_code_for_findings(findings, default_ok=False),
            message="Project intake contract validated." if ok else "Project intake contract blocked.",
            data=data,
            findings=findings,
        )


def stable_sha256(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _resolve_profile(catalog: Mapping[str, Any], frontend: str, backend: str, database: str) -> Mapping[str, Any] | None:
    matches = [
        item
        for item in catalog.get("profiles", [])
        if isinstance(item, Mapping)
        and item.get("frontend") == frontend
        and item.get("backend") == backend
        and item.get("database") == database
    ]
    return matches[0] if len(matches) == 1 else None


def _contains_forbidden_key(value: Any, forbidden: set[str]) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).strip().lower()
            if normalized in forbidden:
                return True
            if _contains_forbidden_key(item, forbidden):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_forbidden_key(item, forbidden) for item in value)
    return False


def _paths_overlap(left: Path, right: Path) -> bool:
    left = left.resolve(strict=False)
    right = right.resolve(strict=False)
    return _is_relative_to(left, right) or _is_relative_to(right, left)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _matching_boundary(target: Path, roots: tuple[Path, ...]) -> Path | None:
    for root in roots:
        if _is_relative_to(target.resolve(strict=False), root.resolve(strict=False)):
            return root.resolve(strict=False)
    return None


def _contains_symlink_component(path: Path) -> bool:
    candidate = path.expanduser()
    # Walk only existing components. Missing descendants cannot themselves be
    # symlinks yet, while any existing symlink ancestor remains detectable.
    parts = candidate.parts
    if not parts:
        return False
    current = Path(parts[0])
    for part in parts[1:]:
        current = current / part
        if current.exists() or current.is_symlink():
            if current.is_symlink():
                return True
    return candidate.is_symlink()


def _sanitize_remote_git_location(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.username is None and parsed.password is None:
        return value
    host = parsed.hostname or ""
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    return parsed._replace(netloc=host).geturl()


def _collision_state(target: Path) -> str:
    if not target.exists():
        return "absent"
    if target.is_dir() and not any(target.iterdir()):
        return "empty-directory"
    if target.is_dir():
        return "non-empty-directory"
    return "non-directory"
