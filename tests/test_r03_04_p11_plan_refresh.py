"""Focused P11: explicit review renewal without loss of Owner state."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

from devpilot_core.application import pre_code_wizard_service as pre


def _service(tmp_path: Path, monkeypatch, *, approval_id=None):
    project = tmp_path / 'pilot-b'
    project.mkdir()
    row = {
        'status': 'APPROVAL_REQUIRED', 'mode': 'MANUAL',
        'content': '# Security\n\nContenido revisado Owner.\n',
        'base_sha256': '0' * 64,
        'artifact': {'state': 'DRAFT', 'artifact_id': 'owner-security'},
        'plan_id': 'eplan_expired', 'plan_hash': 'hash_expired',
        'diff': {'content': 'old diff'}, 'review_id': 'arev_previous',
        'approval_id': approval_id, 'updated_at': 'previous',
        'derivation': {'owner_notes': 'do not modify'},
    }
    state = {'stages': {'security': row}, 'r03_04_authoring': {'selected_option_id': 'T1'}}
    svc = object.__new__(pre.PreCodeWizardApplicationService)
    svc._stage_by_id = {'security': {'relative_path': 'docs/security.md'}}
    monkeypatch.setattr(pre.PreCodeWizardApplicationService, '_context', lambda self: ('pilot-b', project))
    monkeypatch.setattr(pre.PreCodeWizardApplicationService, '_identity', lambda *args, **kwargs: None)
    monkeypatch.setattr(pre.PreCodeWizardApplicationService, '_adr_companion_gate', lambda *args, **kwargs: None)
    monkeypatch.setattr(pre.PreCodeWizardApplicationService, '_load_state', lambda self, wid: state)
    monkeypatch.setattr(pre.PreCodeWizardApplicationService, '_write_state', lambda self, wid, value: state.update(value))
    monkeypatch.setattr(pre.PreCodeWizardApplicationService, '_current_stage', lambda self, value: {'stage_id': 'security'})
    monkeypatch.setattr(pre.PreCodeWizardApplicationService, '_stage_state', lambda self, value, sid: value['stages'][sid])
    calls = []

    def renew(**kwargs):
        calls.append(deepcopy(kwargs))
        return svc._pass('review', 'TEST_PASS', 'Renewed plan.', {
            'review': {
                'review_id': 'arev_successor', 'status': 'APPROVAL_REQUIRED',
                'findings': [], 'validation': {'quality': 'PASS'},
                'plan': {'plan_id': 'eplan_fresh', 'plan_hash': 'hash_fresh',
                         'diff': {'content': 'fresh diff'}},
            }
        })

    svc.reviews = SimpleNamespace(start_runtime_draft=renew)
    return svc, state, row, calls, project


def test_expired_plan_revalidated_without_rewriting_owner_content(tmp_path, monkeypatch):
    svc, state, row, calls, project = _service(tmp_path, monkeypatch)
    original = row['content']
    original_artifact = deepcopy(row['artifact'])
    result = svc.start_review(stage_id='security', actor='owner', actor_role='owner',
                              session_principal='owner', effective_roles=['owner'])
    assert result.ok
    assert len(calls) == 1
    assert calls[0]['artifact'] == original_artifact
    assert calls[0]['content'] == original
    assert row['content'] == original
    assert row['plan_id'] == 'eplan_fresh'
    assert row['plan_hash'] == 'hash_fresh'
    assert row['review_id'] == 'arev_successor'
    assert row['diff'] == {'content': 'fresh diff'}
    assert row['approval_id'] is None
    assert row['derivation'] == {'owner_notes': 'do not modify'}
    assert state['r03_04_authoring']['selected_option_id'] == 'T1'
    assert not list(project.rglob('*.md'))


def test_plan_cannot_refresh_after_approval_exists(tmp_path, monkeypatch):
    svc, _, row, calls, _ = _service(tmp_path, monkeypatch, approval_id='approval_active')
    result = svc.start_review(stage_id='security', actor='owner', actor_role='owner',
                              session_principal='owner', effective_roles=['owner'])
    assert not result.ok
    assert not calls
    assert row['plan_id'] == 'eplan_expired'


def test_draft_required_for_non_approval_stage(tmp_path, monkeypatch):
    svc, _, row, calls, _ = _service(tmp_path, monkeypatch)
    row['status'] = 'APPLIED'
    result = svc.start_review(stage_id='security', actor='owner', actor_role='owner',
                              session_principal='owner', effective_roles=['owner'])
    assert not result.ok
    assert not calls
