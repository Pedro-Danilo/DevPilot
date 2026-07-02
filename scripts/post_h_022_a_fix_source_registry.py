from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / ".devpilot" / "docs_governance" / "source_registry.json"
SCHEMA_PATH = ROOT / "docs" / "schemas" / "documentation_source_registry.schema.json"

DEFAULT_ALLOWED_CLASSIFICATIONS = {
    "source-of-truth",
    "derived",
    "machine-readable-source",
    "generated-runtime",
    "historical",
    "deprecated",
}

EXPLICIT_CLASSIFICATION_BY_DOC_ID = {
    "SCHEMA-DEVPL-ENTERPRISE-THREAT-MODEL-V1": "machine-readable-source",
    "POST-H-022-ENTERPRISE-THREAT-MODEL": "source-of-truth",
    "POST-H-022-A-ENTERPRISE-THREAT-MODEL-INSTANCE": "machine-readable-source",
    "POST-H-022-A-ENTERPRISE-ASSET-INVENTORY-REPORT": "derived",
    "POST-H-022-A-MANIFEST": "machine-readable-source",
    "POST-H-022-A-ENTERPRISE-THREAT-MODEL-TEST": "derived",
}

INVALID_CLASSIFICATION_ALIASES = {
    "source_of_truth": "source-of-truth",
    "schema": "machine-readable-source",
    "manifest": "machine-readable-source",
    "machine": "machine-readable-source",
    "json": "machine-readable-source",
    "audit": "derived",
    "audit-report": "derived",
    "report": "derived",
    "test": "derived",
    "test-contract": "derived",
    "contract": "derived",
    "implementation": "source-of-truth",
    "backlog": "source-of-truth",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_allowed_classifications() -> set[str]:
    if not SCHEMA_PATH.exists():
        return set(DEFAULT_ALLOWED_CLASSIFICATIONS)

    schema = _read_json(SCHEMA_PATH)
    enum_values = (
        schema.get("$defs", {})
        .get("document", {})
        .get("properties", {})
        .get("classification", {})
        .get("enum")
    )
    if enum_values is None:
        enum_values = (
            schema.get("properties", {})
            .get("documents", {})
            .get("items", {})
            .get("properties", {})
            .get("classification", {})
            .get("enum")
        )
    if not isinstance(enum_values, list) or not all(isinstance(item, str) for item in enum_values):
        return set(DEFAULT_ALLOWED_CLASSIFICATIONS)
    return set(enum_values)


def _fallback_classification(document: dict[str, Any], allowed: set[str]) -> str:
    doc_id = str(document.get("doc_id", ""))
    path = str(document.get("path", ""))
    current = str(document.get("classification", ""))

    explicit = EXPLICIT_CLASSIFICATION_BY_DOC_ID.get(doc_id)
    if explicit in allowed:
        return explicit

    alias = INVALID_CLASSIFICATION_ALIASES.get(current)
    if alias in allowed:
        return alias

    lowered = f"{doc_id} {path}".lower()
    if ("schema" in lowered or path.endswith(".schema.json")) and "machine-readable-source" in allowed:
        return "machine-readable-source"
    if ("manifest" in lowered or path.endswith(".json")) and "machine-readable-source" in allowed:
        return "machine-readable-source"
    if ("audit" in lowered or "report" in lowered or "test" in lowered) and "derived" in allowed:
        return "derived"
    if ("backlog" in lowered or "/post-h-" in lowered or "\\post-h-" in lowered) and "source-of-truth" in allowed:
        return "source-of-truth"
    if "derived" in allowed:
        return "derived"
    return sorted(allowed)[0]


def main() -> int:
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"source registry not found: {REGISTRY_PATH}")

    allowed = _load_allowed_classifications()
    payload = _read_json(REGISTRY_PATH)
    documents = payload.get("documents")
    if not isinstance(documents, list):
        raise ValueError("source_registry.json must contain a top-level documents list")

    updates: list[dict[str, str]] = []
    for document in documents:
        if not isinstance(document, dict):
            continue
        current = document.get("classification")
        if isinstance(current, str) and current in allowed:
            continue
        replacement = _fallback_classification(document, allowed)
        document["classification"] = replacement
        updates.append(
            {
                "doc_id": str(document.get("doc_id", "")),
                "previous": str(current),
                "replacement": replacement,
            }
        )

    REGISTRY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "allowed_classifications": sorted(allowed),
                "updated_total": len(updates),
                "updates": updates,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
