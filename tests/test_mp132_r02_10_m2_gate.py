"""R02-10 strict M2 gate; no mocks of FROZEN as an automatic quality PASS."""
import copy, hashlib, json
from pathlib import Path
import pytest
from devpilot_core.maturity.r02_m2_gate import assess_pilot_b, digest

PID='pilot_b_fixture'
SCOPE='''## MVP\n| SC-IN-01 | Alta de productos |\n'''
REQ='''## Requerimientos funcionales\n### RF-001 — Alta\nOrigen: SC-IN-01\nComportamiento: Registrar producto validado.\n'''
VISION='''## Visión\nGestionar productos y ventas.\n'''
DOCS={'product-vision':('docs/00_product/product_vision.md',VISION),
      'scope':('docs/00_product/mvp_scope.md',SCOPE),
      'requirements':('docs/01_requirements/requirements_specification.md',REQ)}

def fixture(tmp_path):
    ws=tmp_path/'ws'; root=tmp_path/'platform'
    pj=ws/'.devpilot/project.yaml';pj.parent.mkdir(parents=True)
    pj.write_text('project_id: '+PID+'\nproject_name: Pilot B fixture\nbusiness_need: registrar inventario, ventas y consultas.\n')
    data={'workspace_id':PID,'stages':{}}
    for stage,(rel,content) in DOCS.items():
        p=ws/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
        data['stages'][stage]={'status':'FROZEN','approved_sha256':digest(content.encode()),'content_sha256':digest(content.encode()),
            'review_id':'arev_1','approval_id':'APPROVAL-1','execution_id':'uedit_1','mode':'LOCAL_MODEL'}
    st=root/'outputs/pre_code_wizard/gsdlc_05_e'/PID/'state.json';st.parent.mkdir(parents=True)
    st.write_text(json.dumps(data))
    closure={'result':'PASS','project_id':PID,'requirements_state':'FROZEN',
             'source_content_sha256_lf':digest(REQ.encode())}
    model={'cor221_operation':{'model_calls_started':1,'per_target':[{'status':'PASS'}]}}
    ui={'owner_journey_observed':True,'restart_observed':True,'owner_notes_present':True}
    return ws,root,closure,model,ui,st

def audit(tmp_path):
    w,r,c,m,u,p=fixture(tmp_path)
    return assess_pilot_b(workspace=w,platform=r,project_id=PID,closure=c,model_evidence=m,ui_evidence=u)

def test_valid_evidence_honest_pass_with_findings(tmp_path):
    x=audit(tmp_path)
    assert x['decision']=='PASS_WITH_FINDINGS' and x['model_calls']==0
    assert x['operator_project_writes']==0 and x['checks']['scope_to_requirements']['missing_rf_origins']==[]
    assert x['checks']['local_model']['all_stages_real_competence_independently_proven'] is False

def test_unverified_browser_remains_partial(tmp_path):
    w,r,c,m,u,p=fixture(tmp_path)
    assert assess_pilot_b(workspace=w,platform=r,project_id=PID,closure=c,model_evidence=m)['decision']=='PARTIAL'

def test_missing_real_receipt_remains_partial(tmp_path):
    w,r,c,m,u,p=fixture(tmp_path)
    assert assess_pilot_b(workspace=w,platform=r,project_id=PID,closure=c,model_evidence={},ui_evidence=u)['decision']=='PARTIAL'

def test_frozen_source_modified_blocks(tmp_path):
    w,r,c,m,u,p=fixture(tmp_path)
    (w/DOCS['scope'][0]).write_text(SCOPE+'\nCambio sin aprobación\n')
    assert audit_result(w,r,c,m,u)['decision']=='BLOCK'

def audit_result(w,r,c,m,u):
    return assess_pilot_b(workspace=w,platform=r,project_id=PID,closure=c,model_evidence=m,ui_evidence=u)

def test_approval_missing_blocks(tmp_path):
    w,r,c,m,u,p=fixture(tmp_path);d=json.loads(p.read_text());d['stages']['requirements']['approval_id']='';p.write_text(json.dumps(d))
    assert audit_result(w,r,c,m,u)['decision']=='BLOCK'

def test_wrong_project_blocks(tmp_path):
    w,r,c,m,u,p=fixture(tmp_path)
    assert assess_pilot_b(workspace=w,platform=r,project_id='other',closure=c,model_evidence=m,ui_evidence=u)['decision']=='BLOCK'

def test_scope_token_only_without_rf_origin_blocks(tmp_path):
    w,r,c,m,u,p=fixture(tmp_path)
    bad='## Alcance\nSC-IN-01\n### RF-001 — Alta\nComportamiento: Registrar producto.\n'
    target=w/DOCS['requirements'][0];target.write_text(bad)
    d=json.loads(p.read_text());d['stages']['requirements']['approved_sha256']=digest(bad.encode());d['stages']['requirements']['content_sha256']=digest(bad.encode());p.write_text(json.dumps(d))
    c['source_content_sha256_lf']=digest(bad.encode())
    x=audit_result(w,r,c,m,u)
    assert x['decision']=='BLOCK' and any(f['rule_id']=='M2_SCOPE_RF_COVERAGE_MISSING' for f in x['findings'])

def test_crlf_normalized(tmp_path):
    w,r,c,m,u,p=fixture(tmp_path)
    target=w/DOCS['requirements'][0];target.write_bytes(REQ.replace('\n','\r\n').encode())
    assert audit_result(w,r,c,m,u)['decision']=='PASS_WITH_FINDINGS'

def test_unchanged_inputs_after_evaluation(tmp_path):
    w,r,c,m,u,p=fixture(tmp_path)
    snapshot=(p.read_bytes(),(w/DOCS['requirements'][0]).read_bytes())
    audit_result(w,r,c,m,u)
    assert snapshot==(p.read_bytes(),(w/DOCS['requirements'][0]).read_bytes())

def test_corrupted_state_fails_closed(tmp_path):
    w,r,c,m,u,p=fixture(tmp_path);p.write_text('{INVALID')
    assert audit_result(w,r,c,m,u)['decision']=='BLOCK'
