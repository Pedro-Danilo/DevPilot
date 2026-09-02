from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .isolation_registry import IsolationState, TestIsolationRegistry
from .temporal_shard_planner import TemporalShardPlanner


DEFAULT_CANDIDATE_MANIFEST = Path('.devpilot/testing/frx_v2_3_br_candidate_manifest.json')
DEFAULT_CONTRACT_CATALOG = Path('.devpilot/testing/isolation_contract_catalog.json')


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def _sha256_json(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class NodeIsolationAudit:
    nodeid: str
    eligible: bool
    contract_id: str | None
    blockers: tuple[str, ...]
    evidence: tuple[str, ...]
    source_sha256: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            'nodeid': self.nodeid,
            'eligible': self.eligible,
            'contract_id': self.contract_id,
            'blockers': list(self.blockers),
            'evidence': list(self.evidence),
            'source_sha256': self.source_sha256,
        }


class IsolationContractCatalog:
    """Reusable contracts. None of them authorizes a test without explicit review evidence."""

    @staticmethod
    def payload() -> dict[str, Any]:
        contracts = [
            {
                'contract_id': 'LOCAL_CLONE_PER_WORKER_V1',
                'status': 'implemented-initial',
                'scope': 'repo-relative filesystem/git/sqlite/cache/process-local state',
                'guarantees': [
                    'each worker receives a separate local Git clone at the exact source commit',
                    'worker cwd, repo-relative outputs, Git metadata, SQLite files and caches are clone-local',
                    'process-global env/cwd/module state is process-local',
                    'subprocesses inherit the worker clone cwd unless the test explicitly overrides it',
                ],
                'forbidden_external_resources': [
                    'real-network-or-external-service',
                    'fixed-localhost-port-or-server-lifecycle',
                    'windows-named-resource',
                    'absolute-external-write-path',
                    'unbounded-clock-or-sleep-dependency',
                ],
                'dynamic_probe_required': True,
                'parallel_safe_by_contract_alone': False,
            },
            {
                'contract_id': 'TMP_PATH_PROCESS_ISOLATED_V1',
                'status': 'implemented-initial',
                'scope': 'pytest tmp_path plus process-local state inside LOCAL_CLONE_PER_WORKER_V1',
                'guarantees': [
                    'pytest tmp_path is unique per test process',
                    'worker repository is a separate local clone',
                    'repo-relative fallback writes remain worker-local',
                ],
                'forbidden_external_resources': [
                    'real-network-or-external-service',
                    'fixed-localhost-port-or-server-lifecycle',
                    'windows-named-resource',
                    'absolute-external-write-path',
                    'unbounded-clock-or-sleep-dependency',
                ],
                'dynamic_probe_required': True,
                'parallel_safe_by_contract_alone': False,
            },
            {
                'contract_id': 'READ_ONLY_REPO_V1',
                'status': 'implemented-initial',
                'scope': 'read-only repo evaluation inside LOCAL_CLONE_PER_WORKER_V1',
                'guarantees': [
                    'test contract asserts no source mutation',
                    'worker repository is a separate local clone',
                    'no external shared resource is allowed',
                ],
                'forbidden_external_resources': [
                    'real-network-or-external-service',
                    'fixed-localhost-port-or-server-lifecycle',
                    'windows-named-resource',
                    'absolute-external-write-path',
                    'unbounded-clock-or-sleep-dependency',
                ],
                'dynamic_probe_required': True,
                'parallel_safe_by_contract_alone': False,
            },
        ]
        payload = {
            'schema_id': 'devpilot.testing.isolation_contract_catalog.v1',
            'version': '1.0.0',
            'status': 'implemented-initial',
            'created_by': 'FRX-v2.3-BR',
            'workers_general_suite': 0,
            'full_runs': 0,
            'contracts': contracts,
        }
        payload['catalog_sha256'] = _sha256_json(payload)
        return payload


