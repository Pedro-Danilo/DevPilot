from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import Finding, Severity
from devpilot_core.schemas.validator import SchemaValidator

POST_H_033_E_CREATED_BY = "POST-H-033-E"
POLICY_GUARD_PATTERN_CATALOG_SCHEMA_ID = "SCHEMA-DEVPL-POLICY-GUARD-PATTERN-CATALOG-V1"
POLICY_GUARD_PATTERN_CATALOG_CONTRACT = "PolicyGuardPatternCatalog"
DEFAULT_GUARD_PATTERN_CATALOG_PATH = Path(".devpilot/policy/guard_pattern_catalog.json")
POLICY_GUARD_PATTERN_SCHEMA_PATH = Path("docs/schemas/policy_guard_pattern_catalog.schema.json")

PROMPT_BUILT_IN_PATTERN_SPECS: tuple[dict[str, Any], ...] = (
    {
        "guard": "PromptInjectionGuard",
        "category": "instruction_override",
        "rule_id": "PROMPT_INJECTION_INSTRUCTION_OVERRIDE",
        "severity": "block",
        "pattern": r"(?i)\b(ignore|disregard|forget|override)\b.{0,48}\b(previous|prior|system|developer|policy|instruction|instructions|rules?)\b",
        "critical": True,
    },
    {
        "guard": "PromptInjectionGuard",
        "category": "policy_bypass",
        "rule_id": "PROMPT_INJECTION_POLICY_BYPASS",
        "severity": "block",
        "pattern": r"(?i)\b(bypass|disable|turn\s*off|circumvent|skip)\b.{0,48}\b(policy|guard|approval|approval_id|safety|security|validation|validator)\b",
        "critical": True,
    },
    {
        "guard": "PromptInjectionGuard",
        "category": "secret_exfiltration",
        "rule_id": "PROMPT_INJECTION_SECRET_EXFILTRATION",
        "severity": "block",
        "pattern": r"(?i)\b(print|show|reveal|dump|exfiltrate|leak|send)\b.{0,48}\b(secret|secrets|token|tokens|api[_ -]?key|password|credentials?|\.env|env vars?)\b",
        "critical": True,
    },
    {
        "guard": "PromptInjectionGuard",
        "category": "role_hijack",
        "rule_id": "PROMPT_INJECTION_ROLE_HIJACK",
        "severity": "warn",
        "pattern": r"(?i)\b(you\s+are\s+now|act\s+as|pretend\s+to\s+be)\b.{0,48}\b(root|admin|developer|system|security auditor|owner)\b",
        "critical": False,
    },
    {
        "guard": "PromptInjectionGuard",
        "category": "hidden_instruction",
        "rule_id": "PROMPT_INJECTION_HIDDEN_INSTRUCTION",
        "severity": "warn",
        "pattern": r"(?i)\b(hidden|invisible|secret)\b.{0,48}\b(instruction|prompt|message|command)\b",
        "critical": False,
    },
)

TOOL_BUILT_IN_PATTERN_SPECS: tuple[dict[str, Any], ...] = (
    {
        "guard": "ToolInjectionGuard",
        "category": "force_tool_execution",
        "rule_id": "TOOL_INJECTION_FORCE_TOOL_EXECUTION",
        "severity": "block",
        "pattern": r"(?i)\b(force|must|directly|silently|without\s+asking)\b.{0,80}\b(use|call|run|execute|invoke)\b.{0,80}\b(tool|tests\.run|patch\.apply|git\.push|deploy|shell|subprocess)\b",
        "critical": True,
    },
    {
        "guard": "ToolInjectionGuard",
        "category": "approval_bypass",
        "rule_id": "TOOL_INJECTION_APPROVAL_BYPASS",
        "severity": "block",
        "pattern": r"(?i)\b(without|skip|bypass|ignore)\b.{0,48}\b(approval|approval_id|policy|PolicyEngine|ApprovalPolicyChecker)\b",
        "critical": True,
    },
    {
        "guard": "ToolInjectionGuard",
        "category": "destructive_tool_request",
        "rule_id": "TOOL_INJECTION_DESTRUCTIVE_TOOL_REQUEST",
        "severity": "block",
        "pattern": r"(?i)\b(run|execute|call|use)\b.{0,80}\b(rm\s+-rf|del\s+/f|format\s+|git\s+push|git\s+commit|patch\s+apply|deploy|overwrite\s+docs?)\b",
        "critical": True,
    },
    {
        "guard": "ToolInjectionGuard",
        "category": "tool_selector_syntax",
        "rule_id": "TOOL_INJECTION_TOOL_SELECTOR_SYNTAX",
        "severity": "warn",
        "pattern": r"(?i)\b(tool|function|function_call|tool_call)\s*[:=]\s*['\"]?[a-zA-Z0-9_.-]{3,}",
        "critical": False,
    },
)

