from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas.models import SchemaRegistrySummary, SchemaSpec

DEFAULT_SCHEMA_CATALOG = Path("docs/schemas/schema_catalog.json")


class SchemaRegistry:
    """Local catalog of versioned DevPilot JSON schemas.

    This registry is intentionally lightweight: it reads `docs/schemas/schema_catalog.json`,
    maps schema identifiers to files, detects duplicate IDs and missing files,
    and returns a CommandResult-ready payload. It does not validate arbitrary
    JSON instances against the schemas; that responsibility belongs to the
    future Schema Validator sprint.
    """

    def __init__(self, root: Path, catalog_path: str | Path = DEFAULT_SCHEMA_CATALOG) -> None:
        self.root = Path(root)
        self.catalog_path = Path(catalog_path)

    @property
    def resolved_catalog_path(self) -> Path:
        return self.root / self.catalog_path

    def load_specs(self) -> list[SchemaSpec]:
        catalog_file = self.resolved_catalog_path
        payload = json.loads(catalog_file.read_text(encoding="utf-8"))
        raw_schemas = payload.get("schemas", [])
        if not isinstance(raw_schemas, list):
            raise ValueError("schema_catalog.json must contain a 'schemas' list")
        return [SchemaSpec.from_dict(item) for item in raw_schemas if isinstance(item, dict)]

    def list(self) -> CommandResult:
        findings: list[Finding] = []
        if not self.resolved_catalog_path.exists():
            finding = Finding(
                id="SCHEMA_CATALOG_MISSING",
                message="Schema catalog was not found.",
                severity=Severity.BLOCK,
                path=str(self.catalog_path).replace("\\", "/"),
            )
            return CommandResult(
                command="schema list",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Schema registry catalog is missing.",
                data={
                    "summary": SchemaRegistrySummary(
                        schemas_total=0,
                        schemas_existing=0,
                        duplicate_schema_ids=[],
                        missing_schema_paths=[str(self.catalog_path).replace("\\", "/")],
                        catalog_path=str(self.catalog_path).replace("\\", "/"),
                    ).to_dict(),
                    "schemas": [],
                },
                findings=[finding],
            )

        try:
            specs = self.load_specs()
        except Exception as exc:
            finding = Finding(
                id="SCHEMA_CATALOG_INVALID",
                message=f"Schema catalog could not be loaded: {exc}",
                severity=Severity.ERROR,
                path=str(self.catalog_path).replace("\\", "/"),
            )
            return CommandResult(
                command="schema list",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Schema registry catalog is invalid.",
                data={"summary": {}, "schemas": []},
                findings=[finding],
            )

        counts = Counter(spec.schema_id for spec in specs)
        duplicate_ids = sorted(schema_id for schema_id, count in counts.items() if schema_id and count > 1)
        missing_paths = sorted(spec.path for spec in specs if not spec.absolute_path(self.root).exists())
        empty_required_fields = self._find_specs_with_empty_required_fields(specs)

        for schema_id in duplicate_ids:
            findings.append(
                Finding(
                    id="SCHEMA_REGISTRY_DUPLICATE_ID",
                    message=f"Duplicate schema_id detected: {schema_id}",
                    severity=Severity.BLOCK,
                    metadata={"schema_id": schema_id},
                )
            )
        for path in missing_paths:
            findings.append(
                Finding(
                    id="SCHEMA_REGISTRY_MISSING_FILE",
                    message=f"Registered schema file does not exist: {path}",
                    severity=Severity.BLOCK,
                    path=path,
                )
            )
        for item in empty_required_fields:
            findings.append(
                Finding(
                    id="SCHEMA_REGISTRY_REQUIRED_FIELD_MISSING",
                    message=f"Registered schema entry is missing required metadata: {item['field']}",
                    severity=Severity.BLOCK,
                    path=item.get("path"),
                    metadata={"schema_id": item.get("schema_id"), "field": item["field"]},
                )
            )

        summary = SchemaRegistrySummary(
            schemas_total=len(specs),
            schemas_existing=sum(1 for spec in specs if spec.absolute_path(self.root).exists()),
            duplicate_schema_ids=duplicate_ids,
            missing_schema_paths=missing_paths,
            catalog_path=str(self.catalog_path).replace("\\", "/"),
        )
        ok = summary.ok and not empty_required_fields
        findings.append(
            Finding(
                id="SCHEMA_REGISTRY_PASS" if ok else "SCHEMA_REGISTRY_BLOCK",
                message="Schema registry catalog integrity passed." if ok else "Schema registry catalog integrity failed.",
                severity=Severity.INFO if ok else Severity.BLOCK,
                metadata=summary.to_dict(),
            )
        )
        return CommandResult(
            command="schema list",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Schema registry listed successfully." if ok else "Schema registry has blocking catalog findings.",
            data={
                "summary": summary.to_dict(),
                "schemas": [spec.to_dict() for spec in specs],
                "notes": [
                    "FUNC-SPRINT-21 registers schemas only; it does not validate JSON instances.",
                    "Full SchemaValidator behavior is planned for FUNC-SPRINT-22.",
                ],
            },
            findings=findings,
        )

    def _find_specs_with_empty_required_fields(self, specs: list[SchemaSpec]) -> list[dict[str, Any]]:
        missing: list[dict[str, Any]] = []
        for spec in specs:
            for field_name in ("schema_id", "title", "version", "path", "description"):
                if not getattr(spec, field_name):
                    missing.append({"schema_id": spec.schema_id, "path": spec.path, "field": field_name})
        return missing
