from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path
from devpilot_core.application.release_closure_service import ReleaseClosureApplicationService

class Ctx:
    configured=True; valid=True; active_workspace_id='devpilot-local'
    def __init__(self, root:Path): self.active_workspace_root=root
class Resolver:
    def __init__(self, root:Path): self.ctx=Ctx(root)
    def resolve(self): return self.ctx

def w(path:Path,payload): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload,indent=2)+'\n')
def git(root:Path,*args:str)->str:return subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True,check=True).stdout.strip()
def setup(tmp:Path):
    (tmp/'.gitignore').write_text('outputs/\ndist/\n')
    subprocess.run(['git','init','-q',str(tmp)],check=True); git(tmp,'config','user.email','test@example.invalid');git(tmp,'config','user.name','Test')
    (tmp/'source.txt').write_text('release\n');git(tmp,'add','source.txt','.gitignore');git(tmp,'commit','-m','release source'); commit=git(tmp,'rev-parse','HEAD'); tree=git(tmp,'rev-parse','HEAD^{tree}'); git(tmp,'tag','-a','v0.1.1','-m','release','HEAD')
    fixture=tmp/'fixture';fixture.mkdir();
    w(tmp/'.devpilot/workspaces/workspace_registry.json',{'schema_version':'1.0','defaults':{'deny_unregistered_workspaces':True},'workspaces':[{'workspace_id':'devpilot-local','project_id':'devpilot-local','path':'fixture','status':'active'}]})
    w(tmp/'.devpilot/project_state.json',{**{f'gsdlc_11_{x}_status':'CLOSED/PASS/WINDOWS-VALIDATED' for x in 'abcd'},'gsdlc_11_e_authorized':True})
    artifact=tmp/'dist/release/devpilot-local-0.1.1-source.zip';artifact.parent.mkdir(parents=True);artifact.write_bytes(b'zip'); sha=hashlib.sha256(artifact.read_bytes()).hexdigest()
    authority={'commit':commit,'tree':tree,'branch':git(tmp,'branch','--show-current'),'dirty_tracked':False}
    w(tmp/'outputs/runtime/gsdlc11b_release_package/job_result.json',{'status':'PASS','source_authority':authority,'artifact':{'path':'dist/release/devpilot-local-0.1.1-source.zip','sha256':sha},'reproducibility':{'package_byte_reproducible':True},'sbom':{'schema_validation':'PASS','path':'outputs/reports/sbom.json'},'checksums':{'path':'outputs/release/gsdlc11b/checksums.sha256'}})
    w(tmp/'outputs/release/gsdlc11c/install_smoke_report.json',{'status':'PASS'})
    w(tmp/'outputs/release/gsdlc11c/upgrade_rollback_report.json',{'status':'PASS','restore_verified':True,'backup_required_before_mutation':True,'production_data_touched':False})
    w(tmp/'outputs/release/gsdlc11d/version_decision.json',{'status':'PASS','version':'0.1.1','source_authority':authority})
    w(tmp/'outputs/release/gsdlc11d/release_approval.json',{'status':'APPROVED','target_commit':commit,'model_or_agent_authority':False})
    w(tmp/'outputs/release/gsdlc11d/tag_verification.json',{'status':'PASS','tag_name':'v0.1.1','tag_target_commit':commit,'exact_commit_match':True,'annotated':True,'push_performed':False,'publish_performed':False,'deploy_performed':False})
    return fixture,commit

def test_release_closure_ready_and_finalize_released(tmp_path:Path):
    fixture,commit=setup(tmp_path); svc=ReleaseClosureApplicationService(tmp_path,context_resolver=Resolver(fixture)); args={'actor':'owner','actor_roles':['owner'],'workspace_scopes':['devpilot-local']}
    st=svc.status(**args); assert st.ok,st.to_dict(); graph=st.data['release_closure']; assert graph['state']=='READY_TO_FINALIZE'; assert graph['normal_user_external_script']==0
    fin=svc.finalize(**args,graph_hash=graph['graph_hash']); assert fin.ok,fin.to_dict(); assert fin.data['final_release_status']['status']=='RELEASED'; assert fin.data['final_release_status']['source_commit']==commit
    state=json.loads((tmp_path/'outputs/workspaces/devpilot-local/engineering_state.json').read_text()); assert state['lifecycle_status']=='RELEASED'; assert state['phase']=='RELEASE'

def test_release_closure_blocks_stale_package(tmp_path:Path):
    fixture,_=setup(tmp_path); p=tmp_path/'outputs/runtime/gsdlc11b_release_package/job_result.json'; d=json.loads(p.read_text());d['source_authority']['commit']='0'*40;w(p,d)
    svc=ReleaseClosureApplicationService(tmp_path,context_resolver=Resolver(fixture)); st=svc.status(actor='owner',actor_roles=['owner'],workspace_scopes=['devpilot-local']); assert st.ok; assert st.data['release_closure']['state']=='BLOCKED'; assert any(x['id']=='package' for x in st.data['release_closure']['blockers'])

def test_release_closure_finalize_requires_release_role(tmp_path:Path):
    fixture,_=setup(tmp_path);svc=ReleaseClosureApplicationService(tmp_path,context_resolver=Resolver(fixture)); graph=svc.status(actor='qa',actor_roles=['qa-reviewer'],workspace_scopes=['devpilot-local']).data['release_closure']; r=svc.finalize(actor='qa',actor_roles=['qa-reviewer'],workspace_scopes=['devpilot-local'],graph_hash=graph['graph_hash']); assert not r.ok
