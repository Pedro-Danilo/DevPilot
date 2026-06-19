from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.miasi import MiasiRegistryValidator, PolicyRule
from devpilot_core.multiagent.coordinator import MultiAgentCoordinator, MultiAgentRunOptions
from devpilot_core.observability import EventLogger
from devpilot_core.schemas import SchemaValidator

_WORKFLOW_SCHEMA = "docs/schemas/multiagent_workflow.schema.json"
_WORKFLOW_DIR = ".devpilot/workflows"
_IMPLEMENTED_AGENT_STATUSES = {"implemented", "implemented-initial"}


@dataclass(frozen=True)
class MultiAgentWorkflowRunOptions:
    """Options for FUNC-SPRINT-91 workflow-registry based multiagent runs."""

    workflow: str
    target: str | None = None
    dry_run: bool = True
    max_steps: int = 10
    workflow_dir: str = _WORKFLOW_DIR
    schema_path: str = _WORKFLOW_SCHEMA


class MultiAgentWorkflowRunner:
    """Run predeclared SDLC multiagent workflows from local JSON definitions.

    Sprint 91 deliberately keeps this runner as a registry-backed wrapper around
    the governed Sprint 90 coordinator. Workflow definitions are data contracts:
    they are validated by JSON Schema, checked against MIASI, and executed only
    in dry-run/report-only mode. No dynamic planner, plugin loader, shell, red,
    remote runner or destructive tool path is introduced here.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.events = EventLogger(self.root)

    def run(self, options: MultiAgentWorkflowRunOptions) -> CommandResult:
        workflow_id = canonical_workflow_id(options.workflow)
        if not options.dry_run:
            return self._blocked(
                workflow_id,
                [
                    Finding(
                        "MULTIAGENT_WORKFLOW_REQUIRES_DRY_RUN",
                        "Registered multiagent workflows are dry-run/report-only in Sprint 91.",
                        Severity.BLOCK,
                        metadata={"workflow": workflow_id},
                    )
                ],
                message="Multiagent workflow blocked: --dry-run is required.",
            )

        workflow_path = self._resolve_workflow_path(workflow_id, options.workflow_dir)
        if workflow_path is None or not workflow_path.exists():
            return self._blocked(
                workflow_id,
                [
                    Finding(
                        "MULTIAGENT_WORKFLOW_DEFINITION_MISSING",
                        "Workflow definition was not found under .devpilot/workflows.",
                        Severity.BLOCK,
                        metadata={"workflow": workflow_id, "workflow_dir": options.workflow_dir},
                    )
                ],
                message="Multiagent workflow blocked: workflow definition is missing.",
            )

        schema_result = SchemaValidator(self.root).validate(schema=options.schema_path, instance=workflow_path)
        if not schema_result.ok:
            return self._blocked(
                workflow_id,
                schema_result.findings,
                message="Multiagent workflow blocked: workflow definition schema validation failed.",
                workflow_path=_rel(workflow_path, self.root),
            )

        try:
            workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # defensive; schema validator should catch first.
            return self._blocked(
                workflow_id,
                [Finding("MULTIAGENT_WORKFLOW_INVALID_JSON", f"Invalid workflow JSON: {exc}", Severity.ERROR, path=_rel(workflow_path, self.root))],
                message="Multiagent workflow blocked: invalid JSON.",
                workflow_path=_rel(workflow_path, self.root),
            )

        semantic_findings = self._validate_semantics(workflow, expected_workflow_id=workflow_id)
        if semantic_findings:
            return self._blocked(
                workflow_id,
                semantic_findings,
                message="Multiagent workflow blocked by semantic governance checks.",
                workflow_path=_rel(workflow_path, self.root),
            )

        target = options.target or workflow.get("default_target") or "src/devpilot_core"
        steps = [
            {
                "step_id": step["step_id"],
                "agent_id": step["agent_id"],
                "reason": step["reason"],
                "target": step.get("target") or target,
            }
            for step in workflow["steps"]
        ]
        max_steps = min(max(1, int(options.max_steps)), int(workflow.get("max_steps", len(steps))))
        coordinator_result = MultiAgentCoordinator(self.root).run(
            MultiAgentRunOptions(
                workflow=workflow_id,
                target=target,
                dry_run=True,
                max_steps=max_steps,
                workflow_steps=steps,
                workflow_source=_rel(workflow_path, self.root),
                event_sprint="FUNC-SPRINT-91",
            )
        )

        data = dict(coordinator_result.data or {})
        summary = dict(data.get("summary", {}))
        consolidated = self._consolidate(workflow, data)
        summary.update(
            {
                "workflow_definition_path": _rel(workflow_path, self.root),
                "workflow_definition_valid": True,
                "workflow_schema_path": options.schema_path,
                "workflow_report_consolidated": True,
                "report_id": workflow["outputs"]["report_id"],
                "risk_categories_total": len(consolidated["risk_categories"]),
                "recommendations_total": len(consolidated["recommendations"]),
                "mutations_performed": False,
                "destructive_actions_executed": False,
                "network_used": False,
                "external_api_used": False,
                "shell_used": False,
                "remote_execution_used": False,
            }
        )
        data["summary"] = summary
        data["workflow_definition"] = {
            "workflow_id": workflow["workflow_id"],
            "title": workflow["title"],
            "status": workflow["status"],
            "mode": workflow["mode"],
            "dry_run_required": workflow["dry_run_required"],
            "report_only": workflow["report_only"],
            "path": _rel(workflow_path, self.root),
        }
        data["consolidated_report"] = consolidated
        data["notes"] = list(data.get("notes", [])) + [
            "FUNC-SPRINT-91 loads workflows from JSON contracts and delegates execution to the governed coordinator.",
            "Workflow outputs are consolidated evidence, not automatic remediation or release approval.",
        ]

        findings = list(coordinator_result.findings)
        if coordinator_result.ok:
            findings.append(
                Finding(
                    "MULTIAGENT_SDLC_WORKFLOW_DRY_RUN_COMPLETED",
                    "Registered SDLC multiagent workflow completed in dry-run/report-only mode.",
                    Severity.INFO,
                    metadata={"workflow": workflow_id, "workflow_path": _rel(workflow_path, self.root), "steps_total": len(data.get("steps", []))},
                )
            )
        result = CommandResult(
            command="multiagent workflow run",
            ok=coordinator_result.ok,
            exit_code=coordinator_result.exit_code,
            message=(
                "Multiagent SDLC workflow completed in governed dry-run mode."
                if coordinator_result.ok
                else coordinator_result.message
            ),
            data=data,
            findings=findings,
        )
        self.events.emit_result(result, event_type="multiagent.workflow.registry.evaluated", subject=workflow_id)
        return result

    def _resolve_workflow_path(self, workflow_id: str, workflow_dir: str) -> Path | None:
        base = (self.root / workflow_dir).resolve()
        try:
            base.relative_to(self.root)
        except ValueError:
            return None
        candidate = (base / f"{workflow_id.replace('-', '_')}.json").resolve()
        try:
            candidate.relative_to(base)
        except ValueError:
            return None
        return candidate

    def _validate_semantics(self, workflow: dict[str, Any], *, expected_workflow_id: str) -> list[Finding]:
        findings: list[Finding] = []
        if workflow.get("workflow_id") != expected_workflow_id:
            findings.append(
                Finding(
                    "MULTIAGENT_WORKFLOW_ID_MISMATCH",
                    "Workflow filename/request and workflow_id must resolve to the same id.",
                    Severity.BLOCK,
                    metadata={"expected": expected_workflow_id, "actual": workflow.get("workflow_id")},
                )
            )
        safety = workflow.get("safety", {})
        for key in ["mutations_allowed", "destructive_actions_allowed", "network_allowed", "external_api_allowed", "shell_allowed", "remote_execution_allowed"]:
            if safety.get(key) is not False:
                findings.append(Finding("MULTIAGENT_WORKFLOW_UNSAFE_FLAG", "Workflow safety flags must remain false in Sprint 91.", Severity.BLOCK, metadata={"field": key, "value": safety.get(key)}))
        if workflow.get("dry_run_required") is not True or workflow.get("report_only") is not True or workflow.get("autonomy_open") is not False:
            findings.append(Finding("MULTIAGENT_WORKFLOW_MODE_BLOCKED", "Workflow must be dry-run required, report-only and without open autonomy.", Severity.BLOCK))

        bundle, load_findings = MiasiRegistryValidator(self.root).load_bundle()
        if load_findings or bundle is None:
            findings.extend(load_findings)
            return findings
        agents = {agent.agent_id: agent for agent in bundle.agents}
        rules: dict[str, PolicyRule] = {rule.rule_id: rule for rule in bundle.rules}
        for rule_id in workflow.get("policy_rule_ids", []):
            if rule_id not in rules:
                findings.append(Finding("MULTIAGENT_WORKFLOW_POLICY_UNKNOWN", "Workflow references an unknown policy rule.", Severity.BLOCK, metadata={"rule_id": rule_id}))
        seen_sequences: set[int] = set()
        seen_steps: set[str] = set()
        for step in workflow.get("steps", []):
            sequence = int(step.get("sequence", 0) or 0)
            step_id = str(step.get("step_id", ""))
            if sequence in seen_sequences or step_id in seen_steps:
                findings.append(Finding("MULTIAGENT_WORKFLOW_STEP_DUPLICATE", "Workflow step ids and sequences must be unique.", Severity.BLOCK, metadata={"step_id": step_id, "sequence": sequence}))
            seen_sequences.add(sequence)
            seen_steps.add(step_id)
            if step.get("required_trace") is not True:
                findings.append(Finding("MULTIAGENT_WORKFLOW_STEP_TRACE_REQUIRED", "Every workflow step must require trace evidence.", Severity.BLOCK, metadata={"step_id": step_id}))
            agent_id = step.get("agent_id")
            agent = agents.get(agent_id)
            if agent is None:
                findings.append(Finding("MULTIAGENT_WORKFLOW_AGENT_UNKNOWN", "Workflow references an agent absent from MIASI registry.", Severity.BLOCK, metadata={"agent_id": agent_id}))
                continue
            if agent.status not in _IMPLEMENTED_AGENT_STATUSES:
                findings.append(Finding("MULTIAGENT_WORKFLOW_AGENT_STATUS_BLOCKED", "Workflow can only use implemented/implemented-initial agents.", Severity.BLOCK, metadata={"agent_id": agent_id, "status": agent.status}))
        if seen_sequences and sorted(seen_sequences) != list(range(1, len(seen_sequences) + 1)):
            findings.append(Finding("MULTIAGENT_WORKFLOW_SEQUENCE_GAP", "Workflow step sequences must be contiguous starting at 1.", Severity.BLOCK, metadata={"sequences": sorted(seen_sequences)}))
        return findings

    def _consolidate(self, workflow: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        steps = data.get("steps", []) or []
        workflow_steps = workflow.get("steps", []) or []
        risk_categories = sorted({risk for step in workflow_steps for risk in step.get("risk_categories", [])})
        recommendations = [
            {
                "step_id": step.get("step_id"),
                "agent_id": step.get("agent_id"),
                "recommendation": f"Review `{step.get('expected_output')}` before promoting findings to backlog or patches.",
            }
            for step in workflow_steps
        ]
        child_findings_total = sum(int((step.get("summary") or {}).get("findings_total", 0) or 0) for step in steps)
        child_suggestions_total = sum(int((step.get("summary") or {}).get("suggestions_total", 0) or 0) for step in steps)
        return {
            "report_id": workflow["outputs"]["report_id"],
            "format": workflow["outputs"].get("format", "json+markdown"),
            "coverage": [step.get("step_id") for step in workflow_steps],
            "risk_categories": risk_categories,
            "child_findings_total": child_findings_total,
            "child_suggestions_total": child_suggestions_total,
            "recommendations": recommendations,
            "promotion_policy": "Manual review required before opening tasks, patches or approvals.",
            "automatic_remediation_enabled": False,
            "quality_gate": "report-only; Sprint 92 may add advanced eval/safety scoring gates.",
        }

    def _blocked(self, workflow_id: str, findings: list[Finding], *, message: str, workflow_path: str | None = None) -> CommandResult:
        result = CommandResult(
            command="multiagent workflow run",
            ok=False,
            exit_code=ExitCode.BLOCK if not any(f.severity == Severity.ERROR for f in findings) else ExitCode.ERROR,
            message=message,
            data={
                "summary": {
                    "schema_version": "1.0.0",
                    "workflow_id": workflow_id,
                    "workflow_definition_path": workflow_path,
                    "dry_run": True,
                    "workflow_definition_valid": False,
                    "mutations_performed": False,
                    "destructive_actions_executed": False,
                    "network_used": False,
                    "external_api_used": False,
                    "shell_used": False,
                    "remote_execution_used": False,
                    "preliminary": True,
                }
            },
            findings=findings,
        )
        self.events.emit_result(result, event_type="multiagent.workflow.registry.evaluated", subject=workflow_id)
        return result


def canonical_workflow_id(value: str) -> str:
    normalized = (value or "").strip().lower().replace("_", "-")
    aliases = {"sdlc": "sdlc-review", "sdlc-review": "sdlc-review", "sdlc-review-workflow": "sdlc-review"}
    return aliases.get(normalized, normalized)


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
