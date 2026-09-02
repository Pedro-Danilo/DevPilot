from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

DEFAULT_ALLOWLIST = Path('.devpilot/testing/quality_gate_aggregate_execution_allowlist.json')
_BINDING_WORDS = ('include', 'contains', 'registered', 'binding', 'membership', 'consumes')


def _is_quality_gate_ctor(call: ast.Call) -> bool:
    func = call.func
    return isinstance(func, ast.Name) and func.id == 'QualityGate' or isinstance(func, ast.Attribute) and func.attr == 'QualityGate'


def _function_runs_quality_gate(fn: ast.FunctionDef) -> bool:
    variables: set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and _is_quality_gate_ctor(node.value):
            variables.update(target.id for target in node.targets if isinstance(target, ast.Name))
    for node in ast.walk(fn):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'run'):
            continue
        receiver = node.func.value
        if isinstance(receiver, ast.Call) and _is_quality_gate_ctor(receiver):
            return True
        if isinstance(receiver, ast.Name) and receiver.id in variables:
            return True
    return False


@dataclass(frozen=True)
class AggregateExecutionCostAudit:
    root: Path
    allowlist_path: Path = DEFAULT_ALLOWLIST

    def run(self) -> CommandResult:
        root = Path(self.root).resolve()
        allow_path = self.allowlist_path if self.allowlist_path.is_absolute() else root / self.allowlist_path
        payload = json.loads(allow_path.read_text(encoding='utf-8')) if allow_path.exists() else {'allowed': []}
        allowed = set(str(item) for item in payload.get('allowed', []))
        aggregate_runs: list[str] = []
        binding_violations: list[str] = []
        for path in sorted((root / 'tests').glob('test_*.py')):
            try:
                tree = ast.parse(path.read_text(encoding='utf-8'))
            except SyntaxError:
                continue
            for node in tree.body:
                if not isinstance(node, ast.FunctionDef) or not _function_runs_quality_gate(node):
                    continue
                ref = f"{path.relative_to(root).as_posix()}::{node.name}"
                aggregate_runs.append(ref)
                binding_like = any(word in node.name.lower() for word in _BINDING_WORDS)
                if binding_like and ref not in allowed:
                    binding_violations.append(ref)
        findings = [
            Finding('FRX_V2_3_A_BINDING_AGGREGATE_RUN', 'Binding/registration test invokes QualityGate.run().', Severity.BLOCK, metadata={'test': ref})
            for ref in binding_violations
        ]
        summary: dict[str, Any] = {
            'aggregate_quality_gate_test_runs_total': len(aggregate_runs),
            'binding_aggregate_violations_total': len(binding_violations),
            'allowlist_total': len(allowed),
            'aggregate_runs': aggregate_runs,
            'binding_violations': binding_violations,
            'network_used': False,
            'external_api_used': False,
            'mutations_performed': False,
        }
        ok = not binding_violations
        return CommandResult(
            'tests aggregate-cost-audit', ok, ExitCode.PASS if ok else ExitCode.BLOCK,
            'Aggregate execution cost audit passed.' if ok else 'Aggregate execution cost audit blocked.',
            data={'summary': summary}, findings=findings or [Finding('FRX_V2_3_A_AGGREGATE_COST_AUDIT_PASS', 'No binding-only aggregate executions outside allowlist.', Severity.INFO)],
        )
