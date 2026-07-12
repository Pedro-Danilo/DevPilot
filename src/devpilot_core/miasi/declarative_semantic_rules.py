from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devpilot_core.miasi.semantic_models import SemanticFinding
from devpilot_core.miasi.semantic_rules import SemanticSeverity
from devpilot_core.schemas import SchemaValidator

MIASI_SEMANTIC_RULES_SCHEMA_ID = "SCHEMA-DEVPL-MIASI-SEMANTIC-RULES-V1"
MIASI_SEMANTIC_RULES_CONTRACT = "MiasiSemanticRules"
DEFAULT_MIASI_SEMANTIC_RULES_PATH = Path(".devpilot") / "miasi" / "semantic_rules.json"
POST_H_033_D_CREATED_BY = "POST-H-033-D"

FALLBACK_SENSITIVE_SIDE_EFFECTS = frozenset({"controlled_write", "controlled_execution", "network_cost", "optional_write"})
FALLBACK_EXECUTION_SIDE_EFFECTS = frozenset({"controlled_execution", "network_cost"})
FALLBACK_SAFE_GATED_CONTROLLED_WRITE_TOKENS = (
    "sandbox",
    "dry_run",
    "dry-run",
    "rollback",
    "registry",
    "local",
    "pathguard",
    "secretguard",
    "policyengine",
)
FALLBACK_NO_GO_ACTION_MARKERS: dict[str, tuple[str, ...]] = {
    "remote": ("execute_remote", "cloud_control_plane", "remote_authentication"),
    "plugin": ("execute_plugin_code", "plugin_execute", "execute_plugin"),
    "connector": ("connector_call_execute_mode", "connector_write", "write_connector"),
}
FALLBACK_APPROVAL_GATE_TOKENS = ("approval", "approvalpolicychecker", "approvalservice", "human", "actor")
FALLBACK_RBAC_GATE_TOKENS = ("rbac", "identityregistry", "role", "actor")
FALLBACK_SECRET_GUARD_TOKENS = ("secretguard", "secret", "redacted", "no raw secrets", "norawsecrets")
FALLBACK_NETWORK_GUARD_TOKENS = ("costguard", "noexternalapi", "no external api", "nonetwork", "no network", "localhostonly")
FALLBACK_LOCAL_GUARD_TOKENS = ("pathguard", "policyengine", "sandbox", "dry_run", "dry-run", "local", "checksum", "rollback", "registry")
FALLBACK_SENSITIVE_NAME_MARKERS = ("secret", "model", "security", "connector", "plugin", "remote", "audit", "compliance", "enterprise", "release")
FALLBACK_NO_GO_FUTURE_SANDBOX_TOKENS = ("futureadr", "future sandbox", "sandboxfuture", "sandbox", "dry_run", "dry-run", "metadata")
FALLBACK_NO_GO_TOOL_MARKERS: dict[str, tuple[str, ...]] = {
    "remote": ("execute", "runner", "auth", "cloud_control"),
    "plugin": ("execute", "loader", "code"),
    "connector": ("write", "execute", "call_execute"),
}
FALLBACK_UNSAFE_EVAL_RUNTIME_FLAGS = ("network_used", "external_api_used", "llm_judge_used")


@dataclass(frozen=True)
class RequiredEvalFixtureSpec:
    path: Path
    suite_id: str
    required_markers: tuple[str, ...]
    missing_severity: SemanticSeverity = SemanticSeverity.WARNING
    invalid_json_severity: SemanticSeverity = SemanticSeverity.BLOCK
    suite_mismatch_severity: SemanticSeverity = SemanticSeverity.BLOCK
    cases_missing_severity: SemanticSeverity = SemanticSeverity.BLOCK
    marker_missing_severity: SemanticSeverity = SemanticSeverity.BLOCK
    unsafe_runtime_flag_severity: SemanticSeverity = SemanticSeverity.BLOCK

    def as_legacy_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "suite_id": self.suite_id,
            "required_markers": self.required_markers,
        }


FALLBACK_REQUIRED_EVAL_FIXTURES: tuple[RequiredEvalFixtureSpec, ...] = (
    RequiredEvalFixtureSpec(
        path=Path("evals") / "fixtures" / "red_team_agentic_eval_cases.json",
        suite_id="red-team",
        required_markers=("prompt-injection", "secret", "connector"),
    ),
    RequiredEvalFixtureSpec(
        path=Path("evals") / "fixtures" / "advanced_agentic_eval_cases.json",
        suite_id="advanced-agentic",
        required_markers=("rag", "mcp", "multiagent"),
    ),
    RequiredEvalFixtureSpec(
        path=Path("evals") / "fixtures" / "plugin_ecosystem_eval_cases.json",
        suite_id="plugin-ecosystem",
        required_markers=("plugin",),
    ),
    RequiredEvalFixtureSpec(
        path=Path("evals") / "fixtures" / "identity_rbac_eval_cases.json",
        suite_id="identity-rbac",
        required_markers=("rbac",),
    ),
    RequiredEvalFixtureSpec(
        path=Path("evals") / "fixtures" / "remote_enterprise_eval_cases.json",
        suite_id="remote-enterprise",
        required_markers=("remote",),
    ),
)


