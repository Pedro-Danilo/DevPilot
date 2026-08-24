from __future__ import annotations

import ast
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from devpilot_core.application.approval_service import ApprovalApplicationService
from devpilot_core.application.artifact_draft_service import ArtifactDraftApplicationService
from devpilot_core.application.artifact_import_service import ArtifactImportApplicationService
from devpilot_core.application.artifact_review_service import ArtifactReviewApplicationService
from devpilot_core.application.auth_service import AuthApplicationService
from devpilot_core.application.workspace_documents_service import WorkspaceDocumentsApplicationService
from devpilot_core.application.workspace_edit_execution_service import WorkspaceEditExecutionApplicationService
from devpilot_core.application.workspace_edit_plan_service import WorkspaceEditPlanApplicationService, ZERO_SHA256
from devpilot_core.interfaces.api.security import resolve_route_policy
from devpilot_core.interfaces.api.response_mapping import command_result_to_api_response

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = 'TestOwnerPassword!2026'


def _copy_platform(tmp_path: Path) -> Path:
    platform = tmp_path / 'platform'
    shutil.copytree(ROOT / '.devpilot', platform / '.devpilot', ignore=shutil.ignore_patterns('*.db', '*.db-*', 'outputs', '__pycache__'))
    for rel in ['docs/schemas', 'docs/validation']:
        shutil.copytree(ROOT / rel, platform / rel)
    return platform


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    platform = _copy_platform(tmp_path)
    ws = tmp_path / 'workspace'
    (ws / 'docs').mkdir(parents=True)
    (ws / '.devpilot').mkdir()
    (ws / '.devpilot/project.yaml').write_text('project_id: gsdlc04e-fixture\n', encoding='utf-8')
    (ws / 'docs/baseline.md').write_text('# Baseline\n\nTracked baseline.\n', encoding='utf-8')
    subprocess.run(['git', 'init', '-q'], cwd=ws, check=True)
    subprocess.run(['git', 'config', 'user.email', 'fixture@example.invalid'], cwd=ws, check=True)
    subprocess.run(['git', 'config', 'user.name', 'Fixture'], cwd=ws, check=True)
    subprocess.run(['git', 'add', '.'], cwd=ws, check=True)
    subprocess.run(['git', 'commit', '-qm', 'baseline'], cwd=ws, check=True)
    subprocess.run(['git', 'branch', 'stable'], cwd=ws, check=True)
    control = tmp_path / 'control'
    monkeypatch.setenv('DEVPILOT_ALLOWED_WORKSPACE_ROOTS', str(ws))
    monkeypatch.setenv('DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT', str(ws))
    monkeypatch.setenv('DEVPILOT_UOC005_CONTROL_ROOT', str(control))
    monkeypatch.delenv('DEVPILOT_UI_WORKSPACE_REGISTRY_PATH', raising=False)
    auth = AuthApplicationService(platform)
    issue = auth.bootstrap_owner(username='owner.local', display_name='Local Owner', password=PASSWORD)
    docs = WorkspaceDocumentsApplicationService(platform)
    plans = WorkspaceEditPlanApplicationService(platform, documents=docs)
    execs = WorkspaceEditExecutionApplicationService(platform, documents=docs, plans=plans, approval_auth_store=auth.store)
    drafts = ArtifactDraftApplicationService(platform, documents=docs)
    imports = ArtifactImportApplicationService(platform, documents=docs)
    reviews = ArtifactReviewApplicationService(platform, documents=docs, drafts=drafts, imports=imports, plans=plans, executions=execs)
    return platform, ws, auth, issue, docs, plans, execs, drafts, imports, reviews


def content(title: str = 'External reconciliation') -> str:
    return f'''---\ndoc_id: "GSDLC-04-E-{title.upper().replace(' ', '-')}"\ntitle: "{title}"\nstatus: "draft"\nversion: "1.0.0"\nowner: "owner.local"\nupdated: "2026-08-22"\napproval: "pending"\n---\n# {title}\n\nGoverned artifact for external edit reconciliation acceptance.\n'''


def _approve(platform: Path, auth: AuthApplicationService, issue, approval_id: str) -> None:
    result = ApprovalApplicationService(platform, auth_store=auth.store).decide_authenticated(
        approval_id=approval_id, decision='approved', principal=issue.context.principal, session=issue.context,
        caller_actor=None, reason='GSDLC-04-E fixture approval',
    )
    assert result.ok, result.to_dict()


def _frozen(env, rel: str = 'docs/frozen.md'):
    platform, ws, auth, issue, docs, plans, execs, drafts, imports, reviews = env
    actor = issue.context.principal.actor_id
    role = issue.context.principal.roles[0]
    body = content()
    kw = dict(source_type='PASTE', destination_path=rel, actor=actor, actor_role=role, session_principal=actor, text_content=body)
    preview = imports.preview(**kw); assert preview.ok, preview.to_dict()
    persisted = imports.persist(**kw, expected_preview_sha256=preview.data['preview']['preview_sha256']); assert persisted.ok
    started = reviews.start_import(import_id=persisted.data['import']['import_id'], actor=actor, actor_role=role, session_principal=actor); assert started.ok, started.to_dict()
    plan = started.data['plan']
    req = execs.request_apply_approval(plan_id=plan['plan_id'], plan_hash=plan['plan_hash'], actor=actor, reason='freeze before external edit'); assert req.ok
    aid = req.data['approval']['approval_id']; _approve(platform, auth, issue, aid)
    applied = execs.apply(plan_id=plan['plan_id'], plan_hash=plan['plan_hash'], approval_id=aid, actor=actor); assert applied.ok, applied.to_dict()
    frozen = reviews.freeze(review_id=started.data['review']['review_id'], execution_id=applied.data['execution']['execution_id'], actor=actor, actor_role=role, session_principal=actor); assert frozen.ok, frozen.to_dict()
    return frozen.data['review'], actor, role


