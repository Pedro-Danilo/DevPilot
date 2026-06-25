from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

POST_H_006_D_CREATED_BY = "POST-H-006-D"
HOTSPOT_REPORT_ID = "devpilot-cli-command-hotspot-ownership-report"
TEST_FILE_PATTERN = re.compile(r"tests/[A-Za-z0-9_./-]+\.py")


@dataclass(frozen=True)
class CliHotspotOwnershipReportBuilder:
    """Build the POST-H-006-D read-only CLI hotspot and ownership report.

    The report is deliberately derived from the schema-backed CLI command
    registry plus local Test Contract Registry data. It does not import CLI
    handlers, does not call command functions and does not mutate source files.
    """

    root: Path
    registry_payload: dict[str, Any]
    v1_contract_path: Path = Path(".devpilot/testing/test_contract_registry.json")
    v2_contract_path: Path = Path(".devpilot/testing/test_contract_registry_v2.json")

    def build(self) -> dict[str, Any]:
        commands = _flatten_commands(self.registry_payload)
        v1_contracts = _load_contracts(self.root / self.v1_contract_path)
        v2_contracts = _load_contracts(self.root / self.v2_contract_path)
        test_index = _build_test_contract_index(v1_contracts, v2_contracts)

        analyzed_commands: list[dict[str, Any]] = []
        status_counts: Counter[str] = Counter()
        risk_counts: Counter[str] = Counter()
        domain_counts: Counter[str] = Counter()
        owner_counts: Counter[str] = Counter()
        side_effect_counts: Counter[str] = Counter()
        without_test_contract: list[dict[str, Any]] = []
        without_application_service_boundary: list[dict[str, Any]] = []
        critical_commands: list[dict[str, Any]] = []

        for command in commands:
            phase = _ownership_status(command)
            status_counts[phase] += 1
            risk_counts[command["risk_level"]] += 1
            domain_counts[command["domain"]] += 1
            owner_counts[command["owner_module"]] += 1
            for effect in command.get("side_effects", []):
                side_effect_counts[effect] += 1

            tests = _extract_test_files(command.get("recommended_tests", []))
            matched_contracts = sorted({item for test in tests for item in test_index.get(test, [])})
            missing_contract = not matched_contracts
            app_service_gap = _is_without_application_service_boundary(command)
            score, reasons = _score_command(command, phase, missing_contract, app_service_gap)
            record = {
                "command_id": command["command_id"],
                "command_path": command["command_path"],
                "public_invocation": command["public_invocation"],
                "domain": command["domain"],
                "owner_module": command["owner_module"],
                "handler": command["handler"],
                "risk_level": command["risk_level"],
                "side_effects": command.get("side_effects", []),
                "writes_files": command.get("writes_files", False),
                "policy_check_required": command.get("policy_check_required", False),
                "ownership_status": phase,
                "legacy_cli_owned": command.get("legacy_cli_owned", True),
                "test_files": tests,
                "associated_test_contracts": matched_contracts,
                "missing_test_contract": missing_contract,
                "application_service_boundary_present": not app_service_gap,
                "hotspot_score": score,
                "hotspot_reasons": reasons,
                "recommendations": _recommendations_for(command, phase, missing_contract, app_service_gap),
            }
            analyzed_commands.append(record)
            if missing_contract:
                without_test_contract.append(_summary_record(record))
            if app_service_gap:
                without_application_service_boundary.append(_summary_record(record))
            if command["risk_level"] in {"high", "critical"}:
                critical_commands.append(_summary_record(record))

        hotspots = sorted(analyzed_commands, key=lambda item: (-item["hotspot_score"], item["command_id"]))
        commands_with_side_effects = [item for item in analyzed_commands if item["side_effects"] != ["none"]]
        high_critical = [item for item in analyzed_commands if item["risk_level"] in {"high", "critical"}]

        summary = {
            "commands_total": len(commands),
            "domains_total": len(domain_counts),
            "owners_total": len(owner_counts),
            "migrated_commands_total": status_counts.get("migrated", 0),
            "registered_only_commands_total": status_counts.get("registered_only", 0),
            "legacy_commands_total": status_counts.get("legacy", 0),
            "ownership_status_counts": dict(sorted(status_counts.items())),
            "commands_with_side_effects_total": len(commands_with_side_effects),
            "high_or_critical_risk_commands_total": len(high_critical),
            "commands_without_application_service_boundary_total": len(without_application_service_boundary),
            "commands_without_test_contract_total": len(without_test_contract),
            "top_hotspots_total": min(20, len(hotspots)),
            "test_contracts_v1_total": len(v1_contracts),
            "test_contracts_v2_total": len(v2_contracts),
            "advisory_only": True,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }

        return {
            "schema_version": "1.0",
            "report_id": HOTSPOT_REPORT_ID,
            "created_by": POST_H_006_D_CREATED_BY,
            "generated_from": self.registry_payload.get("registry_id", "devpilot-cli-command-registry"),
            "status": "implemented-initial",
            "summary": summary,
            "ownership": {
                "by_domain": _counter_to_records(domain_counts, "domain"),
                "by_owner_module": _counter_to_records(owner_counts, "owner_module"),
                "by_status": _counter_to_records(status_counts, "ownership_status"),
                "application_service_boundary": {
                    "present_total": len(commands) - len(without_application_service_boundary),
                    "missing_total": len(without_application_service_boundary),
                    "missing_commands": without_application_service_boundary,
                },
            },
            "risk": {
                "by_risk_level": _counter_to_records(risk_counts, "risk_level"),
                "side_effects": _counter_to_records(side_effect_counts, "side_effect"),
                "high_or_critical_commands": critical_commands,
            },
            "test_contract_coverage": {
                "indexed_test_files_total": len(test_index),
                "commands_without_test_contract": without_test_contract,
                "note": "Coverage is inferred from recommended_tests mapped to Test Contract Registry v1/v2 test_files; it is advisory, not a substitute for command-specific tests.",
            },
            "hotspots": hotspots[:20],
            "roadmap_links": [
                {
                    "id": "POST-H-007",
                    "reason": "Commands without ApplicationService boundary are direct input for ApplicationService hardening.",
                },
                {
                    "id": "POST-H-003",
                    "reason": "Commands without test-contract association are direct input for Test Contract Registry coverage and impact rules.",
                },
                {
                    "id": "POST-H-006-E",
                    "reason": "Legacy and registered-only commands feed the no-growth gate and allowlist policy.",
                },
            ],
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
                "Use migrated/registered_only/legacy counts as the baseline for POST-H-006-E no-growth enforcement.",
                "Prioritize high/critical legacy commands before migrating command families with subprocess, write-files or potential-network side effects.",
                "Use commands_without_application_service_boundary as direct input for POST-H-007 ApplicationService boundary hardening.",
                "Use commands_without_test_contract as direct input for POST-H-003/TCR v2 coverage refinement.",
            ],
        }


