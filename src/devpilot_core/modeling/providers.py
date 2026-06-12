from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling.contracts import ModelProviderConfig, ModelProviderKind
from devpilot_core.policy import SecretGuard

LOCALHOST_NAMES = {"localhost", "127.0.0.1", "::1"}
EXTERNAL_PROVIDER_IDS = {"openai", "gemini", "mistral", "huggingface", "hugging-face", "hf"}

DEFAULT_PROVIDER_CONFIGS = (
    ModelProviderConfig(
        provider_id="mock",
        kind=ModelProviderKind.MOCK,
        enabled=True,
        default_model="mock-deterministic-v1",
        external_api=False,
        requires_api_key=False,
        estimated_cost_per_1k_tokens_usd=0.0,
        status="implemented",
        notes=[
            "Deterministic offline provider used by tests and default CLI flows.",
            "FUNC-SPRINT-45 keeps mock mandatory before optional local adapters are implemented.",
        ],
    ),
    ModelProviderConfig(
        provider_id="ollama",
        kind=ModelProviderKind.LOCAL,
        enabled=False,
        default_model="qwen2.5:3b-instruct",
        external_api=False,
        requires_api_key=False,
        endpoint="http://localhost:11434",
        estimated_cost_per_1k_tokens_usd=0.0,
        status="implemented-initial",
        notes=["Local optional provider implemented initially in FUNC-SPRINT-46; disabled by default and bounded by localhost-only health/model calls."],
    ),
    ModelProviderConfig(
        provider_id="lmstudio",
        kind=ModelProviderKind.LOCAL,
        enabled=False,
        default_model="local-model",
        external_api=False,
        requires_api_key=False,
        endpoint="http://localhost:1234",
        estimated_cost_per_1k_tokens_usd=0.0,
        status="planned",
        notes=["Local OpenAI-compatible placeholder planned for FUNC-SPRINT-47; disabled by default."],
    ),
    ModelProviderConfig(
        provider_id="openai",
        kind=ModelProviderKind.API,
        enabled=False,
        default_model="gpt-placeholder",
        external_api=True,
        requires_api_key=True,
        api_key_env="OPENAI_API_KEY",
        endpoint="https://api.openai.com",
        estimated_cost_per_1k_tokens_usd=0.01,
        status="disabled",
        notes=["External API placeholder; blocked by CostGuard and not called in Sprint 45."],
    ),
    ModelProviderConfig(
        provider_id="gemini",
        kind=ModelProviderKind.API,
        enabled=False,
        default_model="gemini-placeholder",
        external_api=True,
        requires_api_key=True,
        api_key_env="GEMINI_API_KEY",
        endpoint="https://generativelanguage.googleapis.com",
        estimated_cost_per_1k_tokens_usd=0.01,
        status="disabled",
        notes=["External API placeholder; blocked by CostGuard and not called in Sprint 45."],
    ),
)


