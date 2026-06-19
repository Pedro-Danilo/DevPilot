from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.observability import EventLogger, EventRecord
from devpilot_core.policy import PathGuard, PolicyEffect, PolicyEngine, PolicyRequest, SecretGuard
from devpilot_core.schemas import SchemaValidator
from devpilot_core.workspace.manager import parse_project_yaml_metadata

_DEFAULT_REGISTRY_PATH = ".devpilot/workspaces/workspace_registry.json"
_DEFAULT_SCHEMA_PATH = "docs/schemas/multiworkspace_registry.schema.json"
_VALID_WORKSPACE_STATUSES = {"active", "registered", "disabled", "archived"}
_VALID_RISK_LEVELS = {"low", "medium", "medium_high", "high"}


@dataclass(frozen=True)
class WorkspaceRegistryOptions:
    """Options for the local multiworkspace registry."""

    registry_path: str = _DEFAULT_REGISTRY_PATH
    schema_path: str = _DEFAULT_SCHEMA_PATH


@dataclass(frozen=True)
class WorkspaceRegisterOptions:
    """Options for registering one local DevPilot workspace."""

    path: str
    workspace_id: str | None = None
    name: str | None = None
    registry_path: str = _DEFAULT_REGISTRY_PATH


@dataclass(frozen=True)
class WorkspaceSelectOptions:
    """Options for selecting the active workspace in the local portfolio."""

    workspace_id: str
    registry_path: str = _DEFAULT_REGISTRY_PATH