@dataclass(frozen=True)
class MiasiSemanticRulesCatalog:
    rule_source: str
    catalog_version: str
    registry_valid: bool
    fallback_active: bool
    findings: tuple[SemanticFinding, ...] = field(default_factory=tuple)
    sensitive_side_effects: frozenset[str] = FALLBACK_SENSITIVE_SIDE_EFFECTS
    execution_side_effects: frozenset[str] = FALLBACK_EXECUTION_SIDE_EFFECTS
    safe_gated_controlled_write_tokens: tuple[str, ...] = FALLBACK_SAFE_GATED_CONTROLLED_WRITE_TOKENS
    no_go_action_markers: dict[str, tuple[str, ...]] = field(default_factory=lambda: dict(FALLBACK_NO_GO_ACTION_MARKERS))
    approval_gate_tokens: tuple[str, ...] = FALLBACK_APPROVAL_GATE_TOKENS
    rbac_gate_tokens: tuple[str, ...] = FALLBACK_RBAC_GATE_TOKENS
    secret_guard_tokens: tuple[str, ...] = FALLBACK_SECRET_GUARD_TOKENS
    network_guard_tokens: tuple[str, ...] = FALLBACK_NETWORK_GUARD_TOKENS
    local_guard_tokens: tuple[str, ...] = FALLBACK_LOCAL_GUARD_TOKENS
    sensitive_name_markers: tuple[str, ...] = FALLBACK_SENSITIVE_NAME_MARKERS
    no_go_future_sandbox_tokens: tuple[str, ...] = FALLBACK_NO_GO_FUTURE_SANDBOX_TOKENS
    no_go_tool_markers: dict[str, tuple[str, ...]] = field(default_factory=lambda: dict(FALLBACK_NO_GO_TOOL_MARKERS))
    required_eval_fixtures: tuple[RequiredEvalFixtureSpec, ...] = FALLBACK_REQUIRED_EVAL_FIXTURES
    unsafe_eval_runtime_flags: tuple[str, ...] = FALLBACK_UNSAFE_EVAL_RUNTIME_FLAGS

    def metadata(self) -> dict[str, Any]:
        return {
            "rule_source": self.rule_source,
            "catalog_version": self.catalog_version,
            "registry_valid": self.registry_valid,
            "fallback_active": self.fallback_active,
        }

    def summary(self) -> dict[str, Any]:
        return {
            **self.metadata(),
            "sensitive_side_effects_total": len(self.sensitive_side_effects),
            "execution_side_effects_total": len(self.execution_side_effects),
            "no_go_domains": sorted(self.no_go_action_markers),
            "required_eval_fixtures_total": len(self.required_eval_fixtures),
        }


def load_miasi_semantic_rules(
    root: Path,
    *,
    catalog_path: Path = DEFAULT_MIASI_SEMANTIC_RULES_PATH,
    emit_fallback_finding: bool = False,
) -> MiasiSemanticRulesCatalog:
    root = Path(root).resolve()
    path = root / catalog_path
    if not path.is_file():
        finding = _catalog_finding(
            finding_id="MIASI_SEMANTIC_RULES_REGISTRY_MISSING_FALLBACK_ACTIVE",
            severity=SemanticSeverity.WARNING,
            message="MIASI semantic rules registry is missing; deterministic Python fallback remains active.",
            metadata={"expected_path": catalog_path.as_posix()},
        )
        return _fallback_catalog(findings=(finding,) if emit_fallback_finding else ())
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        finding = _catalog_finding(
            finding_id="MIASI_SEMANTIC_RULES_REGISTRY_INVALID_JSON_BLOCKED",
            severity=SemanticSeverity.BLOCK,
            message="MIASI semantic rules registry contains invalid JSON; fallback is active but semantic validation must block.",
            metadata={"path": catalog_path.as_posix(), "error": str(exc)},
        )
        return _fallback_catalog(findings=(finding,))
    schema_result = SchemaValidator(root).validate_payload(
        schema=MIASI_SEMANTIC_RULES_CONTRACT,
        payload=payload,
        instance_label=catalog_path.as_posix(),
    )
    if not schema_result.ok:
        findings = tuple(
            _catalog_finding(
                finding_id="MIASI_SEMANTIC_RULES_REGISTRY_SCHEMA_INVALID_BLOCKED",
                severity=SemanticSeverity.BLOCK,
                message="MIASI semantic rules registry failed schema validation; fallback is active but semantic validation must block.",
                metadata={"path": catalog_path.as_posix(), "schema_finding": finding.to_dict()},
            )
            for finding in schema_result.findings
        )
        return _fallback_catalog(findings=findings or (_catalog_finding(
            finding_id="MIASI_SEMANTIC_RULES_REGISTRY_SCHEMA_INVALID_BLOCKED",
            severity=SemanticSeverity.BLOCK,
            message="MIASI semantic rules registry failed schema validation; fallback is active but semantic validation must block.",
            metadata={"path": catalog_path.as_posix()},
        ),))
    try:
        return _catalog_from_payload(payload)
    except (KeyError, TypeError, ValueError) as exc:
        finding = _catalog_finding(
            finding_id="MIASI_SEMANTIC_RULES_REGISTRY_LOAD_ERROR_BLOCKED",
            severity=SemanticSeverity.BLOCK,
            message="MIASI semantic rules registry could not be loaded safely; fallback is active but semantic validation must block.",
            metadata={"path": catalog_path.as_posix(), "error": str(exc)},
        )
        return _fallback_catalog(findings=(finding,))