@dataclass(frozen=True)
class ProviderRegistry:
    """Safe provider registry for ModelAdapter routing.

    FUNC-SPRINT-45 hardens provider configuration before real local adapters
    are introduced. The registry reads `.devpilot/providers.yaml` when present,
    otherwise `.devpilot/providers.yaml.example`, and finally deterministic
    built-in defaults. It performs semantic checks in addition to JSON Schema:

    - `mock` must exist and be enabled;
    - local providers must be localhost-only and must not require API keys;
    - external API providers must remain disabled by default;
    - raw secret values are rejected before adapter routing.
    """

    root: Path
    providers: dict[str, ModelProviderConfig]
    source_path: str
    used_example: bool = False
    schema_version: str = "built-in"
    validation_findings: tuple[Finding, ...] = field(default_factory=tuple)
    semantic_valid: bool = True

    @classmethod
    def load(cls, root: Path) -> "ProviderRegistry":
        root = root.resolve()
        candidates = [root / ".devpilot/providers.yaml", root / ".devpilot/providers.yaml.example"]
        for candidate in candidates:
            if candidate.is_file():
                payload, configs, findings = parse_provider_config_file(candidate)
                semantic_findings = validate_provider_configs(configs, payload=payload, source_path=_relative(candidate, root))
                all_findings = tuple(findings + semantic_findings)
                if configs:
                    return cls(
                        root=root,
                        providers={config.provider_id: config for config in configs},
                        source_path=_relative(candidate, root),
                        used_example=candidate.name.endswith(".example"),
                        schema_version=str(payload.get("schema_version") or "unknown"),
                        validation_findings=all_findings,
                        semantic_valid=not any(finding.severity in {Severity.BLOCK, Severity.ERROR} for finding in all_findings),
                    )
        return cls(
            root=root,
            providers={config.provider_id: config for config in DEFAULT_PROVIDER_CONFIGS},
            source_path="built-in-defaults",
            used_example=False,
            schema_version="2.0",
            validation_findings=tuple(validate_provider_configs(list(DEFAULT_PROVIDER_CONFIGS), payload={"schema_version": "2.0"}, source_path="built-in-defaults")),
            semantic_valid=True,
        )

    def get(self, provider_id: str) -> ModelProviderConfig | None:
        return self.providers.get(provider_id.strip().lower())

    def to_result(self) -> CommandResult:
        semantic_blocking = [finding for finding in self.validation_findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]
        findings = list(self.validation_findings)
        if not semantic_blocking:
            findings.insert(
                0,
                Finding(
                    id="MODEL_PROVIDER_REGISTRY_PASS",
                    message="Model provider registry loaded with safe local-first semantics.",
                    severity=Severity.INFO,
                ),
            )
        data = {
            "summary": {
                "providers_total": len(self.providers),
                "enabled_total": sum(1 for provider in self.providers.values() if provider.enabled),
                "api_providers_total": sum(1 for provider in self.providers.values() if provider.kind == ModelProviderKind.API),
                "local_providers_total": sum(1 for provider in self.providers.values() if provider.kind == ModelProviderKind.LOCAL),
                "mock_providers_total": sum(1 for provider in self.providers.values() if provider.kind == ModelProviderKind.MOCK),
                "source_path": self.source_path,
                "used_example": self.used_example,
                "schema_version": self.schema_version,
                "semantic_valid": not semantic_blocking,
                "external_api_enabled_total": sum(1 for provider in self.providers.values() if provider.enabled and provider.external_api),
                "local_enabled_total": sum(1 for provider in self.providers.values() if provider.enabled and provider.kind == ModelProviderKind.LOCAL),
                "mock_enabled": bool((self.providers.get("mock") and self.providers["mock"].enabled)),
                "network_used": False,
                "external_api_used": False,
                "preliminary": True,
            },
            "providers": [provider.to_dict() for provider in self.providers.values()],
            "preliminary": True,
            "notes": [
                "FUNC-SPRINT-46 implements the optional Ollama local adapter; LM Studio remains a future optional sprint.",
                "External providers remain disabled by default and are blocked by CostGuard/PolicyEngine.",
                "Raw API keys or secret values must never be stored in provider metadata.",
            ],
        }
        return CommandResult(
            command="model providers",
            ok=not semantic_blocking,
            exit_code=ExitCode.PASS if not semantic_blocking else ExitCode.BLOCK,
            message="Model provider registry status passed." if not semantic_blocking else "Model provider registry failed safe semantic checks.",
            data=data,
            findings=findings,
        )


def parse_providers_yaml(path: Path) -> list[ModelProviderConfig]:
    """Parse provider configs from DevPilot's narrow YAML contract.

    Public compatibility function used by older tests and modules. For semantic
    diagnostics, use `parse_provider_config_file` and `validate_provider_configs`.
    """

    _payload, configs, _findings = parse_provider_config_file(path)
    return configs