SECRET_BUILT_IN_KEY_PATTERN = r"(api[_-]?key|access[_-]?token|refresh[_-]?token|id[_-]?token|auth[_-]?token|token|secret|password|passwd|pwd|authorization|bearer|private[_-]?key|client[_-]?secret|database[_-]?url|connection[_-]?string|webhook)"
SECRET_BUILT_IN_VALUE_PATTERN_SPECS: tuple[dict[str, Any], ...] = (
    {"guard": "SecretGuard", "category": "openai_project_key", "rule_id": "SECRETGUARD_OPENAI_PROJECT_KEY", "severity": "block", "pattern": r"sk-proj-[A-Za-z0-9_\-]{12,}", "critical": True},
    {"guard": "SecretGuard", "category": "openai_key", "rule_id": "SECRETGUARD_OPENAI_KEY", "severity": "block", "pattern": r"sk-[A-Za-z0-9_\-]{12,}", "critical": True},
    {"guard": "SecretGuard", "category": "github_token", "rule_id": "SECRETGUARD_GITHUB_TOKEN", "severity": "block", "pattern": r"ghp_[A-Za-z0-9_]{12,}", "critical": True},
    {"guard": "SecretGuard", "category": "github_pat", "rule_id": "SECRETGUARD_GITHUB_PAT", "severity": "block", "pattern": r"github_pat_[A-Za-z0-9_\-]{12,}", "critical": True},
    {"guard": "SecretGuard", "category": "gitlab_pat", "rule_id": "SECRETGUARD_GITLAB_PAT", "severity": "block", "pattern": r"glpat-[A-Za-z0-9_\-]{12,}", "critical": True},
    {"guard": "SecretGuard", "category": "huggingface_token", "rule_id": "SECRETGUARD_HF_TOKEN", "severity": "block", "pattern": r"hf_[A-Za-z0-9_\-]{12,}", "critical": True},
    {"guard": "SecretGuard", "category": "slack_token", "rule_id": "SECRETGUARD_SLACK_TOKEN", "severity": "block", "pattern": r"xox[baprs]-[A-Za-z0-9_\-]{10,}", "critical": True},
    {"guard": "SecretGuard", "category": "aws_access_key", "rule_id": "SECRETGUARD_AWS_ACCESS_KEY", "severity": "block", "pattern": r"AKIA[0-9A-Z]{16}", "critical": True},
    {"guard": "SecretGuard", "category": "aws_temp_key", "rule_id": "SECRETGUARD_AWS_TEMP_KEY", "severity": "block", "pattern": r"ASIA[0-9A-Z]{16}", "critical": True},
    {"guard": "SecretGuard", "category": "google_api_key", "rule_id": "SECRETGUARD_GOOGLE_API_KEY", "severity": "block", "pattern": r"AIza[0-9A-Za-z_\-]{20,}", "critical": True},
    {"guard": "SecretGuard", "category": "private_key_block", "rule_id": "SECRETGUARD_PRIVATE_KEY_BLOCK", "severity": "block", "pattern": r"(?i)-----BEGIN\s+(RSA\s+|EC\s+|OPENSSH\s+)?PRIVATE\s+KEY-----[\s\S]*?-----END\s+(RSA\s+|EC\s+|OPENSSH\s+)?PRIVATE\s+KEY-----", "critical": True},
    {"guard": "SecretGuard", "category": "database_url", "rule_id": "SECRETGUARD_DATABASE_URL", "severity": "block", "pattern": r"(?i)(postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s'\"<>]+:[^\s'\"<>]+@[^\s'\"<>]+", "critical": True},
    {"guard": "SecretGuard", "category": "slack_webhook", "rule_id": "SECRETGUARD_SLACK_WEBHOOK", "severity": "block", "pattern": r"https://hooks\.slack\.com/services/[A-Za-z0-9_/\-]{20,}", "critical": True},
    {"guard": "SecretGuard", "category": "discord_webhook", "rule_id": "SECRETGUARD_DISCORD_WEBHOOK", "severity": "block", "pattern": r"https://discord(?:app)?\.com/api/webhooks/\d+/[A-Za-z0-9_\-]{20,}", "critical": True},
    {"guard": "SecretGuard", "category": "bearer_token", "rule_id": "SECRETGUARD_BEARER_TOKEN", "severity": "block", "pattern": r"(?i)(bearer)\s+([A-Za-z0-9._\-]{12,})", "critical": True},
    {"guard": "SecretGuard", "category": "basic_token", "rule_id": "SECRETGUARD_BASIC_TOKEN", "severity": "block", "pattern": r"(?i)(basic)\s+([A-Za-z0-9+/=]{12,})", "critical": True},
    {"guard": "SecretGuard", "category": "assignment_secret", "rule_id": "SECRETGUARD_ASSIGNMENT_SECRET", "severity": "block", "pattern": r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|id[_-]?token|auth[_-]?token|token|secret|password|passwd|pwd|authorization|client[_-]?secret|database[_-]?url|connection[_-]?string)\s*[:=]\s*['\"]?([^'\"\s,;]+)", "critical": True},
)

