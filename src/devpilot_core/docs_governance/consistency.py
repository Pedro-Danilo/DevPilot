from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.runtime_state.models import utc_now_iso
from devpilot_core.validators.frontmatter import parse_frontmatter_file

from .authority import DocumentationAuthorityGraph, DocumentationDriftLedger, DerivedMetadataProjection

DEFAULT_CLOSURE_STATE_CONSISTENCY_REPORT = Path('outputs/reports/closure_state_consistency_report.json')


def _norm(value: Any) -> str:
    return str(value or '').strip().lower().replace('_', '-').replace(' ', '')


def _repo_path(root: Path, path: str | Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(root.resolve())).replace('\\', '/')
    except (ValueError, OSError):
        return str(path).replace('\\', '/')


@dataclass(frozen=True)
class ClosureStateConsistencyOptions:
    write_report: bool = False
    output_json: str | Path = DEFAULT_CLOSURE_STATE_CONSISTENCY_REPORT


class ClosureStateConsistencyValidator:
    """Cross-check current closure state across P0/P1 documentary authorities."""

    def __init__(self, root: Path, options: ClosureStateConsistencyOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ClosureStateConsistencyOptions()

    @property
    def configured(self) -> bool:
        return (self.root / '.devpilot/docs_governance/documentation_authority_graph.json').exists()

    def run(self) -> CommandResult:
        if not self.configured:
            return CommandResult(
                'docs-governance closure-consistency',
                True,
                ExitCode.PASS,
                'Closure state consistency is not configured for this repository.',
                data={'summary': {'configured': False, 'read_only': True, 'network_used': False}},
                findings=[],
            )
        try:
            graph = DocumentationAuthorityGraph(self.root)
            ledger = DocumentationDriftLedger(self.root)
            state = self._read_json('.devpilot/project_state.json')
            source_registry = self._read_json('.devpilot/docs_governance/source_registry.json')
            findings, checks = self._evaluate(graph, ledger, state, source_registry)
        except Exception as exc:
            finding = Finding('CLOSURE_STATE_CONSISTENCY_ERROR', f'Closure consistency could not be evaluated: {exc}', Severity.ERROR)
            return CommandResult(
                'docs-governance closure-consistency', False, ExitCode.ERROR,
                'Closure state consistency validation failed unexpectedly.',
                data={'summary': {'configured': True, 'read_only': True, 'network_used': False}}, findings=[finding],
            )

        blocking = [item for item in findings if item.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        ok = not blocking
        report = {
            'schema_version': '1.0',
            'report_id': 'frx-v2.2-closure-state-consistency',
            'status': 'PASS' if ok else 'BLOCK',
            'generated_at_utc': utc_now_iso(),
            'commit_hint': state.get('current_repo_git_commit') or state.get('gsdlc_07_e_windows_closure_commit') or state.get('gsdlc_07_e_commit'),
            'checks': checks,
            'findings': [self._finding_dict(item) for item in findings],
            'summary': {
                'configured': True,
                'checks_total': len(checks),
                'checks_passed': sum(1 for item in checks if item.get('ok')),
                'findings_total': len(findings),
                'blocking_findings_total': len(blocking),
                'drift_p0_p1_open_total': len(ledger.open_blocking_findings()),
                'closure_state_consistency_passed': ok,
                'read_only': True,
                'network_used': False,
                'external_api_used': False,
                'secrets_exposed': False,
                'mutations_performed': False,
                'full_regression_runs_consumed': int(state.get('gsdlc_07_e_full_regression_runs_consumed', 0) or 0),
            },
        }
        reports: dict[str, str] = {}
        if self.options.write_report:
            out = self.root / self.options.output_json
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            reports['json'] = _repo_path(self.root, out)
        return CommandResult(
            'docs-governance closure-consistency', ok, ExitCode.PASS if ok else ExitCode.BLOCK,
            'Closure state consistency passed.' if ok else 'Closure state consistency found blocking cross-authority drift.',
            data={'summary': report['summary'], 'report': report, 'reports': reports}, findings=findings,
        )

    def _evaluate(
        self,
        graph: DocumentationAuthorityGraph,
        ledger: DocumentationDriftLedger,
        state: dict[str, Any],
        registry: dict[str, Any],
    ) -> tuple[list[Finding], list[dict[str, Any]]]:
        findings: list[Finding] = []
        checks: list[dict[str, Any]] = []
        by_doc_id = {item.get('doc_id'): item for item in registry.get('documents', []) if isinstance(item, dict)}

        missing_paths = graph.validate_paths()
        self._check(checks, findings, 'AUTHORITY_GRAPH_PATHS_EXIST', not missing_paths, 'P0 authority graph paths exist.', metadata={'missing_paths': missing_paths})

        for contract in graph.closure_contracts:
            contract_id = str(contract.get('contract_id', 'closure-contract'))
            expected = str(contract.get('expected_closure', 'CLOSED/PASS'))
            state_field = str(contract.get('project_state_field', ''))
            self._check(
                checks, findings, f'{contract_id}:project-state', _norm(state.get(state_field)) == _norm(expected),
                f'Project State {state_field} must be {expected}.', path='.devpilot/project_state.json',
                metadata={'expected': expected, 'current': state.get(state_field)},
            )

            backlog_path = str(contract.get('backlog_path', ''))
            backlog = parse_frontmatter_file(self.root / backlog_path)
            expected_frontmatter = str(contract.get('backlog_frontmatter_status', 'closed'))
            expected_backlog_state = str(contract.get('backlog_state_expected', expected))
            self._check(
                checks, findings, f'{contract_id}:backlog-frontmatter',
                backlog.has_frontmatter and _norm(backlog.frontmatter.get('status')) == _norm(expected_frontmatter)
                and _norm(backlog.frontmatter.get('backlog_status')) == _norm(expected_backlog_state),
                'Backlog frontmatter must reflect current closure state.', path=backlog_path,
                metadata={'expected_status': expected_frontmatter, 'current_status': backlog.frontmatter.get('status'), 'expected_backlog_status': expected_backlog_state, 'current_backlog_status': backlog.frontmatter.get('backlog_status')},
            )

            source_cfg = contract.get('source_registry', {}) if isinstance(contract.get('source_registry'), dict) else {}
            backlog_entry = by_doc_id.get(source_cfg.get('backlog_doc_id'))
            self._check(
                checks, findings, f'{contract_id}:source-registry-backlog',
                bool(backlog_entry) and _norm(backlog_entry.get('status_required')) == _norm(source_cfg.get('expected_status_required', 'closed'))
                and _norm(backlog_entry.get('lifecycle')) == _norm(source_cfg.get('expected_lifecycle', 'closed')),
                'Source Registry backlog entry must be closed/current-authority consistent.', path='.devpilot/docs_governance/source_registry.json', metadata={'entry': backlog_entry},
            )

            proposal_entry = by_doc_id.get(source_cfg.get('proposal_doc_id'))
            self._check(
                checks, findings, f'{contract_id}:proposal-historical',
                bool(proposal_entry) and proposal_entry.get('classification') == source_cfg.get('proposal_expected_classification', 'historical')
                and proposal_entry.get('lifecycle') == source_cfg.get('proposal_expected_lifecycle', 'historical'),
                'Pre-closure owner proposal must be historical/superseded, never current authority.', path='.devpilot/docs_governance/source_registry.json', metadata={'entry': proposal_entry},
            )

            final_entry = by_doc_id.get(source_cfg.get('final_adjudication_doc_id'))
            self._check(
                checks, findings, f'{contract_id}:final-adjudication-registered',
                bool(final_entry) and final_entry.get('classification') == 'source-of-truth' and final_entry.get('lifecycle') == 'active',
                'Final owner adjudication must be registered as current source of truth.', path='.devpilot/docs_governance/source_registry.json', metadata={'entry': final_entry},
            )

            final_path = str(contract.get('final_adjudication_path', ''))
            final_doc = parse_frontmatter_file(self.root / final_path)
            self._check(
                checks, findings, f'{contract_id}:final-adjudication-status',
                final_doc.has_frontmatter and _norm(final_doc.frontmatter.get('status')) == _norm(contract.get('final_adjudication_status', 'closed')),
                'Final adjudication frontmatter must be closed.', path=final_path,
                metadata={'current_status': final_doc.frontmatter.get('status')},
            )

            readme = (self.root / 'README.md').read_text(encoding='utf-8')
            markers = [str(item) for item in contract.get('readme_required_markers', [])]
            self._check(checks, findings, f'{contract_id}:readme', all(item in readme for item in markers), 'README must expose current closure and next engineering action.', path='README.md', metadata={'required_markers': markers})

            changelog_path = str(contract.get('changelog_path', 'docs/release/CHANGELOG.md'))
            changelog = (self.root / changelog_path).read_text(encoding='utf-8')
            changelog_markers = [str(item) for item in contract.get('changelog_required_markers', [])]
            self._check(checks, findings, f'{contract_id}:changelog', all(item in changelog for item in changelog_markers), 'Changelog must record closure reconciliation and successor activation.', path=changelog_path, metadata={'required_markers': changelog_markers})

            next_cfg = contract.get('next', {}) if isinstance(contract.get('next'), dict) else {}
            for field, value in next_cfg.get('project_state_expectations', {}).items():
                self._check(checks, findings, f'{contract_id}:next:{field}', _norm(state.get(field)) == _norm(value), f'Project State {field} must equal {value}.', path='.devpilot/project_state.json', metadata={'expected': value, 'current': state.get(field)})

        mismatches = DerivedMetadataProjection.source_registry_mismatches(registry)
        self._check(checks, findings, 'SOURCE_REGISTRY_DERIVED_SUMMARY', not mismatches, 'Source Registry mutable summary must be derived from live documents collection.', path='.devpilot/docs_governance/source_registry.json', metadata={'mismatches': mismatches})

        open_blocking = list(ledger.open_blocking_findings())
        self._check(checks, findings, 'DOCUMENTATION_DRIFT_P0_P1_ZERO', not open_blocking, 'No P0/P1 current-active documentation drift may remain open.', path='.devpilot/docs_governance/documentation_drift_ledger.json', metadata={'open_findings': open_blocking})
        return findings, checks

    def _check(
        self,
        checks: list[dict[str, Any]],
        findings: list[Finding],
        check_id: str,
        ok: bool,
        message: str,
        *,
        path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        checks.append({'id': check_id, 'ok': bool(ok), 'path': path, 'message': message, 'metadata': metadata or {}})
        if not ok:
            findings.append(Finding(f'CLOSURE_STATE_{check_id.upper().replace(":", "_").replace("-", "_")}', message, Severity.BLOCK, path=path, metadata=metadata or {}))

    def _read_json(self, rel: str) -> dict[str, Any]:
        return json.loads((self.root / rel).read_text(encoding='utf-8'))

    @staticmethod
    def _finding_dict(item: Finding) -> dict[str, Any]:
        return {'id': item.id, 'message': item.message, 'severity': item.severity.value, 'path': item.path, 'metadata': item.metadata}
