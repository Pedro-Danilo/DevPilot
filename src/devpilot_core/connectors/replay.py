from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

CONNECTOR_REPLAY_FIXTURE_SCHEMA_ID = "SCHEMA-DEVPL-CONNECTOR-REPLAY-FIXTURE-V1"
DEFAULT_CONNECTOR_REPLAY_FIXTURES_PATH = Path("evals/fixtures/connector_replay_cases.json")
DEFAULT_CONNECTOR_REDACTION_REPORT_JSON = Path("outputs/reports/connector_replay_redaction_report.json")
DEFAULT_CONNECTOR_REDACTION_REPORT_MD = Path("outputs/reports/connector_replay_redaction_report.md")
_ALLOWED_REPLAY_MODES = {"replay"}
_SECRET_KEY_TERMS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "client_secret",
    "credential",
    "credentials",
    "password",
    "private_key",
    "secret",
    "token",
}
_SECRET_VALUE_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_\-]{12,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)bearer\s+[a-z0-9._\-]{12,}"),
    re.compile(r"(?i)(password|token|api[_-]?key|secret)\s*[=:]\s*[^\s,;]{4,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(^|[\\/])\.env($|[\\/])"),
    re.compile(r"https?://[^\s\"']+"),
)
_SAFETY_FALSE_FIELDS = (
    "secrets_included",
    "network_used",
    "external_api_used",
    "mutations_performed",
)
_EXPECTED_FALSE_FIELDS = (
    "network_used",
    "external_api_used",
    "mutations_performed",
)


@dataclass(frozen=True)
class ConnectorReplayRequest:
    """Replay selector for deterministic POST-H-018-C connector fixtures.

    The request identifies a connector and operation. It does not authorize real
    connector execution; replay is satisfied exclusively from local JSON fixtures.
    """

    connector_id: str = "local.docs"
    operation: str = "list_sources"
    mode: str = "replay"
    input_payload: dict[str, Any] | None = None


@dataclass(frozen=True)
class ConnectorReplayOptions:
    """Options for deterministic fixture replay and redaction evidence."""

    fixtures_path: Path | str = DEFAULT_CONNECTOR_REPLAY_FIXTURES_PATH
    output_json: Path | str = DEFAULT_CONNECTOR_REDACTION_REPORT_JSON
    output_markdown: Path | str = DEFAULT_CONNECTOR_REDACTION_REPORT_MD
    write_report: bool = False


