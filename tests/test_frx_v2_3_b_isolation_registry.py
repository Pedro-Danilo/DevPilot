from __future__ import annotations
import json
from pathlib import Path
import pytest
from devpilot_core.schemas import SchemaValidator
from devpilot_core.testing.isolation_registry import IsolationState, IsolationStaticAnalyzer, ResourceClass, TestIsolationRegistry
ROOT=Path(__file__).resolve().parents[1]

RESOURCE_FIXTURES={
 ResourceClass.FIXED_FILESYSTEM.value:'Path("outputs/shared.json").write_text("x")',
 ResourceClass.SQLITE_DB.value:'import sqlite3\nsqlite3.connect("state.db")',
 ResourceClass.GIT_WORKTREE.value:'subprocess.run(["git","status"], cwd=worktree)',
 ResourceClass.PORT_SERVER.value:'host="127.0.0.1"\nport=8787',
 ResourceClass.ENV_CWD.value:'os.environ["X"]="1"\nos.chdir(tmp_path)',
 ResourceClass.GLOBAL_STATE.value:'global shared_state\nshared_state={}',
 ResourceClass.SUBPROCESS.value:'subprocess.Popen(["python","x.py"])',
 ResourceClass.NETWORK.value:'requests.get("https://example.invalid")',
 ResourceClass.CLOCK_TIME.value:'time.sleep(1)\ndatetime.now()',
 ResourceClass.SHARED_CACHE.value:'cache_dir=".pytest_cache"',
 ResourceClass.WINDOWS_NAMED.value:'CreateMutex named mutex',
}

@pytest.mark.parametrize('resource_class,text', RESOURCE_FIXTURES.items())
def test_static_analyzer_suggests_every_resource_class_without_authorizing(resource_class,text):
    hints=IsolationStaticAnalyzer().analyze_text(text)
    assert resource_class in {h['resource_class'] for h in hints}
    assert all(h['confidence']=='suggested' for h in hints)


def test_default_entry_is_unclassified_and_never_parallel_safe():
    entry=TestIsolationRegistry.default_entry('tests/test_x.py::test_x', suggested_hints=[{'resource_class':ResourceClass.NETWORK.value,'confidence':'suggested','evidence':['network']}])
    assert entry['state']=='UNCLASSIFIED'
    assert entry['parallel_safe'] is False
    assert entry['explicit_review_required'] is True
    assert entry['review'] is None


def test_static_suggestion_cannot_authorize_parallel_safe():
    entry=TestIsolationRegistry.default_entry('tests/test_x.py::test_x', suggested_hints=IsolationStaticAnalyzer().analyze_text('requests.get("x")'))
    result=TestIsolationRegistry.validate_semantics({'entries':[entry]})
    assert result['ok'] and result['proven_parallel_safe_total']==0


def test_explicit_positive_review_requires_evidence_and_authorizes_only_reviewed_entry():
    entry=TestIsolationRegistry.default_entry('tests/test_x.py::test_x')
    with pytest.raises(ValueError):
        TestIsolationRegistry.review_entry(entry,decision='PROVEN_PARALLEL_SAFE',reviewer='owner',reason='pure fixture',reviewed_at='2026-09-02T00:00:00Z',evidence_ids=[])
    reviewed=TestIsolationRegistry.review_entry(entry,decision='PROVEN_PARALLEL_SAFE',reviewer='owner',reason='pure fixture',reviewed_at='2026-09-02T00:00:00Z',evidence_ids=['FRX-V2.3-B-FOCAL'])
    assert reviewed['parallel_safe'] is True and reviewed['state']=='PROVEN_PARALLEL_SAFE'
    assert TestIsolationRegistry.validate_semantics({'entries':[reviewed]})['ok']


def test_explicit_negative_review_keeps_serial():
    entry=TestIsolationRegistry.default_entry('tests/test_x.py::test_x')
    reviewed=TestIsolationRegistry.review_entry(entry,decision='SERIAL_REQUIRED',reviewer='owner',reason='shared DB',reviewed_at='2026-09-02T00:00:00Z',evidence_ids=[],resource_classes=[ResourceClass.SQLITE_DB.value],isolation_domains=['db:shared'],resource_lock_keys=['db:shared'])
    assert reviewed['parallel_safe'] is False and reviewed['state']=='SERIAL_REQUIRED'
    assert TestIsolationRegistry.validate_semantics({'entries':[reviewed]})['ok']


def test_runtime_coverage_does_not_treat_unknown_as_safe():
    a=TestIsolationRegistry.default_entry('a',runtime_estimate={'known':True,'seconds':9.0,'confidence':'high','source_environment':'x','last_seen':'x'})
    b=TestIsolationRegistry.review_entry(TestIsolationRegistry.default_entry('b',runtime_estimate={'known':True,'seconds':1.0,'confidence':'high','source_environment':'x','last_seen':'x'}),decision='SERIAL_REQUIRED',reviewer='owner',reason='shared',reviewed_at='x',evidence_ids=[])
    report=TestIsolationRegistry.coverage_report({'entries':[a,b]})
    assert report['runtime_weighted_parallel_safe_percent']==0.0
    assert report['runtime_weighted_unclassified_percent']==90.0
    assert report['runtime_weighted_serial_required_percent']==10.0


def test_repo_registry_schema_and_semantics_pass_and_all_current_nodeids_start_unclassified():
    payload=json.loads((ROOT/'.devpilot/testing/test_isolation_registry.json').read_text(encoding='utf-8'))
    schema=SchemaValidator(ROOT).validate(schema='docs/schemas/test_isolation_registry.schema.json',instance='.devpilot/testing/test_isolation_registry.json')
    assert schema.ok, schema.to_dict()
    semantic=TestIsolationRegistry.validate_semantics(payload)
    assert semantic['ok'], semantic
    assert semantic['entries_total']>2800
    assert semantic['proven_parallel_safe_total']==0
    assert semantic['serial_required_total']==0
    assert semantic['unclassified_total']==semantic['entries_total']
    assert payload['policy']['workers']==0 and payload['policy']['full_runs']==0


def test_repo_coverage_report_is_runtime_weighted_and_no_inference_is_safe():
    report=json.loads((ROOT/'docs/audits/FRX_V2_3_B_ISOLATION_COVERAGE.json').read_text(encoding='utf-8'))
    assert report['status']=='PASS'
    assert report['proven_parallel_safe_total']==0
    assert report['runtime_weighted_parallel_safe_percent']==0.0
    assert report['static_suggestions_authorize_parallel'] is False
    assert report['workers']==0 and report['full_runs']==0
