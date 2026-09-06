from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from devpilot_core.schemas import SchemaValidator


DEFAULT_REGISTRY_PATH = Path('.devpilot/testing/test_isolation_registry.json')
DEFAULT_DURATION_REGISTRY_PATH = Path('.devpilot/testing/node_duration_registry.json')
DEFAULT_SCHEMA_PATH = Path('docs/schemas/test_isolation_registry.schema.json')


class IsolationState(str, Enum):
    UNCLASSIFIED = 'UNCLASSIFIED'
    SERIAL_REQUIRED = 'SERIAL_REQUIRED'
    PROVEN_PARALLEL_SAFE = 'PROVEN_PARALLEL_SAFE'


class ResourceClass(str, Enum):
    FIXED_FILESYSTEM = 'fixed-filesystem-shared-outputs'
    SQLITE_DB = 'sqlite-db-files'
    GIT_WORKTREE = 'git-worktree-repo-mutation'
    PORT_SERVER = 'localhost-ports-server-lifecycle'
    ENV_CWD = 'process-global-env-cwd'
    GLOBAL_STATE = 'singleton-global-module-state'
    SUBPROCESS = 'subprocess-process-trees'
    NETWORK = 'network-external-service'
    CLOCK_TIME = 'clock-time-sensitive-state'
    SHARED_CACHE = 'shared-caches'
    WINDOWS_NAMED = 'windows-named-resources-locks'