def render_hotspot_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "# POST-H-006-D — CLI hotspots and command ownership report",
        "",
        "Estado: `implemented-initial / read-only advisory report`.",
        "",
        "Este reporte deriva del CLI Command Registry y del Test Contract Registry local. No ejecuta comandos, no importa handlers y no modifica fuentes.",
        "",
        "## Summary",
        "",
        f"- Commands total: {summary.get('commands_total')}",
        f"- Domains total: {summary.get('domains_total')}",
        f"- Owners total: {summary.get('owners_total')}",
        f"- Migrated commands total: {summary.get('migrated_commands_total')}",
        f"- Registered-only commands total: {summary.get('registered_only_commands_total')}",
        f"- Legacy commands total: {summary.get('legacy_commands_total')}",
        f"- Commands with side effects total: {summary.get('commands_with_side_effects_total')}",
        f"- High/critical risk commands total: {summary.get('high_or_critical_risk_commands_total')}",
        f"- Commands without ApplicationService boundary total: {summary.get('commands_without_application_service_boundary_total')}",
        f"- Commands without test-contract association total: {summary.get('commands_without_test_contract_total')}",
        "",
        "## Ownership status",
        "",
        "| Status | Commands |",
        "|---|---:|",
    ]
    for item in report.get("ownership", {}).get("by_status", []):
        lines.append(f"| `{item['ownership_status']}` | {item['commands_total']} |")
    lines.extend([
        "",
        "## Domains",
        "",
        "| Domain | Commands |",
        "|---|---:|",
    ])
    for item in report.get("ownership", {}).get("by_domain", []):
        lines.append(f"| `{item['domain']}` | {item['commands_total']} |")
    lines.extend([
        "",
        "## Top command hotspots",
        "",
        "| Score | Command | Risk | Status | Owner |",
        "|---:|---|---|---|---|",
    ])
    for item in report.get("hotspots", []):
        lines.append(
            f"| {item['hotspot_score']} | `{item['command_id']}` | `{item['risk_level']}` | `{item['ownership_status']}` | `{item['owner_module']}` |"
        )
    lines.extend([
        "",
        "## Industrial notes",
        "",
        "- Esta versión es preliminar y advisory: orienta refactor, ownership y test coverage, pero no bloquea todavía cambios.",
        "- La transición a gate de no crecimiento se implementa en POST-H-006-E.",
        "- No habilita remote execution, connector write, plugin execution ni runtime registry routing.",
        "",
    ])
    return "\n".join(lines)


