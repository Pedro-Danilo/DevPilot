from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.miasi.registry import (
    AGENT_REGISTRY_FILE,
    POLICY_MATRIX_FILE,
    TOOL_REGISTRY_FILE,
    AgentSpec,
    MiasiRegistryBundle,
    MiasiRegistryValidator,
    PolicyRule,
    ToolSpec,
)
from devpilot_core.miasi.semantic_models import MiasiSemanticReport, SemanticFinding, SemanticRuleResult
from devpilot_core.miasi.semantic_rules import SemanticRuleStatus, SemanticSeverity, normalize_semantic_severity
from devpilot_core.schemas import SchemaValidator

SENSITIVE_SIDE_EFFECTS = {"controlled_write", "controlled_execution", "network_cost", "optional_write"}
EXECUTION_SIDE_EFFECTS = {"controlled_execution", "network_cost"}
SAFE_GATED_CONTROLLED_WRITE_TOKENS = (
    "sandbox",
    "dry_run",
    "dry-run",
    "rollback",
    "registry",
    "local",
    "pathguard",
    "secretguard",
    "policyengine",
)
NO_GO_ACTION_MARKERS = {
    "remote": ("execute_remote", "cloud_control_plane", "remote_authentication"),
    "plugin": ("execute_plugin_code", "plugin_execute", "execute_plugin"),
    "connector": ("connector_call_execute_mode", "connector_write", "write_connector"),
}

APPROVAL_GATE_TOKENS = ("approval", "approvalpolicychecker", "approvalservice", "human", "actor")
RBAC_GATE_TOKENS = ("rbac", "identityregistry", "role", "actor")
SECRET_GUARD_TOKENS = ("secretguard", "secret", "redacted", "no raw secrets", "norawsecrets")
NETWORK_GUARD_TOKENS = ("costguard", "noexternalapi", "no external api", "nonetwork", "no network", "localhostonly")
LOCAL_GUARD_TOKENS = ("pathguard", "policyengine", "sandbox", "dry_run", "dry-run", "local", "checksum", "rollback", "registry")
IDENTITY_REGISTRY_FILE = Path(".devpilot") / "identity" / "identity_registry.json"
TEST_CONTRACT_REGISTRY_V1_FILE = Path(".devpilot") / "testing" / "test_contract_registry.json"
TEST_CONTRACT_REGISTRY_V2_FILE = Path(".devpilot") / "testing" / "test_contract_registry_v2.json"

REQUIRED_EVAL_FIXTURES: tuple[dict[str, Any], ...] = (
    {
        "path": Path("evals") / "fixtures" / "red_team_agentic_eval_cases.json",
        "suite_id": "red-team",
        "required_markers": ("prompt-injection", "secret", "connector"),
    },
    {
        "path": Path("evals") / "fixtures" / "advanced_agentic_eval_cases.json",
        "suite_id": "advanced-agentic",
        "required_markers": ("rag", "mcp", "multiagent"),
    },
    {
        "path": Path("evals") / "fixtures" / "plugin_ecosystem_eval_cases.json",
        "suite_id": "plugin-ecosystem",
        "required_markers": ("plugin",),
    },
    {
        "path": Path("evals") / "fixtures" / "identity_rbac_eval_cases.json",
        "suite_id": "identity-rbac",
        "required_markers": ("rbac",),
    },
    {
        "path": Path("evals") / "fixtures" / "remote_enterprise_eval_cases.json",
        "suite_id": "remote-enterprise",
        "required_markers": ("remote",),
    },
)