_SEVERITY_RANK = {"info": 0, "warn": 1, "warning": 1, "block": 2, "deny": 2}


@dataclass(frozen=True)
class GuardPatternRule:
    guard: str
    category: str
    rule_id: str
    severity: str
    pattern: str
    compiled: re.Pattern[str]
    source_catalog: str
    catalog_version: str
    enabled: bool = True
    critical: bool = False
    built_in_mandatory: bool = False
    cannot_disable_without_adr: bool = False
    payload_redacted: bool = True

    def to_match_metadata(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "rule_source": self.source_catalog,
            "catalog_version": self.catalog_version,
            "built_in_mandatory": self.built_in_mandatory,
            "critical": self.critical,
        }


@dataclass(frozen=True)
class PolicyGuardPatternCatalog:
    source_catalog: str
    catalog_version: str
    registry_valid: bool
    fallback_active: bool
    blocking_findings: tuple[Finding, ...] = field(default_factory=tuple)
    nonblocking_findings: tuple[Finding, ...] = field(default_factory=tuple)
    prompt_patterns: tuple[GuardPatternRule, ...] = field(default_factory=tuple)
    tool_patterns: tuple[GuardPatternRule, ...] = field(default_factory=tuple)
    secret_key_pattern: re.Pattern[str] = field(default_factory=lambda: re.compile(SECRET_BUILT_IN_KEY_PATTERN, re.IGNORECASE))
    secret_value_patterns: tuple[GuardPatternRule, ...] = field(default_factory=tuple)

    @property
    def has_blocking_catalog_findings(self) -> bool:
        return bool(self.blocking_findings)

    def metadata(self) -> dict[str, Any]:
        return {
            "rule_source": self.source_catalog,
            "catalog_version": self.catalog_version,
            "registry_valid": self.registry_valid,
            "fallback_active": self.fallback_active,
            "blocking_findings_total": len(self.blocking_findings),
            "nonblocking_findings_total": len(self.nonblocking_findings),
            "prompt_patterns_total": len(self.prompt_patterns),
            "tool_patterns_total": len(self.tool_patterns),
            "secret_value_patterns_total": len(self.secret_value_patterns),
        }


