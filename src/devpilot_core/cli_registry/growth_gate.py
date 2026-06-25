from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.cli_registry.registry import DeclarativeCliRegistryBuilder

POST_H_006_E_CREATED_BY = "POST-H-006-E"
NO_GROWTH_GATE_ID = "devpilot-cli-no-growth-gate"
DEFAULT_ALLOWLIST_PATH = Path(".devpilot/cli_registry/legacy_command_allowlist.json")
DEFAULT_REPORT_JSON = Path("outputs/reports/cli_command_registry_no_growth_gate.json")
DEFAULT_REPORT_MARKDOWN = Path("outputs/reports/cli_command_registry_no_growth_gate.md")


@dataclass(frozen=True)
class CliNoGrowthGateOptions:
    """Options for the POST-H-006-E CLI no-growth gate.

    The gate is intentionally local and deterministic. It reads the static CLI
    command registry and a source-controlled allowlist of legacy commands. It
    does not execute public commands, import handler targets dynamically or
    mutate source files. Optional report writing is restricted to outputs/.
    """

    allowlist_path: Path = DEFAULT_ALLOWLIST_PATH
    write_report: bool = False
    output_json: Path = DEFAULT_REPORT_JSON
    output_markdown: Path = DEFAULT_REPORT_MARKDOWN