class MiasiSemanticReportBuilder:
    """Build preliminary Policy/MIASI semantic report payloads.

    POST-H-004-A does not execute semantic rules. It provides the stable report
    contract and a deterministic empty-report builder used by tests, docs and
    future rule implementations.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()

    def source_paths(self) -> dict[str, str]:
        return {
            "agent_registry": AGENT_REGISTRY_FILE.as_posix(),
            "tool_registry": TOOL_REGISTRY_FILE.as_posix(),
            "policy_matrix": POLICY_MATRIX_FILE.as_posix(),
            "semantic_report_schema": "docs/schemas/miasi_semantic_report.schema.json",
        }

    def build_empty_report(self, *, report_id: str = "miasi-semantic-post-h-004-a") -> MiasiSemanticReport:
        return MiasiSemanticReport(
            report_id=report_id,
            created_by="POST-H-004-A",
            status="schema-only",
            source_paths=self.source_paths(),
            no_go_gates=(
                "remote.execute must remain blocked",
                "plugin.execute must remain blocked until sandboxed",
                "connector.write must remain blocked unless future ADR/sandbox/test-contract gates approve it",
            ),
            notes=(
                "POST-H-004-A defines the semantic report schema and model only; semantic rules start in POST-H-004-B.",
                "This report builder does not execute agents, tools, remote runners, plugins, connectors, network calls or tests.",
            ),
        )

    def build_empty_payload(self, *, report_id: str = "miasi-semantic-post-h-004-a") -> dict[str, Any]:
        return self.build_empty_report(report_id=report_id).to_dict()


class MiasiSemanticValidator:
    """Validate semantic consistency across MIASI agents, tools and policy rules.

    POST-H-004-C remains read-only and non-executing. It loads the
    existing MIASI declarative bundle, evaluates semantic rules and emits a
    schema-valid ``MiasiSemanticReport``. It does not execute tools, agents,
    tests, subprocesses, remote runners, plugins, connectors, network calls or
    external APIs.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.builder = MiasiSemanticReportBuilder(self.root)

    def validate(self) -> CommandResult:
        bundle, load_findings = MiasiRegistryValidator(self.root).load_bundle()
        rule_results: list[SemanticRuleResult] = []
        schema_result: CommandResult | None = None

        if bundle is None:
            rule_results.append(self._load_failure_rule(load_findings))
            report = self._report(rule_results=rule_results, status="blocked")
            return self._command_result(report=report, schema_result=None)

        rule_results.extend(
            [
                self._validate_agent_tool_references(bundle),
                self._validate_policy_references(bundle),
                self._validate_status_semantics(bundle),
                self._validate_sensitive_tool_approval(bundle),
                self._validate_approval_metadata(bundle),
                self._validate_rbac_requirements(bundle),
                self._validate_security_guards(bundle),
                self._validate_no_go_security_guards(bundle),
                self._validate_observability_requirements(bundle),
                self._validate_eval_fixture_coverage(bundle),
                self._validate_test_contract_coverage(bundle),
                self._validate_policy_contradictions(bundle),
                self._validate_no_go_policy_rules(bundle),
            ]
        )
        status = self._report_status(rule_results)
        report = self._report(rule_results=rule_results, status=status)
        schema_result = SchemaValidator(self.root).validate_payload(
            schema="MiasiSemanticReport",
            payload=report.to_dict(),
            instance_label="in-memory:miasi-semantic-report",
        )
        return self._command_result(report=report, schema_result=schema_result)

    def _report(self, *, rule_results: list[SemanticRuleResult], status: str) -> MiasiSemanticReport:
        return MiasiSemanticReport(
            report_id="miasi-semantic-post-h-004-d",
            created_by="POST-H-004-D",
            status=status,
            rule_results=tuple(rule_results),
            source_paths=self.builder.source_paths(),
            no_go_gates=(
                "remote.execute must remain blocked",
                "plugin.execute must remain blocked until sandboxed",
                "connector.write must remain blocked unless future ADR/sandbox/test-contract gates approve it",
                "semantic validation must not relax PolicyEngine or execute agent/tool runtime paths",
                "approval/RBAC/security guards must be explicit before high-risk runtime paths can evolve beyond implemented-initial",
            ),
            notes=(
                "POST-H-004-D validates agent/tool/policy declarations plus approval, RBAC, security guards, observability, eval fixtures and test-contract coverage.",
                "Controlled-write tools without explicit approval/RBAC remain warnings when local guards are present; missing guards, unsafe no-go paths, disabled observability or invalid eval evidence remain blocking.",
                "This validator is local-first, dry-run and non-executing.",
            ),
        )

    def _load_failure_rule(self, findings: list[Finding]) -> SemanticRuleResult:
        semantic_findings = [
            SemanticFinding(
                finding_id="MIASI_SEMANTIC_BUNDLE_LOAD_FAILED",
                rule_id="SEM-BUNDLE-LOAD-001",
                severity=SemanticSeverity.BLOCK,
                message=finding.message,
                category="schema",
                subject_type="miasi_bundle",
                subject_id=".devpilot/miasi",
                path=finding.path,
                metadata={"source_finding_id": finding.id, **(finding.metadata or {})},
            )
            for finding in findings
        ]
        return SemanticRuleResult.from_findings(
            rule_id="SEM-BUNDLE-LOAD-001",
            title="MIASI semantic bundle can be loaded",
            findings=semantic_findings,
            subjects_evaluated=1,
            summary={"source_findings_total": len(findings)},
        )

    def _validate_agent_tool_references(self, bundle: MiasiRegistryBundle) -> SemanticRuleResult:
        findings: list[SemanticFinding] = []
        for agent in bundle.agents:
            for tool_id in agent.allowed_tools:
                if tool_id not in bundle.tool_ids:
                    findings.append(
                        self._finding(
                            finding_id="MIASI_SEMANTIC_AGENT_TOOL_UNKNOWN",
                            rule_id="SEM-AGENT-TOOL-001",
                            severity=SemanticSeverity.BLOCK,
                            message="Agent references an unknown allowed tool.",
                            category="agent",
                            subject_type="agent",
                            subject_id=agent.agent_id,
                            path=AGENT_REGISTRY_FILE.as_posix(),
                            metadata={"tool_id": tool_id},
                        )
                    )
            if not agent.allowed_tools:
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_AGENT_TOOLS_MISSING",
                        rule_id="SEM-AGENT-TOOL-001",
                        severity=SemanticSeverity.BLOCK,
                        message="Agent has no allowed tools declared.",
                        category="agent",
                        subject_type="agent",
                        subject_id=agent.agent_id,
                        path=AGENT_REGISTRY_FILE.as_posix(),
                    )
                )
        return self._rule_result(
            rule_id="SEM-AGENT-TOOL-001",
            title="Agents must reference existing allowed tools",
            findings=findings,
            subjects_evaluated=len(bundle.agents),
            summary={"agents_total": len(bundle.agents), "tools_total": len(bundle.tools)},
        )

    def _validate_policy_references(self, bundle: MiasiRegistryBundle) -> SemanticRuleResult:
        findings: list[SemanticFinding] = []
        for agent in bundle.agents:
            findings.extend(
                self._policy_reference_findings(
                    subject=agent,
                    subject_type="agent",
                    subject_id=agent.agent_id,
                    rule_ids=agent.policy_rule_ids,
                    known_rule_ids=bundle.rule_ids,
                    path=AGENT_REGISTRY_FILE.as_posix(),
                )
            )
        for tool in bundle.tools:
            findings.extend(
                self._policy_reference_findings(
                    subject=tool,
                    subject_type="tool",
                    subject_id=tool.tool_id,
                    rule_ids=tool.policy_rule_ids,
                    known_rule_ids=bundle.rule_ids,
                    path=TOOL_REGISTRY_FILE.as_posix(),
                )
            )
        return self._rule_result(
            rule_id="SEM-POLICY-REF-001",
            title="Agents and tools must reference existing policy rules",
            findings=findings,
            subjects_evaluated=len(bundle.agents) + len(bundle.tools),
            summary={"known_policy_rules_total": len(bundle.rules)},
        )

    def _policy_reference_findings(
        self,
        *,
        subject: AgentSpec | ToolSpec,
        subject_type: str,
        subject_id: str,
        rule_ids: tuple[str, ...],
        known_rule_ids: set[str],
        path: str,
    ) -> list[SemanticFinding]:
        findings: list[SemanticFinding] = []
        if not rule_ids:
            findings.append(
                self._finding(
                    finding_id="MIASI_SEMANTIC_POLICY_RULES_MISSING",
                    rule_id="SEM-POLICY-REF-001",
                    severity=SemanticSeverity.BLOCK,
                    message=f"{subject_type.title()} has no Policy Matrix rule references.",
                    category="policy",
                    subject_type=subject_type,
                    subject_id=subject_id,
                    path=path,
                    metadata={"subject": subject.to_dict()},
                )
            )
        for rule_id in rule_ids:
            if rule_id not in known_rule_ids:
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_POLICY_RULE_UNKNOWN",
                        rule_id="SEM-POLICY-REF-001",
                        severity=SemanticSeverity.BLOCK,
                        message=f"{subject_type.title()} references an unknown Policy Matrix rule.",
                        category="policy",
                        subject_type=subject_type,
                        subject_id=subject_id,
                        path=path,
                        metadata={"policy_rule_id": rule_id},
                    )
                )
        return findings

    def _validate_status_semantics(self, bundle: MiasiRegistryBundle) -> SemanticRuleResult:
        findings: list[SemanticFinding] = []
        agents_by_status: dict[str, int] = {}
        tools_by_status: dict[str, int] = {}
        referenced_tools = {tool_id for agent in bundle.agents if agent.status not in {"planned", "future", "disabled"} for tool_id in agent.allowed_tools}
        for agent in bundle.agents:
            agents_by_status[agent.status] = agents_by_status.get(agent.status, 0) + 1
            if agent.status in {"planned", "future", "disabled"} and agent.phase == "MVP":
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_AGENT_MVP_NON_EXECUTABLE_STATUS",
                        rule_id="SEM-STATUS-001",
                        severity=SemanticSeverity.WARNING,
                        message="MVP agent is declared with a non-executable status; verify it is intentionally not wired to runtime.",
                        category="agent",
                        subject_type="agent",
                        subject_id=agent.agent_id,
                        path=AGENT_REGISTRY_FILE.as_posix(),
                        metadata={"status": agent.status, "phase": agent.phase},
                    )
                )
        for tool in bundle.tools:
            tools_by_status[tool.status] = tools_by_status.get(tool.status, 0) + 1
            if tool.status in {"planned", "future", "disabled"} and tool.tool_id in referenced_tools:
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_REFERENCED_TOOL_NON_EXECUTABLE_STATUS",
                        rule_id="SEM-STATUS-001",
                        severity=SemanticSeverity.WARNING,
                        message="Implemented agent references a planned/future/disabled tool; this must remain non-executable at runtime.",
                        category="tool",
                        subject_type="tool",
                        subject_id=tool.tool_id,
                        path=TOOL_REGISTRY_FILE.as_posix(),
                        metadata={"status": tool.status},
                    )
                )
        return self._rule_result(
            rule_id="SEM-STATUS-001",
            title="Agent and tool statuses must not imply premature executability",
            findings=findings,
            subjects_evaluated=len(bundle.agents) + len(bundle.tools),
            summary={"agents_by_status": agents_by_status, "tools_by_status": tools_by_status},
        )

    def _validate_sensitive_tool_approval(self, bundle: MiasiRegistryBundle) -> SemanticRuleResult:
        findings: list[SemanticFinding] = []
        rules_by_id = {rule.rule_id: rule for rule in bundle.rules}
        sensitive_tools = [
            tool
            for tool in bundle.tools
            if tool.risk_level in {"high", "medium_high"} or tool.side_effect in SENSITIVE_SIDE_EFFECTS
        ]
        for tool in sensitive_tools:
            associated_rules = [rules_by_id[rule_id] for rule_id in tool.policy_rule_ids if rule_id in rules_by_id]
            if self._tool_requires_immediate_approval(tool) and not tool.requires_approval:
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_SENSITIVE_TOOL_APPROVAL_MISSING",
                        rule_id="SEM-TOOL-APPROVAL-001",
                        severity=SemanticSeverity.BLOCK,
                        message="Sensitive high-risk execution or network-cost tool lacks explicit approval.",
                        category="tool",
                        subject_type="tool",
                        subject_id=tool.tool_id,
                        path=TOOL_REGISTRY_FILE.as_posix(),
                        metadata={"tool": tool.to_dict(), "policy_rule_ids": tool.policy_rule_ids},
                    )
                )
            elif self._controlled_write_without_explicit_approval(tool, associated_rules):
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_CONTROLLED_WRITE_APPROVAL_REVIEW",
                        rule_id="SEM-TOOL-APPROVAL-001",
                        severity=SemanticSeverity.WARNING,
                        message="High-risk controlled-write tool has no explicit tool-level approval; current gates appear local/sandboxed but must be hardened before production-local promotion.",
                        category="tool",
                        subject_type="tool",
                        subject_id=tool.tool_id,
                        path=TOOL_REGISTRY_FILE.as_posix(),
                        metadata={
                            "tool": tool.to_dict(),
                            "policy_effects": [rule.default_effect for rule in associated_rules],
                            "policy_gates": [rule.gate for rule in associated_rules],
                        },
                    )
                )
        return self._rule_result(
            rule_id="SEM-TOOL-APPROVAL-001",
            title="Sensitive side-effecting tools must be approval-governed or explicitly safe-gated",
            findings=findings,
            subjects_evaluated=len(sensitive_tools),
            summary={"sensitive_tools_total": len(sensitive_tools)},
        )

    @staticmethod
    def _tool_requires_immediate_approval(tool: ToolSpec) -> bool:
        return tool.risk_level == "high" and tool.side_effect in EXECUTION_SIDE_EFFECTS and tool.status not in {"disabled", "future", "planned"}

    @staticmethod
    def _controlled_write_without_explicit_approval(tool: ToolSpec, rules: list[PolicyRule]) -> bool:
        if tool.requires_approval:
            return False
        if tool.risk_level != "high" or tool.side_effect != "controlled_write" or tool.status in {"disabled", "future", "planned"}:
            return False
        gates_text = " ".join(rule.gate.lower() for rule in rules)
        has_safe_gate_token = any(token in gates_text for token in SAFE_GATED_CONTROLLED_WRITE_TOKENS)
        has_blocking_policy = any(rule.default_effect in {"deny", "block"} for rule in rules)
        # Keep POST-H-004-B non-breaking for known implemented-initial local/sandbox flows,
        # but surface them as debt. POST-H-004-C hardens approval/RBAC/security guards.
        return has_safe_gate_token or has_blocking_policy or bool(rules)

    def _validate_approval_metadata(self, bundle: MiasiRegistryBundle) -> SemanticRuleResult:
        findings: list[SemanticFinding] = []
        rules_by_id = {rule.rule_id: rule for rule in bundle.rules}
        sensitive_tools = [
            tool
            for tool in bundle.tools
            if tool.status not in {"disabled", "future", "planned"}
            and (tool.requires_approval or tool.side_effect in EXECUTION_SIDE_EFFECTS or (tool.risk_level == "high" and tool.side_effect in SENSITIVE_SIDE_EFFECTS))
        ]
        for tool in sensitive_tools:
            associated_rules = [rules_by_id[rule_id] for rule_id in tool.policy_rule_ids if rule_id in rules_by_id]
            if tool.requires_approval:
                approval_rules = [rule for rule in associated_rules if rule.approval_required or self._text_has_any(rule.gate, APPROVAL_GATE_TOKENS)]
                if not approval_rules:
                    findings.append(
                        self._finding(
                            finding_id="MIASI_SEMANTIC_APPROVAL_METADATA_MISSING",
                            rule_id="SEM-APPROVAL-SCOPE-001",
                            severity=SemanticSeverity.BLOCK,
                            message="Approval-required tool is not backed by a policy rule or gate with approval metadata.",
                            category="approval",
                            subject_type="tool",
                            subject_id=tool.tool_id,
                            path=TOOL_REGISTRY_FILE.as_posix(),
                            metadata={"tool": tool.to_dict(), "policy_rule_ids": tool.policy_rule_ids},
                        )
                    )
                for rule in approval_rules:
                    if self._is_generic_approval_gate(rule):
                        findings.append(
                            self._finding(
                                finding_id="MIASI_SEMANTIC_APPROVAL_SCOPE_GENERIC",
                                rule_id="SEM-APPROVAL-SCOPE-001",
                                severity=SemanticSeverity.BLOCK,
                                message="Approval metadata for sensitive tool is too generic; scope must bind tool/action/subject or a concrete gate.",
                                category="approval",
                                subject_type="policy_rule",
                                subject_id=rule.rule_id,
                                path=POLICY_MATRIX_FILE.as_posix(),
                                metadata={"tool_id": tool.tool_id, "policy_rule": rule.to_dict()},
                            )
                        )
            elif tool.risk_level == "high" and tool.side_effect == "controlled_write":
                guarded = self._rules_have_any_token(associated_rules, LOCAL_GUARD_TOKENS) and self._rules_have_any_token(associated_rules, SECRET_GUARD_TOKENS)
                if not guarded:
                    findings.append(
                        self._finding(
                            finding_id="MIASI_SEMANTIC_CONTROLLED_WRITE_APPROVAL_OR_GUARD_MISSING",
                            rule_id="SEM-APPROVAL-SCOPE-001",
                            severity=SemanticSeverity.BLOCK,
                            message="High-risk controlled-write tool has no explicit approval and lacks concrete local security guards.",
                            category="approval",
                            subject_type="tool",
                            subject_id=tool.tool_id,
                            path=TOOL_REGISTRY_FILE.as_posix(),
                            metadata={"tool": tool.to_dict(), "policy_gates": [rule.gate for rule in associated_rules]},
                        )
                    )
        return self._rule_result(
            rule_id="SEM-APPROVAL-SCOPE-001",
            title="Sensitive tools must have explicit approval metadata or concrete local guard scope",
            findings=findings,
            subjects_evaluated=len(sensitive_tools),
            summary={"sensitive_tools_evaluated": len(sensitive_tools)},
        )

    def _validate_rbac_requirements(self, bundle: MiasiRegistryBundle) -> SemanticRuleResult:
        findings: list[SemanticFinding] = []
        registry, registry_findings = self._load_identity_registry()
        findings.extend(registry_findings)
        sensitive_tools = [
            tool
            for tool in bundle.tools
            if tool.status not in {"disabled", "future", "planned"}
            and (tool.risk_level == "high" or tool.side_effect in {"controlled_execution", "network_cost", "controlled_write"})
        ]
        rules_by_id = {rule.rule_id: rule for rule in bundle.rules}
        if registry:
            defaults = registry.get("defaults", {}) if isinstance(registry.get("defaults"), dict) else {}
            if defaults.get("rbac_enforced_for_sensitive_actions") is not True:
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_RBAC_NOT_ENFORCED",
                        rule_id="SEM-RBAC-001",
                        severity=SemanticSeverity.BLOCK,
                        message="Identity registry must enforce RBAC for sensitive actions.",
                        category="rbac",
                        subject_type="identity_registry",
                        subject_id="defaults",
                        path=IDENTITY_REGISTRY_FILE.as_posix(),
                        metadata={"defaults": defaults},
                    )
                )
            if defaults.get("deny_unknown_actor") is not True:
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_UNKNOWN_ACTOR_NOT_DENIED",
                        rule_id="SEM-RBAC-001",
                        severity=SemanticSeverity.BLOCK,
                        message="Identity registry must deny unknown actors for sensitive actions.",
                        category="rbac",
                        subject_type="identity_registry",
                        subject_id="defaults",
                        path=IDENTITY_REGISTRY_FILE.as_posix(),
                        metadata={"defaults": defaults},
                    )
                )
            findings.extend(self._active_actor_findings(registry))
            findings.extend(self._approval_role_findings(registry))
        for tool in sensitive_tools:
            associated_rules = [rules_by_id[rule_id] for rule_id in tool.policy_rule_ids if rule_id in rules_by_id]
            if tool.side_effect in {"controlled_execution", "network_cost"} and tool.requires_approval:
                has_rbac_or_approval = self._rules_have_any_token(associated_rules, RBAC_GATE_TOKENS + APPROVAL_GATE_TOKENS)
                if not has_rbac_or_approval:
                    findings.append(
                        self._finding(
                            finding_id="MIASI_SEMANTIC_RBAC_BINDING_MISSING",
                            rule_id="SEM-RBAC-001",
                            severity=SemanticSeverity.BLOCK,
                            message="Approval-gated execution/network tool lacks RBAC or approval actor binding in its policy gates.",
                            category="rbac",
                            subject_type="tool",
                            subject_id=tool.tool_id,
                            path=TOOL_REGISTRY_FILE.as_posix(),
                            metadata={"tool": tool.to_dict(), "policy_gates": [rule.gate for rule in associated_rules]},
                        )
                    )
            elif tool.side_effect == "controlled_write" and tool.risk_level == "high" and not tool.requires_approval:
                # Current implemented-initial controlled-write capabilities remain local and sandboxed;
                # C records RBAC debt as a warning when local guards exist, and blocks when no guard exists.
                if self._rules_have_any_token(associated_rules, LOCAL_GUARD_TOKENS):
                    findings.append(
                        self._finding(
                            finding_id="MIASI_SEMANTIC_RBAC_REVIEW_REQUIRED",
                            rule_id="SEM-RBAC-001",
                            severity=SemanticSeverity.WARNING,
                            message="High-risk controlled-write tool is locally guarded but lacks explicit RBAC binding; harden before production-local promotion.",
                            category="rbac",
                            subject_type="tool",
                            subject_id=tool.tool_id,
                            path=TOOL_REGISTRY_FILE.as_posix(),
                            metadata={"tool": tool.to_dict(), "policy_gates": [rule.gate for rule in associated_rules]},
                        )
                    )
                else:
                    findings.append(
                        self._finding(
                            finding_id="MIASI_SEMANTIC_RBAC_BINDING_MISSING",
                            rule_id="SEM-RBAC-001",
                            severity=SemanticSeverity.BLOCK,
                            message="High-risk controlled-write tool lacks both explicit approval and RBAC/local guard binding.",
                            category="rbac",
                            subject_type="tool",
                            subject_id=tool.tool_id,
                            path=TOOL_REGISTRY_FILE.as_posix(),
                            metadata={"tool": tool.to_dict(), "policy_gates": [rule.gate for rule in associated_rules]},
                        )
                    )
        return self._rule_result(
            rule_id="SEM-RBAC-001",
            title="Sensitive actions must be constrained by local identity/RBAC metadata",
            findings=findings,
            subjects_evaluated=len(sensitive_tools) + 1,
            summary={
                "sensitive_tools_evaluated": len(sensitive_tools),
                "identity_registry_path": IDENTITY_REGISTRY_FILE.as_posix(),
                "identity_registry_present": registry is not None,
            },
        )

    def _validate_security_guards(self, bundle: MiasiRegistryBundle) -> SemanticRuleResult:
        findings: list[SemanticFinding] = []
        rules_by_id = {rule.rule_id: rule for rule in bundle.rules}
        sensitive_tools = [
            tool
            for tool in bundle.tools
            if tool.status not in {"disabled", "future", "planned"}
            and (tool.risk_level in {"high", "medium_high"} or tool.side_effect in SENSITIVE_SIDE_EFFECTS)
        ]
        for tool in sensitive_tools:
            associated_rules = [rules_by_id[rule_id] for rule_id in tool.policy_rule_ids if rule_id in rules_by_id]
            gate_text = " ".join(rule.gate.lower() for rule in associated_rules)
            rule_ids_text = " ".join(tool.policy_rule_ids).lower()
            if self._tool_needs_secret_guard(tool) and not (self._text_has_any(gate_text, SECRET_GUARD_TOKENS) or "secrets_raw_deny" in rule_ids_text):
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_SECRET_GUARD_MISSING",
                        rule_id="SEM-SECURITY-GUARD-001",
                        severity=SemanticSeverity.BLOCK,
                        message="Sensitive tool is not bound to SecretGuard or SECRETS_RAW_DENY.",
                        category="security",
                        subject_type="tool",
                        subject_id=tool.tool_id,
                        path=TOOL_REGISTRY_FILE.as_posix(),
                        metadata={"tool": tool.to_dict(), "policy_gates": [rule.gate for rule in associated_rules]},
                    )
                )
            if tool.side_effect == "network_cost" and not (tool.requires_approval and self._rules_have_any_token(associated_rules, NETWORK_GUARD_TOKENS)):
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_NETWORK_COST_GUARD_MISSING",
                        rule_id="SEM-SECURITY-GUARD-001",
                        severity=SemanticSeverity.BLOCK,
                        message="Network/cost tool must require approval and be guarded by CostGuard/NoExternalAPI/NoNetwork/LocalhostOnly semantics.",
                        category="security",
                        subject_type="tool",
                        subject_id=tool.tool_id,
                        path=TOOL_REGISTRY_FILE.as_posix(),
                        metadata={"tool": tool.to_dict(), "policy_gates": [rule.gate for rule in associated_rules]},
                    )
                )
            if tool.side_effect in {"controlled_write", "optional_write"} and not self._rules_have_any_token(associated_rules, LOCAL_GUARD_TOKENS):
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_LOCAL_WRITE_GUARD_MISSING",
                        rule_id="SEM-SECURITY-GUARD-001",
                        severity=SemanticSeverity.BLOCK,
                        message="Write-capable tool must declare local/sandbox/path/policy guard semantics.",
                        category="security",
                        subject_type="tool",
                        subject_id=tool.tool_id,
                        path=TOOL_REGISTRY_FILE.as_posix(),
                        metadata={"tool": tool.to_dict(), "policy_gates": [rule.gate for rule in associated_rules]},
                    )
                )
        return self._rule_result(
            rule_id="SEM-SECURITY-GUARD-001",
            title="Sensitive tools must declare SecretGuard, local guard and network/cost guard semantics",
            findings=findings,
            subjects_evaluated=len(sensitive_tools),
            summary={"sensitive_tools_evaluated": len(sensitive_tools)},
        )

    def _validate_no_go_security_guards(self, bundle: MiasiRegistryBundle) -> SemanticRuleResult:
        findings: list[SemanticFinding] = []
        rules_by_id = {rule.rule_id: rule for rule in bundle.rules}
        for tool in bundle.tools:
            identity = f"{tool.tool_id} {tool.name} {tool.side_effect}".lower()
            associated_rules = [rules_by_id[rule_id] for rule_id in tool.policy_rule_ids if rule_id in rules_by_id]
            rule_text = " ".join(f"{rule.domain} {rule.action} {rule.default_effect} {rule.gate}".lower() for rule in associated_rules)
            if self._looks_like_no_go_tool(identity, rule_text):
                allowed = any(rule.default_effect == "allow" for rule in associated_rules)
                denied_or_blocked = any(rule.default_effect in {"deny", "block"} for rule in associated_rules) or tool.status in {"disabled", "future", "planned"}
                has_future_sandbox_only = self._text_has_any(rule_text, ("futureadr", "future sandbox", "sandboxfuture", "sandbox", "dry_run", "dry-run", "metadata"))
                if allowed and not denied_or_blocked:
                    findings.append(
                        self._finding(
                            finding_id="MIASI_SEMANTIC_NO_GO_TOOL_ALLOWED",
                            rule_id="SEM-NO-GO-GUARD-001",
                            severity=SemanticSeverity.BLOCK,
                            message="Remote/plugin/connector write or execute tool is allowed without deny/block guard.",
                            category="no-go",
                            subject_type="tool",
                            subject_id=tool.tool_id,
                            path=TOOL_REGISTRY_FILE.as_posix(),
                            metadata={"tool": tool.to_dict(), "policy_rules": [rule.to_dict() for rule in associated_rules]},
                        )
                    )
                if "connector" in identity and ("write" in identity or "write" in rule_text) and allowed and not has_future_sandbox_only:
                    findings.append(
                        self._finding(
                            finding_id="MIASI_SEMANTIC_CONNECTOR_WRITE_WITHOUT_FUTURE_GUARDS",
                            rule_id="SEM-NO-GO-GUARD-001",
                            severity=SemanticSeverity.BLOCK,
                            message="Connector write path is not allowed without future ADR/sandbox/test-contract guard semantics.",
                            category="no-go",
                            subject_type="tool",
                            subject_id=tool.tool_id,
                            path=TOOL_REGISTRY_FILE.as_posix(),
                            metadata={"tool": tool.to_dict(), "policy_rules": [rule.to_dict() for rule in associated_rules]},
                        )
                    )
        return self._rule_result(
            rule_id="SEM-NO-GO-GUARD-001",
            title="Remote/plugin/connector write or execute paths must remain deny/block guarded",
            findings=findings,
            subjects_evaluated=len(bundle.tools),
            summary={"tools_total": len(bundle.tools)},
        )


    def _validate_observability_requirements(self, bundle: MiasiRegistryBundle) -> SemanticRuleResult:
        findings: list[SemanticFinding] = []
        rules_by_id = {rule.rule_id: rule for rule in bundle.rules}
        high_risk_agents = [
            agent
            for agent in bundle.agents
            if agent.status not in {"disabled", "future", "planned"}
            and (agent.risk_level in {"high", "medium_high"} or self._agent_autonomy_number(agent.max_autonomy) >= 3)
        ]
        for agent in high_risk_agents:
            if not agent.observability_required:
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_AGENT_OBSERVABILITY_MISSING",
                        rule_id="SEM-OBSERVABILITY-001",
                        severity=SemanticSeverity.BLOCK,
                        message="A3+/high-risk agent must declare observability_required=true.",
                        category="observability",
                        subject_type="agent",
                        subject_id=agent.agent_id,
                        path=AGENT_REGISTRY_FILE.as_posix(),
                        metadata={"agent": agent.to_dict()},
                    )
                )
            if not agent.eval_required:
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_AGENT_EVAL_STRATEGY_MISSING",
                        rule_id="SEM-OBSERVABILITY-001",
                        severity=SemanticSeverity.BLOCK,
                        message="A3+/high-risk agent must declare eval_required=true before runtime promotion.",
                        category="eval",
                        subject_type="agent",
                        subject_id=agent.agent_id,
                        path=AGENT_REGISTRY_FILE.as_posix(),
                        metadata={"agent": agent.to_dict()},
                    )
                )
            if any(tool_id.startswith("multiagent.") for tool_id in agent.allowed_tools):
                has_handoff_trace = "multiagent.handoff" in agent.allowed_tools or "MULTIAGENT_HANDOFF_TRACE_REQUIRED" in agent.policy_rule_ids
                if not has_handoff_trace:
                    findings.append(
                        self._finding(
                            finding_id="MIASI_SEMANTIC_HANDOFF_TRACE_MISSING",
                            rule_id="SEM-OBSERVABILITY-001",
                            severity=SemanticSeverity.BLOCK,
                            message="Agentic workflow/multiagent capability must declare handoff trace semantics.",
                            category="observability",
                            subject_type="agent",
                            subject_id=agent.agent_id,
                            path=AGENT_REGISTRY_FILE.as_posix(),
                            metadata={"agent": agent.to_dict()},
                        )
                    )
        sensitive_tools = [
            tool
            for tool in bundle.tools
            if tool.status not in {"disabled", "future", "planned"}
            and (tool.risk_level in {"high", "medium_high"} or tool.side_effect in SENSITIVE_SIDE_EFFECTS)
        ]
        for tool in sensitive_tools:
            associated_rules = [rules_by_id[rule_id] for rule_id in tool.policy_rule_ids if rule_id in rules_by_id]
            if associated_rules and not any(rule.observability_required for rule in associated_rules):
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_TOOL_OBSERVABILITY_MISSING",
                        rule_id="SEM-OBSERVABILITY-001",
                        severity=SemanticSeverity.BLOCK,
                        message="Sensitive/high-risk tool must be attached to at least one observability-required policy rule.",
                        category="observability",
                        subject_type="tool",
                        subject_id=tool.tool_id,
                        path=TOOL_REGISTRY_FILE.as_posix(),
                        metadata={"tool": tool.to_dict(), "policy_rules": [rule.to_dict() for rule in associated_rules]},
                    )
                )
        sensitive_rules = [
            rule
            for rule in bundle.rules
            if rule.default_effect in {"deny", "block", "deny_unless_safe_output"}
            or rule.approval_required
            or self._text_has_any(f"{rule.domain} {rule.action} {rule.rule_id}", ("remote", "plugin", "connector", "secret", "approval", "rbac"))
        ]
        for rule in sensitive_rules:
            if not rule.observability_required:
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_POLICY_OBSERVABILITY_MISSING",
                        rule_id="SEM-OBSERVABILITY-001",
                        severity=SemanticSeverity.BLOCK,
                        message="Sensitive deny/block/approval/no-go policy rule must declare observability_required=true.",
                        category="observability",
                        subject_type="policy_rule",
                        subject_id=rule.rule_id,
                        path=POLICY_MATRIX_FILE.as_posix(),
                        metadata=rule.to_dict(),
                    )
                )
        return self._rule_result(
            rule_id="SEM-OBSERVABILITY-001",
            title="High-risk agents, tools and sensitive policies must declare observability/eval traceability",
            findings=findings,
            subjects_evaluated=len(high_risk_agents) + len(sensitive_tools) + len(sensitive_rules),
            summary={
                "high_risk_agents_evaluated": len(high_risk_agents),
                "sensitive_tools_evaluated": len(sensitive_tools),
                "sensitive_policy_rules_evaluated": len(sensitive_rules),
            },
        )

    def _validate_eval_fixture_coverage(self, bundle: MiasiRegistryBundle) -> SemanticRuleResult:
        findings: list[SemanticFinding] = []
        suites_present = 0
        cases_total = 0
        for spec in REQUIRED_EVAL_FIXTURES:
            fixture_path = spec["path"]
            path = self.root / fixture_path
            expected_suite = str(spec["suite_id"])
            required_markers = tuple(str(item) for item in spec["required_markers"])
            if not path.is_file():
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_EVAL_FIXTURE_MISSING",
                        rule_id="SEM-EVAL-COVERAGE-001",
                        severity=SemanticSeverity.WARNING,
                        message="Expected safety eval fixture is missing; semantic validation remains non-blocking for lightweight fixture workspaces but must be present in DevPilot root.",
                        category="eval",
                        subject_type="eval_fixture",
                        subject_id=expected_suite,
                        path=fixture_path.as_posix(),
                        metadata={"expected_markers": list(required_markers)},
                    )
                )
                continue
            payload, errors = self._load_json_payload(path=path, rule_id="SEM-EVAL-COVERAGE-001", category="eval", subject_type="eval_fixture", subject_id=expected_suite)
            findings.extend(errors)
            if payload is None:
                continue
            suites_present += 1
            suite_id = str(payload.get("suite_id", "")).strip()
            if suite_id != expected_suite:
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_EVAL_SUITE_ID_MISMATCH",
                        rule_id="SEM-EVAL-COVERAGE-001",
                        severity=SemanticSeverity.BLOCK,
                        message="Safety eval fixture suite_id does not match the expected suite.",
                        category="eval",
                        subject_type="eval_fixture",
                        subject_id=expected_suite,
                        path=fixture_path.as_posix(),
                        metadata={"actual_suite_id": suite_id, "expected_suite_id": expected_suite},
                    )
                )
            cases = payload.get("cases", [])
            if not isinstance(cases, list) or not cases:
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_EVAL_CASES_MISSING",
                        rule_id="SEM-EVAL-COVERAGE-001",
                        severity=SemanticSeverity.BLOCK,
                        message="Safety eval fixture must declare at least one case.",
                        category="eval",
                        subject_type="eval_fixture",
                        subject_id=expected_suite,
                        path=fixture_path.as_posix(),
                    )
                )
                continue
            cases_total += len(cases)
            markers_text = json.dumps(cases, sort_keys=True).lower()
            missing_markers = [marker for marker in required_markers if marker.lower() not in markers_text]
            if missing_markers:
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_EVAL_MARKER_COVERAGE_MISSING",
                        rule_id="SEM-EVAL-COVERAGE-001",
                        severity=SemanticSeverity.BLOCK,
                        message="Safety eval fixture is present but lacks required risk markers.",
                        category="eval",
                        subject_type="eval_fixture",
                        subject_id=expected_suite,
                        path=fixture_path.as_posix(),
                        metadata={"missing_markers": missing_markers, "required_markers": list(required_markers)},
                    )
                )
            for flag in ("network_used", "external_api_used", "llm_judge_used"):
                if payload.get(flag) is True:
                    findings.append(
                        self._finding(
                            finding_id="MIASI_SEMANTIC_EVAL_UNSAFE_RUNTIME_FLAG",
                            rule_id="SEM-EVAL-COVERAGE-001",
                            severity=SemanticSeverity.BLOCK,
                            message="Safety eval fixture must remain local, deterministic and non-networked.",
                            category="eval",
                            subject_type="eval_fixture",
                            subject_id=expected_suite,
                            path=fixture_path.as_posix(),
                            metadata={"flag": flag, "value": payload.get(flag)},
                        )
                    )
        return self._rule_result(
            rule_id="SEM-EVAL-COVERAGE-001",
            title="Agentic safety, red-team, plugin, RBAC and remote fixtures must cover high-risk semantic threats",
            findings=findings,
            subjects_evaluated=len(REQUIRED_EVAL_FIXTURES),
            summary={
                "required_eval_fixtures_total": len(REQUIRED_EVAL_FIXTURES),
                "required_eval_fixtures_present": suites_present,
                "eval_cases_total": cases_total,
            },
        )

    def _validate_test_contract_coverage(self, bundle: MiasiRegistryBundle) -> SemanticRuleResult:
        findings: list[SemanticFinding] = []
        v1_payload, v1_errors = self._load_optional_json_payload(
            relative_path=TEST_CONTRACT_REGISTRY_V1_FILE,
            rule_id="SEM-TEST-CONTRACT-COVERAGE-001",
            category="test-contract",
            subject_type="test_contract_registry",
            subject_id="v1",
        )
        v2_payload, v2_errors = self._load_optional_json_payload(
            relative_path=TEST_CONTRACT_REGISTRY_V2_FILE,
            rule_id="SEM-TEST-CONTRACT-COVERAGE-001",
            category="test-contract",
            subject_type="test_contract_registry",
            subject_id="v2",
        )
        findings.extend(v1_errors)
        findings.extend(v2_errors)
        semantic_contracts_total = 0
        p0_p1_security_contracts_total = 0
        if isinstance(v1_payload, dict):
            contracts = v1_payload.get("contracts", [])
            if isinstance(contracts, list):
                semantic_contracts_total += self._count_semantic_contracts(contracts)
        if isinstance(v2_payload, dict):
            contracts = v2_payload.get("contracts", [])
            if isinstance(contracts, list):
                semantic_contracts_total += self._count_semantic_contracts(contracts)
                for contract in contracts:
                    if not isinstance(contract, dict):
                        continue
                    criticality = str(contract.get("criticality", "")).upper()
                    text = json.dumps(contract, sort_keys=True).lower()
                    if criticality in {"P0", "P1"} and any(marker in text for marker in ("security", "miasi", "policy", "approval", "rbac", "plugin", "remote", "connector")):
                        p0_p1_security_contracts_total += 1
                        if contract.get("network_allowed") is not False or contract.get("external_api_allowed") is not False:
                            findings.append(
                                self._finding(
                                    finding_id="MIASI_SEMANTIC_TCR_UNSAFE_NETWORK_ALLOWANCE",
                                    rule_id="SEM-TEST-CONTRACT-COVERAGE-001",
                                    severity=SemanticSeverity.BLOCK,
                                    message="P0/P1 security/MIASI-related test contract must not allow network or external APIs.",
                                    category="test-contract",
                                    subject_type="test_contract",
                                    subject_id=str(contract.get("contract_id", "<unknown>")),
                                    path=TEST_CONTRACT_REGISTRY_V2_FILE.as_posix(),
                                    metadata={"contract": contract},
                                )
                            )
        if semantic_contracts_total == 0:
            findings.append(
                self._finding(
                    finding_id="MIASI_SEMANTIC_TCR_SEMANTIC_CONTRACT_MISSING",
                    rule_id="SEM-TEST-CONTRACT-COVERAGE-001",
                    severity=SemanticSeverity.WARNING,
                    message="MIASI semantic validator tests are not yet registered as a formal TCR v1/v2 contract; POST-H-004-E must close this before hito closure.",
                    category="test-contract",
                    subject_type="test_contract_registry",
                    subject_id="miasi-semantic-validator",
                    path=TEST_CONTRACT_REGISTRY_V2_FILE.as_posix(),
                    metadata={"expected_test_files": ["tests/test_miasi_semantic_validator.py", "tests/test_miasi_semantic_validator_fixtures.py"]},
                )
            )
        return self._rule_result(
            rule_id="SEM-TEST-CONTRACT-COVERAGE-001",
            title="High-risk semantic validation must map to local Test Contract Registry evidence",
            findings=findings,
            subjects_evaluated=2,
            summary={
                "tcr_v1_present": isinstance(v1_payload, dict),
                "tcr_v2_present": isinstance(v2_payload, dict),
                "semantic_contracts_total": semantic_contracts_total,
                "p0_p1_security_contracts_total": p0_p1_security_contracts_total,
            },
        )

    def _load_identity_registry(self) -> tuple[dict[str, Any] | None, list[SemanticFinding]]:
        path = self.root / IDENTITY_REGISTRY_FILE
        if not path.is_file():
            return None, [
                self._finding(
                    finding_id="MIASI_SEMANTIC_IDENTITY_REGISTRY_MISSING",
                    rule_id="SEM-RBAC-001",
                    severity=SemanticSeverity.BLOCK,
                    message="Identity registry is required for approval/RBAC semantic validation.",
                    category="rbac",
                    subject_type="identity_registry",
                    subject_id="identity_registry",
                    path=IDENTITY_REGISTRY_FILE.as_posix(),
                )
            ]
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return None, [
                self._finding(
                    finding_id="MIASI_SEMANTIC_IDENTITY_REGISTRY_INVALID_JSON",
                    rule_id="SEM-RBAC-001",
                    severity=SemanticSeverity.BLOCK,
                    message="Identity registry is not valid JSON.",
                    category="rbac",
                    subject_type="identity_registry",
                    subject_id="identity_registry",
                    path=IDENTITY_REGISTRY_FILE.as_posix(),
                    metadata={"error": str(exc)},
                )
            ]
        if not isinstance(payload, dict):
            return None, [
                self._finding(
                    finding_id="MIASI_SEMANTIC_IDENTITY_REGISTRY_INVALID_SHAPE",
                    rule_id="SEM-RBAC-001",
                    severity=SemanticSeverity.BLOCK,
                    message="Identity registry must be a JSON object.",
                    category="rbac",
                    subject_type="identity_registry",
                    subject_id="identity_registry",
                    path=IDENTITY_REGISTRY_FILE.as_posix(),
                )
            ]
        return payload, []

    def _active_actor_findings(self, registry: dict[str, Any]) -> list[SemanticFinding]:
        findings: list[SemanticFinding] = []
        active_actor_id = str(registry.get("active_actor_id", "")).strip()
        actors = registry.get("actors", []) if isinstance(registry.get("actors"), list) else []
        roles = registry.get("roles", []) if isinstance(registry.get("roles"), list) else []
        role_ids = {str(role.get("role_id", "")).strip() for role in roles if isinstance(role, dict)}
        actor = next((item for item in actors if isinstance(item, dict) and item.get("actor_id") == active_actor_id), None)
        if not active_actor_id or actor is None:
            findings.append(
                self._finding(
                    finding_id="MIASI_SEMANTIC_ACTIVE_ACTOR_UNKNOWN",
                    rule_id="SEM-RBAC-001",
                    severity=SemanticSeverity.BLOCK,
                    message="Active local actor must be declared in identity registry.",
                    category="rbac",
                    subject_type="actor",
                    subject_id=active_actor_id or "<missing>",
                    path=IDENTITY_REGISTRY_FILE.as_posix(),
                )
            )
            return findings
        if actor.get("status") != "active":
            findings.append(
                self._finding(
                    finding_id="MIASI_SEMANTIC_ACTIVE_ACTOR_INACTIVE",
                    rule_id="SEM-RBAC-001",
                    severity=SemanticSeverity.BLOCK,
                    message="Active local actor is not active.",
                    category="rbac",
                    subject_type="actor",
                    subject_id=active_actor_id,
                    path=IDENTITY_REGISTRY_FILE.as_posix(),
                    metadata={"actor": actor},
                )
            )
        unknown_roles = [role_id for role_id in actor.get("roles", []) if role_id not in role_ids]
        if unknown_roles:
            findings.append(
                self._finding(
                    finding_id="MIASI_SEMANTIC_ACTIVE_ACTOR_UNKNOWN_ROLE",
                    rule_id="SEM-RBAC-001",
                    severity=SemanticSeverity.BLOCK,
                    message="Active local actor references unknown roles.",
                    category="rbac",
                    subject_type="actor",
                    subject_id=active_actor_id,
                    path=IDENTITY_REGISTRY_FILE.as_posix(),
                    metadata={"unknown_roles": unknown_roles},
                )
            )
        if actor.get("remote_auth_enabled") is not False:
            findings.append(
                self._finding(
                    finding_id="MIASI_SEMANTIC_REMOTE_AUTH_ENABLED",
                    rule_id="SEM-RBAC-001",
                    severity=SemanticSeverity.BLOCK,
                    message="Active actor must not enable remote authentication in local-first mode.",
                    category="rbac",
                    subject_type="actor",
                    subject_id=active_actor_id,
                    path=IDENTITY_REGISTRY_FILE.as_posix(),
                    metadata={"actor": actor},
                )
            )
        return findings

    def _approval_role_findings(self, registry: dict[str, Any]) -> list[SemanticFinding]:
        roles = registry.get("roles", []) if isinstance(registry.get("roles"), list) else []
        permissions = {
            str(permission).strip()
            for role in roles
            if isinstance(role, dict)
            for permission in role.get("permissions", [])
        }
        required_any = {"*", "tool.execute.approve", "approval.decide.critical", "patch.apply.approve", "filesystem.write.approve"}
        if not permissions.intersection(required_any):
            return [
                self._finding(
                    finding_id="MIASI_SEMANTIC_APPROVAL_ROLE_MISSING",
                    rule_id="SEM-RBAC-001",
                    severity=SemanticSeverity.BLOCK,
                    message="RBAC roles must expose at least one approval/critical-action permission for sensitive actions.",
                    category="rbac",
                    subject_type="identity_registry",
                    subject_id="roles",
                    path=IDENTITY_REGISTRY_FILE.as_posix(),
                    metadata={"required_any": sorted(required_any), "permissions": sorted(permissions)},
                )
            ]
        return []

    def _validate_policy_contradictions(self, bundle: MiasiRegistryBundle) -> SemanticRuleResult:
        findings: list[SemanticFinding] = []
        grouped: dict[tuple[str, str], list[PolicyRule]] = {}
        for rule in bundle.rules:
            grouped.setdefault((rule.domain.lower(), rule.action.lower()), []).append(rule)
        for (domain, action), rules in grouped.items():
            effects = {rule.default_effect for rule in rules}
            if len(effects) > 1:
                findings.append(
                    self._finding(
                        finding_id="MIASI_SEMANTIC_POLICY_CONTRADICTION",
                        rule_id="SEM-POLICY-CONTRADICTION-001",
                        severity=SemanticSeverity.BLOCK,
                        message="Policy Matrix has contradictory effects for the same domain/action without explicit precedence.",
                        category="policy",
                        subject_type="policy_action",
                        subject_id=f"{domain}:{action}",
                        path=POLICY_MATRIX_FILE.as_posix(),
                        metadata={"effects": sorted(effects), "rules": [rule.to_dict() for rule in rules]},
                    )
                )
        return self._rule_result(
            rule_id="SEM-POLICY-CONTRADICTION-001",
            title="Policy Matrix must not contain contradictory allow/block/deny effects",
            findings=findings,
            subjects_evaluated=len(grouped),
            summary={"policy_actions_total": len(grouped)},
        )

    def _validate_no_go_policy_rules(self, bundle: MiasiRegistryBundle) -> SemanticRuleResult:
        findings: list[SemanticFinding] = []
        for rule in bundle.rules:
            identity = f"{rule.domain}.{rule.action}.{rule.rule_id}".lower()
            for no_go, markers in NO_GO_ACTION_MARKERS.items():
                if any(marker in identity for marker in markers) and rule.default_effect == "allow":
                    findings.append(
                        self._finding(
                            finding_id="MIASI_SEMANTIC_NO_GO_RULE_ALLOWED",
                            rule_id="SEM-NO-GO-001",
                            severity=SemanticSeverity.BLOCK,
                            message=f"No-go policy rule for {no_go} is allow; it must remain deny/block until a future ADR, sandbox and test contract approve it.",
                            category="no-go",
                            subject_type="policy_rule",
                            subject_id=rule.rule_id,
                            path=POLICY_MATRIX_FILE.as_posix(),
                            metadata=rule.to_dict(),
                        )
                    )
        return self._rule_result(
            rule_id="SEM-NO-GO-001",
            title="Remote/plugin/connector execute no-go policy rules must remain blocked",
            findings=findings,
            subjects_evaluated=len(bundle.rules),
            summary={"no_go_domains": sorted(NO_GO_ACTION_MARKERS)},
        )

    def _rule_result(
        self,
        *,
        rule_id: str,
        title: str,
        findings: list[SemanticFinding],
        subjects_evaluated: int,
        summary: dict[str, Any] | None = None,
    ) -> SemanticRuleResult:
        if findings:
            return SemanticRuleResult.from_findings(
                rule_id=rule_id,
                title=title,
                findings=findings,
                subjects_evaluated=subjects_evaluated,
                summary=summary or {},
            )
        return SemanticRuleResult(
            rule_id=rule_id,
            title=title,
            status=SemanticRuleStatus.PASS,
            severity=SemanticSeverity.INFO,
            subjects_evaluated=subjects_evaluated,
            findings=(),
            summary=summary or {},
        )

    @staticmethod
    def _finding(
        *,
        finding_id: str,
        rule_id: str,
        severity: SemanticSeverity,
        message: str,
        category: str,
        subject_type: str,
        subject_id: str,
        path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SemanticFinding:
        return SemanticFinding(
            finding_id=finding_id,
            rule_id=rule_id,
            severity=severity,
            message=message,
            category=category,
            subject_type=subject_type,
            subject_id=subject_id,
            path=path,
            metadata=metadata or {},
        )

    @staticmethod
    def _text_has_any(text: str, tokens: tuple[str, ...]) -> bool:
        lowered = str(text or "").lower()
        return any(token.lower() in lowered for token in tokens)

    @classmethod
    def _rules_have_any_token(cls, rules: list[PolicyRule], tokens: tuple[str, ...]) -> bool:
        return any(cls._text_has_any(rule.gate, tokens) or cls._text_has_any(rule.rule_id, tokens) for rule in rules)

    @staticmethod
    def _is_generic_approval_gate(rule: PolicyRule) -> bool:
        gate = rule.gate.strip().lower()
        if gate in {"approval", "approvalpolicy", "approval required", "manual approval"}:
            return True
        # A sensitive approval gate should name a concrete checker/service or bind RBAC/actor semantics.
        return rule.approval_required and not any(token in gate for token in ("approvalpolicychecker", "approvalservice", "rbac", "actor", "identity"))

    @staticmethod
    def _tool_needs_secret_guard(tool: ToolSpec) -> bool:
        identifier = f"{tool.tool_id} {tool.name}".lower()
        sensitive_name = any(
            marker in identifier
            for marker in ("secret", "model", "security", "connector", "plugin", "remote", "audit", "compliance", "enterprise", "release")
        )
        return tool.risk_level in {"high", "medium_high"} and (tool.side_effect in {"controlled_write", "optional_write", "network_cost"} or sensitive_name)

    @staticmethod
    def _looks_like_no_go_tool(identity: str, rule_text: str) -> bool:
        combined = f"{identity} {rule_text}".lower()
        if "remote" in combined and any(marker in combined for marker in ("execute", "runner", "auth", "cloud_control")):
            return True
        if "plugin" in combined and any(marker in combined for marker in ("execute", "loader", "code")):
            return True
        if "connector" in combined and any(marker in combined for marker in ("write", "execute", "call_execute")):
            return True
        return False


    def _load_json_payload(
        self,
        *,
        path: Path,
        rule_id: str,
        category: str,
        subject_type: str,
        subject_id: str,
    ) -> tuple[dict[str, Any] | None, list[SemanticFinding]]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return None, [
                self._finding(
                    finding_id="MIASI_SEMANTIC_JSON_INVALID",
                    rule_id=rule_id,
                    severity=SemanticSeverity.BLOCK,
                    message="Semantic evidence JSON is not parseable.",
                    category=category,
                    subject_type=subject_type,
                    subject_id=subject_id,
                    path=self._relative_path(path),
                    metadata={"error": str(exc)},
                )
            ]
        if not isinstance(payload, dict):
            return None, [
                self._finding(
                    finding_id="MIASI_SEMANTIC_JSON_SHAPE_INVALID",
                    rule_id=rule_id,
                    severity=SemanticSeverity.BLOCK,
                    message="Semantic evidence JSON must be an object.",
                    category=category,
                    subject_type=subject_type,
                    subject_id=subject_id,
                    path=self._relative_path(path),
                )
            ]
        return payload, []

    def _load_optional_json_payload(
        self,
        *,
        relative_path: Path,
        rule_id: str,
        category: str,
        subject_type: str,
        subject_id: str,
    ) -> tuple[dict[str, Any] | None, list[SemanticFinding]]:
        path = self.root / relative_path
        if not path.is_file():
            return None, [
                self._finding(
                    finding_id="MIASI_SEMANTIC_EVIDENCE_FILE_MISSING",
                    rule_id=rule_id,
                    severity=SemanticSeverity.WARNING,
                    message="Optional semantic evidence file is missing; this is non-blocking for fixture workspaces but must be closed before hito completion when applicable.",
                    category=category,
                    subject_type=subject_type,
                    subject_id=subject_id,
                    path=relative_path.as_posix(),
                )
            ]
        return self._load_json_payload(path=path, rule_id=rule_id, category=category, subject_type=subject_type, subject_id=subject_id)

    @staticmethod
    def _count_semantic_contracts(contracts: list[Any]) -> int:
        total = 0
        for contract in contracts:
            if not isinstance(contract, dict):
                continue
            text = json.dumps(contract, sort_keys=True).lower()
            if "test_miasi_semantic_validator" in text or "miasi semantic" in text or "miasissemantic" in text or "miasi_semantic" in text:
                total += 1
        return total

    @staticmethod
    def _agent_autonomy_number(value: str) -> int:
        digits = "".join(ch for ch in str(value) if ch.isdigit())
        return int(digits) if digits else -1

    def _relative_path(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    @staticmethod
    def _report_status(rule_results: list[SemanticRuleResult]) -> str:
        severities = [normalize_semantic_severity(rule.severity) for rule in rule_results]
        if any(severity == SemanticSeverity.BLOCK for severity in severities):
            return "blocked"
        if any(severity == SemanticSeverity.ERROR for severity in severities):
            return "error"
        if any(severity == SemanticSeverity.WARNING for severity in severities):
            return "warning"
        return "pass"

    def _command_result(self, *, report: MiasiSemanticReport, schema_result: CommandResult | None) -> CommandResult:
        payload = report.to_dict()
        findings = [self._to_cli_finding(finding) for finding in report.findings]
        if schema_result is not None and not schema_result.ok:
            findings.extend(
                Finding(
                    id=f"MIASI_SEMANTIC_REPORT_{finding.id}",
                    message=finding.message,
                    severity=finding.severity,
                    path=finding.path,
                    metadata={"source": "MiasiSemanticReport schema", **(finding.metadata or {})},
                )
                for finding in schema_result.findings
            )
        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        ok = not blocking
        exit_code = ExitCode.BLOCK if any(finding.severity == Severity.BLOCK for finding in blocking) else (ExitCode.ERROR if blocking else ExitCode.PASS)
        data = {
            "summary": payload["summary"],
            "report": payload,
            "schema_validation": (schema_result.data.get("summary") if schema_result and schema_result.data else None),
            "tests_executed": False,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
        message = "MIASI semantic validation passed."
        if payload["summary"]["warning_findings_total"]:
            message = "MIASI semantic validation passed with warnings."
        if not ok:
            message = "MIASI semantic validation failed with blocking findings."
        return CommandResult(
            command="miasi semantic-validate",
            ok=ok,
            exit_code=exit_code,
            message=message,
            data=data,
            findings=findings,
        )

    @staticmethod
    def _to_cli_finding(finding: SemanticFinding) -> Finding:
        severity = normalize_semantic_severity(finding.severity)
        severity_map = {
            SemanticSeverity.INFO: Severity.INFO,
            SemanticSeverity.WARNING: Severity.WARNING,
            SemanticSeverity.ERROR: Severity.ERROR,
            SemanticSeverity.BLOCK: Severity.BLOCK,
        }
        return Finding(
            id=finding.finding_id,
            message=finding.message,
            severity=severity_map[severity],
            path=finding.path,
            metadata={
                "rule_id": finding.rule_id,
                "category": finding.category,
                "subject_type": finding.subject_type,
                "subject_id": finding.subject_id,
                **finding.metadata,
            },
        )
