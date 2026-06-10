from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas.validator import SchemaValidator


MIASI_CONTRACTS = {
    "agents": ("MiasiAgentRegistry", ".devpilot/miasi/agent_registry.json"),
    "tools": ("MiasiToolRegistry", ".devpilot/miasi/tool_registry.json"),
    "policy": ("MiasiPolicyMatrix", ".devpilot/miasi/policy_matrix.json"),
}


class BuiltinContractValidator:
    """Validate DevPilot built-in operational contracts.

    FUNC-SPRINT-23 adds structural contract validation for MIASI registries,
    workspace metadata, provider metadata and functional sprint manifests. This
    class orchestrates existing SchemaValidator checks without replacing the
    dedicated business validators such as MiasiRegistryValidator, PolicyEngine or
    readiness gates.

    YAML support is intentionally narrow and dependency-free. It supports only
    the `.devpilot/project.yaml` and `.devpilot/providers.yaml.example` shapes
    DevPilot already owns. If future configuration needs full YAML semantics,
    a new ADR must justify PyYAML or another parser.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.validator = SchemaValidator(self.root)

    def validate_miasi(self, *, scope: str = "all") -> CommandResult:
        keys = list(MIASI_CONTRACTS) if scope == "all" else [scope]
        invalid = [key for key in keys if key not in MIASI_CONTRACTS]
        if invalid:
            return CommandResult(
                command="schema validate-miasi",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Unknown MIASI validation scope.",
                data={"summary": {"scope": scope, "valid_scopes": ["all", *MIASI_CONTRACTS.keys()]}},
                findings=[
                    Finding(
                        id="SCHEMA_BUILTIN_SCOPE_INVALID",
                        message=f"Unsupported MIASI scope: {scope}",
                        severity=Severity.BLOCK,
                        metadata={"scope": scope},
                    )
                ],
            )
        results = [self.validator.validate(schema=MIASI_CONTRACTS[key][0], instance=MIASI_CONTRACTS[key][1]) for key in keys]
        return self._combine(
            command="schema validate-miasi",
            message_ok="MIASI registries passed structural schema validation.",
            message_block="MIASI registries failed structural schema validation.",
            results=results,
            contract_group="MIASI",
            subject=".devpilot/miasi",
            extra_summary={"scope": scope, "contracts_total": len(results)},
        )

    def validate_workspace(self, *, path: str | Path = ".devpilot/project.yaml") -> CommandResult:
        target = self._workspace_path(path)
        try:
            payload = parse_workspace_project_yaml(target)
        except Exception as exc:
            return self._parse_error("schema validate-workspace", target, "SCHEMA_WORKSPACE_PARSE_ERROR", exc)
        result = self.validator.validate_payload(schema="WorkspaceProject", payload=payload, instance_label=self._relative(target))
        return self._rename(
            result,
            command="schema validate-workspace",
            subject=self._relative(target),
            extra={"source_format": "yaml", "parser": "dependency-free-devpilot-narrow-yaml"},
        )

    def validate_providers(self, *, path: str | Path = ".devpilot/providers.yaml.example") -> CommandResult:
        target = self._workspace_path(path)
        try:
            payload = parse_provider_config_yaml(target)
        except Exception as exc:
            return self._parse_error("schema validate-providers", target, "SCHEMA_PROVIDER_PARSE_ERROR", exc)
        result = self.validator.validate_payload(schema="ProviderConfig", payload=payload, instance_label=self._relative(target))
        return self._rename(
            result,
            command="schema validate-providers",
            subject=self._relative(target),
            extra={"source_format": "yaml", "parser": "dependency-free-devpilot-narrow-yaml"},
        )

    def validate_manifest(self, manifest_path: str | Path) -> CommandResult:
        target = self._workspace_path(manifest_path)
        result = self.validator.validate(schema="FunctionalSprintManifest", instance=target)
        return self._rename(result, command="schema validate-manifest", subject=self._relative(target), extra={"contract": "FunctionalSprintManifest"})

    def _combine(
        self,
        *,
        command: str,
        message_ok: str,
        message_block: str,
        results: list[CommandResult],
        contract_group: str,
        subject: str,
        extra_summary: dict[str, Any] | None = None,
    ) -> CommandResult:
        ok = all(result.ok for result in results)
        findings: list[Finding] = []
        details: list[dict[str, Any]] = []
        for result in results:
            details.append(result.to_dict())
            for finding in result.findings:
                metadata = dict(finding.metadata or {})
                metadata.setdefault("source_command", result.command)
                findings.append(
                    Finding(
                        id=finding.id,
                        message=finding.message,
                        severity=finding.severity,
                        path=finding.path,
                        metadata=metadata,
                    )
                )
        summary = {
            "contract_group": contract_group,
            "subject": subject,
            "validations_total": len(results),
            "validations_passed": sum(1 for result in results if result.ok),
            "validations_failed": sum(1 for result in results if not result.ok),
            "preliminary": True,
        }
        summary.update(extra_summary or {})
        return CommandResult(
            command=command,
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message=message_ok if ok else message_block,
            data={
                "summary": summary,
                "validations": details,
                "notes": [
                    "FUNC-SPRINT-23 performs structural schema validation only.",
                    "Business rules remain in dedicated validators such as miasi validate, readiness-check and policy check.",
                ],
            },
            findings=findings,
        )

    def _rename(self, result: CommandResult, *, command: str, subject: str, extra: dict[str, Any] | None = None) -> CommandResult:
        data = dict(result.data or {})
        summary = dict(data.get("summary") or {})
        summary.update(extra or {})
        summary.setdefault("subject", subject)
        summary.setdefault("preliminary", True)
        data["summary"] = summary
        data.setdefault(
            "notes",
            [
                "FUNC-SPRINT-23 validates structural contracts only.",
                "Semantic gates remain in dedicated validators.",
            ],
        )
        return CommandResult(
            command=command,
            ok=result.ok,
            exit_code=result.exit_code,
            message=result.message,
            data=data,
            findings=result.findings,
        )

    def _parse_error(self, command: str, path: Path, finding_id: str, exc: Exception) -> CommandResult:
        return CommandResult(
            command=command,
            ok=False,
            exit_code=ExitCode.ERROR,
            message="Contract source could not be parsed.",
            data={"summary": {"path": self._relative(path), "preliminary": True}},
            findings=[Finding(id=finding_id, message=str(exc), severity=Severity.ERROR, path=self._relative(path))],
        )

    def _workspace_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        return candidate if candidate.is_absolute() else self.root / candidate

    def _relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return str(path).replace("\\", "/")


def parse_workspace_project_yaml(path: Path) -> dict[str, Any]:
    """Parse DevPilot's deterministic `.devpilot/project.yaml` shape.

    This parser is intentionally not a general YAML parser. It supports the
    sections DevPilot owns: project, standards, miasi, paths and runtime.
    """

    if not path.is_file():
        raise FileNotFoundError(f"Workspace project file does not exist: {path}")
    payload: dict[str, Any] = {}
    section: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        stripped = raw_line.strip()
        if not raw_line.startswith(" ") and stripped.endswith(":"):
            section = stripped[:-1]
            payload.setdefault(section, [] if section == "standards" else {})
            continue
        if not raw_line.startswith(" ") and ":" in stripped:
            key, value = stripped.split(":", 1)
            payload[key.strip()] = _parse_scalar(value.strip())
            section = None
            continue
        if section == "standards" and stripped.startswith("-"):
            payload.setdefault("standards", []).append(_parse_scalar(stripped[1:].strip()))
            continue
        if section in {"project", "miasi", "paths", "runtime"} and raw_line.startswith("  ") and ":" in stripped:
            key, value = stripped.split(":", 1)
            payload.setdefault(section, {})[key.strip()] = _parse_scalar(value.strip())
    return payload


def parse_provider_config_yaml(path: Path) -> dict[str, Any]:
    """Parse DevPilot's deterministic provider metadata YAML shape.

    The parser preserves unknown keys so `provider_config.schema.json` can block
    unsafe fields such as raw `api_key` entries. It never reads environment
    variables and never contacts provider endpoints.
    """

    if not path.is_file():
        raise FileNotFoundError(f"Provider config file does not exist: {path}")
    payload: dict[str, Any] = {}
    providers: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_list_key: str | None = None
    top_section: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        stripped = raw_line.strip()
        if not raw_line.startswith(" ") and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            top_section = key if value == "" else None
            if value:
                payload[key] = _parse_scalar(value)
            elif key == "providers":
                payload["providers"] = providers
            else:
                payload.setdefault(key, {})
            continue
        if top_section == "providers" and raw_line.startswith("  - "):
            if current:
                providers.append(current)
            current = {}
            current_list_key = None
            remainder = raw_line.strip()[2:].strip()
            if remainder and ":" in remainder:
                key, value = remainder.split(":", 1)
                current[key.strip()] = _parse_scalar(value.strip())
            continue
        if current is None:
            continue
        if current_list_key and raw_line.startswith("      -"):
            current.setdefault(current_list_key, []).append(_parse_scalar(stripped[1:].strip()))
            continue
        if raw_line.startswith("    ") and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_list_key = key if value == "" else None
            if value == "":
                current.setdefault(key, [])
            else:
                current[key] = _parse_scalar(value)
    if current:
        providers.append(current)
    payload.setdefault("providers", providers)
    return payload


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value
