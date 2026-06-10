from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas.errors import SchemaValidationDependencyError, SchemaValidationInputError
from devpilot_core.schemas.registry import SchemaRegistry

try:  # pragma: no cover - exercised through runtime dependency checks.
    import jsonschema
    from jsonschema.validators import validator_for
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012
except Exception as exc:  # pragma: no cover - defensive branch for broken envs.
    jsonschema = None  # type: ignore[assignment]
    validator_for = None  # type: ignore[assignment]
    Registry = None  # type: ignore[assignment]
    Resource = None  # type: ignore[assignment]
    DRAFT202012 = None  # type: ignore[assignment]
    _JSONSCHEMA_IMPORT_ERROR = exc
else:
    _JSONSCHEMA_IMPORT_ERROR = None


class SchemaValidator:
    """Validate local JSON instances against DevPilot JSON Schemas.

    FUNC-SPRINT-22 turns the catalog-only Schema Registry into an executable
    contract validation capability. The validator is local-first: it reads schema
    and instance files from the workspace, resolves local references such as
    `finding.schema.json`, never calls the network, and converts all failures to
    CommandResult findings.

    The validator performs structural JSON Schema validation. It does not replace
    MIASI policy checks, readiness semantics, business rules, approval gates or
    future traceability rules.
    """

    def __init__(self, root: Path, *, registry: SchemaRegistry | None = None) -> None:
        self.root = Path(root).resolve()
        self.registry = registry or SchemaRegistry(self.root)

    def validate(self, *, schema: str | Path, instance: str | Path) -> CommandResult:
        """Validate one JSON instance against one registered or path-based schema."""

        findings: list[Finding] = []
        schema_display = _display_path(schema)
        instance_display = _display_path(instance)

        if jsonschema is None or validator_for is None or Registry is None or Resource is None or DRAFT202012 is None:
            findings.append(
                Finding(
                    id="SCHEMA_VALIDATOR_DEPENDENCY_MISSING",
                    message=f"jsonschema dependency is unavailable: {_JSONSCHEMA_IMPORT_ERROR}",
                    severity=Severity.ERROR,
                    metadata={"dependency": "jsonschema", "sprint": "FUNC-SPRINT-22"},
                )
            )
            return self._result(False, ExitCode.ERROR, "Schema validation dependency is unavailable.", schema_display, instance_display, {}, findings)

        try:
            schema_path = self.resolve_schema_path(schema)
        except SchemaValidationInputError as exc:
            findings.append(
                Finding(
                    id="SCHEMA_REFERENCE_NOT_FOUND",
                    message=str(exc),
                    severity=Severity.BLOCK,
                    path=schema_display,
                )
            )
            return self._result(False, ExitCode.BLOCK, "Schema reference could not be resolved.", schema_display, instance_display, {}, findings)

        try:
            schema_payload = self._read_json(schema_path)
        except SchemaValidationInputError as exc:
            findings.append(
                Finding(
                    id="SCHEMA_FILE_INVALID_JSON",
                    message=str(exc),
                    severity=Severity.ERROR,
                    path=_relative(schema_path, self.root),
                )
            )
            return self._result(False, ExitCode.ERROR, "Schema JSON could not be loaded.", _relative(schema_path, self.root), instance_display, {}, findings)

        instance_path = self._resolve_workspace_path(instance)
        if not instance_path.exists():
            findings.append(
                Finding(
                    id="SCHEMA_INSTANCE_MISSING",
                    message=f"Instance file does not exist: {_relative(instance_path, self.root)}",
                    severity=Severity.BLOCK,
                    path=_relative(instance_path, self.root),
                )
            )
            return self._result(False, ExitCode.BLOCK, "Instance file is missing.", _relative(schema_path, self.root), _relative(instance_path, self.root), {}, findings)

        try:
            instance_payload = self._read_json(instance_path)
        except SchemaValidationInputError as exc:
            findings.append(
                Finding(
                    id="SCHEMA_INSTANCE_INVALID_JSON",
                    message=str(exc),
                    severity=Severity.ERROR,
                    path=_relative(instance_path, self.root),
                )
            )
            return self._result(False, ExitCode.ERROR, "Instance JSON could not be loaded.", _relative(schema_path, self.root), _relative(instance_path, self.root), {}, findings)

        return self._validate_loaded_payload(
            schema_path=schema_path,
            schema_payload=schema_payload,
            instance_payload=instance_payload,
            instance_display=_relative(instance_path, self.root),
        )

    def validate_payload(
        self,
        *,
        schema: str | Path,
        payload: dict[str, Any] | list[Any],
        instance_label: str,
    ) -> CommandResult:
        """Validate an in-memory JSON-compatible payload against a schema.

        FUNC-SPRINT-23 uses this path for narrow YAML contracts such as
        `.devpilot/project.yaml` and `.devpilot/providers.yaml.example`: DevPilot
        parses the known local YAML shape into a JSON-compatible dictionary and
        then reuses the same SchemaValidator/Error/Finding contract. This is not
        a general YAML validation engine and intentionally avoids adding PyYAML.
        """

        findings: list[Finding] = []
        schema_display = _display_path(schema)
        instance_display = instance_label

        if jsonschema is None or validator_for is None or Registry is None or Resource is None or DRAFT202012 is None:
            findings.append(
                Finding(
                    id="SCHEMA_VALIDATOR_DEPENDENCY_MISSING",
                    message=f"jsonschema dependency is unavailable: {_JSONSCHEMA_IMPORT_ERROR}",
                    severity=Severity.ERROR,
                    metadata={"dependency": "jsonschema", "sprint": "FUNC-SPRINT-22"},
                )
            )
            return self._result(False, ExitCode.ERROR, "Schema validation dependency is unavailable.", schema_display, instance_display, {}, findings)

        try:
            schema_path = self.resolve_schema_path(schema)
        except SchemaValidationInputError as exc:
            findings.append(
                Finding(
                    id="SCHEMA_REFERENCE_NOT_FOUND",
                    message=str(exc),
                    severity=Severity.BLOCK,
                    path=schema_display,
                )
            )
            return self._result(False, ExitCode.BLOCK, "Schema reference could not be resolved.", schema_display, instance_display, {}, findings)

        try:
            schema_payload = self._read_json(schema_path)
        except SchemaValidationInputError as exc:
            findings.append(
                Finding(
                    id="SCHEMA_FILE_INVALID_JSON",
                    message=str(exc),
                    severity=Severity.ERROR,
                    path=_relative(schema_path, self.root),
                )
            )
            return self._result(False, ExitCode.ERROR, "Schema JSON could not be loaded.", _relative(schema_path, self.root), instance_display, {}, findings)

        return self._validate_loaded_payload(
            schema_path=schema_path,
            schema_payload=schema_payload,
            instance_payload=payload,
            instance_display=instance_display,
        )

    def resolve_schema_path(self, schema: str | Path) -> Path:
        """Resolve a schema path, schema_id or contract name to a workspace path."""

        raw = str(schema).strip()
        if not raw:
            raise SchemaValidationInputError("Schema reference is empty.")

        direct = self._resolve_workspace_path(raw)
        if direct.exists():
            return direct

        try:
            specs = self.registry.load_specs()
        except Exception as exc:
            raise SchemaValidationInputError(f"Cannot read schema catalog to resolve {raw!r}: {exc}") from exc

        normalized = raw.lower()
        matches = [
            spec
            for spec in specs
            if spec.schema_id.lower() == normalized
            or (spec.contract or "").lower() == normalized
            or spec.path.lower() == normalized
        ]
        if len(matches) == 1:
            return matches[0].absolute_path(self.root)
        if len(matches) > 1:
            raise SchemaValidationInputError(f"Schema reference is ambiguous: {raw}")
        raise SchemaValidationInputError(f"Schema reference was not found as path, schema_id or contract: {raw}")

    def _read_json(self, path: Path) -> dict[str, Any] | list[Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise SchemaValidationInputError(f"JSON file does not exist: {_relative(path, self.root)}") from exc
        except json.JSONDecodeError as exc:
            raise SchemaValidationInputError(f"Invalid JSON in {_relative(path, self.root)}: {exc.msg} at line {exc.lineno}, column {exc.colno}") from exc
        if not isinstance(payload, (dict, list)):
            raise SchemaValidationInputError(f"JSON root must be an object or array: {_relative(path, self.root)}")
        return payload

    def _validate_loaded_payload(
        self,
        *,
        schema_path: Path,
        schema_payload: dict[str, Any] | list[Any],
        instance_payload: dict[str, Any] | list[Any],
        instance_display: str,
    ) -> CommandResult:
        findings: list[Finding] = []
        try:
            validator_cls = validator_for(schema_payload)
            validator_cls.check_schema(schema_payload)
            registry = self._build_local_schema_registry()
            validator = validator_cls(schema_payload, registry=registry)
            validation_errors = sorted(validator.iter_errors(instance_payload), key=lambda error: list(error.absolute_path))
        except Exception as exc:
            findings.append(
                Finding(
                    id="SCHEMA_DEFINITION_INVALID",
                    message=f"Schema definition could not be evaluated: {exc}",
                    severity=Severity.ERROR,
                    path=_relative(schema_path, self.root),
                    metadata={"schema": _relative(schema_path, self.root)},
                )
            )
            return self._result(False, ExitCode.ERROR, "Schema definition is invalid.", _relative(schema_path, self.root), instance_display, {}, findings)

        for error in validation_errors:
            instance_pointer = _json_pointer(error.absolute_path)
            schema_pointer = _json_pointer(error.absolute_schema_path)
            findings.append(
                Finding(
                    id="SCHEMA_VALIDATION_ERROR",
                    message=error.message,
                    severity=Severity.BLOCK,
                    path=instance_pointer,
                    metadata={
                        "validator": error.validator,
                        "instance_path": instance_pointer,
                        "schema_path": schema_pointer,
                        "schema_file": _relative(schema_path, self.root),
                        "instance_file": instance_display,
                    },
                )
            )

        ok = not validation_errors
        if ok:
            findings.append(
                Finding(
                    id="SCHEMA_VALIDATION_PASS",
                    message="Instance conforms to schema.",
                    severity=Severity.INFO,
                    metadata={"schema": _relative(schema_path, self.root), "instance": instance_display},
                )
            )

        return self._result(
            ok,
            ExitCode.PASS if ok else ExitCode.BLOCK,
            "Schema validation passed." if ok else "Schema validation failed with blocking findings.",
            _relative(schema_path, self.root),
            instance_display,
            {
                "schema_title": schema_payload.get("title") if isinstance(schema_payload, dict) else None,
                "schema_id": (schema_payload.get("x-devpilot-schema-id") or schema_payload.get("$id")) if isinstance(schema_payload, dict) else None,
                "errors_total": len(validation_errors),
                "validator": "jsonschema",
                "jsonschema_version": _jsonschema_version(),
                "preliminary": True,
            },
            findings,
        )

    def _build_local_schema_registry(self):
        """Build an in-memory registry for local schema references.

        DevPilot schemas may use local references such as `finding.schema.json`.
        The registry maps file URIs, canonical `$id` values and
        `https://devpilot.local/schemas/<filename>` aliases to local schema
        resources, preventing accidental network resolution.
        """

        registry = Registry()
        resources: list[tuple[str, Any]] = []
        schemas_dir = self.root / "docs" / "schemas"
        if schemas_dir.exists():
            for path in schemas_dir.glob("*.schema.json"):
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                resource = Resource.from_contents(payload, default_specification=DRAFT202012)
                resources.append((path.resolve().as_uri(), resource))
                resources.append((f"https://devpilot.local/schemas/{path.name}", resource))
                if isinstance(payload, dict) and payload.get("$id"):
                    resources.append((str(payload["$id"]), resource))
        return registry.with_resources(resources)

    def _resolve_workspace_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        return candidate.resolve()

    def _result(
        self,
        ok: bool,
        exit_code: ExitCode,
        message: str,
        schema_path: str,
        instance_path: str,
        extra_summary: dict[str, Any],
        findings: list[Finding],
    ) -> CommandResult:
        errors_total = sum(1 for finding in findings if finding.id == "SCHEMA_VALIDATION_ERROR")
        summary = {
            "schema": schema_path,
            "instance": instance_path,
            "valid": ok,
            "errors_total": errors_total,
            "findings_total": len(findings),
            "network_used": False,
            "external_api_used": False,
            **extra_summary,
        }
        return CommandResult(
            command="schema validate",
            ok=ok,
            exit_code=exit_code,
            message=message,
            data={
                "summary": summary,
                "schema": schema_path,
                "instance": instance_path,
                "notes": [
                    "FUNC-SPRINT-22 validates JSON structure only; semantic gates remain in dedicated validators.",
                    "Validation is local-first and does not call network or external APIs.",
                ],
            },
            findings=findings,
        )


def _display_path(value: str | Path) -> str:
    return str(value).replace("\\", "/")


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _json_pointer(parts: Any) -> str:
    sequence = list(parts)
    if not sequence:
        return "/"
    escaped = [str(part).replace("~", "~0").replace("/", "~1") for part in sequence]
    return "/" + "/".join(escaped)


def _jsonschema_version() -> str:
    try:
        from importlib.metadata import version

        return version("jsonschema")
    except Exception:  # pragma: no cover - defensive fallback.
        return "unknown"