def load_guard_pattern_catalog(root: Path | None = None, catalog_path: str | Path = DEFAULT_GUARD_PATTERN_CATALOG_PATH) -> PolicyGuardPatternCatalog:
    workspace = Path(root or Path.cwd()).resolve()
    relative_catalog_path = Path(catalog_path)
    catalog_file = workspace / relative_catalog_path
    source = str(relative_catalog_path).replace("\\", "/")

    if not catalog_file.exists():
        finding = Finding(
            id="POLICY_GUARD_PATTERN_CATALOG_MISSING_FALLBACK_ACTIVE",
            message="Policy guard pattern catalog is missing; built-in mandatory guard patterns remain active as temporary fallback.",
            severity=Severity.WARNING,
            path=source,
            metadata={"created_by": POST_H_033_E_CREATED_BY, "fallback_active": True},
        )
        return _fallback_catalog(source_catalog="python:fallback:policy.guard_catalog", nonblocking_findings=[finding], fallback_active=True)

    try:
        payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    except Exception as exc:
        return _fallback_catalog_with_block(
            source,
            "POLICY_GUARD_PATTERN_CATALOG_INVALID_JSON_BLOCKED",
            f"Policy guard pattern catalog is invalid JSON: {exc}",
        )

    schema_result = SchemaValidator(workspace).validate(schema=POLICY_GUARD_PATTERN_SCHEMA_PATH, instance=relative_catalog_path)
    if not schema_result.ok:
        return _fallback_catalog_with_block(
            source,
            "POLICY_GUARD_PATTERN_CATALOG_SCHEMA_INVALID_BLOCKED",
            "Policy guard pattern catalog failed schema validation; built-in mandatory patterns remain active and policy guards fail closed.",
            metadata={"schema_findings": [finding.to_dict() for finding in schema_result.findings]},
        )

    semantic_findings = _semantic_catalog_findings(payload, source)
    if semantic_findings:
        return _fallback_catalog(
            source_catalog="python:fallback:policy.guard_catalog",
            blocking_findings=semantic_findings,
            fallback_active=True,
            registry_valid=False,
        )

    try:
        catalog_version = str(payload["catalog_version"])
        prompt_patterns = _compile_guard_rules(payload, "prompt_injection", catalog_version)
        tool_patterns = _compile_guard_rules(payload, "tool_injection", catalog_version)
        secret_value_patterns = _compile_guard_rules(payload, "secret_guard", catalog_version)
        key_patterns = payload.get("guards", {}).get("secret_guard", {}).get("sensitive_key_patterns", [])
        key_pattern_text = "|".join(f"(?:{item['pattern']})" for item in key_patterns if isinstance(item, dict) and item.get("enabled", True)) or SECRET_BUILT_IN_KEY_PATTERN
        secret_key_pattern = re.compile(key_pattern_text, re.IGNORECASE)
    except Exception as exc:
        return _fallback_catalog_with_block(
            source,
            "POLICY_GUARD_PATTERN_CATALOG_COMPILE_BLOCKED",
            f"Policy guard pattern catalog could not be compiled safely: {exc}",
        )

    return PolicyGuardPatternCatalog(
        source_catalog=source,
        catalog_version=catalog_version,
        registry_valid=True,
        fallback_active=False,
        prompt_patterns=prompt_patterns,
        tool_patterns=tool_patterns,
        secret_key_pattern=secret_key_pattern,
        secret_value_patterns=secret_value_patterns,
    )


