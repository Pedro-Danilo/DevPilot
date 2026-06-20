from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

from .contracts import TestContract, TestContractRegistry


@dataclass(frozen=True)
class TestImpactOptions:
    __test__ = False
    changed_files_path: str | None = None
    changed_files: tuple[str, ...] = ()
    conservative: bool = True


class TestImpactAnalyzer:
    __test__ = False

    """Conservative test impact analyzer for POST-H-001.

    This first version never claims that no tests are needed for critical
    contract changes. If it cannot map a path confidently, it recommends full
    pytest as a safe fallback.
    """

    def __init__(self, root: Path, *, registry: TestContractRegistry | None = None) -> None:
        self.root = Path(root).resolve()
        self.registry = registry or TestContractRegistry(self.root)

    def analyze(self, options: TestImpactOptions | None = None) -> CommandResult:
        options = options or TestImpactOptions()
        changed_files = self._load_changed_files(options)
        contracts = self.registry.list_contracts()
        matched: dict[str, dict[str, Any]] = {}
        unmatched: list[str] = []

        for changed in changed_files:
            normalized = changed.strip().replace("\\", "/")
            if not normalized:
                continue
            matched_contracts = self._match_contracts(normalized, contracts)
            if matched_contracts:
                for contract in matched_contracts:
                    entry = matched.setdefault(contract.contract_id, {"contract": contract, "paths": []})
                    entry["paths"].append(normalized)
            else:
                unmatched.append(normalized)

        recommended_tests: list[str] = []
        recommended_commands: list[str] = []
        matched_contract_ids: list[str] = []
        for contract_id in sorted(matched):
            contract: TestContract = matched[contract_id]["contract"]
            matched_contract_ids.append(contract_id)
            for test_file in contract.test_files:
                if test_file not in recommended_tests:
                    recommended_tests.append(test_file)
            for command in contract.recommended_commands:
                if command not in recommended_commands:
                    recommended_commands.append(command)

        full_pytest_required = not changed_files or bool(unmatched)
        if any(path.startswith(("pyproject.toml", "src/devpilot_core/cli.py", "src/devpilot_core/quality/")) for path in changed_files):
            full_pytest_required = True
        if full_pytest_required and "pytest -q" not in recommended_commands:
            recommended_commands.append("pytest -q")

        ok = True
        findings = [
            Finding(
                "TEST_IMPACT_ANALYSIS_PASS",
                "Test impact analyzer produced conservative recommendations.",
                Severity.INFO,
                metadata={"changed_files_total": len(changed_files), "full_pytest_required": full_pytest_required},
            )
        ]
        if unmatched:
            findings.append(
                Finding(
                    "TEST_IMPACT_UNMATCHED_PATHS_FULL_PYTEST",
                    "Some changed files were not mapped to contracts; full pytest is required conservatively.",
                    Severity.WARNING,
                    metadata={"unmatched_paths": unmatched},
                )
            )
        return CommandResult(
            command="test-impact analyze",
            ok=ok,
            exit_code=ExitCode.PASS,
            message="Test impact analysis completed with conservative recommendations.",
            data={
                "summary": {
                    "changed_files_total": len(changed_files),
                    "matched_contracts_total": len(matched_contract_ids),
                    "recommended_tests_total": len(recommended_tests),
                    "full_pytest_required": full_pytest_required,
                    "unmatched_paths_total": len(unmatched),
                    "network_used": False,
                    "external_api_used": False,
                    "mutations_performed": False,
                    "preliminary": True,
                },
                "changed_files": changed_files,
                "matched_contracts": [
                    {"contract_id": contract_id, "paths": matched[contract_id]["paths"]}
                    for contract_id in matched_contract_ids
                ],
                "unmatched_paths": unmatched,
                "recommended_tests": recommended_tests,
                "recommended_commands": recommended_commands,
            },
            findings=findings,
        )

    def _load_changed_files(self, options: TestImpactOptions) -> list[str]:
        files = [item.strip().replace("\\", "/") for item in options.changed_files if item.strip()]
        if options.changed_files_path:
            path = Path(options.changed_files_path)
            if not path.is_absolute():
                path = self.root / path
            if path.exists():
                files.extend(line.strip().replace("\\", "/") for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        # preserve order, remove duplicates
        seen: set[str] = set()
        output: list[str] = []
        for item in files:
            if item not in seen:
                seen.add(item)
                output.append(item)
        return output

    def _match_contracts(self, changed: str, contracts: list[TestContract]) -> list[TestContract]:
        matches: list[TestContract] = []
        for contract in contracts:
            candidates = set(contract.test_files) | set(contract.watched_paths) | set(contract.validates)
            for candidate in candidates:
                token = candidate.replace("\\", "/").rstrip("*")
                if not token:
                    continue
                if changed == token or changed.startswith(token.rstrip("/")) or token.rstrip("/") in changed:
                    matches.append(contract)
                    break
        return matches
