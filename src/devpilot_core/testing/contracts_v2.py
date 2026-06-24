from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, Finding, Severity
from devpilot_core.schemas import SchemaValidator

DEFAULT_TEST_CONTRACT_REGISTRY_V2_SCHEMA_PATH = Path("docs/schemas/test_contract_registry_v2.schema.json")
__test__ = False


class TestContractDomain(str, Enum):
    GOVERNANCE_SCHEMAS = "governance.schemas"
    GOVERNANCE_TESTING = "governance.testing"
    GOVERNANCE_POLICY = "governance.policy"
    QUALITY_GATE = "quality.gate"
    INTERFACE_CLI = "interface.cli"
    APPLICATION_SERVICE = "application.service"
    SECURITY_GUARDS = "security.guards"
    DOCUMENTATION_HISTORICAL = "documentation.historical"


class TestContractCriticality(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class TestContractRiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TestContractExecutionProfile(str, Enum):
    ALWAYS = "always"
    IMPACT = "impact"
    RELEASE = "release"
    MANUAL = "manual"
    NIGHTLY_LOCAL = "nightly-local"


class TestContractCostClass(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TestContractType(str, Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    CONTRACT = "contract"
    UI_SMOKE = "ui-smoke"
    SECURITY = "security"
    RELEASE = "release"
    DOCUMENTATION = "documentation"
    SCHEMA = "schema"
    QUALITY_GATE = "quality-gate"


@dataclass(frozen=True)
class TestContractRegistryV2Design:
    """Schema-backed design helper for POST-H-003-A.

    This class intentionally does not migrate or execute test contracts. It only
    validates local JSON-compatible payloads against the v2 schema so the v2
    contract can evolve without breaking the current v1 registry.
    """

    root: Path
    schema_path: Path = DEFAULT_TEST_CONTRACT_REGISTRY_V2_SCHEMA_PATH

    def validate_payload(self, payload: dict[str, Any], *, instance_label: str = "in-memory:test-contract-registry-v2") -> CommandResult:
        result = SchemaValidator(self.root).validate_payload(
            schema=self.schema_path,
            payload=payload,
            instance_label=instance_label,
        )
        return self._annotate(result)

    def validate_file(self, path: str | Path) -> CommandResult:
        result = SchemaValidator(self.root).validate(schema=self.schema_path, instance=path)
        return self._annotate(result)

    def _annotate(self, result: CommandResult) -> CommandResult:
        if not result.ok:
            return result
        findings = list(result.findings)
        findings.append(
            Finding(
                id="TEST_CONTRACT_REGISTRY_V2_SCHEMA_PASS",
                message="Test Contract Registry v2 payload conforms to the POST-H-003-A design schema.",
                severity=Severity.INFO,
                metadata={
                    "schema_path": str(self.schema_path).replace("\\", "/"),
                    "v1_compatibility_required": True,
                    "migrates_v1": False,
                    "executes_tests": False,
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                },
            )
        )
        data = dict(result.data)
        data["post_h_003_a"] = {
            "schema_version": "2.0",
            "v1_compatibility_required": True,
            "migrates_v1": False,
            "executes_tests": False,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
        }
        return CommandResult(
            command=result.command,
            ok=result.ok,
            exit_code=result.exit_code,
            message=result.message,
            data=data,
            findings=findings,
        )


def load_registry_v2_fixture(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Test Contract Registry v2 fixture must be a JSON object.")
    return payload