_RESOURCE_PATTERNS: dict[ResourceClass, tuple[str, ...]] = {
    ResourceClass.FIXED_FILESYSTEM: ('outputs/', 'Path("outputs', "Path('outputs", 'shared_output', 'fixed_path'),
    ResourceClass.SQLITE_DB: ('sqlite3', '.db', '.sqlite', 'sqlite'),
    ResourceClass.GIT_WORKTREE: ('git ', "['git'", 'worktree', '.git', 'repo mutation'),
    ResourceClass.PORT_SERVER: ('localhost', '127.0.0.1', 'uvicorn', 'port=', 'socketserver'),
    ResourceClass.ENV_CWD: ('os.environ', 'monkeypatch.setenv', 'os.chdir', 'monkeypatch.chdir', 'cwd='),
    ResourceClass.GLOBAL_STATE: ('global ', 'singleton', 'sys.modules', 'module_state', 'lru_cache'),
    ResourceClass.SUBPROCESS: ('subprocess.', 'Popen(', 'run([', 'process tree'),
    ResourceClass.NETWORK: ('requests.', 'httpx.', 'urllib.', 'socket.', 'external_api', 'network'),
    ResourceClass.CLOCK_TIME: ('time.sleep', 'datetime.now', 'utcnow', 'freezegun', 'monotonic'),
    ResourceClass.SHARED_CACHE: ('.pytest_cache', '__pycache__', 'cache_dir', 'shared_cache', '.cache'),
    ResourceClass.WINDOWS_NAMED: ('NamedTemporaryFile', 'win32event', 'CreateMutex', 'named mutex', 'windows named'),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def _sha256_json(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class StaticHint:
    resource_class: str
    confidence: str
    evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {'resource_class': self.resource_class, 'confidence': self.confidence, 'evidence': list(self.evidence)}


class IsolationStaticAnalyzer:
    """Conservative analyzer. It can suggest risks, never authorize parallel execution."""

    def analyze_text(self, text: str) -> list[dict[str, Any]]:
        low = text.lower()
        hints: list[StaticHint] = []
        for resource, patterns in _RESOURCE_PATTERNS.items():
            matches = tuple(sorted({pat for pat in patterns if pat.lower() in low}))
            if matches:
                hints.append(StaticHint(resource.value, 'suggested', matches))
        return [h.to_dict() for h in hints]

    def analyze_nodeid(self, root: Path, nodeid: str) -> list[dict[str, Any]]:
        path_text = str(nodeid).split('::', 1)[0].replace('\\', '/')
        path = Path(root) / path_text
        if not path.exists() or not path.is_file():
            return []
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            return []
        return self.analyze_text(text)


class RuntimeEstimateResolver:
    """Uses newest available duration evidence per nodeid, preferring A successor observations naturally by last_seen."""

    def __init__(self, root: Path, registry_path: Path = DEFAULT_DURATION_REGISTRY_PATH):
        self.root = Path(root)
        self.path = self.root / registry_path
        self._data = json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else {}

    def estimate(self, nodeid: str) -> dict[str, Any]:
        candidates: list[tuple[str, dict[str, Any]]] = []
        for env, payload in (self._data.get('environments') or {}).items():
            rec = (payload.get('nodes') or {}).get(nodeid)
            if rec:
                candidates.append((env, rec))
        if not candidates:
            return {'known': False, 'seconds': None, 'confidence': 'unknown', 'source_environment': None, 'last_seen': None}
        env, rec = max(candidates, key=lambda pair: str(pair[1].get('last_seen') or ''))
        return {
            'known': True,
            'seconds': float(rec.get('robust_estimate') or 0.0),
            'confidence': str(rec.get('confidence') or 'unknown'),
            'source_environment': env,
            'last_seen': rec.get('last_seen'),
        }


class TestIsolationRegistry:
    __test__ = False
    schema_id = 'devpilot.testing.test_isolation_registry.v1'
    version = '1.0.0'

    def __init__(self, root: Path, registry_path: Path = DEFAULT_REGISTRY_PATH):
        self.root = Path(root)
        self.path = self.root / registry_path
        self.analyzer = IsolationStaticAnalyzer()
        self.runtime = RuntimeEstimateResolver(self.root)

    @staticmethod
    def default_entry(nodeid: str, *, suggested_hints: list[dict[str, Any]] | None = None, runtime_estimate: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            'nodeid': nodeid,
            'state': IsolationState.UNCLASSIFIED.value,
            'parallel_safe': False,
            'explicit_review_required': True,
            'resource_classes': [],
            'suggested_hints': list(suggested_hints or []),
            'isolation_domains': [],
            'resource_lock_keys': [],
            'runtime_estimate': runtime_estimate or {'known': False, 'seconds': None, 'confidence': 'unknown', 'source_environment': None, 'last_seen': None},
            'review': None,
        }

    def build(self, nodeids: Iterable[str], *, source_commit: str, collection_sha256: str) -> dict[str, Any]:
        ordered = [str(x) for x in nodeids]
        if len(ordered) != len(set(ordered)):
            raise ValueError('duplicate nodeids are not allowed')
        entries = []
        for nodeid in ordered:
            entries.append(self.default_entry(nodeid, suggested_hints=self.analyzer.analyze_nodeid(self.root, nodeid), runtime_estimate=self.runtime.estimate(nodeid)))
        payload = {
            'schema_id': self.schema_id,
            'version': self.version,
            'status': 'implemented-initial',
            'updated': _now(),
            'source_commit': source_commit,
            'collection_sha256': collection_sha256,
            'policy': {
                'default_state': IsolationState.UNCLASSIFIED.value,
                'default_parallel_safe': False,
                'explicit_review_required': True,
                'static_suggestions_authorize_parallel': False,
                'duration_or_name_authorize_parallel': False,
                'workers': 0,
                'full_runs': 0,
            },
            'resource_classes': [r.value for r in ResourceClass],
            'entries': entries,
        }
        payload['registry_sha256'] = _sha256_json({k: v for k, v in payload.items() if k != 'registry_sha256'})
        return payload

    def save(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

    def load(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding='utf-8'))

    @staticmethod
    def review_entry(entry: dict[str, Any], *, decision: str, reviewer: str, reason: str, reviewed_at: str, evidence_ids: list[str], resource_classes: list[str] | None = None, isolation_domains: list[str] | None = None, resource_lock_keys: list[str] | None = None) -> dict[str, Any]:
        decision = str(decision)
        if decision not in {IsolationState.PROVEN_PARALLEL_SAFE.value, IsolationState.SERIAL_REQUIRED.value}:
            raise ValueError('review decision must be PROVEN_PARALLEL_SAFE or SERIAL_REQUIRED')
        if not reviewer.strip() or not reason.strip() or not reviewed_at.strip():
            raise ValueError('reviewer, reason and reviewed_at are required')
        if decision == IsolationState.PROVEN_PARALLEL_SAFE.value and not evidence_ids:
            raise ValueError('parallel-safe review requires focal evidence')
        out = json.loads(json.dumps(entry))
        out['state'] = decision
        out['parallel_safe'] = decision == IsolationState.PROVEN_PARALLEL_SAFE.value
        out['explicit_review_required'] = False
        out['resource_classes'] = sorted(set(resource_classes or []))
        out['isolation_domains'] = sorted(set(isolation_domains or []))
        out['resource_lock_keys'] = sorted(set(resource_lock_keys or []))
        out['review'] = {
            'reviewer': reviewer,
            'reason': reason,
            'reviewed_at': reviewed_at,
            'evidence_ids': list(evidence_ids),
            'decision': decision,
        }
        return out

    def validate_schema(self, payload: dict[str, Any] | None = None):
        """Validate the complete registry JSON Schema before semantic authority is trusted."""
        validator = SchemaValidator(self.root)
        if payload is None:
            return validator.validate(schema='TestIsolationRegistry', instance=self.path)
        return validator.validate_payload(schema='TestIsolationRegistry', payload=payload, instance_label=self.path.as_posix())

    @staticmethod
    def validate_semantics(payload: dict[str, Any]) -> dict[str, Any]:
        problems: list[str] = []
        entries = payload.get('entries') or []
        seen: set[str] = set()
        safe = serial = unknown = 0
        for entry in entries:
            nodeid = str(entry.get('nodeid') or '')
            if not nodeid or nodeid in seen:
                problems.append(f'duplicate-or-empty-nodeid:{nodeid}')
            seen.add(nodeid)
            state = entry.get('state')
            parallel_safe = bool(entry.get('parallel_safe'))
            review = entry.get('review')
            if state == IsolationState.UNCLASSIFIED.value:
                unknown += 1
                if parallel_safe or review is not None or not entry.get('explicit_review_required'):
                    problems.append(f'unclassified-authority-violation:{nodeid}')
            elif state == IsolationState.SERIAL_REQUIRED.value:
                serial += 1
                if parallel_safe or not review:
                    problems.append(f'serial-review-violation:{nodeid}')
            elif state == IsolationState.PROVEN_PARALLEL_SAFE.value:
                safe += 1
                if not parallel_safe or not review or not (review.get('evidence_ids') or []):
                    problems.append(f'safe-review-evidence-violation:{nodeid}')
            else:
                problems.append(f'unknown-state:{nodeid}:{state}')
            if parallel_safe and state != IsolationState.PROVEN_PARALLEL_SAFE.value:
                problems.append(f'parallel-safe-without-proven-state:{nodeid}')
        return {
            'ok': not problems,
            'problems': problems,
            'entries_total': len(entries),
            'unclassified_total': unknown,
            'serial_required_total': serial,
            'proven_parallel_safe_total': safe,
        }

    @staticmethod
    def coverage_report(payload: dict[str, Any]) -> dict[str, Any]:
        semantics = TestIsolationRegistry.validate_semantics(payload)
        total_runtime = classified_runtime = safe_runtime = serial_runtime = unknown_runtime = 0.0
        known_runtime_nodes = 0
        for entry in payload.get('entries') or []:
            est = entry.get('runtime_estimate') or {}
            seconds = float(est.get('seconds') or 0.0) if est.get('known') else 0.0
            if est.get('known'):
                known_runtime_nodes += 1
                total_runtime += seconds
            state = entry.get('state')
            if state != IsolationState.UNCLASSIFIED.value:
                classified_runtime += seconds
            if state == IsolationState.PROVEN_PARALLEL_SAFE.value:
                safe_runtime += seconds
            elif state == IsolationState.SERIAL_REQUIRED.value:
                serial_runtime += seconds
            else:
                unknown_runtime += seconds
        def pct(x: float) -> float:
            return round((x / total_runtime * 100.0), 3) if total_runtime > 0 else 0.0
        return {
            'schema_id': 'devpilot.testing.test_isolation_coverage.v1',
            'status': 'PASS' if semantics['ok'] else 'BLOCK',
            'entries_total': semantics['entries_total'],
            'known_runtime_nodes_total': known_runtime_nodes,
            'unclassified_total': semantics['unclassified_total'],
            'serial_required_total': semantics['serial_required_total'],
            'proven_parallel_safe_total': semantics['proven_parallel_safe_total'],
            'runtime_seconds_known_total': round(total_runtime, 6),
            'runtime_weighted_classified_percent': pct(classified_runtime),
            'runtime_weighted_parallel_safe_percent': pct(safe_runtime),
            'runtime_weighted_serial_required_percent': pct(serial_runtime),
            'runtime_weighted_unclassified_percent': pct(unknown_runtime),
            'workers': 0,
            'full_runs': 0,
            'static_suggestions_authorize_parallel': False,
            'problems': semantics['problems'],
        }