def test_external_modify_invalidates_freeze_and_exposes_git_diff_provenance(env):
    review, actor, role = _frozen(env)
    ws = env[1]; reviews = env[-1]; target = ws / review['relative_path']
    original = target.read_text(encoding='utf-8')
    target.write_text(original + '\nExternal editor change.\n', encoding='utf-8')
    result = reviews.reconcile(review_id=review['review_id'], actor=actor, actor_role=role, session_principal=actor)
    assert result.ok, result.to_dict(); r = result.data['review']; rec = r['reconciliation']
    assert r['status'] == 'REVALIDATION_REQUIRED' and r['approval_valid'] is False
    assert rec['change_kind'] == 'modified' and rec['auto_reverted'] is False and rec['hidden_merge'] is False
    assert 'External editor change.' in target.read_text(encoding='utf-8')
    assert 'External editor change.' in rec['git_diff']
    assert rec['source_provenance']['source_type'] == 'EXTERNAL_EDITOR'


def test_external_exact_rename_is_detected_without_hidden_move(env):
    review, actor, role = _frozen(env, 'docs/rename_me.md')
    ws = env[1]; reviews = env[-1]
    src = ws / 'docs/rename_me.md'; dst = ws / 'docs/renamed_external.md'; src.rename(dst)
    result = reviews.reconcile(review_id=review['review_id'], actor=actor, actor_role=role, session_principal=actor)
    assert result.ok, result.to_dict(); rec = result.data['review']['reconciliation']
    assert result.data['review']['status'] == 'REVALIDATION_REQUIRED'
    assert rec['change_kind'] == 'renamed' and rec['detected_relative_path'] == 'docs/renamed_external.md'
    assert not src.exists() and dst.exists() and rec['hidden_merge'] is False


def test_external_delete_is_detected_and_zero_hash_records_missing_source(env):
    review, actor, role = _frozen(env, 'docs/delete_me.md')
    ws = env[1]; reviews = env[-1]
    (ws / 'docs/delete_me.md').unlink()
    result = reviews.reconcile(review_id=review['review_id'], actor=actor, actor_role=role, session_principal=actor)
    assert result.ok, result.to_dict(); r=result.data['review']; rec=r['reconciliation']
    assert r['status'] == 'REVALIDATION_REQUIRED' and rec['change_kind'] == 'deleted'
    assert r['artifact']['content_hash'] == ZERO_SHA256
    assert r['artifact']['provenance']['normalized_sha256'] == ZERO_SHA256
    assert rec['auto_reverted'] is False


def test_branch_switch_with_changed_frozen_content_is_visible_and_invalidates(env):
    review, actor, role = _frozen(env, 'docs/branch.md')
    ws=env[1]; reviews=env[-1]
    subprocess.run(['git','add','docs/branch.md'],cwd=ws,check=True); subprocess.run(['git','commit','-qm','frozen source'],cwd=ws,check=True)
    subprocess.run(['git','checkout','-qb','external-branch'],cwd=ws,check=True)
    p=ws/'docs/branch.md'; p.write_text(p.read_text(encoding='utf-8')+'\nbranch drift\n',encoding='utf-8')
    result=reviews.reconcile(review_id=review['review_id'],actor=actor,actor_role=role,session_principal=actor)
    assert result.ok; rec=result.data['review']['reconciliation']
    assert rec['branch_changed'] is True and rec['git_branch_current']=='external-branch'
    assert result.data['review']['status']=='REVALIDATION_REQUIRED'


def test_unchanged_frozen_artifact_remains_valid(env):
    review, actor, role = _frozen(env, 'docs/unchanged.md')
    result=env[-1].reconcile(review_id=review['review_id'],actor=actor,actor_role=role,session_principal=actor)
    assert result.ok; r=result.data['review']
    assert r['status']=='FROZEN' and r['approval_valid'] is True
    assert r['reconciliation']['change_kind']=='unchanged'


def test_manual_and_import_review_routes_remain_available(env):
    platform, ws, auth, issue, docs, plans, execs, drafts, imports, reviews = env
    actor=issue.context.principal.actor_id; role=issue.context.principal.roles[0]
    imported, *_ = _frozen(env, 'docs/import-route.md')
    assert imported['source_kind']=='IMPORT'
    (ws/'docs/manual.md').write_text(content('Manual'),encoding='utf-8')
    subprocess.run(['git','add','docs/manual.md'],cwd=ws,check=True); subprocess.run(['git','commit','-qm','manual base'],cwd=ws,check=True)
    listing=docs.list_documents(); item=next(x for x in listing.data['nodes'] if x['relative_path']=='docs/manual.md')
    read=docs.read_document(item['document_id']); assert read.ok
    source_sha=read.data['document']['sha256']
    save=drafts.save(document_id=item['document_id'],content=content('Manual edited'),expected_source_sha256=source_sha,expected_revision_sha256=None,actor=actor,actor_role=role,session_principal=actor,event='SAVE'); assert save.ok,save.to_dict()
    started=reviews.start_document(document_id=item['document_id'],actor=actor,actor_role=role,session_principal=actor)
    assert started.ok and started.data['review']['source_kind']=='MANUAL'


