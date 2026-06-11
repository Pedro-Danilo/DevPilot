from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

MIASI_CONFIG_DIR = Path(".devpilot") / "miasi"
AGENT_REGISTRY_FILE = MIASI_CONFIG_DIR / "agent_registry.json"
TOOL_REGISTRY_FILE = MIASI_CONFIG_DIR / "tool_registry.json"
POLICY_MATRIX_FILE = MIASI_CONFIG_DIR / "policy_matrix.json"

AGENT_REGISTRY_DOC = Path("docs") / "06_miasi" / "agent_registry.md"
TOOL_REGISTRY_DOC = Path("docs") / "06_miasi" / "tool_registry.md"
POLICY_MATRIX_DOC = Path("docs") / "06_miasi" / "policy_matrix.md"

ALLOWED_PHASES = {"MVP", "MVP+", "Post-MVP"}
ALLOWED_STATUSES = {"planned", "future", "implemented", "implemented-initial", "existing", "disabled"}
ALLOWED_RISKS = {"low", "medium", "medium_high", "high"}
ALLOWED_EFFECTS = {"allow", "deny", "block", "deny_unless_safe_output"}
ALLOWED_SIDE_EFFECTS = {
    "none",
    "read",
    "report",
    "simulation",
    "controlled_write",
    "optional_write",
    "controlled_execution",
    "local_compute",
    "network_cost",
}
REQUIRED_MIASI_DOCS = (
    Path("docs/06_miasi/agent_card.md"),
    Path("docs/06_miasi/tool_card.md"),
    Path("docs/06_miasi/policy_card.md"),
    Path("docs/06_miasi/eval_card.md"),
    Path("docs/06_miasi/human_approval_card.md"),
    Path("docs/06_miasi/observability_card.md"),
    AGENT_REGISTRY_DOC,
    TOOL_REGISTRY_DOC,
    POLICY_MATRIX_DOC,
)


def _repo_path(path: Path, root: Path) -> str:
    """Return a stable POSIX-style path for JSON/report contracts."""

    candidate = path.resolve()
    try:
        return candidate.relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_id(value: str) -> str:
    return value.strip().strip("`").strip()


