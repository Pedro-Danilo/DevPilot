from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

DEFAULT_SANDBOX_POLICY_PATH = Path(".devpilot/connectors/connector_sandbox_policy.json")
DEFAULT_CONNECTOR_REGISTRY_PATH = Path(".devpilot/connectors/connector_registry.json")
_ALLOWED_MODES = {"validate", "dry-run", "replay"}
_READ_ONLY_SIDE_EFFECTS = {"none", "read", "report"}
_HIGH_RISK = {"high", "critical"}


@dataclass(frozen=True)
class ConnectorSandboxPolicyOptions:
    """Options for local connector sandbox policy validation.

    POST-H-018-A validates policy and connector classification only. It does
    not execute connector calls, replay fixtures, network requests, external
    APIs, connector write, remote execution or plugins.
    """

    policy_path: Path | str = DEFAULT_SANDBOX_POLICY_PATH
    registry_path: Path | str = DEFAULT_CONNECTOR_REGISTRY_PATH


class ConnectorSandboxPolicyValidator:
    """Validate the POST-H-018-A connector sandbox policy.

    The validator cross-checks `.devpilot/connectors/connector_sandbox_policy.json`
    against the existing Connector Registry so every declared connector has a
    deny-write sandbox classification. It is deterministic, read-only and
    local-first; it deliberately does not perform connector calls or replay.
    """

    def __init__(self, root: Path, *, options: ConnectorSandboxPolicyOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ConnectorSandboxPolicyOptions()

    @property
    def policy_path(self) -> Path:
        path = Path(self.options.policy_path)
        return path if path.is_absolute() else self.root / path

    @property
    def registry_path(self) -> Path:
        path = Path(self.options.registry_path)
        return path if path.is_absolute() else self.root / path

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        policy = self._load_json(self.policy_path, findings, artifact="policy")
        registry = self._load_json(self.registry_path, findings, artifact="registry")
        if policy is None or registry is None:
            summary = self._summary_template(policy, registry, findings)
            return CommandResult(
                command="connector sandbox-policy validate",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Connector sandbox policy validation blocked because required JSON artifacts are missing or invalid.",
                data={"summary": summary},
                findings=findings,
            )

        self._validate_defaults(policy, findings)
        self._validate_connector_coverage(policy, registry, findings)

        has_block = any(f.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for f in findings)
        if not has_block:
            findings.append(
                Finding(
                    "CONNECTOR_SANDBOX_POLICY_PASS",
                    "Connector sandbox policy covers all registered connectors and keeps network, external APIs and write denied by default.",
                    Severity.INFO,
                    metadata={
                        "connectors_total": len(policy.get("connectors", [])),
                        "allowed_modes": policy.get("allowed_modes", []),
                    },
                )
            )

        summary = self._summary_template(policy, registry, findings)
        return CommandResult(
            command="connector sandbox-policy validate",
            ok=not has_block,
            exit_code=ExitCode.PASS if not has_block else ExitCode.BLOCK,
            message="Connector sandbox policy validation passed." if not has_block else "Connector sandbox policy validation blocked.",
            data={
                "summary": summary,
                "policy": {
                    "policy_id": policy.get("policy_id"),
                    "status": policy.get("status"),
                    "default_mode": policy.get("default_mode"),
                    "allowed_modes": policy.get("allowed_modes"),
                    "connectors": policy.get("connectors", []),
                },
                "notes": [
                    "POST-H-018-A validates policy/schemas only; sandbox runner, replay, RBAC binding and quality gate remain later micro-sprints.",
                    "A Connector Registry entry is not permission to execute write operations.",
                ],
            },
            findings=findings,
        )

    def validate_payloads(self, policy: dict[str, Any], registry: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        self._validate_defaults(policy, findings)
        self._validate_connector_coverage(policy, registry, findings)
        return findings

    def _load_json(self, path: Path, findings: list[Finding], *, artifact: str) -> dict[str, Any] | None:
        rel = self._rel(path)
        if not path.exists():
            findings.append(Finding(f"CONNECTOR_SANDBOX_{artifact.upper()}_MISSING", f"Missing connector sandbox {artifact}: {rel}", Severity.BLOCK, path=rel))
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding(f"CONNECTOR_SANDBOX_{artifact.upper()}_INVALID_JSON", str(exc), Severity.ERROR, path=rel))
            return None
        if not isinstance(payload, dict):
            findings.append(Finding(f"CONNECTOR_SANDBOX_{artifact.upper()}_NOT_OBJECT", f"Connector sandbox {artifact} must be a JSON object.", Severity.BLOCK, path=rel))
            return None
        return payload

    def _validate_defaults(self, policy: dict[str, Any], findings: list[Finding]) -> None:
        expected_false = {
            "network_allowed_by_default": "CONNECTOR_SANDBOX_NETWORK_DEFAULT_BLOCKED",
            "external_api_allowed_by_default": "CONNECTOR_SANDBOX_EXTERNAL_API_DEFAULT_BLOCKED",
            "mutation_allowed_by_default": "CONNECTOR_SANDBOX_MUTATION_DEFAULT_BLOCKED",
            "connector_write_enabled": "CONNECTOR_SANDBOX_WRITE_ENABLED_BLOCKED",
        }
        for field, finding_id in expected_false.items():
            if policy.get(field) is not False:
                findings.append(Finding(finding_id, f"{field} must be false in connector sandbox policy.", Severity.BLOCK, path=self._rel(self.policy_path)))
        if policy.get("default_mode") != "deny-write":
            findings.append(Finding("CONNECTOR_SANDBOX_DEFAULT_MODE_BLOCKED", "default_mode must be deny-write.", Severity.BLOCK, path=self._rel(self.policy_path)))
        modes = set(policy.get("allowed_modes") or [])
        if not modes or not modes.issubset(_ALLOWED_MODES) or "write" in modes or "execute" in modes:
            findings.append(Finding("CONNECTOR_SANDBOX_ALLOWED_MODES_BLOCKED", "Only validate/dry-run/replay modes are allowed in POST-H-018-A.", Severity.BLOCK, path=self._rel(self.policy_path), metadata={"allowed_modes": sorted(modes)}))
        safety = policy.get("safety") if isinstance(policy.get("safety"), dict) else {}
        for flag in ("network_used", "external_api_used", "mutations_performed", "source_mutations_performed", "connector_write_used", "remote_execution_used", "plugin_execution_used", "secrets_included"):
            if safety.get(flag) is not False:
                findings.append(Finding("CONNECTOR_SANDBOX_SAFETY_FLAG_BLOCKED", f"safety.{flag} must remain false.", Severity.BLOCK, path=self._rel(self.policy_path), metadata={"flag": flag}))

    def _validate_connector_coverage(self, policy: dict[str, Any], registry: dict[str, Any], findings: list[Finding]) -> None:
        registry_connectors = registry.get("connectors") if isinstance(registry, dict) else []
        policy_connectors = policy.get("connectors") if isinstance(policy, dict) else []
        if not isinstance(registry_connectors, list):
            registry_connectors = []
        if not isinstance(policy_connectors, list):
            policy_connectors = []

        registry_ids = {str(item.get("connector_id")) for item in registry_connectors if isinstance(item, dict) and item.get("connector_id")}
        policy_by_id = {str(item.get("connector_id")): item for item in policy_connectors if isinstance(item, dict) and item.get("connector_id")}
        missing = sorted(registry_ids - set(policy_by_id))
        extra = sorted(set(policy_by_id) - registry_ids)
        if missing:
            findings.append(Finding("CONNECTOR_SANDBOX_POLICY_COVERAGE_MISSING", "Every registered connector must have a sandbox policy entry.", Severity.BLOCK, path=self._rel(self.policy_path), metadata={"connectors": missing, "total": len(missing)}))
        if extra:
            findings.append(Finding("CONNECTOR_SANDBOX_POLICY_EXTRA_CONNECTOR", "Sandbox policy must not declare connectors absent from Connector Registry.", Severity.BLOCK, path=self._rel(self.policy_path), metadata={"connectors": extra, "total": len(extra)}))

        for connector_id, connector in sorted(policy_by_id.items()):
            self._validate_connector(connector_id, connector, findings)

    def _validate_connector(self, connector_id: str, connector: dict[str, Any], findings: list[Finding]) -> None:
        for field in ("side_effect", "risk_level", "data_sensitivity"):
            if not connector.get(field):
                findings.append(Finding("CONNECTOR_SANDBOX_CONNECTOR_CLASSIFICATION_MISSING", f"Connector {connector_id} is missing {field}.", Severity.BLOCK, path=self._rel(self.policy_path), metadata={"connector_id": connector_id, "field": field}))
        if connector.get("network_allowed") is not False:
            findings.append(Finding("CONNECTOR_SANDBOX_CONNECTOR_NETWORK_BLOCKED", "No connector may allow network in POST-H-018-A.", Severity.BLOCK, path=self._rel(self.policy_path), metadata={"connector_id": connector_id}))
        if connector.get("external_api_allowed") is not False:
            findings.append(Finding("CONNECTOR_SANDBOX_CONNECTOR_EXTERNAL_API_BLOCKED", "No connector may allow external APIs in POST-H-018-A.", Severity.BLOCK, path=self._rel(self.policy_path), metadata={"connector_id": connector_id}))
        for flag in ("mutations_allowed", "write_allowed", "execution_allowed"):
            if connector.get(flag) is not False:
                findings.append(Finding("CONNECTOR_SANDBOX_CONNECTOR_WRITE_BLOCKED", f"Connector {connector_id} must keep {flag}=false.", Severity.BLOCK, path=self._rel(self.policy_path), metadata={"connector_id": connector_id, "flag": flag}))
        modes = set(connector.get("allowed_modes") or [])
        if not modes or not modes.issubset(_ALLOWED_MODES):
            findings.append(Finding("CONNECTOR_SANDBOX_CONNECTOR_MODE_BLOCKED", "Connector allowed_modes must be validate/dry-run/replay only.", Severity.BLOCK, path=self._rel(self.policy_path), metadata={"connector_id": connector_id, "allowed_modes": sorted(modes)}))
        side_effect = str(connector.get("side_effect"))
        if side_effect not in _READ_ONLY_SIDE_EFFECTS and connector.get("approval_required") is not True:
            findings.append(Finding("CONNECTOR_SANDBOX_APPROVAL_REQUIRED", "Side-effecting connector classifications must require approval even though write remains blocked.", Severity.BLOCK, path=self._rel(self.policy_path), metadata={"connector_id": connector_id, "side_effect": side_effect}))
        if str(connector.get("risk_level")) in _HIGH_RISK and connector.get("rbac_required") is not True:
            findings.append(Finding("CONNECTOR_SANDBOX_RBAC_REQUIRED", "High/critical risk connectors must require RBAC binding.", Severity.BLOCK, path=self._rel(self.policy_path), metadata={"connector_id": connector_id, "risk_level": connector.get("risk_level")}))
        if not connector.get("policy_rules"):
            findings.append(Finding("CONNECTOR_SANDBOX_POLICY_RULES_MISSING", "Every connector sandbox entry must declare policy_rules.", Severity.BLOCK, path=self._rel(self.policy_path), metadata={"connector_id": connector_id}))

    def _summary_template(self, policy: dict[str, Any] | None, registry: dict[str, Any] | None, findings: list[Finding]) -> dict[str, Any]:
        policy_connectors = policy.get("connectors") if isinstance(policy, dict) else []
        registry_connectors = registry.get("connectors") if isinstance(registry, dict) else []
        if not isinstance(policy_connectors, list):
            policy_connectors = []
        if not isinstance(registry_connectors, list):
            registry_connectors = []
        risk_counts = Counter(str(item.get("risk_level")) for item in policy_connectors if isinstance(item, dict) and item.get("risk_level"))
        mode_counts = Counter(mode for item in policy_connectors if isinstance(item, dict) for mode in item.get("allowed_modes", []) if isinstance(mode, str))
        blocking = sum(1 for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL})
        return {
            "created_by": "POST-H-018-A",
            "status": "implemented-initial",
            "preliminary": True,
            "policy_path": self._rel(self.policy_path),
            "registry_path": self._rel(self.registry_path),
            "policy_id": policy.get("policy_id") if isinstance(policy, dict) else None,
            "default_mode": policy.get("default_mode") if isinstance(policy, dict) else None,
            "connectors_total": len(policy_connectors),
            "registry_connectors_total": len(registry_connectors),
            "risk_counts": dict(risk_counts),
            "mode_counts": dict(mode_counts),
            "network_allowed_by_default": policy.get("network_allowed_by_default") if isinstance(policy, dict) else None,
            "external_api_allowed_by_default": policy.get("external_api_allowed_by_default") if isinstance(policy, dict) else None,
            "mutation_allowed_by_default": policy.get("mutation_allowed_by_default") if isinstance(policy, dict) else None,
            "connector_write_enabled": policy.get("connector_write_enabled") if isinstance(policy, dict) else None,
            "policy_coverage_complete": len(policy_connectors) == len(registry_connectors) and blocking == 0,
            "blocking_findings_total": blocking,
            "findings_total": len(findings),
            "local_first": True,
            "dry_run": True,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "connector_write_used": False,
            "remote_execution_used": False,
            "plugin_execution_used": False,
            "secrets_included": False,
        }

    def _rel(self, path: Path | str) -> str:
        p = Path(path)
        try:
            return p.resolve().relative_to(self.root).as_posix()
        except Exception:
            return p.as_posix()
