from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PathGuard, PolicyEngine, PolicyRequest
from devpilot_core.policy.decisions import PolicyEffect
from devpilot_core.schemas import SchemaValidator

_DEFAULT_REGISTRY = ".devpilot/remote/runner_registry.json"
_DEFAULT_SCHEMA = "docs/schemas/remote_runner.schema.json"


@dataclass(frozen=True)
class RemoteRunnerStatusOptions:
    """Options for inspecting the experimental remote runner registry."""

    registry_path: str = _DEFAULT_REGISTRY
    schema_path: str = _DEFAULT_SCHEMA


class RemoteRunnerRegistry:
    """Validate the local remote-runner experiment registry.

    Sprint 98 intentionally introduces only a disabled-by-default metadata
    boundary. The registry may describe future runner profiles, but it must not
    enable command execution, network calls, cloud control plane usage or source
    mutations. Validation is local-only and fails closed when the contract is
    missing or unsafe.
    """

    def __init__(self, root: Path, *, options: RemoteRunnerStatusOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or RemoteRunnerStatusOptions()
        self.path_guard = PathGuard(self.root)

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        registry_path = self._resolve(self.options.registry_path)
        schema_path = self._resolve(self.options.schema_path)
        registry_rel = _rel(self.root, registry_path)
        schema_rel = _rel(self.root, schema_path)
        summary: dict[str, Any] = {
            "registry_path": registry_rel,
            "schema_path": schema_rel,
            "registry_exists": registry_path.is_file(),
            "schema_exists": schema_path.is_file(),
            "schema_valid": False,
            "remote_runner_enabled": False,
            "execution_allowed": False,
            "remote_execution_used": False,
            "cloud_control_plane_enabled": False,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
        decision = self.path_guard.evaluate(registry_rel, action="read")
        if decision.effect == PolicyEffect.BLOCK:
            findings.append(decision.to_finding())
        if not registry_path.is_file():
            findings.append(Finding("REMOTE_RUNNER_REGISTRY_MISSING", "Remote runner registry is missing.", Severity.BLOCK, path=registry_rel))
        if not schema_path.is_file():
            findings.append(Finding("REMOTE_RUNNER_SCHEMA_MISSING", "Remote runner schema is missing.", Severity.BLOCK, path=schema_rel))
        if findings:
            return CommandResult("remote runner status", False, _exit_code(findings), "Remote runner status blocked by missing or unsafe registry.", data={"summary": summary}, findings=findings)

        schema_result = SchemaValidator(self.root).validate(schema=schema_rel, instance=registry_rel)
        summary["schema_valid"] = bool(schema_result.ok and schema_result.data.get("summary", {}).get("valid") is True)
        if not summary["schema_valid"]:
            findings.extend(schema_result.findings)
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding("REMOTE_RUNNER_REGISTRY_JSON_INVALID", "Remote runner registry is not valid JSON.", Severity.ERROR, path=registry_rel, metadata={"error": str(exc)}))
            return CommandResult("remote runner status", False, ExitCode.ERROR, "Remote runner registry JSON is invalid.", data={"summary": summary}, findings=findings)

        security = registry.get("security", {}) if isinstance(registry, dict) else {}
        runners = registry.get("runners", []) if isinstance(registry, dict) else []
        summary.update(
            {
                "status": registry.get("status"),
                "experimental": bool(registry.get("experimental", True)),
                "runners_total": len(runners) if isinstance(runners, list) else 0,
                "remote_runner_enabled": bool(security.get("remote_runner_enabled", False)),
                "execution_allowed": bool(security.get("execution_allowed", False)),
                "remote_execution_used": bool(security.get("remote_execution_used", False)),
                "cloud_control_plane_enabled": bool(security.get("cloud_control_plane_enabled", False)),
                "network_used": bool(security.get("network_used", False)),
                "external_api_used": bool(security.get("external_api_used", False)),
                "shell_allowed": bool(security.get("shell_allowed", False)),
                "arbitrary_command_execution_allowed": bool(security.get("arbitrary_command_execution_allowed", False)),
                "credentials_required": bool(security.get("credentials_required", False)),
                "secrets_read": bool(security.get("secrets_read", False)),
            }
        )
        unsafe_flags = {
            "remote_runner_enabled": summary["remote_runner_enabled"],
            "execution_allowed": summary["execution_allowed"],
            "remote_execution_used": summary["remote_execution_used"],
            "cloud_control_plane_enabled": summary["cloud_control_plane_enabled"],
            "network_used": summary["network_used"],
            "external_api_used": summary["external_api_used"],
            "shell_allowed": summary["shell_allowed"],
            "arbitrary_command_execution_allowed": summary["arbitrary_command_execution_allowed"],
            "credentials_required": summary["credentials_required"],
            "secrets_read": summary["secrets_read"],
        }
        for key, enabled in unsafe_flags.items():
            if enabled:
                findings.append(Finding("REMOTE_RUNNER_UNSAFE_FLAG_BLOCKED", "Remote runner registry enables a forbidden experimental flag.", Severity.BLOCK, path=registry_rel, metadata={"flag": key}))
        if isinstance(runners, list):
            for runner in runners:
                if not isinstance(runner, dict):
                    continue
                if str(runner.get("status", "disabled")) != "disabled":
                    findings.append(Finding("REMOTE_RUNNER_PROFILE_NOT_DISABLED", "Remote runner profile must remain disabled in Sprint 98.", Severity.BLOCK, path=registry_rel, metadata={"runner_id": runner.get("runner_id")}))
                if bool(runner.get("execution_allowed", False)) or bool(runner.get("network_allowed", False)) or bool(runner.get("external_api_allowed", False)):
                    findings.append(Finding("REMOTE_RUNNER_PROFILE_EXECUTION_BLOCKED", "Remote runner profile attempts to enable execution or remote access.", Severity.BLOCK, path=registry_rel, metadata={"runner_id": runner.get("runner_id")}))
        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        ok = not blocking and summary["schema_valid"] and not any(unsafe_flags.values())
        if ok:
            findings.append(Finding("REMOTE_RUNNER_STATUS_DISABLED_PASS", "Remote runner experiment is present but disabled by default.", Severity.INFO, metadata={"runners_total": summary["runners_total"]}))
        return CommandResult("remote runner status", ok, ExitCode.PASS if ok else _exit_code(blocking), "Remote runner experiment is disabled by default." if ok else "Remote runner registry has unsafe flags.", data={"summary": summary, "registry": registry}, findings=findings)

    def _resolve(self, path: str) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        return candidate.resolve()


class RemoteRunnerStub:
    """Explicit non-executing remote runner boundary.

    This class exists so integrations can depend on a stable remote-runner API
    without enabling remote execution. Any execution attempt is blocked with a
    deterministic finding. Future work must add ADR-approved authentication,
    sandboxing, transport and approval controls before changing this behavior.
    """

    def __init__(self, root: Path, *, options: RemoteRunnerStatusOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.registry = RemoteRunnerRegistry(self.root, options=options)

    def status(self) -> CommandResult:
        policy = PolicyEngine(self.root).evaluate(
            PolicyRequest(
                action="read",
                path=self.registry.options.registry_path,
                dry_run=True,
                tool_id="remote.runner.status",
                subject="remote-runner-experimental-status",
                actor="local-owner",
                metadata={"component": "RemoteRunnerStub", "sprint": "FUNC-SPRINT-98", "remote_runner_enabled": False},
            )
        )
        if not policy.ok:
            return CommandResult("remote runner status", False, policy.exit_code, "Remote runner status blocked by PolicyEngine.", data={"summary": {"policy_engine_used": True, "preliminary": True}}, findings=policy.findings)
        result = self.registry.validate()
        data = dict(result.data or {})
        summary = dict(data.get("summary") or {})
        summary["policy_engine_used"] = True
        summary["policy_engine_replaced"] = False
        data["summary"] = summary
        data["policy"] = policy.data
        return CommandResult(result.command, result.ok, result.exit_code, result.message, data=data, findings=result.findings)

    def execute(self, *, runner_id: str = "experimental-disabled", command: str | None = None) -> CommandResult:
        finding = Finding(
            "REMOTE_RUNNER_EXECUTION_BLOCKED",
            "Remote runner execution is disabled by default and is not implemented in Sprint 98.",
            Severity.BLOCK,
            metadata={"runner_id": runner_id, "command_redacted": bool(command)},
        )
        return CommandResult(
            "remote runner execute",
            False,
            ExitCode.BLOCK,
            "Remote runner execution is blocked.",
            data={
                "summary": {
                    "runner_id": runner_id,
                    "remote_runner_enabled": False,
                    "execution_allowed": False,
                    "remote_execution_used": False,
                    "cloud_control_plane_enabled": False,
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "source_mutations_performed": False,
                    "preliminary": True,
                }
            },
            findings=[finding],
        )


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