def _parse_markdown_table(path: Path) -> list[dict[str, str]]:
    """Parse the first simple Markdown table found in a MIASI registry document.

    This is intentionally small and dependency-free. It supports the table
    shape used by DevPilot pre-code artifacts and is not a general Markdown
    parser. Sprint 11 uses it to detect drift between approved MIASI docs and
    executable JSON contracts.
    """

    if not path.is_file():
        return []
    rows: list[list[str]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    if len(rows) < 2:
        return []
    headers = [header.lower().strip() for header in rows[0]]
    parsed: list[dict[str, str]] = []
    for row in rows[1:]:
        if len(row) != len(headers):
            continue
        parsed.append({headers[index]: row[index] for index in range(len(headers))})
    return parsed


def _autonomy_number(value: str) -> int:
    match = re.search(r"A(\d)", value.upper())
    return int(match.group(1)) if match else -1


@dataclass(frozen=True)
class ToolSpec:
    tool_id: str
    name: str
    phase: str
    side_effect: str
    risk_level: str
    status: str
    requires_approval: bool
    policy_rule_ids: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolSpec":
        return cls(
            tool_id=str(data.get("tool_id", "")).strip(),
            name=str(data.get("name", "")).strip(),
            phase=str(data.get("phase", "")).strip(),
            side_effect=str(data.get("side_effect", "")).strip(),
            risk_level=str(data.get("risk_level", "")).strip(),
            status=str(data.get("status", "")).strip(),
            requires_approval=bool(data.get("requires_approval", False)),
            policy_rule_ids=tuple(str(item).strip() for item in data.get("policy_rule_ids", []) if str(item).strip()),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "phase": self.phase,
            "side_effect": self.side_effect,
            "risk_level": self.risk_level,
            "status": self.status,
            "requires_approval": self.requires_approval,
            "policy_rule_ids": list(self.policy_rule_ids),
        }


@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    name: str
    phase: str
    max_autonomy: str
    status: str
    risk_level: str
    allowed_tools: tuple[str, ...]
    required_artifacts: tuple[str, ...]
    policy_rule_ids: tuple[str, ...]
    approval_required: bool
    observability_required: bool
    eval_required: bool

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentSpec":
        return cls(
            agent_id=str(data.get("agent_id", "")).strip(),
            name=str(data.get("name", "")).strip(),
            phase=str(data.get("phase", "")).strip(),
            max_autonomy=str(data.get("max_autonomy", "")).strip(),
            status=str(data.get("status", "")).strip(),
            risk_level=str(data.get("risk_level", "")).strip(),
            allowed_tools=tuple(str(item).strip() for item in data.get("allowed_tools", []) if str(item).strip()),
            required_artifacts=tuple(str(item).strip() for item in data.get("required_artifacts", []) if str(item).strip()),
            policy_rule_ids=tuple(str(item).strip() for item in data.get("policy_rule_ids", []) if str(item).strip()),
            approval_required=bool(data.get("approval_required", False)),
            observability_required=bool(data.get("observability_required", False)),
            eval_required=bool(data.get("eval_required", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "phase": self.phase,
            "max_autonomy": self.max_autonomy,
            "status": self.status,
            "risk_level": self.risk_level,
            "allowed_tools": list(self.allowed_tools),
            "required_artifacts": list(self.required_artifacts),
            "policy_rule_ids": list(self.policy_rule_ids),
            "approval_required": self.approval_required,
            "observability_required": self.observability_required,
            "eval_required": self.eval_required,
        }


@dataclass(frozen=True)
class PolicyRule:
    rule_id: str
    domain: str
    action: str
    default_effect: str
    gate: str
    approval_required: bool
    observability_required: bool

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PolicyRule":
        return cls(
            rule_id=str(data.get("rule_id", "")).strip(),
            domain=str(data.get("domain", "")).strip(),
            action=str(data.get("action", "")).strip(),
            default_effect=str(data.get("default_effect", "")).strip(),
            gate=str(data.get("gate", "")).strip(),
            approval_required=bool(data.get("approval_required", False)),
            observability_required=bool(data.get("observability_required", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "domain": self.domain,
            "action": self.action,
            "default_effect": self.default_effect,
            "gate": self.gate,
            "approval_required": self.approval_required,
            "observability_required": self.observability_required,
        }


@dataclass(frozen=True)
class MiasiRegistryBundle:
    root: Path
    agents: tuple[AgentSpec, ...]
    tools: tuple[ToolSpec, ...]
    rules: tuple[PolicyRule, ...]
    source_paths: dict[str, str] = field(default_factory=dict)

    @property
    def tool_ids(self) -> set[str]:
        return {tool.tool_id for tool in self.tools}

    @property
    def rule_ids(self) -> set[str]:
        return {rule.rule_id for rule in self.rules}

    @property
    def agent_ids(self) -> set[str]:
        return {agent.agent_id for agent in self.agents}

    def to_summary(self) -> dict[str, Any]:
        return {
            "agents_total": len(self.agents),
            "tools_total": len(self.tools),
            "policy_rules_total": len(self.rules),
            "mvp_agents": sum(1 for agent in self.agents if agent.phase == "MVP"),
            "high_risk_tools": sum(1 for tool in self.tools if tool.risk_level == "high"),
            "approval_gated_rules": sum(1 for rule in self.rules if rule.approval_required),
            "source_paths": self.source_paths,
        }


class MiasiRegistryValidator:
    """Executable MIASI validator for Agent Registry, Tool Registry and Policy Matrix.

    Sprint 11 converts approved MIASI documents into deterministic contracts.
    The validator is local-first, does not run agents/tools and only checks
    declarative consistency, policy coverage and safety gates.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def load_bundle(self) -> tuple[MiasiRegistryBundle | None, list[Finding]]:
        findings: list[Finding] = []
        paths = {
            "agent_registry": self.root / AGENT_REGISTRY_FILE,
            "tool_registry": self.root / TOOL_REGISTRY_FILE,
            "policy_matrix": self.root / POLICY_MATRIX_FILE,
        }
        for key, path in paths.items():
            if not path.is_file():
                findings.append(
                    Finding(
                        id="MIASI_CONFIG_MISSING",
                        message=f"Required executable MIASI config is missing: {key}.",
                        severity=Severity.BLOCK,
                        path=_repo_path(path, self.root),
                    )
                )
        if findings:
            return None, findings

        try:
            agent_payload = _load_json(paths["agent_registry"])
            tool_payload = _load_json(paths["tool_registry"])
            matrix_payload = _load_json(paths["policy_matrix"])
        except json.JSONDecodeError as exc:
            findings.append(
                Finding(
                    id="MIASI_CONFIG_JSON_INVALID",
                    message=f"Executable MIASI JSON is invalid: {exc}",
                    severity=Severity.ERROR,
                )
            )
            return None, findings

        bundle = MiasiRegistryBundle(
            root=self.root,
            agents=tuple(AgentSpec.from_dict(item) for item in agent_payload.get("agents", [])),
            tools=tuple(ToolSpec.from_dict(item) for item in tool_payload.get("tools", [])),
            rules=tuple(PolicyRule.from_dict(item) for item in matrix_payload.get("rules", [])),
            source_paths={name: _repo_path(path, self.root) for name, path in paths.items()},
        )
        return bundle, findings

    def validate_all(self) -> CommandResult:
        bundle, findings = self.load_bundle()
        if bundle is None:
            return self._result(
                command="miasi validate",
                bundle=None,
                findings=findings,
                message="MIASI executable registry validation failed before consistency checks.",
            )
        findings.extend(self._validate_required_docs())
        findings.extend(self._validate_policy_matrix(bundle))
        findings.extend(self._validate_tool_registry(bundle))
        findings.extend(self._validate_agent_registry(bundle))
        findings.extend(self._validate_document_drift(bundle))
        return self._result(
            command="miasi validate",
            bundle=bundle,
            findings=findings,
            message="MIASI executable registry validation passed.",
        )

    def validate_agents(self) -> CommandResult:
        bundle, findings = self.load_bundle()
        if bundle is not None:
            findings.extend(self._validate_agent_registry(bundle))
            findings.extend(self._validate_agent_document_drift(bundle))
        return self._result("miasi validate-registry", bundle, findings, "MIASI Agent Registry validation passed.")

    def validate_tools(self) -> CommandResult:
        bundle, findings = self.load_bundle()
        if bundle is not None:
            findings.extend(self._validate_tool_registry(bundle))
            findings.extend(self._validate_tool_document_drift(bundle))
        return self._result("miasi validate-tools", bundle, findings, "MIASI Tool Registry validation passed.")

    def validate_policy_matrix(self) -> CommandResult:
        bundle, findings = self.load_bundle()
        if bundle is not None:
            findings.extend(self._validate_policy_matrix(bundle))
            findings.extend(self._validate_policy_document_drift(bundle))
        return self._result("miasi validate-policy-matrix", bundle, findings, "MIASI Policy Matrix validation passed.")

    def _validate_required_docs(self) -> list[Finding]:
        findings: list[Finding] = []
        for relative in REQUIRED_MIASI_DOCS:
            path = self.root / relative
            if not path.is_file():
                findings.append(
                    Finding(
                        id="MIASI_REQUIRED_DOC_MISSING",
                        message="Required MIASI baseline document is missing.",
                        severity=Severity.BLOCK,
                        path=relative.as_posix(),
                    )
                )
        return findings

    def _validate_policy_matrix(self, bundle: MiasiRegistryBundle) -> list[Finding]:
        findings: list[Finding] = []
        seen: set[str] = set()
        required_domains = {"Docs", "Filesystem", "Git", "Patch", "Model", "Agent", "Secrets", "Deployment"}
        domains = {rule.domain for rule in bundle.rules}
        for rule in bundle.rules:
            if not rule.rule_id:
                findings.append(Finding("MIASI_POLICY_RULE_ID_MISSING", "Policy rule is missing rule_id.", Severity.BLOCK))
            if rule.rule_id in seen:
                findings.append(Finding("MIASI_POLICY_RULE_DUPLICATE", "Policy rule_id is duplicated.", Severity.BLOCK, metadata={"rule_id": rule.rule_id}))
            seen.add(rule.rule_id)
            if rule.default_effect not in ALLOWED_EFFECTS:
                findings.append(Finding("MIASI_POLICY_EFFECT_INVALID", "Policy rule has invalid default_effect.", Severity.BLOCK, metadata=rule.to_dict()))
            if not rule.gate:
                findings.append(Finding("MIASI_POLICY_GATE_MISSING", "Policy rule has no executable gate reference.", Severity.BLOCK, metadata=rule.to_dict()))
            if rule.default_effect in {"deny", "block"} and not rule.observability_required:
                findings.append(Finding("MIASI_POLICY_OBSERVABILITY_MISSING", "Deny/block policy rules must be observable.", Severity.BLOCK, metadata=rule.to_dict()))
        for domain in sorted(required_domains - domains):
            findings.append(Finding("MIASI_POLICY_DOMAIN_MISSING", "Policy Matrix lacks required domain coverage.", Severity.BLOCK, metadata={"domain": domain}))
        if not findings:
            findings.append(Finding("MIASI_POLICY_MATRIX_PASS", "Policy Matrix coverage passed.", Severity.INFO))
        return findings

    def _validate_tool_registry(self, bundle: MiasiRegistryBundle) -> list[Finding]:
        findings: list[Finding] = []
        seen: set[str] = set()
        for tool in bundle.tools:
            if not tool.tool_id:
                findings.append(Finding("MIASI_TOOL_ID_MISSING", "Tool is missing tool_id.", Severity.BLOCK))
            if tool.tool_id in seen:
                findings.append(Finding("MIASI_TOOL_ID_DUPLICATE", "Tool ID is duplicated.", Severity.BLOCK, metadata={"tool_id": tool.tool_id}))
            seen.add(tool.tool_id)
            if tool.phase not in ALLOWED_PHASES:
                findings.append(Finding("MIASI_TOOL_PHASE_INVALID", "Tool has invalid phase.", Severity.BLOCK, metadata=tool.to_dict()))
            if tool.status not in ALLOWED_STATUSES:
                findings.append(Finding("MIASI_TOOL_STATUS_INVALID", "Tool has invalid status.", Severity.BLOCK, metadata=tool.to_dict()))
            if tool.risk_level not in ALLOWED_RISKS:
                findings.append(Finding("MIASI_TOOL_RISK_INVALID", "Tool has invalid risk level.", Severity.BLOCK, metadata=tool.to_dict()))
            if tool.side_effect not in ALLOWED_SIDE_EFFECTS:
                findings.append(Finding("MIASI_TOOL_SIDE_EFFECT_INVALID", "Tool has invalid side_effect.", Severity.BLOCK, metadata=tool.to_dict()))
            if tool.risk_level == "high" and tool.side_effect in {"controlled_execution", "network_cost", "optional_write"} and not tool.requires_approval:
                findings.append(Finding("MIASI_TOOL_APPROVAL_REQUIRED", "High-risk side-effecting tools require approval.", Severity.BLOCK, metadata=tool.to_dict()))
            if not tool.policy_rule_ids:
                findings.append(Finding("MIASI_TOOL_POLICY_MISSING", "Tool has no Policy Matrix coverage.", Severity.BLOCK, metadata=tool.to_dict()))
            for rule_id in tool.policy_rule_ids:
                if rule_id not in bundle.rule_ids:
                    findings.append(Finding("MIASI_TOOL_POLICY_UNKNOWN", "Tool references unknown policy rule.", Severity.BLOCK, metadata={"tool_id": tool.tool_id, "rule_id": rule_id}))
        if not findings:
            findings.append(Finding("MIASI_TOOL_REGISTRY_PASS", "Tool Registry validation passed.", Severity.INFO))
        return findings

    def _validate_agent_registry(self, bundle: MiasiRegistryBundle) -> list[Finding]:
        findings: list[Finding] = []
        seen: set[str] = set()
        for agent in bundle.agents:
            if not agent.agent_id:
                findings.append(Finding("MIASI_AGENT_ID_MISSING", "Agent is missing agent_id.", Severity.BLOCK))
            if agent.agent_id in seen:
                findings.append(Finding("MIASI_AGENT_ID_DUPLICATE", "Agent ID is duplicated.", Severity.BLOCK, metadata={"agent_id": agent.agent_id}))
            seen.add(agent.agent_id)
            if agent.phase not in ALLOWED_PHASES:
                findings.append(Finding("MIASI_AGENT_PHASE_INVALID", "Agent has invalid phase.", Severity.BLOCK, metadata=agent.to_dict()))
            if agent.status not in ALLOWED_STATUSES:
                findings.append(Finding("MIASI_AGENT_STATUS_INVALID", "Agent has invalid status.", Severity.BLOCK, metadata=agent.to_dict()))
            if agent.risk_level not in ALLOWED_RISKS:
                findings.append(Finding("MIASI_AGENT_RISK_INVALID", "Agent has invalid risk level.", Severity.BLOCK, metadata=agent.to_dict()))
            autonomy = _autonomy_number(agent.max_autonomy)
            if autonomy < 0:
                findings.append(Finding("MIASI_AGENT_AUTONOMY_INVALID", "Agent has invalid autonomy level.", Severity.BLOCK, metadata=agent.to_dict()))
            if agent.phase == "MVP" and autonomy > 2:
                findings.append(Finding("MIASI_AGENT_MVP_AUTONOMY_TOO_HIGH", "MVP agents must not exceed A2.", Severity.BLOCK, metadata=agent.to_dict()))
            if autonomy >= 4 and not agent.approval_required:
                findings.append(Finding("MIASI_AGENT_APPROVAL_REQUIRED", "A4+ agents require human approval policy.", Severity.BLOCK, metadata=agent.to_dict()))
            if not agent.observability_required:
                findings.append(Finding("MIASI_AGENT_OBSERVABILITY_REQUIRED", "All registered agents require observability.", Severity.BLOCK, metadata=agent.to_dict()))
            if not agent.eval_required:
                findings.append(Finding("MIASI_AGENT_EVAL_REQUIRED", "All registered agents require eval coverage.", Severity.BLOCK, metadata=agent.to_dict()))
            if not agent.allowed_tools:
                findings.append(Finding("MIASI_AGENT_TOOLS_MISSING", "Agent has no allowed tools.", Severity.BLOCK, metadata=agent.to_dict()))
            for tool_id in agent.allowed_tools:
                if tool_id not in bundle.tool_ids:
                    findings.append(Finding("MIASI_AGENT_TOOL_UNKNOWN", "Agent references unknown tool.", Severity.BLOCK, metadata={"agent_id": agent.agent_id, "tool_id": tool_id}))
            if not agent.policy_rule_ids:
                findings.append(Finding("MIASI_AGENT_POLICY_MISSING", "Agent has no Policy Matrix coverage.", Severity.BLOCK, metadata=agent.to_dict()))
            for rule_id in agent.policy_rule_ids:
                if rule_id not in bundle.rule_ids:
                    findings.append(Finding("MIASI_AGENT_POLICY_UNKNOWN", "Agent references unknown policy rule.", Severity.BLOCK, metadata={"agent_id": agent.agent_id, "rule_id": rule_id}))
        if not findings:
            findings.append(Finding("MIASI_AGENT_REGISTRY_PASS", "Agent Registry validation passed.", Severity.INFO))
        return findings

    def _validate_document_drift(self, bundle: MiasiRegistryBundle) -> list[Finding]:
        return self._validate_agent_document_drift(bundle) + self._validate_tool_document_drift(bundle) + self._validate_policy_document_drift(bundle)

    def _validate_agent_document_drift(self, bundle: MiasiRegistryBundle) -> list[Finding]:
        rows = _parse_markdown_table(self.root / AGENT_REGISTRY_DOC)
        doc_ids = {_normalize_id(row.get("agent id", "")) for row in rows if row.get("agent id")}
        return self._drift_findings("MIASI_AGENT_DOC_DRIFT", "Agent Registry executable config is missing an agent declared in the MIASI document.", doc_ids, bundle.agent_ids)

    def _validate_tool_document_drift(self, bundle: MiasiRegistryBundle) -> list[Finding]:
        rows = _parse_markdown_table(self.root / TOOL_REGISTRY_DOC)
        doc_ids = {_normalize_id(row.get("tool id", "")) for row in rows if row.get("tool id")}
        return self._drift_findings("MIASI_TOOL_DOC_DRIFT", "Tool Registry executable config is missing a tool declared in the MIASI document.", doc_ids, bundle.tool_ids)

    def _validate_policy_document_drift(self, bundle: MiasiRegistryBundle) -> list[Finding]:
        rows = _parse_markdown_table(self.root / POLICY_MATRIX_DOC)
        domains = {row.get("dominio", "").strip() for row in rows if row.get("dominio")}
        rule_domains = {rule.domain for rule in bundle.rules}
        return self._drift_findings("MIASI_POLICY_DOC_DRIFT", "Policy Matrix executable config is missing a domain declared in the MIASI document.", domains, rule_domains)

    @staticmethod
    def _drift_findings(id_: str, message: str, documented: set[str], executable: set[str]) -> list[Finding]:
        findings: list[Finding] = []
        for missing in sorted(documented - executable):
            findings.append(Finding(id=id_, message=message, severity=Severity.BLOCK, metadata={"missing": missing}))
        return findings

    def _result(self, command: str, bundle: MiasiRegistryBundle | None, findings: list[Finding], message: str) -> CommandResult:
        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]
        failing = [finding for finding in findings if finding.severity == Severity.FAIL]
        ok = not blocking and not failing
        exit_code = ExitCode.BLOCK if blocking else (ExitCode.FAIL if failing else ExitCode.PASS)
        data: dict[str, Any] = {
            "summary": bundle.to_summary() if bundle else {},
            "contract": "MIASIExecutableRegistry",
            "preliminary": True,
            "notes": [
                "Sprint 11 validates declarations only; it does not execute agents or tools.",
                "Agent runtime, eval harness and approval workflows remain future sprints.",
            ],
        }
        if bundle:
            data["agents"] = [agent.to_dict() for agent in bundle.agents]
            data["tools"] = [tool.to_dict() for tool in bundle.tools]
            data["policy_rules"] = [rule.to_dict() for rule in bundle.rules]
        return CommandResult(
            command=command,
            ok=ok,
            exit_code=exit_code,
            message=message if ok else "MIASI executable registry validation failed.",
            data=data,
            findings=findings,
        )
