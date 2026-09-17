from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def read(rel:str)->str: return (ROOT/rel).read_text(encoding='utf-8')

def test_ux_p0_b_current_authority_is_preserved_across_successors():
    state=json.loads(read('.devpilot/project_state.json'))
    assert state['ux_p0_a_status']=='CLOSED/PASS/WINDOWS-VALIDATED'
    assert state['ux_p0_status'] in {'ACTIVE/UX-P0-B', 'ACTIVE/UX-P0-B-CORRECTIVE', 'ACTIVE/UX-P0-C', 'ACTIVE/UX-P0-D', 'ACTIVE/UX-P0-E', 'CLOSED/PASS/WINDOWS-VALIDATED'}
    assert state['ux_p0_b_status']=='CLOSED/PASS/WINDOWS-VALIDATED'
    assert state['ux_p0_current_micro_sprint'] in {'DEVPL-UX-P0-B', 'DEVPL-UX-P0-B-CORRECTIVE', 'DEVPL-UX-P0-C', 'DEVPL-UX-P0-D', 'DEVPL-UX-P0-E'}
    if state['ux_p0_current_micro_sprint'] in {'DEVPL-UX-P0-C', 'DEVPL-UX-P0-D', 'DEVPL-UX-P0-E'}:
        if state['ux_p0_current_micro_sprint']=='DEVPL-UX-P0-C':
            assert state['ux_p0_next_micro_sprint']=='DEVPL-UX-P0-D'
        elif state['ux_p0_current_micro_sprint']=='DEVPL-UX-P0-D':
            assert state['ux_p0_next_micro_sprint']=='DEVPL-UX-P0-E'
        else:
            assert state['ux_p0_next_micro_sprint']=='DEVPL-GSDLC-13'
        if state['ux_p0_current_micro_sprint']=='DEVPL-UX-P0-C':
            assert state['ux_p0_source_repo'].startswith('repo_DevPilot_Local_433_')
            assert state['ux_p0_source_commit']=='dc63672f2d617968998f3c68374a03581b348578'
        elif state['ux_p0_current_micro_sprint']=='DEVPL-UX-P0-D':
            assert state['ux_p0_source_repo'].startswith('repo_DevPilot_Local_434_')
            assert state['ux_p0_source_commit']=='75dbead73c6c6aaf1f792e02f3659ee2b6c0b927'
        else:
            assert state['ux_p0_source_repo'].startswith('repo_DevPilot_Local_435_')
            assert state['ux_p0_source_commit']=='f1e4c5b8dc1882f7dc724ba87755cdd894f274c8'
        assert state['ux_p0_b_successor_repo'].startswith('repo_DevPilot_Local_433_')
    else:
        assert state['ux_p0_next_micro_sprint']=='DEVPL-UX-P0-C'
        assert state['ux_p0_source_repo'].startswith(('repo_DevPilot_Local_431_', 'repo_DevPilot_Local_432_'))
        assert state['ux_p0_source_commit'] in {
            '013cc84f0df9eff1fb750b542644bfd0c7dc8717',
            '0136c3cac5d10ef8c647f96e38423f4940cadb6c',
        }
    assert state['ux_p0_b_full_regression_runs']==0
    assert state['ux_p0_full_regression_budget'] in {'0/1-RESERVED-FOR-UX-P0-E','1/1-CONSUMED-BY-UX-P0-E'}

def test_grouped_navigation_preserves_paths_and_route_authority():
    main=read('ui/web/src/main.ts'); nav=read('ui/web/src/ux/navigationPresentation.ts')
    for path in ['/', '/project/status','/pre-code','/planning/roadmap','/workspace/documents','/story/code','/quality','/release/readiness','/recovery','/reconciliation','/ai','/settings','/account','/help']:
        assert f"path: '{path}'" in main
    for label in ['Start','Understand & Plan','Build & Validate','Release','Recover','AI','Diagnostics','Global']:
        assert f"label: '{label}'" in nav
    assert 'function routeAllowed' in main and 'function routeVisible' in main
    assert 'guidedCorePaths' not in main

def test_persistent_context_is_server_authoritative_and_fail_closed():
    src=read('ui/web/src/components/ShellProjectContext.ts')
    assert 'api.projectStatus()' in src
    assert 'api.recoveryStatus()' in src
    assert 'read_only === true' in src
    assert 'actor_neutral === true' in src
    assert 'network_used === false' in src
    assert 'external_api_used === false' in src
    assert 'mutations_performed === false' in src
    assert "browserStorageAuthority = 'false'" in src
    assert 'data.next_action' in src
    assert 'Contexto del proyecto no disponible' in src

def test_guided_expert_and_handoff_preserve_authority():
    main=read('ui/web/src/main.ts'); mode=read('ui/web/src/components/ExperienceModeControl.ts')
    assert "item.path === '/approvals' || item.path === '/account'" in main
    assert 'auxiliaryApprovalHandoff' in main
    assert 'primary-nav__group' in mode
    assert 'authority' in mode.lower()
    assert 'expert-only' in read('ui/web/src/components/SessionBanner.ts')

def test_shell_is_responsive_and_accessible():
    css=read('ui/web/src/styles.css'); main=read('ui/web/src/main.ts')
    assert '@media (max-width: 1180px)' in css
    assert '@media (max-width: 760px)' in css
    assert '@media (max-width: 480px)' in css
    assert 'var(--dp-control-min-target)' in css
    assert "aria-label','Ubicación actual'" in main
    assert "setAttribute('aria-current','page')" in main

def test_b_is_preliminary_and_full_remains_zero():
    report=read('docs/audits/DEVPL_UX_P0_B_IMPLEMENTATION_REPORT.md')
    assert 'not the final industrial UI' in report
    state=json.loads(read('.devpilot/project_state.json'))
    assert state['ux_p0_b_full_regression_runs']==0
