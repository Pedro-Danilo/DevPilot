from __future__ import annotations

import hashlib, json, shutil, subprocess
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator

from devpilot_core.application.release_lifecycle_service import ReleaseLifecycleApplicationService
from devpilot_core.release.package_builder import PackageBuildBuilder, PackageBuildOptions

ROOT=Path(__file__).resolve().parents[1]

class Ctx:
    configured=True; valid=True; active_workspace_root=ROOT; active_workspace_id='devpilot-local'
class Resolver:
    def resolve(self): return Ctx()

def _git(*args:str)->str:
    return subprocess.run(['git','-C',str(ROOT),*args],capture_output=True,text=True,check=True).stdout.strip()
def _sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def _clean():
    for rel in ['outputs/runtime/gsdlc11b_release_package','outputs/runtime/gsdlc11c_release_lifecycle','outputs/release/gsdlc11c']:
        shutil.rmtree(ROOT/rel,ignore_errors=True)

def _package():
    out=PackageBuildBuilder(ROOT,options=PackageBuildOptions(version='0.1.0',kind='repo-zip',execute=True)).build(); assert out.ok,out.to_dict()
    artifact=ROOT/'dist/release/devpilot-local-0.1.0-source.zip'; assert artifact.is_file()
    receipt={'status':'PASS','source_authority':{'commit':_git('rev-parse','HEAD'),'tree':_git('rev-parse','HEAD^{tree}'),'branch':_git('branch','--show-current') or 'DETACHED','dirty_tracked':False},'artifact':{'path':'dist/release/devpilot-local-0.1.0-source.zip','sha256':_sha(artifact),'file_count':len(__import__('zipfile').ZipFile(artifact).infolist())},'reproducibility':{'package_byte_reproducible':True}}
    p=ROOT/'outputs/runtime/gsdlc11b_release_package/job_result.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(receipt,indent=2)+'\n')

def _svc():return ReleaseLifecycleApplicationService(ROOT,context_resolver=Resolver())
def _args():return {'actor':'local-owner','actor_roles':['owner'],'workspace_scopes':['devpilot-local']}

def test_11c_clean_install_upgrade_fault_and_rollback_restore():
    _clean();_package();s=_svc()
    p=s.install_plan(**_args());assert p.ok,p.to_dict(); plan=p.data['plan']
    i=s.install_execute(**_args(),plan_id=plan['plan_id'],plan_hash=plan['plan_hash']);assert i.ok,i.to_dict(); assert i.data['install']['status']=='PASS'
    i2=s.install_execute(**_args(),plan_id=plan['plan_id'],plan_hash=plan['plan_hash']);assert i2.ok and i2.data['reused'] is True
    up=s.upgrade_plan(**_args());assert up.ok,up.to_dict();upl=up.data['plan'];assert upl['backup_required_before_mutation'] is True
    ux=s.upgrade_execute(**_args(),plan_id=upl['plan_id'],plan_hash=upl['plan_hash']);assert ux.ok,ux.to_dict();assert ux.data['upgrade']['status']=='ROLLBACK_REQUIRED';assert ux.data['upgrade']['backup']['verified_before_mutation'] is True
    ux2=s.upgrade_execute(**_args(),plan_id=upl['plan_id'],plan_hash=upl['plan_hash']);assert ux2.ok and ux2.data['reused'] is True
    rp=s.rollback_plan(**_args());assert rp.ok,rp.to_dict();rpl=rp.data['plan']
    rx=s.rollback_execute(**_args(),plan_id=rpl['plan_id'],plan_hash=rpl['plan_hash']);assert rx.ok,rx.to_dict();assert rx.data['rollback']['hash_parity'] is True;assert rx.data['rollback']['fault_marker_absent'] is True
    rx2=s.rollback_execute(**_args(),plan_id=rpl['plan_id'],plan_hash=rpl['plan_hash']);assert rx2.ok and rx2.data['reused'] is True
    for report,schema in [('outputs/release/gsdlc11c/install_smoke_report.json','docs/schemas/gsdlc11c_install_smoke_report.schema.json'),('outputs/release/gsdlc11c/upgrade_rollback_report.json','docs/schemas/gsdlc11c_upgrade_rollback_report.schema.json')]:
        Draft202012Validator(json.loads((ROOT/schema).read_text())).validate(json.loads((ROOT/report).read_text()))
    assert _git('status','--porcelain','--untracked-files=no')==''

def test_11c_install_blocks_checksum_mismatch():
    _clean();_package();s=_svc(); receipt=ROOT/'outputs/runtime/gsdlc11b_release_package/job_result.json';d=json.loads(receipt.read_text());d['artifact']['sha256']='0'*64;receipt.write_text(json.dumps(d))
    r=s.install_plan(**_args());assert not r.ok;assert any(f.id=='GSDLC11C_PACKAGE_ARTIFACT_BLOCK' for f in r.findings)

def test_11c_mutation_requires_release_role():
    _clean();s=_svc();r=s.install_plan(actor='qa',actor_roles=['qa-reviewer'],workspace_scopes=['devpilot-local']);assert not r.ok;assert any(f.id=='GSDLC11C_RELEASE_ROLE_BLOCK' for f in r.findings)