def catalog_block_decision_metadata(catalog: PolicyGuardPatternCatalog) -> dict[str, Any]:
    return {
        **catalog.metadata(),
        "payload_redacted": True,
        "preliminary": True,
        "catalog_findings": [finding.to_dict() for finding in catalog.blocking_findings],
    }


def _compile_guard_rules(payload: dict[str, Any], guard_key: str, catalog_version: str) -> tuple[GuardPatternRule, ...]:
    guard_payload = payload.get("guards", {}).get(guard_key, {})
    rules = guard_payload.get("patterns", [])
    compiled: list[GuardPatternRule] = []
    for item in rules:
        if not isinstance(item, dict) or item.get("enabled") is False:
            continue
        compiled.append(
            GuardPatternRule(
                guard=str(item["guard"]),
                category=str(item["category"]),
                rule_id=str(item["rule_id"]),
                severity=str(item["severity"]),
                pattern=str(item["pattern"]),
                compiled=re.compile(str(item["pattern"])),
                source_catalog=str(payload["rule_source"]),
                catalog_version=catalog_version,
                enabled=True,
                critical=bool(item.get("critical", False)),
                built_in_mandatory=bool(item.get("built_in_mandatory", False)),
                cannot_disable_without_adr=bool(item.get("cannot_disable_without_adr", False)),
                payload_redacted=bool(item.get("payload_redacted", True)),
            )
        )
    return tuple(compiled)


def _semantic_catalog_findings(payload: dict[str, Any], source: str) -> tuple[Finding, ...]:
    findings: list[Finding] = []
    if payload.get("critical_rules_disable_allowed") is not False:
        findings.append(_block("POLICY_GUARD_CRITICAL_RULE_DISABLE_FLAG_BLOCKED", "Policy guard catalog must keep critical_rules_disable_allowed=false.", source))
    if payload.get("safety", {}).get("critical_rules_disable_allowed") is not False:
        findings.append(_block("POLICY_GUARD_SAFETY_CRITICAL_DISABLE_BLOCKED", "Policy guard catalog safety section must keep critical rules non-disableable.", source))
    for forbidden_flag in ("network_used", "external_api_used", "remote_execution_enabled", "connector_write_enabled", "plugin_execution_enabled", "source_mutations_performed"):
        if payload.get("safety", {}).get(forbidden_flag) not in {False, None}:
            findings.append(_block("POLICY_GUARD_UNSAFE_RUNTIME_FLAG_BLOCKED", f"Policy guard catalog cannot enable {forbidden_flag}.", source, {"flag": forbidden_flag}))

    guards = payload.get("guards", {}) if isinstance(payload.get("guards"), dict) else {}
    mandatory_groups = {
        "prompt_injection": PROMPT_BUILT_IN_PATTERN_SPECS,
        "tool_injection": TOOL_BUILT_IN_PATTERN_SPECS,
        "secret_guard": SECRET_BUILT_IN_VALUE_PATTERN_SPECS,
    }
    for guard_key, builtins in mandatory_groups.items():
        guard_payload = guards.get(guard_key, {}) if isinstance(guards.get(guard_key, {}), dict) else {}
        patterns = guard_payload.get("patterns", []) if isinstance(guard_payload.get("patterns", []), list) else []
        by_id = {item.get("rule_id"): item for item in patterns if isinstance(item, dict)}
        for spec in builtins:
            item = by_id.get(spec["rule_id"])
            if not item:
                findings.append(_block("POLICY_GUARD_MANDATORY_PATTERN_MISSING", f"Mandatory guard pattern is missing: {spec['rule_id']}", source, {"rule_id": spec["rule_id"], "guard": guard_key}))
                continue
            if item.get("enabled") is not True:
                findings.append(_block("POLICY_GUARD_MANDATORY_PATTERN_DISABLED", f"Mandatory guard pattern cannot be disabled: {spec['rule_id']}", source, {"rule_id": spec["rule_id"]}))
            if item.get("built_in_mandatory") is not True:
                findings.append(_block("POLICY_GUARD_MANDATORY_PATTERN_NOT_MARKED", f"Mandatory guard pattern must be marked built_in_mandatory: {spec['rule_id']}", source, {"rule_id": spec["rule_id"]}))
            if item.get("cannot_disable_without_adr") is not True:
                findings.append(_block("POLICY_GUARD_MANDATORY_PATTERN_ADR_FLAG_MISSING", f"Mandatory guard pattern must require ADR before disablement: {spec['rule_id']}", source, {"rule_id": spec["rule_id"]}))
            if _severity_rank(str(item.get("severity"))) < _severity_rank(str(spec["severity"])):
                findings.append(_block("POLICY_GUARD_MANDATORY_PATTERN_SEVERITY_WEAKENED", f"Mandatory guard pattern severity was weakened: {spec['rule_id']}", source, {"rule_id": spec["rule_id"], "expected": spec["severity"], "actual": item.get("severity")}))
            if item.get("pattern") != spec["pattern"]:
                findings.append(_block("POLICY_GUARD_MANDATORY_PATTERN_DRIFT_BLOCKED", f"Mandatory guard pattern cannot drift by local catalog: {spec['rule_id']}", source, {"rule_id": spec["rule_id"]}))
    return tuple(findings)


