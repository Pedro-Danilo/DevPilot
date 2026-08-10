from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def read(rel): return (ROOT/rel).read_text(encoding='utf-8')

def test_uoc005_ui_exposes_explicit_human_approval_apply_and_separate_rollback_approval():
    ui=read('ui/web/src/components/DocumentEditPlanner.ts')
    for marker in ['Solicitar aprobación de apply','Aprobar','Denegar','Aplicar cambio aprobado','Solicitar aprobación de rollback','Revertir cambio aprobado']:
        assert marker in ui
    assert "applyApproval.status !== 'approved'" in ui
    assert "rollbackApproval.status !== 'approved'" in ui
    assert 'Git stage/commit siguen fuera de UOC-005' in ui
    assert 'patch.apply genérico' in ui

def test_uoc005_ui_calls_typed_api_client_not_shell():
    ui=read('ui/web/src/components/DocumentEditPlanner.ts'); client=read('ui/web/src/api/client.ts')
    assert 'requestWorkspaceEditApplyApproval' in ui and 'applyWorkspaceEdit' in ui
    assert 'requestWorkspaceEditRollbackApproval' in ui and 'rollbackWorkspaceEdit' in ui
    assert '/approval-request' in client and '/rollback-approval-request' in client
    assert 'child_process' not in ui and 'exec(' not in ui and 'spawn(' not in ui

def test_uoc005_ui_shows_hashes_backup_reference_and_responsive_governance_surface():
    ui=read('ui/web/src/components/DocumentEditPlanner.ts'); css=read('ui/web/src/styles.css')
    assert 'Pre SHA' in ui and 'Post SHA' in ui and 'backup_ref' in ui
    assert '.uoc005-governance' in css and '.uoc005-approval-card' in css and '.uoc005-execution-card' in css
    assert '@media (max-width:720px)' in css


def test_uoc005_ui_preserves_execution_across_document_reload_and_supports_recovery():
    ui=read('ui/web/src/components/DocumentEditPlanner.ts')
    for marker in [
        'transientMutationReload',
        'rememberExecution(nextExecution)',
        'recoverExecutionForDocument',
        'workspaceEditExecutionStatus',
        'EXECUTION_QUERY_PARAM',
        'APPLY PASS (recuperado)',
        'ROLLBACK PASS (recuperado)',
    ]:
        assert marker in ui
    assert "if (!plan && !execution) return;" in ui
    assert "if (documentValue) void recoverExecutionForDocument(documentValue);" in ui
    assert "execution.document_id === currentDocument.document_id" in ui


def test_uoc005_recovered_execution_exposes_persistent_evidence_refs_without_reapply():
    ui=read('ui/web/src/components/DocumentEditPlanner.ts')
    for marker in ['Approval ID', 'Evidence', 'Report', 'Restored SHA', 'evidence_ref', 'report_ref']:
        assert marker in ui
    recovery_block=ui[ui.index('async function recoverExecutionForDocument'):ui.index('function secretLike')]
    assert 'applyWorkspaceEdit' not in recovery_block
    assert 'rollbackWorkspaceEdit' not in recovery_block
