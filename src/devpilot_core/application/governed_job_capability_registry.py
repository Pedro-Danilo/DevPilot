from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity


DEFAULT_REGISTRY_PATH = Path('.devpilot/interfaces/governed_job_capability_registry.json')
UI_CAPABILITY_REGISTRY_PATH = Path('.devpilot/interfaces/ui_capability_registry.json')


@dataclass(frozen=True)
class GovernedJobCapabilityContract:
    capability_id: str
    cli_command_id: str
    cli_command: str
    application_service: str | None
    risk_class: str
    parity_status: str
    policy_binding: dict[str, Any]
    budgets: dict[str, int]
    contracts: dict[str, Any]
    controls: dict[str, Any]
    evidence_mapping: dict[str, Any]
    runtime: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> 'GovernedJobCapabilityContract':
        return cls(
            capability_id=str(payload['capability_id']),
            cli_command_id=str(payload['cli_command_id']),
            cli_command=str(payload['cli_command']),
            application_service=payload.get('application_service'),
            risk_class=str(payload['risk_class']),
            parity_status=str(payload['parity_status']),
            policy_binding=dict(payload['policy_binding']),
            budgets={k: int(v) for k, v in dict(payload['budgets']).items()},
            contracts=dict(payload['contracts']),
            controls=dict(payload['controls']),
            evidence_mapping=dict(payload['evidence_mapping']),
            runtime=dict(payload['runtime']),
        )

    @property
    def planning_enabled(self) -> bool:
        return bool(self.runtime.get('planning_enabled', False))

    @property
    def execution_enabled(self) -> bool:
        return bool(self.runtime.get('execution_enabled', False))

    @property
    def adapter_bound(self) -> bool:
        return bool(self.runtime.get('adapter_bound', False))

    @property
    def requires_approval(self) -> bool:
        return bool(self.controls.get('approval_required', False))

    @property
    def supports_cancel(self) -> bool:
        return bool(self.controls.get('supports_cancel', False))

    @property
    def supports_rollback(self) -> bool:
        return bool(self.controls.get('supports_rollback', False))


