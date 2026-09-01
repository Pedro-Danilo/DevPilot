from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from devpilot_core.cli_models import CommandResult, ExitCode
from devpilot_core.runtime_state.models import utc_now_iso

from .authority import DocumentationAuthorityGraph

DEFAULT_DOC_IMPACT_REPORT = Path('outputs/reports/doc_impact_plan.json')


@dataclass(frozen=True)
class DocImpactPlanOptions:
    write_report: bool = False
    output_json: str | Path = DEFAULT_DOC_IMPACT_REPORT


class DocImpactPlanner:
    """Plan documentation/contract reconciliation from changed repository paths."""

    CLOSURE_CORE = {
        '.devpilot/project_state.json',
        '.devpilot/docs_governance/source_registry.json',
        '.devpilot/docs_governance/documentation_authority_graph.json',
        '.devpilot/docs_governance/documentation_drift_ledger.json',
        'DEVPL-GSDLC-07_agent_assisted_engineering_and_rag_v1_4_0_APPROVED_REBOUND.md',
        'README.md',
        'docs/release/CHANGELOG.md',
        'DEVPL_GSDLC_07_E_FINAL_OWNER_ADJUDICATION_v1_0_0.md',
        'DEVPL_GSDLC_07_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md',
    }

    def __init__(self, root: Path, changed_paths: Iterable[str], options: DocImpactPlanOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.changed_paths = tuple(sorted({str(item).replace('\\', '/').removeprefix('./') for item in changed_paths if str(item).strip()}))
        self.options = options or DocImpactPlanOptions()

    def run(self) -> CommandResult:
        registry = json.loads((self.root / '.devpilot/docs_governance/source_registry.json').read_text(encoding='utf-8'))
        graph = DocumentationAuthorityGraph(self.root)
        impacted_docs: set[str] = set()
        tests: set[str] = set()
        criticalities: set[str] = set()
        reasons: list[dict[str, Any]] = []

        changed = set(self.changed_paths)
        for item in registry.get('documents', []):
            if not isinstance(item, dict):
                continue
            related = {str(item.get('path', '')).replace('\\', '/')}
            for key in ('machine_readable_counterparts', 'human_readable_counterparts', 'derived_documents', 'related_adrs'):
                related.update(str(value).replace('\\', '/') for value in item.get(key, []) if isinstance(value, str))
            matched = sorted(changed & related)
            if matched:
                impacted_docs.add(str(item.get('path', '')))
                tests.update(str(value) for value in item.get('required_tests', []) if isinstance(value, str))
                criticalities.add(str(item.get('criticality', '')))
                reasons.append({'doc_id': item.get('doc_id'), 'path': item.get('path'), 'matched_changed_paths': matched})

        closure_consistency_required = bool(changed & self.CLOSURE_CORE)
        if closure_consistency_required:
            impacted_docs.update(self.CLOSURE_CORE)
            tests.update({
                'tests/test_documentation_closure_consistency_current.py',
                'tests/test_documentation_source_registry_schema.py',
            })
            criticalities.add('P0')

        plan = {
            'schema_version': '1.0',
            'plan_id': 'frx-v2.2-doc-impact-plan',
            'status': 'PASS',
            'generated_at_utc': utc_now_iso(),
            'changed_paths': list(self.changed_paths),
            'impacted_documents': sorted(impacted_docs),
            'required_tests': sorted(tests),
            'criticalities': sorted(item for item in criticalities if item),
            'closure_consistency_required': closure_consistency_required,
            'full_regression_required': False,
            'browser_required': False,
            'reasons': reasons,
            'summary': {
                'changed_paths_total': len(self.changed_paths),
                'impacted_documents_total': len(impacted_docs),
                'required_tests_total': len(tests),
                'p0_p1_reconciliation_required': bool({'P0', 'P1'} & criticalities),
                'network_used': False,
                'external_api_used': False,
                'secrets_exposed': False,
                'mutations_performed': False,
                'full_regression_runs_consumed': 0,
            },
        }
        reports: dict[str, str] = {}
        if self.options.write_report:
            out = self.root / self.options.output_json
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            reports['json'] = str(out.relative_to(self.root)).replace('\\', '/')
        return CommandResult(
            'docs-governance impact-plan', True, ExitCode.PASS,
            'Documentation impact plan generated.',
            data={'summary': plan['summary'], 'plan': plan, 'reports': reports}, findings=[],
        )
