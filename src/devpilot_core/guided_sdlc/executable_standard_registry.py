from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import jsonschema

REGISTRY_REL = Path('.devpilot/gsdlc/executable_standard_registry.json')
SCHEMA_REL = Path('docs/schemas/executable_standard_registry.schema.json')
READINESS_REL = Path('.devpilot/readiness/readiness_requirements.json')
TRANSITION_CATALOG_REL = Path('.devpilot/gsdlc/workflow_transition_catalog.json')
EXPECTED_SCHEMA_ID = 'SCHEMA-DEVPL-GSDLC-05-A-EXECUTABLE-STANDARD-REGISTRY-V1'
EXPECTED_SCHEMA_VERSION = '1.0'
_SEMVER = re.compile(r'^\d+\.\d+\.\d+$')


class ExecutableStandardRegistryError(ValueError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ids(rows: list[Mapping[str, Any]], key: str) -> list[str]:
    return [str(row.get(key, '')) for row in rows]


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    dup: set[str] = set()
    for value in values:
        if value in seen:
            dup.add(value)
        seen.add(value)
    return sorted(dup)


def _cycle_nodes(graph: Mapping[str, set[str]]) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    cycle: set[str] = set()

    def walk(node: str, stack: list[str]) -> None:
        if node in visited:
            return
        if node in visiting:
            if node in stack:
                cycle.update(stack[stack.index(node):])
            else:
                cycle.add(node)
            return
        visiting.add(node)
        stack.append(node)
        for dep in sorted(graph.get(node, set())):
            if dep in graph:
                walk(dep, stack)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in sorted(graph):
        walk(node, [])
    return sorted(cycle)


@dataclass(frozen=True)
class RegistryFinding:
    finding_id: str
    severity: str
    message: str
    path: str | None = None
    subject_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            'finding_id': self.finding_id,
            'severity': self.severity,
            'message': self.message,
            'path': self.path,
            'subject_id': self.subject_id,
        }


@dataclass(frozen=True)
class RegistryValidationReport:
    status: str
    findings: tuple[RegistryFinding, ...]
    metrics: dict[str, Any]
    source_drift: tuple[dict[str, Any], ...]

    @property
    def ok(self) -> bool:
        return self.status == 'PASS'

    def to_dict(self) -> dict[str, Any]:
        return {
            'schema_id': 'DEVPL-GSDLC-05-A-EXECUTABLE-STANDARD-REGISTRY-VALIDATION-v1',
            'status': self.status,
            'findings': [f.to_dict() for f in self.findings],
            'metrics': dict(self.metrics),
            'source_drift': [dict(row) for row in self.source_drift],
            'network_used': False,
            'external_api_used': False,
            'model_execution_used': False,
            'mutations_performed': False,
            'source_mutations_performed': False,
        }