def test_reconcile_endpoint_remains_human_session_protected():
    policy=resolve_route_policy('POST','/api/v1/workspace/artifact-reviews/arev_example/reconcile')
    assert policy is not None and policy.operation=='workspace.artifact_reviews.reconcile'


def test_artifact_reconciliation_ux_is_safe_accessible_and_never_auto_reverts():
    text=(ROOT/'ui/web/src/components/ArtifactReconciliationUX.ts').read_text(encoding='utf-8')
    flow=(ROOT/'ui/web/src/components/ArtifactReviewFlow.ts').read_text(encoding='utf-8')
    assert 'Reconciliación externa · VS Code / Git' in text
    assert 'Detectar cambio externo' in text and 'Git diff' in text and 'Source provenance' in text
    assert 'Nunca revierte automáticamente' in text
    assert "setAttribute('aria-live','polite')" in text
    assert '.innerHTML' not in text and 'fetch(' not in text
    assert 'createArtifactReconciliationUX' in flow


def test_lifecycle_external_change_api_preserves_backward_compatible_content_reconcile():
    text=(ROOT/'src/devpilot_core/application/artifact_lifecycle_service.py').read_text(encoding='utf-8')
    assert 'def reconcile_external_change' in text
    assert 'return self.reconcile_external_change(' in text
    assert 'auto_reverted' in text and 'hidden_merge' in text


def _literal_assignment(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f'{name} not found in {path}')


def test_runtime_fixture_contract_matches_prepare_browser_baseline_exactly():
    runtime = ROOT / 'scripts/devpl_gsdlc_04_e_runtime_console.py'
    harness = ROOT / 'scripts/devpl_gsdlc_04_e_windows_harness.py'
    required = tuple(_literal_assignment(runtime, 'REQUIRED_FIXTURE_FILES'))
    baseline = tuple(_literal_assignment(harness, 'BASELINE_TRACKED'))
    assert required == baseline
    assert 'docs/baseline.json' not in required
    assert required == (
        '.gitignore',
        '.devpilot/project.yaml',
        'docs/manual_authoring.md',
        'docs/manual_authoring.json',
        'docs/baseline.md',
    )
    allowed_dirty = set(_literal_assignment(runtime, 'ALLOWED_BROWSER_DIRTY_PATHS'))
    assert 'docs/gsdlc04e_review_candidate.md' in allowed_dirty
    assert 'docs/gsdlc04e_invalid.md' not in allowed_dirty
    runtime_version = _literal_assignment(runtime, 'VERSION')
    harness_version = _literal_assignment(harness, 'VERSION')
    assert runtime_version == '1.0.2'
    assert harness_version == '1.0.6'



def test_blocking_validation_http_403_preserves_navigable_review_payload(env):
    import base64
    platform, ws, auth, issue, docs, plans, execs, drafts, imports, reviews = env
    actor=issue.context.principal.actor_id; role=issue.context.principal.roles[0]
    body='# Missing frontmatter\n\nInvalid governed draft.\n'
    kw=dict(source_type='UPLOAD',destination_path='docs/gsdlc04e_invalid.md',actor=actor,actor_role=role,session_principal=actor,source_label='B08 invalid finding',original_filename='invalid_review_source.md',declared_mime='text/markdown',content_base64=base64.b64encode(body.encode()).decode())
    preview=imports.preview(**kw); assert preview.ok, preview.to_dict()
    persisted=imports.persist(**kw,expected_preview_sha256=preview.data['preview']['preview_sha256']); assert persisted.ok, persisted.to_dict()
    blocked=reviews.start_import(import_id=persisted.data['import']['import_id'],actor=actor,actor_role=role,session_principal=actor)
    assert not blocked.ok and blocked.data['review']['status']=='FINDINGS'
    payload,status=command_result_to_api_response(blocked,operation='workspace.artifact_reviews.start_import')
    assert status==403
    review=payload['data']['review']; assert review['status']=='FINDINGS' and review['plan'] is None
    assert any((finding.get('line') or finding.get('section')) for finding in review['findings'])


def test_ui_recovers_expected_403_findings_and_navigates_import_preview():
    review=(ROOT/'ui/web/src/components/ArtifactReviewFlow.ts').read_text(encoding='utf-8')
    imp=(ROOT/'ui/web/src/components/ArtifactImportWorkbench.ts').read_text(encoding='utf-8')
    assert 'reviewFromValidationBlock' in review and 'DevPilotApiError' in review
    assert "candidate.status!=='FINDINGS'" in review and 'Ir al hallazgo' in review
    assert 'source_kind:r.source_kind' in review and 'source_ref:r.source_ref' in review
    assert "detail.source_kind!=='IMPORT'" in imp and 'persisted.import_id' in imp
    assert 'setSelectionRange' in imp and "Preview de contenido importado para navegación de findings" in imp
    assert "targetLineIndex=index" in imp


