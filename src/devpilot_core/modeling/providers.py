from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling.contracts import ModelProviderConfig, ModelProviderKind
from devpilot_core.policy import SecretGuard

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
        notes=["Deterministic offline provider used by tests and default CLI flows."],
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
        status="planned",
        notes=["Local provider placeholder; no process is started in Sprint 17."],
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
        notes=["Local OpenAI-compatible endpoint placeholder; disabled by default."],
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
        notes=["External API placeholder; blocked by CostGuard and not called in Sprint 17."],
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
        notes=["External API placeholder; blocked by CostGuard and not called in Sprint 17."],
    ),
)


@dataclass(frozen=True)
class ProviderRegistry:
    """Safe provider registry for ModelAdapter routing.

    It reads `.devpilot/providers.yaml` when present, otherwise falls back to
    `.devpilot/providers.yaml.example`, and finally to deterministic defaults.
    The parser is intentionally narrow and dependency-free.
    """

    root: Path
    providers: dict[str, ModelProviderConfig]
    source_path: str
    used_example: bool = False

    @classmethod
    def load(cls, root: Path) -> "ProviderRegistry":
        root = root.resolve()
        candidates = [root / ".devpilot/providers.yaml", root / ".devpilot/providers.yaml.example"]
        for candidate in candidates:
            if candidate.is_file():
                configs = parse_providers_yaml(candidate)
                if configs:
                    return cls(
                        root=root,
                        providers={config.provider_id: config for config in configs},
                        source_path=_relative(candidate, root),
                        used_example=candidate.name.endswith(".example"),
                    )
        return cls(
            root=root,
            providers={config.provider_id: config for config in DEFAULT_PROVIDER_CONFIGS},
            source_path="built-in-defaults",
            used_example=False,
        )

    def get(self, provider_id: str) -> ModelProviderConfig | None:
        return self.providers.get(provider_id.strip().lower())

    def to_result(self) -> CommandResult:
        findings = [
            Finding(
                id="MODEL_PROVIDER_REGISTRY_PASS",
                message="Model provider registry loaded without raw secret values.",
                severity=Severity.INFO,
            )
        ]
        data = {
            "summary": {
                "providers_total": len(self.providers),
                "enabled_total": sum(1 for provider in self.providers.values() if provider.enabled),
                "api_providers_total": sum(1 for provider in self.providers.values() if provider.kind == ModelProviderKind.API),
                "local_providers_total": sum(1 for provider in self.providers.values() if provider.kind == ModelProviderKind.LOCAL),
                "mock_providers_total": sum(1 for provider in self.providers.values() if provider.kind == ModelProviderKind.MOCK),
                "source_path": self.source_path,
                "used_example": self.used_example,
            },
            "providers": [provider.to_dict() for provider in self.providers.values()],
            "preliminary": True,
            "notes": [
                "FUNC-SPRINT-17 stores provider metadata only, never raw API keys.",
                "External providers are placeholders and are blocked unless future policy/budget gates allow them.",
            ],
        }
        return CommandResult(
            command="model providers",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Model provider registry status passed.",
            data=data,
            findings=findings,
        )


def parse_providers_yaml(path: Path) -> list[ModelProviderConfig]:
    """Parse the narrow providers YAML shape used by DevPilot.

    This is not a general YAML parser. It supports the list-of-mappings shape
    emitted in `.devpilot/providers.yaml.example` and ignores unknown keys.
    """

    raw_items: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_list_key: str | None = None
    secret_guard = SecretGuard()

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        stripped = raw_line.strip()
        if stripped == "providers:":
            continue
        if raw_line.startswith("  - "):
            if current:
                raw_items.append(current)
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
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_list_key = key if value == "" else None
            if value == "":
                current.setdefault(key, [])
            else:
                current[key] = _parse_scalar(value)
    if current:
        raw_items.append(current)

    configs: list[ModelProviderConfig] = []
    for item in raw_items:
        provider_id = str(item.get("id") or item.get("provider_id") or "").strip().lower()
        if not provider_id:
            continue
        if _contains_raw_secret(item):
            # Fail closed by skipping unsafe provider configs. Dedicated tests
            # cover that raw secrets are not accepted as provider metadata.
            continue
        kind_raw = str(item.get("kind") or "mock").strip().lower()
        try:
            kind = ModelProviderKind(kind_raw)
        except ValueError:
            kind = ModelProviderKind.MOCK
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
    return configs


def _parse_scalar(value: str) -> Any:
    value = value.strip().strip('"').strip("'")
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _contains_raw_secret(item: dict[str, Any]) -> bool:
    secret_guard = SecretGuard()
    for key, value in item.items():
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