class MultiworkspaceRegistry:
    """Governed local registry for FUNC-SPRINT-94 multiworkspace metadata.

    The registry is intentionally local-first and metadata-only. It stores an
    explicit allowlist of DevPilot workspaces, validates each registered path,
    checks isolation of per-workspace state files, and never reads secrets or
    copies data between workspaces. Sprint 94 supports local registry writes for
    registration/selection; portfolio inspection remains read-only.
    """

    def __init__(self, root: Path, *, options: WorkspaceRegistryOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or WorkspaceRegistryOptions()
        self.path_guard = PathGuard(self.root)
        self.secret_guard = SecretGuard()
        self.policy = PolicyEngine(self.root)

    @property
    def registry_path(self) -> Path:
        return self._resolve(self.options.registry_path)

    @property
    def schema_path(self) -> Path:
        return self._resolve(self.options.schema_path)

    def validate(self) -> CommandResult:
        registry_display = _rel(self.root, self.registry_path)
        schema_display = _rel(self.root, self.schema_path)
        findings: list[Finding] = []

        for path, label in [(self.registry_path, "registry"), (self.schema_path, "schema")]:
            decision = self.path_guard.evaluate(path, action="read")
            if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
                return CommandResult(
                    command="workspace registry validate",
                    ok=False,
                    exit_code=ExitCode.BLOCK,
                    message=f"Multiworkspace {label} path was blocked by PathGuard.",
                    data={"summary": _summary_template(registry_display, schema_display, path_allowed=False)},
                    findings=[Finding("MULTIWORKSPACE_PATH_BLOCKED", decision.reason, Severity.BLOCK, path=decision.subject, metadata=decision.metadata)],
                )
            if not path.exists():
                return CommandResult(
                    command="workspace registry validate",
                    ok=False,
                    exit_code=ExitCode.BLOCK,
                    message=f"Multiworkspace {label} file is missing.",
                    data={"summary": _summary_template(registry_display, schema_display, path_allowed=True)},
                    findings=[Finding("MULTIWORKSPACE_REGISTRY_FILE_MISSING", f"Missing multiworkspace {label}: {_rel(self.root, path)}", Severity.BLOCK, path=_rel(self.root, path))],
                )

        registry, load_findings = self._load_registry(command="workspace registry validate")
        if load_findings:
            return CommandResult(
                command="workspace registry validate",
                ok=False,
                exit_code=_exit_code(load_findings),
                message="Multiworkspace registry could not be loaded.",
                data={"summary": _summary_template(registry_display, schema_display, path_allowed=True)},
                findings=load_findings,
            )

        redaction = self.secret_guard.redact(json.dumps(registry, ensure_ascii=False))
        if redaction.redactions:
            findings.append(Finding("MULTIWORKSPACE_REGISTRY_SECRET_RISK_BLOCKED", "SecretGuard detected secret-like material in Multiworkspace Registry; store references only.", Severity.BLOCK, path=registry_display, metadata={"redactions_total": redaction.redactions}))

        schema_result = SchemaValidator(self.root).validate(schema=self.options.schema_path, instance=self.options.registry_path)
        if not schema_result.ok:
            findings.extend(schema_result.findings)

        defaults = registry.get("defaults", {}) if isinstance(registry, dict) else {}
        security = registry.get("security", {}) if isinstance(registry, dict) else {}
        workspaces = registry.get("workspaces") if isinstance(registry, dict) else []
        workspaces = workspaces if isinstance(workspaces, list) else []

        if defaults.get("deny_unregistered_workspaces") is not True:
            findings.append(Finding("UNREGISTERED_WORKSPACES_NOT_DENIED", "Unregistered workspaces must be denied by default.", Severity.BLOCK, path=registry_display))
        if defaults.get("cross_workspace_state_reads") is not False:
            findings.append(Finding("CROSS_WORKSPACE_STATE_READS_NOT_DISABLED", "Cross-workspace state reads must be disabled by default.", Severity.BLOCK, path=registry_display))
        if defaults.get("secret_sharing_allowed") is not False:
            findings.append(Finding("MULTIWORKSPACE_SECRET_SHARING_NOT_DISABLED", "Secrets must not be shared across workspaces.", Severity.BLOCK, path=registry_display))
        for flag in ["network_used", "external_api_used", "shell_used", "remote_execution_used", "mutations_performed", "secrets_read"]:
            if security.get(flag) is not False:
                findings.append(Finding("MULTIWORKSPACE_SECURITY_FLAG_BLOCKED", f"Multiworkspace security flag {flag} must remain false.", Severity.BLOCK, path=registry_display, metadata={"flag": flag}))

        seen_workspace_ids: set[str] = set()
        duplicate_workspace_ids: list[str] = []
        status_counts: Counter[str] = Counter()
        risk_counts: Counter[str] = Counter()
        state_paths: list[str] = []
        path_isolation_passed = True
        state_isolation_passed = True
        unregistered_path_reads = False
        active_workspace_id = str(registry.get("active_workspace_id") or "") if isinstance(registry, dict) else ""
        active_workspace_found = False

        for entry in workspaces:
            if not isinstance(entry, dict):
                findings.append(Finding("MULTIWORKSPACE_ENTRY_INVALID", "Each workspace registry entry must be an object.", Severity.BLOCK, path=registry_display))
                continue
            workspace_id = str(entry.get("workspace_id", "<missing>"))
            if workspace_id in seen_workspace_ids:
                duplicate_workspace_ids.append(workspace_id)
            seen_workspace_ids.add(workspace_id)
            if workspace_id == active_workspace_id:
                active_workspace_found = True
            status = str(entry.get("status", ""))
            risk = str(entry.get("risk_level", ""))
            if status in _VALID_WORKSPACE_STATUSES:
                status_counts[status] += 1
            if risk in _VALID_RISK_LEVELS:
                risk_counts[risk] += 1
            if entry.get("default_effect") != "deny":
                findings.append(Finding("MULTIWORKSPACE_ALLOW_BY_DEFAULT_BLOCKED", "Each workspace entry must be deny-by-default.", Severity.BLOCK, path=registry_display, metadata={"workspace_id": workspace_id}))
            if entry.get("observability_required") is not True or entry.get("eval_required") is not True:
                findings.append(Finding("MULTIWORKSPACE_GOVERNANCE_REQUIRED", "Each workspace entry must require observability and evals.", Severity.BLOCK, path=registry_display, metadata={"workspace_id": workspace_id}))
            if entry.get("network_allowed") is not False or entry.get("external_api_allowed") is not False:
                findings.append(Finding("MULTIWORKSPACE_EXTERNAL_ACCESS_BLOCKED", "Workspace registry entries must not allow network or external APIs in Sprint 94.", Severity.BLOCK, path=registry_display, metadata={"workspace_id": workspace_id}))
            path_value = str(entry.get("path", ""))
            resolved, path_finding = self._registered_workspace_path(path_value, action="read", workspace_id=workspace_id)
            if path_finding is not None:
                path_isolation_passed = False
                findings.append(path_finding)
                continue
            if resolved is None:
                path_isolation_passed = False
                findings.append(Finding("MULTIWORKSPACE_PATH_MISSING", "Workspace registry entry must include a path.", Severity.BLOCK, path=registry_display, metadata={"workspace_id": workspace_id}))
                continue
            project_file = resolved / ".devpilot" / "project.yaml"
            state_file = resolved / ".devpilot" / "devpilot.db"
            if not project_file.is_file():
                findings.append(Finding("MULTIWORKSPACE_PROJECT_FILE_MISSING", "Registered workspace must contain .devpilot/project.yaml.", Severity.BLOCK, path=_rel(self.root, project_file), metadata={"workspace_id": workspace_id}))
            metadata = parse_project_yaml_metadata(project_file)
            declared_project_id = str(metadata.get("project_id") or "")
            if declared_project_id and declared_project_id != entry.get("project_id"):
                findings.append(Finding("MULTIWORKSPACE_PROJECT_ID_MISMATCH", "Workspace project id does not match registry metadata.", Severity.BLOCK, path=_rel(self.root, project_file), metadata={"workspace_id": workspace_id, "project_id": declared_project_id}))
            expected_state = resolved / ".devpilot" / "devpilot.db"
            declared_state_path = str(entry.get("state_path") or ".devpilot/devpilot.db")
            if declared_state_path.replace("\\", "/") != ".devpilot/devpilot.db":
                state_isolation_passed = False
                findings.append(Finding("MULTIWORKSPACE_STATE_PATH_UNSAFE", "Workspace state_path must remain .devpilot/devpilot.db for Sprint 94 isolation.", Severity.BLOCK, path=registry_display, metadata={"workspace_id": workspace_id, "state_path": declared_state_path}))
            state_paths.append(str(expected_state.resolve()))
            if "secret" in json.dumps(entry, ensure_ascii=False).lower() and entry.get("secret_policy") != "reference-only":
                findings.append(Finding("MULTIWORKSPACE_SECRET_POLICY_REQUIRED", "Workspace entries may not embed or share secrets; secret_policy must be reference-only.", Severity.BLOCK, path=registry_display, metadata={"workspace_id": workspace_id}))

        if duplicate_workspace_ids:
            findings.append(Finding("MULTIWORKSPACE_DUPLICATE_WORKSPACE_ID", "Duplicate workspace ids are not allowed.", Severity.BLOCK, path=registry_display, metadata={"workspace_ids": duplicate_workspace_ids}))
        if active_workspace_id and not active_workspace_found:
            findings.append(Finding("MULTIWORKSPACE_ACTIVE_WORKSPACE_MISSING", "active_workspace_id must reference a registered workspace.", Severity.BLOCK, path=registry_display, metadata={"active_workspace_id": active_workspace_id}))
        if len(state_paths) != len(set(state_paths)):
            state_isolation_passed = False
            findings.append(Finding("MULTIWORKSPACE_STATE_PATH_COLLISION", "Each workspace must have an isolated .devpilot/devpilot.db path.", Severity.BLOCK, path=registry_display))

        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.FAIL, Severity.ERROR}]
        summary = {
            **_summary_template(registry_display, schema_display, path_allowed=True),
            "schema_valid": schema_result.ok,
            "workspaces_total": len(workspaces),
            "active_workspace_id": active_workspace_id or None,
            "status_counts": dict(sorted(status_counts.items())),
            "risk_counts": dict(sorted(risk_counts.items())),
            "path_isolation_passed": path_isolation_passed,
            "state_isolation_passed": state_isolation_passed,
            "unregistered_path_reads": unregistered_path_reads,
            "registered_paths_total": len(workspaces),
            "state_paths_total": len(state_paths),
            "blocked_findings_total": len(blocking),
            "network_used": False,
            "external_api_used": False,
            "shell_used": False,
            "remote_execution_used": False,
            "mutations_performed": False,
            "secrets_read": False,
            "preliminary": True,
        }
        ok = not blocking
        return CommandResult(
            command="workspace registry validate",
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(blocking),
            message="Multiworkspace Registry validation passed." if ok else "Multiworkspace Registry validation failed or blocked.",
            data={"summary": summary, "workspaces": [self._public_workspace(entry) for entry in workspaces if isinstance(entry, dict)]},
            findings=findings or [Finding("MULTIWORKSPACE_REGISTRY_VALIDATED", "Multiworkspace Registry is valid, isolated and deny-by-default.", Severity.INFO, metadata=summary)],
        )

    def list(self) -> CommandResult:
        result = self.validate()
        if not result.ok:
            return CommandResult(command="workspace list", ok=False, exit_code=result.exit_code, message="Workspace list blocked because registry validation failed.", data=result.data, findings=result.findings)
        return CommandResult(
            command="workspace list",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Workspace Registry listed successfully.",
            data=result.data,
            findings=[Finding("MULTIWORKSPACE_LIST_PASS", "Workspace Registry listed registered metadata only.", Severity.INFO, metadata=result.data.get("summary", {}))],
        )

    def register(self, options: WorkspaceRegisterOptions) -> CommandResult:
        registry, load_findings = self._load_registry(command="workspace register", create_if_missing=True)
        if load_findings:
            return CommandResult(command="workspace register", ok=False, exit_code=_exit_code(load_findings), message="Workspace registration blocked because registry could not be loaded.", data={}, findings=load_findings)

        target, path_finding = self._registered_workspace_path(options.path, action="read", workspace_id=options.workspace_id or "pending")
        if path_finding is not None:
            return CommandResult(
                command="workspace register",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Workspace registration path was blocked by isolation policy.",
                data={"summary": {"registered": False, "path_allowed": False, "mutations_performed": False}},
                findings=[path_finding],
            )
        assert target is not None
        project_file = target / ".devpilot" / "project.yaml"
        if not project_file.is_file():
            finding = Finding("MULTIWORKSPACE_PROJECT_FILE_MISSING", "Cannot register a path that is not an initialized DevPilot workspace.", Severity.BLOCK, path=_rel(self.root, project_file))
            return CommandResult(command="workspace register", ok=False, exit_code=ExitCode.BLOCK, message="Workspace registration blocked; .devpilot/project.yaml is missing.", data={"summary": {"registered": False, "path_allowed": True, "mutations_performed": False}}, findings=[finding])

        policy_result = self.policy.evaluate(
            PolicyRequest(
                action="write",
                path=self.options.registry_path,
                dry_run=False,
                tool_id="workspace.registry.register",
                subject="multiworkspace:register",
                metadata={"sprint": "FUNC-SPRINT-94"},
            )
        )
        if not policy_result.ok:
            return CommandResult(command="workspace register", ok=False, exit_code=policy_result.exit_code, message="Workspace registration blocked by PolicyEngine.", data=policy_result.data, findings=policy_result.findings)

        metadata = parse_project_yaml_metadata(project_file)
        workspace_id = options.workspace_id or str(metadata.get("project_id") or _slug(target.name))
        name = options.name or str(metadata.get("project_name") or target.name)
        now = _utc_now()
        entries = registry.setdefault("workspaces", [])
        if not isinstance(entries, list):
            finding = Finding("MULTIWORKSPACE_REGISTRY_WORKSPACES_INVALID", "Registry workspaces field must be an array.", Severity.BLOCK, path=_rel(self.root, self.registry_path))
            return CommandResult(command="workspace register", ok=False, exit_code=ExitCode.BLOCK, message="Workspace registration blocked by invalid registry shape.", data={}, findings=[finding])

        rel_path = _rel(self.root, target)
        new_entry = {
            "workspace_id": workspace_id,
            "project_id": str(metadata.get("project_id") or workspace_id),
            "name": name,
            "path": rel_path,
            "path_mode": "relative-to-registry-root",
            "status": "active" if registry.get("active_workspace_id") in (None, workspace_id) else "registered",
            "risk_level": "medium_high",
            "default_effect": "deny",
            "state_path": ".devpilot/devpilot.db",
            "reports_path": "outputs/reports",
            "traces_path": "outputs/traces",
            "secrets_path": ".devpilot/providers.yaml",
            "secret_policy": "reference-only",
            "network_allowed": False,
            "external_api_allowed": False,
            "observability_required": True,
            "eval_required": True,
            "registered_at": now,
            "updated_at": now,
        }
        replaced = False
        for index, entry in enumerate(entries):
            if isinstance(entry, dict) and entry.get("workspace_id") == workspace_id:
                existing = dict(entry)
                existing.update(new_entry)
                existing["registered_at"] = entry.get("registered_at") or now
                entries[index] = existing
                replaced = True
                break
        if not replaced:
            entries.append(new_entry)
        if not registry.get("active_workspace_id"):
            registry["active_workspace_id"] = workspace_id
        registry["updated_at"] = now
        self._write_registry(registry)
        self._emit_event("workspace.register", workspace_id)
        validation = self.validate()
        summary = dict((validation.data or {}).get("summary") or {})
        summary.update({"registered": True, "workspace_id": workspace_id, "replaced": replaced, "mutations_performed": True, "registry_path": _rel(self.root, self.registry_path)})
        return CommandResult(
            command="workspace register",
            ok=validation.ok,
            exit_code=validation.exit_code,
            message="Workspace registered in local Multiworkspace Registry." if validation.ok else "Workspace was written but registry validation now fails.",
            data={"summary": summary, "workspace": self._public_workspace(new_entry), "validation": validation.data.get("summary", {}) if validation.data else {}},
            findings=validation.findings if not validation.ok else [Finding("MULTIWORKSPACE_REGISTERED", "Workspace registration completed as controlled metadata write.", Severity.INFO, metadata=summary)],
        )

    def select(self, options: WorkspaceSelectOptions) -> CommandResult:
        registry, load_findings = self._load_registry(command="workspace select")
        if load_findings:
            return CommandResult(command="workspace select", ok=False, exit_code=_exit_code(load_findings), message="Workspace selection blocked because registry could not be loaded.", data={}, findings=load_findings)
        workspaces = registry.get("workspaces") if isinstance(registry, dict) else []
        workspaces = workspaces if isinstance(workspaces, list) else []
        if not any(isinstance(entry, dict) and entry.get("workspace_id") == options.workspace_id for entry in workspaces):
            return CommandResult(
                command="workspace select",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Workspace selection blocked; workspace_id is not registered.",
                data={"summary": {"selected": False, "workspace_id": options.workspace_id, "mutations_performed": False}},
                findings=[Finding("MULTIWORKSPACE_NOT_REGISTERED", "Cannot select an unregistered workspace.", Severity.BLOCK, metadata={"workspace_id": options.workspace_id})],
            )
        policy_result = self.policy.evaluate(
            PolicyRequest(action="write", path=self.options.registry_path, dry_run=False, tool_id="workspace.registry.select", subject="multiworkspace:select", metadata={"sprint": "FUNC-SPRINT-94"})
        )
        if not policy_result.ok:
            return CommandResult(command="workspace select", ok=False, exit_code=policy_result.exit_code, message="Workspace selection blocked by PolicyEngine.", data=policy_result.data, findings=policy_result.findings)
        registry["active_workspace_id"] = options.workspace_id
        registry["updated_at"] = _utc_now()
        for entry in workspaces:
            if isinstance(entry, dict):
                entry["status"] = "active" if entry.get("workspace_id") == options.workspace_id else "registered"
                entry["updated_at"] = registry["updated_at"]
        self._write_registry(registry)
        self._emit_event("workspace.select", options.workspace_id)
        validation = self.validate()
        summary = dict((validation.data or {}).get("summary") or {})
        summary.update({"selected": True, "workspace_id": options.workspace_id, "mutations_performed": True})
        return CommandResult(
            command="workspace select",
            ok=validation.ok,
            exit_code=validation.exit_code,
            message="Active workspace selection updated." if validation.ok else "Workspace selection was written but registry validation now fails.",
            data={"summary": summary},
            findings=validation.findings if not validation.ok else [Finding("MULTIWORKSPACE_SELECTED", "Active workspace updated as controlled metadata write.", Severity.INFO, metadata=summary)],
        )

    def resolve_registered_workspace(self, entry: dict[str, Any]) -> Path | None:
        resolved, finding = self._registered_workspace_path(str(entry.get("path", "")), action="read", workspace_id=str(entry.get("workspace_id", "unknown")))
        return None if finding else resolved

    def _load_registry(self, *, command: str, create_if_missing: bool = False) -> tuple[dict[str, Any], list[Finding]]:
        decision = self.path_guard.evaluate(self.registry_path, action="read")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            return {}, [Finding("MULTIWORKSPACE_REGISTRY_PATH_BLOCKED", decision.reason, Severity.BLOCK, path=decision.subject, metadata=decision.metadata)]
        if not self.registry_path.exists():
            if create_if_missing:
                return _default_registry(), []
            return {}, [Finding("MULTIWORKSPACE_REGISTRY_FILE_MISSING", "Multiworkspace registry file is missing.", Severity.BLOCK, path=_rel(self.root, self.registry_path))]
        try:
            payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return {}, [Finding("MULTIWORKSPACE_REGISTRY_INVALID_JSON", str(exc), Severity.ERROR, path=_rel(self.root, self.registry_path))]
        if not isinstance(payload, dict):
            return {}, [Finding("MULTIWORKSPACE_REGISTRY_INVALID_SHAPE", "Multiworkspace registry root must be an object.", Severity.BLOCK, path=_rel(self.root, self.registry_path))]
        return payload, []

    def _write_registry(self, registry: dict[str, Any]) -> None:
        decision = self.path_guard.evaluate(self.registry_path, action="write")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            raise ValueError(f"PathGuard blocked registry write: {decision.reason}")
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def _registered_workspace_path(self, value: str, *, action: str, workspace_id: str) -> tuple[Path | None, Finding | None]:
        if not value or value.strip() == "":
            return None, Finding("MULTIWORKSPACE_PATH_MISSING", "Workspace path is required.", Severity.BLOCK, metadata={"workspace_id": workspace_id})
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        resolved = candidate.resolve()
        decision = self.path_guard.evaluate(resolved, action=action)
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            return None, Finding("MULTIWORKSPACE_PATH_BLOCKED", decision.reason, Severity.BLOCK, path=decision.subject, metadata={"workspace_id": workspace_id, **decision.metadata})
        return resolved, None

    def _public_workspace(self, entry: dict[str, Any]) -> dict[str, Any]:
        return {
            "workspace_id": entry.get("workspace_id"),
            "project_id": entry.get("project_id"),
            "name": entry.get("name"),
            "path": entry.get("path"),
            "status": entry.get("status"),
            "risk_level": entry.get("risk_level"),
            "default_effect": entry.get("default_effect"),
            "state_path": entry.get("state_path"),
            "reports_path": entry.get("reports_path"),
            "traces_path": entry.get("traces_path"),
            "secret_policy": entry.get("secret_policy"),
            "network_allowed": entry.get("network_allowed"),
            "external_api_allowed": entry.get("external_api_allowed"),
            "observability_required": entry.get("observability_required"),
            "eval_required": entry.get("eval_required"),
        }

    def _resolve(self, path: str | Path) -> Path:
        candidate = Path(path)
        return candidate if candidate.is_absolute() else self.root / candidate

    def _emit_event(self, event_type: str, workspace_id: str) -> None:
        EventLogger(self.root).emit(
            EventRecord(
                event_type=event_type,
                command=event_type.replace(".", " "),
                subject=f"workspace:{workspace_id}",
                message="Multiworkspace metadata event emitted.",
                metadata={"workspace_id": workspace_id, "sprint": "FUNC-SPRINT-94", "preliminary": True},
            )
        )


def _default_registry() -> dict[str, Any]:
    now = _utc_now()
    return {
        "schema_version": "1.0",
        "created_by": "FUNC-SPRINT-94",
        "updated_at": now,
        "active_workspace_id": None,
        "defaults": {
            "deny_unregistered_workspaces": True,
            "cross_workspace_state_reads": False,
            "secret_sharing_allowed": False,
            "portfolio_status_read_only": True,
        },
        "security": {
            "network_used": False,
            "external_api_used": False,
            "shell_used": False,
            "remote_execution_used": False,
            "mutations_performed": False,
            "secrets_read": False,
        },
        "workspaces": [],
    }


def _summary_template(registry_path: str, schema_path: str, *, path_allowed: bool) -> dict[str, Any]:
    return {
        "registry_path": registry_path,
        "schema_path": schema_path,
        "path_allowed": path_allowed,
        "network_used": False,
        "external_api_used": False,
        "shell_used": False,
        "remote_execution_used": False,
        "mutations_performed": False,
        "secrets_read": False,
        "preliminary": True,
    }


def _exit_code(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _slug(value: str) -> str:
    normalized = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    return normalized or "workspace"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