class CliNoGrowthGate:
    """Block unregistered growth of the monolithic CLI surface.

    POST-H-006-E turns the advisory metrics from POST-H-006-D into an actionable
    gate: every legacy-unregistered command must be present in the explicit
    temporary allowlist. A new public parser command added directly to cli.py
    without a declarative descriptor becomes an unexpected legacy command and
    the gate returns BLOCK.
    """

    def __init__(self, root: Path, options: CliNoGrowthGateOptions | None = None) -> None:
        self.root = Path(root)
        self.options = options or CliNoGrowthGateOptions()

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        registry = DeclarativeCliRegistryBuilder(self.root).build_registry().to_dict()
        allowlist_payload, allowlist_findings = self._load_allowlist()
        findings.extend(allowlist_findings)

        commands = _flatten_commands(registry)
        legacy_commands = sorted(
            command["command_id"]
            for command in commands
            if command.get("metadata", {}).get("registry_phase") == "legacy-unregistered"
        )
        registered_commands = sorted(
            command["command_id"]
            for command in commands
            if command.get("metadata", {}).get("registry_phase") == "declarative-initial"
        )
        migrated_commands = sorted(
            command["command_id"]
            for command in commands
            if command.get("metadata", {}).get("registry_phase") == "handler-migrated-incremental"
        )

        allowed_legacy = sorted(_allowed_legacy_ids(allowlist_payload))
        unexpected_legacy = sorted(set(legacy_commands) - set(allowed_legacy))
        stale_allowed = sorted(set(allowed_legacy) - set(legacy_commands))
        duplicate_allowed = sorted(_duplicates(_raw_allowlist_ids(allowlist_payload)))
        sensitive_unexpected = sorted(
            command_id
            for command_id in unexpected_legacy
            if _command_by_id(commands, command_id).get("risk_level") in {"high", "critical"}
        )

        if unexpected_legacy:
            findings.append(
                Finding(
                    id="CLI_NO_GROWTH_UNEXPECTED_LEGACY_COMMANDS",
                    message="CLI no-growth gate found public commands without declarative registry descriptor or migration metadata.",
                    severity=Severity.BLOCK,
                    metadata={"unexpected_legacy_command_ids": unexpected_legacy},
                )
            )
        else:
            findings.append(
                Finding(
                    id="CLI_NO_GROWTH_LEGACY_ALLOWLIST_MATCH",
                    message="All legacy CLI commands are explicitly covered by the temporary POST-H-006-E allowlist.",
                    severity=Severity.INFO,
                    metadata={"legacy_commands_total": len(legacy_commands)},
                )
            )

        if duplicate_allowed:
            findings.append(
                Finding(
                    id="CLI_NO_GROWTH_ALLOWLIST_DUPLICATES",
                    message="The CLI legacy allowlist contains duplicate command ids.",
                    severity=Severity.BLOCK,
                    metadata={"duplicate_command_ids": duplicate_allowed},
                )
            )

        if stale_allowed:
            findings.append(
                Finding(
                    id="CLI_NO_GROWTH_STALE_ALLOWLIST_ENTRIES",
                    message="The CLI legacy allowlist contains entries that no longer exist as legacy commands.",
                    severity=Severity.WARNING,
                    metadata={"stale_command_ids": stale_allowed},
                )
            )

        summary: dict[str, Any] = {
            "gate_id": NO_GROWTH_GATE_ID,
            "created_by": POST_H_006_E_CREATED_BY,
            "registry_created_by": registry.get("created_by"),
            "allowlist_path": str(self.options.allowlist_path).replace("\\", "/"),
            "commands_total": len(commands),
            "registered_commands_total": len(registered_commands),
            "migrated_commands_total": len(migrated_commands),
            "legacy_commands_total": len(legacy_commands),
            "allowed_legacy_commands_total": len(allowed_legacy),
            "unexpected_legacy_commands_total": len(unexpected_legacy),
            "stale_allowed_commands_total": len(stale_allowed),
            "duplicate_allowed_commands_total": len(duplicate_allowed),
            "sensitive_unexpected_legacy_commands_total": len(sensitive_unexpected),
            "reports_written": False,
            "output_json": None,
            "output_markdown": None,
            "dry_run": True,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "dynamic_handler_loading_enabled": False,
            "preliminary": True,
        }
        gate_payload = {
            "schema_version": "1.0",
            "gate_id": NO_GROWTH_GATE_ID,
            "created_by": POST_H_006_E_CREATED_BY,
            "status": "implemented-initial",
            "summary": summary,
            "policy": {
                "new_public_cli_commands_must_be_registered": True,
                "temporary_legacy_allowlist_required": True,
                "runtime_router_enabled": False,
                "dynamic_handler_loading_enabled": False,
                "fail_condition": "unexpected_legacy_commands_total > 0 or invalid allowlist",
            },
            "commands": {
                "legacy_command_ids": legacy_commands,
                "allowed_legacy_command_ids": allowed_legacy,
                "unexpected_legacy_command_ids": unexpected_legacy,
                "stale_allowed_command_ids": stale_allowed,
                "registered_command_ids": registered_commands,
                "migrated_command_ids": migrated_commands,
            },
            "safety": {
                "read_only": True,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "dynamic_handler_loading_enabled": False,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "preliminary": True,
            },
            "recommendations": [
                "Register every new public CLI command in the declarative registry before merging parser changes.",
                "Remove entries from the temporary legacy allowlist as handlers are registered or migrated.",
                "Use POST-H-007 to move eligible command families behind ApplicationService/domain boundaries.",
            ],
        }

        if self.options.write_report:
            self._write_reports(gate_payload)
            summary["reports_written"] = True
            summary["output_json"] = str(self.options.output_json).replace("\\", "/")
            summary["output_markdown"] = str(self.options.output_markdown).replace("\\", "/")

        blocking_findings_total = sum(1 for finding in findings if finding.severity == Severity.BLOCK)
        summary["blocking_findings_total"] = blocking_findings_total
        ok = blocking_findings_total == 0 and not unexpected_legacy and not duplicate_allowed

        return CommandResult(
            command="cli-registry guard",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message=(
                "CLI no-growth gate passed."
                if ok
                else "CLI no-growth gate blocked unregistered monolithic CLI growth."
            ),
            data={
                "summary": summary,
                "gate": gate_payload,
                "allowlist": allowlist_payload,
                "notes": [
                    "POST-H-006-E blocks new legacy-unregistered CLI commands unless explicitly added to the temporary allowlist.",
                    "The gate is static/read-only and does not execute public commands or import handlers dynamically.",
                    "Report writing is explicit and limited to outputs/reports; release ZIPs should exclude outputs/.",
                ],
            },
            findings=findings,
        )

    def _load_allowlist(self) -> tuple[dict[str, Any], list[Finding]]:
        path = self.root / self.options.allowlist_path
        findings: list[Finding] = []
        if not path.exists():
            return {}, [
                Finding(
                    id="CLI_NO_GROWTH_ALLOWLIST_MISSING",
                    message="CLI no-growth allowlist file is missing.",
                    severity=Severity.BLOCK,
                    path=str(self.options.allowlist_path).replace("\\", "/"),
                )
            ]
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return {}, [
                Finding(
                    id="CLI_NO_GROWTH_ALLOWLIST_INVALID_JSON",
                    message="CLI no-growth allowlist is not valid JSON.",
                    severity=Severity.BLOCK,
                    path=str(self.options.allowlist_path).replace("\\", "/"),
                    metadata={"error": str(exc)},
                )
            ]
        if payload.get("created_by") != POST_H_006_E_CREATED_BY:
            findings.append(
                Finding(
                    id="CLI_NO_GROWTH_ALLOWLIST_OWNER_MISMATCH",
                    message="CLI no-growth allowlist is not marked as POST-H-006-E owned.",
                    severity=Severity.BLOCK,
                    path=str(self.options.allowlist_path).replace("\\", "/"),
                    metadata={"created_by": payload.get("created_by")},
                )
            )
        if not isinstance(payload.get("allowed_legacy_command_ids"), list):
            findings.append(
                Finding(
                    id="CLI_NO_GROWTH_ALLOWLIST_COMMANDS_INVALID",
                    message="CLI no-growth allowlist must contain allowed_legacy_command_ids as a list.",
                    severity=Severity.BLOCK,
                    path=str(self.options.allowlist_path).replace("\\", "/"),
                )
            )
        return payload, findings

    def _write_reports(self, payload: dict[str, Any]) -> None:
        json_path = (self.root / self.options.output_json).resolve()
        markdown_path = (self.root / self.options.output_markdown).resolve()
        root = self.root.resolve()
        try:
            json_path.relative_to(root)
            markdown_path.relative_to(root)
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise ValueError("CLI no-growth gate reports must be written inside the workspace.") from exc
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(render_no_growth_markdown(payload), encoding="utf-8")


