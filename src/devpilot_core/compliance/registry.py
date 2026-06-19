from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PathGuard
from devpilot_core.policy.decisions import PolicyEffect
from devpilot_core.schemas import SchemaRegistry, SchemaValidator

_DEFAULT_REGISTRY = Path(".devpilot/compliance/packs.json")
_DEFAULT_SCHEMA = Path("docs/schemas/compliance_pack.schema.json")
_ALLOWED_RUNNERS = {
    "schema.registry.list",
    "validation.gateway.all",
    "miasi.validate.all",
    "readiness.strict",
    "standards.status",
}
_FORBIDDEN_TOKENS = {
    "shell",
    "subprocess",
    "remote",
    "network",
    "external-api",
    "write-file",
    "delete",
    "deploy",
    "publish",
    "git.push",
}


@dataclass(frozen=True)
class ComplianceRegistryOptions:
    """Options for local compliance pack registry inspection."""

    registry_path: str = str(_DEFAULT_REGISTRY)
    schema_path: str = str(_DEFAULT_SCHEMA)


class CompliancePackRegistry:
    """Validate and list local declarative compliance/policy packs.

    FUNC-SPRINT-97 keeps compliance packs as metadata-only contracts. Packs are
    declarative groupings of existing DevPilot gates, policy rules, schemas and
    report expectations. They never execute arbitrary commands, shell snippets,
    remote runners, cloud calls or external APIs.
    """

    def __init__(self, root: Path, *, options: ComplianceRegistryOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ComplianceRegistryOptions()
        self.path_guard = PathGuard(self.root)

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        summary: dict[str, Any] = self._base_summary()
        registry_result = self._load_registry()
        if isinstance(registry_result, CommandResult):
            return registry_result
        payload = registry_result

        schema_result = SchemaValidator(self.root).validate(schema=self.options.schema_path, instance=self.options.registry_path)
        summary["schema_valid"] = schema_result.ok
        if not schema_result.ok:
            findings.extend(schema_result.findings)

        packs = payload.get("packs", []) if isinstance(payload, dict) else []
        summary["packs_total"] = len(packs) if isinstance(packs, list) else 0
        pack_ids: list[str] = []
        policy_ids = self._miasi_policy_ids()
        schema_ids = self._schema_ids()
        declared_runners: list[str] = []
        policy_engine_required = bool(payload.get("security", {}).get("policy_engine_required", False)) if isinstance(payload, dict) else False
        summary["policy_engine_required"] = policy_engine_required
        if not policy_engine_required:
            findings.append(Finding("COMPLIANCE_POLICY_ENGINE_REQUIRED_BLOCK", "Compliance packs must require PolicyEngine instead of replacing it.", Severity.BLOCK, path=self.options.registry_path))

        if not isinstance(packs, list) or not packs:
            findings.append(Finding("COMPLIANCE_PACKS_EMPTY", "Compliance Pack Registry must declare at least one pack.", Severity.BLOCK, path=self.options.registry_path))
        else:
            for pack in packs:
                if not isinstance(pack, dict):
                    findings.append(Finding("COMPLIANCE_PACK_INVALID", "Compliance pack entry must be an object.", Severity.BLOCK, path=self.options.registry_path))
                    continue
                pack_id = str(pack.get("pack_id", "")).strip()
                pack_ids.append(pack_id)
                if not pack_id:
                    findings.append(Finding("COMPLIANCE_PACK_ID_MISSING", "Compliance pack entry is missing pack_id.", Severity.BLOCK, path=self.options.registry_path))
                if bool(pack.get("execution_allowed", False)):
                    findings.append(Finding("COMPLIANCE_PACK_EXECUTION_BLOCKED", "Compliance packs may not enable arbitrary execution.", Severity.BLOCK, path=self.options.registry_path, metadata={"pack_id": pack_id}))
                for item in pack.get("checks", []) or []:
                    runner = str(item.get("runner", "")).strip()
                    declared_runners.append(runner)
                    if runner not in _ALLOWED_RUNNERS:
                        findings.append(Finding("COMPLIANCE_PACK_RUNNER_UNDECLARED_BLOCK", "Compliance pack check uses an undeclared or unsupported runner.", Severity.BLOCK, path=self.options.registry_path, metadata={"pack_id": pack_id, "runner": runner}))
                    token_blob = " ".join(str(item.get(k, "")) for k in ("runner", "command", "action", "tool_id")).lower()
                    if any(token in token_blob for token in _FORBIDDEN_TOKENS):
                        findings.append(Finding("COMPLIANCE_PACK_FORBIDDEN_ACTION_BLOCK", "Compliance pack attempted to declare a forbidden action.", Severity.BLOCK, path=self.options.registry_path, metadata={"pack_id": pack_id, "runner": runner}))
                missing_policies = sorted(set(pack.get("policy_rule_ids", []) or []) - policy_ids)
                missing_schemas = sorted(set(pack.get("schema_ids", []) or []) - schema_ids)
                for policy_id in missing_policies:
                    findings.append(Finding("COMPLIANCE_POLICY_RULE_MISSING", "Compliance pack references a missing MIASI policy rule.", Severity.BLOCK, path=self.options.registry_path, metadata={"pack_id": pack_id, "policy_rule_id": policy_id}))
                for schema_id in missing_schemas:
                    findings.append(Finding("COMPLIANCE_SCHEMA_MISSING", "Compliance pack references a missing schema catalog id.", Severity.BLOCK, path=self.options.registry_path, metadata={"pack_id": pack_id, "schema_id": schema_id}))

        duplicates = sorted({pack_id for pack_id in pack_ids if pack_id and pack_ids.count(pack_id) > 1})
        for pack_id in duplicates:
            findings.append(Finding("COMPLIANCE_PACK_DUPLICATE_ID", "Compliance Pack Registry contains duplicate pack ids.", Severity.BLOCK, path=self.options.registry_path, metadata={"pack_id": pack_id}))

        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        summary.update({
            "pack_ids": sorted(set(pack_ids)),
            "declared_runners": sorted(set(declared_runners)),
            "allowed_runners": sorted(_ALLOWED_RUNNERS),
            "declared_checks_only": not any(f.id in {"COMPLIANCE_PACK_RUNNER_UNDECLARED_BLOCK", "COMPLIANCE_PACK_FORBIDDEN_ACTION_BLOCK"} for f in findings),
            "blocking_findings_total": len(blocking),
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        })
        ok = not blocking
        return CommandResult(
            command="compliance validate",
            ok=ok,
            exit_code=ExitCode.PASS if ok else _exit_code(blocking),
            message="Compliance Pack Registry validation passed." if ok else "Compliance Pack Registry validation failed or blocked.",
            data={"summary": summary, "packs": packs if isinstance(packs, list) else []},
            findings=findings or [Finding("COMPLIANCE_REGISTRY_PASS", "Compliance Pack Registry is valid and declarative.", Severity.INFO, metadata=summary)],
        )

    def list(self) -> CommandResult:
        validation = self.validate()
        packs = validation.data.get("packs", []) if isinstance(validation.data, dict) else []
        public = [
            {
                "pack_id": pack.get("pack_id"),
                "title": pack.get("title"),
                "status": pack.get("status"),
                "profile": pack.get("profile"),
                "checks_total": len(pack.get("checks", []) or []),
                "policy_rules_total": len(pack.get("policy_rule_ids", []) or []),
                "schemas_total": len(pack.get("schema_ids", []) or []),
            }
            for pack in packs
            if isinstance(pack, dict)
        ]
        summary = dict(validation.data.get("summary", {}) if isinstance(validation.data, dict) else {})
        summary.update({"packs_total": len(public), "registry_valid": validation.ok})
        return CommandResult(
            command="compliance list",
            ok=validation.ok,
            exit_code=validation.exit_code,
            message="Compliance packs listed." if validation.ok else "Compliance packs could not be listed because registry validation failed.",
            data={"summary": summary, "packs": public},
            findings=validation.findings if not validation.ok else [Finding("COMPLIANCE_PACKS_LISTED", "Compliance packs listed from validated registry.", Severity.INFO, metadata={"packs_total": len(public)})],
        )

    def get_pack(self, pack_id: str) -> dict[str, Any] | None:
        payload = self._load_registry()
        if isinstance(payload, CommandResult):
            return None
        packs = payload.get("packs", []) if isinstance(payload, dict) else []
        for pack in packs:
            if isinstance(pack, dict) and str(pack.get("pack_id")) == pack_id:
                return pack
        return None

    def _base_summary(self) -> dict[str, Any]:
        registry_path = Path(self.options.registry_path)
        registry_abs = self.root / registry_path
        decision = self.path_guard.evaluate(registry_path.as_posix(), action="read")
        return {
            "registry_path": registry_path.as_posix(),
            "schema_path": str(self.options.schema_path).replace("\\", "/"),
            "registry_exists": registry_abs.exists(),
            "path_allowed": decision.effect != PolicyEffect.BLOCK,
            "schema_valid": False,
            "local_first": True,
            "cloud_used": False,
            "network_used": False,
            "external_api_used": False,
            "preliminary": True,
        }

    def _load_registry(self) -> dict[str, Any] | CommandResult:
        summary = self._base_summary()
        if not summary["path_allowed"]:
            finding = Finding("COMPLIANCE_REGISTRY_PATH_BLOCKED", "Compliance Pack Registry path is outside the governed workspace.", Severity.BLOCK, path=self.options.registry_path)
            return CommandResult("compliance validate", False, ExitCode.BLOCK, "Compliance registry path blocked.", data={"summary": summary}, findings=[finding])
        path = self.root / self.options.registry_path
        if not path.exists():
            finding = Finding("COMPLIANCE_REGISTRY_MISSING", "Compliance Pack Registry does not exist.", Severity.BLOCK, path=self.options.registry_path)
            return CommandResult("compliance validate", False, ExitCode.BLOCK, "Compliance Pack Registry is missing.", data={"summary": summary}, findings=[finding])
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            finding = Finding("COMPLIANCE_REGISTRY_JSON_INVALID", "Compliance Pack Registry is not valid JSON.", Severity.ERROR, path=self.options.registry_path, metadata={"error": str(exc)})
            return CommandResult("compliance validate", False, ExitCode.ERROR, "Compliance Pack Registry JSON is invalid.", data={"summary": summary}, findings=[finding])

    def _miasi_policy_ids(self) -> set[str]:
        path = self.root / ".devpilot/miasi/policy_matrix.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return set()
        return {str(item.get("rule_id")) for item in payload.get("rules", []) if isinstance(item, dict)}

    def _schema_ids(self) -> set[str]:
        try:
            specs = SchemaRegistry(self.root).load_specs()
        except Exception:
            return set()
        return {spec.schema_id for spec in specs}


def _exit_code(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS
