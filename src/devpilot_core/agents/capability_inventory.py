from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.schemas import SchemaValidator

POST_H_032_A_CREATED_BY = "POST-H-032-A"
AGENT_CAPABILITY_INVENTORY_COMMAND = "agent capability-inventory"
AGENT_CAPABILITY_INVENTORY_SCHEMA_ID = "SCHEMA-DEVPL-AGENT-CAPABILITY-INVENTORY-V1"
AGENT_CAPABILITY_INVENTORY_CONTRACT = "AgentCapabilityInventory"
AGENT_PROMOTION_CRITERIA_SCHEMA_ID = "SCHEMA-DEVPL-AGENT-PROMOTION-CRITERIA-V1"
AGENT_PROMOTION_CRITERIA_CONTRACT = "AgentPromotionCriteria"
DEFAULT_AGENT_REGISTRY_PATH = Path(".devpilot/miasi/agent_registry.json")
DEFAULT_TOOL_REGISTRY_PATH = Path(".devpilot/miasi/tool_registry.json")
DEFAULT_POLICY_MATRIX_PATH = Path(".devpilot/miasi/policy_matrix.json")
DEFAULT_INVENTORY_PATH = Path(".devpilot/agents/agent_capability_inventory.json")
DEFAULT_PROMOTION_CRITERIA_PATH = Path(".devpilot/agents/agent_promotion_criteria.json")
DEFAULT_INVENTORY_REPORT_JSON = Path("outputs/reports/agent_capability_inventory.json")
DEFAULT_INVENTORY_REPORT_MARKDOWN = Path("outputs/reports/agent_capability_inventory.md")

IMPLEMENTATION_MODULE_BY_AGENT_ID: dict[str, str] = {
    "precode.documentation": "src/devpilot_core/agents/runtime.py",
    "precode.audit": "src/devpilot_core/agents/runtime.py",
    "requirements.agent": "src/devpilot_core/agents/requirements_agent.py",
    "architecture.agent": "src/devpilot_core/agents/architecture_agent.py",
    "security.agent": "src/devpilot_core/agents/security_agent.py",
    "testplanner.agent": "src/devpilot_core/agents/test_planner_agent.py",
    "repo.analysis": "src/devpilot_core/agents/repo_analysis_agent.py",
    "code.review": "src/devpilot_core/agents/code_review_agent.py",
    "patch.review": "src/devpilot_core/agents/patch_review_agent.py",
    "safe.refactor": "src/devpilot_core/agents/safe_refactor_agent.py",
    "release.agent": "src/devpilot_core/agents/release_agent.py",
    "release.assistant": "src/devpilot_core/agents/release_agent.py",
    "operations.agent": "src/devpilot_core/agents/runtime.py",
    "multiagent.coordinator": "src/devpilot_core/multiagent/coordinator.py",
}

TEST_FILES_BY_AGENT_ID: dict[str, list[str]] = {
    "precode.documentation": ["tests/test_agent_runtime.py", "tests/test_agent_runtime_v2.py"],
    "precode.audit": ["tests/test_agent_runtime.py", "tests/test_agent_runtime_v2.py"],
    "requirements.agent": ["tests/test_sdlc_agents.py"],
    "architecture.agent": ["tests/test_sdlc_agents.py"],
    "security.agent": ["tests/test_sdlc_agents.py", "tests/test_prompt_injection_guard.py"],
    "testplanner.agent": ["tests/test_refactor_testplanner_agents.py"],
    "repo.analysis": ["tests/test_repo_analysis_agent.py"],
    "code.review": ["tests/test_review_agents.py"],
    "patch.review": ["tests/test_review_agents.py"],
    "safe.refactor": ["tests/test_refactor_testplanner_agents.py"],
    "release.agent": ["tests/test_release_agent.py"],
    "release.assistant": ["tests/test_release_agent.py"],
    "operations.agent": ["tests/test_sprint_94_documentation.py", "tests/test_sprint_99_documentation.py"],
    "multiagent.coordinator": ["tests/test_multiagent_coordinator.py", "tests/test_multiagent_workflow.py"],
}

RAG_CANDIDATE_AGENT_IDS = {
    "requirements.agent",
    "architecture.agent",
    "security.agent",
    "testplanner.agent",
    "release.assistant",
    "repo.analysis",
    "code.review",
    "patch.review",
}