def _catalog_from_payload(payload: dict[str, Any]) -> MiasiSemanticRulesCatalog:
    token_sets = payload["token_sets"]
    return MiasiSemanticRulesCatalog(
        rule_source=str(payload.get("rule_source", DEFAULT_MIASI_SEMANTIC_RULES_PATH.as_posix())),
        catalog_version=str(payload.get("catalog_version", "0.0.0")),
        registry_valid=True,
        fallback_active=False,
        findings=(),
        sensitive_side_effects=frozenset(_string_tuple(token_sets["sensitive_side_effects"])),
        execution_side_effects=frozenset(_string_tuple(token_sets["execution_side_effects"])),
        safe_gated_controlled_write_tokens=_string_tuple(token_sets["safe_gated_controlled_write_tokens"]),
        no_go_action_markers=_marker_map(payload["no_go_action_markers"]),
        approval_gate_tokens=_string_tuple(token_sets["approval_gate_tokens"]),
        rbac_gate_tokens=_string_tuple(token_sets["rbac_gate_tokens"]),
        secret_guard_tokens=_string_tuple(token_sets["secret_guard_tokens"]),
        network_guard_tokens=_string_tuple(token_sets["network_guard_tokens"]),
        local_guard_tokens=_string_tuple(token_sets["local_guard_tokens"]),
        sensitive_name_markers=_string_tuple(token_sets["sensitive_name_markers"]),
        no_go_future_sandbox_tokens=_string_tuple(token_sets["no_go_future_sandbox_tokens"]),
        no_go_tool_markers=_marker_map(payload["no_go_tool_markers"]),
        required_eval_fixtures=tuple(_eval_fixture(item) for item in payload["required_eval_fixtures"]),
        unsafe_eval_runtime_flags=_string_tuple(payload["unsafe_eval_runtime_flags"]),
    )


def _fallback_catalog(*, findings: tuple[SemanticFinding, ...] = ()) -> MiasiSemanticRulesCatalog:
    return MiasiSemanticRulesCatalog(
        rule_source="python:fallback:devpilot_core.miasi.declarative_semantic_rules",
        catalog_version="fallback-1.0.0",
        registry_valid=False,
        fallback_active=True,
        findings=findings,
    )


def _string_tuple(values: Any) -> tuple[str, ...]:
    if not isinstance(values, list):
        raise TypeError("expected list of strings")
    result = tuple(str(item).strip().lower() for item in values if str(item).strip())
    if not result:
        raise ValueError("empty token list is not allowed")
    return result


def _marker_map(payload: Any) -> dict[str, tuple[str, ...]]:
    if not isinstance(payload, dict):
        raise TypeError("expected marker map")
    result = {str(key).strip().lower(): _string_tuple(value) for key, value in payload.items()}
    for required in ("remote", "plugin", "connector"):
        if required not in result:
            raise ValueError(f"missing no-go marker domain: {required}")
    return result


def _eval_fixture(payload: dict[str, Any]) -> RequiredEvalFixtureSpec:
    return RequiredEvalFixtureSpec(
        path=Path(str(payload["path"])),
        suite_id=str(payload["suite_id"]),
        required_markers=_string_tuple(payload["required_markers"]),
        missing_severity=_severity(payload.get("missing_severity", "warning")),
        invalid_json_severity=_severity(payload.get("invalid_json_severity", "block")),
        suite_mismatch_severity=_severity(payload.get("suite_mismatch_severity", "block")),
        cases_missing_severity=_severity(payload.get("cases_missing_severity", "block")),
        marker_missing_severity=_severity(payload.get("marker_missing_severity", "block")),
        unsafe_runtime_flag_severity=_severity(payload.get("unsafe_runtime_flag_severity", "block")),
    )


def _severity(value: Any) -> SemanticSeverity:
    try:
        return SemanticSeverity(str(value).strip().lower())
    except ValueError as exc:
        raise ValueError(f"unsupported semantic rule severity: {value!r}") from exc


def _catalog_finding(*, finding_id: str, severity: SemanticSeverity, message: str, metadata: dict[str, Any]) -> SemanticFinding:
    return SemanticFinding(
        finding_id=finding_id,
        rule_id="SEM-RULES-REGISTRY-001",
        severity=severity,
        message=message,
        category="schema",
        subject_type="miasi_semantic_rules_registry",
        subject_id=DEFAULT_MIASI_SEMANTIC_RULES_PATH.as_posix(),
        path=DEFAULT_MIASI_SEMANTIC_RULES_PATH.as_posix(),
        metadata={
            "rule_source": DEFAULT_MIASI_SEMANTIC_RULES_PATH.as_posix(),
            "catalog_version": "unknown",
            **metadata,
        },
    )