def render_no_growth_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    commands = payload.get("commands", {})
    lines = [
        "# POST-H-006-E — CLI no-growth gate",
        "",
        "Estado: `implemented-initial / blocking gate for new unregistered CLI commands`.",
        "",
        "Este gate compara el CLI Command Registry actual contra la allowlist temporal de comandos legacy conocidos. No ejecuta comandos, no importa handlers dinámicamente y no modifica fuentes.",
        "",
        "## Summary",
        "",
        f"- Commands total: {summary.get('commands_total')}",
        f"- Migrated commands total: {summary.get('migrated_commands_total')}",
        f"- Registered commands total: {summary.get('registered_commands_total')}",
        f"- Legacy commands total: {summary.get('legacy_commands_total')}",
        f"- Allowed legacy commands total: {summary.get('allowed_legacy_commands_total')}",
        f"- Unexpected legacy commands total: {summary.get('unexpected_legacy_commands_total')}",
        f"- Stale allowed commands total: {summary.get('stale_allowed_commands_total')}",
        f"- Blocking findings total: {summary.get('blocking_findings_total')}",
        "",
        "## Unexpected legacy commands",
        "",
    ]
    unexpected = commands.get("unexpected_legacy_command_ids", [])
    if unexpected:
        for command_id in unexpected:
            lines.append(f"- `{command_id}`")
    else:
        lines.append("No unexpected legacy commands detected.")
    lines.extend(
        [
            "",
            "## Policy",
            "",
            "- Todo comando público nuevo debe tener descriptor declarativo o handler migrado.",
            "- El legacy actual se permite solo mediante allowlist temporal source-controlled.",
            "- La allowlist debe reducirse progresivamente conforme se migren/registren comandos.",
            "- No se habilita runtime router ni dynamic handler loading.",
            "",
        ]
    )
    return "\n".join(lines)


def _flatten_commands(registry_payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [command for group in registry_payload.get("groups", []) for command in group.get("commands", [])]


def _raw_allowlist_ids(payload: dict[str, Any]) -> list[str]:
    raw = payload.get("allowed_legacy_command_ids", [])
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, str)]


def _allowed_legacy_ids(payload: dict[str, Any]) -> set[str]:
    return set(_raw_allowlist_ids(payload))


def _duplicates(items: list[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in items:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return duplicates


def _command_by_id(commands: list[dict[str, Any]], command_id: str) -> dict[str, Any]:
    for command in commands:
        if command.get("command_id") == command_id:
            return command
    return {}
