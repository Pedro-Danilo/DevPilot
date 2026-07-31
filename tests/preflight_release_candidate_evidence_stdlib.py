#!/usr/bin/env python3
"""Read-only stdlib preflight for release-candidate evidence contracts.

This script intentionally mirrors the path, JSON, schema-id, expected-field and
required-marker checks performed by EvidenceFreshnessScanner. It does not import
DevPilot, pytest or jsonschema, does not write reports, and does not mutate the
repository. Its purpose is to detect packaging-time governance drift before the
dependency-backed validators run.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_CRITERIA = ".devpilot/release/local_release_candidate_criteria.json"
STATUSES = ("fresh", "stale", "missing", "invalid", "not_applicable")


def _inside(root: Path, value: str | Path) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()
    resolved.relative_to(root)
    return resolved


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_id(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    for key in ("schema_id", "x-devpilot-schema-id"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return None


def _lookup(payload: Any, dotted_key: str) -> Any:
    current = payload
    for part in dotted_key.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def evaluate(root: Path, item: dict[str, Any]) -> dict[str, Any]:
    path = _inside(root, str(item.get("path", "")))
    critical = bool(item.get("critical", False))
    runtime_optional = bool(item.get("runtime_optional", False))
    failures: list[dict[str, Any]] = []
    status = "fresh"
    reason = "freshness checks passed"
    payload: Any = None
    text: str | None = None

    if not path.exists():
        status = "not_applicable" if runtime_optional else "missing"
        reason = (
            "optional runtime evidence absent"
            if runtime_optional
            else "path does not exist"
        )
    elif path.is_dir():
        status = "invalid"
        reason = "expected evidence file, found directory"
    else:
        json_required = bool(item.get("json_required")) or path.suffix.lower() == ".json"
        if json_required:
            try:
                payload = _load_json(path)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                status = "invalid"
                reason = f"invalid json: {exc}"
            if status == "fresh":
                expected_schema_id = item.get("expected_schema_id")
                actual_schema_id = _schema_id(payload)
                if expected_schema_id and actual_schema_id != expected_schema_id:
                    status = "invalid"
                    reason = "schema_id mismatch"
                    failures.append(
                        {
                            "check": "schema_id",
                            "expected": expected_schema_id,
                            "actual": actual_schema_id,
                        }
                    )

        if status == "fresh":
            for key, expected in (item.get("expected_fields") or {}).items():
                actual = _lookup(payload, key) if payload is not None else None
                if actual != expected:
                    failures.append(
                        {
                            "check": f"field:{key}",
                            "expected": expected,
                            "actual": actual,
                        }
                    )

            if payload is not None:
                text = json.dumps(payload, sort_keys=True, ensure_ascii=False)
            else:
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    text = ""

            for marker in item.get("required_markers", []) or []:
                if str(marker) not in (text or ""):
                    failures.append(
                        {
                            "check": "required_marker",
                            "marker": str(marker),
                        }
                    )

            if failures:
                status = "stale"
                first = failures[0]
                if first["check"] == "required_marker":
                    reason = f"required marker not found: {first['marker']}"
                else:
                    reason = f"{first['check']} does not match"

    return {
        "evidence_id": item.get("evidence_id"),
        "path": _relative(root, path),
        "critical": critical,
        "runtime_optional": runtime_optional,
        "status": status,
        "reason": reason,
        "failed_checks": failures,
    }


def scan(root: Path, criteria_value: str = DEFAULT_CRITERIA) -> dict[str, Any]:
    root = root.resolve()
    criteria_path = _inside(root, criteria_value)
    criteria = _load_json(criteria_path)
    items = [
        evaluate(root, item)
        for item in criteria.get("evidence", [])
        if isinstance(item, dict)
    ]
    critical = [item for item in items if item["critical"]]
    counts = {
        status: sum(item["status"] == status for item in items)
        for status in STATUSES
    }
    critical_counts = {
        status: sum(item["status"] == status for item in critical)
        for status in ("stale", "missing", "invalid")
    }
    no_go_gates = dict(criteria.get("no_go_gates", {}))
    no_go_gates_passed = all(value is False for value in no_go_gates.values())
    decision = (
        "PASS"
        if not any(critical_counts.values()) and no_go_gates_passed
        else "BLOCK"
    )
    return {
        "schema_id": "devpilot.release_candidate_evidence_preflight.stdlib.v1",
        "decision": decision,
        "criteria_path": _relative(root, criteria_path),
        "criteria_id": criteria.get("criteria_id"),
        "evidence_total": len(items),
        "critical_total": len(critical),
        "fresh_total": counts["fresh"],
        "stale_total": counts["stale"],
        "missing_total": counts["missing"],
        "invalid_total": counts["invalid"],
        "not_applicable_total": counts["not_applicable"],
        "critical_stale_total": critical_counts["stale"],
        "critical_missing_total": critical_counts["missing"],
        "critical_invalid_total": critical_counts["invalid"],
        "no_go_gates_passed": no_go_gates_passed,
        "no_go_gates": no_go_gates,
        "blocking_items": [
            item
            for item in critical
            if item["status"] in {"stale", "missing", "invalid"}
        ],
        "safety": {
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "reports_written": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--criteria", default=DEFAULT_CRITERIA)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = scan(Path(args.root), args.criteria)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(
            "EVIDENCE PREFLIGHT = "
            f"{result['decision']} | total={result['evidence_total']} | "
            f"critical_stale={result['critical_stale_total']} | "
            f"critical_missing={result['critical_missing_total']} | "
            f"critical_invalid={result['critical_invalid_total']}"
        )
        for item in result["blocking_items"]:
            print(
                f"BLOCK | {item['evidence_id']} | "
                f"{item['path']} | {item['reason']}"
            )
    return 0 if result["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
