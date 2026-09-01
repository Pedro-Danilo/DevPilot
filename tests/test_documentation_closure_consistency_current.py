from pathlib import Path
from devpilot_core.docs_governance import ClosureStateConsistencyValidator, DocumentationDriftLedger

ROOT=Path(__file__).resolve().parents[1]

def test_current_closure_state_consistency_has_no_blocking_drift():
    result=ClosureStateConsistencyValidator(ROOT).run()
    assert result.ok, result.to_dict()
    assert result.data['summary']['closure_state_consistency_passed'] is True
    assert result.data['summary']['drift_p0_p1_open_total']==0

def test_current_documentation_drift_ledger_has_no_open_p0_p1():
    assert DocumentationDriftLedger(ROOT).open_blocking_findings()==()