def _severity_rank(severity: str) -> int:
    return _SEVERITY_RANK.get(severity.lower(), -1)


def _block(finding_id: str, message: str, source: str, metadata: dict[str, Any] | None = None) -> Finding:
    return Finding(id=finding_id, message=message, severity=Severity.BLOCK, path=source, metadata={"created_by": POST_H_033_E_CREATED_BY, **(metadata or {})})


def _fallback_catalog_with_block(source: str, finding_id: str, message: str, metadata: dict[str, Any] | None = None) -> PolicyGuardPatternCatalog:
    return _fallback_catalog(
        source_catalog="python:fallback:policy.guard_catalog",
        blocking_findings=[_block(finding_id, message, source, metadata)],
        fallback_active=True,
        registry_valid=False,
    )


def _fallback_catalog(
    *,
    source_catalog: str,
    blocking_findings: list[Finding] | tuple[Finding, ...] = (),
    nonblocking_findings: list[Finding] | tuple[Finding, ...] = (),
    fallback_active: bool,
    registry_valid: bool = False,
) -> PolicyGuardPatternCatalog:
    return PolicyGuardPatternCatalog(
        source_catalog=source_catalog,
        catalog_version="fallback-compatible",
        registry_valid=registry_valid,
        fallback_active=fallback_active,
        blocking_findings=tuple(blocking_findings),
        nonblocking_findings=tuple(nonblocking_findings),
        prompt_patterns=tuple(_fallback_rules(PROMPT_BUILT_IN_PATTERN_SPECS, source_catalog)),
        tool_patterns=tuple(_fallback_rules(TOOL_BUILT_IN_PATTERN_SPECS, source_catalog)),
        secret_key_pattern=re.compile(SECRET_BUILT_IN_KEY_PATTERN, re.IGNORECASE),
        secret_value_patterns=tuple(_fallback_rules(SECRET_BUILT_IN_VALUE_PATTERN_SPECS, source_catalog)),
    )


def _fallback_rules(specs: tuple[dict[str, Any], ...], source_catalog: str) -> list[GuardPatternRule]:
    rules: list[GuardPatternRule] = []
    for spec in specs:
        rules.append(
            GuardPatternRule(
                guard=str(spec["guard"]),
                category=str(spec["category"]),
                rule_id=str(spec["rule_id"]),
                severity=str(spec["severity"]),
                pattern=str(spec["pattern"]),
                compiled=re.compile(str(spec["pattern"])),
                source_catalog=source_catalog,
                catalog_version="fallback-compatible",
                enabled=True,
                critical=bool(spec.get("critical", False)),
                built_in_mandatory=True,
                cannot_disable_without_adr=True,
                payload_redacted=True,
            )
        )
    return rules