def _flatten_commands(registry_payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [command for group in registry_payload.get("groups", []) for command in group.get("commands", [])]


def _load_contracts(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    contracts = payload.get("contracts", [])
    return contracts if isinstance(contracts, list) else []


def _build_test_contract_index(v1_contracts: list[dict[str, Any]], v2_contracts: list[dict[str, Any]]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    for contract in [*v1_contracts, *v2_contracts]:
        contract_id = contract.get("contract_id")
        if not contract_id:
            continue
        for test_file in contract.get("test_files", []):
            if isinstance(test_file, str):
                index[test_file.replace("\\", "/")].append(str(contract_id))
    return index


def _extract_test_files(recommended_tests: list[str]) -> list[str]:
    files: set[str] = set()
    for command in recommended_tests:
        if not isinstance(command, str):
            continue
        files.update(match.group(0).replace("\\", "/") for match in TEST_FILE_PATTERN.finditer(command))
    return sorted(files)


def _ownership_status(command: dict[str, Any]) -> str:
    metadata = command.get("metadata", {})
    phase = metadata.get("registry_phase")
    if phase == "handler-migrated-incremental":
        return "migrated"
    if phase == "declarative-initial":
        return "registered_only"
    return "legacy"


def _is_without_application_service_boundary(command: dict[str, Any]) -> bool:
    owner_module = command.get("owner_module", "")
    metadata = command.get("metadata", {})
    if metadata.get("registry_phase") == "handler-migrated-incremental":
        return False
    return owner_module == "src/devpilot_core/cli.py" or command.get("legacy_cli_owned") is True


def _score_command(command: dict[str, Any], phase: str, missing_contract: bool, app_service_gap: bool) -> tuple[float, list[str]]:
    risk_weight = {"low": 5.0, "medium": 15.0, "high": 35.0, "critical": 45.0}.get(command.get("risk_level"), 15.0)
    side_effects = command.get("side_effects", [])
    score = risk_weight
    reasons = [f"risk_level={command.get('risk_level')} contributes {risk_weight:.1f} points"]
    side_effect_weight = 0.0
    if side_effects and side_effects != ["none"]:
        side_effect_weight = 8.0 + 4.0 * len(side_effects)
        score += side_effect_weight
        reasons.append(f"side_effects={side_effects} contribute {side_effect_weight:.1f} points")
    if command.get("writes_files"):
        score += 8.0
        reasons.append("writes_files=true adds local mutation/reporting review pressure")
    if command.get("policy_check_required"):
        score += 6.0
        reasons.append("policy_check_required=true adds governance pressure")
    if phase == "legacy":
        score += 18.0
        reasons.append("legacy command remains owned by cli.py")
    elif phase == "registered_only":
        score += 10.0
        reasons.append("command is registered but handler has not migrated yet")
    if app_service_gap:
        score += 10.0
        reasons.append("no explicit ApplicationService/cli_commands boundary yet")
    if missing_contract:
        score += 12.0
        reasons.append("no associated Test Contract Registry entry inferred from recommended_tests")
    return round(score, 2), reasons


def _recommendations_for(command: dict[str, Any], phase: str, missing_contract: bool, app_service_gap: bool) -> list[str]:
    recommendations: list[str] = []
    if command.get("risk_level") in {"high", "critical"}:
        recommendations.append("Prioritize explicit policy metadata, dry-run semantics and command-specific tests before handler migration.")
    if phase == "legacy":
        recommendations.append("Add a declarative descriptor or keep in POST-H-006-E legacy allowlist with explicit owner.")
    if phase == "registered_only":
        recommendations.append("Evaluate migration to cli_commands only after parity tests exist for this command family.")
    if app_service_gap:
        recommendations.append("Review as POST-H-007 ApplicationService boundary candidate.")
    if missing_contract:
        recommendations.append("Associate recommended_tests with Test Contract Registry v1/v2 or create a command-specific contract.")
    if not recommendations:
        recommendations.append("Keep as governed command; monitor for drift in POST-H-006-E no-growth gate.")
    return recommendations


def _summary_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "command_id": record["command_id"],
        "risk_level": record["risk_level"],
        "domain": record["domain"],
        "owner_module": record["owner_module"],
        "ownership_status": record["ownership_status"],
        "hotspot_score": record["hotspot_score"],
    }


def _counter_to_records(counter: Counter[str], key_name: str) -> list[dict[str, Any]]:
    return [{key_name: key, "commands_total": count} for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))]
