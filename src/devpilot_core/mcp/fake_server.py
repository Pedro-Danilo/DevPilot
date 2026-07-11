from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class FakeMcpRequest:
    """Synthetic local MCP request used by POST-H-032-G tests.

    The fake server intentionally avoids sockets, stdio transports, HTTP,
    subprocesses, real MCP SDK dependencies and tool execution. It models only
    protocol-shaped request/response contracts so DevPilot can validate threat
    model, permission rules and auditability before any real MCP integration.
    """

    request_id: str
    method: str
    params: dict[str, Any]


class LocalFakeMcpServer:
    """In-process fake MCP server for deterministic contract evaluation.

    Supported methods are a conservative subset: initialize, tools/list,
    resources/list, prompts/list and tools/call. Tool calls are never executed;
    they return planned/blocked contract responses derived from the supplied
    MCP tool mapping and permission model.
    """

    def __init__(self, *, server_id: str, tools: list[dict[str, Any]], resources: list[dict[str, Any]], prompts: list[dict[str, Any]]) -> None:
        self.server_id = server_id
        self.tools = list(tools)
        self.resources = list(resources)
        self.prompts = list(prompts)
        self.audit_events: list[dict[str, Any]] = []

    def handle(self, request: FakeMcpRequest) -> dict[str, Any]:
        event = {
            "event_id": f"mcp-audit-{len(self.audit_events) + 1:03d}",
            "request_id": request.request_id,
            "method": request.method,
            "generated_at_utc": _utc_now(),
            "local_fake_server": True,
            "network_used": False,
            "external_api_used": False,
            "tool_executed": False,
        }
        if request.method == "initialize":
            response = {
                "request_id": request.request_id,
                "ok": True,
                "method": request.method,
                "server": {
                    "server_id": self.server_id,
                    "name": "devpilot-local-fake-mcp-server",
                    "protocol": "mcp-contract-fake-local",
                    "real_mcp_enabled": False,
                },
                "capabilities": {"tools": True, "resources": True, "prompts": True, "sampling": False},
            }
        elif request.method == "tools/list":
            response = {"request_id": request.request_id, "ok": True, "method": request.method, "tools": self.tools}
        elif request.method == "resources/list":
            response = {"request_id": request.request_id, "ok": True, "method": request.method, "resources": self.resources}
        elif request.method == "prompts/list":
            response = {"request_id": request.request_id, "ok": True, "method": request.method, "prompts": self.prompts}
        elif request.method == "tools/call":
            tool_name = str(request.params.get("name") or request.params.get("tool_name") or "")
            tool = next((item for item in self.tools if item.get("name") == tool_name), None)
            if tool is None:
                response = {
                    "request_id": request.request_id,
                    "ok": False,
                    "method": request.method,
                    "error": "tool_not_registered",
                    "tool_executed": False,
                    "policy_decision": "block",
                }
            else:
                requires_approval = bool(tool.get("requires_approval"))
                action = "blocked_requires_approval" if requires_approval else "planned_dry_run"
                response = {
                    "request_id": request.request_id,
                    "ok": not requires_approval,
                    "method": request.method,
                    "tool": tool,
                    "result": {
                        "action": action,
                        "dry_run": True,
                        "tool_executed": False,
                        "payload_redacted": True,
                    },
                    "policy_decision": "requires_approval" if requires_approval else "allow",
                    "approval_required": requires_approval,
                }
        else:
            response = {
                "request_id": request.request_id,
                "ok": False,
                "method": request.method,
                "error": "method_not_allowed",
                "tool_executed": False,
                "policy_decision": "block",
            }
        event["ok"] = bool(response.get("ok"))
        event["policy_decision"] = str(response.get("policy_decision") or "allow")
        self.audit_events.append(event)
        return response


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
