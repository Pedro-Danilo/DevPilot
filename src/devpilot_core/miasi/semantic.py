from __future__ import annotations

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

    POST-H-004-B intentionally remains read-only and non-executing. It loads the
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
            report_id="miasi-semantic-post-h-004-b",
            created_by="POST-H-004-B",
            status=status,
            rule_results=tuple(rule_results),
            source_paths=self.builder.source_paths(),
            no_go_gates=(
                "remote.execute must remain blocked",
                "plugin.execute must remain blocked until sandboxed",
                "connector.write must remain blocked unless future ADR/sandbox/test-contract gates approve it",
                "semantic validation must not relax PolicyEngine or execute agent/tool runtime paths",
            ),
            notes=(
                "POST-H-004-B validates agent/tool/policy declarations only; approval/RBAC/security guards are hardened in POST-H-004-C.",
                "Controlled-write tools without explicit approval are surfaced as warnings unless a present allow rule creates an immediate unsafe execution path.",
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
                        message="High-risk controlled-write tool has no explicit tool-level approval; current gates appear local/sandboxed but must be hardened in POST-H-004-C.",
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
