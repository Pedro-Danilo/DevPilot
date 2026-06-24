from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas import SchemaValidator

DEFAULT_V1_REGISTRY_PATH = Path(".devpilot/testing/test_contract_registry.json")
DEFAULT_V2_REGISTRY_PATH = Path(".devpilot/testing/test_contract_registry_v2.json")
DEFAULT_V2_SCHEMA_PATH = Path("docs/schemas/test_contract_registry_v2.schema.json")
__test__ = False


@dataclass(frozen=True)
class TestContractRegistryV2MigrationOptions:
    __test__ = False

    """Options for the deterministic v1 -> v2 migration preview.

    POST-H-003-B is dry-run by default: it reads the v1 registry, builds a v2
    representation in memory, validates it against the v2 schema, and writes an
    output file only when an explicit path is supplied by the caller.
    """

    registry_path: str | Path = DEFAULT_V1_REGISTRY_PATH
    schema_path: str | Path = DEFAULT_V2_SCHEMA_PATH
    write_output: str | Path | None = None


class TestContractRegistryV2Migrator:
    __test__ = False

    """Deterministic local migrator for Test Contract Registry v1 -> v2.

    The migrator does not execute tests, does not call the network, does not use
    external APIs, and never overwrites the v1 registry. Its output is a schema-
    valid v2 registry plus explicit classification-gap findings for every field
    inferred from v1 metadata.
    """

    def __init__(self, root: Path, options: TestContractRegistryV2MigrationOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or TestContractRegistryV2MigrationOptions()
        self.registry_path = self._resolve(self.options.registry_path)
        self.schema_path = self._resolve(self.options.schema_path)

    def migrate(self) -> CommandResult:
        findings: list[Finding] = []
        payload = self._load_v1(findings)
        if payload is None:
            return self._result(False, ExitCode.BLOCK, {}, findings, reports_written=False)

        contracts_v1 = [item for item in payload.get("contracts", []) if isinstance(item, dict)]
        contracts_v2: list[dict[str, Any]] = []
        gaps: list[dict[str, Any]] = []
        for item in contracts_v1:
            migrated, contract_gaps = self._migrate_contract(item)
            contracts_v2.append(migrated)
            gaps.extend(contract_gaps)

        registry_v2 = self._build_registry(contracts_v2)
        schema_result = SchemaValidator(self.root).validate_payload(
            schema=self.schema_path,
            payload=registry_v2,
            instance_label="in-memory:test-contract-registry-v2-migration",
        )
        findings.extend(schema_result.findings)
        for gap in gaps:
            findings.append(
                Finding(
                    id="TEST_CONTRACT_V2_CLASSIFICATION_GAP",
                    message="Test contract v2 classification was inferred during dry-run migration and should be reviewed before relying on it as an industrial contract.",
                    severity=Severity.WARNING,
                    metadata=gap,
                )
            )

        reports_written = False
        output_path: Path | None = None
        if self.options.write_output:
            output_path = self._resolve(self.options.write_output)
            if output_path.resolve() == self.registry_path.resolve():
                findings.append(
                    Finding(
                        id="TEST_CONTRACT_V2_REFUSES_V1_OVERWRITE",
                        message="The v2 migrator refuses to overwrite the active v1 registry.",
                        severity=Severity.BLOCK,
                        path=self.relative(output_path),
                    )
                )
            else:
                self._ensure_within_workspace(output_path, findings)
                if not any(f.severity in {Severity.BLOCK, Severity.ERROR} for f in findings):
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(json.dumps(registry_v2, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                    reports_written = True
                    findings.append(
                        Finding(
                            id="TEST_CONTRACT_V2_MIGRATION_OUTPUT_WRITTEN",
                            message="Test Contract Registry v2 migration output was written explicitly.",
                            severity=Severity.INFO,
                            path=self.relative(output_path),
                        )
                    )

        ok = schema_result.ok and not any(f.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for f in findings)
        return self._result(
            ok,
            ExitCode.PASS if ok else self._exit_code(findings),
            registry_v2,
            findings or [
                Finding(
                    id="TEST_CONTRACT_V2_MIGRATION_PASS",
                    message="Test Contract Registry v1 to v2 migration preview passed.",
                    severity=Severity.INFO,
                    metadata={"contracts_total": len(contracts_v2)},
                )
            ],
            reports_written=reports_written,
            output_path=output_path,
            gaps=gaps,
        )

    def _build_registry(self, contracts: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "schema_version": "2.0",
            "schema_id": "SCHEMA-DEVPL-TEST-CONTRACT-REGISTRY-V2",
            "created_by": "POST-H-003-B",
            "status": "implemented-initial",
            "description": "Deterministic dry-run migration output from Test Contract Registry v1 to v2. Generated by POST-H-003-B without replacing v1.",
            "generated_from": self.relative(self.registry_path),
            "compatibility": {
                "v1_compatible": True,
                "v1_registry_path": ".devpilot/testing/test_contract_registry.json",
                "v1_schema_id": "SCHEMA-DEVPL-TEST-CONTRACT-REGISTRY-V1",
                "v2_schema_path": "docs/schemas/test_contract_registry_v2.schema.json",
                "migration_required": True,
                "compatibility_mode": "migration-dry-run",
                "notes": [
                    "The active v1 registry remains available for compatibility after POST-H-003-E; v2 is validated by quality-gate hardening as a local non-executing contract source.",
                    "All v2 classifications generated here are deterministic and marked as inferred or needs-review where appropriate.",
                ],
            },
            "profiles": self._default_profiles(),
            "contracts": contracts,
            "migration_metadata": {
                "source_contracts_total": len(contracts),
                "migrator": "TestContractRegistryV2Migrator",
                "source_registry_preserved": True,
                "tests_executed": False,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed_by_default": False,
            },
        }

    def _default_profiles(self) -> list[dict[str, Any]]:
        return [
            {
                "profile_id": "p0-critical",
                "description": "P0 contracts required for local hardening and release decisions.",
                "criticalities": ["P0"],
                "execution_profiles": ["always", "release"],
                "network_allowed": False,
                "external_api_allowed": False,
            },
            {
                "profile_id": "security",
                "description": "Security-sensitive contracts, all local and explicit.",
                "criticalities": ["P0", "P1"],
                "execution_profiles": ["always", "impact", "release"],
                "network_allowed": False,
                "external_api_allowed": False,
            },
            {
                "profile_id": "release",
                "description": "Contracts expected before local release packaging.",
                "criticalities": ["P0", "P1"],
                "execution_profiles": ["always", "release"],
                "network_allowed": False,
                "external_api_allowed": False,
            },
            {
                "profile_id": "impact",
                "description": "Contracts selected by changed watched paths.",
                "criticalities": ["P0", "P1", "P2"],
                "execution_profiles": ["impact"],
                "network_allowed": False,
                "external_api_allowed": False,
            },
            {
                "profile_id": "docs-historical",
                "description": "Historical documentation regression contracts selected by documentation impact.",
                "criticalities": ["P2", "P3"],
                "execution_profiles": ["impact", "nightly-local"],
                "network_allowed": False,
                "external_api_allowed": False,
            },
        ]

    def _migrate_contract(self, item: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        source_id = str(item.get("contract_id", "")).strip()
        scope = str(item.get("scope", "")).strip()
        critical = bool(item.get("critical", True))
        test_files = self._clean_list(item.get("test_files", [])) or ["tests/test_missing_contract_placeholder.py"]
        watched_paths = self._clean_list(item.get("watched_paths", [])) or list(test_files)
        validates = self._clean_list(item.get("validates", [])) or [f"Migrated coverage declaration for {source_id}."]
        commands = self._clean_list(item.get("recommended_commands", [])) or [f"python -m pytest {' '.join(test_files)} -q"]

        mapping = self._classification_for(item)
        classification_status = mapping["classification_status"]
        gaps = [
            {
                "contract_id": source_id,
                "source_scope": scope,
                "classification_status": classification_status,
                "domain": mapping["domain"],
                "criticality": mapping["criticality"],
                "risk_level": mapping["risk_level"],
                "reason": mapping["reason"],
            }
        ]
        if classification_status == "needs-review":
            gaps[0]["review_required"] = True

        v2 = {
            "contract_id": source_id,
            "schema_version": "2.0",
            "source_contract_id": source_id,
            "domain": mapping["domain"],
            "capability": mapping["capability"],
            "criticality": mapping["criticality"],
            "risk_level": mapping["risk_level"],
            "test_type": mapping["test_type"],
            "execution_profile": mapping["execution_profile"],
            "cost_class": mapping["cost_class"],
            "expected_duration_seconds": mapping["expected_duration_seconds"],
            "test_files": test_files,
            "watched_paths": watched_paths,
            "validates": validates,
            "trigger_hints": mapping["trigger_hints"],
            "impact_scope": mapping["impact_scope"],
            "required_for_release": mapping["required_for_release"],
            "required_for_security_gate": mapping["required_for_security_gate"],
            "network_allowed": False,
            "external_api_allowed": False,
            "mutations_allowed": False,
            "source_mutations_allowed": bool(item.get("mutable_global_state_allowed", False)),
            "requires_human_approval": bool(item.get("mutable_global_state_allowed", False)),
            "owner": str(item.get("owner", "POST-H-003-B")).strip() or "POST-H-003-B",
            "recommended_commands": commands,
            "classification_status": classification_status,
            "classification_notes": [
                f"Migrated deterministically from v1 scope '{scope}' during POST-H-003-B.",
                mapping["reason"],
            ],
        }
        if v2["source_mutations_allowed"]:
            v2["safety_exception"] = {
                "justification": "Existing v1 global-state contract explicitly owns mutable project state metadata and is retained only as a local governance exception.",
                "approved_by": "POST-H-003-B",
                "expires_at_utc": "2026-12-31T23:59:59Z",
                "scope": ".devpilot/project_state.json",
                "rollback_or_cleanup": "Revert project-state metadata changes through Git and rerun project-state validate.",
            }
            v2["execution_profile"] = "manual"
        return v2, gaps

    def _classification_for(self, item: dict[str, Any]) -> dict[str, Any]:
        contract_id = str(item.get("contract_id", "")).strip()
        scope = str(item.get("scope", "")).strip()
        critical = bool(item.get("critical", True))
        watched = " ".join(self._clean_list(item.get("watched_paths", []))).lower()
        tests = " ".join(self._clean_list(item.get("test_files", []))).lower()
        text = f"{contract_id} {scope} {watched} {tests}".lower()

        if scope == "global-state":
            return self._class("governance.project_state", "ProjectGlobalState", "P0", "high", "contract", "manual", "low", 10, True, False, ["project-state-change"], ["project-state", "docs-sync"], "Global-state contract is P0 because it owns centralized mutable metadata.", "inferred")
        if "post-h-003" in contract_id or "test_contract_registry_2" in text or "test-contract-registry-v2" in text:
            return self._class("governance.testing", "TestContractRegistryV2", "P0", "high", "integration", "always", "low", 30, True, False, ["test-contract-registry-v2-change", "quality-gate-hardening-change"], ["testing", "contracts", "impact", "quality-gate"], "POST-H-003 closes Test Contract Registry 2.0 as a P0 local testing/governance contract with v1 compatibility.", "explicit")
        if contract_id == "test-contract-registry" or "test_contract_registry" in text:
            return self._class("governance.testing", "TestContractRegistry", "P0", "high", "contract", "always", "low", 10, True, False, ["test-contract-registry-change"], ["testing", "contracts"], "Test Contract Registry v1 remains a P0 compatibility contract.", "inferred")
        if contract_id == "schema-registry" or "schemas" in text:
            return self._class("governance.schemas", "SchemaRegistry", "P0", "high", "schema", "always", "low", 10, True, False, ["schema-change", "catalog-change"], ["schemas", "contract-validation"], "Schema changes can break multiple machine-readable contracts.", "inferred")
        if "quality" in contract_id or scope == "quality-gate":
            return self._class("quality.gate", "QualityGate", "P0", "high", "quality-gate", "always", "medium", 30, True, True, ["quality-gate-change"], ["quality", "hardening"], "Quality gate contracts are P0 because they guard local hardening.", "inferred")
        if contract_id == "test-impact-analyzer" or "testing/impact" in text:
            return self._class("governance.testing", "TestImpactAnalyzer", "P1", "medium", "contract", "impact", "low", 10, False, False, ["impact-analyzer-change"], ["test-impact", "testing"], "Impact analyzer is P1 and feeds the v2 impact plan without executing tests.", "inferred")
        if scope == "ui-smoke" or "ui/web" in text:
            return self._class("product.ui", "WebUISmoke", "P2", "medium" if critical else "low", "ui-smoke", "manual", "medium", 60, False, False, ["ui-change"], ["ui", "visual-smoke"], "UI smoke is local but not always required for every backend-only change.", "inferred")
        if "post-h-002" in contract_id or "maturity" in text:
            return self._class("quality.gate", "MaturityDashboard", "P0", "high", "integration", "always", "low", 30, True, False, ["maturity-dashboard-change", "post-h-source-change"], ["maturity", "post-h"], "POST-H-002 maturity dashboard now participates in hardening quality gates.", "inferred")
        if contract_id.startswith("post-h") or "post_h" in text:
            return self._class("documentation.governance", "PostHDocumentation", "P1", "medium", "documentation", "impact", "low", 20, False, False, ["post-h-doc-change"], ["post-h", "documentation"], "POST-H documentation/integration contracts require stronger classification in later v2 review.", "needs-review")
        if scope == "historical-sprint":
            return self._class("documentation.historical", "HistoricalSprintDocumentation", "P2" if critical else "P3", "medium" if critical else "low", "documentation", "impact", "low", 10, False, False, ["historical-doc-change"], ["documentation", "historical-sprints"], "Historical sprint tests are documentation regressions and do not prove functional industrial coverage.", "inferred")
        if scope == "integration":
            return self._class("governance.testing", "IntegrationContract", "P1", "medium", "integration", "impact", "low", 20, False, False, ["integration-change"], ["integration", "contracts"], "Generic v1 integration contract requires review to assign precise domain.", "needs-review")
        return self._class("governance.testing", "MigratedTestContract", "P1" if critical else "P2", "medium" if critical else "low", "contract", "impact", "low", 10, False, False, ["contract-change"], ["testing"], "Fallback deterministic classification from v1 metadata.", "needs-review")

    def _class(self, domain: str, capability: str, criticality: str, risk: str, test_type: str, profile: str, cost: str, duration: int, release: bool, security: bool, triggers: list[str], impact: list[str], reason: str, status: str) -> dict[str, Any]:
        return {
            "domain": domain,
            "capability": capability,
            "criticality": criticality,
            "risk_level": risk,
            "test_type": test_type,
            "execution_profile": profile,
            "cost_class": cost,
            "expected_duration_seconds": duration,
            "required_for_release": release,
            "required_for_security_gate": security,
            "trigger_hints": triggers,
            "impact_scope": impact,
            "reason": reason,
            "classification_status": status,
        }

    def _load_v1(self, findings: list[Finding]) -> dict[str, Any] | None:
        try:
            payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            findings.append(Finding("TEST_CONTRACT_V1_REGISTRY_MISSING", "Test Contract Registry v1 is missing.", Severity.BLOCK, path=self.relative(self.registry_path)))
            return None
        except json.JSONDecodeError as exc:
            findings.append(Finding("TEST_CONTRACT_V1_REGISTRY_INVALID_JSON", "Test Contract Registry v1 is invalid JSON.", Severity.ERROR, path=self.relative(self.registry_path), metadata={"error": str(exc)}))
            return None
        if not isinstance(payload, dict):
            findings.append(Finding("TEST_CONTRACT_V1_REGISTRY_INVALID_TYPE", "Test Contract Registry v1 must be a JSON object.", Severity.ERROR, path=self.relative(self.registry_path)))
            return None
        return payload

    def _ensure_within_workspace(self, path: Path, findings: list[Finding]) -> None:
        try:
            path.resolve().relative_to(self.root)
        except ValueError:
            findings.append(
                Finding(
                    id="TEST_CONTRACT_V2_OUTPUT_OUTSIDE_WORKSPACE",
                    message="The v2 migration output path must stay inside the workspace.",
                    severity=Severity.BLOCK,
                    path=str(path).replace("\\", "/"),
                )
            )

    def _clean_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip().replace("\\", "/") for item in value if str(item).strip()]

    def _resolve(self, path: str | Path) -> Path:
        candidate = Path(path)
        return candidate if candidate.is_absolute() else (self.root / candidate).resolve()

    def relative(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.root)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")

    def _result(
        self,
        ok: bool,
        exit_code: ExitCode,
        registry_v2: dict[str, Any],
        findings: list[Finding],
        *,
        reports_written: bool,
        output_path: Path | None = None,
        gaps: list[dict[str, Any]] | None = None,
    ) -> CommandResult:
        contracts = registry_v2.get("contracts", []) if isinstance(registry_v2, dict) else []
        gaps = gaps or []
        summary = {
            "source_registry_path": self.relative(self.registry_path),
            "target_schema_path": self.relative(self.schema_path),
            "contracts_v1_total": len(contracts),
            "contracts_v2_total": len(contracts),
            "classification_gaps_total": len(gaps),
            "needs_review_total": sum(1 for gap in gaps if gap.get("classification_status") == "needs-review"),
            "reports_written": reports_written,
            "output_path": self.relative(output_path) if output_path else None,
            "v1_registry_preserved": True,
            "tests_executed": False,
            "dry_run": output_path is None,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": reports_written,
            "source_mutations_performed": reports_written,
            "preliminary": True,
        }
        return CommandResult(
            command="test-contracts migrate-v2",
            ok=ok,
            exit_code=exit_code,
            message="Test Contract Registry v2 migration passed." if ok else "Test Contract Registry v2 migration failed.",
            data={
                "summary": summary,
                "registry": registry_v2,
                "classification_gaps": gaps[:25],
                "classification_gaps_truncated": len(gaps) > 25,
            },
            findings=findings,
        )

    def _exit_code(self, findings: list[Finding]) -> ExitCode:
        severities = {finding.severity for finding in findings}
        if Severity.ERROR in severities:
            return ExitCode.ERROR
        if Severity.BLOCK in severities:
            return ExitCode.BLOCK
        if Severity.FAIL in severities:
            return ExitCode.FAIL
        return ExitCode.PASS
