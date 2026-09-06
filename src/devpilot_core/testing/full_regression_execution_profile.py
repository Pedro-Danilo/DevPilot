from __future__ import annotations

import hashlib
import json
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas import SchemaValidator
from devpilot_core.testing.conflict_graph import ParallelShadowPlanner
from devpilot_core.testing.duration_registry import NodeDurationRegistry
from devpilot_core.testing.isolation_registry import IsolationState, TestIsolationRegistry
from devpilot_core.testing.temporal_shard_planner import TemporalPlannerError, TemporalShardPlanner

PROFILE_REGISTRY_PATH = Path('.devpilot/testing/full_regression_execution_profile_registry.json')
CURRENT_POINTER_PATH = Path('.devpilot/testing/full_regression_execution_profile_current.json')
PROFILE_REGISTRY_CONTRACT = 'FullRegressionExecutionProfileRegistry'
CURRENT_POINTER_CONTRACT = 'FullRegressionExecutionProfilePointer'
PREFLIGHT_REPORT_CONTRACT = 'FullRegressionPreflightReport'
PREFLIGHT_COMMAND = 'tests full-regression preflight'
PROFILE_COMMAND = 'tests full-regression profile'
TOPOLOGY_COMMAND = 'tests full-regression topology-check'

LOCKED_TOPOLOGY_FIELDS = (
    'planner',
    'target_shard_seconds',
    'max_nodeids',
    'max_command_chars',
    'nodeid_transport',
    'default_workers',
    'parallel_opt_in_ceiling',
)


