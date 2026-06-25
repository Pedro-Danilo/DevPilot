from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas import SchemaValidator

DEFAULT_TEST_CONTRACT_REGISTRY_PATH = Path(".devpilot/testing/test_contract_registry.json")
DEFAULT_TEST_CONTRACT_SCHEMA_PATH = Path("docs/schemas/test_contract_registry.schema.json")
DEFAULT_PROJECT_STATE_PATH = Path(".devpilot/project_state.json")
DEFAULT_PROJECT_STATE_SCHEMA_PATH = Path("docs/schemas/project_state.schema.json")

_ALLOWED_SCOPES = {
    "unit",
    "feature",
    "historical-sprint",
    "global-state",
    "integration",
    "quality-gate",
    "safety",
    "ui-smoke",
}


@dataclass(frozen=True)
class TestContract:
    """One declarative test contract from `.devpilot/testing`.

    POST-H-001 deliberately keeps this data model small: it documents and
    validates the intent of test suites, but it does not execute tests from JSON.
    """

    contract_id: str
    scope: str
    owner: str
    test_files: tuple[str, ...]
    validates: tuple[str, ...] = ()
    watched_paths: tuple[str, ...] = ()
    mutable_global_state_allowed: bool = False
    global_state_source: str | None = None
    critical: bool = True
    recommended_commands: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TestContract":
        return cls(
            contract_id=str(payload.get("contract_id", "")).strip(),
            scope=str(payload.get("scope", "")).strip(),
            owner=str(payload.get("owner", "")).strip(),
            test_files=tuple(str(item).strip().replace("\\", "/") for item in payload.get("test_files", []) if str(item).strip()),
            validates=tuple(str(item).strip().replace("\\", "/") for item in payload.get("validates", []) if str(item).strip()),
            watched_paths=tuple(str(item).strip().replace("\\", "/") for item in payload.get("watched_paths", []) if str(item).strip()),
            mutable_global_state_allowed=bool(payload.get("mutable_global_state_allowed", False)),
            global_state_source=str(payload.get("global_state_source") or "").strip() or None,
            critical=bool(payload.get("critical", True)),
            recommended_commands=tuple(str(item).strip() for item in payload.get("recommended_commands", []) if str(item).strip()),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "scope": self.scope,
            "owner": self.owner,
            "test_files": list(self.test_files),
            "validates": list(self.validates),
            "watched_paths": list(self.watched_paths),
            "mutable_global_state_allowed": self.mutable_global_state_allowed,
            "global_state_source": self.global_state_source,
            "critical": self.critical,
            "recommended_commands": list(self.recommended_commands),
        }