def parse_provider_config_file(path: Path) -> tuple[dict[str, Any], list[ModelProviderConfig], list[Finding]]:
    """Parse `.devpilot/providers.yaml(.example)` without external YAML deps."""

    payload = _parse_provider_yaml_payload(path)
    raw_items = payload.get("providers", [])
    findings: list[Finding] = []
    configs: list[ModelProviderConfig] = []
    for item in raw_items:
        if not isinstance(item, dict):
            findings.append(
                Finding(
                    id="MODEL_PROVIDER_CONFIG_ITEM_INVALID",
                    message="Provider entry must be a mapping/object.",
                    severity=Severity.BLOCK,
                    path=str(path),
                )
            )
            continue
        provider_id = str(item.get("id") or item.get("provider_id") or "").strip().lower()
        if not provider_id:
            findings.append(
                Finding(
                    id="MODEL_PROVIDER_ID_MISSING",
                    message="Provider entry is missing a non-empty id.",
                    severity=Severity.BLOCK,
                    path=str(path),
                )
            )
            continue
        if _contains_raw_secret(item):
            findings.append(
                Finding(
                    id="MODEL_PROVIDER_RAW_SECRET_BLOCKED",
                    message=f"Provider '{provider_id}' contains a raw secret-like value and is not routable.",
                    severity=Severity.BLOCK,
                    path=str(path),
                    metadata={"provider": provider_id},
                )
            )
            continue
        kind_raw = str(item.get("kind") or "mock").strip().lower()
        try:
            kind = ModelProviderKind(kind_raw)
        except ValueError:
            findings.append(
                Finding(
                    id="MODEL_PROVIDER_KIND_UNKNOWN",
                    message=f"Provider '{provider_id}' declares unsupported kind '{kind_raw}'.",
                    severity=Severity.BLOCK,
                    path=str(path),
                    metadata={"provider": provider_id, "kind": kind_raw},
                )
            )
            continue
        configs.append(
            ModelProviderConfig(
                provider_id=provider_id,
                kind=kind,
                enabled=bool(item.get("enabled", False)),
                default_model=str(item.get("default_model") or f"{provider_id}-model"),
                external_api=bool(item.get("external_api", kind == ModelProviderKind.API)),
                requires_api_key=bool(item.get("requires_api_key", kind == ModelProviderKind.API)),
                api_key_env=str(item["api_key_env"]) if item.get("api_key_env") else None,
                endpoint=str(item["endpoint"]) if item.get("endpoint") else None,
                estimated_cost_per_1k_tokens_usd=float(item.get("estimated_cost_per_1k_tokens_usd") or 0.0),
                status=str(item.get("status") or ("implemented" if kind == ModelProviderKind.MOCK else "planned")),
                notes=[str(value) for value in item.get("notes", [])] if isinstance(item.get("notes"), list) else [],
            )
        )
    return payload, configs, findings