def _canonical_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _profile_hash(profile: dict[str, Any]) -> str:
    return _canonical_hash({k: v for k, v in profile.items() if k != 'profile_sha256'})


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _result(command: str, *, ok: bool, message: str, data: dict[str, Any], findings: list[Finding]) -> CommandResult:
    blocking = [f for f in findings if f.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
    return CommandResult(
        command=command,
        ok=ok and not blocking,
        exit_code=ExitCode.PASS if ok and not blocking else ExitCode.BLOCK,
        message=message if ok and not blocking else message.replace('passed', 'blocked'),
        data=data,
        findings=findings,
    )


@dataclass(frozen=True)
class FullRegressionExecutionProfile:
    profile_id: str
    version: str
    lifecycle: str
    profile_sha256: str
    planner: str
    target_shard_seconds: float
    max_nodeids: int
    max_command_chars: int
    nodeid_transport: str
    default_workers: int
    parallel_opt_in_default: bool
    parallel_opt_in_ceiling: int
    parallel_opt_in_required: bool
    unknown_policy: str
    unclassified_isolation_policy: str
    parallel_safe_policy: str
    completion_first: bool
    exact_accounting: bool
    full_regression_runs_allowed: int
    second_full_allowed: bool
    resume_same_session: bool
    composite_recovery_after_functional_fail: bool
    source_guard_policy: str
    collection_policy: str
    registry_schema_required: bool
    registry_coverage_required: bool
    budget_reservation_policy: str
    environment_fingerprint: str
    cold_start_policy: str
    full_regression_confirmation: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> 'FullRegressionExecutionProfile':
        return cls(**{k: payload[k] for k in cls.__dataclass_fields__})

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    def topology(self) -> dict[str, Any]:
        return {field: getattr(self, field) for field in LOCKED_TOPOLOGY_FIELDS}


class FullRegressionExecutionProfileRegistry:
    """FRX-v2.4-B current-active profile registry and pointer authority.

    This layer is read-only. It validates schema, profile hash, uniqueness of the
    current profile and current-pointer parity. It never reserves or consumes a
    full-regression budget.
    """

    def __init__(self, root: Path, *, registry_path: Path = PROFILE_REGISTRY_PATH, pointer_path: Path = CURRENT_POINTER_PATH) -> None:
        self.root = Path(root).resolve()
        self.registry_path = self.root / registry_path
        self.pointer_path = self.root / pointer_path

    def load_registry(self) -> dict[str, Any]:
        return json.loads(self.registry_path.read_text(encoding='utf-8'))

    def load_pointer(self) -> dict[str, Any]:
        return json.loads(self.pointer_path.read_text(encoding='utf-8'))

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        try:
            registry = self.load_registry()
            pointer = self.load_pointer()
        except Exception as exc:
            findings.append(Finding('FRX24B_PROFILE_LOAD_BLOCK', f'Execution profile registry/pointer could not be loaded: {exc}', Severity.BLOCK))
            return _result(PROFILE_COMMAND, ok=False, message='Full Regression execution profile blocked.', data={'summary': {'profile_registry_valid': False, 'budget_reserved': False}}, findings=findings)

        validator = SchemaValidator(self.root)
        registry_schema = validator.validate_payload(schema=PROFILE_REGISTRY_CONTRACT, payload=registry, instance_label=_rel(self.root, self.registry_path))
        pointer_schema = validator.validate_payload(schema=CURRENT_POINTER_CONTRACT, payload=pointer, instance_label=_rel(self.root, self.pointer_path))
        if not registry_schema.ok:
            findings.extend(Finding(f'FRX24B_PROFILE_REGISTRY_{f.id}', f.message, f.severity, path=f.path, metadata=f.metadata) for f in registry_schema.findings)
        if not pointer_schema.ok:
            findings.extend(Finding(f'FRX24B_PROFILE_POINTER_{f.id}', f.message, f.severity, path=f.path, metadata=f.metadata) for f in pointer_schema.findings)

        profiles = [x for x in registry.get('profiles', []) if isinstance(x, dict)]
        ids = [str(x.get('profile_id') or '') for x in profiles]
        current_id = str(registry.get('current_profile_id') or '')
        active = [x for x in profiles if x.get('lifecycle') == 'current-active']
        if not current_id or ids.count(current_id) != 1:
            findings.append(Finding('FRX24B_CURRENT_PROFILE_ID_BLOCK', 'Registry must identify exactly one current_profile_id.', Severity.BLOCK, path=_rel(self.root, self.registry_path)))
        if len(active) != 1 or (active and active[0].get('profile_id') != current_id):
            findings.append(Finding('FRX24B_CURRENT_PROFILE_UNIQUENESS_BLOCK', 'Exactly one current-active profile must match current_profile_id.', Severity.BLOCK, path=_rel(self.root, self.registry_path)))
        if len(ids) != len(set(ids)) or any(not x for x in ids):
            findings.append(Finding('FRX24B_PROFILE_ID_DUPLICATE_BLOCK', 'Execution profile ids must be unique and non-empty.', Severity.BLOCK, path=_rel(self.root, self.registry_path)))

        profile_hash_ok = True
        for profile in profiles:
            expected = str(profile.get('profile_sha256') or '')
            actual = _profile_hash(profile)
            if actual != expected:
                profile_hash_ok = False
                findings.append(Finding('FRX24B_PROFILE_HASH_BLOCK', 'Execution profile semantic hash does not match profile_sha256.', Severity.BLOCK, metadata={'profile_id': profile.get('profile_id'), 'expected': expected, 'actual': actual}))

        pointer_ok = (
            str(pointer.get('current_profile_id') or '') == current_id
            and bool(active)
            and str(pointer.get('current_profile_sha256') or '') == str(active[0].get('profile_sha256') or '')
            and str(pointer.get('registry_path') or '') == PROFILE_REGISTRY_PATH.as_posix()
        )
        if not pointer_ok:
            findings.append(Finding('FRX24B_CURRENT_POINTER_BLOCK', 'Current profile pointer does not match the registry current profile/hash.', Severity.BLOCK, path=_rel(self.root, self.pointer_path)))

        consumer = registry.get('consumer_contract') or {}
        consumer_ok = (
            consumer.get('profile_id_only') is True
            and consumer.get('low_level_overrides_default') == 'BLOCK'
            and consumer.get('waiver_required_for_low_level_override') is True
            and consumer.get('preflight_required_before_budget_reservation') is True
            and consumer.get('full_budget_reserved_by_preflight') is False
        )
        if not consumer_ok:
            findings.append(Finding('FRX24B_CONSUMER_CONTRACT_BLOCK', 'Consumer contract must be profile-id-only and preflight-before-budget.', Severity.BLOCK, path=_rel(self.root, self.registry_path)))

        summary = {
            'created_by': 'FRX-v2.4-B',
            'profile_registry_valid': registry_schema.ok,
            'profile_pointer_valid': pointer_schema.ok,
            'profile_hashes_valid': profile_hash_ok,
            'current_pointer_parity': pointer_ok,
            'consumer_contract_locked': consumer_ok,
            'profiles_total': len(profiles),
            'current_active_total': len(active),
            'current_profile_id': current_id,
            'current_profile_sha256': str(active[0].get('profile_sha256') or '') if active else None,
            'budget_reserved': False,
            'full_regression_runs': 0,
            'browser_runs': 0,
            'network_used': False,
            'external_api_used': False,
            'mutations_performed': False,
        }
        ok = not any(f.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} for f in findings)
        return _result(PROFILE_COMMAND, ok=ok, message='Full Regression execution profile passed.', data={'summary': summary, 'registry': registry, 'pointer': pointer}, findings=findings or [Finding('FRX24B_PROFILE_PASS', 'Current Full Regression execution profile is unique, hash-bound and profile-id-only.', Severity.INFO, metadata=summary)])

    def require(self, profile_id: str = 'current') -> FullRegressionExecutionProfile:
        result = self.validate()
        if not result.ok:
            raise ValueError('Full Regression execution profile registry is not valid')
        registry = result.data['registry']
        resolved = str(registry['current_profile_id']) if profile_id in {'', 'current'} else str(profile_id)
        matches = [x for x in registry['profiles'] if x.get('profile_id') == resolved]
        if len(matches) != 1:
            raise ValueError(f'Execution profile not found: {profile_id}')
        return FullRegressionExecutionProfile.from_dict(matches[0])