class FunctionIsolationAuditor:
    """Node-level structural review for BR.

    It is deliberately conservative. Passing this audit only makes a node a candidate;
    PROVEN_PARALLEL_SAFE additionally requires a checked-in contract assignment and a
    successful Windows contract probe.
    """

    _external_patterns = {
        'real-network-or-external-service': (
            r'\brequests\.', r'\bhttpx\.', r'\burllib\.', r'\bsocket\.', r'create_connection\(',
        ),
        'fixed-localhost-port-or-server-lifecycle': (
            r'127\.0\.0\.1', r'\blocalhost\b', r'uvicorn', r'httpserver', r'tcpserver',
            r'serve_forever\(', r'\.bind\(', r'\.listen\(',
        ),
        'windows-named-resource': (r'win32event', r'createmutex', r'named mutex', r'global\\'),
        'unbounded-clock-or-sleep-dependency': (r'time\.sleep\(',),
    }
    _absolute_windows_path = re.compile(r'[A-Za-z]:\\[^"\']+')

    def __init__(self, root: Path):
        self.root = Path(root)

    def _function(self, nodeid: str) -> tuple[Path, str, ast.AST | None, str]:
        path_text, *parts = nodeid.split('::')
        function_name = parts[-1].split('[', 1)[0] if parts else ''
        path = self.root / path_text
        if not path.exists():
            return path, function_name, None, ''
        source = path.read_text(encoding='utf-8')
        tree = ast.parse(source)
        target = next(
            (n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == function_name),
            None,
        )
        if target is None:
            return path, function_name, None, ''
        lines = source.splitlines()
        body_parts = ['\n'.join(lines[target.lineno - 1:(target.end_lineno or target.lineno)])]
        # Include directly referenced top-level helpers/classes from the same test module.
        # This catches hidden external resources such as a local HTTPServer wrapped in a helper.
        top_defs = {
            n.name: n
            for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        pending = {n.id for n in ast.walk(target) if isinstance(n, ast.Name) and n.id in top_defs}
        visited: set[str] = set()
        for _ in range(3):
            if not pending:
                break
            current = sorted(pending - visited)
            pending = set()
            for name in current:
                visited.add(name)
                helper = top_defs[name]
                body_parts.append('\n'.join(lines[helper.lineno - 1:(helper.end_lineno or helper.lineno)]))
                pending.update(
                    n.id for n in ast.walk(helper)
                    if isinstance(n, ast.Name) and n.id in top_defs and n.id not in visited
                )
        body = '\n'.join(body_parts)
        return path, function_name, target, body

    def audit(self, nodeid: str, requested_contract: str | None = None) -> NodeIsolationAudit:
        path, _, target, body = self._function(nodeid)
        if target is None:
            return NodeIsolationAudit(nodeid, False, None, ('test-function-not-found',), (), None)
        low = body.lower()
        blockers: list[str] = []
        evidence: list[str] = []
        for blocker, patterns in self._external_patterns.items():
            if any(re.search(pattern, low, flags=re.I) for pattern in patterns):
                blockers.append(blocker)
        # Absolute Windows paths are external to a worker clone unless they are only documentation strings.
        if self._absolute_windows_path.search(body):
            blockers.append('absolute-external-write-path')
        args = [a.arg for a in target.args.args] if isinstance(target, (ast.FunctionDef, ast.AsyncFunctionDef)) else []
        if 'os.environ[' in low and 'monkeypatch' not in args:
            blockers.append('unscoped-process-environment-mutation')
        if 'tempfile.gettempdir' in low:
            blockers.append('external-system-temp-path')
        if 'tmp_path' in args:
            inferred = 'TMP_PATH_PROCESS_ISOLATED_V1'
            evidence.append('pytest-tmp-path-fixture')
        elif ('mutations_performed' in low and 'is false' in low) or ('source_mutations' in low and 'is false' in low):
            inferred = 'READ_ONLY_REPO_V1'
            evidence.append('explicit-no-mutation-assertion')
        else:
            inferred = 'LOCAL_CLONE_PER_WORKER_V1'
            evidence.append('worker-local-clone-required')
        contract = requested_contract or inferred
        if requested_contract and requested_contract != inferred:
            # Explicit manifest may choose the stronger clone contract, but never downgrade tmp/read-only into an unrelated contract.
            if requested_contract == 'LOCAL_CLONE_PER_WORKER_V1':
                evidence.append(f'explicit-contract-override:{inferred}')
            else:
                blockers.append(f'contract-mismatch:{requested_contract}!={inferred}')
        src_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        return NodeIsolationAudit(nodeid, not blockers, contract if not blockers else None, tuple(sorted(set(blockers))), tuple(evidence), src_sha)


class RuntimeSafePromotion:
    """Builds a successor registry from explicit candidate reviews and probe receipts."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.registry = TestIsolationRegistry(self.root)
        self.auditor = FunctionIsolationAuditor(self.root)

    def successor_registry(self, base_payload: dict[str, Any], collection_nodeids: Iterable[str], *, source_commit: str) -> dict[str, Any]:
        ordered = [str(x) for x in collection_nodeids]
        if not ordered or len(ordered) != len(set(ordered)):
            raise ValueError('collection must be unique and non-empty')
        by_nodeid = {str(e['nodeid']): json.loads(json.dumps(e)) for e in base_payload.get('entries') or []}
        entries: list[dict[str, Any]] = []
        for nodeid in ordered:
            if nodeid in by_nodeid:
                entry = by_nodeid[nodeid]
                entry['runtime_estimate'] = self.registry.runtime.estimate(nodeid)
                entry['suggested_hints'] = self.registry.analyzer.analyze_nodeid(self.root, nodeid)
            else:
                entry = TestIsolationRegistry.default_entry(
                    nodeid,
                    suggested_hints=self.registry.analyzer.analyze_nodeid(self.root, nodeid),
                    runtime_estimate=self.registry.runtime.estimate(nodeid),
                )
            entries.append(entry)
        payload = json.loads(json.dumps(base_payload))
        payload['status'] = 'implemented-initial'
        payload['updated'] = _now()
        payload['source_commit'] = source_commit
        payload['collection_sha256'] = TemporalShardPlanner.collection_sha256(ordered)
        payload['entries'] = entries
        payload['registry_sha256'] = _sha256_json({k: v for k, v in payload.items() if k != 'registry_sha256'})
        return payload

    def apply_evidence(
        self,
        payload: dict[str, Any],
        *,
        candidate_manifest: dict[str, Any],
        contract_probe_report: dict[str, Any],
        reviewer: str,
        reviewed_at: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        out = json.loads(json.dumps(payload))
        by_nodeid = {str(e['nodeid']): e for e in out.get('entries') or []}
        probe_by_contract = {str(x['contract_id']): x for x in contract_probe_report.get('contracts') or []}
        decisions: list[dict[str, Any]] = []
        for item in candidate_manifest.get('candidates') or []:
            nodeid = str(item['nodeid'])
            contract_id = str(item['contract_id'])
            entry = by_nodeid.get(nodeid)
            if entry is None:
                decisions.append({'nodeid': nodeid, 'decision': 'UNCLASSIFIED', 'reason': 'nodeid-not-in-current-collection'})
                continue
            audit = self.auditor.audit(nodeid, requested_contract=contract_id)
            probe = probe_by_contract.get(contract_id) or {}
            if not audit.eligible:
                reviewed = TestIsolationRegistry.review_entry(
                    entry,
                    decision=IsolationState.SERIAL_REQUIRED.value,
                    reviewer=reviewer,
                    reason='BR structural audit rejected external/shared resource: ' + ','.join(audit.blockers),
                    reviewed_at=reviewed_at,
                    evidence_ids=[f'br-structural-audit:{item.get("candidate_id")}'],
                    resource_classes=[h['resource_class'] for h in entry.get('suggested_hints') or []],
                    isolation_domains=['serial:structural-blocker'],
                    resource_lock_keys=[],
                )
                by_nodeid[nodeid] = reviewed
                decisions.append({'nodeid': nodeid, 'decision': 'SERIAL_REQUIRED', 'contract_id': contract_id, 'audit': audit.to_dict()})
                continue
            if probe.get('status') != 'PASS':
                decisions.append({'nodeid': nodeid, 'decision': 'UNCLASSIFIED', 'contract_id': contract_id, 'reason': 'contract-probe-not-pass', 'audit': audit.to_dict()})
                continue
            evidence_ids = [
                f'br-structural-audit:{item.get("candidate_id")}',
                str(probe.get('evidence_id') or f'br-contract-probe:{contract_id}'),
            ]
            reviewed = TestIsolationRegistry.review_entry(
                entry,
                decision=IsolationState.PROVEN_PARALLEL_SAFE.value,
                reviewer=reviewer,
                reason=f'Explicit BR review: structural audit PASS and {contract_id} dynamic isolation probe PASS.',
                reviewed_at=reviewed_at,
                evidence_ids=evidence_ids,
                resource_classes=[h['resource_class'] for h in entry.get('suggested_hints') or []],
                isolation_domains=[],
                resource_lock_keys=[],
            )
            by_nodeid[nodeid] = reviewed
            decisions.append({'nodeid': nodeid, 'decision': 'PROVEN_PARALLEL_SAFE', 'contract_id': contract_id, 'audit': audit.to_dict(), 'evidence_ids': evidence_ids})
        out['entries'] = [by_nodeid[str(e['nodeid'])] for e in out.get('entries') or []]
        out['updated'] = reviewed_at
        out['registry_sha256'] = _sha256_json({k: v for k, v in out.items() if k != 'registry_sha256'})
        coverage = TestIsolationRegistry.coverage_report(out)
        report = {
            'schema_id': 'devpilot.testing.runtime_safe_promotion_report.v1',
            'status': 'PASS' if coverage['status'] == 'PASS' else 'BLOCK',
            'reviewer': reviewer,
            'reviewed_at': reviewed_at,
            'candidate_entries_total': len(candidate_manifest.get('candidates') or []),
            'decisions': decisions,
            'coverage': coverage,
            'workers_general_suite': 0,
            'full_runs': 0,
            'registry_sha256': out['registry_sha256'],
        }
        return out, report