def validate_provider_configs(configs: list[ModelProviderConfig] | tuple[ModelProviderConfig, ...], *, payload: dict[str, Any], source_path: str) -> list[Finding]:
    """Run semantic provider-safety checks that JSON Schema cannot express."""

    findings: list[Finding] = []
    schema_version = str(payload.get("schema_version") or "").strip()
    if schema_version and schema_version != "2.0":
        findings.append(
            Finding(
                id="MODEL_PROVIDER_SCHEMA_VERSION_LEGACY",
                message=f"Provider config schema_version is '{schema_version}', expected '2.0' for FUNC-SPRINT-45.",
                severity=Severity.WARNING,
                path=source_path,
                metadata={"schema_version": schema_version},
            )
        )

    ids = [config.provider_id for config in configs]
    duplicates = sorted({provider_id for provider_id in ids if ids.count(provider_id) > 1})
    if duplicates:
        findings.append(
            Finding(
                id="MODEL_PROVIDER_DUPLICATE_ID_BLOCKED",
                message="Provider ids must be unique.",
                severity=Severity.BLOCK,
                path=source_path,
                metadata={"duplicates": duplicates},
            )
        )

    by_id = {config.provider_id: config for config in configs}
    mock = by_id.get("mock")
    if mock is None or mock.kind != ModelProviderKind.MOCK or not mock.enabled or mock.external_api or mock.requires_api_key:
        findings.append(
            Finding(
                id="MODEL_PROVIDER_MOCK_REQUIRED_BLOCKED",
                message="The mock provider must exist, be enabled, offline and API-key-free.",
                severity=Severity.BLOCK,
                path=source_path,
            )
        )

    for config in configs:
        if config.kind == ModelProviderKind.LOCAL:
            if config.external_api or config.requires_api_key:
                findings.append(
                    Finding(
                        id="MODEL_PROVIDER_LOCAL_SECRET_OR_EXTERNAL_BLOCKED",
                        message=f"Local provider '{config.provider_id}' must not be external_api or require API keys.",
                        severity=Severity.BLOCK,
                        path=source_path,
                        metadata={"provider": config.provider_id},
                    )
                )
            if config.endpoint and not _is_local_http_endpoint(config.endpoint):
                findings.append(
                    Finding(
                        id="MODEL_PROVIDER_LOCAL_ENDPOINT_NOT_LOCAL_BLOCKED",
                        message=f"Local provider '{config.provider_id}' endpoint must be localhost-only.",
                        severity=Severity.BLOCK,
                        path=source_path,
                        metadata={"provider": config.provider_id, "endpoint": config.endpoint},
                    )
                )
            if config.enabled and config.status == "planned":
                findings.append(
                    Finding(
                        id="MODEL_PROVIDER_LOCAL_ENABLED_BEFORE_ADAPTER_WARNING",
                        message=f"Local provider '{config.provider_id}' is enabled while its adapter status is still planned.",
                        severity=Severity.WARNING,
                        path=source_path,
                        metadata={"provider": config.provider_id},
                    )
                )

        if config.kind == ModelProviderKind.API:
            if config.enabled:
                findings.append(
                    Finding(
                        id="MODEL_PROVIDER_EXTERNAL_ENABLED_BLOCKED",
                        message=f"External API provider '{config.provider_id}' must remain disabled by default.",
                        severity=Severity.BLOCK,
                        path=source_path,
                        metadata={"provider": config.provider_id},
                    )
                )
            if not config.external_api or not config.requires_api_key or not config.api_key_env:
                findings.append(
                    Finding(
                        id="MODEL_PROVIDER_EXTERNAL_CONTRACT_INVALID_BLOCKED",
                        message=f"External API provider '{config.provider_id}' must be explicit about external_api, requires_api_key and api_key_env.",
                        severity=Severity.BLOCK,
                        path=source_path,
                        metadata={"provider": config.provider_id},
                    )
                )
            if config.status != "disabled":
                findings.append(
                    Finding(
                        id="MODEL_PROVIDER_EXTERNAL_STATUS_NOT_DISABLED_BLOCKED",
                        message=f"External API provider '{config.provider_id}' status must be disabled in Sprint 45.",
                        severity=Severity.BLOCK,
                        path=source_path,
                        metadata={"provider": config.provider_id, "status": config.status},
                    )
                )
    return findings


def _parse_provider_yaml_payload(path: Path) -> dict[str, Any]:
    """Parse DevPilot's owned provider YAML shape and preserve unknown keys."""

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


def _is_local_http_endpoint(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except Exception:
        return False
    host = parsed.hostname or ""
    return parsed.scheme == "http" and host.lower() in LOCALHOST_NAMES


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


def _contains_raw_secret(item: dict[str, Any]) -> bool:
    secret_guard = SecretGuard()
    unsafe_keys = {"api_key", "token", "secret", "password", "client_secret"}
    for key, value in item.items():
        normalized_key = key.lower().strip()
        if normalized_key in unsafe_keys:
            return True
        if key == "api_key_env":
            continue
        if isinstance(value, str) and secret_guard.scan_text(value).effect.value == "block":
            return True
        if isinstance(value, list):
            for entry in value:
                if isinstance(entry, str) and secret_guard.scan_text(entry).effect.value == "block":
                    return True
    return False


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