class GovernedJobCapabilityRegistry:
    """Read-only UOC-007 capability registry.

    The registry is deliberately not a router. It classifies every CLI capability,
    carries policy/budget/input-output/evidence contracts, and blocks runtime
    execution until a later sprint binds a typed adapter explicitly.
    """

    def __init__(self, root: Path, registry_path: Path | str = DEFAULT_REGISTRY_PATH) -> None:
        self.root = Path(root).resolve()
        self.registry_path = Path(registry_path)
        if not self.registry_path.is_absolute():
            self.registry_path = self.root / self.registry_path
        self._payload: dict[str, Any] | None = None

    def payload(self) -> dict[str, Any]:
        if self._payload is None:
            self._payload = json.loads(self.registry_path.read_text(encoding='utf-8'))
        return self._payload

    def list(self) -> list[GovernedJobCapabilityContract]:
        return [GovernedJobCapabilityContract.from_dict(item) for item in self.payload().get('capabilities', [])]

    def get(self, capability_id: str) -> GovernedJobCapabilityContract | None:
        capability_id = str(capability_id).strip()
        for item in self.payload().get('capabilities', []):
            if item.get('capability_id') == capability_id:
                return GovernedJobCapabilityContract.from_dict(item)
        return None

    def require(self, capability_id: str) -> GovernedJobCapabilityContract:
        contract = self.get(capability_id)
        if contract is None:
            raise KeyError(f'Unregistered governed-job capability: {capability_id}')
        return contract

    def validate(self) -> CommandResult:
        errors: list[str] = []
        payload = self.payload()
        capabilities = payload.get('capabilities', [])
        ids = [str(item.get('capability_id', '')) for item in capabilities]
        if not ids or any(not item for item in ids):
            errors.append('capability-id-empty')
        if len(ids) != len(set(ids)):
            errors.append('capability-id-duplicate')

        ui_path = self.root / UI_CAPABILITY_REGISTRY_PATH
        if not ui_path.exists():
            errors.append('ui-capability-registry-missing')
            ui_ids: set[str] = set()
        else:
            ui_payload = json.loads(ui_path.read_text(encoding='utf-8'))
            ui_ids = {str(item.get('capability_id', '')) for item in ui_payload.get('capabilities', [])}
            current_ids = set(ids)
            if current_ids != ui_ids:
                if ui_ids - current_ids:
                    errors.append('capability-coverage-missing')
                if current_ids - ui_ids:
                    errors.append('capability-coverage-extra')

        for item in capabilities:
            cid = str(item.get('capability_id', ''))
            risk = item.get('risk_class')
            contracts = item.get('contracts') or {}
            controls = item.get('controls') or {}
            runtime = item.get('runtime') or {}
            policy = item.get('policy_binding') or {}
            evidence = item.get('evidence_mapping') or {}
            budgets = item.get('budgets') or {}
            if not contracts.get('request_envelope_schema_id') or not contracts.get('result_envelope_schema_id'):
                errors.append(f'{cid}:missing-envelope-contract')
            if not contracts.get('command_result_schema_id'):
                errors.append(f'{cid}:missing-command-result-contract')
            if not policy.get('source') or 'required' not in policy or 'default_decision' not in policy:
                errors.append(f'{cid}:missing-policy-binding')
            if not isinstance(evidence, dict) or 'evidence_reference_required' not in evidence:
                errors.append(f'{cid}:missing-evidence-mapping')
            if int(budgets.get('timeout_seconds', 0)) <= 0:
                errors.append(f'{cid}:invalid-timeout-budget')
            if int(budgets.get('retry_limit', -1)) < 0:
                errors.append(f'{cid}:invalid-retry-budget')
            if int(budgets.get('heartbeat_interval_seconds', 0)) <= 0:
                errors.append(f'{cid}:invalid-heartbeat-budget')
            if risk == 'forbidden' and (runtime.get('planning_enabled') or runtime.get('execution_enabled')):
                errors.append(f'{cid}:forbidden-runtime-enabled')
            if runtime.get('execution_enabled'):
                if not runtime.get('adapter_bound'):
                    errors.append(f'{cid}:execution-without-adapter')
                if not contracts.get('typed_parameters_schema_id'):
                    errors.append(f'{cid}:execution-without-typed-input')
                if risk in {'mutating', 'sensitive'} and not controls.get('dry_run_required'):
                    errors.append(f'{cid}:mutating-execution-without-dry-run-contract')
                if risk == 'sensitive' and not controls.get('approval_required'):
                    errors.append(f'{cid}:sensitive-execution-without-approval')

        summary = {
            'capabilities_total': len(capabilities),
            'ui_capabilities_total': len(ui_ids),
            'coverage_exact': set(ids) == ui_ids if ui_ids else False,
            'planning_enabled_total': sum(bool((item.get('runtime') or {}).get('planning_enabled')) for item in capabilities),
            'execution_enabled_total': sum(bool((item.get('runtime') or {}).get('execution_enabled')) for item in capabilities),
            'adapter_bound_total': sum(bool((item.get('runtime') or {}).get('adapter_bound')) for item in capabilities),
            'forbidden_total': sum(item.get('risk_class') == 'forbidden' for item in capabilities),
            'errors_total': len(errors),
        }
        ok = not errors
        return CommandResult(
            command='governed-job capability-registry validate',
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message='Governed job capability registry passed.' if ok else 'Governed job capability registry blocked.',
            data={'summary': summary, 'registry_path': str(self.registry_path).replace('\\', '/')},
            findings=[
                Finding(
                    id='UOC007_CAPABILITY_REGISTRY_PASS' if ok else 'UOC007_CAPABILITY_REGISTRY_BLOCK',
                    message='All CLI capabilities have governed-job contracts.' if ok else '; '.join(errors[:20]),
                    severity=Severity.INFO if ok else Severity.BLOCK,
                    metadata={'errors': errors, **summary},
                )
            ],
        )