class TestContractRegistry:
    __test__ = False

    """Validate and expose DevPilot test contracts.

    The registry exists to reduce hidden coupling between historical sprint tests
    and mutable project state. It is intentionally conservative and local-only.
    """

    def __init__(
        self,
        root: Path,
        *,
        registry_path: str | Path = DEFAULT_TEST_CONTRACT_REGISTRY_PATH,
        schema_path: str | Path = DEFAULT_TEST_CONTRACT_SCHEMA_PATH,
    ) -> None:
        self.root = Path(root).resolve()
        self.registry_path = self._resolve(registry_path)
        self.schema_path = self._resolve(schema_path)

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        schema_result = SchemaValidator(self.root).validate(schema=self.schema_path, instance=self.registry_path)
        if not schema_result.ok:
            findings.extend(schema_result.findings)
            return self._result(False, schema_result.exit_code, "Test contract registry schema validation failed.", [], findings)

        payload = self._load_payload(findings)
        if payload is None:
            return self._result(False, self._exit_code(findings), "Test contract registry could not be loaded.", [], findings)

        contracts = [TestContract.from_dict(item) for item in payload.get("contracts", []) if isinstance(item, dict)]
        findings.extend(self._semantic_findings(contracts))
        ok = not any(f.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} for f in findings)
        return self._result(
            ok,
            ExitCode.PASS if ok else self._exit_code(findings),
            "Test contract registry passed." if ok else "Test contract registry failed semantic validation.",
            contracts,
            findings or [Finding("TEST_CONTRACT_REGISTRY_PASS", "Test contract registry passed structural and semantic validation.", Severity.INFO, metadata={"contracts_total": len(contracts)})],
        )

    def list_contracts(self) -> list[TestContract]:
        payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        return [TestContract.from_dict(item) for item in payload.get("contracts", []) if isinstance(item, dict)]

    def project_state(self) -> CommandResult:
        findings: list[Finding] = []
        state_path = self.root / DEFAULT_PROJECT_STATE_PATH
        state_schema = self.root / DEFAULT_PROJECT_STATE_SCHEMA_PATH
        schema_result = SchemaValidator(self.root).validate(schema=state_schema, instance=state_path)
        findings.extend(schema_result.findings)
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            findings.append(Finding("PROJECT_STATE_LOAD_FAILED", "Project global state could not be loaded.", Severity.ERROR, path=str(DEFAULT_PROJECT_STATE_PATH), metadata={"error": str(exc)}))
            state = {}
        last_completed = str(state.get("last_completed_sprint", ""))
        next_sprint = str(state.get("next_sprint", ""))
        checks = {
            "readme_current_hito": self._file_contains("README.md", f"Último hito: `{last_completed}"),
            "readme_next_hito": self._file_contains("README.md", f"Siguiente hito: `{next_sprint}"),
            "post_h_001_doc_approved": self._file_contains("docs/POST-H-001_industrial_hardening_tests_contracts.md", 'status: "approved"'),
            "runbook_last_completed": self._file_contains("docs/05_operations/runbook.md", last_completed),
            "post_h_backlog_next": self._file_contains("docs/backlogs/post_phase_h_ideas.md", next_sprint) or self._file_contains("docs/backlogs/post_h_prioritized_roadmap.md", next_sprint),
            "changelog_last_completed": self._file_contains("docs/release/CHANGELOG.md", last_completed.lower()) or self._file_contains("docs/release/CHANGELOG.md", last_completed),
        }
        if last_completed == "POST-H-002":
            checks["post_h_002_backlog_closed"] = self._file_contains("docs/backlogs/POST-H-002_maturity_dashboard_local.md", 'implementation_status: "closed"')
            checks["post_h_002_closure_report"] = self._file_contains("docs/audits/post_h_002_closure_report.md", "POST-H-002")
        if last_completed == "POST-H-003":
            checks["post_h_003_backlog_closed"] = self._file_contains("docs/backlogs/POST-H-003_test_contract_registry_2.md", 'implementation_status: "closed"')
            checks["post_h_003_closure_report"] = self._file_contains("docs/audits/post_h_003_closure_report.md", "POST-H-003")
            checks["post_h_003_contract_registered"] = self._file_contains(".devpilot/testing/test_contract_registry.json", "post-h-003-test-contract-registry-2")
        if last_completed == "POST-H-004":
            checks["post_h_004_backlog_closed"] = self._file_contains("docs/backlogs/POST-H-004_policy_miasi_semantic_validator.md", 'implementation_status: "closed"')
            checks["post_h_004_closure_report"] = self._file_contains("docs/audits/post_h_004_closure_report.md", "POST-H-004")
            checks["post_h_004_contract_registered"] = self._file_contains(".devpilot/testing/test_contract_registry.json", "post-h-004-miasi-semantic-validator")
            checks["post_h_004_quality_gate_subgate"] = self._file_contains("src/devpilot_core/quality/gate.py", "miasi-semantic-validate")
        if last_completed == "POST-H-005":
            checks["post_h_005_backlog_closed"] = self._file_contains("docs/backlogs/POST-H-005_architecture_map_executable.md", 'implementation_status: "closed"')
            checks["post_h_005_closure_report"] = self._file_contains("docs/audits/post_h_005_closure_report.md", "POST-H-005")
            checks["post_h_005_contract_registered"] = self._file_contains(".devpilot/testing/test_contract_registry.json", "post-h-005-architecture-map")
            checks["post_h_005_quality_gate_subgate"] = self._file_contains("src/devpilot_core/quality/gate.py", "architecture-map")
        for key, passed in checks.items():
            if not passed:
                findings.append(Finding("PROJECT_GLOBAL_STATE_DRIFT", f"Project global state check failed: {key}.", Severity.FAIL, metadata={"check": key}))
        ok = schema_result.ok and not any(f.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} for f in findings)
        return CommandResult(
            command="project-state validate",
            ok=ok,
            exit_code=ExitCode.PASS if ok else self._exit_code(findings),
            message="Project global state passed." if ok else "Project global state drift detected.",
            data={
                "summary": {
                    "state_path": str(DEFAULT_PROJECT_STATE_PATH),
                    "schema_path": str(DEFAULT_PROJECT_STATE_SCHEMA_PATH),
                    "last_completed_sprint": state.get("last_completed_sprint"),
                    "next_sprint": state.get("next_sprint"),
                    "checks_total": len(checks),
                    "checks_passed": sum(1 for value in checks.values() if value),
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "preliminary": True,
                },
                "state": state,
                "checks": checks,
            },
            findings=findings or [Finding("PROJECT_GLOBAL_STATE_PASS", "Mutable global project state is centralized and synchronized.", Severity.INFO, metadata={"state_path": str(DEFAULT_PROJECT_STATE_PATH)})],
        )

    def _load_payload(self, findings: list[Finding]) -> dict[str, Any] | None:
        try:
            payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            findings.append(Finding("TEST_CONTRACT_REGISTRY_MISSING", "Test contract registry is missing.", Severity.BLOCK, path=self.relative(self.registry_path)))
            return None
        except json.JSONDecodeError as exc:
            findings.append(Finding("TEST_CONTRACT_REGISTRY_INVALID_JSON", "Test contract registry is invalid JSON.", Severity.ERROR, path=self.relative(self.registry_path), metadata={"error": str(exc)}))
            return None
        return payload if isinstance(payload, dict) else None

    def _semantic_findings(self, contracts: list[TestContract]) -> list[Finding]:
        findings: list[Finding] = []
        ids: set[str] = set()
        global_state_contracts = 0
        for contract in contracts:
            if contract.contract_id in ids:
                findings.append(Finding("TEST_CONTRACT_DUPLICATE_ID", "Duplicate test contract id.", Severity.ERROR, metadata={"contract_id": contract.contract_id}))
            ids.add(contract.contract_id)
            if contract.scope not in _ALLOWED_SCOPES:
                findings.append(Finding("TEST_CONTRACT_SCOPE_INVALID", "Test contract scope is not allowed.", Severity.ERROR, metadata=contract.to_dict()))
            if contract.scope == "global-state":
                global_state_contracts += 1
                if not contract.mutable_global_state_allowed:
                    findings.append(Finding("TEST_CONTRACT_GLOBAL_STATE_FLAG_MISSING", "Global-state contract must explicitly allow mutable global state.", Severity.FAIL, metadata={"contract_id": contract.contract_id}))
            if contract.scope == "historical-sprint" and contract.mutable_global_state_allowed:
                findings.append(Finding("TEST_CONTRACT_HISTORICAL_MUTABLE_STATE_DENY", "Historical sprint tests must not own mutable global state.", Severity.BLOCK, metadata={"contract_id": contract.contract_id}))
            for test_file in contract.test_files:
                path = self.root / test_file
                if not path.exists():
                    findings.append(Finding("TEST_CONTRACT_TEST_FILE_MISSING", "Declared test file does not exist.", Severity.BLOCK, path=test_file, metadata={"contract_id": contract.contract_id}))
            if contract.critical and not contract.recommended_commands:
                findings.append(Finding("TEST_CONTRACT_COMMANDS_MISSING", "Critical test contract should declare recommended verification commands.", Severity.WARNING, metadata={"contract_id": contract.contract_id}))
        if global_state_contracts != 1:
            findings.append(Finding("TEST_CONTRACT_GLOBAL_STATE_OWNER_INVALID", "Exactly one global-state contract must own mutable project state.", Severity.BLOCK, metadata={"global_state_contracts": global_state_contracts}))
        return findings

    def _file_contains(self, path: str, needle: str) -> bool:
        candidate = self.root / path
        return candidate.exists() and needle in candidate.read_text(encoding="utf-8")

    def _resolve(self, path: str | Path) -> Path:
        candidate = Path(path)
        return candidate if candidate.is_absolute() else (self.root / candidate).resolve()

    def relative(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.root)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")

    def _result(self, ok: bool, exit_code: ExitCode, message: str, contracts: list[TestContract], findings: list[Finding]) -> CommandResult:
        scope_counts: dict[str, int] = {}
        for contract in contracts:
            scope_counts[contract.scope] = scope_counts.get(contract.scope, 0) + 1
        return CommandResult(
            command="test-contracts validate",
            ok=ok,
            exit_code=exit_code,
            message=message,
            data={
                "summary": {
                    "registry_path": self.relative(self.registry_path),
                    "schema_path": self.relative(self.schema_path),
                    "contracts_total": len(contracts),
                    "scope_counts": scope_counts,
                    "historical_contracts_total": scope_counts.get("historical-sprint", 0),
                    "global_state_contracts_total": scope_counts.get("global-state", 0),
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "preliminary": True,
                },
                "contracts": [contract.to_dict() for contract in contracts],
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
