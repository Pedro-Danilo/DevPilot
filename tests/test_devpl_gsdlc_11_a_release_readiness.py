from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from devpilot_core.application.release_readiness_service import ReleaseReadinessApplicationService
from devpilot_core.cli_models import CommandResult, ExitCode


def ok(data):
    return CommandResult('mock', True, ExitCode.PASS, 'ok', data=data, findings=[])


class Resolver:
    def __init__(self, root: Path, *, valid=True):
        self.root=root; self.valid=valid
    def resolve(self):
        return SimpleNamespace(configured=True, valid=self.valid, active_workspace_root=self.root, active_workspace_id='ws-11a')


def service(tmp_path: Path, *, story_status='DONE', quality='PASS', stale=False, jobs='PASS', dirty=False, pending=False, no_go=False, trace=True):
    platform=tmp_path/'platform'; workspace=tmp_path/'workspace'; platform.mkdir(); workspace.mkdir()
    criteria=platform/'.devpilot/release/local_release_candidate_criteria.json'; criteria.parent.mkdir(parents=True)
    (platform/'.devpilot/release/reproducibility_policy.json').write_text('{}',encoding='utf-8')
    (platform/'.devpilot/release/source_zip_release_policy.json').write_text('{}',encoding='utf-8')
    (platform/'.devpilot/project_state.json').write_text(json.dumps({'post_h_026_status':'closed/local-release-candidate-pass','post_h_027_status':'closed/packaging-local-ready'}),encoding='utf-8')
    for rel in ['docs/backlogs/POST-H-017_release_reproducibility_pack.md','docs/backlogs/POST-H-026_local_release_candidate_operator_verification.md','docs/backlogs/POST-H-027_packaging_reproducible_local_installation.md','src/devpilot_core/release/reproducibility_pack.py','src/devpilot_core/release_candidate/report.py','src/devpilot_core/release/artifact_manifest.py']:
        target=platform/rel; target.parent.mkdir(parents=True,exist_ok=True); target.write_text('fixture',encoding='utf-8')
    criteria.write_text(json.dumps({'no_go_gates':{'enterprise_ready_claim':no_go,'remote_ready_claim':False,'saas_ready_claim':False,'compliance_certification_claim':False,'remote_execution_enabled':False,'connector_write_enabled':False,'plugin_execution_enabled':False,'external_apis_required':False}}),encoding='utf-8')
    report={'report_id':'quality-1','report_hash':'qh','story_execution_id':'exec-1','decision':quality,'commit_ready':quality=='PASS','stale':stale,'required_job_results':[{'job_id':'j1','story_validation_status':jobs}],'findings':[]}
    def list_quality(): return [report]
    def load_quality(*,report_id): return ok({'story_quality_report':report})
    def approvals(**kwargs):
        rows=[] if not pending else [{'approval_id':'APP-1','status':'requested','scope':{'workspace_id':'ws-11a'},'metadata':{}}]
        return ok({'approvals':rows})
    git_status={'summary':{'head':'abc123'},'status':{'short_status':[' M src/a.py'] if dirty else []}}
    def commits(_): return [{'workspace_id':'ws-11a','story_execution_id':'exec-1','commit_hash':'abc123','commit_record_id':'commit-1','traceability_complete':trace}]
    def story(_root,_workspace_id): return {'execution_id':'exec-1','story_id':'S1','status':story_status}
    return ReleaseReadinessApplicationService(platform,context_resolver=Resolver(workspace),quality_reports_lister=list_quality,quality_report_loader=load_quality,approvals_lister=approvals,git_status_loader=lambda:ok(git_status),commit_records_loader=commits,story_projection_loader=story)


def test_ready_projection_is_deterministic_and_not_release_approval(tmp_path: Path):
    svc=service(tmp_path)
    first=svc.evaluate(actor='owner',actor_roles=['owner'],workspace_scopes=['ws-11a']).data['release_readiness']
    second=svc.evaluate(actor='owner',actor_roles=['owner'],workspace_scopes=['ws-11a']).data['release_readiness']
    assert first['state']=='RELEASE_READY' and first['release_ready'] is True
    assert first['blockers']==second['blockers']==[]
    assert first['release_authority']['allowed'] is True
    assert first['release_authority']['readiness_is_release_approval'] is False
    assert first['release_authority']['approval_required_later'] is True
    assert first['safety']['full_regression_started'] is False


def test_unknown_missing_quality_fails_closed(tmp_path: Path):
    svc=service(tmp_path)
    svc.quality_reports_lister=lambda:[]
    result=svc.evaluate(actor='dev',actor_roles=['developer'],workspace_scopes=['ws-11a']).data['release_readiness']
    assert result['state']=='UNKNOWN' and result['release_ready'] is False
    assert any(b['blocker_id']=='quality-evidence-missing' and b['state']=='UNKNOWN' for b in result['blockers'])


def test_stale_dirty_pending_and_traceability_block_with_owner_and_next_action(tmp_path: Path):
    svc=service(tmp_path,stale=True,dirty=True,pending=True,trace=False)
    result=svc.evaluate(actor='dev',actor_roles=['developer'],workspace_scopes=['ws-11a']).data['release_readiness']
    assert result['state']=='BLOCKED'
    ids={b['blocker_id'] for b in result['blockers']}
    assert {'quality-stale','git-worktree-dirty','traceability-incomplete','pending-approvals'} <= ids
    assert all(b['owner'] and b['next_action'] and b['policy_source'] for b in result['blockers'])
    assert result['release_authority']['allowed'] is False


def test_unsupported_claim_blocks_and_never_overclaims(tmp_path: Path):
    result=service(tmp_path,no_go=True).evaluate(actor='owner',actor_roles=['owner'],workspace_scopes=['ws-11a']).data['release_readiness']
    assert result['state']=='BLOCKED'
    assert 'enterprise_ready_claim' in result['claims']['forbidden_claims_enabled']
    assert result['claims']['enterprise_ready_claim'] is False
    assert result['claims']['compliance_certification_claim'] is False
    assert result['claims']['public_release_claim'] is False


def test_project_scope_mismatch_blocks_before_projection(tmp_path: Path):
    result=service(tmp_path).evaluate(actor='owner',actor_roles=['owner'],workspace_scopes=['other'])
    assert not result.ok and any(f.id=='GSDLC11A_WORKSPACE_SCOPE_BLOCK' for f in result.findings)
