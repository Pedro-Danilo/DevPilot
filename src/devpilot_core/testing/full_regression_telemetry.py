from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


class FullRegressionTelemetryExporter:
    """Export immutable v2.1 terminal telemetry for later v2.2/v2.3 design.

    v2.2 consumes nodeid/outcome/duration samples. v2.3 remains conservative:
    every node is UNCLASSIFIED, parallel_safe=false and requires explicit review.
    """

    def __init__(self, root: Path, *, runtime_root: Path = Path('outputs/testing/full_regression')) -> None:
        self.root = Path(root).resolve()
        self.runtime_root = runtime_root if runtime_root.is_absolute() else self.root / runtime_root

    def export(self, session_id: str, *, output_path: Path | None = None) -> CommandResult:
        command = 'tests full-session export-telemetry'
        session_dir = self.runtime_root / session_id
        if not session_dir.is_dir():
            return CommandResult(command, False, ExitCode.BLOCK, 'Full-regression session directory was not found.', {}, [Finding('FRX_TELEMETRY_SESSION_MISSING', session_id, Severity.BLOCK)])
        receipts = sorted((session_dir / 'receipts').glob('*.json')) if (session_dir / 'receipts').is_dir() else []
        if not receipts:
            return CommandResult(command, False, ExitCode.BLOCK, 'No shard receipts were found for telemetry export.', {}, [Finding('FRX_TELEMETRY_RECEIPTS_MISSING', session_id, Severity.BLOCK)])
        samples: list[dict[str, Any]] = []
        for receipt_path in receipts:
            payload = json.loads(receipt_path.read_text(encoding='utf-8'))
            outcomes = payload.get('outcomes') or {}
            durations: dict[str, float] = {}
            outcome_log_rel = payload.get('outcome_log_path')
            if outcome_log_rel:
                outcome_log = self.root / str(outcome_log_rel)
                if outcome_log.is_file():
                    for line in outcome_log.read_text(encoding='utf-8', errors='replace').splitlines():
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        nodeid = str(record.get('nodeid') or '')
                        if nodeid:
                            durations[nodeid] = round(float(record.get('duration_seconds') or 0.0), 6)
            shard_duration = float(payload.get('duration_seconds') or 0.0)
            observed = [n for n, o in outcomes.items() if o not in {'UNEXECUTED', 'INFRA_ABORT'}]
            fallback = round(shard_duration / len(observed), 6) if observed else 0.0
            for nodeid, outcome in outcomes.items():
                if outcome in {'UNEXECUTED', 'INFRA_ABORT'}:
                    continue
                samples.append({
                    'nodeid': nodeid,
                    'outcome': outcome,
                    'duration_seconds': round(float(durations.get(nodeid, fallback)), 6),
                    'source_receipt': str(receipt_path.relative_to(self.root)).replace('\\', '/'),
                    'v2_3_isolation': {
                        'classification': 'UNCLASSIFIED',
                        'parallel_safe': False,
                        'explicit_review_required': True,
                        'shared_resource_hints': [],
                    },
                })
        samples.sort(key=lambda item: item['nodeid'])
        payload = {
            'schema_id': 'FullRegressionTelemetryHandoff',
            'status': 'PASS' if samples else 'BLOCK',
            'version': '1.0.0',
            'owner': 'DEVPL-GSDLC-07-E',
            'updated': '2026-08-30',
            'session_id': session_id,
            'generated_at': _now(),
            'samples_total': len(samples),
            'samples': samples,
            'v2_2': {
                'next': True,
                'node_duration_registry_ready_for_ingest': bool(samples),
                'scheduler_duration_balanced_enabled': False,
                'future_statistics': ['median', 'p95', 'sample_count', 'cold_start', 'shard_overhead'],
            },
            'v2_3': {
                'prepared_not_enabled': True,
                'parallel_execution_enabled': False,
                'workers': 0,
                'default_classification': 'UNCLASSIFIED',
            },
        }
        if not samples:
            return CommandResult(command, False, ExitCode.BLOCK, 'No terminal node telemetry was available.', {'summary': {'samples_total': 0}}, [Finding('FRX_TELEMETRY_EMPTY', session_id, Severity.BLOCK)])
        target = output_path or (self.root / 'outputs/testing/full_regression' / session_id / 'telemetry_handoff.json')
        if not target.is_absolute():
            target = self.root / target
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
        return CommandResult(command, True, ExitCode.PASS, 'Full-regression telemetry handoff exported for v2.2/v2.3.', {'summary': {'samples_total': len(samples), 'parallel_workers': 0, 'v2_2_next': True}, 'telemetry': payload, 'output_path': str(target)}, [])