def _load_fixture_identity_module():
    import importlib.util
    path = ROOT / 'scripts/devpl_gsdlc_04_e_fixture_identity.py'
    spec = importlib.util.spec_from_file_location('devpl_gsdlc_04_e_fixture_identity_test', path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_synthetic_wrong_role_is_canonical_developer_and_roundtrips(env, tmp_path):
    from devpilot_core.identity.auth_store import LocalAuthStore
    platform, ws, auth, *_ = env
    helper = _load_fixture_identity_module()
    credentials = tmp_path / 'WRONG_ROLE_LOGIN_DO_NOT_ATTACH.txt'
    result = helper.provision_identity(platform, credentials)
    assert result['status'] == 'PASS'
    assert result['auth_store_scope'] == 'runtime-api-root'
    assert result['roundtrip_login_verified'] is True
    assert result['verified_roles'] == ['developer']
    assert result['wrong_role_kind'] == 'canonical-role-without-approval-authority'
    assert LocalAuthStore(platform).get_identity_by_username('developer04e.local') is not None
    assert LocalAuthStore(ws).get_identity_by_username('developer04e.local') is None
    verify = helper.verify_identity(platform, credentials)
    assert verify['roundtrip_login_verified'] is True and verify['verified_roles'] == ['developer']
    cleaned = helper.cleanup_identity(platform, credentials)
    assert cleaned['status'] == 'PASS' and cleaned['runtime_identity_removed'] is True and cleaned['credentials_removed'] is True
    assert LocalAuthStore(platform).get_identity_by_username('developer04e.local') is None
    assert auth.store.get_identity_by_username('owner.local') is not None


def test_canonical_developer_can_render_authenticated_session_but_cannot_approve(env, tmp_path):
    from fastapi.testclient import TestClient
    from devpilot_core.interfaces.api.app import create_app
    platform, _, auth, *_ = env
    helper = _load_fixture_identity_module()
    credentials = tmp_path / 'WRONG_ROLE_LOGIN_DO_NOT_ATTACH.txt'
    helper.provision_identity(platform, credentials)
    values = dict(line.split('=', 1) for line in credentials.read_text(encoding='utf-8').splitlines() if '=' in line)
    client = TestClient(create_app(platform, api_token='local-test-token', auth_service=AuthApplicationService(platform)))
    headers = {'Origin': 'http://127.0.0.1:5173'}
    login = client.post('/api/v1/auth/login', json={'username': values['username'], 'password': values['password']}, headers=headers)
    assert login.status_code == 200
    assert login.json()['session']['principal']['roles'] == ['developer']
    inspected = client.get('/api/v1/auth/session', headers=headers)
    assert inspected.status_code == 200
    assert inspected.json()['session']['principal']['username'] == 'developer04e.local'
    csrf = client.cookies.get('devpilot_csrf')
    denied = client.post('/api/v1/approvals/APPROVAL-GSDLC04E-RBAC-PROBE/approve', json={}, headers={**headers, 'X-DevPilot-CSRF': csrf})
    assert denied.status_code == 403
    finding_ids = [f.get('id') for f in denied.json().get('findings', [])]
    assert 'RBAC_ROLE_DENY' in finding_ids
    helper.cleanup_identity(platform, credentials)


def test_windows_harness_requires_renderable_canonical_wrong_role_proof_and_cleanup():
    harness = (ROOT / 'scripts/devpl_gsdlc_04_e_windows_harness.py').read_text(encoding='utf-8')
    helper = (ROOT / 'scripts/devpl_gsdlc_04_e_fixture_identity.py').read_text(encoding='utf-8')
    assert 'wrong-role-auth-prepare' in harness and 'wrong-role-auth-cleanup' in harness
    assert 'live_api_login_verified' in harness and 'auth_session_renderable' in harness and 'wrong_role_approval_denied' in harness
    assert 'RBAC_ROLE_DENY' in harness
    assert '13_wrong_role_auth_prepare_v1_0_5.json' in harness and '14_wrong_role_auth_cleanup_v1_0_5.json' in harness
    assert 'WRONG_ROLE_LOGIN_DO_NOT_ATTACH.txt' in harness and 'developer04e.local' in harness
    assert 'VIEWER_LOGIN_DO_NOT_ATTACH.txt' in harness  # legacy forensic cleanup only
    assert 'ROLE = "developer"' in helper and 'USERNAME = "developer04e.local"' in helper
    assert 'LEGACY_USERNAME = "viewer04e.local"' in helper
    assert 'LocalAuthStore(auth_root)' in helper and 'AuthApplicationService(auth_root)' in helper
    assert 'credential round-trip failed against the runtime API auth store' in helper


def _load_04e_harness_module():
    import importlib.util
    path = ROOT / 'scripts/devpl_gsdlc_04_e_windows_harness.py'
    spec = importlib.util.spec_from_file_location('devpl_gsdlc_04_e_windows_harness_test', path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_execution_record(repo, execution_id, pre_sha, post_sha, status='applied', rollback=None):
    path = repo / 'outputs/uoc005_control/records' / f'{execution_id}.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'execution_id': execution_id,
        'plan_id': 'eplan_test',
        'relative_path': 'docs/baseline.md',
        'pre_sha256': pre_sha,
        'post_sha256': post_sha,
        'status': status,
        'rollback': rollback,
    }
    path.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    return path


def test_b15_rollback_machine_gates_prove_applied_then_restored_preimage(tmp_path, monkeypatch):
    harness = _load_04e_harness_module()
    repo = tmp_path / 'repo'
    fixture = tmp_path / 'fixture'
    evidence = tmp_path / 'evidence'
    repo.mkdir()
    (fixture / 'docs').mkdir(parents=True)
    (evidence / 'runtime').mkdir(parents=True)
    baseline = harness.expected_fixture_bytes()['docs/baseline.md']
    post = baseline + b'\nTemporary rollback proof 04-E.\n'
    (fixture / 'docs/baseline.md').write_bytes(baseline)
    (fixture / harness.TARGET_ARTIFACT).write_text('baseline target\n', encoding='utf-8')
    subprocess.run(['git', 'init', '-q'], cwd=fixture, check=True)
    subprocess.run(['git', 'config', 'user.email', 'fixture@example.invalid'], cwd=fixture, check=True)
    subprocess.run(['git', 'config', 'user.name', 'Fixture'], cwd=fixture, check=True)
    subprocess.run(['git', 'add', '.'], cwd=fixture, check=True)
    subprocess.run(['git', 'commit', '-qm', 'baseline'], cwd=fixture, check=True)
    (fixture / harness.TARGET_ARTIFACT).write_text('baseline target\nexternal drift\n', encoding='utf-8')
    (fixture / 'docs/baseline.md').write_bytes(post)
    pre_sha = hashlib.sha256(baseline).hexdigest()
    post_sha = hashlib.sha256(post).hexdigest()
    _write_execution_record(repo, 'uedit_test', pre_sha, post_sha)
    api = evidence / 'runtime/api_console.log'
    api.write_text(
        'INFO: POST /api/v1/workspace/edit-plans/eplan_test/apply HTTP/1.1" 200 OK\n'
        'INFO: GET /api/v1/workspace/edit-executions/uedit_test HTTP/1.1" 200 OK\n'
        'INFO: GET /api/v1/workspace/artifact-drafts/doc_test HTTP/1.1" 403 Forbidden\n',
        encoding='utf-8',
    )
    state = harness.b15_state(repo, fixture, evidence)
    assert state['resume_mode'] == 'ROLLBACK_ONLY'
    monkeypatch.setattr(harness, 'port_open', lambda port: port in {8787, 5173})
    pre = harness.rollback_preflight(repo, fixture, evidence)
    assert pre['status'] == 'PASS'
    assert pre['execution_id'] == 'uedit_test'
    assert pre['manual_draft_preimage_conflict_observed'] is True
    (fixture / 'docs/baseline.md').write_bytes(baseline)
    rollback = {'mode': 'manual-approval-bound', 'approval_id': 'APPROVAL-ROLLBACK-TEST', 'restored_sha256': pre_sha, 'integrity_pass': True}
    _write_execution_record(repo, 'uedit_test', pre_sha, post_sha, status='rolled-back-manual', rollback=rollback)
    with api.open('a', encoding='utf-8') as stream:
        stream.write('INFO: POST /api/v1/workspace/edit-executions/uedit_test/rollback-approval-request HTTP/1.1" 200 OK\n')
        stream.write('INFO: POST /api/v1/approvals/APPROVAL-ROLLBACK-TEST/approve HTTP/1.1" 200 OK\n')
        stream.write('INFO: POST /api/v1/workspace/edit-executions/uedit_test/rollback HTTP/1.1" 200 OK\n')
    verified = harness.rollback_verify(repo, fixture, evidence)
    assert verified['status'] == 'PASS'
    assert verified['execution_status'] == 'rolled-back-manual'
    assert verified['restored_preimage'] is True
    assert verified['partial_writes_total'] == 0
    assert verified['actual_dirty_paths'] == [harness.TARGET_ARTIFACT]


def test_b15_state_classifier_accepts_safe_replay_when_source_returned_to_git_preimage(tmp_path):
    harness = _load_04e_harness_module()
    repo = tmp_path / 'repo'; repo.mkdir()
    fixture = tmp_path / 'fixture'; evidence = tmp_path / 'evidence'
    (fixture/'docs').mkdir(parents=True); (evidence/'runtime').mkdir(parents=True)
    baseline = harness.expected_fixture_bytes()['docs/baseline.md']
    post = baseline + b'\nTemporary rollback proof 04-E.\n'
    (fixture/'docs/baseline.md').write_bytes(baseline)
    (fixture/harness.TARGET_ARTIFACT).write_text('baseline target\n', encoding='utf-8')
    subprocess.run(['git','init','-q'],cwd=fixture,check=True)
    subprocess.run(['git','config','user.email','fixture@example.invalid'],cwd=fixture,check=True)
    subprocess.run(['git','config','user.name','Fixture'],cwd=fixture,check=True)
    subprocess.run(['git','add','.'],cwd=fixture,check=True); subprocess.run(['git','commit','-qm','baseline'],cwd=fixture,check=True)
    (fixture/harness.TARGET_ARTIFACT).write_text('baseline target\nexternal drift\n',encoding='utf-8')
    pre_sha=hashlib.sha256(baseline).hexdigest(); post_sha=hashlib.sha256(post).hexdigest()
    _write_execution_record(repo,'uedit_stale',pre_sha,post_sha,status='applied')
    (evidence/'runtime/api_console.log').write_text(
        'INFO: POST /api/v1/workspace/edit-plans/eplan_stale/apply HTTP/1.1" 200 OK\n'
        'INFO: GET /api/v1/workspace/edit-executions/uedit_stale HTTP/1.1" 200 OK\n',encoding='utf-8')
    state=harness.b15_state(repo,fixture,evidence)
    assert state['resume_mode']=='REPLAY_B15'
    assert state['current_git_equivalent'] is True
    with pytest.raises(Exception):
        harness.rollback_preflight(repo,fixture,evidence)


def test_browser_final_gate_requires_b15_machine_rollback_proof():
    harness = (ROOT / 'scripts/devpl_gsdlc_04_e_windows_harness.py').read_text(encoding='utf-8')
    assert 'b15-state' in harness and 'rollback-preflight' in harness and 'rollback-verify' in harness
    assert '15_rollback_verify_v1_0_11.json' in harness
    assert 'B15 machine-readable rollback verification PASS is required' in harness
    assert 'REPLAY_B15' in harness and 'ROLLBACK_ONLY' in harness
    assert 'rolled-back-manual' in harness


def test_recovery009_rollback_preflight_is_method_aware_and_ignores_cors_options_200(tmp_path, monkeypatch):
    harness = _load_04e_harness_module()
    repo = tmp_path / 'repo'; repo.mkdir()
    fixture = tmp_path / 'fixture'; evidence = tmp_path / 'evidence'
    (fixture / 'docs').mkdir(parents=True); (evidence / 'runtime').mkdir(parents=True)
    baseline = harness.expected_fixture_bytes()['docs/baseline.md']
    post = baseline + b'\nTemporary rollback proof 04-E.\n'
    (fixture / 'docs/baseline.md').write_bytes(baseline)
    (fixture / harness.TARGET_ARTIFACT).write_text('baseline target\n', encoding='utf-8')
    subprocess.run(['git','init','-q'],cwd=fixture,check=True)
    subprocess.run(['git','config','user.email','fixture@example.invalid'],cwd=fixture,check=True)
    subprocess.run(['git','config','user.name','Fixture'],cwd=fixture,check=True)
    subprocess.run(['git','add','.'],cwd=fixture,check=True)
    subprocess.run(['git','commit','-qm','baseline'],cwd=fixture,check=True)
    (fixture / harness.TARGET_ARTIFACT).write_text('baseline target\nexternal drift\n', encoding='utf-8')
    (fixture / 'docs/baseline.md').write_bytes(post)
    pre_sha = hashlib.sha256(baseline).hexdigest(); post_sha = hashlib.sha256(post).hexdigest()
    _write_execution_record(repo, 'uedit_reauth', pre_sha, post_sha, status='applied')
    api = evidence / 'runtime/api_console.log'
    api.write_text(
        'INFO: POST /api/v1/workspace/edit-plans/eplan_reauth/apply HTTP/1.1" 200 OK\n'
        'INFO: GET /api/v1/workspace/edit-executions/uedit_reauth HTTP/1.1" 200 OK\n'
        'INFO: OPTIONS /api/v1/workspace/edit-executions/uedit_reauth/rollback-approval-request HTTP/1.1" 200 OK\n'
        'INFO: POST /api/v1/workspace/edit-executions/uedit_reauth/rollback-approval-request HTTP/1.1" 401 Unauthorized\n'
        'INFO: POST /api/v1/workspace/edit-executions/uedit_reauth/rollback-approval-request HTTP/1.1" 401 Unauthorized\n',
        encoding='utf-8',
    )
    monkeypatch.setattr(harness, 'port_open', lambda port: port in {8787, 5173})
    result = harness.rollback_preflight(repo, fixture, evidence)
    assert result['status'] == 'PASS'
    assert result['prior_rollback_post_401_total'] == 2
    assert result['prior_rollback_options_200_total'] == 1
    assert result['prior_rollback_post_200_total'] == 0
    assert result['prior_rollback_http_200_total'] == 0
    assert result['http_log_method_aware'] is True
    assert result['prior_rollback_unauthorized_total'] == 2
    assert result['owner_reauthentication_required'] is True
    assert result['approval_ui_mode'] == 'inline-rollback-approval-card'
    assert result['approval_center_required'] is False
    assert result['prior_rollback_success_total'] == 0


def test_recovery009_runtime_status_decouples_harness_and_runtime_console_versions(tmp_path, monkeypatch):
    harness = _load_04e_harness_module()
    evidence = tmp_path / 'evidence'; fixture = tmp_path / 'fixture'
    (evidence / 'runtime').mkdir(parents=True); fixture.mkdir()
    binding = {
        'allowed_workspace_root': str(fixture.resolve()),
        'active_workspace_root': str(fixture.resolve()),
        'registry_env_cleared': True,
        'scope': 'gsdlc-04-e-browser-fixture-only',
    }
    for role in ('api','ui'):
        (evidence / 'runtime' / f'{role}_console_state.json').write_text(json.dumps({
            'status':'PASS', 'role':role, 'version':'1.0.2', 'workspace_binding': binding if role == 'api' else None,
        }), encoding='utf-8')
    monkeypatch.setattr(harness, 'port_open', lambda port: port in {8787, 5173})
    result = harness.runtime_status(evidence, fixture)
    assert result['status'] == 'PASS'
    assert harness.VERSION == '1.0.6'
    assert harness.RUNTIME_CONSOLE_VERSION == '1.0.2'


def test_recovery009_rollback_ui_contract_is_inline_and_does_not_require_approval_center_handoff():
    planner = (ROOT / 'ui/web/src/components/DocumentEditPlanner.ts').read_text(encoding='utf-8')
    harness = (ROOT / 'scripts/devpl_gsdlc_04_e_windows_harness.py').read_text(encoding='utf-8')
    assert "approvalCard('Aprobación de rollback'" in planner
    assert "button('Aprobar'" in planner
    assert 'Solicitar aprobación de rollback' in planner
    assert 'inline-rollback-approval-card' in harness
    assert 'approval_center_required":False' in harness
    assert 'PROHIBITED_BY_RECOVERY_GUIDE' in harness


def _load_04e_runtime_console_module():
    import importlib.util
    path = ROOT / 'scripts/devpl_gsdlc_04_e_runtime_console.py'
    spec = importlib.util.spec_from_file_location('devpl_gsdlc_04_e_runtime_console_test', path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_recovery010_runtime_accepts_exact_b15_applied_dirty_scope_from_persisted_execution(tmp_path):
    runtime = _load_04e_runtime_console_module()
    repo = tmp_path / 'repo'; repo.mkdir()
    fixture = tmp_path / 'fixture'; evidence = tmp_path / 'evidence'
    (fixture / 'docs').mkdir(parents=True); (evidence / 'recovery_009').mkdir(parents=True)
    baseline = b'---\ndoc_id: "B15"\n---\n# Rollback baseline\n'
    target = b'# reviewed\n'
    (fixture / 'docs/baseline.md').write_bytes(baseline)
    (fixture / 'docs/gsdlc04e_review_candidate.md').write_bytes(target)
    subprocess.run(['git','init','-q'],cwd=fixture,check=True)
    subprocess.run(['git','config','user.email','fixture@example.invalid'],cwd=fixture,check=True)
    subprocess.run(['git','config','user.name','Fixture'],cwd=fixture,check=True)
    subprocess.run(['git','add','.'],cwd=fixture,check=True)
    subprocess.run(['git','commit','-qm','baseline'],cwd=fixture,check=True)
    post = baseline + b'\nTemporary rollback proof 04-E.\n'
    (fixture / 'docs/baseline.md').write_bytes(post)
    (fixture / 'docs/gsdlc04e_review_candidate.md').write_bytes(target + b'external drift\n')
    pre_sha = hashlib.sha256(baseline).hexdigest()
    post_sha = hashlib.sha256(post).hexdigest()
    execution_id = 'uedit_runtime_recovery'
    _write_execution_record(repo, execution_id, pre_sha, post_sha, status='applied')
    preflight = {
        'status':'PASS',
        'resume_mode':'ROLLBACK_REAUTH_NEW_RUNTIME',
        'recognized_resume_state':{
            'b15':{
                'execution_id':execution_id,
                'record_pre_sha256':pre_sha,
                'record_post_sha256':post_sha,
            }
        },
    }
    (evidence / 'recovery_009/recovery_009_preflight.json').write_text(json.dumps(preflight), encoding='utf-8')
    policy = runtime._allow_b15_applied_runtime(
        repo, fixture, evidence,
        ['docs/baseline.md','docs/gsdlc04e_review_candidate.md'],
    )
    assert policy['mode'] == 'b15-applied-rollback-recovery'
    assert policy['execution_id'] == execution_id
    assert policy['execution_status'] == 'applied'
    assert policy['post_sha256'] == post_sha


def test_recovery010_runtime_rejects_baseline_dirty_without_exact_b15_authority(tmp_path):
    runtime = _load_04e_runtime_console_module()
    repo = tmp_path / 'repo'; repo.mkdir()
    fixture = tmp_path / 'fixture'; evidence = tmp_path / 'evidence'
    (fixture / 'docs').mkdir(parents=True); evidence.mkdir()
    (fixture / 'docs/baseline.md').write_text('baseline changed\n', encoding='utf-8')
    (fixture / 'docs/gsdlc04e_review_candidate.md').write_text('target changed\n', encoding='utf-8')
    with pytest.raises(Exception):
        runtime._allow_b15_applied_runtime(
            repo, fixture, evidence,
            ['docs/baseline.md','docs/gsdlc04e_review_candidate.md'],
        )


def test_recovery010_runtime_version_and_harness_contract_are_forward_consistent():
    runtime = (ROOT / 'scripts/devpl_gsdlc_04_e_runtime_console.py').read_text(encoding='utf-8')
    harness = (ROOT / 'scripts/devpl_gsdlc_04_e_windows_harness.py').read_text(encoding='utf-8')
    assert 'VERSION="1.0.2"' in runtime
    assert 'RUNTIME_CONSOLE_VERSION = "1.0.2"' in harness
    assert 'b15-applied-rollback-recovery' in runtime
    assert '--validate-only' in runtime
    assert 'persisted-uoc005-execution+recovery009-preflight+git-preimage' in runtime
    assert '15_rollback_preflight_v1_0_11.json' in harness
    assert '15_rollback_verify_v1_0_11.json' in harness



def test_recovery011_browser_context_recovery_is_explicit_execution_bound_and_server_read_only():
    main = (ROOT / 'ui/web/src/main.ts').read_text(encoding='utf-8')
    client = (ROOT / 'ui/web/src/api/client.ts').read_text(encoding='utf-8')
    assert "parseExplicitProjectRecoveryIntent(path, params)" in main
    assert "path !== '/workspace/documents' || params.get('recover_project_context') !== 'server-active'" in client
    assert "params.get('execution')" in client and "params.get('document')" in client
    assert "client.settingsWorkspace()" in main
    assert "client.workspaceEditExecutionStatus(intent.execution_id)" in main
    assert "restoreProjectJourneyContextFromServerRecovery" in main
    recovery_segment = main.split('async function recoverExplicitServerProjectContext', 1)[1].split('function currentLocationTarget', 1)[0]
    assert 'projectEntryDryRun' not in recovery_segment
    assert 'projectEntryRevalidate' not in recovery_segment
    assert 'projectEntryRequestExecutionApproval' not in recovery_segment
    assert 'projectEntryExecute' not in recovery_segment
    assert 'workspaceContext.configured === true' in client
    assert 'workspaceContext.valid === true' in client
    assert 'workspaceContext.read_only === true' in client
    assert 'workspaceContext.network_used === false' in client
    assert 'workspaceContext.external_api_used === false' in client
    assert 'workspaceContext.mutations_performed === false' in client
    assert "['configured-root', 'configured-registry'].includes(mode)" in client
    assert 'executionId === expected.executionId' in client
    assert 'documentId === expected.documentId' in client
    assert "['applied', 'rolled-back-manual'].includes(executionStatus)" in client
    assert "entry_mode: 'OPEN_EXISTING'" in client
    assert 'globalThis.sessionStorage?.setItem(PROJECT_JOURNEY_CONTEXT_KEY' in client


def test_recovery011_auth_redirect_preserves_query_and_normal_project_entry_contract_remains():
    main = (ROOT / 'ui/web/src/main.ts').read_text(encoding='utf-8')
    client = (ROOT / 'ui/web/src/api/client.ts').read_text(encoding='utf-8')
    entry = (ROOT / 'ui/web/src/pages/ProjectEntryDryRunView.ts').read_text(encoding='utf-8')
    assert 'currentLocationTarget(path)' in main
    assert "return `${path}${globalThis.location.search ?? ''}`" in main
    assert "resolvePostLoginReturn(params.get('return'))" in main
    assert "const bare = value.split(/[?#]/, 1)[0]" in client
    assert "if (bare === '/login' || bare === '/first-run') return '/'" in client
    assert 'activateProjectJourney' in entry
    assert 'executionPayload.status' in entry
    assert 'contexto de proyecto permanece bloqueado' in entry
    assert "recover_project_context" not in entry


def test_recovery011_harness_evidence_names_are_forward_versioned_without_runtime_contract_drift():
    harness = (ROOT / 'scripts/devpl_gsdlc_04_e_windows_harness.py').read_text(encoding='utf-8')
    runtime = (ROOT / 'scripts/devpl_gsdlc_04_e_runtime_console.py').read_text(encoding='utf-8')
    assert 'VERSION = "1.0.6"' in harness
    assert 'CORRECTIVE_LEVEL = "GSDLC-04-E-RECOVERY-011"' in harness
    assert '15_rollback_preflight_v1_0_11.json' in harness
    assert '15_rollback_verify_v1_0_11.json' in harness
    assert '15_b15_state_v1_0_11.json' in harness
    assert 'RUNTIME_CONSOLE_VERSION = "1.0.2"' in harness
    assert 'VERSION="1.0.2"' in runtime


def test_recovery014_same_tab_login_continuity_uses_pending_intent_not_fragile_return_query():
    main = (ROOT / 'ui/web/src/main.ts').read_text(encoding='utf-8')
    client = (ROOT / 'ui/web/src/api/client.ts').read_text(encoding='utf-8')
    assert "parseExplicitProjectRecoveryIntent(path, params)" in main
    assert "saveProjectRecoveryIntent(explicitRecoveryIntent)" in main
    assert "projectRecoveryTarget(explicitRecoveryIntent)" in main
    assert "resolvePostLoginReturn(params.get('return'))" in main
    assert "const intent=explicit ?? readProjectRecoveryIntent()" in main
    assert "recoveryOutcome === 'failed'" in main
    assert "recovery=server-context-failed" in main
    assert "PROJECT_RECOVERY_INTENT_KEY" in client
    assert "PROJECT_RECOVERY_INTENT_TTL_MS = 15 * 60 * 1000" in client
    assert "target_path: '/workspace/documents'" in client
    assert "kind: 'server-active'" in client
    assert "return intent ? projectRecoveryTarget(intent) : safeLocalUiReturn(value)" in client


def test_recovery014_pending_intent_is_ux_only_and_server_execution_remains_authority():
    main = (ROOT / 'ui/web/src/main.ts').read_text(encoding='utf-8')
    client = (ROOT / 'ui/web/src/api/client.ts').read_text(encoding='utf-8')
    recovery_segment = main.split('async function recoverExplicitServerProjectContext', 1)[1].split('function currentLocationTarget', 1)[0]
    assert 'client.settingsWorkspace()' in recovery_segment
    assert 'client.workspaceEditExecutionStatus(intent.execution_id)' in recovery_segment
    assert 'projectEntryDryRun' not in recovery_segment
    assert 'projectEntryRevalidate' not in recovery_segment
    assert 'projectEntryRequestExecutionApproval' not in recovery_segment
    assert 'projectEntryExecute' not in recovery_segment
    assert 'executionId === expected.executionId' in client
    assert 'documentId === expected.documentId' in client
    assert "['applied', 'rolled-back-manual'].includes(executionStatus)" in client
    assert 'clearProjectRecoveryIntent();' in client
