from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.cli_registry.registry import DeclarativeCliRegistryBuilder

from .boundary import (
    APPLICATION_SERVICE_BOUNDARY_REPORT_ID,
    APPLICATION_SERVICE_BOUNDARY_REPORT_SCHEMA_ID,
    POST_H_007_A_CREATED_BY,
    ApplicationBoundaryBypass,
    ApplicationBoundaryOperation,
)


@dataclass(frozen=True)
class ApplicationServiceBoundaryReportOptions:
    """Options for the POST-H-007-A read-only boundary inventory."""

    write_report: bool = False
    output_json: Path = Path("outputs/reports/application_service_boundary_report.json")
    output_markdown: Path = Path("outputs/reports/application_service_boundary_report.md")


class ApplicationServiceBoundaryReportBuilder:
    """Build a static ApplicationService boundary and bypass report.

    The builder is intentionally static/read-only: it parses Python/TypeScript
    source files and the existing CLI registry, but it does not execute public
    commands, import API routers, call domain engines, enable remote execution or
    mutate source files. Optional report writing is limited to outputs/reports.
    """

    def __init__(self, root: Path, options: ApplicationServiceBoundaryReportOptions | None = None) -> None:
        self.root = Path(root)
        self.options = options or ApplicationServiceBoundaryReportOptions()
        self.application_dir = self.root / "src" / "devpilot_core" / "application"
        self.api_router_dir = self.root / "src" / "devpilot_core" / "interfaces" / "api" / "routers"
        self.ui_dir = self.root / "ui"
        self.cli_path = self.root / "src" / "devpilot_core" / "cli.py"

    def run(self) -> CommandResult:
        payload = self.build_report()
        reports: dict[str, str] = {}
        if self.options.write_report:
            payload["summary"]["reports_written"] = True
            payload["summary"]["output_json"] = str(self.options.output_json).replace("\\", "/")
            payload["summary"]["output_markdown"] = str(self.options.output_markdown).replace("\\", "/")
            reports = self._write_reports(payload)
            payload["summary"]["output_json"] = reports["json"]
            payload["summary"]["output_markdown"] = reports["markdown"]
        findings = [
            Finding(
                id="APPLICATION_SERVICE_BOUNDARY_INVENTORY_PASS",
                message="ApplicationService boundary inventory and bypass report was generated read-only.",
                severity=Severity.INFO,
                metadata={
                    "direct_core_bypass_total": payload["summary"]["direct_core_bypass_total"],
                    "api_routes_total": payload["summary"]["api_routes_total"],
                },
            )
        ]
        if payload["summary"]["critical_bypass_total"]:
            findings.append(
                Finding(
                    id="APPLICATION_SERVICE_BOUNDARY_CRITICAL_BYPASS_ADVISORY",
                    message="Critical CLI bypasses remain as advisory POST-H-007-A inventory items.",
                    severity=Severity.WARNING,
                    metadata={"critical_bypass_total": payload["summary"]["critical_bypass_total"]},
                )
            )
        data: dict[str, Any] = {"summary": payload["summary"], "report": payload}
        if reports:
            data["reports"] = reports
        return CommandResult(
            command="application boundary report",
            ok=True,
            exit_code=ExitCode.PASS,
            message="ApplicationService boundary report passed.",
            data=data,
            findings=findings,
        )

    def build_report(self) -> dict[str, Any]:
        generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        facade_methods = self._extract_class_methods(self.application_dir / "services.py", "ApplicationService")
        service_methods = self._extract_domain_service_methods()
        dispatch_operations = self._extract_dispatch_operations(self.application_dir / "services.py")
        api_routes = self._extract_api_routes()
        ui_api_calls = self._extract_ui_api_calls()
        cli_inventory = self._build_cli_inventory(dispatch_operations, api_routes, ui_api_calls)
        operations = self._build_operations(dispatch_operations, api_routes, ui_api_calls, cli_inventory)
        bypasses = [ApplicationBoundaryBypass(**item) for item in cli_inventory["bypasses"]]

        api_routes_bound = sum(1 for route in api_routes if route["application_service_bound"])
        cli_bound_total = sum(1 for item in cli_inventory["commands"] if item["application_service_boundary_present"])
        direct_core_bypass_total = len(bypasses)
        high_or_critical = [item for item in bypasses if item.risk_level in {"high", "critical"}]
        critical = [item for item in bypasses if item.risk_level == "critical"]
        operation_ids = sorted({item.operation_id for item in operations})
        summary = {
            "report_id": APPLICATION_SERVICE_BOUNDARY_REPORT_ID,
            "schema_version": "1.0",
            "schema_id": APPLICATION_SERVICE_BOUNDARY_REPORT_SCHEMA_ID,
            "created_by": POST_H_007_A_CREATED_BY,
            "status": "implemented-initial",
            "generated_at_utc": generated_at,
            "operations_total": len(operation_ids),
            "application_service_methods_total": len(facade_methods),
            "domain_services_total": len(service_methods),
            "domain_service_methods_total": sum(len(item["methods"]) for item in service_methods),
            "cli_commands_total": len(cli_inventory["commands"]),
            "cli_bound_total": cli_bound_total,
            "cli_unbound_total": len(cli_inventory["commands"]) - cli_bound_total,
            "api_routes_total": len(api_routes),
            "api_bound_total": api_routes_bound,
            "api_unbound_total": len(api_routes) - api_routes_bound,
            "ui_bound_total": len(ui_api_calls),
            "direct_core_bypass_total": direct_core_bypass_total,
            "high_or_critical_bypass_total": len(high_or_critical),
            "critical_bypass_total": len(critical),
            "reports_written": False,
            "output_json": None,
            "output_markdown": None,
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "runtime_routes_added": False,
            "runtime_behavior_changed": False,
            "preliminary": True,
        }
        return {
            "schema_version": "1.0",
            "schema_id": APPLICATION_SERVICE_BOUNDARY_REPORT_SCHEMA_ID,
            "report_id": APPLICATION_SERVICE_BOUNDARY_REPORT_ID,
            "created_by": POST_H_007_A_CREATED_BY,
            "summary": summary,
            "application_service": {
                "facade_class": "ApplicationService",
                "facade_methods": facade_methods,
                "dispatch_operations": dispatch_operations,
                "domain_services": service_methods,
            },
            "operations": [operation.to_dict() for operation in operations],
            "interfaces": {
                "cli": cli_inventory,
                "api": {"routes": api_routes},
                "ui": {"api_calls": ui_api_calls},
            },
            "bypasses": [item.to_dict() for item in bypasses],
            "top_boundary_candidates": [item.to_dict() for item in sorted(bypasses, key=_bypass_sort_key)[:25]],
            "safety": {
                "read_only": True,
                "dry_run": True,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "dynamic_handler_loading_enabled": False,
                "runtime_behavior_changed": False,
                "preliminary": True,
            },
            "recommendations": [
                "Prioritize critical/high CLI bypasses before normalizing low-risk command families.",
                "Keep POST-H-007-A advisory: do not correct all bypasses in the inventory sprint.",
                "Promote selected operation rows into the POST-H-007-B ApplicationOperationCatalog schema.",
                "Preserve CLI compatibility while API/UI continue to consume ApplicationService dispatch operations.",
            ],
            "notes": [
                "POST-H-007-A is a static inventory and report only; it does not modify runtime routing.",
                "A direct_core_bypass means the public CLI command does not have an explicit ApplicationService operation mapping yet.",
                "Some bypasses are acceptable until incremental normalization is implemented by POST-H-007-B/C/D/E.",
            ],
        }

    def _write_reports(self, payload: dict[str, Any]) -> dict[str, str]:
        json_path = self.root / self.options.output_json
        markdown_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(render_application_service_boundary_markdown(payload), encoding="utf-8")
        return {"json": _rel(json_path, self.root), "markdown": _rel(markdown_path, self.root)}

    def _extract_class_methods(self, path: Path, class_name: str) -> list[str]:
        if not path.exists():
            return []
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return sorted(item.name for item in node.body if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"))
        return []

    def _extract_domain_service_methods(self) -> list[dict[str, Any]]:
        services: list[dict[str, Any]] = []
        for path in sorted(self.application_dir.glob("*_service.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, ast.ClassDef) and node.name.endswith("ApplicationService"):
                    methods = sorted(item.name for item in node.body if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"))
                    services.append({"service": node.name, "path": _rel(path, self.root), "methods": methods, "methods_total": len(methods)})
        return services

    def _extract_dispatch_operations(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        tree = ast.parse(path.read_text(encoding="utf-8"))
        operations: list[dict[str, Any]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_operation_dispatch":
                for inner in ast.walk(node):
                    if isinstance(inner, ast.Dict):
                        for key, value in zip(inner.keys, inner.values):
                            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                                operation_id = key.value
                                service_method = _find_service_method_name(value)
                                operations.append(
                                    {
                                        "operation_id": operation_id,
                                        "domain": operation_id.split(".", 1)[0],
                                        "service_method": service_method,
                                        "request_contract": "ApplicationRequest",
                                        "response_contract": "ApplicationResponse",
                                        "source": _rel(path, self.root),
                                    }
                                )
                        break
        return sorted(operations, key=lambda item: item["operation_id"])

    def _extract_api_routes(self) -> list[dict[str, Any]]:
        routes: list[dict[str, Any]] = []
        if not self.api_router_dir.exists():
            return routes
        for path in sorted(self.api_router_dir.glob("*.py")):
            if path.name == "__init__.py":
                continue
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text)
            for node in tree.body:
                if not isinstance(node, ast.FunctionDef):
                    continue
                method = None
                route_path = None
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                        if isinstance(decorator.func.value, ast.Name) and decorator.func.value.id == "router":
                            method = decorator.func.attr.upper()
                            if decorator.args and isinstance(decorator.args[0], ast.Constant) and isinstance(decorator.args[0].value, str):
                                route_path = decorator.args[0].value
                if not method or not route_path:
                    continue
                operation = _find_literal_keyword_call(node, "dispatch_application_request", "operation")
                routes.append(
                    {
                        "route_id": f"{method} {route_path}",
                        "method": method,
                        "path": route_path,
                        "function": node.name,
                        "module": _rel(path, self.root),
                        "operation": operation,
                        "application_service_bound": "dispatch_application_request" in text and "ApplicationService" in text,
                        "direct_core_imports": _non_application_devpilot_imports(tree),
                    }
                )
        return sorted(routes, key=lambda item: item["route_id"])

    def _extract_ui_api_calls(self) -> list[dict[str, Any]]:
        calls: list[dict[str, Any]] = []
        if not self.ui_dir.exists():
            return calls
        absolute_pattern = re.compile(r"/api/v1/[A-Za-z0-9_./{}?=&${}:-]+")
        relative_pattern = re.compile(r"[\'\"](/(?:workspace|application|standards|miasi|validation|reports|traces|metrics|approvals|actions|settings)[A-Za-z0-9_./{}?=&${}:-]*)[\'\"]")
        for path in sorted(self.ui_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".js", ".jsx", ".ts", ".tsx", ".html", ".md"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            matches = set(absolute_pattern.findall(text))
            matches.update(f"/api/v1{item}" for item in relative_pattern.findall(text))
            for match in sorted(matches):
                calls.append({"path": match, "source": _rel(path, self.root), "application_service_via_api": True})
        return calls

    def _build_cli_inventory(self, dispatch_operations: list[dict[str, Any]], api_routes: list[dict[str, Any]], ui_api_calls: list[dict[str, Any]]) -> dict[str, Any]:
        registry = DeclarativeCliRegistryBuilder(self.root).build_registry()
        dispatch_ids = {item["operation_id"] for item in dispatch_operations}
        api_operations = {item.get("operation") for item in api_routes if item.get("operation")}
        ui_paths = {item["path"] for item in ui_api_calls}
        function_nodes = self._top_level_functions(self.cli_path)
        commands: list[dict[str, Any]] = []
        bypasses: list[dict[str, Any]] = []
        for group in registry.groups:
            for command in group.commands:
                handler_body = function_nodes.get(command.handler)
                handler_uses_application_service = _node_contains_name(handler_body, "ApplicationService") if handler_body else False
                operation_candidates = _operation_candidates_for_command(command.command_id)
                mapped_operation = next((candidate for candidate in operation_candidates if candidate in dispatch_ids), None)
                boundary_present = bool(handler_uses_application_service or mapped_operation or command.command_id in dispatch_ids or command.command_id in api_operations)
                is_bypass = bool(command.owner_module.endswith("cli.py") and not boundary_present)
                item = {
                    "command_id": command.command_id,
                    "public_invocation": command.public_invocation,
                    "domain": command.domain,
                    "owner_module": command.owner_module,
                    "handler": command.handler,
                    "risk_level": command.risk_level.value,
                    "side_effects": [effect.value for effect in command.side_effects],
                    "writes_files": command.writes_files,
                    "policy_check_required": command.policy_check_required,
                    "application_service_boundary_present": boundary_present,
                    "mapped_operation": mapped_operation,
                    "handler_uses_application_service": handler_uses_application_service,
                    "direct_core_bypass": is_bypass,
                    "registry_phase": command.metadata.get("registry_phase"),
                    "registration_status": command.metadata.get("registration_status"),
                    "legacy_cli_owned": command.legacy_cli_owned,
                    "ui_api_paths_detected_total": len(ui_paths),
                }
                commands.append(item)
                if is_bypass:
                    bypasses.append(
                        {
                            "interface": "cli",
                            "identifier": command.command_id,
                            "domain": command.domain,
                            "owner_module": command.owner_module,
                            "risk_level": command.risk_level.value,
                            "side_effects": [effect.value for effect in command.side_effects],
                            "writes_files": command.writes_files,
                            "policy_required": command.policy_check_required,
                            "reason": "Command remains public through cli.py without an explicit ApplicationService operation mapping.",
                            "recommendation": "Create an ApplicationOperationDescriptor and route the interface through ApplicationService in a later POST-H-007 micro-sprint.",
                        }
                    )
        return {"commands_total": len(commands), "commands": sorted(commands, key=lambda item: item["command_id"]), "bypasses": sorted(bypasses, key=lambda item: item["identifier"])}

    def _top_level_functions(self, path: Path) -> dict[str, ast.FunctionDef]:
        if not path.exists():
            return {}
        tree = ast.parse(path.read_text(encoding="utf-8"))
        return {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}

    def _build_operations(self, dispatch_operations: list[dict[str, Any]], api_routes: list[dict[str, Any]], ui_api_calls: list[dict[str, Any]], cli_inventory: dict[str, Any]) -> list[ApplicationBoundaryOperation]:
        cli_by_operation: dict[str, list[str]] = {}
        for command in cli_inventory["commands"]:
            operation_id = command.get("mapped_operation") or (command["command_id"] if command["command_id"] in {item["operation_id"] for item in dispatch_operations} else None)
            if operation_id:
                cli_by_operation.setdefault(operation_id, []).append(command["public_invocation"])
        routes_by_operation: dict[str, list[str]] = {}
        for route in api_routes:
            operation = route.get("operation")
            if operation:
                routes_by_operation.setdefault(operation, []).append(route["route_id"])
        ui_by_route: dict[str, list[str]] = {}
        for call in ui_api_calls:
            ui_by_route.setdefault(call["path"], []).append(call["source"])

        rows: list[ApplicationBoundaryOperation] = []
        for item in dispatch_operations:
            operation_id = item["operation_id"]
            api_route_ids = routes_by_operation.get(operation_id, [])
            ui_surfaces = sorted({source for route in api_routes for source in ui_by_route.get(route["path"], []) if route.get("operation") == operation_id})
            rows.append(
                ApplicationBoundaryOperation(
                    operation_id=operation_id,
                    domain=item["domain"],
                    service=_service_for_operation(operation_id),
                    method=item.get("service_method") or operation_id.split(".")[-1],
                    cli_commands=sorted(cli_by_operation.get(operation_id, [])),
                    api_routes=sorted(api_route_ids),
                    ui_surfaces=ui_surfaces,
                    policy_required=_operation_policy_required(operation_id),
                    dry_run_default=_operation_dry_run_default(operation_id),
                    writes_files=_operation_writes_files(operation_id),
                    risk_level=_operation_risk(operation_id),
                    direct_core_bypass=False,
                )
            )
        return sorted(rows, key=lambda item: item.operation_id)


def render_application_service_boundary_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# POST-H-007-A — ApplicationService boundary report",
        "",
        "Estado: `implemented-initial`",
        "",
        "## Summary",
        "",
        f"- Operations total: `{summary['operations_total']}`",
        f"- CLI commands total: `{summary['cli_commands_total']}`",
        f"- CLI bound total: `{summary['cli_bound_total']}`",
        f"- Direct core bypass total: `{summary['direct_core_bypass_total']}`",
        f"- High/Critical bypass total: `{summary['high_or_critical_bypass_total']}`",
        f"- API routes total: `{summary['api_routes_total']}`",
        f"- API bound total: `{summary['api_bound_total']}`",
        f"- UI API calls total: `{summary['ui_bound_total']}`",
        "",
        "## Top boundary candidates",
        "",
        "| Interface | Identifier | Risk | Writes | Policy | Recommendation |",
        "|---|---|---:|---:|---:|---|",
    ]
    for item in payload.get("top_boundary_candidates", [])[:25]:
        lines.append(
            f"| {item['interface']} | `{item['identifier']}` | {item['risk_level']} | {item['writes_files']} | {item['policy_required']} | {item['recommendation']} |"
        )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "```text",
            "read_only=true",
            "network_used=false",
            "external_api_used=false",
            "source_mutations_performed=false",
            "remote_execution_enabled=false",
            "connector_write_enabled=false",
            "plugin_execution_enabled=false",
            "runtime_behavior_changed=false",
            "```",
            "",
            "## Notes",
            "",
        ]
    )
    for note in payload.get("notes", []):
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _find_service_method_name(node: ast.AST) -> str | None:
    for item in ast.walk(node):
        if isinstance(item, ast.Attribute):
            return item.attr
    return None


def _find_literal_keyword_call(node: ast.AST, call_name: str, keyword_name: str) -> str | None:
    for item in ast.walk(node):
        if isinstance(item, ast.Call):
            func = item.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
            if name != call_name:
                continue
            for keyword in item.keywords:
                if keyword.arg == keyword_name and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                    return keyword.value.value
    return None


def _non_application_devpilot_imports(tree: ast.AST) -> list[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("devpilot_core"):
            if not node.module.startswith("devpilot_core.application") and "interfaces.api" not in node.module:
                imports.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("devpilot_core") and not alias.name.startswith("devpilot_core.application"):
                    imports.add(alias.name)
    return sorted(imports)


def _node_contains_name(node: ast.AST | None, name: str) -> bool:
    if node is None:
        return False
    for item in ast.walk(node):
        if isinstance(item, ast.Name) and item.id == name:
            return True
        if isinstance(item, ast.Attribute) and item.attr == name:
            return True
    return False


def _operation_candidates_for_command(command_id: str) -> list[str]:
    candidates = [command_id]
    aliases = {
        "repo-inventory": "repo.inventory",
        "code-review": "review.code",
        "refactor-plan": "refactor.plan",
        "metrics.summary": "observability.metrics_summary",
        "trace.report": "observability.trace_report",
        "trace.inspect": "observability.trace_inspect",
        "miasi.validate": "miasi.validate",
        "standards.status": "standards.status",
        "app.contract": "app.contract",
        "history.list": "history.runs",
    }
    if command_id in aliases:
        candidates.append(aliases[command_id])
    if command_id.startswith("approval."):
        candidates.append("approvals." + command_id.split(".", 1)[1])
    if command_id.startswith("settings."):
        candidates.append(command_id.replace("settings.provider", "settings.providers"))
    return candidates


def _service_for_operation(operation_id: str) -> str:
    prefix = operation_id.split(".", 1)[0]
    return {
        "workspace": "WorkspaceApplicationService",
        "validation": "ValidationApplicationService",
        "miasi": "MiasiApplicationService",
        "standards": "ValidationApplicationService",
        "repo": "RepoApplicationService",
        "review": "ReviewApplicationService",
        "refactor": "RefactorApplicationService",
        "model": "ModelApplicationService",
        "observability": "ObservabilityApplicationService",
        "history": "HistoryApplicationService",
        "reports": "ReportsApplicationService",
        "approvals": "ApprovalApplicationService",
        "settings": "SettingsApplicationService",
        "maturity": "MaturityApplicationService",
        "operator": "OperatorDashboardApplicationService",
        "ui": "ApplicationService",
        "app": "ApplicationService",
    }.get(prefix, "ApplicationService")


def _operation_policy_required(operation_id: str) -> bool:
    return operation_id.startswith("approvals.") or operation_id.startswith("settings.providers.plan") or operation_id.startswith("ui.actions")


def _operation_writes_files(operation_id: str) -> bool:
    return operation_id in {"approvals.request", "approvals.approve", "approvals.deny", "settings.providers.plan"}


def _operation_dry_run_default(operation_id: str) -> bool:
    return not _operation_writes_files(operation_id) or operation_id.startswith("settings.providers.plan")


def _operation_risk(operation_id: str) -> str:
    if operation_id.startswith(("approvals.", "ui.actions", "settings.providers.plan")):
        return "high"
    if operation_id.startswith(("model.", "repo.", "review.", "refactor.")):
        return "medium"
    return "low"


def _bypass_sort_key(item: ApplicationBoundaryBypass) -> tuple[int, int, str]:
    risk_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(item.risk_level, 4)
    side_effect_rank = 0 if (item.writes_files or item.policy_required or "execute-subprocess" in item.side_effects) else 1
    return (risk_rank, side_effect_rank, item.identifier)
