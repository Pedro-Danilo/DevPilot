from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from devpilot_core.validators.frontmatter import validate_frontmatter_file

MARKDOWN_TEMPLATE_PATHS: tuple[str, ...] = (
    "docs/templates/new_project/product_vision.template.md",
    "docs/templates/new_project/mvp_scope.template.md",
    "docs/templates/new_project/requirements_specification.template.md",
    "docs/templates/new_project/architecture_document.template.md",
    "docs/templates/new_project/security_threat_model.template.md",
    "docs/templates/new_project/test_strategy.template.md",
)

MIASI_TEMPLATE_PATHS: dict[str, str] = {
    "MiasiAgentRegistry": "docs/templates/new_project/miasi_agent_registry.template.json",
    "MiasiToolRegistry": "docs/templates/new_project/miasi_tool_registry.template.json",
    "MiasiPolicyMatrix": "docs/templates/new_project/miasi_policy_matrix.template.json",
}

SCHEMA_PATHS: dict[str, str] = {
    "MiasiAgentRegistry": "docs/schemas/miasi_agent_registry.schema.json",
    "MiasiToolRegistry": "docs/schemas/miasi_tool_registry.schema.json",
    "MiasiPolicyMatrix": "docs/schemas/miasi_policy_matrix.schema.json",
}

REQUIRED_TEMPLATE_PATHS: tuple[str, ...] = MARKDOWN_TEMPLATE_PATHS + tuple(MIASI_TEMPLATE_PATHS.values())
FORBIDDEN_TEMPLATE_FRAGMENTS: tuple[str, ...] = (
    "api_key",
    "apikey",
    "access_token",
    "private_key",
    "secret_key",
    "BEGIN PRIVATE KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "MISTRAL_API_KEY",
    "ANTHROPIC_API_KEY",
)


@dataclass(frozen=True)
class TemplateValidationResult:
    """Deterministic validation summary for POST-H-024-B new-project templates."""

    ok: bool
    checked_paths: tuple[str, ...]
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "checked_paths": list(self.checked_paths),
            "errors": list(self.errors),
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
        }


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_new_project_templates(root: Path) -> TemplateValidationResult:
    """Validate POST-H-024-B templates without mutating source files.

    The function intentionally performs only local structural checks:
    Markdown frontmatter, JSON schema validation for MIASI templates and a
    conservative secret/vendor-lock-in guard. Bootstrap execution belongs to
    POST-H-024-C and is deliberately out of scope here.
    """

    root = Path(root)
    checked: list[str] = []
    errors: list[str] = []

    for rel in REQUIRED_TEMPLATE_PATHS:
        path = root / rel
        checked.append(rel)
        if not path.exists():
            errors.append(f"Missing template: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for fragment in FORBIDDEN_TEMPLATE_FRAGMENTS:
            if fragment.lower() in lowered:
                errors.append(f"Forbidden sensitive fragment {fragment!r} found in {rel}")

    for rel in MARKDOWN_TEMPLATE_PATHS:
        path = root / rel
        if not path.exists():
            continue
        result = validate_frontmatter_file(path, root=root, strict=True)
        if not result.ok:
            errors.append(f"Frontmatter validation failed for {rel}: {result.message}")

    for schema_id, rel in MIASI_TEMPLATE_PATHS.items():
        path = root / rel
        schema_path = root / SCHEMA_PATHS[schema_id]
        if not path.exists() or not schema_path.exists():
            continue
        schema = _load_json(schema_path)
        payload = _load_json(path)
        validator = Draft202012Validator(schema)
        schema_errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.path))
        for error in schema_errors:
            location = "/".join(str(part) for part in error.path) or "<root>"
            errors.append(f"{rel} does not conform to {schema_id} at {location}: {error.message}")

    return TemplateValidationResult(ok=not errors, checked_paths=tuple(checked), errors=tuple(errors))
