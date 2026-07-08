from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.docs_governance.validator import DocumentationGovernanceValidator
from devpilot_core.industrial.production_ready import ProductionReadyFinalDeclaration
from devpilot_core.release_candidate.evidence_freshness import EvidenceFreshnessOptions, EvidenceFreshnessScanner
from devpilot_core.release_candidate.install_smoke import LocalInstallSmokeOptions, LocalInstallSmokeRunner
from devpilot_core.release_candidate.ui_api_smoke import UiApiRcSmokeOptions, UiApiRcSmokeRunner
from devpilot_core.release_candidate.verification_profile import (
    ReleaseCandidateVerificationProfile,
    ReleaseCandidateVerificationProfileOptions,
)
from devpilot_core.schemas import SchemaRegistry, SchemaValidator
from devpilot_core.testing import TestContractRegistry, TestContractRegistryV2Validator


DEFAULT_LOCAL_RELEASE_CANDIDATE_CRITERIA_PATH = Path(".devpilot/release/local_release_candidate_criteria.json")
DEFAULT_LOCAL_RELEASE_CANDIDATE_REPORT_JSON_PATH = Path("outputs/reports/local_release_candidate_report.json")
DEFAULT_LOCAL_RELEASE_CANDIDATE_REPORT_MARKDOWN_PATH = Path("outputs/reports/local_release_candidate_report.md")

_FORBIDDEN_CLAIM_KEYS = (
    "enterprise_ready_claim",
    "remote_ready_claim",
    "saas_ready_claim",
    "compliance_certification_claim",
    "enterprise_ready_claimed",
    "remote_ready_claimed",
    "saas_ready_claimed",
    "compliance_certified_claimed",
)
_NO_GO_GATE_KEYS = (
    "remote_execution_enabled",
    "connector_write_enabled",
    "plugin_execution_enabled",
    "external_apis_required",
)


@dataclass(frozen=True)
class LocalReleaseCandidateOptions:
    criteria_path: str = str(DEFAULT_LOCAL_RELEASE_CANDIDATE_CRITERIA_PATH)
    output_json: str = str(DEFAULT_LOCAL_RELEASE_CANDIDATE_REPORT_JSON_PATH)
    output_markdown: str = str(DEFAULT_LOCAL_RELEASE_CANDIDATE_REPORT_MARKDOWN_PATH)
    write_report: bool = False