class ExecutableStandardRegistryValidator:
    """Fail-closed validator for the GSDLC-05-A executable standards registry.

    Documentation under docs/standards remains normative. The registry is a
    machine-readable projection and cannot silently override source content.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()

    def load(self, registry_path: Path | None = None) -> dict[str, Any]:
        path = Path(registry_path) if registry_path else self.root / REGISTRY_REL
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
        except Exception as exc:  # fail closed at boundary
            raise ExecutableStandardRegistryError(f'cannot load registry: {exc}') from exc
        if not isinstance(payload, dict):
            raise ExecutableStandardRegistryError('registry root must be an object')
        return payload

    def validate(self, payload: Mapping[str, Any] | None = None) -> RegistryValidationReport:
        findings: list[RegistryFinding] = []
        drift: list[dict[str, Any]] = []
        data = dict(payload or self.load())

        # Strict schema validation first.
        try:
            schema = json.loads((self.root / SCHEMA_REL).read_text(encoding='utf-8'))
            jsonschema.Draft202012Validator(schema).validate(data)
        except Exception as exc:
            findings.append(RegistryFinding('REGISTRY_SCHEMA_INVALID', 'BLOCK', str(exc), SCHEMA_REL.as_posix()))

        if data.get('schema_id') != EXPECTED_SCHEMA_ID or data.get('schema_version') != EXPECTED_SCHEMA_VERSION:
            findings.append(RegistryFinding('REGISTRY_SCHEMA_IDENTITY_UNSUPPORTED', 'BLOCK', 'Unsupported registry schema identity.'))
        if not _SEMVER.fullmatch(str(data.get('registry_version', ''))):
            findings.append(RegistryFinding('REGISTRY_VERSION_INVALID', 'BLOCK', 'registry_version must be SemVer.'))
        if data.get('registry_authoritative') is True and data.get('status') != 'approved':
            findings.append(RegistryFinding('REGISTRY_AUTHORITY_PREMATURE', 'BLOCK', 'Registry cannot become authoritative before owner approval.'))

        phases = list(data.get('phases') or [])
        steps = list(data.get('steps') or [])
        artifacts = list(data.get('artifacts') or [])
        requirements = list(data.get('requirements') or [])

        for rows, key, code in [
            (phases, 'phase_id', 'PHASE_ID_DUPLICATE'),
            (steps, 'step_id', 'STEP_ID_DUPLICATE'),
            (artifacts, 'artifact_id', 'ARTIFACT_ID_DUPLICATE'),
            (requirements, 'requirement_id', 'REQUIREMENT_ID_DUPLICATE'),
        ]:
            for duplicate in _duplicates(_ids(rows, key)):
                findings.append(RegistryFinding(code, 'BLOCK', f'Duplicate {key}: {duplicate}', subject_id=duplicate))

        phase_ids = set(_ids(phases, 'phase_id'))
        step_ids = set(_ids(steps, 'step_id'))
        artifact_ids = set(_ids(artifacts, 'artifact_id'))

        phase_membership: dict[str, int] = {sid: 0 for sid in step_ids}
        for phase in phases:
            for sid in phase.get('step_ids') or []:
                if sid not in step_ids:
                    findings.append(RegistryFinding('PHASE_STEP_UNKNOWN', 'BLOCK', f'Phase references unknown step {sid}.', subject_id=str(phase.get('phase_id'))))
                else:
                    phase_membership[sid] += 1
        for step in steps:
            sid = str(step.get('step_id'))
            phase_id = str(step.get('phase_id'))
            if phase_id not in phase_ids:
                findings.append(RegistryFinding('STEP_PHASE_UNKNOWN', 'BLOCK', f'Step references unknown phase {phase_id}.', subject_id=sid))
            if phase_membership.get(sid, 0) != 1:
                findings.append(RegistryFinding('ORPHAN_OR_MULTIPARENT_STEP', 'BLOCK', 'Step must belong to exactly one phase.', subject_id=sid))
            for aid in step.get('artifact_ids') or []:
                if aid not in artifact_ids:
                    findings.append(RegistryFinding('STEP_ARTIFACT_UNKNOWN', 'BLOCK', f'Step references unknown artifact {aid}.', subject_id=sid))
            if step.get('mandatory') and not step.get('source_refs'):
                findings.append(RegistryFinding('MANDATORY_STEP_WITHOUT_SOURCE', 'BLOCK', 'Mandatory step requires source_refs.', subject_id=sid))
            if step.get('mandatory') and (not step.get('validators') or not step.get('exit_gates') or not step.get('next_action_refs')):
                findings.append(RegistryFinding('MANDATORY_STEP_INCOMPLETE', 'BLOCK', 'Mandatory step requires validators, exit gates and next actions.', subject_id=sid))

        # Transition dependency graph. Reference edges are deliberately excluded.
        graph: dict[str, set[str]] = {sid: set() for sid in step_ids}
        for step in steps:
            sid = str(step.get('step_id'))
            for edge in step.get('prerequisites') or []:
                dep = str(edge.get('step_id'))
                if dep not in step_ids:
                    findings.append(RegistryFinding('STEP_PREREQUISITE_UNKNOWN', 'BLOCK', f'Unknown prerequisite {dep}.', subject_id=sid))
                elif edge.get('edge_kind') == 'transition':
                    graph[sid].add(dep)
        cycles = _cycle_nodes(graph)
        for sid in cycles:
            findings.append(RegistryFinding('TRANSITION_CYCLE', 'BLOCK', 'Transition dependency cycle detected.', subject_id=sid))

        # Critical controls cannot be disabled without an explicit ADR/decision reference.
        for req in requirements:
            rid = str(req.get('requirement_id'))
            aid = str(req.get('artifact_id'))
            if aid not in artifact_ids:
                findings.append(RegistryFinding('REQUIREMENT_ARTIFACT_UNKNOWN', 'BLOCK', f'Requirement references unknown artifact {aid}.', subject_id=rid))
            if req.get('critical') and not req.get('enabled', False):
                decision = str(req.get('decision_ref') or '')
                if not decision.startswith('docs/'):
                    findings.append(RegistryFinding('CRITICAL_CONTROL_DISABLED_WITHOUT_DECISION', 'BLOCK', 'Critical requirement disabled without governed decision/ADR.', subject_id=rid))
            if req.get('mandatory') and not req.get('source_refs'):
                findings.append(RegistryFinding('MANDATORY_REQUIREMENT_WITHOUT_SOURCE', 'BLOCK', 'Mandatory requirement requires source_refs.', subject_id=rid))

        # Verify source path, heading and byte hash. Standards docs remain normative.
        all_refs: list[Mapping[str, Any]] = []
        for collection in (phases, steps, artifacts, requirements):
            for row in collection:
                all_refs.extend(row.get('source_refs') or [])
        seen_ref_keys: set[tuple[str, str, str, str]] = set()
        for ref in all_refs:
            key = (str(ref.get('doc_id')), str(ref.get('path')), str(ref.get('heading')), str(ref.get('source_sha256')))
            if key in seen_ref_keys:
                continue
            seen_ref_keys.add(key)
            rel = Path(key[1])
            source_path = (self.root / rel).resolve()
            if not str(source_path).startswith(str((self.root / 'docs/standards').resolve())):
                findings.append(RegistryFinding('SOURCE_OUTSIDE_NORMATIVE_ROOT', 'BLOCK', 'Executable rule source must be under docs/standards.', key[1], key[0]))
                continue
            if not source_path.is_file():
                findings.append(RegistryFinding('SOURCE_PATH_MISSING', 'BLOCK', 'Source path does not exist.', key[1], key[0]))
                continue
            actual_sha = _sha256(source_path)
            row = {'doc_id': key[0], 'path': key[1], 'heading': key[2], 'expected_sha256': key[3], 'actual_sha256': actual_sha, 'status': 'PASS'}
            if actual_sha != key[3]:
                row['status'] = 'BLOCK'
                findings.append(RegistryFinding('SOURCE_HASH_DRIFT', 'BLOCK', 'Normative source SHA-256 changed.', key[1], key[0]))
            text = source_path.read_text(encoding='utf-8')
            if key[2] not in text.splitlines():
                row['status'] = 'BLOCK'
                findings.append(RegistryFinding('SOURCE_HEADING_MISSING', 'BLOCK', 'Mapped heading no longer exists.', key[1], key[0]))
            drift.append(row)

        # Mandatory pre-code coverage is derived from the live readiness collection.
        readiness = json.loads((self.root / READINESS_REL).read_text(encoding='utf-8'))
        expected_artifacts = {f"artifact:{row['artifact']}" for row in readiness.get('requirements', []) if row.get('critical')}
        mapped_artifacts = {str(req.get('artifact_id')) for req in requirements if req.get('mandatory') and req.get('enabled', False)}
        missing_mandatory = sorted(expected_artifacts - mapped_artifacts)
        extra_mandatory = sorted(mapped_artifacts - expected_artifacts)
        for aid in missing_mandatory:
            findings.append(RegistryFinding('MANDATORY_PRECODE_UNMAPPED', 'BLOCK', 'Critical readiness artifact is not mapped.', subject_id=aid))
        for aid in extra_mandatory:
            findings.append(RegistryFinding('MANDATORY_PRECODE_NOT_IN_READINESS', 'BLOCK', 'Mandatory mapping has no live readiness requirement.', subject_id=aid))

        # Coexistence with the frozen generic transition catalog.
        for ref in data.get('integration_refs') or []:
            path = self.root / str(ref.get('path'))
            if not path.is_file():
                findings.append(RegistryFinding('INTEGRATION_REF_MISSING', 'BLOCK', 'Integration reference missing.', str(ref.get('path'))))
                continue
            if _sha256(path) != ref.get('sha256'):
                findings.append(RegistryFinding('INTEGRATION_REF_DRIFT', 'BLOCK', 'Integration reference hash drift.', str(ref.get('path'))))
            fragment = str(ref.get('expected_scope_fragment') or '')
            if fragment and fragment not in path.read_text(encoding='utf-8'):
                findings.append(RegistryFinding('WORKFLOW_CATALOG_SCOPE_DRIFT', 'BLOCK', 'Generic transition catalog no longer declares GSDLC-05 deferral.', str(ref.get('path'))))

        blocking = [f for f in findings if f.severity == 'BLOCK']
        mapped = len(expected_artifacts & mapped_artifacts)
        total = len(expected_artifacts)
        metrics = {
            'standards_total': len(data.get('standards') or []),
            'phases_total': len(phases),
            'steps_total': len(steps),
            'artifacts_total': len(artifacts),
            'requirements_total': len(requirements),
            'mandatory_pre_code_total': total,
            'mandatory_pre_code_mapped': mapped,
            'mandatory_pre_code_mapping_percent': round((mapped / total * 100.0) if total else 100.0, 2),
            'orphan_critical_steps': sum(1 for f in findings if f.finding_id == 'ORPHAN_OR_MULTIPARENT_STEP'),
            'duplicate_ids_total': sum(1 for f in findings if f.finding_id.endswith('_DUPLICATE')),
            'transition_cycle_nodes_total': len(cycles),
            'source_refs_unique_total': len(seen_ref_keys),
            'source_drift_total': sum(1 for row in drift if row['status'] != 'PASS'),
            'blocking_findings_total': len(blocking),
            'registry_authoritative': bool(data.get('registry_authoritative')),
            'owner_approval_required_for_promotion': bool(data.get('owner_approval_required_for_promotion')),
        }
        return RegistryValidationReport('PASS' if not blocking else 'BLOCK', tuple(findings), metrics, tuple(drift))


class ExecutableStandardRegistryService:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.validator = ExecutableStandardRegistryValidator(self.root)

    def validate_current(self) -> dict[str, Any]:
        return self.validator.validate().to_dict()

    def source_mapping_coverage(self) -> dict[str, Any]:
        report = self.validator.validate()
        return {
            'schema_id': 'DEVPL-GSDLC-05-A-STANDARD-MAPPING-COVERAGE-v1',
            'status': report.status,
            'mandatory_pre_code_total': report.metrics['mandatory_pre_code_total'],
            'mandatory_pre_code_mapped': report.metrics['mandatory_pre_code_mapped'],
            'mandatory_pre_code_mapping_percent': report.metrics['mandatory_pre_code_mapping_percent'],
            'orphan_critical_steps': report.metrics['orphan_critical_steps'],
            'new_rule_without_source_total': sum(1 for f in report.findings if f.finding_id in {'MANDATORY_STEP_WITHOUT_SOURCE','MANDATORY_REQUIREMENT_WITHOUT_SOURCE'}),
            'network_used': False,
            'external_api_used': False,
            'mutations_performed': False,
        }

    def source_drift_report(self) -> dict[str, Any]:
        report = self.validator.validate()
        return {
            'schema_id': 'DEVPL-GSDLC-05-A-SOURCE-DRIFT-REPORT-v1',
            'status': 'PASS' if report.metrics['source_drift_total'] == 0 else 'BLOCK',
            'sources_checked_total': report.metrics['source_refs_unique_total'],
            'source_drift_total': report.metrics['source_drift_total'],
            'sources': [dict(row) for row in report.source_drift],
            'network_used': False,
            'external_api_used': False,
            'mutations_performed': False,
        }
