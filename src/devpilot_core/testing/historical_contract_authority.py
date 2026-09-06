from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.schemas import SchemaValidator
from devpilot_core.testing.duration_registry import NodeDurationRegistry
from devpilot_core.testing.isolation_registry import TestIsolationRegistry

DEFAULT_AUTHORITY_REGISTRY_PATH = Path('.devpilot/testing/historical_contract_authority_registry.json')
AUTHORITY_REGISTRY_CONTRACT = 'HistoricalContractAuthorityRegistry'
COMMAND = 'historical-contract-authority'
BLOCKING = {Severity.FAIL, Severity.BLOCK, Severity.ERROR}
ALLOWED_SCOPES = {
    'historical-freeze','current-active','successor-needed','deprecated-after-proof','derived','runtime-ephemeral'
}

@dataclass(frozen=True)
class HistoricalContractAuthorityOptions:
    registry_path: str | Path = DEFAULT_AUTHORITY_REGISTRY_PATH

class HistoricalContractAuthorityGate:
    """FRX-v2.4-A deterministic authority gate.

    The gate never executes pytest and never mutates source. It validates authority metadata,
    immutable historical fixtures, lifecycle disambiguation, and complete JSON Schema +
    semantic contracts for FRX Isolation/Duration registries.
    """

    def __init__(self, root: Path, options: HistoricalContractAuthorityOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or HistoricalContractAuthorityOptions()
        self.registry_path = self._resolve(self.options.registry_path)

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        try:
            registry = json.loads(self.registry_path.read_text(encoding='utf-8'))
        except Exception as exc:
            finding = Finding('HISTORICAL_AUTHORITY_REGISTRY_INVALID', f'Authority registry could not be loaded: {exc}', Severity.ERROR, path=self._rel(self.registry_path))
            return CommandResult(COMMAND, False, ExitCode.ERROR, 'Historical contract authority gate could not load its registry.', data={'summary': self._empty_summary()}, findings=[finding])

        schema_result = SchemaValidator(self.root).validate_payload(schema=AUTHORITY_REGISTRY_CONTRACT, payload=registry, instance_label=self._rel(self.registry_path))
        findings.extend(self._prefixed(schema_result.findings, 'HISTORICAL_AUTHORITY_REGISTRY'))
        registry_schema_errors = 0 if schema_result.ok else len([f for f in schema_result.findings if f.severity in BLOCKING])

        intrinsic_problems: list[str] = []
        leakage: list[dict[str, str]] = []
        missing_snapshots: list[str] = []
        scope_counts = {scope: 0 for scope in sorted(ALLOWED_SCOPES)}
        contract_ids: set[str] = set()
        contracts = registry.get('contracts') if isinstance(registry, dict) else []
        for record in contracts if isinstance(contracts, list) else []:
            if not isinstance(record, dict):
                intrinsic_problems.append('contract-record-not-object')
                continue
            rid = str(record.get('contract_id') or '')
            if rid in contract_ids or not rid:
                intrinsic_problems.append(f'duplicate-or-empty-contract-id:{rid}')
            contract_ids.add(rid)
            scope = str(record.get('authority_scope') or '')
            if scope in scope_counts:
                scope_counts[scope] += 1
            else:
                intrinsic_problems.append(f'unknown-authority-scope:{rid}:{scope}')
            intrinsic_problems.extend(self.validate_contract_record(record))
            for test_file in record.get('test_files') or []:
                test_path = self.root / str(test_file)
                if not test_path.exists():
                    intrinsic_problems.append(f'missing-test-file:{rid}:{test_file}')
            if scope == 'historical-freeze':
                snapshot = str(record.get('snapshot_path') or '')
                snapshot_path = self.root / snapshot if snapshot else None
                if snapshot_path is None or not snapshot_path.exists():
                    missing_snapshots.append(rid)
                for test_file in record.get('test_files') or []:
                    test_path = self.root / str(test_file)
                    if not test_path.exists():
                        continue
                    text = test_path.read_text(encoding='utf-8').replace('\\','/')
                    if snapshot and snapshot not in text:
                        intrinsic_problems.append(f'historical-test-does-not-bind-snapshot:{rid}:{test_file}')
                    for mutable in record.get('mutable_current_paths') or []:
                        mutable_s = str(mutable).replace('\\','/')
                        if mutable_s and mutable_s in text:
                            leakage.append({'contract_id':rid,'test_file':str(test_file),'mutable_current_path':mutable_s})

        for problem in intrinsic_problems:
            findings.append(Finding('HISTORICAL_AUTHORITY_CONTRACT_INVALID', problem, Severity.BLOCK, path=self._rel(self.registry_path)))
        for rid in missing_snapshots:
            findings.append(Finding('HISTORICAL_AUTHORITY_SNAPSHOT_MISSING', 'historical-freeze contract requires an immutable snapshot.', Severity.BLOCK, metadata={'contract_id':rid}))
        for item in leakage:
            findings.append(Finding('HISTORICAL_AUTHORITY_CURRENT_LEAKAGE', 'Historical test reads a mutable/current authority instead of its declared snapshot.', Severity.BLOCK, path=item['test_file'], metadata=item))

        lifecycle_ambiguities = self._validate_lifecycle(registry, findings)
        registry_checks, complete_schema_errors, isolation_entries, isolation_semantic_errors, duration_rejections = self._validate_frx_registries(registry, findings)
        registry_schema_errors += complete_schema_errors

        blocking = [f for f in findings if f.severity in BLOCKING]
        summary = {
            'created_by':'FRX-v2.4-A','authority_contracts_total':len(contracts or []),'authority_scope_counts':scope_counts,
            'historical_current_leakage_total':len(leakage),'missing_snapshots_total':len(missing_snapshots),
            'lifecycle_ambiguities_total':lifecycle_ambiguities,'registry_schema_errors_total':registry_schema_errors,
            'frx_registry_checks_total':len(registry_checks),'isolation_entries_total':isolation_entries,
            'isolation_semantic_errors_total':isolation_semantic_errors,'duration_rejections_total':duration_rejections,
            'blocking_findings_total':len(blocking),'full_regression_runs':0,'browser_runs':0,
            'network_used':False,'external_api_used':False,'mutations_performed':False,
            'authority_scope_deterministic':set(scope_counts)==ALLOWED_SCOPES and all(scope_counts[s] >= 1 for s in ALLOWED_SCOPES),
        }
        ok = not blocking and summary['authority_scope_deterministic']
        if not summary['authority_scope_deterministic']:
            findings.append(Finding('HISTORICAL_AUTHORITY_SCOPE_COVERAGE_BLOCK', 'All six authority scopes must be represented deterministically.', Severity.BLOCK, metadata={'scope_counts':scope_counts}))
            ok = False
        return CommandResult(
            command=COMMAND, ok=ok, exit_code=ExitCode.PASS if ok else exit_code_for_findings([f for f in findings if f.severity in BLOCKING], default_ok=False),
            message='Historical contract authority gate passed.' if ok else 'Historical contract authority gate blocked.',
            data={'summary':summary,'registry_checks':registry_checks,'notes':['Read-only deterministic gate; no pytest/full/browser/API/UI/network execution.','Historical facts are never rewritten to match current-active state.']},
            findings=findings or [Finding('HISTORICAL_AUTHORITY_PASS','Historical contract authority gate passed.',Severity.INFO,metadata=summary)],
        )

    @staticmethod
    def validate_contract_record(record: dict[str, Any]) -> list[str]:
        rid = str(record.get('contract_id') or '<missing>')
        scope = str(record.get('authority_scope') or '')
        problems: list[str] = []
        if scope == 'historical-freeze':
            if not str(record.get('snapshot_path') or '').strip(): problems.append(f'missing-snapshot:{rid}')
            if not isinstance(record.get('mutable_current_paths'), list): problems.append(f'missing-mutable-current-paths:{rid}')
        elif scope == 'current-active':
            if not (record.get('current_paths') or []): problems.append(f'missing-current-paths:{rid}')
        elif scope == 'successor-needed':
            if not str(record.get('successor_contract_id') or '').strip(): problems.append(f'missing-successor-contract-id:{rid}')
        elif scope == 'deprecated-after-proof':
            if not str(record.get('proof_path') or '').strip(): problems.append(f'missing-deprecation-proof:{rid}')
        elif scope == 'derived':
            if not (record.get('derived_from') or []): problems.append(f'missing-derived-sources:{rid}')
        elif scope == 'runtime-ephemeral':
            if not (record.get('excluded_patterns') or []): problems.append(f'missing-runtime-exclusions:{rid}')
        elif scope not in ALLOWED_SCOPES:
            problems.append(f'unknown-scope:{rid}:{scope}')
        return problems

    def _validate_lifecycle(self, registry: dict[str, Any], findings: list[Finding]) -> int:
        ambiguities = 0
        for check in registry.get('lifecycle_checks') or []:
            path = self.root / str(check.get('path') or '')
            try:
                payload = json.loads(path.read_text(encoding='utf-8'))
            except Exception as exc:
                ambiguities += 1
                findings.append(Finding('HISTORICAL_AUTHORITY_LIFECYCLE_SOURCE_INVALID', f'Lifecycle source unavailable: {exc}', Severity.BLOCK, path=self._rel(path)))
                continue
            required_field = str(check.get('required_at_detection_field') or '')
            pending_field = str(check.get('pending_now_field') or '')
            if required_field not in payload or pending_field not in payload or not isinstance(payload.get(required_field), bool) or not isinstance(payload.get(pending_field), bool):
                ambiguities += 1
                findings.append(Finding('HISTORICAL_AUTHORITY_LIFECYCLE_AMBIGUOUS', 'Lifecycle authority must explicitly separate required_at_detection from pending_now booleans.', Severity.BLOCK, path=self._rel(path), metadata={'required_at_detection_field':required_field,'pending_now_field':pending_field}))
            for optional in ('status_at_close_field','current_status_field'):
                field = check.get(optional)
                if field and not str(payload.get(str(field)) or '').strip():
                    ambiguities += 1
                    findings.append(Finding('HISTORICAL_AUTHORITY_LIFECYCLE_STATUS_AMBIGUOUS', f'Lifecycle field is missing or empty: {field}', Severity.BLOCK, path=self._rel(path)))
        return ambiguities

    def _validate_frx_registries(self, registry: dict[str, Any], findings: list[Finding]) -> tuple[list[dict[str, Any]], int, int, int, int]:
        checks: list[dict[str, Any]] = []
        schema_errors = 0
        isolation_entries = 0
        isolation_semantic_errors = 0
        duration_rejections = 0
        for spec in registry.get('schema_complete_registries') or []:
            kind = spec.get('semantic_validator')
            instance_path = str(spec.get('instance_path') or '')
            schema_contract = str(spec.get('schema_contract') or '')
            if kind == 'test-isolation':
                instance = TestIsolationRegistry(self.root, registry_path=Path(instance_path))
                schema_result = instance.validate_schema()
                payload = instance.load()
                semantics = TestIsolationRegistry.validate_semantics(payload)
                isolation_entries = int(semantics.get('entries_total') or 0)
                isolation_semantic_errors = len(semantics.get('problems') or [])
                semantic_ok = bool(semantics.get('ok'))
            elif kind == 'node-duration':
                instance = NodeDurationRegistry(self.root, registry_path=self.root/instance_path)
                schema_result = instance.validate_schema()
                payload = instance.load()
                status = instance.status()
                duration_rejections = int(status.get('rejections_total') or 0)
                semantic_ok = duration_rejections == 0
                semantics = {'ok':semantic_ok,'problems':[] if semantic_ok else [f'rejected-telemetry:{duration_rejections}'], **status}
            else:
                findings.append(Finding('HISTORICAL_AUTHORITY_REGISTRY_VALIDATOR_UNKNOWN', f'Unknown registry semantic validator: {kind}', Severity.BLOCK, path=instance_path))
                schema_errors += 1
                continue
            schema_blocking = [f for f in schema_result.findings if f.severity in BLOCKING]
            if schema_blocking:
                schema_errors += len(schema_blocking)
                findings.extend(self._prefixed(schema_blocking, 'HISTORICAL_AUTHORITY_FRX_REGISTRY_SCHEMA'))
            if not semantic_ok:
                for problem in semantics.get('problems') or ['semantic-validation-failed']:
                    findings.append(Finding('HISTORICAL_AUTHORITY_FRX_REGISTRY_SEMANTIC_BLOCK', str(problem), Severity.BLOCK, path=instance_path, metadata={'registry_id':spec.get('registry_id')}))
            checks.append({'registry_id':spec.get('registry_id'),'instance_path':instance_path,'schema_contract':schema_contract,'schema_ok':schema_result.ok,'semantic_ok':semantic_ok,'summary':semantics})
        return checks, schema_errors, isolation_entries, isolation_semantic_errors, duration_rejections

    @staticmethod
    def _prefixed(items: list[Finding], prefix: str) -> list[Finding]:
        out: list[Finding] = []
        for finding in items:
            out.append(Finding(f'{prefix}_{finding.id}', finding.message, finding.severity, path=finding.path, metadata=dict(finding.metadata or {})))
        return out

    def _resolve(self, value: str | Path) -> Path:
        path = Path(value)
        return path.resolve() if path.is_absolute() else (self.root/path).resolve()

    def _rel(self, path: Path) -> str:
        try: return path.resolve().relative_to(self.root).as_posix()
        except ValueError: return path.as_posix()

    @staticmethod
    def _empty_summary() -> dict[str, Any]:
        return {'created_by':'FRX-v2.4-A','authority_contracts_total':0,'historical_current_leakage_total':0,'registry_schema_errors_total':1,'full_regression_runs':0,'browser_runs':0,'network_used':False,'external_api_used':False,'mutations_performed':False}
