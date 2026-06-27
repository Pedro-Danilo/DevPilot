from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.approval.binding import ApprovalBindingRequest, StrongApprovalBindingValidator, compute_subject_hash
from devpilot_core.approval.models import ApprovalRecord, ApprovalStatus
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

POST_H_012_E_CREATED_BY = "POST-H-012-E"
APPROVAL_RBAC_HARDENING_COMMAND = "quality approval-rbac-hardening"


@dataclass(frozen=True)
class ApprovalRbacHardeningGateOptions:
    """Options for the POST-H-012-E Approval/RBAC hardening subgate.

    The gate is intentionally read-only. It validates source-controlled catalogs,
    registries, docs, test-contract metadata and deterministic PolicyEngine
    behavior without writing reports, executing tools, calling network services,
    touching providers or mutating source/runtime state.
    """

    require_runbook: bool = True
    require_human_approval_card: bool = True


class ApprovalRbacHardeningGate:
    """POST-H-012-E operational gate for local Approval/RBAC hardening.

    This gate converts the POST-H-012 A-D controls into a single quality-gate
    signal. It does not grant permissions and does not execute approval-gated
    operations. It checks that sensitive actions, strong approval binding, RBAC
    exposure reporting, PolicyEngine enforcement and approval lifecycle docs are
    present and mutually coherent.
    """

    def __init__(self, root: Path, *, options: ApprovalRbacHardeningGateOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ApprovalRbacHardeningGateOptions()

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        file_summary = self._check_required_files(findings)
        from devpilot_core.policy.sensitive_actions import SensitiveActionCatalogValidator

        catalog_result = SensitiveActionCatalogValidator(self.root).run()
        findings.extend(self._prefixed_findings(catalog_result, prefix="APPROVAL_RBAC_CATALOG"))

        from devpilot_core.identity.exposure import RbacExposureOptions, RbacExposureReporter

        exposure_result = RbacExposureReporter(
            self.root,
            options=RbacExposureOptions(write_report=False),
        ).run()
        findings.extend(self._prefixed_findings(exposure_result, prefix="APPROVAL_RBAC_EXPOSURE"))

        policy_summary = self._policy_scenarios(findings)
        binding_summary = self._binding_scenario(findings)
        docs_summary = self._documentation_checks(findings)
        contract_summary = self._test_contract_checks(findings)

        catalog_summary = catalog_result.data.get("summary", {}) if isinstance(catalog_result.data, dict) else {}
        exposure_summary = exposure_result.data.get("summary", {}) if isinstance(exposure_result.data, dict) else {}
        blocking_findings = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        summary = {
            "created_by": POST_H_012_E_CREATED_BY,
            "status": "implemented-initial",
            "preliminary": True,
            "quality_gate_ready": not blocking_findings,
            "required_files_total": file_summary["required_files_total"],
            "required_files_existing_total": file_summary["required_files_existing_total"],
            "catalog_actions_total": catalog_summary.get("actions_total", 0),
            "catalog_critical_actions_total": catalog_summary.get("critical_actions_total", 0),
            "catalog_ok": bool(catalog_result.ok),
            "rbac_exposure_ok": bool(exposure_result.ok),
            "rbac_matrix_entries_total": exposure_summary.get("matrix_entries_total", 0),
            "policy_scenarios_total": policy_summary["scenarios_total"],
            "policy_scenarios_blocked_total": policy_summary["blocked_total"],
            "policy_expected_findings_covered": policy_summary["expected_findings_covered"],
            "approval_binding_scope_mismatch_blocked": binding_summary["scope_mismatch_blocked"],
            "docs_lifecycle_documented": docs_summary["lifecycle_documented"],
            "docs_revocation_documented": docs_summary["revocation_documented"],
            "docs_actor_role_interface_documented": docs_summary["actor_role_interface_documented"],
            "test_contract_registered": contract_summary["v1_registered"],
            "test_contract_v2_registered": contract_summary["v2_registered"],
            "blocking_findings_total": len(blocking_findings),
            "findings_total": len(findings),
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "reports_written": False,
        }
        ok = not blocking_findings
        return CommandResult(
            command=APPROVAL_RBAC_HARDENING_COMMAND,
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Approval/RBAC hardening gate passed." if ok else "Approval/RBAC hardening gate blocked.",
            data={
                "summary": summary,
                "catalog_summary": catalog_summary,
                "rbac_exposure_summary": exposure_summary,
                "policy_scenarios": policy_summary["scenarios"],
                "required_files": file_summary["files"],
                "notes": [
                    "POST-H-012-E converts Approval/RBAC hardening into a hardening/industrial quality-gate subgate.",
                    "The gate is deterministic, read-only and does not execute sensitive actions.",
                    "A valid approval never overrides catalog-level non-executable, remote, connector-write or plugin-execution blocks.",
                ],
            },
            findings=findings or [Finding("APPROVAL_RBAC_HARDENING_PASS", "Approval/RBAC hardening checks passed.", Severity.INFO, metadata=summary)],
        )

    def _check_required_files(self, findings: list[Finding]) -> dict[str, Any]:
        required = [
            ".devpilot/approval/sensitive_action_catalog.json",
            ".devpilot/identity/identity_registry.json",
            ".devpilot/miasi/policy_matrix.json",
            "src/devpilot_core/approval/binding.py",
            "src/devpilot_core/approval/hardening.py",
            "src/devpilot_core/approval/policy.py",
            "src/devpilot_core/identity/exposure.py",
            "src/devpilot_core/policy/engine.py",
            "docs/03_security/approval_rbac_hardening.md",
            "docs/06_miasi/human_approval_card.md",
            "docs/05_operations/runbook.md",
            "docs/audits/post_h_012_d_policy_engine_enforcement_report.md",
            "docs/post_h_012_d_manifest.json",
            "docs/post_h_012_e_manifest.json",
            "tests/test_approval_rbac_hardening_gate.py",
        ]
        files: list[dict[str, Any]] = []
        for item in required:
            exists = (self.root / item).exists()
            files.append({"path": item, "exists": exists})
            if not exists:
                findings.append(Finding("APPROVAL_RBAC_REQUIRED_FILE_MISSING", "Approval/RBAC hardening required file is missing.", Severity.BLOCK, path=item))
        return {
            "required_files_total": len(required),
            "required_files_existing_total": sum(1 for item in files if item["exists"]),
            "files": files,
        }

    def _policy_scenarios(self, findings: list[Finding]) -> dict[str, Any]:
        from devpilot_core.policy.engine import PolicyEngine, PolicyRequest

        engine = PolicyEngine(self.root, observability_enabled=False)
        scenarios = [
            {
                "id": "critical_without_approval",
                "request": PolicyRequest(
                    action="publish_deploy_tag",
                    tool_id="release.manager",
                    subject="v1.2.3",
                    actor="local-owner",
                    role_at_decision="owner",
                    command_id="cmd-post-h-012-e",
                    tool_call_id="tool-call-post-h-012-e",
                    interface="cli",
                ),
                "expected_findings": {"APPROVAL_REQUIRED", "APPROVAL_REQUIRED_MISSING", "SENSITIVE_ACTION_NON_EXECUTABLE_BLOCKED"},
            },
            {
                "id": "blocked_interface_api",
                "request": PolicyRequest(
                    action="apply",
                    tool_id="patch.sandbox",
                    subject="changes.patch",
                    actor="local-owner",
                    role_at_decision="owner",
                    command_id="cmd-post-h-012-e",
                    tool_call_id="tool-call-post-h-012-e",
                    interface="api",
                ),
                "expected_findings": {"SENSITIVE_ACTION_INTERFACE_BLOCKED", "APPROVAL_REQUIRED"},
            },
            {
                "id": "rbac_required_role_gap",
                "request": PolicyRequest(
                    action="apply",
                    tool_id="patch.sandbox",
                    subject="changes.patch",
                    actor="local-owner",
                    role_at_decision="owner",
                    command_id="cmd-post-h-012-e",
                    tool_call_id="tool-call-post-h-012-e",
                    interface="cli",
                ),
                "expected_findings": {"RBAC_DENIED"},
            },
        ]
        records: list[dict[str, Any]] = []
        covered: set[str] = set()
        for scenario in scenarios:
            result = engine.evaluate(scenario["request"])
            finding_ids = {finding.id for finding in result.findings}
            expected = set(scenario["expected_findings"])
            missing = sorted(expected - finding_ids)
            covered.update(expected & finding_ids)
            record = {
                "id": scenario["id"],
                "ok": result.ok,
                "exit_code": int(result.exit_code),
                "blocked": bool(result.data.get("summary", {}).get("blocked")) if isinstance(result.data, dict) else False,
                "finding_ids": sorted(finding_ids),
                "expected_findings": sorted(expected),
                "missing_expected_findings": missing,
            }
            records.append(record)
            if result.ok or not record["blocked"]:
                findings.append(Finding("APPROVAL_RBAC_POLICY_SCENARIO_NOT_BLOCKED", "Policy scenario expected to block did not block.", Severity.BLOCK, metadata={"scenario": scenario["id"], "finding_ids": sorted(finding_ids)}))
            if missing:
                findings.append(Finding("APPROVAL_RBAC_POLICY_FINDING_MISSING", "Policy scenario did not emit expected normalized finding IDs.", Severity.BLOCK, metadata={"scenario": scenario["id"], "missing": missing, "finding_ids": sorted(finding_ids)}))
        expected_all = sorted({item for scenario in scenarios for item in scenario["expected_findings"]})
        return {
            "scenarios_total": len(records),
            "blocked_total": sum(1 for item in records if item["blocked"]),
            "expected_findings": expected_all,
            "expected_findings_covered": sorted(covered),
            "scenarios": records,
        }

    def _binding_scenario(self, findings: list[Finding]) -> dict[str, Any]:
        record = ApprovalRecord(
            approval_id="APPROVAL-POSTH012E-DEMO",
            subject="changes.patch",
            tool_id="patch.sandbox",
            action="apply",
            status=ApprovalStatus.APPROVED.value,
            actor="local-owner",
            reason="POST-H-012-E in-memory binding scenario; not persisted.",
            scope={
                "actor_id": "local-owner",
                "role_at_decision": "maintainer",
                "tool_id": "patch.sandbox",
                "action": "apply",
                "subject": "changes.patch",
                "subject_hash": compute_subject_hash("changes.patch"),
                "command_id": "cmd-approved",
                "tool_call_id": "tool-call-approved",
                "interface": "cli",
            },
            created_at="2026-06-27T00:00:00Z",
            updated_at="2026-06-27T00:00:00Z",
            expires_at="2099-01-01T00:00:00Z",
            decision_at="2026-06-27T00:01:00Z",
            decided_by="local-owner",
            metadata={"source": POST_H_012_E_CREATED_BY},
        )
        result = StrongApprovalBindingValidator(self.root).evaluate(
            record,
            ApprovalBindingRequest(
                approval_id=record.approval_id,
                actor_id="local-owner",
                role_at_decision="maintainer",
                tool_id="patch.sandbox",
                action="apply",
                subject="other.patch",
                command_id="cmd-approved",
                tool_call_id="tool-call-approved",
                subject_hash=compute_subject_hash("other.patch"),
                interface="cli",
            ),
        )
        finding_ids = {finding.id for finding in result.findings}
        scope_mismatch = not result.ok and any("MISMATCH" in finding_id for finding_id in finding_ids)
        if not scope_mismatch:
            findings.append(Finding("APPROVAL_RBAC_BINDING_SCOPE_MISMATCH_NOT_BLOCKED", "Strong approval binding did not block the scope mismatch scenario.", Severity.BLOCK, metadata={"finding_ids": sorted(finding_ids)}))
        return {"scope_mismatch_blocked": scope_mismatch, "finding_ids": sorted(finding_ids)}

    def _documentation_checks(self, findings: list[Finding]) -> dict[str, Any]:
        paths = [
            "docs/03_security/approval_rbac_hardening.md",
            "docs/05_operations/runbook.md",
            "docs/06_miasi/human_approval_card.md",
        ]
        combined = "\n".join((self.root / path).read_text(encoding="utf-8") if (self.root / path).exists() else "" for path in paths).lower()
        required_terms = {
            "request": "approval request",
            "approve": "approval approve",
            "deny": "approval deny",
            "revoke": "approval revoke",
            "actor": "actor",
            "role": "role_at_decision",
            "interface": "interface",
            "dry_run": "dry-run",
            "no_permanent": "no approvals globales permanentes",
        }
        missing = [key for key, term in required_terms.items() if term not in combined]
        for key in missing:
            findings.append(Finding("APPROVAL_RBAC_DOCUMENTATION_TERM_MISSING", "Approval/RBAC lifecycle documentation is missing a required term.", Severity.BLOCK, metadata={"term_key": key, "expected": required_terms[key]}))
        return {
            "lifecycle_documented": all(key not in missing for key in ["request", "approve", "deny"]),
            "revocation_documented": "revoke" not in missing,
            "actor_role_interface_documented": all(key not in missing for key in ["actor", "role", "interface"]),
            "missing_terms": missing,
        }

    def _test_contract_checks(self, findings: list[Finding]) -> dict[str, Any]:
        v1 = self._load_json(".devpilot/testing/test_contract_registry.json")
        v2 = self._load_json(".devpilot/testing/test_contract_registry_v2.json")
        v1_contract = self._find_contract(v1, "post-h-012-approval-rbac-hardening-gate")
        v2_contract = self._find_contract(v2, "post-h-012-approval-rbac-hardening-gate")
        if not v1_contract:
            findings.append(Finding("APPROVAL_RBAC_TCR_CONTRACT_MISSING", "TCR v1 does not register POST-H-012-E approval-rbac-hardening gate.", Severity.BLOCK, path=".devpilot/testing/test_contract_registry.json"))
        if not v2_contract:
            findings.append(Finding("APPROVAL_RBAC_TCR_V2_CONTRACT_MISSING", "TCR v2 does not register POST-H-012-E approval-rbac-hardening gate.", Severity.BLOCK, path=".devpilot/testing/test_contract_registry_v2.json"))
        return {
            "v1_registered": bool(v1_contract),
            "v2_registered": bool(v2_contract),
            "v1_owner": v1_contract.get("owner") if v1_contract else None,
            "v2_capability": v2_contract.get("capability") if v2_contract else None,
        }

    def _load_json(self, relative_path: str) -> dict[str, Any]:
        try:
            loaded = json.loads((self.root / relative_path).read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        return loaded if isinstance(loaded, dict) else {}

    def _find_contract(self, payload: dict[str, Any], contract_id: str) -> dict[str, Any]:
        for item in payload.get("contracts", []):
            if isinstance(item, dict) and item.get("contract_id") == contract_id:
                return item
        return {}

    def _prefixed_findings(self, result: CommandResult, *, prefix: str) -> list[Finding]:
        if result.ok:
            return []
        return [
            Finding(
                id=f"{prefix}_{finding.id}",
                message=finding.message,
                severity=finding.severity,
                path=finding.path,
                metadata=finding.metadata,
            )
            for finding in result.findings
            if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}
        ]
