from pathlib import Path
import json
from devpilot_core.testing.duration_registry import NodeDurationRegistry

ENV='windows-pytest-devpilot-gsdlc07e-v1'

def payload(samples): return {'generated_at':'2026-08-31T00:00:00Z','environment_fingerprint':ENV,'samples':samples}

def test_ingest_idempotent_and_estimate(tmp_path):
 r=NodeDurationRegistry(tmp_path); p=payload([{'nodeid':'tests/a.py::test_x','duration_seconds':1.0},{'nodeid':'tests/b.py::test_y','duration_seconds':3.0}])
 a=r.ingest_payload(p,source_receipt='r1'); b=r.ingest_payload(p,source_receipt='r1')
 assert (a.accepted,a.rejected,a.duplicate_receipt)==(2,0,False); assert b.duplicate_receipt
 assert r.status()['samples_total']==2; assert r.estimate('tests/a.py::test_x',ENV)['estimate_seconds']==1.0

def test_environment_separation_and_unknown(tmp_path):
 r=NodeDurationRegistry(tmp_path); r.ingest_payload(payload([{'nodeid':'tests/a.py::test_x','duration_seconds':1}]),source_receipt='a')
 assert not r.estimate('tests/a.py::test_x','other-env')['known']

def test_nodeid_suffix_preserved_byte_for_byte(tmp_path):
 r=NodeDurationRegistry(tmp_path); n='tests/p.py::test_param[value\\t\\x7f]'; r.ingest_payload(payload([{'nodeid':n,'duration_seconds':.1}]),source_receipt='a')
 assert n in r.load()['environments'][ENV]['nodes']

def test_corrupt_negative_rejected_explicitly(tmp_path):
 r=NodeDurationRegistry(tmp_path); x=r.ingest_payload(payload([{'nodeid':'tests/a.py::bad','duration_seconds':-1},{'nodeid':'tests/b.py::bad','duration_seconds':'x'}]),source_receipt='bad')
 assert (x.accepted,x.rejected)==(0,2); assert r.status()['rejections_total']==2

def test_cold_warm_and_deterministic_estimate(tmp_path):
 r=NodeDurationRegistry(tmp_path); n='tests/a.py::test_x'
 for i,d in enumerate((1,2,10),1): r.ingest_payload(payload([{'nodeid':n,'duration_seconds':d}]),source_receipt=f'r{i}')
 e=r.estimate(n,ENV); assert e['classification']=='warm'; assert e['median']==2.0; assert e['p95']==10.0; assert e['estimate_seconds']==4.3775

def test_preview_never_enables_scheduler_or_parallelism(tmp_path):
 r=NodeDurationRegistry(tmp_path); r.ingest_payload(payload([{'nodeid':'tests/a.py::x','duration_seconds':2}]),source_receipt='a')
 p=r.preview(ENV); assert p['scheduler_enabled'] is False and p['parallel_workers']==1

def test_aging_policy_preserves_evidence(tmp_path):
 r=NodeDurationRegistry(tmp_path); d=r.load(); assert d['aging_policy']['method']=='sequential_ewma' and d['aging_policy']['alpha']==0.35 and d['aging_policy']['older_observations_lose_geometric_weight'] is True and d['aging_policy']['evidence_deleted'] is False

def test_versioned_bootstrap_registry_reconciles_all_2805_samples():
 root=Path(__file__).resolve().parents[1]
 telemetry=json.loads((root/'.devpilot/testing/frx_v2_2_b_initial_telemetry.json').read_text(encoding='utf-8'))
 registry=NodeDurationRegistry(root).status()
 assert telemetry['samples_total']==2805
 assert len({item['nodeid'] for item in telemetry['samples']})==2805
 assert registry['samples_total']>=2805
 assert registry['nodeids_total']>=2805
 assert registry['rejections_total']==0
 assert registry['environments_total']>=1
 assert registry['scheduler_enabled'] is False
 assert registry['parallel_workers']==1


def test_versioned_registry_validates_against_registered_json_schema():
 from devpilot_core.schemas import SchemaValidator
 root=Path(__file__).resolve().parents[1]
 result=SchemaValidator(root).validate(schema='NodeDurationRegistry', instance='.devpilot/testing/node_duration_registry.json')
 assert result.ok, result.to_dict()
 assert result.data['summary']['valid'] is True

def test_doc_impact_preserves_dot_devpilot_prefix_and_requires_closure_gate():
 from devpilot_core.docs_governance import DocImpactPlanner
 root=Path(__file__).resolve().parents[1]
 result=DocImpactPlanner(root,['.devpilot/project_state.json']).run()
 assert result.ok
 plan=result.data['plan']
 assert plan['changed_paths']==['.devpilot/project_state.json']
 assert plan['closure_consistency_required'] is True
 assert plan['full_regression_required'] is False
 assert plan['browser_required'] is False

def test_authoritative_2805_handoff_ingests_from_scratch(tmp_path):
 root=Path(__file__).resolve().parents[1]
 source=root/'.devpilot/testing/frx_v2_2_b_initial_telemetry.json'
 r=NodeDurationRegistry(tmp_path)
 result=r.ingest_file(source, environment_fingerprint=ENV)
 assert (result.accepted,result.rejected,result.duplicate_receipt)==(2805,0,False)
 assert r.status()['samples_total']==2805
 assert r.status()['nodeids_total']==2805


def test_sequential_ewma_ages_old_observations_without_deleting_evidence(tmp_path):
 node='tests/a.py::test_aging'
 r=NodeDurationRegistry(tmp_path)
 estimates=[]
 for i,d in enumerate((100.0,10.0,10.0,10.0),1):
  r.ingest_payload(payload([{'nodeid':node,'duration_seconds':d}]),source_receipt=f'r{i}')
  estimates.append(r.estimate(node,ENV)['estimate_seconds'])
 # With alpha=0.35, the influence of the first 100s sample decays by (1-alpha)
 # each time a compatible successor sample is ingested; sealed evidence remains present.
 assert estimates[2] == 48.025
 assert estimates[3] == 34.71625
 assert estimates[3] < estimates[2] < estimates[1]
 rec=r.load()['environments'][ENV]['nodes'][node]
 assert [x['duration_seconds'] for x in rec['samples']] == [100.0,10.0,10.0,10.0]
