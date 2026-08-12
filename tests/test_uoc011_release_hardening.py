from pathlib import Path
from devpilot_core.release.uoc011_hardening import evaluate_uoc011_hardening
ROOT=Path(__file__).resolve().parents[1]

def test_uoc011_hardening_evaluator_passes() -> None:
    report=evaluate_uoc011_hardening(ROOT)
    assert report['status']=='PASS', report
    assert report['summary']['browser_matrix_cases_total']==108
    assert report['summary']['checks_total']==report['summary']['checks_passed']
    assert report['safety']['external_api_used'] is False
