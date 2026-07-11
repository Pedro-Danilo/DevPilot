from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas import SchemaValidator

POST_H_033_A_CREATED_BY = "POST-H-033-A"
VALIDATOR_INVENTORY_SCHEMA_ID = "SCHEMA-DEVPL-VALIDATOR-INVENTORY-V1"
VALIDATOR_MIGRATION_REPORT_SCHEMA_ID = "SCHEMA-DEVPL-VALIDATOR-MIGRATION-REPORT-V1"
VALIDATOR_INVENTORY_CONTRACT = "ValidatorInventory"
VALIDATOR_MIGRATION_REPORT_CONTRACT = "ValidatorMigrationReport"

MINIMUM_VALIDATOR_IDS = {
    "validators.artifact_profiles",
    "validators.frontmatter",
    "validators.readiness",
    "miasi.registry",
    "miasi.semantic",
    "miasi.semantic_rules",
    "docs_governance.validator",
    "docs_governance.backlogs",
    "docs_governance.drift",
    "policy.prompt_guard",
    "policy.tool_injection_guard",
    "policy.secrets",
    "validation.artifact_profile_registry",
    "schemas.validator",
}

ALLOWED_DECISIONS = {"migrate", "keep", "fallback", "parser", "security-core"}
BLOCKED_RUNTIME_FLAGS = (
    "runtime_behavior_changed",
    "llm_judge_used",
    "network_used",
    "external_api_used",
    "remote_execution_enabled",
    "connector_write_enabled",
    "plugin_execution_enabled",
    "source_mutations_performed",
    "critical_rules_disable_allowed",
)


@dataclass(frozen=True)
class ValidatorInventoryOptions:
    inventory_path: Path = Path(".devpilot/validation/validator_inventory.json")
    migration_plan_path: Path = Path(".devpilot/validation/validator_migration_plan.json")
    write_report: bool = False
    output_json: Path = Path("outputs/reports/validator_inventory_migration_plan_report.json")
    output_markdown: Path = Path("outputs/reports/validator_inventory_migration_plan_report.md")


