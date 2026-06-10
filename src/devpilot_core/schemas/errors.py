from __future__ import annotations


class SchemaValidationDependencyError(RuntimeError):
    """Raised when the configured JSON Schema validation dependency is unavailable.

    FUNC-SPRINT-22 intentionally uses the external `jsonschema` package, governed
    by ADR-0010, because DevPilot's contracts declare JSON Schema Draft 2020-12.
    This explicit error lets the CLI convert missing dependency failures into a
    controlled CommandResult instead of leaking stack traces.
    """


class SchemaValidationInputError(ValueError):
    """Raised for invalid schema/instance inputs before JSON Schema validation.

    These errors cover missing files, invalid JSON and unsupported schema
    references. The CLI must surface them as actionable findings.
    """