class TopologyCompatibilityGuard:
    """Block silent downgrade of current FRX topology before budget reservation."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.registry = FullRegressionExecutionProfileRegistry(self.root)

    def check(self, proposed_topology: dict[str, Any], *, profile_id: str = 'current', waiver: dict[str, Any] | None = None) -> CommandResult:
        findings: list[Finding] = []
        try:
            profile = self.registry.require(profile_id)
        except Exception as exc:
            findings.append(Finding('FRX24B_PROFILE_REQUIRED_BLOCK', str(exc), Severity.BLOCK))
            return _result(TOPOLOGY_COMMAND, ok=False, message='Full Regression topology blocked.', data={'summary': {'compatible': False, 'budget_reserved': False}}, findings=findings)

        expected = profile.topology()
        mismatches: dict[str, dict[str, Any]] = {}
        for field in LOCKED_TOPOLOGY_FIELDS:
            if field in proposed_topology and proposed_topology.get(field) != expected[field]:
                mismatches[field] = {'expected': expected[field], 'proposed': proposed_topology.get(field)}
        shard_strategy = str(proposed_topology.get('shard_strategy') or 'profile-governed')
        if shard_strategy in {'count50', 'count-based-50', 'legacy-count50'}:
            mismatches['shard_strategy'] = {'expected': 'profile-governed', 'proposed': shard_strategy}

        waiver_ok = False
        if mismatches and isinstance(waiver, dict):
            allowed = set(str(x) for x in waiver.get('allowed_overrides', []))
            waiver_ok = (
                waiver.get('status') == 'owner-approved'
                and bool(str(waiver.get('waiver_id') or '').strip())
                and set(mismatches).issubset(allowed)
            )
        if mismatches and not waiver_ok:
            findings.append(Finding('FRX24B_TOPOLOGY_DOWNGRADE_BLOCK', 'Low-level topology differs from the owner-governed current profile.', Severity.BLOCK, metadata={'mismatches': mismatches, 'profile_id': profile.profile_id}))
        elif mismatches and waiver_ok:
            findings.append(Finding('FRX24B_TOPOLOGY_OVERRIDE_WAIVER', 'Owner-approved low-level topology waiver accepted and explicitly scoped.', Severity.WARNING, metadata={'mismatches': mismatches, 'waiver_id': waiver.get('waiver_id')}))

        summary = {
            'profile_id': profile.profile_id,
            'profile_sha256': profile.profile_sha256,
            'compatible': not mismatches or waiver_ok,
            'mismatches_total': len(mismatches),
            'mismatches': mismatches,
            'waiver_used': bool(mismatches and waiver_ok),
            'budget_reserved': False,
            'full_regression_runs': 0,
            'browser_runs': 0,
        }
        return _result(TOPOLOGY_COMMAND, ok=summary['compatible'], message='Full Regression topology compatibility passed.', data={'summary': summary, 'expected_topology': expected, 'proposed_topology': proposed_topology}, findings=findings or [Finding('FRX24B_TOPOLOGY_PASS', 'Proposed topology matches the current Full Regression execution profile.', Severity.INFO, metadata=summary)])

    def check_fixture(self, fixture_path: str | Path, *, profile_id: str = 'current') -> CommandResult:
        path = Path(fixture_path)
        if not path.is_absolute():
            path = self.root / path
        try:
            fixture = json.loads(path.read_text(encoding='utf-8'))
        except Exception as exc:
            return _result(TOPOLOGY_COMMAND, ok=False, message='Full Regression topology fixture blocked.', data={'summary': {'compatible': False, 'budget_reserved': False}}, findings=[Finding('FRX24B_TOPOLOGY_FIXTURE_BLOCK', f'Cannot load topology fixture: {exc}', Severity.BLOCK, path=_rel(self.root, path))])
        result = self.check(dict(fixture.get('proposed_topology') or {}), profile_id=str(fixture.get('profile_id') or profile_id))
        result.data['fixture'] = {'fixture_id': fixture.get('fixture_id'), 'kind': fixture.get('kind'), 'path': _rel(self.root, path), 'expected_status': fixture.get('expected_status')}
        return result


class FullRegressionPreflight:
    """Machine-readable profile-locked preflight. Never executes tests or reserves full budget."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.registry = FullRegressionExecutionProfileRegistry(self.root)

    @staticmethod
    def _nodeids(collection: dict[str, Any]) -> list[str]:
        rows = collection.get('nodes')
        if not isinstance(rows, list):
            raise ValueError('Collection must contain nodes[].')
        out = [str(x.get('nodeid') if isinstance(x, dict) else x) for x in rows]
        if not out or len(out) != len(set(out)) or any(not x or '::' not in x for x in out):
            raise ValueError('Collection must be non-empty, unique pytest nodeids.')
        return out

    def run(
        self,
        *,
        collection: str | Path | dict[str, Any],
        profile_id: str = 'current',
        environment_fingerprint: str | None = None,
        parallel_opt_in: bool = False,
        full_budget_state: int = 0,
        topology_fixture: str | Path | None = None,
    ) -> CommandResult:
        findings: list[Finding] = []
        profile_result = self.registry.validate()
        if not profile_result.ok:
            findings.extend(profile_result.findings)
            return self._finish(None, None, False, findings, {}, {}, {}, {}, full_budget_state)
        try:
            profile = self.registry.require(profile_id)
        except Exception as exc:
            findings.append(Finding('FRX24B_PREFLIGHT_PROFILE_BLOCK', str(exc), Severity.BLOCK))
            return self._finish(None, None, False, findings, {}, {}, {}, {}, full_budget_state)

        if isinstance(collection, dict):
            collection_payload = json.loads(json.dumps(collection))
            collection_label = '<in-memory-collection>'
        else:
            path = Path(collection)
            if not path.is_absolute():
                path = self.root / path
            collection_label = _rel(self.root, path)
            try:
                collection_payload = json.loads(path.read_text(encoding='utf-8'))
            except Exception as exc:
                findings.append(Finding('FRX24B_COLLECTION_LOAD_BLOCK', f'Cannot load sealed collection: {exc}', Severity.BLOCK, path=collection_label))
                return self._finish(profile, None, False, findings, {}, {}, {}, {}, full_budget_state)

        try:
            nodeids = self._nodeids(collection_payload)
        except ValueError as exc:
            findings.append(Finding('FRX24B_COLLECTION_BLOCK', str(exc), Severity.BLOCK, path=collection_label))
            return self._finish(profile, None, False, findings, {}, {}, {}, {}, full_budget_state)
        computed_collection_sha = TemporalShardPlanner.collection_sha256(nodeids)
        sealed_sha = str(collection_payload.get('collection_sha256') or '')
        sealed = bool(sealed_sha) and sealed_sha == computed_collection_sha
        if not sealed:
            findings.append(Finding('FRX24B_COLLECTION_SEAL_BLOCK', 'Collection must carry a collection_sha256 matching its exact nodeids.', Severity.BLOCK, path=collection_label, metadata={'declared': sealed_sha, 'computed': computed_collection_sha}))
        collection_info = {'sealed': sealed, 'collection_total': len(nodeids), 'collection_sha256': computed_collection_sha, 'collection_label': collection_label}

        if full_budget_state not in {0, 1}:
            findings.append(Finding('FRX24B_BUDGET_STATE_BLOCK', 'Full budget state must be 0 or 1.', Severity.BLOCK, metadata={'full_budget_state': full_budget_state}))
        elif full_budget_state != 0:
            findings.append(Finding('FRX24B_BUDGET_ALREADY_CONSUMED_BLOCK', 'The one-full budget is already consumed; preflight cannot authorize a second full.', Severity.BLOCK, metadata={'full_budget_state': full_budget_state}))

        if parallel_opt_in and profile.parallel_opt_in_ceiling < 2:
            findings.append(Finding('FRX24B_PARALLEL_OPT_IN_BLOCK', 'Current profile does not authorize a two-worker opt-in ceiling.', Severity.BLOCK))
        effective_workers = 2 if parallel_opt_in else profile.default_workers
        if effective_workers > profile.parallel_opt_in_ceiling:
            findings.append(Finding('FRX24B_WORKER_POLICY_BLOCK', 'Effective workers exceed the profile ceiling.', Severity.BLOCK, metadata={'effective_workers': effective_workers, 'ceiling': profile.parallel_opt_in_ceiling}))

        isolation = TestIsolationRegistry(self.root)
        isolation_schema = isolation.validate_schema()
        isolation_payload = isolation.load()
        isolation_semantics = isolation.validate_semantics(isolation_payload)
        if not isolation_schema.ok:
            findings.append(Finding('FRX24B_ISOLATION_SCHEMA_BLOCK', 'Isolation Registry failed complete JSON Schema validation.', Severity.BLOCK))
        if not isolation_semantics.get('ok'):
            findings.append(Finding('FRX24B_ISOLATION_SEMANTICS_BLOCK', 'Isolation Registry semantic validation failed.', Severity.BLOCK, metadata={'problems': isolation_semantics.get('problems', [])[:50]}))
        isolation_by_nodeid = {str(x.get('nodeid')): x for x in isolation_payload.get('entries', []) if isinstance(x, dict)}
        isolation_missing = [n for n in nodeids if n not in isolation_by_nodeid]
        if isolation_missing:
            findings.append(Finding('FRX24B_ISOLATION_COVERAGE_BLOCK', 'Isolation Registry must cover every nodeid in the sealed collection.', Severity.BLOCK, metadata={'missing_total': len(isolation_missing), 'sample': isolation_missing[:20]}))

        duration = NodeDurationRegistry(self.root)
        duration_schema = duration.validate_schema()
        duration_payload = duration.load()
        if not duration_schema.ok:
            findings.append(Finding('FRX24B_DURATION_SCHEMA_BLOCK', 'Duration Registry failed complete JSON Schema validation.', Severity.BLOCK))
        if len(duration_payload.get('rejections') or []) != 0:
            findings.append(Finding('FRX24B_DURATION_REJECTIONS_BLOCK', 'Duration Registry contains rejected telemetry.', Severity.BLOCK, metadata={'rejections_total': len(duration_payload.get('rejections') or [])}))
        environment = str(environment_fingerprint or profile.environment_fingerprint)
        duration_nodes = (((duration_payload.get('environments') or {}).get(environment) or {}).get('nodes') or {})
        duration_known = [n for n in nodeids if n in duration_nodes]
        duration_unknown = [n for n in nodeids if n not in duration_nodes]

        shadow: dict[str, Any] = {}
        conflict_consistent = False
        try:
            shadow = ParallelShadowPlanner(self.root).plan(isolation_payload, collection_nodeids=nodeids, worker_slots_preview=2, target_parallel_reduction_percent=30.0)
            conflict_consistent = int(shadow.get('implicit_unclassified_total') or 0) == 0
            if not conflict_consistent:
                findings.append(Finding('FRX24B_CONFLICT_ISOLATION_COVERAGE_BLOCK', 'Conflict/isolation projection introduced implicit unclassified nodeids.', Severity.BLOCK, metadata={'implicit_unclassified_total': shadow.get('implicit_unclassified_total')}))
        except Exception as exc:
            findings.append(Finding('FRX24B_CONFLICT_ISOLATION_BLOCK', f'Conflict/isolation consistency could not be established: {exc}', Severity.BLOCK))

        topology_result: CommandResult | None = None
        if topology_fixture:
            topology_result = TopologyCompatibilityGuard(self.root).check_fixture(topology_fixture, profile_id=profile.profile_id)
            if not topology_result.ok:
                findings.extend(topology_result.findings)

        temporal: dict[str, Any] = {}
        try:
            temporal = TemporalShardPlanner(
                self.root,
                target_shard_seconds=profile.target_shard_seconds,
                max_nodeids=profile.max_nodeids,
                max_command_chars=profile.max_command_chars,
                nodeid_transport=profile.nodeid_transport,
            ).plan(
                nodeids,
                environment_fingerprint=environment,
                collection_sha256=computed_collection_sha,
                expected_collection_sha256=computed_collection_sha,
            )
        except (TemporalPlannerError, Exception) as exc:
            findings.append(Finding('FRX24B_TEMPORAL_PLAN_BLOCK', f'Profile-governed temporal plan failed: {exc}', Severity.BLOCK))

        known_values = [float((duration_nodes[n] or {}).get('robust_estimate') or 0.0) for n in duration_known]
        fallback = round(float(statistics.median(known_values)), 6) if known_values else 1.0
        fallback = max(0.001, fallback)
        planned_known_seconds = round(sum(float(s.get('estimated_seconds') or 0.0) for s in temporal.get('shards', [])), 6) if temporal else 0.0
        eta_seconds = round(planned_known_seconds + fallback * len(duration_unknown), 6)

        proposed_generated = {
            'planner': temporal.get('planner') if temporal else profile.planner,
            'target_shard_seconds': temporal.get('target_shard_seconds') if temporal else profile.target_shard_seconds,
            'max_nodeids': temporal.get('max_nodeids') if temporal else profile.max_nodeids,
            'max_command_chars': temporal.get('max_command_chars') if temporal else profile.max_command_chars,
            'nodeid_transport': temporal.get('nodeid_transport') if temporal else profile.nodeid_transport,
            'default_workers': profile.default_workers,
            'parallel_opt_in_ceiling': profile.parallel_opt_in_ceiling,
            'shard_strategy': 'profile-governed',
        }
        generated_topology = TopologyCompatibilityGuard(self.root).check(proposed_generated, profile_id=profile.profile_id)
        if not generated_topology.ok:
            findings.extend(generated_topology.findings)

        registries_info = {
            'isolation_schema_pass': isolation_schema.ok,
            'isolation_semantics_pass': bool(isolation_semantics.get('ok')),
            'isolation_entries_total': len(isolation_payload.get('entries') or []),
            'isolation_collection_covered_total': len(nodeids) - len(isolation_missing),
            'isolation_collection_missing_total': len(isolation_missing),
            'duration_schema_pass': duration_schema.ok,
            'duration_rejections_total': len(duration_payload.get('rejections') or []),
            'duration_environment_fingerprint': environment,
            'duration_known_total': len(duration_known),
            'duration_unknown_cold_start_total': len(duration_unknown),
            'duration_coverage_policy_pass': profile.unknown_policy == 'serial',
            'conflict_isolation_consistency_pass': conflict_consistent,
            'conflict_edges_total': int(((shadow.get('conflict_graph') or {}).get('edges_total') or 0)) if shadow else 0,
            'proven_parallel_safe_total': int(shadow.get('safe_candidates_total') or 0) if shadow else 0,
            'unknown_serial_total': int(shadow.get('unknown_serial_total') or 0) if shadow else 0,
        }
        topology_info = {
            'profile_locked': generated_topology.ok,
            'planner': proposed_generated['planner'],
            'target_shard_seconds': proposed_generated['target_shard_seconds'],
            'max_nodeids': proposed_generated['max_nodeids'],
            'nodeid_transport': proposed_generated['nodeid_transport'],
            'projected_shards_total': int(temporal.get('shards_total') or 0) if temporal else 0,
            'effective_workers': effective_workers,
            'parallel_opt_in': bool(parallel_opt_in),
            'parallel_opt_in_ceiling': profile.parallel_opt_in_ceiling,
            'topology_fixture_checked': bool(topology_fixture),
            'topology_fixture_pass': None if topology_result is None else topology_result.ok,
        }
        eta_info = {
            'method': 'full-plan-known-estimates-plus-cold-start-median-fallback',
            'planned_known_seconds': planned_known_seconds,
            'cold_start_count': len(duration_unknown),
            'cold_start_fallback_seconds_each': fallback,
            'projected_full_eta_seconds': eta_seconds,
            'derived_from_full_collection': len(nodeids),
        }
        safety = {
            'preflight_read_only': True,
            'budget_reserved': False,
            'tests_executed': False,
            'full_regression_runs': 0,
            'browser_runs': 0,
            'network_used': False,
            'external_api_used': False,
            'source_mutations_performed': False,
        }
        return self._finish(profile, collection_info, True, findings, registries_info, topology_info, eta_info, safety, full_budget_state, temporal=temporal)

    def _finish(
        self,
        profile: FullRegressionExecutionProfile | None,
        collection_info: dict[str, Any] | None,
        base_ok: bool,
        findings: list[Finding],
        registries: dict[str, Any],
        topology: dict[str, Any],
        eta: dict[str, Any],
        safety: dict[str, Any],
        full_budget_state: int,
        *,
        temporal: dict[str, Any] | None = None,
    ) -> CommandResult:
        blocking = [f for f in findings if f.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        ok = base_ok and not blocking and profile is not None and collection_info is not None
        budget = {
            'full_regression_runs_allowed': profile.full_regression_runs_allowed if profile else 1,
            'full_budget_state_before': full_budget_state,
            'full_budget_available': full_budget_state == 0,
            'budget_reserved': False,
            'reservation_policy': profile.budget_reservation_policy if profile else 'reserve-only-after-preflight-pass',
        }
        report = {
            'schema_id': 'devpilot.testing.full_regression_preflight_report.v1',
            'version': '1.0.0',
            'status': 'PASS' if ok else 'BLOCK',
            'profile_id': profile.profile_id if profile else '',
            'profile_sha256': profile.profile_sha256 if profile else '0' * 64,
            'collection': collection_info or {'sealed': False, 'collection_total': 0, 'collection_sha256': ''},
            'registries': registries,
            'topology': topology,
            'eta': eta,
            'budget': budget,
            'safety': safety or {'preflight_read_only': True, 'budget_reserved': False, 'tests_executed': False, 'full_regression_runs': 0, 'browser_runs': 0},
            'findings': [f.to_dict() for f in findings],
        }
        # Self-schema validation is advisory to the result but becomes blocking when invalid.
        if profile is not None:
            schema_result = SchemaValidator(self.root).validate_payload(schema=PREFLIGHT_REPORT_CONTRACT, payload=report, instance_label='<full-regression-preflight-report>')
            if not schema_result.ok:
                findings.extend(Finding(f'FRX24B_PREFLIGHT_REPORT_{f.id}', f.message, f.severity, path=f.path, metadata=f.metadata) for f in schema_result.findings)
                report['status'] = 'BLOCK'
                report['findings'] = [f.to_dict() for f in findings]
                ok = False
        data = {'summary': {
            'status': report['status'],
            'profile_id': report['profile_id'],
            'profile_sha256': report['profile_sha256'],
            'collection_total': report['collection'].get('collection_total', 0),
            'collection_sealed': report['collection'].get('sealed', False),
            'projected_shards_total': report['topology'].get('projected_shards_total', 0),
            'effective_workers': report['topology'].get('effective_workers', 0),
            'cold_start_count': report['eta'].get('cold_start_count', 0),
            'projected_full_eta_seconds': report['eta'].get('projected_full_eta_seconds', 0.0),
            'budget_reserved': False,
            'full_regression_runs': 0,
            'browser_runs': 0,
            'blocking_findings_total': len([f for f in findings if f.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]),
        }, 'report': report, 'temporal_plan': temporal or {}}
        return _result(PREFLIGHT_COMMAND, ok=ok, message='Full Regression profile-locked preflight passed.', data=data, findings=findings or [Finding('FRX24B_PREFLIGHT_PASS', 'Profile, collection, registries, topology, ETA, worker policy and one-full budget passed preflight without reserving the full.', Severity.INFO, metadata=data['summary'])])


def load_collection_nodeids(payload: dict[str, Any]) -> list[str]:
    return FullRegressionPreflight._nodeids(payload)
