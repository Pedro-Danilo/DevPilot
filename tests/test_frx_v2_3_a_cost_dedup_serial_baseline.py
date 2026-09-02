from __future__ import annotations
import json, subprocess
from pathlib import Path
from devpilot_core.cli_models import CommandResult, ExitCode
from devpilot_core.quality import QualityExecutionContext, QualityGate, QualityGateOptions
from devpilot_core.testing.aggregate_cost_audit import AggregateExecutionCostAudit
from devpilot_core.testing.temporal_shard_planner import TemporalShardPlanner
from devpilot_core.testing.normalized_serial_baseline import NormalizedSerialBaselineBuilder
ROOT=Path(__file__).resolve().parents[1]

def _pass(command='ok'):
    return CommandResult(command,True,ExitCode.PASS,'ok',data={'summary':{}},findings=[])

def test_quality_gate_plan_is_read_only_and_exposes_aggregates(monkeypatch):
    gate=QualityGate(ROOT,options=QualityGateOptions(profile='hardening'))
    monkeypatch.setattr(gate,'_run_subgate',lambda *a,**k: (_ for _ in ()).throw(AssertionError('must not execute')))
    plan=gate.describe_plan().to_dict()
    assert 'ui-api-local-hardening' in plan['ordered_subgate_ids']
    item=next(x for x in plan['subgates'] if x['id']=='ui-api-local-hardening')
    assert set(item['aggregate_of']) >= {'api-contract-drift-guard','ui-route-enforcement'}

def test_execution_context_reuses_canonical_component_once():
    ctx=QualityExecutionContext(source_identity='test')
    calls=[]
    r1,re1=ctx.execute('docs-governance',lambda:(calls.append(1) or _pass()))
    r2,re2=ctx.execute('docs-governance',lambda:(calls.append(2) or _pass()))
    assert r1 is r2 and not re1 and re2 and calls==[1]
    assert ctx.audit()['duplicate_component_executions_total']==0

def test_binding_aggregate_cost_audit_has_no_violations():
    result=AggregateExecutionCostAudit(ROOT).run()
    assert result.ok, result.to_dict()
    assert result.data['summary']['binding_aggregate_violations_total']==0

def test_manifest_temporal_plan_coarsens_v22_collection_at_least_60_percent():
    collection=ROOT/'.devpilot/testing/frx_v2_3_a_v2_2_collection_snapshot.json'
    session=json.loads((ROOT/'.devpilot/testing/frx_v2_3_a_v2_2_session_snapshot.json').read_text())
    report=NormalizedSerialBaselineBuilder(ROOT).build(collection_path=collection,environment_fingerprint=session['environment_fingerprint'])
    assert report['collection_total']==2844
    assert report['process_reduction_percent']>=60
    assert report['workers']==0 and report['full_runs']==0

def test_git_clean_source_descriptor_uses_no_hash_object_per_file(monkeypatch,tmp_path):
    subprocess.run(['git','init'],cwd=tmp_path,check=True,capture_output=True)
    subprocess.run(['git','config','user.email','a@b.invalid'],cwd=tmp_path,check=True)
    subprocess.run(['git','config','user.name','t'],cwd=tmp_path,check=True)
    (tmp_path/'x.txt').write_text('x\n')
    subprocess.run(['git','add','.'],cwd=tmp_path,check=True); subprocess.run(['git','commit','-m','x'],cwd=tmp_path,check=True,capture_output=True)
    import devpilot_core.testing.full_regression as fr
    calls=[]; real=fr._git_run
    def wrapped(root,args,**kw): calls.append(tuple(args)); return real(root,args,**kw)
    monkeypatch.setattr(fr,'_git_run',wrapped)
    guard=fr._git_semantic_clean_guard(tmp_path); desc=fr._git_semantic_source_descriptor(tmp_path)
    assert guard and guard['clean'] and desc and desc['per_file_git_subprocesses']==0
    assert not any(args and args[0]=='hash-object' for args in calls)

def test_manifest_transport_executes_exact_selected_nodeids(tmp_path):
    import os, sys
    manifest = tmp_path / 'nodeids.json'
    targets = [
        'tests/test_frx_v2_3_a_cost_dedup_serial_baseline.py::test_execution_context_reuses_canonical_component_once',
        'tests/test_frx_v2_3_a_cost_dedup_serial_baseline.py::test_binding_aggregate_cost_audit_has_no_violations',
    ]
    manifest.write_text(json.dumps({'nodeids': targets}, indent=2), encoding='utf-8')
    env = os.environ.copy(); env['PYTHONPATH'] = 'src'; env['DEVPILOT_FULL_SESSION_NODEID_MANIFEST'] = str(manifest)
    completed = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'devpilot_core.testing.full_regression_manifest_plugin'], cwd=ROOT, env=env, capture_output=True, text=True, timeout=120, shell=False)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert '2 passed' in completed.stdout


def test_dirty_git_guard_blocks_without_strong_rehash(tmp_path, monkeypatch):
    subprocess.run(['git','init'], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(['git','config','user.email','a@b.invalid'], cwd=tmp_path, check=True)
    subprocess.run(['git','config','user.name','t'], cwd=tmp_path, check=True)
    (tmp_path/'tests').mkdir(); (tmp_path/'tests/test_x.py').write_text('def test_x(): assert True\n')
    subprocess.run(['git','add','.'], cwd=tmp_path, check=True); subprocess.run(['git','commit','-m','x'], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path/'dirty.txt').write_text('dirty\n')
    import devpilot_core.testing.full_regression as fr
    monkeypatch.setattr(fr, '_source_descriptor', lambda root: (_ for _ in ()).throw(AssertionError('strong descriptor must not run for dirty Git collect')))
    result = fr.FullRegressionSessionManager(tmp_path).collect(session_id='dirty-fast-block')
    assert not result.ok
    assert any(f.id == 'FRX2_SOURCE_DIRTY' for f in result.findings)


def test_manifest_mode_removes_command_line_char_coupling(tmp_path):
    registry = tmp_path/'.devpilot/testing/node_duration_registry.json'
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(json.dumps({'schema_id':'devpilot.testing.node_duration_registry.v1','version':'1.0.0','updated':'x','scheduler_enabled':False,'parallel_workers':1,'aging_policy':{},'ingested_receipts':{},'environments':{'env':{'nodes':{},'samples_total':0}},'rejections':[]}), encoding='utf-8')
    nodeids=[f'tests/test_long_{i:04d}.py::test_{"x"*100}_{i}' for i in range(300)]
    planner=TemporalShardPlanner(tmp_path, registry_path=registry, target_shard_seconds=900, max_nodeids=200, max_command_chars=512, nodeid_transport='manifest')
    plan=planner.plan(nodeids, environment_fingerprint='env')
    assert plan['shards_total']==2
    assert plan['command_line_coupling'] is False
    assert max(shard['command_chars'] for shard in plan['shards']) > 512