MEMORY_CANDIDATE_AGENT_IDS = {"requirements.agent", "architecture.agent"}

DETERMINISTIC_PASS_BLOCK_AGENT_IDS = {"precode.audit", "security.agent", "safe.refactor", "release.agent", "release.assistant"}

ALWAYS_FORBIDDEN_TOOLS = [
    "remote.runner.execute",
    "connector.write",
    "plugin.code.execute",
    "filesystem.delete",
    "rollback.execute",
]


@dataclass(frozen=True)
class AgentCapabilityInventoryOptions:
    agent_registry_path: str | Path = DEFAULT_AGENT_REGISTRY_PATH
    tool_registry_path: str | Path = DEFAULT_TOOL_REGISTRY_PATH
    policy_matrix_path: str | Path = DEFAULT_POLICY_MATRIX_PATH
    inventory_path: str | Path = DEFAULT_INVENTORY_PATH
    promotion_criteria_path: str | Path = DEFAULT_PROMOTION_CRITERIA_PATH
    output_json: str | Path = DEFAULT_INVENTORY_REPORT_JSON
    output_markdown: str | Path = DEFAULT_INVENTORY_REPORT_MARKDOWN
    write_report: bool = False


class AgentCapabilityInventoryBuilder:
    """Build and validate the POST-H-032-A governed agent capability inventory.

    The builder is read-only over runtime behavior: it inspects source-controlled
    MIASI registries, implementation paths, test coverage and promotion policy.
    It does not run agents, models, tools, RAG, memory, providers or workflows.
    """

    def __init__(self, root: Path, options: AgentCapabilityInventoryOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or AgentCapabilityInventoryOptions()
        self.agent_registry_path = Path(self.options.agent_registry_path)
        self.tool_registry_path = Path(self.options.tool_registry_path)
        self.policy_matrix_path = Path(self.options.policy_matrix_path)
        self.inventory_path = Path(self.options.inventory_path)
        self.promotion_criteria_path = Path(self.options.promotion_criteria_path)

    def build(self) -> CommandResult:
        findings: list[Finding] = []
        agents_registry = self._load_json(self.agent_registry_path, findings, "AGENT_CAPABILITY_AGENT_REGISTRY_LOAD_ERROR")
        tool_registry = self._load_json(self.tool_registry_path, findings, "AGENT_CAPABILITY_TOOL_REGISTRY_LOAD_ERROR")
        policy_matrix = self._load_json(self.policy_matrix_path, findings, "AGENT_CAPABILITY_POLICY_MATRIX_LOAD_ERROR")
        criteria = self._load_json(self.promotion_criteria_path, findings, "AGENT_PROMOTION_CRITERIA_LOAD_ERROR")

        agent_items = [item for item in agents_registry.get("agents", []) if isinstance(item, dict)]
        tool_items = [item for item in tool_registry.get("tools", []) if isinstance(item, dict)]
        policy_items = [item for item in policy_matrix.get("rules", []) if isinstance(item, dict)]
        tools_by_id = {str(item.get("tool_id")): item for item in tool_items if item.get("tool_id")}
        policies_by_id = {str(item.get("rule_id")): item for item in policy_items if item.get("rule_id")}

        inventory_agents: list[dict[str, Any]] = []
        for raw_agent in agent_items:
            inventory_agents.append(self._build_agent(raw_agent, tools_by_id, policies_by_id, findings))

        criteria_validation = self._validate_criteria(criteria, findings)
        summary = self._summary(inventory_agents, agent_items, tool_items, criteria_validation, findings)
        ok = summary["decision"] == "PASS"
        inventory = {
            "schema_version": "1.0",
            "schema_id": AGENT_CAPABILITY_INVENTORY_SCHEMA_ID,
            "inventory_id": "devpilot-agent-capability-inventory",
            "created_by": POST_H_032_A_CREATED_BY,
            "status": "implemented-initial" if ok else "blocked",
            "generated_at_utc": _now_utc(),
            "source_paths": {
                "agent_registry": _posix(self.agent_registry_path),
                "tool_registry": _posix(self.tool_registry_path),
                "policy_matrix": _posix(self.policy_matrix_path),
                "promotion_criteria": _posix(self.promotion_criteria_path),
            },
            "summary": summary,
            "agents": inventory_agents,
            "promotion_criteria_ref": {
                "path": _posix(self.promotion_criteria_path),
                "schema_id": criteria.get("schema_id"),
                "criteria_id": criteria.get("criteria_id"),
                "available": bool(criteria),
                "schema_valid": criteria_validation["ok"],
            },
            "safety": {
                "local_first": True,
                "read_only": True,
                "dry_run": True,
                "agents_executed": False,
                "tools_executed": False,
                "models_called": False,
                "rag_executed": False,
                "memory_read": False,
                "memory_written": False,
                "network_used": False,
                "external_api_used": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "source_mutations_performed": False,
                "llm_judge_used": False,
            },
            "findings": [finding.to_dict() for finding in findings] or [Finding("AGENT_CAPABILITY_INVENTORY_PASS", "Agent capability inventory passed.", Severity.INFO, metadata=summary).to_dict()],
            "notes": [
                "POST-H-032-A is inventory/promotion governance only; it does not enable new runtime autonomy.",
                "LLM, RAG, memory, tools, MCP and multiagent hardening remain gated by later POST-H-032 micro-sprints.",
                "External APIs, connector write, plugin execution and remote execution remain disabled by default.",
            ],
        }

        schema_result = SchemaValidator(self.root).validate_payload(
            schema=AGENT_CAPABILITY_INVENTORY_CONTRACT,
            payload=inventory,
            instance_label="in-memory-agent-capability-inventory",
        )
        if not schema_result.ok:
            findings.extend(_prefixed_findings(schema_result, "AGENT_CAPABILITY_INVENTORY_SCHEMA"))
            ok = False
            inventory["status"] = "blocked"
            inventory["summary"]["decision"] = "BLOCK"
            inventory["summary"]["schema_valid"] = False
            inventory["summary"]["blocking_findings_total"] = len(_blocking_findings(findings))
            inventory["findings"] = [finding.to_dict() for finding in findings]
        else:
            inventory["summary"]["schema_valid"] = True

        reports: dict[str, str] = {}
        if self.options.write_report:
            reports = self._write_reports(inventory)
            inventory["summary"]["reports_written"] = True
        return CommandResult(
            command=AGENT_CAPABILITY_INVENTORY_COMMAND,
            ok=ok,
            exit_code=ExitCode.PASS if ok else exit_code_for_findings(_blocking_findings(findings), default_ok=False),
            message="Agent capability inventory passed." if ok else "Agent capability inventory has blocking findings.",
            data={"summary": inventory["summary"], "inventory": inventory, "criteria": criteria, "reports": reports},
            findings=findings or [Finding("AGENT_CAPABILITY_INVENTORY_PASS", "Agent capability inventory passed.", Severity.INFO, metadata=inventory["summary"])],
        )

    def _build_agent(self, agent: dict[str, Any], tools_by_id: dict[str, dict[str, Any]], policies_by_id: dict[str, dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        agent_id = str(agent.get("agent_id", "")).strip()
        allowed_tools = [str(item) for item in agent.get("allowed_tools", []) if str(item)]
        policy_rules = [str(item) for item in agent.get("policy_rule_ids", []) if str(item)]
        status = str(agent.get("status", "unknown"))
        implemented = status in {"implemented", "implemented-initial"}
        implementation_module = IMPLEMENTATION_MODULE_BY_AGENT_ID.get(agent_id)
        tests = TEST_FILES_BY_AGENT_ID.get(agent_id, [])
        missing_tools = sorted(tool_id for tool_id in allowed_tools if tool_id not in tools_by_id)
        missing_policies = sorted(rule_id for rule_id in policy_rules if rule_id not in policies_by_id)
        module_exists = bool(implementation_module and (self.root / implementation_module).exists())
        tests_existing = [path for path in tests if (self.root / path).exists()]
        mode = self._primary_mode(agent_id, allowed_tools)
        modes = self._modes(agent_id, allowed_tools, mode)
        tool_contracts = [self._tool_contract(tool_id, tools_by_id.get(tool_id, {})) for tool_id in allowed_tools]
        approval_required_actions = sorted(
            {
                tool_id
                for tool_id in allowed_tools
                if bool(tools_by_id.get(tool_id, {}).get("requires_approval"))
                or str(tools_by_id.get(tool_id, {}).get("risk_level")) in {"high", "critical"}
                and str(tools_by_id.get(tool_id, {}).get("side_effect")) not in {"read", "none"}
            }
        )
        allowed_tool_set = set(allowed_tools)
        forbidden_tools = sorted({tool for tool in ALWAYS_FORBIDDEN_TOOLS if tool not in allowed_tool_set})
        blocking_gaps: list[dict[str, Any]] = []
        if implemented and not agent.get("owner") and not agent.get("name"):
            blocking_gaps.append(_gap("AGENT_OWNER_MISSING", "Implemented agent lacks owner/name metadata.", "owner"))
        if implemented and not agent.get("risk_level"):
            blocking_gaps.append(_gap("AGENT_RISK_LEVEL_MISSING", "Implemented agent lacks risk_level.", "risk_level"))
        if implemented and not module_exists:
            blocking_gaps.append(_gap("AGENT_IMPLEMENTATION_MODULE_MISSING", "Implemented agent module is missing.", implementation_module or "<unknown>"))
        if implemented and not tests_existing:
            blocking_gaps.append(_gap("AGENT_TEST_COVERAGE_MISSING", "Implemented agent has no existing focal tests.", ",".join(tests) or "<unknown>"))
        if allowed_tools and missing_tools:
            blocking_gaps.append(_gap("AGENT_TOOL_ALLOWLIST_UNKNOWN_TOOL", "Agent allowlist references unknown MIASI tools.", ",".join(missing_tools)))
        if missing_policies:
            blocking_gaps.append(_gap("AGENT_POLICY_RULE_UNKNOWN", "Agent references unknown policy rules.", ",".join(missing_policies)))
        if agent.get("external_api_allowed") is True:
            blocking_gaps.append(_gap("AGENT_EXTERNAL_API_DEFAULT_ENABLED", "External API is not allowed by default in POST-H-032-A.", agent_id))
        if agent.get("memory_enabled") is True:
            blocking_gaps.append(_gap("AGENT_MEMORY_DEFAULT_ENABLED", "Agent memory remains disabled until POST-H-032-E ADR/policy.", agent_id))

        for gap in blocking_gaps:
            findings.append(Finding(gap["gap_id"], gap["message"], Severity.BLOCK, path=gap.get("path"), metadata={"agent_id": agent_id}))

        rag_candidate = agent_id in RAG_CANDIDATE_AGENT_IDS
        memory_candidate = agent_id in MEMORY_CANDIDATE_AGENT_IDS
        model_candidate = "agent.model.generate" in allowed_tools
        return {
            "agent_id": agent_id,
            "name": agent.get("name"),
            "implementation_module": implementation_module,
            "implementation_module_exists": module_exists,
            "status": status,
            "risk_level": agent.get("risk_level"),
            "mode": mode,
            "modes": modes,
            "autonomy_level": agent.get("max_autonomy", "A0"),
            "allowed_tools": allowed_tools,
            "forbidden_tools": forbidden_tools,
            "tool_contracts": tool_contracts,
            "policy_rules": policy_rules,
            "approval_required_actions": approval_required_actions,
            "eval_coverage": tests,
            "eval_coverage_existing": tests_existing,
            "observability_events": self._observability_events(agent),
            "rag_enabled": False,
            "rag_candidate": rag_candidate,
            "rag_groundedness_eval_required": rag_candidate,
            "rag_groundedness_eval": "tests/test_post_h_011_rag_groundedness.py" if rag_candidate else None,
            "memory_enabled": False,
            "memory_candidate": memory_candidate,
            "memory_policy_required": memory_candidate,
            "external_api_allowed": False,
            "external_api_default_enabled": False,
            "provider_modes_allowed": ["mock", "local_llm_opt_in"] if model_candidate else ["mock"],
            "llm_enabled_by_default": False,
            "model_calls_allowed_only_when_opt_in": model_candidate,
            "tool_calling_allowed": bool(allowed_tools),
            "tool_calling_dry_run_first": True,
            "source_mutation_allowed": False,
            "source_mutation_requires_approval": True,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "remote_execution_enabled": False,
            "promotion_target": self._promotion_target(agent_id, mode, rag_candidate, memory_candidate, model_candidate),
            "promotion_criteria_refs": self._promotion_criteria_refs(agent_id, rag_candidate, memory_candidate, model_candidate),
            "blocking_gaps": blocking_gaps,
            "implemented_agent": implemented,
            "pass_block_decision_must_remain_deterministic": agent_id in DETERMINISTIC_PASS_BLOCK_AGENT_IDS,
            "notes": self._agent_notes(agent_id, status, rag_candidate, memory_candidate, model_candidate),
        }

    def _tool_contract(self, tool_id: str, tool: dict[str, Any]) -> dict[str, Any]:
        return {
            "tool_id": tool_id,
            "registered": bool(tool),
            "risk_level": tool.get("risk_level"),
            "side_effect": tool.get("side_effect"),
            "requires_approval": bool(tool.get("requires_approval")),
            "dry_run_first_required": str(tool.get("side_effect")) not in {"read", "none"},
            "external_write_enabled": False,
        }

    def _primary_mode(self, agent_id: str, allowed_tools: list[str]) -> str:
        if agent_id == "multiagent.coordinator":
            return "multiagent"
        if agent_id in {"precode.audit", "safe.refactor", "release.agent"}:
            return "deterministic"
        if agent_id == "release.assistant":
            return "rule-based"
        if "agent.model.generate" in allowed_tools:
            return "model-aware"
        if allowed_tools:
            return "tool-calling"
        return "deterministic"

    def _modes(self, agent_id: str, allowed_tools: list[str], primary: str) -> list[str]:
        modes = {primary}
        if allowed_tools:
            modes.add("tool-calling")
        if "agent.model.generate" in allowed_tools:
            modes.add("model-aware")
        if agent_id in RAG_CANDIDATE_AGENT_IDS:
            modes.add("rag-aware")
        if agent_id in MEMORY_CANDIDATE_AGENT_IDS:
            modes.add("memory-aware")
        if agent_id == "multiagent.coordinator":
            modes.add("multiagent")
        if primary in {"deterministic", "rule-based"}:
            modes.add(primary)
        order = ["deterministic", "rule-based", "model-aware", "rag-aware", "memory-aware", "tool-calling", "multiagent"]
        return [item for item in order if item in modes]

    def _promotion_target(self, agent_id: str, mode: str, rag_candidate: bool, memory_candidate: bool, model_candidate: bool) -> str:
        if agent_id in DETERMINISTIC_PASS_BLOCK_AGENT_IDS:
            return "stay-deterministic-for-pass-block; advisory-only-model-use"
        if agent_id == "multiagent.coordinator":
            return "handoff-hardening-before-autonomy"
        targets: list[str] = []
        if model_candidate:
            targets.append("local-llm-opt-in-hardening")
        if rag_candidate:
            targets.append("rag-aware-with-citations")
        if memory_candidate:
            targets.append("memory-opt-in-after-adr")
        return "+".join(targets) if targets else f"maintain-{mode}"

    def _promotion_criteria_refs(self, agent_id: str, rag_candidate: bool, memory_candidate: bool, model_candidate: bool) -> list[str]:
        refs = ["baseline-governed-agent"]
        if model_candidate:
            refs.append("model-aware-local-opt-in")
        if rag_candidate:
            refs.append("rag-aware-grounded")
        if memory_candidate:
            refs.append("memory-aware-opt-in")
        if agent_id == "multiagent.coordinator":
            refs.append("multiagent-supervised-handoff")
        return refs

    def _agent_notes(self, agent_id: str, status: str, rag_candidate: bool, memory_candidate: bool, model_candidate: bool) -> list[str]:
        notes = ["Inventory-only classification; runtime behavior is unchanged by POST-H-032-A."]
        if status == "future":
            notes.append("Future agent remains non-promotable until implementation and tests exist.")
        if model_candidate:
            notes.append("Model use is opt-in only; mock remains the safe default.")
        if rag_candidate:
            notes.append("RAG promotion requires citations, freshness and groundedness negative tests in POST-H-032-D.")
        if memory_candidate:
            notes.append("Memory promotion requires POST-H-032-E ADR/policy; memory remains disabled now.")
        return notes

    def _observability_events(self, agent: dict[str, Any]) -> list[str]:
        if agent.get("observability_required") is not True:
            return []
        return ["agent.run.started", "agent.run.completed", "agent.tool_call.planned", "policy.decision", "agent.finding.emitted"]

    def _validate_criteria(self, criteria: dict[str, Any], findings: list[Finding]) -> dict[str, Any]:
        if not criteria:
            findings.append(Finding("AGENT_PROMOTION_CRITERIA_MISSING", "Agent promotion criteria file is missing or empty.", Severity.BLOCK, path=_posix(self.promotion_criteria_path)))
            return {"ok": False, "schema_valid": False}
        result = SchemaValidator(self.root).validate(schema=AGENT_PROMOTION_CRITERIA_CONTRACT, instance=self.promotion_criteria_path)
        if not result.ok:
            findings.extend(_prefixed_findings(result, "AGENT_PROMOTION_CRITERIA_SCHEMA"))
        no_go = criteria.get("global_no_go_gates", []) if isinstance(criteria.get("global_no_go_gates"), list) else []
        no_go_ids = {str(item.get("gate_id")) for item in no_go if isinstance(item, dict)}
        required = {"external-api-disabled-by-default", "memory-disabled-by-default", "no-source-mutation-without-approval", "no-remote-connector-plugin-execution"}
        missing = sorted(required - no_go_ids)
        for gate_id in missing:
            findings.append(Finding("AGENT_PROMOTION_CRITERIA_NO_GO_MISSING", f"Required promotion no-go gate is missing: {gate_id}", Severity.BLOCK, path=_posix(self.promotion_criteria_path), metadata={"gate_id": gate_id}))
        return {"ok": result.ok and not missing, "schema_valid": result.ok, "missing_no_go_gates": missing}

    def _summary(self, agents: list[dict[str, Any]], raw_agents: list[dict[str, Any]], tools: list[dict[str, Any]], criteria_validation: dict[str, Any], findings: list[Finding]) -> dict[str, Any]:
        blocking = _blocking_findings(findings)
        implemented = [agent for agent in agents if agent.get("implemented_agent")]
        return {
            "created_by": POST_H_032_A_CREATED_BY,
            "status": "implemented-initial" if not blocking else "blocked",
            "decision": "PASS" if not blocking else "BLOCK",
            "agents_total": len(agents),
            "registry_agents_total": len(raw_agents),
            "implemented_agents_total": len(implemented),
            "future_agents_total": sum(1 for agent in agents if agent.get("status") == "future"),
            "tools_total": len(tools),
            "agents_with_tools_total": sum(1 for agent in agents if agent.get("allowed_tools")),
            "agents_with_tools_without_allowlist_total": sum(1 for agent in agents if agent.get("tool_calling_allowed") and not agent.get("allowed_tools")),
            "implemented_without_module_total": sum(1 for agent in implemented if not agent.get("implementation_module_exists")),
            "implemented_without_tests_total": sum(1 for agent in implemented if not agent.get("eval_coverage_existing")),
            "model_aware_candidates_total": sum(1 for agent in agents if "model-aware" in agent.get("modes", [])),
            "rag_candidates_total": sum(1 for agent in agents if agent.get("rag_candidate") is True),
            "rag_enabled_total": sum(1 for agent in agents if agent.get("rag_enabled") is True),
            "rag_enabled_without_groundedness_total": sum(1 for agent in agents if agent.get("rag_enabled") is True and not agent.get("rag_groundedness_eval")),
            "memory_candidates_total": sum(1 for agent in agents if agent.get("memory_candidate") is True),
            "memory_enabled_total": sum(1 for agent in agents if agent.get("memory_enabled") is True),
            "external_api_allowed_total": sum(1 for agent in agents if agent.get("external_api_allowed") is True),
            "source_mutation_allowed_total": sum(1 for agent in agents if agent.get("source_mutation_allowed") is True),
            "source_mutation_without_approval_total": 0,
            "remote_execution_enabled_total": sum(1 for agent in agents if agent.get("remote_execution_enabled") is True),
            "connector_write_enabled_total": sum(1 for agent in agents if agent.get("connector_write_enabled") is True),
            "plugin_execution_enabled_total": sum(1 for agent in agents if agent.get("plugin_execution_enabled") is True),
            "promotion_criteria_valid": criteria_validation.get("ok") is True,
            "schema_valid": False,
            "reports_written": False,
            "read_only": True,
            "dry_run": True,
            "agents_executed": False,
            "tools_executed": False,
            "models_called": False,
            "network_used": False,
            "external_api_used": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "source_mutations_performed": False,
            "llm_judge_used": False,
            "blocking_findings_total": len(blocking),
            "findings_total": len(findings),
            "preliminary": True,
        }

    def _load_json(self, path: Path, findings: list[Finding], finding_id: str) -> dict[str, Any]:
        try:
            return json.loads((self.root / path).read_text(encoding="utf-8"))
        except Exception as exc:
            findings.append(Finding(finding_id, f"Could not load {path}: {exc}", Severity.ERROR, path=_posix(path)))
            return {}

    def _write_reports(self, inventory: dict[str, Any]) -> dict[str, str]:
        output_json = _safe_output_path(self.root, self.options.output_json)
        output_markdown = _safe_output_path(self.root, self.options.output_markdown)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_markdown.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(_json_dumps(inventory) + "\n", encoding="utf-8")
        output_markdown.write_text(render_agent_capability_inventory_markdown(inventory), encoding="utf-8")
        return {"json": _relative(output_json, self.root), "markdown": _relative(output_markdown, self.root)}


def render_agent_capability_inventory_markdown(inventory: dict[str, Any]) -> str:
    summary = inventory.get("summary", {})
    lines = [
        "# POST-H-032-A — Agent capability inventory",
        "",
        f"- Decision: `{summary.get('decision')}`",
        f"- Agents total: `{summary.get('agents_total')}`",
        f"- Implemented agents total: `{summary.get('implemented_agents_total')}`",
        f"- RAG candidates total: `{summary.get('rag_candidates_total')}`",
        f"- Memory enabled total: `{summary.get('memory_enabled_total')}`",
        f"- External API allowed total: `{summary.get('external_api_allowed_total')}`",
        f"- Blocking findings total: `{summary.get('blocking_findings_total')}`",
        "",
        "## Safety contract",
        "",
        "POST-H-032-A is read-only/inventory-only. It does not execute agents, call models, run RAG, enable memory, execute tools, call external APIs, enable remote execution, enable connector write or enable plugin execution.",
        "",
        "## Agent summary",
        "",
        "| Agent | Status | Mode | Risk | Promotion target | Blocking gaps |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for agent in inventory.get("agents", []):
        lines.append(
            f"| `{agent.get('agent_id')}` | `{agent.get('status')}` | `{agent.get('mode')}` | `{agent.get('risk_level')}` | `{agent.get('promotion_target')}` | {len(agent.get('blocking_gaps', []))} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "This report classifies current governed agents and promotion criteria. Promotion to LLM/RAG/memory/tool/MCP/multiagent maturity requires later POST-H-032 micro-sprints, negative tests and explicit gates.",
        "",
    ])
    return "\n".join(lines)


def _safe_output_path(root: Path, path: str | Path) -> Path:
    rel = Path(path)
    if rel.is_absolute() or not str(rel).replace("\\", "/").startswith("outputs/"):
        raise ValueError(f"Output path must be relative and under outputs/: {path}")
    resolved = (root / rel).resolve()
    if root.resolve() not in resolved.parents and resolved != root.resolve():
        raise ValueError(f"Output path escapes workspace: {path}")
    return resolved


def _prefixed_findings(result: CommandResult, prefix: str) -> list[Finding]:
    return [
        Finding(
            id=f"{prefix}_{finding.id}",
            message=finding.message,
            severity=finding.severity,
            path=finding.path,
            metadata=finding.metadata,
        )
        for finding in result.findings
    ]


def _blocking_findings(findings: list[Finding]) -> list[Finding]:
    return [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]


def _gap(gap_id: str, message: str, path: str) -> dict[str, Any]:
    return {"gap_id": gap_id, "message": message, "severity": "block", "path": path}


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _posix(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