class ValidatorInventoryManager:
    """Evaluate POST-H-033-A validator inventory and migration plan.

    The manager is intentionally read-only by default. It validates that the
    inventory covers the minimum validator set, classifies every hardcoded rule
    element with an explicit decision and preserves deterministic/runtime-safe
    invariants. It does not alter validator runtime behavior.
    """

    def __init__(self, root: Path, options: ValidatorInventoryOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ValidatorInventoryOptions()
        self.schema_validator = SchemaValidator(self.root)

    def evaluate(self) -> CommandResult:
        findings: list[Finding] = []
        inventory = self._read_json(self.options.inventory_path, findings)
        migration_plan = self._read_json(self.options.migration_plan_path, findings)
        if inventory is None or migration_plan is None:
            return self._result(False, findings, {}, None)

        self._validate_inventory(inventory, findings)
        self._validate_migration_plan(migration_plan, inventory, findings)

        inventory_schema_result = self.schema_validator.validate_payload(
            schema=VALIDATOR_INVENTORY_CONTRACT,
            payload=inventory,
            instance_label=str(self.options.inventory_path).replace("\\", "/"),
        )
        migration_schema_result = self.schema_validator.validate_payload(
            schema=VALIDATOR_MIGRATION_REPORT_CONTRACT,
            payload=migration_plan,
            instance_label=str(self.options.migration_plan_path).replace("\\", "/"),
        )
        if not inventory_schema_result.ok:
            findings.extend(inventory_schema_result.findings)
        if not migration_schema_result.ok:
            findings.extend(migration_schema_result.findings)

        blocking = [f for f in findings if f.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        summary = self._summary(inventory, migration_plan, blocking)
        report = {
            "schema_version": "1.0",
            "schema_id": VALIDATOR_MIGRATION_REPORT_SCHEMA_ID,
            "report_id": "devpilot-validator-inventory-migration-plan-report",
            "created_by": POST_H_033_A_CREATED_BY,
            "status": "blocked" if blocking else "implemented-initial",
            "updated_at": migration_plan.get("updated_at", "2026-07-11"),
            "inventory_path": str(self.options.inventory_path).replace("\\", "/"),
            "migration_plan_path": str(self.options.migration_plan_path).replace("\\", "/"),
            "backlog_path": migration_plan.get("backlog_path", "docs/backlogs/POST-H-033_schema_backed_validators_declarative_semantics.md"),
            "summary": summary,
            "migration_waves": migration_plan.get("migration_waves", []),
            "validator_decisions": migration_plan.get("validator_decisions", []),
            "risks": migration_plan.get("risks", []),
            "safety": migration_plan.get("safety", {}),
            "findings": [finding.to_dict() for finding in findings] or [
                {
                    "id": "VALIDATOR_INVENTORY_MIGRATION_PLAN_PASS",
                    "message": "Validator inventory and migration plan passed.",
                    "severity": "info",
                }
            ],
            "notes": migration_plan.get("notes", []),
            "limitations": migration_plan.get("limitations", []),
        }
        reports: dict[str, str] = {}
        if self.options.write_report:
            reports = self._write_reports(report)
        data = {"summary": summary, "inventory": inventory, "migration_plan": migration_plan, "report": report, "reports": reports}
        findings.append(
            Finding(
                id="VALIDATOR_INVENTORY_MIGRATION_PLAN_PASS" if not blocking else "VALIDATOR_INVENTORY_MIGRATION_PLAN_BLOCK",
                message="POST-H-033-A validator inventory and migration plan passed." if not blocking else "POST-H-033-A validator inventory and migration plan has blocking findings.",
                severity=Severity.INFO if not blocking else Severity.BLOCK,
                metadata=summary,
            )
        )
        return self._result(not blocking, findings, data, summary)

    def _read_json(self, path: Path, findings: list[Finding]) -> dict[str, Any] | None:
        resolved = self.root / path
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except FileNotFoundError:
            findings.append(Finding(id="VALIDATOR_INVENTORY_FILE_MISSING", message=f"Missing file: {path}", severity=Severity.BLOCK, path=str(path)))
            return None
        except json.JSONDecodeError as exc:
            findings.append(Finding(id="VALIDATOR_INVENTORY_INVALID_JSON", message=f"Invalid JSON in {path}: {exc.msg}", severity=Severity.ERROR, path=str(path)))
            return None
        if not isinstance(payload, dict):
            findings.append(Finding(id="VALIDATOR_INVENTORY_INVALID_PAYLOAD", message=f"Expected object JSON in {path}.", severity=Severity.BLOCK, path=str(path)))
            return None
        return payload

    def _validate_inventory(self, inventory: dict[str, Any], findings: list[Finding]) -> None:
        validators = inventory.get("validators", [])
        if not isinstance(validators, list):
            findings.append(Finding(id="VALIDATOR_INVENTORY_VALIDATORS_NOT_LIST", message="Inventory validators must be a list.", severity=Severity.BLOCK))
            return
        ids = {item.get("validator_id") for item in validators if isinstance(item, dict)}
        missing_ids = sorted(MINIMUM_VALIDATOR_IDS - ids)
        if missing_ids:
            findings.append(Finding(id="VALIDATOR_INVENTORY_MINIMUM_SET_MISSING", message="Minimum validator inventory is incomplete.", severity=Severity.BLOCK, metadata={"missing": missing_ids}))
        for item in validators:
            if not isinstance(item, dict):
                findings.append(Finding(id="VALIDATOR_INVENTORY_ITEM_INVALID", message="Validator item must be an object.", severity=Severity.BLOCK))
                continue
            validator_id = str(item.get("validator_id", ""))
            for field_name in ("owner", "module_path", "criticality", "inputs", "outputs", "tests", "migration_micro_sprint", "compatibility_strategy"):
                if not item.get(field_name):
                    findings.append(Finding(id="VALIDATOR_INVENTORY_FIELD_MISSING", message=f"Validator {validator_id} is missing {field_name}.", severity=Severity.BLOCK, metadata={"validator_id": validator_id, "field": field_name}))
            module_path = self.root / str(item.get("module_path", ""))
            if item.get("module_path") and not module_path.exists():
                findings.append(Finding(id="VALIDATOR_INVENTORY_MODULE_MISSING", message=f"Validator module does not exist: {item.get('module_path')}", severity=Severity.BLOCK, path=str(item.get("module_path"))))
            elements = item.get("hardcoded_elements", [])
            if not elements:
                findings.append(Finding(id="VALIDATOR_INVENTORY_HARDCODED_DECISION_MISSING", message=f"Validator {validator_id} has no hardcoded element decisions.", severity=Severity.BLOCK, metadata={"validator_id": validator_id}))
            for element in elements:
                decision = element.get("decision") if isinstance(element, dict) else None
                if decision not in ALLOWED_DECISIONS:
                    findings.append(Finding(id="VALIDATOR_INVENTORY_INVALID_DECISION", message=f"Validator {validator_id} has invalid hardcoded element decision.", severity=Severity.BLOCK, metadata={"validator_id": validator_id, "decision": decision}))

    def _validate_migration_plan(self, migration_plan: dict[str, Any], inventory: dict[str, Any], findings: list[Finding]) -> None:
        summary = migration_plan.get("summary", {})
        if summary.get("runtime_behavior_changed") is not False:
            findings.append(Finding(id="VALIDATOR_MIGRATION_RUNTIME_CHANGED", message="POST-H-033-A must not alter runtime validator behavior.", severity=Severity.BLOCK))
        if summary.get("llm_judge_required") is not False:
            findings.append(Finding(id="VALIDATOR_MIGRATION_LLM_JUDGE_FORBIDDEN", message="POST-H-033 cannot replace deterministic validators with an LLM judge.", severity=Severity.BLOCK))
        if summary.get("critical_defenses_disable_allowed") is not False:
            findings.append(Finding(id="VALIDATOR_MIGRATION_CRITICAL_DISABLE_FORBIDDEN", message="Critical defenses cannot be made disableable by configuration.", severity=Severity.BLOCK))
        if summary.get("no_go_gates_preserved") is not True:
            findings.append(Finding(id="VALIDATOR_MIGRATION_NO_GO_GATES_NOT_PRESERVED", message="No-go gates must remain preserved.", severity=Severity.BLOCK))
        safety = migration_plan.get("safety", {})
        for flag in BLOCKED_RUNTIME_FLAGS:
            if safety.get(flag) is not False:
                findings.append(Finding(id="VALIDATOR_MIGRATION_SAFETY_FLAG_BLOCK", message=f"Safety flag must remain false: {flag}", severity=Severity.BLOCK, metadata={"flag": flag, "value": safety.get(flag)}))
        if safety.get("local_first") is not True or safety.get("read_only") is not True:
            findings.append(Finding(id="VALIDATOR_MIGRATION_LOCAL_READONLY_REQUIRED", message="Migration plan must remain local-first and read-only.", severity=Severity.BLOCK))
        waves = migration_plan.get("migration_waves", [])
        planned = {wave.get("micro_sprint") for wave in waves if isinstance(wave, dict)}
        for expected in {"POST-H-033-B", "POST-H-033-C", "POST-H-033-D", "POST-H-033-E", "POST-H-033-F"}:
            if expected not in planned:
                findings.append(Finding(id="VALIDATOR_MIGRATION_WAVE_MISSING", message=f"Migration wave missing: {expected}", severity=Severity.BLOCK, metadata={"micro_sprint": expected}))

    def _summary(self, inventory: dict[str, Any], migration_plan: dict[str, Any], blocking: list[Finding]) -> dict[str, Any]:
        inventory_summary = inventory.get("summary", {}) if isinstance(inventory.get("summary"), dict) else {}
        plan_summary = migration_plan.get("summary", {}) if isinstance(migration_plan.get("summary"), dict) else {}
        return {
            "created_by": POST_H_033_A_CREATED_BY,
            "status": "blocked" if blocking else "implemented-initial",
            "decision": "BLOCK" if blocking else "PASS",
            "preliminary": True,
            "validators_total": inventory_summary.get("validators_total", 0),
            "hardcoded_elements_total": inventory_summary.get("hardcoded_elements_total", 0),
            "hardcoded_elements_with_decision_total": plan_summary.get("hardcoded_elements_with_decision_total", 0),
            "migration_waves_total": plan_summary.get("migration_waves_total", 0),
            "fallbacks_declared_total": plan_summary.get("fallbacks_declared_total", 0),
            "runtime_behavior_changed": False,
            "llm_judge_required": False,
            "external_dependencies_added": False,
            "critical_defenses_disable_allowed": False,
            "no_go_gates_preserved": True,
            "network_used": False,
            "external_api_used": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "source_mutations_performed": False,
            "blocking_findings_total": len(blocking),
            "findings_total": len(blocking),
        }

    def _write_reports(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = self.root / self.options.output_json
        md_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        summary = report.get("summary", {})
        md_path.write_text(
            "# POST-H-033-A — Validator inventory and migration plan report\n\n"
            f"Decision: `{summary.get('decision')}`\n\n"
            f"Validators: `{summary.get('validators_total')}`\n\n"
            f"Hardcoded elements: `{summary.get('hardcoded_elements_total')}`\n\n"
            "Runtime behavior changed: `false`\n\n"
            "LLM judge required: `false`\n\n"
            "Critical defenses disable allowed: `false`\n",
            encoding="utf-8",
        )
        return {"json": str(self.options.output_json).replace("\\", "/"), "markdown": str(self.options.output_markdown).replace("\\", "/")}

    def _result(self, ok: bool, findings: list[Finding], data: dict[str, Any], summary: dict[str, Any] | None) -> CommandResult:
        return CommandResult(
            command="validator inventory evaluate",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Validator inventory and migration plan passed." if ok else "Validator inventory and migration plan blocked.",
            data=data if data else {"summary": summary or {}},
            findings=findings,
        )