class ConnectorReplayRunner:
    """Validate and replay local connector fixtures without red or mutaciones.

    POST-H-018-C intentionally keeps replay deterministic and fixture-backed.
    It never invokes connector adapters, network clients, shell commands, remote
    runners or plugins. The runner validates that fixture content is redacted,
    secret-free and declares the same no-network/no-mutation guarantees expected
    by the connector sandbox report.
    """

    def __init__(self, root: Path, *, options: ConnectorReplayOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ConnectorReplayOptions()

    @property
    def fixtures_path(self) -> Path:
        return _resolve(self.root, self.options.fixtures_path)

    def run(self, request: ConnectorReplayRequest) -> CommandResult:
        connector_id = _normalize_id(request.connector_id)
        operation = _normalize_operation(request.operation)
        mode = _normalize_mode(request.mode)
        findings: list[Finding] = []
        fixture_set = self._load_fixture_set(findings)
        fixtures = _fixture_list(fixture_set)

        if mode not in _ALLOWED_REPLAY_MODES:
            findings.append(
                Finding(
                    "CONNECTOR_REPLAY_MODE_BLOCKED",
                    "Connector replay runner only accepts replay mode; validate/dry-run are handled by ConnectorSandboxRunner.",
                    Severity.BLOCK,
                    metadata={"requested_mode": mode, "allowed_modes": sorted(_ALLOWED_REPLAY_MODES)},
                )
            )

        selected = [
            fixture
            for fixture in fixtures
            if isinstance(fixture, dict)
            and fixture.get("connector_id") == connector_id
            and fixture.get("operation") == operation
            and fixture.get("mode") == "replay"
        ]
        if fixture_set is not None:
            findings.extend(_validate_fixture_set(fixture_set, self.fixtures_path, self.root))
        if mode == "replay" and not selected:
            findings.append(
                Finding(
                    "CONNECTOR_REPLAY_FIXTURE_MISSING",
                    "Replay mode requires at least one local fixture for the selected connector and operation.",
                    Severity.BLOCK,
                    path=_rel(self.root, self.fixtures_path),
                    metadata={"connector_id": connector_id, "operation": operation},
                )
            )

        fixture_results: list[dict[str, Any]] = []
        for fixture in selected:
            fixture_findings = _validate_fixture(fixture, self.fixtures_path, self.root)
            findings.extend(fixture_findings)
            fixture_blocked = any(item.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for item in fixture_findings)
            expected = fixture.get("expected") if isinstance(fixture.get("expected"), dict) else {}
            fixture_results.append(
                {
                    "fixture_id": fixture.get("fixture_id"),
                    "connector_id": connector_id,
                    "operation": operation,
                    "mode": fixture.get("mode"),
                    "ok": not fixture_blocked and bool(expected.get("ok", False)),
                    "redaction_required": fixture.get("redaction_required") is True,
                    "redaction_passed": not fixture_blocked,
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "deterministic_fingerprint": _fingerprint(fixture),
                    "expected": expected,
                    "input_fingerprint": _fingerprint(fixture.get("input", {})),
                }
            )

        redaction_findings = [item for item in findings if item.id.startswith("CONNECTOR_REPLAY_REDACTION") or item.id.startswith("CONNECTOR_REPLAY_SECRET")]
        blocking = sum(1 for item in findings if item.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL})
        fixtures_total = len(selected)
        fixtures_passed = sum(1 for item in fixture_results if item.get("ok") is True)
        ok = blocking == 0 and fixtures_total == fixtures_passed and fixtures_total > 0
        if ok:
            findings.append(
                Finding(
                    "CONNECTOR_REPLAY_PASS",
                    "Connector replay fixtures passed deterministic replay and redaction checks without network, external APIs or mutations.",
                    Severity.INFO,
                    metadata={"fixtures_total": fixtures_total, "fixtures_passed": fixtures_passed},
                )
            )
        else:
            # Recompute after the informational finding only when ok; otherwise leave totals exact for block reasons.
            pass

        report = {
            "schema_version": "1.0",
            "report_id": _report_id(connector_id, operation),
            "created_by": "POST-H-018-C",
            "status": "passed" if ok else "blocked",
            "connector_id": connector_id,
            "operation": operation,
            "mode": "replay",
            "ok": ok,
            "fixtures_path": _rel(self.root, self.fixtures_path),
            "summary": {
                "created_by": "POST-H-018-C",
                "status": "implemented-initial",
                "preliminary": True,
                "connector_id": connector_id,
                "operation": operation,
                "mode": "replay",
                "fixtures_total": fixtures_total,
                "fixtures_passed": fixtures_passed,
                "fixtures_failed": fixtures_total - fixtures_passed,
                "redaction_checks_total": fixtures_total,
                "redaction_findings_total": len(redaction_findings),
                "blocking_findings_total": blocking,
                "deterministic_replay": ok,
                "redaction_passed": blocking == 0,
                "secrets_included": False,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "connector_write_used": False,
                "remote_execution_used": False,
                "plugin_execution_used": False,
                "reports_written": False,
                "output_json": None,
                "output_markdown": None,
            },
            "fixture_results": fixture_results,
            "safety": _safety(),
            "findings": [finding.to_dict() for finding in findings],
            "preliminary": True,
        }
        data: dict[str, Any] = {
            "summary": dict(report["summary"]),
            "report": report,
            "fixtures": fixture_results,
            "notes": [
                "POST-H-018-C replays local fixtures only; it does not invoke real connector adapters, network, external APIs, remote execution or plugins.",
                "Fixture redaction blocks likely tokens, .env references, private keys, bearer values and URLs before replay evidence is accepted.",
            ],
        }
        if self.options.write_report:
            reports = self._write_report(report)
            report = dict(report)
            summary = dict(report["summary"])
            summary["reports_written"] = True
            summary["output_json"] = reports["json"]
            summary["output_markdown"] = reports["markdown"]
            report["summary"] = summary
            self._write_report(report)
            data["summary"] = summary
            data["report"] = report
            data["reports"] = reports

        return CommandResult(
            command="connector replay run",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Connector replay passed." if ok else "Connector replay blocked.",
            data=data,
            findings=findings,
        )

    def _load_fixture_set(self, findings: list[Finding]) -> dict[str, Any] | None:
        path = self.fixtures_path
        if not path.exists():
            findings.append(
                Finding(
                    "CONNECTOR_REPLAY_FIXTURE_SET_MISSING",
                    "Missing connector replay fixture set.",
                    Severity.BLOCK,
                    path=_rel(self.root, path),
                )
            )
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding("CONNECTOR_REPLAY_FIXTURE_SET_INVALID_JSON", str(exc), Severity.ERROR, path=_rel(self.root, path)))
            return None
        if not isinstance(payload, dict):
            findings.append(Finding("CONNECTOR_REPLAY_FIXTURE_SET_NOT_OBJECT", "Connector replay fixture set must be a JSON object.", Severity.BLOCK, path=_rel(self.root, path)))
            return None
        return payload

    def _write_report(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = _resolve(self.root, self.options.output_json)
        markdown_path = _resolve(self.root, self.options.output_markdown)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(_render_markdown(report), encoding="utf-8")
        return {"json": _rel(self.root, json_path), "markdown": _rel(self.root, markdown_path)}


def _validate_fixture_set(fixture_set: dict[str, Any], path: Path, root: Path) -> list[Finding]:
    findings: list[Finding] = []
    if fixture_set.get("created_by") not in {"POST-H-018-C", "POST-H-018-A"}:
        findings.append(Finding("CONNECTOR_REPLAY_FIXTURE_SET_OWNER_INVALID", "Fixture set must declare POST-H-018-C ownership.", Severity.BLOCK, path=_rel(root, path)))
    safety = fixture_set.get("safety") if isinstance(fixture_set.get("safety"), dict) else {}
    for flag in _SAFETY_FALSE_FIELDS:
        if safety.get(flag) is not False:
            findings.append(Finding("CONNECTOR_REPLAY_FIXTURE_SET_SAFETY_BLOCKED", f"Fixture set safety.{flag} must be false.", Severity.BLOCK, path=_rel(root, path), metadata={"flag": flag}))
    if fixture_set.get("redaction_required") is not True:
        findings.append(Finding("CONNECTOR_REPLAY_REDACTION_REQUIRED", "Fixture set must require redaction checks.", Severity.BLOCK, path=_rel(root, path)))
    fixtures = fixture_set.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        findings.append(Finding("CONNECTOR_REPLAY_FIXTURES_EMPTY", "Fixture set must contain at least one replay fixture.", Severity.BLOCK, path=_rel(root, path)))
    findings.extend(_scan_for_secrets(fixture_set, path=_rel(root, path), scope="fixture_set"))
    return findings


def _validate_fixture(fixture: dict[str, Any], path: Path, root: Path) -> list[Finding]:
    findings: list[Finding] = []
    rel = _rel(root, path)
    for field in ("schema_version", "fixture_id", "connector_id", "operation", "mode", "input", "expected", "redaction_required", "safety"):
        if field not in fixture:
            findings.append(Finding("CONNECTOR_REPLAY_FIXTURE_FIELD_MISSING", f"Replay fixture is missing {field}.", Severity.BLOCK, path=rel, metadata={"field": field, "fixture_id": fixture.get("fixture_id")}))
    if fixture.get("schema_id") not in {None, CONNECTOR_REPLAY_FIXTURE_SCHEMA_ID}:
        findings.append(Finding("CONNECTOR_REPLAY_FIXTURE_SCHEMA_ID_INVALID", "Replay fixture schema_id is invalid.", Severity.BLOCK, path=rel, metadata={"fixture_id": fixture.get("fixture_id")}))
    if fixture.get("mode") != "replay":
        findings.append(Finding("CONNECTOR_REPLAY_FIXTURE_MODE_BLOCKED", "Replay fixtures must declare mode=replay.", Severity.BLOCK, path=rel, metadata={"fixture_id": fixture.get("fixture_id"), "mode": fixture.get("mode")}))
    if fixture.get("redaction_required") is not True:
        findings.append(Finding("CONNECTOR_REPLAY_REDACTION_REQUIRED", "Every replay fixture must require redaction.", Severity.BLOCK, path=rel, metadata={"fixture_id": fixture.get("fixture_id")}))
    expected = fixture.get("expected") if isinstance(fixture.get("expected"), dict) else {}
    if expected.get("ok") is not True:
        findings.append(Finding("CONNECTOR_REPLAY_EXPECTED_NOT_OK", "Replay fixture expected.ok must be true for accepted fixtures.", Severity.BLOCK, path=rel, metadata={"fixture_id": fixture.get("fixture_id")}))
    for flag in _EXPECTED_FALSE_FIELDS:
        if expected.get(flag) is not False:
            findings.append(Finding("CONNECTOR_REPLAY_EXPECTED_SAFETY_BLOCKED", f"Replay fixture expected.{flag} must be false.", Severity.BLOCK, path=rel, metadata={"fixture_id": fixture.get("fixture_id"), "flag": flag}))
    safety = fixture.get("safety") if isinstance(fixture.get("safety"), dict) else {}
    for flag in _SAFETY_FALSE_FIELDS:
        if safety.get(flag) is not False:
            findings.append(Finding("CONNECTOR_REPLAY_FIXTURE_SAFETY_BLOCKED", f"Replay fixture safety.{flag} must be false.", Severity.BLOCK, path=rel, metadata={"fixture_id": fixture.get("fixture_id"), "flag": flag}))
    findings.extend(_scan_for_secrets(fixture, path=rel, scope=str(fixture.get("fixture_id") or "fixture")))
    return findings


def _scan_for_secrets(value: Any, *, path: str, scope: str) -> list[Finding]:
    findings: list[Finding] = []

    def visit(node: Any, key_path: tuple[str, ...]) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                key_str = str(key)
                key_lower = key_str.lower()
                # Field names like external_api_used are safety flags, not secrets.
                if key_lower in _SECRET_KEY_TERMS or key_lower.endswith(("_token", "_secret", "_password", "_api_key")):
                    findings.append(
                        Finding(
                            "CONNECTOR_REPLAY_SECRET_KEY_BLOCKED",
                            "Replay fixtures must not contain secret-bearing key names.",
                            Severity.BLOCK,
                            path=path,
                            metadata={"scope": scope, "json_path": ".".join((*key_path, key_str))},
                        )
                    )
                visit(child, (*key_path, key_str))
        elif isinstance(node, list):
            for index, child in enumerate(node):
                visit(child, (*key_path, str(index)))
        elif isinstance(node, str):
            for pattern in _SECRET_VALUE_PATTERNS:
                if pattern.search(node):
                    findings.append(
                        Finding(
                            "CONNECTOR_REPLAY_SECRET_VALUE_BLOCKED",
                            "Replay fixtures must not contain tokens, .env references, private keys, bearer values or URLs.",
                            Severity.BLOCK,
                            path=path,
                            metadata={"scope": scope, "json_path": ".".join(key_path), "pattern": pattern.pattern},
                        )
                    )
                    break

    visit(value, ())
    return findings


def _fixture_list(fixture_set: dict[str, Any] | None) -> list[Any]:
    if not isinstance(fixture_set, dict):
        return []
    fixtures = fixture_set.get("fixtures")
    return fixtures if isinstance(fixtures, list) else []


def _fingerprint(value: Any) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _safety() -> dict[str, Any]:
    return {
        "local_first": True,
        "dry_run": True,
        "network_used": False,
        "external_api_used": False,
        "mutations_performed": False,
        "source_mutations_performed": False,
        "connector_write_used": False,
        "remote_execution_used": False,
        "plugin_execution_used": False,
        "secrets_included": False,
    }


def _render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    lines = [
        "# Connector Replay Redaction Report",
        "",
        f"- Report ID: `{report.get('report_id')}`",
        f"- Generated by: `{report.get('created_by')}`",
        f"- Status: `{report.get('status')}`",
        f"- Connector: `{report.get('connector_id')}`",
        f"- Operation: `{report.get('operation')}`",
        f"- Fixtures total: `{summary.get('fixtures_total')}`",
        f"- Fixtures passed: `{summary.get('fixtures_passed')}`",
        f"- Redaction passed: `{summary.get('redaction_passed')}`",
        f"- Blocking findings: `{summary.get('blocking_findings_total')}`",
        f"- Network used: `{summary.get('network_used')}`",
        f"- External API used: `{summary.get('external_api_used')}`",
        f"- Mutations performed: `{summary.get('mutations_performed')}`",
        "",
        "## Fixture results",
    ]
    for item in report.get("fixture_results", []) or []:
        lines.append(f"- `{item.get('fixture_id')}` ok=`{item.get('ok')}` fingerprint=`{item.get('deterministic_fingerprint')}`")
    lines.extend(["", "## Findings"])
    findings = report.get("findings", []) or []
    if findings:
        for finding in findings:
            lines.append(f"- `{finding.get('severity')}` `{finding.get('id')}` — {finding.get('message')}")
    else:
        lines.append("- No findings.")
    lines.append("")
    lines.append("This report is deterministic, local-first and fixture-backed. It is not permission for real connector execution, write, network, external APIs, remote execution or plugin execution.\n")
    return "\n".join(lines)


def _report_id(connector_id: str, operation: str) -> str:
    safe = f"{connector_id}-{operation}-replay".replace(".", "-").replace("_", "-")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"connector-replay-{safe}-{stamp}"


def _normalize_id(value: str) -> str:
    return str(value or "").strip().lower().replace(" ", "-") or "local.docs"


def _normalize_operation(value: str) -> str:
    return str(value or "").strip().lower().replace("-", "_") or "list_sources"


def _normalize_mode(value: str) -> str:
    return str(value or "").strip().lower()


def _resolve(root: Path, path: Path | str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def _rel(root: Path, path: Path | str) -> str:
    candidate = Path(path)
    try:
        return candidate.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return candidate.as_posix()