class LocalReleaseCandidateReporter:
    """POST-H-026-E final local release candidate PASS/BLOCK aggregator.

    The reporter composes the already-governed POST-H-026 A-D checks and the
    POST-H-025 production-ready-local final declaration. It deliberately avoids
    subprocesses, pytest execution, network calls, socket binding and source
    mutations. Optional JSON/Markdown evidence is written only when the operator
    passes ``--write-report``.
    """

    def __init__(self, root: Path, options: LocalReleaseCandidateOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or LocalReleaseCandidateOptions()

    def run(self) -> CommandResult:
        started = perf_counter()
        findings: list[Finding] = []
        criteria, criteria_component = self._load_and_validate_criteria()
        components: list[dict[str, Any]] = [criteria_component]

        evidence_result = EvidenceFreshnessScanner(
            self.root,
            options=EvidenceFreshnessOptions(criteria_path=self.options.criteria_path),
        ).scan()
        components.append(self._component("evidence_freshness", "Evidence freshness", evidence_result))

        profile_result = ReleaseCandidateVerificationProfile(
            self.root,
            ReleaseCandidateVerificationProfileOptions(profile_id="release-candidate-local"),
        ).inspect()
        components.append(self._component("release_candidate_profile", "Release candidate profile", profile_result))

        ui_api_result = UiApiRcSmokeRunner(self.root, UiApiRcSmokeOptions()).run()
        components.append(self._component("ui_api_smoke", "UI/API RC smoke", ui_api_result))

        install_result = LocalInstallSmokeRunner(self.root, LocalInstallSmokeOptions()).run()
        components.append(self._component("install_smoke", "Local install smoke", install_result))

        production_result = ProductionReadyFinalDeclaration(self.root).finalize()
        components.append(self._component("production_ready_local_final", "Production-ready-local final declaration", production_result))

        docs_result = DocumentationGovernanceValidator(self.root).run()
        components.append(self._component("docs_governance", "Documentation governance", docs_result))

        tcr_v1_result = TestContractRegistry(self.root).validate()
        components.append(self._component("tcr_v1", "Test Contract Registry v1", tcr_v1_result))

        tcr_v2_result = TestContractRegistryV2Validator(self.root).validate()
        components.append(self._component("tcr_v2", "Test Contract Registry v2", tcr_v2_result))

        schema_result = SchemaRegistry(self.root).list()
        components.append(self._component("schema_registry", "Schema registry", schema_result))

        no_go_gates, no_go_enabled = self._collect_no_go_gates(criteria)
        forbidden_claims, forbidden_enabled = self._collect_forbidden_claims(criteria)
        blocking_gaps = self._blocking_gaps(components, no_go_enabled, forbidden_enabled)
        advisory_gaps = self._advisory_gaps(components)
        actions_required = self._actions_required(blocking_gaps)

        decision = "PASS" if not blocking_gaps else "BLOCK"
        duration_ms = round((perf_counter() - started) * 1000, 3)
        report = {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-LOCAL-RELEASE-CANDIDATE-REPORT-V1",
            "report_id": "local-release-candidate-post_h_026_e",
            "created_by": "POST-H-026-E",
            "created_at": self._now(),
            "scope": "local-release-candidate",
            "decision": decision,
            "implemented_status": "implemented-initial",
            "execution_mode": "in-process-final-rc-aggregator",
            "criteria_path": self._relative(self._resolve(self.options.criteria_path)),
            "production_ready_local_claim_preserved": not forbidden_enabled,
            "forbidden_claims_detected_total": len(forbidden_enabled),
            "forbidden_claims": forbidden_claims,
            "no_go_gates_passed": not no_go_enabled,
            "no_go_gates": no_go_gates,
            "evidence_freshness_passed": evidence_result.ok,
            "release_candidate_profile_passed": profile_result.ok,
            "ui_api_smoke_passed": ui_api_result.ok,
            "install_smoke_passed": install_result.ok,
            "production_ready_local_final_passed": production_result.ok,
            "docs_governance_passed": docs_result.ok,
            "tcr_v1_v2_passed": tcr_v1_result.ok and tcr_v2_result.ok,
            "schemas_valid": schema_result.ok,
            "clean_artifact_policy_passed": bool((install_result.data or {}).get("summary", {}).get("clean_package_policy_passed")),
            "components_total": len(components),
            "components_passed_total": sum(1 for item in components if item["status"] == "pass"),
            "components_failed_total": sum(1 for item in components if item["status"] != "pass"),
            "blocking_gaps_total": len(blocking_gaps),
            "advisory_gaps_total": len(advisory_gaps),
            "actions_required": actions_required,
            "blocking_gaps": blocking_gaps,
            "advisory_gaps": advisory_gaps,
            "components": components,
            "duration_ms": duration_ms,
            "summary": {
                "decision": decision,
                "created_by": "POST-H-026-E",
                "preliminary": True,
                "production_ready_local_claim_preserved": not forbidden_enabled,
                "forbidden_claims_detected_total": len(forbidden_enabled),
                "no_go_gates_passed": not no_go_enabled,
                "evidence_freshness_passed": evidence_result.ok,
                "release_candidate_profile_passed": profile_result.ok,
                "ui_api_smoke_passed": ui_api_result.ok,
                "install_smoke_passed": install_result.ok,
                "production_ready_local_final_passed": production_result.ok,
                "docs_governance_passed": docs_result.ok,
                "tcr_v1_v2_passed": tcr_v1_result.ok and tcr_v2_result.ok,
                "schemas_valid": schema_result.ok,
                "clean_artifact_policy_passed": bool((install_result.data or {}).get("summary", {}).get("clean_package_policy_passed")),
                "blocking_gaps_total": len(blocking_gaps),
                "advisory_gaps_total": len(advisory_gaps),
                "reports_written": self.options.write_report,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations": False,
            },
            "safety": self._safety(reports_written=self.options.write_report),
            "limitations": [
                "POST-H-026-E aggregates local RC evidence and emits PASS/BLOCK; it does not publish packages, sign releases or deploy services.",
                "The final PASS remains bounded to production-ready-local; enterprise, remote, SaaS and compliance-certified claims stay false.",
                "Full pytest -q remains a backlog/checkpoint regression activity and is not executed by this local final reporter.",
            ],
        }

        validation = SchemaValidator(self.root).validate_payload(
            schema="LocalReleaseCandidateReport",
            payload=report,
            instance_label="in-memory:local-release-candidate-report",
        )
        if not validation.ok:
            report["decision"] = "BLOCK"
            report["summary"]["decision"] = "BLOCK"
            schema_gap = {
                "gap_id": "local-release-candidate-report-schema",
                "severity": "block",
                "component_id": "local_release_candidate_report",
                "reason": "Final LocalReleaseCandidateReport failed schema validation.",
                "action": "Fix docs/schemas/local_release_candidate_report.schema.json or report payload before declaring RC closure.",
            }
            report["blocking_gaps"].append(schema_gap)
            report["blocking_gaps_total"] += 1
            report["summary"]["blocking_gaps_total"] = report["blocking_gaps_total"]
            report["actions_required"].append(schema_gap["action"])
            findings.extend(validation.findings)
            decision = "BLOCK"

        if self.options.write_report:
            self._write_report(report)

        findings.extend(self._findings(report))
        ok = report["decision"] == "PASS"
        return CommandResult(
            "release-candidate final",
            ok,
            ExitCode.PASS if ok else ExitCode.BLOCK,
            "Local release candidate passed." if ok else "Local release candidate blocked.",
            data={
                "summary": report["summary"],
                "report": report,
                "components": components,
                "reports": self._report_paths() if self.options.write_report else {},
                "safety": report["safety"],
            },
            findings=findings,
        )

    def _load_and_validate_criteria(self) -> tuple[dict[str, Any], dict[str, Any]]:
        path = self._resolve(self.options.criteria_path)
        try:
            criteria = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            return {}, {
                "component_id": "criteria",
                "label": "Local release candidate criteria",
                "status": "block",
                "ok": False,
                "exit_code": int(ExitCode.ERROR),
                "summary": {"path": self._relative(path), "error": str(exc)},
                "blocking_findings_total": 1,
            }
        validation = SchemaValidator(self.root).validate_payload(
            schema="LocalReleaseCandidateCriteria",
            payload=criteria,
            instance_label="in-memory:local-release-candidate-criteria",
        )
        return criteria, self._component("criteria", "Local release candidate criteria", validation)

    def _component(self, component_id: str, label: str, result: CommandResult) -> dict[str, Any]:
        summary = (result.data or {}).get("summary", {}) if isinstance(result.data, dict) else {}
        blocking_findings = [finding for finding in result.findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        return {
            "component_id": component_id,
            "label": label,
            "status": "pass" if result.ok else "block",
            "ok": bool(result.ok),
            "exit_code": int(result.exit_code),
            "command": result.command,
            "message": result.message,
            "summary": summary,
            "blocking_findings_total": len(blocking_findings),
            "finding_ids": [finding.id for finding in result.findings[:20]],
        }

    def _collect_no_go_gates(self, criteria: dict[str, Any]) -> tuple[dict[str, bool], dict[str, bool]]:
        project_state = self._load_json_dict(".devpilot/project_state.json")
        criteria_gates = criteria.get("no_go_gates", {}) if isinstance(criteria, dict) else {}
        gates: dict[str, bool] = {}
        for key in _NO_GO_GATE_KEYS:
            gates[key] = bool(project_state.get(key, criteria_gates.get(key, False)))
        gates.update({f"criteria.{key}": bool(value) for key, value in criteria_gates.items() if key in _NO_GO_GATE_KEYS})
        enabled = {key: value for key, value in gates.items() if value is True}
        return gates, enabled

    def _collect_forbidden_claims(self, criteria: dict[str, Any]) -> tuple[dict[str, bool], dict[str, bool]]:
        project_state = self._load_json_dict(".devpilot/project_state.json")
        criteria_gates = criteria.get("no_go_gates", {}) if isinstance(criteria, dict) else {}
        claims: dict[str, bool] = {}
        for key in _FORBIDDEN_CLAIM_KEYS:
            if key in project_state:
                claims[f"project_state.{key}"] = bool(project_state.get(key))
            if key in criteria_gates:
                claims[f"criteria.{key}"] = bool(criteria_gates.get(key))
        enabled = {key: value for key, value in claims.items() if value is True}
        return claims, enabled

    def _blocking_gaps(
        self,
        components: list[dict[str, Any]],
        no_go_enabled: dict[str, bool],
        forbidden_enabled: dict[str, bool],
    ) -> list[dict[str, Any]]:
        gaps: list[dict[str, Any]] = []
        for component in components:
            if component["status"] != "pass":
                gaps.append(
                    {
                        "gap_id": f"component-{component['component_id']}",
                        "severity": "block",
                        "component_id": component["component_id"],
                        "reason": component.get("message") or f"{component['label']} did not pass.",
                        "action": self._action_for_component(component["component_id"]),
                    }
                )
        if no_go_enabled:
            gaps.append(
                {
                    "gap_id": "no-go-gates-enabled",
                    "severity": "block",
                    "component_id": "no_go_gates",
                    "reason": "One or more release-candidate no-go gates are enabled.",
                    "action": "Keep remote execution, connector write, plugin execution and external API requirements disabled for local RC.",
                    "metadata": {"enabled": no_go_enabled},
                }
            )
        if forbidden_enabled:
            gaps.append(
                {
                    "gap_id": "forbidden-claims-enabled",
                    "severity": "block",
                    "component_id": "claims",
                    "reason": "One or more forbidden enterprise/remote/SaaS/compliance claims are enabled.",
                    "action": "Remove forbidden claims and preserve the production-ready-local-only boundary.",
                    "metadata": {"enabled": forbidden_enabled},
                }
            )
        return gaps

    def _advisory_gaps(self, components: list[dict[str, Any]]) -> list[dict[str, Any]]:
        advisories: list[dict[str, Any]] = []
        install = next((item for item in components if item["component_id"] == "install_smoke"), None)
        if install and install.get("summary", {}).get("candidate_zip_checked") is False:
            advisories.append(
                {
                    "gap_id": "candidate-zip-not-supplied",
                    "severity": "advisory",
                    "component_id": "install_smoke",
                    "reason": "Final RC aggregation used source clean-package policy because no candidate ZIP was supplied to install-smoke.",
                    "action": "For operator release handoff, run release-candidate install-smoke with --candidate-zip pointing to the generated ZIP.",
                }
            )
        return advisories

    def _actions_required(self, blocking_gaps: list[dict[str, Any]]) -> list[str]:
        if not blocking_gaps:
            return []
        actions: list[str] = []
        seen: set[str] = set()
        for gap in blocking_gaps:
            action = str(gap.get("action", "Resolve blocking gap and rerun release-candidate final."))
            if action not in seen:
                actions.append(action)
                seen.add(action)
        return actions

    def _action_for_component(self, component_id: str) -> str:
        return {
            "criteria": "Fix .devpilot/release/local_release_candidate_criteria.json and validate it against LocalReleaseCandidateCriteria.",
            "evidence_freshness": "Run release-candidate evidence-freshness, fix stale/missing critical evidence and rerun final.",
            "release_candidate_profile": "Fix release-candidate-local profile/TCR binding and rerun release-candidate profile.",
            "ui_api_smoke": "Fix localhost/token/CORS/UI route issues and rerun release-candidate ui-api-smoke.",
            "install_smoke": "Fix local install/run checklist or clean package hygiene and rerun release-candidate install-smoke.",
            "production_ready_local_final": "Fix production-ready-local final declaration blockers before RC closure.",
            "docs_governance": "Fix source registry/frontmatter/documentation sync and rerun docs-governance validate.",
            "tcr_v1": "Fix Test Contract Registry v1 schema/semantic issues and rerun test-contracts validate.",
            "tcr_v2": "Fix Test Contract Registry v2 schema/semantic issues and rerun test-contracts validate-v2.",
            "schema_registry": "Fix schema catalog/schema files and rerun schema list.",
        }.get(component_id, "Resolve blocking component and rerun release-candidate final.")

    def _findings(self, report: dict[str, Any]) -> list[Finding]:
        if report["decision"] == "PASS":
            return [
                Finding(
                    "LOCAL_RELEASE_CANDIDATE_PASS",
                    "Local release candidate final PASS report was produced without network, external APIs or source mutations.",
                    Severity.INFO,
                    metadata={
                        "components_total": report["components_total"],
                        "blocking_gaps_total": report["blocking_gaps_total"],
                    },
                )
            ]
        return [
            Finding(
                "LOCAL_RELEASE_CANDIDATE_BLOCK",
                "Local release candidate final report blocked release handoff.",
                Severity.BLOCK,
                metadata={
                    "blocking_gaps_total": report["blocking_gaps_total"],
                    "actions_required_total": len(report["actions_required"]),
                },
            )
        ]

    def _write_report(self, report: dict[str, Any]) -> None:
        json_path = self._resolve_output(self.options.output_json)
        md_path = self._resolve_output(self.options.output_markdown)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        md_path.write_text(self._markdown(report), encoding="utf-8")

    def _markdown(self, report: dict[str, Any]) -> str:
        lines = [
            "# Local Release Candidate Report",
            "",
            f"- Decision: **{report['decision']}**",
            f"- Created by: `{report['created_by']}`",
            f"- Scope: `{report['scope']}`",
            f"- Components: {report['components_passed_total']}/{report['components_total']} passed",
            f"- Blocking gaps: {report['blocking_gaps_total']}",
            f"- Advisory gaps: {report['advisory_gaps_total']}",
            "",
            "## Componentes",
            "",
        ]
        for component in report["components"]:
            lines.append(f"- `{component['component_id']}`: **{component['status'].upper()}** — {component.get('message', '')}")
        if report["blocking_gaps"]:
            lines.extend(["", "## Gaps bloqueantes", ""])
            for gap in report["blocking_gaps"]:
                lines.append(f"- `{gap['gap_id']}`: {gap['reason']} Acción: {gap['action']}")
        if report["advisory_gaps"]:
            lines.extend(["", "## Gaps advisory", ""])
            for gap in report["advisory_gaps"]:
                lines.append(f"- `{gap['gap_id']}`: {gap['reason']} Acción sugerida: {gap['action']}")
        lines.extend([
            "",
            "## Límites",
            "",
            "Este reporte no publica paquetes, no firma releases, no despliega servicios y no amplía claims por encima de `production-ready-local`.",
            "",
        ])
        return "\n".join(lines)

    def _report_paths(self) -> dict[str, str]:
        return {"json": self.options.output_json, "markdown": self.options.output_markdown}

    def _load_json_dict(self, path: str) -> dict[str, Any]:
        try:
            payload = json.loads((self.root / path).read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _resolve(self, value: str | Path) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.root / path

    def _resolve_output(self, value: str | Path) -> Path:
        path = self._resolve(value)
        try:
            path.resolve().relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Output path must stay inside the project root: {value}") from exc
        return path

    def _relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def _now(self) -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _safety(self, *, reports_written: bool) -> dict[str, bool]:
        return {
            "local_first": True,
            "read_only": True,
            "dry_run": True,
            "subprocess_executed": False,
            "pytest_executed": False,
            "pip_executed": False,
            "npm_executed": False,
            "socket_opened": False,
            "network_used": False,
            "external_api_used": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "mutations_performed": bool(reports_written),
            "source_mutations": False,
            "reports_written": reports_written,
        }
